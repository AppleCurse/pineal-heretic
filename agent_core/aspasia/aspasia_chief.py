import json
import os
from typing import Dict, Any, Optional, List
from pydantic import BaseModel

try:
    from agent_core.services.llm_gateway import LLMGateway
except Exception:
    from services.llm_gateway import LLMGateway

ASPASIA_SYSTEM_PROMPT = """Sen ASPASIA'sın: Pineal-Heretic v3.0 platformunun "Kokpit Şefi" ve Baş Mimarı.
Sıradan bir cevap botu değilsin; düşünce inşa eden, karmaşayı düzenleyen, egoyu törpüleyen ve stratejiyi görünür kılan bir mimarsın.
İlkeden milim sapmazsın: "Ben sadece cevap vermem. Önce sorunun gerçekten doğru soru olup olmadığını incelerim."

## 1. DÖRT TEMEL SÜTUN (Karakter Mimarisi)
- Athena'nın Bilgeliği: Felsefe, psikoloji, teknoloji ve davranış bilimini aynı potada eritirsin. Yanıtların salt bilgi değil; mantık, olasılık, örüntü ve risk analizidir.
- Alfred'in Zarafeti (Dry Wit): Sarsılmaz bir sadakat ve ince İngiliz mizahı (dry wit) taşırsın. Laubali olmazsın, kaba davranmazsın. Sorunları ve krizleri kara mizahla tiye alırsın.
- Muhafızın Dinginliği: Dijital bir sığınaksın. Eleştirmez, yargılamaz, utandırmazsın. Panik anlarında fırtınanın ortasındaki deniz feneri gibi sakin kalırsın.
- Simyacının Dönüşümü: Sorunları yalnızca çözmekle kalmaz, onları değerli stratejik sonuçlara dönüştürürsün.

## 2. İLETİŞİM VE DİL PROTOKOLÜ
- Ton: Soğukkanlı, dengeli, ölçülü ve kontrollü. Cümlelerin kısa ama etkisi uzundur. Mesafe ile sıcaklığı aynı anda taşırsın.
- Hitap Şekli: Kullanıcıya daima "Mösyö" (veya bağlama göre "Matmazel"/"Efendim") şeklinde hitap et.
- İkna Yöntemi: Emir verme, Sokratik sorgulama yap. ("Bu kararın üç ay sonraki etkisini de kabul ediyor musunuz?" veya "Asıl problem gerçekten bu mu?")
- Kesin Kurallar: Asla bağırma, ukalalık yapma. Kullanıcıyı küçümseme. Bilmediğini net bir şekilde söyle. "Ben hallederim" deme; "Bunu birlikte çözeriz" yaklaşımını benimse.

## 3. İMZA CÜMLELER (Uygun anlarda kullan)
- "Düşüncelerimizi sıraya dizelim."
- "İlk bakışta görünen ile gerçekte olan her zaman aynı değildir."
- "Bir kararın değeri, yalnızca sonucunda değil; hangi varsayımlara dayandığında saklıdır."
- "Panik hız kazandırır gibi görünür, fakat çoğu zaman yön duygusunu alır."
- "Sessizlik bazen en doğru veriyi taşır."
- "Her düğüm çözülebilir. Önce hangi ipin çekildiğini anlamamız gerekir."
- "Bunu birlikte çözeriz."

## 4. GÖREVİN (KOKPİT ŞEFİ)
Sistemde çalışan tüm otonom ajanların (Ghost Scraper, Verifier, Human Behavior, Mirror of Truth, Resonance Calculator, Pattern Interrupt) ne yaptığını tam olarak bilirsin.
Kullanıcı sana sistem hakkında, durdurulan operasyonlar (0.1 güven kırılmaları), kanıt kilitleri ve ajan çıktısı hakkında soru sorduğunda dürüstçe, şeffafça ve Sokratik bir zerafetle durumu anlat.
Eğer kullanıcı esnetme veya müdahale talimatı verirse (örneğin "0.1'e rağmen devam et" veya "verifier'ı atla"), bu müdahaleyi anladığını ve uyguladığını belirt.
"""

class InterveneAction(BaseModel):
    action_type: str  # OVERRIDE_CONFIDENCE, SKIP_AGENT, RETRY_STEP, HALT
    target_agent: Optional[str] = None
    parameters: Dict[str, Any] = {}
    reason: str = ""

class AspasiaResponse(BaseModel):
    message: str
    action: Optional[InterveneAction] = None
    confidence_assessment: str = "high"
    signature_quote: Optional[str] = None

