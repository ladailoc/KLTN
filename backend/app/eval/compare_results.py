# so sánh 2 file benchmark/report
# ví dụ so edge_benchmark.json và hybrid_benchmark.json
from __future__ import annotations
import json
from pathlib import Path


EDGE_PATH = Path("outputs/benchmarks/edge_benchmark.json")
HYBRID_PATH = Path("outputs/benchmarks/hybrid_benchmark.json")


def load_json(path: Path):
    if not path.exists():
        print(f"[WARN] Không tìm thấy file: {path}")
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    edge = load_json(EDGE_PATH)
    hybrid = load_json(HYBRID_PATH)

    if edge is None and hybrid is None:
        print("Không có file benchmark nào để so sánh.")
        return

    print("===== SO SÁNH KẾT QUẢ =====")

    if edge:
        print("\n[EDGE]")
        print(json.dumps(edge, ensure_ascii=False, indent=2))

    if hybrid:
        print("\n[HYBRID]")
        print(json.dumps(hybrid, ensure_ascii=False, indent=2))

    print("\n===== TÓM TẮT =====")
    if edge and "avg_cpu_percent" in edge:
        print(f"CPU Edge trung bình: {edge['avg_cpu_percent']}%")
    if edge and "avg_mem_mb" in edge:
        print(f"RAM Edge trung bình: {edge['avg_mem_mb']} MB")
    if hybrid and "avg_latency_ms" in hybrid:
        print(f"Latency Cloud trung bình: {hybrid['avg_latency_ms']} ms")


if __name__ == "__main__":
    main()

# python -m app.eval.compare_results