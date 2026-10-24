/* Hold lifecycle is clock-injected so the deadline and cancellation can be tested. */
(function(root,factory) {
  const api=factory();
  if(typeof module==='object'&&module.exports)module.exports=api;else root.AfterglowGestures=api;
})(typeof globalThis!=='undefined'?globalThis:this,function() {
  function createHold({begin,cancel,complete,progress=()=>{},now=()=>performance.now(),schedule=setTimeout,clear=clearTimeout,frame=requestAnimationFrame,cancelFrame=cancelAnimationFrame}) {
    let active=false,started=0,timer=null,animation=null;
    function reset() {active=false;clear(timer);cancelFrame(animation);timer=animation=null;progress(0,false);}
    function finish() {if(!active)return;reset();complete();}
    function tick() {if(!active)return;progress(Math.min(1,(now()-started)/1000),true);animation=frame(tick);}
    return {
      start() {if(active||!begin())return false;active=true;started=now();progress(0,true);timer=schedule(finish,1000);animation=frame(tick);return true;},
      release() {if(!active)return;if(now()-started>=1000)finish();else{reset();cancel();}},
      cancel() {if(!active)return;reset();cancel();},
      isActive:()=>active
    };
  }
  function bind({face,completeButton,main,toggle,openDuration,canInteract,holdEnabled,hold}) {
    let tap=null,pressTimer=null,completePointer=null,completeKey=null;
    const pointers=new Set();
    const clearTap=()=>{clearTimeout(pressTimer);pressTimer=null;tap=null;};
    const cancelAll=()=>{clearTap();completePointer=null;completeKey=null;hold.cancel();};
    document.addEventListener('pointerdown',event=> {
      pointers.add(event.pointerId);
      if(pointers.size>1)cancelAll();
    },true);
    for(const name of ['pointerup','pointercancel']) document.addEventListener(name,event=>pointers.delete(event.pointerId),true);
    main.addEventListener('pointerdown',event=> {
      if(!event.isPrimary||event.button!==0||pointers.size>1||!canInteract()||event.target.closest('button,input,textarea,select,a,summary,label,[contenteditable],dialog'))return;
      clearTap();tap={id:event.pointerId,x:event.clientX,y:event.clientY,at:performance.now(),long:false};
      if(face.contains(event.target))pressTimer=setTimeout(()=> {
        if(!tap||!canInteract())return;
        tap.long=true;openDuration();
      },500);
    });
    document.addEventListener('pointermove',event=> {
      if(tap?.id===event.pointerId&&Math.hypot(event.clientX-tap.x,event.clientY-tap.y)>10)clearTap();
      if(completePointer===event.pointerId) {
        const r=completeButton.getBoundingClientRect();
        if(event.clientX<r.left-8||event.clientX>r.right+8||event.clientY<r.top-8||event.clientY>r.bottom+8) {completePointer=null;hold.cancel();}
      }
    });
    document.addEventListener('pointerup',event=> {
      if(completePointer===event.pointerId) {completePointer=null;hold.release();}
      if(tap?.id!==event.pointerId)return;
      const shouldToggle=!tap.long&&performance.now()-tap.at<500&&canInteract();
      clearTap();if(shouldToggle)toggle();
    });
    document.addEventListener('pointercancel',cancelAll);
    completeButton.addEventListener('pointerdown',event=> {
      if(!holdEnabled()||!event.isPrimary||event.button!==0||pointers.size>1||!canInteract())return;
      event.preventDefault();clearTap();
      if(hold.start()){completePointer=event.pointerId;completeButton.setPointerCapture(event.pointerId);}
    });
    completeButton.addEventListener('lostpointercapture',()=>{if(completePointer!==null){completePointer=null;hold.cancel();}});
    completeButton.addEventListener('click',event=>{if(holdEnabled()){event.preventDefault();event.stopImmediatePropagation();}},true);
    completeButton.addEventListener('keydown',event=> {
      if(!holdEnabled()||!['Space','Enter'].includes(event.code))return;
      event.preventDefault();if(!event.repeat&&completeKey===null&&canInteract()&&hold.start())completeKey=event.code;
    });
    completeButton.addEventListener('keyup',event=>{if(completeKey===event.code){event.preventDefault();completeKey=null;hold.release();}});
    completeButton.addEventListener('blur',()=>{if(completeKey!==null){completeKey=null;hold.cancel();}});
    face.addEventListener('keydown',event=> {
      if(!['Space','Enter'].includes(event.code)||event.repeat||!canInteract())return;
      event.preventDefault();event.stopPropagation();if(event.shiftKey)openDuration();else toggle();
    });
    window.addEventListener('blur',cancelAll);
    document.addEventListener('visibilitychange',()=>{if(document.hidden)cancelAll();});
    return {cancel:cancelAll};
  }
  return {createHold,bind};
});
