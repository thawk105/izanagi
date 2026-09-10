## 編集面のアンカー表

| file / 現行位置 | 編集対象 | 種別 | 規模見込み |
|---|---|---:|---:|
| [screening_driver.py:8-13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/campaign/screening_driver.py:8) | import 群。`ExitStack` 相当と `tempfile` を追加 | 追加 | 2 行前後 |
| [screening_driver.py:168-210](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/campaign/screening_driver.py:168) | `_run_condition_gate_for_genome`。manifest の受領、一時 base、prepare、configure 引数追加、寿命管理 | 変更 | 25〜35 行追加、3〜5 行変更 |
| [screening_driver.py:213-231](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/campaign/screening_driver.py:213) | `_require_condition_gate_before_evaluation`。manifest を受け、stock / non-stock の両分岐へ転送 | 変更 | 5〜8 行 |
| [screening_driver.py:473-561](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/campaign/screening_driver.py:473) | `evaluate_candidate`。既存の `expected_toolchain_manifest` を関門 helper へ渡す | 変更 | 1〜3 行 |
| [test_screening_driver.py:169-280](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/tests/test_screening_driver.py:169) | 関門の正例、負例、prepare exact argv、`None` 非発火、stock 入れ子 | 追加・変更 | 100〜150 行 |
| [test_screening_driver.py:609-703](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/tests/test_screening_driver.py:609) | `evaluate_candidate` からの manifest / root 転送と prepare 失敗境界 | 追加・変更 | 40〜70 行 |

production の変更は `screening_driver.py` だけに閉じる。`backoff_sweep.py`、`s6_sort_sweep.py`、`s8a_trigger_sweep.py`、`backoff_repro.py`、`s1_direct_comparison.py` は編集しない。`buildcache.py` と `condition_meaning_gate.py` も既存 API をそのまま利用し、変更しない。

## 供給の配線

引数の流れは次のとおり。

1. `backoff_sweep.run_workload` が toolchain を一度観測する。

   - `backoff_sweep.py:344-347`: compiler を解決して `expected_toolchain_manifest` を生成。
   - `backoff_sweep.py:394-400`: `_run_screened_workload` へ渡す。
   - `backoff_sweep.py:258-264`: baseline の `evaluate_candidate` へ渡す。
   - `backoff_sweep.py:297-303`: 各候補の `evaluate_candidate` へ渡す。

2. `screening_driver.evaluate_candidate` が同じ manifest と source evidence を確定する。

   - `screening_driver.py:481`: manifest の既存引数。
   - `screening_driver.py:492-495`: manifest と env contract の既存整合検査。
   - `screening_driver.py:520-523`: 関門用 C++ compiler と CMake requested 名を同じ manifest から解決。
   - `screening_driver.py:528-533`: `SourceEvidence` を解決。
   - `source_digest.py:2344-2345,2365-2368`: `source_root` は `realpath(abspath(sub))` の canonical patched root。
   - `screening_driver.py:555-561`: manifest を `_require_condition_gate_before_evaluation` へ新規転送する。

3. `_require_condition_gate_before_evaluation` は manifest を stock / non-stock のどちらでも `_run_condition_gate_for_genome` へ渡す。

   - non-stock: `screening_driver.py:222-225`
   - stock: `screening_driver.py:226-231`

4. `_run_condition_gate_for_genome` では、現行 `requests` の空判定と build-route 検査、すなわち `screening_driver.py:173-176` を先に残す。その後、manifest がある場合だけ一時 base を作る。

`prepare_masstree_fetchcontent` の exact keyword は次とする。

| keyword | 値と出所 |
|---|---|
| `ccbench_dir` | `evidence.source_root` から来た canonical `source_root`。prepare と `capture_define_inputs` の両方へ同じ文字列を渡す |
| `fetchcontent_base_dir` | `_run_condition_gate_for_genome` 内の `TemporaryDirectory(prefix="izanagi-screening-condition-gate-")` を `Path.resolve()` した canonical path |
| `expected_toolchain_manifest` | `evaluate_candidate` が既に受けている同一 object。コピーや再観測をしない |
| `configure_timeout_s` | `900`。D1666 の `backoff_sweep.py:374` と同値 |
| `target_timeout_s` | `900`。D1666 の `backoff_sweep.py:375` と同値 |
| `site` | 明示的に `None`。`buildcache.py:2029` から `_resolve_site(None)`、同 `:1820-1822` の `site_policy.current_site()` で解決させる |
| `dependency_prefix` | 渡さない。既定 `""` |
| `masstree_source_dir` / `mimalloc_source_dir` / `googletest_source_dir` | 渡さない。既定 `None`。D1666 の driver 段と同じ |

