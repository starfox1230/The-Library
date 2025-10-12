; TranscriptRunner_v1.ahk  (AutoHotkey v1.1+)
; Flow:
;   - Opens transcript site, TYPES the URL into the already-focused field, presses Enter (clipboard untouched)
;   - You click "Copy" on the site
;   - On first LEFT-CLICK RELEASE (with a short delay), a prompt appears -> OK waits for transcript on clipboard, saves, opens next
; Shortcuts:
;   Ctrl+Win+N  -> Skip current and advance
;   Ctrl+Win+Q  -> Quit

#NoEnv
#SingleInstance Force
SendMode Input
SetWorkingDir %A_ScriptDir%
ListLines Off

; -------------------- Globals --------------------
gItems := []          ; array of {title:..., url:...}
gIdx := 1
gOutDir := ""
gSection := "01"
gStart := 1
gPad := 2
gTemplate := "{section}.{i} - {title}.txt"
gSite := "tactiq"     ; "tactiq" or "savesubs"
gLoadDelay := 1200    ; ms to wait after opening site before type+Enter
gClipTimeout := 7000  ; ms max to wait for transcript to land on clipboard
gAwaitingClick := false
gPreClipText := ""    ; clipboard snapshot from BEFORE we type the URL
gClickDelayMs := 350  ; delay after your left-click before the confirm prompt (adjust 300–800)
gConfirmScheduled := false

; -------------------- GUI --------------------
Gui, Font, s10
Gui, Add, Text,, Paste your list (Title - URL on each line). URL can be anywhere on the line.
Gui, Add, Edit, w820 r12 vListInput gUpdatePreview

Gui, Add, Text, y+10, Output folder:
Gui, Add, Button, x+m gChooseFolder, Choose...
Gui, Add, Edit, w650 x+m vOutDir ReadOnly

Gui, Add, Text, y+12, How the numbering works:
Gui, Add, Text,, 1) Section (before the dot). Enter two digits like 01, 02, 11. If you type 2 it becomes 02.
Gui, Add, Text,, 2) Start index is the first "xx" (usually 1). 3) Pad width controls digits for "xx" (2 -> 01, 3 -> 001).
Gui, Add, Text,, Do NOT type numbers into the template; use the boxes below. Watch the Preview to confirm.

Gui, Add, Text, y+8, Section:
Gui, Add, Edit, w80 vSection gUpdatePreview, 01

Gui, Add, Text, x+20 yp, Start index:
Gui, Add, Edit, w60 vStart gUpdatePreview
Gui, Add, UpDown, Range1-9999 1

Gui, Add, Text, x+20 yp, Pad width for xx:
Gui, Add, Edit, w60 vPad gUpdatePreview
Gui, Add, UpDown, Range1-9 2

Gui, Add, Text, y+10, Filename template (tokens: {section}, {i}, {title})
Gui, Add, Edit, w820 vTemplate gUpdatePreview, {section}.{i} - {title}.txt

Gui, Add, Text, y+10, Site:
Gui, Add, Radio, vSiteGroup Checked gUpdatePreview, Tactiq (recommended)
Gui, Add, Radio, gUpdatePreview, SaveSubs (fallback)

Gui, Add, Text, y+10, Preview (first 3 files):
Gui, Add, Edit, w820 r4 vPreviewBox ReadOnly

Gui, Add, Button, w160 gStartRun, Start
Gui, Add, Button, w120 x+m gCancelRun, Cancel
Gui, Show,, Bulk Transcript Saver (AHK v1)
Gosub, UpdatePreview
return

; -------------------- Handlers --------------------
ChooseFolder:
    FileSelectFolder, picked, , 3, Choose output folder
    if (picked <> "")
    {
        gOutDir := picked
        GuiControl,, OutDir, %picked%
    }
return

CancelRun:
    ExitApp
return

