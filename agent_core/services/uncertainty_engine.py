from pydantic import BaseModel, ConfigDict
from typing import Dict, Any

class UncertaintyReport(BaseModel):
    is_suspicious: bool
    confidence: float
    reason: str
    
    model_config = ConfigDict(extra="forbid")

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

        confidence = getattr(result, 'confidence', 0.5)

        # 2. Kanıt eksikliği (Gerçekten boş veri gelmişse puanı çökert)
        is_empty = False
        if isinstance(result, BaseModel):
            result_dict = result.dict() if hasattr(result, 'dict') else result.model_dump()
            
            total_fields = len(result_dict)
            if total_fields > 0:
                empty_fields = sum(1 for v in result_dict.values() if not v or (isinstance(v, str) and 'bulunamadı' in v.lower()))
                data_score = 1.0 - (empty_fields / total_fields)
                confidence = min(confidence, data_score)
                
                if empty_fields == total_fields:
                    is_empty = True
                    confidence = 0.1
            
            # If any list is empty in the result, it's missing evidence
            if any(isinstance(v, list) and len(v) == 0 for v in result_dict.values()):
                is_empty = True
                confidence = 0.1
                
        if 'evidence' in result_text and 'bulunamadı' in result_text:
            is_empty = True
            confidence = 0.1
            
        if is_empty:
             return UncertaintyReport(
                is_suspicious=True,
                confidence=confidence,
                reason="Eksik kanıt (Boş liste veya 'bulunamadı'). Router kesilmeli."
             )

        if confidence > 0.95 and has_absolutes:
            return UncertaintyReport(
                is_suspicious=True,
                confidence=0.9,
                reason="Aşırı kesinlik + yüksek confidence = Halüsinasyon şüphesi"
            )

        return UncertaintyReport(
            is_suspicious=False,
            confidence=confidence,
            reason="Güvenli"
        )
