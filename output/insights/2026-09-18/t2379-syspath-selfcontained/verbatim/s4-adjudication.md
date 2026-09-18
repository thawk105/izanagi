# 段 4 裁定 — [T-2379] (段 2・3 は DW-C00 の軽量版で省略)

- 裁定 inbox 再走査: `/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/` に T-2379 を変える更新なし (hit は 2026-08-16 の別 driver)。
- (P1) 採用: `orchestrator.` 接頭の絶対 import。理由は brief のとおり (file 自身の ROOT 挿入で閉じる、先例あり)。
- scope 確定: 2 行の import 修正のみ。docstring・他行は触らない。DW-G05: 放置時に変わるのは焦点走・変異 baseline の
  偽赤 (wall 空費) であり、certified 選択・レポート・台帳の値は変わらない → 局所修正、追加防壁なし。

## 実装方向 (plan v2、逐語)

実装子 1 本 (Codex author) が次の 2 行を置換する。他の行・順序・comment・docstring は変えない。

1. `orchestrator/tests/test_s8b_approved.py` 31 行目
   - 現行: `from tests.skiputil import Skip, skip  # noqa: E402`
   - 変更後: `from orchestrator.tests.skiputil import Skip, skip  # noqa: E402`
2. `orchestrator/tests/test_profiler_directive.py` 341 行目 (関数 `test_derived_directive_is_accepted_by_the_role_policy_check` の本体先頭、4 space indent)
   - 現行: `    from codex_roles import policy  # noqa: PLC0415`
   - 変更後: `    from orchestrator.codex_roles import policy  # noqa: PLC0415`

受理・拒否の含意: 変えるのは import の解決経路だけ。変更前は `orchestrator/` が sys.path に無い (他 module が同じ process で
先に import されていない) 狭い選択走で `ModuleNotFoundError` になり、変更後は file 自身の `sys.path.insert(0, ROOT)` だけで
解決する。検査の意味 (policy の関数・Skip/skip) は同一で、受理集合は変わらない。通る正例 = 対象 2 file だけの選択走が緑。

## 変異事前登録 (DW-M01、実装前)

runner 選択 = 対象 2 file だけ (`orchestrator/tests/test_s8b_approved.py` `orchestrator/tests/test_profiler_directive.py`)、
baseline は修正後の同選択で緑必須。

- M-A (negative): `test_s8b_approved.py` の import 行を `from tests.skiputil import Skip, skip  # noqa: E402` へ戻す。
  期待 = 同選択で file 全体が収集 ERROR (`ModuleNotFoundError: No module named 'tests'`、単一理由)。形状が collection error で
  標準 harness (`_failed_nodes` は `FAILED ` 行のみ抽出、tools/mutation_harness.py:1253) に登録不能 → 手動検証
  (Edit → 同選択 run_tests → 単一原因の error 文言確認 → `git checkout --` 復元 → HEAD blob 照合、DW-O19)。
  記録: request ID・digest 行・復元後の blob sha を job dir → insight へ。
- M-B (negative): `test_profiler_directive.py:341` を `    from codex_roles import policy  # noqa: PLC0415` へ戻す。
  期待 KILLED = `orchestrator/tests/test_profiler_directive.py::test_derived_directive_is_accepted_by_the_role_policy_check`
  (単一 node、`No module named 'codex_roles'`)。標準 harness に登録。
- M-C (positive、等価、SURVIVED 期待、expected_nodes 空): `test_profiler_directive.py:341` の行末コメント
  `# noqa: PLC0415` を `# noqa: PLC0415  # equivalent-mutation` に変える (実行 bytecode 不変)。harness の SURVIVED 検出の正例。
- 単一理由性 (F820): M-A / M-B の赤は各 1 つの ModuleNotFoundError で、前後・内側に同じ入力を拒否する層は無い
  (段 1 の実測 5501.nqsv で同形を観測済み)。

## 前提訂正 (段 5 後に一次資料で判明、実装方向は不変)

依頼文は「F982 の原因で、entry 1644 の焦点走 f1 でも再発」と書くが、一次資料は次のとおり:
- F982 (`docs/failures.md`) の機構は `test_real_repo_serialization.py` の wrapper が実行中に `test_p3_s4_loop` を import し、
  conftest の site 中立化 fixture が setup 時点で `sys.modules` に無い module を差し替えないこと。赤は WAL lock の JSON 不一致。
- entry 1644 (`docs/archive/worklog-phase3-0918-1644.md`) の f1 (request 4932.nqsv) の赤も同じ WAL lock 不一致 = F982 の署名。
- T-2379 (D1707、entry 1306) は `test_s8b_approved.py` / `test_profiler_directive.py` の `orchestrator/` sys.path 暗黙依存で、
  赤は `ModuleNotFoundError` (本 wave の 5501.nqsv で実測)。
両者は「狭い選択走の偽赤」の同族だが機構は別。本 wave は T-2379 を直し、F982 (wrapper / conftest) は触らない (scope 外、
依頼の「本題の局所修正だけ」に従う)。F982 の「恒久対応: なし」は本 wave で変わらない。

## 受入・焦点走

受入全走は免除しない (land 経路で 1 走)。焦点走 = 対象 2 file 選択 (修正後緑の主張)。DW-O26 の consumer 拡張: test file
しか変えないので production consumer は無し。`test_campaign_import_invariant.py` は campaign 配下の source を走査する検査で
test file の import 形は対象外。「file 全体」の緑は受入全走で示す。
