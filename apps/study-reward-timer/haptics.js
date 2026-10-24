/* Brrrowser's documented native bridge, with standard Vibration API fallback. */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.AfterglowHaptics = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';
  const DEFAULT = 'rise-snap';
  const tap = (at, intensity = .55, sharpness = .65) => ({ at, intensity, sharpness });
  const buzz = (at, duration, intensity, sharpness = .2) => ({ at, duration, intensity, sharpness });
  const ramp = (count, step, from = .12, to = .9, sharp = .15) => Array.from({ length: count }, (_, i) => buzz(i * step, step, from + (to - from) * i / (count - 1), sharp + .45 * i / (count - 1)));
  const preset = (id, name, group, description, events, vibration = null) => ({ id, name, group, description, events, vibration });
  const patterns = [
    preset('rise-snap', 'Crescendo + snap', 'Build & finish', 'A warm buzz builds, takes a breath, then clicks shut.', [...ramp(6, 90), tap(620, 1, .95)]),
    preset('power-up', 'Power up', 'Build & finish', 'Four rising steps with a firm final lock.', [tap(0,.2,.2), tap(110,.35,.35), tap(210,.55,.5), tap(300,.75,.7), tap(450,1,.9)]),
    preset('charge-release', 'Charge & release', 'Build & finish', 'A longer, smoother build with a sharp release.', [...ramp(10, 90), tap(1000,1,1)]),
    preset('lift-off', 'Lift off', 'Build & finish', 'Accelerating taps lift into a bright finishing buzz.', [tap(0,.18,.2),tap(140,.28,.3),tap(260,.4,.4),tap(360,.55,.5),tap(440,.7,.65),buzz(500,160,.9,.8),tap(760,1,.95)]),
    preset('level-up', 'Level up', 'Build & finish', 'Three little builds, then a clean double finish.', [buzz(0,100,.25,.2),buzz(150,130,.5,.4),buzz(330,160,.8,.6),tap(580,.7,.75),tap(680,1,.95)]),
    preset('spark-lock', 'Spark & lock', 'Build & finish', 'A quick flutter gathers into one decisive click.', [tap(0,.2,.4),tap(65,.3,.45),tap(125,.45,.55),tap(180,.6,.65),tap(230,.8,.8),tap(380,1,1)]),
    preset('classic', 'Original double tap', 'Crisp & short', 'The original Afterglow completion rhythm.', [tap(0,.5,.6),tap(56,.8,.8)], [16,40,24]),
    preset('clean-click', 'Clean click', 'Crisp & short', 'One precise, mechanical click.', [{at:0,preset:'rigid',intensity:.8,sharpness:1}]),
    preset('soft-click', 'Soft click', 'Crisp & short', 'One rounded, cushioned tap.', [{at:0,preset:'soft',intensity:.4,sharpness:.1}]),
    preset('double-click', 'Double click', 'Crisp & short', 'Two crisp taps, with more weight on the second.', [tap(0,.5,.8),tap(100,.9,.9)]),
    preset('triple-click', 'Triple click', 'Crisp & short', 'A compact three-tap flourish.', [tap(0,.35,.65),tap(80,.6,.8),tap(170,.9,.95)]),
    preset('native-success', 'iPhone success', 'Crisp & short', 'Brrrowser’s native success notification; a short double tap elsewhere.', [{at:0,preset:'success',intensity:.7,sharpness:.6}], [20,65,35]),
    preset('coin-drop', 'Coin drop', 'Tactile rhythms', 'A light drop, a bounce, and a solid deposit.', [tap(0,.35,.8),tap(145,.25,.7),tap(260,.8,.5)]),
    preset('ratchet', 'Ratchet lock', 'Tactile rhythms', 'Tiny ratchet teeth tighten into a final click.', [...Array.from({length:8},(_,i)=>tap(i*65,.2+i*.07,.85)),tap(650,1,.95)]),
    preset('ripple', 'Ripple', 'Tactile rhythms', 'A clear center tap with softer ripples trailing away.', [tap(0,.9,.6),tap(110,.65,.5),tap(220,.4,.4),tap(340,.2,.25)]),
    preset('heartbeat', 'Heartbeat', 'Tactile rhythms', 'Two rounded beats, followed by a reassuring second pair.', [tap(0,.65,.15),tap(95,.4,.1),tap(420,.75,.2),tap(515,.45,.1)]),
    preset('rolling-wave', 'Rolling wave', 'Soft & smooth', 'A rounded wave rises and settles without a hard snap.', [...ramp(5,85,.15,.75,.05),...Array.from({length:4},(_,i)=>buzz(425+i*85,85,.65-i*.15,.2))]),
    preset('velvet-finish', 'Velvet finish', 'Soft & smooth', 'A gentle continuous swell and a soft closing tap.', [...ramp(5,85,.12,.65,.02),tap(530,.5,.12)]),
    preset('breathing', 'Breathing pulse', 'Soft & smooth', 'Two slow, rounded waves with space between them.', [buzz(0,100,.2,.05),buzz(100,100,.5,.12),buzz(200,100,.25,.05),buzz(500,100,.25,.05),buzz(600,100,.65,.15),buzz(700,100,.25,.05)]),
    preset('celebration', 'Victory flourish', 'Big finish', 'A rolling build and a bright three-tap payoff.', [...ramp(6,80,.15,.85,.2),tap(580,.5,.7),tap(690,.75,.85),tap(840,1,1)]),
    preset('rumble-pop', 'Rumble + pop', 'Big finish', 'A low-textured rumble resolves into a sharp pop.', [buzz(0,180,.35,.05),buzz(180,180,.6,.1),buzz(360,180,.85,.2),tap(650,1,1)]),
    preset('orbit', 'Orbit & land', 'Big finish', 'Three distinct pulses circle into a firm landing.', [buzz(0,70,.35,.2),buzz(180,90,.55,.4),buzz(390,110,.75,.6),tap(660,1,.85)])
  ];
  const get = id => patterns.find(p => p.id === id) || patterns[0];
  // Vibration API cannot set amplitude. Duty cycles approximate the envelope.
  function vibrationFor(pattern) {
    if (pattern.vibration) return [...pattern.vibration];
    const segments = [];
    let cursor = 0;
    function append(on, ms) {
      ms = Math.round(ms);
      if (ms <= 0) return;
      if (!segments.length && !on) segments.push(0);
      const nextOn = segments.length % 2 === 0;
      if (nextOn === on) segments.push(ms);
      else segments[segments.length - 1] += ms;
    }
    for (const event of pattern.events) {
      append(false, event.at - cursor);
      const length = event.duration || Math.round(12 + event.intensity * 25);
      const on = event.duration ? Math.max(8, Math.round(length * event.intensity)) : length;
      append(true, on); append(false, length - on);
      cursor = event.at + length;
    }
    if (segments.length % 2 === 0) segments.pop();
    return segments;
  }
  const duration = pattern => Math.max(pattern.events.reduce((max,e) => Math.max(max,e.at+(e.duration || (e.preset === 'success' ? 260 : 50))),0), vibrationFor(pattern).reduce((a,b)=>a+b,0));
  function createPlayer(nav, schedule = setTimeout, cancel = clearTimeout) {
    let timers = [], generation = 0;
    function stop() {
      generation++;
      timers.forEach(cancel); timers = [];
      try { if (typeof nav.vibrate === 'function') nav.vibrate(0); } catch { /* Optional bridge. */ }
      // Native calls are bounded to short segments; there is no documented HD stop API.
    }
    function capability() { return typeof nav.haptic === 'function' ? 'hd' : typeof nav.vibrate === 'function' ? 'standard' : 'none'; }
    function play(id, { engine = 'auto', strength = 80 } = {}) {
      stop();
      const pattern = get(id), token = generation;
      let fallbackStarted = false;
      const fallback = () => {
        if (fallbackStarted || token !== generation) return;
        fallbackStarted = true; timers.forEach(cancel); timers = [];
        if (typeof nav.vibrate !== 'function') return;
        try { nav.vibrate(vibrationFor(pattern)); } catch { /* Never interrupt a completed case. */ }
      };
      const mode = engine === 'standard' ? (typeof nav.vibrate === 'function' ? 'standard' : 'none') : capability();
      if (mode === 'none') return { mode, duration: 0, pattern };
      if (mode === 'standard') fallback();
      else {
        const gain = Math.max(.1, Math.min(1, Number(strength) / 100 || .8));
        const send = event => {
          if (token !== generation || fallbackStarted) return;
          try {
            // System presets retain their documented shape and fixed strength.
            const value = event.preset || [{ intensity: Math.min(1,event.intensity*gain), sharpness: event.sharpness, ...(event.duration ? {duration:event.duration} : {}) }];
            const result = nav.haptic(value);
            if (result === false) fallback();
            else if (result && typeof result.catch === 'function') result.catch(fallback);
          } catch { fallback(); }
        };
        pattern.events.forEach(event => {
          if (event.at === 0) send(event);
          else if (!fallbackStarted) timers.push(schedule(() => send(event), event.at));
        });
      }
      return { mode: fallbackStarted ? (typeof nav.vibrate === 'function' ? 'standard' : 'none') : mode, duration: duration(pattern), pattern };
    }
    return { play, stop, capability };
  }
  return { DEFAULT, patterns, get, vibrationFor, duration, createPlayer };
});
