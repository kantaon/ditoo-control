"use strict";
/* Ditoo Control UI – vanilla JS, no build step. Strings are English; t() translates (i18n.js). */

const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const h = (tag, attrs = {}, ...kids) => {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v == null || v === false) continue;
    if (k === "class") el.className = v;
    else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else el.setAttribute(k, v === true ? "" : v);
  }
  for (const k of kids.flat()) if (k != null && k !== false) el.append(k.nodeType ? k : document.createTextNode(k));
  return el;
};
const icon = (id) => { const s = document.createElementNS("http://www.w3.org/2000/svg", "svg"); s.innerHTML = `<use href="#i-${id}"/>`; return s; };
const debounce = (fn, ms = 250) => { let tm; return (...a) => { clearTimeout(tm); tm = setTimeout(() => fn(...a), ms); }; };
const rgbHex = (c) => "#" + c.map((v) => v.toString(16).padStart(2, "0")).join("");
const hexRgb = (s) => [1, 3, 5].map((i) => parseInt(s.slice(i, i + 2), 16));
const fmtTime = (ts) => new Date(ts * 1000).toLocaleTimeString(LANG === "cs" ? "cs-CZ" : undefined, { hour: "2-digit", minute: "2-digit", second: "2-digit" });

const api = {
  get: (p) => fetch(p).then((r) => r.json()),
  post: async (p, body = {}) => {
    const r = await fetch(p, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    const j = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(j.error || r.statusText);
    return j;
  },
};

function toast(msg, err = false) {
  const el = h("div", { class: "toast" + (err ? " err" : ""), role: "status" }, icon(err ? "info" : "check"), msg);
  $("#toasts").append(el);
  setTimeout(() => el.remove(), 3400);
}

/* ------------------------------------------------------------------ LED renderer */
function parseFrame(hex) {
  const a = new Uint8Array(768);
  for (let i = 0; i < 768; i++) a[i] = parseInt(hex.substr(i * 2, 2), 16);
  return a;
}

class Led {
  constructor(canvas, { gap = 0.16, radius = 0.28, offColor = [16, 17, 22], glow = null } = {}) {
    this.c = canvas; this.ctx = canvas.getContext("2d");
    this.gap = gap; this.radius = radius; this.off = offColor; this.glow = glow;
    this.frames = []; this.ms = []; this.i = 0; this.next = 0; this.bright = 1;
    Led.all.add(this);
  }
  set(scene) {
    this.frames = (scene.frames || []).map(parseFrame);
    this.ms = scene.ms || [];
    this.i = 0; this.next = performance.now() + (this.ms[0] || 100);
    this.draw();
  }
  tick(now) {
    if (this.frames.length < 2 || now < this.next || !this.c.offsetParent) return;
    this.i = (this.i + 1) % this.frames.length;
    this.next = now + (this.ms[this.i] || 100);
    this.draw();
  }
  draw() {
    const { c, ctx } = this, W = c.width, cell = W / 16, g = cell * this.gap, r = cell * this.radius;
    ctx.clearRect(0, 0, W, W);
    const f = this.frames[this.i];
    let sr = 0, sg = 0, sb = 0, lit = 0;
    for (let y = 0; y < 16; y++) for (let x = 0; x < 16; x++) {
      const o = (y * 16 + x) * 3;
      let R = f ? f[o] : 0, G = f ? f[o + 1] : 0, B = f ? f[o + 2] : 0;
      if (R + G + B > 12) { sr += R; sg += G; sb += B; lit++; R *= this.bright; G *= this.bright; B *= this.bright; }
      else [R, G, B] = this.off;
      ctx.fillStyle = `rgb(${R | 0},${G | 0},${B | 0})`;
      ctx.beginPath();
      ctx.roundRect(x * cell + g / 2, y * cell + g / 2, cell - g, cell - g, r);
      ctx.fill();
    }
    if (this.glow && lit) {
      const k = 1.2 / lit;
      this.glow(Math.min(255, sr * k) | 0, Math.min(255, sg * k) | 0, Math.min(255, sb * k) | 0);
    }
  }
}
Led.all = new Set();
let rafOn = false;
function loop(now) {
  if (document.hidden) { rafOn = false; return; }   // hidden window = zero work
  for (const l of Led.all) l.tick(now);
  requestAnimationFrame(loop);
}
function startLoop() { if (!rafOn) { rafOn = true; requestAnimationFrame(loop); } }

function sparkline(canvas, values, color, lo, hi) {
  const dpr = devicePixelRatio || 1, w = canvas.clientWidth, hgt = canvas.clientHeight;
  if (!w) return;
  canvas.width = w * dpr; canvas.height = hgt * dpr;
  const ctx = canvas.getContext("2d"); ctx.scale(dpr, dpr);
  const v = values.filter((x) => x != null);
  if (v.length < 2) return;
  const min = lo ?? Math.min(...v) - 2, max = hi ?? Math.max(...v) + 2;
  const pts = values.map((x, i) => x == null ? null : [i / (values.length - 1) * w, hgt - 3 - (x - min) / (max - min || 1) * (hgt - 6)]).filter(Boolean);
  const grad = ctx.createLinearGradient(0, 0, 0, hgt);
  grad.addColorStop(0, color + "55"); grad.addColorStop(1, color + "00");
  ctx.beginPath(); ctx.moveTo(pts[0][0], hgt);
  pts.forEach((p) => ctx.lineTo(p[0], p[1]));
  ctx.lineTo(pts[pts.length - 1][0], hgt); ctx.fillStyle = grad; ctx.fill();
  ctx.beginPath(); pts.forEach((p, i) => i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1]));
  ctx.strokeStyle = color; ctx.lineWidth = 1.6; ctx.lineJoin = "round"; ctx.stroke();
}

/* ------------------------------------------------------------------ static data */
const MODE_META = {
  auto: ["auto", "Automatic", "Reacts to games, AI agents, temperatures and time of day"],
  clock: ["clock", "Clock", "Animated, with seconds"],
  monitor: ["monitor", "PC monitor", "CPU / GPU temperature and load"],
  game: ["game", "Gaming", "FPS and temperatures while playing"],
  weather: ["weather", "Weather", "Animated, with forecast"],
  ai: ["ai", "AI agents", "Claude Code and Codex"],
  pomodoro: ["timer", "Pomodoro", "Focus timer"],
  ambient: ["ambient", "Ambient", "Plasma, fire, Matrix…"],
  text: ["text", "Text", "Your own scrolling message"],
  media: ["image", "Image / GIF", "Your pixel art"],
  visualizer: ["viz", "Visualizer", "Reacts to music"],
  lamp: ["lamp", "Lamp", "Night light"],
  off: ["off", "Off", "LEDs off"],
};
const PAGES = {
  overview: ["Overview", "What Ditoo shows right now and why"],
  gallery: ["Scene gallery", "Everything your Ditoo Pro can do"],
  rules: ["Automation", "How Ditoo decides on its own"],
  games: ["Games", "Gaming HUD and game detection"],
  content: ["Content", "Images, text, effects, clock and lamp"],
  sound: ["Sounds", "Notifications from the Ditoo speaker"],
  integrations: ["Integrations", "Claude Code, Codex, start with Windows and API"],
  settings: ["Settings", "Connection, location and language"],
  help: ["Help", "What everything on the display means and how it all works"],
};
const GALLERY_MODE = { clock: "clock", monitor: "monitor", game: "game", intro: "game", weather: "weather", weather_sun: "weather",
  weather_snow: "weather", weather_night: "weather", ai_claude: "ai", ai_codex: "ai", ai_both: "ai", ai_done: "ai", ai_attn: "ai",
  ai_error: "ai", pomodoro: "pomodoro", text: "text", viz: "visualizer" };
const AI_STATE = { working: ["Working", "accent"], done: ["Done", "ok"], error: ["Error", "bad"], attention: ["Waiting for you", "warn"], idle: ["Idle", ""] };

const S = { cfg: null, meta: null, st: null, rev: -1, gallery: null, langRev: null };
let mainLed;

