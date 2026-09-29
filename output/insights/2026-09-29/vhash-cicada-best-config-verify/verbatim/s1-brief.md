# 段 1 brief — [T-2902] Cicada 観測最良設定の正しさ検査 (md_20)

- 研究前進: VHash 論文の主比較の相手 (構成 A = 調整済み Cicada、md_11 §10) を「判定器で巡回なし (indeterminate)」か「失格」かに確定する。完了判定 = 下の matrix の全 run に判定 (巡回数・integrity 数値項目・C 行 = commit 数) が付き、正例対照が同じ設定で検出されること。巡回が出た設定は主比較から外し、1 軸ずつ切り分けた結果を残す。
- scope: repo 外起動器 (md_17 の `launch_cicada_run.py` の写しを job dir に置き Codex author が拡張) で、pin C `68106660` + `patches/instr-cicada-trace.patch` (bytes 不変) を最良設定の CMake 値で build し、YCSB 小走行の trace を判定器 (`orchestrator/verifier/`、変更なし) に掛ける。repo への変更は一次資料 `output/insights/2026-09-29/vhash-cicada-best-config-verify/README.md` と spool fragment だけ (実装面の repo 差分ゼロの見込み)。
- 設定 (md_11 §6、B=BACK_OFF O=INLINE_VERSION_OPT P=PROMOTION R=REUSE_VERSION W=WRITE_LATEST_ONLY): BEST = B0 O1 P0 R1 W0 (rr5/50/95)、BEST100 = B0 O0 P0 R0 W0 (rr95・max_ope 100)、CTRL = B1 O0 P0 R1 W0 (md_11 の control)。BACK_OFF は共通引数 `STOCK_G.cmake_defines()` から入るので上書きし、CMake cache と 3 TU の compile command の -D で束縛する (md_11 の `check_compile_commands` と同型)。
- workload: skew 0.9・rmw 0・rr5/rr50/rr95 は max_ope 10、W4 は rr95・max_ope 100 (md_11 と同じ)。gc_inter_us は BEST の md_11 最良 GC (W1 100・W2 100・W3 10・W4 1000) と 10。
- (P1) 規模 (親の provisional、攻撃対象): 尺度 A = md_11 と同じ tuple 1M・t48・extime 1、尺度 B = 高競合 tuple 200 (W4 は要検討)・t4 と t48・extime 1。trace 量と判定器の所要 (md_3: K t4 で約 18 万 commit、判定器は 2,000 万 txn で約 23 分) から 1 run の所要を見積り、合計 2 node 時間未満・複数ノードへ分割。
- (P2) inline 版の記録: 静的には inline かどうかで読み書きの経路は分かれない (読みは `read_internal` → `read_set_` → R、書きは `write_set_` → W、版は読んだ時点に保存した wts)。初期版は OPT=1 で inline slot に置かれるので genesis 読みは inline 読みである。inline 書き (GC が slot を返した後の再利用) の発生は trace から区別できないので、repo 外の使い捨て診断 patch (Codex author、`#if TRACE` の内側だけ、trace 行を変えず stderr に件数だけ出す) で R/W のうち inline slot を指す件数を数える。instr patch の bytes は変えない (md_14/md_21 が重ねている)。記録されない経路が見つかった場合だけ instr patch を最小修正する。
- (P3) 正例対照: 既存 `broken-cicada-skip-read-recheck.patch` を BEST の build に重ね、同じ cell で巡回として検出されることを確かめる (「巡回なし」がこの設定でも検出力を持つことの根拠)。
- (P4) TRACE=0 の同一性を BEST と BEST100 の CMake 値でも取る (起動器の `trace_zero_identity`、YCSB 3 TU)。性能値はこの wave で出さない。
- READ_WTS_MISMATCH (読んだ時点の wts と commit 時の wts の食い違い) は run ごとに記録し、stock 設定で 0 でなければ「版 object が読み手の生存中に再利用された」所見として一次資料に書く (判定の合否は巡回・integrity で決める)。REUSE=0 では同じ比較が解放済み版を読む可能性がある (GC が安全なら起きない)。
- 巡回が出た場合: witness を構造化 (巡回の txid・辺・key・版) し、CTRL から 1 軸だけ BEST 側へ動かした build (B0 単独・O1 単独、BEST100 なら B0 単独・R0 単独) で同じ cell を再走して原因の軸を切り分ける。起動器に条件付き mode として持たせ、巡回が出たときだけ投げる。
- 確定済み裁定: D2279 (trace は out-of-tree patch、判定器不変、上限 indeterminate、OPT かつ PROMOTION は `#error`)、D2291 (較正は診断値)、D2294 (instr patch の bytes 不変)、D2277 (pin は C のまま、C2' 前進は別)。絶対規律 1・2: trace build の throughput を性能値に使わない、巡回が出た設定は即失格。
- 不変条件: 判定器・instr patch・external/ccbench の gitlink・他 wave の所有物 (patches/cicada-forwarding-*・cicada-interval-gc-*・md_19 の CCBench 修正) を変えない。certified とは書かない。
- 成果物: 一次資料 README (設定と条件、trace の網羅の確認、判定表、正例、同一性、限界、計算と工程)、spool worklog fragment (T-2902 の完了または更新)、必要なら decisions fragment。
- 分割: 段 5 は Codex author 1 本 (起動器拡張 + 診断 patch、repo 外)。段 6 はレビュー 2 本 (正しさ主張の妥当性 / 起動器の束縛と集計)。
- 実測環境: Pegasus 計算ノード (generic dispatch、`docs/pegasus-runbook.md`)、login では build・計測しない。受入は `tools/dev_wave_wait.py acceptance`。
- 変異 matrix: repo の実装面差分ゼロなら免除 (DW-S04)。起動器の検出力は (P3) の正例で示す。
- DW-G05: 放置すると論文の主比較の相手が正しさ未検証のまま headline に入り、規律 2 に反する (報告の値の受理集合が変わる)。
