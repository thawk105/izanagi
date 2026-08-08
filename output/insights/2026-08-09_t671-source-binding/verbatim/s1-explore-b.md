# 段 1 実測 B — campaign id 分裂の機序 (Explore 子、read-only、2026-08-09)

## campaign_id の導出 (main)

- `orchestrator/campaign/ident.py:125-144` `canonical_preimage()` — pre-image は
  spec_content / ccbench_commit / search_tag / search_config(sorted) / trial。main に contract 系
  キーは登場しない。`build_admission` 欠落は ValueError (:132-135)。
- `ident.py:147-156` `cfg_hash()` / `campaign_id()` → 先頭 8hex。`model.py:79-86` で
  `slug-search_tag-cfg_hash8` がそのまま dir 名 (`layout.py:1-16`)。
- T-343 先例: `test_p3_s4_loop_trigger_gating.py:107-118` が `...-3f72ecd5` → `...-ccba936e` を pin。
  D125 決定 (2) は既に破られ land 済み。

## t530 branch の差分 (contract hash の入り方)

- `model.py:27-28`: `ENVIRONMENT_CONTRACT_SEARCH_KEY = "environment_contract_sha256"`、
  `COMMIT_CONTRACT_SHA256_KEY = "contract_sha256"`。
- `ident.py:52-74` `bind_environment_contract()` — search_config へ焼く =
  **id の pre-image に直接入る** (lock 隣接 field ではない)。
- `ident.py:155-186` `canonical_preimage(require_environment_contract=True 既定)`。
- `wal.py:947-985` `validate_commit_contract_bindings()` — lock にキーがあるときだけ全 COMMIT の
  `contract_sha256` を照合 + `resolve_by_contract_sha256` の ever-active 解決で env_tag 交差検査。
  キーが無い legacy/guided は skip (:943-961)。
- `pipeline.py:1028, 1088` — COMMIT 2 口へ書込み。
- `loop.py:127-134` — `_authorize_measurement()` の戻り (= **その瞬間の current 契約**) を
  `bind_environment_contract` してから `campaign_id(cfg)` → layout 確定。

## 分裂の機序

- `env_contract.py:606-625` `lookup()` / :636-663 `authorize()` は常に activation head の current を
  返す (snapshot ではない)。`resolve_by_contract_sha256` (:671-699) は ever-active 解決 —
  g2 活性化後も g1 ロック済み WAL の検証は壊れない。
- g2 跨ぎ resume: 再実行時の cfg が g2 hash を束縛 → 別 cfg_hash8 →
  `ident.py:216-257` `ensure_campaign_identity` が旧 dir を一度も見ずに新 layout を atomic acquire
  = **静かな二重化**。旧 dir は自己整合のまま凍結。互いの整合性検査はない。
- 読出し: `replay.py:89-107` `discover_campaign_dir` は id 非依存の prefix glob。分裂後に両 dir が
  `runs/wal.jsonl` を持つと 2 hit で **FileNotFoundError** (曖昧選択しない fail-closed、可用性破断)。
- guided lane は t530 で解決済み: `guided.py:172-175, 199-201` が
  `require_environment_contract=False`、wal 側も lock にキーが無ければ skip。
- 未解消の温床: ambient `env_contract.lookup(ENV_TAG)` / `authorize(ENV_TAG)` 直呼びが 15 か所超
  (`backoff_repro.py:99`, `backoff_sweep.py:83`, `p3_kickoff.py:100`,
  `p3_s4_loop.py:752,865,998,1085`, `p3_s4_loop_sort.py:197,230,322,430`, `p3_s4_red.py:147`,
  `s1_direct_comparison.py:239`, `s6_sort_sweep.py:190`, `s8a_trigger_sweep.py:288` 他)。
  lock 固定世代を resume 時に引き継ぐ仕組みは現存しない。

## 場合分け (g2 活性化 × t530 land の順序)

| 順序 | 帰結 |
|---|---|
| main のみ (t530 未 land) で g2 活性化 | id 不変・分裂なし。ただし g1/g2 由来 COMMIT が同一 WAL へ**無区別合流** (契約 provenance 消失)。COMMIT 検証機構自体が無い |
| t530 land → g2 活性化 | 活性化前開始・未完了 campaign の g2 跨ぎ resume で**分裂** (新旧 2 dir、旧 dir 凍結・新 dir へ追記)。同一 slug で 2 dir が WAL を持つと discover が FileNotFoundError |
| g2 活性化 → t530 land | 分裂は起きないが、land 前 (contract 無し identity) 開始の campaign は land 後の contract 必須 identity から外れ、既存 30 本と同型の断絶 |

## 既存母数

- `output/campaigns/*/campaign.lock` = 30 本、`build_admission` を含むもの 0 (実測)。
  smoke evidence 2 本は `output/insights/2026-08-04_wave-a-campaign-transport-smoke/` 配下。
- main の `canonical_preimage` は pre-T343 cfg からの id 再計算自体が不可能 → 30 本の到達不能は
  status quo (t530 の新規の穴ではない)。
- 別分類 `historical-not-reclassified` 21 件 (`artifact_admission.py:623`) は t530 件 1・2 の残件。
