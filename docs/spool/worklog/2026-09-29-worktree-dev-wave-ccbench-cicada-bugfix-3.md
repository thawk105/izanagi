---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-29
wave: worktree-dev-wave-ccbench-cicada-bugfix
seq: 3
title: [T-2904] CCBench Cicada の build 不具合 2 件と計器 build 1 件を F の子 commit G で直し、24 genome と W5 が build でき上流 CI 2 本を手元で通した。promotion 有効の genome は判定器が直列化違反を検出し TPC-C で異常終了したので 8 genome とも失格、D297 検査器は cicada の変更を判定できない (insight + spool fragment、CCBench local branch izanagi-cicada-build-fix、branch worktree-dev-wave-ccbench-cicada-bugfix)
---

## 本文

- 依頼: md_19 (VHash の並行 wave の 1 本)。ユーザーの判断「CCBench の不具合は直したい」で [T-2904] の還元判断を「直す」で確定した ({{D:ccbench-cicada-build-fix}})。md_19 の項目 3 (TPC-C の gc_records の ERR、[T-2908]) は、後から作られた専用依頼 md_23 の session が分担を申し出たので、md_23.txt の実物 (21:35 作成、md_19 は 21:30) を確かめて譲った。本 wave は [T-2908] に触れていない。
- 結果の要約は一次資料 `output/insights/2026-09-29/ccbench-cicada-bugfix/README.md` §0。G = `eb93423bbb27a2694d3d75861696c365f0fb8f7c` (F `25898d00` の子、cc/cicada の 2 file・5 行置換、物理行数不変)。push していない。
- 工程: 軽量版 (段 2 省略)。段 3 相談 2 本、段 6 レビュー: 修正に 2 本 + 焦点 1 本、検証 script に 2 本 + 焦点 1 本。Codex 子は相談 2・author 2・fix 4 (A2・B2・B3・B4)・レビュー 5 (うち 1 本は親の投げ文の path 誤りで不受理、F819 の再発)・焦点 2。計算ノード job 6 本 (build+CI、trace、判定 2 回、診断 1) で合計 1 node 時間を大きく下回った。
- 段 6 で閉じた親の誤り: (1) 「物理行数が同じなら既存 patch は当たる」という予測 — 実装子が未使用引数を無名にし、計装 patch の hunk の文脈行が変わって当たらなくなる所をレビュー B2 が検出した (引数名を戻して解消)。(2) 段 4 裁定で判定 job の path 照合を「C→G = 5 file」と書いた — T-2854 の判定 job が照合していたのは直親 → 新 tip の path で、実測は C→G = 6 file・F→G = 2 file。判定 job 1 回目は入力照合で 5 秒で止まり、検査器は起動していない (裁定追補 1 で訂正)。(3) G の 1 回目の commit message が「重複要素は scan() で 2 回返されていた」と言い過ぎた — 検証に使う前に branch を消して message だけ直した (tree は同じ)。
- 検証 script の偽の緑をレビュー SA・SB が 6 件・起動失敗 2 件検出した (空 trace が合格になる、compile 時の -D と走行時の flag を照合しない、CI の合格条件が rc だけ、repo root の推測、Python の版、一時 build の置き場)。すべて投入前に fix して焦点再レビューで closed。
- 起動器の後処理 (子 worktree の残差の commit) が fix B3・B4 で `add-all` の失敗を 2 回返した (起動器 rc=3)。Codex 子自体は completed で、子の編集は gitignore 下の script だけ、子 worktree は clean だったので実害はない。原因は調べていない。
- W5 の throughput の事前予測 (2 thread・待機なしは 1 thread の約 2 倍、100 ms 待機で 1 thread と同程度) は大きさが外れた (1.14 倍、1 thread より 35,000 件前後少ない)。待機の実在は trace の thread 別 commit 数で直接確かめた。外れた理由は調べていない。

## 次の一手差分

### 完了

- [T-2904] 還元判断はユーザー判断で「直す」に確定し ({{D:ccbench-cicada-build-fix}})、2 件 (と ADD_ANALYSIS=1 の 1 件) を CCBench の local branch `izanagi-cicada-build-fix` の commit G `eb93423bbb27a2694d3d75861696c365f0fb8f7c` で直した。24 genome と W5 は G で build できる。push とその後、promotion の失格、W5 の測定は新しい項目へ移した。
  remaining: none
  base: b62a74881bf419c5ae6ee9d8ebce940f307777e6a6be8466fa05766282296078

### 新規

- {{T:cicada-build-fix-push}} **P2・人間の手番 (push)**: CCBench の branch `izanagi-cicada-build-fix` (G `eb93423b`、F `25898d00` の子) を主 checkout の submodule から push し (`cd external/ccbench && git push origin izanagi-cicada-build-fix`、別名の新 branch なので force 不要。F が GitHub に無ければ祖先として一緒に上がる)、GitHub の Actions で build・format が緑で GitHub から G を取得できることを確かめる。md_23 の gc_records の修理 branch (同じ F の子) と 1 本にまとめるかはこのときに決める。緑になった後の pin の前進 ([T-2854] の続き) は、(a) D297 検査器が cicada の transaction.cc の変更を「未知 macro の条件指令」で fails-closed に拒否する (一次資料 §6) ので、cicada の文脈 macro の扱い (CONTEXT_MACROS への登録か、cicada の変更を別の同一性検査で扱うか) を先に決める、(b) promotion 有効の 8 genome は失格のまま使わない、(c) patches/ の cicada 系の当たり方は G と F で同じ (一次資料 §7)、を前提にする。資料: `output/insights/2026-09-29/ccbench-cicada-bugfix/README.md` §6・§9。
- {{T:cicada-promotion-anomaly}} **P2・新規**: Cicada の promotion 有効の genome (INLINE_VERSION_OPT=1 ∧ INLINE_VERSION_PROMOTION=1) で、判定器が YCSB K・R × thread 4 に G2 の巡回を検出し (4 件・327 件)、TPC-C M・R2 × thread 4 が `std::bad_alloc` で異常終了した (G `eb93423b`、計装は `#error` を外した診断変種)。原因を特定してから直す (直列化可能性を緩める直し方は採らない)。一次資料 §5 の切り分け (重複登録を戻しても YCSB K・R の巡回は残る、計装なしでも TPC-C は異常終了する) と、残した raw trace (job dir `evidence/diag-1-kept-trace/`) から始める。直るまでこの 8 genome を比較・探索に使わない。資料: `output/insights/2026-09-29/ccbench-cicada-bugfix/README.md` §4.3・§5。
- {{T:vhash-w5-measure}} **P2・新規 (pin 前進後)**: 読み取り後に待つ長い tx の型 W5 を、pin が G (か G を含む tip) に進んだ後に、較正 wave (`output/insights/2026-09-29/vhash-cicada-baseline-tuning/README.md`) の条件で測る。待ち時間は runtime flag `-worker1_insert_delay_rphase_us` で与え (compile 時定数 `WORKER1_INSERT_DELAY_RPHASE_US` は G では使われない)、`instr-cicada-version-lifetime.patch` の `IZANAGI_CICADA_LONGTX` と同時に有効にしない (worker 1 が 2 回待つ)。本 wave の W5 の throughput は待機の実在の確認用で性能値ではない (一次資料 §4.1)。
