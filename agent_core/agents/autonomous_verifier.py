from pydantic import BaseModel, ConfigDict
from typing import Dict, Any, List
import asyncio

class Claim(BaseModel):
    claim_text: str
    category: str # Örn: "Meslek", "Lokasyon", "Yetenek"

class VerificationResult(BaseModel):
    claim_text: str
    truth_status: str # "DOĞRULANDI", "ÇELİŞKİLİ", "YALAN", "BİLİNMİYOR"
    evidence_url: str
    contradiction_detail: str
    
class VerifierReport(BaseModel):
    verifications: List[VerificationResult]
    overall_authenticity_score: float # 0.0 (Tamamen Yalan) - 1.0 (Tamamen Gerçek)
    
    model_config = ConfigDict(extra="forbid")

class AutonomousVerifier:
    """
    Hedefin (özellikle X) beyan ettiği bilgileri web'de (Tavily aracılığıyla)
    otonom olarak aratıp teyit eden (veya yalanlarını patlatan) ajan.
    """
    def __init__(self, search_engine):
        self.search_engine = search_engine

    async def execute(self, input_data: Dict, memory, llm_gateway) -> VerifierReport:
        target_profile = input_data.get('target_profile', {})
        bio = target_profile.get('bio', '')
        
        if not bio or not self.search_engine.tavily_key:
            # Biyografi boşsa veya arama anahtarı yoksa geç
            return VerifierReport(verifications=[], overall_authenticity_score=1.0)
            
        # Adım 1: Biyografideki iddiaları (claims) çıkar
        claim_prompt = (
            f"Hedefin biyografisi şu: '{bio}'\n"
            f"Burada hedefin iddia ettiği nesnel, teyit edilebilir bilgileri (Örn: CEO, şirket adı, yaşadığı şehir, okul vb.) çıkar.\n"
            f"Eğer teyit edilebilecek bir iddia yoksa boş liste dön.\n"
        )
        
        class ClaimList(BaseModel):
            claims: List[Claim]
            
        claim_data = await llm_gateway.query_json(claim_prompt, ClaimList, tier=2)
        
        if not claim_data.claims:
            return VerifierReport(verifications=[], overall_authenticity_score=1.0)
            
        verifications = []
        
        # Adım 2: Her bir iddiayı arat
        for claim in claim_data.claims:
            query = f"{claim.claim_text}"
            # Hedefin adı varsa ekle
            name = target_profile.get("name", "")
            if name: query = f"{name} {query}"
                
            results = await self.search_engine.search(query, num_results=2)
            
            if not results:
                verifications.append(VerificationResult(
                    claim_text=claim.claim_text,
                    truth_status="BİLİNMİYOR",
                    evidence_url="",
                    contradiction_detail="İnternette bu iddiayı doğrulayan / yalanlayan iz bulunamadı."
                ))
                continue
                
            # Adım 3: LLM'e arama sonuçlarını verip teyit etmesini iste
            search_context = "\n".join([f"- Kaynak ({r.source_url}): {r.content}" for r in results])
            
            verify_prompt = (
                f"Hedefin İddiası: '{claim.claim_text}'\n\n"
                f"İnternet Arama Sonuçları:\n{search_context}\n\n"
                f"Görevin: İnternet sonuçlarına bakarak bu iddianın doğru mu, abartılı mı, yoksa tamamen yalan mı olduğunu bulmak.\n"
                f"Statü olarak SADECE şu kelimeleri kullanabilirsin: 'DOĞRULANDI', 'ÇELİŞKİLİ', 'YALAN', 'BİLİNMİYOR'.\n"
            )
            
            # Yeniden kullanılabilir Schema (tekil)
            single_verification = await llm_gateway.query_json(verify_prompt, VerificationResult, tier=2)
            verifications.append(single_verification)
            
        # Skor hesapla
        total = len(verifications)
        score = 1.0
        if total > 0:
            lies = sum(1 for v in verifications if v.truth_status in ["YALAN", "ÇELİŞKİLİ"])
            score = max(0.0, 1.0 - (lies / total))
            
        return VerifierReport(
            verifications=verifications,
            overall_authenticity_score=score
        )
