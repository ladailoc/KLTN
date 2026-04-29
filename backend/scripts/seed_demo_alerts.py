from __future__ import annotations
import requests
from datetime import datetime, timedelta
import random


SERVER_URL = "http://127.0.0.1:8000"


def main():
    event_types = ["using_phone", "smoking", "no_seatbelt"]

    for i in range(10):
        payload = {
            "event_type": random.choice(event_types),
            "timestamp": (datetime.now() - timedelta(minutes=i)).isoformat(timespec="seconds"),
            "confidence": round(random.uniform(0.6, 0.95), 3),
            "frame_index": random.randint(100, 5000),
            "source_device": "seed-demo-edge",
            "notes": "demo seeded alert",
        }

        r = requests.post(f"{SERVER_URL}/alerts", data=payload, timeout=10)
        r.raise_for_status()
        print(f"[OK] Created alert {i+1}: {r.json()['event_type']}")

    print("Đã seed xong dữ liệu demo.")


if __name__ == "__main__":
    main()