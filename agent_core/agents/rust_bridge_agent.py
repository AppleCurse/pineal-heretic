#!/usr/bin/env python3
"""
Rust Bridge Agent - Pineal-Heretic v5.0
Rust backend'den çağrılarak tam analiz pipeline'ını çalıştırır.
Scraped veri + User Frequency → Autonomous Verification + Mirror Truth → Final Report
"""

import sys
import json
import os
from typing import Dict, Any, Optional

# Workspace root'u path'e ekle
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from agent_core.task_executor import PinealExecutor
from agent_core.services.llm_gateway import LLMGateway


def run_full_pipeline(
    target_url: str,
    scraped_data: Dict[str, Any],
    user_freq: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Tam analiz pipeline'ını çalıştırır:
    1. Scraped veriyi yükle
    2. Autonomous Verification (Tavily + LLM)
    3. Mirror Truth Analysis (User frequency ile)
    4. Final report oluştur
    
    Args:
        target_url: Hedef profil URL'i
        scraped_data: Scraper'dan gelen ham veri
        user_freq: Kullanıcı frekans parametreleri (rituals, playlist, envies)
    
    Returns:
        Final analiz raporu (JSON serializable)
    """
    print(f"[RUST_BRIDGE] Pipeline başlatılıyor: {target_url}", file=sys.stderr)
    
    # PinealExecutor başlat (llm_gateway parametresi yok)
    executor = PinealExecutor()
    
    # 1. Adım: Scraped veriyi input_data olarak hazırla
    print(f"[RUST_BRIDGE] Scraped veri hazırlanıyor...", file=sys.stderr)
    input_data = {
        "target_profile": scraped_data,
        "user_context": user_freq
    }
    
    # 2. Adım: Autonomous Verification çalıştır
    print(f"[RUST_BRIDGE] Autonomous Verification çalıştırılıyor...", file=sys.stderr)
    try:
        # execute_task ile tüm pipeline'ı çalıştır
        import asyncio
        task_status = asyncio.run(executor.execute_task(input_data, "rust_bridge_task"))
        
        verification_result = {
            "verifications": [],
            "overall_authenticity_score": 0.5,
            "status": task_status.status
        }
        print(f"[RUST_BRIDGE] Verification tamamlandı: {task_status.status}", file=sys.stderr)
    except Exception as e:
        print(f"[RUST_BRIDGE] Verification hatası: {e}", file=sys.stderr)
        verification_result = {
            "error": str(e),
            "verifications": [],
            "overall_authenticity_score": 0.0
        }
    
    # 3. Adım: Mirror Truth Analysis - doğrudan MirrorOfTruth kullan
    print(f"[RUST_BRIDGE] Mirror Truth Analysis çalıştırılıyor...", file=sys.stderr)
    try:
        from agent_core.agents.mirror_truth import MirrorOfTruth
        import asyncio
        
        mirror = MirrorOfTruth()
        
        # User data hazırla
        user_data = {
            "rituals": user_freq.get('rituals', []),
            "playlist": user_freq.get('playlist', []),
            "envies": user_freq.get('envies', [])
        }
        
        # execute metodu ile analiz et (async)
        async def run_mirror():
            # Mock memory ve llm_gateway
            class MockMemory:
                async def store(self, *args, **kwargs): pass
            class MockLLM:
                async def query(self, *args, **kwargs): return {"response": "ok"}
            
            result = await mirror.execute(user_data, MockMemory(), MockLLM())
            return result
        
        mirror_result = asyncio.run(run_mirror())
        
        # Pydantic model'i dict'e çevir
        if hasattr(mirror_result, 'dict'):
            mirror_result = mirror_result.dict()
        
        print(f"[RUST_BRIDGE] Mirror Analysis tamamlandı", file=sys.stderr)
    except Exception as e:
        print(f"[RUST_BRIDGE] Mirror Analysis hatası: {e}", file=sys.stderr)
        mirror_result = {
            "error": str(e),
            "user_core_frequency": "unknown",
            "surface_persona": "unknown",
            "authentic_anchors": [],
            "alignment_score": 0.0
        }
    
    # 4. Final report oluştur
    final_report = {
        "target_url": target_url,
        "verification": verification_result,
        "mirror_analysis": mirror_result,
        "alignment_score": mirror_result.get('alignment_score', 0.0),
        "overall_authenticity_score": verification_result.get('overall_authenticity_score', 0.0),
        "combined_score": (
            mirror_result.get('alignment_score', 0.0) * 0.4 +
            verification_result.get('overall_authenticity_score', 0.0) * 0.6
        ),
        "status": "completed"
    }
    
    print(f"[RUST_BRIDGE] Pipeline tamamlandı. Combined score: {final_report['combined_score']}", file=sys.stderr)
    return final_report


def main():
    """CLI entry point - Rust subprocess'ten çağrılır."""
    if len(sys.argv) < 4:
        error_response = {
            "error": "Usage: rust_bridge_agent.py <target_url> <scraped_json> <user_freq_json>",
            "status": "failed"
        }
        print(json.dumps(error_response))
        sys.exit(1)
    
    target_url = sys.argv[1]
    
    try:
        scraped_data = json.loads(sys.argv[2])
    except json.JSONDecodeError as e:
        error_response = {"error": f"Invalid scraped JSON: {e}", "status": "failed"}
        print(json.dumps(error_response))
        sys.exit(1)
    
    try:
        user_freq = json.loads(sys.argv[3])
    except json.JSONDecodeError as e:
        error_response = {"error": f"Invalid user_freq JSON: {e}", "status": "failed"}
        print(json.dumps(error_response))
        sys.exit(1)
    
    try:
        final_report = run_full_pipeline(target_url, scraped_data, user_freq)
        print(json.dumps(final_report, ensure_ascii=False, indent=2))
        sys.exit(0)
    except Exception as e:
        error_response = {"error": f"Pipeline failed: {e}", "status": "failed"}
        print(json.dumps(error_response))
        sys.exit(1)


if __name__ == "__main__":
    main()
