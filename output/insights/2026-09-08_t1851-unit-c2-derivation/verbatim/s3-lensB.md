## pin 閉包の残り (file:line)

段 2 plan は、親から伏せられた 2 点を独立に発見している。

- `capture_measure_point()` と `measure_point()` の両面を明記している。
- `s8b_floor_stats.py` の第 2 exact gate も明記している。

ただし、AST と全 callsite の引き直しで次の残りが出た。

- `_derive_rep_integrity()` を 3 値から 4 値へ変える plan が、`orchestrator/campaign/s8b_terminal_evidence.py:1030` の 3 値 unpack を落としている。直接 consumer は `orchestrator/tests/test_s8b_terminal_evidence.py:468` と `:479`。plan が挙げた `:641`、`:900`、`:8377` だけでは閉じない。
- 6-key literal の全 AST 抽出結果は次のとおり。plan の所有 file 集合にはすべて入っているが、親 brief の「runner 生成 2 箇所」は初期化 literal 2 箇所を数えていない。

  - producer/gate: `runner.py:940,990,1106,1203`、`s8b_floor_campaign.py:1901,1947`、`s8b_floor_stats.py:64,487`
  - test/fixture: `s8b_v2_freeze_fixture.py:155`、`test_s8b_attempt_registry.py:347`、`test_s8b_floor_attempt_launcher.py:238,864,868,872,944,1410`、`test_s8b_floor_campaign.py:902`、`test_s8b_floor_stats.py:269`、`test_s8b_ratified_freeze.py:530`、`test_s8b_ratified_verify.py:377`、`test_s8b_terminal_evidence.py:108`

独立検算で残らなかったものも明記する。

- `missing_perf_events` の live Python file は親・plan 記載どおり 12 本。`output/insights/` に旧 schema の歴史記録もあるが、live consumer ではなく改変対象外。
- 対象 7 file の現 SHA-256を tracked repository 全体で検索し、whole-file hash hit は 0 件。
- canonical bytes の静的 literal に 6 key を含むものは 0 件。
- `test_official_perf_closure.py:44,533,905` は既登録 file の編集だけでは変化しない。
- `test_t671_source_binding.py:67,267-269` も `runner.py` が既登録で、新 path を足さない限り変化しない。

## consumer 取り残し

実害のある取り残しは `_derive_rep_integrity()` の返値 consumer である。

- `s8b_terminal_evidence.py:1030` は plan に無い。4 値返却へ変更するとそのままでは `ValueError` になる。
- `test_s8b_terminal_evidence.py:468,479` も返値形の追随または helper の外部返値維持が必要。

親・plan が列挙していない subset consumer もある。

- `orchestrator/campaign/pipeline.py:2794-2866` は `measure_point()` の observation から件数と `throughput` を読む。
- 親が挙げた `backoff_counterfactual_analysis.py:256-257,322` には `rep_observations`、`missing_perf_events`、`counter_status`、`perf_raw` の参照がなく、runner observation consumer ではない。
- `backoff_extended_sweep.py:547-609` と `floor_pair_driver.py:1794-1835` は余分な第 7 key を許す subset consumer なのでコード変更は不要。

14-file baseline 外の consumer test は少なくとも次である。

- `test_calibrator_deferred_output.py` — 両 runner surface の実出力を直接読む。
- `test_backoff_extended_sweep.py` — production runner と `_T2266RepCapture` を実際につなぐ。
- `test_s8b_ratified_freeze.py`
- `test_s8b_ratified_verify.py`
- 広い subset 回帰として `test_campaign.py` と `test_holdout_observation.py`

特に ratified 2 file は plan の編集対象なのに、親の 14-file baseline に含まれていない。

## 射程の正直さ — 契約 9 節を満たすか

満たさない。

plan が実際に証明できるのは、次の 1 文だけである。

> fake build と fake subprocess を使う pilot test が、production `measure_point()` から campaign journal まで `execution_failure` の True/False を搬送できることを示す。

`test_rep_integrity_positive_control_default_measure_point` は `test_s8b_floor_campaign.py:9253-9279` で subprocess を fake にし、build、probe、時刻も fake である。実 CCBench 値域を測らず、`capture_measure_point()`、`launch_floor_attempt()`、試行台帳 terminal のいずれも通らない。

