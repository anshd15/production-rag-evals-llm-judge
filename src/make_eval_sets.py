"""Sample the golden (test) set and the dev set from the eval pool.

- one message per thread per set, and no thread or customer shared between sets
- golden = 150 random (natural distribution) + 50 "coverage" picks spread across
  rare clusters, so small intents get enough examples for per-class metrics
- dev = 250 random; used (with silver labels) for the improvement loop, so the
  golden set is only ever touched for the final numbers

Run:  python -m src.make_eval_sets
"""
import json
import sys

import pandas as pd
from sklearn.cluster import KMeans

from src.config import MESSAGES, PROCESSED, SEED
from src.embeddings import embed

GOLDEN_RANDOM, GOLDEN_COVERAGE, DEV_SIZE = 150, 50, 250
GOLDEN_FILE = PROCESSED / "golden_set.jsonl"
DEV_FILE = PROCESSED / "dev_set.jsonl"
FIELDS = ["msg_id", "thread_id", "customer_id", "created_at", "is_opener", "context", "text",
          "brand_reply", "reply_asks_dm"]


def write_jsonl(df: pd.DataFrame, path):
    with open(path, "w", encoding="utf-8") as f:
        for r in df[FIELDS + ["stratum"]].to_dict("records"):
            r["created_at"] = str(r["created_at"])
            r["context"] = json.loads(r["context"])
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def read_jsonl(path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def main():
    # The sets are frozen once created: human labels are keyed to them.
    if (GOLDEN_FILE.exists() or DEV_FILE.exists()) and "--force" not in sys.argv:
        sys.exit(f"{GOLDEN_FILE.name}/{DEV_FILE.name} already exist and are frozen "
                 "(labels depend on them). Pass --force to resample anyway.")
    m = pd.read_parquet(MESSAGES)
    pool = m[m.split == "eval_pool"]
    # one message per thread, then shuffle
    pool = pool.sample(frac=1, random_state=SEED).drop_duplicates("thread_id")

    golden_rand = pool.drop_duplicates("customer_id").head(GOLDEN_RANDOM)
    rest = pool[~pool.customer_id.isin(golden_rand.customer_id)]

    # coverage stratum: round-robin over clusters, smallest clusters first
    vecs = embed(rest.text.tolist(), cache_name="eval_pool_rest")
    rest = rest.assign(cluster=KMeans(n_clusters=25, n_init=10, random_state=SEED).fit(vecs).labels_)
    order = rest.cluster.value_counts(ascending=True).index
    picks, used_customers = [], set()
    for rank in range(10):
        for c in order:
            g = rest[(rest.cluster == c) & ~rest.customer_id.isin(used_customers)]
            if len(g) > rank and len(picks) < GOLDEN_COVERAGE:
                row = g.iloc[rank]
                picks.append(row.msg_id)
                used_customers.add(row.customer_id)
    golden_cov = rest[rest.msg_id.isin(picks)]

    golden = pd.concat([golden_rand.assign(stratum="random"), golden_cov.assign(stratum="coverage")])
    golden = golden.sample(frac=1, random_state=SEED)  # mix strata so labelling order is blind

    dev_pool = pool[~pool.customer_id.isin(golden.customer_id) & ~pool.thread_id.isin(golden.thread_id)]
    dev = dev_pool.drop_duplicates("customer_id").head(DEV_SIZE).assign(stratum="random")

    write_jsonl(golden, GOLDEN_FILE)
    write_jsonl(dev, DEV_FILE)
    print(f"golden {len(golden)} ({golden.stratum.value_counts().to_dict()}) -> {GOLDEN_FILE}")
    print(f"dev {len(dev)} -> {DEV_FILE}")
    print("openers: golden %.0f%%, dev %.0f%%" % (100 * golden.is_opener.mean(), 100 * dev.is_opener.mean()))


if __name__ == "__main__":
    main()
