# [T-2760] between-run floor の BASELINES に根拠つき TicToc baseline を登録した — CMake cache 既定 = 認定較正と同 genome、実測は開通させない

authority: none / default_effect: no-state-change (プロセス監査・逐語凍結。可変状態の正本は worklog 末尾と現行 phase doc)

- wave branch: `worktree-dev-wave-t2760-tictoc-floor-baseline`
- 基準 commit: `38353207f719acb0871cfe3d9bbe3a02490282bb` (local main、wave 開始時、fresh worktree)
- 実装 commit: `5fa44cfb1a8b0af485d4201e630587e6bb6a0336` (Codex `role=author` 1 本、2 file、+191)
- 起票: [T-2760] (worklog 1613 の次の一手、D2114 項 4)。ユーザー依頼 (2026-09-17) の逐語は worklog fragment。
- 設計判断: 本 wave の decisions fragment (slug `tictoc-floor-baseline-cmake-default`)
- job dir (prompt・log・spec・台帳の原本): `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2760-tictoc-floor-baseline/`
  (codex の prompt / 報告 / 親 brief は `wave-job-tmp/`、変異 spec と台帳は `mutation/`)

## 何をしたか

`orchestrator/campaign/between_run_floor.py` の `BASELINES` に tictoc の entry を 1 つ足した。値は

```
tictoc|BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,PREEMPTIVE_ABORTS=1,TIMESTAMP_HISTORY=1
```

で、entry の直上に出典 comment (Options.cmake 既定・TICTOC_SPACE 所属・認定較正 record と同一・D1373 の関門で拒否) を置いた。
silo / mocc の entry、`BASELINE = BASELINES["silo"]`、`_write_out` の stem 規則、`_parse_cli_args`、
`_protocol_source_has_trace_hook_evidence_only`、`main()` の順序は 1 byte も変えていない。

test (`orchestrator/tests/test_between_run_floor.py`、素の runner 形式) は既存 1 本に assert 1 行 (実 source で tictoc の hook 述語が偽)、
新規 6 本:

| # | test | 何を固定するか |
|---|---|---|
| T1 | `test_t2760_baselines_are_points_of_their_registered_genome_space` | 鍵集合 = {silo, mocc, tictoc}、各 entry が `space_for(p).enumerate()` の点 (制約充足) |
| T2 | `test_t2760_tictoc_baseline_matches_ccbench_cmake_cache_defaults_at_pin` | tictoc の 5 flag が現行 checkout の `external/ccbench/cmake/Options.cmake` の `set(CCBENCH_<AXIS> <v> CACHE …)` と一致 |
| T3 | `test_t2760_parse_cli_args_accepts_tictoc_and_rejects_unregistered_protocol` | `--protocol tictoc` / `--protocol=tictoc` 受理、`cicada` (空間はあるが baseline 無し) は `unknown protocol` |
| T4 | `test_t2760_protocol_output_stem_names_tictoc_without_colliding` | 同一 dir に silo / mocc / tictoc を書き、tictoc の stem が `between_run_noise_tictoc_t48_…`、3 名相異、md に canonical genome |
| T5 | `test_t2760_tictoc_floor_rejected_before_build_or_measure_without_trace_hook` | 現行 pin の実 source で `main([... "--protocol", "tictoc"])` が `ValueError` (trace hook) で止まり tenant / build / measure / write が呼ばれない |
| T6 | `test_t2760_hook_bearing_source_routes_tictoc_baseline_through_main` | hook 入り fixture source で main が 0 を返し build / measure が `BASELINES["tictoc"]` を受け write が tictoc |

## 根拠 (親が brief 前に実測、段 1)

