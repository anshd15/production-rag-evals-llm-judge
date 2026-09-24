from src.observability import METRICS, render_prometheus


def test_metrics_render_without_traffic():
    METRICS.clear()
    out = render_prometheus()
    assert "handoff_uptime_seconds" in out and "automation_rate" not in out


def test_derived_rates_appear_once_requests_are_served():
    METRICS.clear()
    METRICS.update({"requests": 4, "auto_handled": 3, "escalated": 1, "latency_ms_total": 800})
    out = render_prometheus()
    assert "handoff_automation_rate 0.750" in out
    assert "handoff_latency_ms_avg 200.0" in out
