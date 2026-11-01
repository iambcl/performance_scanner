from argparse import Namespace
from pathlib import Path
import json

def compare_results(args: Namespace):
    results_dir = Path(__file__).resolve().parents[2] / "results"
    baseline_path = results_dir / "benchmark" / args.baseline
    current_path = results_dir / "readings" / args.current
    max_time_diff, max_memory_diff = args.max_time_regression, args.max_memory_regression
    with baseline_path.open(encoding="utf-8") as f:
        baseline = json.load(f)
    with current_path.open(encoding="utf-8") as f:
        current = json.load(f)
    wall_time_diff = (abs(baseline["wall_seconds"]-current["wall_seconds"]) / baseline["wall_seconds"])*100
    cpu_time_diff = (abs(baseline["cpu_seconds"]-current["cpu_seconds"]) / baseline["cpu_seconds"])*100
    memory_diff = (abs(baseline["peak_rss_bytes"]-current["peak_rss_bytes"]) / baseline["peak_rss_bytes"])*100
    results = {
        "wall_time_good": bool(wall_time_diff < max_time_diff),
        "cpu_time_good": bool(cpu_time_diff < max_time_diff),
        "memory_diff_good": bool(memory_diff < max_memory_diff)
    }
    print(json.dumps(results, indent=2))
    return results
