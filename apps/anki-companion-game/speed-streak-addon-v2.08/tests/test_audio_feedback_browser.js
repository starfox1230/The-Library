"use strict";

const assert = require("assert");
const path = require("path");

const instances = [];

class FakeAudio {
  constructor() {
    this.preload = "";
    this.src = "";
    this.volume = 1;
    this.paused = true;
    this.ended = false;
    this.currentTime = 0;
    this.readyState = 1;
    this.playCount = 0;
    this.pauseCount = 0;
    instances.push(this);
  }

  load() {}

  play() {
    this.paused = false;
    this.playCount += 1;
    return Promise.resolve();
  }

  pause() {
    this.paused = true;
    this.pauseCount += 1;
  }

  addEventListener(_name, callback) {
    callback();
  }
}

global.window = {};
global.Audio = FakeAudio;
require(path.join(__dirname, "..", "web", "audio_feedback.js"));

const player = global.window.SpeedStreakAudio;
assert.ok(player);
assert.strictEqual(player.prepare("sound.mp3"), true);
assert.strictEqual(instances.length, 1);

assert.strictEqual(
  player.play("sound.mp3", {
    channel: "feedback",
    interrupt: true,
    volumePercent: 0,
  }),
  true
);
const firstFeedback = instances[0];
assert.strictEqual(firstFeedback.playCount, 1);
assert.strictEqual(firstFeedback.volume, 0);

assert.strictEqual(
  player.play("sound.mp3", {
    channel: "feedback",
    interrupt: true,
    volumePercent: 200,
  }),
  true
);
const secondFeedback = instances[1];
assert.notStrictEqual(secondFeedback, firstFeedback);
assert.strictEqual(firstFeedback.pauseCount, 1);
assert.strictEqual(secondFeedback.volume, 1);

assert.strictEqual(
  player.play("tick.mp3", {
    channel: "countdown",
    interrupt: true,
    volumePercent: 100,
  }),
  true
);
const countdown = instances[3];
assert.strictEqual(secondFeedback.pauseCount, 0);
player.stop("countdown");
assert.strictEqual(countdown.pauseCount, 1);
assert.strictEqual(secondFeedback.pauseCount, 0);

assert.strictEqual(
  player.play("alignment.mp3", {
    channel: "alignment",
    interrupt: true,
    volumePercent: 100,
    positionMs: 135,
  }),
  true
);
const alignment = instances[5];
assert.strictEqual(alignment.currentTime, 0.135);

console.log("browser audio player checks passed");
