import type { ReactNode } from 'react';
import { useEffect, useRef, useState } from 'react';
import type { Tone } from '@/lib/score';

export function Card({
  children,
  className = '',
  ...rest
}: { children: ReactNode; className?: string } & React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={`card ${className}`} {...rest}>
      {children}
    </div>
  );
}

export function Badge({
  tone = 'nodata',
  children,
  large = false,
  title,
}: {
  tone?: Tone | 'accent' | 'info' | 'neutral';
  children: ReactNode;
  large?: boolean;
  title?: string;
}) {
  const cls = tone === 'neutral' ? '' : `badge--${tone}`;
  return (
    <span className={`badge ${cls} ${large ? 'badge--lg' : ''}`} title={title}>
      {children}
    </span>
  );
}

export function Spinner({ label }: { label?: string }) {
  return (
    <span className="row" role="status" aria-live="polite">
      <span className="spinner" />
      {label ? <span className="text-muted">{label}</span> : null}
    </span>
  );
}

export function EmptyState({
  title,
  description,
  action,
  icon = '◎',
}: {
  title: string;
  description?: ReactNode;
  action?: ReactNode;
  icon?: string;
}) {
  return (
    <div className="empty">
      <div style={{ fontSize: 28, opacity: 0.5 }} aria-hidden>
        {icon}
      </div>
      <h3>{title}</h3>
      {description ? <p className="text-muted" style={{ maxWidth: 460 }}>{description}</p> : null}
      {action}
    </div>
  );
}

export function Banner({
  tone = 'info',
  icon,
  children,
}: {
  tone?: 'info' | 'warn' | 'nodata';
  icon?: ReactNode;
  children: ReactNode;
}) {
  return (
    <div className={`banner ${tone === 'info' ? '' : `banner--${tone}`}`} role="note">
      {icon ? <span aria-hidden>{icon}</span> : null}
      <div>{children}</div>
    </div>
  );
}

export function Tooltip({ text }: { text: string }) {
  const [open, setOpen] = useState(false);
  return (
    <span
      className="tooltip-host"
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
      onFocus={() => setOpen(true)}
      onBlur={() => setOpen(false)}
    >
      <span className="tooltip-host__icon" tabIndex={0} role="button" aria-label={text}>
        ?
      </span>
      {open ? <span className="tooltip" role="tooltip">{text}</span> : null}
    </span>
  );
}

export function Progress({ value, label }: { value: number; label?: string }) {
  return (
    <div className="stack-sm">
      <div className="progress" role="progressbar" aria-valuenow={value} aria-valuemin={0} aria-valuemax={100}>
        <div className="progress__fill" style={{ width: `${Math.max(2, Math.min(100, value))}%` }} />
      </div>
      {label ? <span className="text-subtle">{label}</span> : null}
    </div>
  );
}

export function Skeleton({ height = 16, width = '100%' }: { height?: number | string; width?: number | string }) {
  return <div className="skeleton" style={{ height, width }} />;
}

export function Dropdown({
  trigger,
  children,
  align = 'right',
}: {
  trigger: (props: { open: boolean; toggle: () => void }) => ReactNode;
  children: (close: () => void) => ReactNode;
  align?: 'left' | 'right';
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false);
    };
    document.addEventListener('mousedown', onClick);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', onClick);
      document.removeEventListener('keydown', onKey);
    };
  }, [open]);

  return (
    <div className="dropdown" ref={ref}>
      {trigger({ open, toggle: () => setOpen((v) => !v) })}
      {open ? (
        <div className="dropdown__menu" style={align === 'left' ? { left: 0, right: 'auto' } : undefined}>
          {children(() => setOpen(false))}
        </div>
      ) : null}
    </div>
  );
}

export function Toast({ message }: { message: string | null }) {
  if (!message) return null;
  return (
    <div
      className="card card--pad-sm"
      role="status"
      style={{
        position: 'fixed',
        bottom: 24,
        left: '50%',
        transform: 'translateX(-50%)',
        zIndex: 50,
        boxShadow: 'var(--shadow-lg)',
      }}
    >
      {message}
    </div>
  );
}

/** Небольшой хук для одноразовых уведомлений («Скопировано», «Отчёт скачан»). */
export function useToast(): [string | null, (msg: string) => void] {
  const [message, setMessage] = useState<string | null>(null);
  const timer = useRef<number | null>(null);
  const show = (msg: string) => {
    setMessage(msg);
    if (timer.current) window.clearTimeout(timer.current);
    timer.current = window.setTimeout(() => setMessage(null), 2600);
  };
  useEffect(() => () => {
    if (timer.current) window.clearTimeout(timer.current);
  }, []);
  return [message, show];
}
