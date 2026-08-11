## 所見

- **BLOCKER — `verify_manifest` は configuration 欠落を塞いだが、holdout 全体の欠落を許す。** `orchestrator/campaign/s8b_oracle_manifest.py:1031-1037` は期待積の holdout 集合を schedule 自身から導出し、同 `:744-747` も freeze の部分集合を許す。judge も存在する holdout 間だけを比較する (`orchestrator/campaign/s8b_oracle_judge.py:194-203`)。新規負例は全 holdout を残している (`orchestrator/tests/test_s8b_oracle_manifest.py:297-311`)。**放置時:** `rr20` を丸ごと落とした manifest が通り、report の `expected_cells` と verdict の `holdouts` から `rr20` が消え、不完全な証拠で certified 選択が成立し得る。

- **BLOCKER — budget 承認は producer 内だけで、ratified proof chain に残らない既知穴が実装後も存続する。** candidate は approval hash を非構造化 `refreeze_note` に埋めるだけ (`s8b_holdout_freeze.py:1394-1399`) で、ratified schema は approval record に budget authority を持たず (`s8b_ratified_freeze.py:106-116`)、transition は `/budget` を自由変更可能としている (`:127-140`)。**放置時:** producer を経ない候補の任意 `budget.total_bench_s` が世代承認を通り得て、ledger reservation 上限と観測集合が変わる。

- **BLOCKER — MU-2/MU-3/MU-5/MU-6 は事前登録どおりの単一理由変異になっていない。** MU-2 の namespace 分岐は固定 path 検査後で到達不能 (`s8b_holdout_freeze.py:1418-1423`)、MU-5 は同じ `None` 拒否が二箇所 (`:1145-1150`, `:1334-1339`)、MU-6 は分岐撤去後も SHA 型検査が `None` を拒否する (`s8b_oracle_spec.py:156-162`)、MU-3 は parent nofollow と leaf exclusivity を一変異に束ねている (`s8b_holdout_freeze.py:1441-1464`)。**放置時:** mutation matrix に実効 gate を殺していない `KILLED` が記録され、検出力の証明値が偽陽性になる。

- **MAJOR — reviewed spec と approved CLI は production consumer の trust chain に入っていない。** manifest schema に spec hash はなく (`s8b_oracle_manifest.py:43-48`)、driver/report は任意 manifest を `verify_manifest` するだけ (`s8b_oracle_driver.py:1119-1128`, `s8b_oracle_report.py:1750-1762`)。`build_approved_manifest` の caller は同 module の CLI だけ (`s8b_oracle_manifest.py:1195-1200`) だった。**放置時:** cell 集合以外の `n`、`master_seed`、campaign ID、run contract は approved spec を迂回して変更でき、試行数・WAL 所有・report 数値が変わる。

- **MAJOR — v2 candidate producer の通常出力先は実 repo に存在せず、正例だけが親 directory を事前作成している。** writer は各 parent を `os.open` するだけで作成しない (`s8b_holdout_freeze.py:1455-1459`) 一方、テスト fixture は `output/s8b-freeze-candidates` を先に作る (`s8b_v2_freeze_fixture.py:296-299`)。現 checkout では同 directory は不在。**放置時:** budget pin と floor が揃っても CLI は candidate を一件も生成できず、certified 選択は v1 の `floor=null` / `budget=null` に止まる。

- **MINOR — 新設 spec module は未追跡のまま。** `orchestrator/campaign/s8b_oracle_spec.py` は `git status` で `??`。**放置時:** tracked-only commit では module が欠落し、manifest test の import と `build-approved` が失敗する。

## MU-1〜MU-8 単一理由性

