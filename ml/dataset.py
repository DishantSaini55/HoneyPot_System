from __future__ import annotations

import random

from ml.features import FEATURE_NAMES


def development_dataset(samples_per_class: int = 250, seed: int = 42) -> tuple[list[list[float]], list[str]]:
    """Create labeled synthetic data for development only, never production claims."""
    rng = random.Random(seed)
    rows: list[list[float]] = []
    labels: list[str] = []

    def add(label: str, values: dict[str, tuple[float, float]]) -> None:
        for _ in range(samples_per_class):
            sample = {name: rng.uniform(*values.get(name, (0, 1))) for name in FEATURE_NAMES}
            rows.append([sample[name] for name in FEATURE_NAMES])
            labels.append(label)

    add("benign", {"session_duration_seconds": (1, 600), "request_rate": (0, 3)})
    add("brute_force", {"failed_login_count": (5, 40), "known_attack_pattern_count": (1, 8)})
    add("web_scanning", {"request_count": (8, 100), "unique_paths": (5, 40), "request_rate": (5, 80), "known_attack_pattern_count": (1, 12)})
    add("command_attack", {"command_count": (3, 30), "suspicious_command_count": (2, 15), "known_attack_pattern_count": (1, 12)})
    return rows, labels