/* ------------------------------------------------------------------ config helpers */
function deepMerge(a, b) {
  for (const [k, v] of Object.entries(b)) {
    if (v && typeof v === "object" && !Array.isArray(v) && a[k] && typeof a[k] === "object") deepMerge(a[k], v);
    else a[k] = v;
  }
  return a;
}
const pending = {};
const flush = debounce(async () => {
  const body = JSON.parse(JSON.stringify(pending));
  for (const k of Object.keys(pending)) delete pending[k];
  try { await api.post("/api/config", body); } catch (e) { toast(t("Couldn't save: {err}", { err: e.message }), true); }
}, 300);
function setCfg(patch) {
  deepMerge(S.cfg, JSON.parse(JSON.stringify(patch)));
  deepMerge(pending, patch);
  flush();
}
async function setMode(mode) {
  S.cfg.mode = mode; updateModeButtons();
  try { await api.post("/api/mode", { mode }); } catch (e) { toast(e.message, true); }
  poll();
}
function rangeFill(inp) { inp.style.setProperty("--p", ((inp.value - inp.min) / (inp.max - inp.min) * 100) + "%"); }
function bindSwitch(el, get, set) {
  el.setAttribute("aria-checked", String(!!get()));
  el.onclick = () => { const v = el.getAttribute("aria-checked") !== "true"; el.setAttribute("aria-checked", String(v)); set(v); };
}
function bindRange(inp, valEl, get, set, fmt = (v) => v) {
  inp.value = get(); rangeFill(inp); if (valEl) valEl.textContent = fmt(inp.value);
  inp.oninput = () => { rangeFill(inp); if (valEl) valEl.textContent = fmt(inp.value); set(+inp.value); };
}
function bindSeg(box, get, set) {
  const paint = () => $$("button", box).forEach((b) => b.setAttribute("aria-checked", String(b.dataset.v === get())));
  $$("button", box).forEach((b) => (b.onclick = () => { set(b.dataset.v); paint(); }));
  paint();
}
const openTarget = (target) => api.post("/api/open", { target }).catch((e) => toast(e.message, true));
document.addEventListener("click", (e) => { const b = e.target.closest("[data-open]"); if (b) openTarget(b.dataset.open); });

/* ------------------------------------------------------------------ navigation */
function go(page) {
  $$(".nav button").forEach((b) => b.classList.toggle("active", b.dataset.page === page));
  $$(".page").forEach((p) => p.classList.toggle("active", p.id === "page-" + page));
  $("#pageTitle").textContent = t(PAGES[page][0]);
  $("#pageSub").textContent = t(PAGES[page][1]);
  if (page === "gallery") renderGallery();
  if (page === "integrations") renderIntegrations();
  if (page === "content") renderContent(S.st);
  if (page === "help") renderHelp();
  hideTip();
  $(".main").scrollTop = 0;
}
$$(".nav button").forEach((b) => (b.onclick = () => go(b.dataset.page)));

/* ------------------------------------------------------------------ overview */
function renderModes() {
  const box = $("#modes"); box.innerHTML = "";
  for (const m of S.meta.modes) {
    const [ic, title, desc] = MODE_META[m.id];
    const d = m.id === "weather" && S.cfg.city ? `${t("Animated")} · ${S.cfg.city}` : t(desc);
    box.append(h("button", { class: "mode" + (m.id === "auto" ? " auto" : ""), "data-mode": m.id, "aria-pressed": String(S.cfg.mode === m.id),
      onclick: () => setMode(m.id) },
      h("span", { class: "mi" }, icon(ic)), h("span", {}, h("div", { class: "mt" }, t(title)), h("div", { class: "md" }, d))));
  }
  const hk = S.cfg.hotkeys;
  $("#modesHint").replaceChildren(t("Ctrl + Shift + Alt + "), h("kbd", {}, hk.prev), "/", h("kbd", {}, hk.next), " " + t("switches by context"));
}
function updateModeButtons() {
  $$("#modes .mode").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.mode === S.cfg.mode)));
}

const TILE_DEFS = [
  ["cpu_temp", "CPU temperature", "thermo", "°C", "#ff8a4a"],
  ["gpu_temp", "GPU temperature", "thermo", "°C", "#7ddc4a"],
  ["cpu_load", "CPU load", "monitor", "%", "#5ab8ff"],
  ["gpu_load", "GPU load", "activity", "%", "#b07cff"],
];
function renderTiles() {
  const box = $("#tiles"); box.innerHTML = "";
  for (const [k, label, ic] of TILE_DEFS) {
    box.append(h("div", { class: "tile", id: "tile-" + k }, h("div", { class: "tile-top" }, t(label), icon(ic)),
      h("div", { class: "tile-val" }, "—"), h("canvas", {})));
  }
  box.append(h("div", { class: "tile hidden", id: "tile-fps" }, h("div", { class: "tile-top" }, "FPS", icon("game")),
    h("div", { class: "tile-val" }, "—"), h("canvas", {})));
}
function updateTiles(st) {
  const tel = st.telemetry;
  for (const [k, , , unit, color] of TILE_DEFS) {
    const el = $("#tile-" + k), v = tel[k];
    el.classList.toggle("empty", v == null);
    $(".tile-val", el).replaceChildren(v == null ? "—" : String(Math.round(v)), v == null ? "" : h("small", {}, unit));
    sparkline($("canvas", el), st.history[k], color, unit === "%" ? 0 : null, unit === "%" ? 100 : null);
  }
  const fps = $("#tile-fps");
  fps.classList.toggle("hidden", !st.game);
  if (st.game) {
    $(".tile-val", fps).replaceChildren(st.game.fps == null ? "—" : String(st.game.fps), h("small", {}, "fps"),
      st.game.frametime ? h("small", { class: "ft" }, ` · ${st.game.frametime} ${t("ms/frame")}`) : "");
    sparkline($("canvas", fps), st.history.fps, "#3ddc97", 0, null);
  }
  let warn = $("#abWarn");
  const missing = !tel.afterburner || !tel.rtss;
  if (missing && !warn) {
    warn = h("div", { class: "tile tile-wide tile-info", id: "abWarn" },
      h("div", { class: "tile-top" }, t("Optional tools"), icon("info")),
      h("p", { class: "note" }, t("Everything works without them. MSI Afterburner adds the CPU temperature (until then the display shows CPU load), RivaTuner adds FPS and frame time in games. Both are free.")),
      h("div", { class: "tools-slot" }));
    $("#tiles").append(warn);
  } else if (!missing && warn) { warn.remove(); warn = null; }
  if (warn) $(".tools-slot", warn).replaceChildren(toolRows(tel));
  const settingsSlot = $("#toolsSettings");
  if (settingsSlot) settingsSlot.replaceChildren(toolRows(tel));
}

/* optional third-party tools: status + download */
const TOOLS = [
  ["afterburner", "MSI Afterburner", "adds the CPU temperature", (tel) => tel.afterburner],
  ["rtss", "RivaTuner Statistics Server", "adds FPS and frame time in games", (tel) => tel.rtss],
];
function toolRows(tel) {
  return h("ul", { class: "tools" }, TOOLS.map(([id, name, what, ok]) => {
    const on = !!ok(tel || {});
    return h("li", { class: on ? "ok" : "" }, h("span", { class: "wz-check" }, icon(on ? "check" : "x")),
      h("div", { class: "grow" }, h("b", {}, name), h("span", {}, t(what))),
      on ? h("span", { class: "badge ok" }, t("Running"))
        : h("button", { class: "btn sm", onclick: () => openTarget(id) }, icon("upload"), t("Download")));
  }));
}

function updateChips(st) {
  const ctxIcon = { game: "game", ai: "ai", desk: "desk" }[st.context];
  const chips = [h("span", { class: "chip accent" }, icon(MODE_META[st.mode][0]), st.mode_label),
    h("span", { class: "chip" }, icon(ctxIcon), t("Context: {name}", { name: st.context_label }))];
  if (st.away) chips.push(h("span", { class: "chip" }, icon("power"), t("Display off – you're away")));
  else if (st.night) chips.push(h("span", { class: "chip" }, icon("moon"), t("Night brightness")));
  if (st.game) chips.push(h("span", { class: "chip ok" }, icon("game"), st.game.name));
  $("#chips").replaceChildren(...chips);
}

const DEV_TEXT = { connected: "Connected", connecting: "Connecting…", error: "Not reachable", disconnected: "Disconnected" };
function updateConn(st) {
  const d = st.device;
  $("#connDot").className = "dot " + ({ connected: "ok", connecting: "busy", error: "bad" }[d.status] || "");
  $("#connSub").textContent = d.status === "connected" ? t("Connected · channel {port}", { port: d.port }) : t(DEV_TEXT[d.status] || d.status);
  $("#connBtnText").textContent = d.status === "error" ? t("Fix connection") : t("Reconnect");
  $("#conn").title = d.error || "";
  const b = $("#devBadge");
  b.textContent = t(DEV_TEXT[d.status] || d.status);
  b.className = "badge " + ({ connected: "ok", connecting: "warn", error: "bad" }[d.status] || "");
  if (!$("#mac").matches(":focus")) $("#mac").value = d.mac || "";
  updateBanner(st);
}

