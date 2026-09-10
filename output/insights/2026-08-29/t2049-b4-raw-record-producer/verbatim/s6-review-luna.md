## 変異 M01〜M18 の帰属検証

`certified 正例` は `test_positive_201_block_certified_preserves_decimal_and_all_pair_protocol_bindings`、`欠測正例` は `test_positive_201_block_all_terminal_records_absent` を指す。

| 変異 | 判定 | 実装位置 | 実効的な帰属 |
|---|---|---|---|
| M01 | 検出不能 | `p3_b4_raw_record_producer.py:1236,1347` | 登録 node は通常時の registry 転記しか見ない。caller 値を任意指定可能にする mutant は M01 でなく M16 が落ち、receipt 由来へ切り替える mutant は入力差がなく検出できない。 |
| M02 | 到達不能 | `p3_b4_raw_record_producer.py:544-549,593-605,1116` | `record_root` は予定 path 照合より先に unknown field として拒否される。`_planned_path()` の照合だけを外しても登録 node は緑。 |
| M03 | 検出不能 | `p3_b4_raw_record_producer.py:1209-1216` | 登録 node の時刻順と publish 順がともに on/off なので、固定 `["on","off"]` mutant が緑。certified 正例へ検出が移り、しかも schedule は乱数生成なので帰属が登録 node に固定されない。 |
| M04 | 一意 | `p3_b4_raw_record_producer.py:1325-1326` | 最終 pair 検査を外すと `test_m04_final_assembly_rejects_different_on_off_pair_ids` だけが直接落ちる。 |
| M05 | 検出不能 | `p3_b4_raw_record_producer.py:768,981` | `_snapshot_regular()` 経由の二読取なら M05 だけが落ちるが、`open()` や `Path.read_bytes()` による二読取は spy に見えず緑。 |
| M06 | 複数 | `p3_b4_raw_record_producer.py:948` | WAL stage を素通しすると M06、`test_abort_reason_is_projected_as_terminal_reason`、certified 正例が落ちる。 |
| M07 | 複数 | `p3_b4_raw_record_producer.py:971-973` | float 再出力で M07 と certified 正例の双方が十進 token 不一致になる。 |
| M08 | 到達不能 | `p3_b4_raw_record_producer.py:1218-1228,1360-1362` | publish 側を外せば M08 は落ちるが assembly 側が最終受理を拒否する。assembly 側だけを外しても publish 側が先に拒否し、登録 node は緑。 |
| M09 | 複数 | `p3_b4_raw_record_producer.py:864-877,939-947` | 非終端 WAL を executed にすると M09、M11、M15、欠測正例が同時に落ちる。実装形によっては M14 も落ちる。 |
| M10 | 複数 | `p3_b4_raw_record_producer.py:913-918` | off を一律 false にすると M10 と certified 正例が落ちる。逆に両 arm を一律 true にする mutant は全新規 test を通過できる。 |
| M11 | 複数 | `p3_b4_raw_record_producer.py:932-947` | terminal 不在を crash 等で埋めると M09、M11、M15、欠測正例が落ちる。 |
| M12 | 一意 | `p3_b4_raw_record_producer.py:1118-1127` | publish 側で丸めて通すと M12 だけが直接落ちる。ただし assembly に同じ拒否があり、登録 node は「consumer まで欺いて通る」という事前登録上の影響を検査していない。 |
| M13 | 検出不能 | 具体的変異位置なし | 正例であって kill 対象が定義されていない。M01、M03、M13 などが同じ certified evidence を使うため、一般的な過剰拒否は多数 node に波及する。 |
| M14 | 複数 | `p3_b4_raw_record_producer.py:939-945` | lock 検査を文字どおり削ると M14 に加え、`acquired is True` を要求する M15 も落ちる。 |
| M15 | 複数 | `p3_b4_raw_record_producer.py:939-945` | terminal 不在を常に deferred にすると M09、M11、M15、欠測正例が落ちる。 |
| M16 | 一意 | `p3_b4_raw_record_producer.py:66-85,541-563` | judgment field を 1 つ許可する mutant は、単一の parameterized M16 node に帰属する。 |
| M17 | 検出不能 | `p3_b4_raw_record_producer.py:609-663` | `_snapshot_regular()` を再度呼ぶ mutant だけを数える。別 API で original receipt を再読すれば登録 node は緑。 |
| M18 | 一意 | `p3_b4_raw_record_producer.py:348-398` | leaf の `O_NOFOLLOW` を外すと M18 の symlink 負例だけが落ちる。 |

一意と認定できるのは M04、M16、M18、および publish 層だけに限定した M12 である。M01、M02、M03、M05、M08、M13、M17 は登録された機構へ到達しないか、別 node・別 API に検出が逃げる。

