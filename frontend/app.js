const state = {
  frames: [],
  candidates: [],
  spectrumWavelength: [],
  spectrumFlux: [],
  index: 0,
  view: 'sky',
  blinkTimer: null,
  selected: null,
};

const $ = (id) => document.getElementById(id);
const canvas = $('skyCanvas');
const ctx = canvas.getContext('2d');
const spectrumCanvas = $('spectrumCanvas');
const spectrumCtx = spectrumCanvas.getContext('2d');

function setStatus(text, live=false){ $('status').textContent=text; $('status').style.color = live ? 'var(--accent2)' : 'var(--accent)'; }
function dateOnly(iso){ return new Date(iso).toISOString().slice(0,10); }

function renderFrame(){
  if (!state.frames.length) return;
  const frame = state.frames[state.index];
  const img = new Image();
  img.onload = () => {
    ctx.clearRect(0,0,canvas.width,canvas.height);
    if(state.view === 'sky') ctx.drawImage(img,0,0,canvas.width,canvas.height);
    else renderDifference();
    drawCandidateMarkers();
  };
  img.src = frame.image_data_url;
  $('epochLabel').textContent = frame.label;
  $('frameDate').textContent = dateOnly(frame.timestamp);
  $('timeline').value = state.index;
}

function renderDifference(){
  if(state.index === 0){
    ctx.fillStyle='#07080c'; ctx.fillRect(0,0,canvas.width,canvas.height);
    ctx.fillStyle='#9299aa'; ctx.font='18px system-ui'; ctx.textAlign='center';
    ctx.fillText('Difference starts at epoch 2', canvas.width/2, canvas.height/2);
    return;
  }
  const a = new Image(); const b = new Image();
  a.onload = () => { b.onload = () => {
    const ca=document.createElement('canvas'), cb=document.createElement('canvas');
    ca.width=cb.width=canvas.width; ca.height=cb.height=canvas.height;
    const xa=ca.getContext('2d'), xb=cb.getContext('2d');
    xa.drawImage(a,0,0,canvas.width,canvas.height); xb.drawImage(b,0,0,canvas.width,canvas.height);
    const A=xa.getImageData(0,0,canvas.width,canvas.height).data;
    const B=xb.getImageData(0,0,canvas.width,canvas.height).data;
    const out=ctx.createImageData(canvas.width,canvas.height);
    for(let i=0;i<A.length;i+=4){
      const d=(B[i]-A[i]); const m=Math.min(255,Math.abs(d)*8);
      out.data[i]=d>0?m:0; out.data[i+1]=d<0?m:0;
      out.data[i+2]=Math.min(255,Math.abs(d)*3); out.data[i+3]=255;
    }
    ctx.putImageData(out,0,0); drawCandidateMarkers();
  }; b.src=state.frames[state.index].image_data_url; };
  a.src=state.frames[state.index-1].image_data_url;
}

function drawCandidateMarkers(){
  if(!state.candidates.length) return;
  for(const c of state.candidates){
    const px = c.x / 256 * canvas.width; const py = c.y / 256 * canvas.height;
    ctx.beginPath(); ctx.arc(px,py,7,0,Math.PI*2); ctx.strokeStyle = '#d6ff4b'; ctx.lineWidth=2; ctx.stroke();
    ctx.beginPath(); ctx.moveTo(px-12,py);ctx.lineTo(px+12,py);ctx.moveTo(px,py-12);ctx.lineTo(px,py+12);
    ctx.strokeStyle='rgba(214,255,75,.6)';ctx.lineWidth=1;ctx.stroke();
  }
}

function renderCandidates(){
  $('candidateCount').textContent=state.candidates.length;
  const el=$('candidateList');
  if(!state.candidates.length){el.innerHTML='<div class="empty">No candidates in this sequence.</div>';return;}
  el.innerHTML=state.candidates.map((c,i)=>`<div class="candidate ${state.selected===i?'selected':''}" data-index="${i}">
    <div class="candidate-top"><span><strong>${c.id}</strong></span><span class="candidate-type">${c.kind}</span></div>
    <div class="candidate-meta"><div>Motion<strong>${c.motion_px.toFixed(2)} px</strong></div><div>S/N<strong>${c.snr.toFixed(1)}</strong></div><div>Score<strong>${Math.round(c.score*100)}%</strong></div><div>Vector<strong>${c.dx.toFixed(2)}, ${c.dy.toFixed(2)}</strong></div></div>
  </div>`).join('');
  el.querySelectorAll('.candidate').forEach(n=>n.addEventListener('click',()=>{
    state.selected=Number(n.dataset.index); renderCandidates();
    $('selectedCandidate').textContent=state.candidates[state.selected].id; drawCandidateMarkers();
  }));
}

function renderSpectrum(){
  const w=spectrumCanvas.width, h=spectrumCanvas.height; spectrumCtx.clearRect(0,0,w,h);
  spectrumCtx.fillStyle='#090c12'; spectrumCtx.fillRect(0,0,w,h);
  if(!state.spectrumWavelength.length)return;
  const pad=36, minX=0.75,maxX=5;
  const minY=Math.min(...state.spectrumFlux), maxY=Math.max(...state.spectrumFlux);
  spectrumCtx.strokeStyle='#222737'; spectrumCtx.lineWidth=1;
  for(let i=0;i<5;i++){const y=pad+i*(h-2*pad)/4;spectrumCtx.beginPath();spectrumCtx.moveTo(pad,y);spectrumCtx.lineTo(w-pad,y);spectrumCtx.stroke();}
  spectrumCtx.beginPath();
  state.spectrumWavelength.forEach((xv,i)=>{
    const x=pad+(xv-minX)/(maxX-minX)*(w-2*pad);
    const y=h-pad-(state.spectrumFlux[i]-minY)/(maxY-minY)*(h-2*pad);
    if(i===0)spectrumCtx.moveTo(x,y);else spectrumCtx.lineTo(x,y);
  });
  spectrumCtx.strokeStyle='#7ef6ff'; spectrumCtx.lineWidth=2; spectrumCtx.stroke();
}

