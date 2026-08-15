import random

class ZeigarnikEngine:
    """
    Tamamlanmamış görevler beyni meşgul eder.
    Açık döngüler (open loops) hedefi düşündürür.
    """
    
    OPEN_LOOP_PHRASES = [
        "Sana bir şey söyleyecektim ama... Belki başka zaman.",
        "Bu konuda daha fazlası var ama şimdi değil.",
        "O hikayenin devamı var... Eğer merak edersen.",
        "Tam olarak anlatamadım... Belki tamamını duymak istersin.",
        "Bir şey eksik... Sen de hissediyor musun?",
        "O anı tam olarak tarif edemiyorum... Ama hatırlıyorum.",
    ]
    
    CLIFFHANGER_TEMPLATES = [
        "Ve sonra olan şey... {emotion}",
        "Ama asıl önemli olan... {insight}",
        "Kimse bilmedi ama... {secret}",
    ]
    
    def inject_open_loop(self, base_message: str, intensity: float = 0.7) -> str:
        """
        Mesaja açık döngü ekle - tamamlanmamışlık hissi.
        """
        if random.random() > intensity:
            return base_message
        
        loop = random.choice(self.OPEN_LOOP_PHRASES)
        return f"{base_message} {loop}"
    
    def create_cliffhanger(self, topic: str, target_emotion: str) -> str:
        """
        Bir sonraki etkileşim için "devamı gelecek" hissi.
        """
        template = random.choice(self.CLIFFHANGER_TEMPLATES)
        
        fillers = {
            '{emotion}': target_emotion,
            '{insight}': 'seninle ilgili fark ettiğim şey',
            '{secret}': 'sadece sana söyleyebileceğim'
        }
        
        result = template
        for key, value in fillers.items():
            result = result.replace(key, value)
        
        return result + " (Ama şimdi değil...)"
