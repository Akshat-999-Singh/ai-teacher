"""Problem classifier experiments: TF-IDF vs sentence-embeddings, v1 vs v2 data.

Three runs, same seed, each an honest baseline (default hyperparameters,
no tuning, no alternative models beyond the two named here):

  1. v1_9class_tfidf      - data/problems_v1_9class.csv, TF-IDF + logreg
  2. v2_6class_tfidf       - data/problems.csv (v2),      TF-IDF + logreg
  3. v2_6class_embeddings  - data/problems.csv (v2),      all-MiniLM-L6-v2 + logreg

Run 1 is the documented starting point (56.25% on the label-ambiguous
9-class set). Runs 2 and 3 share the same v2 data and the same
train/test split, so the TF-IDF -> embeddings delta is isolated from
any dataset change.

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

from sentence_embedder import SentenceEmbedder

SEED = 42
MODELS_DIR = Path("models")
TOP_N_FEATURES = 10
ACCURACY_FLAG_THRESHOLD = 0.95
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

RUNS = [
    {"name": "v1_9class_tfidf", "data": "data/problems_v1_9class.csv", "featurizer": "tfidf"},
    {"name": "v2_6class_tfidf", "data": "data/problems.csv", "featurizer": "tfidf"},
    {"name": "v2_6class_embeddings", "data": "data/problems.csv", "featurizer": "embeddings"},
]


def _json_default(o):
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    raise TypeError(f"not JSON serializable: {type(o)}")


def make_pipeline(featurizer):
    if featurizer == "tfidf":
        return Pipeline([
            ("tfidf", TfidfVectorizer()),
            ("clf", LogisticRegression(max_iter=1000, random_state=SEED)),
        ])
    if featurizer == "embeddings":
        return Pipeline([
            ("embed", SentenceEmbedder(EMBEDDING_MODEL)),
            ("clf", LogisticRegression(max_iter=1000, random_state=SEED)),
        ])
    raise ValueError(featurizer)


def run_experiment(spec):
    df = pd.read_csv(spec["data"])
    X, y = df["text"], df["category"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=SEED
    )

    pipeline = make_pipeline(spec["featurizer"])
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    classes = pipeline.named_steps["clf"].classes_

    accuracy = float(accuracy_score(y_test, y_pred))
    report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
    macro_f1 = float(report["macro avg"]["f1-score"])
    cm = confusion_matrix(y_test, y_pred, labels=classes)

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
                aggregated_pairs.append({"pair": [classes[i], classes[j]], "count": total})
    aggregated_pairs.sort(key=lambda d: -d["count"])

    top_features = None
    if spec["featurizer"] == "tfidf":
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

    artefact_flag = accuracy > ACCURACY_FLAG_THRESHOLD
    n_classes = len(classes)
    result = {
        "name": spec["name"],
        "data_path": spec["data"],
        "featurizer": spec["featurizer"],
        "seed": SEED,
        "n_classes": n_classes,
        "n_train": len(X_train),
        "n_test": len(X_test),
        "accuracy": accuracy,
        "macro_f1": macro_f1,
        "artefact_risk_flag": artefact_flag,
        "artefact_risk_note": (
            f"Accuracy {accuracy:.4f} exceeds {ACCURACY_FLAG_THRESHOLD:.0%} on "
            f"{n_classes} classes with {len(X_train) + len(X_test)} rows. That's more "
            "consistent with the model keying on dataset artefacts than on genuine "
            "concept separation."
            if artefact_flag else None
        ),
        "classification_report": report,
        "confusion_matrix": {"labels": list(classes), "matrix": cm.tolist()},
        "top_confused_pairs_directional": directional_pairs[:10],
        "top_confused_pairs_aggregated": aggregated_pairs[:10],
        "top_features_per_class": top_features,
    }
    return result, pipeline


def save_confusion_matrix_png(result, path):
    classes = result["confusion_matrix"]["labels"]
    cm = np.array(result["confusion_matrix"]["matrix"])
    fig, ax = plt.subplots(figsize=(8, 7))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks(range(len(classes)))
    ax.set_yticks(range(len(classes)))
    ax.set_xticklabels(classes, rotation=45, ha="right")
    ax.set_yticklabels(classes)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title(f"Confusion matrix - {result['name']} (accuracy={result['accuracy']:.3f})")
    for i in range(len(classes)):
        for j in range(len(classes)):
            if cm[i, j]:
                ax.text(j, i, str(cm[i, j]), ha="center", va="center",
                         color="white" if cm[i, j] > cm.max() / 2 else "black")
    fig.colorbar(im, ax=ax)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main():
    MODELS_DIR.mkdir(exist_ok=True)

    results = {}
    pipelines = {}
    for spec in RUNS:
        print(f"=== {spec['name']} ({spec['featurizer']} on {spec['data']}) ===")
        result, pipeline = run_experiment(spec)
        results[spec["name"]] = result
        pipelines[spec["name"]] = pipeline
        print(f"  accuracy={result['accuracy']:.4f}  macro_f1={result['macro_f1']:.4f}  "
              f"n_train={result['n_train']} n_test={result['n_test']} n_classes={result['n_classes']}")
        if result["artefact_risk_flag"]:
            print(f"  FLAG: {result['artefact_risk_note']}")
        print()

    comparison = [
        {
            "run": r["name"],
            "data": r["data_path"],
            "n_classes": r["n_classes"],
            "featurizer": r["featurizer"],
            "accuracy": r["accuracy"],
            "macro_f1": r["macro_f1"],
        }
        for r in results.values()
    ]

    # v1 is a historical reference only: its 9 labels include categories retrieval
    # cannot serve, so it is never eligible to become the saved model.
    deployable = [s["name"] for s in RUNS if s["data"] == "data/problems.csv"]
    best_name = max(deployable, key=lambda k: (results[k]["macro_f1"], results[k]["accuracy"]))
    best = results[best_name]

    save_confusion_matrix_png(best, MODELS_DIR / "confusion_matrix.png")

    with open(MODELS_DIR / "classifier.pkl", "wb") as f:
        pickle.dump(pipelines[best_name], f)

    metrics = {
        "seed": SEED,
        "best_run": best_name,
        "runs": results,
        "comparison": comparison,
    }
    with open(MODELS_DIR / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2, default=_json_default)

    # --- console summary ---
    print("Comparison table:")
    header = f"  {'run':24s} {'classes':>7s} {'featurizer':>11s} {'accuracy':>9s} {'macro_f1':>9s}"
    print(header)
    for c in comparison:
        print(f"  {c['run']:24s} {c['n_classes']:7d} {c['featurizer']:>11s} "
              f"{c['accuracy']:9.4f} {c['macro_f1']:9.4f}")

    print()
    print(f"Best model: {best_name} (accuracy={best['accuracy']:.4f}, macro_f1={best['macro_f1']:.4f})")
    print(f"Confusion matrix saved for best model -> {MODELS_DIR / 'confusion_matrix.png'}")

    print()
    print(f"Class pairs still dominating confusion for {best_name}:")
    if best["top_confused_pairs_aggregated"]:
        for p in best["top_confused_pairs_aggregated"][:10]:
            print(f"  {p['pair'][0]:22s} <-> {p['pair'][1]:22s} {p['count']}")
    else:
        print("  (none - zero off-diagonal errors on the test set)")

    print()
    print(f"Saved pipeline (best model) -> {MODELS_DIR / 'classifier.pkl'}")
    print(f"Saved metrics (all 3 runs)  -> {MODELS_DIR / 'metrics.json'}")


if __name__ == "__main__":
    main()
