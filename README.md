# Hiver Support Agent

AI support agent for one brand from the Kaggle *Customer Support on Twitter* dataset:
classifies intent, drafts a grounded reply, and decides auto-handle vs. escalate — plus an
evaluation harness proving how good it is.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

Download `twcs.csv` from [Kaggle](https://www.kaggle.com/datasets/thoughtvector/customer-support-on-twitter)
and place it at `data/raw/twcs.csv`.

## Layout

```
data/raw/        raw Kaggle CSV (gitignored)
data/processed/  brand subsample, threads, golden set
src/             agent pipeline
eval/            evaluation harness
reports/         report + decision log
```
