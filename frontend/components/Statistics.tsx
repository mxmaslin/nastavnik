'use client';

import { useEffect, useState } from 'react';
import { getStatistics } from '@/lib/api';

interface Stats {
  total_sessions: number;
  completed_sessions: number;
  total_questions_answered: number;
  correct_answers: number;
  success_rate: number;
  ml_failures: number;
  timeouts: number;
  ml_successful_validations: number;
  avg_session_duration_sec: number;
  scope?: 'all' | 'lesson' | 'attempt';
  lesson_title?: string | null;
}

interface StatisticsProps {
  sessionId: string;
  /** Все попытки урока — только lesson_id; одна попытка — ещё и attempt_number (после «Статистика» из урока). */
  lessonId?: string;
  lessonTitle?: string;
  attemptNumber?: number;
  onBack: () => void;
}

export default function Statistics({
  sessionId,
  lessonId,
  lessonTitle,
  attemptNumber,
  onBack,
}: StatisticsProps) {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!sessionId) {
      return;
    }
    setLoading(true);
    setStats(null);
    const attemptArg =
      lessonId && attemptNumber != null && attemptNumber >= 1
        ? attemptNumber
        : undefined;
    getStatistics(sessionId, lessonId, attemptArg)
      .then(data => {
        setStats(data);
        setLoading(false);
      })
      .catch(() => {
        setStats(null);
        setLoading(false);
      });
  }, [sessionId, lessonId, attemptNumber]);

  if (loading) {
    return (
      <div style={{
        background: 'white',
        borderRadius: '16px',
        padding: '32px',
        textAlign: 'center'
      }}>
        Loading statistics...
      </div>
    );
  }

  if (!stats) {
    return (
      <div style={{
        background: 'white',
        borderRadius: '16px',
        padding: '32px',
        textAlign: 'center'
      }}>
        <p>Failed to load statistics</p>
        <button onClick={onBack} style={{ marginTop: '16px' }}>Go Back</button>
      </div>
    );
  }

  const isAllLessons = !lessonId;
  const isSingleAttempt = Boolean(lessonId && attemptNumber != null);

  return (
    <div style={{
      background: 'white',
      borderRadius: '16px',
      padding: '32px',
      maxWidth: '500px',
      width: '100%',
      boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)'
    }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        gap: '16px',
        marginBottom: '24px'
      }}>
        <div>
          <h2 style={{ fontSize: '24px', margin: 0 }}>📊 Статистика</h2>
          <p style={{ fontSize: '13px', color: 'var(--gray-500)', marginTop: '8px' }}>
            {isSingleAttempt
              ? lessonTitle
                ? `Только эта попытка (№${attemptNumber}): ${lessonTitle}`
                : `Только эта попытка (№${attemptNumber})`
              : lessonId
                ? lessonTitle
                  ? `Все попытки урока: ${lessonTitle}`
                  : 'Все попытки этого урока'
                : 'Все пройденные ранее уроки'}
          </p>
        </div>
        <button
          onClick={onBack}
          style={{
            background: 'var(--gray-100)',
            border: 'none',
            padding: '8px 16px',
            borderRadius: '6px',
            cursor: 'pointer'
          }}
        >
          ← Back
        </button>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: '16px',
        marginBottom: '12px'
      }}>
        <StatCard
          label="Уникальных уроков"
          hint={
            isSingleAttempt
              ? 'В выборке один урок.'
              : isAllLessons
                ? 'Разных уроков, по которым есть данные (не число проходов).'
                : 'Уроков в выборке при фильтре по одному уроку.'
          }
          value={stats.total_sessions}
          color="var(--primary)"
        />
        <StatCard
          label="Завершённых проходов"
          hint={
            isSingleAttempt
              ? '1, если по этой попытке закрыты все вопросы урока; иначе 0.'
              : isAllLessons
                ? 'Сколько раз урок был доведён до конца; повтор того же урока добавляет +1.'
                : 'Сумма завершений по выбранному уроку (все попытки).'
          }
          value={stats.completed_sessions}
          color="var(--success)"
        />
        <StatCard
          label="Записей ответов"
          hint="Все ответы и служебные записи (в т.ч. таймауты и добор при завершении), суммарно по выбранному диапазону."
          value={stats.total_questions_answered}
          color="var(--primary)"
        />
        <StatCard
          label="Верных"
          hint="Ответы, по которым проверка дала «верно»."
          value={stats.correct_answers}
          color="var(--success)"
        />
      </div>

      <div style={{
        background: 'var(--gray-100)',
        borderRadius: '12px',
        padding: '24px',
        textAlign: 'center',
        marginBottom: '24px'
      }}>
        <p style={{ fontSize: '14px', color: 'var(--gray-500)', marginBottom: '8px' }}>
          Доля верных ответов
        </p>
        <p style={{
          fontSize: '48px',
          fontWeight: 'bold',
          color: stats.success_rate >= 70 ? 'var(--success)' :
                 stats.success_rate >= 40 ? 'var(--warning)' : 'var(--error)'
        }}>
          {stats.success_rate}%
        </p>
      </div>

      <p style={{
        fontSize: '11px',
        color: 'var(--gray-500)',
        lineHeight: 1.45,
        margin: '0 0 12px 0',
        padding: '10px 12px',
        background: 'rgba(0,0,0,0.03)',
        borderRadius: '8px'
      }}>
        Ниже — отдельные счётчики по признакам записи. Они <strong>не суммируются</strong> в число
        ответов: например, таймаут часто одновременно учитывается и как сбой проверки ML.
      </p>

      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: '16px',
        padding: '16px',
        background: 'var(--gray-100)',
        borderRadius: '8px'
      }}>
        <div style={{ textAlign: 'center' }}>
          <p style={{ fontSize: '24px', fontWeight: 'bold', color: 'var(--error)' }}>
            {stats.timeouts}
          </p>
          <p style={{ fontSize: '12px', color: 'var(--gray-500)' }}>Таймауты</p>
          <p style={{ fontSize: '10px', color: 'var(--gray-500)', marginTop: '4px', lineHeight: 1.35 }}>
            Пустой ответ (ожидание / пропуск)
          </p>
        </div>
        <div style={{ textAlign: 'center' }}>
          <p style={{ fontSize: '24px', fontWeight: 'bold', color: 'var(--warning)' }}>
            {stats.ml_failures}
          </p>
          <p style={{ fontSize: '12px', color: 'var(--gray-500)' }}>Сбои ML</p>
          <p style={{ fontSize: '10px', color: 'var(--gray-500)', marginTop: '4px', lineHeight: 1.35 }}>
            Сервис проверки недоступен / ошибка
          </p>
        </div>
        <div style={{ textAlign: 'center' }}>
          <p style={{ fontSize: '24px', fontWeight: 'bold', color: 'var(--success)' }}>
            {stats.ml_successful_validations}
          </p>
          <p style={{ fontSize: '12px', color: 'var(--gray-500)' }}>Проверка ML ОК</p>
          <p style={{ fontSize: '10px', color: 'var(--gray-500)', marginTop: '4px', lineHeight: 1.35 }}>
            Ответ дошёл до ML и получил результат
          </p>
        </div>
        <div style={{ textAlign: 'center' }}>
          <p style={{ fontSize: '24px', fontWeight: 'bold', color: 'var(--primary)' }}>
            {stats.avg_session_duration_sec}s
          </p>
          <p style={{ fontSize: '12px', color: 'var(--gray-500)' }}>Ср. длительность</p>
          <p style={{ fontSize: '10px', color: 'var(--gray-500)', marginTop: '4px', lineHeight: 1.35 }}>
            {isSingleAttempt
              ? 'От первой до последней записи ответа в этой попытке'
              : 'По завершённым проходам в выборке'}
          </p>
        </div>
      </div>
    </div>
  );
}

function StatCard({
  label,
  hint,
  value,
  color,
}: {
  label: string;
  hint?: string;
  value: number;
  color: string;
}) {
  return (
    <div style={{
      background: 'var(--gray-100)',
      borderRadius: '8px',
      padding: '16px',
      textAlign: 'center'
    }}>
      <p style={{ fontSize: '24px', fontWeight: 'bold', color }}>{value}</p>
      <p style={{ fontSize: '12px', color: 'var(--gray-500)' }}>{label}</p>
      {hint ? (
        <p style={{
          fontSize: '10px',
          color: 'var(--gray-500)',
          marginTop: '8px',
          lineHeight: 1.35,
          textAlign: 'left',
        }}>
          {hint}
        </p>
      ) : null}
    </div>
  );
}
