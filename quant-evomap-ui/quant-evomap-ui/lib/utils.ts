export function getNodeColor(score: number): string {
  if (score > 1.0) return '#10b981'; // Green - passed
  if (score > 0.5) return '#6366f1'; // Purple - survived
  if (score < 0) return '#ef4444'; // Red - eliminated
  return '#f59e0b'; // Orange - new
}

export function getTrustTierColor(tier: number): string {
  if (tier >= 3) return '#ffd700'; // Gold
  if (tier >= 2) return '#c0c0c0'; // Silver
  return '#cd7f32'; // Bronze
}

export function formatNumber(value: number | undefined | null): string {
  if (value === undefined || value === null) return '-';
  return value.toFixed(2);
}

export function formatPercent(value: number | undefined | null): string {
  if (value === undefined || value === null) return '-';
  return `${Math.round(value * 100)}%`;
}

export function truncateId(id: string, length = 8): string {
  if (!id) return '';
  return id.length > length ? `${id.substring(0, length)}...` : id;
}