UpdatePreview:
    Gui, Submit, NoHide
    secRaw := Trim(Section)
    if (secRaw ~= "^\d+$")
        secNorm := LPad(secRaw+0, 2, "0")
    else
        secNorm := secRaw

    tempItems := ParseList(ListInput)
    prevText  := BuildPreview(tempItems, secNorm, Start+0, Pad+0, Trim(Template), 3)
    if (prevText = "")
        prevText := "(Preview will appear here once your list includes at least one valid https:// URL.)"
    GuiControl,, PreviewBox, % prevText
return

StartRun:
    Gui, Submit, NoHide
    if (!OutDir) {
        MsgBox, 48, Missing folder, Please choose an output folder first.
        return
    }
    gOutDir := OutDir

    if (Section ~= "^\d+$")
        gSection := LPad(Section+0, 2, "0")
    else
        gSection := Trim(Section)

    gStart    := Start+0
    gPad      := Pad+0
    gTemplate := Trim(Template)

    GuiControlGet, isFirstRadio,, SiteGroup
    gSite := (isFirstRadio=1) ? "tactiq" : "savesubs"

    raw := ListInput
    if (!raw) {
        MsgBox, 48, No input, Please paste your list.
        return
    }

    gItems := ParseList(raw)
    if (gItems.MaxIndex() = "")
    {
        MsgBox, 48, Nothing to do, I couldn't find any lines with a valid https:// URL.
        return
    }

    ; Hotkeys
    Hotkey, ^#n, SkipAndNext, On
    Hotkey, ^#q, QuitRun, On
    Hotkey, ~LButton Up, On  ; trigger after your click finishes (button UP)

    gIdx := 1
    Msg := "I found " gItems.MaxIndex() " item(s)." . "`n`n"
         . "Per video:" . "`n"
         . "  1) Script opens the transcript site and waits " gLoadDelay " ms." . "`n"
         . "  2) It TYPES the URL (clipboard not touched) and presses Enter." . "`n"
         . "  3) YOU click Copy on the site." . "`n"
         . "  4) On your next left-click, a prompt appears -> OK saves & opens next." . "`n`n"
         . "Skip current: Ctrl+Win+N    Quit: Ctrl+Win+Q"
    MsgBox, 64, Ready, % Msg

    OpenCurrent()
return

; -------------------- Core flow --------------------
OpenCurrent() {
    global gIdx, gItems, gSite
    if (gIdx > gItems.MaxIndex()) {
        MsgBox, 64, Finished, All done!
        ExitApp
    }
    if (gSite = "tactiq")
        Run, https://tactiq.io/tools/youtube-transcript
    else
        Run, https://savesubs.com/sites/download-youtube-subtitles

    SetTimer, _TypeURLAndSubmit, -50
}

_TypeURLAndSubmit:
    global gIdx, gItems, gLoadDelay, gAwaitingClick, gPreClipText
    item := gItems[gIdx]
    gPreClipText := Clipboard  ; snapshot clipboard BEFORE we type

    Sleep, %gLoadDelay%        ; let the page focus the input automatically
    Send, ^a
    Sleep, 60
    ; Type the URL (clipboard remains free for the transcript)
    SendRaw, % item.url
    Sleep, 120
    Send, {Enter}

    gAwaitingClick := true
    ShowTip("URL entered for: " . item.title . "`nClick Copy, then left-click to continue.", 2500)
return

; ---- Left-click release: schedule confirm after a short delay so site Copy finishes
~LButton Up::
    global gAwaitingClick, gClickDelayMs, gConfirmScheduled
    if (gAwaitingClick && !gConfirmScheduled) {
        gConfirmScheduled := true
        SetTimer, __ConfirmAfterClick, -%gClickDelayMs%
    }
return

__ConfirmAfterClick:
    global gAwaitingClick, gConfirmScheduled
    gConfirmScheduled := false
    if (gAwaitingClick) {
        gAwaitingClick := false
        MsgBox, 64, Ready to move on, Ready to move on? Press OK to save and open the next.
        Gosub, SaveAndNext
    }
return

