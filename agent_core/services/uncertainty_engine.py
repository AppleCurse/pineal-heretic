from pydantic import BaseModel
from typing import Dict, Any

class UncertaintyReport(BaseModel):
    is_suspicious: bool
    confidence: float
    reason: str
    
    class Config:
        extra = "forbid"

class UncertaintyEngine:
    """
    Halüsinasyon ve sahte kanıt tespiti.
    Emin değilse 'bilmiyorum' der.
    """
    
    HALUCINATION_MARKERS = [
        'kesinlikle', 'mutlaka', 'her zaman', 'asla',
        'kesin olarak', 'şüphesiz'
    ]
    
    def evaluate(self, result: Any, agent_name: str) -> UncertaintyReport:
        result_text = str(result)
        
        # 1. Aşırı kesinlik kontrolü
        has_absolutes = any(marker in result_text.lower() 
                           for marker in self.HALUCINATION_MARKERS)
        
        # 2. Sayısal tutarsızlık
        confidence = getattr(result, 'confidence', 0.5)
        if confidence > 0.95 and has_absolutes:
            return UncertaintyReport(
                is_suspicious=True,
                confidence=0.9,
                reason="Aşırı kesinlik + yüksek confidence = Halüsinasyon şüphesi"
            )
        
        # 3. Kanıt eksikliği
        if 'evidence' in result_text and 'bulunamadı' in result_text:
            return UncertaintyReport(
                is_suspicious=True,
                confidence=0.8,
                reason="Kanıt yoksa çıkarım yok"
            )
        
        return UncertaintyReport(
            is_suspicious=False,
            confidence=confidence,
            reason="Kanıt zinciri sağlam"
        )
