"""
retrain.py — フィードバックデータを取り込んで再学習する

使い方:
    python retrain.py

何をするか:
  1. 元の学習データ（178枚, base_features.csv）を読む
  2. feedback_log/log.jsonl と feedback_log/corrections.jsonl を読み、
     「人の訂正が付いた予測」だけを新しい学習データとして採用する
     （機械の判定をそのまま鵜呑みにはしない）
  3. 新しい画像は特徴量が未計算なので、その場で抽出する
  4. 元データ＋新データを合わせて学習し、5-fold×20反復の交差検証で評価
  5. 「新モデルが旧モデルより悪化していないか」を確認したうえで
     mango_grader_model.joblib を新バージョンとして書き出す
     （悪化していた場合は書き出さずに警告するだけ）
  6. 旧バージョンは mango_grader_model.v{n}.joblib として残す（ロールバック用）

安全策:
  - 訂正のない予測ログ（人がチェックしなかったもの）は学習に使わない。
    machine_grade をそのまま正解として使うと、モデルが自分の誤りを
    正解として学習してしまい、誤りを強化する悪循環になるため。
  - 新規クラスの個体が極端に少ない場合（例: 新データにC級が1枚もない）は
    警告を出す。
  - 性能が閾値以上悪化した場合は自動採用しない。
"""
import os, json, glob
import numpy as np, pandas as pd, joblib
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.metrics import f1_score, cohen_kappa_score, accuracy_score

from mango_grader import extract_features

MODEL_PATH = "mango_grader_model.joblib"
BASE_FEATURES = "base_features.csv"          # 元の178枚分の特徴量(同梱)
FEEDBACK_DIR = "feedback_log"
COLS = ["vr_whole", "blob_largest_frac", "blob_n"]
ORDER = ["C", "B", "A"]
DEGRADE_TOLERANCE = 0.02      # macro-F1 がこれ以上下がったら自動採用しない


def load_base():
    df = pd.read_csv(BASE_FEATURES)
    df["source"] = "base_2019"
    return df


def load_new_from_feedback():
    """訂正が付いたログだけを新データとして集める"""
    log_path = os.path.join(FEEDBACK_DIR, "log.jsonl")
    corr_path = os.path.join(FEEDBACK_DIR, "corrections.jsonl")
    if not os.path.exists(log_path):
        return pd.DataFrame(columns=COLS + ["surface", "source", "img"])

    logs = [json.loads(l) for l in open(log_path, encoding="utf-8")]
    logs = {r["log_id"]: r for r in logs}          # 同じIDは最新で上書き

    corrections = {}
    if os.path.exists(corr_path):
        for l in open(corr_path, encoding="utf-8"):
            r = json.loads(l)
            corrections[r["log_id"]] = {"human_grade": r["human_grade"],
                                        "has_defect": r.get("has_defect", False)}   # 最新の訂正で上書き

    rows = []
    for log_id, rec in logs.items():
        corr = corrections.get(log_id)
        if corr is None:
            continue                                       # 訂正なしはスキップ
        if corr["has_defect"]:
            continue                                       # 傷・ヤニありは色モデルの学習から除外
        human = corr["human_grade"]
        feat = rec.get("features")
        if feat is None:
            # ログに特徴量が無い場合は画像から抽出し直す
            img_path = os.path.join(FEEDBACK_DIR, rec["image_file"])
            if not os.path.exists(img_path):
                continue
            feat = extract_features(img_path)
            if feat is None:
                continue
        row = {c: feat[c] for c in COLS}
        row["surface"] = human
        row["source"] = "feedback"
        row["img"] = log_id
        rows.append(row)
    return pd.DataFrame(rows)


def cross_val(X, y):
    cv = RepeatedStratifiedKFold(n_splits=5, n_repeats=20, random_state=0)
    accs, f1s, kaps = [], [], []
    for tr, te in cv.split(X, y):
        m = make_pipeline(SimpleImputer(), StandardScaler(),
                          LogisticRegression(max_iter=3000, class_weight="balanced"))
        m.fit(X[tr], y[tr])
        p = m.predict(X[te])
        accs.append(accuracy_score(y[te], p))
        f1s.append(f1_score(y[te], p, average="macro", labels=ORDER, zero_division=0))
        kaps.append(cohen_kappa_score(y[te], p, labels=ORDER))
    return float(np.mean(accs)), float(np.mean(f1s)), float(np.mean(kaps))


def main():
    base = load_base()
    new = load_new_from_feedback()
    print(f"元データ: {len(base)}枚 / フィードバック(訂正あり): {len(new)}枚")

    if len(new) == 0:
        print("新しい訂正データがありません。再学習をスキップします。")
        return

    for g in ORDER:
        if (new.surface == g).sum() == 0:
            print(f"  [注意] 新データに {g} 級の訂正が1件もありません")

    all_df = pd.concat([base[COLS + ["surface", "source"]],
                        new[COLS + ["surface", "source"]]], ignore_index=True)
    X, y = all_df[COLS].values, all_df.surface.values

    old_bundle = joblib.load(MODEL_PATH) if os.path.exists(MODEL_PATH) else None
    old_f1 = old_bundle["meta"]["cv_macro_f1"] if old_bundle else None

    acc, f1, kap = cross_val(X, y)
    print(f"\n新モデル（元{len(base)}+新{len(new)}枚, n={len(all_df)}）の交差検証:")
    print(f"  正解率 {acc*100:.1f}%  macroF1 {f1:.3f}  kappa {kap:.3f}")
    if old_f1 is not None:
        print(f"  旧モデルのmacroF1 {old_f1:.3f}  差 {f1-old_f1:+.3f}")

    if old_f1 is not None and f1 < old_f1 - DEGRADE_TOLERANCE:
        print(f"\n[中止] 新モデルは旧モデルより {old_f1-f1:.3f} 悪化しています。"
              f"自動採用しません。データを確認してください。")
        return

    # 最終モデルは全データで学習
    final_pipeline = make_pipeline(SimpleImputer(), StandardScaler(),
                                   LogisticRegression(max_iter=3000, class_weight="balanced"))
    final_pipeline.fit(X, y)

    old_version = old_bundle["meta"].get("version", "v0") if old_bundle else "v0"
    new_version = f"v{int(old_version[1:]) + 1}" if old_version.startswith("v") else "v1"

    if old_bundle is not None:
        backup_path = MODEL_PATH.replace(".joblib", f".{old_version}.joblib")
        joblib.dump(old_bundle, backup_path)
        print(f"旧モデルを {backup_path} として保存")

    bundle = {
        "pipeline": final_pipeline,
        "classes": final_pipeline.named_steps["logisticregression"].classes_.tolist(),
        "feature_names": COLS,
        "a_thr": old_bundle["a_thr"] if old_bundle else 28,
        "h_thr": old_bundle["h_thr"] if old_bundle else 45,
        "meta": {
            "version": new_version,
            "trained_at": pd.Timestamp.now().strftime("%Y-%m-%d"),
            "parent_version": old_version,
            "n_train": len(all_df),
            "n_base": len(base), "n_feedback": len(new),
            "cv_macro_f1": f1, "cv_kappa": kap, "cv_accuracy": acc,
            "cv_scheme": "StratifiedKFold 5-fold x 20 repeats (100 folds)",
            "note": "フィードバックで再学習したモデル。撮影条件が大きく変わる場合は"
                    "calibrate_thresholds() の再実行も検討すること。",
        },
    }
    joblib.dump(bundle, MODEL_PATH)
    print(f"\n新モデル {new_version} を {MODEL_PATH} として保存しました。")


if __name__ == "__main__":
    main()
