from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_CSV = ROOT / "data" / "raw" / "twcs" / "twcs.csv"
PROCESSED = ROOT / "data" / "processed"
MESSAGES = PROCESSED / "messages.parquet"

BRAND = "SpotifyCares"
BRAND_NAME = "Spotify"

# Threads that start on/after this date form the evaluation pool (golden + dev sets).
# Everything earlier is "history": the retrieval corpus and baseline training data.
# Splitting by time (not randomly) means the agent can never retrieve a reply
# written after the message it is answering.
EVAL_START = "2017-11-25"

MAX_CONTEXT_TURNS = 4
SEED = 42
