# RETRAC · Vision Lab

**Screen-basierte Spielerkennung, ESP-Overlay und kontrollierte Mauseingabe — komplett lokal.**

RETRAC ist eine Windows-Desktop-Konsole (Qt) mit optionaler Next.js-Web-Oberfläche.
Ein YOLO11-Modell erkennt Personen auf dem Bildschirm, ein click-through Overlay
zeichnet Bounding-Boxes, Tracer und Skeletons, und eine getaktete Eingabeschleife
(240 Hz) bewegt den Cursor bzw. sendet relative Mausbewegungen — nur wenn alle
Sicherheits-Gates zutreffen.

| | |
|---|---|
| **Plattform** | Windows 10 (2004+) / Windows 11, Python 3.11 |
| **Stack** | PySide6 · Ultralytics YOLO11 · PyTorch · mss · Next.js 16 |
| **Lizenz-Hinweis** | Eigene Nutzung / Entwicklung — Spiel-ToS beachten |

---

## Setup

### Desktop-App (Windows)

Doppelklick auf:

```text
desktop\Start Retrac Lab.cmd
```

Das Skript legt beim ersten Start eine `.venv` an, installiert `requirements.txt`
und öffnet die **Vision Test Console**. Spätere Starts überspringen die Installation,
solange die Requirements unverändert sind.

