## 実装計画

**新規 module 案を採る。既存 3 系列の driver・loader・成果物生成処理は変更しない。** 共通部分は、本走が明示指定した場合だけ有効になる引数を追加する。

以下の行番号は現物のアンカー。新規 file の `:1` は新設位置を表し、未実装の関数に架空の行番号は付けない。今回は静的読解・検索のみで、編集・テスト・計測は実施していない。

### 1. `orchestrator/campaign/b10_backoff_static_tail_formal.py:1` — 新規

**現状:** 本書を consume する実装は存在しない。先例は `b10_backoff_shape_sweep.py:1113,1763`、系列 driver は `backoff_extended_sweep.py:1331`。

**変更後:** 同じ file に、次の責務を関数単位で分けて置く。

| 新設する関数・型 | 置く内容と理由 |
|---|---|
| `StaticTailSpec`、`PreregistrationBinding` | spec 全体の検証済み値と、文書 commit・raw 文書 SHA-256・抽出 spec SHA-256。測定条件を共有定数から拾わせない。 |
| `extract_spec_bytes(raw)` | 完全な HTML marker 行を一対だけ取り、内側の先頭・末尾 fence 行だけを除く。bytes を保持して hash と JSON parser の両方へ渡す。 |
| `parse_preregistration(raw)` | §5 の全 section を parse。重複 JSON key、非有限値、型違い、未対応の規則を拒否。履歴開示 section も検査・保持するが、解析標本には渡さない。 |
| `load_preregistration(repo_root, commit)` | canonical path の raw bytes と指定 commit の file 内容を一致確認し、祖先関係を確認。先例の Git blob ID を流用しない。 |
| `registered_points(spec, workload)` | spec の格子生成規則を再計算し、登録 physical/raw 対応と照合。昇順 label に指定 seed の shuffle を一回適用し、登録順序と照合。 |
| `config_for(spec, binding, workload, …)` | 独立した campaign identity を作る。run kind、全実行値、格子・順序、正しさ反復数・mode、source/toolchain/環境契約/較正 identity、三つの事前登録 binding を `search_config` に入れる。 |
| `run_workload(preregistration, workload, …)` | 既存の site admission、単独占有、較正照合、patch、condition gate、build admission、perf preflight、`run_campaign` を使う。本走用の引数はすべて spec から組み立てる。 |
| `require_complete_static_builds(spec, builds)` | spec の物理量集合と性能ビルド集合を exact 比較。各値が exact `BuildResult`、`trace is False`、genome 一致、完全長 lowercase SHA-256、全 digest 相異であることを要求。 |
| `load_explore_correctness_mode(path)` | 探索 WAL の採用済み正しさ記録から `workload.tag` の比較基準だけを取り出す。性能標本を返さない。 |
| `load_formal_campaign(spec, binding, campaign)` | certified admission → attempt replay → raw 行対応付け → observation 構築。探索 campaign は formal loader の入口で拒否する。 |
| `analyze_cohort(spec, campaigns)` | 三 campaign の同一性・全 cell/rep 完備性を検査し、整数カウンタから統計量と判定を再構成する。 |
| `materialize_report(…)` | 新 schema の JSON、DAT、完了記録を create-only で発行。失敗時も読み取れた観測と失敗理由を記述用として残す。 |

**規則の実装上の注意:**

- 数値で構造化された field は直接引数にする。`generation_rule`、分類の `definition`、持続区間数など、**文字列にだけ存在する数値は限定した文法で抽出**し、重複して記載された値と照合する。Python の `eval` は使わない。
- 境界参照は測定・報告するが、飽和区間には含めない。
- 標本標準偏差、Welch 自由度、Student t 分位点、`qL/qU/U/L/U_flat` を実装する。分位点は固定の自由度 8 や固定係数で代替しない。必要な数値計算を本 module 内に限定し、独立した分位点の検算値で検証する。
- 全ゼロ、正値→全ゼロ、分散ゼロ、ゼロ→正値の処理順を §4.4 通りにする。閾値比較に独自 epsilon を足さない。
- `required_verdict: "certified"` を **`payload.verdict == "certified"` と解釈しない**。§4.6 の権威は `payload.certified is True`。実探索の `verdict` は `"serializable"`。
- `run_kind = t2500-tail-formal`、schema = `t2500-backoff-static-tail-formal-report/v1`、stem = `t2500-backoff-static-tail-formal` を spec の値と照合して使用する。

