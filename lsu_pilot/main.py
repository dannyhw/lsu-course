import os
import logging
import pandas
import numpy
import pathlib
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from dotenv import load_dotenv
from openai import OpenAI
from questions import answer_question

load_dotenv()  # take environment variables from .env.


openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
tg_bot_token = os.getenv("TG_BOT_TOKEN")

project_root = pathlib.Path(__file__).parent.resolve()
embeddings_file_path = project_root / 'processed' / 'embeddings.csv'


messages = [{
    "role": "system",
    "content": "You are a helpful assistant that answers questions."
}]

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

source_data_frame = pandas.read_csv(
    embeddings_file_path, index_col=0)

source_data_frame['embeddings'] = source_data_frame['embeddings'].apply(
    eval).apply(numpy.array)


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    messages.append({"role": "user", "content": update.message.text})
    completion = openai.chat.completions.create(model="gpt-3.5-turbo",
                                                messages=messages)

    completion_answer = completion.choices[0].message
    messages.append(completion_answer)

    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text=completion_answer.content)


async def mozilla(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = answer_question(
        source_data_frame, question=update.message.text, debug=True)

    await context.bot.send_message(chat_id=update.effective_chat.id, text=answer)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="I'm a bot, please talk to me!")

if __name__ == "__main__":
    # Set up the Telegram bot with the provided token.
    application = ApplicationBuilder().token(tg_bot_token).build()

    # Define command handlers for starting the bot and chatting.
    start_handler = CommandHandler("start", start)
    chat_handler = CommandHandler("chat", chat)
    mozilla_handler = CommandHandler('mozilla', mozilla)

    # Add command handlers to the application.
    application.add_handler(start_handler)
    application.add_handler(chat_handler)
    application.add_handler(mozilla_handler)

    # Start the bot and poll for new messages.
    application.run_polling()
