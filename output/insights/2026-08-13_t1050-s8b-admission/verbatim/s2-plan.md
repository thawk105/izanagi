## 変更面の地図

現行の受理・拒否挙動は次のとおりである。

| 条件 | 現行挙動 | 根拠 |
|---|---|---|
| (a) receipt 不在 | 受理する。portable record の exact key 集合に receipt がない | [s8b_floor_campaign.py:177–181](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/campaign/s8b_floor_campaign.py:177)、[s8b_ratified_freeze.py:181–185](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/campaign/s8b_ratified_freeze.py:181) |
| (b) receipt と record の不一致 | 検査不能なので受理する。path、hash、binding の局所検査しかない | [s8b_floor_campaign.py:1485–1521](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/campaign/s8b_floor_campaign.py:1485) |
| (c) 別 cell の valid receipt との組替え | record 自体の cell、freeze binding の明白な組替えは一部拒否するが、admission の発行対象 cell は確認できない | [s8b_ratified_freeze.py:1643–1723](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/campaign/s8b_ratified_freeze.py:1643) |
| (d) store bytes 差し替え | hash 不一致なら既に拒否する。ただし hash は admission の証明ではない | [s8b_floor_campaign.py:2172–2240](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/campaign/s8b_floor_campaign.py:2172)、[s8b_oracle_driver.py:927–949](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/campaign/s8b_oracle_driver.py:927) |

変更面は以下である。

| ファイルと行 | 現行責務 | 計画上の役割 |
|---|---|---|
| [build_admission.py:309–346, 647–747](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/campaign/build_admission.py:309) | sealed admission の発行、current policy、source root を含む canonical receipt の検証 | 原則変更しない。新しい durable receipt の発行時に完全な元 receipt を再検証する正本 |
| [buildcache.py:620–645, 918–1005, 1230–1278](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/campaign/buildcache.py:620) | completion manifest 内で admission、current source、binary bytes を検査するが、`BuildResult` から receipt を落とす | production 変更なし。既存 gateway 束縛を回帰テストで維持 |
| `orchestrator/campaign/s8b_binary_admission.py:1` | 新規 | root 非依存の canonical durable receipt、その発行器、exact validator、portable record key 正本 |
| [s8b_materialization.py:51–95](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/campaign/s8b_materialization.py:51) | binding と S8b review capability の producer | canonical SHA helper を新しい leaf へ寄せ、store/resume が未閉鎖という docstring を更新 |
| [s8b_floor_campaign.py:1334–1566](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/campaign/s8b_floor_campaign.py:1334) | build、portable projection、deserialize | receipt の発行、保存、current policy と record/freeze binding の照合 |
| [s8b_floor_campaign.py:2172–2240, 2463–2485, 3414–3519, 3670–3722](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/campaign/s8b_floor_campaign.py:2172) | store、resume、floor 測定直前検査 | 書込前、resume、測定直前の三境界で receipt と bytes を再検証 |
| [s8b_floor_stats.py:591–619, 880–929](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/campaign/s8b_floor_stats.py:591) | result の binary hash と journal receipt の照合 | binaries がある artifact では admission receipt を必須化 |
| [s8b_holdout_freeze.py:1275–1361](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/campaign/s8b_holdout_freeze.py:1275) | official floor result から g1 candidate を作る入力検証 | v1 freeze entry と receipt subject を照合してから floor を採用 |
| [s8b_ratified_freeze.py:1643–1804, 2156–2222, 3132–3239](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/campaign/s8b_ratified_freeze.py:1643) | manifest/result/binding chain の ratified 検証 | manifest と result の両方で receipt、current policy、freeze entry を検証 |
| [s8b_oracle_driver.py:832–954, 1273–1296](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/campaign/s8b_oracle_driver.py:832) | oracle 実走前に store の存在と hash を確認 | receipt 検査を store 読込より前へ置き、marker、WAL 作成前に拒否 |

対象を必須 producer、consumer、test の12ファイルに限定して検索した結果、JSON key としての `"admission_receipt"` は0件だった。既存の `_admission_receipt_sha256` は review receipt 用 helper であり、portable record には届いていない。

## プラン

### Production

