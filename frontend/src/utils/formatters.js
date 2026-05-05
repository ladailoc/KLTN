export function formatNumber(value) {
  return new Intl.NumberFormat("en-US").format(Number(value || 0));
}

export function formatConfidence(value) {
  return `${Math.round(Number(value || 0) * 100)}%`;
}
