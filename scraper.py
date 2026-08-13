import json
import time
from playwright.sync_api import sync_playwright

def scrape_readonly(profile_url: str, cookies: str = None) -> dict:
    """
    Network Interception (GraphQL) tabanlı Anti-Kırılgan Scraper.
    DOM Selector yerine X'in kendi API trafiğini dinler.
    """
    scraped_data = {
        "username": "@" + profile_url.split("?")[0].rstrip("/").split("/")[-1],
        "bio": "",
        "posts": [],
        "post_times": [],
        "images": []
    }

    def intercept_response(response):
        try:
            if "graphql" not in response.url:
                return
            
            # CORS Preflight vb. geç
            if response.request.method == "OPTIONS":
                return
                
            # JSON yanıtını al
            resp_json = response.json()
            
            # 1. Biyografi Yakalama (UserByScreenName)
            if "UserByScreenName" in response.url:
                legacy = resp_json.get("data", {}).get("user", {}).get("result", {}).get("legacy", {})
                bio = legacy.get("description", "")
                if bio:
                    scraped_data["bio"] = bio

            # 2. Tweetleri Yakalama (UserTweets)
            elif "UserTweets" in response.url:
                instructions = resp_json.get("data", {}).get("user", {}).get("result", {}).get("timeline_v2", {}).get("timeline", {}).get("instructions", [])
                for instr in instructions:
                    if instr.get("type") == "TimelineAddEntries":
                        entries = instr.get("entries", [])
                        for entry in entries:
                            # Sadece Tweetleri al (Promoted vs geç)
                            if "tweet" in entry.get("entryId", ""):
                                legacy = entry.get("content", {}).get("itemContent", {}).get("tweet_results", {}).get("result", {}).get("legacy", {})
                                if not legacy:
                                    continue
                                
                                # Metin
                                text = legacy.get("full_text", "")
                                if text:
                                    scraped_data["posts"].append(text.replace("\n", " "))
                                
                                # Zaman
                                created_at = legacy.get("created_at", "")
                                if created_at:
                                    scraped_data["post_times"].append(created_at)
                                
                                # Medya (Görsel)
                                media = legacy.get("entities", {}).get("media", [])
                                for m in media:
                                    if m.get("type") == "photo":
                                        scraped_data["images"].append(m.get("media_url_https", ""))

        except Exception as e:
            # Sessizce yut, ağ trafiği gürültülü olabilir
            pass

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        ctx = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Cookie Enjeksiyonu
        if cookies:
            parsed = []
            for part in cookies.split(";"):
                if "=" in part:
                    k, v = part.split("=", 1)
                    parsed.append({"name": k.strip(), "value": v.strip(), "domain": ".x.com", "path": "/"})
            if parsed:
                try:
                    ctx.add_cookies(parsed)
                except Exception:
                    pass
                    
        page = ctx.new_page()
        
        # Ağ Dinleyicisini Tak
        page.on("response", intercept_response)
        
        # Hedefe Git
        page.goto(profile_url, wait_until="networkidle", timeout=20000)
        
        # Ekstra 3 saniye bekle ki GraphQL asenkron yanıtları düşsün
        page.wait_for_timeout(3000)
        
        browser.close()
        
        # Fallback (Eğer GraphQL değişmişse veya veri gelmemişse)
        if not scraped_data["bio"]:
            scraped_data["bio"] = "Kamusal biyografi taranamadi veya gizli."
        if not scraped_data["posts"]:
            scraped_data["posts"] = ["Acik paylasim metni bulunamadi."]
            
        # Sadece ilk 5 tweet ve resmi tut
        scraped_data["posts"] = scraped_data["posts"][:5]
        scraped_data["post_times"] = scraped_data["post_times"][:5]
        scraped_data["images"] = scraped_data["images"][:3]
        
        return scraped_data
