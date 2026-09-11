"""Two non-LLM baselines the agent has to beat.

trivial: always the majority intent; never escalate; always the single most common
         SpotifyCares reply from history.
simple:  TF-IDF + logistic regression for intent and for escalate (trained on the dev
         set's silver labels); reply = copy the brand reply of the most similar
         history tweet (TF-IDF nearest neighbour). No LLM anywhere.
"""
import json
from collections import Counter

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import make_pipeline

from src.config import SEED
from src.retrieval import load_history, query_text


def _text(ex: dict) -> str:
    return query_text(ex["text"], ex.get("context"))


def _classifier():
    return make_pipeline(TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True),
                         LogisticRegression(max_iter=2000, class_weight="balanced", C=5.0))


class Baselines:
    def __init__(self, train_examples: list[dict], train_labels: list[dict]):
        self.hist = load_history()
        self.most_common_reply = Counter(self.hist.brand_reply).most_common(1)[0][0]
        self.majority_intent = Counter(l["intent"] for l in train_labels).most_common(1)[0][0]
        self.train_x = [_text(e) for e in train_examples]
        self.train_intent = [l["intent"] for l in train_labels]
        self.train_esc = [l["escalate"] for l in train_labels]
        self.nn_vec = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, min_df=2)
        contexts = [json.loads(c) for c in self.hist.context]
        self.nn_matrix = self.nn_vec.fit_transform(
            [query_text(t, c) for t, c in zip(self.hist.text, contexts)])

    def _nn_replies(self, examples):
        sims = self.nn_vec.transform([_text(e) for e in examples]) @ self.nn_matrix.T
        return [self.hist.brand_reply[int(np.asarray(sims[i].todense()).argmax())]
                for i in range(len(examples))]

    def trivial(self, examples):
        return [{"intent": self.majority_intent, "escalate": False, "escalation_reason": None,
                 "reply": self.most_common_reply} for _ in examples]

    def simple(self, examples, in_sample: bool = False):
        """in_sample=True: `examples` ARE the training set -> use 5-fold out-of-fold predictions."""
        if in_sample:
            cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
            intents = cross_val_predict(_classifier(), self.train_x, self.train_intent, cv=cv)
            escs = cross_val_predict(_classifier(), self.train_x, self.train_esc, cv=cv)
        else:
            x = [_text(e) for e in examples]
            intents = _classifier().fit(self.train_x, self.train_intent).predict(x)
            escs = _classifier().fit(self.train_x, self.train_esc).predict(x)
        replies = self._nn_replies(examples)
        return [{"intent": str(i), "escalate": bool(e),
                 "escalation_reason": "account_specific" if e else None, "reply": r}
                for i, e, r in zip(intents, escs, replies)]
