import { Navigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '@/auth/AuthProvider';
import { Card } from '@/components/ui';
import { IS_MOCK } from '@/api';

export function LoginPage() {
  const { login, status } = useAuth();
  const [params] = useSearchParams();
  const next = params.get('next') ?? '/dashboard';

  if (status === 'authenticated') return <Navigate to={next} replace />;

  return (
    <div style={{ display: 'grid', placeItems: 'center', minHeight: '55vh' }}>
      <Card style={{ maxWidth: 520 }}>
        <div className="stack">
          <h1>Вход через Я&nbsp;ID</h1>
          <p className="text-muted">
            Авторизация нужна, чтобы проанализировать собственный репозиторий: сервис обращается к
            SourceCraft от вашего имени и видит ровно то, что доступно вам. Данные закрытых
            репозиториев не попадают в публичный рейтинг.
          </p>

          <ul className="text-muted" style={{ margin: 0, paddingLeft: 18 }}>
            <li>получаем список доступных вам репозиториев;</li>
            <li>запускаем анализ выбранного репозитория;</li>
            <li>показываем Score, детализацию и рекомендации;</li>
            <li>отдаём отчёт в Markdown или PDF.</li>
          </ul>

          <button type="button" className="btn btn--primary btn--block" onClick={() => login(next)}>
            Войти через Я&nbsp;ID
          </button>

          {IS_MOCK ? (
            <p className="text-subtle">
              В демо-режиме настоящего редиректа в Я&nbsp;ID нет: вход эмулируется, пользователь и
              список репозиториев берутся из снимка данных. Путь пользователя полностью повторяет боевой.
            </p>
          ) : (
            <p className="text-subtle">
              Вы будете перенаправлены на страницу согласия Яндекс&nbsp;ID. Сервис не хранит ваш пароль,
              а исходный код не сохраняется дольше, чем нужно для анализа.
            </p>
          )}
        </div>
      </Card>
    </div>
  );
}
