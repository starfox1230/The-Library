#NoEnv
#SingleInstance Force
#Persistent
SendMode Input
SetBatchLines, -1
SetTitleMatchMode, 2
DetectHiddenWindows, Off

; -----------------------------
; Anki Companion Game V2 Bridge
; AutoHotkey v1
; -----------------------------
; Assumes:
;   - AnkiConnect is installed
;   - Anki is running
;   - Your bury/skip key in Anki is "-"
;
; Hotkeys while Anki is active:
;   F8    = sync on an unrevealed question card (first synced card is free)
;   Ctrl+F8 = hard reset run to idle/unsynced/zero
;   Space = show answer, or Good after answer is shown
;   1-4   = rating keys, only score if answer is already shown
;   -     = bury/skip current card and start next timer

global BRIDGE_FILE := "_anki_companion_state.json"
global ANSWER_LIMIT_MS := 12000
global REVIEW_LIMIT_MS := 8000
global BOSS_INTERVAL := 25
global TIMEOUT_POLL_MS := 100
global HAPTICS_ENABLED := 1
global XINPUT_DLL := ""
global EDGE_MATCH := "Anki Companion Game V2 ahk_exe msedge.exe"
global ANKI_MATCH := "ahk_exe anki.exe"
global ANKI_ON_LEFT := false

global state := {}
state.version := 2
state.synced := 0
state.sessionActive := 0
state.firstCardFree := 0
state.phase := "idle"
state.phaseStartEpochMs := 0
state.phaseLimitMs := 0
state.answerShown := 0

state.currentCardIndex := 0
state.currentCardId := ""
state.deckName := ""
state.isBossCard := 0

state.answeredCards := 0
state.skippedCards := 0
state.score := 0
state.xp := 0
state.xpIntoLevel := 0
state.xpForNextLevel := 100
state.level := 1

state.streak := 0
state.onTimeStreak := 0
state.onTimeCards := 0
state.perfectCards := 0
state.comboMultiplier := 1.0
state.satelliteColorKey := "easy"

state.lastReward := 0
state.lastEventType := ""
state.lastEventText := ""
state.lastBadge := ""
state.eventNonce := 0
state.timeoutPhaseLatch := ""

global card := ResetCardState()

PublishBridge("boot", "Bridge ready. Press F8 on an unrevealed card to sync.", 0, "Awaiting Sync")
InitXInput()
SetTimer, __CheckPhaseTimeout, %TIMEOUT_POLL_MS%
return


#IfWinActive ahk_exe Anki.exe

F8::
ToolTip, F8 pressed - syncing
SetTimer, __HideToolTip, -1000
SyncOnQuestionSide()
return

$Space::
HandleSpace()
return

$1::
HandleRating(1)
return

$2::
HandleRating(2)
return

$3::
HandleRating(3)
return

$4::
HandleRating(4)
return

$-::
HandleSkip()
return

^F8::
ToolTip, Ctrl+F8 pressed - hard reset
SetTimer, __HideToolTip, -1000
HardResetSession()
return

#IfWinActive

!2::
TileAnkiAndCompanion()
return

!1::
MinimizeAnkiAndCompanion()
return


SyncOnQuestionSide() {
    global state, card, BOSS_INTERVAL

    if (state.currentCardIndex < 1)
        state.currentCardIndex := 1

    state.synced := 1
    state.sessionActive := 1
    state.answerShown := 0
    state.firstCardFree := 1
    state.isBossCard := Mod(state.currentCardIndex, BOSS_INTERVAL) = 0 ? 1 : 0

    card := ResetCardState()
    card.questionFree := 1

    BeginQuestionPhase(1)
    PublishBridge("sync", "Synced on question side. First synced card is free.", 0, "Synced")
    VibratePattern("sync")
}

HandleSpace() {
    global state, card

    if (!state.synced) {
        SendInput, {Space}
        return
    }

    if (state.phase = "question") {
        wasFree := card.questionFree
        card.answerElapsedMs := wasFree ? 0 : MaxValue(0, NowEpochMs() - state.phaseStartEpochMs)

        SendInput, {Space}

        state.answerShown := 1
        state.firstCardFree := 0
        BeginAnswerPhase()

        if (wasFree)
            PublishBridge("show-answer", "Answer revealed on first synced free card.", 0, "Reveal")
        else
            PublishBridge("show-answer", "Answer revealed.", 0, "Reveal")
        VibratePattern("reveal")
        return
    }

    if (state.phase = "answer") {
        SendInput, {Space}
        FinalizeRating(3) ; Space on answer side = Good
        return
    }

    SendInput, {Space}
}

