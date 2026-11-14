# tests/fixtures/engine_body/ -- fixtures for the engine body contract suite

Purpose.  Static probe data for tests/t_engines_body.py: one clean sample, one
  deliberately dirty sample whose banned-face hits are the test payload, and
  two run-manifest shape templates for the i18n pipeline CLI face.
Interface.  Read-only data files; the suite copies them into temporary
  directories before any write-mode exercise; no fixture is written in place.
Dependencies.  tests/t_engines_body.py; seeds/ai_flavor/word-map.json and
  seeds/jargon/jargon-map.json supply the banned-face data at run time.
Evidence.  The own-register segment re-asserts on every run that the clean
  sample is clean, the dirty sample fires, and the manifest shapes parse.
Exit-codes.  Not executable; presence and shape are asserted by the suite
  (suite entry: 0 green, 1 red, 2 usage).

| file | role |
|---|---|
| `clean_sample.txt` | clean prose probe: zero battery hits, zero em-dash, ASCII only |
| `dirty_sample_en.txt` | polluted probe payload: English word-stem, sentence-face and paragraph-initial hits by design (`.txt` sits outside the five scanned extensions, so tree-mode scans stay silent; the suite reads it by explicit path) |
| `run_manifest_repo.json` | run-manifest shape template per the i18n SPEC section 9 (face `repo`, direction `zh2en`, refusal false) |
| `run_manifest_bad.json` | manifest missing required keys, for the fail-loud validation branch |
