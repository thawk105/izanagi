---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-23
wave: dev-wave-t1520-receipt-survives-main-merge
seq: 2
---

## {{D:forward-merge-replay-instrument}}. 受入受領証を跨ぐ main 前方取り込みは、隔離した機械 merge の再演と tree の完全一致で検査する

**決定:** D689 が要求する「取り込み前後で wave 自身の内容が変わっていないこと」の検査を、
差分の比較ではなく **隔離した一時 repository で機械 merge を再演し、その tree OID が
実際の merge commit の tree と完全一致すること**で行う。再演は協調 lock の外で済ませ、
lock 内では SHA の同一性と祖先関係だけを再確認する。

**理由:**
- **差分の比較は実データで成立しない。** main の実履歴にある正当な取り込み
  (衝突なし、`f3c27afb`) で測ると、`git diff` の生 byte 比較も
  `git diff-tree --raw` の byte 比較も不一致になる。原因は `index` 行の blob OID が
  両側とも変わることで、main と wave が同じ file を触れば必ず起きる。
  `docs/dev-wave/operations.md` や台帳のような多数の wave が触る file では稀ではない。
  素朴に実装すると**受理される取り込みがほとんど無くなり、律速はまったく解けない。**
- **patch-id は空白を無視する。** この機体の git は 2.34.1 で、空白を無視しない
  `--verbatim` が無い。patch-id を同一性判定に使うと、wave 側の内容を空白だけ書き換えた
  改変が素通りし、D689 が必須と定めた負の対照が恒真化する。
- **tree 比較でも表現できない。** 取り込みによって wave 側 file の中身自体は変わる。
  変わらないのは wave の寄与だけである。
- 再演なら、text/binary の 1 byte・file mode・symlink・submodule gitlink のいずれの改変も
  blob OID か tree entry の mode に現れて拒否され、衝突する取り込みは再演 merge の
  非 0 rc で拒否される。判定は patch の表現に依存しない。
- **再演を lock の中で行ってはならない。** 初回の作業ツリー展開に 22〜29 秒かかる。
  再演の入力はすべて不変の SHA なので lock の外で確定でき、直列化を減らす変更が
  直列化を増やす事態を避けられる。

**却下した選択肢:**
- **patch text から `index` 行だけを外して byte 比較する** — main が同じ file の前方へ
  行を足すと hunk の行番号がずれ、正当な取り込みをなお拒否する。実例で偶然ずれなかっただけで、
  D689 の意味を patch の表現の偶然に寄せすぎる。
- **main が触った path だけ 3-way merge を再計算して照合する** — 内容しか照合しないため、
  同じ bytes のまま file mode を実行可能へ差し替えたり symlink と通常 file を
  入れ替えたりする手製 commit が通る。rename・delete/add・gitlink・attributes の
  merge driver も 1 つの低水準 merge では再現できない。
- **受領証の schema を上げて取り込んだ main の列を受領証自身へ書く** — 受領証を著すのは
  tested main 側の blob から実行される launcher であり、新しい版の launcher は
  main へ着地するまで実行されない。受領証は旧版のまま出て新しい land がそれを拒否するため、
  **自分の変更が自分の着地を塞ぐ。** 取り込んだ main の列は land が git から独立に導出し、
  結果 JSON と worklog へ記録する形にした。

## {{D:forward-merge-accepted-shape}}. 前方取り込みで受理する形を、段数・起点・merge 設定の 3 点で縛る

**決定:** 受領証を生かしたまま受理する前方取り込みを次の 3 点で縛る。いずれも受理集合を
狭める方向であり、緩和ではない。

1. **段数に定数上限を置く** (現行 8 段)。超過は fail-closed で拒否する。
2. **初段が tested main の子孫であることを要求する。**
3. **merge 結果に影響する git 設定が、両 worktree のどの origin にも無いことを要求する。**

**理由:**
- **段数**: 取り込んだ main の列は land の結果 JSON に載り、その JSON は 64 KiB 上限を
  受入の赤 nodeid と食い合う。上限を超えると peer 通知が fail-closed で落ちる。
  縛らないと「取り込みを重ねると通知が落ちる」経路ができる。
  実履歴の連続取り込みは 1 段 105 列・2 段 23 列・3 段 3 列・4 段 1 列で最大 4 段であり、
  上限 8 は観測最大の 2 倍にあたる。
- **起点**: 2 段目以降は main の単調前進を確かめていたが、初段は取り込む main と
  tested main の関係を見ていなかった。tested main の祖先から分岐した commit を main に据えると、
  再演の tree は一致し lock 内の検査も通るため、**受入でテストしていない系統を着地できた。**
  従来経路は「main が tested main を含む」ことを要求しており、新しい経路だけが
  この保護を落としていた。2 つの独立した敵対レンズが同じ穴を指摘した。
- **merge 設定**: 親の `git merge` は local/global/system の設定を読むが、再演は
  空 repository で global/system を無効にして走る。renormalize・rename 系・attributes・
  低水準 driver が設定されていると、正当な取り込みの過剰拒否と、
  親では衝突するが再演では clean になる手製 commit の過小拒否が同時に起きる。
  どちらも「親の merge が衝突なく通った」という受理集合の定義と食い違う。

**却下した選択肢:**
- **段数を縛らず結果 JSON から列を外す** — D689 は取り込んだ main を事後に追えることを
  実装条件に挙げている。列を落とすとその条件を満たさない。
- **設定の食い違いを再演側の設定を親に合わせて吸収する** — 親と再演のどちらが正かを
  決められないまま受理集合が環境依存になる。存在自体を拒否するほうが定義が明確である。
