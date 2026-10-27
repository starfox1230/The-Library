#pragma once
#include <cstdint>

struct Settings {
    unsigned holdMs = 140, doubleTapMs = 500, keyPulseMs = 25;
    unsigned toolSettleMs = 75, releaseGapMs = 10;
    bool crosshair = true;
};
struct Output {
    virtual void key(bool down) = 0;
    virtual void left(bool down) = 0;
    virtual void cursor(bool on) = 0;
    virtual ~Output() = default;
};

// OS-independent, single-threaded state machine. No sleeping or nested callbacks.
class Engine {
public:
    enum class Gesture { None, Pending, Second, Consumed };
    enum class Phase { Idle, OnKey, Settle, Active, ReleaseGap, OffKey, TapKey };
    Settings settings;
    Gesture gesture = Gesture::None;
    Phase phase = Phase::Idle;
    explicit Engine(Output& output) : out(output) {}
    void down(uint64_t now) {
        if (gesture != Gesture::None) return;
        if (phase != Phase::Idle) { gesture = Gesture::Consumed; return; }
        stop = false;
        if (tapValid && now - lastTap <= settings.doubleTapMs) {
            gesture = Gesture::Second;
            tapValid = false;
        } else {
            gesture = Gesture::Pending;
            holdDue = now + settings.holdMs;
            tapValid = false;
        }
    }
    void up(uint64_t now) {
        auto old = gesture;
        gesture = Gesture::None;
        if (old == Gesture::Pending) { lastTap = now; tapValid = true; }
        else if (old == Gesture::Second && phase == Phase::Idle) {
            out.key(true); phase = Phase::TapKey; due = now + settings.keyPulseMs;
        } else if (old == Gesture::Consumed) requestStop(now);
    }
    void ctrlUp(uint64_t now) {
        if (phase != Phase::Idle && phase != Phase::TapKey) requestStop(now);
        // A hold that ended on Ctrl-up remains Consumed until right-button-up.
    }
    void cancel(uint64_t now) {
        if (gesture != Gesture::None) gesture = Gesture::Consumed;
        tapValid = false;
        requestStop(now);
    }
    void tick(uint64_t now) {
        if (gesture == Gesture::Pending && now >= holdDue && phase == Phase::Idle) {
            gesture = Gesture::Consumed;
            tapValid = false;
            stop = false;
            out.key(true); phase = Phase::OnKey; due = now + settings.keyPulseMs;
        }
        if (phase == Phase::Active || phase == Phase::Idle || now < due) return;
        switch (phase) {
        case Phase::OnKey:
            out.key(false);
            phase = Phase::Settle; due = now + settings.toolSettleMs;
            if (stop) beginOff(now);
            break;
        case Phase::Settle:
            if (stop) beginOff(now);
            else {
                out.left(true); leftDown = true;
                if (settings.crosshair) out.cursor(true);
                phase = Phase::Active;
            }
            break;
        case Phase::ReleaseGap: beginOff(now); break;
        case Phase::OffKey:
        case Phase::TapKey:
            out.key(false); phase = Phase::Idle; stop = false; break;
        default: break;
        }
    }
    bool idle() const { return phase == Phase::Idle; }
    bool needsTimer() const { return !idle() || gesture == Gesture::Pending; }
private:
    Output& out;
    uint64_t holdDue = 0, due = 0, lastTap = 0;
    bool tapValid = false, stop = false, leftDown = false;
    void requestStop(uint64_t now) {
        stop = true;
        if (phase == Phase::Active) {
            if (leftDown) { out.left(false); leftDown = false; }
            out.cursor(false);
            phase = Phase::ReleaseGap; due = now + settings.releaseGapMs;
        } else if (phase == Phase::Settle) beginOff(now);
    }
    void beginOff(uint64_t now) {
        out.cursor(false);
        out.key(true); phase = Phase::OffKey; due = now + settings.keyPulseMs;
    }
};
