# telegram-data-analyst-bot

A Telegram bot that answers data-analysis questions using an LLM agent.
When you message it a question, it:

1. Figures out whether it needs a dataset, and if so where to get it.
2. Downloads and cleans the dataset (CSV / Excel / JSON / HTML table).
3. Writes pandas code to compute the answer (based on the dataset's real
   columns), runs it, and retries automatically if the code errors out.
4. Formats the final answer into the exact JSON shape the question asked for.
5. Replies with `{"answer": ..., "log_url": "..."}` and appends a line to a
   public JSONL run log on GitHub

## Files

- `app.py` — Telegram bot + a tiny FastAPI health-check server (so a host
  like Render can keep the service alive).
- `agent.py` — the agent pipeline (plan → load data → write code → run →
  retry on error → format answer).
- `tools.py` — dataset loading/cleaning and the sandboxed code runner.
- `prompts.py` — the system prompts for each stage.
- `storage.py` — appends each run to `run.jsonl` in a GitHub repo and
  returns its public raw URL.

## 1. Set up your environment variables

Copy `.env.example` to `.env` and fill in:

| Variable | What it is |
|---|---|
| `TELEGRAM_BOT_TOKEN` | From @BotFather (see below) |
| `AIPIPE_TOKEN` | Your AI Pipe token (or swap in any OpenAI-compatible key/base_url) |
| `MODEL` | Defaults to `gpt-4.1-mini` |
| `GITHUB_TOKEN` | A GitHub personal access token with `repo` scope |
| `GITHUB_OWNER` | Your GitHub username |
| `GITHUB_REPO` | The repo the log should be written to |
| `GITHUB_BRANCH` | Defaults to `main` |
| `LOG_FILE_PATH` | Defaults to `run.jsonl` |

### Create the Telegram bot

1. Open Telegram, message **@BotFather**.
2. Send `/newbot`, give it a name, then a username ending in `bot`.
3. BotFather gives you a token — that's `TELEGRAM_BOT_TOKEN`.

### Get an AI Pipe token

Go to https://aipipe.org, sign in, copy your token into `AIPIPE_TOKEN`.
(If you'd rather use OpenAI directly, change the `base_url` in `agent.py`
and use a normal `OPENAI_API_KEY`.)

### Create a GitHub token for the log

1. GitHub → Settings → Developer settings → Personal access tokens →
   Fine-grained tokens.
2. Give it **Contents: Read and write** access on the one repo you'll use
   for logging (can be this same repo).
3. Put the token in `GITHUB_TOKEN`, and the repo's owner/name in
   `GITHUB_OWNER` / `GITHUB_REPO`.

## 2. Run it locally

```bash
pip install -r requirements.txt
python app.py
```

Message your bot on Telegram directly and see if it replies with a single
JSON object.

## 3. Test with the official grading pipeline

Clone https://github.com/Jivraj-18/tds-p1-t2-2026-telegram-bot, point it at
your bot's username, and add your own sample questions to
`evals/questions.json` to sanity-check before the real grading run.

## 4. Deploy so it stays reachable

`render.yaml` + `Dockerfile` are set up for [Render](https://render.com):

1. Push this repo to GitHub.
2. On Render: New → Blueprint → pick this repo → it reads `render.yaml`.
3. Fill in the secret env vars in the Render dashboard (the ones marked
   `sync: false`).
4. Deploy. Render's free web services can sleep after inactivity, so if
   you're on the free tier, consider a lightweight uptime pinger hitting
   `/health` every few minutes, or upgrade to an always-on instance.

## 5. Register your bot

Submit, comma-separated: your public GitHub repo URL, and your Telegram
bot's username (must end in `bot`).

## Known limitations / things worth improving further

- The dataset URL is guessed by the LLM from the question text. If a
  question doesn't literally include a working link, the guess can be
  wrong — you may want to add a real web-search tool for tougher MOSPI
  lookups.
- The pandas code runs in a lightly-restricted `exec()`, not a full
  sandbox/container — fine for this assignment, but don't reuse this
  pattern for untrusted public traffic.
- There's no per-user rate limiting; a burst of messages will fire a burst
  of LLM calls.
