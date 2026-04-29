from __future__ import annotations
import argparse

from app.common.config import reset_config_cache
from app.edge.pipeline_yolo_pose import EdgePipeline

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.yaml", help="Path to config file")
    parser.add_argument("--source", default=None, help="Video file path or webcam index")
    parser.add_argument("--send_to_cloud", action="store_true", help="Send alerts to cloud")
    args = parser.parse_args()

    reset_config_cache()
    pipeline = EdgePipeline(config_path=args.config)
    pipeline.run(source_override=args.source, send_to_cloud_override=args.send_to_cloud)

if __name__ == "__main__":
    main()