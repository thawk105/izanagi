---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-19
wave: dev-wave-t1411-single-process-claim
seq: 1
---

## 新規

### {{F:mutation-harness-contract-loader-incompat}}. mutation_harness.py が CONTRACT_LOADER_RELATIVE_PATHS 閉包メンバーを変異検査できない [手順漏れ]

- 事象: (2026-08-19、T-1411) `orchestrator/campaign/loop.py` への変異6件を
  `tools/mutation_harness.py --runner-mode dispatch` で走らせたところ、全6件が実際の変異検出に
  至る前に `status: MISMATCH`・`rc: 1` で停止した。ログには見積り行1行のみで、実体は
  `--out` の結果 JSON にのみ記録されていた。
- 根本原因: `orchestrator/campaign/loop.py` は `orchestrator/campaign/campaign_lock.py` の
  `CONTRACT_LOADER_RELATIVE_PATHS` (2026-08-18 commit `3fd9fd75` で25 pathへ拡張、本 wave の
  前日) に含まれる。harness は対象 file の disk bytes を一時的に書き換えて (HEAD とは乖離した
  ままコミットせずに) テストランナーを起動するが、`orchestrator/tests/conftest.py:139-180` の
  `ratified_enforcement_source` fixture (15+ test file で `pytestmark`/`usefixtures` により
  広く採用) はセットアップ時に無条件で
  `contract_loader_binding.capture_contract_loader_binding()` を呼び、閉包全 file の
  disk bytes と git HEAD blob の完全一致を要求する。両機構はそれぞれ正しく設計されているが、
  「変異検査は disk を一時的に HEAD から乖離させる」ことと「certified-writer 認可の対象 file
  closure は disk が HEAD と厳密一致していなければならない」ことが構造的に両立しない。
- 恒久対応: 未実施。本 wave は変異ごとに Edit → (hooks 有効のまま) `git commit` →
  `python3 tools/run_tests.py` 実走 → `git reset --hard <元 commit>` で復元、を6回繰り返す
  代替手法で検証した。一時 commit はいずれも canonical history へ残らない。詳細は
  `output/insights/2026-08-19_t1411-single-process-claim/mutation-spec.json` の
  `verification_method`/`observed_run` field。恒久対応 (harness 側に「対象 commit へ
  一時的に進めてから復元する」オプションを足す、または `ratified_enforcement_source` 側に
  変異検査 opt-out の正規 seam を作る、のいずれか) は別タスクの所有。
- 再発検知: `CONTRACT_LOADER_RELATIVE_PATHS` のメンバー (`env_contract.py`、
  `env_contract_activation.py`、`execution_guard.py`、`loop.py`、`pipeline.py`、`wal.py`、
  `ident.py`、`artifact_admission.py`、`orchestrator/verifier/*`、`s8c_preregistration*.py`、
  `s8c_generation_projection.py`、`campaign_lock.py`、`contract_loader_binding.py`、
  `enforcement_source_ratification.py` 等) のいずれかへ変異 matrix を登録する全 wave。
