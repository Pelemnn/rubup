import aiohttp
import re
import random
import urllib.parse

HASHTAGS = [
    "cs2", "кс2", "rubup", "upgrader", "кейсер", "апгрейдер", 
    "тгподарки", "подаркитг", "нфт", "nft", "меллстрой", 
    "меллстройнарезки", "mellstroy", "мелстрой", "dota2", 
    "twitch", "leva2k", "buster", "бустер", "твич", "gensyxa", "генсуха"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7",
}

async def fetch_videos_by_tag(tag: str, limit: int = 5) -> list[str]:
    """Шукає відео за тегом на TikTok"""
    encoded_tag = urllib.parse.quote(tag)
    url = f"https://www.tiktok.com/tag/{encoded_tag}"
    found_urls = set()

    try:
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=7)) as response:
                if response.status == 200:
                    html = await response.text()
                    # Шукаємо шаблони посилань на відео в TikTok
                    # наприклад: https://www.tiktok.com/@username/video/1234567890123456789
                    matches = re.findall(r'https://www\.tiktok\.com/@[a-zA-Z0-9_\.]+/video/\d+', html)
                    for m in matches:
                        found_urls.add(m)
                        if len(found_urls) >= limit:
                            break
    except Exception as e:
        print(f"[TikTok Search Error for #{tag}] {e}")

    return list(found_urls)

async def get_tiktok_videos(count: int = 5) -> list[dict]:
    """
    Повертає список відео з тегами.
    Якщо прямий парсинг обмежено сервером TikTok, повертає швидкі посилання на свіжі стрічки за хештегами.
    """
    count = max(1, min(count, 15))
    results = []
    
    # Вибираємо випадкові теги
    chosen_tags = random.sample(HASHTAGS, min(count * 2, len(HASHTAGS)))
    
    for tag in chosen_tags:
        if len(results) >= count:
            break
        vids = await fetch_videos_by_tag(tag, limit=2)
        for v in vids:
            results.append({
                "type": "direct",
                "tag": f"#{tag}",
                "url": v
            })
            if len(results) >= count:
                break

    # Якщо прямого доступу немає (IP датацентру Render заблоковано Cloudflare/TikTok),
    # формуємо зручні швидкі клікабельні посилання на стрічку свіжих відео з цими хештегами
    while len(results) < count:
        tag = random.choice(chosen_tags)
        results.append({
            "type": "tag_feed",
            "tag": f"#{tag}",
            "url": f"https://www.tiktok.com/tag/{urllib.parse.quote(tag)}"
        })
        chosen_tags.remove(tag) if tag in chosen_tags else None

    return results
