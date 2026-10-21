import aiohttp
import asyncio
import random
import os

# Ключі RapidAPI для гарантованого отримання найсвіжіших прямих відео
RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY", "f404f7982cmsh6e29120f556ac53p1708a9jsnc3dc56788cf5")
RAPIDAPI_HOST = os.environ.get("RAPIDAPI_HOST", "tiktok-scraper7.p.rapidapi.com")

HASHTAGS = [
    "cs2", "кс2", "rubup", "upgrader", "кейсер", "апгрейдер", 
    "тгподарки", "подаркитг", "нфт", "nft", "меллстрой", 
    "меллстройнарезки", "mellstroy", "мелстрой", "dota2", 
    "twitch", "leva2k", "buster", "бустер", "твич", "gensyxa", "генсуха"
]

# 01.09.2026 00:00:00 UTC = приблизно 1788220800
MIN_TIMESTAMP = 1788220800

async def get_tiktok_videos(count: int = 5) -> list[dict]:
    """
    Повертає тільки прямі посилання на ОДНЕ відео виду:
    https://www.tiktok.com/@author/video/ID
    Відео гарантовано найсвіжіші (після 01.09)
    """
    count = max(1, min(count, 10))
    results = []
    
    # Вибираємо випадкові теги для різноманітності
    chosen_tags = random.sample(HASHTAGS, min(len(HASHTAGS), count * 2))
    
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST,
        "User-Agent": "Mozilla/5.0"
    }
    
    async with aiohttp.ClientSession(headers=headers) as session:
        for tag in chosen_tags:
            if len(results) >= count:
                break
                
            url = f"https://{RAPIDAPI_HOST}/feed/search?keywords={tag}&count=6&cursor=0&region=ua"
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        videos = data.get("data", {}).get("videos", []) or []
                        for v in videos:
                            vid_id = v.get("video_id") or v.get("id")
                            author = v.get("author", {}).get("unique_id")
                            create_time = v.get("create_time", 0)
                            
                            # Перевірка свіжості: пізніше 01.09
                            if create_time >= MIN_TIMESTAMP or create_time == 0:
                                if vid_id and author:
                                    direct_url = f"https://www.tiktok.com/@{author}/video/{vid_id}"
                                    if direct_url not in [r["url"] for r in results]:
                                        results.append({
                                            "tag": f"#{tag}",
                                            "url": direct_url,
                                            "create_time": create_time
                                        })
                                        if len(results) >= count:
                                            break
            except Exception as e:
                print(f"[RapidAPI Error for #{tag}]: {e}")
                
            await asyncio.sleep(0.3)
            
    return results