## 重大な所見

### 1

- **所見:** assembly と consumer は source artifact の evidence から判断値を再導出せず、同じ bytes の hash が一致するだけで caller 相当の判断値を受理する。
- **場所:** `orchestrator/campaign/p3_b4_raw_record_producer.py:1304-1390`、`orchestrator/campaign/p3_b4_analysis_path.py:174-196`、`orchestrator/campaign/p3_b4_analysis_adapter.py:559-603`、`orchestrator/tests/test_p3_b4_raw_record_producer.py:674-702`。
- **なぜ欠陥か:** planned path に canonical な偽 attempt artifact を先置きし、manifest binding、重複しない identity、同一 pair_id だけを整えれば、`evidence` と `receipt_projection` を欠落させても `raw.treatment_fired=true`、`protocol_ok=true`、`contaminated=false` を assembly が転記する。consumer はその source bytes 自身の hash を照合した後、同じ boolean をそのまま verdict 入力へ渡す。production derivation と consumer を両方 stub にしても certified 正例は緑になる。
- **成果物への影響:** B-4 の受理集合へ証拠未検証の arm を入れられ、成立・判定不能・protocol violation の verdict を任意方向へ変えられる。
- **判定:** real。

### 2

- **所見:** manifest の `driver` は source binding へ転記されるだけで、campaign/receipt の `driver_kind` と一度も束縛されない。
- **場所:** `orchestrator/campaign/p3_b4_raw_record_producer.py:769-779,1230-1240,1341-1353`、`orchestrator/tests/test_p3_b4_prerun_issuer.py:43`、`orchestrator/tests/test_p3_b4_raw_record_producer.py:193`。
- **なぜ欠陥か:** certified 正例自身が manifest の `driver="base-driver"` と evidence の `driver_kind="base"` を組み合わせて通る。別 driver の有効な on/off pair を任意の manifest row に供給しても、assembly は各値を別々に自己整合確認するだけで拒否しない。
- **成果物への影響:** 事前固定した母集合とは別 driver の試行を B-4 の受理集合へ混入でき、verdict と driver 別報告の帰属が変わる。
- **判定:** real。

### 3

- **所見:** M03 検査は WAL timestamp の実体を名指しせず、publish 順 mutant と同じ on/off 入力しか与えていない。
- **場所:** `orchestrator/tests/test_p3_b4_raw_record_producer.py:377-387`、`orchestrator/campaign/p3_b4_raw_record_producer.py:1209-1216`。
- **なぜ欠陥か:** `assignment_observation=["on","off"]` と固定しても登録 M03 node は通る。`first_record_position >= 3` も実際の `first_record_ts`、frame bytes、期待位置を照合せず、任意の大きな位置で恒真になる。逆順の検出は別の 201-block 正例と乱数 schedule に偶然依存する。
- **成果物への影響:** schedule 違反を遵守として渡し、protocol violation である block を通常 verdict の計算へ入れられる。
- **判定:** real。

### 4

- **所見:** M02 は予定 path 検査でなく request schema の unknown-field 拒否しか検査していない。
- **場所:** `orchestrator/tests/test_p3_b4_raw_record_producer.py:360-374`、`orchestrator/campaign/p3_b4_raw_record_producer.py:541-549,593-605`。
- **なぜ欠陥か:** `_planned_path()` を任意 path を返す実装へ壊しても、負例は `record_root` を未知 field として先に拒否される。予定 path の照合結果を変える入力は後段へ一度も到達しない。
- **成果物への影響:** M02 の防壁を失った実装を受理しうるため、raw 集合が issuer-planned path 外へ分裂して B-4 の全件報告を欠落させうる。
- **判定:** real。

### 5

- **所見:** M05 と M17 は helper 呼出回数だけを数え、同じ byte buffer が分類・hash・検証の各実体へ渡ったことを検査していない。
- **場所:** `orchestrator/tests/test_p3_b4_raw_record_producer.py:406-424,575-593`。
- **なぜ欠陥か:** original を `_snapshot_regular()` で一度読み、その後 `open()`、`os.read()`、`Path.read_bytes()` のいずれかで別 buffer を得れば、count は 1 のまま両 node が緑になる。どの bytes が `_decode_campaign_identity()`、`campaign_lock_bytes_sha256()`、receipt verifier に渡ったかの期待値がない。
- **成果物への影響:** ABA 差替えで分類と検証が別証拠を見ても受理され、protocol 判定と source evidence hash が一致しなくなる。
- **判定:** real。

### 6