/* actionable banner for problems a non-technical user can fix */
let bannerAction = null;
function updateBanner(st) {
  const d = st.device, box = $("#banner");
  let title = null, text = "", action = null, label = "";
  if (d.status === "error" && d.enabled) {
    title = t("Ditoo isn't connected");
    text = d.error;
    label = t("Help me connect");
    action = () => openWizard(1);
  } else if (d.status === "disconnected" && !d.enabled) {
    title = t("Ditoo is disconnected");
    text = t("The app is not sending anything to the display.");
    label = t("Connect");
    action = () => api.post("/api/device", { action: "connect" });
  }
  box.classList.toggle("hidden", !title);
  if (!title) return;
  $("#bannerTitle").textContent = title;
  $("#bannerText").textContent = text;
  $("#bannerAction").textContent = label;
  bannerAction = action;
}
$("#bannerAction").onclick = () => bannerAction && bannerAction();

function updateAI(st) {
  const ai = st.ai, [lbl, cls] = AI_STATE[ai.state];
  const badge = $("#aiBadge");
  badge.textContent = ai.source ? `${agentName(ai.source)} · ${t(lbl)}` : t(lbl);
  badge.className = "badge " + cls;
  const src = Object.entries(ai.sources);
  $("#aiSources").replaceChildren(...(src.length ? src.map(([name, v]) => {
    const [l, c] = AI_STATE[v.state] || [v.state, ""];
    return h("div", { class: "ai-src" }, h("span", { class: "ai-dot", style: `background:${AGENT_COLOR[name] || "#b478ff"}` }),
      h("b", {}, agentName(name)), h("span", { class: "badge " + c }, t(l)));
  }) : [h("div", { class: "empty-state" }, t("No signal yet. Turn on the Claude Code or Codex integration on the Integrations page."))]));
  $("#aiTimeline").replaceChildren(...ai.events.map((e) => h("li", {}, h("time", {}, fmtTime(e.t)),
    h("span", {}, `${agentName(e.source)}: ${t((AI_STATE[e.state] || [e.state])[0])}${e.detail ? " – " + e.detail : ""}`))));
}
const AGENT_COLOR = { claude: "#eb7846", codex: "#28cdb9" };
const agentName = (s) => ({ claude: "Claude", codex: "Codex" }[s] || (s ? s[0].toUpperCase() + s.slice(1) : "AI"));

function updateLogs(st) {
  const row = (l) => h("li", {}, h("time", {}, fmtTime(l.t)), h("span", {}, l.msg));
  $("#activity").replaceChildren(...st.logs.slice(0, 12).map(row));
  $("#fullLog").replaceChildren(...st.logs.map(row));
}

function updatePomo(st) {
  const p = st.pomodoro, box = $("#pomoCtl");
  box.classList.toggle("hidden", !p.running && st.mode !== "pomodoro");
  $("#pomoGo").classList.toggle("hidden", p.running);
  $("#pomoToggle").classList.toggle("hidden", !p.running);
  $("#pomoStop").classList.toggle("hidden", !p.running);
  $("[data-pomo=skip]").classList.toggle("hidden", !p.running);
  if (!p.running) { $("#pomoText").textContent = t("Ready · {min} min focus", { min: S.cfg.pomodoro.focus }); return; }
  const m = Math.floor(p.remaining / 60), s = String(p.remaining % 60).padStart(2, "0");
  $("#pomoText").textContent = `${t(p.phase === "focus" ? "Focus" : "Break")} · ${m}:${s}${p.paused ? " · " + t("paused") : ""} · ${t("round {n}", { n: p.rounds + 1 })}`;
  const tg = $("#pomoToggle");
  tg.replaceChildren(icon(p.paused ? "play" : "pause"));
  tg.dataset.pomo = p.paused ? "resume" : "pause";
  tg.setAttribute("aria-label", t(p.paused ? "Resume" : "Pause"));
}
$("#pomoCtl").addEventListener("click", async (e) => {
  const b = e.target.closest("[data-pomo]"); if (!b) return;
  await api.post("/api/pomodoro", { action: b.dataset.pomo }); poll();
});

/* ------------------------------------------------------------------ gallery */
async function ensureGallery() {
  if (!S.gallery || S.galleryLang !== S.langRev) { S.gallery = await api.get("/api/gallery"); S.galleryLang = S.langRev; }
  return S.gallery;
}
async function renderGallery() {
  await ensureGallery();
  const box = $("#gallery");
  if (box.childElementCount) return;
  for (const g of S.gallery) {
    const cv = h("canvas", { width: 168, height: 168 });
    const mode = GALLERY_MODE[g.id] || (g.id.startsWith("fx_") ? "ambient" : null);
    box.append(h("div", { class: "g-item" }, h("div", { class: "g-screen" }, cv),
      h("div", { class: "g-body" }, h("div", { class: "g-title" }, g.title), h("div", { class: "g-desc" }, g.desc),
        h("div", { class: "g-actions" },
          h("button", { class: "btn sm", onclick: async () => { await api.post("/api/try", { id: g.id }); toast(t("{title} – showing on Ditoo for 12 s", { title: g.title })); } }, icon("play"), t("Try it")),
          mode ? h("button", { class: "btn sm primary", onclick: async () => {
            if (g.id.startsWith("fx_")) setCfg({ effect: g.id.slice(3) });
            await setMode(mode); toast(t("Mode: {mode}", { mode: t(MODE_META[mode][1]) }));
          } }, t("Use")) : null))));
    new Led(cv, { offColor: [14, 15, 19] }).set(g);
  }
  startLoop();
}

/* ------------------------------------------------------------------ rules */
const RULES = [
  ["alerts", "Overheating", "Blinking warning when the CPU or GPU passes the critical temperature"],
  [null, "Notifications", "Messages from your scripts and webhooks (always on)"],
  [null, "Picked with a shortcut", "Ctrl+Shift+Alt+A/D – stays until the context changes"],
  ["ai_flash", "AI finished / error", "Short confirmation when Claude or Codex finishes"],
  ["games", "Gaming", "Gaming HUD with FPS and temperatures"],
  ["pomodoro", "Pomodoro", "Countdown while the timer runs"],
  ["ai", "AI working / waiting", "Animation while an agent works or waits for your answer"],
  [null, "Idle", "Cycles clock, weather, monitor and effects"],
];
function renderRules() {
  const r = S.cfg.rules;
  $("#rulesList").replaceChildren(...RULES.map(([key, title, desc], i) => {
    const li = h("li", { "data-i": i }, h("div", { class: "rt" }, h("b", {}, t(title)), h("span", {}, t(desc))));
    if (key === "ai_flash") {
      const sw = h("button", { class: "switch", role: "switch", "aria-label": t("Even while gaming") });
      bindSwitch(sw, () => r.ai_over_game, (v) => setCfg({ rules: { ai_over_game: v } }));
      li.append(h("span", { class: "locked" }, t("even while gaming")), sw);
    } else if (key) {
      const sw = h("button", { class: "switch", role: "switch", "aria-label": t(title) });
      bindSwitch(sw, () => r[key], (v) => setCfg({ rules: { [key]: v } }));
      if (key === "games") {
        const intro = h("button", { class: "switch", role: "switch", "aria-label": t("Game start animation") });
        bindSwitch(intro, () => r.intro, (v) => setCfg({ rules: { intro: v } }));
        li.append(h("span", { class: "locked" }, t("intro")), intro);
      }
      li.append(sw);
    } else li.append(h("span", { class: "locked" }, t("always")));
    return li;
  }));
  const idle = [["clock", "Clock", "clock"], ["weather", "Weather", "weather"], ["monitor", "PC monitor", "monitor"], ["ambient", "Ambient", "ambient"]];
  $("#idleList").replaceChildren(...idle.map(([k, label, ic]) => {
    const inp = h("input", { type: "range", min: 0, max: 120, step: 5, "aria-label": t(label) });
    const val = h("span", { class: "val" });
    const row = h("div", { class: "idle-row" }, h("span", {}, icon(ic), t(label)), inp, val);
    bindRange(inp, val, () => S.cfg.idle[k] || 0, (v) => setCfg({ idle: { [k]: v } }), (v) => (+v ? v + " s" : t("off")));
    return row;
  }));
  const n = S.cfg.night;
  bindSwitch($("#nightSwitch"), () => n.enabled, (v) => setCfg({ night: { enabled: v } }));
  for (const id of ["nightStart", "nightEnd"]) {
    const sel = $("#" + id);
    sel.replaceChildren(...Array.from({ length: 24 }, (_, i) => h("option", { value: i }, `${String(i).padStart(2, "0")}:00`)));
    sel.value = id === "nightStart" ? n.start : n.end;
    sel.onchange = () => setCfg({ night: { [id === "nightStart" ? "start" : "end"]: +sel.value } });
  }
  bindRange($("#nightBright"), $("#nightBrightVal"), () => n.brightness, (v) => setCfg({ night: { brightness: v } }), (v) => (+v ? v + " %" : t("display off")));
  const aw = S.cfg.away;
  bindSwitch($("#awaySwitch"), () => aw.enabled, (v) => setCfg({ away: { enabled: v } }));
  bindSwitch($("#awayLock"), () => aw.on_lock, (v) => setCfg({ away: { on_lock: v } }));
  bindRange($("#awayMinutes"), $("#awayMinutesVal"), () => aw.minutes, (v) => setCfg({ away: { minutes: v } }), (v) => t("{n} min", { n: v }));
  const th = [["cpu_warn", "CPU warning °C"], ["cpu_crit", "CPU critical °C"], ["gpu_warn", "GPU warning °C"], ["gpu_crit", "GPU critical °C"]];
  $("#thresholds").replaceChildren(...th.map(([k, l]) => {
    const inp = h("input", { type: "number", min: 40, max: 110, value: S.cfg[k] });
    inp.onchange = () => setCfg({ [k]: Math.max(40, Math.min(110, +inp.value || S.cfg[k])) });
    return h("label", {}, h("span", {}, t(l)), inp);
  }));
  const hk = S.cfg.hotkeys;
  bindSwitch($("#hkSwitch"), () => hk.enabled, (v) => setCfg({ hotkeys: { enabled: v } }));
  const acts = [["prev", "Previous screen"], ["next", "Next screen"], ["auto", "Back to Automatic"], ["bright", "Toggle brightness"]];
  $("#hotkeys").replaceChildren(...acts.map(([k, l]) => {
    const inp = h("input", { maxlength: 1, value: hk[k], "aria-label": t(l) });
    inp.oninput = () => { inp.value = inp.value.toUpperCase().replace(/[^A-Z0-9]/g, ""); if (inp.value) setCfg({ hotkeys: { [k]: inp.value } }); };
    return h("div", { class: "hk" }, combo(), inp, h("span", { class: "what" }, t(l)));
  }));
}
const combo = (k) => h("span", { class: "combo" }, h("kbd", {}, "Ctrl"), "+", h("kbd", {}, "Shift"), "+", h("kbd", {}, "Alt"), "+", k ? h("kbd", {}, k) : "");
const RULE_OF_REASON = [[/^(Careful|Pozor)/, 0], [/^(Incoming|Příchozí)/, 1], [/^(Picked|Vybráno)/, 2], [/(finished|reports|dokončil|hlásí)/, 3],
  [/(Playing|Game started|Běží hra|Spuštěna hra)/, 4], [/(Pomodoro running|Běží pomodoro)/, 5], [/(working|waiting|pracuj|čeká)/, 6], [/^(Idle|Klid)/, 7]];
