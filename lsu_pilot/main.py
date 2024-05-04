import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()  # take environment variables from .env.


openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
tg_bot_token = os.getenv("TG_BOT_TOKEN")


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    messages.append({"role": "user", "content": update.message.text})
    completion = openai.chat.completions.create(model="gpt-3.5-turbo",
                                                messages=messages)

    completion_answer = completion.choices[0].message
    messages.append(completion_answer)

    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text=completion_answer.content)


messages = [{
    "role": "system",
    "content": "You are a helpful assistant that answers questions."
}]

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="I'm a bot, please talk to me!")

if __name__ == "__main__":
    # Set up the Telegram bot with the provided token.
    application = ApplicationBuilder().token(tg_bot_token).build()

    # Define command handlers for starting the bot and chatting.
    start_handler = CommandHandler("start", start)
    chat_handler = CommandHandler("chat", chat)

    # Add command handlers to the application.
    application.add_handler(start_handler)
    application.add_handler(chat_handler)

    # Start the bot and poll for new messages.
    application.run_polling()
