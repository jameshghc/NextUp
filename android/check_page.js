// Inside the phone's WebView: reload the page with Chrome's debugging
// protocol listening, click through every tab, and report every uncaught
// javascript error and console error. Android's own log doesn't carry the
// page's errors from this WebView, so a quiet log proved nothing.
//
//   node android/check_page.js <forwarded port>     (check_page.py sets it up)
const port = process.argv[2] || "9223";
const errors = [];
const wait0 = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  const targets = await (await fetch(`http://127.0.0.1:${port}/json`)).json();
  const page = targets.find(t => t.type === "page" && /127\.0\.0\.1/.test(t.url));
  if (!page) { console.log("FAIL  no Next Up page in the WebView"); process.exit(1); }
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  let id = 0;
  const waiting = new Map();
  const send = (method, params = {}) => new Promise(res => {
    const n = ++id; waiting.set(n, res); ws.send(JSON.stringify({ id: n, method, params }));
  });
  ws.onmessage = ev => {
    const m = JSON.parse(ev.data);
    if (m.id && waiting.has(m.id)) { waiting.get(m.id)(m.result || m.error); waiting.delete(m.id); }
    if (m.method === "Runtime.exceptionThrown") {
      const d = m.params.exceptionDetails;
      errors.push("uncaught: " + ((d.exception && d.exception.description) || d.text).split("\n")[0]);
    }
    if (m.method === "Runtime.consoleAPICalled" && m.params.type === "error") {
      errors.push("console.error: " + m.params.args.map(a => a.value || a.description).join(" "));
    }
    if (m.method === "Log.entryAdded" && m.params.entry.level === "error") {
      errors.push("log: " + m.params.entry.text + (m.params.entry.url ? " (" + m.params.entry.url + ")" : ""));
    }
  };
  await new Promise(r => ws.onopen = r);
  await send("Runtime.enable"); await send("Log.enable"); await send("Page.enable");
  // Runtime.enable replays what the page already logged before the reload —
  // an old run's errors included — so start counting once the reload is in.
  await wait0(300);
  errors.length = 0;
  await send("Page.reload", { ignoreCache: true });
  const wait = wait0;
  await wait(4000);
  const evalJs = async expr => (await send("Runtime.evaluate", { expression: expr, awaitPromise: true, returnByValue: true })).result?.value;
  // Past the profile picker, if it's up.
  await evalJs(`(() => { const b = document.querySelector('#picker:not(.hidden) .profilecard, #picker:not(.hidden) button'); if (b) b.click(); return !!b; })()`);
  await wait(2500);
  for (const view of ["now", "library", "rate", "channels", "settings", "library"]) {
    await evalJs(`(() => { const t = [...document.querySelectorAll('.tab')].find(x => x.dataset.view === '${view}'); if (t) t.click(); return !!t; })()`);
    await wait(2500);
  }
  for (const section of ["TV shows", "Favourites", "History", "Recommendations", "Drives", "Films"]) {
    await evalJs(`(() => { const b = [...document.querySelectorAll('#libnav .subtab, #libplaces .libplace')].find(x => x.textContent.trim().startsWith('${section}')); if (b) b.click(); return !!b; })()`);
    await wait(1500);
  }
  // --selftest: throw one on purpose, to prove this check can fail at all.
  if (process.argv.includes("--selftest")) {
    await evalJs("setTimeout(() => { throw new Error('check_page selftest'); }, 10); true");
    await wait(500);
  }
  const width = await evalJs("innerWidth");
  ws.close();
  console.log("page width " + width + "px");
  if (errors.length) { [...new Set(errors)].forEach(e => console.log("FAIL  " + e)); process.exit(1); }
  console.log("PASS  every tab and Library section opened with no page errors");
  process.exit(0);
})().catch(e => { console.log("FAIL  " + e); process.exit(1); });