HandleRating(ease) {
    global state

    if (!state.synced) {
        SendInput, %ease%
        return
    }

    if (state.phase != "answer") {
        ; Pass through to Anki, but do not score in companion before reveal.
        SendInput, %ease%
        return
    }

    SendInput, %ease%
    FinalizeRating(ease)
}

HandleSkip() {
    global state

    SendInput, -

    if (!state.synced)
        return

    state.skippedCards += 1

    MoveToNextQuestion("skip", "Card buried / skipped.", 0, "Skip")
    VibratePattern("skip")
}

FinalizeRating(ease) {
    global state, card, ANSWER_LIMIT_MS, REVIEW_LIMIT_MS

    if (ease = 1)
        ratingName := "Again"
    else if (ease = 2)
        ratingName := "Hard"
    else if (ease = 3)
        ratingName := "Good"
    else
        ratingName := "Easy"

    if (ease = 1)
        basePoints := 0
    else if (ease = 2)
        basePoints := 2
    else if (ease = 3)
        basePoints := 3
    else
        basePoints := 4

    reviewElapsedMs := MaxValue(0, NowEpochMs() - state.phaseStartEpochMs)
    answerElapsedMs := card.answerElapsedMs

    if (card.questionFree)
        answerOnTime := 1
    else
        answerOnTime := (answerElapsedMs <= ANSWER_LIMIT_MS) ? 1 : 0

    reviewOnTime := (reviewElapsedMs <= REVIEW_LIMIT_MS) ? 1 : 0
    perfect := (ease > 1 && answerOnTime && reviewOnTime) ? 1 : 0

    ; "Again" still builds streak in this mode (speed-first motivation).
    state.streak += 1

    if (answerOnTime && reviewOnTime) {
        state.onTimeStreak += 1
        state.onTimeCards += 1
    } else {
        state.onTimeStreak := 0
    }

    state.comboMultiplier := 1 + (Floor(state.onTimeStreak / 10) * 0.1)

    if (card.questionFree)
        answerBonus := 0
    else
        answerBonus := MaxValue(0, CeilValue(((ANSWER_LIMIT_MS / 1000.0) - (answerElapsedMs / 1000.0)) / 2.0))

    reviewBonus := MaxValue(0, CeilValue(((REVIEW_LIMIT_MS / 1000.0) - (reviewElapsedMs / 1000.0)) / 2.0))

    rawPoints := basePoints + answerBonus + reviewBonus
    bossMult := state.isBossCard ? 1.25 : 1.0
    reward := Round(rawPoints * state.comboMultiplier * bossMult)

    state.score += reward
    state.xp += reward
    state.answeredCards += 1

    if (perfect)
        state.perfectCards += 1

    UpdateLevelFields()

    badge := perfect ? "Perfect" : ratingName
    if (state.isBossCard)
        badge := badge . " • Boss"

    answerSeconds := Round(answerElapsedMs / 100.0) / 10.0
    reviewSeconds := Round(reviewElapsedMs / 100.0) / 10.0

    eventText := ratingName . ": +" . reward . " | answer " . answerSeconds . "s | review " . reviewSeconds . "s"
    eventType := StrLowerCustom(ratingName)
    if (ease = 1 && answerOnTime && reviewOnTime)
        eventType := "again-on-time"

    if (ease = 1)
        state.satelliteColorKey := "again"
    else if (ease = 2)
        state.satelliteColorKey := "hard"
    else if (ease = 3)
        state.satelliteColorKey := "good"
    else
        state.satelliteColorKey := "easy"
    MoveToNextQuestion(eventType, eventText, reward, badge)

    if (ease = 1)
        VibratePattern("again")
    else if (ease = 2)
        VibratePattern("hard")
    else if (ease = 3)
        VibratePattern("good")
    else
        VibratePattern("easy")

    if (state.isBossCard && reward > 0)
        VibratePattern("bossClear")
}

