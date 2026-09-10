# 親 brief — [T-529] 契約世代の活性化権限

worktree (repo root): `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation-authority`
基準 commit: 616ef5db (branch worktree-dev-wave-t529-activation-authority、tree clean)

## タスクの出自 (worklog の起票原文)

> [T-529] **P1・新規**: 契約世代の**活性化権限**を実装する。
> activation record からの権威導出と、全入口 (floor / oracle / P3 / 適格性 / selector / silo 昇格) が
> 最初の書込み前に同じ migration epoch と bundle hash を検査する activation receipt を**対で**入れる。
> これが入るまで D176 の fuse は外せない
> (外すと、正規 publish を通っていない較正を source へ足すだけで current にできてしまう)。
> campaign identity への contract hash 束縛と versioned predicate dispatch も同 wave の候補

## 既存実装の所在 (親が実測で確認済み)

- `orchestrator/campaign/env_contract.py`
  - `GenerationEntry` 163-179 (docstring: 「これは data であって権限ではない。issuer の型 gate に使わない」)
  - `is_valid_successor` 202-228 (calibration の path/sha256 の対だけを変える successor を許す)
  - `_build_registry` 231-275 (env 固有 literal はこの関数内だけ。AST 検査の免除 region)
  - `_validate_generations_without_bootstrap_fuse` 278-313
  - `validate_generations` 316-326 (D176 の bootstrap fuse。各 env の世代列長 != 1 を拒否)
  - `GENERATIONS` 344-346 / `validate_generations(GENERATIONS)` 347 /
    `_CONTRACT_SHA256_INDEX` 348 / `REGISTRY` 349-352 (**`sequence[-1]` を無条件に current とする**)
  - `resolve_by_contract_sha256` 355-380 / `lookup` 383-390 / `find_env_literals` 412-
- activation record / activation receipt / migration epoch / bundle hash に相当する実装は
  repo 全体に**存在しない** (親が grep 済み。全て新規)
- 正規 publish 証拠は実在する:
  `output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json` の
  top-level key に `acquisition_receipt` があり、schema は
  `orchestrator/calibrator/schema_v2.py` の `AcquisitionReceipt`
  (`qsub` / `allocation` / `toolchain` / `ccbench` / `job_script_sha256` / `walltime` /
  `known_values_check`)。`output/env/pegasus/calibration/` には `attempts` / `job-staging` /
  `registered` があり、registered だけが publish 済み。

## 親が段 1 で実測した 2 点 (これも攻撃対象)

`_build_registry()` の pegasus へ generation=2 を**実編集**で追加し、`git checkout --` で復元した
(復元後 `git status --porcelain` 空、`git diff HEAD --stat` 空、HEAD blob abe103e5 と一致)。

1. 現状の fuse は import 時に発火する:
   `EnvContractError: 活性化権限 (activation record / activation receipt) が未実装のため、2 世代目の登録を fail-closed で拒否する`
2. fuse を外した反実仮想 (module 複製で `validate_generations` を
   `_validate_generations_without_bootstrap_fuse` へ差し替え) では import が成功し、
   `lookup("pegasus")` が g2 を返した。g2 の `calibration_ref.path` は
   実在しないファイルを指していたのに current になった。存在検査も bytes 検査も publish 証拠検査もない。

この実測の一般化がどこで破れるかも検討対象とする。

## scope

契約世代の current を「source 上の位置」ではなく「activation record」から導出し、
6 入口が最初の書込み前に同一の活性化状態を検査する receipt を対で入れる。

## 不変条件 (触らない)

- `ExecutionEnvironmentContract` の field 集合・`_canonical_obj()`・既存 2 env の
  `contract_sha256` を 1 bit も動かさない (D176)
- `lookup()` の signature と `REGISTRY` の公開 mapping 形は現行のまま
- 既存 committed 成果物の bytes を変えない
- 正しさゲートを緩める方向の変更をしない。受理集合を広げるなら、その広がりを明示し
  positive control を添える

## 親の provisional 裁定 (P1〜P4。親の暫定判断であり攻撃対象)