function updateRules(st) {
  const hit = RULE_OF_REASON.find(([re]) => re.test(st.reason || ""));
  const active = hit ? hit[1] : -1;
  $$("#rulesList li").forEach((li) => li.classList.toggle("on-now", st.mode === "auto" && +li.dataset.i === active));
  const cyc = { game: ["Gaming", "HUD → monitor → clock → weather"], ai: ["Working with AI", "AI → pomodoro → clock → monitor → weather → ambient"],
    desk: ["Idle", "clock → weather → monitor → ambient → AI → pomodoro → visualizer"] };
  $("#contexts").replaceChildren(...Object.entries(cyc).map(([k, [ti, d]]) => h("div", { class: "ctx" + (st.context === k ? " on" : "") }, h("b", {}, t(ti)), t(d))));
}

/* ------------------------------------------------------------------ games */
function renderGames() {
  const games = S.cfg.games;
  $("#gameCount").textContent = t("{n} games", { n: games.length });
  $("#gameList").replaceChildren(...games.map((g, i) => h("li", {},
    h("div", { class: "grow" }, h("b", {}, g.name || g.exe), h("span", {}, g.exe)),
    h("button", { class: "btn icon sm ghost danger", "aria-label": t("Remove {name}", { name: g.name || g.exe }), onclick: () => {
      const next = games.filter((_, j) => j !== i); setCfg({ games: next }); S.cfg.games = next; renderGames();
    } }, icon("trash")))));
  bindSwitch($("#autoDetect"), () => S.cfg.auto_detect_games, (v) => setCfg({ auto_detect_games: v }));
  $("#ignoreList").replaceChildren(...S.cfg.ignore_apps.map((a, i) => h("span", { class: "chip" }, a,
    h("button", { "aria-label": t("Remove {name}", { name: a }), onclick: () => { const n = S.cfg.ignore_apps.filter((_, j) => j !== i); setCfg({ ignore_apps: n }); S.cfg.ignore_apps = n; renderGames(); } }, icon("x")))));
}
function addGame(exe, name) {
  exe = exe.trim().toLowerCase().replace(/^.*[\\/]/, ""); if (!exe) return;
  if (!exe.endsWith(".exe")) exe += ".exe";
  if (S.cfg.games.some((g) => g.exe === exe)) return toast(t("This game is already on the list"), true);
  const next = [...S.cfg.games, { exe, name: name.trim() || exe.replace(/\.exe$/, "") }];
  setCfg({ games: next }); S.cfg.games = next; renderGames(); toast(t("Added: {name}", { name: name || exe }));
}
$("#gameForm").onsubmit = (e) => { e.preventDefault(); addGame($("#gameExe").value, $("#gameName").value); e.target.reset(); };
$("#ignoreForm").onsubmit = (e) => {
  e.preventDefault(); const v = $("#ignoreExe").value.trim().toLowerCase(); if (!v) return;
  const n = [...S.cfg.ignore_apps, v]; setCfg({ ignore_apps: n }); S.cfg.ignore_apps = n; renderGames(); e.target.reset();
};
function updateGames(st) {
  const g = st.game, box = $("#gameNow");
  box.className = "card game-now" + (g ? " on" : "");
  box.replaceChildren(h("div", { class: "gi" }, icon("game")), h("div", {},
    h("b", {}, g ? g.name : t("No game running")),
    h("span", {}, g ? `${g.fps != null ? g.fps + " FPS · " : ""}${t(g.auto ? "detected automatically" : "from your list")} · ${t("since {time}", { time: fmtTime(g.since) })}`
      : t("As soon as you start a game, Ditoo switches to the gaming HUD"))));
  const c = st.candidates;
  $("#candidates").replaceChildren(...(c.length ? c.map((x) => h("li", {},
    h("div", { class: "grow" }, h("b", {}, x.exe), h("span", {}, `${x.fps} FPS${x.foreground ? " · " + t("full screen") : ""}`)),
    h("button", { class: "btn sm", onclick: () => addGame(x.exe, "") }, icon("plus"), t("Add")))) :
    [h("li", {}, h("div", { class: "grow" }, h("span", {}, t("RivaTuner isn't tracking any 3D app right now"))))]));
}

/* ------------------------------------------------------------------ content */
function renderContent(st) {
  const sel = S.cfg.media;
  $("#mediaGrid").replaceChildren(...(st?.media || []).map((m) => h("div", { class: "media" + (m === sel ? " sel" : ""), title: m, tabindex: 0, role: "button",
      onclick: async () => { setCfg({ media: m }); await setMode("media"); renderContent(S.st); toast(t("Showing {name}", { name: m })); } },
    h("img", { src: "/media/" + encodeURIComponent(m), alt: m, loading: "lazy" }),
    h("button", { "aria-label": t("Delete {name}", { name: m }), onclick: async (e) => {
      e.stopPropagation(); await api.post("/api/media/delete", { name: m }); await poll(); renderContent(S.st);
    } }, icon("trash")))));
  const fx = $("#fxGrid");
  if (!fx.childElementCount && S.gallery) {
    for (const g of S.gallery.filter((x) => x.id.startsWith("fx_"))) {
      const id = g.id.slice(3), cv = h("canvas", { width: 128, height: 128 });
      fx.append(h("button", { class: "fx", "data-fx": id, "aria-pressed": String(S.cfg.effect === id), onclick: async () => {
        setCfg({ effect: id }); $$("#fxGrid .fx").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.fx === id)));
        await setMode("ambient");
      } }, cv, h("span", {}, g.title)));
      new Led(cv, { offColor: [12, 12, 16] }).set(g);
    }
    startLoop();
  }
}
async function upload(file) {
  if (!file) return;
  if (file.size > 20 * 1024 * 1024) return toast(t("The file is too big (max 20 MB)"), true);
  const data = await new Promise((res) => { const r = new FileReader(); r.onload = () => res(r.result); r.readAsDataURL(file); });
  try {
    const r = await api.post("/api/media", { name: file.name, data });
    S.cfg.media = r.name; S.cfg.mode = "media"; updateModeButtons();
    await poll(); renderContent(S.st); toast(t("Uploaded and shown on Ditoo"));
  } catch (e) { toast(e.message, true); }
}
const drop = $("#drop");
drop.addEventListener("dragover", (e) => { e.preventDefault(); drop.classList.add("over"); });
drop.addEventListener("dragleave", () => drop.classList.remove("over"));
drop.addEventListener("drop", (e) => { e.preventDefault(); drop.classList.remove("over"); upload(e.dataTransfer.files[0]); });
drop.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); $("#fileInput").click(); } });
$("#fileInput").onchange = (e) => upload(e.target.files[0]);

