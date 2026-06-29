// ── Reference data ─────────────────────────────────────────────────────────────
const GESTURE_REF = [
  { emoji:"✊", name:"Fist",        desc:"All fingers closed",   tag:"gesture" },
  { emoji:"🖐", name:"Open Hand",   desc:"All 5 fingers open",   tag:"gesture" },
  { emoji:"☝️", name:"Pointing",    desc:"Index finger only",    tag:"gesture" },
  { emoji:"✌️", name:"Peace / V",   desc:"Index + Middle",       tag:"gesture" },
  { emoji:"👍", name:"Thumbs Up",   desc:"Thumb pointing up",    tag:"gesture" },
  { emoji:"👎", name:"Thumbs Down", desc:"Thumb pointing down",  tag:"gesture" },
  { emoji:"🤙", name:"Hang Loose",  desc:"Thumb + Pinky",        tag:"gesture" },
  { emoji:"🤘", name:"Rock On",     desc:"Index + Pinky",        tag:"gesture" },
  { emoji:"🖖", name:"Four Fingers",desc:"All except thumb",     tag:"gesture" },
  { emoji:"🤙", name:"Pinky Up",    desc:"Only pinky raised",    tag:"gesture" },
];

const DIGIT_REF = [
  { digit:"0", name:"Zero",  desc:"Fist — no fingers",          tag:"digit" },
  { digit:"1", name:"One",   desc:"Index finger only",          tag:"digit" },
  { digit:"2", name:"Two",   desc:"Index + Middle",             tag:"digit" },
  { digit:"3", name:"Three", desc:"Index + Middle + Ring",      tag:"digit" },
  { digit:"4", name:"Four",  desc:"All except thumb",           tag:"digit" },
  { digit:"5", name:"Five",  desc:"All 5 fingers open",         tag:"digit" },
];

// ── DOM ────────────────────────────────────────────────────────────────────────
const dot        = document.getElementById('dot');
const slabel     = document.getElementById('slabel');
const feed       = document.getElementById('feed');
const feedOv     = document.getElementById('feedOv');
const fpsPill    = document.getElementById('fpsPill');
const handsPill  = document.getElementById('handsPill');
const bigDigit   = document.getElementById('bigDigit');
const digitName  = document.getElementById('digitName');
const bigEmoji   = document.getElementById('bigEmoji');
const gestureName= document.getElementById('gestureName');
const colorBar   = document.getElementById('colorBar');
const logList    = document.getElementById('logList');
const clrBtn     = document.getElementById('clrBtn');
const sTot       = document.getElementById('sTot');
const sGest      = document.getElementById('sGest');
const sDigit     = document.getElementById('sDigit');
const sFps       = document.getElementById('sFps');
const refGrid    = document.getElementById('refGrid');
const tabs       = document.querySelectorAll('.tab');

// ── State ──────────────────────────────────────────────────────────────────────
let totalCount = 0, gestureCount = 0, digitCount = 0;
let lastGesture = '', lastLog = 0;
let currentTab = 'both';

// ── Camera ────────────────────────────────────────────────────────────────────
feed.onload = () => { feedOv.classList.add('hidden'); setStatus(true); };
feed.onerror = () => setStatus(false);
function setStatus(ok) {
  dot.className = 'dot ' + (ok ? 'live' : 'err');
  slabel.textContent = ok ? 'Live' : 'Camera error';
}

// ── Render reference grid ──────────────────────────────────────────────────────
function buildRef(tab) {
  refGrid.innerHTML = '';
  const items = tab === 'gesture' ? GESTURE_REF
               : tab === 'digit'   ? DIGIT_REF
               : [...GESTURE_REF, ...DIGIT_REF];
  items.forEach(item => {
    const el = document.createElement('div');
    el.className = 'ref-card ' + (item.tag === 'digit' ? 'digit-card' : '');
    el.innerHTML = item.digit
      ? `<span class="ref-digit">${item.digit}</span>
         <span class="ref-name">${item.name}</span>
         <span class="ref-desc">${item.desc}</span>
         <span class="ref-tag">digit</span>`
      : `<span class="ref-emoji">${item.emoji}</span>
         <span class="ref-name">${item.name}</span>
         <span class="ref-desc">${item.desc}</span>
         <span class="ref-tag">gesture</span>`;
    refGrid.appendChild(el);
  });
}
buildRef('both');

