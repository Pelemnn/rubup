import aiohttp
import json
import random
import urllib.parse
import re

HASHTAGS = [
    "cs2", "кс2", "rubup", "upgrader", "кейсер", "апгрейдер", 
    "тгподарки", "подаркитг", "нфт", "nft", "меллстрой", 
    "меллстройнарезки", "mellstroy", "мелстрой", "dota2", 
    "twitch", "leva2k", "buster", "бустер", "твич", "gensyxa", "генсуха"
]

# Заголовки як у мобільного додатку / актуального браузера
HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Mobile/15E148 Safari/604.1",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Dest": "document",
}

async def fetch_direct_video_urls(tag: str, limit: int = 5) -> list[str]:
    """Витягує тільки прямі посилання на відео виду tiktok.com/@user/video/ID"""
    direct_urls = []
    encoded_tag = urllib.parse.quote(tag)
    
    # Спосіб 1: Парсинг вбудованого JSON SIGI_STATE або UNIVERSAL_DATA з TikTok сторінки тегу
    url = f"https://www.tiktok.com/tag/{encoded_tag}"
    try:
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as response:
                if response.status == 200:
                    text = await response.text()
                    
                    # 1. Пошук прямих посилань у тегах <a href="...">
                    found = re.findall(r'href=[\'"](https://www\.tiktok\.com/@[^/]+/video/\d+)[\'"]', text)
                    for f in found:
                        if f not in direct_urls:
                            direct_urls.append(f)
                            
                    # 2. Якщо в href не знайшло, шукаємо в JSON структурі сторінки
                    if len(direct_urls) < limit:
                        # Шукаємо id відео та автора в JSON
                        id_matches = re.findall(r'"id":"(\d{18,20})"', text)
                        author_matches = re.findall(r'"uniqueId":"([a-zA-Z0-9_\.]+)"', text)
                        
                        if id_matches and author_matches:
                            author = author_matches[0]
                            for vid_id in id_matches[:limit]:
                                full_url = f"https://www.tiktok.com/@{author}/video/{vid_id}"
                                if full_url not in direct_urls:
                                    direct_urls.append(full_url)
    except Exception as e:
        print(f"[TikTok direct fetch error for #{tag}]: {e}")

    # Спосіб 2: Якщо TikTok заблокував веб-сторінку, беремо через відкритий RSS/Search Bridge
    if not direct_urls:
        try:
            # Запасний відкритий API пошуку відео за тегом
            search_api = f"https://www.tiktok.com/api/challenge/item_list/?challengeID={encoded_tag}&count=10&cursor=0"
            async with aiohttp.ClientSession(headers=HEADERS) as session:
                async with session.get(search_api, timeout=aiohttp.ClientTimeout(total=6)) as res:
                    if res.status == 200:
                        data = await res.json()
                        items = data.get("itemList", [])
                        for it in items:
                            v_id = it.get("id")
                            author = it.get("author", {}).get("uniqueId")
                            if v_id and author:
                                direct_urls.append(f"https://www.tiktok.com/@{author}/video/{v_id}")
        except Exception:
            pass

    return direct_urls[:limit]

async def get_tiktok_videos(count: int = 5) -> list[dict]:
    """Повертає виключно прямі посилання на відео"""
    count = max(1, min(count, 10))
    results = []
    
    # Вибираємо випадкові теги для різноманітності
    sample_tags = random.sample(HASHTAGS, min(len(HASHTAGS), 8))
    
    for tag in sample_tags:
        if len(results) >= count:
            break
        vids = await fetch_direct_video_urls(tag, limit=2)
        for v in vids:
            results.append({
                "tag": f"#{tag}",
                "url": v
            })
            if len(results) >= count:
                break
                
    return results
