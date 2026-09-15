---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-15
wave: dev-wave-t2625-sealed-snapshot-qualification
seq: 1
title: [T-2625] sealed snapshot の実 CMake qualification を計算ノードで取り、driver と機構の実在欠陥 4 件を閉じた (コード + docs、branch worktree-dev-wave-t2625-sealed-snapshot-qualification、変異 matrix = baseline 緑・11/11 KILLED・SURVIVED 0・MISMATCH 0・期待 node 完全一致)
---

## 本文

D1439(c) の artifact を取った。job 999363.nqsv (bnode001)、`overall=true`、check 59 件すべて緑、
赤 0 件、3 build case 完走。**投入前に合否基準 (overall=true・赤 0 件・3 label 完走) を固定してから
走らせた。** 詳細と限界は insight `output/insights/2026-09-15_t2625-sealed-snapshot-qualification/`。

**qualification が一度も走っていなかったため、実走でしか出ない欠陥が 4 件あった。** 4 回投入し、
毎回さらに奥へ進んだ (configure → build options → 封止 session → 封止内の実 build)。

1. 依存 prefix 不足で masstree 事前構築の configure が gflags 不在で落ちた (供給側の不足)。
2. `stock_common` の 2 case が base dir と dependency receipt の対必須検査に抵触し build 前に死んだ。
3. 条件 gate の supply-effectuation に offline 供給が届かず configure が失敗した。
4. 封止内の書込みが EROFS でなく EACCES を返した / oracle 束縛 configuration の src_token が
   必ず食い違った。

4 の後者は [T-1994] 以前からある機構側の限界で、**封止 snapshot は oracle 束縛 configuration を
通せなかった**。呼び出し元から再導出まで contract id を通して閉じた。照合そのものは変えていない。

**事前検査が偽の緑を出した。** login node で `find_package(gflags REQUIRED)` が通ったのは、
別 wave の残骸を CMake の user package registry 経由で拾っていたためで、login にも計算ノードにも
system の gflags/glog は無い。CCBench は自前の Find module を module path 先頭に置くので、
config mode の成功は module mode の反証にならない。**事前検査は本番と同じ finder で行う。**

**敵対レビューが親の説明を縮めさせた。** 「`chmod` の EROFS は mount-ro でしか説明できない」
「token 一致は contract id の独立検証になる」はどちらも成立しない。所見は「新たに不正を受理する
経路は見つからない」だったが、射程の限定が要った。insight の「主張しないこと」がその縮約である。

**運用事故 1 件。** 焦点走の dispatcher を detached でない背景 job として起動したところ走行中に
殺され、計算ノードの job だけが生き残って `pending-qsub` の orphan hold が 1 件残った。
この状態では以後の dispatch が全部止まる。手動 `qdel` は別の防壁を武装させるので使わず、
hold 自身が書く手順 (終端確認 → source の clean/HEAD 確認 → 手動削除) で復旧した。
**計算ノードへの投入は必ず detached 経路から行う。**

**非帰属の赤 22 件。** `buildcache.py` は contract-loader 束縛 path で、未 commit のまま焦点走を
かけると `contract-loader-drift` で `test_s1_direct_comparison.py` が全赤になる。実装の回帰ではない。

工数: codex 子 8 本 (plan 1・consult 3・review 2・fix 2、いずれも gpt-6-astra / medium)。
計算ノード job は qualification 4 回、焦点走 3 回、変異 4 回 (probe 2 + 本走 2)。

## 次の一手差分

### 完了

- [T-2625] D1439(c) の artifact を計算ノードで取得した (job 999363.nqsv、`overall=true`、赤 0 件)。
  remaining: none
  base: ffbbe989c1173e19496c2f2565eaecf96d71d213dd30d743ed5d6d618172cd32
- [T-1994] sealed snapshot の実装に加え、D1439(c) の qualification artifact も取得した。
  封止 snapshot が oracle 束縛 configuration を通せなかった機構側の限界も閉じた。
  remaining: none
  base: 3c9138d331d5f02c07002bf0b944b5bffaf92d2f61e9151da6ad2223a9e4cb54
