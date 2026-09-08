# [T-2228] screening 段の条件関門へ準備済み FetchContent base を供給した — 実装まで。緑になったとは名乗らない

日付: 2026-09-08 / wave: `dev-wave-t2228-screening-gate` / branch `worktree-dev-wave-t2228-screening-gate`
基点 main: `087132811`、着手後に `240ee6360` を取り込み。authority: none / default_effect: no-state-change。

## 要点

1. **入れたのは 1 箇所だけである。** `orchestrator/campaign/screening_driver.py` の
   `_run_condition_gate_for_genome` が `condition_meaning_gate.capture_define_inputs` へ渡す
   configure 引数に、準備済み FetchContent base を 1 本足した。形は D1666 が
   `backoff_sweep` の driver 段へ入れたものと同型である。
2. **本 wave は「screening 関門が緑になった」とは名乗らない。** 名乗れるのは
   「driver 段と同型の供給を screening 関門へ入れた」ことだけである。現行の正規入口から
   実 CCBench で関門を通す生死確認は行っていない (§4)。
3. **ユーザー裁定 D1733 の射程は守った。** `backoff_repro` と `s1_direct_comparison` への供給、
   pin の整合、freeze の再生成には触れていない。両者に同型の欠陥があることは複数のレンズが
   確認したが、いずれも must-fix にせず裁定パッケージ候補へ分けた (§5)。
4. **判定式は 1 行も変えていないが、受理集合は変わる。** 変わるのは
   「準備済み base の未供給だけを理由に前段の preprocess で赤になっていた呼び出し」が
   判定へ進む分である。これを**制御された拡張**として記録する。「緩めていない」とは書かない。
5. **段 2 プランの正例は恒真だった。**供給が届いていない実装でも緑になる形だったので、
   供給が無ければ赤・あれば緑になる fixture を新設した (§3)。

## 実行 identity

- 実装 commit: `38eae5fdb`
- 焦点走 1 回目 (fix 前): `python3 tools/run_tests.py orchestrator/tests/test_screening_driver.py -q`、
  計算ノードへ dispatch、request `982476.nqsv`、queue `gen_S@nqsv`、Elapse 15S、
  **1 failed / 48 passed in 9.75s** (rc=1)
- 焦点走 2 回目 (fix 後、12 file): **776 passed / 3 skipped in 56.98s** (rc=0)
- 変異 matrix: baseline PASSED・KILLED 15・SURVIVED 0・MISMATCH 0・期待 node 完全一致 15/15
  (spec `mutation-final-spec.json`、結果 `mutation-final-out.json`)
- 子: codex 7 本 (plan 1・consult 2・author 1・review 2・fix 1)。全て `launcher_rc=0`、
  model は全段 `gpt-5.6-sol`、reasoning は全段 `xhigh`。

## 1. 何を入れたか

`_run_condition_gate_for_genome` に keyword-only の `expected_toolchain_manifest` (既定 `None`) を足し、
非 `None` のときだけ次を行う。

1. request 空判定と build-route 検査の**後**に一時 directory を作り canonical 化する。
2. `buildcache.prepare_masstree_fetchcontent` を 1 度呼ぶ
   (`ccbench_dir` は関門へ渡す `source_root` と同じ canonical path、`configure_timeout_s=900`、
   `target_timeout_s=900`、`site=None` を明示、`dependency_prefix` と 3 つの source_dir は渡さない)。
3. `-DFETCHCONTENT_BASE_DIR=<canonical base>` を configure 引数の**末尾へ 1 本だけ**足す。
4. 一時 base は supply 腕・meaning 腕・family admission の完了後に閉じる。
   stock 経路では stock checkout の内側で作られ、内側で閉じる。
5. prepare の例外は捕捉しない。`evaluate_candidate` の candidate-abort 捕捉より前にあるので、
   偽の関門赤にも WAL の candidate abort にもならず、評価全体を停止する。

`_require_condition_gate_before_evaluation` は manifest を stock / 非 stock の両分岐へ転送し、
`evaluate_candidate` は既に受けている manifest を渡す。production の変更はこの 3 関数だけである。

