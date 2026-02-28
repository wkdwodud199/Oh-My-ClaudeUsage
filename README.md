# Oh-my-claudeusage

A real-time GUI dashboard for monitoring your Claude.ai usage limits.

## Features

- **Real-time usage monitoring** (auto-updates every 1 minute)
  - Current session usage (5-hour limit)
  - Weekly limit (all models)
  - Weekly limit (Sonnet only)
- **3 view modes** — Full / Mid / Min size toggle
- **Always on top (Pin)** — Keep the window above other windows
- **Opacity slider** — Adjust window transparency
- **Progress bar colors** — Green → Yellow → Red based on usage
- **Dark theme GUI** with Inter font

## Tech Stack

- Python 3.13+
- CustomTkinter (GUI)
- Playwright (Cloudflare-bypassing API calls + browser login)

## Installation

```bash
pip install -r requirements.txt
```

> Chromium browser is automatically installed on first run if not already present.

## Usage

```bash
python main.py
```

### First run

1. Dashboard and login window will appear
2. Click "Sign in with Browser"
3. Sign in to Claude.ai in the Playwright browser
4. Login is automatically detected and session is saved
5. Usage data is displayed on the dashboard

> **If you find this project useful, please consider giving it a ⭐ on [GitHub](https://github.com/wkdwodud199/Oh-My-ClaudeUsage).**
> It helps others discover the project and motivates further development.

### Subsequent runs

The saved session is loaded automatically and the dashboard is displayed immediately.

## How It Works

```
                      python main.py
                           │
                ensure_playwright_chromium()
                (auto-install if missing)
                           │
                        App.run()
              ┌────────────┴────────────┐
              │                         │
      session exists              no session
   (config/session.json)                │
              │                ┌────────▼─────────┐
              │                │   LoginWindow     │
              │                │   (login prompt)  │
              │                └────────┬─────────┘
              │                         │
              │                ┌────────▼──────────────┐
              │                │  Playwright Browser    │
              │                │  (headless=False)      │
              │                │  open claude.ai        │
              │                │  → user signs in       │
              │                │  → detect cookies      │
              │                │  → save session.json   │
              │                └────────┬──────────────┘
              │                         │
              ├─────────────────────────┘
              │
     ┌────────▼──────────────┐
     │   start_monitoring     │
     │   (background thread)  │
     └────────┬──────────────┘
              │
     ┌────────▼──────────────────┐
     │  Playwright Browser       │
     │  (headless=True, persist) │
     │  inject cookies           │
     └────────┬──────────────────┘
              │
              │  ◄── every 1 min ──┐
              │                    │
     ┌────────▼──────────────────┐ │
     │  Claude API calls         │ │
     │                           │ │
     │  1. GET /api/organizations│ │
     │     → get org_id (cached) │ │
     │                           │ │
     │  2. GET /api/organizations│ │
     │     /{org_id}/usage       │ │
     │     → usage JSON response │ │
     └────────┬──────────────────┘ │
              │                    │
     ┌────────▼──────────────────┐ │
     │  Parse usage data         │ │
     │                           │ │
     │  • five_hour              │ │
     │    → current session %    │ │
     │  • seven_day              │ │
     │    → weekly all models %  │ │
     │  • seven_day_sonnet       │ │
     │    → weekly sonnet %      │ │
     └────────┬──────────────────┘ │
              │                    │
     ┌────────▼──────────────────┐ │
     │  Dashboard GUI            │ │
     │                           │ │
     │  ┌──────────────────────┐ │ │
     │  │ Current Session      │ │ │
     │  │ ██████░░░░ 58%       │ │ │
     │  │ Resets in 2h 30m     │ │ │
     │  ├──────────────────────┤ │ │
     │  │ Weekly All Models    │ │ │
     │  │ ████░░░░░░ 42%       │ │ │
     │  ├──────────────────────┤ │ │
     │  │ Weekly Sonnet        │ │ │
     │  │ ███░░░░░░░ 31%       │ │ │
     │  └──────────────────────┘ │ │
     └────────┬──────────────────┘ │
              │                    │
              └── wait 1 min ──────┘
```

### Why Playwright + Chromium?

Claude.ai is protected by Cloudflare, which blocks simple HTTP requests (e.g. Python `requests` library). A real browser engine (Chromium) is needed to bypass Cloudflare, and Playwright controls that browser programmatically.

| | **Playwright** | **Chromium** |
|---|---|---|
| **Role** | Browser automation library (the driver) | Actual browser engine (the car) |
| **Login** | Opens Chromium with UI, extracts cookies after user signs in | Renders claude.ai, passes Cloudflare |
| **Usage scraping** | Launches headless Chromium, injects cookies, calls API | Executes the actual HTTP requests |

## Project Structure

```
Oh-My-ClaudeUsage/
├── main.py                    # Main application
├── gui/
│   ├── dashboard.py           # Dashboard (view modes, opacity, pin)
│   └── login.py               # Login window
├── scraper/
│   ├── auth.py                # Authentication & session management
│   └── usage_playwright.py    # Playwright-based usage scraper
├── config/
│   └── session.json           # Saved session (auto-generated)
└── requirements.txt
```
