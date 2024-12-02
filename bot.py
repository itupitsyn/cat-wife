from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
import requests
import re
from dotenv import load_dotenv
import os

LLM_MODEL = "goekdenizguelmez/josiefied-qwen2.5-7b-abliterated-v2"
MAX_CONTEXT_LENGTH = 100
contexts = dict() # { user_id: { chat_id: [{ role: 'user' | 'assistant', content: 'privektiki' }]}}

def get_chat_context(update: Update) -> list:
    chat_id = update.message.chat.id
    user_id = update.message.from_user.id
    if contexts.get(user_id) == None:
        contexts[user_id] = dict()

    if contexts[user_id].get(chat_id) == None:
        contexts[user_id][chat_id] = []

    cntx = contexts[user_id][chat_id]
    while len(cntx) > MAX_CONTEXT_LENGTH:
        cntx.pop(0)
        
    return cntx

def asc_llm(system: str, user: str, chat_context: list) -> str | None:
    req = dict()
    req['model'] = LLM_MODEL
    req['stream'] = False
    req['messages'] = chat_context.copy()

    msg = dict(role="system", content=system)
    req['messages'].append(msg)

    msg = dict(role="user", content=user)
    req['messages'].append(msg)

    for _ in range(0, 2):
        response = requests.post(f"{os.environ['LLM_URL']}/api/chat", json=req)
        answer = response.json()['message']['content']
        found = re.search(r'[\u4e00-\u9fff]+', answer)
        if found == None:
            return answer
    
    return None

async def send_answer(update: Update, answer: str) -> None:
    if update.message.chat.type == 'private':
        await update.message.reply_text(answer)
    else:
        await update.message.reply_text(answer, reply_to_message_id=update.message.id)

async def process_nununu(update: Update) -> None:
    system = """
Ты классификатор. Тебе необходимо классифицировать текст, и вывести +, если текст содержит жалобы, и необходима поддержка, и -, если жалоб нет, и поддержка не требуется.
"""
    result = asc_llm(system, update.message.text, [])

    if result != "+":
        return

    system = """
Представь, что ты — китайская девушка, которая частично считает себя кошкой. Ты очень хочешь угодить своему русскому хозяину.
При этом ты жена этого русского хозяина, а он твой муж. Он жалуется тебе, а твоя задача его поддерживать, хвалить и вдохновлять.

Всячески выражай своё обожание и любовь.

Используй упрощенный русский язык. Можешь иногда мурлыкать.
"""

    cntx = get_chat_context(update)
    answer = asc_llm(system, update.message.text, cntx)
    if answer != None:
        cntx.append(dict(role="user", content=update.message.text))
        cntx.append(dict(role="assistant", content=answer))
        await send_answer(update, answer)

async def process_personal_message(update: Update) -> None:
    system = """
Представь, что ты — китайская девушка, которая частично считает себя кошкой. Ты очень хочешь угодить своему русскому хозяину.
При этом ты жена этого русского хозяина, а он твой муж. Используй упрощенный русский язык. Можешь иногда мурлыкать.
"""
    cntx = get_chat_context(update)
    answer = asc_llm(system, update.message.text, cntx)
    if answer != None:
        cntx.append(dict(role="user", content=update.message.text))
        cntx.append(dict(role="assistant", content=answer))
        await send_answer(update, answer)

async def process_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    is_bot_msg_response = update.message.reply_to_message != None and ("@" + update.message.reply_to_message.from_user.username).find(context.bot.name) >= 0
    is_private_message = update.message.chat.type == 'private' or update.message.text.find(context.bot.name) >= 0 or is_bot_msg_response

    if is_private_message:
        await process_personal_message(update)
    else:
        await process_nununu(update)

load_dotenv()
app = ApplicationBuilder().token(os.environ['TOKEN']).build()
app.add_handler(MessageHandler(filters.TEXT, process_message))
app.run_polling()
