import { Link, useParams } from 'react-router-dom';
import { ApiError } from '@/api';
import { useRepoReport } from '@/api/hooks';
import { useAuth } from '@/auth/AuthProvider';
import { ReportView } from '@/components/report/ReportView';
import { ExportMenu } from '@/components/report/ExportMenu';
import { Banner, Card, EmptyState, Skeleton, Toast, useToast } from '@/components/ui';

export function RepoPage() {
  const { owner, name } = useParams<{ owner: string; name: string }>();
  const report = useRepoReport(owner, name);
  const { status, login } = useAuth();
  const [toast, showToast] = useToast();

  if (report.isLoading) {
    return (
      <div className="stack">
        <Skeleton height={40} width="55%" />
        <Card>
          <div className="hero">
            <Skeleton height={220} width={220} />
            <div className="stack-sm">
              <Skeleton height={20} />
              <Skeleton height={20} width="80%" />
              <Skeleton height={20} width="65%" />
            </div>
          </div>
        </Card>
        <div className="grid-2">
          <Skeleton height={180} />
          <Skeleton height={180} />
        </div>
      </div>
    );
  }

  if (report.isError || !report.data) {
    const err = report.error as ApiError | undefined;
    return (
      <EmptyState
        icon="⌀"
        title={err?.status === 404 ? 'Репозиторий ещё не анализировался' : 'Не удалось получить отчёт'}
        description={
          err?.status === 404 ? (
            <>
              В снимке рейтинга нет репозитория <span className="mono">{owner}/{name}</span>. Если это
              ваш репозиторий, войдите через Я ID и запустите анализ вручную.
            </>
          ) : (
            err?.userMessage ?? 'Сервис недоступен.'
          )
        }
        action={
          <span className="row">
            <Link to="/" className="btn">
              К рейтингу
            </Link>
            {status === 'authenticated' ? (
              <Link to="/dashboard" className="btn btn--primary">
                Мои репозитории
              </Link>
            ) : (
              <button type="button" className="btn btn--primary" onClick={() => login('/dashboard')}>
                Войти через Я ID
              </button>
            )}
          </span>
        }
      />
    );
  }

  const data = report.data;

  return (
    <>
      <div className="stack">
        <ReportView
          report={data}
          actions={
            <>
              <Link className="btn" to={`/compare?repos=${data.full_path}`}>
                Сравнить
              </Link>
              <ExportMenu report={data} onDone={showToast} />
            </>
          }
        />

        {status !== 'authenticated' ? (
          <Banner icon="→">
            Это ваш репозиторий?{' '}
            <button
              type="button"
              className="btn btn--sm btn--primary"
              style={{ marginLeft: 8 }}
              onClick={() => login(`/repo/${data.full_path}`)}
            >
              Войдите через Я ID
            </button>{' '}
            — сервис запросит данные от вашего имени и заполнит категории, которые сейчас закрыты
            правами доступа.
          </Banner>
        ) : null}
      </div>
      <Toast message={toast} />
    </>
  );
}
