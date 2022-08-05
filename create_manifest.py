import numpy as np
import pandas as pd
import json
import boto3
import glob
import os
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from PIL import Image

bucket = "set you bucket"
prefix = "dataset/mvtec_anomaly_detection"
s3 = boto3.resource('s3')
labeling_job_name = "mvtec-ss"
local_mvtec_path = "set your lonal dataset path"


## create colormap for PIL putpallet
cm = plt.cm.get_cmap('tab20') # get color map from matplotlib
cm_colors_list = list(cm.colors)
cm_colors_list.insert(0, (1,1,1)) # first label is BACKGROUND data #ffffff
cm_colors_tuple = tuple(cm_colors_list)
color_palette = (np.array(cm_colors_list) * 255).astype(int) # [0, 255]
color_palette = list(color_palette.flatten()) # length = 3 * (20 + 1)
 


### Find materials containing more than 20 images per anomaly
materials_over_20_images = [] # initialize

materials_folders = glob.glob(os.path.join(local_mvtec_path, '**/'))

for m in materials_folders:
    is_over_20 = True # initialize
    material_name = m.split("/")[-2]
    print(f"\t {material_name}")
    anomalies_folders = glob.glob(os.path.join(m, 'test', '**/'))

    for i, a in enumerate(anomalies_folders):
        anomaly_name = a.split("/")[-2]
        input_images = glob.glob(os.path.join(a, '*.png'))
        num_images = len(input_images)
        print(f"\t\t{anomaly_name}: {num_images} images")
        if num_images < 20:
            is_over_20 = False
    if is_over_20:
        materials_over_20_images.append(material_name)

print(f"materials containing more than 20 images for each anomaly")
print(materials_over_20_images)


### create output.manifest for over20-image materials
for material_name in materials_over_20_images:
    m = os.path.join(local_mvtec_path, material_name)
    anomalies_folders = glob.glob(os.path.join(m, 'test', '**/'))
    anomaly_name_list = [f.split("/")[-2] for f in anomalies_folders]

    mask_metadata = {#"internal-color-map":"cannot set here, will be set later for each sample""
            "type":"groundtruth/semantic-segmentation",
            "human-annotated":"no",
            "creation-date":"2022-08-04T14:50:00.000000",
            "job-name":"labeling-job/" + labeling_job_name
            }
 
    label_metadata = {#"class-name":"cannot set here" will be set later for eash sample",
           "job-name":"labeling-job/" + labeling_job_name,
           "human-annotated":"no",
           "creation-date":"2022-08-04T14:50:00.000000",
           "type":"groundtruth/image-classification"
           }

  
    with open(f"{material_name}.manifest", "w") as f:
        class_key = 0 # counter

        for a in anomalies_folders:
            anomaly_name = a.split("/")[-2]
            input_images = glob.glob(os.path.join(a, "*.png"))

            if anomaly_name == "good":
                anomaly_label=0
                label_class_name = "normal" # to be used in label-metadata
                internal_color_map = {"0": {"class-name":"BACKGROUND", # to be used in mask-metadata
                                            "hex-color":"#ffffff",
                                            "confidence":0
                                            }
                                        }
            else:
                class_key += 1
                anomaly_label=1
                label_class_name = "anomaly" # to be used in label-metadata
                internal_color_map = {str(class_key): {"class-name":str(anomaly_name), # to be used in mask-metadata
                                                       "hex-color":mcolors.to_hex(cm_colors_tuple[class_key]),
                                                       "confidence":0
                                                       }
                                                   }

            # insert to metadata dictionaly
            mask_metadata["internal-color-map"] = internal_color_map
            label_metadata["class-name"] = label_class_name,


            # create png image for both normal and anomaly data
            for img_path in input_images:
                basename = os.path.basename(img_path)

                # If normal, create empty image
                if anomaly_name == "good":
                    img = Image.open(img_path)
                    arr = np.zeros(img.size) 
                    arr = arr.astype(np.int32)
                    mask_img = Image.fromarray(arr)
                # If anomaly, modify mask image (_mask.png)
                else:
                    mask_img_path = img_path.replace("test", "ground_truth").replace(".png", "_mask.png")
                    mask_img = Image.open(mask_img_path)
                    arr = np.array(mask_img)
                    arr[arr==255] = class_key
                    print("class_key: " + str(class_key))
                    mask_img = Image.fromarray(arr)
                mask_img = mask_img.convert('P')
                mask_img.putpalette(color_palette)
                mask_img.save("tmp.png")
                s3_upload_path = os.path.join(prefix, 
                                                material_name, 
                                                "modified_ground_truth", 
                                                anomaly_name, 
                                                basename.replace(".png", "_mask.png")
                                                )
                s3.Bucket(bucket).upload_file("tmp.png", s3_upload_path)
                print("S3 upload done: " + s3_upload_path)

                source_ref = os.path.join("s3://", bucket, prefix, material_name, "test", anomaly_name, basename)
                mask_ref = os.path.join("s3://", bucket, prefix, material_name, "modified_ground_truth", anomaly_name, basename.replace(".png", "_mask.png"))

                # finally create json lines for each sample
                out = {"source-ref":source_ref,
                        "anomaly-label":anomaly_label,
                        "anomaly-label-metadata":label_metadata,
                        "anomaly-mask-ref":mask_ref,
                        "anomaly-mask-ref-metadata":mask_metadata}
                out_str = json.dumps(out, separators=(',', ':'))
                f.write(out_str + '\n') # dump json line
    
    # upload manifest file for each material
    s3.Bucket(bucket).upload_file(f"{material_name}.manifest", 
                                os.path.join(prefix, material_name, f"{material_name}.manifest")
                                )

            
