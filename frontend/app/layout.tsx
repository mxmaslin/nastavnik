import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Nastavnik - AI Learning Assistant',
  description: 'Interactive learning platform with AI-powered validation',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
