## 変更計画

### `orchestrator/campaign/genome.py`

参照: [genome.py:74](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/orchestrator/campaign/genome.py:74)

- 現在の挙動
  - `SILO_SPACE` だけが定義され、`SPACES` は `{"silo": SILO_SPACE}` のみです (`:74-90`)。
  - `space_for()` は未登録 protocol を `KeyError` にします (`:93-96`)。
- 変更後の挙動
  - `MOCC_SPACE` を追加し、次の 3 ブール軸、制約なし、raw/effective ともに 8 genome とします。
    - `BACK_OFF`: universal cache option は [Options.cmake:20](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/external/ccbench/cmake/Options.cmake:20)、全 protocol への供給は [ProtocolHelpers.cmake:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/external/ccbench/cmake/ProtocolHelpers.cmake:29)、mocc の live 分岐は `transaction.cc:981,1087`。
    - `TEMPERATURE_RESET_OPT`: default は `1` (`Options.cmake:48`)、mocc target への供給は [mocc/CMakeLists.txt:6](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/external/ccbench/cc/mocc/CMakeLists.txt:6)、live 分岐は `transaction.cc:827` と `util.cc:208`。
    - `KEY_SORT`: default は `0` (`Options.cmake:26`)、mocc target への供給は `mocc/CMakeLists.txt:7`、YCSB access order の live 分岐は `include/ycsb.hh:81-83`。
  - `SPACES` は `silo` と `mocc` の 2 件にします。
- 除外する軸
  - `RWLOCK` は `mocc/CMakeLists.txt:5` の bare define です。`#ifdef RWLOCK` が常に真になり、対応する `CCBENCH_RWLOCK` cache option もないため、`Genome.cmake_defines()` から直交的に off にできません。
  - `INSERT_READ_DELAY_MS` / `INSERT_BATCH_DELAY_MS` は `Options.cmake:38-39` で空既定です。mocc の read delay 呼び出しはコメントアウト (`transaction.cc:609-610`)、残りは表示用途 (`util.cc:230-234`) であり、探索軸にしません。将来 live になっても計測撹乱ノブです。
  - `TRACE` は `Genome` の予約名として拒否済みです ([model.py:49](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/orchestrator/campaign/model.py:49))。
  - `KEY_SIZE`、`VAL_SIZE`、`MASSTREE_USE` は workload/storage 条件、`ADD_ANALYSIS` は計装なので固定します。
- tictoc/cicada
  - 本 wave では登録しません。初手 mocc という D1360 に合わせた段階導入とします。
  - tictoc/cicada の CMake option 群には別の意味制約調査が必要で、両 `transaction.cc` とも現 pin の `TRACE` 出現は 0 件でした。形だけ登録して探索可能に見せるのは避けます。
- 変更しない部分
  - silo の 8 genome、XOR 制約、canonical 順序は変更しません。
  - mocc 登録だけでは計測や COMMIT を解禁しません。`space_for()` の現行 production caller はありません。

### `orchestrator/campaign/between_run_floor.py`

参照: [between_run_floor.py:53](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/orchestrator/campaign/between_run_floor.py:53)

- 現在の挙動
  - `BASELINE` は silo 固定です (`:57-59`)。
  - `measure_point_floor()` は返却 JSON の `genome` にその固定値を入れます (`:96-145`)。
  - path は `between_run_noise_t...` で protocol がありません (`:148-162`)。
  - `main()` は常に同じ silo genome を build します (`:193-237`)。
- 変更後の挙動
  - baseline を protocol から引く `BASELINES` にします。
    - silo は現行値をそのまま維持。
    - mocc stock preimage は CMake defaults に対応する `Genome("mocc", {"BACK_OFF": 1, "KEY_SORT": 0, "TEMPERATURE_RESET_OPT": 1})`。
  - CLI に既定 `silo` の `--protocol` を追加し、既存の `[point]` 呼び出しは維持します。
  - `measure_point_floor()` は選択された baseline を引数で受け、JSON の既存 `genome` field に canonical を記録します。新しい `protocol` field や schema version は不要です。
  - 新規 protocol の stem は `between_run_noise_<protocol>_t...` とします。既存 silo path は互換例外として現行 stemを維持し、既存ファイルがあれば create-only で拒否します。
  - JSON/Markdown は上書きではなく create-only にし、既存 `output/env/*/calibration/between_run_noise_*.json` の bytes を変更できないようにします。
  - 現 pin で floor production を許す protocol 集合は `{"silo"}` に閉じます。`mocc` は protocol/point 解決後、単一テナント確認、build、measure、write より前に拒否します。
