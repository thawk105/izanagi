# 段 1 brief — [T-2847] 残り (2) のうち sort-nonswo (V07) 1 行の計算ノード実走

wave: dev-wave-t2847-sort-nonswo / worktree /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-sort-nonswo
(branch worktree-dev-wave-t2847-sort-nonswo、起点 local main 620a6bb13、開始 gate rc=0 = startup-gate.log、ccbench pin e9e477ca)

1. 研究前進: VLDB 差分分析 P0「検証の意味」。設計書 (output/insights/2026-09-22/t2847-verifier-detection-design/README.md) §4.3 の V07 行 (前回 wave 2026-09-23 t2847-patch-verify で唯一の未実走「その他」) を実測で 4 分類に付ける。完了判定 = V07 の観測・分類・stock 対照が insight に着地。
2. scope: patches/broken-silo-sort-nonswo.patch 1 本だけ。並走 wave dev-wave-t2847-mutation-run は sort-nonswo を scope 外と明記 (同 job dir brief.md の (P1))。condition gate の登録表・patches/ README・CCBench・verifier・既存 driver は編集しない。gate・検査・台帳・一般化の追加はしない。性能値は取らない。
3. 確定裁定 (依頼文): 起動器は前回の repo 外起動器 (Codex author) の方式。build の供給経路を gate と一致させる。期待 (層と verdict) と最小 workload を投入前に表で固定し、同じ job に stock 対照。期待と違っても patch・workload を事後に寄せない。2 node 時間以上ならユーザー確認。規律 2 不変 (patch 適用 = patchharness.applied の git apply fuzz なし、verifier 判定不変)。T-2847 carry の統合更新は相手 wave の着地を見てから fragment へ。
4. 親が段 1 で実測した前提 (攻撃対象):
   (P1) 供給経路: gate の SORT_VARIANT は ROUTE_CMAKE_CACHE (condition_meaning_gate.py:180-183)、configure は `-DCCBENCH_SORT_VARIANT=<v>` (同 :1774-1790)。s5._build_broken は `-DCMAKE_CXX_FLAGS=-D<macro>=1` (s5_permutation_coverage.py:239-240) で不一致。親案: 起動器は s5._require_condition_gate(sub, "SORT_VARIANT") をそのまま呼び (request 値 1・既定 0、s5:77-115)、実 build は s5._build_broken と同じ cmake argv のうち CMAKE_CXX_FLAGS だけを `-DCCBENCH_SORT_VARIANT=1` に置き換える。
   (P2) stock 対照: 同じ patch 適用木で `-DCCBENCH_SORT_VARIANT=0` (#else = 素の sort、patches/README の「既定 0 で inert」)。同じ applied() 文脈で 2 build。gate の登録 patch (silo-sort-variant.patch) と sort-nonswo patch は変更 path が同じ 2 file (transaction.cc・Options.cmake)。
   (P3) 閾値の新事実: 設計書 §4.3 と D42 の記録は「write set 16 要素以上で hang」。libstdc++ 11 (/usr/include/c++/11/bits/stl_algo.h:1855,1864,1929) は要素数 > 16 で introsort の分割に入り、16 要素ちょうどは guarded な insertion sort で終わる。比較はアドレス比較だけでメモリを読まない。よって source 上は 17 以上で `__unguarded_partition` (:1878-1894) の走査が範囲外へ進む。ただし -O2 以上の GCC は副作用の無いループを終わると仮定しうる (C++ の前進保証) ので、hang でなく別の壊れ方 (heap sort への退避・要素の破壊・crash) もありうる (未定義動作)。
   (P4) 最小 workload: s5 の SINGLE_FLAGS (s5:68-70) から ycsb_rratio=0・ycsb_zipf_skew=0・ycsb_max_ope ∈ {16, 17} だけを変える (1 thread・200 tuple・rmw=true・extime 1)。一様 200 key で 17 個が全部異なる確率は約 0.5/取引なので 17 は最初の数取引で届く。16 行は記録の境界 (設計書) と source の境界の弁別。到達の照合 = trace の C 行 write_count の最大値 (orchestrator/verifier/parse.py:6)。
   (P5) run の timeout は s5 の RUN_TIMEOUT_S=120 と同じ。timeout した run は verifier にかけず「verdict 無し」とし、trace の部分的な統計 (C 行数・write_count 最大) だけを記録。
5. 投入経路: tools/pegasus/dispatch_compute.py --task generic --walltime 00:30:00 -- /usr/bin/python3.10 <job dir>/<起動器> ... (前回 run-dispatch.sh と同形)。1 job。見積り: 前回 s5 job 134 s + hang 行の timeout 120 s ≒ 5 分 (≪ 2 node 時間)。
6. 成果物: 起動器 (job dir、Codex author、逐語を insight の verbatim へ)、insight output/insights/2026-09-23/t2847-sort-nonswo/README.md (事前登録表・観測・4 分類)、worklog fragment。repo 内の実装面差分ゼロ → 変異 matrix 免除 (DW-S04)、受入全走は行う。
7. 分割: 段 2 省略 (軽量版、変更面は起動器 1 file)。段 3 相談 1 本 (brief・事前登録表の攻撃)、段 5 author 1 本、段 6 review 1 本 (起動器、投入前) + insight の read-only review 1 本。