**実行時間と再開:**

- `bench_max_rounds=1` を使い、登録された rep を再測定・選別しない。これは既存の非既定引数で指定できる。
- sweep 上限は spec から取得し、本 module の実行境界で期限を強制する。期限例外は `run_campaign` の variant 単位 `except Exception` に吸収されない形にし、外側で incomplete/invalid を記録する。
- PBS の開始時刻・実予約時間・終了根拠を走行記録へ取り込み、spec の job 上限と比較する。取得が必要な scheduler 問合せは専用の読み取り関数一箇所に集める。
- resume は既存 campaign の lock と今回の設定・binding の一致を要求する。別 campaign の cell は結合しない。
- 本 wave でこれらの起動経路は実装・検証するが、job は投入しない。

**理由:** 既存 `RUN_KINDS`、格子、捕捉 class、discovery、report writer に分岐を追加せず、本走固有の受理条件を閉じ込められる。

### 2. `orchestrator/calibrator/benchparse.py:66` — 整数 parser を隣接追加

**現状:** `abort_rate()` は印字値があればそれを返し、fallback も `_num()` による浮動小数化を通る。

**変更後:** 新しい `integer_abort_commit_counts(metrics)` を追加する。

- `abort_counts_` と `commit_counts_` を十進整数文字列として検査し、直接 `int` に変換する。
- 欠落、負数、小数、指数表記、非有限値、合計ゼロは拒否する。
- 既存 `abort_rate()`、`parse_bench_stdout()`、throughput parser の挙動は変えない。

**理由:** 既存系列の丸め値利用を変えず、本走だけに整数由来の経路を与える。

### 3. `orchestrator/calibrator/runner.py:803,938,1010,1064,1111,1230`

**現状:** `capture_measure_point()` と `measure_point()` は別実装。親の `938–1012` だけでは前者しか覆わない。

**変更後:**

- 両関数に `record_rep_integer_counters=False` を追加する。
- True のときだけ、各 rep の metrics 開封後に整数 parser を呼び、rep observation に二つの整数を加える。
- throughput の代入後に同じ rep の値を対応付ける。`finally` 内の初期値 `None` を成功値として運ばない。
- `capture_measure_point()` は token の開封前に metrics・整数値を外部へ出さない。
- False の呼び手には追加 key も新しい拒否条件も適用しない。

**理由:** s8b 等の既存 `rep_observations` の形と遅延開封契約を保つ。

### 4. `orchestrator/campaign/pipeline.py` — 発行経路の最小拡張

| アンカー | 現状 | 変更後・理由 |
|---|---|---|
| `1179` `_PreparedEvaluation` | bench 方針の運搬先 | `record_rep_integer_counters=False` を保持。既存の直接構築を壊さない既定値にする。 |
| `1524` `_prepare_evaluation_core`、`2540` 付近 `evaluate`、`2638` 呼出し | 公開 API から prepare への配線 | 同 opt-in を渡す。正しさ workload は既存引数を使う。 |
| `2440` prepared 構築、`2452` `_bench_prepared` | prepare から bench への配線 | 同 opt-in を転送。本走では全 rep 成功を要求する。qualification の意味には結び付けない。 |
| `1299` `_run_bench`、`1340` `_measure` | `measure_point` 呼出し | 本走だけ rep observation sink と整数 opt-in を渡す。 |
| `1411` 採用 round 確定後 | `rem.point` が採用 throughput の権威 | **その point 自身の** observation から reps を作る。最後に測った別 round の sink を使わない。 |
| `1475` 条件付き payload 追加部 | screening/returncodes の追加 | `bench_payload["reps"]` を本走だけ代入。各要素は spec 指定の四 key だけ。 |
| `1254` conditional key 集合 | 三 key | `reps` 一 key を追加。required 13 key は維持。 |
| `1257,1277,1479` extra 経路 | `{"screening_disabled"}` exact | **変更しない。** reps を caller-owned extra に入れない。 |
| `1484` 最終検査・emit | 隣接した閉包検査と発行 | 配置・検査順を維持する。 |

