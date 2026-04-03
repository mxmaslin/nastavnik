'use client';

import { useState, useEffect } from 'react';
import LessonChat from '@/components/LessonChat';
import LessonSelect from '@/components/LessonSelect';
import Statistics from '@/components/Statistics';

type View = 'select' | 'lesson' | 'statistics';

interface Lesson {
  id: string;
  title: string;
  question_count: number;
}

export default function Home() {
  const [view, setView] = useState<View>('select');
  const [selectedLesson, setSelectedLesson] = useState<Lesson | null>(null);
  const [sessionId, setSessionId] = useState<string>('');
  /** После урока — номер попытки для статистики «только этот проход»; с главной — null. */
  const [statsAttemptNumber, setStatsAttemptNumber] = useState<number | null>(null);

  useEffect(() => {
    let sid = sessionStorage.getItem('session_id');
    if (!sid) {
      sid = 'session_' + Math.random().toString(36).substr(2, 9);
      sessionStorage.setItem('session_id', sid);
    }
    setSessionId(sid);
  }, []);

  const handleSelectLesson = (lesson: Lesson) => {
    setSelectedLesson(lesson);
    setView('lesson');
  };

  const handleComplete = (payload: { attemptNumber: number }) => {
    setStatsAttemptNumber(payload.attemptNumber);
    setView('statistics');
  };

  const handleBack = () => {
    setView('select');
    setSelectedLesson(null);
    setStatsAttemptNumber(null);
  };

  return (
    <main style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: '100vh',
      padding: '20px'
    }}>
      {view === 'select' && (
        <div style={{
          background: 'white',
          borderRadius: '16px',
          padding: '32px',
          maxWidth: '600px',
          width: '100%',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)'
        }}>
          <h1 style={{ marginBottom: '8px', fontSize: '28px' }}>
            Nastavnik
          </h1>
          <p style={{ color: 'var(--gray-500)', marginBottom: '24px' }}>
            AI-powered learning assistant
          </p>
          <LessonSelect
            sessionId={sessionId}
            onSelect={handleSelectLesson}
          />
          <button
            onClick={() => {
              setStatsAttemptNumber(null);
              setView('statistics');
            }}
            style={{
              marginTop: '16px',
              width: '100%',
              padding: '12px',
              background: 'var(--gray-100)',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            View Statistics
          </button>
        </div>
      )}

      {view === 'lesson' && selectedLesson && (
        <LessonChat
          lessonId={selectedLesson.id}
          sessionId={sessionId}
          onComplete={handleComplete}
        />
      )}

      {view === 'statistics' && (
        <Statistics
          sessionId={sessionId}
          lessonId={selectedLesson?.id}
          lessonTitle={selectedLesson?.title}
          attemptNumber={statsAttemptNumber ?? undefined}
          onBack={handleBack}
        />
      )}
    </main>
  );
}
