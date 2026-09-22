import type { HistoryPoint } from '@/api/types';
import { formatDate, formatScore } from '@/lib/format';

/** История изменения Score. Одна точка — показываем как «пока одна точка». */
export function Sparkline({ points, width = 420, height = 96 }: { points: HistoryPoint[]; width?: number; height?: number }) {
  const data = points.filter((p) => p.total !== null) as Required<HistoryPoint>[];
  if (data.length < 2) return null;

  const xs = data.map((_, i) => (i / (data.length - 1)) * (width - 24) + 12);
  const min = Math.min(...data.map((p) => p.total!)) - 5;
  const max = Math.max(...data.map((p) => p.total!)) + 5;
  const y = (v: number) => height - 16 - ((v - min) / Math.max(1, max - min)) * (height - 32);
  const path = data.map((p, i) => `${i === 0 ? 'M' : 'L'} ${xs[i]} ${y(p.total!)}`).join(' ');

  return (
    <svg className="sparkline" width={width} height={height} role="img" aria-label="Динамика Repo Health Score">
      <path d={path} fill="none" stroke="var(--info)" strokeWidth={2} strokeLinecap="round" />
      {data.map((p, i) => (
        <g key={p.analyzed_at}>
          <circle cx={xs[i]} cy={y(p.total!)} r={3.5} fill="var(--info)" />
          <title>{`${formatDate(p.analyzed_at)}: ${formatScore(p.total)}`}</title>
        </g>
      ))}
    </svg>
  );
}
