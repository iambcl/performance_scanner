import json
import os
import time
import subprocess
import sys
from dataclasses import asdict, dataclass
from argparse import Namespace
from pathlib import Path

PROCESS_SUCCESS = 0

@dataclass
class Results:
    wall_seconds: int
    cpu_seconds: int
    peak_rss_bytes: int
    exit_code: int

def record_action(args: Namespace):
    record_name, record_runs = args.name, args.runs
    if record_runs < 1:
        raise ValueError("runs must be at least 1")
    commands = args.command
    result_record = []
    for _ in range(record_runs):
        results = measure(commands)
        if results.exit_code != PROCESS_SUCCESS:
            result_record = [results]
            break
        result_record.append(results)

    max_results = Results(
        wall_seconds=max(result.wall_seconds for result in result_record),
        cpu_seconds=max(result.cpu_seconds for result in result_record),
        peak_rss_bytes=max(result.peak_rss_bytes for result in result_record),
        exit_code=max(result.exit_code for result in result_record),
    )

    output_path = Path(f"{record_name}.json")
    output_path.write_text(
        json.dumps(asdict(max_results), indent=2) + "\n",
        encoding="utf-8",
    )
    print("Saved max readings at {output_path}.")
    print(json.dumps(asdict(max_results), indent=2))
    return 


def measure(command: list[str]):
    time_started = time.perf_counter()
    process = subprocess.Popen(command,
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL,)
    _, status, usage = os.wait4(process.pid,0)
    time_ended = time.perf_counter()
    return_code = os.waitstatus_to_exitcode(status)
    peak_rss_bytes = usage.ru_maxrss

    if sys.platform.startswith("linux"):
        peak_rss_bytes *= 1024

    return Results(
        wall_seconds=time_ended - time_started,
        cpu_seconds=usage.ru_utime + usage.ru_stime,
        peak_rss_bytes=peak_rss_bytes,
        exit_code=return_code
    )
