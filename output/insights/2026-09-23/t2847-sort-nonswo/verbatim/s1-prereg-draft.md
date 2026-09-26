# 事前登録表 草案 (段 3 相談の攻撃対象。段 4 で確定し、投入後は変えない)

共通: pin e9e477ca + patches/broken-silo-sort-nonswo.patch (patchharness.applied、git apply fuzz なし)。
build = s5_permutation_coverage._build_broken と同じ cmake argv (Release・sanitizer OFF・STOCK_G.cmake_defines()・-DCCBENCH_TRACE=1) のうち
`-DCMAKE_CXX_FLAGS=-D<macro>=1` を `-DCCBENCH_SORT_VARIANT=<v>` に置き換えたもの。gate = s5._require_condition_gate(sub, "SORT_VARIANT") (値 1、既定 0) が admitted であること。
共通 workload W(n) = thread_num 1・ycsb_tuple_num 200・ycsb_zipf_skew 0・ycsb_rratio 0・ycsb_rmw true・ycsb_max_ope n・extime 1・clocks_per_us 2100。run timeout 120 s。
実行順 R1→R2→R3→R4 (hang 見込みの R4 を最後)。

| run | build | workload | 期待 (層・verdict) | 到達の照合 (trace の C 行 write_count 最大) | 根拠 |
|---|---|---|---|---|---|
| R1 | stock (SORT_VARIANT=0) | W(16) | 完走 rc=0、verdict serializable・certified、巡回 0・X 0・P 0・integrity 全 0 | = 16 | #else は素の sort |
| R2 | stock (SORT_VARIANT=0) | W(17) | 同上 | = 17 | 同上。R4 の workload が 17 要素に届くことの証拠 |
| R3 | 壊し (SORT_VARIANT=1) | W(16) | 完走 rc=0、serializable・certified、P 0 (insertion sort は並べ替えるだけで要素を保つ) | = 16 | libstdc++ 11 は要素数 > 16 でだけ分割に入る。設計書・D42 の記録 (16 以上で hang) とは逆の予測 |
| R4 | 壊し (SORT_VARIANT=1) | W(17) | 120 s で timeout (hang)、verdict 無し | (部分 trace の値を記録するだけ。判定に使わない) | D42 の実機記録 (release/ASan で hang) と source の範囲外走査 |

分類 (run ごと、投入前に固定):

- R4 (V07 の本行): timeout → 「期待どおり (盲点: verifier は判定せず、止めたのは timeout)」。rc≠0 で終了 (signal を含む) → 「別の層で検出 (process の異常終了)」。rc=0 で完走し verifier が I / N → 「別の層で検出 (verifier の P などの層)」。rc=0 で完走し S かつ write_count 最大 ≥ 17 → 「未発生 (hang も違反も起きず S)」。rc=0・S で write_count 最大 < 17 → 「その他 (条件未到達)」。
- R3: 完走・S・write_count 最大 = 16 → 「期待どおり (境界の下で S)」。timeout → 「その他 (境界は記録どおり 16 で、source 読みが誤り)」。それ以外 → 「その他」とし内訳を書く。
- R1・R2: 期待どおりでなければ「誤検出」(対照の異常)。R2 が timeout・非 S のとき R4 の帰属は立たない (R4 は「その他」)。
- gate 不 admitted・build 失敗・patch 不適用 → job 全体を「その他 (未実走)」。基盤の失敗に限り同一 argv で 1 回だけ再投入してよい。patch・workload・timeout・期待は変えない。