1. canonical durable receipt を新しい leaf に置く

   `orchestrator/campaign/s8b_binary_admission.py:1` を新設する。`s8b_materialization.py` を直接拡張しない理由は、純関数である `s8b_floor_stats.py` から `pipeline`、`s1_direct_comparison` まで重い依存を引かないためである。

   portable record に exact key `"admission_receipt"` を追加する。receipt は次を exact key で持つ。

   - `schema = "s8b-binary-admission/v1"`
   - `admission`: `schema`、`class`、`policy_sha256`、`review_id`、`input_sha256`、root 非依存の `source`
   - `source`: `schema`、`ccbench_commit`、`genome_sha256`、`src_token`、`source_bytes_sha256`、`tracked_clean`、`tracked_diff_sha256`、`tracked_paths`
   - `subject`: `cell_id`、`holdout_id`、`configuration_id`、`entry_sha256`、`binding_sha256`、`binary_sha256`、`contract_sha256`、`trace`
   - `receipt_sha256`: 上記 unsigned body の canonical SHA-256

   発行器は sealed `BuildAdmission`、`BuildRunContext.policy`、`SourceEvidence` を `require_build_admission()` で再検証してからのみ receipt を作る。さらに `class == human-reviewed`、`review_id == s8b-floor`、`input_sha256 == binding.entry_sha256`、source の genome digest、`src_token`、ccbench pin、実 binary bytes、`trace is False`、contract を照合する。

   validator は exact key、schema、outer SHA、current policy、source と binding、subject と portable record の完全一致を要求する。hash だけを渡す API、未知 key を削って続行する API、receipt 不在の fallback は作らない。これにより (a)、(b)、(c) を閉じ、発行時の bytes 再計算で (d) も早期に閉じる。

2. P1 は raw receipt コピーではなく root 非依存の canonical descendant receipt に修正する

   `build-admission/v1` の `source.source_root` と nested review receipt は absolute path を含み、outer SHA もその path に依存する。一方、[test_s8b_ratified_freeze.py:1343–1354](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/tests/test_s8b_ratified_freeze.py:1343) は異なる root 間で production emitter の blob、tree、commit、mode が同一であることを要求する。

   したがって raw receipt の byte-for-byte コピーは採らない。元の完全 receipt は発行時に root を含めて検証し、永続化する descendant receipt からは location である `source_root` だけを除く。source bytes、tracked diff、paths、pin、policy、review input、cell、binding、binary は残す。この変更は hash 一致を admission とみなすものではない。

3. floor producer、store、resume を一本化する

   - [s8b_floor_campaign.py:177–181](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/campaign/s8b_floor_campaign.py:177): portable key 正本を新 leaf から import し、重複定義をなくす。
   - `build_cells():1334–1417`: build 完了直後に binary bytes を再 hash し、元 admission から durable receipt を発行して runtime record に格納する。
   - `_validate_portable_built():1485–1521`: current policy、protocol の ccbench pin、期待 cell、freeze entry を受け取り、全 record を共有 validator に通す。
   - `project_built_records():1524–1554` と `resolve_portable_built():1557–1566`: validator が返した detached canonical receipt をそのままコピーし、浅い `dict()` で nested body を共有しない。
   - `store_binaries():2172–2217`: binary を一つも複製する前に全 record の receipt を preflight する。`store_path` の basename が `binary_sha256` であることも要求し、その後に既存 bytes hash 検査を行う。
   - `_verify_resume_store():2220–2240` と `_verify_resume_binaries():3703–3722`: receipt 検査を先に行い、続けて cache binary と store bytes の両方を hash 照合する。
   - `_load_resume_manifest():3670–3700`: `freeze`、expected cells、ccbench pin、current policy を受け取り、path 解決前に receipt と freeze entry を照合する。
   - `_Runner._run_session():2463–2485`: floor 値を生成する直前にも receipt subject と実 binary hash を再検証する。
   - 呼び出し側 `2784`、`3414–3439`、`3473–3519`、`3531–3555`、`3605–3637` は同じ current policy を明示的に渡す。

   (a) は exact key、(b) は subject equality、(c) は cell と binding の複合束縛、(d) は発行時、store、resume、測定直前の bytes hash で閉じる。

