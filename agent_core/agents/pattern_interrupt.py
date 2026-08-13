from pydantic import BaseModel, ConfigDict
from typing import Dict, Any, Optional, List
import random

class ScenarioResponse(BaseModel):
    scenario_type: str  # "agresif", "savunmaci", "ilgili"
    expected_target_reaction: str
    our_counter_move: str

class GeneratedMessage(BaseModel):
    message: str
    strategy: str
    confidence: float
    compliance_score: float  # 0.0 - 100.0 (Kutsal Kural ihlal skoru)
    dialogue_tree: List[ScenarioResponse]

    
    model_config = ConfigDict(extra="forbid")

class PatternInterrupt:
    """
    Beklenti kırma ve mesaj üretimi.
    Kural: Geri çekil ve boşluk bırak. Reaktif olma.
    """
    
    # KESİN, soru iması İÇERMEYEN şablonlar
    TEMPLATES = {
        'mirror_truth': [
            "O {detail}'ı gördüm. Çoğu insan kaçırır ama sen oraya sabitlemişsin. "
            "Bu bir tesadüf değil, bir seçim. Ben de benzer seçimler yaparım.",
            
            "{detail}'daki o {micro_signal}. "
            "Yüzeyde değil, arka planda duran. "
            "Orada bir şey var ve sen bunu biliyorsun."
        ],
        
        'void_resonance': [
            "O {time}'de attığın şey. "
            "Kalabalık yerde yalnızlık hissi. "
            "Ben de o saatlerde kendi sessizliğimle konuşurum.",
            
            "{reference}'daki o an. "
            "Kimse anlamıyor ama sen anlıyorsun. "
            "Ben de anlıyorum."
        ],
        
        'contradiction_bridge': [
            "{surface} diyorsun ama {behavior} yapıyorsun. "
            "Bu bir çelişki değil, bir yorgunluk. "
            "Ben de bazen kendimi ikiye bölerim.",
            
            "O {claimed_identity} pozunun ardındaki {real_signal}. "
            "Maske değil, korunma. Ben de korunurum."
        ]
    }
    
    async def execute(self, input_data: Dict, memory, llm_gateway) -> GeneratedMessage:
        target_analysis = input_data.get('target_analysis', {})
        user_truth = input_data.get('user_mirror', {})
        sacred_rules = input_data.get('sacred_rules', "")
        
        prompt = (
            f"Sen 'Pattern Interrupt' ajanısın. Görevin, beklentileri kıran ve hedefte yankı uyandıran tek bir açılış cümlesi üretmek.\n"
            f"Bununla yetinmeyeceksin; satranç oynar gibi hedefin bu kancaya verebileceği 3 olası tepkiyi (Agresif, Savunmacı, İlgili) öngörüp, 2. ve 3. hamleleri (counter-moves) önceden hazırlayacaksın.\n"
            f"Asla reaktif olma, boşluk bırak, soru sorma.\n\n"
            f"Hedef Analizi: {target_analysis}\n"
            f"Kullanıcı Gerçeği: {user_truth}\n\n"
            f"{sacred_rules}\n\n"
            f"Beklenen JSON formatında çıktını üret. 'message' alanı senin nihai açılış mesajındır.\n"
            f"'dialogue_tree' listesi içinde 3 farklı senaryo ('agresif', 'savunmaci', 'ilgili') için öngörülerini ve karşı-hamlelerini ('our_counter_move') tanımla.\n"
            f"'compliance_score' alanında ise bu mesajın Kutsal Kurallara (varsa) yüzde kaç (0-100) oranında uyduğunu değerlendir."
        )
        
        return await llm_gateway.query_json(prompt, GeneratedMessage)
    
    def _extract_specific_detail(self, analysis: Dict) -> str:
        """
        En spesifik, en görünmeyen detayı çıkar
        """
        signals = analysis.get('micro_signals', [])
        if not signals:
            return "fotoğraftaki detay"
        
        # En yüksek ağırlıklı sinyal
        top_signal = max(signals, key=lambda x: x.psychological_weight)
        return top_signal.evidence[:50]  # İlk 50 karakter
        
    def _extract_micro_signal(self, analysis: Dict) -> str:
        return "sessiz sinyal"
        
    def _extract_temporal_signal(self, analysis: Dict) -> str:
        return "gece vakti"
        
    def _extract_cultural_reference(self, analysis: Dict) -> str:
        return "paylaşım"