configure 引数は次の exact tuple とする。

```text
(
    *_condition_gate_base_configure_args(genome),
    "-DFETCHCONTENT_BASE_DIR=<canonical_base>",
)
```

`_condition_gate_base_configure_args` は `screening_driver.py:156-165` のままにし、domain macro を除いた実 build 入力を保持する。FetchContent 引数は末尾に 1 本だけ追加する。

`capture_define_inputs` は `condition_meaning_gate.py:802-840` で tuple を保存する。supply 腕では `:2548-2556` から `_configured_define_compile_commands` に入り、`:1657-1670` で requested / control の両 configure argv に同じ base が入る。screening の meaning 腕は `screening_driver.py:188-192` が今後も `declaration=None` を渡すため、`condition_meaning_gate.py:3295-3301` で `unestablished` を返し、CMake configure は新たに行わない。

## 裁定案 (P1)

親の provisional 裁定を支持する。条件は恒真ではない。

- backoff の全 genome は `backoff_sweep.py:198-201` で `BACKOFF_FIXED` を持ち、2 つの `evaluate_candidate` 呼び出しは `backoff_sweep.py:258-264,297-303` で manifest を渡す。
- s6 は `s6_sort_sweep.py:214-215` で `SORT_VARIANT` を持つが、`:421-427` の呼び出しは manifest を渡さない。
- s8a は `s8a_trigger_sweep.py:310-311` で `BACKOFF_TRIGGER_GATING` を持つが、`:523-529` の呼び出しは manifest を渡さない。

したがって「domain request が存在する候補集合」にも manifest `None` の実例があり、分岐は実効的である。backoff 経路内では恒真だが、それは今回実測済みの経路を選ぶ意図どおりの結果である。

実装条件は `_run_condition_gate_for_genome` 内の次の二段にする。

```text
requests が空なら現行どおり即 return None
expected_toolchain_manifest is not None の場合だけ prepare と base 追加
```

`None` の場合は prepare、一時 directory、FetchContent 引数を一切発生させず、現行 `_condition_gate_base_configure_args(genome)` をそのまま `capture_define_inputs` に渡す。

新しい boolean や driver-id 判定を追加する案は採らない。別の policy knob や経路名依存を増やすためである。ただし将来 s6 / s8a が manifest を渡すよう変更される場合、この分岐も発火する。その変更時は D1733 の再裁定対象であり、今回追加する `None` 非発火テストを同時に更新しない限り水平展開できない形にする。

## 裁定案 (P2)(P3)(P4)

P2 は「関門 1 回につき prepare 1 回」を採る。配置は `_run_condition_gate_for_genome` の request/build-route 検査後、`capture_define_inputs` の直前とする。macro や supply request ごとのループ内には置かない。

stock request の入れ子は次になる。

```text
_require_condition_gate_before_evaluation
└─ patchharness.checkout(stock)
   └─ _run_condition_gate_for_genome
      └─ TemporaryDirectory(fetchcontent base)
         ├─ prepare patched source
         ├─ capture patched + stock roots
         ├─ supply 腕
         ├─ meaning 腕
         ├─ family admission
         └─ base を閉じる
   └─ stock checkout を閉じる
```

現行 `screening_driver.py:226-231` の stock checkout を外側に保つことで、prepare、関門、base cleanup が stock checkout の生存中に完結する。非-stock request は checkout なしで同じ `_run_condition_gate_for_genome` に入る。

数量評価:

- 通常 `backoff_sweep.genomes()` は 8 genome。20 秒 × 8 = 約160秒の追加 / workload。
- 3 workload 全走なら 20秒 × 24 = 約480秒、約8分。
- `screening_fixed_us` の最小 screening は baseline + 選択候補の2 genomeなので約40秒 / workload。
- `screening_driver.py:541-543` で terminal candidate が replay skip される場合と、request が空の場合は prepare しない。
- driver 段の既存 prepare 1 回約20秒は別であり、この160秒には含めない。