`reps` は次の形に固定する。

```json
{
  "rep_index": 0,
  "abort_counts_": 123,
  "commit_counts_": 456,
  "throughput_tps": 789
}
```

件数、明示 index、整数型・範囲、throughput の正値・有限性、`reps[i].throughput_tps == tps[i]` を保存前と本走 loader で検査する。丸めた `leading_indicators.abort_rate` は解析に使用しない。

### 5. `orchestrator/campaign/loop.py:347,511,743,774`

**現状:** `run_campaign()` は extra correctness を組み立てるが、legacy の `CorrectnessWorkload` を受け取って `evaluate()` に渡す引数がない。

**変更後:**

- `correctness=None` と `record_rep_integer_counters=False` の keyword 引数を追加する。
- 非既定時だけ `evaluate_options` に入れる。既存 caller の呼出し形を維持する。
- 本走 driver が `CorrectnessWorkload(reps=spec.execution.correctness_reps_per_cell)` を渡す。
- 本走では extra correctness、screening、balanced schedule、fanout を選ばない。legacy workload の flags は保持する。
- この反復方針・mode・flags は本走の campaign identity に記録し、runtime 引数と照合する。

**理由:** 既存の `pipeline.py:2153` の逐次反復へ到達させるための配線だけが不足している。

### 6. loader の raw bytes 対応 — 共通 admission/WAL は変更しない

新 module の `load_formal_campaign()` に置く。参照アンカーは次の通り。

- `artifact_admission.py:295`：decision が campaign id、lock SHA-256、WAL 全体 SHA-256 を持つ。
- `artifact_admission.py:285`：immutable record 自身には raw bytes がない。
- `wal.py:362,435,450`：厳密 parser と物理行の扱い。
- `backoff_extended_sweep.py:1023`：admitted view と committed attempt の既存消費例。

admission 済み snapshot と同じ lock/WAL 全体 hash であることを確認した bytes を読み、各物理行を再 parse して immutable record と順序付きで対応付ける。**WAL 行 digest は保存された行 bytes の SHA-256。JSON 再 serialize の hash は使わない。**

性能 rep の index は保存された明示値。正しさ observation の index は、採用 attempt 内の五本の verify record の発行順から導出する。性能 index を読取位置から推測する処理とは区別する。

### 7. テストと Layer3 の境界

- 新規 `orchestrator/tests/test_b10_backoff_static_tail_formal.py:1` に spec、binding、driver 配線、loader、解析、materializer、五条件の probe を置く。
- 自走 `_run()` と `__main__` を備える。先例は `test_backoff_extended_sweep.py` 末尾。
- `test_layer3_report.py:1084,1244,1340` は変更対象。conditional key 数と、旧 payload の全 key 集合を明示的に更新する。
- **Layer3 schema は変更しない案とする。** 新しい formal WAL は本走専用 materializer が扱う。既存 Layer3 の全 property と比較するテストは、旧経路の key 集合を明示して維持し、本走専用 `reps` が従来 Layer3 schema では受理されないことも検査する。単に schema を拡張して全 consumer を追随させない。

## 5 件の投入前条件ごとの充足方法と実測手段

### 条件 1 — spec consumer の発火

**入力:** 指定された事前登録文書の実 bytes と、それを含む実 commit。

**走らせる経路:** `load_preregistration → parse_preregistration → registered_points/config_for → driver の測定直前境界`。

**確認:** 二つの SHA-256、全 workload の解決済み格子・順序・PerfConfig・correctness reps を記録する。文書そのものは変更せず、試験用 bytes の marker、fence、順序、型、未対応規則を変えた負例を同じ parser へ通す。runtime 値の変異は、測定呼出し到達前に拒否されることを確認する。

parser 単体の成功だけでなく、**driver がその戻り値を使ったこと**まで示す。

### 条件 2 — 性能 rep の整数保存と再計算

**親の指定入力だけでは不足する。** explore root で `abort_counts_|commit_counts_` を検索したが該当 file は無かった。

