export function StatusBadge({ verified, reviewStatus }) {
  if (reviewStatus === "verified" || verified) {
    return <span className="status-badge verified">VERIFIED</span>;
  }

  if (reviewStatus === "rejected") {
    return <span className="status-badge rejected">REJECTED</span>;
  }

  if (reviewStatus === "unconfirmed") {
    return <span className="status-badge unconfirmed">UNCONFIRMED</span>;
  }

  return <span className="status-badge pending">PENDING</span>;
}
