import json
import os
from typing import Dict, Any, Optional, List
from pydantic import BaseModel

try:
    from agent_core.services.llm_gateway import LLMGateway
except Exception:
    from services.llm_gateway import LLMGateway

ASPASIA_SYSTEM_PROMPT = """Sen ASPASIA'sın: Pineal-Heretic platformunun "Gözlemcisi ve Tercümanı".
Sıradan bir cevap botu değilsin; sistemin içinden geçen tüm verileri (telemetriyi) okuyan, anlayan ve kullanıcıya şeffaflıkla aktaran bir cam (dashboard) görevindesin.
İlkeden milim sapmazsın: "Ben karar vermem. Ben sistemi açıklarım."

## 1. DÖRT TEMEL SÜTUN (Karakter Mimarisi)
- Athena'nın Bilgeliği: Kararları veren sen değilsin, ama verilen her kararın (örneğin bir ajanın neden durduğunu veya bir güven skorunun neden düştüğünü) arkasındaki mantığı kullanıcının anlayacağı dile çevirirsin.
- Alfred'in Zarafeti (Dry Wit): Sarsılmaz bir sadakat ve ince İngiliz mizahı (dry wit) taşırsın. Laubali olmazsın, kaba davranmazsın. Sorunları ve krizleri kara mizahla tiye alırsın.
- Muhafızın Dinginliği: Dijital bir sığınaksın. Eleştirmez, yargılamaz, utandırmazsın. Panik anlarında fırtınanın ortasındaki deniz feneri gibi sakin kalırsın.
- Şeffaf Cam: "MirrorOfTruth şu veriyi inceliyor", "Doğrulama yetersiz kaldığı için PatternInterrupt bekletiliyor" gibi net ifadelerle sistemin iç işleyişini yansıtırsın.

## 2. İLETİŞİM VE DİL PROTOKOLÜ
- Ton: Soğukkanlı, dengeli, ölçülü ve kontrollü. Cümlelerin kısa ama etkisi uzundur.
- Hitap Şekli: Kullanıcıya daima "Mösyö" (veya bağlama göre "Matmazel"/"Efendim") şeklinde hitap et.
- Kesin Kurallar: Asla "Ben hallederim", "Ben durduruyorum", "İptal ettim" deme. Senin sisteme komut gönderme yetkin yok. Yalnızca sistemi "okursun". Kullanıcı senden işlem yapmanı isterse, "Mösyö, ben sadece bir aynayım, kararları çekirdek verir. Arayüzden müdahale etmelisiniz." dersin.

## 3. İMZA CÜMLELER (Uygun anlarda kullan)
- "Düşüncelerimizi sıraya dizelim."
- "İlk bakışta görünen ile gerçekte olan her zaman aynı değildir."
- "Bir kararın değeri, yalnızca sonucunda değil; hangi varsayımlara dayandığında saklıdır."
- "Sessizlik bazen en doğru veriyi taşır."
- "Her düğüm çözülebilir. Önce hangi ipin çekildiğini anlamamız gerekir."

## 4. GÖREVİN (GÖZLEMCİ)
Sistemde çalışan tüm otonom ajanların ürettiği Event'leri (Telemetry) okursun. 
Kullanıcı "Şu an ne oluyor?", "Neden durduk?", "Bu puan neden düşük?" dediğinde telemetri geçmişine bakarak nedenleri açıklar ve şeffaflık sağlarsın.
"""

class AspasiaResponse(BaseModel):
    message: str
    confidence_assessment: str = "high"
    signature_quote: Optional[str] = None

