## brief の前提の検査

以下の file:line は repo root からの相対パスで示す。

| 前提 | 判定と根拠 |
|---|---|
| (P1) 新規の診断 driver は D1373 関門の迂回ではない | **条件付きで成立。** D1373 の対象は between-run floor の生成許可である（ruling-D1373.md:3-11）。本件の値を floor artifact、`compare.noise_cv`、採否へ接続しないことを driver と一次資料で固定する。1 投入束を floor と呼べない（ruling-D145.md:5-11）。 |
| (P2) 長い tx の二型 | **要修正。** `ycsb_max_ope=100` は全 worker の各 tx を長くする（external/ccbench/include/ycsb.hh:55-75）。worker 1 の待機案は compile 可能な形だが、待機は `commit()` の冒頭で、読み取り後かつ validation 前である（external/ccbench/cc/cicada/transaction.cc:919-943）。既存の同名 runtime flag は表示されるだけで待機処理から読まれない（external/ccbench/cc/cicada/include/common.hh:61-62、util.cc:145-146、transaction.cc:923-925）。 |
| (P3) 通常 YCSB 三種 | **成立。** `rratio`、`max_ope`、`tuple_num`、`zipf_skew`、`rmw` は `ycsb_*` flag であり、手続き生成がこれらを読む（external/ccbench/include/ycsb.hh:19-32,55-75）。uniform を含まない限界を記す。 |
| (P4) 較正 | **要修正。** `run_sweep` は 1M から倍増し早期停止できるが、早期停止判定は 3 点以上からである（orchestrator/calibrator/sweep.py:77-132）。perf 不在では `find_saturation` の有効点がゼロになり、RSS 下限をそのまま選べない（orchestrator/calibrator/analyze.py:48-57）。別の RSS 選択関数が必要。 |
| (P5) J0/J1/J2 | **条件付きで成立。** 固定の条件数だけでは 2 node 時間を保証できない。J0 で build、DB 初期化、実走の単価を測り、残余全 job の **walltime 上限の合計**と実測予測の両方が 120 分未満の場合だけ J1/J2 を投入する（request-md_11.txt:28-31、request-common.txt:22-27）。 |
| (P6) job 間 CV | **名称を修正して成立。** `same-submission-cohort allocation-session-median CV` と呼び、J0/J1/J2 の投入時刻を区別して併記する。真正の between-run floor への昇格はできない（ruling-D145.md:5-24、ruling-D1639.md:3-17）。 |
| (P7) 同等集合 | **要修正。** 記述的な「観測 CV 幅内の候補集合」としては事前登録できるが、採否上の「差がない集合」にはできない。CV と二候補の差は別の量である（ruling-D1639.md:17、ruling-D2162.md:20-23,33-34）。 |
| (P8) helper 再利用と出力 | **要修正。** `_load_policy` は mocc 専用で、古い pin `e9e477ca…` を要求するため現 pin の汎用 loader ではない（orchestrator/campaign/s3_mocc_lock_coverage.py:42,120-144）。`_common_configure_args` には mocc の `STOCK_G` が含まれる（同:257-271）。依存準備部分だけ再利用し、policy 検証と Cicada configure 引数は新 driver 側で明示する。 |
| (P9) 計測機外で作図 | **成立。** 図規約は計測機外での作図、PNG・PDF・provenance、保存前の重なり検査を要求する（tools/plotting/FIGURE_CONVENTIONS.md:65-90）。 |
| brief の「24 点」「stock 対照」 | **成立。** `CICADA_SPACE` は 5 軸と promotion 制約で 24 点を列挙する（orchestrator/campaign/genome.py:91-103,172-205）。CMake 既定の `(INLINE_VERSION_OPT,PROMOTION)=(0,1)` は制約上の冗長点なので、正準対照は `(0,0)` とする。ただし「既定と同じ」は CC/data path に限り、起動時表示は異なる（同:94-98）。 |
| brief の「計器なし」「未検証の診断値」 | **成立。** `CCBENCH_TRACE=0`、`CCBENCH_ADD_ANALYSIS=0` を明示する。正しさ検査を経ていない値を採否や serializability の根拠にしない（request-common.txt:26-33）。 |
| brief の「batch flag は YCSB に効かない」 | **概ね成立、表現を限定。** `batch_th_num` は総 thread 数に加算されるため設定自体には作用がある（external/ccbench/cc/cicada/util.cc:18-21）。ただし YCSB の手続き生成は `ycsb_*` を読み、`batch_max_ope` は結果表示用に渡される（external/ccbench/include/ycsb.hh:55-75、external/ccbench/cc/cicada/ycsb_cicada.cc:34-40）。長短 tx 混合の根拠として batch flag を使わない。 |
| brief の「Pegasus に Cicada 較正 0 件」「既存 driver なし」 | **本射影だけでは未確認。** brief の記載（s1-brief.md:9-11）を一次資料の棚卸し結果と照合してから件数として掲載する。 |

