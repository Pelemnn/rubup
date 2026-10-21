import os
import asyncio
import re
import pytz
from datetime import datetime
from aiohttp import web
from telethon import TelegramClient, events, Button
from telethon.sessions import StringSession
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import database
import comments_generator
import tiktok_finder

# Константи та конфігурація
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
STRING_SESSION = os.environ.get("STRING_SESSION", "")
PORT = int(os.environ.get("PORT", 8080))
TIMEZONE = pytz.timezone(os.environ.get("TZ", "Europe/Kyiv"))

RUBUP_COMMENT_BOT = "@rubupcomment_bot"
collecting_lock = asyncio.Lock()

async def collect_five_images(client: TelegramClient):
    """Збирає 5 картинок з @rubupcomment_bot та пересилає ТІЛЬКИ їх у Saved Messages"""
    if not client or not client.is_connected():
        print("[Collect] Клієнт Telegram не підключений.")
        return

    async with collecting_lock:
        print(f"[{datetime.now()}] Початок збору 5 картинок з {RUBUP_COMMENT_BOT}...")
        try:
            bot_entity = await client.get_input_entity(RUBUP_COMMENT_BOT)
            
            messages = await client.get_messages(bot_entity, limit=5)
            target_msg = None
            
            for msg in messages:
                if msg.buttons:
                    target_msg = msg
                    break
            
            if not target_msg:
                print("[Collect] Відправка /start боту...")
                await client.send_message(bot_entity, "/start")
                await asyncio.sleep(3)
                messages = await client.get_messages(bot_entity, limit=3)
                for msg in messages:
                    if msg.buttons:
                        target_msg = msg
                        break

            if not target_msg or not target_msg.buttons:
                print("[Collect] Не знайдено кнопок у боті.")
                return

            collected_media = []
            
            # 1. Тиснемо кнопку "Сгенерировать картинки"
            clicked = False
            for row in target_msg.buttons:
                for btn in row:
                    if "Сгенерировать картинки" in btn.text or (hasattr(btn, 'data') and btn.data and b"newphoto" in btn.data):
                        await btn.click()
                        clicked = True
                        break
                if clicked:
                    break

            if not clicked:
                try:
                    await target_msg.click(data=b"r:newphoto")
                    clicked = True
                except Exception as e:
                    print(f"[Collect] Клік r:newphoto: {e}")

            await asyncio.sleep(4)

            # Перевіряємо першу картинку
            latest_msgs = await client.get_messages(bot_entity, limit=3)
            for m in latest_msgs:
                if m.media:
                    collected_media.append(m)
                    target_msg = m
                    break

            # 2. Тиснемо кнопку "Ещё картинка" ще 4 рази (всього 5)
            for step in range(4):
                more_clicked = False
                latest_msgs = await client.get_messages(bot_entity, limit=2)
                cur_msg = latest_msgs[0] if latest_msgs else target_msg
                
                if cur_msg and cur_msg.buttons:
                    for row in cur_msg.buttons:
                        for btn in row:
                            if "Ещё картинка" in btn.text or "Еще картинка" in btn.text:
                                await btn.click()
                                more_clicked = True
                                break
                        if more_clicked:
                            break
                            
                if not more_clicked and target_msg and target_msg.buttons:
                    for row in target_msg.buttons:
                        for btn in row:
                            if "Ещё картинка" in btn.text or "Еще картинка" in btn.text:
                                await btn.click()
                                more_clicked = True
                                break
                        if more_clicked:
                            break

                await asyncio.sleep(4)
                
                new_msgs = await client.get_messages(bot_entity, limit=2)
                for m in new_msgs:
                    if m.media and m.id not in [x.id for x in collected_media]:
                        collected_media.append(m)
                        target_msg = m
                        break

            print(f"[Collect] Успішно зібрано картинок: {len(collected_media)}")
            
            # Пересилаємо ТІЛЬКИ картинки у Saved Messages ("me")
            for media_msg in collected_media:
                await client.send_file("me", file=media_msg.media)
                await asyncio.sleep(1)

        except Exception as e:
            print(f"[Collect Error] {e}")


# Веб-сервер для підтримки Render Web Service
async def handle_ping(request):
    return web.Response(text="RubUP Helper is running 24/7! Status: OK")

async def init_web_app():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    app.router.add_get("/health", handle_ping)
    return app