function bindContent() {
  const c = S.cfg;
  $("#textInput").value = c.text; $("#textColor").value = rgbHex(c.text_color);
  bindSwitch($("#rainbow"), () => c.text_rainbow, (v) => setCfg({ text_rainbow: v }));
  $("#textShow").onclick = async () => {
    setCfg({ text: $("#textInput").value || "HELLO", text_color: hexRgb($("#textColor").value) });
    await new Promise((r) => setTimeout(r, 350));
    await setMode("text"); toast(t("The text is on the display"));
  };
  $("#textNotify").onclick = async () => {
    const txt = $("#textInput").value.trim(); if (!txt) return toast(t("Type a message first"), true);
    await api.post("/api/notify", { text: txt, color: hexRgb($("#textColor").value) }); toast(t("Notification sent"));
  };
  bindSeg($("#clockType"), () => S.cfg.clock_type, (v) => setCfg({ clock_type: v }));
  $("#clockColor").value = rgbHex(c.clock_color);
  $("#clockColor").oninput = debounce((e) => setCfg({ clock_color: hexRgb(e.target.value) }), 150);
  const sw = [[255, 150, 60], [255, 220, 160], [255, 255, 255], [255, 60, 40], [255, 70, 180], [150, 90, 255], [60, 140, 255], [0, 220, 200], [60, 230, 90]];
  const drawSw = () => $("#lampSwatches").replaceChildren(...sw.map((col) => h("button", { style: `background:${rgbHex(col)}`, "aria-label": rgbHex(col),
    "aria-pressed": String(rgbHex(col) === rgbHex(S.cfg.lamp_color)),
    onclick: async () => { setCfg({ lamp_color: col }); drawSw(); $("#lampColor").value = rgbHex(col); await setMode("lamp"); } })));
  drawSw();
  $("#lampColor").value = rgbHex(c.lamp_color);
  $("#lampColor").oninput = debounce((e) => { setCfg({ lamp_color: hexRgb(e.target.value) }); drawSw(); }, 150);
  $("#pomoFocus").value = c.pomodoro.focus; $("#pomoBreak").value = c.pomodoro.break;
  $("#pomoFocus").onchange = (e) => setCfg({ pomodoro: { focus: Math.max(1, Math.min(120, +e.target.value || 25)) } });
  $("#pomoBreak").onchange = (e) => setCfg({ pomodoro: { break: Math.max(1, Math.min(60, +e.target.value || 5)) } });
  $("#pomoStart").onclick = async () => { await api.post("/api/pomodoro", { action: "start" }); toast(t("Pomodoro is running – focus!")); poll(); };
}

/* ------------------------------------------------------------------ sound */
function renderSound() {
  const s = S.cfg.sound;
  bindSwitch($("#soundSwitch"), () => s.enabled, (v) => setCfg({ sound: { enabled: v } }));
  bindSwitch($("#muteGame"), () => s.mute_in_game, (v) => setCfg({ sound: { mute_in_game: v } }));
  bindSwitch($("#quietNight"), () => s.quiet_night, (v) => setCfg({ sound: { quiet_night: v } }));
  bindRange($("#volume"), $("#volumeVal"), () => Math.round(s.volume * 100), (v) => setCfg({ sound: { volume: v / 100 } }), (v) => v + " %");
  $("#soundEvents").replaceChildren(...Object.entries(S.meta.sounds).map(([k, label]) => {
    const sw = h("button", { class: "switch", role: "switch", "aria-label": label });
    bindSwitch(sw, () => s.events[k], (v) => setCfg({ sound: { events: { [k]: v } } }));
    return h("li", {}, h("div", { class: "grow" }, h("b", {}, label)),
      h("button", { class: "btn sm ghost", onclick: () => api.post("/api/sound", { name: k }) }, icon("play"), t("Play")), sw);
  }));
}

/* ------------------------------------------------------------------ integrations */
async function renderIntegrations() {
  const cfg = await api.get("/api/config"); S.meta.integrations = cfg.integrations;
  const st = cfg.integrations;
  const card = (kind, logo, bg, title, sub, desc, bullets, on, available = true) => {
    const btn = h("button", { class: "btn " + (on ? "" : "primary"), disabled: !available, onclick: async () => {
      btn.disabled = true;
      try { await api.post("/api/integration", { kind, enable: !on }); toast(t(on ? "{name} turned off" : "{name} turned on", { name: title })); }
      catch (e) { toast(e.message, true); }
      renderIntegrations();
    } }, t(on ? "Turn off" : available ? "Turn on" : "Not installed"));
    return h("div", { class: "card int" },
      h("div", { class: "int-head" }, h("div", { class: "int-logo", style: `background:${bg}` }, logo), h("div", {}, h("b", {}, title), h("span", {}, sub)),
        h("span", { class: "badge " + (on ? "ok" : ""), style: "margin-left:auto" }, t(on ? "On" : "Off"))),
      h("p", {}, t(desc)), h("ul", {}, bullets.map((b) => h("li", {}, t(b)))), h("div", { class: "btn-row" }, btn));
  };
  $("#intGrid").replaceChildren(
    card("claude", "C", "linear-gradient(135deg,#d97757,#b8553a)", "Claude Code", t("hooks in ~/.claude/settings.json"),
      "Ditoo shows when Claude is working, waiting for your approval or has finished.",
      ["working: after you send a prompt", "waiting for you: permission request", "done: end of the answer + jingle", "restart Claude Code after turning it on"], st.claude, st.claude_installed),
    card("codex", "Cx", "linear-gradient(135deg,#1aa58f,#0d5f55)", "OpenAI Codex", t("notify in ~/.codex/config.toml"),
      "After every Codex turn Ditoo shows a check mark and plays a jingle.",
      ["done: end of the agent's turn", "keeps the Codex app's own notify working", "restart the Codex app after turning it on"], st.codex, st.codex_installed),
    card("autostart", icon("power"), "linear-gradient(135deg,#ff6b4a,#ffa25a)", t("Start with Windows"), t("shortcut in the Startup folder"),
      "Ditoo Control starts in the tray after you sign in and reacts right away.",
      ["starts hidden in the tray", "low priority, easy on performance"], st.autostart),
    card("start_menu", icon("overview"), "linear-gradient(135deg,#6f6cff,#9c5cff)", t("Start menu shortcut"), t("find it by typing \"Ditoo\""),
      "Adds Ditoo Control to the Start menu so you can open it like any other app.",
      ["opens the window", "uninstall by turning it off"], st.start_menu));
  const base = `http://127.0.0.1:${S.cfg.http_port}`;
  const ex = [
    ["Text on the display", `curl "${base}/api/notify?text=BUILD%20OK&color=3ddc97"`],
    ["Your own agent's status", `curl "${base}/api/ai?source=agent&state=working"`],
    ["Agent finished", `curl "${base}/api/ai?source=agent&state=done"`],
    ["From any script", `${st.notify_command} text "TESTS PASSED"`],
  ];
  $("#apiExamples").replaceChildren(...ex.map(([w, c]) => h("div", { class: "code" }, h("span", { class: "what" }, t(w)), h("code", {}, c),
    h("button", { class: "btn icon sm ghost", "aria-label": t("Copy"), onclick: async () => { await navigator.clipboard.writeText(c); toast(t("Copied")); } }, icon("copy")))));
}

