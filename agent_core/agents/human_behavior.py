"""Deterministic evidence collection for the human-behaviour analysis agent.

The LLM is only given observations produced here; it is not used to invent
visual or temporal evidence.  The module deliberately describes signals as
observations rather than diagnoses.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import cv2
import httpx
import numpy as np
from pydantic import BaseModel, ConfigDict, Field


class MicroSignal(BaseModel):
    signal_type: str
    confidence: float = Field(ge=0.0, le=1.0)
    location: str
    evidence: str
    # Existing integrations use both normalized weights and legacy 0-100 weights.
    psychological_weight: float


class DigitalColdReading(BaseModel):
    surface_identity: str
    detected_wound: str
    defense_mechanism: str
    micro_signals: List[MicroSignal]
    achilles_score: float = Field(ge=0.0, le=100.0)
    resonance_potential: float = Field(ge=0.0, le=1.0)

    model_config = ConfigDict(extra="forbid")


class HumanBehaviorAnalyzer:
    """Collect text, timing, and image observations for the analysis prompt."""

    MAX_IMAGES = 3
    MAX_IMAGE_BYTES = 10 * 1024 * 1024

    async def execute(
        self, input_data: Dict[str, Any], memory: Any, llm_gateway: Any
    ) -> DigitalColdReading:
        profile = input_data.get("target_profile") or {}
        sacred_rules = input_data.get("sacred_rules", "")
        bio = self._as_text(profile.get("bio", ""))
        posts = [self._as_text(post) for post in (profile.get("posts") or [])]
        post_times = profile.get("post_times") or []
        images = profile.get("images") or []

        temporal_signals = self._temporal_forensics(post_times)
        text_data = self._linguistic_forensics(bio, posts)
        text_signals = text_data["signals"]
        visual_signals: List[MicroSignal] = []

        # Download only explicitly HTTP(S) URLs and cap both count and size.
        # A timeout prevents a slow or unavailable image from blocking analysis.
        try:
            async with httpx.AsyncClient(
                follow_redirects=True,
                timeout=httpx.Timeout(10.0, connect=5.0),
            ) as client:
                for image_url in images[: self.MAX_IMAGES]:
                    if not self._is_http_url(image_url):
                        continue
                    try:
                        response = await client.get(image_url)
                        response.raise_for_status()
                        if len(response.content) > self.MAX_IMAGE_BYTES:
                            logging.warning("Skipping oversized image: %s", image_url)
                            continue
                        image = cv2.imdecode(
                            np.frombuffer(response.content, dtype=np.uint8),
                            cv2.IMREAD_COLOR,
                        )
                        if image is not None:
                            visual_signals.extend(self._analyze_visual_micro_img(image))
                    except (httpx.HTTPError, ValueError) as exc:
                        logging.warning("Visual analysis failed for %s: %s", image_url, exc)
        except httpx.HTTPError as exc:
            logging.warning("Unable to initialize visual analysis client: %s", exc)

        all_signals = temporal_signals + text_signals + visual_signals
        contradictions = self._mine_contradictions(visual_signals, text_data)
        hard_data = {
            "signals": [signal.model_dump() for signal in all_signals],
            "contradictions": contradictions,
        }
        prompt = (
            "Sen 'Human Behavior Analyzer' ajanısın. Yalnızca verilen gözlemlere "
            "dayan; gözlemleri klinik tanı veya kesin kişilik yargısı gibi sunma.\n"
            f"Hedef Profili:\nBio: {bio}\nTweetler: {posts}\n\n"
            "GERÇEK METRİKLER (OpenCV ve Linguistic Analiz Sonuçları):\n"
            f"{json.dumps(hard_data, ensure_ascii=False, indent=2)}\n\n"
            f"{sacred_rules}\n"
            "Bu kanıtları temkinli biçimde özetle ve beklenen JSON formatında cevap ver."
        )
        return await llm_gateway.query_json(prompt, DigitalColdReading)

    @staticmethod
    def _as_text(value: Any) -> str:
        return value if isinstance(value, str) else str(value)

    @staticmethod
    def _is_http_url(value: Any) -> bool:
        if not isinstance(value, str):
            return False
        parsed = urlparse(value)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)

    def _analyze_visual_micro(self, images: List[str]) -> List[MicroSignal]:
        """Analyze local image paths (kept for callers and offline tests)."""
        signals: List[MicroSignal] = []
        for image_path in images or []:
            image = cv2.imread(image_path)
            if image is not None:
                signals.extend(self._analyze_visual_micro_img(image))
        return signals

    def _analyze_visual_micro_img(self, img: np.ndarray) -> List[MicroSignal]:
        signals: List[MicroSignal] = []
        if img is None or img.size == 0 or len(img.shape) < 2:
            return signals
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        height, width = img.shape[:2]
        shoulder_roi = img[int(height * 0.3):int(height * 0.6), int(width * 0.2):int(width * 0.8)]
        if shoulder_roi.size:
            tension_level = float(np.mean(cv2.Canny(shoulder_roi, 100, 200)))
            if tension_level > 50:
                signals.append(MicroSignal(
                    signal_type="tension", confidence=min(tension_level / 100, 1.0),
                    location="shoulder_region",
                    evidence=f"Omuz bölgesi kenar yoğunluğu: {tension_level:.2f}",
                    psychological_weight=0.7,
                ))
        laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        if laplacian_var < 100:
            signals.append(MicroSignal(
                signal_type="void", confidence=0.8, location="background_blur",
                evidence=f"Görüntü netliği düşük (Laplacian varyansı: {laplacian_var:.1f})",
                psychological_weight=0.6,
            ))
        return signals

    def _linguistic_forensics(self, bio: str, posts: List[str]) -> Dict[str, Any]:
        full_text = f"{bio} {' '.join(posts)}"
        signals: List[MicroSignal] = []
        emoji_count = sum(1 for char in full_text if ord(char) > 127000)
        if full_text and emoji_count > len(full_text) * 0.05:
            signals.append(MicroSignal(signal_type="authentic", confidence=0.75,
                location="emoji_density", evidence=f"Yüksek emoji kullanımı: {emoji_count}", psychological_weight=0.5))
        passive_count = sum(full_text.lower().count(marker) for marker in ("oldu", "edildi", "yapıldı", "gerekiyor"))
        if passive_count > 3:
            signals.append(MicroSignal(signal_type="contradiction", confidence=0.8,
                location="passive_voice", evidence=f"Pasif kipi kullanım: {passive_count}", psychological_weight=0.85))
        if "sadece" in full_text.lower():
            signals.append(MicroSignal(signal_type="defense", confidence=0.9,
                location="linguistic", evidence="'Sadece' kelimesi tespiti - sınır çizme/savunma", psychological_weight=0.8))
        return {"signals": signals, "claimed_identity": self._extract_claimed_identity(bio)}

    def _temporal_forensics(self, post_times: List[str]) -> List[MicroSignal]:
        late_night_count = total_valid = 0
        for value in post_times or []:
            try:
                hour = int(str(value).strip().split(":", 1)[0])
                if 0 <= hour <= 23:
                    total_valid += 1
                    late_night_count += hour >= 23 or hour <= 4
            except (TypeError, ValueError):
                continue
        ratio = late_night_count / total_valid if total_valid else 0
        if ratio > 0.3:
            return [MicroSignal(signal_type="insomnia_isolation", confidence=min(ratio, 1.0),
                location="temporal_post_distribution", evidence=f"Gece (23:00-04:00) paylaşım oranı: %{ratio * 100:.1f}", psychological_weight=0.75)]
        return []

    def _mine_contradictions(self, visual_signals: List[MicroSignal], text_signals: Dict[str, Any]) -> List[Dict[str, Any]]:
        contradictions: List[Dict[str, Any]] = []
        signals = text_signals.get("signals", [])
        if any(s.signal_type in ("tension", "void") for s in visual_signals) and any(s.signal_type in ("authentic", "defense") for s in signals):
            contradictions.append({"type": "visual_linguistic_mismatch", "evidence": "Görsel sinyaller ile metinsel sunum arasında fark gözlendi", "severity": 0.85})
        contradictions.extend({"type": "linguistic_contradiction", "evidence": s.evidence, "severity": s.psychological_weight} for s in signals if s.signal_type == "contradiction")
        return contradictions

    def _extract_claimed_identity(self, bio: str) -> str:
        return "Unknown Identity"

    def _calculate_achilles(self, contradictions: List, text_signals: Dict) -> float:
        score = len(contradictions) * 15 + sum(s.psychological_weight * 10 for s in text_signals.get("signals", []))
        return min(score, 100)

    def _identify_wound_as_bridge(self, contradictions: List, text_signals: Dict) -> Dict[str, Any]:
        if not contradictions:
            return {"type": "unknown", "defense": "unknown"}
        primary = max(contradictions, key=lambda item: item.get("weight", item.get("severity", 0)))
        wound_types = {
            "social_vs_alone": {"type": "yalnizlik_köprüsü", "defense": "kalabalik_maskesi", "approach": "bosluk_rezonansi"},
            "independent_vs_needy": {"type": "bagimsizlik_celiskisi", "defense": "kontrol_mekanizmasi", "approach": "guven_insaati"},
            "happy_vs_tired": {"type": "tukenmislik_yarasi", "defense": "pozitif_maske", "approach": "izin_verme_alani"},
        }
        return wound_types.get(primary.get("type"), {"type": "generic", "defense": "generic"})

    def _calculate_resonance_potential(self, wound: Dict, input_data: Dict) -> float:
        authenticity = min(max(float(input_data.get("user_authenticity_score", 0.5)), 0.0), 1.0)
        openness = 1 - min(max(float(wound.get("defense_strength", 0.5)), 0.0), 1.0)
        return float((authenticity * openness) ** 0.5)
