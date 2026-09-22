実装済み・未実走です。指定の 5 ファイルのみ変更しました。pytest は dispatch 障害で本体未起動のため、受入成功・v2 bytes 不変・変異 KILLED は未確認です。

## 変更の要約 (file ごとの差分行数)

追加＋削除の実測値です。

| file | 追加 | 削除 | 合計 |
|---|---:|---:|---:|
| [model.py](orchestrator/verifier/model.py) | 40 | 0 | 40 |
| [parse.py](orchestrator/verifier/parse.py) | 92 | 24 | 116 |
| [dsg.py](orchestrator/verifier/dsg.py) | 43 | 35 | 78 |
| [core.py](orchestrator/verifier/core.py) | 30 | 2 | 32 |
| [test_verifier.py](orchestrator/tests/test_verifier.py) | 433 | 0 | 433 |

production は **266 / 550 行**、tests は **433 / 800 行**。`report.py`、docs、共有 fixture は未変更。commit・push・branch 操作はしていません。

## 段 4 裁定 R1〜R9 の充足 (項目ごとに file:line)

以下は静的確認です。

| 裁定 | 実装箇所・内容 |
|---|---|
| R1 | `model.py:487,506` に非認定 field と `clean()` 条件。`core.py:64` で v3 非空 run に印・notes を追加。capability 経路の試験は `test_verifier.py:3690`。 |
| R2 | `parse.py:366` で同一 file の混在を拒否。共通 helper は `:271`、legacy 呼出しは `:859`、compact は failure 処理後の `:897`。merge・親エラー再走査は未変更。 |
| R3 | `parse.py:262` の正規形検査を、新設整数 field に適用。v2 の整数変換は保持。 |
| R4 | `parse.py:346` 以降に v3 行長・table・op、`:371` 以降に nS/nQ・tx_type 検査。S/Q は未知 tag のまま。 |
| R5 | 派生型は `model.py:342,347,352,420,425`。identity は `:360`、intern は `parse.py:625`、復元は `:575`。DSG 各経路と理由復元は表込み identity を使用。 |
| R6 | `core.py:201` に `result_to_dict_v3`。節点数不一致・基底 reason 混入を拒否。既存 serializer・CLI・package 再 export は未変更。 |
| R7 | `parse.py:439,448` の X/I tuple 第2要素に表を保持。`core.py:133,151` の sample、DSG の version-dup notes に表を表示。 |
| R8 | 引数なしの 18 試験を追加。全経路比較、last-wins、pool 障害、子 PID、存在履歴の非認定と v2 対照を含む。実効性は未実走。 |
| R9 | production 266 行、tests 433 行で上限内。 |

## 追加した試験の一覧

全 nodeid は `orchestrator/tests/test_verifier.py::` に以下の関数名を続けたものです。後の変異表では T 番号で参照します。

| ID | 関数名 | 主な検査 |
|---|---|---|
| T01 | `test_v3_table_identity_separates_edges` | 表識別、異表 token ID、参照辺集合 |
| T02 | `test_v3_serial_tables_types_and_ops` | table 0..10、tx_type 1..5、U/I/D |
| T03 | `test_v3_cycle_reports_tables_and_tx_types` | cycle metadata、新出力、report 上限 |
| T04 | `test_v3_reasons_preserve_ww_wr_rw_identity` | 同一 txn の異表同 hex、理由の exact 比較 |
| T05 | `test_v3_packed_mapping_and_read_bounds` | read-only 解決、異表 writer、Mapping、境界 |
| T06 | `test_v3_same_version_table_duplicates_and_notes` | 異表同版と同表重複の対照 |
| T07 | `test_v3_tuple_and_legacy_fallback_preserve_metadata` | 32-bit / 64-bit 超過 fallback |
| T08 | `test_v3_last_winner_tx_type_in_cycle` | 別 file の勝者 tx_type |
| T09 | `test_v3_rejects_mixed_schema_in_one_file` | 同一 file の混在 |
| T10 | `test_v3_rejects_mixed_schema_across_files` | file 間混在、中立 file、overflow |
| T11 | `test_v3_schema_failure_precedes_cross_file_mixture` | 構文エラー先行 |
| T12 | `test_v3_rejects_invalid_table_and_tx_type` | 値域・正規形・空白混入 |
| T13 | `test_v3_rejects_scan_counts_tags_ops_and_record_shapes` | nS/nQ、S/Q、op、行長 |
| T14 | `test_v3_x_i_keep_table_and_make_indeterminate` | X/I tuple、件数、notes |
| T15 | `test_v3_existence_unverified_and_v2_control` | 通常・unborn・DELETE 読み、capability、v2 対照 |
| T16 | `test_v3_framing_and_neutral_files` | 件数・終端違反、空 run |
| T17 | `test_v3_parallel_processes_and_pool_failure_fallback` | 採用された子 PID、pool 障害 fallback |
| T18 | `test_v3_output_validation_and_v2_projection` | 不正 witness 拒否、v2 射影一致 |