/* ------------------------------------------------------------------ settings */
function bindSettings() {
  $("#mac").value = S.cfg.mac; $("#port").value = S.cfg.port;
  $("#appVersion").textContent = "v" + S.meta.version;
  $("#devSave").onclick = async () => {
    const mac = $("#mac").value.trim().toUpperCase();
    if (mac && !/^([0-9A-F]{2}:){5}[0-9A-F]{2}$/.test(mac)) return toast(t("That isn't a valid MAC address (e.g. AA:BB:CC:DD:EE:FF)"), true);
    await api.post("/api/config", { mac, port: Math.max(1, Math.min(30, +$("#port").value || 2)) }); S.cfg.mac = mac;
    await api.post("/api/device", { action: "connect" }); toast(t("Connecting…"));
  };
  $("#devFind").onclick = async () => {
    await api.post("/api/config", { mac: "" }); S.cfg.mac = "";
    await api.post("/api/device", { action: "connect" }); toast(t("Looking for a paired Ditoo…"));
  };
  $("#devDisconnect").onclick = async () => { await api.post("/api/device", { action: "disconnect" }); toast(t("Disconnected")); };
  $("#connBtn").onclick = () => {
    if (S.st && S.st.device.status === "error") return openWizard(1);
    api.post("/api/device", { action: "connect" }); toast(t("Connecting…"));
  };
  $("#cityNow").textContent = S.cfg.city || t("not set");
  $("#cityForm").onsubmit = (e) => { e.preventDefault(); searchCity($("#cityQuery").value, $("#cityResults"), () => { $("#cityNow").textContent = S.cfg.city; }); };
  bindSeg($("#langSeg"), () => S.cfg.lang, async (v) => {
    await api.post("/api/config", { lang: v });
    location.reload();
  });
  $("#runWizard").onclick = () => openWizard(0);
}
async function searchCity(q, list, done) {
  q = q.trim(); if (!q) return;
  try {
    const res = await api.get("/api/geocode?q=" + encodeURIComponent(q));
    list.replaceChildren(...(res.length ? res.map((r) => h("li", { class: "clickable", tabindex: 0, onclick: () => {
      setCfg({ city: r.name, lat: r.lat, lon: r.lon }); list.replaceChildren(); toast(t("Weather for {city}", { city: r.name })); renderModes(); done && done();
    } }, h("div", { class: "grow" }, h("b", {}, r.name), h("span", {}, [r.admin, r.country].filter(Boolean).join(", "))), icon("arrow"))) :
      [h("li", {}, h("div", { class: "grow" }, h("span", {}, t("Nothing found – try another spelling"))))]));
  } catch (err) { toast(t("Search failed – are you online?"), true); }
}

/* ------------------------------------------------------------------ explanations */
const C_CPU = "#ff7828", C_GPU = "#6ed23c";
const LEGENDS = {
  monitor: { items: [
    [C_CPU, "C + number", "processor temperature (°C)"],
    [C_GPU, "G + number", "graphics card temperature (°C)"],
    ["grad", "Bar under the number", "load 0–100 % (blue = low, red = high)"],
    ["temp", "Number colour", "green fine · yellow warm · orange warning · red critical"],
    ["#5ab8ff", "Number without the ° mark", "load in % – shown when the temperature isn't available (CPU temperature needs MSI Afterburner)"]] },
  game: { items: [
    ["#00e66e", "Big number on top", "FPS – green ≥ 60, yellow ≥ 30, red below 30"],
    [C_CPU, "Left number + orange line", "processor temperature (°C)"],
    [C_GPU, "Right number + green line", "graphics temperature (°C)"],
    ["ft", "Bottom row", "frame time over the last 16 s – green smooth, yellow slower, red / taller bar = stutter. Not ping or mouse latency – only NVIDIA Reflex measures that"],
    ["#6e6eff", "Controller instead of FPS", "a game runs but RivaTuner isn't measuring FPS (not installed or not running)"]] },
  intro: { items: [["#d25ad2", "Controller + name", "a game just started, the gaming HUD follows in a moment"]] },
  clock: { items: [
    ["#50c8ff", "Top number", "hours"], ["#50c8ff", "Bottom number", "minutes"],
    ["#a0e0ff", "Blinking dots in the middle", "tick every second"],
    ["#2a6a88", "Side columns", "fill up during the minute – full = end of the minute"]] },
  nclock: { items: [["#50c8ff", "Divoom clock", "Ditoo's built-in clock face, runs even without the PC"]] },
  pomo: { items: [
    ["#ff5a3c", "Big number", "minutes left (seconds in the last minute)"],
    ["#ff5a3c", "MIN / BRK / II", "focus / break / paused"],
    ["#ff5a3c", "Frame", "time left – switches off bit by bit"],
    ["#3cdc82", "Green colour", "break"]] },
  pomo_ready: { items: [["#ff5a3c", "Dimmed number", "focus length – the timer isn't running, start it with Start"]] },
  weather: { items: [
    ["#ffcd28", "Picture", "current weather (animated rain, snow, sun, storm, fog)"],
    ["#82dcff", "Number", "outside temperature – blue freezing, light blue chilly, yellow pleasant, orange hot"],
    ["#9696aa", "T bottom left", "tomorrow's forecast (high)"]] },
  weather_loading: { items: [["#9696b4", "Three dots", "downloading the forecast"]] },
  weather_unset: { items: [["#5a8cff", "Pin", "choose your city in Settings to see the weather"]] },
  ai_working: { items: [
    ["#eb7846", "Orange spark", "Claude is working (ring turns clockwise)"],
    ["#28cdb9", "Teal >_", "Codex / ChatGPT is working (ring turns counter-clockwise)"],
    ["#888888", "Taking turns", "both agents are working at once"]] },
  ai_attn: { items: [
    ["#ffcd00", "Exclamation mark", "the agent needs your approval or answer"],
    ["#eb7846", "Corner mark", "colour says who: orange Claude, teal Codex"]] },
  ai_done: { items: [["#28e66e", "Check mark", "the agent finished its task"], ["#eb7846", "Corner mark", "who finished (orange Claude, teal Codex)"]] },
  ai_error: { items: [["#ff3228", "Cross", "the agent reports an error"], ["#eb7846", "Corner mark", "which agent"]] },
  ai_idle: { items: [["#6e6e96", "Dimmed frame", "no agent is working right now"]] },
  hot: { items: [["#ff2a1e", "Thermometer + number", "the temperature passed the critical limit"], ["#ffffff", "CPU / GPU", "which part is overheating"]] },
  fx: { items: [["grad", "Animation", "decoration without information – choose it on the Content page"]] },
  text: { items: [["#ffffff", "Text", "your message (Content page)"]] },
  notify: { items: [["#ffc800", "Frame + text", "a message from a script or webhook, disappears after one pass"]] },
  media: { items: [["grad", "Picture", "your uploaded image or animation"]] },
  media_missing: { items: [["#9696b4", "Empty frame", "upload an image on the Content page"]] },
  viz: { items: [["grad", "Bars", "react to sound playing through the Ditoo"]] },
  lamp: { items: [["#ff9632", "Colour", "the display glows like a lamp"]] },
  off: { items: [["#222222", "Blank display", "nothing is shown"]] },
  test: { items: [["#28e66e", "Rainbow frame + check", "test pattern from the setup"]] },
};
const swatch = (c) => {
  const st = c === "grad" ? "background:linear-gradient(90deg,#00a0ff,#ff2828)"
    : c === "temp" ? "background:linear-gradient(90deg,#00dc5a,#e6dc00,#ff8c00,#ff1e14)"
    : c === "ft" ? "background:linear-gradient(90deg,#00dc6e 60%,#f0c800 60% 80%,#ff2d23 80%)" : `background:${c}`;
  return h("span", { class: "sw", style: st });
};
const legendList = (items) => h("ul", { class: "legend-list" }, items.map(([c, a, b]) => h("li", {}, swatch(c), h("span", {}, h("b", {}, t(a)), " – " + t(b)))));
let legendKey = null;
function updateLegend(st) {
  const id = st.scene.id;
  const key = { img: "media" }[id] || id;
  if (key === legendKey) return;
  legendKey = key;
  const L = LEGENDS[key] || (key === "pomo_ready" ? LEGENDS.pomo_ready : null);
  const box = $("#legend");
  if (!L) { box.replaceChildren(); return; }
  box.replaceChildren(h("div", { class: "legend-title" }, icon("help"), t("What you see")), legendList(L.items));
}

/* tooltips: every element with data-help gets an (i) button */
const tip = h("div", { class: "tip", role: "tooltip", id: "tip" });
document.body.append(tip);
function showTip(btn) {
  tip.textContent = btn.dataset.text; tip.classList.add("on");
  const r = btn.getBoundingClientRect(), tw = Math.min(320, innerWidth - 24);
  tip.style.maxWidth = tw + "px";
  tip.style.left = Math.min(Math.max(12, r.left + r.width / 2 - tw / 2), innerWidth - tw - 12) + "px";
  const below = r.bottom + 10 + tip.offsetHeight < innerHeight;
  tip.style.top = (below ? r.bottom + 8 : r.top - tip.offsetHeight - 8) + "px";
}
function hideTip() { tip.classList.remove("on"); }
function initTips() {
  $$("[data-help]").forEach((el) => {
    if (el.querySelector(".info")) return;
    const b = h("button", { class: "info", type: "button", "aria-label": t("Explanation"), "aria-describedby": "tip", "data-text": el.dataset.help }, "i");
    b.addEventListener("mouseenter", () => showTip(b)); b.addEventListener("mouseleave", hideTip);
    b.addEventListener("focus", () => showTip(b)); b.addEventListener("blur", hideTip);
    b.addEventListener("click", (e) => { e.stopPropagation(); tip.classList.contains("on") ? hideTip() : showTip(b); });
    el.append(b);
  });
}
document.addEventListener("keydown", (e) => { if (e.key === "Escape") hideTip(); });
$(".main").addEventListener("scroll", hideTip, { passive: true });

