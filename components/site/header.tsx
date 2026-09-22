import Link from 'next/link'

const NAV = [
  { href: '#features', label: 'Funktionen' },
  { href: '#how', label: 'Ablauf' },
  { href: '#stack', label: 'Technik' },
  { href: '#safety', label: 'Sicherheit' },
  { href: '#download', label: 'Download' },
]

export function SiteHeader() {
  return (
    <header className="fixed inset-x-0 top-0 z-50 border-b border-line-soft/80 bg-ink/80 backdrop-blur-xl">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-5">
        <Link href="/" className="group flex items-center gap-2.5">
          <span className="flex size-7 items-center justify-center rounded-md border border-mint/40 bg-mint-deep/60 text-mint transition group-hover:border-mint">
            <svg width="14" height="14" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6" aria-hidden>
              <path d="M14.2 14.2H17V6.9C17 4.8 15.2 3 13.1 3H5.8V5.8M14.2 14.2V7.8L7.8 14.2H14.2ZM14.2 14.2V17H6.9C4.8 17 3 15.2 3 13.1V5.8H5.8M5.8 5.8V12.2L12.2 5.8H5.8Z" strokeLinejoin="round" />
            </svg>
          </span>
          <span className="text-[13px] font-bold tracking-[0.22em] text-chalk">
            RETRAC
          </span>
        </Link>

        <nav className="hidden items-center gap-1 md:flex" aria-label="Hauptnavigation">
          {NAV.map((item) => (
            <a
              key={item.href}
              href={item.href}
              className="rounded-md px-3 py-1.5 text-[13px] font-medium text-mist transition hover:bg-card hover:text-mint-bright"
            >
              {item.label}
            </a>
          ))}
        </nav>

        <div className="flex items-center gap-2">
          <span className="hidden rounded-full border border-line bg-card px-2.5 py-1 text-[11px] font-semibold tracking-wide text-mint sm:inline">
            v5.0 · LOCAL
          </span>
          <a
            href="#download"
            className="rounded-lg bg-mint px-3.5 py-1.5 text-[13px] font-bold text-ink transition hover:bg-mint-bright"
          >
            Starten
          </a>
        </div>
      </div>
    </header>
  )
}
