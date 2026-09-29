# 段 1 brief — md_11: 比較相手の Cicada を較正し最良設定を決める (2026-09-29 JST)

wave: dev-wave-vhash-cicada-baseline-tuning / worktree /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-baseline-tuning (基点 main 1887f56e4、開始 gate fresh rc=0) / CCBench pin 68106660 (不変)
依頼逐語: 同 dir request-md_11.txt と /work/1/SFC/tanab/tmp/vhash-2026-09-29/common.txt

## 研究前進
VHash 論文の主 baseline「最適化と GC 設定を調整した Cicada」(docs/paper-story-vhash/2026-09-29.md §9 構成 A、出典メモ §25・§28.1) を、較正 (レコード数)・Cicada の走行間ばらつき・workload 別の最良設定と同等集合・gc_inter_us 曲線として実測で確定する。完了判定 = 一次資料 output/insights/2026-09-29/vhash-cicada-baseline-tuning/README.md に 5 workload (または実測できた部分集合と理由) の N・ばらつき・最良設定・同等集合・図 2 種 (生成器付き) が載ること。

## 既存被覆 (純増のみ)
- Cicada の較正 record は Pegasus に 0 件 (他 protocol 11 件は全て 48 thread・1M〜2M・D15 下限採用)。Cicada の throughput を Pegasus で測る driver は main に無い (md_6 の vhash_forwarding_prototype.py は未着地 branch、patch 適用前提)。
- 既存 floor driver `orchestrator/campaign/between_run_floor.py` は D1373 の関門 (`_protocol_source_has_trace_hook_evidence_only`) で cicada を拒否し、BASELINES にも無い (D2083 項 4・D2127 の却下欄)。

## 確定済み裁定・不変条件
- stock のまま測る: patches/・cc/cicada・gitlink を変えない。`-DCCBENCH_TRACE=0`、ADD_ANALYSIS=0 (計器なし、絶対規律 1)。既存 campaign driver・genome.py・between_run_floor.py を編集しない。tools/vhash_forwarding_model/ に触らない。
- CICADA_SPACE (24 有効点、`_cicada_promotion_requires_inline_opt`) を守る。CMake 既定 (OPT=0, PROMOTION=1) は冗長点で、同挙動の正準点 (0,0) を対照に使う。
- 性能値は全て「未検証の診断値」(common.txt §4)。md_3 は stock 既定を trace build で巡回 0 (上限 indeterminate) にしたが、最良設定は検査していない。serializable とは書かない。
- D19/D145/D1639: 採否 floor へ配線しない。1 投入束の値を「floor」と名乗らず estimand 名で呼ぶ。floor artifact (`output/env/*/calibration/between_run_noise_*`) を作らない。
- 計算: 合計 2 node 時間以上の見込みなら投入せず止める。単価の無い新種 job は walltime 上限で数える。条件は複数ノードへ割り、各 job に同時刻の対照 (control genome) を置く。login で計測しない。job tmp は /work/SFC/tanab/tmp/ 系。
- rr20 / rr80 は holdout 関門 (orchestrator/holdout_observation.py) に当たるので使わない。Cicada YCSB は `-ycsb_*` 接頭辞 flag だけが workload を変える (`-tuple_num` 等は効かない)。

## 親の provisional 裁定 (攻撃対象)
- (P1) 新規 driver で Cicada を測ることは D1373 関門の迂回ではない: 関門の射程は「between-run floor artifact の生成」で、本 wave は floor artifact を作らず compare・採否へ配線せず、診断値として insight に書くだけ。
- (P2) 長い tx の 2 型は stock で次のように作る。操作数が多い型 = 全 thread `-ycsb_max_ope=100 -ycsb_rratio=95` (短い tx と混ぜる形は stock で不可: batch_* flag は YCSB 経路で dead、util.cc:21 と result.cc だけ)。読み取り後に待つ型 = `-DCCBENCH_WORKER1_INSERT_DELAY_RPHASE=1` + `CMAKE_CXX_FLAGS=-DWORKER1_INSERT_DELAY_RPHASE_US=1000` (worker 1 だけが read phase 後に 1 ms 待つ、transaction.cc:923-927。`_US` はソースに定義が無く define で与える。ソース無変更)。base は rr50。
- (P3) 通常 YCSB は skew 0.9・max_ope 10・rmw 0 の rr5 / rr50 / rr95 (既存較正と md_6 の条件に揃える)。uniform は測らない (限界に書く)。
- (P4) レコード数は calibrator 方針 (orchestrator/calibrator/analyze.find_saturation: Δ=0.01、D15 下限 K=4、L3 110,100,480 B) を workload 別に control genome で 1M→2M→4M→8M (早期打切り)、48 thread、extime 3、reps 3。perf が使えなければ D15 の maxrss 基準だけで決め、その旨を書く。
- (P5) 工程: J0 pilot 1 job (生死確認 + 単価実測 + 較正 + within-run 10 reps) → 親が Elapse で残りを見積もり 2 node 時間未満なら J1 → J2。J1 = 24 genome を 4 job に 6 点ずつ + 各 job に control、全 workload (W5 は build が倍になるため単価次第で control + 上位 3)、gc 10、reps 3 を genome 巡回順で。J2 = workload 別上位 3 ∪ control × gc_inter_us {1,10,100,1000,10000}、reps 3、job を条件で分割。
- (P6) 走行間ばらつき = control の job 別 session median の CV (J0/J1/J2 の全 job、2〜3 投入時刻)。名前は「Cicada control の job 間 session-median CV (複数投入束、D145 の floor ではない)」。
- (P7) 同等集合の規則を結果前に固定: workload w で median_g ≥ median_best × (1 − cv_w) の g。cv_w は (P6) の値。√2 補正や有意差判定へ広げない (D2162 の記述的用法)。
- (P8) driver は `tools/vhash_cicada_tuning/` (tools 配下: test_ccbench_spawn_sites の棚卸し対象外)、起動は `tools/pegasus/dispatch_compute.py --task generic`。生出力 JSON は output/env/pegasus/vhash-cicada-baseline-tuning/ (create-only)。build は s3_mocc_lock_coverage の `_load_policy/_resolve_toolchain/_prepare_dependencies/_common_configure_args` を import (mocc の STOCK_G define は除く)、run は calibrator の benchparse / runner.measure_point 系。各 run の `#ShowOptParameters()` 行を解析して意図した genome と一致しなければ fail-closed (smoke の bindings 照合)。
- (P9) 図の生成器は tools/plotting/ の新規 file、作図は login (計測機の外)。

## 成果物の形
一次資料 (上記) / driver + test + 図生成器 (Codex author) / 生出力 JSON / spool fragment (worklog・decisions、新規 item「比較相手の Cicada を較正」)。

## 並列分割
実装子 1 本 (driver・test・plotter は相互依存するので 1 所有単位)。計測 job は J0 1 本 → J1 最大 4 本並列 → J2 最大 4 本並列。

## 受入・実測環境
Pegasus (pegasus02 login、gen_S 計算ノード、runbook docs/pegasus-runbook.md)。受入は tools/dev_wave_wait.py acceptance。

## 条件表の評価 (段 1 時点)
08 不成立 (freeze / oracle / proof chain に触れない) / 09・10 不成立 (凍結成果物を変えない、新規 file のみ) / 11 不成立 / 13 成立 (driver の genome 照合・単独性・site 検査の fail-closed を新設) → 入力 `#ShowOptParameters()` 行は util.cc:326-336 が必ず印字、J0 で実値域を測る。20 成立 (読了・gate rc=0)。
