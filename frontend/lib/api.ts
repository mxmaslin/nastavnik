function apiBase(): string {
  const explicit = process.env.NEXT_PUBLIC_API_URL;
  if (explicit !== undefined && explicit !== '') {
    return explicit.replace(/\/$/, '');
  }
  if (typeof window !== 'undefined') {
    return '';
  }
  return process.env.INTERNAL_API_URL || 'http://backend:8000';
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

export async function getStatistics(sessionId?: string) {
  const url = sessionId
    ? apiUrl(`/api/statistics/?session_id=${encodeURIComponent(sessionId)}`)
    : apiUrl('/api/statistics/');
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch statistics');
  return res.json();
}
