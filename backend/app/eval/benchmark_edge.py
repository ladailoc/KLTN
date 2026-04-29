from __future__ import annotations
import json
import time
import psutil

from app.common.utils import ensure_dir

def run_simple_edge_benchmark(seconds: int = 30, output_path: str = "outputs/benchmarks/edge_benchmark.json"):
    ensure_dir("outputs/benchmarks")
    process = psutil.Process()

    samples = []
    start = time.time()
    while time.time() - start < seconds:
        cpu_percent = psutil.cpu_percent(interval=1.0)
        mem_mb = process.memory_info().rss / (1024 * 1024)
        samples.append({"cpu_percent": cpu_percent, "mem_mb": round(mem_mb, 2)})

    avg_cpu = sum(s["cpu_percent"] for s in samples) / len(samples)
    avg_mem = sum(s["mem_mb"] for s in samples) / len(samples)

    result = {
        "duration_sec": seconds,
        "avg_cpu_percent": round(avg_cpu, 2),
        "avg_mem_mb": round(avg_mem, 2),
        "samples": samples,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    run_simple_edge_benchmark()