代替として、repo に実在する次の保存 stdout を使える。

`output/env/pegasus/t139-r4-env-probe/0:896504.nqsv/run-R01.log:13`

この file には、abort `24435129`、commit `2270481`、印字率 `0.9150`、throughput `756827` がある。隣接する保存 run を含む五入力を選び、元 path・bytes hash を記録する。

**走らせる経路:** subprocess の返却入力だけを保存 stdout に置換し、実 `run_once → measure_point → _run_bench → WAL writer → 本走の rep 読取・再計算関数` を通す。別 probe で `capture_measure_point().open()` も通す。

**確認:**

- WAL に四 key の reps が五本保存される。
- 保存前後で整数が一致し、再計算が整数比に一致する。
- 印字率を変えても解析値が変わらない。
- 欠落・小数・負数・合計ゼロ・index 重複・throughput 不一致を拒否する。
- opt-in 無しでは旧 payload と observation key 集合が変わらない。

これは保存経路の再生実測であり、T-139 の数値を formal cohort の標本として採用する試験ではない。

### 条件 3 — observation の出所導出

**入力:** 探索の実 lock/WAL、および probe が production writer で新規発行した試験 campaign。

**走らせる経路:** admission、attempt replay、raw 行対応付け、observation 構築、report materialization。

導出元を固定する。

| field | 導出元 |
|---|---|
| `source_run_kind` | lock の identity 内の run kind |
| `campaign_id` | layout basename と lock identity の一致 |
| `campaign_lock_digest` | 実 lock raw bytes と admission decision |
| `attempt_id` | 採用 commit に結び付く build attempt |
| `rep_index` | 性能は保存された明示 index、正しさは採用 attempt の発行順 |
| `wal_record_digest` | 対応する保存 JSONL 行 bytes |
| `canonical_genome` | 同 attempt の `build_start.payload.genome` |
| `source_measurement` | bench/verify の stage から導出 |

探索の実 campaign は formal 入力として拒否されることを実測する。成功側には新規の試験 campaign が必要であり、探索 lock を書き換えて成功例にしてはならない。

### 条件 4 — 五本の正しさ記録の実発行

**既存 WAL の一行を五回 replay するだけでは不足する。**

**入力:** spec の反復数と、既存 `orchestrator/tests/fixtures/g1_serial` の trace fixture。負例には既存 `r1_write_skew` 等を使う。

**走らせる経路:** driver の設定生成 → `run_campaign → evaluate → _run_one_pass → _execute_verification_repetition → 実 verifier/capability 発行 → _project_repetition_outcome → 実 WAL writer`。

trace process の境界で fixture を供給し、verifier、capability、commit receipt、WAL 発行は本物を使う。`test_campaign.py:5998` の実 verifier を呼ぶ fixture 経路が参考になる。

**確認:** 一 attempt に verify 五本、その後に bench、commit が並び、committed verify に五本残る。途中 rep に anomaly を入れた場合、その場で reject され、後続 rep と性能測定が走らない。

これで発行機構の実測はできる。新しい CCBench trace 走行を五回行ったことまでは主張しない。

### 条件 5 — mode の記録と探索との一致

**入力:** 探索実 WAL の `verify_done.payload.workload.tag` と、条件 4 で新規発行した記録。

**走らせる経路:** 探索 mode 専用 reader → 本走設定 → verify 発行 → 本走 loader → report。

**確認:** 比較基準が実記録から `legacy` と解決され、本走の五本すべてに同じ座標がある。report に各正しさ記録の mode と出所を出す。欠落、異なる tag、一つだけ違う tag を拒否する。

性能 workload の 48 threads・read ratio を legacy 正しさ workload の flags に流用しない。

## 設計上の分岐への回答

### P1-a — 新規 module を採る

既存 `backoff_extended_sweep.py` は無編集とする。ただし、**新規 module にすれば共通経路の回帰が消えるわけではない**。旧 opt-in 無しの動作を焦点走で守る。

特に次の既存テストは変更せず回す。

