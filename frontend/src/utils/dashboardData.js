import { EVENT_META } from "../constants/events.jsx";

export function getEventCount(stats, eventType) {
  return (
    (stats?.by_event_type || []).find((item) => item.event_type === eventType)
      ?.count || 0
  );
}

export function getTopDevice(stats) {
  const rows = stats?.by_device || [];
  if (!rows.length) return "-";

  return [...rows].sort(
    (a, b) => Number(b.count || 0) - Number(a.count || 0),
  )[0]?.source_device;
}

export function buildPieData(stats) {
  const phone = getEventCount(stats, "using_phone");
  const smoking = getEventCount(stats, "smoking");
  const seatbelt = getEventCount(stats, "no_seatbelt");
  const known = phone + smoking + seatbelt;
  const total = stats?.total_alerts || known;
  const other = Math.max(0, total - known);

  return [
    { name: "using_phone", value: phone, color: EVENT_META.using_phone.color },
    { name: "smoking", value: smoking, color: EVENT_META.smoking.color },
    {
      name: "no_seatbelt",
      value: seatbelt,
      color: EVENT_META.no_seatbelt.color,
    },
    { name: "other", value: other, color: EVENT_META.unknown.color },
  ].filter((item) => item.value > 0);
}

export function buildDeviceData(stats) {
  return (stats?.by_device || []).map((item) => ({
    name: item.source_device || "unknown",
    alerts: item.count || 0,
  }));
}

export function buildTrendData(alerts) {
  const buckets = [];
  const now = new Date();

  for (let i = 7; i >= 0; i--) {
    const hour = new Date(now.getTime() - i * 3 * 60 * 60 * 1000);
    const label = `${String(hour.getHours()).padStart(2, "0")}:00`;
    buckets.push({ time: label, alerts: 0, start: i });
  }

  if (!alerts?.length) return buckets;

  for (const alert of alerts) {
    if (!alert.timestamp) continue;
    const ts = new Date(alert.timestamp);
    const diffMs = now.getTime() - ts.getTime();
    const diffHours = diffMs / (1000 * 60 * 60);

    if (diffHours < 0 || diffHours >= 24) continue;

    const bucketIndex = 7 - Math.floor(diffHours / 3);
    if (bucketIndex >= 0 && bucketIndex < 8) {
      buckets[bucketIndex].alerts++;
    }
  }

  return buckets.map(({ time, alerts }) => ({ time, alerts }));
}
