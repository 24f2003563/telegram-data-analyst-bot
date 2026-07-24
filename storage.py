# storage.py

import os
import json
import base64
import datetime
import requests


GITHUB_TOKEN = os.getenv(
    "GITHUB_TOKEN"
)

GITHUB_OWNER = os.getenv(
    "GITHUB_OWNER"
)

GITHUB_REPO = os.getenv(
    "GITHUB_REPO"
)

GITHUB_BRANCH = os.getenv(
    "GITHUB_BRANCH",
    "main"
)

LOG_FILE_PATH = os.getenv(
    "LOG_FILE_PATH",
    "run.jsonl"
)



def upload_log(log_data):
    """
    Upload JSONL logs to GitHub.
    Returns public raw URL.
    """


    if not all(
        [
            GITHUB_TOKEN,
            GITHUB_OWNER,
            GITHUB_REPO
        ]
    ):

        return (
            "https://github.com/"
            + str(GITHUB_OWNER)
            + "/"
            + str(GITHUB_REPO)
            + "/raw/"
            + GITHUB_BRANCH
            + "/"
            + LOG_FILE_PATH
        )



    api_url = (

        f"https://api.github.com/repos/"
        f"{GITHUB_OWNER}/"
        f"{GITHUB_REPO}/contents/"
        f"{LOG_FILE_PATH}"

    )



    headers = {

        "Authorization":
            f"Bearer {GITHUB_TOKEN}",

        "Accept":
            "application/vnd.github+json"

    }



    new_line = (

        json.dumps(
            log_data,
            ensure_ascii=False
        )

        +

        "\n"

    )



    try:

        # Get existing file

        response = requests.get(
            api_url,
            headers=headers,
            timeout=30
        )


        sha = None


        if response.status_code == 200:

            file_data = response.json()

            sha = file_data["sha"]

            old_content = base64.b64decode(
                file_data["content"]
            ).decode(
                "utf-8"
            )

        else:

            old_content = ""



        updated_content = (
            old_content
            +
            new_line
        )



        encoded = base64.b64encode(

            updated_content.encode(
                "utf-8"
            )

        ).decode(
            "utf-8"
        )



        payload = {

            "message":
                "update bot run log",

            "content":
                encoded,

            "branch":
                GITHUB_BRANCH

        }


        if sha:

            payload["sha"] = sha



        upload = requests.put(

            api_url,

            headers=headers,

            json=payload,

            timeout=30

        )


        upload.raise_for_status()



        return (

            f"https://raw.githubusercontent.com/"
            f"{GITHUB_OWNER}/"
            f"{GITHUB_REPO}/"
            f"{GITHUB_BRANCH}/"
            f"{LOG_FILE_PATH}"

        )



    except Exception as e:

        print(
            "GitHub log upload failed:",
            e
        )


        return (

            f"https://raw.githubusercontent.com/"
            f"{GITHUB_OWNER}/"
            f"{GITHUB_REPO}/"
            f"{GITHUB_BRANCH}/"
            f"{LOG_FILE_PATH}"

        )