- **所見:** source artifact は §7.1 必須項目の初期 snapshot hash、model hash、予算消費、anomaly class を持たず、停止理由と verdict も専用項目ではなく部分的な raw 値に留まる。
- **場所:** `orchestrator/campaign/p3_b4_raw_record_producer.py:1001-1051`、`docs/phase3-b4-reflux-ablation-preregistration.md:580-584`。
- **なぜ欠陥か:** `precursor_hash` は registry の `initial_proposal_sha256` の転記であって初期 snapshot hash ではない。`model_snapshot` は実装自身が非 hash と明記している。budget と precursor anomaly class は存在せず、`terminal_reason` は ABORT reason だけである。
- **成果物への影響:** B-4 の全件報告行が §7.1 の必須 provenance を満たさず、モデル・初期状態・予算・anomaly ごとの監査可能な報告を作れない。
- **判定:** real。

`model_snapshot` を `model_hash` と偽称する field はなかった。一方、`precursor_hash`、`reference_snapshot_hash`、`reference_receipt_hash` は producer が対応 artifact を読み直して算出した hash ではなく、sealed publication からの宣言値である。

### 7

- **所見:** terminal 不在時の lock は context を抜けてから publish され、後から campaign が再開できるという裁定上の非保証も source artifact に列挙されていない。
- **場所:** `orchestrator/campaign/p3_b4_raw_record_producer.py:57-64,939-945,1258-1259`。
- **なぜ欠陥か:** producer が lock を取得して直ちに解放した後、別 process が campaign を再開し terminal record を追加しても、先に読んだ WAL を `terminal-record-absent` として封印できる。裁定 §2.4 が要求した「一度終わった campaign が後から再開されることを排除しない」という非保証も `flock は advisory` の一文に省略されている。
- **成果物への影響:** 実行された arm が missing として B-4 verdict に入り、報告上も terminal 実行が欠測へ誤分類される。
- **判定:** real。

## 親が走らせるべき既存 test

新規 production/test file を実際に列挙または内容走査する既存 node は次である。

- `orchestrator/tests/test_plain_runner_coverage.py::test_every_test_file_is_self_runnable_or_allowlisted`
- `orchestrator/tests/test_campaign_import_invariant.py::test_real_repository_legacy_namespace_matches_exception_ledger`
- `orchestrator/tests/test_campaign_import_invariant.py::test_real_campaign_package_has_canonical_direct_bootstrap`
- `orchestrator/tests/test_campaign_import_invariant.py::test_real_campaign_package_uses_relative_sibling_imports`
- `orchestrator/tests/test_campaign.py::test_certified_writer_authorization_caller_inventory_is_closed`
- `orchestrator/tests/test_t1286_commit_receipt.py::test_production_commit_producer_census_is_exactly_five`
- `orchestrator/tests/test_ccbench_spawn_sites.py::test_reviewed_process_launch_inventory_is_recursive_and_exact`
- `orchestrator/tests/test_s8b_floor_campaign.py::test_materializer_registry_covers_all_python_build_launches`
- `orchestrator/tests/test_p3_s4_loop.py::test_backoff_coder_text_materialization_ingress_is_closed_and_nonempty`
- `orchestrator/tests/test_p3_b4_analysis_path.py::test_public_evaluate_analysis_production_caller_inventory_is_pinned_not_closed`
- `orchestrator/tests/test_pytest_collection_config.py::test_permanent_exclusion_table_has_no_other_verifier_or_oracle_tests`

## nit

- 十進 token は `0.10000000000000001` で、binary64 では正確に表せない。M07 の値選択は有効であり、既知の `491796.5` 型 false negative はない。
- M12 の `(1,3)` も有限十進展開を持たず、`DECIMAL_NOT_TERMINATING` 分岐自体には到達する。
- certified 正例は現行実装では treatment、`protocol_ok`、pair 一致、十進 token 保存の各分岐を通る。ただし重大所見 1 のとおり、その実体を stub から識別できない。
- M14 は実 lock を保持する同期点を使っており、時点狙いの負例として固定されている。M05/M17 は呼出回数だけで byte identity の同期点がない。
- expected literal に working-tree hash、現在時刻、pid、固定絶対 path の焼き込みは見つからなかった。iteration 由来 timestamp と `tmp_path` は fixture 入力であり、外部揮発値との一致を期待していない。

## 総括

M01〜M18 の「名前上の一対一」は成立しているが、実効的に一意なのは M04、M16、M18と publish 層限定の M12だけである。特に M01/M02/M03/M05/M08/M13/M17 は intended mutation を登録 node が直接検出しない。

現実装で最も重大なのは、source artifact の evidence を assembly/consumer が再検証せず、自己整合 hash と producer 由来 boolean をそのまま verdict 入力へ渡す点である。加えて driver authority が未束縛で、§7.1 の行 provenance も不足している。既知の v1 lock fixture 赤は所見に含めていない。