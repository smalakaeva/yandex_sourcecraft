import { Component, type ErrorInfo, type ReactNode } from 'react';

interface Props {
  children: ReactNode;
}
interface State {
  error: Error | null;
}

/** Ошибка рендера не должна превращать демо в белый экран. */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    // В боевой версии здесь был бы вызов системы мониторинга.
    console.error('Ошибка интерфейса:', error, info.componentStack);
  }

  render() {
    if (!this.state.error) return this.props.children;
    return (
      <div className="container page">
        <div className="card stack">
          <h1>Что-то сломалось в интерфейсе</h1>
          <p className="text-muted">
            Данные отчёта могли прийти в неожиданном формате. Попробуйте обновить страницу — если
            ошибка повторяется, сообщите команде и приложите адрес страницы.
          </p>
          <pre className="mono" style={{ whiteSpace: 'pre-wrap', color: 'var(--text-subtle)' }}>
            {this.state.error.message}
          </pre>
          <div className="row">
            <button type="button" className="btn btn--primary" onClick={() => window.location.reload()}>
              Обновить страницу
            </button>
            <a className="btn" href="/">
              К рейтингу
            </a>
          </div>
        </div>
      </div>
    );
  }
}
