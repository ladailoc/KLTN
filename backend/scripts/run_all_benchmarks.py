"""
Script chạy benchmark 4 cấu hình để đo FPS cho Bảng 4.1.
Kết quả lưu vào outputs/benchmarks/ và in ra bảng tổng hợp.

Chạy trên máy tính cá nhân hoặc Jetson:
    cd backend
    python -m scripts.run_all_benchmarks

Lưu ý: Chạy lần lượt từng config để tránh ảnh hưởng lẫn nhau.
"""
from __future__ import annotations
import json
import subprocess
import sys
import time
from pathlib import Path

BENCH_CONFIGS = [
    {
        "name": "Config 1 (Cơ sở) - YOLO only, no skip",
        "config": "bench_configs/bench_config_1.yaml",
    },
    {
        "name": "Config 2 (Toàn tải) - YOLO+Pose, no skip",
        "config": "bench_configs/bench_config_2.yaml",
    },
    {
        "name": "Config 3 (Tối ưu chu kỳ) - YOLO+Pose, skip N=3",
        "config": "bench_configs/bench_config_3.yaml",
    },
    {
        "name": "Config 4 (Tối ưu toàn diện) - YOLO+Pose, skip N=3, resize 640",
        "config": "bench_configs/bench_config_4.yaml",
    },
]

BENCHMARK_DIR = Path("outputs/benchmarks")


def run_one_bench(config_path: str) -> dict | None:
    """Chạy pipeline với config cho trước, trả về benchmark result."""
    print(f"\n{'='*60}")
    print(f"Running: {config_path}")
    print(f"{'='*60}")

    cmd = [
        sys.executable,
        "-m",
        "app.edge.main_edge",
        "--config",
        config_path,
    ]

    start = time.time()
    result = subprocess.run(cmd, capture_output=False)
    elapsed = time.time() - start

    if result.returncode != 0:
        print(f"  [ERROR] Pipeline exited with code {result.returncode}")
        return None

    # Tìm file benchmark mới nhất
    bench_files = sorted(BENCHMARK_DIR.glob("edge_runtime_benchmark_*.json"), key=lambda f: f.stat().st_mtime)
    if not bench_files:
        print("  [ERROR] No benchmark file found")
        return None

    latest = bench_files[-1]
    with open(latest, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data


def main():
    print("=" * 60)
    print("BENCHMARK: Đo FPS cho 4 cấu hình (Bảng 4.1)")
    print("=" * 60)

    results = []

    for bench in BENCH_CONFIGS:
        data = run_one_bench(bench["config"])
        if data:
            effective_fps = round(data["total_frames"] / data["total_time_sec"], 2)
            results.append({
                "name": bench["name"],
                "config": bench["config"],
                "total_frames": data["total_frames"],
                "total_time_sec": data["total_time_sec"],
                "effective_fps": effective_fps,
                "resize_width": data.get("resize_width"),
                "pose_every": data.get("pose_every_n_frames"),
            })
            print(f"  -> FPS = {effective_fps} ({data['total_frames']} frames / {data['total_time_sec']}s)")
        else:
            results.append({
                "name": bench["name"],
                "config": bench["config"],
                "effective_fps": "ERROR",
            })

    # In bảng tổng hợp
    print("\n")
    print("=" * 70)
    print("KẾT QUẢ TỔNG HỢP - Điền vào Bảng 4.1")
    print("=" * 70)
    print(f"{'Kịch bản':<50} | {'FPS':>8}")
    print("-" * 70)
    for r in results:
        print(f"{r['name']:<50} | {str(r['effective_fps']):>8}")
    print("-" * 70)

    # Lưu kết quả
    output_path = BENCHMARK_DIR / "benchmark_summary.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nKết quả chi tiết đã lưu: {output_path}")


if __name__ == "__main__":
    main()
