## must-fix

### 1. `not-incurred` が非ゼロ token を黙って捨てる

- 対象: `tools/codex_reasoning_ab.py:9531-9541`, `tools/codex_reasoning_ab.py:10474-10517`, `tools/codex_reasoning_ab.py:10797-10825`
- 失敗シナリオ: `process_started=false`, `not_launched=true`, 正しい形の `prelaunch_failure` を持つ completion row に `input_tokens=1_000_000` を入れる。supervisor ledger 検査は未起動 row の token が全て exact 0 であることを要求しない。その値は replay attempt へコピーされるが、費用層は token を見る前に `prelaunch_failure is not None` だけで `not-incurred` を返す。結果は `accounted_amount` 無しで、非ゼロ token との矛盾も failure reason にならない。
- 成果物影響: 矛盾した ledger が valid report に残り、`resource_ledger.normalized_cost` は人工的に `not-incurred`、軸 `attempt_count` と `accounted_amount` から当該試行が消えるため、合計費用を過小化し、残存試行から作る平均を過大化できる。

未起動の technical row と pair mate の双方について、4 token field が exact int の 0、`model_calls=0` であることを上流 ledger validator で要求すべきである。新設 `test_m02_prelaunch_zero_tokens_are_not_incurred_and_not_counted` は全 0 の正例しか試しておらず、この矛盾入力を検出しない。

### 2. `verify-snapshot` が snapshot を別 manifest へ再ラベルできる

- 対象: `tools/codex_reasoning_ab.py:3236-3371`, `tools/codex_reasoning_ab.py:11740-11743`, `tools/codex_reasoning_ab.py:11929-11934`
- 失敗シナリオ: manifest A と B を、snapshot/provenance は同一、`known_finding_ids` だけ異なる valid manifest とする。`build-snapshot --task-manifest A` で作った snapshot に `verify-snapshot --task-manifest B` を実行すると、先行 oracle の digest A を受け取る引数が無いため比較せず、同じ snapshot に digest B を付けた oracle を正常出力する。その oracle から schedule B を作れば、以後の exact digest 検査は全て B で通り、B にしかない `equivalent_to` を受理できる。
- 成果物影響: snapshot 作成時の task 解釈 A から adjudication の受理集合 B への交換が final report まで検出されず、verdict の受理集合と finding ledger が変わる。

これは `ruling.md:98-102` の fallback に該当する。先行 digest を運べない現状のままなら、standalone `verify-snapshot` から `--task-manifest` を外す必要がある。

### 3. `append-verdicts` は既存 verdict log の digest を検査しない

- 対象: `tools/codex_reasoning_ab.py:11438-11442`, `tools/codex_reasoning_ab.py:11453-11480`
- 失敗シナリオ: packet state は manifest B の digest、既存 verdict log は同じ packet ID を持つ parent row だが manifest A の digest、とする。`append-verdicts --reader second-reader --task-manifest B` は packet state B と新規 row B だけを検査し、既存 row は `reader` 重複しか見ない。そのため A/B 混在 log へ追記し、digest B を掲げた成功結果を返す。
- 成果物影響: `append-verdicts` の受理集合と返却する `verdict_log_sha256` 参照が別 manifest の既存行を含む方向へ広がる。後段 `freeze-verdicts` は拒否するが、「各 consumer がその場で exact 一致を要求する」という裁定を満たさない。

既存全 row に `_validate_verdict_row(..., task_manifest=...)` を適用してから追記すべきである。

### 4. material manifest の再読失敗が「descriptor 無し」に化け、valid report から費用が消える

- 対象: `tools/codex_reasoning_ab.py:9786-9791`, `tools/codex_reasoning_ab.py:10014-10032`, `tools/codex_reasoning_ab.py:10400-10423`
- 失敗シナリオ: `_replay_manifest` が schedule descriptor を持つ正しい manifest を読んだ後、`_aggregate_has_schedule_descriptor` の再読時だけ同じ path を `{}` に差し替え、最終 `manifest_sha256` 再読前に元へ戻す。同 helper は schedule 不在を `False` として正常扱いし、reason を追加しない。最終出力は元の digest、`valid=true` のまま、全 `normalized_cost` key と `normalized_cost_axis_ledger` が欠落する。
- 成果物影響: bound v3 report が valid のまま費用 ledger を全欠落させ、レポート上の費用証拠を黙って過小化する。

