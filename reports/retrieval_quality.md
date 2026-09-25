# Retrieval quality (n=250 dev messages, proxy = the reply the brand actually sent)

| Method | precedent@1 | precedent@3 | precedent@5 | precedent@10 | mean@5 | route@1 |
|---|---|---|---|---|---|---|
| dense | 0.430 | 0.564 | 0.609 | 0.668 | 0.420 | 74.8% |
| tfidf | 0.404 | 0.548 | 0.600 | 0.657 | 0.395 | 69.2% |
| hybrid | 0.431 | 0.572 | 0.617 | 0.676 | 0.421 | 76.4% |

**Paired bootstrap on precedent@5, method minus dense:**

- tfidf: -0.010 [-0.033, +0.013], P(not better) = 0.801
- hybrid: +0.008 [-0.013, +0.027], P(not better) = 0.239

Cosine between MiniLM embeddings of the retrieved reply and the true reply; the
true reply is held out from the agent. `route@1` asks whether the top case took the
same next step (ask for a DM, or not) as the real agent did.

Dense remains the shipped default: switching would change every prompt and void the
committed golden numbers until a full re-run with a live model.
