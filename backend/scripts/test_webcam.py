from __future__ import annotations
import argparse
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--camera", default="0", help="Index webcam, ví dụ 0 hoặc 1")
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
        str(args.camera),
    ]

    if args.send_to_cloud:
        cmd.append("--send_to_cloud")

    print("Running:", " ".join(cmd))
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()

# python -m scripts.test_webcam --camera 0
# python -m scripts.test_webcam --camera 1
# python -m scripts.test_webcam --camera 0 --send_to_cloud