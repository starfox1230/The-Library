# Xbox Couch Controller

A Windows desktop helper for couch control. JoyToKey remains responsible for controller-to-mouse and ordinary key output; this app replaces the AutoHotkey function-key layer with a tray app and radial menu.

- Responds to JoyToKey's F9/F10 output.
- Shows a modern dark radial menu.
- Hides and constrains the mouse while radial navigation is open.
- Lives in the system tray with Show, Pause, and Quit commands.
- Can be installed into Windows startup.

## Install

```powershell
cd "C:\Users\sterl\OneDrive\Documents\GitHub\The-Library\apps\xbox-couch-controller"
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Run

```powershell
.\.venv\Scripts\python.exe .\xbox_couch_controller.py
```

## Start With Windows

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\sterl\OneDrive\Documents\GitHub\The-Library\apps\xbox-couch-controller\install-startup.ps1"
```

That creates a Startup-folder shortcut named `Xbox Couch Controller.lnk`.

## Controls

| JoyToKey output | App effect |
| --- | --- |
| F9 | Open/close radial menu |
| F10 | Send `1` if Anki is active; otherwise send Backspace |
| Ctrl+Alt+F9 | Emergency close radial menu |
| F3 | Pass through unchanged |

JoyToKey still owns mouse movement, left click, Space, 4, 2, Ctrl+Z, P, Ctrl+4, Ctrl+Shift+4, Ctrl+Shift+5, and the other non-function-key mappings in `Xbox Anki.cfg`.

The radial menu contains Paste, Copy, Backspace, Period, and Ctrl+F3. While it is open, JoyToKey can still move the cursor, but this app hides it and constrains it to the radial circle. Click to choose the selected option, or press F9 again to close it.
