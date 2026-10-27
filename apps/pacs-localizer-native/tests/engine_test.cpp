#include "../engine.h"
#include <cassert>
#include <iostream>
#include <string>
#include <vector>
struct Recorder : Output {
    std::vector<std::string> events;
    void key(bool d) override { events.push_back(d ? "F+" : "F-"); }
    void left(bool d) override { events.push_back(d ? "L+" : "L-"); }
    void cursor(bool d) override { if (d) events.push_back("C+"); }
};
int main() {
    { Recorder r; Engine e(r); e.down(0); e.up(50); e.tick(1000); assert(r.events.empty()); }
    { Recorder r; Engine e(r); e.down(0); e.up(50); e.down(200); e.tick(1000);
      assert(r.events.empty()); e.up(1100); e.tick(1125);
      assert((r.events == std::vector<std::string>{"F+", "F-"})); }
    { Recorder r; Engine e(r); e.down(0); e.tick(139); assert(r.events.empty());
      e.tick(140); e.tick(165); e.tick(239); assert(r.events.size() == 2);
      e.tick(240); e.up(300); e.tick(310); e.tick(335);
      assert((r.events == std::vector<std::string>{"F+","F-","L+","C+","L-","F+","F-"}));
      assert(e.idle()); }
    { Recorder r; Engine e(r); e.down(0); e.tick(140); e.up(141); e.tick(165); e.tick(190);
      assert((r.events == std::vector<std::string>{"F+","F-","F+","F-"})); }
    { Recorder r; Engine e(r); e.down(0); e.tick(140); e.tick(165); e.tick(240);
      e.ctrlUp(250); e.tick(260); e.tick(285); e.up(300);
      e.down(400); e.tick(540); assert(e.phase == Engine::Phase::OnKey); }
    { Recorder r; Engine e(r); e.down(0); e.cancel(30); e.tick(1000); e.up(1001);
      e.down(1100); e.tick(1240); assert(e.phase == Engine::Phase::OnKey); }
    { Recorder r; Engine e(r); e.down(0); e.tick(140); e.tick(165); e.up(166);
      e.down(167); e.tick(191); e.up(200); assert(e.idle());
      assert((r.events == std::vector<std::string>{"F+","F-","F+","F-"})); }
    // Long random streams: no overlapping F12 pulses, unbalanced mouse holds,
    // or duplicate activation/off sequences, including cancellation mid-pulse.
    unsigned seed = 19;
    for (int trial = 0; trial < 200; ++trial) {
        Recorder r; Engine e(r); uint64_t t = 0;
        for (int i = 0; i < 1000; ++i) {
            seed = seed * 1664525u + 1013904223u; t += (seed >> 16) % 60;
            switch (seed % 5) { case 0:e.down(t);break; case 1:e.up(t);break;
              case 2:e.ctrlUp(t);break; case 3:e.cancel(t);break; default:e.tick(t); }
            e.tick(t);
        }
        e.cancel(t); e.up(t);
        for (int i=0;i<10;++i) e.tick(t += 1000);
        bool key=false, left=false;
        for (const auto& event : r.events) {
            if (event=="F+") { assert(!key); key=true; }
            if (event=="F-") { assert(key); key=false; }
            if (event=="L+") { assert(!left && !key); left=true; }
            if (event=="L-") { assert(left); left=false; }
        }
        assert(!key && !left && e.idle());
    }
    std::cout << "Gesture cases and 200,000 randomized transitions passed.\n";
}
