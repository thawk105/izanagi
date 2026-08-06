# 段 1 brief — [T-574] historical resolver + versioned predicate dispatch の production 配線

親 (Claude) が書いた brief。子はこれを攻撃対象として読む。`(P1)`〜`(P5)` は
**親の provisional 裁定であり攻撃対象**である。

## scope

artifact に記録された `contract_sha256` から契約世代を解決する historical resolver を、
**publish 済み成果物を read-only で再検証する consumer** へ配線する。
current registry lookup は **新規 producer と resume admission** に限る。
D196 が命じた [T-529] の前提であり、較正再取得の真の blocker を外す作業である。

対象 (親が現物で同定した 4 箇所):

| # | file:line | 役割 | 現状 | 目標 |
|---|---|---|---|---|
| C1 | `orchestrator/campaign/s8b_ratified_freeze.py:2878-2881` | publish 済み floor protocol の再検証 | `contract_sha256_lookup=lambda env: _env_contract.lookup(env).contract_sha256` | 記録された hash から解決 |
| C2 | `orchestrator/campaign/s8b_ratified_freeze.py:1803` (`_validate_journal`) | journal receipt / calibration 検証 | `_env_contract.lookup(protocol["env_tag"])` | 同上 |
| C3 | `orchestrator/campaign/s8b_ratified_freeze.py:2287` (`_run_cmd_matches_portable_session`) | 記録済み run_cmd の再導出 (`clocks_per_us` / `numactl`) | 同上 | 同上 |
| C4 | `orchestrator/campaign/s8b_oracle_report.py:1202` (`_receipt_expectations`) | publish 済み manifest `run_contract` の再検証 | `env_contract.lookup(env_tag)` + hash 一致要求 | 同上 |

**current のまま据え置く (producer / admission)**: `s8b_floor_campaign.validate_protocol`
(`:308`、`run_campaign:2750` と CLI `:3483` が呼ぶ)、`loop._authorize_measurement`、
`pipeline`、`p3_s4_loop_trigger_gating`、`s8b_ratified_freeze:960` (env_tag 実在検査のみ)。

## 親の実測 (この brief の根拠、模擬でなく実編集 + 即時復元)

`_build_registry()` の pegasus へ g2 (calibration path/sha のみ差分 = valid successor) を実編集で足し、
`validate_generations` の fuse を一時的に `> 2` へ緩めて測った。復元後 tree clean、
`orchestrator/campaign/env_contract.py` の worktree hash は HEAD blob `abe103e5` と一致。

- g1 のみ (baseline): C1 相当 leaf・C4 とも緑。`resolve_by_contract_sha256` も g1 を解決。
- g2 を current にした瞬間:
  - `s8b_floor_campaign.validate_protocol(output/s8b-freeze/floor_protocol.json)` →
    `FloorCampaignError: protocol.contract_sha256 が env_contract.lookup('pegasus').contract_sha256 と不一致`
  - `s8b_oracle_report._receipt_expectations` → `ReportError: manifest contract_sha256 が registry contract と不一致`
  - **同じ document を「記録された hash から解決した契約」で検証すると通る** (`consumer_floor_protocol_historical_resolve: ok`)
- `resolve_by_contract_sha256` の production consumer は **0 件** (test のみ)。D176 の
  「履歴 resolver は production の消費者を持たない」がそのまま残っている。
- probe 逐語: `/work/1/SFC/tanab/dev-wave-jobs/t574-historical-resolver/probe_g2_consumers.py`

`s8b_ratified_freeze.launch_validate` は本 branch では `[no-active] live active pointer が無い
(v2 未発効)` で入口に到達しない。**C1〜C3 は現時点で E2E 実走できない** — 検証は leaf 単体と
unit test で行い、E2E 緑を主張しない。

## 不変条件 (破ったら停止)

1. **受理集合の拡大は read-only 再検証だけ。** producer と resume admission が current 契約以外を
   受理してはならない。実装後、producer が g1 記録の protocol で新規 run を開始できないことを
   positive/negative 両方で示す。
