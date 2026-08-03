# マンゴー等級判定（試作） — Cloudflare Pages PWA

スマホのカメラでマンゴーを撮ると、表面等級（A=赤秀 / B=黒秀 / C=白箱）をその場で
判定する試作アプリです。Cloudflare Pages 上にホストし、ホーム画面に追加して
ネイティブアプリのように使えます（PWA）。

## 構成

- **判定はすべてブラウザ内で完結します。** サーバーにもCloudflare Workers AIにも
  投げません。`python-reference/mango_grader.py` の学習済みモデル
  （`mango_grader_model.joblib`）の中身をそのままJavaScriptに移植しています。
- Cloudflare Pages（静的ホスティング）+ Pages Functions（Workers）+ D1（フィードバック保存用DB）
- ビルドステップなし（素のES Modules）。フレームワーク不使用。

```
mango-grader/
├── public/                 # Cloudflare Pagesが配信する静的アセット（PWA本体）
│   ├── index.html
│   ├── manifest.webmanifest
│   ├── sw.js                # オフラインキャッシュ用Service Worker
│   ├── css/style.css
│   └── js/
│       ├── imaging.js       # HSV/Lab変換・二値の膨張収縮・連結成分（cv2互換の自前実装）
│       ├── features.js      # mango_grader.py の extract_features() の移植
│       ├── model.js         # joblibの中身（Imputer/Scaler/LogisticRegression係数）を直書き
│       ├── worker.js         # 上記をWeb Workerで実行（UIスレッドを塞がない）
│       └── app.js            # 画面制御・カメラ入力・API呼び出し
├── functions/api/
│   ├── log.js                # POST 判定ログの保存（画像は送らない。数値のみ）
│   ├── correction.js         # POST 人による訂正の保存
│   └── export.js             # GET  再学習用に log.jsonl/corrections.jsonl 形式で書き出し
├── schema.sql                 # D1スキーマ
├── wrangler.toml
└── python-reference/          # 元のPythonモデル一式（オフライン再学習用にそのまま同梱）
    ├── mango_grader.py
    ├── mango_grader_model.joblib
    ├── retrain.py
    ├── base_features.csv
    └── MODEL_CARD.md          # 元のモデルカード（撮影条件の較正・既知の不具合など重要な注意点）
```

## 判定モデルについて（必ず読んでください）

`python-reference/MODEL_CARD.md` に元のモデルカードがそのまま入っています。特に重要な点：

- **2019年撮影178枚の条件に較正されたモデル**です。スマホでの撮影環境（背景・照明・
  ホワイトバランス）が変わると精度が落ちる可能性があります。実運用前に、実際の撮影
  環境で正解付きサンプルを集めて `calibrate_thresholds()` で閾値を選び直すことを
  強く推奨します（`python-reference/mango_grader.py` 内）。
- **表面の着色のみを判定します。** 傷・ヤニによる格下げは見ていません。最終等級は
  人が確認する前提の設計です。
- **学習データはA100/B11/C3と極端に不均衡**で、特にC級の精度は未検証に近いです。
- 確信度が低い判定は自動的に「要確認」と表示されます（`confidence_threshold=0.55`）。

アプリのUI冒頭にもこれらの注意を警告バナーとして表示しています。

## JS移植の正確性について

`public/js/imaging.js` は OpenCV (`cv2`) の `cvtColor`（HSV/Lab）・`morphologyEx`
（膨張・収縮）・`connectedComponentsWithStats` を、ドキュメント化されたアルゴリズム
どおりに手書きで再実装したものです（依存ライブラリなし・OpenCV.jsのWASMも不要）。

- 膨張・収縮は「同じ矩形フラット構造要素を`iterations`回繰り返す」＝「1回だけ、
  実効カーネルサイズ `(k-1)*iterations+1` で処理する」という数学的に厳密な等価性を
  使って、ループなしの1パス（分離可能なmin/maxフィルタ）で実装しています。
- ロジスティック回帰の係数（`model.js`）は `mango_grader_model.joblib` から抽出した
  実際の数値です。Node上でsklearnの`predict_proba`出力と突き合わせて一致することを
  確認済みです（複数のテスト特徴量ベクトルで完全一致）。
- 一方、**画像処理パイプライン全体（HSV/Labの色変換の丸め誤差・リサイズのアルゴリズム
  差）は実写真での検証をまだ行っていません。** 元データの画像ファイルが手元になく、
  Python版とJS版を同じ写真で突き合わせるテストができていないためです。デプロイ後、
  実際の写真で `python-reference/mango_grader.py` の出力とアプリの「詳細を見る」欄
  （vr_whole / blob_largest_frac / blob_n）を突き合わせて検証することを推奨します。

## フィードバック・再学習の仕組み

元のモデルの設計（`MODEL_CARD.md` の「みんなに使ってもらいながら再学習する仕組み」）
をそのまま踏襲しています。

1. 判定するたびに、**画像を送らず**数値（特徴量・等級・確信度）だけを `/api/log` 経由で
   D1に記録します（アプリのトグルでオフにできます）。
2. 「この判定は違う」から人が正しい等級を入力すると `/api/correction` に記録されます。
3. `/api/export?token=...&kind=log` / `kind=corrections` で、元の `feedback_log/log.jsonl`
   / `corrections.jsonl` と**同じスキーマ**でダウンロードできます。特徴量は毎回
   ログに含まれているため、`retrain.py` は画像なしでもそのまま動きます。
4. ダウンロードした2ファイルを `python-reference/feedback_log/` に置き、
   `python python-reference/retrain.py` を実行すると再学習されます（このリポジトリの
   外、開発者のPCで実行する想定。既存の設計どおり「訂正のない予測は学習に使わない」
   「旧モデルより悪化したら自動採用しない」という安全策も踏襲されています）。

## デプロイ手順

前提: [Cloudflareアカウント](https://dash.cloudflare.com/) と `wrangler` CLI
（`npm install -g wrangler` または `npx wrangler`）。

```bash
cd mango-grader

# 1. D1データベースを作成し、wrangler.tomlのdatabase_idを書き換える
npx wrangler d1 create mango_grader_db
# 出力された database_id を wrangler.toml の REPLACE_WITH_D1_DATABASE_ID に貼り付ける

# 2. スキーマを適用
npx wrangler d1 execute mango_grader_db --remote --file=./schema.sql

# 3. 書き出しAPIのトークンを設定（未設定だと/api/exportは常に401を返す）
npx wrangler pages secret put EXPORT_TOKEN --project-name mango-grader

# 4. デプロイ
npx wrangler pages deploy public --project-name mango-grader
```

初回デプロイ後は、Cloudflareダッシュボード側でこのGitHubリポジトリと連携すれば
push時に自動デプロイもできます（Pages > プロジェクト > Git連携）。

### ローカルで動作確認

```bash
npx wrangler pages dev public --d1=DB
```

## 既知の制約・今後やること

- 画像処理をJSで手書き移植したため、**実写真でのPython版との突き合わせ検証が未実施**
  （上記「JS移植の正確性について」参照）。
- `/api/log` `/api/correction` はオフライン時は静かに失敗します（再送キューは未実装）。
- 撮影環境向けの閾値再較正（`calibrate_thresholds`）はまだPython版のみで、アプリ内
  UIからは行えません。
