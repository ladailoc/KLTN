import { AlertTriangle, Cigarette, Phone, Shield } from "lucide-react";

export const EVENT_META = {
  using_phone: {
    label: "Phone Use",
    apiLabel: "using_phone",
    icon: Phone,
    className: "event-phone",
    color: "#4f46e5",
  },
  smoking: {
    label: "Smoking",
    apiLabel: "smoking",
    icon: Cigarette,
    className: "event-smoking",
    color: "#e07800",
  },
  no_seatbelt: {
    label: "No Seatbelt",
    apiLabel: "no_seatbelt",
    icon: Shield,
    className: "event-seatbelt",
    color: "#c9181d",
  },
  unknown: {
    label: "Unknown",
    apiLabel: "unknown",
    icon: AlertTriangle,
    className: "event-unknown",
    color: "#bfc3cc",
  },
};

export function getEventMeta(eventType) {
  return EVENT_META[eventType] || EVENT_META.unknown;
}