/* help page */
async function renderHelp() {
  if ($("#helpScreens").childElementCount) return;
  await ensureGallery();
  const pick = [["clock", "clock"], ["monitor", "monitor"], ["game", "game"], ["weather", "weather"], ["ai_claude", "ai_working"],
    ["ai_codex", "ai_working"], ["ai_attn", "ai_attn"], ["ai_done", "ai_done"], ["pomodoro", "pomo"], ["hot", "hot"]];
  for (const [gid, lk] of pick) {
    const g = S.gallery.find((x) => x.id === gid); if (!g) continue;
    const cv = h("canvas", { width: 132, height: 132 });
    $("#helpScreens").append(h("div", { class: "help-screen" }, h("div", { class: "hs-led" }, cv), h("div", {}, h("b", {}, g.title), legendList(LEGENDS[lk].items))));
    new Led(cv, { offColor: [14, 15, 19] }).set(g);
  }
  startLoop();
  $("#helpColors").replaceChildren(...legendList([
    ["temp", "Temperatures", "green up to (warning − 15 °C) · yellow · orange from the warning · red from critical (limits under Automation)"],
    ["grad", "Load", "blue = low, purple = medium, red = full"],
    ["#00e66e", "FPS", "green from 60 · yellow 30–59 · red below 30"],
    ["ft", "Frame time", "green up to 17.5 ms (60+ FPS) · yellow up to 34 ms · red = stutter"],
    ["#eb7846", "Claude", "orange"], ["#28cdb9", "Codex / ChatGPT", "teal"],
  ]).children);
  $("#helpAuto").replaceChildren(...[
    "CPU or GPU overheating – blinking warning and a sound",
    "Notifications from scripts and webhooks",
    "The screen you picked with a shortcut (until the context changes)",
    "An agent just finished its task or reports an error (briefly)",
    "A game is running – gaming HUD",
    "Pomodoro is running",
    "An agent is working or waiting for your answer",
    "None of the above – clock, weather, monitor and effects take turns",
  ].map((x) => h("li", {}, t(x))));
  $("#helpModes").replaceChildren(...S.meta.modes.map((m) => {
    const [ic, title, desc] = MODE_META[m.id];
    return h("div", { class: "hm" }, h("span", { class: "mi" }, icon(ic)), h("div", {}, h("b", {}, t(title)), h("span", {}, t(desc))));
  }));
  const hk = S.cfg.hotkeys;
  $("#helpKeys").replaceChildren(
    ...[[hk.prev, "previous screen"], [hk.next, "next screen"], [hk.auto, "back to Automatic"], [hk.bright, "toggle brightness"]]
      .map(([k, x]) => h("div", { class: "hk" }, combo(k), h("span", { class: "what" }, t(x)))),
    h("p", { class: "note", style: "margin-top:12px" }, t("Screens follow the context: while gaming HUD → monitor → clock → weather, while working with AI agent → pomodoro → clock…, otherwise clock → weather → monitor → effects. Works inside games too.")));
  const faq = [
    ["The display doesn't react although the app says connected", "Ditoo Pro only listens to the first device that connects. Turn off Bluetooth on your phone (or close the Divoom app), then switch Ditoo off and on."],
    ["I don't see the CPU temperature or FPS", "CPU and GPU load (and GPU temperature on NVIDIA cards) work out of the box. The CPU temperature needs MSI Afterburner, FPS needs RivaTuner Statistics Server. Both are free; Windows doesn't offer these values to normal apps. Until then the display shows CPU load instead of the temperature."],
    ["Do I need MSI Afterburner or RivaTuner?", "No, both are optional. Afterburner adds the CPU temperature, RivaTuner adds FPS and frame time (and automatic detection of games that aren't on your list). Clock, weather, AI status, effects, load and NVIDIA GPU temperature work without them. Download links are under Settings, Optional tools."],
    ["The app window doesn't open (Windows 10)", "The window needs Microsoft Edge WebView2, which is part of Windows 11 and most up-to-date Windows 10 PCs. If it's missing, the app opens in your browser instead. Install WebView2 from developer.microsoft.com/microsoft-edge/webview2 and restart the app."],
    ["My game wasn't detected", "Add its .exe on the Games page – or add it with one click from the list of apps RivaTuner is tracking."],
    ["No sounds", "Ditoo has to be connected in Windows as an audio device too (DitooPro-Audio). Sounds are muted on purpose while gaming and at night."],
    ["Claude / Codex doesn't show up", "Turn the integration on under Integrations and restart Claude Code / the Codex app – they only read their settings at start."],
    ["What happens when the Ditoo battery runs out?", "Ditoo doesn't report its battery level over Bluetooth, so the app can't show a percentage. When it switches off, the app shows a message and reconnects by itself once you charge it and switch it on. It also works while charging over USB-C – at a desk, just leave it plugged in."],
    ["Can I switch the display off completely?", "Yes. The Off mode turns the LEDs off (brightness 0). Under Automation the display also switches off when you're away from the PC or lock it, and night brightness can go down to 0."],
    ["How do I turn pomodoro off completely", "The square Stop button under the display preview stops the timer and returns the display to Automatic."],
    ["Does the HUD show input latency or ping?", "No. The bottom graph is frame time (how long one frame takes to draw) – the part of input latency you can influence. Real mouse-to-screen latency is only measured by NVIDIA Reflex in its overlay, and only the game knows its ping; neither is available to other apps."],
    ["Shortcuts don't work", "Another app may use the same combination. Change the letters under Automation → Keyboard shortcuts and restart the app."],
  ];
  $("#helpFaq").replaceChildren(...faq.map(([q, a]) => h("details", {}, h("summary", {}, t(q)), h("p", {}, t(a)))));
}

/* ------------------------------------------------------------------ setup wizard */
const WZ_STEPS = ["Welcome", "Connect", "Test", "Sensors", "Weather", "Finish"];
let wz = 0, wzTimer = null;
function openWizard(step = 0) {
  wz = step;
  $("#wizard").classList.remove("hidden");
  renderWizard();
  clearInterval(wzTimer);
  wzTimer = setInterval(() => { if (wz === 1 || wz === 3) renderWizard(true); }, 1500);
}
function closeWizard(done = true) {
  $("#wizard").classList.add("hidden");
  clearInterval(wzTimer);
  if (done && !S.cfg.setup_done) setCfg({ setup_done: true });
}
const wzHead = (ic, title, text) => [h("div", { class: "wz-icon" }, icon(ic)), h("h2", { id: "wzTitle" }, t(title)), h("p", { class: "wz-lead" }, t(text))];
const stepList = (items) => h("ol", { class: "wz-list" }, items.map(([ic, title, text, btn]) =>
  h("li", {}, h("span", { class: "wz-li-icon" }, icon(ic)), h("div", {}, h("b", {}, t(title)), h("span", {}, t(text)), btn || ""))));
