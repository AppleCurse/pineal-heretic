from fastapi import FastAPI, WebSocket, Request, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import json
import os
import hashlib
from datetime import datetime

try:
    from agent_core.task_executor import PinealExecutor, InsufficientEvidenceError
except Exception:
    from task_executor import PinealExecutor, InsufficientEvidenceError

try:
    from scraper import scrape_readonly
except Exception:
    scrape_readonly = None

try:
    from agent_core.scraper.instagram_ghost import InstagramGhostScraper, InsufficientEvidenceError
except Exception:
    InstagramGhostScraper = None

try:
    from agent_core.shadow.shadow_executor import ShadowExecutor
    shadow_executor = ShadowExecutor()
except Exception:
    shadow_executor = None

try:
    from agent_core.chat.dialogue_manager import DialogueManager
    dialogue_manager = DialogueManager()
except Exception:
    dialogue_manager = None

app = FastAPI(title="PINEAL-HERETIC v2.0 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.rooms = {}  # client_id -> {"executor": PinealExecutor, "vault": {}, "websockets": set()}

def get_room(client_id: str) -> dict:
    if client_id not in app.state.rooms:
        app.state.rooms[client_id] = {
            "executor": PinealExecutor(log_callback=lambda lvl, msg: sync_log(client_id, lvl, msg)),
            "vault": {},
            "websockets": set()
        }
    return app.state.rooms[client_id]

def get_executor(client_id: str) -> PinealExecutor:
    return get_room(client_id)["executor"]

def get_vault(client_id: str) -> dict:
    return get_room(client_id)["vault"]


async def broadcast_log(client_id: str, level: str, msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    payload = json.dumps({"type": "log", "ts": ts, "level": level, "msg": msg})
    room = app.state.rooms.get(client_id)
    if not room: return
    ws_set = room["websockets"]
    for ws in list(ws_set):
        try:
            await ws.send_text(payload)
        except:
            ws_set.discard(ws)

def sync_log(client_id: str, level: str, msg: str):
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(broadcast_log(client_id, level, msg))
    except RuntimeError:
        pass 

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    room = get_room(client_id)
    room["websockets"].add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except:
        room["websockets"].discard(websocket)

class InitiatePayload(BaseModel):
    client_id: str
    url: str
    rituals: str
    playlist: str
    envies: str
    aggressiveness: float
    evidence_th: int
    scraper_type: str = "x"

async def run_mission(req: InitiatePayload):
    client_id = req.client_id
    executor = get_executor(client_id)
    vault = get_vault(client_id)
    
    try:
        payload = {
            "user_profile": {
                "private_rituals": [r.strip() for r in req.rituals.split(",")],
                "late_night_playlist": [req.playlist],
                "secret_envies": [e.strip() for e in req.envies.split(",")],
            },
            "target_profile": {"bio": "", "posts": [], "post_times": [], "images": []}
        }
        
        # Otonom Cookie Rotasyonu
        cookie = ""
        cookie_pool = vault.get("x_cookie", "").strip()
        if cookie_pool:
            cookie_list = [c.strip() for c in cookie_pool.split('\n') if c.strip()]
            if cookie_list:
                import random
                cookie = random.choice(cookie_list)
                await broadcast_log(client_id, "INFO", f"DAEMON: Rotasyondan rastgele cookie seçildi.")
                
        if req.url:
            await broadcast_log(client_id, "INFO", f"UPLINK: Hedefe sızılıyor -> {req.url} [{req.scraper_type.upper()}]")
            try:
                from playwright.async_api import async_playwright
                from playwright_stealth import stealth_async
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
                    ctx_kwargs = {"user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
                    
                    if req.scraper_type == "instagram" and InstagramGhostScraper:
                        ctx = await browser.new_context(**ctx_kwargs)
                        if cookie:
                            parsed = []
                            for part in cookie.split(";"):
                                if "=" in part:
                                    k, v = part.split("=", 1)
                                    parsed.append({"name": k.strip(), "value": v.strip(), "domain": ".instagram.com", "path": "/"})
                            if parsed:
                                await ctx.add_cookies(parsed)
                        
                        page = await ctx.new_page()
                        await stealth_async(page)
                        ig_scraper = InstagramGhostScraper(vault_cookies={"sessionid": cookie} if cookie else None)
                        ig_data = await ig_scraper.scrape_async(req.url.strip("/").split("/")[-1], playwright_page=page)
                        
                        payload["target_profile"].update({
                            "username": "@" + ig_data.username,
                            "bio": ig_data.biography or "",
                            "posts": [p.caption for p in ig_data.posts if p.caption],
                            "images": [p.display_url for p in ig_data.posts],
                            "followers": ig_data.follower_count or 0,
                            "is_private": ig_data.is_private
                        })
                        
                    elif req.scraper_type == "cross" and scrape_readonly and InstagramGhostScraper:
                        # Scrape X (runs sync via thread)
                        x_data = await asyncio.to_thread(scrape_readonly, req.url, cookies=cookie)
                        
                        # Scrape IG
                        ctx = await browser.new_context(**ctx_kwargs)
                        if cookie:
                            parsed = []
                            for part in cookie.split(";"):
                                if "=" in part:
                                    k, v = part.split("=", 1)
                                    parsed.append({"name": k.strip(), "value": v.strip(), "domain": ".instagram.com", "path": "/"})
                            if parsed:
                                await ctx.add_cookies(parsed)
                        page = await ctx.new_page()
                        await stealth_async(page)
                        ig_scraper = InstagramGhostScraper(vault_cookies={"sessionid": cookie} if cookie else None)
                        ig_data = await ig_scraper.scrape_async(req.url.strip("/").split("/")[-1], playwright_page=page)
                        
                        merged = x_data.copy()
                        merged["posts"] = x_data.get("posts", []) + [p.caption for p in ig_data.posts if p.caption]
                        merged["images"] = x_data.get("images", []) + [p.display_url for p in ig_data.posts]
                        payload["target_profile"].update({k: v for k, v in merged.items() if v})
                        
                    elif scrape_readonly:
                        data = await asyncio.to_thread(scrape_readonly, req.url, cookies=cookie)
                        payload["target_profile"].update({k: v for k, v in data.items() if v})
                        
                await broadcast_log(client_id, "INFO", f"TELEMETRİ: Veri ele geçirildi.")
            except Exception as e:
                await broadcast_log(client_id, "ERROR", f"UPLINK KOPTU: {str(e)[:100]}")
                if "InsufficientEvidenceError" in type(e).__name__ or "TargetPrivateError" in type(e).__name__:
                    raise e
        
        task_id = f"op_{datetime.now().strftime('%H%M%S')}"
        for attempt in range(1, 4):
            try:
                await broadcast_log(client_id, "INFO", f"OPERASYON BAŞLATILIYOR (Deneme {attempt}/3)...")
                res = await executor.execute_task(payload, task_id)
                await broadcast_result(client_id, res)
                return
            except InsufficientEvidenceError:
                raise
            except Exception as e:
                await broadcast_log(client_id, "ERROR", f"HATA: {type(e).__name__}: {str(e)[:100]}")
                if attempt == 3:
                    await broadcast_log(client_id, "ERROR", "SİSTEM PANİĞİ: MAKSİMUM DENEME AŞILDI.")
    except InsufficientEvidenceError:
        await broadcast_result_error(client_id, "halted_evidence", "DURDURULDU: YETERSİZ KANIT")
    except Exception as e:
        await broadcast_result_error(client_id, "failed", f"SİSTEM PANİĞİ: {str(e)}")

async def broadcast_result_error(client_id, status, msg):
    await broadcast_log(client_id, "ERROR", msg)
    data = {"type": "result", "status": status}
    room = app.state.rooms.get(client_id)
    if not room: return
    ws_set = room["websockets"]
    for ws in list(ws_set):
        try:
            await ws.send_text(json.dumps(data))
        except:
            pass

async def broadcast_result(client_id, res):
    def find(chain, name):
        for e in chain:
            if e["agent"] == name:
                return e["result"]
        return None
        
    data = {
        "type": "result",
        "status": res.status,
        "mirror": find(res.evidence_chain, "mirror_truth"),
        "reading": find(res.evidence_chain, "human_behavior"),
        "reso": find(res.evidence_chain, "resonance_calc"),
        "hook": find(res.evidence_chain, "pattern_interrupt")
    }
    room = app.state.rooms.get(client_id)
    if not room: return
    ws_set = room["websockets"]
    for ws in list(ws_set):
        try:
            await ws.send_text(json.dumps(data))
        except:
            pass

@app.post("/api/initiate")
async def api_initiate(req: InitiatePayload, background_tasks: BackgroundTasks):
    background_tasks.add_task(run_mission, req)
    return {"status": "started"}

class VaultPayload(BaseModel):
    client_id: str
    x_cookie: str = ""
    api_key: str = ""
    tavily_key: str = ""
    serpapi_key: str = ""
    exa_key: str = ""
    
@app.post("/api/vault")
async def api_vault(req: VaultPayload):
    vault = get_vault(req.client_id)
    executor = get_executor(req.client_id)
    if req.x_cookie:
        vault["x_cookie"] = req.x_cookie
        await broadcast_log(req.client_id, "INFO", f"KASA: Cookie belleğe mühürlendi.")
    if req.api_key:
        executor.llm_gateway.set_key(req.api_key)
        if shadow_executor is not None:
            shadow_executor.llm_gateway.set_key(req.api_key)
        if dialogue_manager is not None:
            dialogue_manager.llm.set_key(req.api_key)
        vault["or_key"] = True
        await broadcast_log(req.client_id, "INFO", "KASA: API Anahtarı girildi. Ağ geçidi aktif.")
        
    if req.tavily_key or req.serpapi_key or req.exa_key:
        executor.search_engine.set_keys(tavily=req.tavily_key, serpapi=req.serpapi_key, exa=req.exa_key)
        vault["search_keys"] = True
        await broadcast_log(req.client_id, "INFO", "KASA: Arama Motoru anahtarları mühürlendi.")
        
    return {"status": "secured"}

class OverridePayload(BaseModel):
    client_id: str
    fact: str
    tag: str

@app.post("/api/override")
async def api_override(req: OverridePayload):
    if req.fact.strip():
        executor = get_executor(req.client_id)
        mem_dir = executor.memory.storage_path
        lp = os.path.join(mem_dir, "learnings.json")
        learn = json.load(open(lp, encoding="utf-8")) if os.path.exists(lp) else []
        learn.append({"fact": req.fact.strip(), "tag": req.tag.strip(), "ts": datetime.now().isoformat(), "hash": hashlib.sha256(req.fact.strip().encode()).hexdigest()[:12]})
        with open(lp, "w", encoding="utf-8") as f:
            json.dump(learn, f, ensure_ascii=False, indent=2)
        await broadcast_log(req.client_id, "INFO", f"HAFIZA: Yeni konsept mühürlendi [{req.tag.strip()}]")
    return {"status": "sealed"}

@app.get("/api/telemetry")
async def api_telemetry(client_id: str):
    executor = get_executor(client_id)
    vault = get_vault(client_id)
    return {
        "core": True,
        "gateway": getattr(executor.llm_gateway, 'api_key', None) is not None,
        "scraper": scrape_readonly is not None,
        "vault": "x_cookie" in vault,
        "search_engine": vault.get("search_keys", False)
    }

@app.post("/api/shadow/analyze")
async def shadow_analyze(profile: dict):
    """Dark Triad analizi"""
    if shadow_executor is None:
        return {"error": "Shadow Protocol yüklü değil"}
    from agent_core.psychology.dark_triad import DarkTriadAnalyzer
    analyzer = DarkTriadAnalyzer()
    result = analyzer.analyze(profile)
    return result.model_dump()

@app.post("/api/shadow/generate")
async def shadow_generate(task: dict):
    """Shadow mesaj üretimi"""
    if shadow_executor is None:
        return {"error": "Shadow Protocol yüklü değil"}
    result = await shadow_executor.execute(task)
    return result.model_dump()

class ChatPayload(BaseModel):
    task_id: str
    target_profile: dict
    user_profile: dict
    target_message: str

@app.post("/api/chat/respond")
async def chat_respond(payload: ChatPayload):
    """Hedefin mesajına otonom karşı hamle üretir"""
    if dialogue_manager is None:
        return {"error": "Gölge Sohbet modülü yüklü değil"}
    
    try:
        if payload.task_id not in dialogue_manager.sessions:
            dialogue_manager.start_session(payload.task_id, payload.target_profile, payload.user_profile)
            
        res = await dialogue_manager.generate_response(payload.task_id, payload.target_message)
        return res.model_dump()
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

os.makedirs("frontend", exist_ok=True)
# Sona ekliyoruz ki api rotaları statik dosyalardan önce ezilmesin
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
