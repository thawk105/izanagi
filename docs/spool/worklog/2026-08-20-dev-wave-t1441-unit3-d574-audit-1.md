---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-20
wave: dev-wave-t1441-unit3-d574-audit
seq: 1
title: '[T-1441] 単位3のB1実装をD574決定(3)へ適合させた (コード+テスト、branch worktree-dev-wave-t1441-unit3-d574-audit、変異matrix = baseline PASSED・2/2 KILLED・SURVIVED 0・MISMATCH 0)'
---

## 本文

- 2026-08-20ユーザー裁定Q-B=択(a) (一次資料
  `output/insights/2026-08-20_t338-unit5-d574-conflict/package.md`) に従い、T-338単位3
  (`_semantic_validator.py`、entry724で本日land済み) のB1実装がD574決定(3)を満たすか監査した。
  親の直接調査・段2 read-only codex独立監査・段3敵対相談2レンズの三重検証により、
  compile_commands脚が実CCBenchの出力macro名 (`TRACE`/`ADD_ANALYSIS`) と一致しない
  `CCBENCH_TRACE`/`CCBENCH_ADD_ANALYSIS` を検索する実装バグを発見。正当な受領証を含め常に
  拒否する状態だった。詳細は `output/insights/2026-08-20_t1441-unit3-d574-audit/package.md`。
- 段2 codex plan (real所見: `ReceiptSchema.__post_init__`のdocument再ハッシュ欠如、production
  caller 0件で今回は対応不要)。段3レンズB (real所見: correctness_evidence空配列による
  correctness側検査未実行の経路、D574(3)自体の欠陥ではないと親裁定)、段3レンズA (real所見:
  macro名不一致、決定的)。段6敵対レビュー2本は real所見なし。
- 変異matrix: `tools/mutation_worktree.py` (固定commit使い捨てworktree) で本走。2件事前登録
  (M1: compile_commands脚TRACE macro名revert、M2: 同ADD_ANALYSIS macro名revert)。baseline
  PASSED (39 passed)、2/2 KILLED、SURVIVED 0、MISMATCH 0、TIMEOUT 0。各変異の失敗nodeは
  事前登録した6件と完全一致、単一理由性を実測確認。
- **セッション異常: 段5実装子1回目の試行が`## 総括`見出し欠落でcheck_codex_output.py rc=1
  (not_accepted) になった。** 実装内容自体 (差分) は正確だったため、親が直接diff・実走
  (39 passed) で検証し、`## 総括`付き確認のみの2回目試行で正式採用した。実装のやり直しは不要。
- **セッション異常: 段6後のM1単独probe (一時変異) 時、`python3 tools/run_tests.py`のPegasus
  dispatchがtimeout (300秒) し、request 927195.nqsvがorphan hold (state-not-cancellable) と
  なった。** 手動qdelはせず (F47 submission-disabled.json武装回避)、`qstat -f`で終端 (does not
  exist) を確認してから復旧。tracked file (`_semantic_validator.py`) は`git diff HEAD`で
  byte一致を確認して復元済み。M1単独のexpected_nodesはコード構造 (各macroチェックが独立した
  if文で`_macro_value`が値欠落時に即座に例外) からM1+M2同時と同一と判断し、正式な変異matrix
  本走 (`--runner-mode dispatch --force-dispatch --detached`) でM1単独の結果も含め実測確認した。
- エージェント工数: 段2 codex plan 1本、段3敵対相談2本、段5並列author 2本 (1回目`## 総括`欠落で
  not_accepted、2回目確認のみでaccepted)、段6敵対レビュー2本、変異harness本走1回
  (baseline+2件、全KILLED)。

## 次の一手差分

### 完了

- [T-1441] B1実装 (`_validate_compile_legs`) のcompile_commands脚macro名をCCBench実出力へ
  修正し、D574決定(3)を満たす状態にした。段6レビュー・変異matrix・受入全走で検証済み。
  remaining: none
  base: 16ebf777e80550e8f7e271532d2c8b3c03ad8b683cbab9a0b963ce25b650227e

### 新規

- {{T:correctness-evidence-min-items-gap}} **P2・新規**: `receipt-schema-v1.json`の
  `correctness_evidence.minItems:0` (§7.1(1)の失敗stage許容) により、B1のcorrectness側三者
  比較 (trace=1/analysis=1) が一度も実行されない受領証が成立しうる。D574決定(3)自体の欠陥では
  ないが (段3レンズA=refuted、レンズB=real、親裁定はレンズA採用)、単位5/6着手時に
  「validatorが存在するcorrectness compile recordを常に検査する」という実効性の限定として
  確認すること。一次資料: `output/insights/2026-08-20_t1441-unit3-d574-audit/package.md`
  副次的所見1。
- {{T:receipt-schema-document-rehash}} **P2・新規**: `_receipt_schema.py:34-43`の
  `ReceiptSchema.__post_init__`がdocumentの再ハッシュをせず、同一ref/sha256で偽documentを
  直接渡す構築が理論上可能 (production callerは現状0件、段2 codex plan・段3レンズA・親の
  3者独立grepで確認済み)。単位6でtop-level API配線時にhardeningを検討すること。一次資料:
  同上、副次的所見2。
