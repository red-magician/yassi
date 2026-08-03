"""
mango_grader.py — マンゴー表面等級 自動判定モデル

概要
----
果実1個の写真から、JA沖縄の表面等級（A=赤秀 / B=黒秀 / C=白箱）を推定する。
2019年撮影の178枚（人間の判定つき）で学習・検証済み。

判定方式
--------
1. 画像から果実領域を切り出す（背景は無彩色前提）
2. 果実の各画素を Lab 色空間に変換し、鮮紅色画素を判定
     鮮紅色 = (a* > A_THR) かつ (色相角 < H_THR)
3. 3つの特徴を計算する
     vr_whole           : 鮮紅色画素が果実面積に占める割合(%)
     blob_largest_frac  : 鮮紅色領域の最大連結成分が占める割合(%)
     blob_n             : 鮮紅色領域の連結成分の数（小さい断片は除外）
4. ロジスティック回帰（3クラス, 標準化込み）で A/B/C を判定

性能（2019年撮影データ、5-fold×20反復=100分割の交差検証）
  正解率  93.0%
  macro-F1 0.744
  kappa    0.747
  等級別正答率: C 100% (60/60) ／ B 85.2% (341/400) ／ A 93.9% (2911/3100)
  参考: JA公式ルール(面積率のみ, 70%/30%)は macro-F1 0.685
        → 連結性を加えた本モデルが統計的に有意に上回る (Wilcoxon p=0.0035)

重要な注意（アプリ化にあたって必読）
----------------------------------
* このモデルの閾値 A_THR・H_THR・重みは【2019年の撮影条件】に較正されている。
  カメラ・照明・背景・ホワイトバランスが変わると、同じ果実でも
  鮮紅色画素の割合が変わり、精度が保証されなくなる。
  → 新しい撮影環境で使う場合は、既知の等級のサンプルを使って
     再較正 (calibrate_thresholds 関数) すること。
  → 実例: 2010年の色差計データで最良だったBチャンネルは画像には
     移植できず、鮮紅色の(a*,色相角)閾値も2010年と2019年で
     別の値になった。閾値の使い回しは危険。

* 学習データはC級がわずか3枚と極端に不均衡。C級の性能(100%)は
  サンプル数が少ないための見かけ上の高さである可能性が高く、
  実運用で大量のC級を判定する場合は改めて検証すること。

* 本モデルは「表面の着色」のみを見ている。傷・ヤニによる
  格下げ（JA基準の複合ルール）は判定できない。最終結果まで
  含めた判別を行うには、別途、傷・ヤニ検出モデルが必要。
  2019年データでの検証では、表面等級94.9%に対し最終結果は69.1%
  （傷ヤニを見ていない分のギャップが約26ポイント）。

* 選択的予測を推奨: 判定確率が閾値付近の果実は人の確認に回すと
  精度が大きく上がる（80%自動化で正解率99.3%）。
  predict_proba() の最大確率が低い個体を "要確認" として
  UIに出すことを推奨する。
"""
import json
import numpy as np
import cv2
from PIL import Image

# ── 較正済みパラメータ（2019年撮影条件） ──────────────────────
A_THR = 28          # a* の閾値
H_THR = 45           # 色相角の閾値(度)
MAXPX = 1200         # 長辺をこの画素数に縮小して処理

# ロジスティック回帰の係数（3クラス, one-vs-rest, 標準化後）
# 178枚全データで学習した最終モデル。
FEATURE_NAMES = ["vr_whole", "blob_largest_frac", "blob_n"]
_SCALER_MEAN = None   # 実行時に MODEL_BUNDLE から読み込む
_SCALER_SCALE = None
MODEL_PATH_DEFAULT = "mango_grader_model.joblib"


# ── 特徴抽出 ────────────────────────────────────────────
def _fruit_mask(rgb):
    """背景(無彩色)を除去し、最大の連結領域を果実として返す"""
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    m = ((hsv[:, :, 1] > 60) & (hsv[:, :, 2] > 40)).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8), iterations=2)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8), iterations=3)
    n, lab_, st, _ = cv2.connectedComponentsWithStats(m, 8)
    if n <= 1:
        return None
    k = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    mask = (lab_ == k)
    mask = cv2.morphologyEx(mask.astype(np.uint8), cv2.MORPH_CLOSE,
                            np.ones((15, 15), np.uint8), iterations=3).astype(bool)
    return mask


