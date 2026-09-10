## A. 4 点目の射程

親の provisional 裁定を採る。契約 9 節の「供給」は C2 では producer 側の実値域を成立させる意味であり、`launch_floor_attempt()` の production 呼出しまで要求しない。

根拠は次のデータフローである。

- launcher の production dependency は既に `calibrator_runner.capture_measure_point` に固定されている: `orchestrator/campaign/s8b_floor_attempt_launcher.py:210-213`
- launcher は private sink を capture へ渡し、open 後に `repetition_evidence` として固定する: 同 `:1002-1012`, `:1072-1075`
- 現 campaign の default 実測経路は `measure_point()` を使用する: `orchestrator/campaign/s8b_floor_campaign.py:7848-7876`
- C2 では runner の `capture_measure_point()` と `measure_point()` の両方を同じ 7-key schema にする。前者が将来の launcher 入力、後者が現 campaign の実値域となる
- 現 campaign は `_project_scalepoint()` でその実値を journal session へ載せる: 同 `:6280-6286`, `:6371-6393`

`test_rep_integrity_positive_control_default_measure_point` (`orchestrator/tests/test_s8b_floor_campaign.py:9242`) に部分実行例外 case を追加し、runner 実装から campaign journal まで次を固定する。

- 正常 rep: `execution_failure is False`
- `TimeoutExpired` または `OSError` を捕捉した rep: `execution_failure is True`
- 非 zero rc だけの rep: `execution_failure is False`
- top-level `exec_failures` は True の本数
- `rep_integrity_failures` は別途再導出される

この receipt が証明するのは「実 campaign 経路が launcher に渡せる値域を産出する」までである。`launch_floor_attempt()` がその値を実際に消費した、台帳へ terminal が記録された、result v5 が proof chain を束縛した、とは主張しない。

したがって C2 内の campaign→launcher 配線量は 0 file / 0 line。実配線は D1341 の proof-chain 束縛と同じ後続単位に残す。

強い読みとして「供給とは現 production caller からの実 invocation である」と定義し直すなら provisional 裁定は満たさない。その場合は少なくとも次が必要になる。

- `s8b_floor_campaign.py:5951-6005`: ticket 消費を launcher reservation/marker 発行へ組み替える
- 同 `:6032-6094`, `:6515-6588`: run-start identity、profile、binding、closed genesis を `_Runner` に保持させる
- 同 `:6223-6350`: probe・capture・terminal 化を launcher へ委譲する
- 同 `:6356-6393`: `_finish_session()` を pure builder と journal emit に分離する
- `s8b_holdout_admission.py:4349-4392`, `:5082-5103`: observation admission と consumption marker の対応を配線する
- launcher、campaign、admission と対応 test の計 5 file 前後、概算 350-550 行

これは C2 の 7-key 化を大幅に超えるため、今回の既定案にはしない。

## B. 構造化 execution_failure の形

7 番目の key は次で固定する。

```python
"execution_failure": False  # 捕捉例外なし
"execution_failure": True   # runner が rep 実行例外を捕捉
```

型は exact `bool`、値域は `{False, True}`。`isinstance(value, bool)` ではなく `type(value) is bool` で検査し、`0` / `1` / `None` は拒否する。

`None` と key 欠落のどちらも採らない。

- key 欠落は campaign と verifier の exact 7-key 等値を壊す
- `None` は「正常」「未観測」「値の欠落」という第三状態を持ち込み、top-level count の意味を曖昧にする
- 未観測や carrier 欠落は既存の `returncode=None`、`counter_status="incomplete"`、`rep_integrity_failures` で表現できる
- boolean は契約 3 節の必要量、すなわち「runner が例外を捕捉したか」だけを表す

runner では次を同時に直す。

- deferred surface の初期 observation: `runner.py:938-951`
- deferred surface の例外捕捉と finally: `:956-1002`
- direct surface の初期 observation: `:1104-1117`
- direct surface の例外捕捉と finally: `:1130-1215`

例外型名と message は新 field に載せない。`type(exc).__name__` や `str(exc)` は外部実行に由来しうるため、信頼計算へ運ばない。

既存の診断用 notes (`runner.py:966-980`, `:1171-1186`) は残してよい。ただし C2 後はどの算出も notes を読まない。文字列は診断データとしてのみ保存され、`exec_failures` の判定入力にはならない。

## C. campaign の算出変更

`_EXEC_FAIL_RE` と `_count_exec_failures()` は呼び手ごと削除する。

- 定義: `orchestrator/campaign/s8b_floor_campaign.py:1879-1890`
- 唯一の呼び手: 同 `:1965`
- `re` import は他の多数の正規表現が使うため残す

