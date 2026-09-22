import { useState } from 'react';
import type { CategoryScore } from '@/api/types';
import { formatPercent, formatScore } from '@/lib/format';
import { CATEGORY_HINT, SOURCE_LABEL, STATUS_LABEL, scoreColor } from '@/lib/score';
import { Badge, Tooltip } from '@/components/ui';
import { MiniBar } from '@/components/score/ScoreBits';

export function CategoryCard({ category, defaultOpen = false }: { category: CategoryScore; defaultOpen?: boolean }) {
  const [open, setOpen] = useState(defaultOpen);
  const noData = category.score === null;

  return (
    <div className={`category-card ${noData ? 'category-card--nodata' : ''}`} aria-expanded={open}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="btn btn--ghost"
        style={{ padding: 0, justifyContent: 'flex-start', width: '100%', background: 'none', textAlign: 'left' }}
        aria-expanded={open}
      >
        <div className="stack-sm" style={{ width: '100%' }}>
          <div className="row" style={{ justifyContent: 'space-between' }}>
            <span className="row" style={{ gap: 6 }}>
              <strong>{category.title}</strong>
              <Tooltip text={CATEGORY_HINT[category.key]} />
            </span>
            <span className="row" style={{ gap: 8 }}>
              {noData ? (
                <Badge tone="nodata">{STATUS_LABEL[category.status]}</Badge>
              ) : (
                <>
                  <MiniBar score={category.score} />
                  <span style={{ color: scoreColor(category.score), fontWeight: 700 }}>
                    {formatScore(category.score)}
                  </span>
                </>
              )}
              <span className="text-subtle" aria-hidden>
                {open ? '▲' : '▼'}
              </span>
            </span>
          </div>

          <p className="text-muted" style={{ fontSize: 13.5 }}>
            {noData ? category.no_data_reason : category.summary.replace(/^\d+\/100:\s*/, '')}
          </p>

          <div className="row-wrap" style={{ gap: 6 }}>
            <span className="text-subtle">
              Вес {formatPercent(category.weight)}
              {noData ? ' → 0% (исключена)' : ` → ${formatPercent(category.effective_weight)} в этом расчёте`}
            </span>
            {category.status === 'partial' ? (
              <Badge tone="warn">
                данных по категории {formatPercent(category.signal_coverage)}
              </Badge>
            ) : null}
          </div>
        </div>
      </button>

      {open ? (
        <div className="stack-sm">
          {category.metrics.length ? (
            <div className="metric-list">
              {category.metrics.map((m) => (
                <div key={m.key} className={`metric ${m.status === 'no_data' ? 'metric--nodata' : ''}`}>
                  <span className="metric__label">
                    {m.label}
                    {m.hint ? (
                      <>
                        {' '}
                        <Tooltip text={m.hint} />
                      </>
                    ) : null}
                  </span>
                  <span className="metric__value" title={m.source ? `Источник: ${SOURCE_LABEL[m.source] ?? m.source}` : undefined}>
                    {m.display}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-subtle">Метрики недоступны: источник данных не ответил.</p>
          )}

          {category.strengths.length || category.weaknesses.length ? (
            <div className="grid-2">
              {category.strengths.length ? (
                <div className="stack-sm">
                  <span className="field__label">Сильные стороны</span>
                  <ul style={{ margin: 0, paddingLeft: 18 }}>
                    {category.strengths.map((s) => (
                      <li key={s} style={{ fontSize: 13.5 }}>{s}</li>
                    ))}
                  </ul>
                </div>
              ) : null}
              {category.weaknesses.length ? (
                <div className="stack-sm">
                  <span className="field__label">Требует внимания</span>
                  <ul style={{ margin: 0, paddingLeft: 18 }}>
                    {category.weaknesses.map((s) => (
                      <li key={s} style={{ fontSize: 13.5 }}>{s}</li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
