// Tailwind Play CDN 이 런타임에 만드는 CSS 를 한 번 뽑아 정적 파일로 저장한다.
// 사용법: node scripts/theme/tailwind_extract.js [출력=kkeut_seo_site/assets/tailwind.css]
// 방법: 사이트 전 페이지 + 초안 + 어드민 템플릿의 <body> 를 한 문서에 모으고(클래스 합집합), head.html 의 tailwind.config 와 CDN 을
//       넣어 헤드리스 크롬으로 연 뒤, CDN 이 삽입한 <style> 내용을 읽는다. 새 클래스를 쓰는 페이지가 생기면 다시 돌린다.
const { spawn } = require("child_process");
const fs = require("fs");
const os = require("os");
const path = require("path");

const ROOT = path.resolve(__dirname, "..", "..");
const SITE = path.join(ROOT, "kkeut_seo_site");
const OUT = process.argv[2] || path.join(SITE, "assets", "tailwind.css");
const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";

const cfgSrc = fs.readFileSync(path.join(ROOT, "scripts", "theme", "tailwind.config.js"), "utf8");
const cfg = [null, cfgSrc.replace(/^\/\/.*$/m, "")];

const files = [
  ...fs.readdirSync(SITE).filter((f) => f.endsWith(".html") && !/^(google|naver)[0-9a-f]+\.html$/.test(f)).map((f) => path.join(SITE, f)),
  ...(fs.existsSync(path.join(ROOT, "drafts", "magazine")) ? fs.readdirSync(path.join(ROOT, "drafts", "magazine")).filter((f) => f.endsWith(".html")).map((f) => path.join(ROOT, "drafts", "magazine", f)) : []),
];
const bodies = files.map((f) => {
  const h = fs.readFileSync(f, "utf8");
  const m = h.match(/<body([^>]*)>([\s\S]*)<\/body>/);
  return m ? `<div${m[1]}>` + m[2].replace(/<script[\s\S]*?<\/script>/g, "") + "</div>" : "";
});
// 어드민 buildPage 템플릿(.post-body 본문은 site.css) — kkeut_admin.html 안의 템플릿 리터럴에서 body 부분만
const admin = fs.readFileSync(path.join(ROOT, "kkeut_admin.html"), "utf8");
const am = admin.match(/function buildPage\(d\) \{[\s\S]*?<body class="antialiased">([\s\S]*?)<\/body>/);
if (am) bodies.push(am[1].replace(/<\\\/script>/g, "").replace(/<script[\s\S]*?<\/script>/g, "").replace(/\$\{[^}]*\}/g, "x"));

const combined = `<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8">
<script src="https://cdn.tailwindcss.com"></script>
<script>${cfg[1]}</script>
</head><body>${bodies.map((b) => `<div>${b}</div>`).join("\n")}</body></html>`;
const tmp = path.join(os.tmpdir(), `tw-combined-${Date.now()}.html`);
fs.writeFileSync(tmp, combined);

const port = 9222 + Math.floor(Math.random() * 500);
const profile = fs.mkdtempSync(path.join(os.tmpdir(), "tw-"));
const chrome = spawn(CHROME, ["--headless=new", `--remote-debugging-port=${port}`, `--user-data-dir=${profile}`, "--no-first-run", "--disable-gpu", "about:blank"], { stdio: "ignore" });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
(async () => {
  for (let i = 0; i < 50; i++) { try { if ((await fetch(`http://127.0.0.1:${port}/json/version`)).ok) break; } catch {} await sleep(200); }
  const page = (await (await fetch(`http://127.0.0.1:${port}/json`)).json()).find((t) => t.type === "page");
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  await new Promise((r) => (ws.onopen = r));
  let id = 0; const pending = new Map(); const events = [];
  ws.onmessage = (m) => { const d = JSON.parse(m.data); if (d.id && pending.has(d.id)) { pending.get(d.id)(d); pending.delete(d.id); } else events.push(d); };
  const send = (method, params = {}) => new Promise((r) => { const i = ++id; pending.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
  await send("Page.enable");
  await send("Page.navigate", { url: "file:///" + tmp.replace(/\\/g, "/") });
  for (let i = 0; i < 100 && !events.some((e) => e.method === "Page.loadEventFired"); i++) await sleep(100);
  await sleep(4000);
  const ev = await send("Runtime.evaluate", { returnByValue: true, expression: `[...document.querySelectorAll('style')].map(s => s.textContent).join('\\n')` });
  let css = ev.result.result.value || "";
  if (css.length < 5000) throw new Error("생성된 CSS 가 너무 작음: " + css.length);
  css = `/* Tailwind Play CDN 이 생성한 CSS 의 정적 사본. scripts/theme/tailwind_extract.js 로 재생성. 손으로 고치지 않는다. */\n` + css;
  fs.writeFileSync(OUT, css);
  console.log(JSON.stringify({ out: path.relative(ROOT, OUT), pages: files.length + (am ? 1 : 0), bytes: css.length, classesSample: (css.match(/\.[a-zA-Z][\w\\:/\[\]\.%#-]*\{/g) || []).length }));
  ws.close(); chrome.kill();
  try { fs.rmSync(profile, { recursive: true, force: true }); fs.unlinkSync(tmp); } catch {}
  process.exit(0);
})().catch((e) => { console.error(e); chrome.kill(); process.exit(1); });
