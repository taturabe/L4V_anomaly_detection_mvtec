# L4V_anomaly_detection_mvtec

異常検知（外観検査）のデータセット[Mvtec AD](https://www.mvtec.com/company/research/datasets/mvtec-ad)をAWSの外観検査サービス[Lookout for Vision](https://aws.amazon.com/jp/lookout-for-vision/) で試すためのデータ変換セットスクリプトです。

異常画像が20枚以上あるデータセットのみを対象にしています。



## 使い方

* mvtec ADのサイトよりデータをダウンロードしてください。
* create_manifest.pyのなかの下記の変数を自分の環境に書き換えてください
   * bucket: 画像データをアップロードするS3バケット名
   * prefix: 画像データをアップロードするS3プレフィックス
   * local_mvtec_path: ダウンロードしたmvtecデータセットの親フォルダ（直下にbottle, cableなどのデータセットフォルダがあること）

* 以下のコードを実行します

```
python create_manifest.py
```

画像ファイルおよび対応するmanifestファイルがS3にアップロードされます。各クラスのmanifestファイルをLookout for visionのデータセットソースに指定することで、データのインポートができます。

### requirements

- boto3
- numpy
- pandas
- matplotlib
- PIL

### NOTES:

MVTEC ADのライセンスに準拠した使い方をしてください。

https://www.mvtec.com/company/research/datasets/mvtec-ad