- TRACE 実測確認
  - submodule HEAD は `511c9538e4e8efa54b45cda62e72389ed3b706ec` でした。
  - `rg -o TRACE external/ccbench/cc/mocc/transaction.cc | wc -l` は **0**、silo は **15** でした。
  - したがって mocc stock build/floor の経路は本 wave では開きません。TRACE 移植後に admission 集合を別変更で進める形です。
- 変更しない部分
  - reps、sessions、workload、測定処理、build admission、環境選択は変えません。
  - 新規測定、build、qsub、既存成果物の再生成は行いません。

### `orchestrator/campaign/screening_driver.py` と caller

参照: [screening_driver.py:126](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/orchestrator/campaign/screening_driver.py:126)

- 現在の挙動
  - `load_between_run_floor()` は workload だけで絞り、同じ workload がちょうど 1 件でなければ拒否します (`:126-159`)。
  - `prepare_screening_campaign()` も protocol を持たず、その loader を呼びます (`:175-220`)。
- 変更後の挙動
  - `load_between_run_floor(workload, *, protocol, calibration_dir="")` とし、workload が一致した JSON の `genome` canonical から `|` より前を取得して protocol も照合します。
  - protocol は必須 keyword にして、directory path が誤って protocol positional 引数になる互換事故を防ぎます。
  - 同一 workload に silo と mocc が 1 件ずつあれば、要求 protocol の 1 件だけを選びます。同一 protocol が複数なら従来どおり拒否します。
  - workload 一致 JSON の `genome` 欠落・非文字列・canonical 不正は拒否します。実在する既存 between-run JSON 4 件はいずれも `genome` を持っています。
  - `prepare_screening_campaign()` に required keyword `protocol` を加え、loader へ渡します。
  - caller は実 baseline から protocol を渡します。
    - [backoff_sweep.py:131](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/orchestrator/campaign/backoff_sweep.py:131): `baseline.protocol`
    - [s6_sort_sweep.py:270](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/orchestrator/campaign/s6_sort_sweep.py:270): stock `_genome(0).protocol`
    - [s8a_trigger_sweep.py:369](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/orchestrator/campaign/s8a_trigger_sweep.py:369): ident baseline `_genome(1).protocol`
- scope 判定
  - `screening_driver` と 3 caller は scope 内に含める必要があります。除外すると、新しい `between_run_noise_mocc_*.json` が同じ calibration directory に置かれた時点で silo screening も `matches=2` になり壊れます。
- 変更しない部分
  - schema version、CV 値域、screening policy、baseline 再測、verify/COMMIT の契約は変えません。

### `orchestrator/campaign/layer3_report.py`

参照: [layer3_report.py:306](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/orchestrator/campaign/layer3_report.py:306)

- campaign 側の protocol
  - campaign.lock の exact identity key は `spec_content/ccbench_commit/search_tag/search_config/trial` だけです ([campaign_lock.py:19](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/orchestrator/campaign/campaign_lock.py:19))。`build_report()` もこの 5 キーを強制しています (`layer3_report.py:519-555`)。専用 `protocol` field は**実在しません**。
  - `search_config["scale"] == "silo"` の例はありますが、`CampaignConfig.search_config` は任意 dict ([model.py:67](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/orchestrator/campaign/model.py:67)) であり protocol 契約ではないため使いません。
  - whiteboard は `iteration/direction/magnitude/result/delta_pct` だけです ([p3_s4_loop.py:741](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/orchestrator/campaign/p3_s4_loop.py:741))。protocol は実在しません。
  - variant 名も canonical ではなく 12 桁 hash です ([pipeline.py:119](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/orchestrator/campaign/pipeline.py:119))。
  - protocol の一次値は WAL `build_start.payload.genome` です。全 pipeline が `Genome.canonical()` を記録します (`pipeline.py:893-902,997-1008`)。canonical の protocol 部は [model.py:56](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/orchestrator/campaign/model.py:56) の `"<protocol>|..."` です。
