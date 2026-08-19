---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-20
wave: worktree-t1356-sort-closed-region-wiring
seq: 1
---

## 新規

### {{F:mutation-harness-collection-error}}. mutation_harness.py の node 抽出が pytest collection ERROR を扱えない [手順漏れ]

- 事象: [T-1356] で role-spec pin (review_ledger.py の SHA256、manifest.json の schema 値) を
  変異登録しようとしたところ、`tools/mutation_harness.py` が「rc=1 だが canonical stdout から
  failed node を確実に抽出できないため停止」「期待 node が pytest collection に実在しない」で
  2回 abort した (rc=2、作業ツリーは正しく復元、実害なし)。
- 根本原因: `tools/check_codex_agents.py:44` の
  `STATIC_ADAPTERS = frozenset(ROLE_SPEC.load_role_specs(REPO))` が module top-level で
  13 role 全部の pin を即時評価するため、`orchestrator/tests/test_codex_agents.py` を巻き込む
  role-spec pin drift 系の変異は、個別 `::test_name` ノードでなく `ERROR collecting <file>`
  という pytest collection error (ファイル全体1件、xdist worker数だけ重複表示) になる。
  harness の canonical node 抽出器は個別 test の `FAILED test::name` 行を前提としており、
  collection error 形状を扱わない (fail-closed で正しく abort、無理な推測はしない設計自体は
  正しい)。[T-1411] が踏んだ `ratified_enforcement_source` fixture の disk==HEAD blob 検査
  (`CONTRACT_LOADER_RELATIVE_PATHS` 経由) との harness 非互換と同系統 (harness の
  file-swap/node 前提と実際のテスト構造が噛み合わないパターンの2件目)。
- 恒久対応: memory `mutation-harness-collection-error-needs-manual-verify` —
  role-spec 系 pin 変異は Edit→`tools/run_tests.py`実走→単一原因のエラー文言確認→
  `git checkout --`復元、を手動で行う (T-1411 の代替手法と同型、DW-M05 の「独自harnessは
  同等の検査を備えると段4で事前登録する」に該当)。
- 再発検知: 次に role-spec pin 系の変異を harness へ登録しようとして同じ abort メッセージが
  出た時点で顕在化する (lint 化は未実装、目視)。

### {{F:mutation-harness-collection-truncation}}. mutation_harness.py の collect-only 出力が dispatch capture のバイト上限で切り詰まる [手順漏れ]

- 事象: [T-1356] で `test_auditor_gate.py`+`test_p3_s4_loop_trigger_gating.py`+
  `test_codex_agents.py` (計166 test) を1つの runner argv にまとめて変異登録したところ、
  期待した2 node のうち一部が「pytest collection に実在しない」と誤検出され harness が
  abort した (rc=2、作業ツリーは無害に復元)。52 test (2 file) に絞っても同じ誤検出が再現した。
- 根本原因: `_collect_expected_nodes` の `pytest --collect-only -q` 出力を Pegasus dispatch
  経由で取得する際、capture にバイト上限があり (実測: 166 test 分 18414 bytes 中
  14318 bytes が omitted、76%が切り詰め)、切り詰めがちょうど1行の途中で起きるとその行が
  nodeid として parse できなくなる。`test_auditor_gate.py` 分がまるごと消え、
  `test_codex_agents.py` 側も1行が先頭欠落で壊れていた。
- 恒久対応: memory `mutation-harness-collection-output-byte-cap` — 複数 file にまたがる変異は
  runner argv を file 全体でなく期待 node に対応する `file::test_name` 直接指定にする
  (対象 test 数を一桁〜十数個に抑える)。本 wave はこの対応で2件とも標準harnessで
  KILLED・matches_expectation=True を確定できた。
- 再発検知: 次に複数 file 合計60〜80 test 超を1つの runner argv にまとめて登録し、
  期待 node の一部が実在しないと誤検出された時点で顕在化する (lint 化は未実装、目視)。
