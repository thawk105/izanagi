---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-24
wave: dev-wave-known-violation-review-20260823
seq: 1
title: known-violation 台帳 53 件を全数監査し、0 件化は現行契約では到達不能と判定した (docs のみ、実装差分ゼロ、branch worktree-dev-wave-known-violation-review-20260823)
---

## 本文

- ユーザー依頼: 「known-violation の見直しをしてください。現在は known-violation は育っていく一方
  でしょうか。すでに知られた violation について、テストされているところが間違えているならそれを
  なおす、テストが間違えているならそれを直すなどして、known-violation を 0 件にする努力が必要だと
  思います。タスクは適切な大きさで切り、適切でない大きさに関しては別途タスクを切り出して先送りに
  してください」。D662 決定 5 が定めた「高優先度タスクとして随時解決する」の実行にあたる。
- **結果: 実装差分ゼロ。撤去件数 0。台帳は 53 件のまま。** 依頼は 0 件化だったが、
  全数を測った結果、現行契約のもとで AI 側の作業だけで消せる entry は 1 件も無いと判明した。
  減らすには機構をユーザー裁定で変えるしかなく、その裁定パッケージを成果物とした。
- **「育っていく一方か」への答えは、はい。** `ast` で各 blob の registry tuple を構文解析し、
  `--first-parent` で main 本線だけを追った結果、件数の変化点は増加 20 回・減少 2 回。
  意味のある減少は 1 回だけで、2026-08-21T22:49 `e0ac92775c` の 53→34 (T-1479 の checker 是正)。
  **44.7 時間後の 2026-08-23T19:29 `bc927d03c4` で 53 へ復帰した。約 10 件/日。**
  生成器を止めずに台帳だけ減らしても 2 日と持たない、という実測である。
- **49 件は履歴が不変である以上どの経路でも消せない。** 最大の塊は 2026-08-09 の単一事故 22 件で、
  trailer literal は全件同一 (`model=claude-opus-5[1m]`、`role=orchestrator`)。
  「規則が後から出来た legacy 被害では」という親の仮説は反証した — 文法 (`IDENT` と ROLES) は
  checker 導入 commit `50c1ef4e` (2026-07-14) から在り、`docs/ai-provenance.md` も違反 commit
  `f277efd446` (08-08) 時点で同文だった。遡及訂正の経路も潰した: `PR-C01` は一回限りで
  `6d7141dc` で消費済み・拡張禁止、waiver は commit 自身の trailer を読むため遡及不可、
  git notes 経路は repo 内に存在しない (全数検索)。
- **敵対 2 レンズの所見 17 件はすべて real、refuted はゼロ。** 親が段 1 で置いた provisional 裁定
  (P1)(P2)(P3) は 3 つとも覆された。棄却できた親の主張が 1 つも無かったのは異例で、
  段 1 時点の実測が gate の母集合を再現していなかったことが原因である (F144 の再発として記録した)。
- **最も効いた反例 (sol レンズ)。** 親と段 2 の子は独立に「全行が親由来かつ全親が結果の
  subsequence なら merge に著作は無い」という述語へ到達し、撤去 4 件を見込んでいた。sol は
  親 P1 が `@audit`、親 P2 が `@authorize` を持ち結果が両方を並べる例を出した — 全行親由来、
  両親とも subsequence、出現回数も上限内。それでも `audit(authorize(check))` という相対順序を
  決めたことは実装著作である。同一行を 2 回置いて二重登録を作る例も同型。最終 blob からは救えず、
  D721 を維持した ({{D:merge-line-authorship-predicate-rejected}})。
- **親の「逐語ミラーテストは説明文を pin しているだけで価値がない」も誤りだった。** `ruling` と
  `note` は受理判定に使われない**からこそ**全史監査が改変を検出しない。逐語ミラーは 53 件全部の
  5 field・順序・一意性を独立に固定する唯一の検出器で、実 commit 照合テストの被覆は 31 件しかない。
  畳めば裁定根拠を偽造・消去できる。両レンズが独立に、この pin の撤去自体をユーザー裁定にすべきと
  条件を付けた ({{D:known-violation-entry-storage-needs-ruling}})。
- **luna レンズが親の見積りを 2 段階で訂正した。** 親は「台帳の格納形を変えれば生成器が止まり
  14/21 を防げる」と書いたが、(a) 同じ commit を 2 つの wave が独立に登録する競合は entry 単位でも
  残る (`e86d363a` の note が実例)、(b) 支持できる上限は 12/21 であり `311d463f` と `25614f86` は
  台帳格納が原因ではない。したがって正しい表現は「止める」ではなく「最大 12 件分**減らす**」。
- 工数: codex 子 3 本 (段 2 plan 1・段 3 consult 2)、いずれも `check_codex_output.py` rc=0、
  receipt outcome=accepted。段 5・6 は「実装しない」裁定により飛ばした (`4→7→8→9`)。
  実装差分ゼロのため変異 matrix は `DW-S04` により免除、受入全走は免除せず実走した。
- 親の実測 script 8 本と子の成果物は
  `/work/1/SFC/tanab/dev-wave-jobs/known-violation-review-20260823/` に置いた。
  全数分類表・再測定結果・段 4 裁定・裁定パッケージ草稿も同所。

## 次の一手差分

### 新規

- {{T:known-violation-target-metric}} **P1・ユーザー裁定待ち**: known-violation を 0 件にすることを
  目標に据えるか、「不可逆な既知違反」と「新規に増えている違反」を分けて数える指標へ改めるかを
  決める。0 件を選ぶ場合は `PR-C01` の一回性を解除する裁定が要る。親の推奨は指標を分ける側。
- {{T:known-violation-entry-storage}} **P1・ユーザー裁定待ち**: 台帳を entry 単位の格納へ移し、
  並行 wave の競合を減らす。着手条件は逐語 literal pin の撤去をユーザーが裁定すること。
  必須条件は {{D:known-violation-entry-storage-needs-ruling}} に列挙した。
- {{T:mid-merge-codex-author}} **P1・新規**: 受入投入前の local main 取り込み merge を、
  mid-merge の working tree でも Codex `role=author` へ委任できるようにする。現在は
  authority-snapshot 検査が競合マーカーのある tree を拒否するため親が直接解決するしかなく、
  台帳 11 件の直接原因になっている。
- {{T:no-edit-trailer-guard}} **P2・新規**: `git merge --no-edit` と `git revert --no-edit` が
  trailer を 1 行も持たない commit を作るのを機械的に止める。台帳 8 件の生成器。
- {{T:insight-script-implementation-surface}} **P3・新規**: `output/insights/**/*.py` が実装面判定に
  当たるため、解析 script を insight へ置いた docs commit が Codex author 契約に触れる。
  運用と契約の関係を整理する。台帳 3 件の生成器。