既にロード済みの material manifest または検証済み descriptor 状態を `_aggregate_verified` へ渡すべきであり、この helper で path を再読してはならない。

### 5. price snapshot の一度読み契約は守られていない

- 対象: `tools/codex_reasoning_ab.py:8840-8891`, `tools/codex_reasoning_ab.py:9031-9053`, `tools/codex_reasoning_ab.py:9490-9521`, `tools/codex_reasoning_ab.py:10018-10032`
- 失敗シナリオ: schedule 検証時の `_validate_frozen_price_snapshot_record` が正しい bytes を読み検証した後、cost loader の二回目の read 前に snapshot を読取不能または別 bytes にする。二回目は失敗し、既に受理した検証済み tree を使わず report を invalid にして費用 key を全欠落させる。
- 成果物影響: 同一の bound schedule がファイル変更時刻により受理または拒否へ分岐し、`resource_ledger.normalized_cost` と軸 ledger の生成集合が変わる。

二回とも SHA と validator を通すので、SHA-256 衝突を仮定しない限り異なる単価を valid として出す経路ではない。しかし `ruling.md:146-147` の「一度だけ読み、その tree を計算に使う」契約には明確に違反している。

### 10 verb の digest 監査

| verb | 先行成果物の exact 検査 | 判定 |
|---|---|---|
| `build-snapshot` | root producer。oracle に digest を記録する (`:3371`) | 可 |
| `verify-snapshot` | 先行 oracleを受け取らず比較不能 | 不可 |
| `collect-run` | launch receipt を比較 (`:7989-7991`) | 可 |
| `supervise-pair` | schedule を比較 (`:7389-7399`) | 可 |
| `aggregate` | material manifest、schedule、ledger、oracle、receipt、adjudication を replay 検査 (`:10635-10695`, `:10898-10931`, `:9200-9265`) | 可 |
| `verify` | `aggregate` と同じ replay 経路 | 可 |
| `make-packets` | source manifest と schedule を比較 (`:11176-11180`, `:11203-11208`) | 可 |
| `append-verdicts` | packet state は比較するが既存 verdict log row を比較しない | 不可 |
| `freeze-verdicts` | packet state と全 verdict row を比較 (`:11492-11513`) | 可 |
| `reveal-mapping` | state、freeze、verdict row、private mapping を比較 (`:11584-11646`) | 可 |

digest 欠落は `_require_task_manifest_sha256` の `.get(...) != expected` により、検査される箇所では fail-closed である。迂回点は上記二つである。

## nit / backlog

- `unavailable` は `tools/codex_reasoning_ab.py:9743-9747` で必ず report reason に入り、`:10401` の `valid` を false にする。したがって unavailable arm の高い平均を valid evidence として通す通常経路はない。ただし軸 row に `unavailable_count`、`not_incurred_count`、`scheduled_attempt_count` が無く、`attempt_count` が観測済みだけを意味することも機械可読でない。valid を無視する下流では平均を過大化できるため、分母内訳を出すべきである。

- 全 0 かつ prelaunch marker 無しは `unavailable`、正規 prelaunch 全 0 は `not-incurred` となり、人工 0 が `observed` 金額 0 に入る経路は見つからない。問題は must-fix 1 の「marker が非ゼロ token より優先される」経路である。

- cost subtree では全算術が `Decimal` で、出力金額は文字列である。axis でも `Decimal` へ戻しており、float を出す production 経路は見つからない。

- component は `:9686`、総額は `:9692` で別々に丸められ、axis は丸め済み試行額を `:9778-9781` で再加算する。ただし現行凍結単価は、整数 token あたりの金額が全て `0.00000001` の整数倍である。したがって現行 snapshot では component 和、総額、axis 和は食い違わない。将来 snapshot で単価の小数桁が増えた場合は未丸め Decimal を集計する必要がある。

- `cache_write` の非対称性は出力から読める。`unit_prices` に sol `5`、luna `0.25` が残り、`unaccounted_token_categories=["cache_write"]`、`coverage_status="partial"`、component 不在が併記される (`:9601-9612`, `:9764-9775`)。ただし数量不在なので過小額自体は定量化できない。

