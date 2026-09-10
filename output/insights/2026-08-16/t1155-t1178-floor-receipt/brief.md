# 段 1 brief — [T-1155] + [T-1178] (floor durable record への SWO receipt 束縛と admission 台帳検査)

wave: `dev-wave-t1155-t1178-floor-receipt` / branch `worktree-dev-wave-t1155-t1178-floor-receipt`
base: local main `2f7eeb22` (0 commit 差) / 2026-08-16 JST

## 0. 前提の実測 (brief 前に実施済み)

| 主張 | 実測 | 根拠 |
|---|---|---|
| `oracle_attempt` を floor campaign が読まない | 真 | `grep -rn oracle_attempt --include=*.py` の hit は `s1_direct_comparison.py` (S-1 journal 経路) と test のみ。`s8b_floor_campaign.py` に 0 件 |
| 捨てている位置 | `s8b_floor_campaign.py:2445-2449` で `prepared` を束縛し、`:2578-2596` の `built[cell_id]` に `oracle_attempt` を入れない | 実読 |
| result.json が台帳を持たない | 真 | `assemble_result` (`s8b_floor_campaign.py:4389-4430`) の key 集合に admission 由来なし |
| 台帳を読む consumer が admission module 外に存在しない | 真 | `grep -rn "ledger.jsonl\|_LEDGER_NAME\|shared_admission_root" --include=*.py orchestrator/ tools/` の非 test hit は `s8b_holdout_admission.py` のみ (他は qualification の別台帳) |
| 既存の実 floor 成果物 | **0 件** | `find output -name result.json` の hit は t419 probe / qualification / insights のみ。`output/s8b-freeze/` に run dir なし |
| 凍結 bytes pin (DW-O09) | 阻害なし | `FROZEN_MANIFEST` 23 件に `.py` 0 件 (runbook §表)、`s8c_preregistration_evidence_contract.v1.json` の `s8b_ratified_freeze.py` 参照は `field_paths` であって bytes pin でない |

## 1. scope

**A ([T-1155])**: 床値 durable record (`manifest.json` / `result.json` の `binaries[cell_id]`) へ
sort_best cell の SWO PASS receipt を束縛し、無い場合を fail-closed で拒否する。

**B ([T-1178])**: `result.json` へ admission 台帳の claim identity と ledger digest を載せ、
台帳が消えている / 一致しない floor result を verifier・ratified closure・report が拒否する。

scope 外 (実装しない): [T-1179] publish 経路分離、[T-1180] pilot 承認経路、[T-1181] claim 順序、
[T-1156] 再 fetch 禁止。oracle driver 側 (`s8b_oracle_driver.py`) の receipt 束縛。

## 2. 確定済みユーザー裁定

- Codex author = D95 (実装面は Codex `role=author` の子が書く。親は直接編集しない)。
- 成果物 schema を変えるので、既存の実成果物への影響を実測して記録する → **0 件と実測済み** (§0)。
- 稼働中の `dev-wave-t1142-oracle-n-pilot` が `orchestrator/tests/test_s8b_floor_campaign.py` を
  触るので、起動時に重複確認 (済: 別 slug・別 worktree) し、main を都度取り込む。

## 3. 攻撃対象の provisional 裁定 (親の暫定判断。段 3 で攻撃せよ)

- **(P1) receipt の載せ方**: `OracleReceipt.as_dict()` は `compiler_realpath` /
  `dependency_root_realpath` というホスト絶対パスを含む。portable artifact (`_validate_portable_path`
  が `/` 始まりを拒否する世界) へ raw で載せると portability 契約と衝突する。
  暫定裁定 = **artifact には sanitized 射影 + `receipt_sha256` を載せ、full receipt は journal
  (private) 側に置く**。射影 key 案 =
  `{classification, reason_code, oracle_contract_id, materialized_hole_sha256, proposal_sha256,
    corpus_id, corpus_version, compiler_version, compile_flags_sha256, tu_sha256,
    tu_template_sha256, dependency_config_sha256, receipt_sha256}`。
  対抗案: 絶対パスも `_portable_argv` 同様に placeholder 化して全 field を載せる。
- **(P2) 発火条件**: `sort_swo_oracle` は `configuration_id == "sort_best"` の cell に**必ず在り**、
  それ以外の cell には**必ず無い**。テスト fake の `prepare_fn` でも空にできない形にする
  (恒真化の回避)。対抗案: production 経路 (`prepare_fn is prepare_cell`) のときだけ必須。
- **(P3) ledger digest の定義**: 台帳は他 campaign も追記する共有 append-only file なので、
  **この `campaign_run_id` に属する行だけを canonical 順に並べた digest** とする。
  file 全体の digest は他 campaign の追記で必ず壊れる。
- **(P4) 台帳到達不能時の扱い**: ratified closure が admission root へ到達できない環境では
  **fail-closed で拒否**する (skip しない)。ここが「台帳だけ消しても気付かない」の急所。
  対抗案: 到達不能を「検証不能」として別 reason code で拒否し、到達可能な場での再検証を要求する。
- **(P5) schema 番号**: `RESULT_SCHEMA` v3→v4、`MANIFEST_SCHEMA` v2→v3。実成果物 0 件なので
  交差受理 (旧 schema の受理) は**作らない**。

## 4. 不変条件 (緩めてはならない)

1. 規律 1: trace-disabled のまま。receipt は build 時に既に取れている値の転記だけで、
   新しい計測経路・実行時分岐を足さない。
2. 規律 2: 新 key は必須化 (fail-closed)。既存の exact-key 契約 (`PORTABLE_BUILT_KEYS`,
   `_RUNTIME_STORED_KEYS`, `_RUNTIME_FETCHCONTENT_STORED_KEYS`) を「余分な key を許す」方向へ
   緩めない。verify の新検査は空集合・欠損 cell で恒真化しないこと。
