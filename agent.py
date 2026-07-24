# agent.py

import os
import json
import re

from dotenv import load_dotenv
from openai import OpenAI

from tools import (
    load_dataset,
    clean_dataframe,
    dataframe_summary,
    run_analysis,
)

from prompts import (
    DATA_ANALYSIS_PLANNER_PROMPT,
    FINAL_RESPONSE_PROMPT,
)


load_dotenv()


client = OpenAI(
    api_key=os.environ["AIPIPE_TOKEN"],
    base_url="https://aipipe.org/openai/v1"
)


MODEL = os.getenv(
    "MODEL",
    "gpt-4.1-mini"
)



def extract_json(text):

    text = text.strip()

    try:
        return json.loads(text)

    except:

        match = re.search(
            r"\{.*\}",
            text,
            re.DOTALL
        )

        if match:

            return json.loads(
                match.group()
            )

        raise ValueError(
            "Model returned invalid JSON"
        )



def ask_llm(messages):

    response = client.chat.completions.create(

        model=MODEL,

        temperature=0,

        messages=messages

    )


    return (
        response
        .choices[0]
        .message
        .content
    )



def create_plan(history):

    response = ask_llm(

        [
            {
                "role": "system",
                "content":
                    DATA_ANALYSIS_PLANNER_PROMPT
            },

            *history

        ]

    )


    return extract_json(
        response
    )



def format_answer(
    history,
    result
):

    response = ask_llm(

        [
            {
                "role": "system",
                "content":
                    FINAL_RESPONSE_PROMPT
            },

            {
                "role": "user",
                "content": json.dumps(
                    {
                        "conversation": history,
                        "result": result
                    },
                    ensure_ascii=False
                )
            }

        ]

    )


    return extract_json(
        response
    )



def run_agent(history):


    plan = create_plan(
        history
    )


    analysis_result = {

        "plan": plan

    }


    dataframe = None



    try:


        if plan.get(
            "needs_data"
        ):


            url = plan.get(
                "dataset_url"
            )


            if url:


                dataframe = load_dataset(
                    url
                )


                dataframe = clean_dataframe(
                    dataframe
                )


                analysis_result[
                    "dataset_summary"
                ] = dataframe_summary(
                    dataframe
                )



        if dataframe is not None:


            code = plan.get(

                "python_code",

                ""

            )


            analysis_result[
                "calculation"
            ] = run_analysis(

                code,

                dataframe

            )



    except Exception as e:


        analysis_result[
            "error"
        ] = str(e)



    final = format_answer(

        history,

        analysis_result

    )


    return final