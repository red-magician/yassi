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
│       ├── calibrate.js      # mango_grader.py の calibrate_thresholds() の移植
│       ├── worker.js         # 通常の判定をWeb Workerで実行（UIスレッドを塞がない）
│       ├── calibrate-worker.js # 較正の総当たり計算をWeb Workerで実行
│       └── app.js            # 画面制御・カメラ入力・較正モードUI・API呼び出し
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

## アプリ内較正モード

上記のとおりA判定が出にくい傾向が確認されたため、`calibrate_thresholds()`
（撮影環境向けに色のしきい値 `a_thr`/`h_thr` を選び直す機能）を**アプリ内でも
実行できるように移植しました**。設定 → 「⚙ 較正モード（スタッフ向け）」から：

1. 実際の撮影環境で撮った、正解の等級が分かっているサンプル写真を追加する
   （各写真ごとにA/B/Cを選択。目安は各等級20枚程度、最低4枚から実行可）
2. 「較正を実行」→ ブラウザ内でグリッドサーチ（`a_thr`は12〜44、`h_thr`は20〜58を
   2刻み、元のPython版と同じ範囲・同じJA単純ルールでスコアリング）を行い、
   現在の設定との比較（macro-F1スコア）を表示する
3. 「この設定を適用する」で、以降の判定にその `a_thr`/`h_thr` が使われる
   （端末のlocalStorageに保存。「既定の設定に戻す」でいつでも元に戻せる）

**注意**: これは色のしきい値だけを選び直す機能で、ロジスティック回帰自体の
再学習ではありません（そちらは元の設計どおり `retrain.py` をオフラインで実行）。
また `calibrate_thresholds()` はグリッドの全組み合わせ×全サンプルで連結成分の
計算をやり直すため、サンプル枚数が多いとブラウザ内での計算に時間がかかります
（進捗バーを表示します）。

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
- **実写真7枚でPython版と突き合わせ済みです。** 等級判定は7/7枚で完全一致、
  果実マスクの画素数(`n_px`)も7/7枚で完全一致、`vr_whole`も差0.06ポイント未満でした。
  一方 `blob_largest_frac`/`blob_n`（連結成分まわりの特徴量）は2/7枚でややずれました
  （原因はOpenCVのLab変換の内部近似との量子化誤差、詳細は下記）。数値・原因・
  再現手順は [`VALIDATION.md`](./VALIDATION.md) を参照してください。
  検証・比較用のスクリプトは `tools/dump_ground_truth.py` と `tools/compare.mjs` に
  同梱しているので、新しい写真が手に入るたびに再検証できます。
- **この検証で、JS移植とは別の、より重要な問題も見つかりました。** 検証に使った
  7枚の実写真では、A判定が1件も出ず6枚がB・1枚がCでした。目視では赤みの強い
  果実が複数含まれているにもかかわらず`vr_whole`が学習データの想定範囲を下回って
  おり、モデルカードが警告している「撮影条件が変わるとA級が出なくなる」既知の
  失敗パターンとみられます。**本番投入前に、実際の撮影条件で `calibrate_thresholds()`
  による再較正を強く推奨します。** 詳細は [`VALIDATION.md`](./VALIDATION.md)。

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

- **本番投入前に撮影環境向けの再較正を推奨**（[`VALIDATION.md`](./VALIDATION.md) 参照）。
  検証に使った実写真ではA判定が1件も出ませんでした。「較正モード」でアプリ内から
  再較正できます（上記「アプリ内較正モード」参照）。
- `blob_largest_frac`/`blob_n` はOpenCVのLab変換の内部近似との量子化誤差により、
  JS版とPython版で稀にずれることがあります（[`VALIDATION.md`](./VALIDATION.md)）。
- `/api/log` `/api/correction` はオフライン時は静かに失敗します（再送キューは未実装）。
- アプリ内較正モードは色のしきい値（`a_thr`/`h_thr`）だけを選び直します。
  ロジスティック回帰自体の再学習は引き続き `retrain.py` をオフラインで実行してください。
