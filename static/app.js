let S={tech:[],hr:[],round:'technical',idx:0,answers:{},techId:null,hrId:null,cid:null};
let rec=null,recOn=false;

// Offline fallback: identical set, used if /api/default-questions is unreachable
// (e.g. old server still running). Guarantees Qs always show.
const FALLBACK_TECH=[
"Explain OOP concepts (encapsulation, inheritance, polymorphism, abstraction) with an example.",
"What is the difference between SQL and NoSQL databases? When would you use each?",
"What is a REST API? Explain GET, POST, PUT and DELETE with an example.",
"Explain process vs thread. What is a deadlock and how do you prevent it?",
"What is the difference between TCP and UDP? Give a use case for each.",
"How does Git work? Explain commit, branch, merge and how you resolve a merge conflict.",
"Explain Big-O notation. Compare the time complexity of linear search vs binary search.",
"What is normalization in DBMS? Explain 1NF, 2NF and 3NF briefly.",
"Your code crashes in production. Walk me through how you debug and fix it step by step.",
"Explain your final year project: your role, tech stack, and biggest challenge."];
const FALLBACK_HR=[
"Tell me about yourself and walk me through your resume.",
"Why should we hire you for this role? What are your key strengths?",
"Describe a challenging team situation or conflict and how you handled it.",
"Where do you see yourself in 2-3 years? How does this role fit?",
"Tell me about a failure or mistake. What did you learn?",
"How do you handle pressure or tight deadlines? Give an example."];

// Hardcoded defaults so section 2 works before any upload (view + practice only)
async function loadDefaults(){
  try{
    const r=await fetch('/api/default-questions').then(r=>{if(!r.ok)throw 0;return r.json();});
    S.tech=r.technical.map((q,i)=>({id:-(i+1),...q}));
    S.hr=r.hr.map((q,i)=>({id:-(100+i),...q}));
  }catch(e){
    S.tech=FALLBACK_TECH.map((t,i)=>({id:-(i+1),text:t,skill_tag:'general',difficulty:'conceptual'}));
    S.hr=FALLBACK_HR.map((t,i)=>({id:-(100+i),text:t,skill_tag:'hr',difficulty:'behavioral'}));
    document.getElementById('prog').innerText='Offline practice set (restart server for latest: uvicorn app:app --reload)';
  }
  render();
}
loadDefaults();

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
function cur(){return S.round==='technical'?S.tech:S.hr;}
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
  if(!iid){alert('Upload a resume first to save and evaluate this round (defaults are practice-only).');return;}
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