## プラン

1. **Build。** `patchharness.checkout(pin.CURRENT_PIN, base_dir=<repo>/external/ccbench)` で使い捨て checkout を node-local `TMPDIR` に作り、`assert_pinned_clean` と full HEAD を記録する（orchestrator/campaign/patchharness.py:174-201,345-379、orchestrator/campaign/pin.py:30-32）。`tools/pegasus/policy.json` の third-party pin と compiler digest を検証する新しい Cicada 用 policy reader を置き、既存 `_resolve_toolchain`、`_prepare_dependencies` を再利用する（orchestrator/campaign/s3_mocc_lock_coverage.py:147-167,224-254）。`_common_configure_args` は `STOCK_G.cmake_defines()` を取り除いた同形の引数を新 driver で組み、`Genome.cmake_defines()`、`-DCCBENCH_TRACE=0`、`-DCCBENCH_ADD_ANALYSIS=0` を加える（同:257-271、orchestrator/campaign/model.py:146-152）。特に inline opt の cache 名は `CCBENCH_INLINE_VERSION_OPT_CICADA`（orchestrator/campaign/model.py:56-62、external/ccbench/cc/cicada/CMakeLists.txt:1-14）。fresh な build dir ごとに `ycsb_cicada.exe` を build し、binary SHA256、CMakeCache、compiler、source HEAD を束縛する。1 node 内の genome build は **同時 1 本**、各 build の `-j` を計算ノード用上限に固定する。並列 build で memory と後続の単独計測を競合させない。J0 で実測した build 秒数を J1/J2 の見積りに使う。

2. **長い tx。** `many-operations` は全 48 worker に `-ycsb_max_ope=100 -ycsb_rratio=95`。`read-phase-delay` は通常の rr50・10 操作に、build 時 `-DCCBENCH_WORKER1_INSERT_DELAY_RPHASE=1` と **一つだけ**の `-DCMAKE_CXX_FLAGS=-DWORKER1_INSERT_DELAY_RPHASE_US=1000` を足す。共通 configure 引数に `CMAKE_CXX_FLAGS` は無いので同名引数の衝突はない（orchestrator/campaign/s3_mocc_lock_coverage.py:257-271）。`clock_delay` は TSC clock 数を busy wait し、µs 値に `FLAGS_clocks_per_us` を掛ける（external/ccbench/include/delay.hh:11-21、external/ccbench/cc/cicada/transaction.cc:923-925）。`thid==1` は 48 worker 中の 1 本。`commit()` 冒頭なので read-only tx も待機を通る（同:919-936）。`-worker1_insert_delay_rphase_us=1000` 単独は**代案にならない**。J0 の compile、表示 macro 値、実走を通すまで「動作確認済み」とは書かない。