def extract_features(image_path_or_array, a_thr=A_THR, h_thr=H_THR):
    """
    画像1枚から判定用の3特徴を抽出する。

    Parameters
    ----------
    image_path_or_array : str または np.ndarray(H,W,3) RGB
    a_thr, h_thr : 鮮紅色の定義(通常はデフォルトのまま使う)

    Returns
    -------
    dict  {"vr_whole":.., "blob_largest_frac":.., "blob_n":.., "n_px": ..}
    None が返る場合は果実領域を検出できなかったことを示す。
    """
    if isinstance(image_path_or_array, str):
        im = Image.open(image_path_or_array).convert("RGB")
        w, h = im.size
        s = MAXPX / max(w, h)
        if s < 1:
            im = im.resize((int(w * s), int(h * s)), Image.LANCZOS)
        rgb = np.asarray(im)
    else:
        rgb = image_path_or_array

    mask = _fruit_mask(rgb)
    if mask is None or mask.sum() < 5000:
        return None

    er = cv2.erode(mask.astype(np.uint8), np.ones((9, 9), np.uint8), iterations=3).astype(bool)
    core = er if er.sum() > mask.sum() * 0.3 else mask

    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).astype(float)
    a = lab[:, :, 1][core] - 128
    b = lab[:, :, 2][core] - 128
    hue = np.degrees(np.arctan2(b, a))
    vivid_flat = (a > a_thr) & (hue < h_thr)

    vivid_full = np.zeros(core.shape, bool)
    vivid_full[core] = vivid_flat

    n_core = int(core.sum())
    vr_whole = float(vivid_flat.sum()) / n_core * 100

    nn, lb, stt, _ = cv2.connectedComponentsWithStats(vivid_full.astype(np.uint8), 8)
    if nn > 1:
        areas = stt[1:, cv2.CC_STAT_AREA]
        blob_largest_frac = float(areas.max() / max(vivid_flat.sum(), 1) * 100)
        blob_n = int((areas > n_core * 0.005).sum())
    else:
        blob_largest_frac, blob_n = 0.0, 0

    return {"vr_whole": vr_whole, "blob_largest_frac": blob_largest_frac,
            "blob_n": blob_n, "n_px": n_core}


# ── 判定 ────────────────────────────────────────────────
class MangoGrader:
    """学習済みモデルを読み込んで等級判定を行う"""

    def __init__(self, model_path=MODEL_PATH_DEFAULT):
        import joblib
        bundle = joblib.load(model_path)
        self.pipeline = bundle["pipeline"]
        self.classes_ = bundle["classes"]
        self.feature_names = bundle["feature_names"]
        self.a_thr = bundle.get("a_thr", A_THR)
        self.h_thr = bundle.get("h_thr", H_THR)
        self.meta = bundle.get("meta", {})

    def predict(self, image_path_or_array, return_proba=False, confidence_threshold=0.55):
        """
        1枚を判定する。

        Returns
        -------
        dict:
          grade          : "A" / "B" / "C" / None(抽出失敗)
          proba          : {"A":.., "B":.., "C":..}
          confidence     : 最大確率
          needs_review   : confidence が閾値未満なら True
                            （UIで「要確認」に振り分けることを推奨）
          features       : 抽出した特徴量の生値
        """
        feat = extract_features(image_path_or_array, self.a_thr, self.h_thr)
        if feat is None:
            return {"grade": None, "proba": None, "confidence": None,
                    "needs_review": True, "features": None,
                    "error": "果実領域を検出できませんでした"}

        # 安全ガード: 鮮紅色画素が実質ゼロ(blob_n=0)の果実は学習データに
        # 一度も存在しない(学習データの最小値でも vr_whole は20%台)。
        # この領域でロジスティック回帰に外挿させると暴れる(検証済みの不具合:
        # 全緑の果実がB判定になる事故があった)ため、ここだけは
        # ルールベースで直接Cとする。JA基準でも鮮紅色0%はC以外にありえない。
        if feat["blob_n"] == 0:
            return {"grade": "C", "proba": {"A": 0.0, "B": 0.0, "C": 1.0},
                    "confidence": 1.0, "needs_review": False, "features": feat,
                    "note": "鮮紅色画素が検出されなかったため、判定モデルを介さずCとしました"}

        x = np.array([[feat[c] for c in self.feature_names]])
        proba = self.pipeline.predict_proba(x)[0]
        proba_dict = dict(zip(self.classes_, proba.round(4)))
        grade = self.classes_[int(np.argmax(proba))]
        conf = float(proba.max())

        out = {"grade": grade, "proba": proba_dict, "confidence": conf,
               "needs_review": conf < confidence_threshold, "features": feat}
        return out

    def predict_batch(self, image_paths, **kw):
        return [self.predict(p, **kw) for p in image_paths]

    @property
    def version(self):
        return self.meta.get("version", "unknown")