P3 は `site=None` を明示して `buildcache` の既定解決を使う。`p2_2.resolve_site_runtime` も `p2_2.py:244` で同じ `site_policy.current_site()` を使う。`prepare_masstree_fetchcontent` は `buildcache.py:2029` で一度解決した site を configure / build の両方へ渡し、`:2069,2075` から `_run`、`:3522-3523` の heavy-work site gate を通す。site を新たに `evaluate_candidate` の public 引数へ増やす必要はない。

P4 は prepare 例外を捕捉しない。`MasstreeFetchContentError`、manifest/root 検査由来の `BuildCacheError` をそのまま上げる。`evaluate_candidate` の candidate abort 捕捉は `screening_driver.py:562-605` で関門後に始まるため、prepare 失敗は偽の関門赤や WAL の candidate abort に変換されず、評価全体を停止する。例外時も一時 base と stock checkout は context manager により閉じる。

## 不変条件の維持

1. 判定式・受理集合・既定値・stock 比較・meaning 腕を変えない

   - `_CONDITION_DEFAULTS`、`_condition_requests_for_genome`、`_require_requests_match_genome_build_arguments` は無編集。
   - `screening_driver.py:182-210` の supply / meaning / `require_condition_gate_family` / reject 式は移動以外変更しない。
   - `condition_meaning_gate.py:4058-4063` の `supply_green and meaning_not_red` は無編集。
   - meaning の `declaration=None` と `use_class="raw"` を exact assertion で固定する。

2. `config.h` 不在時の preprocess skip を入れない

   - `condition_meaning_gate.py` は無編集。
   - 正例では実 supply evaluator の configure argvに base が入ったことを確認する。
   - `preprocess-failed` や `preprocess-bytes-identical` の扱いを変更しないことを負例で確認する。

3. 検査木と build 木を同じ patched source にする

   - prepare の `ccbench_dir`、`capture_define_inputs` の `source_root`、後続 `evaluate` の `source_evidence.source_root` が同一 canonical path であることを1テスト内で比較する。
   - `stock_root` はその path と異なることも確認する。

4. 関門の `config.h` と計測 build の bytes 同一性を束縛しない

   - `MasstreeFetchContentPreparation` の返り値、build dir、生成 header digestを保存・転送しない。
   - FetchContent base は関門終了直後に削除し、後続 `pipeline.evaluate` へ渡さない。
   - pipeline、buildcache の claim / publish、source digest、WAL schemaを変更しない。

5. 赤入力を緑にしない

   具体的負例は既存 fixture `fixtures/condition_meaning_gate/effectuation-ignored` と `Genome("silo", {"BACKOFF_FIXED": 5})` を使う。prepare だけを成功 stub にし、manifest を与えて実際の `capture_define_inputs` と supply evaluatorを走らせる。requested / default の owner TU preprocess bytes が同一なので、供給後も `preprocess-bytes-identical` の赤となり、`_run_condition_gate_for_genome` が `condition-family-rejected` を上げることを要求する。これは route 検査など別層で先に落ちない入力なので、関門への帰属も保てる。

## test プラン

