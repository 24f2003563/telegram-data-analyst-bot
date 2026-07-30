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
    CODER_PROMPT,
    FINAL_RESPONSE_PROMPT,
)


load_dotenv()


client = OpenAI(
    api_key=os.environ["AIPIPE_TOKEN"],
    base_url="https://aipipe.org/openai/v1"
)


MODEL = os.getenv("MODEL", "gpt-4.1-mini")

MAX_CODE_ATTEMPTS = 3


def extract_json(text):
    text = text.strip()

    # strip markdown fences if the model added them anyway
    text = re.sub(r"^```(json)?", "", text.strip())
    text = re.sub(r"```$", "", text.strip())
    text = text.strip()

    try:
        return json.loads(text)
    except Exception:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise ValueError("Model returned invalid JSON: " + text[:300])


def ask_llm(messages):
    response = client.chat.completions.create(
        model=MODEL,
        temperature=0,
        messages=messages,
    )
    return response.choices[0].message.content


def create_plan(history):
    response = ask_llm(
        [
            {"role": "system", "content": DATA_ANALYSIS_PLANNER_PROMPT},
            *history,
        ]
    )
    return extract_json(response)


def write_code(history, dataset_summary, previous_error=None):
    context = {
        "conversation": history,
        "dataframe_summary": dataset_summary,
    }
    if previous_error:
        context["previous_attempt_error"] = previous_error

    response = ask_llm(
        [
            {"role": "system", "content": CODER_PROMPT},
            {
                "role": "user",
                "content": json.dumps(context, ensure_ascii=False, default=str),
            },
        ]
    )
    return extract_json(response).get("python_code", "")


def format_answer(history, result):
    response = ask_llm(
        [
            {"role": "system", "content": FINAL_RESPONSE_PROMPT},
            {
                "role": "user",
                "content": json.dumps(
                    {"conversation": history, "result": result},
                    ensure_ascii=False,
                    default=str,
                ),
            },
        ]
    )
    return extract_json(response)


def run_agent(history, trace=None):
    """
    Runs the full pipeline and returns the final answer JSON
    (the value that should go under the "answer" key).

    `trace`, if given a list, gets each intermediate step appended to it
    so it can be written into the run log.
    """
    if trace is None:
        trace = []

    plan = create_plan(history)
    trace.append({"step": "plan", "data": plan})

    analysis_result = {"notes": plan.get("notes", "")}
    dataframe = None

    if plan.get("needs_data"):
        url = plan.get("dataset_url")
        if url:
            try:
                dataframe = load_dataset(url)
                dataframe = clean_dataframe(dataframe)
                summary = dataframe_summary(dataframe)
                analysis_result["dataset_summary"] = summary
                trace.append({"step": "load_dataset", "url": url, "summary": summary})
            except Exception as e:
                analysis_result["dataset_error"] = str(e)
                trace.append({"step": "load_dataset_failed", "url": url, "error": str(e)})

    if dataframe is not None:
        previous_error = None
        for attempt in range(1, MAX_CODE_ATTEMPTS + 1):
            code = write_code(
                history,
                analysis_result.get("dataset_summary", {}),
                previous_error=previous_error,
            )
            trace.append({"step": f"code_attempt_{attempt}", "code": code})

            outcome = run_analysis(code, dataframe)
            trace.append({"step": f"code_result_{attempt}", "outcome": outcome})

            if outcome.get("success"):
                analysis_result["calculation"] = outcome
                break

            previous_error = outcome.get("error")
            analysis_result["calculation"] = outcome

    final = format_answer(history, analysis_result)
    trace.append({"step": "final_answer", "data": final})

    return final