SaveAndNext:
    global gIdx, gItems, gOutDir, gSection, gStart, gPad, gTemplate, gPreClipText, gClipTimeout
    if (gIdx > gItems.MaxIndex()) {
        SoundBeep, 1000, 120
        return
    }

    ; Wait for clipboard to actually contain transcript text (not the URL / not unchanged)
    if (!WaitForTranscriptClipboard(gPreClipText, gClipTimeout)) {
        MsgBox, 48, Clipboard not ready
        , I still see the previous clipboard (or a URL). Please click the site's Copy button, then left-click to try again.
        global gAwaitingClick := true
        return
    }

    txt := Clipboard
    if (!txt) {
        MsgBox, 48, No text, Clipboard is empty. Click the site's Copy button first, then left-click again.
        global gAwaitingClick := true
        return
    }

    item := gItems[gIdx]
    seq := gStart + (gIdx - 1)
    num := LPad(seq, gPad, "0")

    filename := gTemplate
    filename := StrReplace(filename, "{section}", gSection)
    filename := StrReplace(filename, "{i}", num)
    filename := StrReplace(filename, "{title}", item.title)
    filename := SanitizeFilename(filename)
    if (InStr(filename, ".txt") = 0)
        filename := filename ".txt"
    full := gOutDir "\" filename

    f := FileOpen(full, "w", "UTF-8-RAW")
    if (!IsObject(f)) {
        MsgBox, 16, Write error, Couldn't open file for writing:`n%full%
        return
    }
    f.Write(txt)
    f.Close()

    TrayTip, Saved, %filename%, 2, 1
    gIdx++
    OpenCurrent()
return

SkipAndNext:
    global gIdx, gAwaitingClick
    gAwaitingClick := false
    gIdx++
    OpenCurrent()
return

QuitRun:
    ExitApp
return

; -------------------- Helpers --------------------
ParseList(text) {
    items := []
    Loop, Parse, text, `n, `r
    {
        line := Trim(A_LoopField)
        if (!line)
            continue
        url := ""
        if (RegExMatch(line, "(https?://\S+)", m))
            url := m1
        if (!url)
            continue

        title := Trim(StrReplace(line, url))
        title := Trim(RegExReplace(title, "\s*-\s*$"))
        title := Trim(RegExReplace(title, "^\s*-\s*"))
        if (!title)
            title := "untitled"

        item := {}
        item.title := title
        item.url := url
        items.Push(item)
    }
    return items
}

BuildPreview(items, section, start, pad, template, count := 3) {
    out := ""
    max := items.MaxIndex()
    if (max = "")
        return out
    loop, % (count < max ? count : max)
    {
        idx := A_Index
        seq := start + (idx - 1)
        num := LPad(seq, pad, "0")
        name := template
        name := StrReplace(name, "{section}", section)
        name := StrReplace(name, "{i}", num)
        name := StrReplace(name, "{title}", items[idx].title)
        name := SanitizeFilename(name)
        if (InStr(name, ".txt") = 0)
            name := name ".txt"
        out .= idx ": " name "`n"
    }
    return out
}

SanitizeFilename(name) {
    name := RegExReplace(name, "[<>:""/\\|?*\x00-\x1F]", " ")
    name := RegExReplace(name, "\s{2,}", " ")
    name := Trim(name, " .")
    if (!StrLen(name))
        name := "untitled"
    return name
}

LPad(val, width, padChar := "0") {
    val := "" . val
    while (StrLen(val) < width)
        val := padChar . val
    return val
}

ShowTip(text, ms := 2000) {
    ToolTip, %text%
    SetTimer, __HideTip, -%ms%
    return
    __HideTip:
        ToolTip
    return
}

WaitForTranscriptClipboard(prevText, timeoutMs := 7000) {
    start := A_TickCount
    while (true) {
        cur := Clipboard
        ; Heuristics: changed vs previous, not a URL, and looks like content (multiline or long)
        if (cur != prevText) {
            if !(cur ~= "i)^\s*https?://") {
                if (InStr(cur, "`n") || StrLen(cur) > 80)
                    return true
            }
        }
        if ((A_TickCount - start) > timeoutMs)
            return false
        Sleep, 150
    }
}