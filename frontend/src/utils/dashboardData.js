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
  const fallback = [
    { time: "00:00", alerts: 2 },
    { time: "03:00", alerts: 3 },
    { time: "06:00", alerts: 6 },
    { time: "09:00", alerts: 4 },
    { time: "12:00", alerts: 2 },
    { time: "15:00", alerts: 3 },
    { time: "18:00", alerts: 5 },
    { time: "21:00", alerts: 2 },
  ];

  if (!alerts?.length) return fallback;

  return fallback.map((item, index) => ({
    ...item,
    alerts: Math.max(1, Math.round(alerts.length / 3) + (index % 3)),
  }));
}
