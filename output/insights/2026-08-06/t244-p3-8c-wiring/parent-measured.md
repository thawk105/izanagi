# 段 1 前提実測 — dev-wave-t244-p3-8c-wiring

すべて本 wave が worktree `dev-wave-t244-p3-8c-wiring` (起点 local main `3143302b`、
submodule init 済み) で実測した。裁定時点の想定と食い違う点を含む。

## N1 — production authority は依然空

`orchestrator/campaign/reflux_origin_authority_v2.json` は
`{"authority_schema":"izanagi-reflux-origin-authority/v2","origins":[]}` の **71 bytes**。
U-10 (予算値) 未決のため entry を 1 件も書けない (D183)。
**帰結: 本 wave の wiring は production では origin 不在で発火しない。**

## N2 — ledger 公開 API は production store 固定

`read_origin` / `commit_event` / `read_sealed_batch` はいずれも本体先頭で
`_production_store()` を呼ぶ。`_production_store()` は `Path(__file__).parents[2]` を repo root にし、
module path が repo 内であることを再検査する。**caller が store を差し替える公開 seam は無い。**
非 production の唯一の seam は private `_fixture_store_for_test(temp_git_repo, ...)` で、
完全な一時 git repo を要求する (liveness wave と `test_reflux_origin_ledger.py` が使用)。

## N3 — reservation FSM は実装済み。caller 側は未実装

`2dc107ce` で `BatchReserved` / `BatchReservationAbandoned` が入り、
event 集合は `BatchReserved → BatchCommitted → BatchResultsPrepared → BatchSealed`
(+ `BatchReservationAbandoned` で `IDLE` へ戻る)、`OriginSealed` で origin を閉じる。
`_apply_event` の受理規則で実測した拘束:

- `BatchReserved` は `IDLE` 相からのみ。`iteration_index == iterations_used` と
  `query_ordinal_start == queries_used` の**連続性**を要求する。
- 予算消費は予約時点。`iterations_used += 1`、`queries_used += member_row_count`。
  `Imax` / `Qmax` 超過は予約時に拒否。`member_row_count` は
  `budget.batch_member_row_count_min` 以上、`_MAX_BATCH_MEMBER_ROW_COUNT = 2248` 以下。
- `BatchReservationAbandoned` は refund せず `forfeited_iterations` / `forfeited_queries` へ計上する。
- `BatchCommitted` は member 数が予約 `member_row_count` と一致し、query ordinal が
  `query_ordinal_start` から連続であることを要求する。さらに
  **candidate commitment は全 member で相異でなければならない**
  (`len({commitment}) != member_row_count` で拒否)。
  単一候補 × R replicate は salt が異なるため成立する。
- U-4 (`85fb97e1`) で count は `member_row_count` / `distinct_candidate_count` /
  `sealed_distinct_candidate_count` の 3 つ。`OriginSealed` 受理時に
  `BudgetPolicy.batch_distinct_candidate_count_min` (既定 1) を batch ごとに検査する。

**caller 側 (U-5 の (b) 成分) は repo 内に存在しない。** reservation FSM wave の brief (P4) が
「8c 結線 wave の担当」として明示的に本 wave へ返した項目である。

## N4 — 8c driver の生成ループの実順序

`p3_autonomous_workload_trial.py::_run_workload` の 1 generation は次の順である (実測)。

1. wall budget 検査 → `_common_payload` → `_whiteboard`
2. **planner** 呼出し (候補に影響する最初の role 呼出し)
3. **coder** 呼出し (候補 wire を産む)
4. `preview()` = machine pre-audit (`passed` / `forbidden_identifiers` / `diff_digest` / `working_diff`)
5. **auditor** 呼出し (pre-audit reject 時は skip し `uncertain` を合成)
6. proposal JSON を `run_root/proposals/<workload>.g<n>.json` へ書く
7. **`drive()`** = 実 harness 実行 (= oracle query 本体)。`outcome` を返す
8. Layer 3 admission (`require_admitted_campaign`) → critic identity projection → **critic** 呼出し
9. `stop_reason` 判定

早期 break は planner-invalid / coder-invalid / auditor-invalid / **critic-invalid** / wall-budget /
harness stop の **6 経路**。

> **erratum (段 3 レンズ A の指摘で親が訂正、2026-08-06):** 初版は critic-invalid を数え落として
> 「5 経路」と書いた。親が現物で確認して 6 経路に訂正した。critic は seal 後の位置にあたるため
> 段 4 の裁定 (実装しない) は変わらない。

## N5 — 注入 seam の既存 pattern

`_run_workload` は `drive` / `preview` を既に explicit keyword の注入 seam として持ち
(既定 = 実関数)、`run_trial()` は `claude-headless` provider のとき
`drive is not _DRIVE_NOT_PROVIDED` で **artifact 作成前に拒否**する
(`providers` も同様。D148 / [T-244] U-1)。テストは `_run_workload` を直接呼ぶ
(`test_p3_autonomous_workload_trial.py` の 5 箇所)。
**本 wave の ledger seam はこの既存 pattern と同型に置ける。**

## N6 — 事前登録の evidence contract が driver を pin している

`orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json` は
`p3_autonomous_workload_trial.py` を **bytes ではなく到達可能性 (reachability)** で pin する。
`main -> run_trial -> _run_workload -> _campaign_for` などの経路と
`_campaign_for.search_config.records` 等の field path を要求し、
`test_s8c_preregistration_predicates.py` が静的に検査する。
**帰結: `_run_workload` の改造は、この 3 経路を壊してはならない。**
一方 bytes pin (FROZEN_MANIFEST / generator source hash) は
`p3_autonomous_workload_trial.py` にも `reflux_origin_ledger.py` にも掛かっていない
(path 検索・key 検索とも hit 0)。`reflux_origin_ledger.py` の自己 path 参照は
`_production_store()` の repo 内性検査であって bytes pin ではない。

## N7 — pilot 限定の既存マーカー

`trial_registry.py` は `certifying: bool = False` / `arm_binding: str = "declared-only"` を既定に持ち、
`admission.certifying is not False` を
`[launch-admission] this wiring wave cannot issue certifying launches` で拒否する。
**pilot 限定は新設でなく既存の受理面である。**

## N8 — 生死は既取得

`output/insights/2026-08-05_t244-p3-liveness/` に、実 E driver の wire bytes を fixture store 上の
ledger が受理し、R=2 の replicate counter を更新し、seal 後に bytes を復元できることの receipt が
凍結されている。**`DW-G01` の生死実験は本 wave では繰り返さない。**

## N9 — 検査 baseline

`python3 tools/check_docs.py` = 違反なし (worktree 作成直後)。
`tools/check_wave_startup.py --external-handoff <handoff>` = rc=0 (submodule init 後)。

## N10 — 環境

login ノードで実行可能なのは静的検査と軽量 CLI のみ。pytest 全走・部分走は計算ノード
(runbook §7)。8c の `--provider fixture --no-build` は login で走る軽量経路である
(D106 の記録では YCSB A/B/C × 1 generation の fixture no-build が 3/3 dry-pass)。
