#ifndef UNICODE
#define UNICODE
#endif
#ifndef _UNICODE
#define _UNICODE
#endif
#define NOMINMAX
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <shellapi.h>
#include <objidl.h>
#include <gdiplus.h>
#include <atomic>
#include <algorithm>
#include <cmath>
#include <cwchar>
#include <string>
#include "engine.h"

namespace {
constexpr wchar_t TITLE[]=L"PACS Precision Scroll Native";
constexpr UINT MIDDLE=WM_APP+1, RELEASE=WM_APP+2, SPEED=WM_APP+3, DIR=WM_APP+4;
constexpr UINT STOP=WM_APP+5, TIP=WM_APP+6, STATE=WM_APP+7, ACTIVATE=WM_APP+8, DEBUG_APP=WM_APP+9, TRAY=WM_APP+10;
constexpr ULONG_PTR TAG=0x5343524C;
constexpr UINT EXIT=100, PAUSE=101, ABOUT=102;
using Mode=ScrollEngine::Mode;
HWND mainWindow{}, ringWindow{}, tipWindow{};
HANDLE workerThread{}, hookThread{}, workerReady{}, hookReady{};
DWORD workerId{}, hookId{};
std::atomic<int> mode{0};
std::atomic<bool> paused{false}, middleHeld{false}, hooksOK{false};
std::atomic<bool> physical[256]{}, blocked[256]{};
std::atomic<double> holdStart{0};
std::atomic<bool> shuttingDown{false};
LARGE_INTEGER frequency{};
NOTIFYICONDATAW tray{};
UINT taskbarCreated{};
ULONG_PTR gdipToken{};
std::wstring tipText;
HDC ringDC{}; HBITMAP ringBitmap{}; HGDIOBJ oldBitmap{}; void* ringBits{};
Gdiplus::Bitmap* canvas{};
bool workerTimerOK=true;

double Now() { LARGE_INTEGER t{}; QueryPerformanceCounter(&t); return 1000.0*static_cast<double>(t.QuadPart)/static_cast<double>(frequency.QuadPart); }
bool Ctrl() { return physical[VK_LCONTROL] || physical[VK_RCONTROL]; }
bool Alt() { return physical[VK_LMENU] || physical[VK_RMENU]; }
void Command(UINT message,WPARAM w=0) { PostThreadMessageW(workerId,message,w,0); }
void Notice(const wchar_t* text,int duration=900) {
    // Ownership is transferred to the UI, so no shared text buffer races.
    auto* copy=new std::wstring(text);
    if (!PostMessageW(mainWindow,TIP,static_cast<WPARAM>(duration),reinterpret_cast<LPARAM>(copy))) delete copy;
}
void Publish(const ScrollEngine& e) {
    holdStart=e.holdStart; mode=static_cast<int>(e.mode);
    PostMessageW(mainWindow,STATE,0,0);
}
std::wstring RateText(const ScrollEngine& e) {
    wchar_t text[64]{}; swprintf(text,64,L"%g/s",ScrollEngine::rates[e.rateIndex]); return text;
}
void SpeedTip(const ScrollEngine& e) {
    if (e.mode==Mode::Auto) { auto text=RateText(e); Notice(text.c_str(),650); }
    else {
        auto text=L"Sensitivity: "+std::to_wstring(e.sensitivity);
        if(e.sensitivity==43)text+=L" (default)";
        Notice(text.c_str());
    }
}
HWND FindTarget() {
    HWND result{};
    EnumWindows([](HWND hwnd,LPARAM data)->BOOL {
        if(!IsWindowVisible(hwnd))return TRUE;
        wchar_t title[1024]{}; GetWindowTextW(hwnd,title,1024);
        if(wcsstr(title,L"VirtualMonitor")) { *reinterpret_cast<HWND*>(data)=hwnd; return FALSE; }
        return TRUE;
    },reinterpret_cast<LPARAM>(&result));
    return result;
}
INPUT Key(WORD vk,bool down) {
    INPUT i{}; i.type=INPUT_KEYBOARD; i.ki.wVk=vk; i.ki.dwExtraInfo=TAG;
    i.ki.dwFlags=down?0:KEYEVENTF_KEYUP;
    if(vk==VK_RCONTROL||vk==VK_RMENU||vk==VK_LWIN||vk==VK_RWIN)i.ki.dwFlags|=KEYEVENTF_EXTENDEDKEY;
    return i;
}
bool SendWheel(int direction) {
    INPUT batch[17]{}; WORD restore[8]{}; unsigned count=0,n=0;
    constexpr WORD modifiers[]={VK_LCONTROL,VK_RCONTROL,VK_LSHIFT,VK_RSHIFT,VK_LMENU,VK_RMENU,VK_LWIN,VK_RWIN};
    for(WORD vk:modifiers)if(physical[vk]&&!blocked[vk]) {batch[count++]=Key(vk,false);restore[n++]=vk;}
    INPUT wheel{}; wheel.type=INPUT_MOUSE; wheel.mi.dwFlags=MOUSEEVENTF_WHEEL;
    wheel.mi.mouseData=static_cast<DWORD>(direction*WHEEL_DELTA); wheel.mi.dwExtraInfo=TAG;
    batch[count++]=wheel;
    for(unsigned j=0;j<n;++j)batch[count++]=Key(restore[j],physical[restore[j]]&&!blocked[restore[j]]);
    if(SendInput(count,batch,sizeof(INPUT))==count)return true;
    // Recover only passed-through physical modifiers if a batch was partially inserted.
    INPUT recovery[8]{};
    for(unsigned j=0;j<n;++j)recovery[j]=Key(restore[j],physical[restore[j]]&&!blocked[restore[j]]);
    if(n)SendInput(n,recovery,sizeof(INPUT));
    return false;
}
DWORD WINAPI Worker(void*) {
    MSG message{}; PeekMessageW(&message,nullptr,0,0,PM_NOREMOVE);
    HANDLE timer=CreateWaitableTimerExW(nullptr,nullptr,0x2,TIMER_ALL_ACCESS);
    if(!timer)timer=CreateWaitableTimerW(nullptr,FALSE,nullptr);
    workerTimerOK=timer!=nullptr;
    SetEvent(workerReady);
    if(!timer)return 1;
    ScrollEngine e;
    double nextSample=ScrollEngine::never;
    bool done=false;
    while(!done) {
        while(PeekMessageW(&message,nullptr,0,0,PM_REMOVE)) {
            double now=Now(); auto before=e.mode;
            if(message.message==WM_QUIT){done=true;break;}
            if(message.message==STOP)e.stop();
            if(message.message==MIDDLE&&!paused) {
                bool ctrl=message.wParam!=0;
                if((ctrl&&before!=Mode::Auto)||(!ctrl&&before!=Mode::Auto&&before!=Mode::Precision))
                    PostMessageW(mainWindow,ACTIVATE,0,0);
                e.middle(ctrl,now);
                if(e.mode==Mode::Auto) { auto text=L"Auto-Scroll ON\n"+RateText(e); Notice(text.c_str()); }
                else if(e.mode==Mode::Off)Notice(before==Mode::Auto?L"Auto-Scroll OFF":L"Scroll OFF",700);
            }
            if(message.message==RELEASE)e.release();
            if(message.message==SPEED) {e.speed(message.wParam==1?1:-1,now);if(e.mode==Mode::Auto||e.mode==Mode::Precision)SpeedTip(e);}
            if(message.message==DIR)e.wheelDirection(message.wParam==1?1:-1,now);
            if(before!=e.mode)Publish(e);
        }
        if(done)break;
        double now=Now();
        if(paused||shuttingDown) {if(e.mode!=Mode::Off){e.stop();Publish(e);}}
        if(e.mode==Mode::Hold) {
            if(!middleHeld) {e.release();Publish(e);}
            else if(now-e.holdStart>=300) {
                POINT p{};
                if(GetCursorPos(&p)&&e.launch(now,p.y)) {
                    nextSample=now+10; Publish(e); PostMessageW(mainWindow,ACTIVATE,0,0);
                    auto text=L"Scroll ON | Sensitivity: "+std::to_wstring(e.sensitivity);
                    if(e.sensitivity==43)text+=L" (default)";
                    Notice(text.c_str());
                }
            }
        }
        if(e.mode==Mode::Precision&&now>=nextSample) {
            POINT p{};
            if(!GetCursorPos(&p)){e.stop();Publish(e);}
            else {
                // Same 100px edge margin and 10ms samples. Use the current monitor
                // so infinite wrapping also works on monitors with negative origins.
                MONITORINFO info{}; info.cbSize=sizeof(info);
                GetMonitorInfoW(MonitorFromPoint(p,MONITOR_DEFAULTTONEAREST),&info);
                const RECT& r=info.rcMonitor;
                if(p.y<r.top+100||p.y>r.bottom-100) {
                    int center=(r.top+r.bottom)/2;
                    if(SetCursorPos(p.x,center))e.lastY=center;
                    else {e.stop();Publish(e);}
                } else e.sample(p.y,now);
            }
            nextSample=now+10;
        }
        int direction=0;
        if(e.emit(now,direction)&&!SendWheel(direction)) {
            e.stop();paused=true;Publish(e);
            Notice(L"Wheel input blocked. Paused. Run at the same permission level as PACS.",4000);
        }
        double deadline=e.deadline();
        if(e.mode==Mode::Precision)deadline=std::min(deadline,nextSample);
        HANDLE handles[]={timer};
        if(std::isfinite(deadline)) {
            LARGE_INTEGER relative{};
            relative.QuadPart=-std::max<LONGLONG>(1,static_cast<LONGLONG>((deadline-Now())*10000.0));
            if(!SetWaitableTimer(timer,&relative,0,nullptr,nullptr,FALSE)) {
                paused=true;e.stop();Publish(e);Notice(L"Scroll timer failed. Paused.",4000);
                deadline=ScrollEngine::never;
            }
        } else CancelWaitableTimer(timer);
        DWORD result=MsgWaitForMultipleObjects(std::isfinite(deadline)?1:0,handles,FALSE,INFINITE,QS_ALLINPUT);
        if(result==WAIT_FAILED){e.stop();paused=true;Publish(e);break;}
    }
    mode=0;CancelWaitableTimer(timer);CloseHandle(timer);return 0;
}
LRESULT CALLBACK MouseHook(int code,WPARAM kind,LPARAM data) {
    if(code==HC_ACTION) {
        auto* event=reinterpret_cast<MSLLHOOKSTRUCT*>(data);
        if(!(event->flags&LLMHF_INJECTED)) {
            if(kind==WM_MBUTTONDOWN&&!paused) {middleHeld=true;Command(MIDDLE,Ctrl()?1:0);return 1;}
            if(kind==WM_MBUTTONUP&&middleHeld.exchange(false)) {Command(RELEASE);return 1;}
            if(kind==WM_MOUSEWHEEL) {
                int d=static_cast<short>(HIWORD(event->mouseData))>0?1:-1;
                Command(DIR,d==1?1:0);
                if(mode==static_cast<int>(Mode::Auto)&&!paused)return 1;
            }
        }
    }
    return CallNextHookEx(nullptr,code,kind,data);
}
LRESULT CALLBACK KeyboardHook(int code,WPARAM kind,LPARAM data) {
    if(code==HC_ACTION) {
        auto* event=reinterpret_cast<KBDLLHOOKSTRUCT*>(data);
        if(!(event->flags&LLKHF_INJECTED)&&event->vkCode<256) {
            unsigned vk=event->vkCode; bool down=kind==WM_KEYDOWN||kind==WM_SYSKEYDOWN;
            bool was=physical[vk].exchange(down);
            bool active=!paused&&(mode==static_cast<int>(Mode::Auto)||mode==static_cast<int>(Mode::Precision));
            bool speedKey=vk==VK_LCONTROL||vk==VK_RCONTROL||vk==VK_LSHIFT||vk==VK_RSHIFT;
            bool arrow=mode==static_cast<int>(Mode::Auto)&&(vk==VK_UP||vk==VK_DOWN);
            bool debug=vk=='3'&&Ctrl()&&Alt();
            bool panic=vk==VK_F12&&Ctrl()&&Alt();
            if(down&&!was)blocked[vk]=debug||panic||(active&&(speedKey||arrow));
            if(blocked[vk]) {
                if(down) {
                    if(panic) {if(!was)PostMessageW(mainWindow,WM_COMMAND,PAUSE,0);}
                    else if(debug)PostMessageW(mainWindow,DEBUG_APP,0,0);
                    else if(active&&speedKey)Command(SPEED,(vk==VK_LSHIFT||vk==VK_RSHIFT)?1:0);
                    else if(active&&arrow)Command(DIR,vk==VK_UP?1:0);
                } else blocked[vk]=false;
                return 1;
            }
        }
    }
    return CallNextHookEx(nullptr,code,kind,data);
}
DWORD WINAPI Hooks(void*) {
    MSG message{};PeekMessageW(&message,nullptr,0,0,PM_NOREMOVE);
    for(unsigned i=0;i<256;++i)physical[i]=(GetAsyncKeyState(static_cast<int>(i))&0x8000)!=0;
    HHOOK mouse=SetWindowsHookExW(WH_MOUSE_LL,MouseHook,GetModuleHandleW(nullptr),0);
    HHOOK keyboard=SetWindowsHookExW(WH_KEYBOARD_LL,KeyboardHook,GetModuleHandleW(nullptr),0);
    hooksOK=mouse&&keyboard;SetEvent(hookReady);
    if(hooksOK)while(GetMessageW(&message,nullptr,0,0)>0){TranslateMessage(&message);DispatchMessageW(&message);}
    if(mouse)UnhookWindowsHookEx(mouse);
    if(keyboard)UnhookWindowsHookEx(keyboard);
    return 0;
}
void DrawRing() {
    POINT p{}; if(!GetCursorPos(&p))return;
    double progress=std::clamp((Now()-holdStart.load())/300.0,0.0,1.0);
    Gdiplus::Graphics g(canvas);g.SetSmoothingMode(Gdiplus::SmoothingModeAntiAlias);
    g.SetCompositingMode(Gdiplus::CompositingModeSourceCopy);g.Clear(Gdiplus::Color(0,0,0,0));
    g.SetCompositingMode(Gdiplus::CompositingModeSourceOver);
    Gdiplus::Pen base(Gdiplus::Color(255,42,42,42),6.0f);
    Gdiplus::Pen arc(Gdiplus::Color(255,static_cast<BYTE>(std::lround(255*(1-progress))),static_cast<BYTE>(std::lround(255*progress)),0),6.0f);
    g.DrawEllipse(&base,5,5,46,46);g.DrawArc(&arc,5,5,46,46,-90.0f,static_cast<float>(std::max(6.0,360*progress)));
    g.Flush(Gdiplus::FlushIntentionSync);
    POINT pos{p.x-28,p.y-28},src{0,0};SIZE size{56,56};BLENDFUNCTION blend{AC_SRC_OVER,0,255,AC_SRC_ALPHA};
    UpdateLayeredWindow(ringWindow,nullptr,&pos,&size,ringDC,&src,0,&blend,ULW_ALPHA);
    ShowWindow(ringWindow,SW_SHOWNOACTIVATE);
}
LRESULT CALLBACK OverlayProc(HWND hwnd,UINT msg,WPARAM w,LPARAM l) {
    if(msg==WM_NCHITTEST)return HTTRANSPARENT;
    if(msg==WM_MOUSEACTIVATE)return MA_NOACTIVATE;
    if(msg==WM_PAINT) {
        PAINTSTRUCT ps{};HDC dc=BeginPaint(hwnd,&ps);RECT r{};GetClientRect(hwnd,&r);
        HBRUSH bg=CreateSolidBrush(RGB(255,255,225));FillRect(dc,&r,bg);DeleteObject(bg);
        SetBkMode(dc,TRANSPARENT);SetTextColor(dc,RGB(0,0,0));
        auto old=SelectObject(dc,GetStockObject(DEFAULT_GUI_FONT));InflateRect(&r,-8,-5);
        DrawTextW(dc,tipText.c_str(),-1,&r,DT_LEFT|DT_NOPREFIX);SelectObject(dc,old);EndPaint(hwnd,&ps);return 0;
    }
    return DefWindowProcW(hwnd,msg,w,l);
}
void ShowTip(const std::wstring& text,int duration) {
    tipText=text;HDC dc=GetDC(tipWindow);auto old=SelectObject(dc,GetStockObject(DEFAULT_GUI_FONT));
    RECT rect{0,0,0,0};DrawTextW(dc,text.c_str(),-1,&rect,DT_CALCRECT|DT_NOPREFIX);SelectObject(dc,old);ReleaseDC(tipWindow,dc);
    POINT p{};GetCursorPos(&p);MONITORINFO info{};info.cbSize=sizeof(info);
    GetMonitorInfoW(MonitorFromPoint(p,MONITOR_DEFAULTTONEAREST),&info);
    int width=rect.right+16,height=rect.bottom+10;
    int x=std::clamp(p.x+16,info.rcWork.left,std::max(info.rcWork.left,info.rcWork.right-width));
    int y=std::clamp(p.y+20,info.rcWork.top,std::max(info.rcWork.top,info.rcWork.bottom-height));
    SetWindowPos(tipWindow,HWND_TOPMOST,x,y,width,height,SWP_NOACTIVATE|SWP_SHOWWINDOW);InvalidateRect(tipWindow,nullptr,TRUE);
    SetTimer(mainWindow,2,static_cast<UINT>(duration),nullptr);
}
void AddTray() {
    tray.cbSize=sizeof(tray);tray.hWnd=mainWindow;tray.uID=1;tray.uFlags=NIF_ICON|NIF_MESSAGE|NIF_TIP;
    tray.uCallbackMessage=TRAY;tray.hIcon=LoadIconW(nullptr,IDI_APPLICATION);
    lstrcpynW(tray.szTip,TITLE,128);Shell_NotifyIconW(NIM_ADD,&tray);
}
void Debug() {
    HWND active=GetForegroundWindow();DWORD pid{};GetWindowThreadProcessId(active,&pid);
    wchar_t title[1024]{},path[32768]{};GetWindowTextW(active,title,1024);
    HANDLE process=OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION,FALSE,pid);DWORD size=32768;
    if(process){QueryFullProcessImageNameW(process,0,path,&size);CloseHandle(process);}
    wchar_t* file=wcsrchr(path,L'\\');
    std::wstring text=L"Active App Details:\n\nEXE: ";text+=(file?file+1:path);text+=L"\nTitle: ";text+=title;
    MessageBoxW(mainWindow,text.c_str(),TITLE,MB_OK);
}
LRESULT CALLBACK WindowProc(HWND hwnd,UINT msg,WPARAM w,LPARAM l) {
    if(taskbarCreated&&msg==taskbarCreated){AddTray();return 0;}
    switch(msg) {
    case ACTIVATE: {HWND target=FindTarget();if(target){if(IsIconic(target))ShowWindow(target,SW_RESTORE);SetForegroundWindow(target);}return 0;}
    case DEBUG_APP:Debug();return 0;
    case TIP:{auto* text=reinterpret_cast<std::wstring*>(l);ShowTip(*text,static_cast<int>(w));delete text;return 0;}
    case STATE:
        if(mode==static_cast<int>(Mode::Hold)){DrawRing();SetTimer(hwnd,1,15,nullptr);}
        else {KillTimer(hwnd,1);ShowWindow(ringWindow,SW_HIDE);}return 0;
    case WM_TIMER:
        if(w==1){if(mode==static_cast<int>(Mode::Hold))DrawRing();else{KillTimer(hwnd,1);ShowWindow(ringWindow,SW_HIDE);}}
        if(w==2){KillTimer(hwnd,2);ShowWindow(tipWindow,SW_HIDE);}return 0;
    case TRAY:
        if(l==WM_RBUTTONUP){HMENU menu=CreatePopupMenu();AppendMenuW(menu,MF_STRING,PAUSE,paused?L"Resume":L"Pause");
            AppendMenuW(menu,MF_STRING,ABOUT,L"Controls / About");AppendMenuW(menu,MF_STRING,EXIT,L"Exit");
            POINT p{};GetCursorPos(&p);SetForegroundWindow(hwnd);
            UINT cmd=TrackPopupMenu(menu,TPM_RETURNCMD|TPM_RIGHTBUTTON,p.x,p.y,0,hwnd,nullptr);DestroyMenu(menu);
            PostMessageW(hwnd,WM_NULL,0,0);if(cmd)PostMessageW(hwnd,WM_COMMAND,cmd,0);}
        if(l==WM_LBUTTONDBLCLK)PostMessageW(hwnd,WM_COMMAND,ABOUT,0);
        return 0;
    case WM_COMMAND:
        if(w==EXIT)PostMessageW(hwnd,WM_CLOSE,0,0);
        if(w==PAUSE){paused=!paused;Command(STOP);ShowTip(paused?L"Scroll tool paused":L"Scroll tool resumed",900);}
        if(w==ABOUT)MessageBoxW(hwnd,L"PACS Precision Scroll Native 1.0.0\n\nHold middle button 300 ms: precision scroll.\nMove vertically to scroll; middle click stops.\nCtrl + middle: toggle auto-scroll (default 25/s).\nShift: faster. Ctrl: slower.\nAuto mode: wheel or Up/Down changes direction.\nCtrl + Alt + 3: active app details.\nCtrl + Alt + F12: pause/resume.\nRight-click tray icon: pause or exit.\n\nClose the old scrolling AHK EXE before starting.\nNo installer or extra runtime required.\n\nNative input pacing; PACS/Citrix needs local testing.",TITLE,MB_OK);
        return 0;
    case WM_HOTKEY:PostMessageW(hwnd,WM_COMMAND,PAUSE,0);return 0;
    case WM_POWERBROADCAST:if(w==PBT_APMSUSPEND){paused=true;Command(STOP);}return TRUE;
    case WM_QUERYENDSESSION:paused=true;Command(STOP);return TRUE;
    case WM_ENDSESSION:if(w)PostMessageW(hwnd,WM_CLOSE,0,0);return 0;
    case WM_CLOSE:paused=true;shuttingDown=true;Command(STOP);DestroyWindow(hwnd);return 0;
    case WM_DESTROY:PostQuitMessage(0);return 0;
    default:return DefWindowProcW(hwnd,msg,w,l);
    }
}
} // namespace
int WINAPI wWinMain(HINSTANCE instance,HINSTANCE,PWSTR,int) {
    HANDLE singleton=CreateMutexW(nullptr,FALSE,L"Local\\PACSPrecisionScrollNative-v1");
    if(!singleton||GetLastError()==ERROR_ALREADY_EXISTS){MessageBoxW(nullptr,L"The scrolling tool is already running. Check the system tray.",TITLE,MB_OK);if(singleton)CloseHandle(singleton);return 0;}
    QueryPerformanceFrequency(&frequency);SetProcessDPIAware();
    Gdiplus::GdiplusStartupInput startup;
    if(Gdiplus::GdiplusStartup(&gdipToken,&startup,nullptr)!=Gdiplus::Ok)return 1;
    WNDCLASSW wc{};wc.hInstance=instance;wc.lpfnWndProc=WindowProc;wc.lpszClassName=L"PACSScrollNative";
    RegisterClassW(&wc);mainWindow=CreateWindowExW(0,wc.lpszClassName,TITLE,0,0,0,0,0,nullptr,nullptr,instance,nullptr);
    wc.lpfnWndProc=OverlayProc;wc.lpszClassName=L"PACSScrollOverlay";RegisterClassW(&wc);
    DWORD ex=WS_EX_TOPMOST|WS_EX_TOOLWINDOW|WS_EX_NOACTIVATE|WS_EX_TRANSPARENT;
    ringWindow=CreateWindowExW(ex|WS_EX_LAYERED,wc.lpszClassName,L"",WS_POPUP,0,0,56,56,nullptr,nullptr,instance,nullptr);
    tipWindow=CreateWindowExW(ex,wc.lpszClassName,L"",WS_POPUP|WS_BORDER,0,0,10,10,nullptr,nullptr,instance,nullptr);
    ringDC=CreateCompatibleDC(nullptr);BITMAPINFO bi{};bi.bmiHeader.biSize=sizeof(BITMAPINFOHEADER);
    bi.bmiHeader.biWidth=56;bi.bmiHeader.biHeight=-56;bi.bmiHeader.biPlanes=1;bi.bmiHeader.biBitCount=32;
    ringBitmap=CreateDIBSection(ringDC,&bi,DIB_RGB_COLORS,&ringBits,nullptr,0);
    if(!mainWindow||!ringWindow||!tipWindow||!ringDC||!ringBitmap)return 1;
    oldBitmap=SelectObject(ringDC,ringBitmap);
    canvas=new Gdiplus::Bitmap(56,56,56*4,PixelFormat32bppPARGB,static_cast<BYTE*>(ringBits));
    workerReady=CreateEventW(nullptr,TRUE,FALSE,nullptr);hookReady=CreateEventW(nullptr,TRUE,FALSE,nullptr);
    if(workerReady)workerThread=CreateThread(nullptr,0,Worker,nullptr,0,&workerId);
    bool ready=workerThread&&WaitForSingleObject(workerReady,5000)==WAIT_OBJECT_0&&workerTimerOK;
    if(ready&&hookReady)hookThread=CreateThread(nullptr,0,Hooks,nullptr,0,&hookId);
    ready=ready&&hookThread&&WaitForSingleObject(hookReady,5000)==WAIT_OBJECT_0&&hooksOK;
    if(!ready){MessageBoxW(nullptr,L"Could not start input hooks or timer. The tool will close.",TITLE,MB_ICONERROR);paused=true;}
    taskbarCreated=RegisterWindowMessageW(L"TaskbarCreated");if(ready)AddTray();
    MSG msg{};if(ready)while(GetMessageW(&msg,nullptr,0,0)>0){TranslateMessage(&msg);DispatchMessageW(&msg);}
    paused=true;shuttingDown=true;
    if(hookThread){PostThreadMessageW(hookId,WM_QUIT,0,0);WaitForSingleObject(hookThread,INFINITE);CloseHandle(hookThread);}
    if(workerThread){PostThreadMessageW(workerId,WM_QUIT,0,0);WaitForSingleObject(workerThread,INFINITE);CloseHandle(workerThread);}
    while(PeekMessageW(&msg,nullptr,TIP,TIP,PM_REMOVE))delete reinterpret_cast<std::wstring*>(msg.lParam);
    Shell_NotifyIconW(NIM_DELETE,&tray);
    DestroyWindow(ringWindow);DestroyWindow(tipWindow);delete canvas;
    SelectObject(ringDC,oldBitmap);DeleteObject(ringBitmap);DeleteDC(ringDC);
    Gdiplus::GdiplusShutdown(gdipToken);if(workerReady)CloseHandle(workerReady);if(hookReady)CloseHandle(hookReady);CloseHandle(singleton);
    return ready?0:1;
}