`_project_scalepoint()` (`:1893-1971`) は observation の exact 7 key と exact bool を検査し、`execution_failure is True` の本数を `exec_failures` とする。`complete` には `execution_failure is False` を追加する。したがって実行例外の rep は同時に integrity failure にもなりうる。

中央 verifier も独立に同じ値を再導出する。

- `s8b_floor_stats.py:64-67`: `_REP_OBSERVATION_KEYS` を 7 key にする
- 同 `:471-589`: `_derive_rep_integrity()` を `(errors, rep_integrity_failures, exec_failures, qualified_tps)` の 4 値へ拡張する
- exact key 不一致を error にするだけでなく、その rep の integrity failure にも数える
- `execution_failure` が exact bool でない場合は schema errorかつ integrity failure
- `execution_failure is True` は valid evidence だが qualified rep ではない
- 同 `:891-943`: `SessionRecord.exec_failures` と再導出値の等値を検査する
- `s8b_floor_campaign.py:8368-8389`: resume gate でも両 count と qualified throughput を再導出して照合する

C1b の terminal evidence も opened measurement について equality-only から rep 再導出へ進める。

- `s8b_terminal_evidence.py:637-645`: `_derive_rep_integrity()` の errors と exec count を保持する。opened measurement の schema error は拒否する
- pre-probe competing / capture failure の空 observation は既存の unavailable projection として例外扱いを維持する
- 同 `:1175-1205`: opened measurement の `campaign_record.exec_failures` を private sink の True 本数と照合する
- internal snapshot に count を足すだけで、terminal evidence 公開 schema は増やさない

`exec_failures` と `rep_integrity_failures` の分離は次で固定する。

- execution exception: `exec_failures == 1` かつ `rep_integrity_failures == 1`
- nonzero rc、counter 欠落、schema 不備: `exec_failures == 0` かつ `rep_integrity_failures == 1`
- notes に `"5/5 reps failed to execute"` を注入しても全 flag が False なら `exec_failures == 0`
- notes が空でも flag が True なら `exec_failures == 1`

証跡 carrier 欠落時の padding (`s8b_floor_campaign.py:1897-1912`) は 7 番目を `False` にする。carrier 欠落から実行例外を捏造してはならない。既存の `returncode=None` と incomplete status が全 rep を integrity failure に倒すため、受理集合は広がらない。

## D. pin 閉包の残り

共有 fixture の observation 変更は、4 consumer 内の 64hex literal へは一件も伝播しない。

- `test_s8b_holdout_freeze.py` の唯一の literal `:41` は `_V2_CANONICAL_PROBE_DOCUMENT` の serializer golden (`:31-42`) で、session observation と無関係
- 同 file は `_synthetic_floor_result()` を `:1715` と `candidate_repository()` 経由で使うが、result / manifest / journal の hash は `:1740-1741`, `:1767-1770` および fixture `:448-478` で動的算出される
- `test_s8b_oracle_driver.py` の 46 literal (`:149-264`) は T080 source、metadata、receipt の golden。共有 fixture から使うのは `fill()` / `per_pair_floor()` / `budget()` (`:2130`, `:2144`, `:5336`) であり、`_synthetic_floor_result()` は呼ばない
- `test_s8b_oracle_manifest.py` の 19 literal (`:55-100`) は schedule / reviewed-spec / generator source の golden。呼ぶのは `fill()` (`:214`, `:286`, `:769`, `:920`, `:1553`) だけ
- `test_s8b_oracle_report.py` に 64hex literal は 0 件。ここも `fill()` / `budget()` (`:209`, `:330`) だけ
- `s8b_v2_freeze_fixture.fill()` (`:61-72`) は floor と budget しか変更せず、6-key observation producer は `_synthetic_floor_result()` (`:128-186`) に隔離されている

したがって更新対象は `s8b_v2_freeze_fixture.py:155-163` の observation literal だけであり、4 consumer の golden literal 更新は不要。

`missing_perf_events` を含む 12 file の判定は次のとおり。

