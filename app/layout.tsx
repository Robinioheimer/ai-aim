import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: {
    default: 'RETRAC — Lokale Vision-Konsole',
    template: '%s · RETRAC',
  },
  description:
    'Screen-basierte Spielerkennung mit lokaler YOLO-Inferenz, ESP-Overlay und kontrollierter Eingabe. Alles läuft auf deinem Rechner — kein Upload, keine Treiber.',
  applicationName: 'RETRAC',
  generator: 'Next.js',
  icons: {
    icon: [
      { url: '/icon-light-32x32.png', media: '(prefers-color-scheme: light)' },
      { url: '/icon-dark-32x32.png', media: '(prefers-color-scheme: dark)' },
      { url: '/icon.svg', type: 'image/svg+xml' },
    ],
    apple: '/apple-icon.png',
  },
}

export const viewport = {
  colorScheme: 'dark',
  themeColor: '#0b0f14',
}

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="de" className="dark">
      <body className="antialiased">{children}</body>
    </html>
  )
}
