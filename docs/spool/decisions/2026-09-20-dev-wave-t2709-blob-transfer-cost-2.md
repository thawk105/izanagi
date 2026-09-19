---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-20
wave: dev-wave-t2709-blob-transfer-cost
seq: 2
---

## {{D:t2709-blob-transfer-measured}}. t080 fixture の「必要 blob だけの移送」は計算ノードで base 1 回 −1.68 秒の改善候補と実測したが、本 wave では fixture を変えず採否をユーザー裁定へ返す

**決定:** D2068 (C) の「効果の符号が未確認」を、次の実測で置き換える。
計算ノード bnode007 (local xfs `/tmp`、受入と同じ置き場) で同一 fixture に対し 5 round 交互に測った base 1 回の index 化〜commit〜
production 形 status の合計は、現行 A (`git add -A`) 10.978 秒、C1 (source 側で OID を選定し blob だけを pack で移送してから `add -A`)
9.296 秒、対差は 5 round とも負 (中央値 −1.682 秒)。結果を見る前に登録した規則 (median ≤ −1.0 秒 かつ 4/5 round で負) により
**改善候補**である。ただし fixture 本体は変えず、採否 (採用 wave / 見送り / D2086 の proto 化と束ねる) はユーザー裁定に委ねる。
一次資料は `output/insights/2026-09-20/t2709-blob-transfer-cost/README.md`。

**理由:**
- 起票文の「削減分 79〜191 秒」は login の外乱値であり、計算ノードでは A の `add -A` は 10.65 秒である (C1 の add 2.15 秒との差 8.5 秒は
  pack 既在で loose 生成を省く説明と整合するが内部内訳は未分解)。index 化を 0 にしても base 1 回 11 秒しか減らない。
- 「index-info で 0.61 秒」に相当する index-info + write-tree + commit-tree は 0.26 秒だが、参照 index を無料で使い複製済み worktree を
  変更せず空 stat の index を `update-index --refresh` で保存する経路 (C2、参考費用) は refresh 2.09 秒と移送 (pack-objects | index-pack、
  19,686 blob / 165 MB) 6.5 秒が乗って 8.9 秒である。selftest で `GIT_OPTIONAL_LOCKS=0` の production 形 status が index を書き戻さないことを
  確認した。C2 は他の自己完結経路 (`checkout-index -u` で blob から再配置する等、未測定) の下限ではない。
- C1 の同値性は「fixture の必要な観測」に限定して検査した: tree / commit / 到達 object 集合の一致、production 形 status が空、
  移送 pack は blob のみ、実 receipt の recorded commit 5 件は missing、参照を隠した複製先で status 空・blob 全件 present、
  content / mode / submodule 内の変更検出。alternates は作らないので D2068 (B) の prune 問題も無い。
- 効果量は base −1.68 秒、fixture 全体の test copy −0.74 秒 (測定条件内)。受入 wall の変化と D357 / D1260 の達否は未測定で、それを
  採否の根拠にしない。今回の効果量に対し、fixture 本体の実装差分・変異登録・実受入の対比較という検証費用が大きいので、親の一存では
  採らず推奨は見送り。
- 副産物として、test 用に `copytree` した複製先で production 形 status を連続 2 回走らせると 2.147 / 2.14 秒だった (元 fixture では 0.06 秒。
  再走査件数・実テスト内の回数・refresh 後は未測定)。scope 外なので裁定パッケージ候補として README に記録し、起票しない。

**却下した選択肢:**
- 「符号確認済み・全体不採用」と書く — 測ったのは 1 設定・1 集合・1 環境での C1 であり、改善候補の側である。D2068 (C) への追記は
  限定文 (bnode007・local xfs・source tip b7f970dfa・`--window=0 --depth=0` の C1 が 5 対の中央値差 −1.682 秒、5/5 負で事前登録上の
  改善候補。受入 wall、cold、48 worker 競合下、他の自己完結経路は未評価) のまま転記する。
- 改善候補だからと fixture を変える — 今回の効果量に対し実装差分・変異登録・実受入の対比較の費用が大きく、採否はユーザーの判断に委ねる。
- per-base の差を受入 wall の改善として記録する — D357 は wall の反復走の中央値でしか改善を認めない。
- 事前登録の閾値を結果を見てから動かす — 規則は段 4 で固定し、n < 3 の縮退だけを本走前に追記した。
