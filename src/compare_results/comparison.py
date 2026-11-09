from argparse import Namespace
from pathlib import Path
import json
import math

METRICS = ("wall_seconds", "cpu_seconds", "peak_rss_bytes")

def _validate_result(result, label, *, baseline=False):
    if result.get("exit_code") != 0:
        raise ValueError(f"{label} recording must have exit_code 0")
    for metric in METRICS:
        value = result.get(metric)
        if (isinstance(value, bool) or not isinstance(value, (int, float))
                or not math.isfinite(value) or value < 0
                or (baseline and value == 0)):
            requirement = "positive" if baseline else "nonnegative"
            raise ValueError(f"{label} {metric} must be finite and {requirement}")

def compare_results(args: Namespace):
    results_dir = Path(__file__).resolve().parents[2] / "results"
    baseline_path = results_dir / "benchmark" / args.baseline
    current_path = results_dir / "readings" / args.current
    max_time_diff, max_memory_diff = args.max_time_regression, args.max_memory_regression
    for threshold in (max_time_diff, max_memory_diff):
        if not math.isfinite(threshold) or threshold < 0:
            raise ValueError("thresholds must be finite and nonnegative")
    with baseline_path.open(encoding="utf-8") as f:
        baseline = json.load(f)
    with current_path.open(encoding="utf-8") as f:
        current = json.load(f)
    _validate_result(baseline, "baseline", baseline=True)
    _validate_result(current, "current")
    differences = {
        metric: (current[metric] - baseline[metric]) / baseline[metric] * 100
        for metric in METRICS
    }
    results = {
        "wall_time_good": differences["wall_seconds"] <= max_time_diff,
        "cpu_time_good": differences["cpu_seconds"] <= max_time_diff,
        "memory_diff_good": differences["peak_rss_bytes"] <= max_memory_diff
    }
    print(json.dumps(results, indent=2))
    return results
