import { SiteHeader } from '@/components/site/header'
import {
  Crosshair,
  Eye,
  Keyboard,
  Layers,
  MonitorSmartphone,
  ShieldCheck,
  Cpu,
  Gauge,
  MousePointer2,
  SlidersHorizontal,
  Sparkles,
  Wind,
} from 'lucide-react'

const FEATURES = [
  {
    icon: Eye,
    title: 'Echtzeit-ESP',
    text: 'Bounding-Boxes, Tracer-Linien, Klassen-Labels und optionale Skeleton-Overlay — konfigurierbar in Farbe, Stärke und Deckkraft.',
    tone: 'mint',
  },
  {
    icon: Crosshair,
    title: 'Ziel-Assistenz',
    text: 'Halten zum Zielen, wahlweise Cursor- oder Fadenkreuz-Modus. Smoothing und Bewegungslimit für kontrollierte Eingaben.',
    tone: 'violet',
  },
  {
    icon: Cpu,
    title: 'Lokale KI-Inferenz',
    text: 'YOLO11 läuft komplett auf deinem Rechner — CUDA, wenn vorhanden, sonst CPU. Kein Cloud-Upload, keine Bildübertragung.',
    tone: 'mint',
  },
  {
    icon: Layers,
    title: 'Drei Erkennungsprofile',
    text: 'Schnell (640 px), Ausgewogen (Pose) oder Qualität (1536 px + Teilbilder) — ein Klick, alle Parameter passen sich an.',
    tone: 'violet',
  },
  {
    icon: MousePointer2,
    title: 'Zwei Eingabemodi',
    text: 'Cursor bewegt den echten Zeiger inkl. Monitorversatz. Fadenkreuz sendet relative Windows-Eingaben ab Bildschirmmitte.',
    tone: 'mint',
  },
  {
    icon: ShieldCheck,
    title: 'Sicherheits-Gates',
    text: 'Eingabe nur bei passendem Spielfokus, frischem Ziel (< 250 ms) und gehaltenem Hotkey. F8 beendet jede Sitzung sofort.',
    tone: 'violet',
  },
  {
    icon: SlidersHorizontal,
    title: 'Live-Konfiguration',
    text: 'Alle Regler, Farben und Hotkeys lassen sich während der Sitzung anpassen — Ergebnisse erscheinen sofort im Overlay.',
    tone: 'mint',
  },
  {
    icon: MonitorSmartphone,
    title: 'Multi-Monitor',
    text: 'Wähle gezielt den Bildschirm mit dem Spiel. Randlose Vollbilder und Fenstermodus werden gleichermaßen unterstützt.',
    tone: 'violet',
  },
  {
    icon: Keyboard,
    title: 'Hotkeys & Notstopp',
    text: 'Individuelle Hold- und Pause-Tasten, Konflikterkennung und ein reservierter F8-Notaus in jeder Situation.',
    tone: 'mint',
  },
]

const STEPS = [
  {
    n: '01',
    title: 'Bildschirm wählen',
    text: 'Display mit dem Spiel selektieren, Capture testen, Fenster-Titel als Fokus-Gate hinterlegen.',
  },
  {
    n: '02',
    title: 'Profil & Modell',
    text: 'Starter-Profil nutzen oder ein eigenes vertrauenswürdiges .pt laden. Klassen-ID und Konfvenz per Regler feinjustieren.',
  },
  {
    n: '03',
    title: 'Sitzung starten',
    text: 'Overlay erscheint, Erkennung läuft. Ziel-Hotkey halten — Eingabe folgt nur, solange alles sicher zutrifft.',
  },
]

const STACK = [
  { label: 'Erkennung', value: 'YOLO11 · Ultralytics', detail: 'Detect & Pose, optional geteilte Bildausschnitte' },
  { label: 'Inferenz', value: 'PyTorch · CUDA/CPU', detail: 'Halb-Präzision auf GPU, Fallback auf CPU' },
  { label: 'Capture', value: 'mss', detail: 'Schnelle Bildschirmaufnahme pro Monitor' },
  { label: 'GUI', value: 'PySide6 / Qt 6', detail: 'Dark-Theme-Konsole mit Tabs und Live-Status' },
  { label: 'Overlay', value: 'Frameless Qt-Window', detail: 'Click-through, aus Aufnahme ausgeschlossen' },
  { label: 'Web', value: 'Next.js 16 · React 19', detail: 'Diese Seite, Tailwind CSS 4' },
]