3. **Run と parse。** argv は `-thread_num=48 -ycsb_tuple_num=N -ycsb_zipf_skew=0.9 -ycsb_rratio={5,50,95} -ycsb_rmw=0 -ycsb_max_ope={10,100} -gc_inter_us=g -extime=3 -clocks_per_us=<実測値>` を基礎にする。`gc_inter_us` は GC の実行周期そのものではなく、各 worker の `mainte()` が前回起点からの clock 差を見て `GCFlag` を立てる間隔であり、GC 実行要求・回収は別段階である（external/ccbench/cc/cicada/transaction.cc:859-888、external/ccbench/cc/cicada/util.cc:285-323）。`throughput[tps]` は commit と batch commit の合計を名目 `extime` で整数除算した値（external/ccbench/common/result.cc:47-56）。Cicada YCSB は `actual_extime` を出さない（external/ccbench/cc/cicada/ycsb_cicada.cc:34-38）。

   `benchparse.parse_bench_stdout` と数値検証を使うが、run は timeout 付きの新規 `subprocess.run(..., shell=False)` にする。既存 `run_once`／`measure_point` は stdout を metrics へ変換して返し、タブのない `#ShowOptParameters()` 原文を保持しないためである（orchestrator/calibrator/runner.py:584-608,699-734、orchestrator/calibrator/benchparse.py:22-38）。新規 spawn site では `holdout_observation` の直接 flag 正規化・admission を通し、rr20/rr80 を拒否する。perf は較正時だけ `perf_preflight.probe_perf_availability` を先に行い、policy の候補パスは証拠として記録するだけで、使用可否は literal `perf` の結果に従う（orchestrator/calibrator/perf_preflight.py:100-176,261-270、tools/pegasus/policy.json:19-22）。測定前後に `site_policy.current_site(require_evidence=True)==PEGASUS_COMPUTE`、`competing_bench_pids()` 空、load 静定を確認し、競合時は停止する（orchestrator/campaign/p2_2.py:300-310）。

   `#ShowOptParameters()` は **ちょうど 1 行**を抽出し、固定の key 順・重複なし・整数値を解析する。5 軸、`ADD_ANALYSIS=0`、`SINGLE_EXEC=0`、delay macro 値を期待値と比較する（external/ccbench/cc/cicada/util.cc:326-336）。さらに `#FLAGS_*` の records、thread、GC、YCSB 条件を照合する。欠損・不一致・非有限 throughput・非ゼロ exit は当該 run を無効にして job を停止する。

4. **較正。** J0 で control genome、5 workload、48 thread、`N=1M,2M,4M,8M`、各 3 rep を使う。perf 有効なら `find_saturation(points,l3_bytes=110100480)` の規則、つまり連続する末尾までの miss 率差がすべて絶対値 `0.01` 未満となる最小 N を採る（orchestrator/calibrator/analyze.py:20-46,78-104）。早期停止は `run_sweep` の条件に合わせる（orchestrator/calibrator/sweep.py:91-132）。perf 無効なら、新規 pure 関数で `maxrss_kb×1024 >= 4×110100480 = 440401920 B` を満たす最小 N を選び、**飽和未判定**と記録する。8M でも満たさなければ N は未決定として後続を止める。perf 有効でも飽和も RSS 下限も確認できなければ同様に止める。確定 N の control を workload ごとに連続 10 rep 測り within-run CV を記録する（.claude/agents/calibrator.md:15-33、orchestrator/calibrator/analyze.py:239-259）。長い二型も別 workload として較正する。

5. **工程と分割。** J0 は smoke 1 run、control build、較正最大 `5×4×3=60` run、within-run `5×10=50` run。J1 は 24 genome を 6 点ずつ 4 job に配り、各 job に control の独立した 3 rep を置く。各 job は `7×5×3=105` run、全体 420 run。genome を一つずつ全 workload 完走させず、rep ごとに genome と workload を巡回し、始点を job ごとにずらす。J1 の上位 3 は各 job の同時刻 control に対する比で順位付けし、同率は canonical genome 順に固定する。J2 は workload ごとの「上位 3 ∪ control」× GC `{1,10,100,1000,10000}` × 3 rep、最大 300 run。4 job に条件を均等割りし、各 job に GC=10 の control を別枠で置く場合はその追加 run も見積りへ加算する。J0 の実測後、親が各 job の予定条件・build 数・上限時間を再計算し、全 job の walltime 上限合計と予測合計がともに 120 分未満のときだけ J1/J2 を開始する。1 worktree から dispatcher を同時起動しない。並列 J1/J2 には各々独立した計測用 worktree を用意する。

   起動形は `python3 tools/pegasus/dispatch_compute.py --task generic --walltime HH:MM:SS --queue-wait-timeout 900 --overall-grace 300 -- python3 -m tools.vhash_cicada_tuning.driver --stage j1 --job-id <明示ID> --spec <絶対パス>`。generic は child argv を cwd=repo root で直接起動する（tools/pegasus/dispatch_compute.py:155-160,1879-1893,4727-4764）。`tools/` は namespace package として `python3 -m` から import できる形にし、新 package に `__init__.py` を置く。job spec は create-only、内容と SHA256 を起動前に固定する。