| ID | 判定 | 実コード上の理由 / 再照準先 | 期待 node（実在する関数名） |
|---|---|---|---|
| MU-1 | **単一理由性 OK** | cell-product gate は `s8b_oracle_manifest.py:1031-1042` の一箇所。builder は subset を受理し、judge は全 holdout 一様 subset を捕捉しない。 | `test_subset_manifest_build_stays_accepted_but_verify_choke_point_rejects` |
| MU-2 | **NG** | `:1420-1421` の固定 path 拒否が先に発火するため、`:1422-1423` の canonical namespace 拒否は死んでいる。固定 path 検査を実効 gate として再登録し、canonical parent を作った専用負例を追加する。 | 現行 `test_v2_candidate_output_gate_rejects_every_nonfixed_raw_path` は parent 不在でも赤にならず不十分。再照準 node は未実装。 |
| MU-3 | **NG** | directory の `O_NOFOLLOW` (`:1441`) と leaf の `O_EXCL` (`:1461-1464`) は別 gate。`open("x")` は exclusivity を維持するため、事前登録文と変異が一致しない。parent symlink と leaf overwrite の二変異に分割する。 | `test_v2_candidate_output_gate_rejects_symlink_parent_and_existing_leaf` |
| MU-4 | **単一理由性 OK** | canonical bytes 比較は `:1365-1366` の一箇所。`_validate_budget` は `100` と `100.0` の双方を数値として受理するため前段 mask はない。 | `test_v2_candidate_budget_approval_compares_canonical_numeric_bytes` |
| MU-5 | **NG** | outer gate `:1338-1339` と loader gate `:1146-1147` が同じ入力を二重拒否する。片方だけの無効化では node は緑のまま。完全な正入力 fixture で両層変異を事前登録するか、authority gate を一箇所へ集約する。 | 現行 `test_v2_candidate_fails_closed_before_reading_inputs_when_budget_unratified` は単独変異を kill しない。 |
| MU-6 | **NG** | `s8b_oracle_spec.py:158-159` を外しても `:160-162` が `None` を invalid SHA として拒否する。現行赤は reason 差だけで、DW-M03 の kill ではない。完全な valid spec を用意し、pin 無しで出力されないことを行動で比較する。 | `test_reviewed_spec_none_pin_is_always_no_approved_spec`、`test_build_approved_active_without_pin_fails_before_output` は diagnostic-only。 |
| MU-7 | **単一理由性 OK** | producer の eligibility gate は `s8b_holdout_freeze.py:1228-1229` の一箇所。`verify_floor_artifact` はこの field を再拒否しない。 | `test_v2_candidate_rejects_floor_not_eligible_for_refreeze` |
| MU-8 | **単一理由性 OK（正例）** | full product fixture は freeze の両 holdout の全6構成と一致する。 | `test_write_is_create_only_and_valid_manifest_verifies`、`test_run_block_verifies_manifest_once_and_reuses_object`、`test_build_observations_accepts_actual_verify_manifest_result` |

## consumer 波及

cell-product 検査によって赤くなる既存 node の静的集合は、3 file とも **空集合**だった。親実測の **179 passed / rc=0** と一致する。

| test file | configuration 集合 | freeze との関係 | 赤 node |
|---|---|---|---|
| `test_s8b_oracle_driver.py` | `:64-67` の6構成。schedule は `:1429-1433`、freeze は共有 fixture で充填 (`:1373-1382`) | `rr20` / `rr80` の `variant_binding.entries` と exact 一致 | なし |
| `test_s8b_oracle_report.py` | `:47-50` の同じ6構成。manifest helper は `:194-229` | 両 holdout と exact 一致 | なし |
| `test_s8b_oracle_judge.py` | `:22` の `c0..c5` | freeze/manifest verifier を使わない独立 observations fixture | なし |

ただし、これは既存 fixture が正当であることしか示さない。holdout 全欠落の負例は3 fileにも新規 manifest testにも存在しない。

## 新規テストの純増検出力

