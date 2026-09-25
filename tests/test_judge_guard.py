from src.judge_agreement import MIN_RATINGS_FOR_KAPPA
from src.judge_robustness import analyse


def test_kappa_threshold_is_meaningful():
    # 2 ratings produced a kappa of 0.00 that read as a finding; the guard exists for that.
    assert MIN_RATINGS_FOR_KAPPA >= 30


def test_robustness_report_covers_every_judged_system():
    res = analyse("final", "golden")
    assert res["n"] == 200
    assert set(res["systems"]) >= {"agent", "simple", "trivial"}
    assert res["systems"]["agent"]["judged"] == 200
    for system, v in res["verbosity"].items():
        assert 0 <= v["would_send_short"] <= 1 and 0 <= v["would_send_long"] <= 1
