import json
import logging
import os
import pathlib

import numpy
import pandas
import requests
from dotenv import load_dotenv
from openai import OpenAI
from telegram import Update
from telegram.ext import (ApplicationBuilder, CommandHandler, ContextTypes,
                          MessageHandler, filters)

from .functions import functions, run_function, text_to_image
from .questions import answer_question

load_dotenv()  # take environment variables from .env.


openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
tg_bot_token = os.getenv("TG_BOT_TOKEN")

project_root = pathlib.Path(__file__).parent.resolve()
embeddings_file_path = project_root / 'processed' / 'embeddings.csv'

CODE_PROMPT = """
Here are two input:output examples for code generation. Please use these and follow the styling for future requests that you think are pertinent to the request.
Make sure All HTML is generated with the JSX flavoring.
// SAMPLE 1
// A Blue Box with 3 yellow cirles inside of it that have a red outline
<div style={{   backgroundColor: 'blue',
  padding: '20px',
  display: 'flex',
  justifyContent: 'space-around',
  alignItems: 'center',
  width: '300px',
  height: '100px', }}>
  <div style={{     backgroundColor: 'yellow',
    borderRadius: '50%',
    width: '50px',
    height: '50px',
    border: '2px solid red'
  }}></div>
  <div style={{     backgroundColor: 'yellow',
    borderRadius: '50%',
    width: '50px',
    height: '50px',
    border: '2px solid red'
  }}></div>
  <div style={{     backgroundColor: 'yellow',
    borderRadius: '50%',
    width: '50px',
    height: '50px',
    border: '2px solid red'
  }}></div>
</div>
"""


messages = [
    {
        "role": "system",
        "content": "You are a helpful assistant that answers questions."
    },
    {
        "role": "system",
        "content": CODE_PROMPT
    },
]

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

source_data_frame = pandas.read_csv(
    embeddings_file_path, index_col=0)

source_data_frame['embeddings'] = source_data_frame['embeddings'].apply(
    eval).apply(numpy.array)


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    messages.append({"role": "user", "content": update.message.text})

    initial_response = openai.chat.completions.create(model="gpt-3.5-turbo",
                                                      messages=messages,
                                                      tools=functions)

    initial_response_message = initial_response.choices[0].message

    messages.append(initial_response_message)

    final_response = None

    tool_calls = initial_response_message.tool_calls

    print(f"tool calls: {tool_calls}")

    if tool_calls:
        for tool_call in tool_calls:
            name = tool_call.function.name

            args = json.loads(tool_call.function.arguments)

            response = run_function(name, args)

            print(f"{tool_call} {response}")

            messages.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": name,
                "content": str(response),
            })

            if name == 'svg_to_png_bytes':
                await context.bot.send_photo(chat_id=update.effective_chat.id,
                                             photo=response)

            if name == 'text_to_image':
                print(f"text to image {response}")

                image_response = requests.get(response)

                await context.bot.send_photo(chat_id=update.effective_chat.id,
                                             photo=image_response.content)

            # Generate the final response
            final_response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
            )

            final_answer = final_response.choices[0].message

            # Send the final response if it exists
            if (final_answer):
                messages.append(final_answer)

                await context.bot.send_message(chat_id=update.effective_chat.id,
                                               text=final_answer.content)
            else:
                # Send an error message if something went wrong
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text='something went wrong, please try again')

    # no functions were executed
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=initial_response_message.content)


async def image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    image_url = text_to_image(image_description=update.message.text)

    image_response = requests.get(image_url)

    await context.bot.send_photo(chat_id=update.effective_chat.id,
                                 photo=image_response.content)


async def mozilla(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = answer_question(
        source_data_frame, question=update.message.text, debug=True)

    await context.bot.send_message(chat_id=update.effective_chat.id, text=answer)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="I'm a bot, please talk to me!")


async def transcribe_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Make sure we have a voice file to transcribe
    voice_id = update.message.voice.file_id
    if voice_id:
        file = await context.bot.get_file(voice_id)
        await file.download_to_drive(f"voice_note_{voice_id}.ogg")
        await update.message.reply_text("Voice note downloaded, transcribing now")
        audio_file = open(f"voice_note_{voice_id}.ogg", "rb")
        transcript = openai.audio.transcriptions.create(
            model="whisper-1", file=audio_file
        )
        await update.message.reply_text(
            f"Transcript finished:\n {transcript.text}"
        )

if __name__ == "__main__":
    # Set up the Telegram bot with the provided token.
    application = ApplicationBuilder().token(tg_bot_token).build()

    # Define command handlers for starting the bot and chatting.
    start_handler = CommandHandler("start", start)
    chat_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), chat)
    mozilla_handler = CommandHandler('mozilla', mozilla)
    image_handler = CommandHandler('image', image)
    voice_handler = MessageHandler(filters.VOICE, transcribe_message)

    # Add command handlers to the application.
    application.add_handler(start_handler)
    application.add_handler(chat_handler)
    application.add_handler(mozilla_handler)
    application.add_handler(image_handler)
    application.add_handler(voice_handler)

    # Start the bot and poll for new messages.
    application.run_polling()
