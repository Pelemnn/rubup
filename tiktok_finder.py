import aiohttp
import asyncio
import random
import os
import database

RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY", "f404f7982cmsh6e29120f556ac53p1708a9jsnc3dc56788cf5")
RAPIDAPI_HOST = os.environ.get("RAPIDAPI_HOST", "tiktok-scraper7.p.rapidapi.com")

ALLOWED_HASHTAGS = [
    "cs2", "кс2", "rubup", "upgrader", "кейсер", "апгрейдер", 
    "тгподарки", "подаркитг", "нфт", "nft", "меллстрой", 
    "меллстройнарезки", "mellstroy", "мелстрой", "dota2", 
    "twitch", "leva2k", "buster", "бустер", "твич", "gensyxa", "генсуха", "нарезка"
]

MIN_TIMESTAMP = 1788220800  # 01.09.2026

async def get_tiktok_videos(count: int = 5, specific_tag: str = None) -> list[dict]:
    """
    Повертає унікальні прямі посилання на відео без повторів.
    Якщо specific_tag вказано, шукає тільки за ним.
    """
    count = max(1, min(count, 15))
    results = []
    
    if specific_tag:
        clean_tag = specific_tag.replace("#", "").strip()
        tags_to_search = [clean_tag]
    else:
        tags_to_search = random.sample(ALLOWED_HASHTAGS, min(len(ALLOWED_HASHTAGS), count * 2))
        
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST,
        "User-Agent": "Mozilla/5.0"
    }
    
    async with aiohttp.ClientSession(headers=headers) as session:
        for tag in tags_to_search:
            if len(results) >= count:
                break
                
            # Запитуємо до 20 результатів, щоб мати запас для фільтрації вже використаних
            url = f"https://{RAPIDAPI_HOST}/feed/search?keywords={tag}&count=15&cursor=0&region=ua"
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        videos = data.get("data", {}).get("videos", []) or []
                        for v in videos:
                            vid_id = str(v.get("video_id") or v.get("id") or "")
                            author = v.get("author", {}).get("unique_id")
                            create_time = v.get("create_time", 0)
                            
                            if not vid_id or not author:
                                continue
                                
                            # 1. Перевіряємо, чи це відео вже було використано раніше
                            if database.is_video_used(vid_id):
                                continue
                                
                            # 2. Перевіряємо дату (після 01.09)
                            if create_time >= MIN_TIMESTAMP or create_time == 0:
                                direct_url = f"https://www.tiktok.com/@{author}/video/{vid_id}"
                                
                                # Записуємо в базу як використане
                                database.mark_video_used(vid_id, direct_url, f"#{tag}")
                                
                                results.append({
                                    "tag": f"#{tag}",
                                    "url": direct_url,
                                    "video_id": vid_id
                                })
                                if len(results) >= count:
                                    break
            except Exception as e:
                print(f"[RapidAPI Error for #{tag}]: {e}")
                
            await asyncio.sleep(0.3)
            
    return results