**変えていないもの:** `_CONDITION_DEFAULTS`、`_condition_requests_for_genome`、
`_require_requests_match_genome_build_arguments`、`_condition_gate_base_configure_args`、
supply 腕・meaning 腕の評価、`require_condition_gate_family` の admission 条件、例外型と文言。
`condition_meaning_gate.py` と `buildcache.py` も無編集である。

## 2. 発火条件は権限ではなく経路の代理である

関門は共有関数で、`backoff_sweep` 以外に `s6_sort_sweep` と `s8a_trigger_sweep` からも到達する。
manifest を渡すのは `backoff_sweep` の 2 呼び出しだけなので、他 2 経路の挙動は 1 bit も変わらない。

**`expected_toolchain_manifest is not None` は供給の権限を表す述語ではない。**
現行 call graph 上で backoff screening 経路を選ぶ代理である。将来 `s6_sort_sweep` か
`s8a_trigger_sweep` が manifest を渡すようになれば、同じ分岐が自動で発火する。
`None` 経路の非発火 test は helper を直接呼ぶので、その変更を検出しない。
**したがって「この test があるので将来の水平展開はできない」とは書かない。**

段 3 の 2 レンズは独立に「この述語は候補集合に含意された恒真ではない」と裏取りしたが、
レンズ B は同時に「対象である backoff 経路の内側では恒真であり、経路タグとして働いている」と
指摘した。この二面性を記録しないと readiness 条件だと誤読される。

## 3. 正例が恒真だった件と、その直し方

段 2 プランの正例は、prepare を stub にしたうえで既存 fixture
`orchestrator/tests/fixtures/condition_meaning_gate/supplied` を使うものだった。
この fixture は `FETCHCONTENT_BASE_DIR` を無害に参照するだけで、header にも target にも使わない。
**したがって供給が実際には何も届けていない実装でも緑になる。**段 3 の両レンズが独立に指摘した。

新設した `condition_meaning_gate/prepared-base-required` は次の形である。

- owner TU が `<izanagi_prepared_dependency.hh>` を include する。この header は fixture 内に存在せず、
  一時 FetchContent base の中にだけ生成される。
- CMakeLists が `${FETCHCONTENT_BASE_DIR}/izanagi-screening-dependency-src/include` だけを
  include path に足す。
- 正例の prepare 代役は、渡された `fetchcontent_base_dir` の中へその header を**実際に置く**。
  つまり prepare の返り値ではなく**副作用**が正例を成立させる。
- 実 supply evaluator と CMake configure / preprocess は stub 化せず、
  requested / control の両 configure argv と依存閉包が同じ header を参照することまで検査する。
- 同じ fixture で prepare 代役を「何も置かない」形にすると `preprocess-failed` になる負例を対で置いた。

変異 M5a (prepare 削除) と M13 (準備した base を capture へ渡さない) がこの正例を殺すことが、
供給が load-bearing である実測である。

## 4. 生死確認を行っていないこと (最も重要な限界)

段 3 の 2 レンズと段 6 のレンズ B が、それぞれ独立に
「実装後に real backoff screening の関門を計算ノードで通す生死確認が要る」と must-fix にした。
**所見は real である。本 wave では実装していない。**

- 依頼が「本題の実装だけ」「仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」と
  明示している。
- D1666 も同じ形を採った — driver 段の供給を実装した wave と、関門の生死を実測した wave
  (T-2228 の一次資料を産んだ wave) は別である。
- したがって本 wave は **「screening 関門が緑になった」とは名乗らない。**

**再訪条件:** 現行の正規入口 (CLI) から `screening_fixed_us=2` の最小 screening を計算ノードで
走らせ、baseline の stock 腕まで緑 record を得ること。

段 3 レンズ A はさらに、一次資料の実測自体が
`backoff_sweep.main` ではなく内部の `run_workload` を直接呼んでおり、
既存 A-5 job body は `--screening` を付けない、と指摘した。
同レンズは同時に「CLI `main` は引数をそのまま `run_workload` へ渡す薄い入口であり、
evidence の traceback は `run_workload → _run_screened_workload → measure_baseline →
evaluate_candidate → screening gate` を示すので、コード上の到達性は実証されている」と反証している。
**残っているのは CLI 入口からの運用上の到達性であって、call graph の到達性ではない。**