- 変更後の挙動
  - `_variant_rows()` 付近に canonical から protocol を取る局所 helper と、全 `build_start` から campaign protocol を集約する helper を追加します。
  - protocol が一意な YCSB campaign だけ report-level floor を照合可能にします。protocol が欠落・不正・複数なら report 自体は生成可能ですが、両 floor は `no-matching-env-record` とし、検索詳細に「campaign protocol を一意に決められない」と残します。単一 report-level floor を混在 campaign に誤適用しません。
  - `_calibration_floors()` (`:333-420`) のキーを `(protocol, records, threads, workload)` にします。
  - `criteria` と `mismatches` に protocol を追加し、matched/no-match の floor result に campaign protocol を記録します。
- floor 側の protocol
  - between-run JSON は既に `genome` を持つため、その canonical の protocol 部で足ります。producer の JSON field 追加は不要です (`between_run_floor.py:131-145`)。
  - 現行 within-run calibration は [calibrator/report.py:72](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/orchestrator/calibrator/report.py:72) と `calibrator/cli.py:1077-1085` が作り、top-level `genome` を持ちません。
  - bytes 互換のため、`noise_floor` block を持ち `genome` がない歴史的 record は **legacy implicit silo** としてのみ照合します。mocc campaign には一致させません。
  - 将来 non-silo within-run calibration を作る producer は top-level `genome` canonical を追加する必要があります。本 wave では非 silo calibration の測定も producer 拡張も行いません。
  - between-run record の `genome` 欠落・不正は producer contract 違反として拒否します。
- 変更しない部分
  - WAL admission、source-ref bijection、verify/COMMIT 投影、acceptance receipt は変更しません。
  - wrong-protocol floor は report 全体のエラーではなく「一致なし」になります。

### `orchestrator/campaign/layer3_schema.json`

参照: [layer3_schema.json:188](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2115-cross-protocol-impl/orchestrator/campaign/layer3_schema.json:188)

- 現在の挙動
  - `noise_floor` と `floor_result` は `additionalProperties:false` です (`:188,255-258`)。
- 変更後の挙動
  - `floor_result` の matched/no-match 両 branch に optional `protocol` string property を追加します。
  - `required` には加えません。新 report は一意な campaign protocol がある場合に出力し、既存 report は protocol 無しのまま valid です。
  - `search` は既に自由 object なので criteria への protocol 追加に schema 変更は不要です。
- 変更しない部分
  - `schema_version` は `layer3-material-report/v3` のままです。
  - 既存 report の再生成や migration は要求しません。

### floor JSON の参照関係

grep で確認できた関係は次のとおりです。

| file | 関係 |
|---|---|
| `between_run_floor.py:148-190` | 公式 `between_run_noise_*.json` writer |
| `screening_driver.py:126-159` | `between_run_noise_*.json` の直接 reader |
| `backoff_sweep.py:167-176` | screening reader の間接 caller |
| `s6_sort_sweep.py:280-284` | screening reader の間接 caller |
| `s8a_trigger_sweep.py:380-384` | screening reader の間接 caller |
| `layer3_report.py:333-420,585-587` | calibration directory の全 `*.json` を読み、`noise_floor` / `between_run` block を分類 |
| `calibrator/report.py:72-84`, `calibrator/cli.py:1077-1085` | within-run `noise_floor` JSON producer |
| `pegasus_floor_scoping.py:135-201` | `scoping_between_run_*.json` writer。repository 外を強制し、公式 glob には接続されない |
| `backoff_sweep_report.py`, `p2_2_report.py`, `backoff_extended_sweep_report.py` | floor 定数・provenance の利用のみ。floor JSON reader/writer ではない |

## 受理集合の変化