契約 9 節は「C1b gate の入力は fake 値域だけであり、実値域は C2 が供給する」と書く。production caller 0 件のまま producer を同形化するだけでは、値を gate へ供給していない。したがって P1 の「配線は別単位」は現契約とは両立しない。採るなら契約側を「producer schema の準備」に弱める別裁定が必要になる。

## 変異の帰属が成立しない件

- 「既存 positive control が M1-M6 の複合陽性対照」は偽である。

  - M1 は `capture_measure_point()` 変異なので、`measure_point()` を呼ぶ同 test へ到達しない。
  - M3 は実行例外 note と structured flag が同じ本数になるため、notes regex へ戻しても差が出ない。
  - M5 は carrier が存在する同 test では padding 分岐へ到達しない。
  - M6 は実 runner の例外 rep が `returncode=None`、counter incomplete でもあるため、flag 条件だけ外しても既存条件が integrity failure にする。
  - M4 は execution exception caseでは両 count がとも 1 で差がなく、nonzero rc caseだけが区別できる。

- M5 は `True`、`None`、key 欠落という異なる 3 変異を 1 IDへ束ねている。赤理由も expected node 集合も同じとは限らない。
- M7 も「exact 集合を 6 keyへ戻す」と「key 不一致を failure countへ足さない」を束ねている。前者は正常な全 7-key fixtureを広く赤にする。後者は schema error が既に artifact を拒否するため受理集合を変えず、diagnostic sensitivity にすぎない。
- M8 の根拠にある `type(value) is bool` と `isinstance(value, bool)` は、Pythonでは受理集合が同じである。後者へ置換する変異なら等価変異で、`0`、`1`、`None` は受理されない。
- M10 は「count 無視」と「schema error 無視」を分離すべきである。また count 不一致は、private qualified throughput 等値と既存の `len(throughputs) + nonfinite_count + exec_failures == reps_expected` gateでも赤になる。明示 equalityだけの正例になっていない。
- M6、M7、M10 は別 gateによる拒否を除いた単一理由性が未成立。現状の「すべて通常 pytest 経路で kill」は実測前の一般化である。

M1、M2、M3、M9 は個別 test設計としては成立可能だが、期待赤 node の完全集合を probe で確定するまでは帰属済みとは書けない。

## 実装子分割の破れ

file所有の重複はなく、1→2→3 の直列順も妥当である。並列競合はない。

破れているのは所有権ではなく子 2 の内部閉包である。

- 子 2 は `s8b_terminal_evidence.py` を所有するが、作業記述が `:637-645` と `:1175-1205` だけで、同 file の `_derive_rep_integrity()` consumer `:1030` を落としている。
- 同じ子が所有する `test_s8b_terminal_evidence.py:468,479` も作業項目へ明記すべきである。
- `test_calibrator_deferred_output.py` に第 7 key の直接 assertionを足すなら子 1へ追加する。別子に渡す必要はない。
- ratified 2 testは子 3所有だが、回帰走対象から落ちている。

## 成果物影響を言えない must-fix

成果物影響を言える core変更は次である。

- runner/campaign算出を放置すると、例外本数が notesに依存し、session受理、除外理由、cell統計、選択値が変わる。
- statsの top-level count等値を放置すると、偽の `exec_failures` を持つ resultの受理集合が広がる。
- resume照合を放置すると、改変済み journalの countを再利用し、再開後の resultと参照系列が変わる。
- terminal再導出を放置すると、試行台帳 proof chainが rep事実でなく campaign自己申告を束縛する。

一方、次は DW-G05 上の must-fixにはできず、nitまたは diagnostic pinへ落とすべきである。

- schema errorを既に返す key不一致を、さらに integrity failure countへ加えること。
- `type(value) is bool` を `isinstance(value, bool)` より強いとすること。
- fixture/test literal追随そのもの。productionの certified値、受理集合、台帳参照は変えず、test正例を新 schemaへ保守する作業である。
- `_source_throughputs()` の返値追随。現 repoの callerは test 2件だけで、production artifactへの経路はない。
- M10の明示 count equalityを独立の受理面強化と数えること。現構成では既存のthroughput等値と件数不変量にmaskされる。

## 親 brief の誤り

brief 4節の表には次の誤りがある。

