# Pomodoro Float

A small Electron Pomodoro timer designed to live as a polished floating desktop window.

## Features

- Frameless translucent floating window
- Lightweight WebGL night-mode background
- Global `Ctrl+Shift+P` show/hide shortcut
- Tray menu with show, start/pause, reset, always-on-top, launch-at-login, and quit
- Always-on-top toggle
- Mini mode
- Focus, short break, and long break durations
- Configurable rounds before long break
- Optional auto-start of the next session
- Night-mode color themes and UI scale control
- Local persistence for settings and daily stats

## Run

```powershell
cd C:\Users\sterl\OneDrive\Documents\GitHub\The-Library\apps\pomodoro-float
npm install
npm start
```

## Start Automatically With Windows

The app also toggles login startup from inside its settings. For a direct Windows Startup folder shortcut, run:

```powershell
cd C:\Users\sterl\OneDrive\Documents\GitHub\The-Library\apps\pomodoro-float
npm run install-startup
```

Remove that shortcut with:

```powershell
cd C:\Users\sterl\OneDrive\Documents\GitHub\The-Library\apps\pomodoro-float
npm run remove-startup
```
