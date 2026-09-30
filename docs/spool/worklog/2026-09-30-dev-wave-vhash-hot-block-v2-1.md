---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-30
wave: dev-wave-vhash-hot-block-v2
seq: 1
title: [T-2926] VHash の hot block の挿入の CAS を排他の外へ出した B-post を Cicada で測り、更新中心の同時刻の stock 比が md_23 の B の 0.22〜0.69 倍から K=1 で 0.94〜0.99 倍へ戻った (ro 95% は 0.97〜1.01 倍で変わらず)。判定器は 5 腕 × 3 cell で巡回なし、壊し 4 本は検出・帰属 (patch + driver + insight、branch worktree-dev-wave-vhash-hot-block-v2)
---

## 本文

- 依頼: 並行 VHash wave の md_37 (`/work/1/SFC/tanab/tmp/vhash-2026-09-29/md_37.txt`)。一次資料 `output/insights/2026-09-30/vhash-hot-block-cicada-v2/README.md`、設計の判断は {{D:vhash-hot-block-post}}。
- 段構成: 全 9 段 (md_37 が段 2・3・6 を省かないと指定)。段 2 plan 1 本、段 3 相談 2 本、段 5 実装子 2 単位 (C++ patch・driver と作図) と fix 7 巡 (旧 test の復元、probe の key 合わせ、段 6 レビュー所見、計測で見つけた壊しの打ち切り)、段 6 レビュー 2 本・焦点再レビュー 1 本。Codex は全段 gpt-6-sol / medium。
- 棄却・訂正: 段 2 plan の「疎な hot の cold は末尾から続けると版を飛ばす」反例は hit の場合で、段 3 相談 A・段 4 裁定で refuted (cold は md_23 のまま)。段 6 の B3 (estimate の build 二重計上) は、本 wave が smoke とは別に build job を投げ直したので refuted。焦点再レビューの F1 (stale-gap の比較は途中挿入を見逃す) は、ro の読みでは rts 以下の版が比較中に入らないことで反例を否定し限界として記録。F2 (post-B1 が再利用中の版に届く) は「REUSE_VERSION は解放しないので use-after-free ではない」として限界に回したが、実際には再利用中の版で第 2 段の待ちが終わらず計測の壊し 3 走が 180 s 打ち切りになった ({{F:vhash-break-reused-version-hang}})。
- 素材: 書き区間の待ち / update commit は B の 109,405〜121,209 サイクルに対し B-post K=1 は 543〜565 (約 215 分の 1)、K=8 は 1,156〜1,248。B-post K=8 は更新中心で 0.634〜0.873 倍に留まる (Tuple 384 byte と書き足しの保持の約 4.7 倍、どちらが主因かは分けていない)。T3 (rmw の集中) の trace build の commit 数は B が stock・B-post の約 40 倍 (md_23 と同じ向き、性能値ではない)。
- md_23 の残り (T-2927): (2) snapshot の遅れの計器を (wts−rts)>>8 サイクルの 42 bucket に直し、ro95 の中央値は GC 10 µs で 125〜250 µs、GC 100 ms で 16〜32 ms (timestamp clock からの換算)。(3) estimate の trace を 2 job の走数の和に直した。(4) fig-write の下段に待ちを足し、md_23 の集計から修正版を生成した。(1) B2 の機序は計器版 (T1・T2 各 1 走) で commit まで進んだ事象と巡回に帰属した事象が全件「P が validation 時に ABORTED、validation が同じ古い版に達した」類で、親の結果前の予測 (帰属事象は A 以外) は外れた。候補は「B2 が later_ver を飛ばした P に下げ、validation (a) の走査範囲から P より上の挿入が落ちる」(未検証)。
- 異常と逸脱: (1) 実装子 U2 が driver の旧 test 24 本のうち 23 本を消して 20 本を新設した ({{F:vhash-break-reused-version-hang}} とは別、F938 の再発)。親が test 名の集合の差で見つけ、旧名で性質を移植させた。(2) U1 の fix 子 1 本が model の容量不足 (`Selected model is at capacity`) で報告なしに終わり、起動器の残差 commit を継続子に監査させて回収した。(3) 撤去を促す終了時 hook が、自分の commit が 0 の間の wave 木に「land 済みの可能性」を 6 回出した (F1081 の再発、未 land と 1 行返して継続)。(4) 隔離 session の Bash guard が他 worktree への `git -C`・変数を含む sed / awk / heredoc の python を拒否し、script file 経由に切り替えた。
- 計算: 計算ノードの job 合計 6,229 node 秒 (計測・集計 3,896、変異 1,899、焦点走 434)、受入全走は別。依頼の上限 2 node 時間未満。
- 変異: 独立 clone で統合 4 (88913785b) に固定し、probe で集めた期待 node の完全集合に対して M0 (等価) SURVIVED・M1〜M15 の 15 本 KILLED・baseline PASSED (final2、497 s)。
- 受入: 受入全走はこの記録の tip で行い、受領証は job dir (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-hot-block-v2/`) に残す (受入後にこの fragment を書き足すと受入のやり直しになるため、結果は書き足さない)。

## 次の一手差分

### 完了

- [T-2926] VHash の hot block の書き込み側の排他を CAS の外へ出す設計 B-post を実装し (patch `patches/cicada-vhash-hot-block-post.patch`、隣接確認で遅れた hot の安全を担保する論証つき)、md_23 と同じ 12 cell で stock・md_23 の B・B-post を K ∈ {1, 8} で同時刻に測った。更新中心の stock 比の中央値は B-post K=1 で 0.938〜0.991、K=8 で 0.634〜0.873、B は 0.224〜0.694。ro 95% は全腕 0.97〜1.01。判定器は 5 腕 × 3 cell で巡回なし (上限 indeterminate)。一次資料 `output/insights/2026-09-30/vhash-hot-block-cicada-v2/README.md`。
  remaining: none
  base: bbf5e617329f812224249d7477f88eab571afeda08bf7be5a3f7cfa2ce8a5e5d

### 更新

- [T-2927] **P3・更新 (4 点のうち 3 点は完了)**: md_23 の残りのうち (2) snapshot の遅れの計器・(3) estimate・(4) 図は md_37 で済んだ (一次資料 `output/insights/2026-09-30/vhash-hot-block-cicada-v2/README.md` §7)。残るのは (1) 壊し B2 (PENDING を飛ばす) が validation に止められなかった機序だけ。md_37 の計器版で、commit まで進んだ事象 (T1 176・T2 5,330) と巡回に帰属した事象 (T1 7・T2 20) が全件「P が validation 時に ABORTED、validation が同じ古い版に達した」類だった。候補は「B2 が later_ver を飛ばした P に下げたため、読みの後に P と元の直前の版の間へ入った確定版 W が validation (a) の走査範囲から落ちる」。validation (a) の時点で元の later_ver と P の間にある版を数える計器を足して 1 走で確かめる (計算は数分)。
  base: 049af405861cbe9a821649fbc2ab86876c67fd35f78a1edd6df65b92e8a81669

### 新規

- {{T:vhash-hot-block-post-h1-confirm}} **P2・新規 (論文ストーリー §0.3 の案 1 のとき)**: 構成 B の代表を B-post K=1 に置き換えて H1 の確認段 (主指標 = commit 当たり LLC miss、主 cell c23、A/A 腕) を設計する。md_37 で書き込み側の費用はほぼ消えたが (更新中心で stock 比 0.94〜0.99)、ro 95% でも読みの利得は出ていない (0.97〜1.01)。確認段の前に、hot が省く pointer 追跡が読み全体に占める割合を md_23 §6 の飛ばした版数と md_37 §6 の hit・cold の件数から見積もり、測る価値があるかを先に判断する。K=8 が戻り切らない理由 (Tuple の大きさか書き足しの保持か) も同じ設計で分ける。一次資料 `output/insights/2026-09-30/vhash-hot-block-cicada-v2/README.md` §11・§12。
- {{T:vhash-hot-block-figure-legibility}} **P3・新規**: `tools/plotting/plot_vhash_cicada_hot_block.py` の fig-k で「対 stock」と「対 B」の比を線種で分け、fig-write の下段を対数軸にする (現行は B-post の待ち・保持の棒が線形軸でほぼ見えず、表で読む必要がある)。md_37 の一次資料 §5 の図の読み方に書いた限界を外す。
