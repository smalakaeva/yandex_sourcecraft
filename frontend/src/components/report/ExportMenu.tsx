import type { RepoReport } from '@/api/types';
import { IS_MOCK, api } from '@/api';
import { Dropdown } from '@/components/ui';
import { copyToClipboard, downloadText } from '@/lib/download';
import { reportFileName, reportToMarkdown } from '@/lib/markdown';

/**
 * Выгрузка отчёта:
 *  - Markdown формируется в браузере из того же объекта, что показан на экране;
 *  - PDF — печать страницы (печатные стили в src/styles/print.css): кириллица и
 *    ссылки остаются векторными, дополнительные библиотеки не нужны;
 *  - если бэкенд отдаёт готовые файлы, используем серверные ссылки.
 */
export function ExportMenu({ report, onDone }: { report: RepoReport; onDone?: (msg: string) => void }) {
  const downloadMarkdown = () => {
    downloadText(reportFileName(report, 'md'), reportToMarkdown(report));
    onDone?.('Markdown-отчёт скачан');
  };

  const printPdf = () => {
    onDone?.('Открылось окно печати: выберите «Сохранить как PDF»');
    setTimeout(() => window.print(), 150);
  };

  const copyBadge = async () => {
    const badge = api.badgeUrl(report.full_path);
    const md = `[![Repo Health Score](${badge})](${window.location.origin}/repo/${report.full_path})`;
    const ok = await copyToClipboard(md);
    onDone?.(ok ? 'Markdown бейджа скопирован' : 'Не удалось скопировать');
  };

  return (
    <Dropdown
      trigger={({ toggle, open }) => (
        <button type="button" className="btn btn--primary" onClick={toggle} aria-expanded={open}>
          Выгрузить отчёт ▾
        </button>
      )}
    >
      {(close) => (
        <>
          <button
            type="button"
            className="dropdown__item"
            onClick={() => {
              downloadMarkdown();
              close();
            }}
          >
            Markdown (.md)
            <span>Полный отчёт: Score, категории, факты, рекомендации</span>
          </button>
          <button
            type="button"
            className="dropdown__item"
            onClick={() => {
              printPdf();
              close();
            }}
          >
            PDF (печать страницы)
            <span>Откроется системный диалог «Сохранить как PDF»</span>
          </button>
          {!IS_MOCK ? (
            <a
              className="dropdown__item"
              href={api.reportUrl(report.full_path, 'pdf')}
              target="_blank"
              rel="noreferrer"
              onClick={close}
            >
              PDF с сервера
              <span>Готовый файл, собранный бэкендом</span>
            </a>
          ) : null}
          <button
            type="button"
            className="dropdown__item"
            onClick={() => {
              void copyBadge();
              close();
            }}
          >
            Скопировать badge для README
            <span>Markdown со ссылкой на публичный отчёт</span>
          </button>
        </>
      )}
    </Dropdown>
  );
}
