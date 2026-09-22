const NBSP = ' ';

export function formatNumber(value: number | null | undefined, fallback = '—'): string {
  if (value === null || value === undefined || Number.isNaN(value)) return fallback;
  return new Intl.NumberFormat('ru-RU').format(value).replace(/\s/g, NBSP);
}

export function formatScore(value: number | null | undefined): string {
  if (value === null || value === undefined) return '—';
  return String(Math.round(value));
}

export function formatPercent(value: number | null | undefined, digits = 0): string {
  if (value === null || value === undefined) return '—';
  return `${(value * 100).toFixed(digits)}%`;
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return '—';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '—';
  return new Intl.DateTimeFormat('ru-RU', { day: '2-digit', month: 'short', year: 'numeric' }).format(d);
}

export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return '—';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '—';
  return new Intl.DateTimeFormat('ru-RU', {
    day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit',
  }).format(d);
}

export function plural(n: number, one: string, few: string, many: string): string {
  const mod10 = n % 10;
  const mod100 = n % 100;
  if (mod10 === 1 && mod100 !== 11) return one;
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) return few;
  return many;
}

/** «3 дня назад», «5 месяцев назад» — без внешних библиотек. */
export function timeAgo(iso: string | null | undefined): string {
  if (!iso) return '—';
  const then = Date.parse(iso);
  if (Number.isNaN(then)) return '—';
  const days = Math.floor((Date.now() - then) / 86_400_000);
  if (days < 0) return formatDate(iso);
  if (days === 0) return 'сегодня';
  if (days === 1) return 'вчера';
  if (days < 30) return `${days}${NBSP}${plural(days, 'день', 'дня', 'дней')}${NBSP}назад`;
  const months = Math.floor(days / 30);
  if (months < 12) return `${months}${NBSP}${plural(months, 'месяц', 'месяца', 'месяцев')}${NBSP}назад`;
  const years = Math.floor(months / 12);
  return `${years}${NBSP}${plural(years, 'год', 'года', 'лет')}${NBSP}назад`;
}

export function truncate(text: string, max: number): string {
  return text.length <= max ? text : `${text.slice(0, max - 1)}…`;
}

/** Простейшая расшифровка cron для расписания пересчёта. */
export function humanCron(expr: string | null | undefined): string {
  if (!expr) return '—';
  const parts = expr.trim().split(/\s+/);
  if (parts.length !== 5) return expr;
  const [min, hour, dom, mon, dow] = parts;
  const at = `${hour.padStart(2, '0')}:${min.padStart(2, '0')}`;
  if (dom === '*' && mon === '*' && dow === '*' && /^\d+$/.test(hour) && /^\d+$/.test(min)) {
    return `ежедневно в ${at}`;
  }
  if (dom === '*' && mon === '*' && /^\d$/.test(dow)) {
    const days = ['по воскресеньям', 'по понедельникам', 'по вторникам', 'по средам',
      'по четвергам', 'по пятницам', 'по субботам'];
    return `${days[Number(dow)]} в ${at}`;
  }
  if (hour.startsWith('*/')) return `каждые ${hour.slice(2)} ч`;
  return expr;
}
