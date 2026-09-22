import { useState } from 'react';
import { useQueries } from '@tanstack/react-query';
import { Link, useSearchParams } from 'react-router-dom';
import { api } from '@/api';
import { useRating } from '@/api/hooks';
import { queryKeys } from '@/api/hooks';
import type { RepoReport } from '@/api/types';
import { Badge, Card, EmptyState, Spinner } from '@/components/ui';
import { MiniBar, ScorePill } from '@/components/score/ScoreBits';
import { formatNumber, formatPercent, formatScore, timeAgo } from '@/lib/format';
import { CATEGORY_ORDER, CATEGORY_TITLE, STATUS_LABEL, scoreColor } from '@/lib/score';
import { useDebounced } from '@/lib/useDebounced';

const MAX = 4;

export function ComparePage() {
  const [params, setParams] = useSearchParams();
  const selected = (params.get('repos') ?? '').split(',').filter(Boolean).slice(0, MAX);
  const [term, setTerm] = useState('');
  const search = useDebounced(term, 300);
  const suggestions = useRating({ query: search || undefined, page: 1, page_size: 6, sort: 'score' });

  const reports = useQueries({
    queries: selected.map((path) => {
      const [owner, name] = path.split('/');
      return {
        queryKey: queryKeys.repo(owner, name),
        queryFn: () => api.getRepo(owner, name),
        staleTime: 60_000,
      };
    }),
  });

  const setSelected = (paths: string[]) => {
    const next = new URLSearchParams(params);
    if (paths.length) next.set('repos', paths.join(','));
    else next.delete('repos');
    setParams(next, { replace: true });
  };

  const add = (path: string) => {
    if (selected.includes(path) || selected.length >= MAX) return;
    setSelected([...selected, path]);
    setTerm('');
  };

  const loaded = reports
    .map((r) => r.data)
    .filter((r): r is RepoReport => Boolean(r));

  /** «Лучший» отмечаем только при единственном максимуме: ничья или нули — не победа. */
  const isBestIn = (key: string, score: number | null | undefined) => {
    if (score == null || score <= 0 || loaded.length < 2) return false;
    const scores = loaded
      .map((r) => r.categories.find((x) => x.key === key)?.score)
      .filter((v): v is number => v != null);
    const max = Math.max(...scores);
    return score === max && scores.filter((v) => v === max).length === 1;
  };

  return (
    <div className="stack" style={{ gap: 'var(--space-6)' }}>
      <header className="stack-sm">
        <h1>Сравнение проектов</h1>
        <p className="text-muted" style={{ maxWidth: 720 }}>
          До {MAX} репозиториев рядом: итоговый Score, категории и полнота данных. Полезно, когда
          выбираете открытый компонент для своего решения.
        </p>
      </header>

      <Card className="card--pad-sm">
        <div className="stack-sm">
          <div className="row-wrap">
            {selected.map((path) => (
              <span key={path} className="badge">
                {path}
                <button
                  type="button"
                  className="btn btn--ghost btn--sm"
                  style={{ padding: '0 4px' }}
                  onClick={() => setSelected(selected.filter((p) => p !== path))}
                  aria-label={`Убрать ${path}`}
                >
                  ✕
                </button>
              </span>
            ))}
            {selected.length < MAX ? (
              <input
                className="input"
                placeholder="Добавить репозиторий…"
                value={term}
                onChange={(e) => setTerm(e.target.value)}
                style={{ minWidth: 240 }}
              />
            ) : null}
          </div>

          {term ? (
            <div className="row-wrap">
              {suggestions.isFetching ? <Spinner /> : null}
              {(suggestions.data?.items ?? []).map((s) => (
                <button key={s.full_path} type="button" className="btn btn--sm" onClick={() => add(s.full_path)}>
                  {s.full_path} · {formatScore(s.total_score)}
                </button>
              ))}
            </div>
          ) : null}
        </div>
      </Card>

      {!selected.length ? (
        <EmptyState
          icon="⇆"
          title="Выберите репозитории"
          description="Начните вводить название в поле выше или перейдите сюда со страницы анализа кнопкой «Сравнить»."
          action={
            <Link className="btn" to="/">
              Открыть рейтинг
            </Link>
          }
        />
      ) : null}

      {reports.some((r) => r.isLoading) ? <Spinner label="Загружаем отчёты" /> : null}

      {loaded.length ? (
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>Показатель</th>
                {loaded.map((r) => (
                  <th key={r.full_path}>
                    <Link to={`/repo/${r.full_path}`}>{r.full_path}</Link>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>
                  <strong>Repo Health Score</strong>
                </td>
                {loaded.map((r) => (
                  <td key={r.full_path}>
                    <span className="row" style={{ gap: 8 }}>
                      <ScorePill score={r.score.total} />
                      <Badge tone="neutral">{r.score.grade}</Badge>
                    </span>
                  </td>
                ))}
              </tr>
              {CATEGORY_ORDER.map((key) => (
                <tr key={key}>
                  <td>{CATEGORY_TITLE[key]}</td>
                  {loaded.map((r) => {
                    const c = r.categories.find((x) => x.key === key);
                    const isBest = isBestIn(key, c?.score);
                    return (
                      <td key={r.full_path}>
                        {c?.score == null ? (
                          <Badge tone="nodata" title={c?.no_data_reason ?? undefined}>
                            {c ? STATUS_LABEL[c.status].toLowerCase() : 'нет данных'}
                          </Badge>
                        ) : (
                          <span className="row" style={{ gap: 8 }}>
                            <MiniBar score={c.score} />
                            <span style={{ color: scoreColor(c.score), fontWeight: 650 }}>
                              {formatScore(c.score)}
                            </span>
                            {isBest ? <Badge tone="good">лучший</Badge> : null}
                          </span>
                        )}
                      </td>
                    );
                  })}
                </tr>
              ))}
              <tr>
                <td>Полнота данных</td>
                {loaded.map((r) => (
                  <td key={r.full_path}>{formatPercent(r.score.coverage)}</td>
                ))}
              </tr>
              <tr>
                <td>Лайки</td>
                {loaded.map((r) => (
                  <td key={r.full_path}>{formatNumber(r.likes)}</td>
                ))}
              </tr>
              <tr>
                <td>Последняя активность</td>
                {loaded.map((r) => (
                  <td key={r.full_path}>{timeAgo(r.last_activity_at)}</td>
                ))}
              </tr>
              <tr>
                <td>Рекомендация №1</td>
                {loaded.map((r) => (
                  <td key={r.full_path} style={{ fontSize: 13 }}>
                    {r.recommendations[0]?.title ?? '—'}
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>
      ) : null}
    </div>
  );
}
