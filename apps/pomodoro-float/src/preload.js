const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('pomodoroNative', {
  getNativeSettings: () => ipcRenderer.invoke('settings:get-native'),
  updateNativeSettings: (settings) => ipcRenderer.send('settings:update-native', settings),
  minimize: () => ipcRenderer.send('window:minimize'),
  hide: () => ipcRenderer.send('window:hide'),
  quit: () => ipcRenderer.send('window:quit'),
  notify: (payload) => ipcRenderer.send('timer:notify', payload),
  onTimerCommand: (callback) => ipcRenderer.on('timer-command', (_event, command) => callback(command)),
  onNativeSettings: (callback) => ipcRenderer.on('native-settings', (_event, settings) => callback(settings)),
});
