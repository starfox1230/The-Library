const { app, BrowserWindow, Tray, Menu, ipcMain, globalShortcut, nativeImage, Notification, screen } = require('electron');
const path = require('path');

const HOTKEY = 'CommandOrControl+Shift+P';

let mainWindow;
let tray;
let currentSettings = {
  alwaysOnTop: true,
  launchAtLogin: true,
  miniMode: false,
  scale: 1,
};

const getAssetPath = (...parts) => path.join(__dirname, '..', 'assets', ...parts);

function createTrayIcon() {
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32">
      <defs>
        <linearGradient id="g" x1="4" y1="4" x2="28" y2="28" gradientUnits="userSpaceOnUse">
          <stop stop-color="#81f7d8"/>
          <stop offset="1" stop-color="#8ba7ff"/>
        </linearGradient>
      </defs>
      <rect width="32" height="32" rx="9" fill="#111521"/>
      <circle cx="16" cy="16" r="10" fill="none" stroke="url(#g)" stroke-width="3"/>
      <path d="M16 9v7l4 3" fill="none" stroke="#f7fbff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>`;
  return nativeImage.createFromDataURL(`data:image/svg+xml;base64,${Buffer.from(svg).toString('base64')}`);
}

function buildTrayMenu() {
  const visible = mainWindow && mainWindow.isVisible();
  return Menu.buildFromTemplate([
    {
      label: visible ? 'Hide Pomodoro Float' : 'Show Pomodoro Float',
      click: toggleWindow,
    },
    {
      label: 'Start / Pause',
      click: () => mainWindow?.webContents.send('timer-command', 'toggle'),
    },
    {
      label: 'Reset Current Session',
      click: () => mainWindow?.webContents.send('timer-command', 'reset'),
    },
    { type: 'separator' },
    {
      label: 'Always on Top',
      type: 'checkbox',
      checked: Boolean(currentSettings.alwaysOnTop),
      click: (item) => setAlwaysOnTop(item.checked),
    },
    {
      label: 'Launch at Login',
      type: 'checkbox',
      checked: Boolean(currentSettings.launchAtLogin),
      click: (item) => setLaunchAtLogin(item.checked),
    },
    { type: 'separator' },
    { label: `Toggle: ${HOTKEY}`, enabled: false },
    { type: 'separator' },
    {
      label: 'Quit',
      click: () => {
        app.isQuitting = true;
        app.quit();
      },
    },
  ]);
}

function updateTray() {
  if (!tray) return;
  tray.setContextMenu(buildTrayMenu());
}

function windowBoundsForMode(settings = currentSettings) {
  const scale = Number(settings.scale) || 1;
  if (settings.miniMode) {
    return {
      width: Math.round(300 * Math.max(0.86, scale)),
      height: Math.round(152 * Math.max(0.9, scale)),
    };
  }
  return {
    width: Math.round(420 * scale),
    height: Math.round(640 * scale),
  };
}

function createWindow() {
  const { width, height } = windowBoundsForMode();
  const display = screen.getPrimaryDisplay();
  const x = Math.round(display.workArea.x + display.workArea.width - width - 28);
  const y = Math.round(display.workArea.y + 48);

  mainWindow = new BrowserWindow({
    width,
    height,
    x,
    y,
    minWidth: 260,
    minHeight: 128,
    frame: false,
    transparent: true,
    resizable: true,
    movable: true,
    show: false,
    alwaysOnTop: currentSettings.alwaysOnTop,
    skipTaskbar: false,
    title: 'Pomodoro Float',
    backgroundColor: '#00000000',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
    },
  });

  mainWindow.loadFile(path.join(__dirname, 'index.html'));

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    mainWindow.focus();
  });

  mainWindow.on('close', (event) => {
    if (!app.isQuitting) {
      event.preventDefault();
      mainWindow.hide();
      updateTray();
    }
  });

  mainWindow.on('show', updateTray);
  mainWindow.on('hide', updateTray);
}

function toggleWindow() {
  if (!mainWindow) return;
  if (mainWindow.isVisible()) {
    mainWindow.hide();
  } else {
    mainWindow.show();
    mainWindow.focus();
  }
  updateTray();
}

function setAlwaysOnTop(value) {
  currentSettings.alwaysOnTop = Boolean(value);
  mainWindow?.setAlwaysOnTop(currentSettings.alwaysOnTop, 'floating');
  mainWindow?.webContents.send('native-settings', currentSettings);
  updateTray();
}

function setLaunchAtLogin(value) {
  currentSettings.launchAtLogin = Boolean(value);
  app.setLoginItemSettings({
    openAtLogin: currentSettings.launchAtLogin,
    path: process.execPath,
    args: app.isPackaged ? [] : [path.join(__dirname, '..')],
  });
  mainWindow?.webContents.send('native-settings', currentSettings);
  updateTray();
}

function applySettings(settings) {
  currentSettings = { ...currentSettings, ...settings };
  setAlwaysOnTop(currentSettings.alwaysOnTop);
  setLaunchAtLogin(currentSettings.launchAtLogin);

  if (mainWindow) {
    const bounds = windowBoundsForMode(currentSettings);
    mainWindow.setMinimumSize(currentSettings.miniMode ? 260 : 340, currentSettings.miniMode ? 128 : 480);
    mainWindow.setSize(bounds.width, bounds.height, true);
  }
  updateTray();
}

function registerShortcuts() {
  globalShortcut.unregisterAll();
  globalShortcut.register(HOTKEY, toggleWindow);
}

app.whenReady().then(() => {
  app.setAppUserModelId('local.pomodoro-float');
  createWindow();
  tray = new Tray(createTrayIcon());
  tray.setToolTip(`Pomodoro Float (${HOTKEY})`);
  tray.on('click', toggleWindow);
  updateTray();
  registerShortcuts();
  setLaunchAtLogin(true);
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  } else {
    mainWindow?.show();
  }
});

app.on('will-quit', () => {
  globalShortcut.unregisterAll();
});

ipcMain.handle('settings:get-native', () => currentSettings);
ipcMain.on('settings:update-native', (_event, settings) => applySettings(settings));
ipcMain.on('window:minimize', () => mainWindow?.minimize());
ipcMain.on('window:hide', () => {
  mainWindow?.hide();
  updateTray();
});
ipcMain.on('window:quit', () => {
  app.isQuitting = true;
  app.quit();
});
ipcMain.on('timer:notify', (_event, payload) => {
  if (!Notification.isSupported()) return;
  new Notification({
    title: payload?.title || 'Pomodoro Float',
    body: payload?.body || 'Session complete.',
    icon: getAssetPath('icon.svg'),
    silent: false,
  }).show();
});
