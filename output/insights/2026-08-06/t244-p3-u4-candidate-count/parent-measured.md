# 親の前提実測 — [T-244] P3 分割の次弾 (U-4)

計測 checkout: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u4-candidate-count`
起点 commit: `616ef5db` (local main と同一)。submodule 初期化済み。

すべて 2026-08-06 に本 checkout で読み取った一次資料である。

## M1 — origin ledger に production consumer は存在しない

`grep -rn "reflux_origin_ledger" --include=*.py`（`external/`・他 worktree を除く）の hit は
`orchestrator/tests/test_reflux_origin_ledger.py` と、過去 wave の使い捨て probe
`output/insights/2026-08-05_t244-p3-liveness/liveness_probe.py` だけである。
`orchestrator/campaign/p3_autonomous_workload_trial.py` は ledger を import していない。

**帰結:** origin-proofs sidecar の `batch_id` / `batch_commit_event_sha256` /
`batch_seal_event_sha256` / `seal_state_commitment` と authority 系 5 field を埋める
実 artifact path が無い。`DW-G04` の発火 gate を満たせない。
report v3 (`origin_proof_ref`) は sidecar への参照なので同じ理由で成立しない。

## M2 — production authority は空で、provisioning は解禁されていない

`orchestrator/campaign/reflux_origin_authority_v2.json` は
`{"authority_schema":"izanagi-reflux-origin-authority/v2","origins":[]}` の 1 行である。
U-10 (予算値 tuple) 未決のため D183 が entry 追加を禁じている。

## M3 — ledger は seal 時に候補平文を持つ

`OpenedBatchMember.candidate_bytes` / `SealedBatchMember.candidate_bytes`
(`reflux_origin_ledger.py:482`, `:495`) により、`BatchSealed` 受理時に候補平文が開示される。
さらに `_SemanticState.replicate_counts` は `dict[bytes, int]`
(`:1061`) で、候補平文 → replicate 数の写像を origin 全体で保持している
(`:1409` 付近の `expected_replicate = next_replicates.get(raw, 0)`)。

**帰結:** 候補数 (distinct candidate count) は producer の自己申告を必要とせず、
ledger が seal 受理時に自分で計算できる。恒真な自己申告 field にしなくてよい。

## M4 — `cardinality` は member 行数であり、候補数を束縛していない

- `BatchReserved.cardinality` (`:505`) と `open_batch["cardinality"]` は予約した member 行数。
- `BatchCommitted` の distinct 検査 (`:1283`) は
  `len({item.candidate_commitment ...}) != cardinality` であり、commitment は
  `_member_preimage(raw, query, replicate)` を salt 付きで hash したもの (`:635`, `:1400` 付近)。
  **同一候補でも (query, replicate) が違えば commitment は必ず異なる**ため、
  この検査は候補の相異を保証しない。
- `BudgetPolicy.batch_cardinality_min` は最小 2 で parse され (`:313`)、
  予約時に `cardinality < budget.batch_cardinality_min` を拒否する (`:1226`)。
  これも member 行数に対する下限であって候補数の下限ではない。

**帰結:** 単一候補 × R replicate の batch は現行の全検査を通り、
`batch_cardinality_min >= 2` も満たす。U-4 が警告した誤認は現に成立しうる。

## M5 — 「P4 証拠」を読む consumer はコードに存在しない

`anti-oracle` / `anti_oracle` / `batch_cardinality` の grep で、ledger 自身以外の hit は無い。
P7 formal consumer は未着手 (worklog (253))。

**帰結:** 「候補数 1 を P4 証拠として受理不能にする」を新しい consumer 側 gate として書くと、
発火路の無い機構になる (`DW-G04` 抵触)。既存の発火路に載せる形を採る必要がある。
既存の発火路として使えるのは `OriginSealed` 受理時の floor 検査
(`sealed_queries < floor.required_queries`、`:1500` 付近) と `BatchSealed` 受理枝である。

## M6 — 凍結 bytes の pin 閉包 (`DW-O09`)

- `orchestrator/tests/test_frozen_artifacts.py` の `FROZEN_MANIFEST` (23 key) に
  `reflux_origin_ledger.py` も `reflux_origin_authority_v2.json` も**無い**。
  key は `output/s1-freeze/**`・`output/s8b-freeze/**`・`output/insights/2026-07-16_*` である。
- ledger の runtime store は git-common-dir 配下
  (`<common>/izanagi/reflux-origin-ledger/v2`、`:1607`) の untracked file であり、
  tracked な出力 bytes を持たない。
- ただし `test_reflux_origin_ledger.py` は event payload と state commitment の
  **独立 golden を literal で持つ** (例: `:621` の `batch-sealed` の `event_sha256`)。
  これは凍結成果物ではなく変更検出用の独立 golden であり、意図した変更として更新してよい
  (`DW-O09` の F39 分類でいう「独立 golden」)。

**帰結:** `DW-O09` / `DW-O10` は凍結 bytes に対しては発火しない。
影響は独立 golden の更新に限られる。

## M7 — D189 が固定した版方針

D189 は「schema ID・domain・runtime path の版は上げない」を、
再解釈される既存 stream が存在しない (tracked runtime store 0 件、production 初期化禁止、
fixture store は毎回新規) ことを根拠に決めている。本 wave でも同じ前提が成立している (M1/M2)。