- `s8b_floor_attempt_launcher.py:158-160` は `OpenedFloorAttempt` の fieldであり、`_PRODUCTION_DEPENDENCIES` ではない。実体は `:210-213`。
- launcherから captureを呼ぶ箇所は `:435` ではなく `:730`。`:435` は `_failure_evidence()` の引数行。
- statsの定数は `:64-67`、exact比較は `:487`。briefの `:63` は `PERF_EVENTS`、`:486` は `continue`。
- runnerの最終 observation代入は `:990` と `:1203` だが、同じ6-key objectの初期化が `:940` と `:1106` にもある。「生成は2箇所」という全称は不正確。
- `backoff_counterfactual_analysis.py` は runner rep observation consumerではない。一方、実 consumer `pipeline.py:2794-2866` が表にない。
- `_launch_floor_attempt` の呼出しは `:1203` と `:1248`。表の `:940/1189/1218` は内部関数とwrapperの定義位置で、呼出し位置の証拠ではない。

正しかった部分もある。

- production caller 0件、launcherの実import元1 test、campaignからattempt registry参照0件。
- `missing_perf_events` のlive file 12本。
- whole-file SHA pin 0件、`FROZEN_MANIFEST`対象外。
- brief 5節の「fixtureの6 keyはhardcode digestへ伝播しない」は正しい。`_synthetic_floor_result()` を使うのはholdout freezeだけで、result、manifest、journal、admission digestを動的再計算する。既存定数 `_V2_WRITER_SHA256_LITERAL`、`APPROVED_SCHEDULE_SHA256`、`SUBSET_SCHEDULE_SHA256`、`PIN_GATE_SCHEDULE_SHA256`、`PIN_GATE_SPEC_SHA256`、`_T080_RECEIPT_RAW_SHA256` はrep observation由来ではない。

P1-P4ではP1が誤り。P2、P3、P4は閉包上妥当である。P4は、将来launcherが使うcapture面を6-keyのまま残すとterminal evidenceが受理できないため、production caller 0件でも両面追随が必要である。

なお段2 planの「親が `s8b_floor_campaign.py:1039-1045` をcomplete述語とした」という異議は、現在の攻撃対象briefには当たらない。現在のbriefは既に `:1947-1950` へ訂正済みである。

## 過去の型の再発

- F28、F820、F887: 変異の前後・内側に別拒否があり、単一理由性が成立しない。M6、M7、M10で再発。
- F780: 既存拒否と受理集合が同じ冗長gateを強化に数える。M7のfailure count追加とM10のcount equalityが同型。
- F39、F345、F474、F864: 識別子・path・現hashだけではpin閉包が閉じない。今回もASTと全callsite追跡で `s8b_terminal_evidence.py:1030` が出た。
- F255、F894: consumer取り残し。返値arity consumerとbaseline外testが該当。
- F29、F774: 測った経路を超えて全称を主張する。fake subprocessのpilot testを「実 campaign経路の実値域」と呼ぶ点が同型。
- F89: 同じ設定・schemaを読む複数経路の受理集合の食い違い。capture面とmeasure面を両方直すP4はこの再発を避けている。

## blocker と nit の仕分け

Blocker:

- P1のままでは契約9節の「実値域をC2が供給」を満たさない。
- positive controlをM1-M6の複合陽性対照とする主張は成立しない。
- M5、M7、M10が複数の異なる変異を1 IDへ束ね、M6、M7、M10の単一理由性も成立していない。このままではmutation receiptの帰属が虚偽になる。
- 「通常経路で全変異をkillできる」という記述は撤回し、semantic kill、diagnostic sensitivity、maskされた変異へ分ける必要がある。

Nitまたは回帰保守:

- `_derive_rep_integrity()` の `s8b_terminal_evidence.py:1030` とtest 2件の追随。
- baseline外consumer testの追加。
- 親briefの行番号訂正と `pipeline.py` の追記。
- fixture/test literalの7-key追随。
- exact bool検査を `type(...) is bool` と書く様式差。
- official perf inventory、T671 inventory、hardcode digestは変更不要。

## 総括

段2 planは、伏せられた「runnerが2公開面」「exact集合gateが2本」を独立に発見しており、その点では親の初版漏れを克服している。しかし、契約9節をfake subprocessのpilot testへ縮めたP1、`_derive_rep_integrity()` consumerの取り残し、単一理由性が壊れたmutation matrixのため、現状のplanは実装投入可能ではない。

静的読解、`rg`、tracked repository検索、AST走査だけを行った。ファイル作成・変更、pytest実行、テスト緑の主張はしていない。