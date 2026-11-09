import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class CliTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        shutil.copytree(ROOT / "src", self.root / "src", ignore=shutil.ignore_patterns("__pycache__"))
        (self.root / "results/benchmark").mkdir(parents=True)
        (self.root / "results/readings").mkdir()
        self.baseline = dict(wall_seconds=10, cpu_seconds=5, peak_rss_bytes=100, exit_code=0)
        self.current = self.baseline.copy()

    def cli(self, *args):
        return subprocess.run(
            [sys.executable, "-m", "src.main", *args], cwd=self.root,
            capture_output=True, text=True, timeout=30,
        )

    def compare(self, *options):
        for folder, result in (("benchmark", self.baseline), ("readings", self.current)):
            (self.root / "results" / folder / "test.json").write_text(json.dumps(result))
        return self.cli("compare", "--baseline", "test.json", "--current", "test.json", *options)

    def test_comparison_accepts_improvements_and_exact_threshold(self):
        for factor in (0.5, 1, 1.2):
            with self.subTest(factor=factor):
                for metric in ("wall_seconds", "cpu_seconds", "peak_rss_bytes"):
                    self.current[metric] = self.baseline[metric] * factor
                result = self.compare()
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue(all(json.loads(result.stdout).values()))

    def test_each_regression_fails(self):
        for metric in ("wall_seconds", "cpu_seconds", "peak_rss_bytes"):
            with self.subTest(metric=metric):
                self.current = self.baseline.copy()
                self.current[metric] *= 1.3
                result = self.compare()
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertIn(False, json.loads(result.stdout).values())

    def test_custom_thresholds(self):
        self.current.update(wall_seconds=13, cpu_seconds=6.5, peak_rss_bytes=140)
        self.assertEqual(self.compare("--max-time-regression", "30",
                                      "--max-memory-regression", "40").returncode, 0)

    def test_failed_recordings_are_rejected(self):
        for label in ("baseline", "current"):
            with self.subTest(label=label):
                self.baseline["exit_code"] = 0
                self.current["exit_code"] = 0
                getattr(self, label)["exit_code"] = 7
                result = self.compare()
                self.assertEqual(result.returncode, 1)
                self.assertIn(f"{label} recording", result.stderr)

    def test_invalid_metrics_are_rejected(self):
        for label, values in (("baseline", (0, -1, float("nan"), float("inf"), "10", None)),
                              ("current", (-1, float("nan"), float("inf"), "10", None))):
            for metric in ("wall_seconds", "cpu_seconds", "peak_rss_bytes"):
                for value in values:
                    with self.subTest(label=label, metric=metric, value=value):
                        self.baseline = dict(wall_seconds=10, cpu_seconds=5, peak_rss_bytes=100, exit_code=0)
                        self.current = self.baseline.copy()
                        getattr(self, label)[metric] = value
                        result = self.compare()
                        self.assertEqual(result.returncode, 1)
                        self.assertIn(f"{label} {metric}", result.stderr)

    def test_zero_current_metrics_are_valid(self):
        self.current.update(wall_seconds=0, cpu_seconds=0, peak_rss_bytes=0)
        self.assertEqual(self.compare().returncode, 0)

    def test_missing_and_invalid_json_fail(self):
        args = ("compare", "--baseline", "test.json", "--current", "test.json")
        self.assertEqual(self.cli(*args).returncode, 1)
        (self.root / "results/benchmark/test.json").write_text("invalid JSON")
        self.assertEqual(self.cli(*args).returncode, 1)

    def test_command_failure_is_saved_and_propagated(self):
        result = self.cli("record", "--name", "readings/failed", "--runs", "3",
                          sys.executable, "-c", "raise SystemExit(7)")
        self.assertEqual(result.returncode, 1, result.stderr)
        saved = json.loads((self.root / "results/readings/failed.json").read_text())
        self.assertEqual(saved["exit_code"], 7)

    def test_successful_recording(self):
        result = self.cli("record", "--name", "readings/success", "--runs", "1",
                          sys.executable, "-c", "print('ok')")
        self.assertEqual(result.returncode, 0, result.stderr)
        saved = json.loads((self.root / "results/readings/success.json").read_text())
        self.assertEqual(saved["exit_code"], 0)

    def test_missing_executable_fails(self):
        result = self.cli("record", "--name", "readings/missing", "--runs", "1",
                          "./nonexistent-command")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Error while recording", result.stderr)

    def test_invalid_arguments_exit_two(self):
        cases = [
            ("record",),
            ("record", "--name", "test", "--runs", "0", "ls"),
            ("record", "--name", "test", "--runs", "1"),
        ]
        for threshold in ("-1", "nan", "inf"):
            cases.append(("compare", "--baseline", "test.json", "--current", "test.json",
                          "--max-time-regression", threshold))
        for args in cases:
            with self.subTest(args=args):
                self.assertEqual(self.cli(*args).returncode, 2)


if __name__ == "__main__":
    unittest.main()
