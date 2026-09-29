# 段 1 brief — md_23 (T-2908) stock Cicada の gc_records ERR を原因特定のうえ修理 (2026-09-29 22:1x JST)

wave: dev-wave-vhash-cicada-gc-records-fix / worktree /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-gc-records-fix / 起点 main 8fe87f852 (開始 gate fresh rc=0)。
依頼: /work/1/SFC/tanab/tmp/vhash-2026-09-29/md_23.txt (+ common.txt、ただし inert patch 規定は不適用)。一次資料: output/insights/2026-09-29/vhash-cicada-verifier-ext/README.md §5 (D2294)。
分担: md_19 (cicada build issues fix) は同 item の項目 3 を md_23 へ移管済み (peer 返信 22:0x、md_19 は INLINE_VERSION_PROMOTION と WORKER1_INSERT_DELAY_RPHASE のみ、gc_records 周辺を触らない)。

研究前進: delete を含む並行 TPC-C の Cicada を VHash の評価と正しさの門 (巡回・integrity・存在履歴) に使えるようにする。完了判定は「修理版 F×t4/t8 が N/N 完走・同時刻の無修理版は落ちる」「修理版 trace が巡回 0・integrity 数値 0・存在履歴違反 0・C 行 = commit 数」「M・R2 で修理前後の判定不変」(修理自身が現れない観測量)。

scope:
- (D) 診断 (DW-G01 の生死確認、修理の前): 使い捨て診断 patch (repo 外、Codex author) を F 25898d00 の TRACE=0 build に当て F×t4 (と t8) を走らせ、ERR 直前の版鎖と「install 済みで abort した版」の事象を stderr に出して仮説を確かめる / 棄却する。
- (X) 修理: cc/cicada/ だけの最小変更 (Codex author)。CCBench local branch (F の子 1 commit、新 branch 名 izanagi-cicada-gc-records-fix 仮) と patches/fix-cicada-gc-records*.patch (pin C → (instr 系) → fix の厳密適用)、patches/README.md の節。ledger.json は触らない。
- (V) 確認: 上の完了判定 3 つ + 上流 CI 2 本 (clang-format 14 と CI image の Release 全 protocol build、T-2854 の run_ci_build.sh を写す)。
- 任意 (時間があれば): delete の意味を壊した正例。

確定済み裁定: D2277 項 1・2 (上流 CI を通す品質、基盤の欠陥は使いながら直す)、D16・D18・D20 (push・PR・gitlink 前進は人間)、D2293 (F の由来)、D2294 項 4、規律 1・2 (正しさを緩める修理を採らない)。

不変条件:
- 修理は受理集合 (どの tx が commit/abort するか) を変えない形を優先。変えるなら直列化可能性の論証と判定器の実走を要件にする。
- ERR の防壁を消して黙らせる修理は不可 (本当の不整合を隠す)。
- TRACE=0 の性能 build は修理以外で不変。性能値は取らない。計算は合計 2 node 時間未満。
- 他 wave の cc/cicada patch (cicada-forwarding-*、instr-cicada-version-lifetime、broken-cicada-*、instr-cicada-trace*) は読むだけ。fix との重ね適用は実測で調べ README に書く。

静的な読み (親、file:line は external/ccbench = pin C = F の cc/cicada):
- 削除の install (transaction.cc:490-520) は最新版の wts しか見ず、最新版が deleted / pending でも CAS で上に積む。
- abort すると writeSetClean (include/transaction.hh:343-349) は install 済みの版を aborted にするだけで版鎖から外さない。
- gc_records (transaction.cc:845-857) は最新版が deleted でなければ ERR。
- (b) の検査 (transaction.cc:576-593) は自分の版の下を pending 待ち→committed/deleted まで辿り、deleted なら abort。したがって deleted 版より上に積まれた版は必ず abort する (commit しない) — 修理案 X1 の安全性の根拠 (P2)。

(P1) 親の provisional 裁定・攻撃対象: 機序は md_17 仮説 (後発の削除版 D2 が aborted のまま最新版に残る)。D で実測するまで未実証。
(P2) 修理の第一案 X1: gc_records が最新版から aborted の版を読み飛ばし、最初の非 aborted 版が deleted なら回収、そうでなければ ERR を残す。受理集合を変えない (GC の判定だけ)。対案 X2 = abort 時に install 済みの版を鎖から外す (並行 CAS と読み手の走査に触る、侵襲大)、X3 = install 時に最新版が deleted なら abort (pending 中の削除との競合を塞げず単独では不足)。
(P3) 「gc_records が回収可と判定した時点 (最新版 wts < MinRts) で版鎖に pending は無い」— X1 の前提。MinRts の算出 (leader) と ThreadRtsArray の不変条件に依る (記憶: model-protection-vs-implementation-invariant)。
(P4) aborted 版 (D2) と D1 自身は delete rec で解放されない (既存の leak)。修理の scope 外とし記録だけ。tuple を他 thread が指したまま delete する既存の危険も scope 外 (記録)。
(P5) 計測の基点は F。F と pin C は cc/cicada が同一 (git diff 空を実測) なので、同じ差分が pin C にも当たる。instr-cicada-trace(-tpcc).patch が F に厳密適用できるかは未測 (C1' 以降と明記はある)。

成果物: CCBench branch 1 本 (F の子)、patches/fix-cicada-gc-records*.patch、patches/README.md 節、output/insights/2026-09-29/vhash-cicada-gc-records-fix/README.md、spool fragment (worklog: T-2908 の完了または更新)。
受入・実測環境: 計算は Pegasus generic dispatch (起動器は md_17 の launch_cicada_run.py を job dir へ写して拡張、Codex author)、受入は tools/dev_wave_wait.py acceptance。
分割: D (診断 patch + 起動器拡張) → 実測 → 段 2・3 → 段 4 → X (CCBench branch の fix + patch file) と V (起動器の確認 job 追加) → 段 6。
