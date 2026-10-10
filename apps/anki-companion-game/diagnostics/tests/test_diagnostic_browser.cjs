const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync(__dirname + '/../diagnostic_browser.js', 'utf8');
const events = [], listeners = {}, audioListeners = {};
let polls = 0, plays = 0;
const sentinel = Promise.resolve('complete');
const actuator = {playEffect() { plays++; return sentinel; }};
const pads = [{index:0,connected:true,vibrationActuator:actuator}];
const context = {Date, Math, Array, Object, Number, JSON,
  pycmd(message) { events.push(JSON.parse(message.split('speed-streak:diagnostic:')[1])); },
  document:{hidden:false,addEventListener(event, fn) {listeners[event] = fn;}},
  window:{addEventListener(event, fn) {listeners[event] = fn;}},
  navigator:{getGamepads() {polls++; return pads;}}};
vm.createContext(context);
vm.runInContext(source, context);
assert.equal(polls, 0, 'logging must not initialize/poll controller services');
assert.strictEqual(context.navigator.getGamepads(), pads);
assert.equal(polls, 1);
assert.strictEqual(actuator.playEffect('dual-rumble', {duration:80}), sentinel);
assert.equal(plays, 1);
assert(events.some(event => event.event === 'haptic_request'));
vm.runInContext(source, context);
actuator.playEffect('dual-rumble', {duration:80});
assert.equal(plays, 2);
assert.equal(events.filter(event => event.event === 'document_loaded').length, 1);
listeners.unhandledrejection({reason:{name:'InvalidStateError',message:'private text'}});
assert.equal(events.at(-1).error, 'InvalidStateError');
assert(!JSON.stringify(events).includes('private text'));
context.window.SpeedStreakDiagnostic.observeAudio({error:{code:3},addEventListener(event, fn) {audioListeners[event] = fn;}});
audioListeners.error();
assert.equal(events.at(-1).event, 'audio_error');
assert.equal(events.at(-1).error, 3);
console.log('Browser observation preserves calls, return values, promise identity, and startup polling behavior.');
