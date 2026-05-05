import { getEventMeta } from "../../constants/events.jsx";

export function EventBadge({ eventType }) {
  const meta = getEventMeta(eventType);
  const Icon = meta.icon;

  return (
    <span className={`event-badge ${meta.className}`}>
      <Icon size={13} />
      {meta.label}
    </span>
  );
}