> **WICHTIG bei langen Pfaden („Windows Long Path"):**
> PySide6 enthält sehr tiefe Dateipfade. Wenn der Projektordner selbst schon
> lang ist (z. B. `Downloads\ai-aim-arena-...\ai-aim-arena-...\`), reicht die
> 260-Zeichen-Grenze von Windows nicht mehr → `pip` bricht mit
> `OSError: ... No such file or directory` ab.
>
> **Sofort-Fix:**
> 1. Defekten Ordner löschen: `...\desktop\.venv`
> 2. Projekt an einen kurzen Pfad verschieben, z. B. `C:\retrac`
> 3. `Start Retrac Lab.cmd` erneut ausführen
>
> Das Startskript legt die Umgebung automatisch nach
> `%LOCALAPPDATA%\RetracLab\venv`, sobald der Projektpfad zu lang ist.
> Alternativ Windows „Long paths" aktivieren:
> *Windows 11:* Einstellungen → System → Für Entwickler → **Long paths** an
> *oder* (Admin): `LongPathsEnabled=1` unter
> `HKLM\SYSTEM\CurrentControlSet\Control\FileSystem` setzen.

Manuell (entspricht dem Skript):

```powershell
cd desktop
py -3.11 -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python main.py
```

### Web-Oberfläche (diese Seite)

```bash
pnpm install
pnpm dev      # http://localhost:3000
pnpm build    # Produktions-Build
```

---

## Projektstruktur

```text
.
├── app/                  # Next.js-Seite (Landing / Docs)
│   ├── layout.tsx
│   ├── page.tsx
│   └── globals.css       # Design-Tokens im Stil der Desktop-Konsole
├── components/
│   ├── site/header.tsx   # Navigations-Header
│   └── ui/button.tsx     # shadcn/Base-UI Button
├── desktop/              # PySide6-Anwendung (Kern)
│   ├── main.py           # Vision Test Console (GUI)
│   ├── engine.py         # Capture-Thread + Control-Loop + SendInput
│   ├── vision.py         # YOLO-Inferenz, Tiling, IoU-NMS, Pose-Matching
│   ├── targeting.py      # Zielauswahl, Eigenzonen-Filter, Status-Texte
│   ├── motion.py         # Zeitbasiertes Smoothing + Schrittlimit
│   ├── overlay.py        # Frameless ESP-Overlay-Fenster
│   ├── config.py         # Einstellungs-Dataclass
│   ├── controls.py       # Hotkey-Button, animierte CheckBox
│   ├── help_text.py      # Tooltips für jedes Bedienelement
│   ├── test_*.py         # 56 Unit-Tests (pytest)
│   └── Start Retrac Lab.cmd
├── public/               # Icons & Placeholder
└── package.json
```

---

## Architecture (Desktop)

```text
┌────────────────────────────┐
│  Console (main.py, Qt-GUI) │  Einstellungen · Statuszeile · Tabs
└─────────────┬──────────────┘
              │ Settings (frozen dataclass)
              ▼
┌────────────────────────────┐     ┌──────────────────────────────┐
│  Detector (engine.py)      │     │  Control-Loop (240 Hz)       │
│  ┌──────────────────────┐  │     │  held(aim_key)?              │
│  │ mss.grab(monitor)    │  │     │  foreground_matches(title)?  │
│  │   ▼                  │  │     │  target_is_fresh(<250 ms)?   │
│  │ YOLO.predict (tiled) │◄─┼─────│  → Motion.step → SetCursor / │
│  │   ▼                  │  │     │    SendInput(relative)       │
│  │ merge (IoU) + poses  │  │     └──────────────────────────────┘
│  └──────────────────────┘  │
└─────────────┬──────────────┘
              │ frame-Signal (30 Hz UI-Update)
              ▼
┌────────────────────────────┐
│  Overlay (overlay.py)      │  Boxes · Tracer · Skeleton · Marker
└────────────────────────────┘
```

**Persistenz:** Alle Regler, Hotkeys, Farben und die Display-Wahl landen in
`desktop/settings.json` (debounced bei Änderung + beim Schließen). Der nächste
Start lädt sie automatisch. Die Datei ist gitignored.

**Sicherheits-Gates** (alle müssen zutreffen, sonst keine Eingabe):

1. `aim_enabled` — Schalter „Enable mouse input“
2. `foreground_matches(window_title)` — Spielfenster ist Vordergrund
3. `target_is_fresh(…, target_max_age=0.25 s)` — Bild nicht älter als 250 ms
4. `automatic or held(aim_key)` — Hotkey halten (oder Automatik)
5. **F8** (`0x77`) bricht sofort alles ab — auch während blockierter Inferenz

---

## Tests

```bash
# 56 Tests · keine Modelle, kein Windows nötig (Mocks für Win32-APIs)
cd desktop
python -m pytest -v
```

| Datei | Gegenstand |
|---|---|
| `test_motion.py` | Smoothing, Zeitbasis, Subpixel, Relativ-Modus |
| `test_targeting.py` | Zielwahl, Radius, Eigenzonen, Hotkey-Gates |
| `test_vision.py` | Klassen, Tiling, IoU-NMS, Pose-Matching, UI-Help-Keys |
| `test_engine.py` | Control-Loop, Fokus/Frische-Gates, F8, Modell-Cache |
| `test_overlay.py` | Overlay-Rendering, Zone, Console-Prefs (offscreen Qt) |

Linux/CI: Qt braucht `QT_QPA_PLATFORM=offscreen`.

---

## Erkennungsprofile

| Profil | Modell | Größe | Tiling | Confidence |
|---|---|---|---|---|
| Schnell | `yolo11n.pt` | 640 px | aus | 20 % |
| Ausgewogen | `yolo11s-pose.pt` | 640 px | aus | 25 % |
| Qualität | `yolo11m-pose.pt` | 1536 px | an | 20 % |

COCO-`person` erkennt Personen allgemein — **nicht** zuverlässig Team vs. Gegner.
Für spezifische Spiele ein eigenes, vertrauenswürdiges `.pt` laden
(PyTorch-Gewichte können Code ausführen).

---

## Web-Entwicklung

```bash
pnpm lint-free # kein ESLint-Plugin nötig — TypeScript prüft
pnpm build
```

Das Design der Website spiegelt das Dark-Theme der Desktop-Konsole
(`#0b0f14` Hintergrund, `#65d5c7` Mint-Akzent, `#b9acff` Violett).

---

## Roadmap-Ideen

- [ ] Einstellungen als JSON profiliert speichern/laden
- [ ] Screenshot-/Benchmark-Overlay für Inferenz-FPS
- [ ] TravisCI/GitHub Actions: pytest + `pnpm build`
- [ ] Trained custom `.pt`-Import mit Klassen-Mapping-UI
