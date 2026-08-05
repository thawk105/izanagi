# 親の独立実測 — 参照閉包 (段 2 codex と照合するための対照表)

worktree = `dev-wave-t478-calibration-contract-generation`、main 44ff1c11 相当。
分類: **(L)** live 照合 / **(P)** 永続記録 (artifact bytes) / **(G)** golden・pin (literal 固定) /
**(N)** namespace。

## 起点

- `orchestrator/campaign/env_contract.py:186-192` — pegasus の `calibration_ref`
  (path=`output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json`,
  sha256=`753f535a…`)。**(G)**
- 導出: `contract_sha256` = 全 field の canonical JSON の sha256
  (`env_contract.py:149-159`)。実測 pegasus = `e576e9cd…`、linux-baremetal = `1b2ee853…`。
- 解決経路は `lookup(env_tag)` のみ (`env_contract.py:202`)。**hash 逆引きも世代も存在しない。**
  campaign 側の `lookup(` 呼び出しは 20 箇所。

## (L) live 照合 — 移行すると即座に拒否になる

| 地点 | 内容 |
|---|---|
| `s8b_floor_contract.py:139-151` | `protocol.contract_sha256 == lookup(env_tag).contract_sha256` 完全一致、不一致は `FloorContractError` |
| `s8b_floor_campaign.py:1411-1416` | 凍結 protocol が `pre_oracle_head` の git blob と worktree で **byte 一致**すること |
| `s8b_ratified_freeze.py:174-175, 3027` | `protocol.contract_sha256 == journal.campaign-start.execution_receipt.contract_sha256` |
| `s8b_ratified_freeze.py:2880` | `contract_sha256_lookup=lambda env: lookup(env).contract_sha256` |
| `s8b_oracle_report.py:1198-1204` | manifest の `run_contract.contract_sha256` != registry → `ReportError` |
| `s8b_oracle_driver.py:782` | `verified.sha256 != contract.calibration_ref.sha256` |
| `execution_guard.py:78,110,122,309,336` | receipt 生成と照合、calibration sha 照合 |
| `env_attestation.py:655-668` | `calibration_ref.path` の実在と sha 一致 |
| `silo_ladder_rung1.py:1933-1934, 3520-3527, 4419-4440` | current binding gate (path/sha/contract すべて) |
| `pegasus_floor_scoping.py:76` | `calibration_ref.path` から実 path を解決 |
| `loop.py:91` | receipt に `contract_sha256` を載せる |
| `p3_s4_loop_trigger_gating.py:367` | 記録に `contract_sha256` を載せる |

## (P) 永続記録 — 旧 bytes は動かせない

| artifact | field | 値 |
|---|---|---|
| `output/s8b-freeze/floor_protocol.json` | `contract_sha256` | `e576e9cd…` |
| `output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json:12,570` | `binding.calibration.contract_sha256`, `gap_leg.attestation.contract_sha256` | `e576e9cd…` |
| `…/silo_ladder_rung1/job-staging/0_873920.nqsv/raw-bundle-attempt-1/gap-result-receipt.json` | `gap_leg.attestation.contract_sha256` | `e576e9cd…` |
| `output/env/pegasus/t419-probe-causality/*/manifest.json`, `result.json` (4 job × 2) | `provenance.*.env_contract_sha256`, `environment.binding.env_contract_sha256` | `88d557ba…` |
| `reflux_origin_ledger.py:243,395,425,1552` が書く origin ledger | `environment_contract_sha256` | 実行時に決まる |

**重要 (親の新規発見)**: T-419 probe の `env_contract_sha256` は contract の canonical
fingerprint ではなく **`orchestrator/campaign/env_contract.py` の source file sha256**
(`tools/pegasus/probes/t419_probe_causality.py:3532-3534`)。実測で
`sha256sum orchestrator/campaign/env_contract.py = 88d557ba…` と一致。
`expected_env_contract_sha256` は存在せず**比較されない**ため、移行後は「古いが無害な provenance」
になる。ただし **名前が env contract の fingerprint と紛らわしく、D75 の同名二義化に該当**する。

## (G) golden・pin

| 地点 | 内容 |
|---|---|
| `orchestrator/tests/test_frozen_artifacts.py:45-46` | `floor_protocol.json` = `261cec1c…` (23 件 manifest の 1 つ) |
| 同 `:67-68` | `selector-runs/journal.jsonl` = `d4113599…` (この journal の `run_header.protocol_sha256` = `261cec1c…`) |
| `orchestrator/tests/test_env_contract.py:60-61, 247-250, 687-690` | calibration path / sha / contract sha の literal golden |
| `orchestrator/tests/test_s8b_floor_campaign.py:3239, 3242` | calibration sha / contract sha の literal |
| `orchestrator/tests/test_env_contract.py:436-463` | `KNOWN_SELF_INCONSISTENT_CALIBRATIONS` を **exact 1 件**と assert。再登録で空集合へ反転する (意図的な反転強制) |
| `orchestrator/tests/test_env_contract.py:465-480` | `LEGACY_CALIBRATION_ALLOWLIST` の exact 一致 |
| `docs/failures.md:2187`, `docs/pegasus-runbook.md:523` | calibration path を本文で参照 (docs 側、F78) |

## (N) namespace

- `buildcache.py:650` — build cache root が `contracts/<contract_sha256>/…`。
  `:392` で manifest の `contract_sha256` を照合。移行すると新 namespace になり
  **旧 cache が孤児化する** (破綻ではなく cache miss)。

## 閉包から除外するもの (同名だが別概念、D75)

- `s8c_preregistration.py` の `evidence_contract_sha256` — prereg 文書の evidence contract の
  hash であって env contract ではない。`output/s8c-preregistration/condition-freeze/…json` の
  `evidence_contract_sha256` も同様。
- `output/env/pegasus/calibration/attempts/*/publish.json` — grep は当たるが contract hash は
  持たない (path 文字列のみ)。

## 親の結論 (provisional、段 3 の攻撃対象)

凍結 protocol は「history の blob と byte 一致」かつ「現行 registry と contract hash 完全一致」の
両方を同時に要求される。較正を再登録すると**この 2 条件は同時に満たせない**。
したがって移行は **旧凍結 bytes を貼り替えない世代分離**でしか通らない。
