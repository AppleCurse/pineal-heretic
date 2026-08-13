import os
import json
import re
import os
import json
import re
from openai import AsyncOpenAI
from pydantic import BaseModel
from typing import Type, TypeVar, Any

T = TypeVar('T', bound=BaseModel)

class LLMGateway:
    TIER_1_MODEL = "anthropic/claude-3.5-sonnet" # Yüksek IQ (Karanlık Triad, Karşı-hamle)
    TIER_2_MODEL = "meta-llama/llama-3-8b-instruct" # Hızlı/Ucuz (Basit veri işleme)

    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.client = None
        self.failure_count = 0
        self.circuit_open = False
        self._rebuild()

    def set_key(self, key: str):
        self.api_key = key
        self.failure_count = 0
        self.circuit_open = False
        self._rebuild()

    def _rebuild(self):
        if self.api_key:
            self.client = AsyncOpenAI(base_url="https://openrouter.ai/api/v1", api_key=self.api_key)

    async def query(self, prompt: str, temperature: float = 0.7, tier: int = 1, model: str = None) -> str:
        if self.circuit_open:
            raise RuntimeError("Circuit breaker ACIK - LLM servisi durduruldu")
        if not self.client:
            raise RuntimeError("LLM anahtari yok. Vault veya .env ile OPENROUTER_API_KEY enjekte et.")
            
        selected_model = model or (self.TIER_1_MODEL if tier == 1 else self.TIER_2_MODEL)
        
        try:
            r = await self.client.chat.completions.create(
                model=selected_model, temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            self.failure_count = 0
            return r.choices[0].message.content
        except Exception as e:
            self.failure_count += 1
            if self.failure_count > 5:
                self.circuit_open = True
            raise

    def extract_json(self, text: str) -> dict:
        """Markdown fence ve etiketleri temizleyip JSON ayıklar."""
        text = text.strip()
        # Remove ```json and ```
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        
        # Sadece { ... } arasını al
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            text = text[start:end+1]
            
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON Ayrıştırma Hatası: {str(e)} | Orijinal metin: {text[:100]}...")

    async def query_json(self, prompt: str, schema: Type[T], temperature: float = 0.7, tier: int = 1, model: str = None) -> T:
        """LLM'den sorgu atar, beklenen JSON formatını (Pydantic schema) tamir mekanizmasıyla garanti eder."""
        full_prompt = (
            f"{prompt}\n\n"
            f"Lütfen çıktını SADECE aşağıdaki JSON formatında ver. Markdown etiketi kullanma, hiçbir ek açıklama yapma:\n"
            f"{json.dumps(schema.model_json_schema())}"
        )
        
        selected_model = model or (self.TIER_1_MODEL if tier == 1 else self.TIER_2_MODEL)
        
        try:
            response_text = await self.query(full_prompt, temperature, tier=tier, model=selected_model)
            parsed_data = self.extract_json(response_text)
            return schema(**parsed_data)
        except ValueError:
            # 1 Kez Repair (Tamir) İsteği
            repair_prompt = (
                f"Önceki çıktın geçerli bir JSON değildi veya format uymuyordu. "
                f"Lütfen SADECE şu yapıya uygun geçerli bir JSON döndür:\n{json.dumps(schema.model_json_schema())}\n"
                f"Eklediğin bozuk çıktı şuydu:\n{response_text[:200]}"
            )
            repair_text = await self.query(repair_prompt, temperature, tier=tier, model=selected_model)
            parsed_data = self.extract_json(repair_text)
            return schema(**parsed_data)
