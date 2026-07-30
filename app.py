# app.py

import os
import json
import uuid
import datetime
import traceback
import threading

from dotenv import load_dotenv

from fastapi import FastAPI

import uvicorn

from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    ContextTypes,
    filters,
)

from openai import AuthenticationError

from agent import run_agent
from storage import upload_log


load_dotenv()


TELEGRAM_BOT_TOKEN = os.environ[
    "TELEGRAM_BOT_TOKEN"
]


USER_MEMORY = {}

MAX_HISTORY = 10



# -------------------------
# Telegram message handler
# -------------------------

async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return


    question = update.message.text


    if not question:
        return


    user_id = str(
        update.effective_user.id
    )


    if user_id not in USER_MEMORY:

        USER_MEMORY[user_id] = []


    USER_MEMORY[user_id].append(

        {
            "role": "user",
            "content": question
        }

    )


    USER_MEMORY[user_id] = (
        USER_MEMORY[user_id]
        [-MAX_HISTORY:]
    )


    run_id = str(
        uuid.uuid4()
    )


    log = {

        "run_id": run_id,

        "timestamp":
            datetime.datetime.utcnow()
            .isoformat(),

        "user_id": user_id,

        "question": question

    }



    try:

        trace = []

        history_for_agent = [
        msg for msg in USER_MEMORY[user_id]
        if msg["role"] == "user"
            ][-3:]

        answer = run_agent(
            history_for_agent,
            trace=trace
        )

        log["trace"] = trace


        final_response = {

            "answer": answer,

            "log_url": ""

        }


        USER_MEMORY[user_id].append(

            {
                "role": "assistant",

                "content":
                    json.dumps(
                        final_response,
                        ensure_ascii=False
                    )
            }

        )


        log.update(

            {
                "status": "success",
                "answer": final_response
            }

        )


        log_url = upload_log(
            log
        )


        final_response["log_url"] = (
            log_url
        )


        await update.message.reply_text(

            json.dumps(

                final_response,

                ensure_ascii=False

            )

        )


    except AuthenticationError:


        log.update(

            {
                "status": "auth_failed",
                "hint":
                    "AIPIPE_TOKEN (or your LLM API key) is invalid or "
                    "expired - refresh it and update the env var.",
                "error":
                    traceback.format_exc()
            }

        )


        log_url = upload_log(
            log
        )


        error_response = {

            "answer":
            {
                "error":
                    "auth_failed"
            },

            "log_url":
                log_url

        }


        await update.message.reply_text(

            json.dumps(

                error_response,

                ensure_ascii=False

            )

        )


    except Exception:


        log.update(

            {
                "status": "failed",
                "error":
                    traceback.format_exc()
            }

        )


        log_url = upload_log(
            log
        )


        error_response = {

            "answer":
            {
                "error":
                    "agent_failed"
            },

            "log_url":
                log_url

        }


        await update.message.reply_text(

            json.dumps(

                error_response,

                ensure_ascii=False

            )

        )



# -------------------------
# Telegram bot setup
# -------------------------

telegram_app = (

    Application
    .builder()
    .token(
        TELEGRAM_BOT_TOKEN
    )
    .build()

)


telegram_app.add_handler(

    MessageHandler(

        filters.TEXT
        &
        ~filters.COMMAND,

        handle_message

    )

)



def start_telegram_bot():
    import asyncio

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    telegram_app.run_polling(stop_signals=None)



# -------------------------
# FastAPI for Render
# -------------------------

api = FastAPI()



@api.get("/")
def health_check():

    return {

        "status": "running",

        "service":
            "telegram-data-analyst-bot"

    }



@api.get("/health")
def health():

    return {

        "ok": True

    }



# -------------------------
# Application start
# -------------------------

if __name__ == "__main__":


    telegram_thread = threading.Thread(

        target=start_telegram_bot,

        daemon=True

    )


    telegram_thread.start()



    uvicorn.run(

        api,

        host="0.0.0.0",

        port=int(

            os.environ.get(

                "PORT",

                10000

            )

        )

    )
