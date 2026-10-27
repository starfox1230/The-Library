; ==============================================================================
; Precision Scroll (AHK v1)
; - Mouse-move-to-wheel scrolling with direction-halt + infinite Y wrap
; - Starting Precision Scroll requires holding MButton for 300 ms
; - While holding MButton, a smooth circular ring appears around the cursor
;   and fills from red to green until launch
; - Toggling Precision Scroll OFF only requires a normal MButton click
; - Clicking MButton also stops Auto-Scroll if Auto-Scroll is running
; - While Precision Scroll mode is ON:
;     Shift increases Sensitivity (faster)
;     Ctrl decreases Sensitivity (slower)
;
; Auto-Scroll (Ctrl+MButton):
; - Tries to activate VirtualMonitor first if it exists, but does NOT require it
; - NO mouse locking / NO cursor movement / NO restrictions
; - Continuously scrolls in the LAST scrolled direction
; - Includes ALL prior speeds plus extra 7/s, 19/s, 31/s options
; - Shift increases Auto-Scroll speed
; - Ctrl decreases Auto-Scroll speed
; - UP/DOWN change Auto-Scroll direction (NO tooltip)
; - While Auto-Scroll is ON, PHYSICAL mouse wheel ONLY changes direction
;   (wheel does NOT pass through to the app, so it won't "fight" the auto-scroll)
;
; Fixes:
; - Avoid "too many hotkeys" pop-up by increasing hotkey rate limits
; ==============================================================================

#NoEnv
#SingleInstance Force
SetBatchLines, -1
ListLines Off
Process, Priority, , High
SendMode Input
SetTitleMatchMode, 2
CoordMode, Mouse, Screen

; --- FIX: prevent "too many hotkeys" dialog ---
#HotkeyInterval 2000
#MaxHotkeysPerInterval 5000

; --- OPTIONAL TARGET ---
TargetTitle = VirtualMonitor

; --- GDI+ STARTUP (for smooth circular hold ring) ---
pToken := Gdip_Startup()
if (!pToken)
{
    MsgBox, 16, Error, GDI+ failed to start.
    ExitApp
}
OnExit, CleanupGDI

; --- PRECISION SCROLL SETTINGS ---
; Higher displayed Sensitivity = faster scrolling
MinSensitivity := 1
MaxSensitivity := 50
OldDefaultThreshold := 8
DefaultSensitivity := MaxSensitivity - OldDefaultThreshold + MinSensitivity
Sensitivity := DefaultSensitivity

HaltDuration := 50
EdgeMargin := 100

; --- HOLD-TO-START RING SETTINGS ---
HoldToStartMs := 300
HoldRingTickMs := 15
HoldRingSize := 56
HoldRingThickness := 6
HoldRingStartAngle := -90          ; starts at top
HoldRingGuiBg := "010101"          ; transparent colorkey
HoldRingBgColorARGB := 0xFF010101  ; must match HoldRingGuiBg exactly
HoldRingBaseColorARGB := 0xFF2A2A2A

; --- AUTO-SCROLL SPEED SETTINGS ---
; Old speeds were 12.5 * N per second (N = 1..20)
; New extras requested: 7/s, 19/s, 31/s
; Combined and sorted:
AutoRates := [7, 12.5, 19, 25, 31, 37.5, 50, 62.5, 75, 87.5, 100, 112.5, 125, 137.5, 150, 162.5, 175, 187.5, 200, 212.5, 225, 237.5, 250]
AutoDefaultRateIndex := 4   ; 25/s (keeps the prior default feel)
AutoRateIndex := AutoDefaultRateIndex
AutoRate := AutoRates[AutoRateIndex]
AutoSendInterval := 1000.0 / AutoRate
AutoLockTickMs := 5

; --- STATE ---
IsScrolling := 0
IsAutoScrolling := 0
LastY := 0
CurrentDir := ""
CooldownEnd := 0
AccumulatedDistance := 0

LastScrollDir := "Down"
AutoDir := ""
AutoLockX := 0
AutoLockY := 0
AutoNextWheel := 0.0

HoldActive := 0
HoldStartTime := 0

HoldRingGuiCreated := 0
HoldRingGuiHwnd := 0
HoldRingPicHwnd := 0
HoldRingBitmap := 0

; --- HOTKEYS ---
MButton::Gosub, HandleMButton
^MButton::Gosub, ToggleAutoScroll
^!3::Gosub, ShowDebug
return


; =========================
; PHYSICAL WHEEL BEHAVIOR
; - When Auto-Scroll is ON: wheel ONLY changes direction (no pass-through)
; - Otherwise: wheel passes through but updates LastScrollDir
; =========================

#If (IsAutoScrolling)
$WheelUp::
AutoDir := "Up"
LastScrollDir := "Up"
return

$WheelDown::
AutoDir := "Down"
LastScrollDir := "Down"
return
#If

#If (!IsAutoScrolling)
$~WheelUp::LastScrollDir := "Up"
$~WheelDown::LastScrollDir := "Down"
#If


; =========================
; While Precision Scroll is ON:
; Shift increases Sensitivity (faster)
; Ctrl decreases Sensitivity (slower)
; =========================
#If (IsScrolling)
LShift::Gosub, SpeedFaster
RShift::Gosub, SpeedFaster
LCtrl::Gosub, SpeedSlower
RCtrl::Gosub, SpeedSlower
#If


; =========================
; While Auto-Scroll is ON:
; Shift increases speed
; Ctrl decreases speed
; UP/DOWN change direction
; =========================
#If (IsAutoScrolling)
LShift::Gosub, AutoFaster
RShift::Gosub, AutoFaster
LCtrl::Gosub, AutoSlower
RCtrl::Gosub, AutoSlower
Up::Gosub, AutoDirUp
Down::Gosub, AutoDirDown
#If


; =========================
; Middle button behavior
; - If Precision Scroll is ON: click turns it OFF
; - If Auto-Scroll is ON: click turns it OFF
; - Otherwise: hold 300 ms to start Precision Scroll
; =========================
HandleMButton:
if (IsScrolling)
{
    Gosub, StopScroll
    return
}

if (IsAutoScrolling)
{
    Gosub, StopAutoScroll
    return
}

if (HoldActive)
    return

Gosub, TryActivateTargetWindow

HoldActive := 1
HoldStartTime := A_TickCount
Gosub, InitHoldRing
SetTimer, PrecisionHoldTick, %HoldRingTickMs%
return


; =========================
; Hold-to-start loop for Precision Scroll
; =========================
PrecisionHoldTick:
if (!HoldActive)
{
    SetTimer, PrecisionHoldTick, Off
    return
}

if !GetKeyState("MButton", "P")
{
    Gosub, CancelPrecisionHold
    return
}

Elapsed := A_TickCount - HoldStartTime
Progress := Elapsed / HoldToStartMs
if (Progress > 1)
    Progress := 1

MouseGetPos, HoldRingX, HoldRingY
DrawHoldRingFrame(Progress, HoldRingX, HoldRingY)

if (Elapsed < HoldToStartMs)
    return

Gosub, CancelPrecisionHold
Gosub, StartPrecisionScroll
return


InitHoldRing:
EnsureHoldRingGui()
MouseGetPos, HoldRingX, HoldRingY
DrawHoldRingFrame(0, HoldRingX, HoldRingY)
return


CancelPrecisionHold:
HoldActive := 0
SetTimer, PrecisionHoldTick, Off
HideHoldRing()
return


; =========================
; Precision Scroll Start
; =========================
StartPrecisionScroll:
if (IsScrolling)
    return

if (IsAutoScrolling)
    Gosub, StopAutoScroll

Gosub, TryActivateTargetWindow

IsScrolling := 1
CurrentDir := ""
CooldownEnd := 0
AccumulatedDistance := 0
MouseGetPos, , LastY

SetTimer, WatchMouse, 10
Gosub, ShowScrollOnTip
return


; =========================
; Precision Scroll Main loop
; =========================
WatchMouse:
if (!IsScrolling)
{
    SetTimer, WatchMouse, Off
    return
}

MouseGetPos, CurrentX, CurrentY
if (CurrentY < EdgeMargin || CurrentY > (A_ScreenHeight - EdgeMargin))
{
    CenterY := A_ScreenHeight // 2
    MouseMove, %CurrentX%, %CenterY%, 0
    LastY := CenterY
    return
}

if (A_TickCount < CooldownEnd)
{
    LastY := CurrentY
    AccumulatedDistance := 0
    return
}

Diff := CurrentY - LastY
if (Abs(Diff) < 1)
    return

if (CurrentDir = "Down")
{
    if (Diff < 0)
    {
        Gosub, TriggerHalt
        return
    }
}
else if (CurrentDir = "Up")
{
    if (Diff > 0)
    {
        Gosub, TriggerHalt
        return
    }
}

; Inverted math:
; higher Sensitivity = lower threshold = faster scrolling
Threshold := MaxSensitivity - Sensitivity + MinSensitivity
if (Threshold < 1)
    Threshold := 1

if (CurrentDir = "")
{
    if (Diff > 0)
        CurrentDir := "Down"
    else
        CurrentDir := "Up"

    if (CurrentDir = "Down")
        Send, {WheelDown}
    else
        Send, {WheelUp}

    LastScrollDir := CurrentDir
    AccumulatedDistance := 0
}
else
{
    AccumulatedDistance := AccumulatedDistance + Abs(Diff)

    if (AccumulatedDistance >= Threshold)
    {
        Clicks := Floor(AccumulatedDistance / Threshold)

        if (CurrentDir = "Down")
            Send, {WheelDown %Clicks%}
        else
            Send, {WheelUp %Clicks%}

        LastScrollDir := CurrentDir
        AccumulatedDistance := AccumulatedDistance - (Clicks * Threshold)
    }
}

LastY := CurrentY
return


; =========================
; Precision Scroll sensitivity adjust
; Shift = faster
; Ctrl  = slower
; =========================
SpeedFaster:
Sensitivity += 1
if (Sensitivity > MaxSensitivity)
    Sensitivity := MaxSensitivity
Gosub, ShowSensitivityTip
return

SpeedSlower:
Sensitivity -= 1
if (Sensitivity < MinSensitivity)
    Sensitivity := MinSensitivity
Gosub, ShowSensitivityTip
return


; =========================
; Ctrl+MButton Auto-Scroll Toggle
; =========================
ToggleAutoScroll:
if (IsAutoScrolling)
{
    Gosub, StopAutoScroll
    return
}

Gosub, CancelPrecisionHold

if (IsScrolling)
    Gosub, StopScroll

Gosub, TryActivateTargetWindow
Gosub, ApplyAutoRate

IsAutoScrolling := 1
MouseGetPos, AutoLockX, AutoLockY

AutoDir := (LastScrollDir != "" ? LastScrollDir : "Down")
AutoNextWheel := A_TickCount

SetTimer, AutoScrollTick, %AutoLockTickMs%
Gosub, ShowAutoOnTip
return


; =========================
; Auto-Scroll loop
; Sends 1 wheel tick each scheduled interval
; =========================
AutoScrollTick:
if (!IsAutoScrolling)
{
    SetTimer, AutoScrollTick, Off
    return
}

while (A_TickCount >= AutoNextWheel)
{
    if (AutoDir = "Down")
        Send, {WheelDown}
    else
        Send, {WheelUp}

    LastScrollDir := AutoDir
    AutoNextWheel := AutoNextWheel + AutoSendInterval
}
return


; =========================
; Auto-Scroll speed controls
; =========================
AutoFaster:
if (AutoRateIndex < AutoRates.Length())
    AutoRateIndex += 1
Gosub, ApplyAutoRate
Gosub, ShowAutoSpeedOnlyTip
return

AutoSlower:
if (AutoRateIndex > 1)
    AutoRateIndex -= 1
Gosub, ApplyAutoRate
Gosub, ShowAutoSpeedOnlyTip
return

AutoDirUp:
AutoDir := "Up"
LastScrollDir := "Up"
return

AutoDirDown:
AutoDir := "Down"
LastScrollDir := "Down"
return


; =========================
; Apply selected auto-scroll rate
; =========================
ApplyAutoRate:
AutoRate := AutoRates[AutoRateIndex]
AutoSendInterval := 1000.0 / AutoRate
return


; =========================
; Helpers
; =========================
TriggerHalt:
CurrentDir := ""
AccumulatedDistance := 0
CooldownEnd := A_TickCount + HaltDuration
LastY := CurrentY
return


StopScroll:
IsScrolling := 0
CurrentDir := ""
SetTimer, WatchMouse, Off
ToolTip, Scroll OFF
SetTimer, RemoveToolTip, -700
return


StopAutoScroll:
IsAutoScrolling := 0
SetTimer, AutoScrollTick, Off
ToolTip, Auto-Scroll OFF
SetTimer, RemoveToolTip, -700
return


ShowScrollOnTip:
TipText := "Scroll ON | Sensitivity: " . Sensitivity
if (Sensitivity = DefaultSensitivity)
    TipText .= " (default)"
ToolTip, %TipText%
SetTimer, RemoveToolTip, -900
return


ShowSensitivityTip:
TipText := "Sensitivity: " . Sensitivity
if (Sensitivity = DefaultSensitivity)
    TipText .= " (default)"
ToolTip, %TipText%
SetTimer, RemoveToolTip, -900
return


ShowAutoOnTip:
TipText := "Auto-Scroll ON`n" . FormatRate(AutoRate) . "/s"
ToolTip, %TipText%
SetTimer, RemoveToolTip, -900
return


ShowAutoSpeedOnlyTip:
TipText := FormatRate(AutoRate) . "/s"
ToolTip, %TipText%
SetTimer, RemoveToolTip, -650
return


ShowDebug:
WinGet, pName, ProcessName, A
WinGetTitle, pTitle, A
MsgBox, Active App Details:`n`nEXE: %pName%`nTitle: %pTitle%
return


RemoveToolTip:
ToolTip
return


; =========================
; Try to activate VirtualMonitor if present, but do not require it
; =========================
TryActivateTargetWindow:
IfWinExist, VirtualMonitor
{
    WinActivate
    WinWaitActive, VirtualMonitor,, 0.5
}
return


CleanupGDI:
HideHoldRing()
DestroyHoldRingResources()
if (pToken)
    Gdip_Shutdown(pToken)
ExitApp
return


; =========================
; Rate display helper
; =========================
FormatRate(rate) {
    if (Mod(rate, 1) = 0)
        return Round(rate)
    return rate
}


; =========================
; Smooth hold ring drawing
; =========================
EnsureHoldRingGui() {
    global HoldRingGuiCreated, HoldRingGuiHwnd, HoldRingPicHwnd, HoldRingSize, HoldRingGuiBg

    if (HoldRingGuiCreated)
        return

    Gui, HoldRing:Destroy
    Gui, HoldRing:+AlwaysOnTop -Caption +ToolWindow +E0x20 +HwndHoldRingGuiHwnd
    Gui, HoldRing:Color, %HoldRingGuiBg%
    Gui, HoldRing:Margin, 0, 0
    Gui, HoldRing:Add, Picture, x0 y0 w%HoldRingSize% h%HoldRingSize% hwndHoldRingPicHwnd 0xE
    Gui, HoldRing:Show, NA x0 y0 w%HoldRingSize% h%HoldRingSize%
    WinSet, TransColor, %HoldRingGuiBg%, ahk_id %HoldRingGuiHwnd%
    Gui, HoldRing:Hide

    HoldRingGuiCreated := 1
}

DrawHoldRingFrame(progress, centerX, centerY) {
    global HoldRingSize, HoldRingThickness, HoldRingStartAngle
    global HoldRingGuiHwnd, HoldRingPicHwnd
    global HoldRingBgColorARGB, HoldRingBaseColorARGB, HoldRingBitmap

    EnsureHoldRingGui()

    size := HoldRingSize
    pad := Ceil(HoldRingThickness / 2) + 2

    x := centerX - Floor(size / 2)
    y := centerY - Floor(size / 2)

    hbm := CreateDIBSection(size, size)
    hdc := CreateCompatibleDC()
    obm := SelectObject(hdc, hbm)

    pGraphics := Gdip_GraphicsFromHDC(hdc)
    Gdip_SetSmoothingMode(pGraphics, 4)
    Gdip_GraphicsClear(pGraphics, HoldRingBgColorARGB)

    ; Base full ring
    pPenBase := Gdip_CreatePen(HoldRingBaseColorARGB, HoldRingThickness)
    Gdip_DrawEllipse(pGraphics, pPenBase, pad, pad, size - (pad * 2), size - (pad * 2))
    Gdip_DeletePen(pPenBase)

    ; Active ring arc (red -> green)
    if (progress < 0)
        progress := 0
    if (progress > 1)
        progress := 1

    r := Round(255 * (1 - progress))
    g := Round(255 * progress)
    activeColor := (0xFF << 24) | (r << 16) | (g << 8)

    sweep := 360.0 * progress
    if (sweep < 6)
        sweep := 6

    pPenActive := Gdip_CreatePen(activeColor, HoldRingThickness)
    Gdip_DrawArc(pGraphics, pPenActive, pad, pad, size - (pad * 2), size - (pad * 2), HoldRingStartAngle, sweep)
    Gdip_DeletePen(pPenActive)

    Gdip_DeleteGraphics(pGraphics)
    SelectObject(hdc, obm)
    DeleteDC(hdc)

    old := SetImage(HoldRingPicHwnd, hbm)
    if (old)
        DeleteObject(old)

    HoldRingBitmap := hbm
    Gui, HoldRing:Show, NA x%x% y%y% w%size% h%size%
}

HideHoldRing() {
    global HoldRingGuiCreated, HoldRingPicHwnd, HoldRingBitmap

    if (HoldRingGuiCreated)
        Gui, HoldRing:Hide

    if (HoldRingPicHwnd) {
        old := SetImage(HoldRingPicHwnd, 0)
        if (old)
            DeleteObject(old)
    }

    HoldRingBitmap := 0
}

DestroyHoldRingResources() {
    global HoldRingGuiCreated, HoldRingGuiHwnd, HoldRingPicHwnd, HoldRingBitmap

    HideHoldRing()

    if (HoldRingGuiCreated)
        Gui, HoldRing:Destroy

    HoldRingGuiCreated := 0
    HoldRingGuiHwnd := 0
    HoldRingPicHwnd := 0
    HoldRingBitmap := 0
}

SetImage(hwnd, hBitmap) {
    ; STM_SETIMAGE = 0x172, IMAGE_BITMAP = 0
    return DllCall("SendMessage", "ptr", hwnd, "uint", 0x172, "ptr", 0, "ptr", hBitmap, "ptr")
}


; =========================
; Minimal GDI+ helpers
; =========================
Gdip_Startup() {
    if !DllCall("GetModuleHandle", "str", "gdiplus", "ptr")
        DllCall("LoadLibrary", "str", "gdiplus")

    VarSetCapacity(si, 16, 0)
    NumPut(1, si, 0, "UInt")

    if DllCall("gdiplus\GdiplusStartup", "ptr*", pToken, "ptr", &si, "ptr", 0)
        return 0
    return pToken
}

Gdip_Shutdown(pToken) {
    return DllCall("gdiplus\GdiplusShutdown", "ptr", pToken)
}

CreateDIBSection(w, h, hdc := 0) {
    ownDC := 0
    if (!hdc) {
        hdc := DllCall("GetDC", "ptr", 0, "ptr")
        ownDC := 1
    }

    VarSetCapacity(bi, 40, 0)
    NumPut(40, bi, 0, "UInt")
    NumPut(w, bi, 4, "Int")
    NumPut(-h, bi, 8, "Int")
    NumPut(1, bi, 12, "UShort")
    NumPut(32, bi, 14, "UShort")
    NumPut(0, bi, 16, "UInt")

    hbm := DllCall("gdi32\CreateDIBSection"
        , "ptr", hdc
        , "ptr", &bi
        , "uint", 0
        , "ptr*", ppvBits
        , "ptr", 0
        , "uint", 0
        , "ptr")

    if (ownDC)
        DllCall("ReleaseDC", "ptr", 0, "ptr", hdc)

    return hbm
}

CreateCompatibleDC(hdc := 0) {
    return DllCall("gdi32\CreateCompatibleDC", "ptr", hdc, "ptr")
}

SelectObject(hdc, hgdiobj) {
    return DllCall("gdi32\SelectObject", "ptr", hdc, "ptr", hgdiobj, "ptr")
}

DeleteObject(hObject) {
    return DllCall("gdi32\DeleteObject", "ptr", hObject)
}

DeleteDC(hdc) {
    return DllCall("gdi32\DeleteDC", "ptr", hdc)
}

Gdip_GraphicsFromHDC(hdc) {
    DllCall("gdiplus\GdipCreateFromHDC", "ptr", hdc, "ptr*", pGraphics)
    return pGraphics
}

Gdip_DeleteGraphics(pGraphics) {
    return DllCall("gdiplus\GdipDeleteGraphics", "ptr", pGraphics)
}

Gdip_SetSmoothingMode(pGraphics, smoothingMode := 4) {
    return DllCall("gdiplus\GdipSetSmoothingMode", "ptr", pGraphics, "int", smoothingMode)
}

Gdip_GraphicsClear(pGraphics, ARGB := 0x00FFFFFF) {
    return DllCall("gdiplus\GdipGraphicsClear", "ptr", pGraphics, "int", ARGB)
}

Gdip_CreatePen(ARGB, width) {
    DllCall("gdiplus\GdipCreatePen1", "int", ARGB, "float", width, "int", 2, "ptr*", pPen)
    return pPen
}

Gdip_DeletePen(pPen) {
    return DllCall("gdiplus\GdipDeletePen", "ptr", pPen)
}

Gdip_DrawArc(pGraphics, pPen, x, y, w, h, startAngle, sweepAngle) {
    return DllCall("gdiplus\GdipDrawArc"
        , "ptr", pGraphics
        , "ptr", pPen
        , "float", x
        , "float", y
        , "float", w
        , "float", h
        , "float", startAngle
        , "float", sweepAngle)
}

Gdip_DrawEllipse(pGraphics, pPen, x, y, w, h) {
    return DllCall("gdiplus\GdipDrawEllipse"
        , "ptr", pGraphics
        , "ptr", pPen
        , "float", x
        , "float", y
        , "float", w
        , "float", h)
}