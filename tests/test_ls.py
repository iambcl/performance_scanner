import io
import json
import shutil
import tempfile
import unittest
from argparse import Namespace
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from src.record_parsing.results import record_action


@unittest.skipUnless(shutil.which("ls"), "ls is required for this integration test")
class LsRecordingTest(unittest.TestCase):
    def test_records_ls_metrics(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "results").mkdir()
            (root / "example.txt").write_text("example\n", encoding="utf-8")
            args = Namespace(name="ls", runs=3, command=[shutil.which("ls"), directory])

            # Keep the recorder's relative output path inside the temporary directory.
            with patch("src.record_parsing.results.Path", side_effect=lambda path: root / path):
                with redirect_stdout(io.StringIO()):
                    record_action(args)

            result = json.loads((root / "results" / "ls.json").read_text(encoding="utf-8"))
            self.assertEqual(
                set(result),
                {"wall_seconds", "cpu_seconds", "peak_rss_bytes", "exit_code"},
            )
            self.assertEqual(result["exit_code"], 0)
            self.assertGreater(result["wall_seconds"], 0)
            self.assertGreaterEqual(result["cpu_seconds"], 0)
            self.assertGreater(result["peak_rss_bytes"], 0)


if __name__ == "__main__":
    unittest.main()
