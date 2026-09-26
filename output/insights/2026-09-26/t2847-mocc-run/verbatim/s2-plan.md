## 判定 (P1〜P5)

| 裁定 | 判定 | 根拠と修正案 |
|---|---|---|
| P1：既存 4 patch は変えず、S を「未発生」と数える | **部分的** | cold の閾値 21 は温度上限 20 を超えるため、V16 の hot 分岐に届かないことは source から示せる（`external/ccbench/cc/mocc/include/tuple.hh:12`、`external/ccbench/cc/mocc/transaction.cc:460`）。一方、発火診断のない他の S、特に default の V16 は「未発生」と実測認定できない。`発火未確認の S` と記録し、五分類への算入を保留する。既存 4 本への診断専用 overlay は patch 4 本、登録・build・比較の追加が要り、依頼の「本題の実装だけ」という範囲を超える。今回追加しない。 |
| P2：V25 の停止 run に部分 trace の verdict を付けない | **部分的** | 停止を verdict に数えない点は正しい（設計書 `output/insights/2026-09-22/t2847-verifier-detection-design/README.md:194`）。ただし `subprocess.run(..., timeout=120)` は強制終了し、trace は worker の `thread_local std::ofstream` の destructor で flush される設計なので、停止時の file は不完全または空になりうる（`orchestrator/campaign/s3_mocc_mutation_proof.py:205-221`、`external/ccbench/include/trace.hh:49-62`）。部分 trace の verify は**参考診断の別欄**にだけ保存し、本 run の verdict にしない。 |
| P3：新規 2 本の cell | **部分的** | V34 の W 6 cell は妥当。V25 の hot t1 を「相互待ちはない」と呼ぶには、同一 tuple の自己再取得を設計で除く必要がある。下記の V25 gate を前提に採用する（`external/ccbench/cc/mocc/transaction.cc:739-764,862-889`）。 |
| P4：job 内 stock 対照、結果を見た workload 変更なし | **real** | 前回の stock 前提と事前登録の規則に合う（`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-mutation-run/s4-ruling.md:20,78-90`）。各 job で使う workload・regime・thread の stock を同じ checkout と toolchain で走らせる。 |
| P5：既存 driver と同じ証人なし verify | **部分的** | 比較可能性を保つ経路として採用できる。実際の argv に commit 証人はない（`orchestrator/campaign/s3_mocc_mutation_proof.py:224-226`）。ただし末尾の commit trace 欠落は証人なしでは certified になりうる（設計書 `output/insights/2026-09-22/t2847-verifier-detection-design/README.md:50-52`）。したがって S は「既存 mocc verifier の証人なし判定」と明記し、commit 完全性まで主張しない。verifier の受理条件は変えない。 |

P2 の停止時診断には契約上の未解決点がある。前回 R2 は「通常終了時の destructor から 1 行」を指定する（`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-mutation-run/s4-ruling.md:35-40`）。SIGTERM を先に送るだけでは destructor の実行は保証されない。最小の確実な案は、V25 patch に SIGTERM 時の **1 回限りの** `T2847_FIRED` 出力を追加し、lock-free atomic の relaxed load と `write(2)` のみを signal handler で使い、その後 `_Exit` すること。これは R2 の「destructor から出力」を停止時だけ拡張するため、段 4 で明示裁定が必要。裁定されなければ停止時の発火は「診断欠落」と記録し、未発生・盲点のどちらにも数えない。

## patch 設計 (V25・V34)

**V25**：`patches/broken-mocc-skip-canonical-restore.patch`、`IZANAGI_BREAK_MOCC_SKIP_CANONICAL_RESTORE`。`external/ccbench/cc/mocc/transaction.cc:835-859` の解放と CLL_ suffix 除去だけを変異枝で飛ばす。直後の正準順 lock loop と対象 tuple の lock（同 `:861-900`）、X emitter（同 `:1183-1257`）、validation（同 `:987-1075`）は維持する。未定義時は元の行をそのまま選び、pin C と一致させる。

単純に `vioctr != 0` で常に飛ばす案は採用できない。既存 CLL_ の tuple は `lock()` 冒頭で探索され、同じ mode なら早期 return するが、read→write upgrade では return しない（同 `:739-760`）。また復元後の RLL_ loop は `key > threshold` の要素を再取得する（同 `:862-879`）。復元を飛ばすと既存 CLL_ の要素を再取得して自己停止し、追加した CLL_ 重複要素を `unlockCLL()` が二重解放しうる（同 `:1119-1138`）。**変異枝は** `vioctr > 0`、`!upgrade`、かつ「再取得する RLL_ key と保持中 CLL_ suffix に共通 tuple がない」場合だけ選ぶ。それ以外は元の復元を実行する。この限定下では対象 tuple は CLL_ に既存保持されず、逆順の lock を保持したまま別の lock を追加する、設計書の機構に一致する。gate が何回成立するかは実走で確認する。

