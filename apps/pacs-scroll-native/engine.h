#pragma once
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <limits>

struct ScrollEngine {
    enum class Mode { Off, Hold, Precision, Auto };
    static constexpr double rates[] = {7,12.5,19,25,31,37.5,50,62.5,75,87.5,100,112.5,125,137.5,150,162.5,175,187.5,200,212.5,225,237.5,250};
    Mode mode = Mode::Off;
    int sensitivity = 43, rateIndex = 3, direction = 0, lastDirection = -1;
    int lastY = 0, distance = 0, queued = 0;
    double holdStart = 0, cooldown = 0, nextWheel = 0, spacing = 10, lastMotion = 0;
    double lastEmission = -1e20;
    static constexpr double never = std::numeric_limits<double>::infinity();
    void stop() { mode=Mode::Off; direction=0; distance=0; queued=0; }
    void middle(bool ctrl, double now) {
        if (ctrl) {
            if (mode==Mode::Auto) stop();
            else { stop(); mode=Mode::Auto; direction=lastDirection; nextWheel=now; }
        } else if (mode==Mode::Precision || mode==Mode::Auto) stop();
        else if (mode!=Mode::Hold) { mode=Mode::Hold; holdStart=now; }
    }
    void release() { if (mode==Mode::Hold) stop(); }
    bool launch(double now, int y) {
        if (mode!=Mode::Hold || now-holdStart<300) return false;
        mode=Mode::Precision; lastY=y; direction=0; cooldown=0; distance=queued=0;
        return true;
    }
    void speed(int change, double now) {
        if (mode==Mode::Precision) sensitivity=std::clamp(sensitivity+change,1,50);
        if (mode==Mode::Auto) {
            rateIndex=std::clamp(rateIndex+change,0,22);
            // Preserve the old next deadline on a speed change, then use the new rate.
            nextWheel=std::max(nextWheel,now);
        }
    }
    void wheelDirection(int dir, double now) {
        lastDirection=dir;
        if (mode==Mode::Auto) {
            direction=dir;
            // Never carry an overdue wheel burst through a reversal.
            nextWheel=std::max(nextWheel,now);
        }
    }
    // Called at the original 10 ms sample interval. Caller handles screen wrapping.
    void sample(int y,double now) {
        if (mode!=Mode::Precision) return;
        if (now<cooldown) { lastY=y; distance=queued=0; return; }
        int diff=y-lastY;
        if (!diff) return;
        lastMotion=now;
        int dir=diff>0 ? -1 : 1; // Win32 wheel: negative is down.
        if (direction && dir!=direction) {
            direction=0; distance=queued=0; cooldown=now+50; lastY=y; return;
        }
        int clicks=0;
        if (!direction) { direction=dir; clicks=1; distance=0; }
        else {
            distance+=std::abs(diff);
            int threshold=51-sensitivity;
            clicks=distance/threshold; distance%=threshold;
        }
        if (clicks) {
            // Spread ticks over the sample window instead of one burst. Bound old
            // work under overload; never replay a delayed mountain of wheel input.
            spacing=std::max(1.0,10.0/clicks);
            if (!queued) nextWheel=std::max(now,lastEmission+spacing);
            queued=std::min(64,queued+clicks);
        }
        lastY=y;
    }
    bool emit(double now,int& dir) {
        if (mode==Mode::Auto) {
            if (now+0.001<nextWheel) return false;
            dir=direction; lastDirection=dir; lastEmission=now;
            double period=1000.0/rates[rateIndex];
            // Use absolute phase at normal cadence, but skip overdue deadlines.
            nextWheel+=period;
            if (nextWheel<now+period*0.5) nextWheel=now+period;
            return true;
        }
        if (mode==Mode::Precision) {
            if (now-lastMotion>100) queued=0;
            if (!queued || now<cooldown || now+0.001<nextWheel) return false;
            --queued; dir=direction; lastDirection=dir; lastEmission=now;
            nextWheel=now+spacing; return true;
        }
        return false;
    }
    double deadline() const {
        if (mode==Mode::Auto) return nextWheel;
        if (mode==Mode::Precision && queued) return nextWheel;
        if (mode==Mode::Hold) return holdStart+300;
        return never;
    }
};
