# storage.py

import os
import json
import uuid
import datetime

import boto3
from botocore.exceptions import ClientError


S3_ENDPOINT = os.getenv(
    "S3_ENDPOINT"
)

S3_ACCESS_KEY = os.getenv(
    "S3_ACCESS_KEY"
)

S3_SECRET_KEY = os.getenv(
    "S3_SECRET_KEY"
)

S3_BUCKET = os.getenv(
    "S3_BUCKET"
)

S3_PUBLIC_URL = os.getenv(
    "S3_PUBLIC_URL"
)



def get_s3_client():

    if not all(
        [
            S3_ENDPOINT,
            S3_ACCESS_KEY,
            S3_SECRET_KEY,
            S3_BUCKET
        ]
    ):
        return None


    return boto3.client(

        "s3",

        endpoint_url=S3_ENDPOINT,

        aws_access_key_id=S3_ACCESS_KEY,

        aws_secret_access_key=S3_SECRET_KEY

    )



def upload_log(log_data):
    """
    Upload JSONL log and return public URL.
    """


    filename = (

        "logs/"

        +

        datetime.datetime.utcnow()
        .strftime(
            "%Y%m%d_%H%M%S"
        )

        +

        "_"

        +

        str(uuid.uuid4())

        +

        ".jsonl"

    )


    content = (

        json.dumps(
            log_data,
            ensure_ascii=False
        )

        +

        "\n"

    )



    try:

        s3 = get_s3_client()


        if s3 is None:

            return os.getenv(

                "PUBLIC_LOG_URL",

                "https://your-host/run.jsonl"

            )


        s3.put_object(

            Bucket=S3_BUCKET,

            Key=filename,

            Body=content.encode(
                "utf-8"
            ),

            ContentType="application/json"

        )


        return (

            S3_PUBLIC_URL.rstrip(
                "/"
            )

            +

            "/"

            +

            filename

        )



    except ClientError as e:


        print(
            "S3 upload error:",
            e
        )


        return os.getenv(

            "PUBLIC_LOG_URL",

            "https://your-host/run.jsonl"

        )