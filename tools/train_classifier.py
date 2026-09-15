"""Baseline problem classifier: TF-IDF + logistic regression.

Honest baseline only: default hyperparameters, no alternative models.
Stratified 80/20 split on a fixed seed; fit happens on the train split
only, the test split is touched exactly once, for evaluation.

Run: .venv/Scripts/python.exe tools/train_classifier.py
"""
import json
import pickle
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

SEED = 42
DATA_PATH = Path("data/problems.csv")
MODELS_DIR = Path("models")
TOP_N_FEATURES = 10
ACCURACY_FLAG_THRESHOLD = 0.95


def _json_default(o):
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    raise TypeError(f"not JSON serializable: {type(o)}")


def main():
    MODELS_DIR.mkdir(exist_ok=True)

    df = pd.read_csv(DATA_PATH)
    X, y = df["text"], df["category"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=SEED
    )

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer()),
        ("clf", LogisticRegression(max_iter=1000, random_state=SEED)),
    ])
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    classes = pipeline.named_steps["clf"].classes_

    accuracy = float(accuracy_score(y_test, y_pred))
    report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
    cm = confusion_matrix(y_test, y_pred, labels=classes)

    # --- confusion matrix plot ---
    fig, ax = plt.subplots(figsize=(8, 7))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks(range(len(classes)))
    ax.set_yticks(range(len(classes)))
    ax.set_xticklabels(classes, rotation=45, ha="right")
    ax.set_yticklabels(classes)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title(f"Confusion matrix (test accuracy={accuracy:.3f})")
    for i in range(len(classes)):
        for j in range(len(classes)):
            if cm[i, j]:
                ax.text(j, i, str(cm[i, j]), ha="center", va="center",
                         color="white" if cm[i, j] > cm.max() / 2 else "black")
    fig.colorbar(im, ax=ax)
    fig.tight_layout()
    fig.savefig(MODELS_DIR / "confusion_matrix.png", dpi=150)
    plt.close(fig)

    # --- confused class pairs ---
    directional_pairs = []
    for i in range(len(classes)):
        for j in range(len(classes)):
            if i != j and cm[i, j] > 0:
                directional_pairs.append(
                    {"true": classes[i], "predicted": classes[j], "count": int(cm[i, j])}
                )
    directional_pairs.sort(key=lambda d: -d["count"])

    aggregated_pairs = []
    for i in range(len(classes)):
        for j in range(i + 1, len(classes)):
            total = int(cm[i, j] + cm[j, i])
            if total > 0:
                aggregated_pairs.append(
                    {"pair": [classes[i], classes[j]], "count": total}
                )
    aggregated_pairs.sort(key=lambda d: -d["count"])

    # --- top-weighted features per class ---
    vectorizer = pipeline.named_steps["tfidf"]
    clf = pipeline.named_steps["clf"]
    feature_names = np.array(vectorizer.get_feature_names_out())
    top_features = {}
    for idx, cls in enumerate(classes):
        coefs = clf.coef_[idx]
        top_idx = np.argsort(coefs)[::-1][:TOP_N_FEATURES]
        top_features[cls] = [
            {"feature": feature_names[i], "weight": float(coefs[i])} for i in top_idx
        ]

    # --- save pipeline ---
    with open(MODELS_DIR / "classifier.pkl", "wb") as f:
        pickle.dump(pipeline, f)

    # --- save metrics ---
    artefact_flag = accuracy > ACCURACY_FLAG_THRESHOLD
    metrics = {
        "seed": SEED,
        "n_train": len(X_train),
        "n_test": len(X_test),
        "accuracy": accuracy,
        "artefact_risk_flag": artefact_flag,
        "artefact_risk_note": (
            f"Accuracy {accuracy:.4f} exceeds {ACCURACY_FLAG_THRESHOLD:.0%} on 9 classes "
            "with 400 rows. That's more consistent with the model keying on dataset "
            "artefacts (LeetCode's formulaic phrasing, or physics rows written by a "
            "single author) than on genuine concept separation."
            if artefact_flag else None
        ),
        "classification_report": report,
        "confusion_matrix": {"labels": list(classes), "matrix": cm.tolist()},
        "top_confused_pairs_directional": directional_pairs[:10],
        "top_confused_pairs_aggregated": aggregated_pairs[:10],
        "top_features_per_class": top_features,
    }
    with open(MODELS_DIR / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2, default=_json_default)

    # --- console report ---
    print(f"Train/test: {len(X_train)}/{len(X_test)} (seed={SEED})")
    print(f"Overall accuracy: {accuracy:.4f}")
    if artefact_flag:
        print(f"FLAG: {metrics['artefact_risk_note']}")

    print()
    print("Per-class precision / recall / F1:")
    for cls in classes:
        r = report[cls]
        print(f"  {cls:22s} P={r['precision']:.3f} R={r['recall']:.3f} "
              f"F1={r['f1-score']:.3f} (n={int(r['support'])})")

    print()
    print("Class pairs dominating confusion (aggregated, both directions):")
    if aggregated_pairs:
        for p in aggregated_pairs[:10]:
            print(f"  {p['pair'][0]:22s} <-> {p['pair'][1]:22s} {p['count']}")
    else:
        print("  (none — zero off-diagonal errors on the test set)")

    print()
    print(f"Top {TOP_N_FEATURES} features per class:")
    for cls in classes:
        feats = ", ".join(f"{f['feature']}({f['weight']:.2f})" for f in top_features[cls])
        print(f"  {cls}: {feats}")

    print()
    print(f"Saved pipeline             -> {MODELS_DIR / 'classifier.pkl'}")
    print(f"Saved metrics              -> {MODELS_DIR / 'metrics.json'}")
    print(f"Saved confusion matrix png -> {MODELS_DIR / 'confusion_matrix.png'}")


if __name__ == "__main__":
    main()
