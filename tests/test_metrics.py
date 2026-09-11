import math

from src.metrics import (bootstrap_ci, escalation_stats, intent_accuracy, intent_macro_f1, kappa,
                         paired_bootstrap_diff)


def test_escalation_stats():
    s = escalation_stats([True, True, False, False], [True, False, True, False])
    assert s["recall"] == 0.5 and s["precision"] == 0.5
    assert s["automation_rate"] == 0.5
    assert s["unsafe_auto_rate"] == 0.25 and s["needless_escalation_rate"] == 0.25


def test_escalation_stats_no_positives_is_nan():
    assert math.isnan(escalation_stats([False, False], [False, True])["recall"])


def test_macro_f1_ignores_classes_absent_from_gold():
    assert intent_macro_f1(["a", "a", "b"], ["a", "a", "b"], ["a", "b", "c"]) == 1.0


def test_bootstrap_ci_brackets_point():
    y = ["a"] * 70 + ["b"] * 30
    p = ["a"] * 60 + ["b"] * 40
    point, lo, hi = bootstrap_ci(intent_accuracy, y, p, n_boot=300)
    assert lo <= point <= hi and 0.8 <= point <= 1.0


def test_paired_diff_detects_clear_win():
    y = ["a"] * 100
    res = paired_bootstrap_diff(intent_accuracy, y, ["a"] * 90 + ["b"] * 10, ["a"] * 50 + ["b"] * 50,
                                n_boot=300)
    assert res["diff"] > 0.3 and res["lo"] > 0 and res["p_not_better"] == 0


def test_kappa():
    assert kappa([1, 0, 1, 0], [1, 0, 1, 0]) == 1.0
    assert math.isnan(kappa([1, 1], [1, 1]))
