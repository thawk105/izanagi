---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-30
wave: worktree-dev-wave-cicada-certified-m
seq: 1
title: [T-2874] Cicada の正しさの記録を中間案 M に上げた — 読んだ版の回収・公開の記録漏れ・読みの登録漏れを TRACE ビルドで全 tx 照合し、stock・最良設定・E-max の 18 run で違反 0、壊し 3 種を検出 (patch 4 本 + insight、branch worktree-dev-wave-cicada-certified-m)
---

## 本文

- 依頼: VHash 論文の並行 wave md_33 (`/work/1/SFC/tanab/tmp/vhash-2026-09-29/md_33.txt`)。D2305 項 4 で採った中間案 M を実装した。一次資料 `output/insights/2026-09-30/cicada-certified-m/README.md`、設計判断は {{D:cicada-m-implementation}}。
- 段 1 の判断: 最良設定 (`INLINE_VERSION_OPT=1`・promotion 0) を M の範囲に含めた (比較相手の最良設定と E / E-max の実測がこの設定の上にあるため)。inline slot の返却・再取得も照合の事象に入れ、実走で最良設定と E-max の run に inline の事象が 5,648〜2,681,878 件起きた。
- 結果: stock の既定設定・最良設定と E-max の 18 run (異なる条件 16) で巡回 0・M の違反 0。壊し B (P5 型、D2295 で却下した「tx の途中で読み取り下限を最新へ上げる」) は既定設定 3,273 件・最良設定 3,715 件の `B_RETIRED` が下限を上げた tx に全件帰属、壊し U・API は各 1 件が帰属。3 本とも判定器の巡回は 0 (判定器だけでは見えない)。既存の壊し 3 本は M を重ねても巡回を検出した。変異 3 本 (各照合の違反判定だけを無効化) はすべて kill (MV-U は 1 回目に計数ごと止めて別の生存検査が反応したので再照準)。TRACE=0 は 4 target × 2 genome と E-max の M 無し対 M 有りの 10 組で、命令列・relocation 付き逆アセンブル・前処理の空行以外・`nm`・`strings` が一致。
- 論文に書ける文は一次資料 §7。izanagi 内部の判定は indeterminate のままで certified とは呼ばない。B の帰属は tx 単位まで (個々の違反の因果は示していない)。
- 段 2〜4 のやり直し: 検査を新設する wave なので条件節 DW-O13 (最遅 段 2 前) が着手時から成立していたのに読まず、段 5 の前に気づいて段 2〜4 を無効化し取り直した ({{F:endif-after-line-shifts-trace0}} とは別、F440 の再発として記録)。
- 段 6 で実機だけが見つけた欠陥 11 件 (一次資料 §8): offset 付き適用、`git archive` の `export-ignore` による `cc/oze` 欠落 (F1046 の再発)、壊し B の未宣言識別子と未発火、build dir の使い回し、違反行の書式、計数の順序、E-max で insert / delete の hunk が `update` に当たる、`#line` の 1 行ずれ ({{F:endif-after-line-shifts-trace0}})、前処理比較が空行を数える、MV-U の別層 mask。
- 焦点再レビューは 3 巡の上限まで行い (3 巡とも NO-GO)、残った 4 所見は親が実測と文言で閉じた (段 6 裁定 9)。
- 同じ計測用 checkout から 6 本を同時に dispatch して 5 本が rc=16 (起動前の orphan hold) で拒否された。以後は checkout を 3 本に分けて並行させた。
- 途中で利用上限により中断し、ユーザーの「再開して」で続けた。land 調整役から「計算 job は 1 本 5 分程度に分割し多数並行」「2 node 時間超は調整役へ相談」の中継を受けた (本 wave は 22 job・合計約 0.71 node 時間・1 本最大 228 秒で相談不要)。
- 工数: Codex = plan 2 (うち 1 本は無効化)・相談 4 (同)・author 2・レビュー 2・焦点 3・fix 13、Claude sonnet の read-only 調査子 1。計算ノード job 22 本 + provenance 監査 1 本。

## 次の一手差分

### 更新

- [T-2874] **P2・中間案 M は実装済み (一次資料 `output/insights/2026-09-30/cicada-certified-m/README.md`、{{D:cicada-m-implementation}}) → 残りは範囲の拡張と未確認の発火**: Cicada の trace (D2279) は YCSB point read / update に加え、TPC-C を trace v3 で判定器に掛けられる (`patches/instr-cicada-trace-tpcc.patch`、D2294)。M = `patches/instr-cicada-trace-m.patch` (instr の上に重ねる、`#if TRACE` の内側だけ) が B (読み束縛)・U (公開・設置・W 行の照合)・read 側 API 照合を全 tx に掛け、repo 外起動器 (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cicada-certified-m/launcher/launch_cicada_m.py`) が合否を決める。範囲は YCSB point read / update・`REUSE_VERSION=1`・`group_commit=0`・`INLINE_VERSION_OPT` 0 と 1 (promotion 0)。stock の既定設定・最良設定と E-max の 18 run で巡回 0・M の違反 0、壊し 3 本 (`patches/broken-cicada-m-*.patch`) が発火・帰属、TRACE=0 は 10 組一致。D2305 項 4 (2) により、M の照合を満たした設定の TRACE=0 build の性能値は、論文では照合の中身を明記した測定値として扱ってよい (izanagi 内部では certified と呼ばない)。残り: (1) 未確認の発火 = API 照合のうち再読・自分の書き込みの読み・過剰な登録、U 照合のうち設置と公開の照合、版選択から登録までの窓の中の再利用 (いずれも正例なし)。B の違反の個別の因果 (帰属は tx 単位まで)、(2) 検査した run は各条件 1 秒で、主比較の条件 (tuple 100 万・thread 48・3 秒) そのものは走らせていない。主比較の性能値に M の地位を付けるなら、その条件の trace run で M を回す、(3) pin を C から進めたら計装 3 本・壊し 7 本の厳密適用と生死確認の取り直し (E-max stack では M の 18 hunk の当たる関数も照合)、(4) 未対応 = scan の phantom と不在の読み・並行下の delete (stock が落ちる、[T-2908]、修理 2 本 `patches/fix-cicada-gc-records*.patch`)・版昇格 (`#error`)・`group_commit>0`・`REUSE_VERSION=0`・BOMB / SBOMB / TPC-C の M、(5) trace hook は `izanagi-trace` 枝へ移さず patch のまま置く (D2305 項 4)、(6) certified 化 (案 A) は Cicada を門に通す campaign を登録するときに `output/insights/2026-09-29/cicada-certified-evidence-design/README.md` §6 の設計から着手する。
  base: bbd961b36d5a1d9be65dfd97b78d863207c580730272311c2773ce5a8642c0e2