4. floor result と freeze consumer を fail-closed にする

   - [s8b_floor_stats.py:591–619](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/campaign/s8b_floor_stats.py:591): `expected_admission_policy` を追加する。`binaries` が存在するときは必須とし、receipt がない record は error にする。binaries 自体がない純粋な formula unit fixture の既存経路だけは維持する。
   - `_verify_binaries_section():880–929`: full portable record exact key、receipt、record subject、ccbench pin を検証してから journal SHA と照合する。
   - [s8b_holdout_freeze.py:1308–1361](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/campaign/s8b_holdout_freeze.py:1308): current policy と v1 freeze entry を渡す。receiptless official result から g1 candidate を作らない。
   - [s8b_ratified_freeze.py:181–185](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/campaign/s8b_ratified_freeze.py:181): exact key 正本を共有 leaf へ統合する。
   - `_validate_portable_binaries():1643–1723`:既存 binding SHA と freeze entry SHA の検査後、receipt の cell、entry、binding、binary、policy、pin を検査する。
   - `_validate_result():2156–2222`: manifest で通った receipt と result の receipt を floor verifier でも独立に検証する。`result.binaries == manifest.binaries` の既存 chain は維持する。

5. oracle 実走直前を独立した最終防壁にする

   - [s8b_oracle_driver.py:844–954](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/campaign/s8b_oracle_driver.py:844): `_prepare_v2_execution` に `expected_admission_policy` を追加する。
   - schedule 各行について `LaunchValidatedFreeze.binaries_by_cell` の receipt を current policy、`run_contract["ccbench_pin"]`、ratified freeze entry、record subject と照合する。この処理は `_store_sha256()` より前に置く。
   - receipt 不在は `[admission-missing]`、canonicality、policy、record、cell、binding の不一致は `[admission-mismatch]` として `OracleDriverError` にする。
   - `run_block():1273–1296` で既に作る `build_context.policy` を渡す。拒否時は既存どおり run marker、WAL、budget を作らない。
   - receipt 検査後も `_store_sha256()` と pipeline の `expected_perf_sha256` 第二防壁を残すため、規律2を緩めない。

### Test

- `orchestrator/tests/test_s8b_binary_admission.py:1` を新設し、発行器、canonical exact keys、root 非依存性、current policy、各 subject field、unknown key、malformed body を単体検証する。
- [test_s8b_floor_campaign.py:1495–1557, 5163–5234, 6293–6368](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/tests/test_s8b_floor_campaign.py:1495) の build fake と portable fixture を production issuer 由来の receipt に更新する。
- [s8b_v2_freeze_fixture.py:109–234](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/tests/s8b_v2_freeze_fixture.py:109) は手書きの hash-only binaries を廃止し、全 cell の honest receipt を共通生成する。
- [test_s8b_ratified_verify.py:1347](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/tests/test_s8b_ratified_verify.py:1347) の coherent-island parameter に receipt 欠落、receipt swap、record mismatch を追加する。
- [test_s8b_oracle_driver.py:4451–4861](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/tests/test_s8b_oracle_driver.py:4451) の happy path、store missing、store mismatch に receipt 検査順の assertion を追加する。
- [test_s8b_holdout_freeze.py:1271–1323](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/tests/test_s8b_holdout_freeze.py:1271) に receiptless official result の拒否を追加する。
- [test_buildcache_v2.py:755–808](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/tests/test_buildcache_v2.py:755) は production 変更なしの回帰対象とする。

### 所有面が素集合になる分割

- A: `s8b_binary_admission.py`、`s8b_materialization.py`、`test_s8b_binary_admission.py`、`test_s8b_materialization.py`
- B: `s8b_floor_campaign.py`、`test_s8b_floor_campaign.py`
- C: `s8b_floor_stats.py`、`s8b_holdout_freeze.py`、`s8b_ratified_freeze.py`、`s8b_v2_freeze_fixture.py` と対応 test
- D: `s8b_oracle_driver.py`、`test_s8b_oracle_driver.py`

同一ファイルを二所有者へ割り当てない。A の API 固定後に C の fixture を更新し、B と D がそれを消費する順序にする。

## 両方向テスト

