from __future__ import annotations
import argparse
import json

from app.cloud.slowfast_service import get_slowfast_service


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True, help="Path tới clip video")
    parser.add_argument("--event_type_hint", default=None, help="using_phone | smoking | no_seatbelt")
    args = parser.parse_args()

    service = get_slowfast_service()
    result = service.verify_clip(
        video_path=args.video,
        event_type_hint=args.event_type_hint,
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

# python -m scripts.test_slowfast --video outputs/alerts/2026-04-10/using_phone_123.mp4 --event_type_hint using_phone