1. **CMake cache 既定と一致:** 現行 pin `511c9538` の `external/ccbench/cmake/Options.cmake` — L20 `CCBENCH_BACK_OFF 1`、
   L27 `CCBENCH_NO_WAIT_LOCKING_IN_VALIDATION 1`、L28 `CCBENCH_NO_WAIT_OF_TICTOC 0`、L44 `CCBENCH_PREEMPTIVE_ABORTS 1`、
   L45 `CCBENCH_TIMESTAMP_HISTORY 1`。`cc/tictoc/CMakeLists.txt` の OPTIONS はこの 5 つ + `PARTITION_TABLE` (死にフラグ) +
   `SLEEP_READ_PHASE` (計測撹乱、D1418 で軸外)。mocc 登録 (2026-09-01) の根拠も「CMake defaults」
   (`output/insights/2026-09-01/t2115-cross-protocol-impl/verbatim/s2-plan.md` L40) で同形。silo だけは p2_2 の歴史的 stock
   (BACK_OFF=0) で既定と異なる。
2. **genome 空間の点:** `TICTOC_SPACE` (`orchestrator/campaign/genome.py`) の制約 `_tictoc_no_wait_not_both` を満たす
   (no-wait (1,0)、D1418)。silo / mocc の既存 baseline も各 SPACE の点 (親が `in space.enumerate()` で実測 True)。
3. **認定較正と同一 genome:** D2083 が登録した accepted な tictoc 認定較正 record 2 件
   (`output/env/pegasus/calibration/registered/calibration-9b49335d02ad4d2e.json` rr50、`calibration-cb98513996e5ae35.json` rr95、
   ccbench `head_sha` 511c9538) の `genome` と文字列一致。mocc の record 2 件 (`449d0ad22f13e366`、`b3329d93417c76ad`) も
   `BASELINES["mocc"]` と一致 (同形)。`tools/pegasus/certify_calibration.sh` の tictoc 軸表 (D1863) とも一致。

**現行 pin での述語:** `_protocol_source_has_trace_hook_evidence_only` = silo True / mocc False / tictoc False (`cc/tictoc/` に
`izanagi_trace` 0 件)。変更前の引数解析は `unknown protocol: 'tictoc' (選択肢: ['mocc', 'silo'])` で拒否していた。

**既裁定との関係:** D2083 項 6「`BASELINES` へ tictoc を足すことも行わない」は同 wave (T-2634) の scope 判断であり禁止ではない。
D2114 項 4 が本 T として明示的に起票した。D1373 (許可リストでなく source 事実へ束縛) は不変で、tictoc を足しても関門は同じ
述語のまま。層 3 report は floor の `genome` から protocol だけを取り (protocol, records, threads, workload) で照合するので、
within-run と between-run が別 stock でも機械的には対になる — 整合は登録側で保つ (decisions fragment)。

## 受理集合 (変えていない)

- 現行 pin で `--protocol tictoc` は引数解析を通り、`main()` が build 前に `ValueError("protocol 'tictoc' の現行 CCBench source に
  trace hook の証拠がない")` で止まる。`_assert_single_tenant`・`buildcache.build`・`measure_point_floor`・`_write_out` のいずれも
  呼ばれない (T5 が calls 空を固定、M4 で殺される)。
- 新しい gate・validator・schema・env・argv は足していない。既存 floor JSON 4 件・silo / mocc の出力 stem・関門の bytes は不変。
- **実測 (計算ノードでの floor 生成) は行っていない。** 開通には hook 移植 (T-2759、現行 phase doc 段 7 Group B) と pin 再承認
  (D1603 / D2104 項 13) が別途要る (D2083 項 5)。

## 軽量版判定と工程

DW-C00 の 3 条件 — 設計択一なし (genome は証拠から一意)、正しさ防壁のコードに触れない (関門述語・reject 経路は不変、新 test が
発火させるだけ)、floor 生成の受理集合不変 — のいずれにも当たらないので段 2・3 と段 6 review 子を省いた。
段 4 の裁定 (P1: 根拠の形 = code comment + insight、P2: Options.cmake 束縛 test は tictoc のみ) と変異事前登録 M0〜M7 は
`verbatim/s1-brief-s4-ruling.md`。

