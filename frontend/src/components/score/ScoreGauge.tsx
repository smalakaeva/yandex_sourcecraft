import { formatPercent, formatScore } from '@/lib/format';
import { gradeLabel, scoreColor } from '@/lib/score';

/** Круговой индикатор итогового Repo Health Score. */
export function ScoreGauge({
  score,
  grade,
  coverage,
  size = 200,
}: {
  score: number | null;
  grade: string;
  coverage?: number;
  size?: number;
}) {
  const stroke = 14;
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const pct = score === null ? 0 : Math.max(0, Math.min(100, score)) / 100;
  const color = scoreColor(score);

  return (
    <div className="hero__score">
      <div style={{ position: 'relative', width: size, height: size }}>
        <svg width={size} height={size} role="img" aria-label={`Repo Health Score ${formatScore(score)} из 100`}>
          <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--surface-3)" strokeWidth={stroke} />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            fill="none"
            stroke={color}
            strokeWidth={stroke}
            strokeLinecap="round"
            strokeDasharray={`${c * pct} ${c}`}
            transform={`rotate(-90 ${size / 2} ${size / 2})`}
            style={{ transition: 'stroke-dasharray 600ms ease' }}
          />
        </svg>
        <div
          style={{
            position: 'absolute',
            inset: 0,
            display: 'grid',
            placeContent: 'center',
            textAlign: 'center',
          }}
        >
          <div className="gauge__value" style={{ color }}>
            {formatScore(score)}
            <span className="gauge__max"> / 100</span>
          </div>
          <div className="text-subtle">Repo Health Score</div>
        </div>
      </div>

      <div className="row-wrap" style={{ justifyContent: 'center' }}>
        <span className="badge badge--lg" style={{ background: 'var(--surface-3)', color }}>
          {grade} · {gradeLabel(grade)}
        </span>
      </div>
      {coverage !== undefined ? (
        <span className="text-subtle" style={{ textAlign: 'center' }}>
          Посчитан по {formatPercent(coverage)} веса методики
        </span>
      ) : null}
    </div>
  );
}
