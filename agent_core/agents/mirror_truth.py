from pydantic import BaseModel, ConfigDict
from typing import Dict, Any

class MirrorReflection(BaseModel):
    user_core_frequency: str  # Kullanıcının gerçek frekansı
    surface_persona: str      # Dışarıya yansıttığı
    alignment_score: float      # Uyum skoru (0-1)
    authentic_anchors: list   # Gerçekliğin sabit noktaları
    
    model_config = ConfigDict(extra="forbid")

class MirrorOfTruth:
    """
    Kullanıcının kendine ayna tutması.
    Yüzey vs. Öz ayrımı.
    """
    
    async def execute(self, input_data: Dict, memory, llm_gateway) -> MirrorReflection:
        user_data = input_data.get('user_profile', {})
        sacred_rules = input_data.get('sacred_rules', "")
        
        prompt = (
            f"Sen 'Mirror of Truth' ajanısın. Görevin, verilen kullanıcı verisinden yüzey kimliğini ve gerçek (core) frekansı bulmak.\n"
            f"Kullanıcı Verisi:\n"
            f"Ritüeller: {user_data.get('private_rituals', [])}\n"
            f"Müzik: {user_data.get('late_night_playlist', [])}\n"
            f"Kıskançlık/Arzu: {user_data.get('secret_envies', [])}\n\n"
            f"{sacred_rules}\n"
            f"Şimdi bu verileri analiz et ve beklenen JSON formatında çıktı üret."
        )
        
        # Pydantic şemasıyla katı sorgu
        return await llm_gateway.query_json(prompt, MirrorReflection)
        
    def _calculate_alignment(self, surface: str, core: str, user_data: Dict) -> float:
        return user_data.get('authenticity_score', 0.8) if isinstance(user_data, dict) else 0.8
    
    def _extract_core_frequency(self, user_data: Dict) -> str:
        """
        Kullanıcının yalnız kaldığında, kimse görmediğinde yaptığı şeyler
        """
        rituals = user_data.get('private_rituals', [])
        music_taste = user_data.get('late_night_playlist', [])
        envy_triggers = user_data.get('secret_envies', [])
        
        # Frekans vektörü oluştur
        frequency_vector = {
            'introversion': len(rituals) > 3,
            'depth_seeking': 'acoustic' in str(music_taste).lower() or 'jazz' in str(music_taste).lower(),
            'authenticity': len(envy_triggers) > 0  # Envy = Gerçek arzu
        }
        
        if all(frequency_vector.values()):
            return "derin_sakin_klasik_ruh"
        elif frequency_vector['depth_seeking']:
            return "arayici_ruh"
        else:
            return "yuzeyde_kaybolmus"
    
    def _find_anchors(self, user_data: Dict) -> list:
        """
        Kullanıcının gerçekliğini sabitleyen şeyler
        """
        anchors = []
        
        # Neşet Ertaş testi (Kullanıcının örneğinden)
        if 'neset_ertas' in str(user_data.get('music', '')).lower() or 'neset_ertas' in str(user_data.get('private_rituals', '')).lower():
            anchors.append('anadolu_melankolisi')
        
        # Çay/kitap ritüeli
        if any(word in str(user_data.get('rituals', '')).lower() or word in str(user_data.get('private_rituals', '')).lower() 
               for word in ['çay', 'kitap', 'yalniz']):
            anchors.append('yalnizlik_rituelleri')
        
        return anchors
