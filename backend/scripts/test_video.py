from __future__ import annotations
import argparse
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", default="data/sample_videos/test.mp4")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--send_to_cloud", action="store_true")
    args = parser.parse_args()

    cmd = [
        sys.executable,
        "-m",
        "app.edge.main_edge",
        "--config",
        args.config,
        "--source",
        args.video,
    ]

    if args.send_to_cloud:
        cmd.append("--send_to_cloud")

    print("Running:", " ".join(cmd))
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()

# python -m scripts.test_video --video data/sample_videos/test.mp4
# python -m scripts.test_video --video data/sample_videos/test.mp4 --send_to_cloud