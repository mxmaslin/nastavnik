/**
 * База URL для API.
 * Браузер: при входе на Next :3000 — Django на :8000; за nginx (:8080, tuna и т.д.) — относительные /api/....
 * Переопределение: NEXT_PUBLIC_API_URL.
 * SSR: API_INTERNAL_URL или http://backend:8000
 */
function apiBase(): string {
  const explicit = process.env.NEXT_PUBLIC_API_URL;

  if (typeof window !== 'undefined') {
    if (explicit !== undefined && explicit !== '') {
      return explicit.replace(/\/$/, '');
    }
    const { protocol, hostname, port } = window.location;
    if (port === '3000') {
      return `${protocol}//${hostname}:8000`.replace(/\/$/, '');
    }
    return '';
  }

  if (explicit !== undefined && explicit !== '') {
    return explicit.replace(/\/$/, '');
  }
  const internal =
    process.env.API_INTERNAL_URL || process.env.INTERNAL_API_URL || 'http://backend:8000';
  return internal.replace(/\/$/, '');
}

function apiUrl(path: string): string {
  const base = apiBase();
  const p = path.startsWith('/') ? path : `/${path}`;
  return `${base}${p}`;
}

export async function fetchLessons() {
  const res = await fetch(apiUrl('/api/lessons/'));
  if (!res.ok) throw new Error('Failed to fetch lessons');
  return res.json();
}

export async function startLesson(lessonId: string, sessionId: string) {
  const res = await fetch(apiUrl(`/api/lessons/${lessonId}/start/`), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId }),
  });
  if (!res.ok) throw new Error('Failed to start lesson');
  return res.json();
}

export async function submitAnswer(sessionId: string, questionId: string, answer: string) {
  const res = await fetch(apiUrl('/api/answer/submit/'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId,
      question_id: questionId,
      answer,
    }),
  });
  if (!res.ok) throw new Error('Failed to submit answer');
  return res.json();
}

export async function getInteractionStatus(interactionId: string) {
  const res = await fetch(apiUrl(`/api/answer/status/${interactionId}/`));
  if (!res.ok) throw new Error('Failed to get interaction status');
  return res.json();
}

export async function completeLesson(lessonId: string, sessionId: string) {
  const res = await fetch(apiUrl(`/api/lessons/${lessonId}/complete/`), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId }),
  });
  if (!res.ok) throw new Error('Failed to complete lesson');
  return res.json();
}

export async function getStatistics(sessionId?: string, lessonId?: string) {
  const params = new URLSearchParams();
  if (sessionId) params.set('session_id', sessionId);
  if (lessonId) params.set('lesson_id', lessonId);
  const q = params.toString();
  const url = q ? apiUrl(`/api/statistics/?${q}`) : apiUrl('/api/statistics/');
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch statistics');
  return res.json();
}
