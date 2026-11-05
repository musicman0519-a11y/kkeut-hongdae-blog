// 성능 지표(간이): 모바일 에뮬레이션으로 열어 LCP·CLS·요청 수·전송 바이트를 잰다. Lighthouse 대체(점수 아님, 전후 비교용).
// 사용법: node scripts/theme/metrics.js <url> [width=390] [mobile=1]
const { spawn } = require("child_process");
const fs = require("fs");
const os = require("os");
const path = require("path");

const [url, widthArg = "390", mobileArg = "1"] = process.argv.slice(2);
const width = +widthArg, mobile = mobileArg === "1";
const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const port = 9222 + Math.floor(Math.random() * 500);
const profile = fs.mkdtempSync(path.join(os.tmpdir(), "met-"));
const chrome = spawn(CHROME, ["--headless=new", `--remote-debugging-port=${port}`, `--user-data-dir=${profile}`, "--no-first-run", "--disable-gpu", "about:blank"], { stdio: "ignore" });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
(async () => {
  for (let i = 0; i < 50; i++) { try { if ((await fetch(`http://127.0.0.1:${port}/json/version`)).ok) break; } catch {} await sleep(200); }
  const page = (await (await fetch(`http://127.0.0.1:${port}/json`)).json()).find((t) => t.type === "page");
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  await new Promise((r) => (ws.onopen = r));
  let id = 0; const pending = new Map(); let bytes = 0, requests = 0; const types = {};
  ws.onmessage = (m) => {
    const d = JSON.parse(m.data);
    if (d.id && pending.has(d.id)) { pending.get(d.id)(d); pending.delete(d.id); return; }
    if (d.method === "Network.requestWillBeSent") requests++;
    if (d.method === "Network.loadingFinished") bytes += d.params.encodedDataLength || 0;
    if (d.method === "Network.responseReceived") { const t = d.params.type; types[t] = (types[t] || 0) + 1; }
  };
  const send = (method, params = {}) => new Promise((r) => { const i = ++id; pending.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
  await send("Network.enable");
  await send("Page.enable");
  await send("Emulation.setDeviceMetricsOverride", { width, height: 844, deviceScaleFactor: 2, mobile });
  // 모바일 흉내: 4G 수준 망·CPU 4배 느리게 (Lighthouse 모바일 설정과 비슷)
  await send("Network.emulateNetworkConditions", { offline: false, latency: 150, downloadThroughput: 1.6 * 1024 * 1024 / 8, uploadThroughput: 750 * 1024 / 8 });
  await send("Emulation.setCPUThrottlingRate", { rate: 4 });
  await send("Page.addScriptToEvaluateOnNewDocument", { source: `window.__m={cls:0,lcp:0};
    new PerformanceObserver(l=>{for(const e of l.getEntries()){if(!e.hadRecentInput)window.__m.cls+=e.value;}}).observe({type:'layout-shift',buffered:true});
    new PerformanceObserver(l=>{const es=l.getEntries();if(es.length)window.__m.lcp=es[es.length-1].startTime;}).observe({type:'largest-contentful-paint',buffered:true});` });
  await send("Page.navigate", { url });
  await sleep(8000);
  const ev = await send("Runtime.evaluate", { returnByValue: true, expression: `(() => { const n = performance.getEntriesByType('navigation')[0]; return { ...window.__m, domContentLoaded: n.domContentLoadedEventEnd, load: n.loadEventEnd }; })()` });
  const m = ev.result.result.value;
  console.log(JSON.stringify({ url, width, mobile, lcp_ms: Math.round(m.lcp), cls: +m.cls.toFixed(3), domContentLoaded_ms: Math.round(m.domContentLoaded), load_ms: Math.round(m.load), requests, kb: Math.round(bytes / 1024), types }));
  ws.close(); chrome.kill(); try { fs.rmSync(profile, { recursive: true, force: true }); } catch {}
  process.exit(0);
})().catch((e) => { console.error(e); chrome.kill(); process.exit(1); });
