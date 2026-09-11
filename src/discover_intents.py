"""Data-driven intent discovery: cluster history messages, dump examples per cluster.

The output (reports/intent_discovery.md) is what the intent taxonomy in
src/taxonomy.py was derived from: read clusters -> merge/split -> name them.

Run:  python -m src.discover_intents
"""
import json

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans

from src.config import MESSAGES, ROOT, SEED
from src.embeddings import embed

N_SAMPLE = 6000
N_CLUSTERS = 30
N_EXAMPLES = 12


def main():
    m = pd.read_parquet(MESSAGES)
    hist = m[m.split == "history"].sample(N_SAMPLE, random_state=SEED)
    vecs = embed(hist.text.tolist(), cache_name="discovery")
    km = KMeans(n_clusters=N_CLUSTERS, n_init=10, random_state=SEED).fit(vecs)
    hist = hist.assign(cluster=km.labels_)
    dist = np.linalg.norm(vecs - km.cluster_centers_[km.labels_], axis=1)
    hist = hist.assign(dist=dist)

    out = ["# Intent discovery (KMeans on MiniLM embeddings of history messages)\n",
           f"Sample: {N_SAMPLE} history messages, k={N_CLUSTERS}. Examples are the "
           "messages closest to each centroid, then random ones.\n"]
    sizes = hist.cluster.value_counts()
    for c in sizes.index:
        g = hist[hist.cluster == c]
        out.append(f"\n## Cluster {c} — {len(g)} msgs ({len(g) / len(hist):.1%}), "
                   f"brand asked for DM in {g.reply_asks_dm.mean():.0%}, "
                   f"openers {g.is_opener.mean():.0%}\n")
        ex = pd.concat([g.nsmallest(N_EXAMPLES // 2, "dist"),
                        g.sample(min(len(g), N_EXAMPLES // 2), random_state=SEED)]).drop_duplicates("msg_id")
        for _, r in ex.iterrows():
            ctx = json.loads(r.context)
            prev = f" _(after: {ctx[-1]['role']}: {ctx[-1]['text'][:80]})_" if ctx else ""
            out.append(f"- {r.text[:220]}{prev}\n  - → {r.brand_reply[:160]}")
    path = ROOT / "reports" / "intent_discovery.md"
    path.write_text("\n".join(out), encoding="utf-8")
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