MoveToNextQuestion(eventType, eventText, reward, badge) {
    global state, BOSS_INTERVAL

    Sleep, 35

    if (state.currentCardIndex < 1)
        state.currentCardIndex := 1
    else
        state.currentCardIndex += 1

    state.isBossCard := Mod(state.currentCardIndex, BOSS_INTERVAL) = 0 ? 1 : 0
    BeginQuestionPhase(0)
    PublishBridge(eventType, eventText, reward, badge)
    if (state.isBossCard)
        VibratePattern("bossStart")
}

BeginQuestionPhase(isFree := 0) {
    global state, card, ANSWER_LIMIT_MS

    card := ResetCardState()
    card.questionFree := isFree ? 1 : 0

    state.phase := "question"
    state.phaseStartEpochMs := NowEpochMs()
    state.phaseLimitMs := isFree ? 0 : ANSWER_LIMIT_MS
    state.answerShown := 0
    state.firstCardFree := isFree ? 1 : 0
    state.sessionActive := 1
    state.timeoutPhaseLatch := ""

    if (!isFree)
        SafeAnkiCommand("{""action"":""guiStartCardTimer"",""version"":6}")
}

BeginAnswerPhase() {
    global state, REVIEW_LIMIT_MS

    state.phase := "answer"
    state.phaseStartEpochMs := NowEpochMs()
    state.phaseLimitMs := REVIEW_LIMIT_MS
    state.timeoutPhaseLatch := ""
}

ResetCardState() {
    obj := {}
    obj.questionFree := 0
    obj.answerElapsedMs := 0
    return obj
}

UpdateLevelFields() {
    global state
    state.level := Floor(state.xp / 100) + 1
    state.xpIntoLevel := Mod(state.xp, 100)
    state.xpForNextLevel := 100
}

HardResetSession() {
    global state, card

    state.synced := 0
    state.sessionActive := 0
    state.firstCardFree := 0
    state.phase := "idle"
    state.phaseStartEpochMs := 0
    state.phaseLimitMs := 0
    state.answerShown := 0

    state.currentCardIndex := 0
    state.currentCardId := ""
    state.deckName := ""
    state.isBossCard := 0

    state.answeredCards := 0
    state.skippedCards := 0
    state.score := 0
    state.xp := 0
    state.xpIntoLevel := 0
    state.xpForNextLevel := 100
    state.level := 1

    state.streak := 0
    state.onTimeStreak := 0
    state.onTimeCards := 0
    state.perfectCards := 0
    state.comboMultiplier := 1.0
    state.satelliteColorKey := "easy"
    state.timeoutPhaseLatch := ""

    card := ResetCardState()
    PublishBridge("reset", "Run reset. Press F8 on an unrevealed card to sync.", 0, "Reset")
    VibratePattern("reset")
}

CheckPhaseTimeout() {
    global state
    if (!state.synced)
        return
    if (state.phase = "idle")
        return
    if (state.phaseLimitMs <= 0 || state.phaseStartEpochMs <= 0)
        return

    phaseKey := state.phase . ":" . state.phaseStartEpochMs
    if (state.timeoutPhaseLatch = phaseKey)
        return

    elapsed := MaxValue(0, NowEpochMs() - state.phaseStartEpochMs)
    if (elapsed < state.phaseLimitMs)
        return

    state.timeoutPhaseLatch := phaseKey
    state.streak := 0
    state.onTimeStreak := 0
    state.comboMultiplier := 1.0
    PublishBridge("timeout", "Timeout: streak lost.", 0, "Timeout")
    VibratePattern("timeout")
}

PublishBridge(eventType, eventText, reward := 0, badge := "") {
    global state

    state.lastEventType := eventType
    state.lastEventText := eventText
    state.lastReward := reward
    state.lastBadge := badge
    state.eventNonce += 1

    UpdateLevelFields()
    json := J(state)
    StoreBridgeJson(json)
}

