# 段 1 前提実測 — dev-wave-t244-u10-draft

すべて本 wave が worktree `dev-wave-t244-u10-draft` (起点 local main `5a322447`) で実測した。
裁定要約でなく decision 本文とコード現物を根拠にする (F31/F1)。

## N1 — 本番 authority は依然 entry 0 件 (真)

`orchestrator/campaign/reflux_origin_authority_v2.json` は
`{"authority_schema":"izanagi-reflux-origin-authority/v2","origins":[]}` の **71 bytes**。
本 wave は起草のみで、この bytes を 1 byte も変えない (D183 / D147 決定 4)。

## N2 — codec 定数の現物値 (真)

`orchestrator/campaign/reflux_origin_ledger.py`:

- `_MAX_BATCH_MEMBER_ROW_COUNT = 2248` (85–102 行の定数群)。これが 1 batch の member 行数上限
  であり、s2-plan §1.3 の \(C_{\text{codec}}\) にあたる。
- `_JSON_SHA_MEMBER_BYTES = 67`、`_MAX_RECORD_BYTES = 1 << 20` から
  `_MAX_CLASS_CARDINALITY = (1048576 - 1) // 67 = 15650`。これが \(K_{\text{codec}}\)。
- `_MAX_LEDGER_BYTES = 64 << 20` (= 67,108,864)。origin stream と head stream の各上限。
- `_MAX_AUTHORITY_BYTES = 8 << 20`。

## N3 — parser が課す hard 制約 (真)

`_budget_from_object` / `_floor_from_object` / `_check_budget_codec_feasibility` の実測。

- `batch_member_row_count_min` は **minimum=2**。したがって \(B_{\min} \ge 2\) は選択でなく
  parser の下限であり、値案が 1 を提案する余地は無い。
- `batch_distinct_candidate_count_min` は minimum=1 かつ `<= batch_member_row_count_min`。
- `imax`、`qmax` は minimum=1。`kmax` に明示 minimum は無い。
- floor は `queries_per_round >= 1`、`rounds >= 1`。
  \(F = \text{base} + \text{qpr} \times \text{rounds} + \text{evidence\_min}\) が
  \(\max(2, B_{\min}) \le F \le Q_{\max}\) を満たさなければ parse で拒否。
- floor 群は canonical 昇順・重複禁止。`formula_id` は既知 1 種のみ。
- `Qmax <= Imax * 2248`、
  `ceil(maxF / 2248) <= min(Imax, Qmax // max(Bmin, candidate_min))`、
  `Kmax <= 15650`。
- 最終段で `origin_bytes <= 64MiB` かつ `head_bytes <= 64MiB` を実バイト直列化で検査する
  (`_affine_batch_bytes` は `batches = min(Imax, Qmax // effective_row_min)`、
  `members = Qmax` で見積る)。**この 2 本だけは閉形式でなく実行検査**である。

## N4 — D189 の予算消費点は予約時 (真)

`BatchReserved` 受理で `iterations_used += 1` / `queries_used += member_row_count`。
`Imax` / `Qmax` 超過は予約時に拒否。放棄は返却せず `forfeited_*` へ計上。
したがって「課金される query」は**予約した member 行数**であって物理 provider query 数ではない
(D166 決定 5 の限定を継承)。

## N5 — 8c 側の物理定数 (真)

`orchestrator/campaign/p3_autonomous_workload_trial.py`:

- `MAX_GENERATIONS = 10` だが `MAX_APPROVED_GENERATIONS = 1` (D114 上限 1 不変)。
  現に走らせられるのは **1 origin あたり 1 generation = 1 drive**。
- `_perf_for`: `records=100_000`、`threads=4`、`extime=1`、**`reps=2`**。
- workload は ycsb-a / b / c の 3 種 (= 3 cell)。

`orchestrator/campaign/pipeline.py:300,470` の `bench_max_rounds: int = 3`、
`orchestrator/calibrator/stability.py`: `DEFAULT_REMEASURE_ROUNDS = 3`。
`remeasure_until_stable` は **1 round = `measure_fn()` 1 回 = reps 反復を内包した 1 測定点**で、
CV が閾値以下なら打ち切り、最大 3 round。

→ **入力 6「1 round の物理 replicate 数」= 2、入力 7「自動再測定 round の最大数」= 3 が現行実装値**である。
値案はこの現行値と一致させるか、変更なら理由を要する。

## N6 — 二つの「R」が同名で衝突している (新事実)

s2-plan §1.3 の floor tuple は \(F = B_0 + q_{\text{round}} \times R + E_{\min}\) と書き、
この \(R\) は parser の `rounds` (= 測定 round 数) に対応する。
一方 8c V-3 の \(R\) は「同一 wire を R 回測る」member 行数 (= `member_row_count`) である。
**両者は別量で、値も一致する必然が無い。** 同名のまま authority へ載せると D75 の二義化になる。
値案では `R_rounds` / `R_replicates` へ改名して提示する必要がある。

## N7 — T-564 の新較正は publish 済みだが未活性 (真)

`output/env/pegasus/calibration/registered/` に
`calibration-753f535a8d024727.json` と `calibration-94a4b79fa31bba3c.json` の 2 本。
`orchestrator/campaign/env_contract.py:_build_registry` の `pegasus` generation 1 は
**`753f535a` を指したまま**である (`94a4b79f` は未参照)。
worklog (260) も「活性化・登録は名乗らない」と明記している。
→ **値案の較正根拠は活性 contract が指す `753f535a` を正とし、`94a4b79f` は参考に留める。**

## N8 — 8c 結線は実装されていない (真、D201)

`reflux_origin_ledger` の公開 API は `_production_store()` 固定で caller が store を差し替える
seam が無い。8c 側に ledger 呼出しは存在しない。
→ **本 wave の値案は「批准後に結線する時の入力」であり、批准だけでは何も発火しない。**
