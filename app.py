# app.py

import os
import json
import uuid
import datetime
import traceback

from dotenv import load_dotenv

from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    ContextTypes,
    filters,
)

from agent import run_agent
from storage import upload_log


load_dotenv()


TELEGRAM_BOT_TOKEN = os.environ[
    "TELEGRAM_BOT_TOKEN"
]


USER_MEMORY = {}

MAX_HISTORY = 12



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


    # Keep recent conversation only

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


        answer = run_agent(

            USER_MEMORY[user_id]

        )


        final_answer = {

            "answer":
                answer.get(
                    "answer",
                    answer
                ),

            "log_url": ""

        }



        USER_MEMORY[user_id].append(

            {
                "role": "assistant",

                "content":
                    json.dumps(
                        final_answer,
                        ensure_ascii=False
                    )
            }

        )



        log.update(

            {

                "status": "success",

                "answer": final_answer

            }

        )


        log_url = upload_log(
            log
        )


        final_answer["log_url"] = (
            log_url
        )



        await update.message.reply_text(

            json.dumps(

                final_answer,

                ensure_ascii=False

            )

        )



    except Exception:


        log.update(

            {

                "status": "error",

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



def main():


    app = (

        Application
        .builder()
        .token(
            TELEGRAM_BOT_TOKEN
        )
        .build()

    )


    app.add_handler(

        MessageHandler(

            filters.TEXT
            &
            ~filters.COMMAND,

            handle_message

        )

    )


    app.run_polling()



if __name__ == "__main__":

    main()