**V34**：`patches/control-mocc-temperature-predicate.patch`、`IZANAGI_BREAK_MOCC_TEMPERATURE_PREDICATE`。`external/ccbench/cc/mocc/transaction.cc:297,460,567,971` の各 `temp >= FLAGS_temp_threshold` を `!(temp < FLAGS_temp_threshold)` にする。`971` は `(!(temp < FLAGS_temp_threshold) || (*itr).failed_verification_)` として OR の優先関係を保つ。trace include の `#if TRACE`（同 `:13-16`）と emitter は編集しない。TRACE=0 の同一性検査は「計装 patch 前後」の比較ではなく、この patch の無効枝と pin C の source・前処理結果の照合として扱う。macro 名は前回の対照 patch でも `IZANAGI_BREAK_*` を使った先例に合わせる（`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-mutation-run/launch_mutation_run.py:41-43`）。

両 patch の診断は前回 R2 に合わせ、macro 有効時のみ file static の relaxed atomic `reached / changed / committed`、`begin()` で transaction-local flag を落とし（`external/ccbench/cc/mocc/transaction.cc:190-199`）、`commit()` の成功直前で flag を見て committed を加算する（同 `:1279-1285`）。通常終了時に destructor から stderr へ各 slug 1 行を出す。V25 の reached は限定 gate に到達した回数、changed は実際に保持したまま復元を省いた lock が 1 個以上の回数。V34 は等価変形なので挙動差を示す changed は **0 と定義**し、各 site の評価を reached、境界 `temp == threshold` の評価を `boundary` extra として数える。対照の成立条件は reached と非空 commit、および全 cell の S・X/P=0 とし、changed≥1 を要求しない。この例外を事前登録する。

## 登録

`orchestrator/campaign/condition_meaning_gate.py:217-232` の mocc と同形の `DefineSpec(ROUTE_CMAKE_CXX_FLAGS, _MOCC_OWNER, "ycsb_mocc.exe", "patches/<name>.patch")` を 2 件加える。`_CONDITIONAL_BRANCH_WITNESSES` に exact な `#if <macro>` と `cc/mocc/transaction.cc` を追加する（同 `:354-365`）。site 数は patch 完成後、**実際の `#if` 行数**を数えて `_CONDITIONAL_BRANCH_SITE_COUNTS` に固定する（同 `:449-469`）。診断用の追加 `#if` も数えるため、4 述語というだけで V34 の登録 site 数を 4 と決めない。

対応表は `orchestrator/tests/test_condition_meaning_gate.py:86-148,1148-1172,3448-3479`、裸 macro の patch 許容表は `orchestrator/tests/test_p3_s4_loop.py:8463-8495`、patch 由来 define の在庫照合は `orchestrator/tests/test_ccbench_spawn_sites.py:652-733,2912-2925`、既定値 `0` は `orchestrator/campaign/screening_driver.py:82-85` に追加する。spawn-sites の在庫照合は patch を glob するため、通常は手書き define 表の追加ではなく、**新 patch が正しく発見され、登録簿と一致すること**を確認する。`orchestrator/tests/test_screening_driver.py` の既定値照合も実際の赤 node に合わせて更新する。既存の gate の受理述語・touch set・protocol 判定は緩めない。mocc の `_MOCC_OWNER` と `ycsb_mocc.exe` は既存 4 patch の先例に合う。

[T-2849] は `orchestrator/tests/test_ccbench_spawn_sites.py` を変更中と brief に記録されている（`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-mocc-run/brief.md:13`）。本 wave が同 file の在庫照合周辺 `:2912-2925` を編集する場合は、取り込み時に両 branch の差分を照合する。

## 起動器

repo 外の `launch_mocc_run.py` が `s3_mocc_mutation_proof` の `_build_variant`、`_variant_run`、`_verify`、`_summary`、既存の checks の述語を import する（`orchestrator/campaign/s3_mocc_mutation_proof.py:166-192,224-263,320-338,341-415`）。`main()` は旧 pin と計装 patch を固定しているので呼ばず、同等の手順を起動器で組む（同 `:501-575`）。

差し替え・供給する値は以下のとおり。