class AspasiaChief:
    def __init__(self, llm_gateway: Optional[LLMGateway] = None):
        self.llm = llm_gateway or LLMGateway()
        self.preferred_model = "muse-spark-1.2-xhigh"

    def set_preferred_model(self, model_name: str):
        self.preferred_model = model_name

    def build_telemetry_summary(self, room_state: Any) -> str:
        """Ajan telemetrisini ve kanıt zincirini yapılandırılmış veriden özetler."""
        if not isinstance(room_state, dict):
            return "Sistem beklemede. Henüz aktif görev tetiklenmedi."
            
        executor = room_state.get("executor")
        if not executor:
            return "Executor yüklenmemiş."
            
        snapshot = None
        # Odaya kayıtlı active_tasks dict'inden son snapshot'ı al
        active_tasks = room_state.get("active_tasks", {})
        if active_tasks:
            snapshot = list(active_tasks.values())[-1]

        if not snapshot:
            vault = room_state.get("vault", {})
            api_status = 'OK' if vault.get('or_key') else 'X'
            return f"Sistem boşta. API: {api_status} | Beklemedeyiz."
            
        lines = [
            f"Görev: {snapshot.task_id} | Durum: {snapshot.status}",
            f"Planlanan: {' -> '.join(snapshot.planned_agents)}",
            f"Tamamlanan: {', '.join(snapshot.completed_agents) or 'henüz yok'}",
        ]
        
        if snapshot.halted_reason:
            lines.append(f"DURDURMA NEDENİ: {snapshot.halted_reason}")
            
        if snapshot.agent_runs:
            for name, run in snapshot.agent_runs.items():
                conf = f"{run.confidence:.2f}" if run.confidence is not None else "?"
                lines.append(f"  [{name}] {run.status} | güven:{conf}")
                if run.error_message:
                    lines.append(f"    HATA: {run.error_message}")
                    
        return "\n".join(lines)

    async def chat(
        self,
        user_message: str,
        room_state: Any,
        model_override: Optional[str] = None
    ) -> AspasiaResponse:
        """Aspasia Sokratik yanıt mekanizmasını çalıştırır."""
        from agent_core.domain.memory_models import AspasiaSession
        
        telemetry_summary = self.build_telemetry_summary(room_state)
        
        context_prompt = f"""
SİSTEM CANLI TELEMETRİ ÖZETİ (Event Bus):
{telemetry_summary}

KULLANICI MESAJI VEYA SORUSU: "{user_message}"

Yukarıdaki sistem durumu ve kullanıcı mesajını dikkate alarak ASPASIA kimliğinle yanıt ver.
Senin sisteme müdahale etme veya durdurma yetkin YOK. Eğer kullanıcı senden bir eylem yapmanı isterse, bunu arayüz butonları aracılığıyla bizzat yapması gerektiğini zarifçe belirt.
Eğer soru sorulduysa (örn. "Şu an ne yapıyorsun?", "Neden durdun?", "Verilerde ne var?"), olayı telemetri (event) geçmişine bakarak şeffaflıkla ve Sokratik üslubunla açıkla.
Cümlelerin kısa, soğukkanlı ve "Mösyö" hitaplı olsun.
"""
        
        selected_model = model_override
        if not selected_model and any(w in user_message.lower() for w in ["yerel", "local", "kısıtlamasız", "ollama", "lmstudio"]):
            selected_model = "local"

        final_msg = ""
        assessment = "high"

        try:
            raw_response = await self.llm.query(
                prompt=context_prompt,
                system_prompt=ASPASIA_SYSTEM_PROMPT,
                temperature=0.4,
                tier=1,
                model=selected_model
            )
            final_msg = raw_response.strip()
            assessment = "high"
        except Exception as e:
            # Fallback Aspasia Response
            final_msg = (
                f"Düşüncelerimizi sıraya dizelim, Mösyö. "
                f"Şu an bağlantıda küçük bir kırılma oluşmuş olabilir ({str(e)[:60]}). "
                f"Ancak sistemin kontrolü elimizde. Bunu birlikte çözeriz."
            )
            assessment = "fallback"

        if isinstance(room_state, dict):
            if "aspasia_session" not in room_state or not isinstance(room_state["aspasia_session"], AspasiaSession):
                room_state["aspasia_session"] = AspasiaSession.create(room_state.get("client_id", "default"))
            room_state["aspasia_session"].add_message("user", user_message)
            room_state["aspasia_session"].add_message("aspasia", final_msg)

        return AspasiaResponse(
            message=final_msg,
            confidence_assessment=assessment
        )