export default function Home() {
  return (
    <>
      <SiteHeader />

      {/* ── Hero ─────────────────────────────────────────── */}
      <section className="relative overflow-hidden pt-14">
        <div className="bg-glow pointer-events-none absolute inset-0" aria-hidden />
        <div className="bg-grid pointer-events-none absolute inset-0" aria-hidden />

        <div className="relative mx-auto max-w-6xl px-5 pb-20 pt-20 sm:pt-28">
          <div className="animate-rise max-w-3xl">
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-mint/35 bg-mint-deep/50 px-3 py-1 text-[11px] font-bold tracking-[0.18em] text-mint-bright">
              <span className="relative flex size-1.5">
                <span className="absolute inline-flex size-full animate-ping rounded-full bg-mint opacity-60" />
                <span className="relative inline-flex size-1.5 rounded-full bg-mint" />
              </span>
              RETRAC VISION LAB · v5
            </div>

            <h1 className="text-4xl font-bold leading-[1.05] tracking-tight sm:text-5xl lg:text-6xl">
              Sieh, was der <span className="text-gradient">Bildschirm</span> sieht.
              <br />
              Lokal. In Echtzeit.
            </h1>

            <p className="mt-6 max-w-2xl text-base leading-relaxed text-mist sm:text-lg">
              RETRAC verbindet screen-basierte Spielerkennung mit einem konfigurierbaren
              ESP-Overlay und kontrollierter Mauseingabe — alles in einer Desktop-Konsole,
              die auf deinem Rechner läuft. Kein Upload. Keine Treiber. Kein Speicherzugriff.
            </p>

            <div className="mt-9 flex flex-wrap items-center gap-3">
              <a
                href="#download"
                className="group inline-flex items-center gap-2 rounded-lg bg-mint px-6 py-3 text-sm font-bold text-ink shadow-[0_0_40px_-12px_rgb(101_213_199_/_0.6)] transition hover:bg-mint-bright"
              >
                Desktop-App starten
                <span className="transition-transform group-hover:translate-x-0.5">→</span>
              </a>
              <a
                href="#features"
                className="inline-flex items-center gap-2 rounded-lg border border-line bg-card px-6 py-3 text-sm font-semibold text-chalk transition hover:border-mint/50 hover:text-mint-bright"
              >
                Funktionen ansehen
              </a>
            </div>

            <dl className="mt-12 grid max-w-xl grid-cols-3 gap-4 border-t border-line-soft pt-6">
              {[
                ['240 Hz', 'Eingabeschleife'],
                ['0', 'Sekunden Upload'],
                ['F8', 'Notstopp'],
              ].map(([value, label]) => (
                <div key={label}>
                  <dt className="text-xl font-bold text-mint-bright sm:text-2xl">{value}</dt>
                  <dd className="mt-0.5 text-[11px] font-medium uppercase tracking-wider text-mist">
                    {label}
                  </dd>
                </div>
              ))}
            </dl>
          </div>
        </div>
      </section>

      {/* ── Features ─────────────────────────────────────── */}
      <section id="features" className="relative border-t border-line-soft bg-panel/60 py-20">
        <div className="mx-auto max-w-6xl px-5">
          <div className="mb-12 max-w-2xl">
            <p className="mb-3 text-[11px] font-bold tracking-[0.2em] text-mint">01 · FUNKTIONEN</p>
            <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
              Alles, was eine Vision-Konsole braucht
            </h2>
            <p className="mt-4 text-mist">
              Von der Capture-Auswahl bis zum Skeleton-Overlay — durchdacht, getestet, konfigurierbar.
            </p>
          </div>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map((f, i) => (
              <article
                key={f.title}
                className="card-hover animate-rise rounded-xl border border-line-soft bg-card/80 p-6"
                style={{ animationDelay: `${i * 60}ms` }}
              >
                <div
                  className={`mb-4 inline-flex rounded-lg border p-2.5 ${
                    f.tone === 'mint'
                      ? 'border-mint/35 bg-mint-deep/50 text-mint'
                      : 'border-violet/35 bg-violet/10 text-violet'
                  }`}
                >
                  <f.icon size={18} strokeWidth={2} aria-hidden />
                </div>
                <h3 className="text-[15px] font-bold text-chalk">{f.title}</h3>
                <p className="mt-2 text-[13.5px] leading-relaxed text-mist">{f.text}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* ── Ablauf ──────────────────────────────────────── */}
      <section id="how" className="relative border-t border-line-soft py-20">
        <div className="mx-auto max-w-6xl px-5">
          <div className="mb-12 max-w-2xl">
            <p className="mb-3 text-[11px] font-bold tracking-[0.2em] text-violet">02 · ABLAUF</p>
            <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
              In drei Schritten bereit
            </h2>
          </div>

          <ol className="grid gap-5 md:grid-cols-3">
            {STEPS.map((step) => (
              <li
                key={step.n}
                className="card-hover relative rounded-xl border border-line-soft bg-panel p-6 pt-7"
              >
                <span className="absolute -top-3 left-6 rounded-md border border-violet/40 bg-ink px-2 py-0.5 font-mono text-xs font-bold text-violet">
                  {step.n}
                </span>
                <h3 className="text-[15px] font-bold text-chalk">{step.title}</h3>
                <p className="mt-2 text-[13.5px] leading-relaxed text-mist">{step.text}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      {/* ── Technik ─────────────────────────────────────── */}
      <section id="stack" className="relative border-t border-line-soft bg-panel/60 py-20">
        <div className="mx-auto max-w-6xl px-5">
          <div className="mb-12 max-w-2xl">
            <p className="mb-3 text-[11px] font-bold tracking-[0.2em] text-mint">03 · TECHNIK</p>
            <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
              Offener Stack, lokale Daten
            </h2>
            <p className="mt-4 text-mist">
              Bewährte Komponenten statt Blackbox. Jede Schicht lässt sich austauschen und testen.
            </p>
          </div>

          <div className="overflow-hidden rounded-xl border border-line-soft">
            <table className="w-full text-left text-sm">
              <thead className="bg-card text-[11px] uppercase tracking-wider text-mist">
                <tr>
                  <th className="px-5 py-3 font-semibold">Schicht</th>
                  <th className="px-5 py-3 font-semibold">Technologie</th>
                  <th className="hidden px-5 py-3 font-semibold sm:table-cell">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line-soft bg-ink/60">
                {STACK.map((row) => (
                  <tr key={row.label} className="transition hover:bg-card/50">
                    <td className="px-5 py-3.5 font-medium text-mist">{row.label}</td>
                    <td className="px-5 py-3.5 font-semibold text-mint-bright">{row.value}</td>
                    <td className="hidden px-5 py-3.5 text-mist sm:table-cell">{row.detail}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* ── Sicherheit ──────────────────────────────────── */}
      <section id="safety" className="relative border-t border-line-soft py-20">
        <div className="mx-auto grid max-w-6xl gap-10 px-5 lg:grid-cols-[1fr_1.1fr] lg:items-center">
          <div>
            <p className="mb-3 text-[11px] font-bold tracking-[0.2em] text-amber">04 · SICHERHEIT</p>
            <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
              Kontrolle behalten — immer
            </h2>
            <p className="mt-4 text-mist leading-relaxed">
              RETRAC sendet keine Eingaben, wenn auch nur eine Bedingung nicht zutrifft.
              Kein Speicherzugriff, keine Treiber, keine Umgehung gesperrter Eingaben.
            </p>
            <div className="mt-6 flex items-center gap-3 rounded-lg border border-mint/30 bg-mint-deep/40 px-4 py-3">
              <Wind size={18} className="shrink-0 text-mint" aria-hidden />
              <p className="text-[13px] font-semibold text-mint-bright">
                LOCAL INFERENCE · NO SCREEN UPLOADS
              </p>
            </div>
          </div>

          <ul className="grid gap-3 sm:grid-cols-2">
            {[
              { icon: ShieldCheck, t: 'Fokus-Gate', d: 'Nur wenn der Spielfenster-Titel passt' },
              { icon: Gauge, t: 'Frische-Gate', d: 'Bilder älter als 250 ms lösen nichts aus' },
              { icon: Keyboard, t: 'F8 Notstopp', d: 'Stoppt Eingabe und Sitzung sofort' },
              { icon: Sparkles, t: 'Overlay-Ausschluss', d: 'Windows-seitig aus Aufnahmen ausgeblendet' },
            ].map((item) => (
              <li key={item.t} className="card-hover rounded-xl border border-line-soft bg-card/70 p-5">
                <item.icon size={17} className="text-mint" aria-hidden />
                <h3 className="mt-3 text-sm font-bold text-chalk">{item.t}</h3>
                <p className="mt-1 text-[13px] text-mist">{item.d}</p>
              </li>
            ))}
          </ul>
        </div>
      </section>

      {/* ── Download ────────────────────────────────────── */}
      <section id="download" className="relative border-t border-line-soft bg-panel/70 py-20">
        <div className="mx-auto max-w-6xl px-5">
          <div className="relative overflow-hidden rounded-2xl border border-mint/25 bg-gradient-to-br from-card via-panel to-ink p-8 sm:p-12">
            <div className="bg-glow pointer-events-none absolute inset-0 opacity-70" aria-hidden />
            <div className="relative max-w-2xl">
              <p className="mb-3 text-[11px] font-bold tracking-[0.2em] text-mint">05 · DOWNLOAD</p>
              <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
                Retrac Lab starten
              </h2>
              <p className="mt-4 text-mist leading-relaxed">
                Windows 10 (ab 2004) oder Windows 11, Python 3.11 — der Start-Skript
                richtet die virtuelle Umgebung beim ersten Mal automatisch ein.
              </p>

              <div className="mt-7 rounded-lg border border-line bg-ink/80 px-4 py-3 font-mono text-[13px] text-mint-bright">
                <span className="text-mist">PS&gt;</span> .\desktop\Start&nbsp;Retrac&nbsp;Lab.cmd
              </div>

              <div className="mt-6 flex flex-wrap gap-3">
                <a
                  href="https://github.com/Robinioheimer/ai-aim"
                  className="inline-flex items-center gap-2 rounded-lg bg-mint px-5 py-2.5 text-sm font-bold text-ink transition hover:bg-mint-bright"
                >
                  Repository öffnen
                </a>
                <a
                  href="https://github.com/Robinioheimer/ai-aim#readme"
                  className="inline-flex items-center gap-2 rounded-lg border border-line bg-card px-5 py-2.5 text-sm font-semibold text-chalk transition hover:border-mint/50"
                >
                  Anleitung lesen
                </a>
              </div>

              <p className="mt-6 text-xs leading-relaxed text-mist/80">
                Hinweis: Verwage nur vertrauenswürdige .pt-Modelle (PyTorch-Dateien können Code
                ausführen). Beachte die Nutzungsbedingungen der Spiele, in denen du das Tool einsetzt.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ── Footer ──────────────────────────────────────── */}
      <footer className="border-t border-line-soft py-10">
        <div className="mx-auto flex max-w-6xl flex-col items-start justify-between gap-4 px-5 sm:flex-row sm:items-center">
          <div className="flex items-center gap-2.5">
            <span className="flex size-6 items-center justify-center rounded border border-mint/40 text-[10px] font-bold text-mint">
              R
            </span>
            <span className="text-xs font-semibold tracking-[0.18em] text-mist">
              RETRAC VISION LAB
            </span>
          </div>
          <p className="text-xs text-mist/70">
            Lokale Inferenz · Keine Screen-Uploads · Keine Treiber
          </p>
          <p className="text-xs text-mist/50">
            © {new Date().getFullYear()} RETRAC · Entwicklungswerkzeuge
          </p>
        </div>
      </footer>
    </>
  )
}
