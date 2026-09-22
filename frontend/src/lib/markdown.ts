import type { RepoReport } from '@/api/types';
import { formatDateTime, formatNumber, formatPercent, formatScore } from './format';
import { CATEGORY_TITLE, PRIORITY_LABEL, SOURCE_LABEL, STATUS_LABEL } from './score';

/**
 * Markdown-версия отчёта. Содержит всё, что требует ТЗ для страницы анализа:
 * ссылку на репозиторий, Score, разбивку по категориям, сильные и слабые стороны,
 * объяснение расчёта, рекомендации, сведения об отсутствии данных и дату анализа.
 */
export function reportToMarkdown(report: RepoReport): string {
  const L: string[] = [];
  const scored = report.categories.filter((c) => c.score !== null);

  L.push(`# Repo Health Report — ${report.full_path}`);
  L.push('');
  L.push(`**Репозиторий:** [${report.full_path}](${report.url})  `);
  if (report.description) L.push(`**Описание:** ${report.description}  `);
  L.push(`**Основной язык:** ${report.primary_language ?? '—'}  `);
  L.push(`**Лайки:** ${formatNumber(report.likes)}  `);
  L.push(`**Дата анализа:** ${formatDateTime(report.analyzed_at)}  `);
  L.push(`**Версия методики:** ${report.score.formula_version}`);
  L.push('');

  L.push('## Итоговая оценка');
  L.push('');
  L.push(`**Repo Health Score: ${formatScore(report.score.total)} / 100 (${report.score.grade})**`);
  L.push('');
  L.push(
    `Оценка посчитана по ${scored.length} из ${report.categories.length} категорий — ` +
      `это ${formatPercent(report.score.coverage)} веса методики. ` +
      'Категории без данных исключены из расчёта, а не засчитаны как плохой результат.',
  );
  L.push('');
  L.push(report.summary);
  L.push('');

  L.push('## Оценки по категориям');
  L.push('');
  L.push('| Категория | Оценка | Вес в методике | Вес в этом расчёте | Статус данных | Комментарий |');
  L.push('| --- | --- | --- | --- | --- | --- |');
  for (const c of report.categories) {
    L.push(
      `| ${c.title} | ${c.score === null ? '— (нет данных)' : `${formatScore(c.score)}/100`} ` +
        `| ${formatPercent(c.weight)} | ${formatPercent(c.effective_weight)} ` +
        `| ${STATUS_LABEL[c.status]} | ${c.score === null ? c.no_data_reason ?? '' : c.summary.replace(/^\d+\/100:\s*/, '')} |`,
    );
  }
  L.push('');

  L.push('## Как получилась оценка');
  L.push('');
  L.push('```');
  L.push('Repo Health Score = Σ (оценка категории × вес категории) / Σ (вес категорий с данными)');
  L.push('');
  for (const c of scored) {
    L.push(
      `${c.title.padEnd(18, ' ')} ${String(formatScore(c.score)).padStart(3, ' ')} × ` +
        `${c.weight.toFixed(2)}  (эффективный вес ${formatPercent(c.effective_weight)})`,
    );
  }
  L.push('');
  L.push(`Итог: ${formatScore(report.score.total)} / 100`);
  L.push('```');
  L.push('');

  const strengths = report.strengths ?? [];
  const risks = report.risks ?? [];
  if (strengths.length) {
    L.push('## Сильные стороны');
    L.push('');
    for (const s of strengths) L.push(`- **${CATEGORY_TITLE[s.category]}:** ${s.text}`);
    L.push('');
  }
  if (risks.length) {
    L.push('## Что требует внимания');
    L.push('');
    for (const r of risks) L.push(`- **${CATEGORY_TITLE[r.category]}:** ${r.text}`);
    L.push('');
  }

  L.push('## Рекомендации');
  L.push('');
  if (!report.recommendations.length) {
    L.push('Критичных замечаний не найдено.');
    L.push('');
  }
  report.recommendations.forEach((rec, i) => {
    L.push(`### ${i + 1}. ${rec.title}`);
    L.push('');
    L.push(`- **Приоритет:** ${PRIORITY_LABEL[rec.priority]}`);
    L.push(`- **Категория:** ${CATEGORY_TITLE[rec.category]}`);
    L.push(`- **Проблема:** ${rec.problem}`);
    L.push(`- **Почему это важно:** ${rec.why}`);
    L.push(`- **Что сделать:** ${rec.action}`);
    if (rec.evidence.length) {
      L.push(`- **Факты:** ${rec.evidence.map((e) => `${e.label} — ${e.value}`).join('; ')}`);
    }
    L.push(
      `- **Ожидаемый эффект:** ${
        rec.expected_gain > 0
          ? `+${rec.expected_gain.toFixed(1)} балла к Repo Health Score`
          : 'не влияет на Score напрямую, но снижает риск сопровождения'
      }`,
    );
    L.push('');
  });

  const missing = report.categories.filter((c) => c.status === 'no_data' || c.status === 'not_applicable');
  L.push('## Сведения об отсутствии данных');
  L.push('');
  if (!missing.length) {
    L.push('Данные собраны по всем шести категориям.');
  } else {
    for (const c of missing) {
      L.push(`- **${c.title}** — ${STATUS_LABEL[c.status]}. ${c.no_data_reason ?? ''}`);
    }
  }
  L.push('');

  if (report.collection.errors?.length) {
    L.push('### Ошибки сбора данных');
    L.push('');
    L.push('| Категория | Источник | Код | Сообщение |');
    L.push('| --- | --- | --- | --- |');
    for (const e of report.collection.errors) {
      L.push(`| ${e.category ?? '—'} | ${e.source ?? '—'} | ${e.code ?? '—'} | ${sanitize(e.message)} |`);
    }
    L.push('');
  }

  L.push('## Источники данных');
  L.push('');
  for (const [key, used] of Object.entries(report.collection.sources_used ?? {})) {
    L.push(`- ${SOURCE_LABEL[key] ?? key}: ${used ? 'использован' : 'не использован'}`);
  }
  L.push('');
  L.push(
    `Сбор данных занял ${
      report.collection.duration_ms ? `${(report.collection.duration_ms / 1000).toFixed(1)} с` : '—'
    }, версия сборщика ${report.collection.collector_version ?? '—'}.`,
  );
  L.push('');
  L.push('---');
  L.push('');
  L.push(`Отчёт сформирован сервисом SourceCraft Repo Health, ${formatDateTime(new Date().toISOString())}.`);
  L.push('');

  return L.join('\n');
}

function sanitize(text: string): string {
  return text.replace(/\|/g, '\\|').replace(/\n+/g, ' ').slice(0, 220);
}

export function reportFileName(report: RepoReport, ext: string): string {
  const date = report.analyzed_at.slice(0, 10);
  return `repo-health_${report.full_path.replace('/', '_')}_${date}.${ext}`;
}
