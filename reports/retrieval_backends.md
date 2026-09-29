# Retrieval backends — does Qdrant change the answers?

Measured on all 450 evaluation messages (250 dev + 200 golden), k=5, against the
numpy retriever as reference. Qdrant ran in local mode (`QDRANT_URL=:memory:`),
which is an exhaustive scan, so this isolates the ranking contract from anything
the server's HNSW index would add.

| | numpy | Qdrant (exact) |
|---|---|---|
| Index build | 0.9s from the embedding cache | 2.4s upsert |
| Retriever cold start | 0.9s (re-embeds on a cache miss: ~2 min) | 0.0s |
| Same top-5, dev (n=250) | reference | **250/250** |
| Same top-5, golden (n=200) | reference | **200/200** |

## What the first run found

Parity was **97/100**, not 100/100. Every mismatch was an exact score tie:

```
query 23   numpy  rank5: 1921024 @ 0.683   rank6: 1403318 @ 0.683
           qdrant rank5: 1403318 @ 0.683   rank6: 1921024 @ 0.683
```

The corpus contains near-duplicate tweets, so several candidates land on an
identical cosine score and each backend then picked among them by its own
internal order.

That exposed a defect in the numpy retriever that predates Qdrant. `np.argsort`
defaults to quicksort, which is **not stable**, so which of the tied cases made
the top-5 was never specified — it happened to be consistent on one machine with
one numpy version. The prompt carries those cases and `llm_cache/` is keyed by a
hash of the prompt, so the offline-reproduction guarantee was resting on an
implementation detail rather than on anything the code promised.

## The fix

Both backends now apply the same total order: **score descending, then msg_id
ascending.** numpy uses `np.lexsort`; Qdrant over-fetches by 25 and re-sorts, so
a tie straddling the k boundary is resolved by the shared rule rather than by
whichever backend answered. Parity is now 450/450.

`tests/test_retrieval_backend.py` constructs deliberate four-way ties and asserts
both paths agree, so this cannot regress silently.

## What it cost

The fix changes the retrieved set for **9 of 450** messages (4 golden, 5 dev),
which are 9 cache misses against the committed responses. Sequenced before the
live-model re-run this costs nothing, because that run regenerates the cache
anyway. Until then, `LLM_OFFLINE=1` reproduction fails on those 9 messages.

## What is still not measured

HNSW. Local mode is exhaustive by construction, so the approximate-search
question — how much recall an ANN index gives up for how much latency — needs a
real Qdrant server and has not been answered. The shipped default is exact
search, where that trade-off does not arise.
