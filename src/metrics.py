"""Evaluation metrics with bootstrap confidence intervals.

With ~200 labelled examples a 3-point difference can be noise, so every headline
number gets a 95% CI and system comparisons use a *paired* bootstrap (same
resampled examples for both systems).
"""
import numpy as np
from sklearn.metrics import cohen_kappa_score, confusion_matrix, f1_score

from src.config import SEED

N_BOOT = 1000


def intent_accuracy(y_true, y_pred) -> float:
    return float(np.mean(np.asarray(y_true) == np.asarray(y_pred)))


def intent_macro_f1(y_true, y_pred, labels) -> float:
    present = sorted(set(y_true))  # classes absent from the gold set don't count
    return float(f1_score(y_true, y_pred, labels=[l for l in labels if l in present],
                          average="macro", zero_division=0))


def escalation_stats(y_true, y_pred) -> dict:
    t, p = np.asarray(y_true, bool), np.asarray(y_pred, bool)
    tp, fp, fn = int((t & p).sum()), int((~t & p).sum()), int((t & ~p).sum())
    return {
        "recall": tp / (tp + fn) if tp + fn else float("nan"),     # must-escalate caught
        "precision": tp / (tp + fp) if tp + fp else float("nan"),
        "automation_rate": float((~p).mean()),                      # share auto-handled
        "unsafe_auto_rate": fn / len(t),                            # should-escalate but auto-sent
        "needless_escalation_rate": fp / len(t),
    }


def bootstrap_ci(metric_fn, *arrays, n_boot=N_BOOT, seed=SEED):
    """metric_fn(*resampled_arrays) -> float. Returns (point, lo, hi)."""
    arrays = [np.asarray(a, dtype=object) for a in arrays]
    n = len(arrays[0])
    rng = np.random.default_rng(seed)
    point = metric_fn(*arrays)
    stats = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        v = metric_fn(*[a[idx] for a in arrays])
        if v == v:  # drop NaN (e.g. no positives in resample)
            stats.append(v)
    lo, hi = np.percentile(stats, [2.5, 97.5]) if stats else (float("nan"),) * 2
    return float(point), float(lo), float(hi)


def paired_bootstrap_diff(metric_fn, y_true, pred_a, pred_b, n_boot=N_BOOT, seed=SEED):
    """Difference metric(a) - metric(b) with 95% CI and P(a <= b)."""
    y, a, b = (np.asarray(x, dtype=object) for x in (y_true, pred_a, pred_b))
    rng = np.random.default_rng(seed)
    diffs = []
    for _ in range(n_boot):
        idx = rng.integers(0, len(y), len(y))
        d = metric_fn(y[idx], a[idx]) - metric_fn(y[idx], b[idx])
        if d == d:
            diffs.append(d)
    diffs = np.array(diffs)
    point = metric_fn(y, a) - metric_fn(y, b)
    return {"diff": float(point), "lo": float(np.percentile(diffs, 2.5)),
            "hi": float(np.percentile(diffs, 97.5)), "p_not_better": float((diffs <= 0).mean())}


def kappa(a, b) -> float:
    a, b = list(a), list(b)
    if len(set(a) | set(b)) < 2:
        return float("nan")
    return float(cohen_kappa_score(a, b))


def confusion(y_true, y_pred, labels):
    return confusion_matrix(y_true, y_pred, labels=labels).tolist()