async def send_videos_for_tag(client: TelegramClient, tag: str, count: int = 5):
    """Шукає і надсилає відео з коментарями за обраним тегом"""
    clean_tag = None if tag == "random" else tag
    tag_name = f"#{tag}" if clean_tag else "рандомними"
    
    status_msg = await client.send_message("me", f"🔎 Шукаю {count} нових унікальних відео за тегом {tag_name}...")
    
    vids = await tiktok_finder.get_tiktok_videos(count=count, specific_tag=clean_tag)
    
    if not vids:
        await status_msg.edit("⚠️ Нових свіжих відео за цим тегом не знайдено (можливо, всі вже використані). Спробуйте інший тег!")
        return

    comments = comments_generator.generate_comments_pack(len(vids))
    reply_lines = [f"🎯 **Знайдено {len(vids)} унікальних відео ({tag_name}, без повторів):**\n"]
    for i, (v, c) in enumerate(zip(vids, comments), 1):
        reply_lines.append(f"🎬 **#{i} Відео ({v['tag']}):**")
        reply_lines.append(f"{v['url']}")
        reply_lines.append(f"💬 Скопіювати комент (тапніть):")
        reply_lines.append(f"`{c}`\n")
        
    await status_msg.delete()
    await client.send_message("me", "\n".join(reply_lines), link_preview=False)