- `test_mu1_extended_grid_semantic_golden_except_registered_upper_endpoint`
- `test_mu2_grid_upper_endpoint_matches_adaptive_range`
- `test_t2266_grid_is_exact_eight_points_with_physical_1000_encoded_as_3000`
- `test_t2418_exact_grid_identity_order_and_disclosure_are_literal_pinned`
- `test_t2418_v2_discovery_does_not_select_v1`
- `test_t2418_frozen_campaign_is_rejected_by_existing_t2266_consumer`
- `test_t2266_real_rep_capture_flows_through_wal_consumer_for_every_rep`
- `test_t2418_frozen_wal_view_flows_through_capture_loader_and_reports`

### P1-b — 下限は補強すれば足りる

五条件を**実装経路の発火・保存・発行の実測**として示すには、新規計算ノード計測は不要。ただし親の入力集合には不足がある。

- 条件 2：explore の保存物には必要な生 stdout が見つからない。repo 内の別の実保存 stdout を追加する。
- 条件 3：探索入力は拒否側の証拠にしかならない。production writer が作った試験 campaign を成功側に使う。
- 条件 4：旧 verify payload から新しい verifier capability は発行できない。trace fixture を実 verifier に五回通す必要がある。
- 条件 5：既存 mode を読むだけでなく、新 producer の五本から取り出して比較する。

「本走条件で新しい CCBench process を起動して確認した」という意味の live 実測を求めるなら、この下限では足りない。その場合は計算ノードで非本走 probe が別途必要で、所要は build/cache 状態に依存し未実測。本 wave の保存・発行経路確認には要求しない。

### P1-c — payload の拡張は conditional `reps` 一個

`_BENCH_PAYLOAD_EXTRA_KEYS` は変更しない。そこへ `reps` を加えると、現在 `{"screening_disabled"}` だけを渡す caller が missing key で壊れる。

runner の二経路とも opt-in 時だけ拡張し、既存 s8b caller の nested key 集合も維持する。新規関数を追加する整数 parser は既存丸め率 parser と分離する。

また、**commit 前に焦点走を実行しない対象は pipeline だけではない**。`campaign_lock.py:53,54,77` により、今回変更予定の `loop.py`、`pipeline.py`、`runner.py` はすべて loader binding の対象である。実装・テスト・必要な登録更新を commit してから焦点走する。

### P1-d — 反復機構は足りる。配線が足りない

`pipeline.py:2153` は `workload.reps` 回の逐次反復、`:2098` は各回の verify 発行、`:2155` は即 reject、`:2406` は反復数分の receipt tag 蓄積を実装済み。

不足は `loop.run_campaign()` から legacy workload を渡す経路。新しい反復 engine、fanout、五本への水増し処理は作らない。

### hash 定義

- `document_blob_sha256 = sha256(document_raw_bytes)`
- `spec_sha256 = sha256(extracted_spec_bytes)`
- 指定 commit の Git blob 内容との比較は別の処理。
- 先例の `prereg_blob_sha` は Git object ID なので、本件 binding の値に代入しない。
- lock digest と WAL 行 digest も raw bytes。既存の canonical record reference を代用しない。

### marker 抽出

先例 `b10_backoff_shape_sweep.py:358` の regex は CRLF を許し、capture から JSON 終端の改行を外すため、そのまま転用しない。

本件では行単位の bytes 抽出とし、HTML marker の唯一性・順序、fence、UTF-8、LF、末尾改行一つを検査する。`strip()`、改行変換、`json.dumps()` を hash 対象の生成に使わない。

## 登録簿と焦点走の対象

### 登録簿の全列挙

path 検索では既存二 driver 名を repo の Python/shell/config から検索し、識別子検索では列挙された registry 名に加え、`run_campaign`、`evaluate`、build/spawn の在庫を追った。

**親の列挙から抜けていたのは `test_campaign.py` の writer 呼出し在庫。** また、manual-build 登録と machine caller 登録は用途が異なる。