既存全関数の AST 不変を確認しました。既存テストは 114 件です。追加関数に fixture 引数・decorator はありません。末尾 `_run()` が動的列挙するため登録追加は不要で、`test_plain_runner_coverage.py` も file 単位の harness 検査でした。

## 自走結果

実行を試みたコマンド：

```text
python3 tools/run_tests.py -q orchestrator/tests/test_verifier.py -p no:cacheprovider -n 0
```

結果は **rc=16**。`qstat -Q preflight rc=1` により dispatch が失敗し、`child_started=false` でした。

- 指定 pytest：**未実走**。passed / failed 件数、失敗 nodeid は未取得。
- `PYTHONPATH=. python3 orchestrator/tests/test_verifier.py`：**未実走**。Pegasus の実行場所判定を迂回して直接起動していません。
- キュー状態：ENA / STS とも観測不能。
- 静的検査：5 ファイルの AST 構文確認、既存関数 AST 不変、`git diff --check` は成功。
- 変異実行、consumer test、受入全走は未実施。

## 波及の静的列挙

| 所有外 consumer | 波及 |
|---|---|
| `verifier/__init__.py`、`cli.py:70,90` | 既存 API・serializer のまま。v3 の表・取引種別の出力配線は未対応。 |
| `verifier/report.py:17,35,96` | 基底 field の射影を維持。編集なし。 |
| `campaign/pipeline.py:44,506,656` | capability と旧診断出力を使用。v3 非認定は core を通る。 |
| `campaign/silo_ladder_rung1.py:3048` | 既存 verifier・旧 serializer の呼出し。v2 回帰確認が必要。 |
| `campaign/reflux_result_evidence.py:25,352,738` | `VerifyResult` と旧 dict の exact schema を消費。新射影は未配線。 |
| `critic/digest.py:126,790,813` | WAL 内の旧 anomaly dict を消費。新 metadata はまだ届かない。 |
| `campaign/source_digest.py:71`、`between_run_floor.py:45` | model の source assessment 関数を使用。該当関数は未変更。 |
| `campaign/campaign_lock.py` | source digest は変わるが、closure の file 集合は不変。 |
| `test_campaign.py:5817,5819,5820` | 基底 `EdgeReason` / `Anomaly` の生成契約は保持。 |
| `test_reflux_result_evidence.py:841,892,904,986` 以降 | witness hash、空 anomaly、件数、変形 result の consumer 試験。未実走。 |
| その他 consumer tests | `test_t1286_commit_receipt.py`、`test_verify_fanout.py`、`test_reflux_formal_consumer.py`、`test_pipeline_verify_result_retention.py`、`test_mocc_proof_surface.py`、`test_critic.py` 等。未実走。 |
| `tools/` | 対象 verifier 型・API の直接 import / 呼出しは検索で見つからず。source closure 等の間接依存を否定するものではない。 |

共有の `orchestrator/tests/fixtures/`、fixture inventory、既存 JSON / repr / 結果 hash は未変更です。新試験は `_tmp_trace` と既存 synthetic proof source、`commit_receipt_support._proof_build_binding` を使用します。

## 変異の位置表 (M1〜M15)

**全件未実走。期待 KILLED の静的候補であり、殺傷確認済みではありません。** 以下、file は `orchestrator/verifier/` 配下。試験 nodeid は前節の T 番号に対応します。