- loader は UTF-8 strict、全階層 duplicate key、`NaN` / `Infinity`、top-level object、exact int の `schema_version` を実装している (`:2676-2715`, `:2597-2602`)。宣言された四条件との不一致はない。`test_task_manifest_loader_accepts_only_strict_canonical_json_object` という名称に反し、入力 bytes 自体が canonical JSON であることは要求しないが、裁定は「tree の canonical bytes を digest 化」としているため契約違反ではない。

- 実装子 B が上流所有とした三条件は production call graph では本当に上流で担保される。唯一の production caller は検証済み snapshot tree を返す `:9490-9521` を通り、validator は mapping grammar を `tools/t189_price_snapshot.py:617-624`、正の canonical decimal を `:627-647` で検査する。

- 一方、cost 層の次の拒否は production call graph では恒偽である: price version 不一致 (`:9570-9577`)、unknown model / malformed SKU / prices / unknown list (`:9579-9600`)、mapping または prices 不在 (`:9649-9654`)。direct helper test では発火できるが、実験経路では先行 schedule validator または snapshot validator が先に落とす。M09 を独立な実効 gate と数えてはならない。

- `_find_rollout` の候補列挙には `except Exception: pass` が残る (`:520-532`)。fast-path の実装欠陥を full scan へ落とせる。通常の build 経路は後段 SHA 再検証を行うため、今回の final evidence bypass にはならないが、fix の「実装欠陥は伝播」という説明はこの範囲には当てはまらない。

- `supervise_pair` の `except Exception` (`:7483-7500`) も広いが、failure row を作った後 `:7629-7635` で非ゼロ終了するため、正常成功としては握り潰さない。

## 検出力の無いテスト

以下は少なくとも当該テストを緑のまま通る変異である。

- `test_task_manifest_loader_accepts_only_strict_canonical_json_object` (`test_codex_reasoning_ab.py:6099`): loader の duplicate/nonfinite/UTF-8 拒否を全て外して通常 `json.loads` にしても、正例だけなので緑。
- `test_task_manifest_loader_rejects_non_object_top_level` (`:6171`): `_load_task_manifest` の top-level `dict` 検査を外しても、直後の `_validate_task_manifest` が同じ入力を拒否し緑。M14 の単一理由性は無い。
- `test_material_replay_rejects_task_manifest_exchange_at_digest_consumers` (`:8565`): material manifest 冒頭の検査だけ残し、schedule、ledger、oracle、receipt、adjudication の digest 検査を全て外しても緑。
- `test_task_manifest_cli_option_surface_is_closed` (`:9369`): parser option だけ残し、10 verb の dispatch が `task_manifest` を無視しても緑。
- `test_m16_cli_external_manifest_is_loaded_before_alias_resolution` (`:9407`): `build-snapshot` 以外の九つの CLI dispatch が既定 manifest を渡す変異は緑。
- `test_default_and_explicit_default_task_manifest_cli_results_are_equal` (`:9450`): 明示 option を無視して常に既定 manifest を使う変異でも緑。
- `test_m15_packet_consumer_requires_exact_task_manifest_digest_once` (`:12514`): `freeze-verdicts` の packet-state 検査だけ残し、他 consumer の検査を外しても緑。
- `test_task_manifest_digest_is_recorded_through_packet_freeze_and_reveal` (`:12534`): 各関数が引数 manifest を無視し、常に既定 digest を記録する変異でも、全呼出しが既定 manifest なので緑。既存 verdict log の digest 未検査も検出しない。
- `test_m10_cost_snapshot_loader_reads_and_validates_one_byte_observation` (`:13708`): helper 単体の read は 1 回のまま、schedule 検証と cost 計算の全経路で二回読む現実装が緑。また validator の返した fresh tree を捨て、元の parsed tree を返す変異も検出しない。
- `test_p01_bound_cost_is_mapping_driven_decimal_partial_and_uncertified` (`:13737`): `normalized_cost_axis_ledger[*].accounted_amount` を任意の文字列へ変えても、型しか assert しないため緑。component ごとの `amount` も未検査。
- `test_m01_unavailable_zero_tokens_never_enter_cost_denominator` (`:13785`): unavailable reason を残したまま top-level `valid=true` を強制する変異でも緑。
- `test_m02_prelaunch_zero_tokens_are_not_incurred_and_not_counted` (`:13808`): prelaunch marker があれば非ゼロ、負数、非 int token でも無条件に `not-incurred` とする現行変異が緑。
- `test_replay_failure_tokens_are_unavailable_and_not_counted` (`:13828`): replay failure を持つ report を top-level valid にする変異を検出しない。
- `test_cost_token_field_unavailable_matrix` (`:13857`): malformed field ごとの failure reason を失い、全て同じ generic reason にしても緑。
- `test_m03_cost_json_tree_contains_no_float` (`:13877`): float で内部計算し、最後だけ文字列化する変異は、選んだ exact 値が同じ文字列になれば緑。Decimal 計算自体は証明していない。
- `test_m04_cost_rounding_is_eight_place_half_even` (`:13889`): formatter を残したまま、component を丸めてから総額や axis に加える変異は緑。
- `test_m07_cache_write_is_unaccounted_and_never_a_zero_component` (`:13935`): luna の `cache_write` 単価を誤らせても sol しか検査しないため緑。20 倍の非対称性を固定していない。
- `test_m08_p02_p04_null_v3_and_legacy_emit_no_cost_keys` (`:13949`): cost 発火条件を恒偽にして bound v3 でも費用を一切出さない変異は、このテスト単体では緑。
- `test_schedule_descriptor_absence_emits_no_cost_keys` (`:13994`): `_aggregate_has_schedule_descriptor` を常に false にする変異でも緑。
- `test_m09_unknown_model_has_one_direct_cost_rejection` (`:14017`): 上流 `_slot_dimensions` の unknown-model 拒否を外しても direct helper だけを検査するため緑。end-to-end M09 の単一理由性を示さない。
- `test_cost_constant_false_rejections_are_owned_by_snapshot_validator` (`:14035`): cost interpreter が reasoning token を二重計上する、または unsupported operation を処理する変異でも、validator しか呼ばないため緑。