| 入力・操作 | 変更前 | 変更後 |
|---|---|---|
| `space_for("silo")` | 受理、8 genome | 変化なし |
| `space_for("mocc")` | `KeyError` | 受理、3 ブールの 8 genome |
| `space_for("tictoc"/"cicada")` | `KeyError` | 変化なし |
| floor CLI の従来 `[point]` | silo で受理 | silo 既定で受理 |
| floor CLI `--protocol mocc`、現 pin | 指定不能 | build/measure 前に拒否 |
| 同一 workload の silo + mocc floor を置いた screening | 2 件として拒否 | 要求 protocol の 1 件を受理 |
| 同一 workload・同一 protocol の floor 2 件 | 拒否 | 変化なし |
| workload 一致だが `genome` 欠落・不正の between-run floor | protocol を見ず受理し得る | 拒否 |
| layer3: shape 一致・protocol 不一致 floor | 誤って一致し得る | report は受理、floor は no-match |
| layer3: protocol が複数または不明の campaign | shape だけで floor が一致し得る | report は受理、report-level floor の割当は拒否 |
| legacy within-run floor、silo campaign | 受理 | implicit silo として受理 |
| legacy within-run floor、mocc campaign | 誤って一致し得る | no-match |
| protocol field のない既存 layer3 report | 現行 schema で受理 | 引き続き受理 |
| protocol が非文字列の新 floor result | field 自体が許可されない | schema で拒否 |

## テスト計画

### 影響を受ける既存 test

- `orchestrator/tests/test_campaign.py:216-288`
  - silo space と決定論的列挙は回帰確認し、mocc ケースを追加します。
- `orchestrator/tests/test_guided.py`
  - `SILO_SPACE` の直接 import は挙動不変ですが回帰対象です。
- `orchestrator/tests/test_between_run_floor.py:138-446`
  - `_write_out()`、`measure_point_floor()`、`main()` の baseline/protocol 引数に追随します。
- `orchestrator/tests/test_screening_driver.py:130-372`
  - `_write_floor()` fixture に canonical `genome` を追加し、loader 7 test と prepare 5 test に required protocol を渡します。
- `orchestrator/tests/test_p2_2_site_aware.py::test_backoff_sweep_screening_reuses_one_resolved_runtime`
  - `prepare_screening_campaign` の captured kwargs に `protocol=="silo"` を追加確認します。
- `orchestrator/tests/test_t1416_backoff_compiler_binding.py::test_screened_workload_forwards_expected_toolchain_to_baseline_and_candidate`
  - 同じく baseline protocol の転送を確認します。
- `orchestrator/tests/test_layer3_report.py:2760-2880`
  - floor fixture に canonical genome を追加し、照合 criteria/protocol を更新します。
- `orchestrator/tests/test_layer3_report.py:1484-1535`
  - 保存済み v2/v3 report の後方互換 test に、floor protocol を除いた document の検証を追加します。
- `test_layer3_admission_diagnosis.py`、`test_autonomous_trial_completeness.py`、`test_t126_qualification_artifacts.py`、`test_trial_registry.py`
  - `layer3_report` 直接 consumer として回帰実行します。公開 API は変えません。

### 新規・改訂 nodeid 候補

