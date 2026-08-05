"""
dump_ground_truth.py — validation helper (not part of the deployed app).

Runs the original Python model (python-reference/mango_grader.py) on a
folder of real photos and dumps two things for each image:
  - a lossless .ppm of the exact resized RGB array extract_features() saw
    (so the JS port can be fed the identical pixel data — removing any
    JPEG-decode/resize difference as a variable)
  - the Python ground-truth features/grade, as JSON

Usage:
    python dump_ground_truth.py <photos_dir> <out_dir>

Then compare with tools/compare.mjs.
"""
import os, sys, json, warnings

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python-reference"))
from PIL import Image
import numpy as np
from mango_grader import extract_features, MangoGrader, MAXPX


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    src_dir, out_dir = sys.argv[1], sys.argv[2]
    ppm_dir = os.path.join(out_dir, "ppm")
    os.makedirs(ppm_dir, exist_ok=True)

    model_path = os.path.join(os.path.dirname(__file__), "..", "python-reference", "mango_grader_model.joblib")
    grader = MangoGrader(model_path)

    results = {}
    for fname in sorted(os.listdir(src_dir)):
        path = os.path.join(src_dir, fname)
        if not os.path.isfile(path):
            continue
        im = Image.open(path).convert("RGB")
        w, h = im.size
        s = MAXPX / max(w, h)
        if s < 1:
            im = im.resize((int(w * s), int(h * s)), Image.LANCZOS)
        rgb = np.asarray(im)

        ppm_path = os.path.join(ppm_dir, fname + ".ppm")
        hh, ww = rgb.shape[0], rgb.shape[1]
        with open(ppm_path, "wb") as f:
            f.write(f"P6\n{ww} {hh}\n255\n".encode("ascii"))
            f.write(rgb.tobytes())

        feat = extract_features(rgb)
        pred = grader.predict(path)

        results[fname] = {
            "resized_wh": [ww, hh],
            "extract_features_on_resized_array": feat,
            "predict_full": {k: v for k, v in pred.items() if k != "features"},
        }
        print(fname, "->", pred.get("grade"), pred.get("confidence"), feat)

    with open(os.path.join(out_dir, "ground_truth.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