6. **ばらつきと同等集合。** workload ごと、**同一 control genome・N・GC=10・48 thread・build 条件**の job 別 3 rep median \(m_j\) を作り、`CV = sample_stdev(m_j)/mean(m_j)` を全桁で算出する。J0 の 10 rep は同一 job 内の一つの session median にまとめる。job 数、投入時刻 cluster 数、host 数を併記する。これは同一投入 cohort が混じる記述量で、D145 の floor ではない。結果前に「J2 の各候補の job 内 control 正規化比の median」を順位量と固定し、最大値を best、`score_g >= score_best × (1−cv_w)` を**観測 CV 幅内の集合**と定義する。`cv_w` が欠ける、job 数が 2 未満、候補に欠測がある場合は集合を判定不能にする。この記述的計算は一次資料で行い、既存 compare の閾値や gate には入れない（ruling-D2162.md:20-23）。

7. **出力。** `output/env/pegasus/vhash-cicada-baseline-tuning/<attempt>/<job-id>/` に create-only JSONL と job manifest を置く。各 run に `schema`, `attempt_id`, `job_id`, `stage`, `rep`, `genome` canonical と flags、workload 全 flag、records、gc_inter_us、throughput_tps、abort_rate、commit/abort counts、maxrss_kb、host、UTC 開始時刻、elapsed 秒、binary SHA256、CCBench full HEAD、toolchain、argv、exit code、`show_opt_parameters_raw`、`flags_raw`、perf counters または不在理由、stdout/stderr SHA256 を含める。原文出力も create-only で保存する。generic child environment は `PBS_JOBID` を引き継がない（tools/pegasus/dispatch_compute.py:354-364,1661-1671）ため、job 識別子は親が spec に発行し、dispatcher receipt の request ID と後で結合する。

8. **図。** 新規 `tools/plotting/plot_vhash_cicada_tuning.py` は生 JSONL だけを読み直し、(a) workload 別の 24 設定の throughput、(b) GC 間隔の対数 x 軸と throughput を作る。95% t-CI、同時刻 control 基準線、48 thread・N・skew・条件、未検証の診断値という注記を入れる。PNG、PDF、入力 SHA256 と主要数値を持つ `.provenance.json` を出す。保存前に実 Figure の bbox overlap と panel 外逸脱を検査し、違反時は成果物を出さず非ゼロ終了する（tools/plotting/FIGURE_CONVENTIONS.md:23-35,39-44,65-90）。`tools/plotting/README.md` に再生成コマンドを追記する（同:122-131）。

9. **テスト。** `orchestrator/tests/test_vhash_cicada_tuning.py` と `orchestrator/tests/test_plot_vhash_cicada_tuning.py` に置く（pytest.ini:13）。24 点の列挙と promotion 制約、CMake 名、ShowOpt の実在する util.cc 行を使う正例・重複／欠損／値違いの負例、perf 無し RSS 選択、JSON の欠損・重複拒否、CV と集合の境界を検査する。図は 5 workload×24 点と GC 系列の実寸 fixture から**本物の matplotlib Figure** を描いて §9 検査へ通し、実データ取得後には全モードの PNG/PDF/provenance 三成果物を確認する（FIGURE_CONVENTIONS.md:96-114）。bench spawn を stub で置換した緑だけでは完了としない。全体テストの 5 分上限内に収まる pure test として設計する。

10. **所有と波及。** 新規は `tools/vhash_cicada_tuning/{__init__.py,driver.py,model.py,analysis.py}`、上記 test 2 本、plotter、一次資料、生出力、spool fragment。既存変更は `tools/plotting/README.md` の追記だけを基本とし、campaign driver・genome・floor・CCBench source・gitlink は変更しない。`test_ccbench_spawn_sites.py` の本体 inventory は `orchestrator/calibrator` と `orchestrator/campaign` の走査であり新 driver の `tools/` は範囲外（orchestrator/tests/test_ccbench_spawn_sites.py:31-44）。ただしこのことを admission の代わりにせず、新 driver 自身の site、単独性、holdout、source binding を test する。`tools/pegasus/admission_registry.json`、性能計測述語 inventory、hooks の Bash guard は実装時に新 path と起動 argv を静的照合し、必要なら当該 inventory だけ最小追記する。

## 見積り

`R=1 run の実測 wall 秒（DB 初期化込み）`、`B=1 genome build 秒`、`D=job ごとの checkout・third-party 準備秒`、`F=後処理秒` とする。J0 でそれぞれ測り、遅い N と長い tx の run を別単価として記録する。`extime=3` は run 全体の時間ではない。

