# [T-1851] 段 1 brief — 実装単位 C1b: terminal 証拠の contract leaf と封印 API

継承 tip `17e85e413` + local main 取り込み `9c1951179`。branch `worktree-dev-wave-t1851-unit-a`。**land しない (D1341)。**
継承元の正本は `output/insights/2026-09-07_t1851-unit-c-launcher-raw-facts/` の README 7〜9 節と `s4-adjudication.md` の 3 節 (契約 v2) / 5 節 (境界)。

## scope (成果物影響、DW-G05)

v2 台帳の terminal は現在 `_reject_unsealed_s8b_v2_terminal` (`s8b_attempt_profile.py:556-563`) が無条件で拒否し、`S8B_V2_RETRYABLE_FAILURE_REASONS` は空 (`:533`)。
このままでは v2 世代は classification と observation-start までしか進めず、**certified 選択の材料になる floor attempt が台帳へ terminal 行として一切残らない**。
C1b はこの seam を封印証拠 API へ置き換える。放置時の成果物影響: v2 台帳に terminal 行が出ず、B2 の prefix proof が参照する行数が observation-start で止まり、result v5 の `attempt_registry` proof が производ できない。

## 確定済みユーザー裁定・不変条件

- D1341: 本 branch は 6 単位すべてが揃うまで land しない。D1113: 呼び手は証拠の値を選べない。D1522: 上流が拒否する形でも下層の実体を直接呼ぶ test を置く。
- 契約 v2 (exact 24 field + cross-field 不変条件 + campaign と同順の再導出 6 枝 + E2 の 4 語 + crash 後の権威) は C1a の段 4 裁定で**固定済み**。本 wave はそれを再設計せず実体化する。
- 規律 2: `observed` へ落とす逃がし道を 1 本も作らない。cross-field 不変条件が 1 つでも破れたら拒否する。
- `_CERTIFIED_MEASUREMENT_KEYWORDS`、`_owned_post_probe` の argv / timeout / 関数名 (spawn-site pin `test_ccbench_spawn_sites.py:212`) は不変。v1 の event key 集合は不変。

## 変更面のアンカー (実測)

| path | 現物 | C1b が触る点 |
|---|---|---|
| `orchestrator/campaign/s8b_terminal_evidence.py` | **不在** (grep 0 件、参照は insight 文書のみ) | 新設。契約 v2 の exact dataclass、`seal_terminal_evidence(reservation, opened, terminal)`、`require_sealed_terminal_evidence(value)`、E1 再導出の pure 関数 |
| `s8b_attempt_profile.py` (684 行) | `_reject_unsealed_s8b_v2_terminal :556-563`、`S8B_V2_RETRYABLE_FAILURE_REASONS :533` (空 frozenset)、v2 profile `:640-684` | 拒否 hook を封印証拠 validator へ、E2 の 4 語を active 化 |
| `attempt_registry_core.py` (2,131 行) | `terminal_row_validator` field `:214`、呼出し `:1407-1408`、`record_attempt_terminal :1971-2031` | capability 経路 (証拠を validator へ渡す) |
| `s8b_attempt_registry.py` (3,122 行) | `record_attempt_terminal :2544`、deferred reader `:2502` 付近 | `record_sealed_attempt_terminal(observation, evidence)` の新設 |
| `s8b_floor_attempt_launcher.py` (909 行) | terminal call `:844`、`OpenedFloorAttempt` は C1a の raw facts を保持 | 封印 issuer の呼出しと新 adapter API への差し替え |
| test 3 file | launcher 23 関数 / registry 75 / core profile 68 | 各所有者が持つ |

## 割れうる前提 (親の provisional 裁定・攻撃対象)

- **(P1) 本 wave の実装子は 3 本、依存 1 段。** leaf を 1 本目で固定し、完了後に unit1 (launcher 側の発行 + launcher test) と unit2 (core capability + profile の E2 と validator + adapter の封印 API + その test) を並列に置く。C1a は実装子 1 本で production +245 / test +567 だった。C1b は leaf だけで 400〜600 行規模と見積もる。**規模が段 2 で上限を超えるなら leaf + unit1 だけに切り、unit2 を C1c へ送る**。
- **(P2) campaign_record の 27 key は `_finish_session` (`s8b_floor_campaign.py:6346`) の emit を正本にする。** 実測した key は 29 語 (`attempt_id` / `cell_id` / `configuration_id` / `duration_s` / `event` / `excluded_reason` / `exclusion_class` / `exec_failures` / `holdout_id` / `kind` / `notes` / `probe_after` / `probe_before` / `records` / `rep_integrity_failures` / `rep_observations` / `reps_expected` / `retry` / `retry_ordinal` / `round` / `run_cmd` / `seq` / `session_cv` / `session_median` / `threads` / `throughputs` / `trigger` / `valid` / `workload`)。裁定 3 節が書いた「27 key」と食い違うので、**exact 集合は現物から取り直す**。
- **(P3) production 到達性は 0 のまま (DW-O13)。** `launch_floor_attempt()` の production 呼び手は依然 0 件で、terminal_builder は caller が渡す callable である。したがって本 wave の gate 入力は fake 由来の値域しか実測できない。**「実環境の値域」を主張せず、C2 が供給する形 (campaign の `_finish_session` emit) を静的に照合するに留める**。この制約を段 2 / 3 の攻撃対象に明示する。
- **(P4) E2 の 4 語を active 化しても v1 は空のまま。** `S8B_V2_RETRYABLE_FAILURE_REASONS` にだけ 4 語を入れ、v1 profile の `retryable_reasons` は触らない。
- **(P5) 凍結 bytes (DW-O09) は増えない。** 証拠文書の公開先 `floor-attempt-registry-receipts/terminal-evidence/<digest>.json` は `s8b_attempt_profile.py:512,521` の layout 配下で、`FROZEN_MANIFEST` 系 (`test_frozen_artifacts.py` ほか) の pin は path 検索で 0 件。**新しい成果物名を足すので、段 2 で名前を key にした pin 閉包を引き直す**。

## 成果物の形

leaf module 1 本 + その test、既存 4 file への差分、insight `output/insights/2026-09-07_t1851-unit-c1b-sealed-terminal-evidence/`、worklog / decisions fragment。受入は login からの `tools/dev_wave_wait.py acceptance` (lease を取得した走行では D612 の上書きを付けない = 本 wave で新設した規律)。