StoreBridgeJson(jsonText) {
    global BRIDGE_FILE
    b64 := Base64EncodeUtf8(jsonText)

    payload := "{""action"":""storeMediaFile"",""version"":6,""params"":{""filename"":""" 
        . EscapeJson(BRIDGE_FILE) 
        . """,""data"":""" 
        . b64 
        . """}}"

    SafeAnkiCommand(payload)
}

SafeAnkiCommand(payload) {
    try {
        whr := ComObjCreate("WinHttp.WinHttpRequest.5.1")
        whr.Open("POST", "http://127.0.0.1:8765", false)
        whr.SetRequestHeader("Content-Type", "application/json")
        whr.Send(payload)
    } catch e {
        MsgBox, 16, AnkiConnect Error, % "HTTP request failed.`n`n" e.Message
    }
}

__HideToolTip:
ToolTip
return

__CheckPhaseTimeout:
CheckPhaseTimeout()
return

NowEpochMs() {
    now := A_NowUTC
    EnvSub, now, 19700101000000, Seconds
    return (now * 1000) + A_MSec
}

Base64EncodeUtf8(text) {
    size := StrPut(text, "UTF-8") - 1
    VarSetCapacity(bin, size, 0)
    StrPut(text, &bin, size + 1, "UTF-8")

    flags := 0x40000001 ; CRYPT_STRING_BASE64 | CRYPT_STRING_NOCRLF
    chars := 0

    DllCall("Crypt32.dll\CryptBinaryToStringW"
        , "Ptr", &bin
        , "UInt", size
        , "UInt", flags
        , "Ptr", 0
        , "UIntP", chars)

    VarSetCapacity(out, chars * 2, 0)

    DllCall("Crypt32.dll\CryptBinaryToStringW"
        , "Ptr", &bin
        , "UInt", size
        , "UInt", flags
        , "Ptr", &out
        , "UIntP", chars)

    return StrGet(&out, chars, "UTF-16")
}

J(val) {
    if IsObject(val) {
        isArray := IsArrayLike(val)
        out := isArray ? "[" : "{"
        first := true

        for k, v in val {
            if (!first)
                out .= ","
            first := false

            if (isArray) {
                out .= J(v)
            } else {
                out .= """" . EscapeJson(k) . """:" . J(v)
            }
        }

        out .= isArray ? "]" : "}"
        return out
    }

    if (val == true)
        return "true"
    if (val == false)
        return "false"
    if (val == "")
        return """""" ; empty string, not null

    if val is number
        return val

    return """" . EscapeJson(val) . """"
}

IsArrayLike(obj) {
    maxIndex := obj.MaxIndex()
    if (maxIndex = "")
        return false

    count := 0
    for k, v in obj {
        count++
        if (k != count)
            return false
    }
    return true
}

