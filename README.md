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
python -m playwright install chromium
```

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

If you find this project useful, please consider giving it a star on GitHub. It helps others discover the project and motivates further development.

### Subsequent runs

The saved session is loaded automatically and the dashboard is displayed immediately.

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
