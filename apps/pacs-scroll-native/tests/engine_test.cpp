#include "../engine.h"
#include <cassert>
#include <iostream>
int main() {
    using M=ScrollEngine::Mode;
    ScrollEngine e; int dir=0;
    assert(e.sensitivity==43 && e.rateIndex==3);
    e.middle(false,0); assert(e.mode==M::Hold);
    assert(!e.launch(299,500)); e.release(); assert(e.mode==M::Off);
    e.middle(false,1000); assert(e.launch(1300,500)); e.release(); assert(e.mode==M::Precision);
    e.sample(501,1310); assert(e.emit(1310,dir)&&dir==-1);
    e.sample(508,1320); assert(!e.emit(1320,dir));
    e.sample(509,1330); assert(e.emit(1330,dir));
    e.sample(508,1340); assert(!e.emit(1340,dir)); assert(e.cooldown==1390);
    e.sample(500,1389); assert(!e.emit(1389,dir));
    e.sample(499,1390); assert(e.emit(1390,dir)&&dir==1);
    for(int i=0;i<100;++i) {e.speed(1,1400); } assert(e.sensitivity==50);
    for(int i=0;i<100;++i) {e.speed(-1,1400); } assert(e.sensitivity==1);
    e.middle(false,1500); assert(e.mode==M::Off);
    e.middle(true,1600); assert(e.mode==M::Auto); assert(e.emit(1600,dir)&&dir==1);
    assert(!e.emit(1639,dir)); assert(e.emit(1640,dir));
    e.wheelDirection(-1,1641); assert(e.emit(1680,dir)&&dir==-1);
    assert(e.emit(10000,dir)); assert(!e.emit(10000,dir)); assert(!e.emit(10001,dir));
    e.middle(false,10002); assert(e.mode==M::Off);
    e.middle(true,11000); e.middle(true,11001); assert(e.mode==M::Off);
    // Every original rate: exact normal cadence, no backlog burst after a stall.
    for(int rate=0;rate<23;++rate) {
        ScrollEngine a; a.rateIndex=rate; a.middle(true,0);
        double period=1000.0/ScrollEngine::rates[rate];
        for(int i=0;i<1000;++i) { assert(a.emit(i*period,dir)); assert(!a.emit(i*period,dir)); }
        assert(a.emit(1000000,dir)); assert(!a.emit(1000000.1,dir));
    }
    // Precision ticks are separate and expire rather than piling up after a stall.
    ScrollEngine p; p.middle(false,0); p.launch(300,500); p.sample(501,310); p.emit(310,dir);
    p.sample(901,320); assert(p.queued==50); assert(p.emit(320,dir));
    assert(!p.emit(320,dir)); assert(p.emit(321,dir));
    assert(!p.emit(500,dir)); assert(p.queued==0);
    p.sample(800,510); assert(!p.emit(510,dir)); p.stop(); assert(!p.emit(1000,dir));
    std::cout<<"All gestures, threshold/halt, speed bounds, 23 rates, 23,000 cadence checks and stall/reversal tests passed.\n";
}
