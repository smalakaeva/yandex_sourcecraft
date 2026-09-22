/** История запусков анализа в браузере: позволяет показать «прошлый прогон» и дельту Score. */
export interface RunRecord {
  full_path: string;
  analysis_id: string;
  started_at: string;
  finished_at: string | null;
  status: string;
  total: number | null;
}

const KEY = 'rh.runs';
const LIMIT = 40;

export function loadRuns(): RunRecord[] {
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? (JSON.parse(raw) as RunRecord[]) : [];
  } catch {
    return [];
  }
}

export function saveRun(record: RunRecord) {
  try {
    const runs = loadRuns().filter((r) => r.analysis_id !== record.analysis_id);
    runs.unshift(record);
    localStorage.setItem(KEY, JSON.stringify(runs.slice(0, LIMIT)));
  } catch {
    /* хранилище недоступно — история просто не сохранится */
  }
}

export function lastRunFor(fullPath: string, excludeId?: string): RunRecord | undefined {
  return loadRuns().find(
    (r) => r.full_path === fullPath && r.status === 'succeeded' && r.analysis_id !== excludeId,
  );
}