async function loadDemo(){
  setStatus('LOADING DEMO…');
  const r=await fetch('/api/demo'); if(!r.ok) throw new Error(await r.text());
  const data=await r.json();
  state.frames=data.frames; state.candidates=data.candidates;
  state.spectrumWavelength=data.spectrum_wavelength_um; state.spectrumFlux=data.spectrum_flux_ujy;
  state.index=0;state.selected=null;
  $('timeline').max=state.frames.length-1;
  $('timelineLeft').textContent=dateOnly(state.frames[0].timestamp);
  $('timelineRight').textContent=dateOnly(state.frames.at(-1).timestamp);
  renderCandidates();renderSpectrum();renderFrame();setStatus('OFFLINE DEMO');
}

async function liveSearch(){
  const ra=Number($('ra').value),dec=Number($('dec').value),radius=Number($('radius').value),w=Number($('wavelength').value);
  if(!Number.isFinite(ra)||!Number.isFinite(dec)||!Number.isFinite(radius))throw new Error('Enter valid coordinates and radius.');
  setStatus('QUERYING IRSA…',true);
  const p=new URLSearchParams({ra,dec,radius_deg:radius});if(Number.isFinite(w)&&w>0)p.set('wavelength_um',w);
  const r=await fetch('/api/search?'+p); if(!r.ok) throw new Error((await r.json().catch(()=>({detail:r.statusText}))).detail);
  const data=await r.json();
  const obs=data.observations.slice().sort((a,b)=>(a.start_mjd??0)-(b.start_mjd??0));
  state.frames=[]; state.candidates=[]; state.selected=null; renderCandidates();
  setStatus(`LIVE • ${obs.length} OBS`,true);
  if(!obs.length){
    $('epochLabel').textContent='No matching observations'; $('frameDate').textContent='Try a larger radius';
    ctx.fillStyle='#07080c';ctx.fillRect(0,0,canvas.width,canvas.height); return;
  }
  const previews=[];
  for(const [i,o] of obs.slice(0,6).entries()){
    if(!o.access_url) continue;
    try{
      const pp=new URLSearchParams({url:o.access_url,ra:String(ra),dec:String(dec),size_deg:String(Math.min(radius,.25))});
      const pr=await fetch('/api/preview?'+pp); if(!pr.ok) continue;
      const pd=await pr.json();
      previews.push({id:o.obs_id,timestamp:new Date((o.start_mjd-40587)*86400000).toISOString(),label:`SPHEREx ${i+1}`,image_data_url:pd.image_data_url,candidate_count:0});
    }catch(_err){}
  }
  state.frames=previews; $('timeline').max=Math.max(0,state.frames.length-1);
  if(state.frames.length){
    $('timelineLeft').textContent=dateOnly(state.frames[0].timestamp);
    $('timelineRight').textContent=dateOnly(state.frames.at(-1).timestamp);
    state.index=0; renderFrame();
  }else{
    $('epochLabel').textContent='IRSA metadata received'; $('frameDate').textContent=`${obs.length} observations found`;
    ctx.fillStyle='#07080c';ctx.fillRect(0,0,canvas.width,canvas.height);
    ctx.fillStyle='#9299aa';ctx.textAlign='center';ctx.font='17px system-ui';
    ctx.fillText('Archive metadata received.',canvas.width/2,canvas.height/2-12);
    ctx.fillText('No preview could be rendered yet.',canvas.width/2,canvas.height/2+18);
  }
}

$('demoBtn').addEventListener('click',()=>loadDemo().catch(e=>alert(e.message)));
$('searchBtn').addEventListener('click',()=>liveSearch().catch(e=>{setStatus('LIVE ERROR');alert(e.message)}));
$('resetBtn').addEventListener('click',()=>loadDemo().catch(()=>{}));
$('timeline').addEventListener('input',e=>{state.index=Number(e.target.value);renderFrame();});
$('prevBtn').addEventListener('click',()=>{if(state.frames.length){state.index=Math.max(0,state.index-1);renderFrame();}});
$('nextBtn').addEventListener('click',()=>{if(state.frames.length){state.index=Math.min(state.frames.length-1,state.index+1);renderFrame();}});
$('blinkBtn').addEventListener('click',()=>{
  if(state.blinkTimer){clearInterval(state.blinkTimer);state.blinkTimer=null;$('blinkBtn').textContent='▶ BLINK EPOCHS';return;}
  $('blinkBtn').textContent='■ STOP BLINK';
  state.blinkTimer=setInterval(()=>{state.index=(state.index+1)%state.frames.length;renderFrame();},650);
});
document.querySelectorAll('.tab').forEach(btn=>btn.addEventListener('click',()=>{
  document.querySelectorAll('.tab').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');state.view=btn.dataset.view;renderFrame();
}));

loadDemo().catch(e=>{console.error(e);setStatus('DEMO ERROR')});
