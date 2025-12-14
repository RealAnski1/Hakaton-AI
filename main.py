import asyncio
import logging
from typing import Dict, List

from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import Bot, Dispatcher, types
from openai import OpenAI

import asyncio



# ================= НАСТРОЙКИ =================
BOT_TOKEN = "7317688190:AAEsPKHxlmr19gE6z6w2z4lCe0uq5SKTBDw"
OPENAI_API_KEY = "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"

MODEL = "gpt-4o-mini"

logging.basicConfig(level=logging.INFO)

async def handle_message(message: types.Message):
    chat_id = message.chat.id
    text = "Привет! Это ответ бота."


    await bot.send_message(chat_id, text)
    await asyncio.sleep(0.5)
# ================= OPENAI =================
client = OpenAI(api_key=OPENAI_API_KEY)

# ================= AI =================
class ChatGPT:
    def __init__(self):
        self.history: Dict[int, List[dict]] = {}
        self.max_history = 100

    def chat(self, user_id: int, text: str) -> str:
        if user_id not in self.history:
            self.history[user_id] = [
                {"role": "system", "content": (
                    "Ты — умный и полезный AI-ассистент. "
                    "Отвечай обычным текстом. "
                    "НЕ используй LaTeX, Markdown-формулы, символы \\( \\), \\[ \\], $$."
                )}

            ]

        self.history[user_id].append({"role": "user", "content": text})
        self.history[user_id] = self.history[user_id][-self.max_history:]

        response = client.chat.completions.create(
            model=MODEL,
            messages=self.history[user_id],
            temperature=0.7
        )

        answer = response.choices[0].message.content
        self.history[user_id].append({"role": "assistant", "content": answer})
        return answer

    def clear(self, user_id: int):
        self.history.pop(user_id, None)

ai = ChatGPT()

# ================= BOT =================
bot = Bot(BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ================= HANDLERS =================
@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "🤖 Я — полноценная нейросеть.\n\n"
        "Задавай любые вопросы, как в ChatGPT.\n\n"
        "/clear — очистить контекст"
    )

@dp.message(Command("clear"))
async def clear(message: Message):
    ai.clear(message.from_user.id)
    await message.answer("🧹 Контекст очищен")

@dp.message()
async def chat(message: Message):
    await bot.send_chat_action(message.chat.id, "typing")
    answer = ai.chat(message.from_user.id, message.text)
    await message.answer(answer)

# ================= RUN =================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
