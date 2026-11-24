/** Number formatting for the dashboard. */

export function watts(value: number | null | undefined): string {
  if (value === null || value === undefined) return "–";
  return `${value.toFixed(value >= 10 ? 1 : 2)} W`;
}

export function rate(kbps: number): string {
  if (!kbps) return "–";
  return kbps >= 1000 ? `${(kbps / 1000).toFixed(1)} Mbit/s` : `${kbps} kbit/s`;
}

export function speed(mbps: number): string {
  return mbps ? `${mbps} Mbit/s` : "–";
}
