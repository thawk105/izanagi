# 段 1 brief — [T-2234] 予算保証の恒真化を直す

**wave:** `dev-wave-t2234-budget-vacuity` / branch `worktree-dev-wave-t2234-budget-vacuity`
**worktree:** `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2234-budget-vacuity`
**base:** local main `cc9bba523ac7804aadb7891d686bf4c925789a3f` (clean、submodule 初期化済み、
`tools/check_wave_startup.py --mode fresh` rc=0)

## 研究前進 (土台)

8c 事前登録 `docs/phase3-8c-preregistration.md` の §5 予算欄は「実 consumer (§6 の前提条件 6) が
揃うまで記入しない」を解除条件にしている。現行の予算 consumer は 6 cell すべての予約値が 0 でも
`held` を返すため、規範が要求する「実走前に停止する保証」を一度も発火させられない。恒真な consumer は
解除条件を満たさないので、この欄は埋まらず 8c 正式系列は事前登録を発効できない。最小差分は
`_check_limit_state` と `BudgetLimits` の 2 箇所である。

## 確定済みユーザー裁定 (command 引数)

- 本題の実装だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。
- 実装面は Codex `role=author` 必須 (D95)。親は実装面を直接編集しない。
- 規律 2 を緩めない。
- 恒真な保証は再発型なので、直したと主張する前に負例 (保証が実際に発火する入力) を足し、
  変異で殺せることを示す。

## scope と成果物影響 (DW-G05)

放置すると、8c 正式系列の予算台帳が「予約 0 = 予算確保済み」を受理し、`symmetric_indeterminate`
が空集合を返して 6 cell 全部が実走へ進む。実際の停止は最初の `settle` (実走後) まで起きない。
受理集合は**狭くなる方向にだけ**変わる (現在 `held` になる入力の一部が `insufficient` または
`BudgetError` になる)。広がる方向の変更は無い。

## 変更面 (実アンカー)

|path:line|現状|本 wave での扱い|
|---|---|---|
|`orchestrator/campaign/s8c_budget.py:517-531` `_check_limit_state`|3 層の「予約の和 ≤ 上限」だけ|予約の実在を判定へ足す|
|`orchestrator/campaign/s8c_budget.py:80-110` `BudgetLimits.__post_init__`|型・非負・coverage だけ|規範の 2 条件を検査|
|`orchestrator/tests/test_s8c_budget.py:51-75`|3 層別 witness param と held 正例|(P4) の裁定に従い調整|
|`orchestrator/tests/test_s8c_budget.py` 末尾|—|負例 4 種 + 規範適合の正例を追加|

## 不変条件 (壊してはならない)

1. C06 契約 `orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:230-266` の
   `path`・`entrypoints` (`reserve_all_cells`/`settle`/`symmetric_indeterminate`)・`field_paths`・
   `reachable_from`。
2. `orchestrator/campaign/s8c_preregistration_evidence.py:_evaluate_c06` (:3765-3800) が要求する
   関数名 `_check_limit_state`/`_ledger_lock` の実在と、`reserve_all_cells` からの呼び出し辺。
   D613 の再訪条件「同名の別 object を import または局所定義する」に触れない。
3. `orchestrator/tests/test_s8c_preregistration_predicates.py::test_repository_candidate_uses_real_s8c_budget_module`
   (約 13 秒) が緑のまま。
4. ledger schema `s8c-budget-ledger/v1` と `state` の値域 `{"held","insufficient"}` を増やさない。
5. 既存テストの期待値を弱める変更をしない (規律 2)。

## 段 1 で親が確認した実測

- **M1 (DW-O13):** `p3_autonomous_workload_trial._load_s8c_schedule_authority` (:2074-2079) は
  `del root` して無条件 raise。production の `limits`/`cells` は現時点で到達不能なので、規範を
  強制しても生きた経路を塞がない。規範適合値の実例は `docs/s8b-budget-approval-user-turn.md` の
  候補 (2592/1296/1296、2400/1200/1200) — どちらも arm 対称・holdout 和 = 総上限。
- **M2 (DW-O09):** `s8c_budget.py` の whole-file sha256
  `c06c7d3f5fb96d73a623a92aac21ccd8091fca87bc40e0ea8b0e9ff47a3c3949` を key にする pin は
  orchestrator / tools / docs / hooks に 0 件。path を key にする pin は不変条件 1・2 の 2 箇所のみ。
- **M3:** 実コードで `reserved_bench_s` に 0 を渡す呼び手は 0 件。唯一の `0.0` は
  `test_s8c_preregistration_predicates.py:4398` で、これは predicate 評価器へ渡す decoy module の
  source 文字列の中であり実呼び出しではない。
- **M4:** 編集面 2 file を変更している branch tip・未 commit worktree は 0 件 (184 worktree 走査)。

## 割れうる前提 (親の provisional 裁定・段 2/3 の攻撃対象)

- **(P1)** 規範違反の limits (arm 非対称 / holdout 上限の和 ≠ 総上限) は `BudgetError` で拒否する。
  `insufficient` にしない — これは「予算不足」ではなく「入力が規範に反する」であり、
  `symmetric_indeterminate` の理由コード (`budget-insufficient`) を誤らせるため。
- **(P2)** 予約値が 0 の cell が 1 つでもあれば `held` にせず `insufficient` にする。新しい状態も
  新しい gate も足さず、既存の `symmetric_indeterminate` で実走前に対称停止させる (規律 5)。
- **(P3)** 規範の 2 条件は `BudgetLimits.__post_init__` へ置く。`_ledger_from_raw` の読み戻しも
  同じ型を通るので、手編集した台帳も同じ関門で塞がる。
- **(P4)** (P3) を採ると holdout 上限の和 = 総上限になるため、「総上限だけが不足」の witness は
  許容差 `_TOLERANCE`=1e-9 の帯の外では構成できない (holdout 上限の和 = 総上限なので、総和が
  総上限を超えればどれかの holdout も必ず超える)。
  `test_each_budget_layer_has_a_numeric_insufficient_witness[total]` の扱いを段 2 に提案させ、
  段 4 で裁定する。**既存テストの主張を弱める形は採らない。**

## 成果物の形

実装差分 2 file、負例 4 種以上 (全 cell 0 / 1 cell だけ 0 / arm 非対称 / holdout 和不一致) と
規範適合の正例 1 本、変異 matrix (新検査ごとに KILLED)、worklog・decisions の spool fragment、
`output/insights/` の逐語。

## 分割方針

実装面は 1 単位 (2 file が同一 module 契約を共有するため分けない)、Codex `author` 1 本。
段 3 は 2 レンズ並列 (レンズ A: 受理集合と規律 2 / レンズ B: 契約 pin と恒真化の再発)。
段 6 はレビュー 2 本 + fix 1 本。