| 変異 | 位置 | 置換前の1行 → 置換後の1行 | 殺すはずの試験 |
|---|---|---|---|
| M1 | `model.py:361` | `return (access.table, access.key) if isinstance(access, (ReadV3, WriteV3)) else access.key` → `return access.key` | T01 |
| M2 | `parse.py:625` | `identity = (table, token) if schema == 3 and table >= 0 else token` → `identity = token` | T01 |
| M3 | `dsg.py:426` | `key = _object_at(columns, token)` → `key = (9, _object_at(columns, token)[1]) if columns.schema == 3 else _object_at(columns, token)` | T05 |
| M4a | `dsg.py:517` | `key = _object_at(columns, token_id)` → `key = _object_at(columns, token_id)[1] if columns.schema == 3 else _object_at(columns, token_id)` | T01 |
| M4b | `dsg.py:260` | `key = _object_at(columns, columns.read_key_id[read_index])` → `key = _object_at(columns, columns.read_key_id[read_index])[1] if columns.schema == 3 else _object_at(columns, columns.read_key_id[read_index])` | T01 |
| M5 | `parse.py:273` | `for path, current in sorted(files):` → `for path, current in []:` | T10 |
| M6 | `parse.py:366` | `if schema is not None and schema != current_schema:` → `if False:` | T09 |
| M7 | `parse.py:375` | `extra["tx_type"] = _v3_integer(f[9], "tx_type", 1, 5)` → `extra["tx_type"] = _v3_integer(f[9], "tx_type", 0, 6)` | T12 |
| M8 | `parse.py:351` | `access_extra["table"] = _v3_integer(f[2], "table", 0, 10)` → `access_extra["table"] = _v3_integer(f[2], "table", 0, 11)` | T12 |
| M9 | `parse.py:373` | `if ns != 0 or nq != 0:` → `if False:` | T13 |
| M10 | `parse.py:263` | `if re.fullmatch(r"0\|[1-9][0-9]*", token) is None:` → `if False:` | T12 |
| M11 | `dsg.py:780` | `u_writes = {object_identity(w): ut.commit for w in ut.writes}` → `u_writes = {w.key: ut.commit for w in ut.writes}` | T04 |
| M12 | `parse.py:582` | `**({"tx_type": columns.txn_tx_type[row]} if v3 else {}),` → `**({"tx_type": 1} if v3 else {}),` | T03 |
| M13 | `core.py:217` | `reason_dict["table"] = reason.table` → `pass` | T03 |
| M14 | `core.py:64` | `dsg.integrity.v3_existence_unverified = True` → `dsg.integrity.v3_existence_unverified = False` | T15 |
| M15a | `parse.py:439` | `issues.lock_coverage_violations.append(` → `[].append(` | T14 |
| M15b | `parse.py:448` | `issues.write_intent_violations.append(` → `[].append(` | T14 |

帰属上の注意：

- M4 は builder / worker の別箇所なので分割。片側の identity 型不一致による辺消失を検出する候補です。
- M5 は共通 helper 自体を無効化するため、legacy fallback の再呼出しも代替防壁になりません。
- M6 は legacy を先に検査し、混在受理そのものの assertion で検出する構成です。
- M7〜M10 は正規形の範囲外値、S/Q 行なしの非零宣言、値域内の `01` を使い、別の拒否条件による代替検出を避けています。
- M15 は R1 によって verdict が引き続き indeterminate になるため、**verdict では殺せません**。tuple・違反件数・notes の assertion で検出します。
- 上記の単一理由への帰属は、変異実走で最終確認が必要です。

## 未解決・懸念

- 実走環境の復旧後、pytest・素の runner・consumer tests・変異を実行する必要があります。
- v2 の既存期待値は保持しましたが、bytes・witness 順序の不変は未実証です。
- §3.3 の存在履歴は未実装です。認定開始にはその実装と R1 の印の撤去が必要です。
- CLI・pipeline・receipt digest への v3 metadata 配線は後続です。

## 総括

指定の 5 ファイルに v3 parse・表込み identity・構造化 anomaly を実装しました。
v3 非空 run は存在履歴未検査の印によって認定を止めます。
cycle は従来どおり non-serializable として返します。
production 266 行、tests 433 行で規模上限内です。
既存関数の AST は保持し、引数なしの 18 試験を追加しました。
pytest は dispatch rc=16 で本体未起動、素の runner も未実走です。
受入成功・v2 bytes 不変・変異 KILLED は未確認です。
commit・push・branch 操作はしていません。