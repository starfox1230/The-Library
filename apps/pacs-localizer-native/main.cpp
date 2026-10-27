#ifndef UNICODE
#define UNICODE
#endif
#ifndef _UNICODE
#define _UNICODE
#endif
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <shellapi.h>
#include <atomic>
#include <algorithm>
#include "engine.h"

namespace {
constexpr UINT EVENT_DOWN = WM_APP+1, EVENT_UP = WM_APP+2, EVENT_CTRL_UP = WM_APP+3;
constexpr UINT TRAY = WM_APP+4, QUIT_APP = 100, PAUSE_APP = 101, ABOUT_APP = 102;
constexpr ULONG_PTR OUR_INPUT = 0x50414353;
constexpr wchar_t TITLE[] = L"PACS Localizer Native";
HWND window = nullptr, target = nullptr;
HHOOK mouseHook = nullptr, keyboardHook = nullptr;
HANDLE hookReady = nullptr, hookThread = nullptr;
DWORD hookThreadId = 0;
std::atomic<bool> paused{false}, rightHeld{false}, ctrlLeft{false}, ctrlRight{false};
std::atomic<bool> hooksOK{false}, inputFailed{false};
bool quitting = false, timerRunning = false, cursorOn = false;
NOTIFYICONDATAW tray{};
UINT taskbarCreated = 0;
constexpr DWORD cursorIds[] = {32512,32513,32514,32515,32516,32640,32641,32642,
                              32643,32644,32645,32646,32648,32649,32650,32651};
HCURSOR crossCopies[16]{};

void PrepareCursors() {
    HCURSOR cross = LoadCursorW(nullptr, IDC_CROSS);
    for (auto& copy : crossCopies) {
        if (copy) DestroyCursor(copy);
        copy = static_cast<HCURSOR>(CopyImage(cross, IMAGE_CURSOR, 0, 0, 0));
    }
}
void Cursor(bool on) {
    if (on == cursorOn) return;
    cursorOn = on;
    if (on) {
        for (unsigned i=0;i<16;++i) {
            if (crossCopies[i]) {
                if (SetSystemCursor(crossCopies[i], cursorIds[i])) crossCopies[i] = nullptr;
            }
        }
    } else {
        SystemParametersInfoW(SPI_SETCURSORS, 0, nullptr, 0);
        PrepareCursors();
    }
}
INPUT Key(WORD vk, bool down) {
    INPUT input{}; input.type=INPUT_KEYBOARD;
    input.ki.wVk=vk; input.ki.dwFlags=down ? 0 : KEYEVENTF_KEYUP;
    if (vk==VK_RCONTROL || vk==VK_RMENU || vk==VK_LWIN || vk==VK_RWIN)
        input.ki.dwFlags |= KEYEVENTF_EXTENDEDKEY;
    input.ki.dwExtraInfo=OUR_INPUT; return input;
}
// A single ordered batch temporarily releases modifiers and restores them.
// It never sends mouse movement/wheel events or blocks physical movement.
void Inject(INPUT event) {
    INPUT batch[18]{}; WORD restore[8]{}; unsigned count=0, held=0;
    constexpr WORD modifiers[] = {VK_LCONTROL,VK_RCONTROL,VK_LSHIFT,VK_RSHIFT,
                                 VK_LMENU,VK_RMENU,VK_LWIN,VK_RWIN};
    for (WORD vk : modifiers) {
        bool down = vk==VK_LCONTROL ? ctrlLeft.load() :
                    vk==VK_RCONTROL ? ctrlRight.load() : (GetAsyncKeyState(vk)&0x8000)!=0;
        if (down) { batch[count++]=Key(vk,false); restore[held++]=vk; }
    }
    batch[count++]=event;
    for (unsigned i=0;i<held;++i) batch[count++]=Key(restore[i],true);
    if (SendInput(count,batch,sizeof(INPUT)) != count) inputFailed=true;
}
struct NativeOutput : Output {
    bool f12Down = false, leftDown = false;
    void key(bool down) override {
        // Do not send F12 into a different application after a focus change.
        if (down && (GetForegroundWindow()!=target || inputFailed)) return;
        if (!down && !f12Down) return;
        Inject(Key(VK_F12,down)); f12Down=down;
    }
    void left(bool down) override {
        if (down && (GetForegroundWindow()!=target || inputFailed || !rightHeld)) return;
        if (!down && !leftDown) return;
        INPUT input{}; input.type=INPUT_MOUSE;
        input.mi.dwFlags=down ? MOUSEEVENTF_LEFTDOWN : MOUSEEVENTF_LEFTUP;
        input.mi.dwExtraInfo=OUR_INPUT;
        Inject(input); leftDown=down;
    }
    void cursor(bool on) override { Cursor(on && leftDown); }
    void release() {
        // Key-up must still be attempted after an injection failure.
        if (leftDown) left(false);
        if (f12Down) key(false);
        Cursor(false);
    }
} output;
Engine engine(output);

// Dedicated hook thread: no sleeps, cursor changes, input injection or disk I/O.
LRESULT CALLBACK MouseProc(int code, WPARAM message, LPARAM data) {
    if (code==HC_ACTION) {
        const auto* event=reinterpret_cast<MSLLHOOKSTRUCT*>(data);
        if (!(event->flags & LLMHF_INJECTED)) {
            if (message==WM_RBUTTONDOWN && !paused && (ctrlLeft || ctrlRight)) {
                if (!rightHeld.exchange(true)) PostMessageW(window,EVENT_DOWN,0,0);
                return 1;
            }
            if (message==WM_RBUTTONUP && rightHeld.exchange(false)) {
                PostMessageW(window,EVENT_UP,0,0); return 1;
            }
        }
    }
    return CallNextHookEx(nullptr,code,message,data);
}
LRESULT CALLBACK KeyboardProc(int code, WPARAM message, LPARAM data) {
    if (code==HC_ACTION) {
        const auto* event=reinterpret_cast<KBDLLHOOKSTRUCT*>(data);
        if (!(event->flags & LLKHF_INJECTED)) {
            bool down=message==WM_KEYDOWN || message==WM_SYSKEYDOWN;
            if (event->vkCode==VK_LCONTROL) ctrlLeft=down;
            if (event->vkCode==VK_RCONTROL) ctrlRight=down;
            if ((event->vkCode==VK_LCONTROL || event->vkCode==VK_RCONTROL) &&
                !down && !ctrlLeft && !ctrlRight) PostMessageW(window,EVENT_CTRL_UP,0,0);
        }
    }
    return CallNextHookEx(nullptr,code,message,data);
}
DWORD WINAPI HookLoop(void*) {
    MSG message{}; PeekMessageW(&message,nullptr,0,0,PM_NOREMOVE);
    ctrlLeft=(GetAsyncKeyState(VK_LCONTROL)&0x8000)!=0;
    ctrlRight=(GetAsyncKeyState(VK_RCONTROL)&0x8000)!=0;
    mouseHook=SetWindowsHookExW(WH_MOUSE_LL,MouseProc,GetModuleHandleW(nullptr),0);
    keyboardHook=SetWindowsHookExW(WH_KEYBOARD_LL,KeyboardProc,GetModuleHandleW(nullptr),0);
    hooksOK=mouseHook && keyboardHook;
    SetEvent(hookReady);
    if (hooksOK) while (GetMessageW(&message,nullptr,0,0)>0) {
        TranslateMessage(&message); DispatchMessageW(&message);
    }
    if (mouseHook) UnhookWindowsHookEx(mouseHook);
    if (keyboardHook) UnhookWindowsHookEx(keyboardHook);
    return 0;
}
void AddTray() {
    tray.cbSize=sizeof(tray); tray.hWnd=window; tray.uID=1;
    tray.uFlags=NIF_ICON|NIF_MESSAGE|NIF_TIP; tray.uCallbackMessage=TRAY;
    tray.hIcon=LoadIconW(nullptr,IDI_APPLICATION);
    lstrcpynW(tray.szTip,paused ? L"PACS Localizer Native (paused)" : TITLE,128);
    Shell_NotifyIconW(NIM_ADD,&tray);
}
void Schedule() {
    bool need=engine.needsTimer() || quitting;
    if (need && !timerRunning) timerRunning=SetTimer(window,1,10,nullptr)!=0;
    if (!need && timerRunning) { KillTimer(window,1); timerRunning=false; }
    if (need && !timerRunning) {
        paused=true; output.release();
        MessageBoxW(window,L"Windows could not start the input timer. The app will close.",TITLE,MB_ICONERROR);
        PostQuitMessage(1);
    }
}
void Quit() {
    paused=true; quitting=true; engine.cancel(GetTickCount64()); Schedule();
}
void Menu() {
    HMENU menu=CreatePopupMenu();
    AppendMenuW(menu,MF_STRING,PAUSE_APP,paused ? L"Resume" : L"Pause");
    AppendMenuW(menu,MF_STRING,ABOUT_APP,L"Controls / About");
    AppendMenuW(menu,MF_SEPARATOR,0,nullptr);
    AppendMenuW(menu,MF_STRING,QUIT_APP,L"Exit");
    POINT point{}; GetCursorPos(&point); SetForegroundWindow(window);
    UINT command=TrackPopupMenu(menu,TPM_RETURNCMD|TPM_RIGHTBUTTON,point.x,point.y,0,window,nullptr);
    DestroyMenu(menu); PostMessageW(window,WM_NULL,0,0);
    if (command) PostMessageW(window,WM_COMMAND,command,0);
}
LRESULT CALLBACK WindowProc(HWND hwnd, UINT message, WPARAM wParam, LPARAM lParam) {
    uint64_t now=GetTickCount64();
    if (taskbarCreated && message==taskbarCreated) { AddTray(); return 0; }
    switch (message) {
    case EVENT_DOWN:
        if (!paused) {
            if (engine.idle() && engine.gesture==Engine::Gesture::None) target=GetForegroundWindow();
            engine.down(now);
        }
        else engine.cancel(now);
        Schedule(); return 0;
    case EVENT_UP: engine.up(now); Schedule(); return 0;
    case EVENT_CTRL_UP: engine.ctrlUp(now); Schedule(); return 0;
    case WM_TIMER:
        if (!engine.idle() && GetForegroundWindow()!=target) engine.cancel(now);
        // Recover when a release was missed (secure desktop/session transition).
        if (engine.gesture!=Engine::Gesture::None && !rightHeld) engine.up(now);
        engine.tick(now);
        if (inputFailed.exchange(false)) {
            paused=true; engine.cancel(now); output.release();
            tray.uFlags=NIF_INFO;
            lstrcpynW(tray.szInfoTitle,L"Input was blocked; localizer paused",64);
            lstrcpynW(tray.szInfo,L"If PACS runs as administrator, run this app at the same permission level. Right-click its tray icon to resume.",256);
            tray.dwInfoFlags=NIIF_WARNING; Shell_NotifyIconW(NIM_MODIFY,&tray);
            tray.uFlags=NIF_ICON|NIF_MESSAGE|NIF_TIP;
        }
        if (quitting && engine.idle() && !rightHeld) { DestroyWindow(hwnd); return 0; }
        Schedule(); return 0;
    case WM_HOTKEY: Quit(); return 0;
    case TRAY:
        if (lParam==WM_RBUTTONUP || lParam==WM_CONTEXTMENU) Menu();
        if (lParam==WM_LBUTTONDBLCLK) PostMessageW(hwnd,WM_COMMAND,ABOUT_APP,0);
        return 0;
    case WM_COMMAND:
        if (LOWORD(wParam)==QUIT_APP) Quit();
        if (LOWORD(wParam)==PAUSE_APP && !quitting) {
            paused=!paused; engine.cancel(now); Schedule();
            lstrcpynW(tray.szTip,paused ? L"PACS Localizer Native (paused)" : TITLE,128);
            Shell_NotifyIconW(NIM_MODIFY,&tray);
        }
        if (LOWORD(wParam)==ABOUT_APP) MessageBoxW(hwnd,
            L"PACS Localizer Native 1.0.0\n\n"
            L"Ctrl + right-button hold (140 ms): F12, then left-button hold.\n"
            L"Release right button or Ctrl: release left button, then F12.\n"
            L"Ctrl + right-button double tap (500 ms): one F12 press.\n\n"
            L"Ctrl + Alt + F12: exit. Right-click tray icon: pause or exit.\n\n"
            L"Close your old AHK localizer before using this app.\n"
            L"No installer, AutoHotkey, or .NET required.\n"
            L"Optional PACSLocalizer.ini beside the EXE controls timings.\n\n"
            L"Native C++ / Win32. PACS/Citrix behavior still needs local testing.",TITLE,MB_OK|MB_ICONINFORMATION);
        return 0;
    case WM_CLOSE: Quit(); return 0;
    case WM_QUERYENDSESSION: output.release(); return TRUE;
    case WM_ENDSESSION: if (wParam) { output.release(); PostQuitMessage(0); } return 0;
    case WM_DESTROY: PostQuitMessage(0); return 0;
    default: return DefWindowProcW(hwnd,message,wParam,lParam);
    }
}
void LoadSettings() {
    wchar_t path[32768]{}; GetModuleFileNameW(nullptr,path,32768);
    wchar_t* slash=wcsrchr(path,L'\\');
    if (!slash) return;
    *(slash+1)=0; lstrcatW(path,L"PACSLocalizer.ini");
    auto read=[&](const wchar_t* key,unsigned fallback,unsigned low,unsigned high) {
        return std::clamp(GetPrivateProfileIntW(L"Localizer",key,fallback,path),low,high);
    };
    engine.settings.holdMs=read(L"HoldMs",140,30,2000);
    engine.settings.doubleTapMs=read(L"DoubleTapMs",500,100,2000);
    engine.settings.keyPulseMs=read(L"KeyPulseMs",25,10,200);
    engine.settings.toolSettleMs=read(L"ToolSettleMs",75,0,1000);
    engine.settings.releaseGapMs=read(L"ReleaseGapMs",10,0,200);
    engine.settings.crosshair=read(L"Crosshair",1,0,1)!=0;
}
} // namespace

