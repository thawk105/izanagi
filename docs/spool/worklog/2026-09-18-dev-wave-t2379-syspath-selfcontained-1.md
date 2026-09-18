---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-18
wave: dev-wave-t2379-syspath-selfcontained
seq: 1
title: [T-2379] test_s8b_approved.py / test_profiler_directive.py の sys.path 暗黙依存を自己完結にした — 対象 2 file だけの選択走が修正前 1 failed / 1 error → 修正後 69 passed、変異 3/3 事前登録どおり (コード 2 行 + docs、branch dev-wave-t2379-syspath-selfcontained、Codex author)
---

## 本文

- ユーザー依頼は「[T-2379] (P3、entry 1306、F982) `orchestrator/tests/test_s8b_approved.py` と `test_profiler_directive.py` が
  他 test module の sys.path 副作用へ暗黙依存しているのを直す — 対象 2 module の依存を自己完結にする局所修正に絞り、テスト基盤全体の
  再設計や collection 絞り込みの一般化へ広げない。単独選択走 (login) で偽赤を再現してから直し、修正後に単独選択と file 全体の両方で
  緑を示す。Codex author (D95) + 変異事前登録。起動時に対象 file を稼働 wave と照合する。着手直前の local main から fresh worktree
  を作る。規律 2 を緩めない。本題の局所修正だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」。
- **閉じた。** 一次資料は `output/insights/2026-09-18/t2379-syspath-selfcontained/README.md` (verbatim に author 報告・変異 spec と
  台帳・M-A 手動検証 log)。変更は各 file 1 行の import 置換だけ: `from tests.skiputil import` → `from orchestrator.tests.skiputil import`
  (test_s8b_approved.py:31)、`from codex_roles import policy` → `from orchestrator.codex_roles import policy` (test_profiler_directive.py:341)。
  sys.path の挿入は増やさず、検査の意味と受理集合は変えない。conftest / skiputil / production / runner / collection 絞り込み (D711 gate 2、
  D1707 の裁定待ち) は非接触。
- 修正前の実測 (段 1、計算ノードへ自動 dispatch): 対象 2 file だけの選択走 5501.nqsv は `1 failed / 58 passed / 1 error`
  (`test_s8b_approved.py` 収集時 `ModuleNotFoundError: No module named 'tests'`、`test_profiler_directive.py::
  test_derived_directive_is_accepted_by_the_role_policy_check` で `No module named 'codex_roles'`)。副作用の供給元は
  `test_campaign.py` / `test_campaign_import_invariant.py` / `test_reflux_ir.py` の `sys.path.insert(0, ORCHESTRATOR)`。login の直接 pytest は
  guard が拒否 (runner 経由が正規経路)。編集面照合 (210 branch tip + 208 作業ツリー): 対象 2 file と skiputil.py を触る稼働 wave は 0 件。
- **前提訂正:** 依頼文の「F982 の原因で、entry 1644 の焦点走 f1 でも再発」は一次資料と食い違う。F982 と entry 1644 の f1 (4932.nqsv) の赤は
  wrapper `test_real_repo_serialization.py` + conftest site 中立化 fixture の順序による WAL lock 不一致で、T-2379 (D1707、ModuleNotFoundError)
  とは別機構。両者は「狭い選択走の偽赤」の同族だが、本 wave は T-2379 だけを直し F982 は触らない (恒久対応「なし」は不変)。
- (P1) 修正形は `orchestrator.` 接頭の絶対 import を採った。代替の `from skiputil import` (他 20 file の形) は pytest の prepend
  import-mode に依存し file 自身の bootstrap で閉じない。先例は `test_s8b_protocol_builder.py` / `test_codex_agents.py`。
- 段 5: Codex author 1 本 (job-id s5-author-01、gpt-6-astra / medium、receipt accepted)。子の自己検査 = fresh process で IMPORT_PASS ×2 /
  DIRECT_CALL_PASS / 旧 import の DID_RAISE ×2、所有外差分なし。起動器の終端 commit 788433a50 から base 302b94796 基準の所有 path
  限定 patch を取り出し、統合 commit b0eea3720 (blob a19182bb5 / b44a01fae)。段 2・3・段 6 レビュー子は `DW-C00` の既定軽量版で省略
  (設計択一は (P1) のみ、正しさ防壁・受理集合に非接触)。
- 段 6 (修正後、同一 worktree の dispatch を 1 本の chain に直列化、11:35〜11:50 JST): 焦点走 (同じ 2 file 選択、5521.nqsv) **69 passed**。
  変異 matrix は事前登録 3/3 どおり — M-A (s8b の import を戻す、手動検証 5544.nqsv) は `59 passed, 1 error` で収集 ERROR 1 件のみ、
  復元後 blob == HEAD・tree clean; M-B (profiler の import を戻す、harness 5548.nqsv) **KILLED** で failed node は期待の 1 node と完全一致;
  M-C (等価コメント、5547.nqsv) **SURVIVED**。harness の collection 5545 / baseline 5546 PASSED、repo_head b0eea3720。M-A を harness に
  載せなかったのは形状が pytest collection error (file 単位、`FAILED ` 行なし) で `_failed_nodes` が抽出できないためで、独自手順は段 4 で
  事前登録した (`DW-M05`)。script は実装面なので repo へ入れず job dir に保全。
- provenance 全史監査 (実装 commit 後): 11,315 件、新規違反なし、rc=0。受入全走は land 経路で 1 走 (結果は land の受領証)。
- 段 8 (自己改善候補 2 件): (a) handoff に推定時刻を 2 箇所書いた (F1 型の near miss、docs へは入らず date 値で訂正) → routing 1 で
  F1 に再発追記 (専用 commit)。(b) `DW-O18` の「file選択走は`from tests import`確立後に限り未確立赤も偽赤」は本 wave 後に対象が消える
  (test file に `from tests.` 形は残らない) が、同節は exact literal pin と予算満杯 (D730) のため実施せず記録のみ。
- 工数: codex 子 1 本 (author)。親の実測: 選択走 2 本 (再現)、焦点走 1 本、M-A 手動 1 走、harness 3 走 + collection、provenance 監査 1 回、
  編集面照合 (210 branch / 208 worktree)。

## 次の一手差分

### 完了

- [T-2379] 2 file の import を `orchestrator.` 接頭の絶対 import に置換し、対象 2 file だけの選択走が緑 (5521.nqsv、69 passed)、変異 3/3
  事前登録どおり。F982 (wrapper / conftest) と collection 絞り込み (D1707 裁定待ち) は別項目のまま。
  remaining: none
  base: 9399e7fa7bd41b996211965d42e5f3223bdd6bae49c0a0962de130d8c15d99ef
