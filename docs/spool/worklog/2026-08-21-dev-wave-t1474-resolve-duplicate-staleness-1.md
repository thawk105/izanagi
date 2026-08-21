---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-21
wave: dev-wave-t1474-resolve-duplicate-staleness
seq: 1
title: '[T-1474] _resolve_duplicate() が別 attempt の stale verdict を返す欠陥を修正した (コード+テスト、branch worktree-dev-wave-t1474-resolve-duplicate-staleness、変異matrix = baseline PASSED・M01/M02 2/2 KILLED・SURVIVED 0・MISMATCH 0)'
---

## 本文

- 起票時の owner 競合チェック: roster API が repo に存在しない (`find -iname "*roster*"` 0件) ため
  worktree/handoff 単独では非稼働と断定せず、`ps -ef`・稼働中 codex 2 プロセスの
  `/proc/<pid>/fd`・`dev-wave-jobs/` 全列挙・worklog/handoff grep を併用して T-1475/owner不明
  wave の非稼働を確認した。
- 段3 敵対相談 2 レンズ (sol=正しさ境界、luna=整合/scope) が、親 brief の provisional 記述
  「recovery は tail の interrupted attempt だけを見る」が不正確 (実際は全履歴の topology を
  検証するが、閉じる/復旧するのは tail の active attempt だけ) と独立に指摘し訂正した。
  reachability の結論 (real) 自体は変わらなかった。
- 段2 plan は commit 分岐だけに attempt-id 突き合わせを提案していたが、段3 lensA (正しさ境界) が
  abort 分岐 (`_resolve_duplicate()` の commit_payload is None 側) にも同型の stale verdict 混入
  余地があると独立に発見し、段4 裁定で修正範囲を commit/abort 両分岐へ対称的に拡張した
  (敵対検証が段2 plan の見落としを実際に検出した実例)。
- 段6 敵対レビュー B は初回、6件の実質的所見 (すべて refuted、defect なし) を出力したが
  `## 総括` 見出しを書き忘れ、launcher の形式検査 (`validator_rc=1`) で `outcome=not_accepted`
  となり `max_attempts=1` のため出力全体が不採用になった。プロンプトの見出し指示を強化して
  再投入し、同内容 (所見ゼロ、real な defect なし) を採用可能な形式で得た。
- 変異matrix本走 (`--runner-mode dispatch --force-dispatch`) の1回目は pytest collection dispatch
  の queue-wait-timeout (`rc=16`、実測 `qstat -Q gen_S` で QUE=53 の混雑) で中断した。
  `IZANAGI_DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE=3000` を設定して再投入し完走した
  (T-567/wave803 で踏んだのと同型のパターン、既知の対処)。
- DW-O26 焦点走 (production file `p3_s4_loop.py` を参照する13 consumer test file) で
  `test_sort_swo_oracle.py` の5件が赤だったが、`p3_s4_loop` の import が本文中で一度も
  参照されておらず (grep確認)、失敗内容も real oracle E2E の compiler/masstree 環境依存
  (`assert unavailable is False`) であり、diff が到達しえないことを file:line で確認して
  非帰属と判定した (DW-O18)。
- 段8 自己改善候補: DW-O01 (codex subprocess 起動) に「不採用時は artifact-root 配下の
  receipt.json で診断する」旨の1文追記を試みたが、`docs/dev-wave/**` の L1.5 unique footprint が
  既に予算超過寸前 (追記後 9872 bytes > 予算 9566 bytes) だったため見送り、revert した。
  次回 dev-wave docs 整理 wave での検討候補として記録するに留める。
- 既知の残存事項 (scope外・未解消): `out["records"][STAGE_VERIFY_DONE]["verdict"]` は
  修正後も生の (stale な) 値のまま返る — `_resolve_duplicate()` は top-level `verdict` だけを
  ガードし `records` はそのまま返す設計判断 (T-1475 の scope、今回は変更しない)。
  build_attempt_id が commit/abort・verify の両側で absent な pure legacy WAL は、今回のガードを
  すり抜けたまま (D637 が言う digest.py consumer 向け legacy fallback とは別の、
  `_resolve_duplicate()` 固有の既知残存リスク)。
- 一次資料: `/work/SFC/tanab/dev-wave-jobs/dev-wave-t1474-resolve-duplicate-staleness/handoff.md`
  (段1〜6 の裁定経緯全文)、同ディレクトリの `stage2-plan-output.md`/`stage3-lensA-output.md`/
  `stage3-lensB-output.md`/`stage6-reviewA-output.md`/`stage6-reviewB-output.md`
  (各段 codex 出力全文)、`mutation-spec.json`/`mutation-out.json` (変異事前登録と結果)。

## 次の一手差分

### 完了

- [T-1474] `_resolve_duplicate()` の commit/abort 両分岐に、終端 record の build_attempt_id と
  VERIFY_DONE の build_attempt_id を突き合わせるガードを対称的に実装し、attempt が不一致なら
  verdict を空文字にする最小修正を行った。direct test 3本を追加し、既存6テスト・alias共有
  テストを含む `test_p3_s4_loop.py` 全117件と DW-O26 焦点走 (13 consumer test file、
  非帰属赤5件を除き全緑) で実測した。変異matrix (M01: commit分岐guard無効化、M02: abort分岐
  guard無効化) は baseline PASSED・2/2 KILLED (単一理由一致)・SURVIVED 0・MISMATCH 0。
  remaining: none
  base: 6af26580c30ef54ba14364b03ce3574550b6752b2970ca9e35dcf8cb7be3887d
