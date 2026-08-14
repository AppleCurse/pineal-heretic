import asyncio
from playwright.async_api import async_playwright
from agent_core.scraper.instagram_ghost import InstagramGhostScraper

async def test_scrape():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context()
        page = await ctx.new_page()
        
        scraper = InstagramGhostScraper()
        try:
            profile = await scraper.scrape_async("cemiyettesimyaci", page)
            print("SUCCESS:")
            print(profile.model_dump_json(indent=2))
        except Exception as e:
            print("ERROR:")
            print(type(e).__name__)
            print(e)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_scrape())
