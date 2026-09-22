import { Link } from 'react-router-dom';
import { EmptyState } from '@/components/ui';

export function NotFoundPage() {
  return (
    <EmptyState
      icon="404"
      title="Страница не найдена"
      description="Возможно, ссылка устарела или репозиторий был переименован."
      action={
        <Link className="btn btn--primary" to="/">
          Вернуться к рейтингу
        </Link>
      }
    />
  );
}
