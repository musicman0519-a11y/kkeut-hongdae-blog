// 의료광고 모니터링 — 홈페이지 이벤트 페이지 캡처 (헤드리스 Chrome + CDP, 외부 패키지 없음)
// 사용법: node scripts/admon/capture.js --clinics data/admon/clinics.csv --sites data/admon/sites.json --out captures/2026-11 [--only "미소앤봄의원,나인의원"] [--max-pages 8]
// 동작: 포함=Y 인 의원마다 홈 → 보이는 팝업 각각 → 이벤트 URL(설정 + 홈에서 발견한 링크) 전체 페이지 캡처.
//       403/429/503 또는 차단 제목이면 blocked.csv 에 기록하고 그 사이트는 더 시도하지 않는다. UA 위장·우회 없음.
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

const args = Object.fromEntries(process.argv.slice(2).map((a, i, arr) => a.startsWith('--') ? [a.slice(2), arr[i + 1] && !arr[i + 1].startsWith('--') ? arr[i + 1] : true] : []).filter(Boolean));
const CLINICS = args.clinics || 'data/admon/clinics.csv';
const SITES = args.sites || 'data/admon/sites.json';
const OUT = args.out || 'captures/2026-11';
const ONLY = args.only ? String(args.only).split(',').map(s => s.trim()) : null;
const MAX_PAGES = +(args['max-pages'] || 8);
const WIDTH = 1280, SCALE = 1.5, MAX_H = 40000, GAP_MS = 3000;
const CHROME = process.env.CHROME_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const EVENT_RE = /(event|이벤트|promotion|프로모션|price|가격|특가|할인|첫방문|first)/i;
const BLOCK_RE = /(forbidden|403|access denied|차단|blocked|firewall|bot)/i;