2. **hash → 世代の解決は env_tag 束縛付き** (`expected_env_tag`)。別 env の g1 hash を
   受理してはならない。
3. **既存 fuse (`validate_generations` の 1 世代制限) を外さない。** D196 が明示した。
   2 世代の正例は test 内の注入 seam で構成し、production registry を 2 世代にしない。
4. **凍結 bytes を変えない。** DW-O09 の pin 閉包を親が実測: `env_contract.py` は
   `orchestrator/qualification/contract.py:62` と `silo_ladder_rung1.py:260` の runtime 閉包に、
   `s8b_oracle_report.py` は `s8b_oracle_manifest.py:46` の `generator_versions` に束縛される。
   いずれも **実行時に現ファイルを hash して新 artifact へ記録する**形で、
   publish 済み artifact に旧 hash を pin したものは `output/` に存在しない (grep で 0 件)。
   よって DW-O10 の producer 出力 bytes 変化は起きるが、既存 proof chain は無効化しない。
   **この判定は実装後に再検査する。**
5. 恒真な保証を作らない。`if False` で終わる predicate、g1 だけを登録した dispatch 表など、
   正例を書けない機構は作らない (D196 が却下した型)。

## provisional 裁定 (攻撃対象)

- **(P1)** 解決の実体は既存 `env_contract.resolve_by_contract_sha256` をそのまま使い、
  consumer 側に**注入 seam** (既存 `contract_sha256_lookup` と同じ idiom の callable) を足す。
  module 級の新しい可変状態を作らない。
- **(P2)** 「versioned predicate dispatch」は **per-generation の predicate 表を作らない**。
  契約由来の値 (`clocks_per_us` / `numactl` / `calibration_ref` / `attestation_mode`) を
  **解決した世代から取る**ことを指す。正例を書けない dispatch 表は D196 の却下型である。
- **(P3)** C4 の hash 一致検査 (`contract.contract_sha256 != contract_sha256` で raise) は
  **削除でなく置換**する。記録 hash が「どの世代にも解決しない」場合は従来どおり fail-closed。
- **(P4)** resume admission は current のままにする (T-574 の文言)。結果として g1 で始めた
  campaign は g2 current 下で resume 不能になる。pegasus は `allow_resume=False` なので
  現実の受理集合は変わらない。**この副作用を worklog へ明記する。**
- **(P5)** 正例 (positive control) は「current が g2、記録が g1 のとき read-only 検証が通り
  producer が拒む」を test で構成する。注入 seam 経由で 2 世代 mapping を作り、
  production fuse は触らない。

## 成果物の形 (DW-G05 — 実装しない場合に成果物が受ける影響)

- 実装しない場合: 契約世代を 1 つでも進めた瞬間、**certified floor / freeze / selector /
  oracle report の再検証がすべて `protocol-invalid` / `ReportError` で落ちる**。
  すなわち [T-529] の較正再取得が永久に着手できず、
  `output/s8b-freeze/floor_protocol.json` を根とする proof chain の参照が切れる。
- 実装した場合に変わる値: 受理集合のみ。既存 certified 選択・レポート・台帳の**値は変わらない**
  (g1 しか登録されていないため、解決結果は現 current と同一)。

## 分割方針

- 段 5 実装子は 1 本 (所有 = `s8b_ratified_freeze.py` / `s8b_oracle_report.py` /
  `s8b_floor_contract.py` の注入 seam + 新規 test)。file 競合がないため並列化しない。
- 段 6 レビューは 2 本 (レンズ A = 受理集合と fail-closed 性、レンズ B = 恒真保証・正例の実在)。

## 重量判定

`DW-C00` の 3 条件のうち **「正しさ防壁に触る」「受理集合が変わる」が成立**するため、
軽量版にしない。段 2・3 と段 6 の review 子を省略しない。

## 受入・実測の環境

- 受入全走: `python3 tools/run_tests.py` (login node から計算ノードへ自動 dispatch)。
- 変異 matrix: `tools/mutation_harness.py`。走行中は tree へ書かない (既往事故)。
- 主戦場: 本 worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t574-historical-resolver`。
