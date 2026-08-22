import asyncio
import json
import os
import sys
from pydantic import BaseModel
from agent_core.task_executor import PinealExecutor

os.environ["LIVE_LLM_E2E"] = "1"

# Otonom Verifier Mock (Sadece hedefin gerçekliğini kanıtlamak için Tavily aramasını atlıyoruz)
class MockVerifierResult(BaseModel):
    is_identity_consistent: bool = True
    social_graph_verified: bool = True
    anomalies_detected: list = []
    verifier_score: float = 0.95
    verification_status: str = "verified"

async def mock_verifier_execute(input_data, memory, llm):
    return MockVerifierResult()

async def main():
    print(">>> PINEAL-HERETIC V2.0 - MANUEL ATEŞLEME TESTİ BAŞLIYOR <<<\n")
    
    # API Key Kontrolü
    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        print("[UYARI] OPENROUTER_API_KEY bulunamadı.")
        api_key = input("Gerçek bir E2E (Uçtan Uca) test için OpenRouter API Key girin (veya LOCAL yazıp enter'a basın): ").strip()
        if api_key.upper() == "LOCAL":
            os.environ["USE_LOCAL_LLM"] = "true"
            print("[BİLGİ] Local LLM (Ollama vb.) kullanılacak.")
        elif api_key:
            os.environ["OPENROUTER_API_KEY"] = api_key
        else:
            print("[HATA] LLM bağlantısı olmadan gerçek test yapılamaz. Çıkılıyor.")
            sys.exit(1)
            
    executor = PinealExecutor(log_callback=lambda lvl, msg: print(f"[{lvl}] {msg}"))
    executor.agents["autonomous_verifier"].execute = mock_verifier_execute
    
    input_data = {
        "target_url": "https://instagram.com/ornek_hedef",
        "target_profile": {
            "bio": "Girişimci. Sadece pozitif düşünce. Her şey kontrol altında.",
            "posts": [
                "Bugün her şey mükemmel oldu. Asla geriye bakmam.",
                "Bu işler bensiz yapılamaz. Herkes bana muhtaç.",
                "Yalnızlık benim tercihim, kimseye ihtiyacım yok.",
                "Dün gece saat 03:30. Zihnim susmuyor ama harika hissediyorum."
            ],
            "images": [] 
        },
        "user_profile": {
            "bio": "Gözlemci.",
            "posts": ["Sadece izliyorum.", "Karanlık her zaman bir cevap barındırır."]
        },
        "user_context": {
            "rituals": ["Geceleri çalışır"],
            "playlist": ["Dark Synth"],
            "envies": ["Kontrolü kaybetmek"]
        }
    }

    try:
        status = await executor.execute_task(input_data, "test_target_001")
        print("\n================= TEST SONUCU =================")
        print(f"DURUM: {status.status}")
        
        for evidence in status.evidence_chain:
            agent = evidence.get("agent")
            res = evidence.get("result", {})
            print(f"\n--- [ AJAN: {agent} ] ---")
            print(json.dumps(res, indent=2, ensure_ascii=False))
            
    except Exception as e:
        print(f"\n[KRITIK HATA] Motor ateşlenemedi: {e}")

if __name__ == "__main__":
    asyncio.run(main())
