import random
import urllib.parse

HASHTAGS = [
    "cs2", "кс2", "rubup", "upgrader", "кейсер", "апгрейдер", 
    "тгподарки", "подаркитг", "нфт", "nft", "меллстрой", 
    "меллстройнарезки", "mellstroy", "мелстрой", "dota2", 
    "twitch", "leva2k", "buster", "бустер", "твич", "gensyxa", "генсуха"
]

async def get_tiktok_videos(count: int = 5) -> list[dict]:
    """
    Генерує прямі посилання на свіжі стрічки відео в TikTok за цільовими тегами.
    При відкритті на телефоні або ПК одразу відкривається відеоплеєр зі свіжими відео за цим тегом.
    """
    count = max(1, min(count, 10))
    chosen_tags = random.sample(HASHTAGS, count)
    
    results = []
    for tag in chosen_tags:
        encoded = urllib.parse.quote(f"#{tag}")
        # search/video відкриває саме відеоплеєр зі свіжими відео
        video_search_url = f"https://www.tiktok.com/search/video?q={encoded}"
        results.append({
            "tag": f"#{tag}",
            "url": video_search_url
        })
        
    return results
