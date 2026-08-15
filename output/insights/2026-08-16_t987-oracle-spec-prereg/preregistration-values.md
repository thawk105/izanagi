# 事前登録値の候補と決定者 — [T-987]

実測基準 = local main 330f67d0。**すべて AI 草案であり未承認である。**
「承認済み」と書いてはならない。pytest は非実走 (段 2・段 3 は read-only sandbox)。

## 0. spec が固定する field

`ReviewedSpec` の top-level key は 8 つ (`orchestrator/campaign/s8b_oracle_spec.py:25-34`):
`schema_version` / `schedule_parameters` / `schedule_sha256` / `run_contract` /
`campaign_ids` / `binding_identity` / `generator_versions` / `allowed_excluded_reasons`。
`schedule_parameters` の key は 5 つ (同 `:35-41`):
`n` / `master_seed` / `block_sizes` / `holdout_ids` / `configuration_ids`。

## 1. 分類は 2 段階に分けて読む

段 3 レンズ B の指摘を採用した。**同じ値でも「spec 承認段階で何が検査されるか」と
「本走段階で何が検査されるか」が違う。** 一つの欄にまとめてはならない。

| 項目 | 候補値 | spec 承認段階の検査 | 本走段階の検査 | 決定者 |
|---|---|---|---|---|
| `schema_version` | `"s8b-oracle-reviewed-spec/v1"` | literal 一致 (`s8b_oracle_spec.py:18,109-110`) | — | **validator 固定** |
| `n` | 導出根拠なし (§2) | 正整数のみ (`s8b_oracle_manifest.py:226-227`) | schedule 行数・cell 件数と一致 (`s8b_oracle_judge.py:201-208,260-264`) | **ユーザー選択**。ただし §2 |
| `master_seed` | 未確定。形の先例は ISO-8601 JST (§4) | 非空文字列のみ (`s8b_oracle_manifest.py:196-200`) | shuffle seed の domain separation に入る (同 `:203-212`) | **ユーザー選択** |
| block ID | `"b0"` (草案) | 非空文字列 | exact 1 block (`s8b_oracle_manifest.py:302-305`) | **ユーザー選択** |
| `block_sizes` | `{"b0": n}` | **exact 1 block 検査は spec 層で発火しない** (§3 の N2) | `sum == n` かつ exact 1 block | 本走段階で **validator 固定**。spec 段階は**未接続** |
| `holdout_ids` | `["rr20","rr80"]` | list であることのみ (`s8b_oracle_spec.py:119-121`) | `sorted(freeze_holdouts)` と完全一致 (`s8b_oracle_manifest.py:1192-1201`) | **freeze 継承** (自由度ゼロ) |
| `configuration_ids` | `["backoff_fixed_best","ident_all","p2_2_flag_opt","sort_best","stock_common","system_gate"]` | list であることのみ | sort 済みかつ各 holdout の構成集合と一致 (同 `:1202-1213`) | **freeze 継承** (自由度ゼロ) |
| `campaign_ids` | `{"b0": "s8b-oracle-b0-<承認日>"}` (草案) | block と一対一・値重複なし (`s8b_oracle_spec.py:147-158`) | path traversal 防御のみ (`layout.py:212-219`)。**repo 全体の衝突検査は存在しない** | **ユーザー選択** |
| `schedule_sha256` | 機械算出 | `build_schedule` 再生成値と一致 (`s8b_oracle_spec.py:131-137`) | — | **導出値** |
| `run_contract.verify` | `"legacy+s2"` | 完全一致 (`s8b_oracle_manifest.py:399-400`) | — | **validator 固定** |
| `run_contract.screening` | `"off"` | 完全一致 (同 `:401-402`) | — | **validator 固定** |
| `run_contract.bench_max_rounds` | `1` | **1 完全一致** (同 `:415-417`。正整数一般でない) | — | **validator 固定** |
| `run_contract.reps` | `5` | `s8b_experiment_numbers.APPROVED_REPS` と完全一致 (同 `:418-422`) | — | **validator 固定** (2026-07-19 裁定済み) |
| `run_contract.extime` | `5` | `APPROVED_EXTIME_S` と完全一致 (同 `:423-427`) | — | **validator 固定** (同上) |
| `run_contract.clocks` | `2100` | 正整数のみ | env 契約の `clocks_per_us` と完全一致 (`s8b_oracle_driver.py:886-889`) | **env 契約が固定** (ユーザー選択ではない) |
| `run_contract.env_tag` | `"pegasus"` | 非空文字列のみ | `RatifiedFreeze.env_tag` と一致 (`s8b_oracle_driver.py:862-869`) | **freeze 継承** (ユーザー選択ではない) |
| `run_contract.contract_sha256` | `"e576e9cd…"` (pegasus generation 1) | 64hex の書式のみ (`s8b_oracle_manifest.py:405-407`) | `env_contract.lookup` の実値と完全一致 (`s8b_oracle_driver.py:882-885`) | **活性 activation が固定** (§5 の失効リスク) |
| `run_contract.ccbench_pin` | **二択で未決** | 非空文字列のみ | binary receipt の pin と完全一致 (`s8b_oracle_driver.py:949-958`) | **本走目的依存** (package.md §1) |
| `generator_versions` | 5 key の `{path, sha256}` (§6) | canonical path 一致 + 実 byte hash 一致 (`s8b_oracle_manifest.py:53-62,430-470`) | — | **現 source からの機械導出** |
| `binding_identity` | **現時点で導出不能** | 自己 hash と cell 集合のみ (`s8b_oracle_spec.py:160-165`) | 実 binding 照合は marker 作成**後** (`s8b_oracle_driver.py:1462-1475`) | **導出不能** (§7) |
| `allowed_excluded_reasons` | floor の 4 件は**流用未承認** (§8) | 非空・重複なしのみ (`s8b_oracle_spec.py:171-177`) | 形式検査のみ | **ユーザー承認が要る** (未起案) |