const sleep = ms => new Promise(r => setTimeout(r, ms));
const safe = s => s.replace(/[\u{1F000}-\u{1FFFF}\u{2600}-\u{27BF}\u{FE0F}]/gu, '').replace(/[\\/:*?"<>|\r\n\t]+/g, '_').replace(/\s+/g, ' ').trim().slice(0, 50) || 'page';
const nowIso = () => new Date().toISOString();

function parseCsv(text) {
  const rows = []; let row = [], field = '', q = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (q) { if (c === '"') { if (text[i + 1] === '"') { field += '"'; i++; } else q = false; } else field += c; }
    else if (c === '"') q = true;
    else if (c === ',') { row.push(field); field = ''; }
    else if (c === '\n' || c === '\r') { if (c === '\r' && text[i + 1] === '\n') i++; row.push(field); rows.push(row); row = []; field = ''; }
    else field += c;
  }
  if (field || row.length) { row.push(field); rows.push(row); }
  const [h, ...rest] = rows.filter(r => r.length > 1);
  return rest.map(r => Object.fromEntries(h.map((k, i) => [k.replace(/^\uFEFF/, ''), r[i] ?? ''])));
}

async function launch() {
  const port = 9400 + Math.floor(Math.random() * 100);
  const proc = spawn(CHROME, ['--headless=new', '--disable-gpu', '--hide-scrollbars', `--remote-debugging-port=${port}`,
    '--autoplay-policy=no-user-gesture-required', '--user-data-dir=' + path.join(require('os').tmpdir(), 'admon-chrome-' + port), 'about:blank'], { stdio: 'ignore' });
  let targets;
  for (let i = 0; i < 60; i++) { try { targets = await (await fetch(`http://127.0.0.1:${port}/json`)).json(); break; } catch { await sleep(250); } }
  const page = targets.find(t => t.type === 'page');
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  let id = 0; const pending = {}; const listeners = [];
  const send = (method, params = {}) => new Promise((res, rej) => { const i = ++id; pending[i] = { res, rej }; ws.send(JSON.stringify({ id: i, method, params })); });
  ws.onmessage = e => { const m = JSON.parse(e.data); if (m.id && pending[m.id]) { (m.error ? pending[m.id].rej(new Error(m.error.message)) : pending[m.id].res(m.result)); delete pending[m.id]; } else if (m.method) listeners.forEach(f => f(m)); };
  await new Promise(r => ws.onopen = r);
  await send('Page.enable'); await send('Runtime.enable'); await send('Network.enable');
  const close = () => { try { ws.close(); } catch {} try { require('child_process').execSync(`taskkill /PID ${proc.pid} /T /F`, { stdio: 'ignore' }); } catch { proc.kill(); } };
  return { send, on: f => listeners.push(f), close };
}

async function evalJs(cdp, expr) { return (await withTimeout(cdp.send('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true }), 60000, 'evaluate')).result.value; }

async function navigate(cdp, url) {
  let status = null, finalUrl = url;
  const handler = m => { if (m.method === 'Network.responseReceived' && m.params.type === 'Document' && status === null) { status = m.params.response.status; finalUrl = m.params.response.url; } };
  cdp.on(handler);
  await cdp.send('Emulation.setDeviceMetricsOverride', { width: WIDTH, height: 900, deviceScaleFactor: SCALE, mobile: false });
  let navErr = null;
  try { const r = await withTimeout(cdp.send('Page.navigate', { url }), 45000, 'navigate'); if (r.errorText) navErr = r.errorText; } catch (e) { navErr = e.message; }
  await sleep(4000);
  const title = navErr ? '' : await evalJs(cdp, 'document.title');
  return { status, finalUrl, title, navErr };
}

async function calmPage(cdp) {
  await evalJs(cdp, `(()=>{try{document.querySelectorAll("video,audio").forEach(v=>{try{v.pause();v.removeAttribute("autoplay");v.muted=true;}catch{}});const st=document.createElement("style");st.textContent="*,*::before,*::after{animation:none!important;transition:none!important;scroll-behavior:auto!important}";document.head.appendChild(st);}catch{}return true;})()`);
}
async function scrollAll(cdp) {
  await calmPage(cdp);
  // 느린 이미지 로딩을 위해 끝까지 스크롤한 뒤 맨 위로
  await evalJs(cdp, `(async()=>{const h=()=>document.documentElement.scrollHeight;let y=0;while(y<h()&&y<${MAX_H}){window.scrollTo(0,y);await new Promise(r=>setTimeout(r,150));y+=600;}window.scrollTo(0,0);await new Promise(r=>setTimeout(r,800));return h();})()`);
}

const SEG = 5000; // 한 장의 세로 길이(css px). 1.5배율이면 7500px → Chrome 텍스처 한계(16384) 안쪽
async function fullPage(cdp, file, lite = false) {
  const h = Math.min(await evalJs(cdp, 'document.documentElement.scrollHeight'), MAX_H);
  const files = [];
  const seg = lite ? 1200 : SEG, scale = lite ? 1 : SCALE, tmo = lite ? 150000 : 90000;
  for (let y = 0, i = 1; y < h; y += seg, i++) {
    const segH = Math.min(seg, h - y);
    // 뷰포트를 조각 높이로 맞추고 스크롤한 뒤 보이는 영역만 찍는다(clip·captureBeyondViewport 는 큰 페이지에서 멈춤)
    await cdp.send('Emulation.setDeviceMetricsOverride', { width: WIDTH, height: segH, deviceScaleFactor: scale, mobile: false });
    // 두 번째 조각부터는 고정(fixed/sticky) 요소를 숨겨 겹침을 막는다
    await evalJs(cdp, `(()=>{window.scrollTo(0, ${y}); if (${y} > 0) { for (const el of document.querySelectorAll('body *')) { const ps = getComputedStyle(el).position; if (ps === 'fixed' || ps === 'sticky') el.style.setProperty('visibility', 'hidden', 'important'); } } return new Promise(r => setTimeout(r, 700)); })()`);
    const shot = await withTimeout(cdp.send('Page.captureScreenshot', { format: 'png' }), tmo, 'captureScreenshot');
    const f = h > seg ? file.replace(/\.png$/, `_p${i}.png`) : file;
    fs.writeFileSync(f, Buffer.from(shot.data, 'base64'));
    files.push(path.basename(f));
  }
  return { height: h, truncated: h >= MAX_H, files };
}
function withTimeout(p, ms, what) { return Promise.race([p, new Promise((_, rej) => setTimeout(() => rej(new Error(`timeout ${what} ${ms}ms`)), ms))]); }


// 페이지 안의 큰 이미지(광고 배너 원본)를 그대로 내려받는다 — 스크린샷보다 선명하고 팝업 슬라이드(숨은 탭)도 모두 포함
async function harvestImages(cdp, dir, meta, label) {
  const list = await evalJs(cdp, `(()=>{const out=[];const seen=new Set();for(const i of document.images){const u=i.currentSrc||i.src;if(!u||!/^https?:/.test(u)||seen.has(u))continue;if(i.naturalWidth>=500&&i.naturalHeight>=300){seen.add(u);out.push({u,w:i.naturalWidth,h:i.naturalHeight,alt:(i.alt||'').slice(0,60)});}}return out.slice(0,40);})()`);
  const idir = path.join(dir, 'imgs'); fs.mkdirSync(idir, { recursive: true });
  meta.images = meta.images || [];
  let k = 0;
  for (const im of list) {
    if (meta.images.some(x => x.url === im.u)) continue;
    try {
      const res = await fetch(encodeURI(decodeURI(im.u)), { headers: { 'Referer': meta.homepage } });
      if (!res.ok) { meta.notes.push(`img ${res.status} ${im.u.slice(0, 80)}`); continue; }
      const buf = Buffer.from(await res.arrayBuffer());
      const ext = (res.headers.get('content-type') || '').includes('png') ? 'png' : (res.headers.get('content-type') || '').includes('webp') ? 'webp' : 'jpg';
      const file = `${safe(label)}_${String(++k).padStart(2, '0')}.${ext}`;
      fs.writeFileSync(path.join(idir, file), buf);
      meta.images.push({ file: 'imgs/' + file, url: im.u, w: im.w, h: im.h, alt: im.alt, page: label, bytes: buf.length });
    } catch (e) { meta.notes.push(`img_fail ${im.u.slice(0, 80)} ${e.message}`); }
  }
  if (k) console.log(`      이미지 ${k}장 저장 (${label})`);
}

async function visiblePopups(cdp) {
  return evalJs(cdp, `(()=>{const out=[];const seen=new Set();for(const el of document.querySelectorAll('[class*="popup"],[id*="popup"],[class*="modal"],[class*="layer"],[class*="Popup"],[class*="Modal"]')){const cs=getComputedStyle(el);if(cs.display==='none'||cs.visibility==='hidden'||+cs.opacity===0)continue;const r=el.getBoundingClientRect();if(r.width<200||r.height<150)continue;const key=Math.round(r.left)+','+Math.round(r.top)+','+Math.round(r.width)+','+Math.round(r.height);if(seen.has(key))continue;seen.add(key);out.push({x:r.left,y:r.top,w:r.width,h:r.height,cls:(el.className||'').toString().slice(0,60)});}return out.slice(0,8);})()`);
}

async function eventLinks(cdp, host) {
  return evalJs(cdp, `(()=>{const out=new Map();const re=/(event|이벤트|promotion|프로모션|exhibition|기획전|price|가격|특가|할인|세일|sale|첫방문|first|welcome|프라이스|시술비|전체시술|시술안내|procedure|treatment)/i;for(const a of document.querySelectorAll('a[href]')){let u;try{u=new URL(a.href,location.href)}catch{continue}if(u.host!==${JSON.stringify(host)})continue;if(/^(javascript:|#)/.test(a.getAttribute('href')||''))continue;const img=a.querySelector('img');const t=((a.textContent||'').trim()||(img&&img.alt)||a.title||'').replace(/\\s+/g,' ').slice(0,40);const hay=u.pathname+u.search+' '+t+' '+(a.title||'')+' '+(img&&img.alt||'')+' '+(img&&img.src||'');if(re.test(hay)){const k=u.origin+u.pathname+u.search;if(!out.has(k))out.set(k,t);}}return [...out].map(([u,t])=>({url:u,text:t}));})()`);
}

async function captureClinic(cdpBox, clinic, cfg, outDir) {
  let cdp = cdpBox.cdp;
  const relaunch = async (why) => { console.log(`  Chrome 재시작 (${why})`); try { cdp.close(); } catch {} await sleep(1500); cdp = cdpBox.cdp = await launch(); };
  const name = clinic['병원명'];
  const dir = path.join(outDir, safe(name));
  fs.mkdirSync(dir, { recursive: true });
  const meta = { clinic: name, homepage: clinic['홈페이지'], startedAt: nowIso(), width: WIDTH, scale: SCALE, captures: [], blocked: null, notes: [] };
  let n = 0;
  const shot = async (label, url, extra = {}) => {
    const file = path.join(dir, `${String(++n).padStart(2, '0')}_${safe(label)}.png`);
    let info, lastErr;
    for (let attempt = 1; attempt <= 2; attempt++) {
      try { info = await fullPage(cdp, file, attempt === 2); if (attempt === 2) info.lite = true; break; }
      catch (e) { lastErr = e; console.log(`  [${n}] 캡처 실패(${attempt}/2) ${url}: ${e.message}`); if (/timeout/.test(e.message)) { await relaunch("timeout"); try { await navigate(cdp, url); await scrollAll(cdp); } catch {} } else await sleep(2000); }
    }
    if (!info) { meta.notes.push(`capture_failed ${url} ${lastErr && lastErr.message}`); await relaunch("capture failed"); return; }
    // 페이지 텍스트도 함께 저장(가격이 텍스트로 렌더링된 사이트는 이 파일로 바로 추출)
    try { const txt = await evalJs(cdp, 'document.body.innerText'); fs.writeFileSync(file.replace(/\.png$/, '.txt'), txt || '', 'utf8'); info.text = path.basename(file).replace(/\.png$/, '.txt'); } catch (e) { meta.notes.push('text_fail ' + e.message); }
    meta.captures.push({ file: path.basename(file), label, url, capturedAt: nowIso(), ...info, ...extra });
    console.log(`  [${n}] ${path.basename(file)} ← ${url} (${info.height}px)`);
  };
  const isBlocked = (nav) => (nav.status && [401, 403, 429, 503].includes(nav.status)) || BLOCK_RE.test(nav.title || '');

  const writeMeta = () => fs.writeFileSync(path.join(dir, 'meta.json'), JSON.stringify(meta, null, 2));
  try {
  const home = clinic['홈페이지'];
  const nav = await navigate(cdp, home);
  meta.home = nav;
  if (nav.navErr || isBlocked(nav) || (nav.status && nav.status >= 400)) {
    meta.blocked = { url: home, status: nav.status, title: nav.title, err: nav.navErr, at: nowIso() };
    console.log(`  차단/실패: ${home} → ${nav.status} ${nav.title} ${nav.navErr || ''}`);
    writeMeta();
    return meta;
  }
  await scrollAll(cdp);
  const pops = await visiblePopups(cdp);
  try { await harvestImages(cdp, dir, meta, 'home'); } catch (e) { meta.notes.push('harvest_fail home ' + e.message); }
  await shot('home', nav.finalUrl, { popupsVisible: pops.length });
  for (const p of pops) meta.notes.push(`popup ${Math.round(p.w)}x${Math.round(p.h)} ${p.cls}`);
  // 팝업 넘기기(설정에 셀렉터가 있을 때): 다음 버튼을 눌러 가며 각각 캡처
  if (cfg.popupNext) {
    for (let i = 0; i < (cfg.popupCount || 5); i++) {
      const ok = await evalJs(cdp, `(()=>{const b=document.querySelector(${JSON.stringify(cfg.popupNext)});if(!b)return false;b.click();return true;})()`);
      if (!ok) break; await sleep(1200);
      await shot(`popup_${i + 2}`, nav.finalUrl);
    }
  }
  const host = new URL(nav.finalUrl).host;
  const found = await eventLinks(cdp, host);
  const configured = (cfg.eventUrls || []).map(u => ({ url: u, text: '(설정)' }));
  const csvUrl = clinic['이벤트URL'] && clinic['이벤트URL'].startsWith('http') ? [{ url: clinic['이벤트URL'].split(' ')[0], text: '(목록)' }] : [];
  const seen = new Set([nav.finalUrl.replace(/\/$/, '')]);
  const skip = new Set((cfg.skipUrls || []).map(u => u.replace(/\/$/, '')));
  const queue = [...configured, ...csvUrl, ...found].filter(l => { const k = l.url.replace(/\/$/, ''); if (seen.has(k) || skip.has(k)) return false; seen.add(k); return true; }).slice(0, MAX_PAGES);
  meta.eventLinksFound = found.length;
  for (const l of queue) {
    await sleep(GAP_MS);
    let nv;
    try { nv = await navigate(cdp, l.url); } catch (e) { meta.notes.push(`nav_failed ${l.url} ${e.message}`); await relaunch("navigate timeout"); continue; }
    if (nv.navErr || isBlocked(nv)) { meta.notes.push(`skip ${l.url} → ${nv.status} ${nv.title} ${nv.navErr || ''}`); if (isBlocked(nv)) { meta.blocked = { url: l.url, status: nv.status, title: nv.title, at: nowIso() }; break; } continue; }
    try { await scrollAll(cdp); } catch (e) { meta.notes.push(`scroll_failed ${l.url} ${e.message}`); await relaunch("scroll timeout"); continue; }
    try { await harvestImages(cdp, dir, meta, `event_${l.text || 'page'}`); } catch (e) { meta.notes.push('harvest_fail ' + e.message); }
    await shot(`event_${l.text || 'page'}`, nv.finalUrl, { status: nv.status, title: nv.title });
    if (cfg.tabs) {
      for (const t of cfg.tabs) {
        const ok = await evalJs(cdp, `(()=>{const els=[...document.querySelectorAll(${JSON.stringify(t.selector)})];const el=els.find(e=>${t.text ? `e.textContent.includes(${JSON.stringify(t.text)})` : 'true'});if(!el)return false;el.click();return true;})()`);
        if (!ok) continue; await sleep(1500); await scrollAll(cdp);
        await shot(`tab_${t.text || t.selector}`, nv.finalUrl);
      }
    }
  }
  } catch (e) { meta.notes.push('error ' + e.message); console.log('  오류:', e.message); }
  meta.finishedAt = nowIso();
  writeMeta();
  return meta;
}

(async () => {
  const clinics = parseCsv(fs.readFileSync(CLINICS, 'utf8')).filter(c => c['포함'] === 'Y' && (!ONLY || ONLY.includes(c['병원명'])));
  const sites = fs.existsSync(SITES) ? JSON.parse(fs.readFileSync(SITES, 'utf8')) : {};
  fs.mkdirSync(OUT, { recursive: true });
  const blockedPath = path.join(OUT, 'blocked.csv');
  if (!fs.existsSync(blockedPath)) fs.writeFileSync(blockedPath, '\uFEFF병원명,URL,HTTP,제목,시각\n');
  console.log(`대상 ${clinics.length}곳 → ${OUT}`);
  for (const c of clinics) {
    console.log(`\n■ ${c['병원명']} (${c['홈페이지']})`);
    const box = { cdp: await launch() };
    try {
      let meta;
      try { meta = await captureClinic(box, c, sites[c['병원명']] || {}, OUT); }
      catch (e) { console.log('  오류:', e.message); meta = { blocked: null }; }
      if (meta.blocked) fs.appendFileSync(blockedPath, `${c['병원명']},${meta.blocked.url},${meta.blocked.status ?? ''},"${(meta.blocked.title || meta.blocked.err || '').replace(/"/g, "'")}",${meta.blocked.at}\n`);
    } finally { try { box.cdp.close(); } catch {} }
    await sleep(GAP_MS);
  }
  console.log('\n완료');
})();
