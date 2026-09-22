export type Theme = 'light' | 'dark' | 'system';

const KEY = 'rh.theme';

/** По умолчанию тёмная тема: интерфейс SourceCraft тоже тёмный. */
export function getStoredTheme(): Theme {
  try {
    const v = localStorage.getItem(KEY);
    return v === 'light' || v === 'dark' || v === 'system' ? v : 'dark';
  } catch {
    return 'dark';
  }
}

export function applyTheme(theme: Theme) {
  const root = document.documentElement;
  if (theme === 'system') root.removeAttribute('data-theme');
  else root.setAttribute('data-theme', theme);
  try {
    localStorage.setItem(KEY, theme);
  } catch {
    /* приватный режим — тема просто не запомнится */
  }
}