int WINAPI wWinMain(HINSTANCE instance,HINSTANCE,PWSTR,int) {
    HANDLE singleton=CreateMutexW(nullptr,FALSE,L"Local\\PACSLocalizerNative-v1");
    if (!singleton || GetLastError()==ERROR_ALREADY_EXISTS) {
        MessageBoxW(nullptr,L"PACS Localizer Native is already running. Check the system tray.",TITLE,MB_OK);
        if (singleton) CloseHandle(singleton);
        return 0;
    }
    SetProcessDPIAware(); LoadSettings(); PrepareCursors();
    WNDCLASSW wc{}; wc.lpfnWndProc=WindowProc; wc.hInstance=instance;
    wc.lpszClassName=L"PACSLocalizerNativeWindow";
    if (!RegisterClassW(&wc)) return 1;
    window=CreateWindowExW(0,wc.lpszClassName,TITLE,0,0,0,0,0,nullptr,nullptr,instance,nullptr);
    if (!window) return 1;
    hookReady=CreateEventW(nullptr,TRUE,FALSE,nullptr);
    if (hookReady) hookThread=CreateThread(nullptr,0,HookLoop,nullptr,0,&hookThreadId);
    if (!hookReady || !hookThread || WaitForSingleObject(hookReady,5000)!=WAIT_OBJECT_0 || !hooksOK) {
        MessageBoxW(nullptr,L"Windows could not install the input hooks. No shortcuts were activated.",TITLE,MB_ICONERROR);
        return 1;
    }
    taskbarCreated=RegisterWindowMessageW(L"TaskbarCreated"); AddTray();
    RegisterHotKey(window,1,MOD_CONTROL|MOD_ALT|MOD_NOREPEAT,VK_F12);
    MSG message{}; int result;
    while ((result=GetMessageW(&message,nullptr,0,0))>0) {
        TranslateMessage(&message); DispatchMessageW(&message);
    }
    paused=true;
    PostThreadMessageW(hookThreadId,WM_QUIT,0,0);
    WaitForSingleObject(hookThread,5000);
    output.release();
    Shell_NotifyIconW(NIM_DELETE,&tray); UnregisterHotKey(window,1);
    for (auto cursor : crossCopies) if (cursor) DestroyCursor(cursor);
    CloseHandle(hookThread); CloseHandle(hookReady); CloseHandle(singleton);
    return result<0 ? 1 : 0;
}
