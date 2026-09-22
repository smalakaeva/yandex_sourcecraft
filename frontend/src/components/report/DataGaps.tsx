import type { RepoReport } from '@/api/types';
import { Badge, Banner } from '@/components/ui';
import { formatPercent } from '@/lib/format';
import { SOURCE_LABEL, STATUS_LABEL } from '@/lib/score';

/**
 * Отдельный блок «что именно не удалось собрать».
 * Отсутствие данных в сервисе — это статус, а не ноль баллов.
 */
export function DataGaps({ report }: { report: RepoReport }) {
  const gaps = report.categories.filter((c) => c.status === 'no_data' || c.status === 'not_applicable');
  const partial = report.categories.filter((c) => c.status === 'partial');
  const errors = report.collection.errors ?? [];

  return (
    <div className="stack">
      <Banner tone={gaps.length ? 'nodata' : 'info'} icon="ⓘ">
        Оценка посчитана по <strong>{formatPercent(report.score.coverage)}</strong> веса методики.{' '}
        {gaps.length
          ? 'Категории ниже исключены из расчёта: сервис не выдаёт за них ни баллов, ни штрафа.'
          : 'Данные собраны по всем шести категориям.'}
      </Banner>

      {gaps.length ? (
        <div className="stack-sm">
          {gaps.map((c) => (
            <div key={c.key} className="metric metric--nodata" style={{ alignItems: 'flex-start' }}>
              <span className="stack-sm" style={{ gap: 2 }}>
                <strong>{c.title}</strong>
                <span className="text-subtle">{c.no_data_reason}</span>
              </span>
              <Badge tone="nodata">{STATUS_LABEL[c.status]}</Badge>
            </div>
          ))}
        </div>
      ) : null}

      {partial.length ? (
        <div className="stack-sm">
          <span className="field__label">Собрано частично</span>
          {partial.map((c) => (
            <div key={c.key} className="metric">
              <span className="stack-sm" style={{ gap: 2 }}>
                <strong>{c.title}</strong>
                <span className="text-subtle">{c.no_data_reason ?? 'Часть сигналов недоступна.'}</span>
              </span>
              <Badge tone="warn">данных {formatPercent(c.signal_coverage)}</Badge>
            </div>
          ))}
        </div>
      ) : null}

      <div className="stack-sm">
        <span className="field__label">Источники данных</span>
        <div className="row-wrap" style={{ gap: 6 }}>
          {Object.entries(report.collection.sources_used ?? {}).map(([key, used]) => (
            <Badge key={key} tone={used ? 'good' : 'nodata'}>
              {SOURCE_LABEL[key] ?? key}: {used ? 'использован' : 'не использован'}
            </Badge>
          ))}
        </div>
      </div>

      {errors.length ? (
        <details>
          <summary className="text-muted" style={{ cursor: 'pointer' }}>
            Технические ошибки сбора ({errors.length})
          </summary>
          <div className="stack-sm" style={{ marginTop: 12 }}>
            {errors.map((e, i) => (
              <div key={i} className="metric metric--nodata" style={{ alignItems: 'flex-start' }}>
                <span className="stack-sm" style={{ gap: 2 }}>
                  <span className="row" style={{ gap: 6 }}>
                    <Badge tone="nodata">{e.category ?? '—'}</Badge>
                    <span className="mono">{e.code ?? '—'}</span>
                  </span>
                  <span className="text-subtle mono" style={{ wordBreak: 'break-word' }}>
                    {e.message}
                  </span>
                </span>
              </div>
            ))}
          </div>
        </details>
      ) : null}
    </div>
  );
}
