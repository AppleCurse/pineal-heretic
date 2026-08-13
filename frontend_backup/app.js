const API_URL = "http://localhost:8501";
const client_id = "user_" + Math.random().toString(36).substr(2, 9);
const WS_URL = `ws://localhost:8501/ws/${client_id}`;

let socket;
const logsContainer = document.getElementById('radar-logs');
const radarTx = document.getElementById('radar-tx');
const missionWarning = document.getElementById('mission-warning');
const resultsContainer = document.getElementById('results-container');

// Element Refs
const inpRituals = document.getElementById('inp-rituals');
const inpPlaylist = document.getElementById('inp-playlist');
const inpEnvies = document.getElementById('inp-envies');
const inpTemp = document.getElementById('inp-temp');
const inpEv = document.getElementById('inp-ev');
const valTemp = document.getElementById('val-temp');
const valEv = document.getElementById('val-ev');
const inpTargetUrl = document.getElementById('inp-target-url');
const btnFire = document.getElementById('btn-fire');

// Sliders UI update
inpTemp.addEventListener('input', () => valTemp.textContent = inpTemp.value);
inpEv.addEventListener('input', () => valEv.textContent = inpEv.value);

// Boot
function init() {
    connectWS();
    checkTelemetry();
    setInterval(checkTelemetry, 5000);
}

function connectWS() {
    socket = new WebSocket(WS_URL);
    
    socket.onopen = () => {
        radarTx.textContent = "BAĞLANTI AKTİF";
        radarTx.style.color = "#D4AF37";
    };
    
    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === "log") {
            appendLog(data.ts, data.level, data.msg);
        } else if (data.type === "result") {
            missionWarning.style.display = "none";
            renderResults(data);
        }
    };
    
    socket.onclose = () => {
        radarTx.textContent = "BAĞLANTI KOPTU (YENİDEN DENENİYOR...)";
        radarTx.style.color = "#F85149";
        setTimeout(connectWS, 3000);
    };
}

function appendLog(ts, level, msg) {
    const div = document.createElement('div');
    div.className = `log-${level}`;
    div.innerHTML = `<span class="log-ts">[${ts}]</span> ${escapeHTML(msg)}`;
    logsContainer.appendChild(div);
    logsContainer.scrollTop = logsContainer.scrollHeight;
}

function escapeHTML(str) {
    return str.replace(/[&<>'"]/g, tag => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
    }[tag] || tag));
}

// Telemetry Polling
async function checkTelemetry() {
    try {
        const res = await fetch(`${API_URL}/api/telemetry?client_id=${client_id}`);
        const data = await res.json();
        
        document.getElementById('led-core').className = data.core ? "led led-on" : "led led-off";
        document.getElementById('led-gw').className = data.gateway ? "led led-on" : "led led-off";
        document.getElementById('led-scraper').className = data.scraper ? "led led-on" : "led led-off";
        document.getElementById('led-vault').className = data.vault ? "led led-on" : "led led-off";
    } catch (e) {
        // API down
        ['core', 'gw', 'scraper', 'vault'].forEach(id => {
            document.getElementById(`led-${id}`).className = "led led-off";
        });
    }
}

// Fire action
btnFire.addEventListener('click', async () => {
    resultsContainer.innerHTML = '';
    logsContainer.innerHTML = '';
    appendLog(new Date().toLocaleTimeString('tr-TR'), 'INFO', 'BAŞLATILIYOR...');
    missionWarning.style.display = "block";
    
    const payload = {
        client_id: client_id,
        url: inpTargetUrl.value.trim(),
        rituals: inpRituals.value.trim(),
        playlist: inpPlaylist.value.trim(),
        envies: inpEnvies.value.trim(),
        aggressiveness: parseFloat(inpTemp.value),
        evidence_th: parseInt(inpEv.value)
    };
    
    try {
        const res = await fetch(`${API_URL}/api/initiate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (!res.ok) throw new Error("API Hatası");
    } catch (e) {
        appendLog(new Date().toLocaleTimeString('tr-TR'), 'ERROR', 'API BAĞLANTI HATASI');
        missionWarning.style.display = "none";
    }
});

function renderResults(data) {
    if (data.status === "failed") {
        resultsContainer.innerHTML = `<div class="halt-card">💥 SİSTEM PANİĞİ VEYA HATA</div>`;
        return;
    }
    if (data.status === "halted_evidence") {
        resultsContainer.innerHTML = `<div class="halt-card">🛑 İPTAL: YETERSİZ KANIT</div>`;
        return;
    }
    if (data.status === "halted_frequency") {
        resultsContainer.innerHTML += `<div class="halt-card">🛑 İPTAL: FREKANS UYUŞMAZLIĞI (TEHLİKE)</div>`;
    }

    let html = '';
    if (data.mirror) {
        html += `<div class="card">
            <div class="card-title">🪞 FREKANS UYUMU</div>
            <p>Öz Frekans: ${data.mirror.user_core_frequency}</p>
            <p style="margin-top:5px;">Hizalanma Skoru: <b>${parseFloat(data.mirror.alignment_score).toFixed(2)}</b></p>
        </div>`;
    }
    if (data.reading) {
        html += `<div class="card">
            <div class="card-title">🎯 ZAYIF NOKTA (AŞİL)</div>
            <p>Skor: <b>${parseFloat(data.reading.achilles_score).toFixed(1)}/100</b></p>
            <p style="margin-top:5px;">Yara: ${data.reading.detected_wound}</p>
        </div>`;
    }
    if (data.reso) {
        html += `<div class="card ${data.reso.red_flags.length > 0 ? 'card-red' : ''}" style="grid-column: 1 / -1;">
            <div class="card-title">📡 TAKTİK YAKLAŞIM (Rezonans: ${parseFloat(data.reso.compatibility_score).toFixed(2)})</div>
            <p>${data.reso.recommended_approach}</p>
            ${data.reso.red_flags.length > 0 ? `<p style="margin-top:10px; color:#F85149; font-weight:bold;">🚩 KIRMIZI ÇİZGİLER: ${data.reso.red_flags.join(', ')}</p>` : ''}
        </div>`;
    }
    if (data.hook && data.status === "completed") {
        html += `<div class="hook-card">
            <div class="card-title" style="color:#D4AF37;">⚡ SIZMA MESAJI (PATTERN INTERRUPT)</div>
            <div class="hook-text" id="hook-text-content">${escapeHTML(data.hook.message)}</div>
            <button class="copy-btn" onclick="navigator.clipboard.writeText(document.getElementById('hook-text-content').innerText)">[MESAJI KOPYALA]</button>
        </div>`;
    }
    resultsContainer.innerHTML = html;
}

// Vault Actions
document.getElementById('btn-save-cookie').addEventListener('click', async () => {
    const val = document.getElementById('inp-cookie').value;
    if(!val) return;
    await fetch(`${API_URL}/api/vault`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ client_id, x_cookie: val, api_key: "" })
    });
    checkTelemetry();
});

document.getElementById('btn-save-apikey').addEventListener('click', async () => {
    const val = document.getElementById('inp-apikey').value;
    if(!val) return;
    await fetch(`${API_URL}/api/vault`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ client_id, x_cookie: "", api_key: val })
    });
    checkTelemetry();
});

document.getElementById('btn-seal').addEventListener('click', async () => {
    const fact = document.getElementById('inp-fact').value;
    const tag = document.getElementById('inp-tag').value;
    if(!fact) return;
    await fetch(`${API_URL}/api/override`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ client_id, fact, tag })
    });
    document.getElementById('inp-fact').value = '';
});

// Start
init();
