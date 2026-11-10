/* Optional foreground alerts. No timer or reward mutations. */
(function(root,factory){
  const api=factory();
  if(typeof module==='object'&&module.exports)module.exports=api;else root.AfterglowAlerts=api;
})(typeof globalThis!=='undefined'?globalThis:this,()=>{
  'use strict';
  // Skip stale boundaries after sleep instead of replaying a queue of reminders.
  function crossing(previous,current,now) {
    if(!previous||previous.id!==current.id||!previous.running||!current.running||now-previous.at>2000||current.spent<previous.spent)return {};
    return {minute:Math.floor(current.spent/60000)>Math.floor(previous.spent/60000),
      remaining:Math.ceil(current.left/60000)<Math.ceil(previous.left/60000)&&current.left>0,
      deadline:previous.left>0&&current.left<=0};
  }
  function create({haptics,navigator,getState,elapsed,status=()=>{},onAlarm=()=>{},clock=Date.now,env=globalThis}) {
    const player=haptics.createPlayer(navigator);
    const bell=env.Audio?new env.Audio('alarm.wav'):null;
    if(bell){bell.loop=true;bell.preload='auto';}
    let previous=null, alarmId=null, audioUntil=0, vibrationUntil=0, nextBeat=0, nextWave=0, preview=false, mutedId=null, utterance=null, speechUntil=0;
    function stop(){
      if(alarmId)mutedId=alarmId;
      alarmId=null;audioUntil=0;vibrationUntil=0;preview=false;
      onAlarm(false);player.stop();if(bell){bell.pause();bell.currentTime=0;}
      if(utterance){env.speechSynthesis?.cancel();utterance=null;}speechUntil=0;
    }
    function unlock(){
      // Best effort media activation during a deliberate tap, without audible output.
      if(bell&&!audioUntil){bell.muted=true;const attempt=bell.play();attempt?.then(()=>{if(!audioUntil){bell.pause();bell.currentTime=0;}bell.muted=false;}).catch(()=>{bell.muted=false;});}
    }
    function play(event){
      const s=getState(),config=s.settings.hapticEvents[event];
      if(!s.settings.haptics||!config.enabled)return;
      const result=player.play(haptics.get(config.pattern,s.customHaptics),config);
      if(result.mode==='none')status('Haptics are unavailable in this browser.');
      return result;
    }
    function testHaptic(){
      stop();
      const s=getState(),config=s.settings.hapticEvents.minute;
      let message;
      if(!s.settings.haptics)message='Turn on the master Haptics switch above to test.';
      else if(!config.enabled)message='Minute feedback is off. Tap Customize and enable feedback for this action.';
      else {
        const result=play('minute'),pattern=haptics.get(config.pattern,s.customHaptics);
        if(result.mode==='none')message='Haptics unavailable here. On iPhone, use Brrrowser; Safari cannot vibrate.';
        else message=`Sent ${pattern.name} · ${result.mode==='hd'?`HD strength ${config.strength}%`:'standard vibration (phone controls strength)'}. Try it in your pocket.${s.settings.alerts.minuteHaptic?'':' Turn on Minute reminder for automatic pulses.'}`;
      }
      status(message);return message;
    }
    function announce(count,test=false){
      const a=getState().settings.alerts;
      if(!a.spokenMinutes){if(test)status('Turn on Announce minutes remaining to preview.');return;}
      if(!env.speechSynthesis||!env.SpeechSynthesisUtterance){status('Spoken announcements are unavailable in this browser.');return;}
      if(utterance)env.speechSynthesis.cancel();
      utterance=new env.SpeechSynthesisUtterance(`${count}${a.speakUnits?count===1?' minute':' minutes':''}`);
      utterance.lang='en-US';utterance.rate=1; speechUntil=clock()+5000;
      utterance.onerror=()=>{status('The device could not speak. Try Test announcement after enabling sound.');utterance=null;};
      utterance.onend=()=>{utterance=null;speechUntil=0;};
      env.speechSynthesis.speak(utterance);
      if(test)status('Previewing 2 minutes with your device’s voice.');
    }
    function alarm(test=false){
      stop();const s=getState(),a=s.settings.alerts,now=clock();
      preview=test;alarmId=test?'preview':s.active?.id;
      audioUntil=a.audioAlarm?now+a.audioSeconds*1000:0;
      vibrationUntil=a.vibrationAlarm&&s.settings.haptics?now+a.vibrationSeconds*1000:0;
      nextBeat=0;
      if(audioUntil&&bell){bell.muted=false;bell.currentTime=0;bell.play()?.catch(()=>{audioUntil=0;status('Audio was blocked. Tap Test time-up alarms to enable playback.');});}
      if(test)status(audioUntil||vibrationUntil?'Previewing enabled time-up alarms. Tap Stop alerts to end early.':'Enable a time-up alarm to preview it.');
      onAlarm(!!(audioUntil||vibrationUntil));
      service(now);
    }
    function service(now){
      if(audioUntil&&now>=audioUntil){bell?.pause();audioUntil=0;}
      if(vibrationUntil&&now>=vibrationUntil){player.stop();vibrationUntil=0;}
      if(vibrationUntil&&now>=nextBeat){play('alarm');nextBeat=now+Math.max(1600,haptics.duration(haptics.get(getState().settings.hapticEvents.alarm.pattern,getState().customHaptics))+350);}
      if(!audioUntil&&!vibrationUntil){alarmId=null;preview=false;onAlarm(false);}
      if(speechUntil&&now>=speechUntil){env.speechSynthesis?.cancel();utterance=null;speechUntil=0;}
    }
    function tick(){
      const s=getState(),a=s.active,now=clock();
      const current=a?{id:a.id,running:a.runningSince!==null&&!a.holding,spent:elapsed(a,now),at:now}:null;
      if(current)current.left=a.targetMs-current.spent;
      if(alarmId&&!preview&&(!current||current.id!==alarmId||!current.running))stop();
      if(previous&&(!current||current.id!==previous.id||(previous.running&&!current.running))) {if(!preview)stop();nextWave=0;}
      const events=current?crossing(previous,current,now):{};
      previous=current;
      if(events.deadline&&mutedId!==current.id){alarm();return;}
      service(now);
      if(!current?.running||current.left<=0||alarmId)return;
      if(events.minute&&s.settings.alerts.minuteHaptic)play('minute');
      if(events.remaining)announce(Math.ceil(current.left/60000));
      if(s.settings.alerts.warningHaptic&&current.left<=s.settings.alerts.warningMinutes*60000&&now>=nextWave){
        // Let minute reminders finish before another wave.
        if(!events.minute)play('warning');
        nextWave=now+Math.max(3000,haptics.duration(haptics.get(s.settings.hapticEvents.warning.pattern,s.customHaptics))+350);
      }
    }
    return {tick,stop,unlock,announce,alarm,testHaptic};
  }
  return {create,crossing};
});