| 項目 | 設計と根拠 |
|---|---|
| pin | 起動器の局所 `PIN = 68106660686232781bca3be792a750d3e19d7a8a`。driver の旧 `PIN` は `legacy.PIN`（`s3_mocc_mutation_proof.py:28`、`s3_mocc_lock_coverage.py:42`）。各 build を `checkout(PIN)`、`assert_pinned_clean` で束縛（`s3_mocc_mutation_proof.py:551-553`）。 |
| 計装 patch | `INSTRUMENTATION_PATCH` の適用行 `s3_mocc_mutation_proof.py:554` を実行しない。pin C に X/P があるため（`external/ccbench/cc/mocc/transaction.cc:991-1013,1183-1257`）。 |
| patch 適用 | `_apply_owned_patch()` をそのまま使用し、`patch_files == ["cc/mocc/transaction.cc"]` と `apply_patch` の厳密適用を維持する（`s3_mocc_lock_coverage.py:430-436`）。 |
| condition gate | `_build_variant()` の `_require_condition_gate()` と `-DCMAKE_CXX_FLAGS=-D<macro>=1` をそのまま使う（`s3_mocc_mutation_proof.py:166-188`）。 |
| verifier | `_variant_run()`→`_verify()` の既存 argv・rc・verdict を変更しない（同 `:224-245,320-338`）。停止 run の参考 verify だけ別欄へ追加。 |
| ENV_TAG・出力 | `ENV_TAG="pegasus"` は既存値（`s3_mocc_mutation_proof.py:48`）。JSON・raw subprocess・部分 trace は job dir に置き、tracked calibration JSON の既定先（同 `:511`）を使わない。 |
| 依存物・compiler | `s3_mocc_lock_coverage.py:120-257` の policy、toolchain、依存物準備を流用。前回起動器の compiler 供給・依存物 CMake 設定（`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-mutation-run/launch_mutation_run.py:151-174,557-595`）と subprocess の受動保存・stderr 発火行抽出（同 `:96-142,177-189`）を mocc executable 名へ適応する。 |

既存 `compute_checks()` の **32 check**（`s3_mocc_mutation_proof.py:418-483`）を一括で `all_pass` に使わない。stock の静穏性、lockskip・P・early・H の理由別 check、matrix 完走、toolchain、patch touch set は pin C でも同じ意味で再計算できる。ただし patch touch set の集合式 `:477-480` は旧計装 patch を必須にするため、**同じ厳しさの pin C 用集合式**へ置き換える。`trace0_nm_*` と `trace0_strings_*` は計装 patch 前後比較という旧前提を持ち、`trace0_logical_rows_identical` も同前提の比較（同 `:462-470,565-575`）なので、旧 check 名のまま合格にしない。pin C の TRACE=0 確認は別記録にする。`hot_path_evidence` の negative-control check（同 `:460-461`）は V16 の到達を直接証明しない点も明記する。

## workload と期待表

既存 matrix は `stock W / stock U / L W / P W / E W / H U` × hot 0・cold 21・default 10 × thread 1・4 の **36 cell**、W・U・CLK・STOCK_G は `s3_mocc_mutation_proof.py:30-47,72-88` と `s3_mocc_lock_coverage.py:47-61` のまま。V25 は W の hot t4・hot t1・cold t4・default t4、V34 は W の 6 cell。これは事前登録で固定し、結果を見て変更しない。

| 行・cell | 事前期待と層 |
|---|---|
| stock W/U：各 6 cell | S、X/P/他 integrity 0、非空。各 job で使用 cell を対照実走する。 |
| V13 L：各 regime t1 | I、X。t4 は N（巡回）を主期待、X と version dup の併発を記録。旧 pin の 3 regime 実測は設計書 `:244`、pin C の default t1/t4 先行記録は brief `:12`。 |
| V14 P：全 6 cell | I、P の `size-changed`、巡回 0。旧 pin の全 6 cell は設計書 `:246`、pin C default t1 は brief `:12`。 |
| V15 E：各 regime t1 | I、保持破れの X。t4 は N（巡回）を主期待、X と version dup 併発を記録。旧 pin は設計書 `:245`、pin C default t1 は brief `:12`。 |
| V16 H：hot t1/t4 | t1 は I・X、t4 は I・X と version dup を主期待。cold t1/t4 は S・X/P=0、source 上 hot 分岐未到達。default t1/t4 は旧記録上 S・X/P=0だが発火未確認。旧 pin は設計書 `:247`。 |
| V25：hot t4 | 停止を主期待、verdict なし。完走すれば非空 prefix は S・X/P=0 を条件付き期待。hot t1 は自己再取得を除いた対照として完走 S を期待。cold/default t4 は発火が温度・schedule 依存で、S または停止を観測する。 |
| V34：W の全 6 cell | 非空 S、X/P/他 integrity 0。`reached>0`、境界値評価は `boundary` で記録。 |

