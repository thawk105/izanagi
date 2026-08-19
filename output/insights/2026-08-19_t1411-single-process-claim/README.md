# [T-1411] loop.py sink-local single_process 強制 (D553)

wave: `dev-wave-t1411-single-process-claim` / 2026-08-19 / branch
`worktree-dev-wave-t1411-single-process-claim` / 基準 commit `752773cdab05b1f316138d903a0b4fa1f5aabc84`

## この材料が答えたこと

D553 (2026-08-19) の実装。`orchestrator/campaign/loop.py` の `_authorize_measurement` へ、
`contract.isolation_policy.single_process is True` のときだけ発火する sink-local な claim 取得
(`campaign_claim.acquire_claim`) と reservation 検査 (`reservation.check_reservation`) を追加した。
F322 (計測 sink が `single_process` を宣言だけして一度も強制しない恒真ゲート) の恒久対応。

## 構成

- `brief.md` — 段1 brief。
- `s4-adjudication.md` — 段3 敵対相談2レンズの所見と段4 裁定 (plan v2 確定を含む)。
- `mutation-spec.json` — 変異 matrix の最終形。**`verification_method` field に、標準 harness
  (`tools/mutation_harness.py`) が構造的に使えなかった理由と代替手法を記録** ({{F:mutation-harness-contract-loader-incompat}} 参照)。

## 主要な実測

- 段2 プラン (`s2-plan.md` 相当、job dir にのみ保存) の `claim_root` 解決式が、実 8c exploration
  経路 (`p3_s4_loop_trigger_gating.py:637-649`、`output_root` 省略・`declared_use_class="exploration"`)
  の実際の output root と一致しないことを、段3 敵対相談2レンズが独立に発見し、親が
  `p3_s4_loop_trigger_gating.py` を直接読んで裏取りした。plan v2 で是正 (`s4-adjudication.md` 参照)。
- 段6 敵対レビュー・レンズ1 (正確性・退行) が、claim の identity 検証が layout 側より緩く、
  layout 側だけが拒否する `campaign_identity` (先頭ドット等) で孤児 claim が永続的に残りうる
  実欠陥を発見。`layout.validate_campaign_id` (既存 `_campaign_slug` の公開 wrapper) を
  claim 取得前に呼ぶ fix で解消 (commit `e2013e73`)。
- 変異 matrix 6件は標準 harness (`--runner-mode dispatch`) が全件 MISMATCH/rc=1 で拒否した。
  原因は `loop.py` が `campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS` (2026-08-18 に25 pathへ拡張)
  に含まれ、`ratified_enforcement_source` fixture の disk==HEAD blob 検査と harness の
  file-swap 方式が構造的に衝突するため。手動 commit→`tools/run_tests.py`実走→
  `git reset --hard`復元、を6回繰り返す代替手法で検証し、全6件 KILLED を確認した
  (詳細は `mutation-spec.json` の `verification_method`/`observed_run` field)。
  M1 (reservation gate 反転) の実測 kill 数は35件で、事前の手動予測(7件)を大幅に上回った
  (F323 と同型の under-registration リスクの実例)。
- 受入全走: `verdict=child-green`、13523 passed / 96 skipped / 0 failed、
  `tested_tip=7615775c34155c7ff7cc06efb106977efbf0bd61`
  (`tested_main=52ff6db2537d604085b419047be9c5b912272b72` を受入 lease 内で merge 済み)。

## 模擬と実の差 (F29)

静的読解と実 pytest 実走 (親環境・Pegasus dispatch 経由) の両方を行った。8c 実 caller
(`live.pbs`) を実際に起動して claim 取得まで通す positive exercise は行っていない —
[T-1097]/[T-276] の transport 欠陥が未解消のため構造的に不可能 (brief.md の (P2) 参照)。