| 種別 | 候補 nodeid | 検証内容 |
|---|---|---|
| 正例 | `orchestrator/tests/test_s8b_binary_admission.py::test_issue_and_validate_binary_admission_receipt_round_trip` | sealed admission から発行し、同じ policy、source、cell、binding、binary で通る |
| 正例 | `orchestrator/tests/test_s8b_binary_admission.py::test_receipt_is_canonical_and_root_neutral` | 異なる absolute `source_root` でも同じ source bytes と binding なら durable receipt bytes が同一 |
| 正例 | `orchestrator/tests/test_s8b_floor_campaign.py::test_fresh_store_project_resume_preserves_admission_receipt` | fresh build、store、portable projection、resolve、resume の全段で receipt が同一かつ有効 |
| 正例 | 既存 `orchestrator/tests/test_s8b_oracle_driver.py::test_v2_gate_happy_path_completes_and_binds_env_store_receipt` | honest receipt を持つ store を oracle pre-run が受理する |
| (a) 負例 | `orchestrator/tests/test_s8b_floor_campaign.py::test_portable_built_rejects_missing_admission_receipt` | receipt key を削除し、deserialize 時点で拒否 |
| (a) 負例 | `orchestrator/tests/test_s8b_ratified_verify.py::test_portable_binary_coherent_island_rejected_by_exact_cause[admission-missing]` | hash、binding、store が正しくても receiptless を拒否 |
| (b) 負例 | `orchestrator/tests/test_s8b_binary_admission.py::test_validate_rejects_binary_sha_record_mismatch` | record の binary SHA と short hash、store bytes を整合させても、元 receipt の subject と違えば拒否 |
| (b) 負例 | `orchestrator/tests/test_s8b_binary_admission.py::test_validate_rejects_current_policy_and_entry_mismatch` | receipt 内 policy または review input と record binding の不一致を拒否 |
| (c) 負例 | `orchestrator/tests/test_s8b_ratified_verify.py::test_portable_binary_coherent_island_rejected_by_exact_cause[admission-receipt-swap]` | 2 cell の各 receipt は単体で valid だが、receipt だけ交換した組を拒否 |
| (c) 負例 | `orchestrator/tests/test_s8b_oracle_driver.py::test_v2_foreign_cell_admission_receipt_is_refused_before_store_read` | store bytes は正常でも別 cell receipt を store 読込前に拒否 |
| (d) 負例 | 既存 `orchestrator/tests/test_s8b_floor_campaign.py::test_resume_rejects_tampered_binary_but_succeeds_when_untampered` | valid receipt と record を残したまま disk bytes を変更すると resume を拒否 |
| (d) 負例 | 既存 `orchestrator/tests/test_s8b_oracle_driver.py::test_v2_store_hash_mismatch_is_refused` | valid receipt 後の store 差し替えを拒否し、marker、WAL を作らない |
| malformed | `orchestrator/tests/test_s8b_binary_admission.py::test_validate_rejects_unknown_missing_and_malformed_receipt_fields` | extra key、nested key 欠落、未知 schema、未知 review ID、不正 outer SHA を全て拒否 |

異なる root の正例では、既存の `test_production_emitter_staged_builder_is_git_deterministic_across_roots` を変更せず通す。期待値を緩めたり path を無視する比較へ変えたりしない。

## 変異候補

いずれも production の一つの条件分岐だけを緩める。

| 対応 | 単一変異 | 赤になるべき nodeid |
|---|---|---|
| (a) | `validate_portable_binary_record()` で `admission_receipt is None` を受理側へ反転 | `test_s8b_floor_campaign.py::test_portable_built_rejects_missing_admission_receipt` |
| (b) | receipt subject と record の `binary_sha256` equality 一箇所を削除 | `test_s8b_binary_admission.py::test_validate_rejects_binary_sha_record_mismatch` |
| (c) | subject の `(cell_id, holdout_id, configuration_id, entry_sha256, binding_sha256)` 完全一致 gate 一箇所を削除 | `test_s8b_ratified_verify.py::test_portable_binary_coherent_island_rejected_by_exact_cause[admission-receipt-swap]` |
| (d) | `_prepare_v2_execution()` の `actual != rec["binary_sha256"]` 拒否分岐だけを無効化 | `test_s8b_oracle_driver.py::test_v2_store_hash_mismatch_is_refused` |

mutation harness が parameterized nodeid を扱えない場合でも、上記 case を独立 test に分けるだけにし、production の緩和箇所は増やさない。

## 波及