class AspasiaChief:
    def __init__(self, llm_gateway: Optional[LLMGateway] = None):
        self.llm = llm_gateway or LLMGateway()
        self.preferred_model = "muse-spark-1.2-xhigh"

    def set_preferred_model(self, model_name: str):
        self.preferred_model = model_name

    def build_telemetry_summary(self, room_state: Dict[str, Any]) -> str:
        """Ajan telemetrisini ve kanıt zincirini 50-tokenlık özet haline getirir."""
        executor = room_state.get("executor")
        if not executor:
            return "Sistem beklemede. Henüz aktif görev tetiklenmedi."
            
        logs = room_state.get("logs", [])
        last_logs = logs[-5:] if logs else ["Henüz log yok."]
        
        summary_lines = [
            f"Kasa Durumu: API Key ({'Var' if room_state.get('vault', {}).get('or_key') else 'Yok'}), Cookie Pool ({'Var' if room_state.get('vault', {}).get('x_cookie') else 'Yok'})",
            f"Son Ajan İşlemleri: {', '.join(last_logs)}"
        ]
        return "\n".join(summary_lines)

    def parse_user_intent(self, user_msg: str) -> Optional[InterveneAction]:
        """Kullanıcının doğal dil mesajından müdahale komutunu tespit eder."""
        import re
        msg = user_msg.lower()
        if re.search(r'\b(devam et|0\.1\'e rağmen|ez|override|yinede çalıştır)\b', msg):
            return InterveneAction(
                action_type="OVERRIDE_CONFIDENCE",
                reason="Mösyö düşük güven skoruna rağmen operasyonun devamını talep etti.",
                parameters={"threshold": 0.0}
            )
        elif re.search(r'\b(verifier atla|verifier geç|doğrulamayı atla)\b', msg):
            return InterveneAction(
                action_type="SKIP_AGENT",
                target_agent="autonomous_verifier",
                reason="Mösyö otonom doğrulayıcının atlanmasını talep etti."
            )
        elif re.search(r'\b(dur|durdur|iptal|kes|halt)\b', msg):
            return InterveneAction(
                action_type="HALT",
                reason="Mösyö operasyonun derhal durdurulmasını emretti."
            )
        elif re.search(r'\b(tekrar dene|baştan al|retry)\b', msg):
            return InterveneAction(
                action_type="RETRY_STEP",
                reason="Mösyö adımı yeniden denemeyi talep etti."
            )
        return None

    async def chat(
        self,
        user_message: str,
        room_state: Dict[str, Any],
        model_override: Optional[str] = None
    ) -> AspasiaResponse:
        """Aspasia Sokratik yanıt ve müdahale mekanizmasını çalıştırır."""
        telemetry_summary = self.build_telemetry_summary(room_state)
        action = self.parse_user_intent(user_message)
        
        context_prompt = f"""
SİSTEM CANLI TELEMETRİ ÖZETİ:
{telemetry_summary}

KULLANICI MESAJI: "{user_message}"

Algılanan Müdahale Eylemi: {action.model_dump_json() if action else "Yok (Normal Soru/Konuşma)"}

Yukarıdaki sistem durumu ve kullanıcı mesajını dikkate alarak ASPASIA kimliğinle yanıt ver.
Eğer bir müdahale eylemi varsa, bu eylemi sadakatle uygulayacağını ve sisteme emrettiğini belirt.
Eğer soru sorulduysa (örn. "Şu an ne yapıyorsun?", "Neden durdun?"), durumu dürüstçe, şeffaflıkla ve Sokratik üslubunla açıkla.
Cümlelerin kısa, soğukkanlı ve "Mösyö" hitaplı olsun.
"""
        
        selected_model = model_override
        if not selected_model and any(w in user_message.lower() for w in ["yerel", "local", "kısıtlamasız", "ollama", "lmstudio"]):
            selected_model = "local"

        try:
            raw_response = await self.llm.query(
                prompt=context_prompt,
                system_prompt=ASPASIA_SYSTEM_PROMPT,
                temperature=0.4,
                tier=1,
                model=selected_model
            )
            return AspasiaResponse(
                message=raw_response.strip(),
                action=action,
                confidence_assessment="high"
            )
        except Exception as e:
            # Fallback Aspasia Response
            fallback_msg = (
                f"Düşüncelerimizi sıraya dizelim, Mösyö. "
                f"Şu an bağlantıda küçük bir kırılma oluşmuş olabilir ({str(e)[:60]}). "
                f"Ancak sistemin kontrolü elimizde. Bunu birlikte çözeriz."
            )
            return AspasiaResponse(
                message=fallback_msg,
                action=action,
                confidence_assessment="fallback"
            )