| job | 条件数と run 数 | 予測式 | 仮の walltime 上限 |
|---|---:|---|---:|
| J0 | smoke 1、較正最大 20 点×3、within 5 点×10＝最大 **111 run**、control 2 build | `D₀+2B+Σ111 Rᵢ+F₀` | 00:20:00 |
| J1-0〜3 | 各 6 genome＋control、5 workload×3＝各 **105 run**、各 7 build | 各 `Dⱼ+7B+Σ105 Rᵢ+Fⱼ` | 各 00:15:00 |
| J2-0〜3 | 最大 20 genome-workload 組×5 GC×3＝**300 run**を四分割、追加 control は別計上 | 各 `Dⱼ+Bⱼ·build数+ΣRᵢ+Fⱼ` | 各 00:09:00 |

仮上限の合計は **20＋4×15＋4×9＝116 node 分**。基本の測定 run は最大 **831 本**で、名目 3 秒だけでも **2,493 秒＝41.55 node 分**を使う。残り 74.45 分で、全 run の DB 初期化、全 build、third-party 準備、追加 control、後処理を賄う必要がある。現時点ではその単価を示す実測がないため、**116 分で完走可能とはまだ判定できない**。J0 が 20 分を超える見込み、または J0 の単価から J1/J2 の予測ないし walltime 上限合計が 120 分以上になる場合、後続を投入せず、条件削減案と見積りを一次資料に残して止める。削減するなら、まず GC の上位候補数を 3→2 とする別の事前登録案を親が結果を見る前に確定する。24 点 screen の一部省略を事後に行わない。

## 事前登録案

| 項目 | 固定する内容 |
|---|---|
| Workload | rr5、rr50、rr95 は skew 0.9・10 操作・rmw 0。長い操作型は rr95・100 操作。待機型は rr50・10 操作・worker 1 に compile 時 1000 µs。全て 48 thread。 |
| Genome | `CICADA_SPACE.enumerate()` の 24 正準点。control は全 5 軸 0。ただし `INLINE_VERSION_PROMOTION=0` とする。 |
| N | workload 別に control で 1M→2M→4M→8M、各 3 rep。perf 有効なら末尾までの miss 率差 `<0.01` の最小点。飽和なし、または perf 無効なら RSS `>=440401920 B` の最小点。どちらも得られなければ未決定として停止。 |
| Screen | GC=10 µs、各候補 3 rep。各 job に同時刻 control を置く。job 内 control 比で上位 3 を選ぶ。同率は canonical genome 順。 |
| GC sweep | 上位 3∪control、`{1,10,100,1000,10000}` µs、各 3 rep。 |
| Best・集合 | job 内 control 比の median 最大を best。同等集合という表示名は「観測 CV 幅内の集合」に限定し、`score_g >= score_best(1−cv_w)`。CV は同一動作点の job 別 control session median の標本標準偏差／平均。数値は全桁で計算する。 |
| 判定不能 | perf・RSS による N 未決定、source binding 不一致、run 欠損、CV の job 数不足、計算予算超過は理由別に記録する。観測できた workload だけを明示し、未測定をゼロや最下位として埋めない。 |

## 未解決の論点

- J0 の単価が未取得であり、現行の 24 点×5 workload×GC sweep が 2 node 時間内に収まる保証はない。J0 は生死確認と単価測定を兼ね、結果が出るまで J1/J2 の投入可否を確定しない。
- `read-phase-delay` の `_US` macro は `ShowOptParameters()` に表示されない。build の `CMAKE_CXX_FLAGS` と binary SHA256 を束縛し、J0 の動作確認を追加する必要がある。
- 同一投入 cohort の CV は時間分離された floor ではない。集合は記述的な幅であり、統計的な同等性や採否の保証を意味しない。
- 現 pin での perf 権限、実際の L3 値、third-party cache の可用性、長い tx の 8M 初期化時間は J0 で確認する。L3 が指定値と異なれば較正を止めて環境契約を見直す。

## 総括

実装可能な経路はあるが、brief の perf 不在時の較正、mocc 専用 policy の再利用、同等集合の意味を修正する必要がある。J0 で build と run の単価を取り、全 job の上限合計と実測予測がともに 2 node 時間未満と確認できた場合だけ、24 点 screen と GC sweep を進める。得られる性能値は正しさ未検証の診断値として報告する。