| nodeid | 種別 | 殺すもの |
|---|---|---|
| `orchestrator/tests/test_screening_driver.py::test_screening_condition_gate_prepares_once_with_exact_fetchcontent_arguments` | 追加 | prepare の欠落・重複、manifest差し替え、900/900差し替え、`site=None` 欠落、optional引数の過剰供給 |
| `orchestrator/tests/test_screening_driver.py::test_screening_condition_gate_supplies_prepared_base_to_real_supply_arm` | 追加 | prepare base と `-DFETCHCONTENT_BASE_DIR` の不一致、引数未追加、requested/control片側だけの供給 |
| `orchestrator/tests/test_screening_driver.py::test_screening_condition_gate_rejects_real_ignored_runtime_define` | 変更 | FetchContent供給を理由に既存の実効性赤を緑へ変える回帰 |
| `orchestrator/tests/test_screening_driver.py::test_screening_condition_gate_without_manifest_preserves_unsupplied_path` | 追加 | `None` 経路での prepare、一時base、FetchContent引数の誤発火 |
| `orchestrator/tests/test_screening_driver.py::test_screening_condition_gate_no_requests_does_not_prepare_with_manifest` | 追加 | request空判定より前に20秒prepareを置く変異 |
| `orchestrator/tests/test_screening_driver.py::test_screening_condition_gate_prepare_is_nested_inside_stock_checkout` | 追加 | stock checkoutより前のprepare、関門前のbase削除、stock終了後までのbase延命 |
| `orchestrator/tests/test_screening_driver.py::test_evaluate_candidate_uses_one_canonical_root_for_prepare_gate_and_build` | 追加 | manifest転送欠落、prepare/gate/buildのroot分裂、stock rootの誤利用 |
| `orchestrator/tests/test_screening_driver.py::test_evaluate_candidate_prepare_failure_escapes_without_wal_abort` | 追加 | prepare例外の握り潰し、関門赤への変換、後続evaluate呼び出し、WAL abort化 |
| `orchestrator/tests/test_screening_driver.py::test_screening_condition_gate_accepts_real_runtime_genome_value` | 変更 | manifest `None` の既存正例を壊す変更。prepare を bomb stub にして非発火も固定 |
| `orchestrator/tests/test_screening_driver.py::test_screening_condition_gate_is_before_real_evaluate_build_sink` | 変更 | source evidence → prepare/関門 → evaluate の順序崩壊 |

D1666 の同型回帰として、次も焦点走へ含める。

- `orchestrator/tests/test_backoff_sweep.py::test_run_workload_prepares_masstree_once_before_condition_gate`
- `orchestrator/tests/test_backoff_sweep.py::test_run_workload_gates_the_prepared_patched_tree_with_fetchcontent_base`
- `orchestrator/tests/test_official_perf_closure.py::test_bench_callers_are_exact_and_own_canonical_preflight`
- `orchestrator/tests/test_official_perf_closure.py::test_official_perf_surface_inventory_is_exact`
- `orchestrator/tests/test_ccbench_spawn_sites.py::test_reviewed_process_launch_inventory_is_recursive_and_exact`
- `orchestrator/tests/test_ccbench_spawn_sites.py::test_define_sink_cross_product_has_no_unreviewed_ungated_member`
- `orchestrator/tests/test_campaign.py::test_certified_writer_authorization_caller_inventory_is_closed`

正しい実装で赤になると予想する既存 test はない。特に direct helper test は新引数を optional default `None` にするため呼び出し変更不要であり、既存 `evaluate_candidate` test の非-domain genome は request 空で prepare しない。

## pin 閉包

親の「再登録不要」を支持する。

- `test_official_perf_closure.py:74` は既に `screening_driver.py` を reviewed file に含める。
- 同 `:132-137` が `evaluate_candidate` 内の `probe_perf_availability`、`use_perf_from_receipt`、`evaluate` の各1呼び出しを登録し、`:370-372` が `not use_perf`、`:625-629` が bench authorityを登録する。今回これらの個数、関数、guardを変えない。
- `test_ccbench_spawn_sites.py:351-375` の process inventory は直接 process launchだけを数える。新しい production call は Python helper呼び出しであり、実 subprocess は既存 `buildcache._run` に残る。`buildcache._run` は同 test `:98-105` の既存 non-CCBench process site。
- build sink検出は `test_ccbench_spawn_sites.py:751-786` で `build/build_v2`、campaign/evaluate、direct CMake targetを対象にする。`prepare_masstree_fetchcontent` 呼び出しは新しい benchmark sinkとして数えられない。
- `screening_driver.evaluate_candidate` の既存 pipeline sinkは引き続き関門に支配されるので、同 `:2626-2631` の define×sink exact閉包も登録変更不要。
- 親 brief の一次走査で明示されていなかった exact 閉包は `test_campaign.py::test_certified_writer_authorization_caller_inventory_is_closed`。`test_campaign.py:5346-5368` は `screening_driver.py → campaign.pipeline.evaluate` を1件に固定し、`:5461-5478` も direct sinkを検査する。今回 `evaluate` 呼び出しは増減しないため台帳変更は不要。
- `acceptance_duration_ledger.json` は新規 test nodeの scheduling hintであり、production pin閉包ではない。未実測秒数を本 wave で手書き登録しない。

したがって `official_perf`、process spawn、build sink、certified writerのいずれにも再登録は不要である。`backoff_repro` / `s1_direct_comparison` の pin、freeze、供給には触れない。

