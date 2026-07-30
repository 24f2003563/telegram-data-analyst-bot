# tools.py

import io
import json
import traceback

import pandas as pd
import numpy as np
import requests



def download_file(url):

    response = requests.get(
        url,
        timeout=60,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )

    response.raise_for_status()

    return response.content



def load_dataset(url):

    content = download_file(url)

    url_lower = url.lower()


    # JSON

    if (
        ".json" in url_lower
        or "format=json" in url_lower
        or "json" in url_lower
    ):

        data = json.loads(
            content.decode(
                "utf-8"
            )
        )


        if isinstance(
            data,
            dict
        ):

            for key in [
                "records",
                "data",
                "results"
            ]:

                if key in data:

                    data = data[key]

                    break


        return pd.DataFrame(
            data
        )



    # Excel

    if (
        ".xlsx" in url_lower
        or ".xls" in url_lower
    ):

        return pd.read_excel(
            io.BytesIO(content)
        )



    # HTML tables

    text = content.decode(
        "utf-8",
        errors="ignore"
    )


    if (
        "<table" in text.lower()
    ):

        tables = pd.read_html(
            io.StringIO(text)
        )

        if tables:

            return tables[0]



    # CSV default

    return pd.read_csv(
        io.BytesIO(content)
    )



def dataframe_summary(df):

    return {

        "rows":
            int(len(df)),

        "columns":
            [
                str(c)
                for c in df.columns
            ],

        "types":
            {
                str(c):
                str(t)

                for c, t
                in df.dtypes.items()
            },

        "sample":
            df.head(5)
            .to_dict(
                orient="records"
            )
    }



def clean_dataframe(df):

    df = df.copy()


    df.columns = [

        str(c)
        .strip()
        .lower()
        .replace(
            " ",
            "_"
        )
        .replace(
            "-",
            "_"
        )
        for c in df.columns

    ]


    return (
        df
        .dropna(
            how="all"
        )
    )



def run_analysis(code, df):

    environment = {

        "df": df,

        "pd": pd,

        "np": np

    }


    allowed_builtin_names = [
        "len", "int", "float", "str", "bool", "list", "dict", "tuple", "set",
        "max", "min", "sum", "sorted", "reversed", "enumerate", "zip", "map",
        "filter", "round", "abs", "all", "any", "range", "isinstance", "type",
        "print", "None", "True", "False",
    ]

    import builtins as _builtins

    safe_globals = {
        "__builtins__": {
            name: getattr(_builtins, name)
            for name in allowed_builtin_names
            if hasattr(_builtins, name)
        }
    }


    try:

        exec(
            code,
            safe_globals,
            environment
        )


        if "result" not in environment:

            return {

                "success": False,

                "error":
                "Python code did not create result"

            }


        return {

            "success": True,

            "result":
                make_json_safe(
                    environment["result"]
                )

        }


    except Exception:

        return {

            "success": False,

            "error":
            traceback.format_exc()

        }



def make_json_safe(value):


    if isinstance(
        value,
        pd.DataFrame
    ):

        return value.to_dict(
            orient="records"
        )


    if isinstance(
        value,
        pd.Series
    ):

        return value.to_dict()



    if isinstance(
        value,
        (np.integer,)
    ):

        return int(value)



    if isinstance(
        value,
        (np.floating,)
    ):

        return float(value)



    try:

        json.dumps(
            value
        )

        return value


    except Exception:

        return str(value)



def dataframe_to_json(df):

    return json.loads(

        df.to_json(
            orient="records"
        )

    )