| file | 6-key exact 等値への依存 | C2 の処置 |
|---|---|---|
| `calibrator/runner.py:938-1002,1104-1215` | なし。producer | 4 observation literal と両例外経路へ boolean を追加 |
| `campaign/s8b_floor_campaign.py:1897-1970` | あり。`:1947-1950` が直接 exact 等値 | padding、集合、complete、count を更新 |
| `campaign/s8b_floor_stats.py:64-67,471-589` | あり。`:487` が中央 exact gate | 7-key 化、型検査、2 count 再導出 |
| `tests/s8b_v2_freeze_fixture.py:155-163` | file 内にはなし。holdout candidate から verifier へ伝播 | False を追加 |
| `tests/test_calibrator.py:510-550,581-595` | なし。field 単位の producer 検査 | True/False 列の assertion を追加 |
| `tests/test_s8b_attempt_registry.py:346-357` | file 内にはなし。sealed evidence へ伝播 | False を追加 |
| `tests/test_s8b_floor_attempt_launcher.py:237-244,863-876,943-955,1409-1420` | `:863-876` に tuple/dict 全件等値あり。v2 は evidence gate にも伝播 | literal と期待値を更新 |
| `tests/test_s8b_floor_campaign.py:884-909` | production `_project_scalepoint()` の exact gate に直接投入 | fake に False、失敗 case に True |
| `tests/test_s8b_floor_stats.py:262-280` | production verifier の exact gate に直接投入 | fixture に False、schema/count 負例追加 |
| `tests/test_s8b_ratified_freeze.py:524-543` | emitter→campaign projector への間接依存 | False を追加 |
| `tests/test_s8b_ratified_verify.py:367-397` | ratified verifier→floor stats への間接依存 | False を追加 |
| `tests/test_s8b_terminal_evidence.py:107-115` | sealing 時の private sink gate への依存 | 通常 False、full-exec case は True |

この 12 file に加え、`orchestrator/campaign/s8b_terminal_evidence.py` を opened private sink と campaign count の等値検査のため変更する。新しい production file は作らない。

semantic inventory は次の配置で不変にできる。

- `test_official_perf_closure.py` の既登録 file 内だけを変更する。`runner.py`, `s8b_floor_campaign.py`, `s8b_floor_stats.py`, `s8b_floor_attempt_launcher.py` は `_REVIEWED_PERF_FILES` の `:46`, `:64-67` に既登録
- `s8b_terminal_evidence.py` では既存 `_derive_rep_integrity()` の返値を消費するだけにし、新しい perf 判定・tracked call・production file を足さない
- `_production_perf_files()` (`:533-545`) と集合等値 assert (`:905-909`) は無変更
- `test_t671_source_binding.py` の 63-path tuple は変更しない。既存 `runner.py` は `:67` に既登録で、production path の追加がないため件数 assert `:267-269` も無変更
- `s8b_ratified_freeze.py:265-266` の session top-level key は nested observation key と別なので変更しない
- attempt registry v1 event keys、`FROZEN_MANIFEST`、whole-file SHA golden は変更しない

## E. 実装子の分割

3 本を直列にする。全て `author` とし、file 所有は排他にする。

1. carrier producer 子

   - `orchestrator/calibrator/runner.py`
   - `orchestrator/tests/test_calibrator.py`
   - 役割: 両 measurement surface の 7-key 化、捕捉例外の exact bool、正常・timeout・OSError・nonzero rc の固定

2. 算出・信頼 gate 子

   - `orchestrator/campaign/s8b_floor_campaign.py`
   - `orchestrator/campaign/s8b_floor_stats.py`
   - `orchestrator/campaign/s8b_terminal_evidence.py`
   - `orchestrator/tests/test_s8b_floor_campaign.py`
   - `orchestrator/tests/test_s8b_floor_stats.py`
   - `orchestrator/tests/test_s8b_terminal_evidence.py`
   - 役割: notes regex 除去、2 count の独立再導出、resume / verifier / sealed evidence の等値検査、padding

3. fixture・consumer pin 子

   - `orchestrator/tests/s8b_v2_freeze_fixture.py`
   - `orchestrator/tests/test_s8b_attempt_registry.py`
   - `orchestrator/tests/test_s8b_floor_attempt_launcher.py`
   - `orchestrator/tests/test_s8b_ratified_freeze.py`
   - `orchestrator/tests/test_s8b_ratified_verify.py`
   - 役割: 全 observation literal の 7-key 追随、launcher production dependency が `capture_measure_point` のままであることの pin

直列順は 1→2→3。概算は production 4 file、test/fixture 9 file、追加・更新 120-180 行、regex helper 約 12 行削除。新規 production file は 0。

4 consumer の oracle/freeze test file、official perf inventory、T671 inventory は所有対象に入れず、親の回帰走行対象だけにする。

## F. 変異の照準

以下は全て通常 pytest 経路で kill する。専用の非通常 kill 手段が必要なものはない。新設予定 node は明記した。

