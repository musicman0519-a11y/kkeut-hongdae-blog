// 페이지 스크린샷 + 가로 넘침 검사 (Chrome 헤드리스 + CDP 에뮬레이션)
// 사용법: node scripts/theme/shot.js <url> <out.png> [width=1280] [mobile=0|1] [fullPage=0|1]
// 출력(JSON 한 줄): scrollWidth, innerWidth, overflow(넘치는 요소 수), docHeight, fonts(로드된 글꼴 family 목록)
const { spawn } = require("child_process");
const fs = require("fs");
const os = require("os");
const path = require("path");

const [url, out, widthArg = "1280", mobileArg = "0", fullArg = "0"] = process.argv.slice(2);
const width = +widthArg, mobile = mobileArg === "1", fullPage = fullArg === "1";
const height = mobile ? 844 : 800;
const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const port = 9222 + Math.floor(Math.random() * 500);
const profile = fs.mkdtempSync(path.join(os.tmpdir(), "shot-"));
const chrome = spawn(CHROME, ["--headless=new", `--remote-debugging-port=${port}`, `--user-data-dir=${profile}`,
  "--no-first-run", "--no-default-browser-check", "--disable-gpu", "--hide-scrollbars", `--window-size=${Math.max(width, 800)},${height}`, "about:blank"], { stdio: "ignore" });

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
async function waitPort() {
  for (let i = 0; i < 50; i++) {
    try { const r = await fetch(`http://127.0.0.1:${port}/json/version`); if (r.ok) return; } catch {}
    await sleep(200);
  }
  throw new Error("chrome 디버그 포트 열리지 않음");
}
(async () => {
  await waitPort();
  const targets = await (await fetch(`http://127.0.0.1:${port}/json`)).json();
  const page = targets.find((t) => t.type === "page");
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  await new Promise((r) => (ws.onopen = r));
  let id = 0; const pending = new Map(); const events = [];
  ws.onmessage = (m) => { const d = JSON.parse(m.data); if (d.id && pending.has(d.id)) { pending.get(d.id)(d); pending.delete(d.id); } else events.push(d); };
  const send = (method, params = {}) => new Promise((r) => { const i = ++id; pending.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
  await send("Page.enable");
  await send("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: 1, mobile });
  if (mobile) await send("Emulation.setUserAgentOverride", { userAgent: "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1" });
  await send("Page.navigate", { url });
  for (let i = 0; i < 100 && !events.some((e) => e.method === "Page.loadEventFired"); i++) await sleep(100);
  await sleep(1500);
  const ev = await send("Runtime.evaluate", { returnByValue: true, expression: `(() => {
    const over = [...document.querySelectorAll('body *')].filter(e => { const r = e.getBoundingClientRect(); return r.right > innerWidth + 1 && getComputedStyle(e).position !== 'fixed'; });
    const fonts = [...new Set([...document.fonts].filter(f => f.status === 'loaded').map(f => f.family.replace(/"/g,'')))];
    return { scrollWidth: document.documentElement.scrollWidth, innerWidth, overflow: over.length, overflowSample: over.slice(0,3).map(e => e.tagName + '.' + String(e.className).slice(0,40)), docHeight: document.documentElement.scrollHeight, fonts };
  })()` });
  const info = ev.result.result.value;
  const shotParams = { format: "png" };
  if (fullPage) { shotParams.captureBeyondViewport = true; shotParams.clip = { x: 0, y: 0, width, height: Math.min(info.docHeight, 8000), scale: 1 }; }
  const shot = await send("Page.captureScreenshot", shotParams);
  fs.writeFileSync(out, Buffer.from(shot.result.data, "base64"));
  console.log(JSON.stringify({ url, out, width, mobile, ...info }));
  ws.close(); chrome.kill();
  try { fs.rmSync(profile, { recursive: true, force: true }); } catch {}
  process.exit(0);
})().catch((e) => { console.error(e); chrome.kill(); process.exit(1); });