## 5. scope 外の real 所見 (裁定パッケージへ)

本 wave では実装していない。

1. **masstree autotools の CC/CXX が manifest へ束縛されない。**
   `prepare_masstree_fetchcontent` は top-level CMake の compiler を manifest から設定するが、
   masstree の custom command は `./configure` と `make` を CC/CXX 指定なしで実行し、親環境を継承する。
   生成される `config.h` の compiler 入力は manifest に束縛されない。D1666 の既知限界より広い。
2. **`s6_sort_sweep` と `s8a_trigger_sweep` の独自 preflight 関門も同型の base 未供給である。**
   それぞれ正規入口での到達性の実測と裁定を要する。
3. **`backoff_repro` と `s1_direct_comparison`** は D1733 が明示的に禁じている。触っていない。
   再訪条件だけを維持する。
4. **関門が見た `config.h` と計測 build の `config.h` の bytes 非束縛。** D1666 が受容した限界。

## 6. 親が refute した must-fix

段 3 レンズ A の「per-genome の prebuild が baseline (settle あり) と候補 (settle なし) の
熱・cache 状態を非対称にする」という must-fix を、親が現物で反証した。

`pipeline.evaluate` は関門の後に `_prepare_evaluation_core` で variant の**完全 build** を行い、
その後で `_bench_prepared` を走らせる。計測直前の機械状態を支配するのはこの build であって、
関門より前の 20 秒ではない。build は baseline と候補の両方で起きる。
`do_settle` の非対称は本変更以前から存在する設計であり、本変更に帰属しない。
settle を足すと計測の意味論が変わるので採らない (絶対規律 7)。

**ただし関門前の作業量が増えたことは事実である。**通常 sweep は 8 genome なので
1 workload あたり約 160 秒、3 workload 全走で約 8 分の追加になる (D1666 の単一観測 20.2 秒からの概算で、
本 wave の反復測定ではない)。terminal かつ非 retryable な候補は関門より前に return するので
実際の回数はこれより少なくなりうるが、baseline は `force=True` で必ず走る。

## 7. 開発検査

- 段 3 敵対相談 2 本 (`verbatim/s3-lensA.md` / `s3-lensB.md`)。
  レンズ A は must-fix 4 件、レンズ B は must-fix 2 件 + should-fix 1 件。
  親は 4 件を採用、1 件を refute、2 件を scope 外へ分けた。
- 段 6 敵対レビュー 2 本 (`verbatim/s6-reviewA.md` / `s6-reviewB.md`)。
  must-fix は共通の 1 件 (fixture) と、レビュー B の変異登録の訂正 2 件。
  fix 子 1 本が閉じた (`verbatim/s6-fix1.md`)。
- 焦点走 12 file: `test_screening_driver.py`、`test_condition_meaning_gate.py`、
  `test_backoff_sweep.py`、`test_backoff_extended_sweep.py`、`test_official_perf_closure.py`、
  `test_ccbench_spawn_sites.py`、`test_campaign.py`、`test_p2_2_site_aware.py`、
  `test_t1416_backoff_compiler_binding.py`、`test_screening_opt_in.py`、
  `test_s6_sort_sweep.py`、`test_s8a_trigger_sweep.py`。**776 passed / 3 skipped, rc=0**。
  後ろ 2 file はレビュー B が「明示された非発火経路の既存 consumer 回帰」として追加を要求したもの。
- 変異は probe → 本走の 2 段で行った。probe は全 15 件を SURVIVED で登録して観測 node を集め、
  本走はその完全集合を KILLED 期待として登録した (`DW-M07`・`DW-M08`)。
- pin 閉包は親と段 2 と段 3 レンズ B と段 6 レビュー B が独立に検査し、
  perf 閉包・spawn 台帳・certified writer 閉包・line-number pin・file 全体 sha256 pin・
  fixture 在庫検査のいずれも再登録不要と結論した。
