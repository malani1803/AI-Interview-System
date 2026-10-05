let S={tech:[],hr:[],round:'technical',idx:0,answers:{},techId:null,hrId:null,cid:null};
let rec=null,recOn=false;

async function upload(){
  const fd=new FormData();
  fd.append('name',document.getElementById('name').value);
  fd.append('email',document.getElementById('email').value);
  const f=document.getElementById('file').files[0];
  if(!f){alert('choose resume file');return;}
  fd.append('file',f);
  const r=await fetch('/api/upload',{method:'POST',body:fd}).then(r=>r.json());
  S.cid=r.candidate_id;S.tech=r.technical;S.hr=r.hr;S.techId=r.tech_interview_id;S.hrId=r.hr_interview_id;
  S.idx=0;S.answers={};
  document.getElementById('skills').innerText='Skills: '+r.skills.join(', ');
  showRound('technical');
}
function cur(){return S[S.round];}
function showRound(r){S.round=r;S.idx=0;render();}
function render(){
  const q=cur()[S.idx];
  document.getElementById('qbox').innerText=q?`Q${S.idx+1}/${cur().length}: ${q.text}`:'done';
  document.getElementById('ans').value=S.answers[q?.id]||'';
  document.getElementById('prog').innerText=`${S.round} - Q ${Math.min(S.idx+1,cur().length)}/${cur().length}`;
}
function nextQ(){
  const q=cur()[S.idx];if(!q)return;
  S.answers[q.id]=document.getElementById('ans').value;
  if(S.idx<cur().length-1){S.idx++;render();}else alert('round complete - submit now');
}
async function submitRound(){
  nextQ0();
  const iid=S.round==='technical'?S.techId:S.hrId;
  const payload={interview_id:iid,answers:Object.entries(S.answers)
    .filter(([qid])=>cur().some(q=>q.id==qid))
    .map(([qid,t])=>({question_id:+qid,transcript:t}))};
  const r=await fetch('/api/submit',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)}).then(r=>r.json());
  document.getElementById('fb').innerText=`${S.round} overall: ${r.overall}/10\n${r.summary}\nRec: ${r.recommendation}\nStrengths: ${(r.strengths||[]).join(' | ')}\nGaps: ${(r.gaps||[]).join(' | ')}`;
}
function nextQ0(){const q=cur()[S.idx];if(q)S.answers[q.id]=document.getElementById('ans').value;}
async function loadHistory(){
  if(!S.cid){alert('upload first');return;}
  const h=await fetch('/api/history/'+S.cid).then(r=>r.json());
  document.getElementById('hist').textContent=JSON.stringify(h.slice(0,30),null,1);
}
// Web Speech API voice -> text (free, realtime in browser)
function toggleMic(){
  const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
  if(!SR){alert('Voice not supported - type instead (Chrome recommended)');return;}
  if(recOn){rec.stop();return;}
  rec=new SR();rec.lang='en-IN';rec.interimResults=true;rec.continuous=true;
  rec.onresult=e=>{
    let t='';for(const r of e.results)t+=r[0].transcript;
    document.getElementById('ans').value=t;
    document.getElementById('micState').innerText='listening... (interim preview)';
  };
  rec.onend=()=>{recOn=false;document.getElementById('micBtn').innerText='🎤 Start voice';document.getElementById('micState').innerText='mic off';};
  rec.start();recOn=true;
  document.getElementById('micBtn').innerText='⏹ Stop';
}
