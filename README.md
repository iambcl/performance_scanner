# Performance Scanner

A small Python command-line tool for measuring a program's execution time and peak memory usage, then comparing saved readings against a baseline.

## Requirements

- Python 3.9 or newer.
- macOS or Linux. Recording uses `os.wait4`, which is unavailable on Windows.
- No third-party Python packages are required.

Run the commands below from the repository root. The CLI is invoked as a module so its `src` imports resolve correctly.

## Quick start

Optionally create and activate a virtual environment:

```sh
python3 -m venv .venv
source .venv/bin/activate
```

Create the output directories if needed, then record a baseline and a current reading:

```sh
mkdir -p results/benchmark results/readings

python3 -m src.main record --name benchmark/ls --runs 5 ls -la

# Run again after making the change you want to measure.
python3 -m src.main record --name readings/ls --runs 5 ls -la

python3 -m src.main compare --baseline ls.json --current ls.json
```

Use the same command, inputs, and environment for both recordings to make the comparison useful. Very short commands such as `ls` can produce noisy timing results.

## Record a command

```sh
python3 -m src.main record --name readings/my-program --runs 10 python3 path/to/program.py
```

Place scanner options before the command being measured. Everything from the command onward is passed to the program as arguments. Commands run directly without a shell; use an explicit shell command if you need pipes or redirection.

| Argument | Description |
| --- | --- |
| `--name` | Output name relative to `results/`, without the `.json` extension. Use `benchmark/name` or `readings/name` for files intended for comparison. |
| `--runs` | Number of executions; must be at least `1`. |
| `command ...` | Executable and its arguments. |

Supply both `--name` and `--runs`. The recorder writes `results/<name>.json` relative to the working directory, overwriting an existing file with that name. Parent directories must already exist.

For successful runs, the saved result contains the maximum of each metric across all runs. These maxima can come from different executions. The measured program's standard output and standard error are suppressed.

If a run exits with a nonzero status, recording stops and saves only that failed run's metrics, discarding any earlier successful readings.

### Result format

```json
{
  "wall_seconds": 0.012,
  "cpu_seconds": 0.008,
  "peak_rss_bytes": 1572864,
  "exit_code": 0
}
```

- `wall_seconds`: elapsed time from process launch through completion.
- `cpu_seconds`: user CPU time plus system CPU time reported for the process.
- `peak_rss_bytes`: peak resident memory usage in bytes, normalized from the platform's reported units on macOS and Linux.
- `exit_code`: the program's exit status; `0` indicates success.

## Compare results

```sh
python3 -m src.main compare \
  --baseline my-program.json \
  --current my-program.json \
  --max-time-regression 20 \
  --max-memory-regression 20
```

The comparison reads the baseline from `results/benchmark/` and the current result from `results/readings/`, both relative to the repository location. Pass filenames only, including `.json`, rather than paths.

Both thresholds default to `20` percent. The time threshold applies separately to wall time and CPU time; the memory threshold applies to peak RSS.

Example output:

```json
{
  "wall_time_good": true,
  "cpu_time_good": false,
  "memory_diff_good": true
}
```

### Comparison behavior and exit codes

The percentage difference for each metric is calculated as:

```text
(current - baseline) / baseline * 100
```

Improvements pass. A metric passes when its increase is at most the configured threshold, including a difference exactly at the threshold. Thresholds must be finite and nonnegative.

Both recordings must have `exit_code: 0`. Baseline metrics must be finite and positive to avoid division by zero; current metrics must be finite and nonnegative. Invalid recordings fail with a diagnostic on standard error.

The CLI exits with `0` on success, `1` on a regression, failed measured command, or recording/comparison error, and `2` for invalid CLI arguments. A failed measured command's JSON is saved before the scanner exits with `1`; its original status remains in the JSON.

## GitHub Actions

`.github/workflows/performance.yaml` runs tests and compares scanner performance on pushes, pull requests, and manual runs. Pull requests use the target branch's base SHA as the baseline; pushes use the pre-push SHA. Manual runs and new branches fall back to the preceding commit, or the current commit when there is no parent.

The baseline and current source are checked out separately and measured in the same Ubuntu 24.04 job with Python 3.12. `benchmarks/record_workload.py` runs an identical workload against each revision: recording five executions of a fixed Python computation in a temporary directory. The current scanner measures that whole workload five times per revision, then compares the maximum wall time, CPU time, and peak RSS with inclusive 20% limits. This measures end-to-end recording performance, including the child program's cost; it is a synthetic benchmark of this scanner.

Both JSON recordings are uploaded as the `performance-results` artifact even when comparison fails. Shared runners can still introduce measurement noise. For another application, replace the workload with representative commands and inputs.

Commit and push the workflow and benchmark script to run CI. To require a passing result before merging, configure the `performance` job as a required status check in your repository's branch rules.

## Tests

```sh
python3 -m unittest discover -s tests -v
```

Tests cover CLI exit statuses, failed commands, regression limits, improvements, and invalid results. The recording integration test also runs `ls` three times and checks the saved metrics; it skips if `ls` is unavailable.

## Project layout

```text
src/
  main.py                      CLI arguments and command dispatch
  record_parsing/results.py    Process measurement and JSON recording
  compare_results/comparison.py Baseline comparison
results/
  benchmark/                   Baseline JSON files
  readings/                    Current JSON files
tests/
  test_ci.py                   CI behavior and CLI exit-status tests
  test_ls.py                   Recording integration test
benchmarks/
  record_workload.py           Fixed workload for comparing scanner revisions
```

For command help:

```sh
python3 -m src.main --help
python3 -m src.main record --help
python3 -m src.main compare --help
```
