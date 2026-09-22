# 段 1 の事実 (repo = worktree dev-wave-t2851-transfer-prereg、HEAD = local main 8fd2a2f5c)
凡例: [親] = 親が現物で確認、[子] = 調査子 (sonnet) の報告で親は未検算、[子→親] = 子の報告を親が抜き取り検算

1. [子→親] 学習条件: orchestrator/campaign/p2_2.py:51-54 (RECORDS 1,000,000 / THREADS 48 / EXTIME 3 / REPS 5)、:74-77 WORKLOADS
   read-heavy rratio 95・balanced 50・write-heavy 5、いずれも zipf_skew 0.9・rmw 0。orchestrator/campaign/pipeline.py:160-161 S2_FLAGS
   (max_ope 10、thread 48、tuple 1,000,000、rratio 50、skew 0.9、rmw false)。小規模 correctness workload (pipeline.py:147-151) は tuple 200・
   thread 4・max_ope 5・rmw true・extime 1 (性能ではない)。
2. [子→親] CCBench 引数: CCBench の include/ycsb.hh:20-26 に ycsb_rmw (bool, 既定 false)・ycsb_max_ope (既定 10)・ycsb_rratio (既定 50)・
   ycsb_tuple_num (既定 1,000,000)・ycsb_zipf_skew (double, 既定 0、コメント "0 ~ 0.999...")。silo/mocc 共通。thread_num/extime は各
   cc/<proto>/include/common.hh。[子] mocc は common.hh に無接頭辞の重複 flag (tuple_num 等) を持つが、orchestrator は渡さず既定 1,000,000。
3. [子] argv 組立 = orchestrator/calibrator/runner.py:1085-1120 measure_point。pipeline.py:193-220 は workload dict の key を
   {ycsb_zipf_skew, ycsb_rratio, ycsb_rmw, ycsb_max_ope} に強制。pipeline.py:434-436 は ycsb_ 以外の binary を trace 経路で拒否。
4. [子→親] p2_2_flag_opt: orchestrator/campaign/s1_known_axes_freeze.py:42-46 EXPECTED_P2 = balanced 5185ee5e6094 / write-heavy 5185ee5e6094 /
   read-heavy b971a1d9f80a (Silo 専用、P2-2 の 8 genome 全探索の workload 別最良)。:47 EXPECTED_BACKOFF = balanced 5・write-heavy 10・
   read-heavy 2 µs (旧環境の格子 argmax)。[子] MOCC の既知最良は s8b catalog・docs/backoff-*.md に見つからず。
5. [親] Pegasus 正式 protocol の静的 backoff (docs/paper-story/2026-09-21c.md の A-2 / A-6 表): rr5 fixed10 +63.5485%、rr50 fixed5 +14.4213%、
   rr95 fixed2 −5.7841% (無 backoff = stock 比、median 比)。
6. [子] 既存の同等幅・CI: docs/backoff-policy-performance-preregistration.md §4-5 = ln 比の block 平均、±ln(1.03)、t 区間 (n=18)。
   docs/backoff-counterfactual-preregistration.md §5 = 同 ±ln(1.03)、TOST 90% と 95% 下端 > Δ で優越 (n=12)。
   docs/b5-generator-contrast-preregistration.md §6-7 = δ = ln(1+max(0.03, CV_stock(w)))、exact permutation、Holm。
   [親] p2_2.py の BETWEEN_RUN_CV = 0.030 (採否 floor、D19)、WITHIN_RUN_CV = 0.0228。
   [子] 対測定の既存機構 = pipeline.py:1212-1246 derive_balanced_schedule (ABA/BAB、root_seed からの SHA256 導出)、
   orchestrator/campaign/t1998_stock_inline_pair.py (K2 同 job pair、2 腕のみ受理)。
7. [子] Pegasus: docs/pegasus-runbook.md:35-45 = Xeon Platinum 8468 ×1 socket、48 物理コア、HT 無効、DRAM 128 GiB。node 間性能差の実測は
   repo に無い (:1417-1423)。[親] codex-consult-1 の換算 = 30 run ≈ 0.62 node 時間 (1 run ≈ 74 s、準備込み)。
8. [子→親] 8b holdout: orchestrator/campaign/s8b_holdout_freeze.py:87-104 HOLDOUTS = rr80 / rr20 (skew 0.9、rmw 0、1M、48 thr)。走査器は
   「ycsb_<軸>=<値>」と JSON の文字列値の書式だけを file 単位の三軸 conjunction で拾う (同 :64-77、:121)。
   docs/phase3-8b-descriptor-design.md:112-116 に未採用候補 H3 (rr50・skew 0.7) と H4 (rr50・rmw 1)。
9. [子→親] 既知結果の棚卸し (検索範囲 output/ と docs/ の git 管理下、網羅の証明ではない):
   - 読み比率 20/80: 8b floor 較正 1 本 (Silo 5 variant、Pegasus、2026-09-16、output/env/pegasus/calibration/s8b-floor-official/20260916T111925Z-2c8cf9be/)
   - 読み比率 0/100: SS2PL study (output/insights/2026-08-25_ss2pl-lock-protocol-study/raw/controls.json)
   - skew 0: cygnus 較正 (output/env/linux-baremetal/calibration/calibration_t48_skew0_rr50_rmw0_sweep.dat) と SS2PL。skew 0.5 は T139 probe の自己検査 (非 study)。
   - [親] rmw true: Silo・Pegasus・読み比率指定なし (= 既定 50)・skew 0.9・1M・48 thr・max_ope 10・extime 3、stock と ability-probe 変種 "hw" の
     比較 24 本 (output/env/pegasus/silo_ladder_rung1/、2026-07-29、T139。README は「性能比較 headline・calibration・floor の入力にしない」)。
   - thread 1〜48 (4 刻み、12 と 24 を含む): SS2PL study (Pegasus、rratio 50・skew 0.9)。Silo/MOCC の 48 以外は 0 件。
   - max_ope 1/5: trace の自己検査のみ (mocc mutation proof、silo ladder correctness)。
   - tuple 2M/4M: 較正 (Pegasus silo/mocc/tictoc、cygnus)。tuple 10,000: mocc G2 再現の trace 検証。
   - TPC-C: 実行記録 0 件。
   - 読み比率 25/30/40/60/70/75/90・skew 0.6/0.7/0.8/0.95/0.99・thread 56 以上: 検索式の範囲で 0 件。max_ope 20 も 0 件。
10. [子→親] T-2848/T-2849/T-2850 の設計文書は main に無い (T-2849 は並走中 wave が設計中)。T-2850 の手法集合・課題・独立探索数は未確定。
