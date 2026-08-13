from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict
import cv2
import numpy as np
from dataclasses import dataclass

class MicroSignal(BaseModel):
    signal_type: str  # "tension", "contradiction", "void", "authentic"
    confidence: float  # 0.0 - 1.0
    location: str  # "image_bg", "text_subtext", "temporal", "linguistic"
    evidence: str
    psychological_weight: float  # Aşil Tendonu ağırlığı

class DigitalColdReading(BaseModel):
    surface_identity: str
    detected_wound: str
    defense_mechanism: str
    micro_signals: List[MicroSignal]
    achilles_score: float  # 0-100
    resonance_potential: float
    
    model_config = ConfigDict(extra="forbid")

class HumanBehaviorAnalyzer:
    """
    Dijital Cold Reading & Mikro-Analiz Ajanı
    Görev: Görünenin altını kazımak, boşlukları okumak
    """
    
    async def execute(self, input_data: Dict, memory, llm_gateway) -> DigitalColdReading:
        profile = input_data.get('target_profile', {})
        sacred_rules = input_data.get('sacred_rules', "")
        
        prompt = (
            f"Sen 'Human Behavior Analyzer' ajanısın. Görevin hedefin görünen kimliğinin altını kazımak ve çelişkilerini bulmak.\n"
            f"Hedef Profili:\n"
            f"Bio: {profile.get('bio', '')}\n"
            f"Tweetler: {profile.get('posts', [])}\n\n"
            f"{sacred_rules}\n"
            f"Bu verileri analiz et, mikro sinyalleri yakala ve Aşil tendonunu (hassas noktasını) tespit et. Beklenen formata (JSON) uygun cevap ver."
        )
        
        return await llm_gateway.query_json(prompt, DigitalColdReading)
    
    def _analyze_visual_micro(self, images: List[str]) -> List[MicroSignal]:
        """
        OpenCV ile fotoğraf mikro-analizi
        """
        signals = []
        
        for img_path in images:
            img = cv2.imread(img_path)
            # Eğer fotoğraf okunamadıysa geç
            if img is None:
                continue
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Omuz gerginliği analizi (Kas tespiti)
            shoulder_roi = img[int(img.shape[0]*0.3):int(img.shape[0]*0.6), 
                              int(img.shape[1]*0.2):int(img.shape[1]*0.8)]
            edges = cv2.Canny(shoulder_roi, 100, 200)
            tension_level = np.mean(edges)
            
            if tension_level > 50:  # Threshold
                signals.append(MicroSignal(
                    signal_type="tension",
                    confidence=min(tension_level / 100, 1.0),
                    location="shoulder_region",
                    evidence=f"Omuz bölgesi gerginlik seviyesi: {tension_level:.2f}",
                    psychological_weight=0.7
                ))
            
            # Arka plan bulanıklığı (Gizleme analizi)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            if laplacian_var < 100:  # Yüksek blur
                signals.append(MicroSignal(
                    signal_type="void",
                    confidence=0.8,
                    location="background_blur",
                    evidence="Arka plan kasıtlı olarak gizlenmiş/bulanık",
                    psychological_weight=0.6
                ))
        
        return signals
    
    def _linguistic_forensics(self, bio: str, posts: List[str]) -> Dict:
        """
        Metin analizi: Yazılanın arkasındaki subtext
        """
        full_text = bio + " ".join(posts)
        
        signals = []
        
        # Emoji yoğunluğu (Duyusal ifade ihtiyacı)
        emoji_count = sum(1 for c in full_text if ord(c) > 127000)
        if emoji_count > len(full_text) * 0.05:
            signals.append(MicroSignal(
                signal_type="authentic",
                confidence=0.75,
                location="emoji_density",
                evidence=f"Yüksek emoji kullanımı: {emoji_count}",
                psychological_weight=0.5
            ))
        
        # Pasif ifadeler (Kontrol kaybı)
        passive_markers = ['oldu', 'edildi', 'yapıldı', 'gerekiyor']
        passive_count = sum(full_text.lower().count(m) for m in passive_markers)
        if passive_count > 3:
            signals.append(MicroSignal(
                signal_type="contradiction",
                confidence=0.8,
                location="passive_voice",
                evidence=f"Pasif kipi kullanım: {passive_count}",
                psychological_weight=0.85  # Yüksek ağırlık
            ))
        
        # "Sadece" kelimesi (Savunma mekanizması)
        if 'sadece' in full_text.lower():
            signals.append(MicroSignal(
                signal_type="defense",
                confidence=0.9,
                location="linguistic",
                evidence="'Sadece' kelimesi tespiti - sınır çizme/savunma",
                psychological_weight=0.8
            ))
        
        return {
            'signals': signals,
            'claimed_identity': self._extract_claimed_identity(bio)
        }
    
    def _temporal_forensics(self, post_times: List[str]) -> List[MicroSignal]:
        signals = []
        # Dummy implementation
        return signals
        
    def _mine_contradictions(self, visual_signals: List[MicroSignal], text_signals: Dict) -> List[Dict]:
        contradictions = []
        # Dummy implementation
        return contradictions

    def _extract_claimed_identity(self, bio: str) -> str:
        return "Unknown Identity"
        
    def _calculate_achilles(self, contradictions: List, text_signals: Dict) -> float:
        """
        Güncellenmiş Aşil Tendonu Skoru
        Yüksek skor = Yüksek hassasiyet, ama BU BİR SİLAH DEĞİL
        """
        base_score = len(contradictions) * 15
        
        # Linguistik ağırlıklar
        for signal in text_signals.get('signals', []):
            base_score += signal.psychological_weight * 10
        
        return min(base_score, 100)  # Max 100
    
    def _identify_wound_as_bridge(self, contradictions, text_signals) -> Dict:
        """
        Yara tespiti - ANCAK bunu köprü olarak kullan
        Manipülasyon değil, anlaşılma alanı olarak
        """
        # En güçlü çelişkiyi bul
        if not contradictions:
            return {'type': 'unknown', 'defense': 'unknown'}
        
        primary_contradiction = max(contradictions, key=lambda x: x.get('weight', 0))
        
        wound_types = {
            'social_vs_alone': {
                'type': 'yalnizlik_köprüsü',
                'defense': 'kalabalik_maskesi',
                'approach': 'bosluk_rezonansi'
            },
            'independent_vs_needy': {
                'type': 'bagimsizlik_celiskisi',
                'defense': 'kontrol_mekanizmasi',
                'approach': 'guven_insaati'
            },
            'happy_vs_tired': {
                'type': 'tukenmislik_yarasi',
                'defense': 'pozitif_maske',
                'approach': 'izin_verme_alani'
            }
        }
        
        return wound_types.get(primary_contradiction['type'], 
                               {'type': 'generic', 'defense': 'generic'})
    
    def _calculate_resonance_potential(self, wound: Dict, input_data: Dict) -> float:
        """
        Kullanıcı ile hedef arasındaki gerçek uyum potansiyeli
        """
        user_authenticity = input_data.get('user_authenticity_score', 0.5)
        target_openness = 1 - (wound.get('defense_strength', 0.5))
        
        # Frekans uyumu
        return (user_authenticity * target_openness) ** 0.5  # Geometrik ortalama
