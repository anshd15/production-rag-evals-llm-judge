# Judge vs human agreement — not established

2 of 60 drafts rated; a Cohen's kappa needs at least 30 to be worth printing.

Until those ratings exist, every reply-quality number in the report rests on a model grading a
model, and should be read that way. The routing metrics are unaffected — those are scored against
human labels.

Rate the remaining drafts with `python -m src.label_app` (tab 2), or the offline pack:
`python -m src.export_ratings export` then `import labelling/ratings.json`.