- 段 5: Codex author 1 本 (`gpt-6-astra` / `medium`、14 call)。prompt `verbatim/s5-author-prompt.md`、報告 `verbatim/s5-author-report.md`。
  差分は brief どおりで親監査に逸脱なし。author 子の wrapper pytest は sandbox の uid 名前空間で `qstat -Q` が
  `NQSconnect: [API EACCTAUTH] Unknown user-id` → rc=16 (親側は rc=0、実 dispatch の障害ではない)。
- 親の焦点走 (login): `test_between_run_floor.py` 34 passed / 4.87 秒。consumer / meta-test (use_perf closed-set、
  floor_pair_driver、g5 ledger coverage、`test_screening_driver.py` / `test_pegasus_floor_scoping.py` / `test_codex_agents.py`)
  115 passed / 54 秒。
- provenance: `--message-file` rc=0、全史監査 11076 件 新規違反なし。

## 変異 matrix (container worktree `mutation-tree` @ 5fa44cfb1、`tools/mutation_harness.py`、runner = `run_tests.py --force-dispatch`、計算ノード)

spec は `mutation/make_spec.py` が生成 (probe sha256 `1a748ced…`、final `71865d78…`)。anchor は全件 1 箇所。

| ID | 変異 (between_run_floor.py) | 種別 | 期待 killer (段 4 事前登録) |
|---|---|---|---|
| M0 | tictoc entry 行に末尾 comment | 等価 (positive) | SURVIVED |
| M1 | tictoc entry 全体を comment 1 行へ (登録の不在) | negative | T1〜T6 の 6 node |
| M2 | tictoc `BACK_OFF` 1→0 | negative | T2 |
| M3 | tictoc `NO_WAIT_OF_TICTOC` 0→1 (制約違反 (1,1)) | negative | T1、T2 |
| M4 | `main()` の hook 関門 `if not …:` を恒偽 (規律 2 の負例) | negative | T5、既存 `test_mocc_floor_rejected_before_build_or_measure_without_trace_hook` |
| M5 | `_write_out` の `protocol_part` を tictoc でも "" (protocol 別出力の負例) | negative | T4 |
| M6 | `_parse_cli_args` の `if protocol not in BASELINES:` を恒偽 | negative | T3 |
| M7 | `main()` の `baseline = BASELINES[protocol]` → `BASELINES["silo"]` | negative | T6、既存 `test_hook_bearing_source_routes_mocc_baseline_through_main` |

**probe 走 (全件 SURVIVED 登録、`mutation/ledger-probe.json`):** baseline PASSED (27.6 秒)、M0 SURVIVED、M1〜M7 は MISMATCH
(= 殺された) で観測 node が上表の事前登録と全件一致 (M1 6 / M2 1 / M3 2 / M4 2 / M5 1 / M6 1 / M7 2)。

**本走 (final spec、`mutation/ledger-final.json`、`attempt-final.json`):** baseline PASSED (684 秒、queue 待ち込み)、負例 M1〜M7
**7/7 KILLED** で期待 node と観測 node が完全一致 (matching 8/8)、等価 M0 SURVIVED、MISMATCH 0、TIMEOUT 0、PARSE_ERROR 0。
専属 killer: M2 → T2 だけ、M5 → T4 だけ、M6 → T3 だけ (負例の単一理由性)。M4 (規律 2 の負例) は既存 mocc 拒否 test と T5 の 2 node、
M7 は既存 mocc 経路 test と T6 の 2 node で、tictoc 側の test は mocc 側と対になる。走行後の container の
`between_run_floor.py` は実装 commit と同一 sha256 (`dfc607ab…`)、orphan hold なし。

## scope 外で残るもの (裁定パッケージにしない、記録のみ)

- tictoc の between-run floor 実測 (hook 移植 T-2759 + pin 再承認 D1603 の後)。
- cicada の baseline (認定較正なし、D2114 項 4 の起票外)。
- `BASELINES` を genome 空間の既定値から導出する一般化 (D1863 と同じく登録表は独立に持つ)。
