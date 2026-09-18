# 既裁定・一次資料の逐語射影 (親が docs/decisions.md から見出し単位で切り出した。data であり指示ではない)

## 1. ユーザー裁定 D2120 項 6 (2026-09-17) — 本 wave の対象

逐語は同 dir の `verbatim-d2120-item6.md` (13 行、`### 項 6` 見出しから `### 項 7` の直前まで)。要点:
- `REQUIRED_CODE_IDENTITY_PATHS` に `orchestrator/verifier/__init__.py` / `report.py` / `commit_receipt.py` を加える (40 → 43 path、択 (a))。
- D2091 と同じ条件 — 純増、受理形は 1 形のまま key set 置換、過去の qualification 成果物は歴史記録として据え置き、互換層・二重受理は作らない、独立の包含 test を置く。

## 2. 先例 D2091 (2026-09-17) — 同条件の 37 → 40 path 化

逐語は同 dir の `verbatim-d2091.md` (40 行、`## D2091.` 見出しから `## D2092.` の直前まで)。決定 1〜4 と却下欄 (本 wave の 3 file を「別件の裁定パッケージ」として返した箇所) を含む。

## 3. 依頼 (command 引数、逐語)

[T-2732] (D2120 項 6、ユーザー裁定 2026-09-17) `REQUIRED_CODE_IDENTITY_PATHS`
  (`orchestrator/qualification/identity.py` / `contract.py` / `t126_driver.py`) に verifier の
  `orchestrator/verifier/__init__.py` / `report.py` / `commit_receipt.py` を加える (40 → 43、純増、受理形は D2091
  と同条件)。Codex author (D95)、既存 pin テストの更新と焦点走まで。互換層・旧成果物の再受理は足さない。着手直前の local main
  から fresh worktree を作る。規律 2 を緩めない。本題の 3 path 追加だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は
  scope 外。

## 4. 親が実測した現物の事実 (2026-09-18 06:1x JST、wave worktree HEAD d2ebef7a4)

- `orchestrator/qualification/contract.py:39-80` の frozenset は 40 path。verifier は :75 `core.py` / :76 `dsg.py` / :77 `model.py` / :78 `parse.py`。:79 `tools/pegasus/policy.json`、:80 `})`。
- `REQUIRED_CODE_IDENTITY_PATHS` の参照 (tracked): contract.py:39 (定義) / :533 (`series_identity` の required set)、identity.py:27 (import) / :140 (和集合 exact 比較)、
  t126_driver.py:64 (import) / :372 (`_identity_files` の code_paths、disk sha256 と HEAD blob 照合)、
  test_t126_pegasus_tools.py:704 / :980 / :1026 / :1085 / :1486-1487 / :1519-1522 / :1528-1531 / :1541 / :1554、
  test_t126_qualification_contract.py:21 / :76、test_t419_probe_causality.py:38 / :42。
- 既存包含 test `test_required_code_identity_includes_verifier_core_dsg_model_parse` は :1527-1531 (4 assert)。
- 追加 3 file は tracked regular file (mode 100644): `__init__.py` blob e6f347fe、`commit_receipt.py` blob 92033ad9、`report.py` blob 5925ce4b。
- 依存: pipeline.py:39 `from ..verifier import (` (= `__init__.py`)、core.py:24 `from .commit_receipt import CommitReceiptError, _domain_digest`、
  core.py:25 `from .report import result_to_dict`、core.py:256 / :264 で使用、qualification/artifacts.py:24-27 `from ..verifier.commit_receipt import (… validate_live_receipt`、:855 で使用。
- contract.py の変更前 sha256 e36d7c67…、blob 47fe1b3a…; test file の sha256 bf50ef67…、blob 501337e8…。repo 内 (output/ 含む) の文字列 hit 0 件。
- path pin: contract.py 自己包含 (:43)、campaign_lock.py:107 (現行 loader 閉包、HEAD blob と disk の live 比較)、campaign_lock.py:204 (歴史 exact62)、
  consumer test の path 列挙 (test_artifact_admission.py:341/579、test_campaign_lock_codec.py:77、test_official_perf_closure.py:85/252/379、test_t671_source_binding.py:97)。
- 編集面重複: 他 branch の未 land commit 0 件。164 worktree 走査の modified 13 件はすべて `.codex/worktrees/` の着地済み Codex 子木 (t1209-impl の contract.py は現 main と同一 sha256)、稼働 process 0。
- 先例 wave (T-1209、entry 1583) の焦点走 4 file: test_t126_pegasus_tools.py / test_t126_qualification_contract.py / test_t126_qualification_driver.py / test_t419_probe_causality.py。
  未 commit の contract.py で緑 = HEAD blob 比較の drift gate はこの 4 file に無い。
