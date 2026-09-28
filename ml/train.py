from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from ml.dataset import development_dataset
from ml.features import FEATURE_NAMES


def train(output: Path, report_path: Path) -> dict:
    x, y = development_dataset()
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.25, random_state=42, stratify=y)
    pipeline = Pipeline([
        ("scale", StandardScaler()),
        ("classifier", LogisticRegression(max_iter=1000, random_state=42)),
    ])
    pipeline.fit(x_train, y_train)
    predictions = pipeline.predict(x_test)
    report = {
        "warning": "Metrics use synthetic development data and are not evidence of production accuracy.",
        "feature_names": FEATURE_NAMES,
        "classification_report": classification_report(y_test, predictions, output_dict=True),
        "confusion_matrix": confusion_matrix(y_test, predictions, labels=list(pipeline.classes_)).tolist(),
        "classes": list(pipeline.classes_),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"version": "baseline-logreg-v1", "pipeline": pipeline, "features": FEATURE_NAMES}, output)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("ml/model/baseline.joblib"))
    parser.add_argument("--report", type=Path, default=Path("ml/model/evaluation.json"))
    args = parser.parse_args()
    print(json.dumps(train(args.output, args.report), indent=2))