| nodeid | 正例・負例 | 実体を通す内容 |
|---|---|---|
| `test_campaign.py::test_mocc_space_has_eight_live_boolean_genomes` | 正例 | 実 `space_for("mocc").enumerate()` が 3 軸・8 canonical genome を返す |
| `test_campaign.py::test_mocc_space_excludes_fixed_and_measurement_axes` | 負例 | 実 `MOCC_SPACE.axes` に `RWLOCK`、delay、`TRACE` 等がない |
| `test_campaign.py::test_tictoc_and_cicada_remain_unregistered` | 負例 | 実 `space_for()` が両 protocol を拒否 |
| `test_between_run_floor.py::test_protocol_selects_matching_baseline_and_output_stem` | 正例 | 実 main の protocol 解決から selected `Genome`、result genome、path stem まで通す。build/measure の重い sink だけ spy 化 |
| `test_between_run_floor.py::test_mocc_floor_rejected_before_build_or_measure_without_trace_hook` | 負例 | 実 main admission を通し、build/measure/write spy が 0 回であることを確認 |
| `test_between_run_floor.py::test_write_out_is_create_only_and_preserves_existing_bytes` | 負例 | 実 `_write_out()` を既存 path に当て、例外後の bytes が同一であることを確認 |
| `test_screening_driver.py::test_load_between_run_floor_selects_requested_protocol_among_same_workload` | 正例 | silo/mocc の実 JSON 2 件を actual loader に読ませ、要求した方の CV を返す |
| `test_screening_driver.py::test_load_between_run_floor_rejects_duplicate_same_protocol` | 負例 | 同一 protocol 2 件を actual loader が一意性違反で拒否 |
| `test_screening_driver.py::test_load_between_run_floor_rejects_missing_or_malformed_genome` | 負例 | workload 一致 record の実 parser 経路で欠落・不正 canonical を拒否 |
| `test_layer3_report.py::test_floor_match_uses_protocol_records_threads_and_workload` | 正例 | mocc campaign と silo/mocc floor を actual `build_report()` に渡し、mocc だけが source hash 付きで入る |
| `test_layer3_report.py::test_wrong_protocol_floor_is_reported_as_mismatch` | 負例 | shape 同一・protocol 不一致で report は生成されるが floor value は null |
| `test_layer3_report.py::test_mixed_protocol_campaign_cannot_receive_report_level_floor` | 負例 | 複数 protocol の実 build_start 群を通し、report-level floor が付かない |
| `test_layer3_report.py::test_legacy_silo_within_floor_without_genome_still_matches` | 正例 | 既存形の `noise_floor` JSON が silo にだけ一致 |
| `test_layer3_report.py::test_existing_report_without_floor_protocol_remains_schema_valid` | 正例 | 新 builder の protocol property を削除した保存済み相当 v3/v2 を actual schema validator が受理 |
| `test_layer3_report.py::test_schema_rejects_non_string_floor_protocol` | 負例 | `additionalProperties:false` を保った実 schema が不正型を拒否 |

pytest、build、測定、qsub は実走していません。

## 依存と分割

producer/consumer 契約は次のようにまたがります。

```text
Genome.canonical()
    ├─ between_run_floor.py ── genome + protocol別path ──┐
    ├─ pipeline.py ── WAL build_start.payload.genome ───┤
    │                                                    ├─ layer3_report.py
    └─ screening caller baseline.protocol ───────────────┤       └─ layer3_schema.json
                                                         └─ screening_driver.py
```

- floor 契約部分は `between_run_floor.py`、`screening_driver.py`、3 caller、`layer3_report.py`、schema を 1 単位で land すべきです。producer だけ先行すると同一 workload の第 2 protocol floor で既存 screening が壊れます。
- genome 登録は技術的には別単位へ分けられます。
  - 単位 A: `genome.py` + `test_campaign.py`
  - 単位 B: floor producer/consumer/schema + 各専用 test
- A/B の production ownership path は素集合ですが、T-2115 の受入確認は両方をそろえた 1 wave とするのが安全です。
- `test_campaign.py` は A 専有、B の test は `test_between_run_floor.py`、`test_screening_driver.py`、`test_layer3_report.py` と caller test 群に閉じます。

## リスクと未確定

- mocc の `TRACE` 0 件は確認済みですが、silo の 15 出現は hook の意味論全体をこの静的調査だけで再証明するものではありません。既存 certified silo 経路を変更しない前提です。
- legacy within-run JSON には protocol/genome の一次 field が実在しません。implicit silo は既存 bytes と現行用途を維持するための限定互換規則であり、non-silo へ一般化しません。
- report-level `noise_floor` は 1 protocol を前提とする形です。複数 protocol を 1 campaign に混在させる将来仕様には per-protocol map への schema 再設計が必要ですが、本 wave では作りません。
- tictoc/cicada の live 軸、意味制約、baseline は確定していません。そのため同時登録しません。
- read-only 静的調査のみで、pytest、build、測定、成果物生成は行っていません。

## 総括

mocc は 3 ブール・8 genome で登録するが、現 pin の TRACE 0 件により floor production は拒否します。  
campaign protocol は lock/whiteboard/hashではなく WAL `build_start.payload.genome` から取得します。  
between-run JSON の既存 `genome` で protocol 軸を立て、screening と layer3 を同時に追随させます。  
既存 floor bytes と既存 layer3 report は変更せず、schema は optional 追加で後方互換を保ちます。