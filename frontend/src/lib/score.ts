import type { CategoryKey, DataStatus, Priority } from '@/api/types';

export type Tone = 'good' | 'warn' | 'bad' | 'nodata';

/** Единая шкала цвета для всех мест, где показывается балл. */
export function scoreTone(score: number | null | undefined): Tone {
  if (score === null || score === undefined) return 'nodata';
  if (score >= 70) return 'good';
  if (score >= 45) return 'warn';
  return 'bad';
}

export const toneVar: Record<Tone, string> = {
  good: 'var(--good)',
  warn: 'var(--warn)',
  bad: 'var(--bad)',
  nodata: 'var(--nodata)',
};

export const toneSoftVar: Record<Tone, string> = {
  good: 'var(--good-soft)',
  warn: 'var(--warn-soft)',
  bad: 'var(--bad-soft)',
  nodata: 'var(--nodata-soft)',
};

export function scoreColor(score: number | null | undefined): string {
  return toneVar[scoreTone(score)];
}

export function gradeLabel(grade: string): string {
  const map: Record<string, string> = {
    A: 'Здоровый проект',
    B: 'В хорошей форме',
    C: 'Требует внимания',
    D: 'Много проблем',
    E: 'В критическом состоянии',
  };
  return map[grade] ?? 'Оценка не рассчитана';
}

export const CATEGORY_ORDER: CategoryKey[] = [
  'security',
  'code_health',
  'activity',
  'documentation',
  'cicd',
  'issues',
];

export const CATEGORY_TITLE: Record<CategoryKey, string> = {
  security: 'Security',
  code_health: 'Состояние кода',
  activity: 'Активность',
  documentation: 'Документация',
  cicd: 'CI/CD',
  issues: 'Issues',
};

export const CATEGORY_SHORT: Record<CategoryKey, string> = {
  security: 'Sec',
  code_health: 'Code',
  activity: 'Act',
  documentation: 'Docs',
  cicd: 'CI',
  issues: 'Iss',
};

export const CATEGORY_HINT: Record<CategoryKey, string> = {
  security: 'Результаты AppSec SourceCraft: SAST, SCA, secret scanning, критичность и статус исправления.',
  code_health: 'TODO/FIXME и их давность, размер файлов, признаки накопленного технического долга.',
  activity: 'Коммиты, дата последней активности, контрибьюторы, merge request, релизы, bus factor.',
  documentation: 'README, лицензия, инструкция запуска, CONTRIBUTING, CODEOWNERS, шаблоны.',
  cicd: 'Наличие CI, статусы и стабильность прогонов, длительность пайплайнов.',
  issues: 'Поток задач: открытые и закрытые, зависшие, время до первого ответа и закрытия.',
};

export const STATUS_LABEL: Record<DataStatus, string> = {
  ok: 'Данные собраны',
  partial: 'Часть данных недоступна',
  no_data: 'Нет данных',
  not_applicable: 'Не применимо',
};

export const STATUS_TONE: Record<DataStatus, Tone | 'accent'> = {
  ok: 'good',
  partial: 'warn',
  no_data: 'nodata',
  not_applicable: 'nodata',
};

export const PRIORITY_LABEL: Record<Priority, string> = {
  critical: 'Критический',
  high: 'Высокий',
  medium: 'Средний',
  low: 'Низкий',
  info: 'Информация',
};

export const PRIORITY_TONE: Record<Priority, Tone> = {
  critical: 'bad',
  high: 'bad',
  medium: 'warn',
  low: 'good',
  info: 'nodata',
};

export const SOURCE_LABEL: Record<string, string> = {
  git_clone: 'Git-клон',
  platform_api: 'API платформы',
  platform_cli: 'SourceCraft CLI',
  appsec_api: 'AppSec API',
};
