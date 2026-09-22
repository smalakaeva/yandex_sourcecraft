import { useMemo, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import type { DataStatus, RatingQuery, SortKey } from '@/api/types';
import { useLanguages, useRating, useStats } from '@/api/hooks';
import { Badge, Banner, Card, EmptyState, Skeleton, Spinner } from '@/components/ui';
import { CategoryStrip, CoverageMeter, ScorePill } from '@/components/score/ScoreBits';
import { formatDateTime, formatNumber, formatScore, humanCron, timeAgo, truncate } from '@/lib/format';
import { CATEGORY_ORDER, CATEGORY_SHORT, CATEGORY_TITLE } from '@/lib/score';
import { useDebounced } from '@/lib/useDebounced';
import { ApiError } from '@/api';

const PAGE_SIZE = 25;

export function RatingPage() {
  const [params, setParams] = useSearchParams();
  const navigate = useNavigate();
  const [rawQuery, setRawQuery] = useState(params.get('q') ?? '');
  const search = useDebounced(rawQuery, 350);

  const page = Number(params.get('page') ?? 1);
  const sort = (params.get('sort') as SortKey) ?? 'score';
  const order = (params.get('order') as 'asc' | 'desc') ?? 'desc';
  const language = params.get('lang');
  const hasCi = params.get('ci');
  const security = params.get('security') as DataStatus | null;
  // По умолчанию в рейтинге показываем репозитории, у которых данными покрыта
  // хотя бы половина веса методики: иначе проект с одной заполненной категорией
  // соседствует в топе с проектом, проверенным по всем шести.
  const coverageParam = params.get('coverage') ?? '0.5';
  const minCoverage = Number(coverageParam);

  const query: RatingQuery = useMemo(
    () => ({
      query: search || undefined,
      language,
      sort,
      order,
      page,
      page_size: PAGE_SIZE,
      has_ci: hasCi === null ? null : hasCi === '1',
      security_status: security,
      min_coverage: minCoverage > 0 ? minCoverage : null,
    }),
    [search, language, sort, order, page, hasCi, security, minCoverage],
  );

  const rating = useRating(query);
  const languages = useLanguages();
  const stats = useStats();

  const update = (patch: Record<string, string | null>, resetPage = true) => {
    const next = new URLSearchParams(params);
    for (const [k, v] of Object.entries(patch)) {
      if (v === null || v === '') next.delete(k);
      else next.set(k, v);
    }
    if (resetPage) next.delete('page');
    setParams(next, { replace: true });
  };

  const toggleSort = (key: SortKey) => {
    if (sort === key) update({ order: order === 'desc' ? 'asc' : 'desc' }, false);
    else update({ sort: key, order: 'desc' });
  };

  const sortMark = (key: SortKey) => (sort === key ? (order === 'desc' ? ' ↓' : ' ↑') : '');
  const total = rating.data?.total ?? 0;
  const pages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div className="stack" style={{ gap: 'var(--space-6)' }}>
      <header className="stack-sm">
        <h1>Рейтинг здоровья открытых репозиториев</h1>
        <p className="text-muted" style={{ maxWidth: 780 }}>
          Repo Health Score от 0 до 100 по шести категориям: Security, состояние кода, активность,
          документация, CI/CD и issues. Рейтинг сортируется по здоровью проекта, а не по популярности:
          лайки показаны отдельной колонкой и в Score не входят.
        </p>
      </header>

      {stats.data ? (
        <Card className="card--pad-sm">
          <div className="row-wrap" style={{ gap: 'var(--space-6)' }}>
            <div className="kpi">
              <span className="kpi__value">{formatNumber(stats.data.repos_total)}</span>
              <span className="kpi__label">репозиториев в рейтинге</span>
            </div>
            <div className="kpi">
              <span className="kpi__value">{formatScore(stats.data.median_score)}</span>
              <span className="kpi__label">медианный Score</span>
            </div>
            <div className="kpi">
              <span className="kpi__value">{formatNumber(stats.data.with_ci)}</span>
              <span className="kpi__label">проектов с настроенным CI</span>
            </div>
            <div className="kpi">
              <span className="kpi__value">{formatNumber(stats.data.no_data_security)}</span>
              <span className="kpi__label">без данных AppSec</span>
            </div>
            <span className="spacer" />
            <div className="kpi">
              <span className="kpi__label">Последний пересчёт</span>
              <span>{formatDateTime(stats.data.last_run_at)}</span>
              <span className="kpi__label">
                пересчёт {humanCron(stats.data.schedule)}
              </span>
            </div>
          </div>
        </Card>
      ) : null}

      {/* ─────────────── фильтры ─────────────── */}
      <Card className="card--pad-sm">
        <div className="row-wrap" style={{ gap: 'var(--space-4)' }}>
          <div className="field" style={{ flex: '1 1 280px' }}>
            <label className="field__label" htmlFor="search">
              Поиск по названию и описанию
            </label>
            <input
              id="search"
              className="input"
              placeholder="например, datalens или cli"
              value={rawQuery}
              onChange={(e) => {
                setRawQuery(e.target.value);
                update({ q: e.target.value || null });
              }}
            />
          </div>

          <div className="field">
            <label className="field__label" htmlFor="lang">
              Язык
            </label>
            <select
              id="lang"
              className="select"
              value={language ?? ''}
              onChange={(e) => update({ lang: e.target.value || null })}
            >
              <option value="">Все языки</option>
              {(languages.data ?? []).map((l) => (
                <option key={l.language} value={l.language}>
                  {l.language} ({l.count})
                </option>
              ))}
            </select>
          </div>

          <div className="field">
            <label className="field__label" htmlFor="sort">
              Сортировка
            </label>
            <select
              id="sort"
              className="select"
              value={sort}
              onChange={(e) => update({ sort: e.target.value })}
            >
              <option value="score">По Repo Health Score</option>
              <option value="likes">По лайкам</option>
              <option value="activity">По последней активности</option>
              <option value="name">По названию</option>
            </select>
          </div>

          <div className="field">
            <label className="field__label" htmlFor="security">
              Данные Security
            </label>
            <select
              id="security"
              className="select"
              value={security ?? ''}
              onChange={(e) => update({ security: e.target.value || null })}
            >
              <option value="">Любые</option>
              <option value="ok">Есть данные AppSec</option>
              <option value="no_data">Нет данных AppSec</option>
            </select>
          </div>

          <div className="field">
            <label className="field__label" htmlFor="coverage">
              Полнота данных
            </label>
            <select
              id="coverage"
              className="select"
              value={coverageParam}
              onChange={(e) => update({ coverage: e.target.value })}
            >
              <option value="0.5">Не ниже 50%</option>
              <option value="0.8">Не ниже 80%</option>
              <option value="0">Любая</option>
            </select>
          </div>

          <label className="checkbox" style={{ marginTop: 18 }}>
            <input
              type="checkbox"
              checked={hasCi === '1'}
              onChange={(e) => update({ ci: e.target.checked ? '1' : null })}
            />
            Только с настроенным CI
          </label>

          {params.toString() ? (
            <button
              type="button"
              className="btn btn--ghost btn--sm"
              style={{ marginTop: 16 }}
              onClick={() => setParams(new URLSearchParams(), { replace: true })}
            >
              Сбросить
            </button>
          ) : null}
        </div>
      </Card>

      {/* ─────────────── таблица ─────────────── */}
      {rating.isError ? (
        <Banner tone="warn" icon="⚠">
          {rating.error instanceof ApiError ? rating.error.userMessage : 'Не удалось загрузить рейтинг.'}{' '}
          <button type="button" className="btn btn--sm" onClick={() => rating.refetch()}>
            Повторить
          </button>
        </Banner>
      ) : null}

      <div className="stack-sm">
        <div className="row-wrap" style={{ justifyContent: 'space-between' }}>
          <span className="stack-sm" style={{ gap: 2 }}>
            <span className="text-muted">
              {rating.isLoading ? 'Загрузка…' : `Найдено ${formatNumber(total)} репозиториев`}
            </span>
            {minCoverage > 0 ? (
              <span className="text-subtle">
                Показаны проекты, у которых данными покрыто не меньше {Math.round(minCoverage * 100)}%
                веса методики: оценки по разной полноте данных несопоставимы. Переключите фильтр
                «Полнота данных», чтобы увидеть остальные.
              </span>
            ) : null}
          </span>
          {rating.isFetching && !rating.isLoading ? <Spinner label="обновляем" /> : null}
        </div>

        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th className="rank">#</th>
                <th>Репозиторий</th>
                <th className="sortable" onClick={() => toggleSort('score')}>
                  Score{sortMark('score')}
                </th>
                <th title="Оценки по шести категориям, слева направо">Категории</th>
                <th title="Доля веса методики, покрытая данными">Полнота данных</th>
                <th className="sortable" onClick={() => toggleSort('likes')}>
                  Лайки{sortMark('likes')}
                </th>
                <th>Язык</th>
                <th className="sortable" onClick={() => toggleSort('activity')}>
                  Активность{sortMark('activity')}
                </th>
              </tr>
            </thead>
            <tbody>
              {rating.isLoading
                ? Array.from({ length: 10 }).map((_, i) => (
                    <tr key={i}>
                      <td colSpan={8}>
                        <Skeleton height={28} />
                      </td>
                    </tr>
                  ))
                : (rating.data?.items ?? []).map((repo, i) => (
                    <tr
                      key={repo.id ?? repo.full_path}
                      className="clickable"
                      onClick={() => navigate(`/repo/${repo.full_path}`)}
                    >
                      <td className="rank" title="Место в текущей выборке">
                        {(page - 1) * PAGE_SIZE + i + 1}
                        {repo.rank_delta ? (
                          <span
                            className="text-subtle"
                            style={{
                              marginLeft: 4,
                              color: repo.rank_delta > 0 ? 'var(--good)' : 'var(--bad)',
                            }}
                            title="Изменение места с прошлого пересчёта"
                          >
                            {repo.rank_delta > 0 ? '↑' : '↓'}
                            {Math.abs(repo.rank_delta)}
                          </span>
                        ) : null}
                      </td>
                      <td>
                        <div className="repo-cell">
                          <Link
                            to={`/repo/${repo.full_path}`}
                            className="repo-cell__path"
                            onClick={(e) => e.stopPropagation()}
                          >
                            {repo.full_path}
                          </Link>
                          {repo.description ? (
                            <span className="repo-cell__desc">{truncate(repo.description, 90)}</span>
                          ) : null}
                        </div>
                      </td>
                      <td>
                        <ScorePill score={repo.total_score} />
                      </td>
                      <td>
                        <CategoryStrip categories={repo.categories} />
                      </td>
                      <td>
                        <CoverageMeter coverage={repo.coverage} />
                      </td>
                      <td className="nowrap">{formatNumber(repo.likes)}</td>
                      <td className="nowrap">
                        {repo.primary_language ? (
                          <Badge tone="neutral">{repo.primary_language}</Badge>
                        ) : (
                          <span className="text-subtle">—</span>
                        )}
                      </td>
                      <td className="nowrap text-muted">{timeAgo(repo.last_activity_at)}</td>
                    </tr>
                  ))}
            </tbody>
          </table>
        </div>

        {!rating.isLoading && !total ? (
          <EmptyState
            title="Ничего не нашлось"
            description="Попробуйте изменить фильтры или очистить поиск."
            action={
              <button type="button" className="btn" onClick={() => setParams(new URLSearchParams())}>
                Сбросить фильтры
              </button>
            }
          />
        ) : null}

        <div className="pagination">
          <span className="text-subtle">
            Категории в колонке: {CATEGORY_ORDER.map((k) => `${CATEGORY_SHORT[k]} — ${CATEGORY_TITLE[k]}`).join(', ')}
          </span>
          <span className="row">
            <button
              type="button"
              className="btn btn--sm"
              disabled={page <= 1}
              onClick={() => update({ page: String(page - 1) }, false)}
            >
              ← Назад
            </button>
            <span className="text-muted nowrap">
              {page} / {pages}
            </span>
            <button
              type="button"
              className="btn btn--sm"
              disabled={page >= pages}
              onClick={() => update({ page: String(page + 1) }, false)}
            >
              Вперёд →
            </button>
          </span>
        </div>
      </div>
    </div>
  );
}
