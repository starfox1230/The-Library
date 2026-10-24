/* A local, accessible curve editor; points are data, never executable content. */
window.AfterglowCurveEditor = {
  create({ H, E, play, stop, save }) {
    const $ = id => document.getElementById(id);
    const dialog = $('hapticEditorDialog'), graph = $('curveGraph');
    const ns = 'http://www.w3.org/2000/svg';
    let curve, selected = 0, dragging = null, previewTimer;
    const clamp = (n, lo, hi) => Math.min(hi, Math.max(lo, n));
    const layer = () => $('curveLayer').value;
    const point = () => curve.points[selected];
    function svg(tag, attributes, text) {
      const el = document.createElementNS(ns, tag);
      Object.entries(attributes).forEach(([k,v]) => el.setAttribute(k,v));
      if (text !== undefined) el.textContent = text;
      return el;
    }
    const xy = p => [30 + p.at / curve.durationMs * 540, 260 - p[layer()] * 230];
    function stopPreview() {
      clearTimeout(previewTimer); previewTimer = null;
      stop(); graph.classList.remove('playing');
    }
    function draw() {
      graph.replaceChildren();
      for(let i=0;i<=4;i++) {
        const y=30+i*57.5;
        graph.append(svg('line',{x1:30,y1:y,x2:570,y2:y,class:'curve-grid'}));
        graph.append(svg('text',{x:24,y:y+4,'text-anchor':'end',class:'curve-axis'},`${100-i*25}`));
      }
      for(let i=0;i<=4;i++) {
        const x=30+i*135;
        graph.append(svg('line',{x1:x,y1:30,x2:x,y2:260,class:'curve-grid'}));
        graph.append(svg('text',{x,y:287,'text-anchor':'middle',class:'curve-axis'},`${(curve.durationMs*i/4000).toFixed(2)}s`));
      }
      const coords=curve.points.map(xy);
      graph.append(svg('path',{d:`M30 260 L${coords.map(p=>p.join(' ')).join(' L')} L570 260 Z`,class:'curve-area'}));
      graph.append(svg('polyline',{points:coords.map(p=>p.join(',')).join(' '),class:'curve-line'}));
      curve.points.forEach((p,i)=> {
        const [cx,cy]=xy(p);
        graph.append(svg('circle',{cx,cy,r:18,class:'curve-hit','data-point':i,tabindex:0,role:'button','aria-label':`Point ${i+1}, ${Math.round(p.at)} milliseconds, ${Math.round(p[layer()]*100)} percent. Arrow keys adjust; Delete removes.`}));
        graph.append(svg('circle',{cx,cy,r:i===selected?8:6,class:i===selected?'curve-dot selected':'curve-dot','pointer-events':'none'}));
      });
      graph.append(svg('line',{x1:30,y1:30,x2:30,y2:260,class:'curve-playhead'}));
      $('curveLengthLabel').textContent=`${(curve.durationMs/1000).toFixed(2)} seconds`;
      $('curveLayerLabel').textContent=layer()==='intensity'?'RUMBLE STRENGTH':'SHARPNESS';
    }
    function fields() {
      $('curvePoint').replaceChildren(...curve.points.map((p,i)=>new Option(`${i+1} · ${Math.round(p.at)} ms`,i)));
      $('curvePoint').value=String(selected);
      $('pointTime').value=Math.round(point().at);
      $('pointTime').disabled=selected===0||selected===curve.points.length-1;
      $('pointTime').min=selected?curve.points[selected-1].at+10:0;
      $('pointTime').max=selected<curve.points.length-1?curve.points[selected+1].at-10:curve.durationMs;
      $('pointIntensity').value=Math.round(point().intensity*100);
      $('pointSharpness').value=Math.round(point().sharpness*100);
      $('removeCurvePoint').disabled=selected===0||selected===curve.points.length-1;
      $('addCurvePoint').disabled=curve.points.length>=32;
    }
    function render() { draw(); fields(); }
    function add(at, value) {
      if(curve.points.length>=32) { $('curveStatus').textContent='Maximum 32 points. Remove a point to make room.'; return false; }
      at=Math.round(clamp(at,10,curve.durationMs-10));
      const right=curve.points.findIndex(p=>p.at>at);
      if(right<1 || at-curve.points[right-1].at<10 || curve.points[right].at-at<10) return false;
      const p=H.sampleCurve(curve,at);
      if(value!==undefined) p[layer()]=value;
      curve.points.splice(right,0,p); selected=right;
      return true;
    }
    function remove() {
      if(selected===0||selected===curve.points.length-1) return;
      stopPreview(); curve.points.splice(selected,1); selected=Math.min(selected,curve.points.length-1); render();
    }
    function move(event) {
      // Use SVG coordinates, including letterboxing on short phone screens.
      const p=new DOMPoint(event.clientX,event.clientY).matrixTransform(graph.getScreenCTM().inverse());
      return {at:clamp((p.x-30)/540*curve.durationMs,0,curve.durationMs),value:clamp((260-p.y)/230,0,1),x:p.x,y:p.y};
    }
    graph.addEventListener('pointerdown',event=> {
      if(!event.isPrimary||event.button!==0) return;
      event.preventDefault(); stopPreview();
      const hit=event.target.closest('[data-point]');
      const pos=move(event);
      if(hit) selected=Number(hit.dataset.point);
      else {
        const nearest=curve.points.map((p,i)=>{const [x,y]=xy(p);return {i,distance:Math.hypot(x-pos.x,y-pos.y)};}).sort((a,b)=>a.distance-b.distance)[0];
        if(nearest.distance<40) selected=nearest.i;
        else if(!add(pos.at,pos.value)) return;
      }
      dragging=event.pointerId;
      graph.setPointerCapture(event.pointerId); render();
    });
    graph.addEventListener('pointermove',event=> {
      if(dragging!==event.pointerId) return;
      const pos=move(event), p=point();
      if(selected>0&&selected<curve.points.length-1) p.at=Math.round(clamp(pos.at,curve.points[selected-1].at+10,curve.points[selected+1].at-10));
      p[layer()]=pos.value; render();
    });
    for(const name of ['pointerup','pointercancel','lostpointercapture']) graph.addEventListener(name,()=>{dragging=null;});
    graph.addEventListener('keydown',event=> {
      const hit=event.target.closest('[data-point]'); if(!hit) return;
      selected=Number(hit.dataset.point);
      const key=event.key;
      if(!['ArrowUp','ArrowDown','ArrowLeft','ArrowRight','Delete','Backspace'].includes(key)) return;
      event.preventDefault(); stopPreview();
      if(key==='Delete'||key==='Backspace') remove();
      else {
        const p=point();
        if(key==='ArrowUp'||key==='ArrowDown') p[layer()]=clamp(p[layer()]+(key==='ArrowUp'?.05:-.05),0,1);
        else if(selected>0&&selected<curve.points.length-1) p.at=clamp(p.at+(key==='ArrowRight'?10:-10),curve.points[selected-1].at+10,curve.points[selected+1].at-10);
        render();
      }
      graph.querySelector(`[data-point="${selected}"]`)?.focus();
    });
    $('curvePoint').onchange=()=>{selected=Number($('curvePoint').value);render();};
    $('curveLayer').onchange=draw;
    $('removeCurvePoint').onclick=remove;
    $('addCurvePoint').onclick=()=> {
      stopPreview();
      const gaps=curve.points.slice(1).map((p,i)=>({at:(p.at+curve.points[i].at)/2,gap:p.at-curve.points[i].at})).sort((a,b)=>b.gap-a.gap);
      if(!add(gaps[0].at)) $('curveStatus').textContent='No space for another point. Increase the length first.';
      render();
    };
    for(const [id,key] of [['pointTime','at'],['pointIntensity','intensity'],['pointSharpness','sharpness']]) {
      const update=()=> {
        const input=$(id), value=Number(input.value);
        if(input.value===''||!Number.isFinite(value)||!input.checkValidity())return false;
        stopPreview();
        if(key==='at' && !$('pointTime').disabled) point().at=Math.round(clamp(value,curve.points[selected-1].at+10,curve.points[selected+1].at-10));
        else if(key!=='at') point()[key]=clamp(value/100,0,1);
        draw();return true;
      };
      $(id).oninput=update;
      $(id).onchange=()=>{update();fields();};
    }
    function updateDuration(resetInvalid = true) {
      stopPreview();
      if(!$('curveDuration').checkValidity()||!$('curveDuration').value) { if(resetInvalid)$('curveDuration').value=curve.durationMs/1000; return; }
      const next=Math.round(Number($('curveDuration').value)*1000), ratio=next/curve.durationMs;
      const old=E.clone(curve);
      curve.points=curve.points.map(p=>({...p,at:Math.round(p.at*ratio)})).filter((p,i,all)=>i===0||i===all.length-1||p.at-all[i-1].at>=10);
      if(curve.points.at(-1).at-curve.points.at(-2).at<10) curve.points.splice(-2,1);
      curve.durationMs=next;
      if(!E.validCustomHaptic(curve)) { curve=old; $('curveDuration').value=curve.durationMs/1000; $('curveStatus').textContent='Points are too close for this length. Remove a few first.'; }
      selected=0;render();
    }
    $('curveDuration').oninput=()=>updateDuration(false);
    $('curveDuration').onchange=()=>updateDuration();
    $('curveSnap').onchange=()=>{stopPreview();curve.snap=$('curveSnap').checked;};
    $('testCurve').onclick=()=> {
      stopPreview(); const result=play(H.curvePattern(curve));
      $('curveStatus').textContent=result.muted?'Visual preview · the master Haptics switch is off.':result.mode==='none'?'Visual preview · this browser has no haptic API. Test in Brrrowser on your phone.':`Testing curve · ${result.mode==='hd'?'HD haptics':'standard vibration'}`;
      graph.style.setProperty('--haptic-duration',`${result.duration||H.duration(H.curvePattern(curve))}ms`);
      void graph.getBoundingClientRect(); graph.classList.add('playing');
      previewTimer=setTimeout(stopPreview,(result.duration||H.duration(H.curvePattern(curve)))+80);
    };
    $('stopCurve').onclick=stopPreview;
    $('saveCurve').onclick=()=> {
      const name=$('curveName').value.trim();
      if(!name) { $('curveName').focus(); $('curveStatus').textContent='Give this curve a name.'; return; }
      curve.name=name;
      if(!E.validCustomHaptic(curve)) { $('curveStatus').textContent='Check the curve values before saving.'; return; }
      stopPreview(); if(save(E.clone(curve))) dialog.close();
    };
    dialog.addEventListener('close',()=>{if(previewTimer!==null&&previewTimer!==undefined)stopPreview();dragging=null;});
    document.addEventListener('visibilitychange',()=>{if(document.hidden)stopPreview();});
    return { open(pattern=null) {
      stopPreview(); selected=0;
      curve=pattern?H.toCurve(pattern,pattern.id.startsWith('custom-')?pattern.id:`custom-${E.id()}`):{id:`custom-${E.id()}`,name:'My crescendo',durationMs:1000,snap:true,points:[{at:0,intensity:.08,sharpness:.1},{at:500,intensity:.4,sharpness:.25},{at:1000,intensity:.95,sharpness:.7}]};
      if(pattern&&!pattern.id.startsWith('custom-')) curve.name=`${pattern.name} remix`.slice(0,60);
      $('curveName').value=curve.name; $('curveDuration').value=curve.durationMs/1000; $('curveSnap').checked=curve.snap;
      $('curveStatus').textContent=''; $('curveLayer').value='intensity';
      render(); if(!dialog.open)dialog.showModal();
    }, stop:stopPreview };
  }
};