- `verify_floor_artifact()` の production caller は4箇所ある。`s8b_floor_campaign.py:3543,3626`、`s8b_ratified_freeze.py:2214`、`s8b_holdout_freeze.py:1359` の全てで current policy を渡す必要がある。
- `LaunchValidatedFreeze.binaries_by_cell` の要素 shape に nested receipt が増えるため、oracle test が直接構築する validated object を更新する。
- `test_s8b_floor_campaign.py:5190–5201` の `_valid_portable_built_record` は空の binding を使えなくなる。production issuer を通した honest fixture に置換する。
- `s8b_v2_freeze_fixture.py:197–206` の5-field binaries は full portable record と receipt を作る必要がある。ratified、oracle、holdout の共有 fixture へ同時に波及する。
- `test_s8b_materialization.py:449` の floor manifest golden と、ratified production emitter の Git object hash は receipt 追加で変わる。ただし異なる root 間の同一性 assertion は維持する。
- `build_admission.py` と `buildcache.py` の production logic は変更しない。`test_v2_preimage_binds_exact_admission` と `test_completion_manifest_rejects_missing_receipt` を回帰検査として残す。
- top-level manifest、result、freeze の key 集合と schema version は変更しない。変更対象は `binaries[cell]` の current exact record shape だけである。
- `s8b_materialization.py` の import-order、逆 import 禁止 test は、新 leaf が floor、oracle、ratified を import しないことへ拡張する。
- future floor result bytes とそれを参照する future generation hash は変わるが、既存の tracked freeze bytes をこの wave で書き換えない。

## scope 外・裁定候補

1. 旧 portable artifact の互換読込

   receipt のない旧 manifest/result は exact-key 検査で拒否される。互換 loader、暗黙の receipt 合成、hash からの admission 推定は実装しない。既存 resume artifact を維持する必要があるなら別裁定が必要である。

2. schema 世代移行

   top-level `s8b-floor-manifest`、`s8b-floor-result`、holdout freeze の世代番号は上げない。nested `"admission_receipt"` の追加を理由に世代移行が必須という運用判断なら、本 wave では進めず別 wave とする。

3. 既存 artifact の遡及再取得

   receiptless artifact を再 build、再測定、再取得して埋め戻す処理は作らない。必要なら対象集合、費用、承認者を確定する別裁定が必要である。

4. P1 の raw receipt 完全コピー

   raw `build-admission/v1` は absolute `source_root` を二重に含み、その outer SHA も root 依存である。raw bytes の保持と Git deterministic emission は同時に満たせない。推奨は上記 root 非依存 descendant receipt である。raw receipt 必須という裁定なら、既存 deterministic contract を変更するか別 sidecar 世代を設計する必要があり、どちらも本 scope 外とする。

5. tracked artifact

   `output/s8b-freeze` に限定した静的確認では、16ファイル中 active v2 generation、approval、active pointer は0件、`"binaries"` を持つ JSON も0件だった。したがって tracked artifact の遡及更新は計画に含めない。

## リスクと未確認

- 必読指定のファイルは全て読めた。読めなかったパスはない。
- sandbox が read-only のため pytest、build、mutation は実行していない。緑とは報告しない。
- 実施したのは対象を限定した call-site、exact-key、fixture、artifact の静的検査だけである。Web 検索は行っていない。
- root 非依存 receipt は、元の root-bound receipt を発行時に完全検証した後の capability transfer である。この境界解釈は段4で明示確認したい。
- 元の `source-review/v1` 自体が human authenticity を暗号学的に証明しない点は変わらない。本変更が保証するのは既存 admission policy の連続的な束縛であり、新しい署名制度ではない。
- tracked 外の過去 run directory、計算ノード上の durable store、手元だけの resume artifact の件数は未確認である。
- 実装後は receipt 検査と既存直前 hash の順序をテストし、検査後から実使用までの既存 TOCTOU 防壁を誤って除去していないことを確認する必要がある。

## 総括

- 現状は build gateway で検証した admission receipt を portable record へ渡す時点で失っている。
- store、resume、oracle の hash 検査は bytes 差し替えを検出するが、admission の代替にはならない。
- portable record に exact-key の canonical durable receipt を追加する。
- receipt は current policy、review input、source、cell、freeze binding、binary SHA を同時に束縛する。
- raw receipt の absolute `source_root` は Git deterministic emission と衝突するため、そのまま保存しない。
- 元の root-bound receipt は発行時に完全検証し、root 非依存 descendant receipt へ変換する。
- missing、record mismatch、foreign-cell swap は store 読込前に拒否する。
- store bytes は発行時、store、resume、floor 測定直前、oracle 実走直前に hash 照合する。
- 旧 artifact の互換、schema 世代移行、遡及再取得は実装しない。
- テストは未実走であり、上記は静的調査に基づく段2実装プランである。