tabs.forEach(t => t.addEventListener('click', () => {
  tabs.forEach(x => x.classList.remove('active'));
  t.classList.add('active');
  currentTab = t.dataset.tab;
  buildRef(currentTab);
}));

// ── Finger indicators ──────────────────────────────────────────────────────────
function updateFingers(fingers) {
  fingers.forEach((v, i) => {
    const circle = document.querySelector(`#f${i} .f-circle`);
    if (!circle) return;
    circle.className = 'f-circle ' + (v ? 'on' : 'off');
  });
}

// ── Log entry ──────────────────────────────────────────────────────────────────
function addLog(data) {
  const empty = logList.querySelector('.log-empty');
  if (empty) empty.remove();

  const time = new Date().toLocaleTimeString([],{hour:'2-digit',minute:'2-digit',second:'2-digit'});
  const li = document.createElement('li');
  li.className = 'log-item';

  const hex = data.color.replace('#','');
  const r = parseInt(hex.slice(0,2),16), g = parseInt(hex.slice(2,4),16), b = parseInt(hex.slice(4,6),16);

  li.innerHTML = `
    <span class="log-num" style="color:${data.color}">${data.digit}</span>
    <span class="log-gest">${data.emoji} ${data.gesture}</span>
    <span class="log-digit">${data.digit_name}</span>
    <span class="log-time">${time}</span>`;
  logList.prepend(li);
  while (logList.children.length > 60) logList.removeChild(logList.lastChild);
}

// ── Pop animation ──────────────────────────────────────────────────────────────
function pop(el) {
  el.classList.remove('pop');
  void el.offsetWidth;
  el.classList.add('pop');
  setTimeout(() => el.classList.remove('pop'), 300);
}

// ── Poll state ─────────────────────────────────────────────────────────────────
async function poll() {
  try {
    const res  = await fetch('/state');
    const data = await res.json();

    fpsPill.textContent  = `${data.fps} FPS`;
    sFps.textContent     = data.fps;

    const hTxt = data.hands === 0 ? 'No hands'
               : data.hands === 1 ? '1 hand' : `${data.hands} hands`;
    handsPill.textContent = hTxt;

    if (data.hands > 0) {
      // Digit display
      bigDigit.textContent   = data.digit ?? '—';
      bigDigit.style.color   = data.color;
      digitName.textContent  = data.digit_name ?? '—';

      // Gesture display
      bigEmoji.textContent   = data.emoji ?? '🖐';
      gestureName.textContent = data.gesture ?? '—';
      gestureName.style.color = data.color;

      // Color bar
      colorBar.style.background = data.color;

      // Finger indicators
      if (data.fingers) updateFingers(data.fingers);

      // Log (debounce)
      const now = Date.now();
      if (data.gesture !== lastGesture && data.gesture !== 'No hand' && now - lastLog > 700) {
        lastGesture = data.gesture;
        lastLog = now;
        totalCount++;
        gestureCount++;
        digitCount++;
        sTot.textContent   = totalCount;
        sGest.textContent  = gestureCount;
        sDigit.textContent = digitCount;
        addLog(data);
        pop(bigDigit);
        pop(bigEmoji);
      }
    } else {
      bigDigit.textContent    = '—';
      bigDigit.style.color    = '#64748b';
      digitName.textContent   = '—';
      bigEmoji.textContent    = '🖐';
      gestureName.textContent = 'Waiting for hand…';
      gestureName.style.color = '#64748b';
      colorBar.style.background = 'var(--border)';
      updateFingers([0,0,0,0,0]);
    }
  } catch(e) {}
  setTimeout(poll, 180);
}

// ── Clear ──────────────────────────────────────────────────────────────────────
clrBtn.addEventListener('click', () => {
  logList.innerHTML = '<li class="log-empty">No detections yet…</li>';
  totalCount = gestureCount = digitCount = 0;
  sTot.textContent = sGest.textContent = sDigit.textContent = '0';
  lastGesture = '';
});

// ── Start ──────────────────────────────────────────────────────────────────────
poll();
