# 段 1 brief — md_32 cicada-promotion-uaf-fix (2026-09-30、親)

依頼: /work/1/SFC/tanab/tmp/vhash-2026-09-29/md_32.txt (共通指示 common.txt)。台帳 item: worklog の [T-2922] (promotion) と [T-2925] (abort の UAF)。
wave 木: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-promotion-uaf-fix (branch worktree-dev-wave-cicada-promotion-uaf-fix、起点 = local main 4f412c67b)。job dir: /work/SFC/tanab/tmp/cicada-promotion-uaf-fix-2026-09-30/。

研究前進: VHash 論文の比較相手 Cicada の探索空間 24 genome のうち promotion 有効の 8 genome が失格で、比較・md_11 の較正の空間から外れている。完了判定 = 修理後の tip で 8 genome が build でき、YCSB K・W・R・P と TPC-C M・R2 の小走行で判定器の巡回 0 (上限 indeterminate)、TPC-C が繰り返し完走し、同じ job の修理前の再現 (巡回あり・異常終了) と対になる。UAF は ASan の実行中 `ERROR: AddressSanitizer` 0 件 (修理前は検出) で閉じる。

既裁定: 基盤の欠陥は比較から外さず直して使う・上流 CI (Release 全 protocol build と clang-format 14 --dry-run --Werror) を通す品質 (D2277 項 1・2)。直列化可能性を緩めない (規律 2)。push・pin 前進・branch のまとめ方は人間 (D16、T-2921・T-2924)。izanagi の gitlink・pin.py・md_29/md_31 の所有物に触らない。再計測 (md_11 の空間へ戻す) は別 item。計算は合計 2 node 時間未満、md_18・md_29・md_31 と同じノードで計測しない。

原因の仮説 (親の静的読み、攻撃対象):
- (P1) 巡回: `read_internal()` (G の transaction.cc:79-137) は読み取り専用 tx では `rts_` で可視版を探し、`later_ver_` を rts 基準で記録する。promotion (transaction.hh:200-214) はその tx を途中で読み書き tx (`is_ronly_=false`) に変え、commit は validation に回る。validation の読み取り再検査 (transaction.cc:538-570) は `later_ver_` を出発点に `wts_` 未満まで下るが、rts 基準の `later_ver_` は wts 未満でありうるので、それより新しい wts 未満の確定版を飛ばす (`later_ver_` が aborted のとき ver_ まで下りて通る)。観測との整合: 巡回は読み取り専用 tx が多い R (327) > K (4)、読み取り専用が無い W と promotion が起きない P で 0。原論文 §3.3 は promotion を「可視版として読んだ非 inline 版を RMW へ格上げ」と書き、rts で読む読み取り専用 tx の格上げは書いていない (§3.2 は読み取り専用 tx は読み取り集合を検証しない)。
- (P2) TPC-C の bad_alloc: 候補は (a) promotion が書き込み集合に旧 body の写しを積んだ後、同じ tx の本来の `update()` が `searchWriteSet` で素通りし (transaction.cc:205) 書き込みが消える、(b) INLINE_VERSION_OPT=1 の abort で UAF (下の P3) が解放済み tuple の inline 版 status へ書きヒープを壊す、(c) 版本体の写し (`TupleBody(ver->body_)` の deep copy) と回収・再利用の競合。どれも未検証。帰属は実測 (ASan/Debug build の最初の報告、例外送出点の backtrace、候補ごとの使い捨て回避 patch の on/off) で決める。
- (P3) UAF: `abort()` (transaction.cc:745-754) が INSERT の tuple を delete した後、`writeSetClean()` (transaction.hh:343-368) が `rcdptr_->continuing_commit_` と (OPT=1 なら) inline 版 status に書く。Tuple は版を所有しない (tuple.hh、destructor なし)。直し方の provisional 裁定 = abort で索引から外す → writeSetClean → 最後に tuple を delete (writeSetClean は変えない)。
- (P4) 土台: 新 local branch を G `eb93423b` と gc_records 修理 tip `81fc4a84` の merge (衝突なしの見込み、G は transaction.hh:207・210 と transaction.cc:131・924-925、gc 修理は transaction.cc:432・849 付近) から切り、修理 commit をその上に積む。理由: TPC-C (Delivery 以外でも) の UAF 確認と今後の比較は両方の修理を要し、merge は両 branch の SHA を保つので人間は 1 本でも 2 本でも push できる (cherry-pick は同内容の別 SHA を作る)。
- (P5) D297: 検査器は cicada の transaction.cc の変更で fails-closed する (前 wave §6)。変更を cc/cicada/ に限り、F→新 tip の非 cicada path の差分 0 を git で示し、選定文脈は T-2854 の C→F 判定を引き継ぐ (推論と明記)。検査器を 1 回走らせて拒否の rc を記録する。cicada の変更は意図した差分として範囲を書く。

不変条件: 修理は非既定の promotion 経路と abort 経路だけを変え、既定 genome の意味を変えない (既定文脈の前処理比較で確かめる)。計装 patch (instr-cicada-trace・-tpcc) は新 tip に fuzz なしで当たる (当たらなければ repo 外の適応版で走らせ、そう書く)。promotion 中の trace は前 wave と同じ repo 外の診断変種 (`#error` を外す) で取り、標準の計器ではないと書く。判定の受理 = rc∈{0,3}・巡回 0・integrity 数値項目 0・C 行 = commit 数・READ_WTS_MISMATCH 0 (integrity.clean は使わない)。ASan は detect_leaks=0。

成果物: CCBench の新 local branch と修理 commit (submodule 側、Codex author・親 commit)、patches/broken-cicada-promotion-*.patch (promotion の誤りを狙う無条件の壊し、修理後 tip → 計装 → 壊しの順、ledger.json には登録しない先例どおり) と patches/README.md の節、一次資料 output/insights/2026-09-30/ccbench-cicada-promotion-uaf-fix/README.md、spool fragment (T-2922・T-2925 の完了/更新、push の人間手番、再計測の新 item)。

分割方針: 段 5 は 2 段。単位 D (診断、repo 外の job script + 使い捨て計器 patch、Codex author) → 親が帰属を裁定 (段 4 追補) → 単位 F (CCBench の修理 2 件、submodule の子木) と単位 X (壊し patch + 確認・CI・ASan の job script) を並列。帰属しない修理は入れない。