分類は、期待した counter の N/I を「期待した層で検出」、他の counter も動けば「別の層で検出」とする。S は、V25 なら changed と committed が正、V34 なら reached と非空 commit があり、期待した無異常条件を満たす場合だけ「盲点として certified／正しさを保つ対照」とする。発火診断のない既存 4 本の S は、source で未到達が証明できる V16 cold 以外、「発火未確認」と明記する。stock が N/I、空、または integrity 不良なら同 cell の帰属は保留する。対照 V34 の N/I は「誤検出」候補として原 trace と patch の等価性を再監査する。停止と部分 trace の参考 verdict は五分類に混ぜない。

## 投入と見積り

4 job を事前登録する。J1＝stock W＋V13/V14（3 build）、J2＝stock W/U＋V15/V16（3 build）、J3＝stock W＋V25（2 build）、J4＝stock W＋V34（2 build）。計 **10 build**。J1/J2 が既存 36 cell を分担し、job 内 stock は重複しても各使用 cell を揃える。各 job に wave tip の別 detached checkout、submodule 初期化、lock を用意し、`tools/pegasus/dispatch_compute.py --task generic` で投入する（brief `:18,23`）。walltime は J1/J2/J4 を各 15 分、J3 を V25 の 4 cell × 120 秒を含め **20 分**で申請する。

前回の実測単価は 4～5 build の job が 139～194 秒（`output/insights/2026-09-23/t2847-mutation-run/README.md:58-68`）。今回の実走は通常 4 job ×約 200～300 秒＝800～1,200 秒、V25 の停止 1～4 本で追加最大 480 秒、と見積もる。焦点走 2 回約 0.1 node 時間、実装変異 matrix 約 0.4、受入 2 回約 0.5 を加え、**合計約 1.2～1.6 node 時間**。停止が 4 本とも上限まで続き、受入を再試行する場合は 2 node 時間に近づくため、投入前に段 4 で再見積りする。これは計画値であり実測値ではない。

## 段 5 分割と変異候補

- **patch author**：新規 patch 2 本のみを所有。V25 の自己再取得防止 gate、V34 の 4 述語、診断契約を確定する。
- **登録 author**：`condition_meaning_gate.py`、`test_condition_meaning_gate.py`、`test_p3_s4_loop.py`、`test_ccbench_spawn_sites.py`、`screening_driver.py` と必要な既存表 test を所有。macro と site 数確定後に作業する。
- **起動器 author**：repo 外 job dir の `launch_mocc_run.py` のみを所有。`patches/README.md` と insight は親が編集し、所有 file を重ねない。

実装面の変異テスト候補は次の 5 件。前回の M1～M4 の実測では登録欠落・名前不一致・site 数虚偽が殺された（`output/insights/2026-09-23/t2847-mutation-run/README.md:142-158`）。

1. 新 macro 1 件を `_DEFINE_SPECS` から削除。
2. `_CONDITIONAL_BRANCH_WITNESSES` の 1 件を削除。
3. patch 内の `#if` macro 名を登録名と 1 文字ずらす。
4. 登録 site 数を実数より 1 増やす。
5. `screening_driver.py` の新 macro の既定値を `0` 以外にする。

## 未確認点

- V25 の限定 gate が指定 W cell で十分発火するか、停止が自己待ちではなく異なる worker 間の待ちかは静的検査だけでは確定できない。raw の reached/changed、stack、lock 所有を実走で照合する。
- 停止時の `T2847_FIRED` を R2 に追加するかは段 4 裁定が必要。SIGTERM だけでは診断も trace flush も保証しない。
- V34 の `boundary>0` は温度分布次第。`boundary=0` でも述語の等価性は成立するが、「境界を実測した」とは書けない。
- pin C 上の既存 4 本の hot/cold 全 cell と V25/V34 は未実走。旧 pin の数値を pin C の結果として転記しない。

## 総括

pin C の既存計装を使い、旧計装 patch の適用だけを外す。最大の修正点は、**V25 の単純な復元省略が自己再取得と二重解放を招くこと**、および**発火診断のない S を一律に「未発生」と認定できないこと**である。停止 run と証人なし S の限界を結果表に明記すれば、既存 gate と verifier を緩めずに 6 行を実測できる計画になる。