- **(P1)** fuse は撤去せず、活性化 record 由来の等価以上の gate へ**置換**する。
  「record が活性化していない generation は current にできない」を新条件とする。
  世代が 1 本しかない現状では受理集合が不変であることを positive control で示す。
- **(P2)** 命名は `migration_epoch` / `bundle_hash` を採らない (D75 = 同名識別子を二義化しない)。
  repo 内で `epoch` は unix 時刻の一義 (`submit_epoch` / `deadline_epoch` / `completed_epoch` /
  `scheduler_started_epoch`)、`bundle` は別物 (`role_bundle_sha256` / `raw_bundle`)。
  さらに `MAX_GENERATIONS` は `p3_autonomous_workload_trial.py` / `s8c_preregistration.py` では
  **LLM 提案世代**を指し、契約世代と別義。
  暫定: 単調増加整数を `migration_serial`、活性化状態全体の hash を `activation_bundle_sha256`。
- **(P3)** activation record の非偽造性は publish 証拠への束縛で担保する。
  record が活性化する各 (env, generation) について、`calibration_ref.path` の実 bytes が
  `calibration_ref.sha256` に一致し、その JSON が妥当な `acquisition_receipt` を持つことを
  record 検証時に要求する。record を JSON に書くだけでは活性化できない。
- **(P4)** receipt は既存の exact-key schema を壊さない形で持たせる。
  入口の既存 receipt 構造へ field を足すと `_exact_keys` / `set(candidate) != _TOP` 系の
  凍結検査が割れる。形 (埋め込み / 併置 / in-memory 返却) は未確定。

## 入口 6 種 (親の暫定同定。file:line で確定させること)

- floor: `orchestrator/campaign/pegasus_floor_scoping.py` / `s8b_floor_campaign.py` / `s8b_floor_contract.py`
- oracle: `orchestrator/campaign/s8b_oracle_driver.py` / `s8b_oracle_report.py` / `s8b_oracle_manifest.py`
- P3: `orchestrator/campaign/p3_autonomous_workload_trial.py` / `p3_s4_loop_trigger_gating.py`
- 適格性: `orchestrator/qualification/t126_driver.py`
- selector: `orchestrator/campaign/s8b_selector_freeze.py` / `s8b_selector_input.py` / `s8b_selector_output.py`
  (**env_contract を現状 import していない。ここが入口として成立するかは要確認**)
- silo 昇格: `orchestrator/campaign/silo_ladder_rung1.py`

## pin 閉包 (親が path 検索した結果。判定は未了)

`orchestrator/campaign/env_contract.py` を path で pin / 参照するもの:

- `orchestrator/qualification/contract.py:62` (`REQUIRED_CODE_IDENTITY_PATHS`)
- `orchestrator/tests/test_env_contract.py:83` (AST 免除 region `_build_registry`)、`:559`、`:1195`
- `orchestrator/tests/test_silo_ladder_rung1_driver.py:933`
- `orchestrator/tests/test_s8c_preregistration_predicates.py:355` (fake source)
- `tools/pegasus/probes/t419_probe_causality.py:3495`、`:3533`

contract hash golden: `orchestrator/tests/test_env_contract.py:58`、`:263` (linux)、`:1125` (pegasus)。

**これらが committed digest を byte 固定しているのか実行時再計算なのかを判定すること。**

## 成果物影響 (この wave の各項目を実装しない場合)

- 活性化権限が無いまま: D176 の fuse が残り較正の再取得が永久に不能。U-2 の全成果物
  (certified 選択が参照する env 契約 hash) が旧較正に固定される
- (P2) を誤ると receipt の同名 field が 2 義になり proof chain の参照が曖昧化する
- (P3) が欠けると record は「もう一つの source 位置」に過ぎず権威が名ばかりになる
  (D176 が `CurrentContract` / `HistoricalContract` の型分離を却下した理由と同型の失敗)
- (P4) を誤ると既存 6 入口の成果物 schema が一斉に非互換化する

## 分割方針 (段 5)

- 単位 A: `orchestrator/campaign/env_contract.py` + 新 activation module + その test
- 単位 B: 6 入口の receipt 結線 + その test

ファイル所有を重複させない。
