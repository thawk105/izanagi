# 段 6 裁定 2 — md_33 (wave dev-wave-cicada-certified-m、2026-09-30)

入力: focus1.md (焦点再レビュー 1 巡目、NO-GO)、親の SMOKE 実走 (request 38725.nqsv、Elapse 17 s、`runs/smoke-1/result-SMOKE.json` の exceptions: 同一性 build `default-ycsb_cicada-stock-left` の cmake configure が rc 1。build dir の `cc/` に `oze` だけが無く、oze の configure で止まったとみられる。起動器が cmake の stderr を捨てるため本文は無い)。対象 = e82f255d7 と job dir の起動器・変異 patch。fix 前の snapshot は `snapshot-pre-fix2/`。

| ID | 裁定 | 処置 (fix 担当) |
|---|---|---|
| F1 世代 1 回加算の窓 | real (must-fix) | U1: 事象を seqlock 型の 2 段にする。開始で `trace_gen_` を +1 (奇数、acq_rel) → release fence → 所有解除・事象名 → 版の状態変更 → 終了で +1 (偶数、release)。再利用 (`newVersionGeneration`) は開始 +1 → `set()` と新しい所有 tuple の設定 → 終了 +1。読み手の snapshot は `g1` が奇数なら不合格 (`B_WINDOW`)、`g1 == g2` を要求。終了照合は保存した偶数世代との不一致で `B_RETIRED`。順序コメントを合わせる |
| F2 母集団の等式が照合の実行を証明しない | real (must-fix) | U1: 集計 key `b_elements_checked` (終了照合の loop で実際に照合した read set 要素の数) を `b_end_checked_abort` の直後に足す。`api_checked` は呼び出し単位の比較を実行した地点 (OK で戻る分岐それぞれ) で数え、デストラクタで数えない。U2: 等式を `b_registered = b_elements_checked` と `api_checked + read_not_found + read_other_status = read_calls` に替える (他の 3 本 = commit 数・begin 差・`tx_reconnoiter = 0` は維持。`b_end_checked_* = tx_end_reads_nonempty` も残す) |
| F3 E-max の hunk の位置 | real (should) | U1: E-max stack (`instr → variant → gc → target → M`) を scratch で適用し、M の 18 hunk それぞれが当たった位置の関数名 (前方の関数定義行) と、`pin C → instr → M` での関数名が一致することを表で報告する |
| S1 (前回) の実走確認 | — | 親が SMOKE の dry-run で stock の offset 0 を再実測する (前回 rc 0) |
| S2 (親) SMOKE の cmake configure 失敗 | real (must-fix) | U2: (1) cmake の configure・build・実行の失敗時に stdout / stderr の末尾 (各 200 行) を result の exceptions に残す。(2) source の展開と configure を、同じ環境で動いた雛形 1 (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-cicada-gc-records-fix/stage7/launch_gcfix_run.py` の checkout と configure_values) と同じ方法に揃える。`git archive` による展開をやめるなら理由を書く。雛形 1 と今回の cmake 引数の差 (`CCBENCH_INLINE_VERSION_PROMOTION` の値、genome 由来の -D) を列挙し、差が configure を落としうるかを cmake の source (`external/ccbench/CMakeLists.txt`・`cmake/*.cmake`・`cc/oze/CMakeLists.txt`) で確かめる |

焦点再レビューは 2 巡目を fix 後に行う (上限 3 巡、DW-O16)。