上記以外の新設された M11、M12、M13、nonfinite、unreadable、collect digest mismatch、rollout の MemoryError/TypeError/AttributeError 伝播、external provenance pin、make-packets mismatch、M05、M06 の direct seam については、対象変異を残したまま当該テストを通す具体的変異は見つからない。

## 親裁定への反論

### §2 digest 連鎖

digest 連鎖を in-scope にした判断自体は正しい。`known_finding_ids` と `oracle_kind` は正しさ gate の受理集合を変えるため、CLI 入力口だけ追加する案は採れない。

ただし裁定自身が `ruling.md:98-102` で定めた fallback を `verify-snapshot` に適用できていない。先行 digest を運べない verb へ option を追加しないという裁定に従えば、現在の 10 verb surface は受理できない。また `append-verdicts` は各 consumer で即時拒否するという `:91-95` を満たさない。

### §3 費用を certified と呼ばない判断

反論なし。cache-write 数量欠落、served model attestation 不在、gate 未接続があるため、`partial` / `not-certified` とする判断は正しい。現行出力も `_certification_scope` を変更していない。

### §5 変異登録

誤りが残る。

- M10: 実装全経路は既に二回 read しているのに、helper 単体テストを KILL 証拠にしている。
- M14: loader 検査を外しても validator が同じ配列を拒否し、単一理由性が無い。
- M06: upstream token validator と cost helper の拒否が重なるため、end-to-end 単一理由性が無い。
- M09: unknown model は `_slot_dimensions` が先に拒否し、production cost rejection は恒偽。
- M15: freeze の一箇所しか照準せず、10 verb の consumer closure を代表していない。実際に `append-verdicts` の既存 log 穴を見逃している。

したがって M10、M14、M06、M09 は現登録のまま KILLED と扱えず、M15 は consumer ごとの変異へ分割する必要がある。

## 総括

静的レビュー結果は NO-GO である。must-fix は 5 件で、特に重大なのは、非ゼロ token を持つ prelaunch row が `not-incurred` として valid report へ残ること、`verify-snapshot` の manifest 再ラベル、`append-verdicts` の既存 log digest 未検査、material manifest 再読による valid report の費用全欠落である。

loader の四つの strict 条件、Decimal と JSON 非 float、現行単価での丸め整合、cache-write の partial 表示は静的には成立している。

こちらでは pytest を実行していない。親が実測した 559 passed / 2 skipped は事実として区別し、本レビューの正しさ根拠には用いていない。