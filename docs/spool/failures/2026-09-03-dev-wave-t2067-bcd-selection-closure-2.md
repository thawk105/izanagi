---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-03
wave: dev-wave-t2067-bcd-selection-closure
seq: 2
---

## 新規

### {{F:focus-set-only-red}}. 焦点走の file 集合を広げたときだけ大量の赤が出て、全走では再現しなかった [テスト代表性]

- 事象: 段 6 の焦点走で `test_s8b_ratified_verify.py` / `test_s8b_oracle_manifest.py` /
  `test_s8b_oracle_report.py` / `test_s8b_oracle_driver.py` の 4 file を 1 集合で走らせたところ、
  10% 到達時点で赤が 20 件を超えた。同じ worktree・同じ未 commit 差分のまま分割して走らせると、
  `test_s8b_ratified_verify.py` 単独 189 passed、`test_s8b_oracle_manifest.py` 単独 107 passed、
  `test_s8b_oracle_report.py` + `test_s8b_oracle_driver.py` 395 passed / 6 skipped で**赤 0 件**。
  最終的に全走 (正規の走行構成) を回すと、実装起因の赤は 0 件だった
  (唯一の赤は未 commit 差分そのものを検出する
  `test_p3_b4_wiring_probe.py::test_source_and_test_are_the_only_non_output_worktree_changes` で、
  統合 commit 後に自動解消する性質のもの)。
- 根本原因: 焦点走の file 集合は正規の走行構成ではない。集合の作り方によって worker への
  分配とテスト間の相互作用が変わり、実装と無関係な赤が出る。親は赤を見た時点で実装起因を疑い、
  原因特定に 40 分以上を費やした。pytest が失敗本文を最後にしか出さないため、
  進行中の出力からは赤の node 名すら取れず、切り分けが遅れた。
- 恒久対応: `docs/dev-wave/operations.md` の `DW-O26` は「単独緑は file 集合走行での緑を含意しない」と
  一方向だけを書いている。**逆向き (集合走の赤が実装起因とは限らない) も同時に成り立ち、
  帰属の判定は正規の走行構成 (全走) でしか行えない。** 焦点走で赤が出たら、
  (1) `-x` で単独走して失敗本文を取る、(2) file を分割して単独緑を確認する、
  (3) 全走で帰属を確定する、の順に進める。集合走の赤だけを根拠に実装へ fix を当てない。
- 再発検知: 焦点走と全走の赤件数が食い違ったときに本エントリを引く (目視。lint 化は未実装)。
