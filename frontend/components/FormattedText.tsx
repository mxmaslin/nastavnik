'use client';

import type { ReactNode } from 'react';

function parseBoldSegments(line: string): ReactNode[] {
  const parts = line.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) => {
    const m = part.match(/^\*\*(.+?)\*\*$/);
    if (m) return <strong key={i}>{m[1]}</strong>;
    return <span key={i}>{part}</span>;
  });
}

/** Renders plain text with **bold** segments and line breaks (no full Markdown). */
export function FormattedText({ text }: { text: string }) {
  const lines = text.split('\n');
  return (
    <div style={{ lineHeight: 1.5 }}>
      {lines.map((line, li) => (
        <p key={li} style={{ margin: '0 0 0.5em 0' }}>
          {parseBoldSegments(line)}
        </p>
      ))}
    </div>
  );
}