| # | 変異する file:line | 変異 | kill する test node id |
|---|---|---|---|
| M1 | `runner.py:956-1002` | deferred surface の捕捉例外でも `execution_failure=False` にする | `orchestrator/tests/test_calibrator.py::test_capture_measure_point_rep_observations_mark_execution_failures` 新設 |
| M2 | `runner.py:1130-1215` | direct surface の timeout/OSError flag を立てない | `orchestrator/tests/test_calibrator.py::test_measure_point_rep_observations_are_indexed_across_timeout_exception_and_rc` |
| M3 | `s8b_floor_campaign.py:1879-1890,1965` | structured flag を無視し notes regex から算出する | `orchestrator/tests/test_s8b_floor_campaign.py::test_exec_failures_are_derived_from_execution_failure_not_notes` 新設 |
| M4 | `s8b_floor_campaign.py:1926-1970` | `exec_failures = rep_integrity_failures` とする | `orchestrator/tests/test_s8b_floor_campaign.py::test_exec_failures_and_rep_integrity_failures_remain_distinct` 新設 |
| M5 | `s8b_floor_campaign.py:1897-1912` | carrier 欠落 padding を True、None、または key 欠落にする | `orchestrator/tests/test_s8b_floor_campaign.py::test_missing_rep_observation_carrier_pads_execution_failure_false` 新設 |
| M6 | `s8b_floor_campaign.py:1946-1959` | complete 述語から `execution_failure is False` を外す | `orchestrator/tests/test_s8b_floor_campaign.py::test_execution_failure_is_also_an_integrity_failure` 新設 |
| M7 | `s8b_floor_stats.py:64-67,482-512` | exact key 集合を 6 key に戻す、または key 不一致を failure に数えない | `orchestrator/tests/test_s8b_floor_stats.py::test_verify_requires_exact_seven_key_rep_observation` 新設 |
| M8 | `s8b_floor_stats.py:511-589` | `0` / `1` / `None` を execution flag として受理する | `orchestrator/tests/test_s8b_floor_stats.py::test_verify_rejects_non_bool_execution_failure` 新設 |
| M9 | `s8b_floor_stats.py:891-943` | top-level `exec_failures` と rep 再導出値の等値検査を外す | `orchestrator/tests/test_s8b_floor_stats.py::test_verify_rejects_exec_failure_count_mismatch_independently_of_integrity` 新設 |
| M10 | `s8b_terminal_evidence.py:637-645,1175-1205` | private sink の exec count または schema error を無視して campaign count を信用する | `orchestrator/tests/test_s8b_terminal_evidence.py::test_sealed_terminal_rederives_exec_failures_from_private_sink` 新設 |

さらに既存 `test_rep_integrity_positive_control_default_measure_point` の parameter に `execution_failure` を追加し、実 campaign 経路で M1-M6 の複合陽性対照にする。mutation probe では期待赤 node を先に実測し、本走でその集合を exact 固定する。

## 親の実測への異議

意味のある異議は 2 件、行番号だけの補正が 1 件ある。

- `s8b_floor_campaign.py:1039-1045` は rep observation の complete 述語ではない。現 tip `0cb90c5924` では protocol resolver 内である。complete の exact 6-key 述語は `:1946-1959`
- runner の例外捕捉と observation 生成を `:958-1000` だけとするのは C2 の変更閉包として不十分。現 campaign が使う direct `measure_point()` にも等価な捕捉が `:1163-1188`、observation 生成が `:1197-1215` にある。両 surface を同時に変更しないと campaign の実値域は 6 key のままになる
- `test_official_perf_closure.py` の `_REVIEWED_PERF_FILES` は現 tipでは `:44` 開始で、`:43` は `_PERF_DISCOVERY_CALLS`。`_production_perf_files():533` と集合 assert `:905` は実測どおり

production caller 0 件、launcher import 元 1 件、campaign の `attempt_registry` 参照 0 件、12 file の列挙、whole-file golden 0 件、`FROZEN_MANIFEST` 対象外については異議なし。

## 総括

C2 は `execution_failure` を exact bool の 7 番目の key とし、runner の両 measurement surface、campaign、中央 verifier、terminal evidence を一続きで閉じる。notes regex は helper と唯一の呼び手ごと除去し、notes は診断専用に残す。

変更対象は既存 13 file、新規 production file 0。campaign→launcher の production 呼出し配線は行わないが、launcher が固定している capture primitive と現 campaign の direct primitive の両方が同じ実値域を産出する状態を作り、実 campaign 経路の test receipt で記録する。

本段では静的読解と `rg` のみを行った。ファイル作成・変更、commit、pytest 実行は行っておらず、テスト緑は主張しない。