EscapeJson(text) {
    text := text . ""
    text := StrReplace(text, "\", "\\")
    text := StrReplace(text, """", "\""")
    text := StrReplace(text, "/", "\/")
    text := StrReplace(text, "`r", "\r")
    text := StrReplace(text, "`n", "\n")
    text := StrReplace(text, "`t", "\t")
    return text
}

InitXInput() {
    global XINPUT_DLL
    dlls := ["xinput1_4.dll", "xinput1_3.dll", "xinput9_1_0.dll"]
    for i, name in dlls {
        h := DllCall("LoadLibrary", "Str", name, "Ptr")
        if (h) {
            XINPUT_DLL := name
            return
        }
    }
    XINPUT_DLL := ""
}

SetRumble(leftMotor, rightMotor, userIndex := 0) {
    global HAPTICS_ENABLED, XINPUT_DLL
    if (!HAPTICS_ENABLED || XINPUT_DLL = "")
        return false

    left := MaxValue(0, MinValue(65535, leftMotor))
    right := MaxValue(0, MinValue(65535, rightMotor))

    VarSetCapacity(vib, 4, 0)
    NumPut(left, vib, 0, "UShort")
    NumPut(right, vib, 2, "UShort")
    rc := DllCall(XINPUT_DLL . "\XInputSetState", "UInt", userIndex, "Ptr", &vib, "UInt")
    return (rc = 0)
}

PulseRumble(durationMs, leftMotor, rightMotor) {
    ok := SetRumble(leftMotor, rightMotor, 0)
    if (!ok)
        return
    Sleep, %durationMs%
    SetRumble(0, 0, 0)
}

VibratePattern(kind) {
    if (kind = "reveal") {
        PulseRumble(90, 42000, 65535)
    } else if (kind = "again") {
        PulseRumble(80, 42000, 58000)
        Sleep, 55
        PulseRumble(80, 42000, 62000)
    } else if (kind = "hard") {
        PulseRumble(95, 24000, 36000)
    } else if (kind = "good") {
        PulseRumble(120, 52000, 65535)
    } else if (kind = "easy") {
        PulseRumble(125, 22000, 30000)
    } else if (kind = "skip") {
        PulseRumble(80, 12000, 19000)
    } else if (kind = "sync") {
        PulseRumble(95, 13000, 18000)
    } else if (kind = "reset") {
        PulseRumble(120, 17000, 26000)
    } else if (kind = "bossStart") {
        PulseRumble(80, 22000, 38000)
        Sleep, 70
        PulseRumble(110, 26000, 43000)
    } else if (kind = "bossClear") {
        PulseRumble(180, 32000, 52000)
    } else if (kind = "timeout") {
        PulseRumble(420, 52000, 65535)
        Sleep, 95
        PulseRumble(180, 36000, 50000)
    }
}

TileAnkiAndCompanion() {
    global EDGE_MATCH, ANKI_MATCH, ANKI_ON_LEFT

    edgeHwnd := WinExist(EDGE_MATCH)
    ankiHwnd := WinExist(ANKI_MATCH)

    if (!ankiHwnd) {
        MsgBox, 48, Not Found, Anki window not found.
        return
    }

    if (!edgeHwnd) {
        MsgBox, 48, Not Found, Edge companion window not found.`n`nExpected title to contain:`nAnki Companion Game V2
        return
    }

    WinGet, ankiMinMax, MinMax, ahk_id %ankiHwnd%
    if (ankiMinMax = -1)
        WinRestore, ahk_id %ankiHwnd%
    WinShow, ahk_id %ankiHwnd%

    WinGet, edgeMinMax, MinMax, ahk_id %edgeHwnd%
    if (edgeMinMax = -1)
        WinRestore, ahk_id %edgeHwnd%
    WinShow, ahk_id %edgeHwnd%

    monIndex := GetWindowMonitor(ankiHwnd)
    GetMonitorWorkArea(monIndex, left, top, right, bottom)

    totalW := right - left
    totalH := bottom - top
    leftW := Floor(totalW / 2)
    rightW := totalW - leftW

    if (ANKI_ON_LEFT) {
        WinMove, ahk_id %ankiHwnd%, , %left%, %top%, %leftW%, %totalH%
        WinMove, ahk_id %edgeHwnd%, , % left + leftW, %top%, %rightW%, %totalH%
    } else {
        WinMove, ahk_id %edgeHwnd%, , %left%, %top%, %leftW%, %totalH%
        WinMove, ahk_id %ankiHwnd%, , % left + leftW, %top%, %rightW%, %totalH%
    }

    WinActivate, ahk_id %edgeHwnd%
    Sleep, 80
    WinActivate, ahk_id %ankiHwnd%
}

MinimizeAnkiAndCompanion() {
    global EDGE_MATCH, ANKI_MATCH

    edgeHwnd := WinExist(EDGE_MATCH)
    ankiHwnd := WinExist(ANKI_MATCH)

    if (edgeHwnd)
        WinMinimize, ahk_id %edgeHwnd%

    if (ankiHwnd)
        WinMinimize, ahk_id %ankiHwnd%
}

GetWindowMonitor(hwnd) {
    WinGetPos, x, y, w, h, ahk_id %hwnd%
    cx := x + (w / 2)
    cy := y + (h / 2)

    SysGet, monCount, MonitorCount
    Loop, %monCount%
    {
        SysGet, mon, Monitor, %A_Index%
        left := monLeft
        top := monTop
        right := monRight
        bottom := monBottom

        if (cx >= left && cx < right && cy >= top && cy < bottom)
            return A_Index
    }
    return 1
}

GetMonitorWorkArea(monIndex, ByRef left, ByRef top, ByRef right, ByRef bottom) {
    SysGet, wa, MonitorWorkArea, %monIndex%
    left := waLeft
    top := waTop
    right := waRight
    bottom := waBottom
}

CeilValue(x) {
    return Ceil(x)
}

MinValue(a, b) {
    return (a < b) ? a : b
}

MaxValue(a, b) {
    return (a > b) ? a : b
}

StrLowerCustom(s) {
    StringLower, out, s
    return out
}


