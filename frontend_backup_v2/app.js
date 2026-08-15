/* PINEAL-HERETIC v2.0 — Unified Command Console */
const API_URL = window.location.origin;
const client_id = "user_" + Math.random().toString(36).substr(2, 9);
const WS_URL = `ws://${window.location.host}/ws/${client_id}`;

let socket;
let recCounter = 0;
let emergency = false;
let coverOpen = false;
let switches = { power: true, arm: false, record: false, sigint: true };
let keyLocked = true;

const logsEl = document.getElementById("radar-logs");
const radarTx = document.getElementById("radar-tx");
const missionFlag = document.getElementById("mission-flag");
const resultsEl = document.getElementById("results-container");
const statusLed = document.getElementById("status-led");
const statusText = document.getElementById("status-text");
const recEl = document.getElementById("rec-counter");

const needleCore = document.getElementById("needle-core");
const needleGw = document.getElementById("needle-gateway");
const needleScraper = document.getElementById("needle-scraper");
const subCore = document.getElementById("sub-core");
const subGw = document.getElementById("sub-gateway");
const subScraper = document.getElementById("sub-scraper");

const knobThrottle = document.getElementById("knob-throttle");
const knobMixture = document.getElementById("knob-mixture");
const knobProp = document.getElementById("knob-prop");
const valThrottle = document.getElementById("val-throttle");
const valMixture = document.getElementById("val-mixture");
const valProp = document.getElementById("val-prop");

knobThrottle.addEventListener("input", () => (valThrottle.textContent = knobThrottle.value));
knobMixture.addEventListener("input", () => (valMixture.textContent = knobMixture.value));
knobProp.addEventListener("input", () => (valProp.textContent = knobProp.value));

function setNeedle(el, percent) {
  const clamped = Math.max(0, Math.min(100, percent));
  const angle = -90 + (clamped / 100) * 180;
  el.style.setProperty("--angle", angle + "deg");
}

function updateGauges(telemetry) {
  const corePct = telemetry.core ? 55 + Math.random() * 20 : 5;
  setNeedle(needleCore, corePct);
  subCore.textContent = telemetry.core ? "THERMAL • NOMINAL" : "OFFLINE";
  const gwPct = telemetry.gateway ? 60 + Math.random() * 25 : 8;
  setNeedle(needleGw, gwPct);
  subGw.textContent = telemetry.gateway ? "HANDSHAKE • LINKED" : "NO KEY";
  const scPct = telemetry.scraper ? 45 + Math.random() * 30 : 6;
  setNeedle(needleScraper, scPct);
  subScraper.textContent = telemetry.scraper ? "TR POOL • LIVE" : "MUTE";
}

function refreshStatus() {
  if (emergency) {
    statusLed.className = "status-led emergency";
    statusText.textContent = "STATUS: EMERGENCY";
    statusText.style.color = "#ff6b6b";
    return;
  }
  if (!switches.power) {
    statusLed.className = "status-led offline";
    statusText.textContent = "STATUS: OFFLINE";
    statusText.style.color = "#6a5a4a";
    return;
  }
  statusLed.className = "status-led";
  statusText.textContent = "STATUS: ACTIVE";
  statusText.style.color = "#9eff9e";
}

setInterval(() => {
  if (switches.record && switches.power && !emergency) {
    recCounter = (recCounter + 1) % 10000;
    recEl.textContent = "REC:" + String(recCounter).padStart(4, "0");
  }
}, 180);

document.querySelectorAll(".toggle").forEach((btn) => {
  btn.addEventListener("click", () => {
    const key = btn.dataset.key;
    switches[key] = !switches[key];
    btn.dataset.on = switches[key] ? "1" : "0";
    appendLog(ts(), "INFO", `${key.toUpperCase()} ${switches[key] ? "ENGAGED" : "DISENGAGED"}`);
    refreshStatus();
  });
});