## 変異候補の事前登録

行番号は現行アンカー。追加ブロックは `screening_driver.py:168-210` 内へ入る前提である。

| 変異 | 対象 | 殺すはずの test nodeid |
|---|---|---|
| M1 manifest の関門転送を削除 | `screening_driver.py:555-561` | `test_evaluate_candidate_uses_one_canonical_root_for_prepare_gate_and_build` |
| M2 stock 分岐だけ manifest を `None` にする | `screening_driver.py:226-231` | `test_screening_condition_gate_prepare_is_nested_inside_stock_checkout` |
| M3 `expected_toolchain_manifest is not None` を反転 | `screening_driver.py:168-181` の追加 guard | `test_screening_condition_gate_without_manifest_preserves_unsupplied_path` |
| M4 request 空判定より前へ prepare を移動 | `screening_driver.py:173-176` | `test_screening_condition_gate_no_requests_does_not_prepare_with_manifest` |
| M5 prepare を削除、または2回呼ぶ | `screening_driver.py:177-181` の追加 call | `test_screening_condition_gate_prepares_once_with_exact_fetchcontent_arguments` |
| M6 prepare の `ccbench_dir` を `stock_root` または非canonical rootへ差し替える | 同追加 call | `test_evaluate_candidate_uses_one_canonical_root_for_prepare_gate_and_build` |
| M7 `configure_timeout_s` / `target_timeout_s` の一方を90等へ変える | 同追加 call | `test_screening_condition_gate_prepares_once_with_exact_fetchcontent_arguments` |
| M8 `site=None` を固定 `"OTHER"`、または省略方針と不一致にする | 同追加 call | `test_screening_condition_gate_prepares_once_with_exact_fetchcontent_arguments` |
| M9 configure に baseを足さない、または別baseを足す | `screening_driver.py:177-181` 直後の追加 tuple | `test_screening_condition_gate_supplies_prepared_base_to_real_supply_arm` |
| M10 prepare終了時点で一時baseを閉じ、関門を外へ出す | `screening_driver.py:168-210` の追加 lifetime | `test_screening_condition_gate_prepare_is_nested_inside_stock_checkout` |
| M11 prepare例外を捕捉して現行configureで続行する | 同追加 block | `test_evaluate_candidate_prepare_failure_escapes_without_wal_abort` |
| M12 base供給時だけ admission赤を無視する | `screening_driver.py:194-207` 周辺 | `test_screening_condition_gate_rejects_real_ignored_runtime_define` |

いずれも upstream の route検査で先に赤になる入力は使わず、prepare、configure供給、またはfamily rejectの対象 seamまで到達するテストに照準を合わせる。

## 事前予測

予測: backoff_sweep の screening 経路の関門は緑になる可能性が高い。

根拠は次の3点。

- 一次資料 §1.2 の赤は `config.h` 不在による `preprocess-failed` で、準備済み base未供給と一致する。
- D1666 の driver段は、同じ patched root、同じ manifest、900/900秒、同じ base引数で実際に緑になった。
- screening の supply armも `captured.configure_args` を requested/control両方のCMake configureへ渡すため、prepareされたmasstreeの `config.h` を参照できる。

外れうる点は、通常 sweep の8 genome全体の関門がまだ実測されていないこと、各候補で新しい一時baseを作るため環境・容量・toolchainの一時故障が増えること、missing-header層を越えた後に別のsupply赤が露見しうることである。また関門が緑でも、その後のscreening buildや計測全体が緑になる予測ではない。一次資料が述べる第3層など、後続失敗が表面化する可能性は残る。

## 総括

実装は `screening_driver.py` の共有関門にだけ入り、manifestが存在するbackoff screening経路で、genomeごとに一時FetchContent baseを1回prepareして関門へ渡す。manifest `None` のs6/s8a経路は供給なしの現行挙動を維持する。

stock checkoutの内側でprepareと関門を完結させ、prepare失敗は例外のまま評価を停止する。判定式、meaning腕、stock比較、pipeline build、pin、freeze、`backoff_repro`、`s1_direct_comparison` は変更しない。

本段はread-onlyのため、編集、commit、pytest実行は行っていない。静的確認のみであり、テストの緑は主張しない。