| file:line | 今回の処置 |
|---|---|
| `test_official_perf_closure.py:44` `_REVIEWED_PERF_FILES` | 新 production module を追加。 |
| 同 `:110` `_REVIEWED_PREDICATES` | 新 loader の `validate_perf_observation`、新 preflight-stop 処理の `validate_perf_preflight_receipt` を、各実 call site の関数名・回数で登録。 |
| 同 `:272,431` `_REVIEWED_GUARDS` / `_ADDED_REVIEWED_GUARDS` | 新設・変更した perf 条件を走査結果と照合。既存 guard を削除して合わせない。 |
| 同 `:636` `_BENCH_AUTHORITIES` | 新 driver は `run_campaign` 経由なので直接 evaluate authority を増やさない。 |
| `test_campaign.py:5346` `expected_inventory` | 新 module → `campaign.loop.run_campaign` を一 call 登録。総数の 20 を 21 にする。evaluate 五 call は維持。 |
| 同 `:5432` `expected_run_calls` | 新 module 一 call を追加し、合計 16 を 17 にする。 |
| `test_p3_build_authority_cli.py:147` `MACHINE_CALLERS` | 新 module を `BACKOFF_SWEEP` として追加。自身で generator receipt を作る実装と対応させる。 |
| 同 `:157,171,173` manual / admitted-manual / non-admissible 在庫 | **変更不要。** 新 module は直接 CMake `--build` を実行しない。 |
| `test_ccbench_spawn_sites.py:83` `_EXPLICIT_NON_CCBENCH_PROCESS_SITES` | 新 module の読み取り専用 Git 問合せと scheduler 問合せを、実装した各一 call site として登録。 |
| 同 `:35,40,45,66` gateway / bounded clients / safe / diagnostic 在庫 | 既存 `run_once` と pipeline trace を再利用するため新 CCBench spawn を追加しない。Git を safe と non-CCBench の両方へ二重登録しない。 |
| `test_layer3_report.py:1084,1244,1340` | producer の exact 閉包と旧 Layer3 schema の対応を上記方針で更新。 |
| `acceptance_duration_ledger.json:1` | 新 file と追加 nodeid の成功 JUnit から実所要を追記。数値を推定で埋めない。 |
| `materializer_admission.py:52` | 新しい manual materializer は作らないので変更不要。 |
| `docs/test-environment-coincidence-ledger.md:326` | 当時の競合 wave による先送り一覧。新 test の常設登録簿ではなく、今回は追記不要。 |

識別子検索で、`_REVIEWED_PERF_FILES/_REVIEWED_PREDICATES/MACHINE_CALLERS/MANUAL_BUILD_FILES/_DIRECT_SAFE_ALLOWLIST/_BOUNDED_RUN_ONCE_CLIENTS/_EXPLICIT_NON_CCBENCH_PROCESS_SITES` の定義・消費は上記三つの在庫テストに集約されていた。path 検索で得た `test_campaign.py` の Counter も含めることで、名前付き registry の検索だけでは落ちる在庫を補った。

### 参照関係から得た焦点走

変更する production symbol の検索対象は、runner の二測定関数、`run_campaign`、`evaluate`、`_prepare_evaluation_core`、`_PreparedEvaluation`、`_bench_prepared`、`_run_bench`、payload 閉包識別子。

private 四 symbol の検索では、production consumer は `pipeline.py` と `loop.py`、テスト consumer は **10 file**、ほかに `orchestrator/manual_probes/test_t2397_a1_source.py` が見つかった。private consumer も以下に含める。

まず直接影響する file を回す。

```text
test_b10_backoff_static_tail_formal.py       # 新規
test_calibrator.py
test_calibrator_deferred_output.py
test_campaign.py
test_layer3_report.py
test_official_perf_closure.py
test_p3_build_authority_cli.py
test_ccbench_spawn_sites.py
test_backoff_extended_sweep.py
test_backoff_extended_sweep_report.py
test_holdout_observation.py
test_s8b_floor_attempt_launcher.py
test_s8b_floor_campaign.py
test_s8b_floor_stats.py
test_s8b_oracle_driver.py
test_s8b_freeze_io.py
test_t674_qualification_contract_lanes.py
test_p3_s4_loop.py
test_p3_s4_loop_sort.py
test_paper_story_a2_certification.py
```

公開 symbol の呼出し、署名検査、fixture、loader binding の path 参照から得た追加候補は次の通り。すべて `orchestrator/tests/` 配下。

