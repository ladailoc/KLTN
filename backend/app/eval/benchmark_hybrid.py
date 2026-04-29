from __future__ import annotations
import json
import time
import requests

from app.common.utils import ensure_dir

def benchmark_cloud_health(server_url: str = "http://127.0.0.1:8000", rounds: int = 20):
    ensure_dir("outputs/benchmarks")
    latencies = []

    for _ in range(rounds):
        t0 = time.time()
        r = requests.get(f"{server_url}/health", timeout=5)
        r.raise_for_status()
        latencies.append((time.time() - t0) * 1000)

    result = {
        "rounds": rounds,
        "avg_latency_ms": round(sum(latencies) / len(latencies), 2),
        "min_latency_ms": round(min(latencies), 2),
        "max_latency_ms": round(max(latencies), 2),
    }

    with open("outputs/benchmarks/hybrid_benchmark.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    benchmark_cloud_health()