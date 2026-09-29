---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-29
wave: dev-wave-t2872-mocc-g2-split
seq: 1
title: [T-2872] MOCC read-heavy の stock の G2 を切り分け、validation の版の読みと lock 状態の読みの間に他の取引の公開と解錠が入る MOCC 本体の欠陥と判定した。trace 無しの build で 112 走すべてに観測、G2 5 件のうち 2 件は直接一致・3 件は推論で帰着 (insight のみ、branch dev-wave-t2872-mocc-g2-split)
---

## 本文

- 一次資料: `output/insights/2026-09-29/t2872-mocc-g2-split/README.md`。repo のコード変更なし。計器 (診断 patch) と runner は Codex author が job dir `/work/1/SFC/tanab/tmp/t2872-mocc-g2-split-20260929/probe/` に書き、repo に入れていない。G2 の 5 run の保全は `/work/1/SFC/tanab/izanagi-repro-archive/t2872-mocc-g2-split-20260929/` (2.4 GB、`MANIFEST.sha256`)。
- 計算: 計算ノード 6 job、Elapse 計 6,686 s = 1.86 node 時間 (smoke 4 回 358 s + 本走 2 job 6,328 s)。本走の条件は smoke の所要だけを見て結果の前に固定し、walltime 上限でも 1.97 node 時間でユーザー確認の線 (2 node 時間) の内側に収めた。本走は全 28 batch を完走 (欠測 0)。
- 段の経過: 段 2 plan・段 3 相談 2 本 → 段 4 で所見をすべて real (親 brief の計器は lock 読みの後の再読を窓の観測に使っていたので、窓の中の再読 Vmid を足した)。段 5 author は 1 回目が model の混雑 (at capacity) で途中終了し、継続投入で完成。段 6 は親の監査 must-fix 4、read-only レビュー must-fix 3・should 2、smoke の実測欠陥 3 (compile 命令が 4 target 分、前処理の比較が空行を含む、`-Werror=sign-compare`) を fix1〜fix4 で直した。smoke は 1 投入 1 欠陥で 4 回目に完走。事実の再抽出レビュー 1 本の所見 5 件 (行番号 1 件、R2 未達の表記ほか) を採用して本文を直した。変異 matrix は repo の実装面の差分 0 で免除。
- セッション異常: EnterWorktree が name 形で「git config を読めない」、path 形で worktree 一覧の 10 秒上限に 2 回掛かり、絶対 path で作業した。16:19〜16:34 はユーザーの git push のため、land 調整役の依頼で git 書き込みを止めた (fix4 の再投入をこの間待った)。fix4 の 1 回目は親の prompt の path の誤り (`rwlock.hh` の置き場) で子が即停止した。

## 次の一手差分

### 更新

- [T-2872] **P1・切り分け済み (本体の欠陥) → 修理 (AI、CCBench 側は Codex author・CCBench の CI を通す)**: MOCC の read-heavy (48 thread・1,000,000 record・rr95、pin C) の stock の G2 は、validation が版の比較と lock 状態の検査を別の load で行う隙間に、他の取引の公開と解錠が入って両方が commit する MOCC 本体の欠陥と判定した (`output/insights/2026-09-29/t2872-mocc-g2-split/README.md` §0・§7)。trace 無しの build でこの割り込みの commit を 112 走すべて・計 4,284 件観測し、trace 有りの build の G2 5/112 走の witness は 2 件が直接一致・3 件が推論で帰着した (一致なし 0)。
  - 裁定 (D2277 項 2、ユーザー): read-heavy は比較に普通に使い、MOCC の欠陥は直す。t2849 の read-heavy の値は pin C の MOCC の上の測定として有効 (規律 7)。論文ではこの cell の stock に G2 が出たことを事実として書き、原因は本体の欠陥と書ける (上限は insight §6)。規律 2 は不変。
  - 残り (AI): 修理。最小案は validation の read set 走査で lock 状態の検査の後に版を読み直し、最初の版と違えば abort し、`max_rset_` は検査した版から取る (順序の入れ替えも候補、上流 Silo の検査と照らして決める)。検証は本 wave の計器と cell で、commit 側の class A が 0・trace 有りの 112 走で G2 0 を確かめる (計器と runner は job dir に保存済み)。CCBench の CI (build・clang-format 14) を通し、T-2854 の整形 commit と同じ file なのでその後 (C2' 系) に乗せる。pin 前進は D2277 項 1 の順序、修理後の版で測り直すかは修理が pin に入る時点で示す。上流への追加報告・PR は人間の判断 (D16)。
  base: 7d50f9155e4c403480afcbe98aaea66d45fdac7ceb74b3a2f1221255af6949f9