**要旨: ユーザーが選ぶ余地があるのは 4 項目** (`n` / `master_seed` / block ID / `campaign_ids`)
**と、`allowed_excluded_reasons` の流用可否、そして本走目的の 1 問である。**
親が当初 `clocks` と `env_tag` をユーザー承認項目に分類したのは誤りで、段 3 が倒した。

## 2. `n` — 導出できない

**親は当初 `n = 8` を推奨したが撤回した。** 詳細は `package.md` §5。

- a12 stress-check は根拠にならない。a12 の `J` は t139/a11 study の cluster 数であり、
  判定式は `mean - q*sqrt(s/J) > 0`。配線されている `judge_oracle` は median of medians +
  float 完全一致 argmax であって、別の規則である (§3 の N1)。
- 較正からの導出も同定されない。親が使った `1.253*sigma/sqrt(n)` は iid な単一標本中央値の
  漸近式だが、実 estimator は reps=5 の内側 median の外側 median という二段推定であり、
  certified 条件が使うのは on と off の**差**である (共分散が要る)。
  Pegasus の登録済み較正は rr50・120 秒 noise run での within-run CV であって、
  対象 (rr20/rr80・extime=5) の between-run 分布ではない。
  between-run の実測は linux-baremetal の rr5 / rr50 / rr95・extime=3 しか無い。
  per-pair floor の実値も未確定 (`holdout_freeze.json` の `floor` は `null`)。
- **同じ仮定の変奏で必要な n が 7 から 14 まで振れる** (段 3 が算術で提示)。

**書けるのは費用点だけ:** 純測定時間 = 12 cell × n × 5 rep × 5 秒。
n=8 なら 2400 秒 = 40 分 (retry・build・queue 待ちは別)。

**n を導出可能にするために要る pilot:** Pegasus・rr20/rr80・extime=5・対象 configuration で
outer trial median の between-run および paired 差の分布を取得し、
誤選択率または検出力の目標を**事前固定**してから再導出する。

## 3. 単一 block 契約 (A3-3) が spec 層で発火しない

`validate_reviewed_spec` は `build_schedule` を呼ぶだけで `_validate_schedule` を通さない
(`orchestrator/campaign/s8b_oracle_spec.py:123-137`)。
`build_schedule` は複数 block を許し (`s8b_oracle_manifest.py:221-270`)、
exact 1 件の検査は `_validate_schedule` にしかない (同 `:302-305`)。
manifest builder は書込前にこれを発火し (同 `:712-725`)、`verify_manifest` も再検査する。

**帰結:** 複数 block の spec は承認を通過し、manifest 生成で初めて落ちる。
承認手番と durable pin / receipt を消費した後に失敗する。
下流が fail-closed なので誤選択には至らず、欠陥は承認整合性と可用性に限定される。

**推奨:** 別 wave で schedule validator を共有公開関数化し、spec 承認前に発火させる。
2 block の canonical spec が承認前に落ちる負例を併せて追加する。

## 4. `master_seed` — ISO-8601 は先例であって要件ではない

floor protocol の `master_seed` は `"2026-07-18T17:16:12+09:00"` であり、
`s8b_approved.py` も同値を持つ。一方 oracle 側の validator は
`master_seed` を非空 identifier として受けるだけである
(`orchestrator/campaign/s8b_oracle_manifest.py:196-200`)。
slug 形式 (entry 511 の草案) も形式上は通る。

