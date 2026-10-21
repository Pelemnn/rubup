"""
Покращений скрипт для отримання TELEGRAM_STRING_SESSION
"""
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import (
    SessionPasswordNeededError,
    PhoneNumberInvalidError,
    FloodWaitError
)

async def main():
    print("=" * 55)
    print("       ГЕНЕРАТОР TELEGRAM_STRING_SESSION")
    print("=" * 55)
    
    api_id_input = input("Введіть API_ID: ").strip()
    api_hash = input("Введіть API_HASH: ").strip()
    
    try:
        api_id = int(api_id_input)
    except ValueError:
        print("❌ Помилка: API_ID має бути числом!")
        return

    # Задаємо системні параметри, щоб Telegram сприймав запит як офіційний десктоп
    client = TelegramClient(
        StringSession(),
        api_id=api_id,
        api_hash=api_hash,
        device_model="Desktop",
        system_version="Windows 11",
        app_version="4.16.8"
    )

    await client.connect()
    
    phone = input("\nВведіть номер телефону з кодом країни (напр. +380...): ").strip()
    
    try:
        print("\n⏳ Відправляємо запит на код у Telegram...")
        sent_code = await client.send_code_request(phone)
        print("✅ Запит успішно відправлено!")
        print("👉 Перевірте офіційний чат 'Telegram' у додатку на телефоні або ПК.")
        
        code = input("\nВведіть отриманий код: ").strip()
        
        try:
            await client.sign_in(phone=phone, code=code)
        except SessionPasswordNeededError:
            print("\n🔐 Увімкнена хмарна двофакторна автентифікація (2FA).")
            password = input("Введіть ваш хмарний пароль: ").strip()
            await client.sign_in(password=password)
            
        session_str = client.session.save()
        print("\n" + "=" * 60)
        print("🎉 УСПІХ! ВАШ STRING_SESSION:")
        print("=" * 60)
        print(session_str)
        print("=" * 60)
        print("\nСкопіюйте цей рядок і збережіть для Render.")
        
    except PhoneNumberInvalidError:
        print("❌ Помилка: Невірний формат номера телефону!")
    except FloodWaitError as e:
        print(f"❌ Занадто багато спроб! Telegram просить зачекати: {e.seconds} секунд.")
    except Exception as e:
        print(f"❌ Помилка: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
