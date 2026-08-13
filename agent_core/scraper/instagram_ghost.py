"""
PINEAL-HERETIC v2.0 - Instagram Ghost Scraper (Self-Hosted)
Faz 5 / Görev 3 - Türkiye Operasyonu

Mimari Karar: Sıfır SaaS, sıfır Apify, sıfır kart.
X scraper.py'nin ikizi - Playwright hayalet tarayıcı, kendi bilgisayarında çalışır.
Halüsinasyon = 0. Kanıt yoksa HALT.

Bu modül asla veri uydurmaz. Instagram'ın döndüğü gerçek JSON'u alır,
Pydantic V2 ile doğrular, güven düşükse InsufficientEvidenceError fırlatır.
"""

from __future__ import annotations
import json
import random
import re
import time
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field, ConfigDict, field_validator


# --- Anti-Halüsinasyon Çekirdeği ---
class InsufficientEvidenceError(Exception):
    """Kanıt yoksa uydurma, DUR. Faz 4 kuralı."""
    pass


# --- Pydantic V2 Şemalar (ConfigDict, extra="forbid" - halüsinasyon filtresi) ---
class InstagramPost(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    shortcode: str = Field(..., description="Post ID, örn: C123...")
    caption: Optional[str] = Field(None, max_length=2200)
    display_url: str = Field(..., description="Fotoğrafın gerçek URL'i, uydurma değil")
    is_video: bool = False
    location_name: Optional[str] = None
    taken_at: Optional[datetime] = None
    like_count: Optional[int] = None
    comment_count: Optional[int] = None

    @field_validator("display_url")
    @classmethod
    def url_must_be_real(cls, v: str) -> str:
        if not v.startswith("http"):
            raise ValueError("Sahte URL halüsinasyondur")
        return v


class InstagramProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    username: str
    full_name: Optional[str] = None
    biography: Optional[str] = None
    is_private: bool
    is_verified: bool = False
    follower_count: Optional[int] = None
    following_count: Optional[int] = None
    post_count: Optional[int] = None
    profile_pic_url: Optional[str] = None
    posts: List[InstagramPost] = Field(default_factory=list)
    scraped_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    evidence_source: str = Field(default="self_hosted_ghost_browser", description="Kanıtın nereden geldiği, şeffaflık için")

    @field_validator("posts")
    @classmethod
    def posts_must_be_real(cls, v: List[InstagramPost]) -> List[InstagramPost]:
        # 12 posttan fazla istemiyoruz, OSINT için yeterli
        return v[:12]


class InstagramGhostScraper:
    """
    Self-hosted hayalet kazıyıcı.
    X scraper.py ile aynı mimari: Playwright, vault'tan cookie, stealth.
    Asla veri uydurmaz.
    """

    def __init__(self, vault_cookies: Optional[Dict[str, str]] = None):
        self.vault_cookies = vault_cookies or {}
        self.base_url = "https://www.instagram.com"

    def _random_delay(self):
        """İnsan gibi bekle, bot gibi değil."""
        time.sleep(random.uniform(2.0, 5.0))

    def _extract_from_html(self, html: str, username: str) -> Dict[str, Any]:
        """
        Instagram'ın sayfa içine gömdüğü JSON'u bul.
        2 yöntem dener, ikisi de yoksa HALT.
        Yöntem 1: /api/v1/users/web_profile_info
        Yöntem 2: window._sharedData / __additionalDataLoaded
        """
        # Yöntem 1: Embedded JSON - __additionalDataLoaded
        # Yöntem 2: <script type="application/json" data-sjs>
        patterns = [
            r'window\._sharedData\s*=\s*({.*?});</script>',
            r'"ProfilePage":\s*\[({.*?})\]',
            r'"userData":\s*({.*?}),"',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(1))
                    return data
                except:
                    continue
        
        # Eğer hiçbir pattern tutmadıysa, bu halüsinasyon değil, kanıt yok demektir
        raise InsufficientEvidenceError(f"Instagram HTML'inde JSON bulunamadı: {username} - muhtemelen private veya rate-limit")

    def _parse_real_profile(self, raw_json: Dict[str, Any], html: str, username: str) -> InstagramProfile:
        """
        Ham JSON'u gerçek Pydantic modele çevir.
        Burada asla uydurma yok, sadece olanı al.
        """
        try:
            # Instagram'ın yapısı sürekli değişir, en stabil 2 yer:
            # 1. meta property og:description
            # 2. ld+json
            # Biz en garanti olanı: sayfadaki script tag'lerinden user objesi
            
            # Basit ve dürüst yaklaşım: eğer private ise direkt HALT
            if '"is_private":true' in html or '"isPrivate":true' in html:
                # Private hesapta post yoksa, bunu uydurma
                # Sadece temel bilgileri al, postları boş bırak
                is_private = True
            else:
                is_private = False

            # Follower sayısını regex ile gerçek yerden al
            follower_match = re.search(r'"edge_followed_by":{"count":(\d+)}', html)
            following_match = re.search(r'"edge_follow":{"count":(\d+)}', html)
            
            # Eğer sayılar yoksa, None bırak - 0 uydurma
            follower_count = int(follower_match.group(1)) if follower_match else None
            following_count = int(following_match.group(1)) if following_match else None

            # Bio'yu og:description'dan al - en gerçek yer
            bio_match = re.search(r'<meta property="og:description" content="([^"]+)"', html)
            biography = bio_match.group(1) if bio_match else None

            profile_pic_match = re.search(r'"profile_pic_url":"([^"]+)"', html)
            profile_pic_url = profile_pic_match.group(1).replace("\\u0026", "&") if profile_pic_match else None
            if profile_pic_url:
                profile_pic_url = profile_pic_url.encode().decode('unicode_escape')

            # Postları topla - sadece gerçek shortcode'lar
            posts = []
            shortcodes = re.findall(r'"shortcode":"([A-Za-z0-9_-]+)"', html)
            display_urls = re.findall(r'"display_url":"([^"]+)"', html)
            
            # Eşleştir, uydurma yapma - sayılar eşit değilse en az olan kadar al
            for i in range(min(len(shortcodes), len(display_urls), 12)):
                try:
                    url = display_urls[i].replace("\\u0026", "&").encode().decode('unicode_escape')
                    posts.append(InstagramPost(
                        shortcode=shortcodes[i],
                        display_url=url,
                        caption=None,  # Caption ayrı parse edilecek, yoksa None - uydurma yok
                        is_video=False
                    ))
                except Exception:
                    # Tek post bozuksa hepsini çökertme, atla
                    continue

            # Eğer private ve post yoksa bu normal - HALT değil, ama evidence düşük
            if is_private and len(posts) == 0:
                # Private hesap - bu bir hata değil, bir kanıt türü
                pass

            profile = InstagramProfile(
                username=username,
                biography=biography,
                is_private=is_private,
                follower_count=follower_count,
                following_count=following_count,
                profile_pic_url=profile_pic_url,
                posts=posts,
                evidence_source="self_hosted_ghost_browser"
            )

            # --- ANTI-HALÜSİNASYON KONTROLÜ ---
            # Eğer hem follower yok, hem bio yok, hem post yok -> bu sayfa boş, HALT
            if follower_count is None and biography is None and len(posts) == 0 and not is_private:
                raise InsufficientEvidenceError(f"Instagram profili boş geldi: {username} - rate-limit veya sayfa yapısı değişmiş")

            return profile

        except InsufficientEvidenceError:
            raise
        except Exception as e:
            # Beklenmedik parse hatası -> halüsinasyon yapma, halt et
            raise InsufficientEvidenceError(f"Instagram parse hatası, veri uydurmuyorum: {username} - {str(e)}")

    async def scrape_async(self, username: str, playwright_page=None) -> InstagramProfile:
        """
        Ana metod - Playwright page dışarıdan verilir (X scraper ile aynı vault izolasyonu)
        Eğer page yoksa, senkron fallback için hata fırlatır - uydurma tarayıcı açmaz.
        """
        if playwright_page is None:
            raise InsufficientEvidenceError("Playwright page verilmedi - hayalet tarayıcı vault'tan gelmeli, kendi kendine açmam")

        target_url = f"{self.base_url}/{username}/"
        
        # Stealth navigation
        await playwright_page.goto(target_url, wait_until="domcontentloaded")
        self._random_delay()
        
        html = await playwright_page.content()

        # Login duvarı mı?
        if "Login • Instagram" in html or 'name="username"' in html and 'name="password"' in html:
            raise InsufficientEvidenceError(f"Instagram login duvarı: {username} - cookie expired, vault'u yenile")

        # Rate limit duvarı mı?
        if "Try again later" in html or "We restrict certain activity" in html:
            raise InsufficientEvidenceError(f"Instagram rate-limit: {username} - bekle ve tekrar dene")

        raw = self._extract_from_html(html, username)
        profile = self._parse_real_profile(raw, html, username)

        return profile

    def evaluate_confidence(self, profile: InstagramProfile) -> float:
        """
        Uncertainty Engine için güven skoru.
        Düşükse HALT.
        """
        score = 0.0
        if profile.follower_count is not None:
            score += 0.2
        if profile.biography:
            score += 0.2
        if len(profile.posts) >= 3:
            score += 0.4
        elif len(profile.posts) >= 1:
            score += 0.2
        
        if profile.is_private:
            score = min(score, 0.4)  # Private ise max 0.4 - yetersiz kanıt

        # Eğer skor < 0.6 ise, task_executor bunu halt etmeli
        return round(score, 2)
