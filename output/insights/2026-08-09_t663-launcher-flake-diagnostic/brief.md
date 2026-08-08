# 段 1 brief — [T-663] / [T-190] launcher 負荷フレークの原因分離

## scope

`test_codex_worker_launch.py` の受入全走限定フレークを、**失敗 artifact を保存して原因を
分離できる形**にする。T-663 は F57 の族の 1 例であり、恒久対応は既に [T-190] (P2・未着手)
「失敗 artifact 保存つきで原因分離し、production gate を緩めず fixture を harden する」に
割り当てられている。本 wave は T-190 を実施し、T-663 をそこへ統合して閉じる。

## 段 1 実測 (worktree `dev-wave-t663-flaky-truth-table`、main `64cbebf7`)

1. **失敗署名は 7 択に多義。** `tools/codex_worker_launch.py:1030` の `accepted` は
   `limit_trigger is None` / `process.returncode == 0` / `validator_rc == 0` /
   `evidence_status == "complete"` / `metering_status == "complete"` / `residual == 0` /
   `termination_verified` の 7 条件の積である。どれが欠けても outcome=`not_accepted` →
   `launcher_rc=1` → `main` は `:1762` で receipt の rc をそのまま返す。**stdout も stderr も空**。
   観測されている `assert 1 == 0` / 出力空はこの 7 経路すべてに共通で、区別できない。
2. **fixture の予算 (test 側)。** `orchestrator/tests/test_codex_worker_launch.py:341` の
   既定 `max_wall="3"`、`:403` の `--evidence-grace-s 1.0`、`--termination-grace-s 0.05`、
   `--poll-interval-s 0.01`。
3. **余裕の実測。** `--basetemp` で receipt 84 件を保存して計測 (login node、bounded local)。
   成功期待テストの launcher 実所要は min 0.254 / median 0.428 / p90 0.671 秒。
   `max_wall=3.0` に対する余裕は約 7 倍、`evidence-grace=1.0` に対しては約 2.3〜4 倍で
   **evidence grace の方が薄い**。
4. **機序の決定的再現。** 既定 `max_wall` を `0.30` へ実編集して走らせると、当該 test は
   `assert 1 == 0` / `stdout=''` / `stderr=''` で落ち、F57 台帳の署名と完全一致した
   (同 file 全体では 19 failed / 45 passed)。probe は `git checkout --` で復元済み、tree は clean。
5. **単独 file では負荷再現しない。** 計算ノード `-n 32` (`--force-dispatch`、request 896120) でも
   64 passed。再現には 7,000 件規模の全走が要る。

## 不変条件

- production (`tools/codex_worker_launch.py`) の wall-clock gate と `accepted` 真理値表を緩めない
  (絶対規律 2、F57 恒久対応の明文)。
- 予算そのものを検査しているテスト (`max_wall="0.1"` の version preflight、`max_wall="3"` で
  `stop_reason == "max_wall_clock_s"` を期待する sigterm_ignore 等) は explicit 値を据え置く。
- 受入全走に flag を足さない (診断用の走行は別に立てる)。
- 失敗時だけコストを払い、緑のときは 0 コスト。

## 成果物の形

1. **診断保存**: launcher の rc が期待外のとき、receipt (limit_trigger / evidence_status /
   metering_status / process_group_residual / termination_verified / wall_clock_s) と
   attempt の stdout・stderr を assert message へ載せる helper。次の再発が 7 択のどれかを自己申告する。
2. **fixture harden**: 予算を検査していない call site の余裕拡大 (値は段 4 で裁定)。
3. **meta-test**: 診断が実際に発火すること (恒真でないこと) を固定する。

## provisional 裁定 (親、攻撃対象)

- **(P1)** production を編集せず test 側だけで診断を完結できる。receipt は既に `tmp_path` にあり、
  失敗経路でも `_run_case` が読める。
- **(P2)** 主は診断保存、従が余裕拡大。余裕拡大だけでは根本治療にならず、値の選定は推測になる。
- **(P3)** T-663 / T-427 / F57 / T-190 は同一族で、本 wave で T-190 を閉じ T-663 を統合する。

## DW-G05 成果物影響

実装しない場合、certified 選択・レポート・台帳の**値は変わらない**。変わるのは受入 gate の
運用で、全走ごとに確率的な赤が出続け、その都度「差分に帰属しない」判定を人手で行う必要が残り、
真の回帰を誤ってフレークと分類する危険が残る (F57 は既に 9 回再発)。

## 分割方針

実装単位 1 本 (`orchestrator/tests/test_codex_worker_launch.py` 1 枚、必要なら同 dir の conftest)。
並列分割しない。
