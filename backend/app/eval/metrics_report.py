from __future__ import annotations
import json
from collections import Counter, defaultdict
from pathlib import Path

from app.common.utils import ensure_dir


ALERTS_DIR = Path("outputs/alerts")
OUTPUT_PATH = Path("outputs/benchmarks/metrics_report.json")


def load_alert_json_files(alerts_dir: Path):
    if not alerts_dir.exists():
        return []

    files = list(alerts_dir.rglob("*.json"))
    rows = []
    for f in files:
        try:
            with open(f, "r", encoding="utf-8") as fh:
                rows.append(json.load(fh))
        except Exception as e:
            print(f"[WARN] Không đọc được {f}: {e}")
    return rows


def build_report(rows: list[dict]) -> dict:
    total_alerts = len(rows)
    by_event = Counter()
    by_device = Counter()
    by_date = Counter()

    confidence_stats = defaultdict(list)

    for row in rows:
        event_type = row.get("event_type", "unknown")
        source_device = row.get("source_device", "unknown")
        timestamp = row.get("timestamp", "unknown")

        by_event[event_type] += 1
        by_device[source_device] += 1

        if isinstance(timestamp, str) and len(timestamp) >= 10:
            by_date[timestamp[:10]] += 1

        conf = row.get("confidence", None)
        if isinstance(conf, (int, float)):
            confidence_stats[event_type].append(float(conf))

    confidence_summary = {}
    for event_type, values in confidence_stats.items():
        if values:
            confidence_summary[event_type] = {
                "count": len(values),
                "min": round(min(values), 4),
                "max": round(max(values), 4),
                "avg": round(sum(values) / len(values), 4),
            }

    report = {
        "total_alerts": total_alerts,
        "alerts_by_event": dict(by_event),
        "alerts_by_device": dict(by_device),
        "alerts_by_date": dict(by_date),
        "confidence_summary": confidence_summary,
    }
    return report


def main():
    ensure_dir(OUTPUT_PATH.parent)
    rows = load_alert_json_files(ALERTS_DIR)
    report = build_report(rows)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"\nĐã lưu báo cáo tại: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()


    # python -m app.eval.metrics_report