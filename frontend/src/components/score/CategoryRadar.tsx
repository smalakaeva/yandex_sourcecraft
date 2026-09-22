import type { CategoryScore } from '@/api/types';
import { formatScore } from '@/lib/format';
import { CATEGORY_SHORT, scoreColor } from '@/lib/score';

/**
 * Радар по шести категориям. Категории без данных рисуются пунктирной засечкой
 * на внешнем круге — чтобы «нет данных» визуально не читалось как «ноль».
 */
export function CategoryRadar({ categories, size = 300 }: { categories: CategoryScore[]; size?: number }) {
  const cx = size / 2;
  const cy = size / 2;
  const radius = size / 2 - 42;
  const n = categories.length;

  const pointAt = (i: number, value: number) => {
    const angle = (Math.PI * 2 * i) / n - Math.PI / 2;
    const rr = radius * Math.max(0, Math.min(1, value));
    return [cx + rr * Math.cos(angle), cy + rr * Math.sin(angle)] as const;
  };

  const rings = [0.25, 0.5, 0.75, 1];
  const polygon = (value: (c: CategoryScore, i: number) => number) =>
    categories.map((c, i) => pointAt(i, value(c, i)).join(',')).join(' ');

  const withData = categories.map((c) => (c.score === null ? 0 : c.score / 100));
  const avg = withData.filter((v) => v > 0);
  const filler = avg.length ? avg.reduce((a, b) => a + b, 0) / avg.length : 0;

  return (
    <svg width={size} height={size} role="img" aria-label="Оценки по категориям">
      {rings.map((ring) => (
        <polygon
          key={ring}
          points={categories.map((_, i) => pointAt(i, ring).join(',')).join(' ')}
          fill="none"
          stroke="var(--border)"
          strokeWidth={1}
        />
      ))}
      {categories.map((_, i) => {
        const [x, y] = pointAt(i, 1);
        return <line key={i} x1={cx} y1={cy} x2={x} y2={y} stroke="var(--border)" strokeWidth={1} />;
      })}

      {/* область с данными */}
      <polygon
        points={polygon((c, i) => (c.score === null ? filler : withData[i]))}
        fill="color-mix(in srgb, var(--info) 20%, transparent)"
        stroke="var(--info)"
        strokeWidth={2}
        strokeDasharray={categories.some((c) => c.score === null) ? '6 4' : undefined}
      />

      {categories.map((c, i) => {
        const [x, y] = pointAt(i, c.score === null ? filler : withData[i]);
        const [lx, ly] = pointAt(i, 1.24);
        return (
          <g key={c.key}>
            <circle
              cx={x}
              cy={y}
              r={4}
              fill={c.score === null ? 'var(--surface)' : scoreColor(c.score)}
              stroke={c.score === null ? 'var(--nodata)' : 'var(--surface)'}
              strokeWidth={2}
              strokeDasharray={c.score === null ? '2 2' : undefined}
            />
            <text
              x={lx}
              y={ly - 4}
              textAnchor="middle"
              fontSize={11}
              fontWeight={600}
              fill="var(--text-muted)"
            >
              {CATEGORY_SHORT[c.key]}
            </text>
            <text
              x={lx}
              y={ly + 9}
              textAnchor="middle"
              fontSize={11}
              fill={c.score === null ? 'var(--nodata)' : scoreColor(c.score)}
              fontWeight={700}
            >
              {c.score === null ? 'н/д' : formatScore(c.score)}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