function renderWizard(refreshOnly = false) {
  const st = S.st, body = $("#wzBody");
  $("#wzSteps").replaceChildren(...WZ_STEPS.map((s, i) => h("span", { class: i < wz ? "done" : i === wz ? "on" : "" }, t(s))));
  $("#wzBack").classList.toggle("invisible", wz === 0);
  $("#wzNext").firstChild.textContent = t(wz === WZ_STEPS.length - 1 ? "Finish" : "Continue");
  let content = [];
  if (wz === 0) {
    if (refreshOnly) return;
    const seg = h("div", { class: "seg", role: "radiogroup" }, ...[["auto", "Auto"], ["en", "English"], ["cs", "Čeština"]].map(([v, l]) => h("button", { "data-v": v, role: "radio" }, l)));
    bindSeg(seg, () => S.cfg.lang, async (v) => { await api.post("/api/config", { lang: v }); sessionStorage.setItem("ditoo.wizard", "0"); location.reload(); });
    content = [...wzHead("auto", "Welcome to Ditoo Control", "Let's get your Ditoo Pro reacting to your PC. It takes about a minute."), h("div", { class: "wz-row" }, h("span", {}, t("Language")), seg)];
  } else if (wz === 1) {
    const d = st ? st.device : { status: "connecting" };
    const ok = d.status === "connected";
    const status = h("div", { class: "wz-status " + (ok ? "ok" : d.status === "error" ? "bad" : "busy") }, h("span", { class: "dot " + (ok ? "ok" : d.status === "error" ? "bad" : "busy") }),
      h("b", {}, ok ? t("Connected to {mac}", { mac: d.mac }) : d.status === "error" ? t("Not connected yet") : t("Looking for your Ditoo…")));
    content = [...wzHead("bt", "Connect your Ditoo", "The app talks to Ditoo over Bluetooth. If it doesn't connect on its own, go through these steps."), status];
    if (!ok) content.push(stepList([
      ["power", "1. Switch Ditoo on", "Wait until the display lights up."],
      ["bt", "2. Pair it with this PC", "Windows Settings → Bluetooth → Add device → choose \"DitooPro-Audio\".",
        h("button", { class: "btn sm", onclick: () => openTarget("bluetooth") }, t("Open Bluetooth settings"))],
      ["phone", "3. Disconnect your phone", "Ditoo only obeys the first device. Turn off Bluetooth on your phone or close the Divoom app, then switch Ditoo off and on."],
      ["refresh", "4. Try again", "",
        h("button", { class: "btn sm primary", onclick: async () => { await api.post("/api/config", { mac: S.cfg.mac || "" }); await api.post("/api/device", { action: "connect" }); toast(t("Connecting…")); } }, t("Connect now"))],
    ]));
  } else if (wz === 2) {
    if (refreshOnly) return;
    content = [...wzHead("check", "Let's test it", "Press the button and look at your Ditoo. You should see a rainbow frame with a big check mark."),
      h("div", { class: "wz-actions" },
        h("button", { class: "btn primary", onclick: () => api.post("/api/try", { id: "test", seconds: 10 }) }, icon("play"), t("Show test pattern"))),
      h("div", { class: "wz-row" }, h("span", {}, t("Do you see it?")),
        h("div", { class: "btn-row", style: "margin:0" },
          h("button", { class: "btn", onclick: () => { wz = 3; renderWizard(); } }, t("Yes, I see it")),
          h("button", { class: "btn ghost", onclick: () => {
            $("#wzHint").classList.remove("hidden");
          } }, t("No")))),
      h("div", { class: "callout hidden", id: "wzHint" }, icon("info"), h("div", {}, h("strong", {}, t("Almost there.")), " " +
        t("The phone is usually the culprit: turn its Bluetooth off, switch Ditoo off and on, then press Show test pattern again. Still nothing? Go back one step and press Connect now.")))];
  } else if (wz === 3) {
    const tel = st ? st.telemetry : {};
    const have = (v) => v != null;
    const check = (ok, label, value, need = "needs MSI Afterburner") => h("li", { class: ok ? "ok" : "" },
      h("span", { class: "wz-check" }, icon(ok ? "check" : "x")), h("span", {}, t(label)), h("b", {}, ok ? value : t(need)));
    content = [...wzHead("thermo", "PC readings", "What the app can read on this PC right now. Nothing here is required."),
      h("ul", { class: "wz-checks" },
        check(have(tel.cpu_load), "CPU load", `${Math.round(tel.cpu_load ?? 0)} %`),
        check(have(tel.gpu_load), "GPU load", `${Math.round(tel.gpu_load ?? 0)} %`),
        check(have(tel.gpu_temp), "GPU temperature", `${Math.round(tel.gpu_temp ?? 0)} °C`),
        check(have(tel.cpu_temp), "CPU temperature", `${Math.round(tel.cpu_temp ?? 0)} °C`),
        check(tel.rtss, "FPS in games", t("ready"), "needs RivaTuner")),
      (tel.afterburner && tel.rtss) ? "" : h("div", { class: "callout" }, icon("info"), h("div", { class: "grow" },
        h("strong", {}, t("Want CPU temperature and FPS too?")), " " +
        t("Install these two free tools and keep them running in the background. In Afterburner, open Settings, Monitoring and tick CPU temperature. You can do this any time later."),
        toolRows(tel)))];
  } else if (wz === 4) {
    if (refreshOnly) return;
    const list = h("ul", { class: "list" });
    const inp = h("input", { placeholder: t("Search for a city"), "aria-label": t("City"), value: "" });
    const form = h("form", { class: "add-row", onsubmit: (e) => { e.preventDefault(); searchCity(inp.value, list, () => { wz = 5; renderWizard(); }); } },
      inp, h("button", { class: "btn", type: "submit" }, icon("search"), t("Search")));
    content = [...wzHead("weather", "Where are you?", "For the animated weather. Only the city is used, nothing else leaves your PC."),
      S.cfg.city ? h("div", { class: "wz-status ok" }, h("span", { class: "dot ok" }), h("b", {}, t("Weather for {city}", { city: S.cfg.city }))) : "", form, list];
  } else if (wz === 5) {
    if (refreshOnly) return;
    const ints = S.meta.integrations || {};
    const row = (kind, label, on, available = true) => {
      const sw = h("button", { class: "switch", role: "switch", "aria-label": t(label), disabled: !available });
      bindSwitch(sw, () => on, async (v) => { try { await api.post("/api/integration", { kind, enable: v }); } catch (e) { toast(e.message, true); } });
      return h("div", { class: "wz-row" }, h("span", {}, t(label)), sw);
    };
    content = [...wzHead("check", "All set!", "Ditoo now runs in Automatic mode. A few handy extras:"),
      row("autostart", "Start with Windows", ints.autostart), row("start_menu", "Add to the Start menu", ints.start_menu),
      ints.claude_installed ? row("claude", "Show Claude Code status", ints.claude) : "",
      ints.codex_installed ? row("codex", "Show Codex status", ints.codex) : "",
      h("p", { class: "note" }, t("You can change everything later. Closing the window keeps the app running in the tray next to the clock."))];
  }
  body.replaceChildren(...content.filter(Boolean));
}
$("#wzNext").onclick = () => { if (wz >= WZ_STEPS.length - 1) return closeWizard(true); wz++; renderWizard(); };
$("#wzBack").onclick = () => { if (wz > 0) { wz--; renderWizard(); } };
$("#wzSkip").onclick = () => closeWizard(true);

/* ------------------------------------------------------------------ polling */
let pollTimer = null, polling = false;
async function poll() {
  if (polling) return; polling = true;
  try {
    const st = await api.get("/api/state");
    if (S.langRev != null && st.lang_rev !== S.langRev && st.lang !== LANG) { location.reload(); return; }
    S.langRev = st.lang_rev;
    S.st = st;
    $("#nowLabel").textContent = st.scene.label || "—";
    $("#nowReason").textContent = st.reason || "—";
    if (!$("#brightness").matches(":active")) { $("#brightness").value = st.brightness; rangeFill($("#brightness")); }
    $("#brightnessVal").textContent = st.away ? t("off – you're away") : st.brightness_effective === 0 ? t("display off")
      : st.brightness_effective !== st.brightness ? `${st.brightness_effective} % (${t("night")})` : `${st.brightness} %`;
    mainLed.bright = 0.45 + 0.55 * st.brightness_effective / 100;
    if (st.mode !== S.cfg.mode) { S.cfg.mode = st.mode; updateModeButtons(); }
    updateLegend(st); updateChips(st); updateConn(st); updateTiles(st); updateAI(st); updateLogs(st); updatePomo(st); updateRules(st); updateGames(st);
    if (st.preview_rev !== S.rev) {
      const pv = await api.get("/api/preview");
      S.rev = pv.rev; mainLed.set(pv);
    }
    if ($("#page-content").classList.contains("active") && $("#mediaGrid").childElementCount !== st.media.length) renderContent(st);
  } catch (e) {
    $("#connSub").textContent = t("The app isn't responding");
  } finally { polling = false; }
}
function schedule() {
  clearInterval(pollTimer);
  if (document.hidden) return;              // hidden window = zero work
  pollTimer = setInterval(poll, 1000);
  poll(); startLoop();
}
document.addEventListener("visibilitychange", schedule);

/* ------------------------------------------------------------------ boot */
async function boot() {
  const cfg = await api.get("/api/config");
  S.cfg = cfg.config; S.meta = cfg;
  setLang(cfg.lang);
  translatePage();
  mainLed = new Led($("#mainLed"), { glow: (r, g, b) => $("#stage").style.setProperty("--glow", `${r}, ${g}, ${b}`) });
  renderModes(); renderTiles(); renderRules(); renderGames(); bindContent(); renderSound(); bindSettings();
  bindRange($("#brightness"), null, () => S.cfg.brightness, (v) => setCfg({ brightness: v }));
  initTips();
  ensureGallery().then(() => renderContent(S.st));
  schedule();
  const params = new URLSearchParams(location.search);       // ?page=gallery&wizard=0 (docs screenshots)
  if (params.get("page") && PAGES[params.get("page")]) go(params.get("page"));
  const resume = sessionStorage.getItem("ditoo.wizard");
  if (resume != null) { sessionStorage.removeItem("ditoo.wizard"); openWizard(+resume); }
  else if (params.has("wizard")) { if (params.get("wizard") !== "off") openWizard(+params.get("wizard") || 0); }
  else if (!S.cfg.setup_done) openWizard(0);
}
boot();