const estopCover = document.getElementById("estop-cover");
const estopBtn = document.getElementById("btn-estop");
estopCover.addEventListener("click", () => {
  coverOpen = !coverOpen;
  estopCover.classList.toggle("open", coverOpen);
  estopBtn.disabled = !coverOpen;
});
estopBtn.addEventListener("click", () => {
  if (!coverOpen) return;
  emergency = !emergency;
  estopBtn.classList.toggle("engaged", emergency);
  if (emergency) {
    switches = { power: false, arm: false, record: false, sigint: false };
    document.querySelectorAll(".toggle").forEach((b) => { b.dataset.on = "0"; });
    setNeedle(needleCore, 3); setNeedle(needleGw, 3); setNeedle(needleScraper, 3);
    appendLog(ts(), "ERROR", "!!! EMERGENCY STOP — ALL NODES OFFLINE !!!");
  } else {
    switches.power = true; switches.sigint = true;
    document.querySelector('[data-key="power"]').dataset.on = "1";
    document.querySelector('[data-key="sigint"]').dataset.on = "1";
    appendLog(ts(), "INFO", "SYSTEM NOMINAL — reboot complete");
  }
  refreshStatus();
});

const keyBtn = document.getElementById("btn-keylock");
const keyState = document.getElementById("key-state");
keyBtn.addEventListener("click", () => {
  keyLocked = !keyLocked;
  keyBtn.dataset.locked = keyLocked ? "1" : "0";
  keyState.textContent = keyLocked ? "AES-256" : "PLAINTEXT";
  appendLog(ts(), "INFO", `KEY ${keyLocked ? "LOCKED AES-256" : "UNLOCKED PLAINTEXT"}`);
});