3. 規律 3: 拒否は pass/fail でなく構造化 reason code を返す (`RatifiedFreezeError.reason` /
   `verify_floor_artifact` の problems 文字列)。
4. `official` の受理集合は狭くなる方向にだけ動く。広げない。
5. 実装子は docs を編集せず commit もしない。親が統合 commit と記録を行う。

## 5. 成果物影響 (DW-G05、1 行ずつ)

- **A を実装しない場合**: certified 選択の proof chain に「その comparator がどの oracle 実行で
  PASS したか」への durable な辺が無いまま床値が確定し、後から oracle 実行痕跡を差し替えても
  成果物の値・受理集合が一切変わらない。
- **B を実装しない場合**: 実測後に admission 台帳を消した run の `result.json` が
  `verify_floor_artifact`・ratified closure・report のすべてを従来どおり通過し、
  一回性 (one-shot holdout observation) の主張が成果物側の証拠を持たないまま publish される。

## 6. 変更面 実アンカー表

| path | anchor | 役割 |
|---|---|---|
| `orchestrator/campaign/s1_direct_comparison.py` | `:159-164` `PreparedCell` / `:709` `attempt_record(oracle)` | receipt の生成元 (**変更しない想定**) |
| `orchestrator/campaign/s8b_floor_campaign.py` | `:2445-2449` `_prepared_binding` 束縛 | `prepared.oracle_attempt` の入手点 |
| 同 | `:2578-2596` `built[cell["cell_id"]] = {...}` | 捨てている点。A の第一注入点 |
| 同 | `:2685-2738` `_validate_portable_built` | exact key 契約 + 受理検査 |
| 同 | `:2740-2800` `project_built_records` | runtime→portable 射影 (P1 の実装点) |
| 同 | `:2826-2865` `assemble_manifest` | manifest.json `binaries` |
| 同 | `:3429-3450` `_RUNTIME_FRESH_KEYS` / `_RUNTIME_STORED_KEYS` / `_RUNTIME_FETCHCONTENT_STORED_KEYS` | runtime key 契約 |
| 同 | `:4389-4430` `assemble_result` | result.json 本体。B の注入点 |
| 同 | `:5218-5240` `_reserve_floor_holdout_observations_core` / `finalize_floor_holdout_admissions` | reservation・admissions の入手点 |
| 同 | `:5290-5310` 自己検査 `verify_floor_artifact` | 発行前 gate |
| `orchestrator/campaign/s8b_binary_admission.py` | `:36` `PORTABLE_BUILT_KEYS` | key 集合の正本 |
| `orchestrator/campaign/s8b_floor_stats.py` | `:593` `verify_floor_artifact` / `:915` portable key 検査 | verifier |
| `orchestrator/campaign/s8b_floor_contract.py` | `:31-32` `RESULT_SCHEMA` / `MANIFEST_SCHEMA` | schema id |
| `orchestrator/campaign/s8b_holdout_admission.py` | `:76-107` dataclass / `:406-431` `_key_fields` `_claim_digest` / `:865-972` `finalize_floor_holdout_admissions` | B の identity 源 |
| `orchestrator/campaign/s8b_ratified_freeze.py` | `:183` / `:258-263` `_RUN_BASENAMES` / `:2186` schema 検査 / `:2225-2250` floor 検証 / `:2380-2430` 軸漏洩走査 | ratified closure |
| `orchestrator/campaign/s8b_holdout_freeze.py` | `:1319` schema 検査 / `:1393` verify 呼出し | 別 consumer |
| `orchestrator/tests/s8b_v2_freeze_fixture.py` | `:275` | 合成 fixture (更新要) |
| `orchestrator/tests/test_s8b_ratified_verify.py` | `:421` `:502` | 合成 fixture (更新要) |
| `orchestrator/tests/test_s8b_floor_campaign.py` | `:6745` exact key メタテスト / `:297` `:1284` `:2997` fake `PreparedCell` | 並行 wave t1142 が所有。main を都度取り込む |

## 7. 純増検出力 (既存被覆の性質検索の結果)

- 「floor 成果物が oracle receipt を持つこと」を検査するテストは**存在しない**
  (`test_sort_swo_oracle.py:1348-1350` は `prepared.oracle_attempt` の中身を見るだけで、
  floor artifact へ届いたかは見ない)。
- 「floor 成果物が admission 台帳と一致すること」を検査するテストは**存在しない**
  (台帳検証はすべて admission module 内の live path でのみ発火する)。
- 純増分 = (i) sort_best cell の receipt 欠落・改竄の検出、(ii) 台帳削除・claim 不一致・
  ledger digest 不一致の検出。

## 8. 分割方針

- 段 5 実装子 2 本 (所有を分ける):
  - 子 A = A scope: `s8b_binary_admission.py`, `s8b_floor_campaign.py` の built/portable/manifest 系,
    `s8b_floor_stats.py` の binaries 検査, `s8b_floor_contract.py` の `MANIFEST_SCHEMA`。
  - 子 B = B scope: `s8b_holdout_admission.py` の新 public API, `s8b_floor_campaign.py` の
    `assemble_result` + 自己検査, `s8b_floor_stats.py` の `holdout_admission` 検査,
    `s8b_ratified_freeze.py` の closure, `s8b_floor_contract.py` の `RESULT_SCHEMA`。
- `s8b_floor_campaign.py` と `s8b_floor_stats.py` と `s8b_floor_contract.py` を両者が触るため、
  **逐次 (A → B)** とし並行にしない。所有衝突を避ける。
- 段 2・3 は省略しない (受理集合が変わり、正しさ防壁 = proof chain に触る。DW-C00)。
