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
  scope?: 'all' | 'lesson';
  lesson_title?: string | null;
}

interface StatisticsProps {
  sessionId: string;
  /** Если задан — статистика только по этому уроку (после прохождения). */
  lessonId?: string;
  lessonTitle?: string;
  onBack: () => void;
}

export default function Statistics({
  sessionId,
  lessonId,
  lessonTitle,
  onBack,
}: StatisticsProps) {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getStatistics(sessionId || undefined, lessonId)
      .then(data => {
        setStats(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [sessionId, lessonId]);

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
            {lessonId
              ? lessonTitle
                ? `Только урок: ${lessonTitle}`
                : 'Только этот урок'
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
        marginBottom: '24px'
      }}>
        <StatCard
          label="Sessions"
          value={stats.total_sessions}
          color="var(--primary)"
        />
        <StatCard
          label="Completed"
          value={stats.completed_sessions}
          color="var(--success)"
        />
        <StatCard
          label="Questions"
          value={stats.total_questions_answered}
          color="var(--primary)"
        />
        <StatCard
          label="Correct"
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
          Success Rate
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
          <p style={{ fontSize: '12px', color: 'var(--gray-500)' }}>Timeouts</p>
        </div>
        <div style={{ textAlign: 'center' }}>
          <p style={{ fontSize: '24px', fontWeight: 'bold', color: 'var(--warning)' }}>
            {stats.ml_failures}
          </p>
          <p style={{ fontSize: '12px', color: 'var(--gray-500)' }}>AI Failures</p>
        </div>
        <div style={{ textAlign: 'center' }}>
          <p style={{ fontSize: '24px', fontWeight: 'bold', color: 'var(--success)' }}>
            {stats.ml_successful_validations}
          </p>
          <p style={{ fontSize: '12px', color: 'var(--gray-500)' }}>ML OK</p>
        </div>
        <div style={{ textAlign: 'center' }}>
          <p style={{ fontSize: '24px', fontWeight: 'bold', color: 'var(--primary)' }}>
            {stats.avg_session_duration_sec}s
          </p>
          <p style={{ fontSize: '12px', color: 'var(--gray-500)' }}>Avg session</p>
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div style={{
      background: 'var(--gray-100)',
      borderRadius: '8px',
      padding: '16px',
      textAlign: 'center'
    }}>
      <p style={{ fontSize: '24px', fontWeight: 'bold', color }}>{value}</p>
      <p style={{ fontSize: '12px', color: 'var(--gray-500)' }}>{label}</p>
    </div>
  );
}