async def main():
    database.init_db()

    client = None
    if STRING_SESSION and API_ID and API_HASH:
        print("Ініціалізація клієнта Telethon...")
        client = TelegramClient(
            StringSession(STRING_SESSION),
            API_ID,
            API_HASH,
            device_model="Desktop",
            system_version="Windows 11",
            app_version="4.16.8"
        )

        # Реєстрація обробника повідомлень про нарахування коштів у @rubup
        @client.on(events.NewMessage)
        async def handle_new_message(event):
            try:
                sender = await event.get_sender()
                sender_username = getattr(sender, "username", "") or ""
                sender_title = getattr(sender, "title", "") or ""
                
                is_rubup = "rubup" in sender_username.lower() or "rubup" in sender_title.lower()
                if not is_rubup:
                    return

                text = event.raw_text or ""
                if "зачислено" in text.lower() and "комментар" in text.lower():
                    money_match = re.search(r"зачислено\s+([\d\.,]+)\s*₽", text, re.IGNORECASE)
                    comments_match = re.search(r"Засчитано\s+(\d+)\s+комментар", text, re.IGNORECASE)
                    report_match = re.search(r"отчет\s*№?(\d+)", text, re.IGNORECASE)

                    if money_match and comments_match:
                        amount = float(money_match.group(1).replace(",", "."))
                        comments_count = int(comments_match.group(1))
                        report_num = report_match.group(1) if report_match else ""

                        database.add_report(comments_count=comments_count, amount_rub=amount, report_num=report_num, source="auto")
                        print(f"[Auto Stats] Записано: {comments_count} комментів, {amount} ₽ (Звіт #{report_num})")
            except Exception as e:
                print(f"[Msg Handler Error] {e}")

        # Обробка натискання кнопок вибору тегу
        @client.on(events.CallbackQuery)
        async def handle_callback_query(event):
            data = event.data.decode("utf-8", errors="ignore")
            if data.startswith("tag:"):
                selected_tag = data.split("tag:")[1]
                await event.answer(f"Обрано: #{selected_tag}")
                await send_videos_for_tag(client, tag=selected_tag, count=5)

        # Реєстрація команд користувача у "Saved Messages"
        @client.on(events.NewMessage(chats="me"))
        async def handle_saved_messages_commands(event):
            text = event.raw_text.strip()
            
            if text.startswith("/start") or text.startswith("/help"):
                help_text = (
                    "🤖 **RubUP Helper Bot активний!**\n\n"
                    "📅 **Автозбір картинок:** 00:00, 08:00, 16:00 (надсилає тільки 5 картинок)\n\n"
                    "🎬 **Відео TikTok під коментарі:**\n"
                    "• `/video` — відкриває меню вибору хештегу кнопками\n"
                    "• `/video 5 кс2` — швидкий пошук без кнопок за конкретним тегом\n\n"
                    "💬 **Генерація коментарів для TikTok:**\n"
                    "• `/gen` — згенерувати 5 унікальних коментарів\n"
                    "• `/gen 10` — згенерувати від 1 до 30 коментарів\n\n"
                    "🖼 **Ручний збір картинок:**\n"
                    "• `/collect` — зібрати 5 картинок з RubUP прямо зараз\n\n"
                    "📊 **Звіти та статистика заробітку:**\n"
                    "• `/zvit7` — статистика за останні 7 днів\n"
                    "• `/zvit30` — статистика за останні 30 днів\n"
                    "• `/zvit_all` — статистика за весь час\n"
                    "• `/zvit <к-сть> <сума>` — додати звіт вручну (напр: `/zvit 10 30`)\n"
                )
                await event.reply(help_text)

            elif text == "/video":
                # Передаємо callback_data як рядок або коректний utf-8 encode
                tag_buttons = [
                    [Button.inline("🔥 #кс2", "tag:кс2".encode('utf-8')), Button.inline("🎮 #cs2", "tag:cs2".encode('utf-8')), Button.inline("💰 #rubup", "tag:rubup".encode('utf-8'))],
                    [Button.inline("⚡ #меллстрой", "tag:меллстрой".encode('utf-8')), Button.inline("😎 #бустер", "tag:бустер".encode('utf-8')), Button.inline("🎁 #тгподарки", "tag:тгподарки".encode('utf-8'))],
                    [Button.inline("💎 #нфт", "tag:нфт".encode('utf-8')), Button.inline("🎯 #dota2", "tag:dota2".encode('utf-8')), Button.inline("🎲 #кейсер", "tag:кейсер".encode('utf-8'))],
                    [Button.inline("✨ Будь-який (рандом)", "tag:random".encode('utf-8'))]
                ]
                await event.reply("🎯 **Оберіть хештег для пошуку свіжих відео:**", buttons=tag_buttons)

            elif text.startswith("/video "):
                parts = text.split()
                count = 5
                specific_tag = None
                
                if len(parts) == 2:
                    if parts[1].isdigit():
                        count = max(1, min(int(parts[1]), 10))
                    else:
                        specific_tag = parts[1]
                elif len(parts) >= 3:
                    if parts[1].isdigit():
                        count = max(1, min(int(parts[1]), 10))
                        specific_tag = parts[2]
                    else:
                        specific_tag = parts[1]
                
                await send_videos_for_tag(client, tag=specific_tag or "random", count=count)

            elif text.startswith("/gen"):
                parts = text.split()
                count = 5
                if len(parts) > 1 and parts[1].isdigit():
                    count = max(1, min(int(parts[1]), 30))
                    
                comments = comments_generator.generate_comments_pack(count)
                msg_lines = [f"💬 **Ваші {len(comments)} безпечних коментарів для TikTok:**\n"]
                for c in comments:
                    msg_lines.append(f"`{c}`\n")
                
                await event.reply("\n".join(msg_lines))

            elif text == "/collect":
                await event.reply("⏳ Починаю збір 5 картинок...")
                asyncio.create_task(collect_five_images(client))

            elif text.startswith("/zvit7"):
                stats = database.get_stats(days=7)
                ans = (
                    f"📊 **Звіт за останні 7 днів:**\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"💬 Зараховано коментарів: **{stats['total_comments']}**\n"
                    f"💰 Зароблено: **{stats['total_rub']} ₽**\n"
                    f"📝 Кількість виплат/звітів: **{stats['reports_count']}**\n"
                )
                await event.reply(ans)

            elif text.startswith("/zvit30"):
                stats = database.get_stats(days=30)
                ans = (
                    f"📊 **Звіт за останні 30 днів:**\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"💬 Зараховано коментарів: **{stats['total_comments']}**\n"
                    f"💰 Зароблено: **{stats['total_rub']} ₽**\n"
                    f"📝 Кількість виплат/звітів: **{stats['reports_count']}**\n"
                )
                await event.reply(ans)

            elif text.startswith("/zvit_all"):
                stats = database.get_stats()
                ans = (
                    f"📊 **Загальний звіт за весь час:**\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"💬 Всього коментарів: **{stats['total_comments']}**\n"
                    f"💰 Всього зароблено: **{stats['total_rub']} ₽**\n"
                    f"📝 Кількість виплат/звітів: **{stats['reports_count']}**\n"
                )
                await event.reply(ans)

            elif text.startswith("/zvit"):
                parts = text.split()
                if len(parts) >= 3 and parts[1].isdigit():
                    comments_cnt = int(parts[1])
                    try:
                        amt = float(parts[2].replace(",", "."))
                        database.add_report(comments_count=comments_cnt, amount_rub=amt, source="manual")
                        await event.reply(f"✅ Успішно записано: **{comments_cnt}** коментів на суму **{amt} ₽**")
                    except ValueError:
                        await event.reply("❌ Помилка в сумі. Формат: `/zvit <комментів> <сума>` (наприклад: `/zvit 20 60`)")
                else:
                    await event.reply("ℹ️ Формат команди: `/zvit <комментів> <сума>`\nПриклад: `/zvit 20 60`")

        print("Підключення до Telegram...")
        await client.start()
        print("Telegram підключено успішно!")

        # Налаштування розкладу: 00:00, 08:00, 16:00
        scheduler = AsyncIOScheduler(timezone=TIMEZONE)
        scheduler.add_job(lambda: asyncio.create_task(collect_five_images(client)), 'cron', hour='0,8,16', minute=0)
        scheduler.start()
        print(f"Розклад активовано на 00:00, 08:00, 16:00 за часовим поясом {TIMEZONE}")
    else:
        print("[Warning] API_ID, API_HASH або STRING_SESSION не вказано!")

    # Запуск веб-сервера aiohttp
    app = await init_web_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    print(f"Веб-сервер успішно запущено на порті {PORT}")

    # Тримаємо процес живим
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