```text
test_b10_backoff_shape_sweep.py
test_backoff_consumers.py
test_backoff_sweep.py
test_between_run_floor.py
test_calibrator_certify.py
test_floor_pair_driver.py
test_pegasus_floor_scoping.py
test_s1_direct_comparison.py
test_screening_driver.py
test_t126_qualification_driver.py
test_t1286_commit_receipt.py
test_t1416_backoff_compiler_binding.py
test_t2187_adaptive_const_probe.py
test_verify_fanout.py
test_env_contract_activation.py
test_artifact_admission.py
test_campaign_lock_codec.py
test_t671_source_binding.py
test_p2_2_site_aware.py
test_p3_b4_admission_record.py
test_p3_b4_closed_critic.py
test_p3_b4_proposal_binding.py
test_p3_b4_wiring_probe.py
test_p3_exploration_namespace.py
test_p3_s4_loop_trigger_gating.py
test_paper_story_a1_paired.py
test_paper_story_a1_job_contract.py
test_reflux_campaign_issuer.py
test_s6_sort_sweep.py
test_s8a_trigger_sweep.py
test_s8b_binding_driftguards.py
test_s8c_gate_report.py
test_s8c_preregistration_core.py
test_sort_swo_oracle.py
test_trigger_gate_binding.py
test_t419_probe_causality.py
test_real_repo_serialization.py
test_t126_pegasus_tools.py
test_check_ai_provenance.py
test_codex_agents.py
test_dev_wave_land.py
test_growth_test_holds_contract.py
test_hold_inventory.py
```

`growth_test_holds.py` と `s8b_v2_freeze_fixture.py` は補助 consumer として確認する。manual probe は新規計測に結び付けず、署名互換の静的確認対象にする。

焦点走は commit 後に `tools/run_tests.py` 経由で実施し、新規 test の自走 harness も確認する。所要台帳は成功 JUnit から更新する。完了時の `check_codex_agents.py`、`check_docs.py`、commit 後の `check_ai_provenance.py` も計画に含める。

## 親 brief の誤り

1. **実 stdout が指定 explore 成果物に存在するという前提は未成立。** 通常 file 73 件の検索では整数 counter を含む file が無かった。条件 2 には repo 内の別の保存 stdout を追加する必要がある。
2. **正しさ反復機構だけでは配線が完結しない。** `run_campaign` は legacy correctness 引数を受け取らない。既存 engine は十分だが、loop の引数追加・転送が必要。
3. **登録簿が不足。** `test_campaign.py:5346,5432` の二つの呼出し在庫と総数 pin が抜けている。
4. **新 module なら manual-build 在庫も必ず変更、という一般化は誤り。** `test_p3_build_authority_cli.py:1217` は実際に `--build` を含む file を検査する。今回必要なのは machine caller 登録。
5. **runner のアンカーが片側だけ。** `938–1012` に加え、通常の `measure_point` の `1111–1232` も対象。
6. **commit 前焦点走の注意は pipeline だけではない。** loop と runner も loader binding 対象。
7. **同居関係文書を常設登録簿として扱わない。** `docs/test-environment-coincidence-ledger.md:326` は過去 wave の先送り記録。
8. **五 probe の成功だけで「唯一の blocker が外れる」と断言するのは広い。** 成功によって示せるのは五条件の実装経路。実環境の投入条件、cohort 同一性、時間上限等は実投入時にも満たす必要がある。

なお、「envelope 四 key」は payload を除く外側の四座標という意味なら正しい。JSON 行全体の exact key 集合は `payload` を含む五 key であり、変更しない。

## 総括

新規 module に本走の consumer・driver・loader・report を集約する。  
共通変更は legacy correctness の転送と、本走 opt-in の整数 counter 保存に限定する。  
payload 拡張は conditional `reps` 一個とし、extra の exact 契約は保つ。  
五本の正しさ記録は既存逐次反復と実 verifier/receipt 発行経路で確かめる。  
親の probe 入力は補強が必要だが、保存済み stdout と trace fixture により新規計算ノード計測は不要。  
既存三系列、事前登録 bytes、格子上端の pin は変更しない。