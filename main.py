from pyrogram import Client, errors
import asyncio
import os
from dotenv import load_dotenv
from models import create_tables, process_group
from io import BytesIO

load_dotenv(dotenv_path=".env")

# Создаем таблицы при запуске
create_tables()

app = Client(
    "account",
    api_id=os.getenv("API_ID"),
    api_hash=os.getenv("API_HASH"),
)
user_id = int(os.getenv("USER_ID"))

async def main():
    try:
        async with app:
            async for dialog in app.get_dialogs():
                if dialog.chat.id == user_id:
                    continue

                try:
                    history_count = await app.get_chat_history_count(dialog.chat.id)
                except errors.FloodWait as e:
                    print(f"Ожидаем {e.value} секунд...")
                    await asyncio.sleep(e.value + 2)
                    history_count = await app.get_chat_history_count(dialog.chat.id)
                except Exception as e:
                    print(f"Ошибка при получении истории: {e}")
                    history_count = 0

                # Получаем фото в байтах
                photo_bytes = None
                if dialog.chat.photo:
                    try:
                        file_image = await app.download_media(
                            dialog.chat.photo.small_file_id,
                            in_memory=True
                        )
                        if file_image:
                            photo_bytes = file_image.getvalue()
                    except Exception as e:
                        print(f"Ошибка загрузки фото: {e}")

                # Обрабатываем группу
                process_group(dialog.chat, history_count, photo_bytes)


    except Exception as e:
        print(f"Критическая ошибка: {type(e).__name__}: {e}")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
