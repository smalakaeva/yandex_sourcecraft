/** Тонкая обёртка над fetch: базовый URL, токен Я ID, типизированные ошибки. */

export class ApiError extends Error {
  status: number;
  code: string;
  details?: unknown;

  constructor(message: string, status: number, code = 'unknown', details?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.details = details;
  }

  /** Текст, который не стыдно показать пользователю */
  get userMessage(): string {
    switch (this.status) {
      case 0:
        return 'Сервис недоступен: не удалось соединиться с API.';
      case 401:
        return 'Сессия истекла. Войдите через Я ID ещё раз.';
      case 403:
        return 'Недостаточно прав для этого репозитория.';
      case 404:
        return 'Репозиторий ещё не анализировался сервисом.';
      case 429:
        return 'Слишком много запросов. Повторите через минуту.';
      default:
        return this.message || 'Неизвестная ошибка сервиса.';
    }
  }
}

export const TOKEN_STORAGE_KEY = 'rh.token';

export function getToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_STORAGE_KEY);
  } catch {
    return null;
  }
}

export function setToken(token: string | null) {
  try {
    if (token) localStorage.setItem(TOKEN_STORAGE_KEY, token);
    else localStorage.removeItem(TOKEN_STORAGE_KEY);
  } catch {
    /* приватный режим браузера — работаем без сохранения */
  }
}

export const API_BASE_URL: string = import.meta.env.VITE_API_BASE_URL ?? '/api/v1';

export async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers = new Headers(init.headers);
  headers.set('Accept', 'application/json');
  if (init.body && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json');
  if (token) headers.set('Authorization', `Bearer ${token}`);

  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, { ...init, headers, credentials: 'include' });
  } catch (e) {
    throw new ApiError((e as Error).message, 0, 'network_error');
  }

  if (res.status === 204) return undefined as T;

  const text = await res.text();
  const payload = text ? safeJson(text) : null;

  if (!res.ok) {
    const message =
      (payload && typeof payload === 'object' && 'message' in payload
        ? String((payload as Record<string, unknown>).message)
        : res.statusText) || 'Ошибка запроса';
    const code =
      payload && typeof payload === 'object' && 'code' in payload
        ? String((payload as Record<string, unknown>).code)
        : 'http_error';
    throw new ApiError(message, res.status, code, payload);
  }

  return payload as T;
}

function safeJson(text: string): unknown {
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

export function buildQuery(params: Record<string, unknown>): string {
  const sp = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null || v === '') continue;
    sp.set(k, String(v));
  }
  const qs = sp.toString();
  return qs ? `?${qs}` : '';
}
