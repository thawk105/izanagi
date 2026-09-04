---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-04
wave: dev-wave-a2-reject-results-section
seq: 1
---

## 再発

### F42

- **再発: 2026-09-04** — wave dev-wave-a2-reject-results-section で発生。新設した `orchestrator/tests/test_plot_a2_certification.py` が
  自走 harness も allowlist 記載も持たず、受入全走 1 回目 (20420 passed / 68 skipped) を `test_plain_runner_coverage.py` の 1 件赤にした。
  実装子 prompt には DW-S05-C の F42 由来の指示を逐語で入れ、実装子は F42 の検索で `test_pytest_collection_config.py` を見つけて通したが、
  `test_plain_runner_coverage.py` は洗い出しから漏れた。親の焦点走 2 回 (新 test file + collection meta-test) も横断メタ検査を含めていなかった
  (2026-08-11 の再発と同じ degrade 経路)。fix 子 2 本目が `__main__` + `pytest.main` の 4 行を足し、焦点走 (meta-test + 新 test、26 件) の後に閉じた。
  費用は受入全走 1 回分 + fix 子 1 本 + 焦点走 1 回。**新設 test file がある wave では、親の焦点走の集合に `test_plain_runner_coverage.py` を必ず入れる**
  (2026-08-11 の恒久対応の逐語を親が守らなかった再発)。
