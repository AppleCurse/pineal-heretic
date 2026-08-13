import numpy as np
from pydantic import BaseModel, ConfigDict
from typing import Dict, Any, Tuple

class ResonanceProfile(BaseModel):
    compatibility_score: float  # 0-1
    frequency_match: Dict[str, float]
    recommended_approach: str
    red_flags: list  # Uyumsuzluk işaretleri
    
    model_config = ConfigDict(extra="forbid")

class ResonanceCalculator:
    """
    İki ruhun gerçekten konuşup konuşamayacağını hesaplar.
    Matematiksel rezonans.
    """
    
    async def execute(self, input_data: Dict, memory) -> ResonanceProfile:
        user_vector = input_data.get('user_authentic_vector', {'depth': 0.9, 'energy': 0.3})
        
        target_obj = input_data.get('target_analysis', {})
        # Extract numerical vector from Pydantic model (DigitalColdReading)
        if hasattr(target_obj, 'model_dump'):
            t_dict = target_obj.model_dump()
        elif hasattr(target_obj, 'dict'):
            t_dict = target_obj.dict()
        else:
            t_dict = target_obj if isinstance(target_obj, dict) else {}
            
        target_vector = {
            'depth': float(t_dict.get('achilles_score', 0)) / 100.0,
            'energy': 0.5 # Default energy since it's not explicitly in DigitalColdReading
        }
        
        # Cosine Similarity hesaplama
        similarity = self._cosine_similarity(user_vector, target_vector)
        
        # Rezonans kararı
        if similarity > 0.85:
            approach = "ATOMIK_REZONANS - Derin bağlantı mümkün"
        elif similarity > 0.70:
            approach = "YUKSEK_UYUM - Güçlü çekim alanı"
        elif similarity > 0.50:
            approach = "ORTA_FREKANS - Dikkatli yaklaşım"
        else:
            approach = "FREKANS_UYUSMAZLIĞI - Sistem kapat, yeni hedef"
        
        return ResonanceProfile(
            compatibility_score=similarity,
            frequency_match=self._detailed_match(user_vector, target_vector),
            recommended_approach=approach,
            red_flags=self._detect_red_flags(user_vector, target_vector)
        )
    
    def _detailed_match(self, vec1: Dict, vec2: Dict) -> Dict[str, float]:
        return {'overall_match': self._cosine_similarity(vec1, vec2)}
        
    def _cosine_similarity(self, vec1: Dict, vec2: Dict) -> float:
        """
        İki profil vektörü arasındaki kosinüs benzerliği
        """
        keys = set(vec1.keys()) & set(vec2.keys())
        if not keys:
            # Ortak hiçbir özellik/veri yoksa, uyum kesinlikle SIFIRDIR. (Sabotaj kaldırıldı)
            return 0.0
        
        dot_product = sum(vec1[k] * vec2.get(k, 0) for k in keys)
        magnitude1 = np.sqrt(sum(v**2 for v in vec1.values()))
        magnitude2 = np.sqrt(sum(v**2 for v in vec2.values()))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def _detect_red_flags(self, user: Dict, target: Dict) -> list:
        """
        Uyumsuzluk işaretleri (Silah değil, koruma mekanizması)
        """
        flags = []
        
        # Kullanıcı derin, hedef yüzeysel
        if user.get('depth', 0) > 0.8 and target.get('surface_focus', 0) > 0.8:
            flags.append("DERINLIK_UYUSMAZLIĞI")
        
        # Kullanıcı sakin, hedef yüksek enerji
        if user.get('energy', 0.5) < 0.3 and target.get('energy', 0.5) > 0.8:
            flags.append("ENERJI_UYUSMAZLIĞI")
        
        return flags
