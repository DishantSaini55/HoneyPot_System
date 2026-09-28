from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
from sklearn.metrics import classification_report, confusion_matrix

from ml.dataset import development_dataset


def evaluate(model_path: Path) -> dict:
    artifact = joblib.load(model_path)
    x, y = development_dataset(seed=84)
    predictions = artifact["pipeline"].predict(x)
    classes = list(artifact["pipeline"].classes_)
    return {
        "warning": "Metrics use synthetic development data and are not evidence of production accuracy.",
        "classification_report": classification_report(y, predictions, output_dict=True),
        "confusion_matrix": confusion_matrix(y, predictions, labels=classes).tolist(),
        "classes": classes,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("model", type=Path)
    args = parser.parse_args()
    print(json.dumps(evaluate(args.model), indent=2))
