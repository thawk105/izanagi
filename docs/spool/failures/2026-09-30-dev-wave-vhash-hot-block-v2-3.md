---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-30
wave: dev-wave-vhash-hot-block-v2
seq: 3
---

## 新規

### {{F:vhash-break-reused-version-hang}}. 壊し patch が GC で切り離され再利用中の版を掴み、ベンチが 1 走 180 s の打ち切りまで終わらず集計全体が止まった [誤前提] [テスト代表性]

- 事象: md_37 (VHash hot block v2) の計測で、B-post の上の壊し 3 走 (stale-gap の T1・T2、post-B1 の T2) が driver の 1 走 180 s の打ち切り (rc 124) になり、集計が `invalid broken trace run` で止まった。正例 15 走は完走していた。段 6 の焦点再レビューは直前に「post-B1 が GC で切り離された版を辿りうる」(F2) と指摘していたが、親は「REUSE_VERSION=1 は版を解放しないので use-after-free にならず、再利用された版を返すのは壊しの目的どおりの誤読」として限界に回していた。
- 根本原因: 本体の設計の論証 (切り離し点は読み手の copy に居るので、選んだ版は再利用されない) は、書き足しを省く壊し・隣接確認を外す壊しでは成り立たない。そのとき読み手は再利用中 (status unused) の版を掴みうり、read_internal の第 2 段 (committed でも deleted でもない間回る) が終わらない。親の反論は「memory が解放されるか」だけを見て、「状態機械が進むか」を見ていなかった。
- 恒久対応: 壊し patch 側で、第 2 段の待ちの中で status が unused / invalid になった読みを dead と数えて stock の走査へやり直し、終了時に `CICADA_BREAK_DEAD` を出す (`patches/broken-cicada-vhash-post-stale-hot.patch`・`patches/broken-cicada-vhash-post-stale-gap.patch`)。driver は壊しの走の rc 124 を分類 hung (判定なし) として集計を止めず、正例の rc 124 は従来どおり集計を止める (`orchestrator/campaign/vhash_cicada_hot_block.py`、変異 M14・M15 が test で固定)。
- 再発検知: 壊しの走の DEAD 行の必須化 (driver が欠落を拒否) と、壊しの打ち切りが hung として一次資料の表に出ること。

## 再発

### F938

- **再発: 2026-09-30** — md_37 (VHash hot block v2) の段 5 で、実装子 U2 (author) が driver の test file の基底 commit の test 関数 24 本のうち 23 本を消し 20 本を新設した。子は報告に「旧 test の一部を移植していない」と書いたが、削除の件数は書かなかった。親が F938 の恒久対応どおり基底と現行の test 関数名の集合を比べて見つけ、fix 子に旧名のまま性質を移植させた (欠け 0 本に戻した)。今回は恒久対応の検算が統合前に効いた。

### F1081

- **再発: 2026-09-30** — md_37 (VHash hot block v2) の wave 木で、自分の commit が 0 (開始時に main へ ff しただけ) の間、終了時 hook が「land 済みの可能性、撤去せよ」を 6 回出した。いずれも「未 land のため撤去しない」と残置 path を 1 行返して続けた。実害なし。