function ts() {
  return new Date().toLocaleTimeString("tr-TR", { hour12: false });
}
function appendLog(time, level, msg) {
  const div = document.createElement("div");
  div.className = `log-${level}`;
  div.innerHTML = `<span class="log-ts">[${time}]</span> ${escapeHTML(msg)}`;
  logsEl.appendChild(div);
  logsEl.scrollTop = logsEl.scrollHeight;
}
function escapeHTML(str) {
  return String(str).replace(/[&<>'"]/g, (t) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[t] || t)
  );
}
function connectWS() {
  socket = new WebSocket(WS_URL);
  socket.onopen = () => { radarTx.textContent = "BAĞLANTI AKTİF"; radarTx.style.color = "#D4AF37"; };
  socket.onmessage = (ev) => {
    const data = JSON.parse(ev.data);
    if (data.type === "log") appendLog(data.ts || ts(), data.level || "INFO", data.msg);
    else if (data.type === "result") {
      missionFlag.classList.add("hidden");
      document.getElementById("btn-fire").disabled = false;
      renderResults(data);
    }
  };
  socket.onclose = () => {
    radarTx.textContent = "BAĞLANTI KOPTU (YENİDEN…)";
    radarTx.style.color = "#F85149";
    setTimeout(connectWS, 3000);
  };
}
async function checkTelemetry() {
  try {
    const res = await fetch(`${API_URL}/api/telemetry?client_id=${client_id}`);
    const data = await res.json();
    updateGauges(data);
  } catch {
    updateGauges({ core: false, gateway: false, scraper: false, vault: false });
  }
}
document.getElementById("btn-fire").addEventListener("click", async () => {
  if (emergency || !switches.power) {
    appendLog(ts(), "ERROR", "SİSTEM OFFLINE — ATEŞLENEMEZ");
    return;
  }
  resultsEl.innerHTML = "";
  logsEl.innerHTML = "";
  appendLog(ts(), "INFO", "OPERASYON BAŞLATILIYOR…");
  missionFlag.classList.remove("hidden");
  document.getElementById("btn-fire").disabled = true;
  const aggressiveness = parseFloat(knobThrottle.value) / 100;
  const evidence_th = parseInt(knobProp.value, 10);
  const scraper_type = document.querySelector('input[name="scraper_src"]:checked').value;
  const payload = {
    client_id,
    url: document.getElementById("inp-target-url").value.trim(),
    rituals: document.getElementById("inp-rituals").value.trim(),
    playlist: document.getElementById("inp-playlist").value.trim(),
    envies: document.getElementById("inp-envies").value.trim(),
    aggressiveness,
    evidence_th,
    scraper_type,
  };
  try {
    const res = await fetch(`${API_URL}/api/initiate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error("API");
  } catch {
    appendLog(ts(), "ERROR", "API BAĞLANTI HATASI");
    missionFlag.classList.add("hidden");
    document.getElementById("btn-fire").disabled = false;
  }
});
function renderResults(data) {
  if (data.status === "failed") {
    resultsEl.innerHTML = `<div class="halt-card">💥 SİSTEM PANİĞİ VEYA HATA</div>`;
    return;
  }
  if (data.status === "halted_evidence") {
    resultsEl.innerHTML = `<div class="halt-card">🛑 İPTAL: YETERSİZ KANIT</div>`;
    return;
  }
  if (data.status === "halted_frequency") {
    resultsEl.innerHTML = `<div class="halt-card">🛑 İPTAL: FREKANS UYUŞMAZLIĞI</div>`;
  }
  let html = "";
  if (data.mirror) {
    html += `<div class="card"><div class="card-title">🪞 FREKANS</div><p>Öz: ${escapeHTML(data.mirror.user_core_frequency || "—")}</p><p style="margin-top:4px">Hizalanma: <b>${parseFloat(data.mirror.alignment_score || 0).toFixed(2)}</b></p></div>`;
  }
  if (data.reading) {
    html += `<div class="card"><div class="card-title">🎯 AŞİL</div><p>Skor: <b>${parseFloat(data.reading.achilles_score || 0).toFixed(1)}/100</b></p><p style="margin-top:4px">Yara: ${escapeHTML(data.reading.detected_wound || "—")}</p></div>`;
  }
  if (data.reso) {
    html += `<div class="card ${data.reso.red_flags && data.reso.red_flags.length ? "card-red" : ""}" style="grid-column:1/-1"><div class="card-title">📡 REZONANS (${parseFloat(data.reso.compatibility_score || 0).toFixed(2)})</div><p>${escapeHTML(data.reso.recommended_approach || "—")}</p>${data.reso.red_flags && data.reso.red_flags.length ? `<p style="margin-top:8px;color:#ff6b6b;font-weight:700">🚩 ${escapeHTML(data.reso.red_flags.join(", "))}</p>` : ""}</div>`;
  }
  if (data.hook && data.status === "completed") {
    html += `<div class="hook-card"><div class="card-title" style="color:#D4AF37">⚡ PATTERN INTERRUPT</div><div class="hook-text" id="hook-text">${escapeHTML(data.hook.message || "")}</div><button class="copy-btn" onclick="navigator.clipboard.writeText(document.getElementById('hook-text').innerText)">[MESAJI KOPYALA]</button></div>`;
  }
  resultsEl.innerHTML = html;
}
document.getElementById("btn-save-cookie").addEventListener("click", async () => {
  const val = document.getElementById("inp-cookie").value;
  if (!val) return;
  // Multiple cookies can be sent as is, they will be parsed in backend
  await fetch(`${API_URL}/api/vault`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ client_id, x_cookie: val, api_key: "" }) });
  appendLog(ts(), "INFO", "KASA: Cookie(ler) mühürlendi");
  checkTelemetry();
});
document.getElementById("btn-save-apikey").addEventListener("click", async () => {
  const val = document.getElementById("inp-apikey").value;
  if (!val) return;
  await fetch(`${API_URL}/api/vault`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ client_id, x_cookie: "", api_key: val }) });
  appendLog(ts(), "INFO", "KASA: API anahtarı ateşlendi");
  checkTelemetry();
});
document.getElementById("btn-seal").addEventListener("click", async () => {
  const fact = document.getElementById("inp-fact").value;
  const tag = document.getElementById("inp-tag").value;
  if (!fact) return;
  await fetch(`${API_URL}/api/override`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ client_id, fact, tag }) });
  appendLog(ts(), "INFO", `HAFIZA: Kural mühürlendi [${tag}]`);
  document.getElementById("inp-fact").value = "";
});

const chatScroll = document.getElementById("chat-scroll");
const chatInput = document.getElementById("chat-input");
const intercomLed = document.getElementById("intercom-led");
const vuNeedle = document.getElementById("vu-needle");
const pttBtn = document.getElementById("btn-ptt");
const pttHint = document.getElementById("ptt-hint");
const pttBars = document.getElementById("ptt-bars");
let pttActive = false;
let vuTimer = null;

function addChatMessage(role, text) {
  const wrap = document.createElement("div");
  wrap.className = `chat-msg ${role}`;
  const label = role === "user" ? "YOU → HERETIC" : "HERETIC → YOU";
  wrap.innerHTML = `<div class="chat-bubble"><div class="chat-meta"><span class="dot"></span>${label} • ${ts()}</div><div>${escapeHTML(text)}</div></div>`;
  chatScroll.appendChild(wrap);
  chatScroll.scrollTop = chatScroll.scrollHeight;
}
function setVU(level) {
  const angle = -45 + (Math.max(0, Math.min(100, level)) / 100) * 90;
  vuNeedle.style.setProperty("--vu", angle + "deg");
}
function startPTTVisual() {
  pttActive = true;
  pttBtn.classList.add("transmitting");
  intercomLed.classList.add("live");
  pttHint.textContent = "TRANSMITTING…";
  pttBars.innerHTML = "";
  for (let i = 0; i < 16; i++) {
    const bar = document.createElement("div");
    bar.className = "ptt-bar";
    bar.style.height = 6 + Math.random() * 18 + "px";
    bar.style.animationDelay = i * 40 + "ms";
    pttBars.appendChild(bar);
  }
  vuTimer = setInterval(() => setVU(30 + Math.random() * 60), 80);
}
function stopPTTVisual() {
  pttActive = false;
  pttBtn.classList.remove("transmitting");
  intercomLed.classList.remove("live");
  pttHint.textContent = "HOLD • SPEAK";
  pttBars.innerHTML = '<span class="ptt-standby">STANDBY — PRESS PTT</span>';
  clearInterval(vuTimer);
  setVU(5);
}
function bindPTT(el) {
  const down = (e) => { e.preventDefault(); if (emergency || !switches.power) return; startPTTVisual(); };
  const up = () => {
    if (!pttActive) return;
    stopPTTVisual();
    if (chatInput.value.trim()) sendChat();
    else addChatMessage("heretic", "Sinyal alındı. Hedef URL ve frekansını ayarla, sonra ATEŞLE.");
  };
  el.addEventListener("mousedown", down);
  el.addEventListener("mouseup", up);
  el.addEventListener("mouseleave", () => { if (pttActive) up(); });
  el.addEventListener("touchstart", down, { passive: false });
  el.addEventListener("touchend", up);
}
bindPTT(pttBtn);
bindPTT(document.getElementById("btn-chat-ptt"));
function sendChat() {
  const text = chatInput.value.trim();
  if (!text) return;
  addChatMessage("user", text);
  chatInput.value = "";
  setTimeout(() => addChatMessage("heretic", "Not alındı. Tam rezonans için üstteki ATEŞLE ile operasyonu başlat."), 600);
}
document.getElementById("btn-chat-send").addEventListener("click", sendChat);
chatInput.addEventListener("keydown", (e) => { if (e.key === "Enter") sendChat(); });
const _origRenderResults = renderResults;
renderResults = function (data) {
  _origRenderResults(data);
  if (data.hook && data.hook.message && data.status === "completed") {
    intercomLed.classList.add("live");
    setTimeout(() => intercomLed.classList.remove("live"), 4000);
    addChatMessage("heretic", data.hook.message);
    setVU(70);
    setTimeout(() => setVU(10), 1200);
  } else if (data.status === "halted_evidence" || data.status === "halted_frequency") {
    addChatMessage("heretic", data.status === "halted_evidence"
      ? "Kanal kapandı: yetersiz kanıt. Daha fazla sinyal lazım."
      : "Frekans uyuşmazlığı. Bu hedefe rezonans kurulamaz.");
  }
};
addChatMessage("heretic", "Heretic Channel açık. Frekansını ayarla, hedefi gir, ATEŞLE — ya da PTT ile rezonans iste.");
function init() {
  connectWS();
  checkTelemetry();
  setInterval(checkTelemetry, 4000);
  refreshStatus();
  setNeedle(needleCore, 40);
  setNeedle(needleGw, 35);
  setNeedle(needleScraper, 30);
  setVU(8);
  appendLog(ts(), "INFO", "PINEAL-HERETIC v2.0 — SIGINT CONSOLE ONLINE");
}
init();

document.getElementById("btn-shadow").addEventListener("click", async () => {
    const btn = document.getElementById("btn-shadow");
    btn.disabled = true;
    btn.innerText = "YÜKLENİYOR...";
    
    // We assume the user profile input is from rituals and envies
    const user = {
        rituals: document.getElementById("inp-rituals").value.split(","),
        music: document.getElementById("inp-playlist").value,
        envies: document.getElementById("inp-envies").value
    };
    
    // For the target profile, we try to gather it from the existing result if they ran a scrape first,
    // otherwise we just send the URL and we would need it to be scraped. The user plan assumes target bio/posts are passed.
    // If they already ran a scrape, `window.lastScrapedTarget` could be used.
    // Let us fetch the target info from the DOM if available, otherwise just use mock
    const targetUrl = document.getElementById("inp-target-url").value;
    
    const target = window.lastScrapedTarget || {
        username: targetUrl.split("/").pop() || "hedef_kisi",
        bio: "Gerçek bio verisi scraperdan alınmadı.",
        posts: ["test post", "başka bir post"]
    };

    try {
        const response = await fetch("/api/shadow/generate", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                target_profile: target,
                user_profile: user,
                desired_action: "cevap versin",
                target_beliefs: ["anlaşılmak", "özel hissetmek"]
            })
        });
        
        const result = await response.json();
        
        if (result.error) {
            alert(result.error);
            return;
        }

        const darkMeter = `
            <div class="dark-profile">
                <div class="meter">
                    <label>Machiavellianism</label>
                    <progress value="${result.dark_profile.machiavellianism * 100}" max="100"></progress>
                </div>
                <div class="meter">
                    <label>Narcissism</label>
                    <progress value="${result.dark_profile.narcissism * 100}" max="100"></progress>
                </div>
                <div class="meter">
                    <label>Psychopathy</label>
                    <progress value="${result.dark_profile.psychopathy * 100}" max="100"></progress>
                </div>
                <div class="exploitability ${result.confidence > 0.7 ? "high" : "low"}">
                    Exploitability: ${(result.confidence * 100).toFixed(0)}%
                </div>
            </div>
        `;
        
        const message = `
            <div class="shadow-message">
                <div class="strategy-tag">${result.strategy}</div>
                <div class="message-text" style="color: #fff; font-size: 1.1rem; line-height: 1.5;">${result.message}</div>
            </div>
        `;
        
        // Append it to results container instead of overwriting, so we can see it with normal results
        const container = document.getElementById("results-container");
        const div = document.createElement("div");
        div.style.gridColumn = "1 / -1";
        div.innerHTML = darkMeter + message;
        container.prepend(div);
        
    } catch (e) {
        alert("Shadow Mode Error: " + e);
    } finally {
        btn.disabled = false;
        btn.innerText = "💀 SHADOW MODE";
    }
});


let activeChatTaskId = "mock_task_" + Date.now();

document.getElementById("btn-chat").addEventListener("click", async () => {
    const inputEl = document.getElementById("inp-chat");
    const msg = inputEl.value.trim();
    if (!msg) return;

    const chatBtn = document.getElementById("btn-chat");
    chatBtn.disabled = true;
    chatBtn.innerText = "DÜŞÜNÜLÜYOR...";

    const histEl = document.getElementById("chat-history");
    histEl.innerHTML += `<div class="chat-bubble target"><div class="chat-meta">Hedef</div>${escapeHTML(msg)}</div>`;
    histEl.scrollTop = histEl.scrollHeight;
    inputEl.value = "";

    const user = {
        rituals: document.getElementById("inp-rituals").value.split(","),
        music: document.getElementById("inp-playlist").value,
        envies: document.getElementById("inp-envies").value
    };
    
    const targetUrl = document.getElementById("inp-target-url").value;
    const target = window.lastScrapedTarget || {
        username: targetUrl.split("/").pop() || "hedef_kisi",
        bio: "Gerçek veri scraperdan alınmadı.",
    };

    try {
        const response = await fetch("/api/chat/respond", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                task_id: activeChatTaskId,
                target_profile: target,
                user_profile: user,
                target_message: msg
            })
        });
        
        const result = await response.json();
        
        if (result.error) {
            alert(result.error);
            return;
        }

        const analysisStr = `Duruş: ${result.stance} | ${result.internal_analysis}`;
        appendLog(ts(), "WARN", `GÖLGE ANALİZİ: ${analysisStr}`);

        histEl.innerHTML += `<div class="chat-bubble agent"><div class="chat-meta">Pineal-Heretic (Counter-move)</div>${escapeHTML(result.next_move)}</div>`;
        histEl.scrollTop = histEl.scrollHeight;
        
    } catch (e) {
        alert("Chat Error: " + e);
    } finally {
        chatBtn.disabled = false;
        chatBtn.innerText = "YANIT ÜRET";
    }
});

