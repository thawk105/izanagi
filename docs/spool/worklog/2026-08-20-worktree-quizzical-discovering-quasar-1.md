---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-20
wave: worktree-quizzical-discovering-quasar
seq: 1
title: 既知の赤 (test_spool_fold の real-corpus base-digest fixture 陳腐化) を修正した (テスト、commit 2b56f5ae)
---

## 本文

- ユーザー依頼「既知の赤を直す。テストが間違っていればテストを直す、テストされているところが
  間違っていたらそれを適切に直す。リワードハック禁止」を受け、事前に特定の T-番号は無い状態で
  開始した。`python3 tools/run_tests.py -q` の全体走を実測し (13769 passed, 96 skipped,
  **1 failed**)、赤は
  `orchestrator/tests/test_spool_fold.py::test_cli_base_digest_real_corpus_resolves_active_and_rejects_completed`
  の1件のみと確認した。
- 原因調査: `tools/spool_fold.py --base-digest` は worklog の carry chain (`### 次の一手` の
  `(N)` 参照) を遡って task_id の実質的な (非carry) 根 entry を見つけ、その本文の SHA256 を返す。
  対象テストは「現在アクティブな `[T-139]` の根 entry」を実 repo コーパスから独立に raw bytes で
  特定し、ハッシュを期待値と比較する独立オラクル設計 (D567 の base-digest 独立 loader 設計を踏襲)。
  テスト作成時点 (2026-08-13頃) は根 entry が `docs/archive/worklog-phase3-0813-537.md` の
  `- [T-139] **P1` ブロックだったが、2026-08-20 に `[T-139]` が実体更新され (D574 land、
  ordinal 720)、根 entry が `docs/archive/worklog-phase3-0820-720-721.md` の
  `- [T-139] **D574` ブロックへ移動していた。実装 (`_extract_latest_active`/`substantive_digest`)
  は無変更で正しく動作しており、原因はテスト側の fixture ポインタ陳腐化と確定した。
- 独立検証: 親 (Claude) が python3 で該当 archive ファイルを直接読み、新マーカーからの raw bytes
  SHA256 を独立に再計算し、実際の CLI 出力
  (`a0ac7de7b7a2def2a2f5480ecfbd5d87588fa926729fd940cbd644f4c0004f08`) と一致することを確認した
  (fixture へ「現在の出力」を機械的にコピーする迂回ではない、F27 との異同も確認済み — F27 は
  凍結成果物自体が壊れたのを fixture で隠蔽した事故だが、本件は凍結成果物は無傷で実装も正しい)。
- DW-M01 変異事前登録: `substantive_digest` の carry 判定 (`carry = carry_re.fullmatch(item.block)`)
  を `carry = None` に強制する変異 (carry-chain 解決の無効化、単一原因) を、fix 前に probe
  (`orchestrator/tests/test_spool_fold.py -k base_digest`、10件中3件赤化・7件無関係を確認、
  `git checkout --` で復元) → fix commit (`2b56f5ae`) 後に本走 (同じ結果、3 failed/7 passed、
  対象テストは今回はクリーンな baseline から KILLED、`git checkout --` で復元・commit と bytes
  一致確認)。KILLED 3件: 対象テスト自身、
  `test_cli_base_digest_resolves_mixed_carry_chain_across_ordinals`、
  `test_parallel_new_then_existing_update_uses_substantive_base_digest`。
- 段4裁定 (該当なし判定、DW-C00 軽量版): 設計択一なし・CC合成の正しさ防壁 (規律1-3) 非該当・
  受理集合不変のため、段2/3 (codex plan+敵対相談) と段6 review子は省略。段5 codex author
  (実装面のため親は直接編集せず) と変異matrixは省略不可のため実施した。
- 段5: Codex author (`gpt-5.6-luna`, `reasoning=max`, `sandbox=workspace-write`) へ、変更対象2行
  (ファイル名・開始マーカー文字列) だけを指定して投入。`## 総括` 付き完了報告、diff は指示どおり
  2行のみ (`check_codex_output.py` rc=0)。親が `git diff` で検収し一致を確認。
- 焦点走 (DW-O18/O26): `python3 tools/run_tests.py orchestrator/tests/test_spool_fold.py -q` =
  166 passed。`tools/check_ai_provenance.py` (full-history) = 4468件、新規違反なし。
- セッション異常は無し。

## 次の一手差分
