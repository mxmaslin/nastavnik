'use client';

import { useEffect, useState } from 'react';
import { fetchLessons } from '@/lib/api';

interface Lesson {
  id: string;
  title: string;
  question_count: number;
}

interface LessonSelectProps {
  sessionId: string;
  onSelect: (lesson: Lesson) => void;
}

export default function LessonSelect({ sessionId, onSelect }: LessonSelectProps) {
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchLessons()
      .then(data => {
        setLessons(data.results || data);
        setLoading(false);
      })
      .catch(err => {
        setError('Failed to load lessons');
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <p>Loading lessons...</p>;
  }

  if (error) {
    return <p style={{ color: 'var(--error)' }}>{error}</p>;
  }

  return (
    <div>
      <h2 style={{ fontSize: '18px', marginBottom: '16px' }}>Available Lessons</h2>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {lessons.map(lesson => (
          <button
            key={lesson.id}
            onClick={() => onSelect(lesson)}
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '16px',
              background: 'var(--gray-100)',
              border: '2px solid transparent',
              borderRadius: '8px',
              cursor: 'pointer',
              textAlign: 'left',
              transition: 'border-color 0.2s',
            }}
            onMouseEnter={e => (e.currentTarget.style.borderColor = 'var(--primary)')}
            onMouseLeave={e => (e.currentTarget.style.borderColor = 'transparent')}
          >
            <div>
              <strong>{lesson.title}</strong>
              <p style={{ fontSize: '14px', color: 'var(--gray-500)', marginTop: '4px' }}>
                {lesson.question_count} questions
              </p>
            </div>
            <span style={{ fontSize: '20px' }}>→</span>
          </button>
        ))}
      </div>
    </div>
  );
}