**ISO 形式を必須として提示すると、先例を code contract と誤認させる。**
形式の選択と実値の決定は別判断とし、実値は「結果を見る前に確定する」ことだけを要件とする。

## 5. `contract_sha256` の世代失効リスク

`orchestrator/campaign/env_contract.py` には pegasus の generation 2 が存在し、
その `contract_sha256` は `1346c20b…` である。
一方 `orchestrator/campaign/env_contract_activations/00000001.json` が active としているのは
generation 1 の `e576e9cd…` だけである。
spec はこの値を pin し、driver が `env_contract.lookup` の実値との完全一致を検査する。

**帰結: activation serial が進むと、承認済み spec が実行時に止まる。**
承認の有効期間が activation 世代に束縛されることを、承認時に明記する必要がある。

## 6. `generator_versions` の現 HEAD 実値 (330f67d0 時点)

canonical path は code が固定する (`orchestrator/campaign/s8b_oracle_manifest.py:53-62`)。
sha256 は承認時点で取り直す。

| key | path | sha256 (330f67d0 時点) |
|---|---|---|
| artifacts | `orchestrator/campaign/s8b_oracle_artifacts.py` | `b29f3dd6d989044a39f568f9e3621d93a66101b038e9a1913c3500c5e522f614` |
| judge | `orchestrator/campaign/s8b_oracle_judge.py` | `6e90a77532e7ea68c14c2076268e38783180c6c142d23ed9ae7d09466201a0b2` |
| materializer | `orchestrator/campaign/s1_direct_comparison.py` | `38ed8790807e3f1aa7516fd286b365dfe2dc45c18f05fb4566970a587db75e7f` |
| outcome_stage_contract | `orchestrator/campaign/s8b_outcome_stage_contract.py` | `f8a0bb2237dcaf3c643a78c04ca6b8cea2a8f83e3d306d85c781716b165c73af` |
| report | `orchestrator/campaign/s8b_oracle_report.py` | `cc28c86074aead3747eadcaaf1a09a2eaf4bdaae0ca72cca4a9d4f32bfd5acbf` |

**この 5 件が 1 byte でも変われば承認は失効する。**
最終承認はこの 5 source の改修が実質的に止まってからでなければ意味を持たない
(entry 511 の Q4 で親が述べた根拠はここにある)。

## 7. `binding_identity` — 導出不能

schema は 12 entry (holdout 2 × configuration 6)、各 entry は
`holdout_id` / `configuration_id` / `entry_sha256` / `genome_canonical` / `src_token` /
`variant_id` / `binding_sha256` の 7 key で、`binding_sha256` は
`{genome_canonical, src_token, variant_id, entry_sha256}` の canonical JSON hash である
(`orchestrator/campaign/s8b_oracle_manifest.py:63-66,487-537`)。

authority は `LaunchValidatedFreeze.binaries_by_cell` であり
(`orchestrator/campaign/s8b_ratified_freeze.py:766-794`)、これは ratified freeze の
`launch_validate` からしか出ない。**active ratified freeze は不在である。**

加えて段 3 レンズ B の指摘: spec 層の検査は自己 hash と cell 集合だけで、
実 binding との照合は campaign marker 作成**後**に起きる
(`orchestrator/campaign/s8b_oracle_driver.py:1462-1475`)。
**誤った binding は one-shot の初回実走を消費してから拒否される。**
entry 511 が挙げた欠陥がそのまま残っている。

## 8. `allowed_excluded_reasons` — floor からの流用は未承認

floor の 4 件は `["competing_process","launch_failure","nonfinite_or_partial_output","performance_anomaly"]`
で、固定順として `s8b_floor_contract.py` が完全一致を強制している。
一方 oracle 側の validator は非空・重複なししか検査しない
(`orchestrator/campaign/s8b_oracle_spec.py:171-177`)。report も list の形式だけを見る。

**形と順序の先例はあるが、意味の継承は成立していない。**
oracle 固有の failure event と除外理由の対応表を承認せずに流用すると、
**除外裁量の境界を未承認のまま固定する**ことになる。

**推奨:** floor からの流用を既定にせず、oracle 固有の理由集合と event 対応表を別裁定とする。

## 9. 先行 blocker

`APPROVED_SPEC_SHA256` に何を書いても、次の 3 つが揃うまで本走には近づかない。

1. **active ratified freeze が不在。** `output/s8b-freeze/` に approval / active / revocation の
   世代 file が 1 件も無い。`build_approved_manifest` は spec より先に active freeze を読む。
2. **`holdout_freeze.json` の `floor` と `budget` がともに `null`。**
3. **承認の trust root が不在** (`package.md` §2)。
