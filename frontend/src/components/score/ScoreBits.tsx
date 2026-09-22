import type { CategoryKey } from '@/api/types';
import { formatScore } from '@/lib/format';
import { CATEGORY_ORDER, CATEGORY_TITLE, scoreColor, scoreTone } from '@/lib/score';

/** Компактный балл с цветом «светофора». */
export function ScorePill({ score, showMax = true }: { score: number | null; showMax?: boolean }) {
  return (
    <span className="score-pill" style={{ color: scoreColor(score) }}>
      {formatScore(score)}
      {showMax ? <span className="score-pill__max">/100</span> : null}
    </span>
  );
}

export function MiniBar({ score }: { score: number | null }) {
  return (
    <div className="mini-bar" aria-hidden>
      <div
        className="mini-bar__fill"
        style={{ width: `${score === null ? 0 : Math.max(2, score)}%`, background: scoreColor(score) }}
      />
    </div>
  );
}

/** Шесть вертикальных полосок — «здоровье одним взглядом» в строке рейтинга. */
export function CategoryStrip({
  categories,
}: {
  categories: Partial<Record<CategoryKey, number | null>>;
}) {
  return (
    <div className="cat-strip">
      {CATEGORY_ORDER.map((key) => {
        const score = categories[key] ?? null;
        const title =
          score === null
            ? `${CATEGORY_TITLE[key]}: нет данных`
            : `${CATEGORY_TITLE[key]}: ${formatScore(score)}/100`;
        return (
          <span key={key} className="cat-strip__item" title={title}>
            {score === null ? (
              <span
                style={{
                  position: 'absolute',
                  inset: 0,
                  display: 'grid',
                  placeItems: 'center',
                  fontSize: 9,
                  color: 'var(--nodata)',
                }}
              >
                н/д
              </span>
            ) : (
              <span
                className="cat-strip__fill"
                style={{ height: `${Math.max(6, score)}%`, background: scoreColor(score) }}
              />
            )}
          </span>
        );
      })}
    </div>
  );
}

export function CoverageMeter({ coverage }: { coverage: number }) {
  const tone = coverage >= 0.85 ? 'good' : coverage >= 0.6 ? 'warn' : 'bad';
  const color = tone === 'good' ? 'var(--good)' : tone === 'warn' ? 'var(--warn)' : 'var(--bad)';
  return (
    <span className="row" style={{ gap: 6 }} title="Доля веса методики, покрытая фактическими данными">
      <span className="mini-bar" style={{ width: 52 }}>
        <span className="mini-bar__fill" style={{ display: 'block', width: `${coverage * 100}%`, background: color }} />
      </span>
      <span className="text-subtle nowrap">{Math.round(coverage * 100)}%</span>
    </span>
  );
}

export { scoreTone };