# ── フィードバック収集（継続学習用） ─────────────────────────
# 目的: アプリを使う人たちの画像・機械判定・（あれば）人の訂正を
#       時系列で溜め、後で retrain.py にまとめて渡して再学習する。
# 記録は1件1行の JSON Lines。画像そのものはコピーして残す
# （後日パスが失われても再学習できるようにするため）。

def log_prediction(result, image_path_or_array, result_dir="feedback_log",
                    user_id=None, extra=None):
    """
    predict() の結果を1件、feedback_log/ に記録する。
    画像も同じフォルダにコピーして保存する。

    Returns
    -------
    log_id : str  この予測を指すID（後で record_correction に使う）
    """
    import os, json, uuid, shutil, datetime
    os.makedirs(result_dir, exist_ok=True)
    log_id = uuid.uuid4().hex[:12]
    img_dir = os.path.join(result_dir, "images")
    os.makedirs(img_dir, exist_ok=True)

    if isinstance(image_path_or_array, str):
        ext = os.path.splitext(image_path_or_array)[1] or ".jpg"
        dst = os.path.join(img_dir, f"{log_id}{ext}")
        shutil.copy(image_path_or_array, dst)
    else:
        import cv2
        dst = os.path.join(img_dir, f"{log_id}.jpg")
        cv2.imwrite(dst, cv2.cvtColor(image_path_or_array, cv2.COLOR_RGB2BGR))

    record = {
        "log_id": log_id,
        "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
        "user_id": user_id,
        "image_file": os.path.relpath(dst, result_dir),
        "machine_grade": result.get("grade"),
        "confidence": result.get("confidence"),
        "needs_review": result.get("needs_review"),
        "features": result.get("features"),
        "human_grade": None,        # 後で record_correction() が埋める
        "human_grade_source": None, # "app_user" / "expert_review" など
        "extra": extra or {},
    }
    with open(os.path.join(result_dir, "log.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return log_id


def record_correction(log_id, human_grade, source="app_user", result_dir="feedback_log",
                      has_defect=False):
    """
    ある予測(log_id)に対して、人が判定した正しい等級を後から記録する。
    アプリの「これは違う」ボタンなどから呼ぶことを想定。

    has_defect : この果実に傷・ヤニなど、色以外の理由で等級が下がる要素が
                 あるかどうか。True の場合、retrain.py はこのサンプルを
                 「色だけの判定器」の学習データから除外する
                 （本アプリの色モデルは着色のみを見る設計のため、
                   傷・ヤニで下がった個体の色情報を正解として学習させると
                   モデルの性質がぶれる。2019年撮影データでも同じ理由で
                   傷ヤニ54枚・原因不明降格10枚を学習から除外している）。
    """
    import os, json, datetime
    assert human_grade in ("A", "B", "C"), "human_grade は A/B/C のいずれか"
    record = {
        "log_id": log_id,
        "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
        "correction_for": log_id,
        "human_grade": human_grade,
        "human_grade_source": source,
        "has_defect": bool(has_defect),
    }
    with open(os.path.join(result_dir, "corrections.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


# ── 較正（撮影環境を変える場合に使う） ─────────────────────────
def calibrate_thresholds(image_paths, human_grades, a_grid=range(12, 45, 2),
                         h_grid=range(20, 60, 2)):
    """
    新しい撮影環境向けに (a_thr, h_thr) を選び直す。

    Parameters
    ----------
    image_paths : 較正用サンプルの画像パスのリスト（各等級20枚程度を推奨）
    human_grades : 対応する人間の判定 "A"/"B"/"C" のリスト

    Returns
    -------
    (best_a_thr, best_h_thr, score) — macro-F1 が最大の組
    """
    from sklearn.metrics import f1_score
    y = np.array(human_grades)
    feats_cache = {}
    best = (None, None, -1)
    for a in a_grid:
        for h in h_grid:
            preds = []
            for p in image_paths:
                key = (p, a, h)
                if key not in feats_cache:
                    feats_cache[key] = extract_features(p, a, h)
                f = feats_cache[key]
                preds.append("C" if f is None else
                             ("A" if f["vr_whole"] >= 70 else
                              ("B" if f["vr_whole"] >= 30 else "C")))
            s = f1_score(y, preds, average="macro", labels=["C", "B", "A"], zero_division=0)
            if s > best[2]:
                best = (a, h, s)
    return best