| 新規 test 関数 | 無ければ見逃す欠陥 |
|---|---|
| `test_v2_candidate_fails_closed_before_reading_inputs_when_budget_unratified` | 未承認時の早期拒否。ただし二重 gate の片方を壊しても落ちず、MU-5 証拠にはならない。 |
| `test_v2_candidate_build_and_generate_synthetic_g1` | candidate schema・closure・固定出力・create-only の happy path 破損。 |
| `test_v2_candidate_budget_approval_compares_canonical_numeric_bytes` | `100` と `100.0` を同一承認値として扱う欠陥。 |
| `test_v2_candidate_rejects_floor_not_eligible_for_refreeze` | pilot/非 eligible floor の混入。 |
| `test_v2_candidate_rejects_closure_hit_absent_from_captured_head` | HEAD に存在しない untracked closure の採用。 |
| `test_v2_candidate_closure_hash_tracks_worktree_bytes_without_pinned_diagnostic` | generation commit へ入れる予定の worktree closure bytes を取り落とす欠陥。 |
| `test_v2_candidate_output_gate_rejects_every_nonfixed_raw_path` | 非正規・root 外・固定 path 外の出力。ただし MU-2 の dead branch は検出しない。 |
| `test_v2_candidate_output_gate_rejects_symlink_parent_and_existing_leaf` | symlink parent traversal、既存 leaf 上書き、symlink leaf 追跡。 |
| `test_v2_candidate_cli_surface_has_no_approval_or_root_arguments` | caller に approval/root 選択面を与える CLI 回帰。 |
| `test_subset_manifest_build_stays_accepted_but_verify_choke_point_rejects` | generic builder を維持しつつ実行 choke point だけで一様 configuration subset を拒否する性質。 |
| `test_reviewed_spec_exact_schema_and_independent_schedule_hash_literal` | spec schema、pin、独立 schedule hash の破損。 |
| `test_reviewed_spec_none_pin_is_always_no_approved_spec` | `None` reason の変化。ただし fail-open 行動ではなく diagnostic sensitivity。 |
| `test_reviewed_spec_pin_mismatch_is_fail_closed` | pin と spec bytes の不一致受理。 |
| `test_reviewed_spec_key_sets_are_exact` | top/schedule/run-contract の余分 key 受理。 |
| `test_reviewed_spec_requires_canonical_bytes_without_trailing_lf` | 非 canonical bytes や末尾 LF の受理。 |
| `test_build_approved_parser_has_output_as_only_value_input` | schedule・freeze・campaign・root 等の caller 指定面追加。 |
| `test_approved_writer_rejects_outside_candidate_root` | manifest candidate root 外への書込み。 |
| `test_approved_writer_rejects_symlink_parent` | manifest writer の symlink parent traversal。 |
| `test_approved_writer_is_exclusive_create` | 既存 manifest leaf の上書き。 |
| `test_build_approved_active_without_pin_fails_before_output` | pin 無し reason と無出力。ただし MU-6 では次段 SHA 型検査に mask される。 |
| `test_build_approved_uses_one_active_snapshot_and_writes_valid_candidate` | active freeze 再読・複数 snapshot 混成、生成物が verifier を通らない欠陥。 |
| `test_build_approved_rejects_uniform_configuration_subset_before_output` | approved CLI 内の subset 拒否。ただし `verify_manifest` を壊しても CLI 前段で落ちるため MU-1 証拠ではない。 |
| `test_manifest_cli_maps_only_no_active_and_creates_no_output` | `no-active` の公開 reason 写像と無出力契約。 |
| `test_manifest_cli_does_not_round_namespace_dirty_to_no_active` | namespace 汚染を「active 無し」へ丸める欠陥。 |

特に production 到達性を検出しないのは、reviewed-spec/approved-writer/parser 系の全 node である。これらは局所 API を検査するだけで、driver/report が spec を無視しても緑のまま。

## 誰も呼ばない機構

repo-wide symbol 検索では、以下は定義 module とテスト以外に caller がなかった。

- v2 producer API は `s8b_holdout_freeze.main` の手動 CLI 分岐からだけ到達 (`s8b_holdout_freeze.py:1551-1557`)。
- spec validator は `load_approved_spec` 内 (`s8b_oracle_spec.py:156-182`) と approved CLI からだけ到達。
- `build_approved_manifest` は同 module の `main` からだけ到達 (`s8b_oracle_manifest.py:1195-1200`)。
- production に到達している新機構は `verify_manifest` の cell-product gateだけで、driver/report から実際に呼ばれる。

## 既存テスト弱体化・fixture regression

- `git diff HEAD` で既存 test の削除・変更された `assert` は **0件**。
- 既存 `skip` / `xfail` / fixture decorator の緩和・追加は **0件**。
- `s8b_v2_freeze_fixture.py` の既存 API (`holdout_configuration_ids`, `per_pair_floor`, `budget`, `fill`) は `:24-72` のまま変更されず、差分は `:75` 以降の helper 純増。driver/report/manifest の既存 fixture 挙動変更はない。
- `test_s8b_oracle_manifest.py` は共有 fixture importer だが未走行。driver/report は親実測済み。judge は共有 fixture を import しない。
- `build_manifest` の refactor は旧 public wrapperを保持しているが、既存 test 未走行のため最終確認は残る。

## 未走行の穴

親がまだ走らせるべき file は以下。

- `orchestrator/tests/test_s8b_holdout_freeze.py`
- `orchestrator/tests/test_s8b_oracle_manifest.py`
- `orchestrator/tests/test_s8b_ratified_freeze.py`
- 新規 test 名の収集漏れを検出する `orchestrator/tests/test_plain_runner_coverage.py`

焦点3 file (`test_s8b_oracle_driver.py` / `test_s8b_oracle_report.py` / `test_s8b_oracle_judge.py`) は親実測 179 passed のため未走行集合から除外する。

**判定: NO-GO**

## 総括

- holdout 全欠落が `verify_manifest` から judge まで素通りし、certified evidence を縮退できる。
- MU-2/MU-3/MU-5/MU-6 は単一理由性を満たさず、現状の mutation matrix は証拠にならない。
- reviewed spec と budget approval は production proof chain に未接続である。
- producer 正例は実 repo にない parent directory を fixture だけで事前作成している。
- **NO-GO: 上記 BLOCKER の再照準・負例追加・未走行4 file の確認前に記録／landしてはならない。**