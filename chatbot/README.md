# Chatbot

A small window that opens the other tools from a sentence ("VWAP for AAPL", "daily movers"). It can match tools locally. With an API key it also answers in prose.

## Run

From the repo root:

```bash
python -m chatbot
```

Dependencies are in the repo `requirements.txt` (`chatbot/requirements.txt` is only `python-dotenv` and `requests`, if you want just those). Optional: put `OPENROUTER_API_KEY` in `chatbot/.env` for the hosted model. Without it, the window still launches tools from what you type.

The same commands are documented in [screeners](../screeners/README.md), [charts](../charts/README.md), [fundamentals](../fundamentals/README.md), and [launchers](../launchers/README.md).
