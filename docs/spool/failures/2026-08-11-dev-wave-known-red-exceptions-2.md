---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-11
wave: dev-wave-known-red-exceptions
seq: 2
---

## 新規

### {{F:pseudo-skip-passes-as-green}}. 依存物ガードの疑似スキップと防壁配線欠落の skip が、受入全走を緑のまま素通りしていた [恒真ゲート] [テスト代表性]

- 事象: 静的全数走査で 4 箇所が見つかった。(1) `orchestrator/tests/test_calibrator.py` の
  F3 (計測前の単独性確認) 実プロセス番人 2 本が `pgrep` / `/proc` 不在時に早期 `return` で
  打ち切り、**pytest は正常 return を PASS に数える**。(2) `orchestrator/tests/test_hooks.py` の
  `test_settings_json_wires_all_hooks` が `.claude/settings.json` に `hooks` key が無いと skip し、
  第二防壁の配線が丸ごと消えた構成を受入が緑で通す。(3)
  `orchestrator/tests/test_dev_waves_isolation_contract.py` が conftest import 中の全 `ImportError` を
  「pytest 不在」と誤ラベルして skip。(4) `orchestrator/tests/test_p3_s4_loop_trigger_gating.py` の
  `_pinned_clean_sub_or_skip` が git の全例外を「submodule 未取得」の skip に化かす
  (呼び出し元 0 件の死んだ罠)。いずれも赤にならないため、受入全走の rc と件数からは見えない。
- 根本原因: 規約 (`orchestrator/tests/README.md` の「依存物不在時の skip (可視化)」= print + return の
  疑似スキップ禁止と、二重 runner 契約の Skip 分離計上) が**文章としてしか存在せず、機械検査が
  無かった**。(1) は同ファイルの `_run()` が `except Skip` を持たないため、規約どおり
  `skiputil.skip` を使うと素の runner で ERROR に化ける構造になっており、規約違反の方が
  「動く」状態だった。(2) は hooks 未配線時代 (D30 の over-claim 事件) の暫定 skip が、
  配線完了後も残った陳腐化である。
- 恒久対応: 4 箇所を修正し (疑似 return → `skiputil.skip`、`_run()` の Skip 計上、
  hooks key 欠落の assert failure 化、`ImportError` の `exc.name == "pytest"` 限定、死んだ helper の削除)、
  **巻き戻しを撃つ positive control を 2 本新設**した
  (`test_calibrator.py::test_competing_bench_pids_missing_dependency_is_visible_skip` と
  `test_hooks.py::test_settings_json_missing_hooks_is_assertion_failure`)。
  どちらも変異 matrix で kill されることを実測済み (M2 / M3)。
- 再発検知: 上記 2 本の positive control が、それぞれ「依存物不在が PASS に化ける」形と
  「防壁配線の欠落が skip で通る」形の巻き戻しを赤にする。族全体を撃つ meta 検査は、
  疑似 return の producer が 1 ファイルだけであるため `DW-G03` に従い作っていない
  (2 例目が出たら `test_plain_runner_coverage.py` へ寄せる)。
