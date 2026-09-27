# 単位間 interface (段 4 確定、変えてはならない契約) — [T-2865] 段階 F

## 1. 方策 driver の CLI (単位 A が実装、単位 B が呼ぶ)

`python3 -m orchestrator.campaign.p3_s4_loop_policy --form {cpp,ir} [--campaign-env {linux-baremetal,pegasus}] [--fetchcontent-prebuild-receipt PATH] <action>`

action はちょうど 1 つ:

| action | campaign | 計測 | build 認可 |
|---|---|---|---|
| `--emit-coder-input --baseline-throughput-tps X --baseline-abort-rate-pct Y [--critic-output F]` | loop | しない | — |
| `--preview-diff CODER.json` | (使わない) | しない (単独 TU compile だけ) | — |
| `--record-reject CODER.json` | loop | しない | — |
| `--stock-baseline` | bootstrap (`evaluation_purpose=bootstrap`) | stock 1 評価 | 不要 (stock 用 context) |
| `--run-iteration PROPOSAL.json [--stock-control]` | loop | 候補 1 評価 (+ 同じ authorization session で stock 1 評価) | 候補は `--allow-coder-derived-build` 必須 |
| `--replay-proposal PROPOSAL.json` | r2 (`evaluation_purpose=r2`) | 候補 1 評価 (LoopState・履歴は作らない) | `--allow-coder-derived-build` 必須 |

- `--campaign-env` の既定は `linux-baremetal` (現行 identity 不変)。`pegasus` は `p3_s4_loop._campaign_cfg_for_site` と同じ形 (`search_config["measurement_env"]="pegasus"` と `pegasus` 契約の束縛) で identity を作る。
- 計測する action (`--stock-baseline`・`--run-iteration` (no-build でないとき)・`--replay-proposal`) は、解決 site の契約 (`L._current_site()` → `L._admit_env_contract()`) の env tag が `--campaign-env` と一致しなければ実行前に拒否する。
- `--fetchcontent-prebuild-receipt` は計測 action でだけ受け付け、`L._load_masstree_prebuild_receipt` の 5 値を `run_campaign` へ渡す。
- `--no-build` と `--no-isolate-worktree` は既存どおり。
- 標準出力は 1 行の JSON。stock の JSON (単独・pair の stock 部) は `outcome`・`variant`・`fitness_tps`・`abort_rate_pct`・`verdict` を持つ。`abort_rate_pct` は同じ attempt の BENCH_DONE の `leading_indicators.abort_rate` × 100、欠損は null。pair の出力は `{"candidate": {...}, "stock": {...}}`。
- rc: 成功 0。候補が例外で終わった pair は stock を試みた後に例外を再送出 (rc≠0)。

## 2. job body の方策 mode (単位 B)

- env: `IZANAGI_S4_POLICY_MODE` ∈ {`stock`,`pair`,`replay`}、`IZANAGI_S4_POLICY_FORM` ∈ {`cpp`,`ir`} (方策 mode では必須)、`IZANAGI_S4_POLICY_PROPOSAL_PATH` (pair・replay で必須・非空、stock では存在自体を拒否)、`IZANAGI_TRACE_ARCHIVE_ROOT` (方策 mode で必須)。
- 方策 mode と T-2849 (`IZANAGI_S4_T2849_*`)・B-5 (`IZANAGI_S4_B5_*`)・K2 (`IZANAGI_S4_KNOWLEDGE_*`・`IZANAGI_S4_CODER_ROLE`)・`IZANAGI_S4_PROPOSAL_PATH`・`IZANAGI_S4_FIXTURE_VALUE`・`IZANAGI_S4_STOCK_CONTROL` は排他 (repository 解決前に rc=2)。`IZANAGI_S4_POLICY_FORM` / `IZANAGI_S4_POLICY_PROPOSAL_PATH` は方策 mode 無しなら拒否。
- 保全 root: 絶対 path、`realpath -m` 後に repo root・git common repo の中なら拒否。driver 起動前に検査。
- driver 呼出し (前処理と masstree receipt の後、`IZANAGI_BENCH_LOCK="$TMPDIR/bench.lock"` を export して 1 回):
  - 共通: `"$PY" -B -m orchestrator.campaign.p3_s4_loop_policy --form "$IZANAGI_S4_POLICY_FORM" --campaign-env pegasus --fetchcontent-prebuild-receipt "$prebuild_receipt"`
  - stock: `--stock-baseline`
  - pair: `--allow-coder-derived-build --run-iteration "$IZANAGI_S4_POLICY_PROPOSAL_PATH" --stock-control`
  - replay: `--allow-coder-derived-build --replay-proposal "$IZANAGI_S4_POLICY_PROPOSAL_PATH"`
- job の rc = driver の rc。
