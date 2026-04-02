'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { startLesson, submitAnswer, getInteractionStatus, completeLesson } from '@/lib/api';
import { FormattedText } from '@/components/FormattedText';

interface Question {
  id: string;
  text: string;
  order: number;
}

interface StartLessonResponse {
  session_id: string;
  lesson?: { id: string; title?: string; text?: string; questions?: Question[] };
  current_question: Question | null;
  current_question_index: number;
  total_questions: number;
}

interface Message {
  type: 'answer' | 'result' | 'timeout' | 'error' | 'info';
  content: string;
  timestamp: Date;
  isCorrect?: boolean | null;
}

interface LessonChatProps {
  lessonId: string;
  sessionId: string;
  onComplete: () => void;
  onBack: () => void;
}

type Phase = 'reading' | 'questions' | 'completed';

export default function LessonChat({ lessonId, sessionId, onComplete, onBack }: LessonChatProps) {
  const [phase, setPhase] = useState<Phase>('reading');
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentQuestion, setCurrentQuestion] = useState<Question | null>(null);
  const [lessonTitle, setLessonTitle] = useState('');
  const [lessonBody, setLessonBody] = useState('');
  const [answer, setAnswer] = useState('');
  const [timeLeft, setTimeLeft] = useState(30);
  const [isWaiting, setIsWaiting] = useState(false);
  const [isCompleted, setIsCompleted] = useState(false);
  const [totalQuestions, setTotalQuestions] = useState(0);
  const [currentIndex, setCurrentIndex] = useState(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const startPayloadRef = useRef<StartLessonResponse | null>(null);
  const handleTimeoutRef = useRef<() => void>(() => {});

  const addMessage = useCallback((type: Message['type'], content: string, isCorrect?: boolean | null) => {
    setMessages(prev => [...prev, { type, content, timestamp: new Date(), isCorrect }]);
  }, []);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  const stopTimer = useCallback(() => {
    if (timerRef.current) clearInterval(timerRef.current);
    timerRef.current = null;
  }, []);

  const applyStartResponse = useCallback((data: StartLessonResponse) => {
    startPayloadRef.current = data;
    setTotalQuestions(data.total_questions);
    setCurrentIndex(data.current_question_index);

    if (data.lesson?.title) setLessonTitle(data.lesson.title);
    if (data.lesson?.text) setLessonBody(data.lesson.text);

    if (!data.total_questions || !data.current_question) {
      setIsCompleted(true);
      setPhase('completed');
      addMessage('info', 'В этом уроке нет вопросов.');
      void completeLesson(lessonId, sessionId).catch(() => {});
      return;
    }

    const resumedMidLesson = data.current_question_index > 0;
    if (resumedMidLesson) {
      setPhase('questions');
      setCurrentQuestion(data.current_question);
      addMessage('info', 'Продолжаем урок с вопроса ' + (data.current_question_index + 1) + '.');
    } else {
      setPhase('reading');
      setCurrentQuestion(null);
    }
  }, [lessonId, sessionId, addMessage]);

  const enterQuestionsPhaseFromReading = useCallback(() => {
    const data = startPayloadRef.current;
    if (!data?.current_question) return;
    setPhase('questions');
    setCurrentQuestion(data.current_question);
    setCurrentIndex(data.current_question_index);
    setTotalQuestions(data.total_questions);
  }, []);

  useEffect(() => {
    if (phase !== 'questions' || !currentQuestion || isWaiting || isCompleted) {
      stopTimer();
      return;
    }
    setTimeLeft(30);
    timerRef.current = setInterval(() => {
      setTimeLeft(prev => {
        if (prev <= 1) {
          if (timerRef.current) clearInterval(timerRef.current);
          handleTimeoutRef.current();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => stopTimer();
  }, [phase, currentQuestion?.id, isWaiting, isCompleted, stopTimer]);

  const pollForResult = useCallback(
    (interactionId: string, lessonComplete: boolean) => {
      const maxAttempts = 20;
      let attempts = 0;

      const finalizeSuccess = (icon: string, text: string, correctFlag: boolean | null) => {
        addMessage('result', `${icon} ${text}`, correctFlag);
        setIsWaiting(false);
        if (lessonComplete) {
          addMessage('info', 'Урок завершён.');
          setIsCompleted(true);
          setPhase('completed');
          stopTimer();
          void completeLesson(lessonId, sessionId).catch(() => {
            addMessage('error', 'Не удалось зафиксировать урок на сервере.');
          });
        }
      };

      const poll = async () => {
        attempts += 1;
        try {
          const data = await getInteractionStatus(interactionId);

          if (data.is_correct !== null && data.is_correct !== undefined) {
            const icon = data.is_correct ? 'Верно:' : 'Неверно:';
            const status = data.ml_service_success ? '' : ' (сервис проверки недоступен)';
            const label = data.is_correct ? 'ответ засчитан.' : 'ответ не засчитан как верный.';
            finalizeSuccess(icon, `${label}${status}`, data.is_correct);
            return;
          }

          if (!data.ml_service_success && attempts > 4) {
            finalizeSuccess('Внимание:', 'проверка недоступна, переходим дальше.', null);
            return;
          }

          if (attempts < maxAttempts) {
            setTimeout(poll, 2000);
          } else {
            addMessage('error', 'Проверка ответа занимает слишком много времени.');
            setIsWaiting(false);
            if (lessonComplete) {
              setIsCompleted(true);
              setPhase('completed');
              stopTimer();
              void completeLesson(lessonId, sessionId).catch(() => {});
            }
          }
        } catch {
          if (attempts < maxAttempts) {
            setTimeout(poll, 2000);
          } else {
            setIsWaiting(false);
            if (lessonComplete) {
              setIsCompleted(true);
              setPhase('completed');
              stopTimer();
              void completeLesson(lessonId, sessionId).catch(() => {});
            }
          }
        }
      };

      poll();
    },
    [addMessage, lessonId, sessionId, stopTimer]
  );

  const handleTimeout = useCallback(async () => {
    if (phase !== 'questions' || !currentQuestion || isWaiting) return;

    setIsWaiting(true);
    addMessage('timeout', 'Время вышло. Записываем пустой ответ…');

    try {
      const data = await submitAnswer(sessionId, currentQuestion.id, '');
      addMessage('info', 'Пустой ответ сохранён.');
      if (data.next_question) {
        setCurrentQuestion(data.next_question);
        setCurrentIndex(data.current_question_index);
        setTotalQuestions(data.total_questions);
      } else {
        setCurrentQuestion(null);
        setCurrentIndex(data.current_question_index);
        setTotalQuestions(data.total_questions);
      }
      pollForResult(data.interaction_id, Boolean(data.lesson_complete));
    } catch {
      addMessage('error', 'Не удалось записать ответ по таймауту');
      setIsWaiting(false);
    }
  }, [phase, currentQuestion, isWaiting, sessionId, addMessage, pollForResult]);

  useEffect(() => {
    handleTimeoutRef.current = () => {
      void handleTimeout();
    };
  }, [handleTimeout]);

  const loadLesson = useCallback(async () => {
    try {
      const data = (await startLesson(lessonId, sessionId)) as StartLessonResponse;
      applyStartResponse(data);
    } catch {
      addMessage('error', 'Не удалось загрузить урок');
    }
  }, [lessonId, sessionId, applyStartResponse, addMessage]);

  useEffect(() => {
    void loadLesson();
    return () => {
      stopTimer();
    };
  }, [loadLesson, stopTimer]);

  const handleSubmit = async () => {
    if (phase !== 'questions' || !currentQuestion || !answer.trim() || isWaiting) return;

    stopTimer();
    setIsWaiting(true);

    addMessage('answer', `Ваш ответ: ${answer}`);

    try {
      const data = await submitAnswer(sessionId, currentQuestion.id, answer);
      addMessage('info', 'Проверяем ответ…');

      if (data.next_question) {
        setCurrentQuestion(data.next_question);
        setCurrentIndex(data.current_question_index);
        setTotalQuestions(data.total_questions);
      } else {
        setCurrentQuestion(null);
        setCurrentIndex(data.current_question_index);
        setTotalQuestions(data.total_questions);
      }

      pollForResult(data.interaction_id, Boolean(data.lesson_complete));
    } catch {
      addMessage('error', 'Не удалось отправить ответ');
      setIsWaiting(false);
    }

    setAnswer('');
  };

  const handleCompleteEarly = async () => {
    addMessage(
      'info',
      'Досрочное завершение: оставшиеся вопросы будут отмечены как неверные (пустой ответ).'
    );
    try {
      const res = await completeLesson(lessonId, sessionId);
      const n = typeof res.remaining_marked_incorrect === 'number' ? res.remaining_marked_incorrect : 0;
      if (n > 0) {
        addMessage('info', `Записано без ответа: ${n} вопрос(ов).`);
      }
      setIsCompleted(true);
      setPhase('completed');
      stopTimer();
    } catch {
      addMessage('error', 'Не удалось завершить урок');
    }
  };

  const currentNumber = totalQuestions > 0 ? Math.min(currentIndex + 1, totalQuestions) : 0;
  const answeredNums =
    currentIndex > 0 ? Array.from({ length: currentIndex }, (_, i) => i + 1) : [];
  const upcomingNums =
    currentIndex + 1 < totalQuestions
      ? Array.from({ length: totalQuestions - currentIndex - 1 }, (_, i) => currentIndex + 2 + i)
      : [];

  const progressLegend = (() => {
    if (totalQuestions === 0 || phase !== 'questions') return '';
    const parts: string[] = [];
    if (answeredNums.length) parts.push(`Отвечены: ${answeredNums.join(', ')}`);
    if (currentQuestion) parts.push(`Сейчас: ${currentNumber}`);
    if (upcomingNums.length) parts.push(`Ожидают: ${upcomingNums.join(', ')}`);
    return parts.join(' · ');
  })();

  return (
    <div
      style={{
        background: 'white',
        borderRadius: '16px',
        maxWidth: '700px',
        width: '100%',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
        display: 'flex',
        flexDirection: 'column',
        height: '80vh',
        maxHeight: '640px',
      }}
    >
      <div
        style={{
          padding: '16px 24px',
          borderBottom: '1px solid var(--gray-200)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexShrink: 0,
        }}
      >
        <button
          type="button"
          onClick={onBack}
          style={{
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            fontSize: '16px',
          }}
        >
          ← Назад
        </button>
        <div style={{ textAlign: 'center' }}>
          <strong>{lessonTitle || 'Урок'}</strong>
          {totalQuestions > 0 && (
            <p style={{ fontSize: '12px', color: 'var(--gray-500)', marginTop: '4px' }}>
              Вопросов: {totalQuestions}
            </p>
          )}
        </div>
        <button
          type="button"
          onClick={() => void handleCompleteEarly()}
          disabled={isCompleted}
          style={{
            background: 'var(--error)',
            color: 'white',
            border: 'none',
            padding: '8px 16px',
            borderRadius: '6px',
            cursor: isCompleted ? 'not-allowed' : 'pointer',
            fontSize: '12px',
            opacity: isCompleted ? 0.5 : 1,
          }}
        >
          Завершить досрочно
        </button>
      </div>

      {phase === 'questions' && totalQuestions > 0 && (
        <div
          style={{
            padding: '12px 24px',
            borderBottom: '1px solid var(--gray-200)',
            background: 'var(--gray-100)',
            flexShrink: 0,
          }}
        >
          <p style={{ fontSize: '11px', color: 'var(--gray-500)', marginBottom: '8px' }}>
            Прогресс по вопросам
          </p>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', alignItems: 'center' }}>
            {Array.from({ length: totalQuestions }, (_, i) => {
              const n = i + 1;
              let tone: 'done' | 'active' | 'todo' = 'todo';
              if (i < currentIndex) tone = 'done';
              else if (i === currentIndex && currentQuestion) tone = 'active';
              return (
                <div
                  key={n}
                  title={
                    tone === 'done'
                      ? 'Отвечено'
                      : tone === 'active'
                        ? 'Текущий вопрос'
                        : 'Будет далее'
                  }
                  style={{
                    width: 36,
                    height: 36,
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 14,
                    fontWeight: 600,
                    border:
                      tone === 'active'
                        ? '3px solid var(--primary)'
                        : '2px solid var(--gray-300)',
                    background:
                      tone === 'done' ? 'var(--success)' : tone === 'active' ? 'white' : 'var(--gray-200)',
                    color: tone === 'done' ? 'white' : 'var(--gray-900)',
                  }}
                >
                  {tone === 'done' ? '✓' : n}
                </div>
              );
            })}
          </div>
          {progressLegend && (
            <p style={{ fontSize: '12px', color: 'var(--gray-700)', marginTop: '10px' }}>
              {progressLegend}
            </p>
          )}
        </div>
      )}

      {phase === 'reading' && lessonBody && (
        <div
          style={{
            padding: '16px 24px',
            borderBottom: '1px solid var(--gray-200)',
            background: '#f8fafc',
            flexShrink: 0,
          }}
        >
          <p style={{ fontSize: '11px', color: 'var(--gray-500)', marginBottom: '6px' }}>
            Текст для ознакомления ({totalQuestions} вопрос(ов) после прочтения)
          </p>
          <div
            style={{
              maxHeight: 'min(280px, 38vh)',
              overflowY: 'auto',
              fontSize: '15px',
              paddingRight: '8px',
            }}
          >
            <FormattedText text={lessonBody} />
          </div>
        </div>
      )}

      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '16px 24px',
          display: 'flex',
          flexDirection: 'column',
          gap: '12px',
          minHeight: 0,
        }}
      >
        {phase === 'questions' && currentQuestion && !isCompleted && (
          <div
            style={{
              padding: '16px',
              borderRadius: '12px',
              background: '#f0f9ff',
              border: '1px solid #bae6fd',
              flexShrink: 0,
            }}
          >
            <p style={{ fontSize: '12px', color: 'var(--gray-500)', marginBottom: '8px' }}>
              Вопрос {currentNumber} из {totalQuestions}
            </p>
            <div style={{ fontSize: '16px', lineHeight: 1.5 }}>
              <FormattedText text={currentQuestion.text} />
            </div>
          </div>
        )}

        {messages.length > 0 && (
          <p style={{ fontSize: '11px', color: 'var(--gray-500)' }}>История ответов</p>
        )}
        {messages.map((msg, i) => (
          <div
            key={i}
            style={{
              padding: '12px 16px',
              borderRadius: '12px',
              background:
                msg.type === 'answer'
                  ? '#f0fdf4'
                  : msg.type === 'result'
                    ? msg.isCorrect
                      ? '#f0fdf4'
                      : '#fef2f2'
                    : msg.type === 'error' || msg.type === 'timeout'
                      ? '#fef2f2'
                      : 'var(--gray-100)',
              alignSelf: msg.type === 'answer' ? 'flex-end' : 'flex-start',
              maxWidth: '90%',
              whiteSpace: 'pre-wrap',
            }}
          >
            {msg.content}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {!isCompleted && (
        <div
          style={{
            padding: '16px 24px',
            borderTop: '2px solid var(--gray-200)',
            display: 'flex',
            flexDirection: 'column',
            gap: '12px',
            flexShrink: 0,
            background: 'white',
            boxShadow: '0 -4px 12px rgba(0,0,0,0.06)',
          }}
        >
          {phase === 'reading' && (
            <button
              type="button"
              onClick={() => enterQuestionsPhaseFromReading()}
              style={{
                width: '100%',
                padding: '14px 24px',
                background: 'var(--primary)',
                color: 'white',
                border: 'none',
                borderRadius: '10px',
                cursor: 'pointer',
                fontSize: '16px',
                fontWeight: 600,
              }}
            >
              Перейти к вопросам
            </button>
          )}

          {phase === 'questions' && currentQuestion && (
            <>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '12px', color: 'var(--gray-500)', minWidth: '120px' }}>
                  Время на ответ
                </span>
                <div
                  style={{
                    flex: 1,
                    height: '8px',
                    background: 'var(--gray-200)',
                    borderRadius: '4px',
                    overflow: 'hidden',
                  }}
                >
                  <div
                    style={{
                      width: `${(timeLeft / 30) * 100}%`,
                      height: '100%',
                      background:
                        timeLeft > 10
                          ? 'var(--success)'
                          : timeLeft > 5
                            ? 'var(--warning)'
                            : 'var(--error)',
                      transition: 'width 1s linear',
                    }}
                  />
                </div>
                <span
                  style={{
                    fontSize: '14px',
                    fontWeight: 600,
                    color:
                      timeLeft > 10
                        ? 'var(--success)'
                        : timeLeft > 5
                          ? 'var(--warning)'
                          : 'var(--error)',
                    minWidth: '36px',
                    textAlign: 'right',
                  }}
                >
                  {timeLeft}s
                </span>
              </div>

              <label style={{ fontSize: '13px', fontWeight: 600, color: 'var(--gray-700)' }}>
                Ваш ответ
              </label>
              <div style={{ display: 'flex', gap: '8px', alignItems: 'stretch' }}>
                <input
                  type="text"
                  value={answer}
                  onChange={e => setAnswer(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && void handleSubmit()}
                  placeholder="Введите ответ и нажмите «Отправить»"
                  disabled={isWaiting}
                  autoComplete="off"
                  style={{
                    flex: 1,
                    minWidth: 0,
                    padding: '14px 16px',
                    borderRadius: '8px',
                    border: '2px solid var(--gray-300)',
                    fontSize: '16px',
                    outline: 'none',
                  }}
                />
                <button
                  type="button"
                  onClick={() => void handleSubmit()}
                  disabled={isWaiting || !answer.trim()}
                  style={{
                    padding: '14px 22px',
                    background: 'var(--primary)',
                    color: 'white',
                    border: 'none',
                    borderRadius: '8px',
                    cursor: isWaiting || !answer.trim() ? 'not-allowed' : 'pointer',
                    opacity: isWaiting || !answer.trim() ? 0.6 : 1,
                    fontSize: '16px',
                    whiteSpace: 'nowrap',
                  }}
                >
                  Отправить
                </button>
              </div>
            </>
          )}
        </div>
      )}

      {isCompleted && (
        <div
          style={{
            padding: '16px 24px',
            borderTop: '1px solid var(--gray-200)',
            textAlign: 'center',
            flexShrink: 0,
          }}
        >
          <button
            type="button"
            onClick={onComplete}
            style={{
              padding: '12px 32px',
              background: 'var(--success)',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: '16px',
            }}
          >
            Статистика
          </button>
        </div>
      )}
    </div>
  );
}
