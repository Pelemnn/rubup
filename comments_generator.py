import random

# Шаблони та частини речень для побудови унікальних людських коментарів
OPENINGS = [
    "чисто", "реально", "жесть", "не ожидал вообще,", "на халяву", 
    "просто кайф,", "спс за подгон,", "норм тема,", "лол,", "огонь просто,",
    "наконец-то", "сегодня прям везет,", "ну наконец-то нормальный дроп,",
    "по красоте", "легчайший занос,"
]

ACTIONS = [
    "с фри кейсика выдало {keyword}",
    "забрал скинчик через {keyword}",
    "с промика капнуло {keyword}",
    "окупился моментально {keyword}",
    "спс за обмен и подарок {keyword}",
    "поднял халявный скин с {keyword}",
    "мишку или колечко в {keyword} — что бы выбрали?",
    "а в {keyword} реально отдача лучше",
    "вроде ширп, но приятно, спс {keyword}",
    "залутал подарок {keyword}",
    "изи плюс скин с {keyword}",
    "просто с первого кейса выдало в {keyword}",
    "забрал мишку в {keyword}",
    "лучший обменник и кейсы {keyword}",
    "чисто на шару скин забрал в {keyword}"
]

KEYWORDS = [
    "RubUP",
    "@RubUP",
    "рубап",
    "в рубапе",
    "рубапом"
]

ENDINGS = [
    "🔥", "👍", "😎", "😂", "🚀", "кому еще так сыпало?",
    "го еще!", "рекомендую", "топчик", "кто уже крутил?",
    "кайфуем", "норм окуп", "годнота"
]

def generate_single_comment() -> str:
    opening = random.choice(OPENINGS) if random.random() > 0.4 else ""
    keyword = random.choice(KEYWORDS)
    action_template = random.choice(ACTIONS)
    ending = random.choice(ENDINGS) if random.random() > 0.3 else ""
    
    # Підставляємо правильну форму ключа
    # Якщо дія містить "в {keyword}", а обране слово "в рубапе", замінюємо щоб не було "в в рубапе"
    if "в {keyword}" in action_template and keyword == "в рубапе":
        keyword = "рубапе"
    elif "{keyword}" in action_template and keyword == "@RubUP" and random.random() > 0.5:
        keyword = "RubUP"
        
    core = action_template.format(keyword=keyword)
    
    parts = [p for p in [opening, core, ending] if p]
    comment = " ".join(parts).strip()
    # Робимо першу букву великою з певною ймовірністю (для природності іноді з малої, як у тт)
    if random.random() > 0.5 and comment:
        comment = comment[0].upper() + comment[1:]
    return comment

def generate_comments_pack(count: int = 5) -> list[str]:
    count = max(1, min(count, 30))
    comments = set()
    attempts = 0
    while len(comments) < count and attempts < 200:
        attempts += 1
        comments.add(generate_single_comment())
    return list(comments)
