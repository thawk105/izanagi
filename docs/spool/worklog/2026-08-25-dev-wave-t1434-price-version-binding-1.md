---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-25
wave: dev-wave-t1434-price-version-binding
seq: 1
title: [T-1434] price snapshot を schedule へ凍結束縛し、事前登録文書の陳腐化を実測へ張り替えた (コード + docs、branch worktree-dev-wave-t1434-price-version-binding)
---

## 本文

- 引数が指定した編集面は**誤りだった**。`price_version` の非 null 拒否は
  `tools/t189_price_snapshot.py` にも `t189_task_catalog.py` にも無く、
  実体は `tools/codex_reasoning_ab.py` のちょうど 2 箇所だった。全件検索で確定した。
  `t189_task_catalog.py` にある `codex_reasoning_ab` の文字列は keyword 一覧であって import ではない。
- **事前登録文書 §5.2 の file:line 表は 15 行すべてが実在しない位置を指していた。**
  同ファイルが 11000 行超へ拡大したため。表が「未着手の横断 refactor」と呼ぶ主要項目
  (model allowlist、`requested_model` の配線、task manifest schema v3) は既に着地していた。
  同じ陳腐化を繰り返さないため、**表を関数名主・行番号従の形へ作り替えた**。
- 親の段 1 記述を 2 件撤回した。(1)「(5) downstream replayer は閉じた」は不正確で、
  正しくは「機構は着地、受理条件は `unbound` として登録済み (D767)、帰結として fix gate と
  overall は `inconclusive`」である。D767 本文を読み、`unbound` が欠落ではなく
  **受理を定義する oracle が無いという事実の正直な登録**だと確認した。
  「閉じた」とも「未了」とも書かない形へ docs を直した。
  (2)「§5.2 の残件は price 束縛が主」は過大な一般化だった。task manifest は既定値のままで
  CLI 入力口が無い。本 wave は price component の配線だけを担う。
- **段 1 で親が scope を 1 つ足した。** 事前登録 §10 は「schedule の全 slot は同じ
  `price_version` を参照する。欠落すれば schedule を無効化する」と定めていたが、
  **この検査は実装に存在しなかった**。全 slot が null なので恒真に成立していただけで、
  非 null を受理可能にした瞬間に「謳うだけで発火しない保証」へ変わる。同じ commit で塞いだ。
- **段 3 の 2 レンズはどちらも NO-GO を返し、2 件は独立に同じ穴へ到達した** —
  (a) 旧形式 (v2・schema 欠落) の schedule まで新受理形が漏れる、
  (b) packet の文字列検査を無条件にすると**旧受理集合が縮む**。両方とも裁定へ反映した。
- **プランの module 読込み方式は、そのままでは道具が import 時に落ちた。** 親が再現した
  (`AttributeError: 'NoneType' object has no attribute '__dict__'`)。原因は検証器の `@dataclass` と
  遅延注釈の組合せで、`sys.modules` へ登録してから `exec_module` すれば通ることも実測した。
  既存 ledger に dataclass が無いため、同じ方式でも露呈していなかった。
- **段 6 のレビュー 2 本と焦点再レビューが、Python の数値型混同で受理集合が広がる穴を 3 件見つけた** —
  `schema_version: 3.0`、`block_order: true / 2.0`、slot の `stage`。いずれも親が再現した。
  `3.0 == 3` も `True in {1,2}` も `[True, 2.0] == [1,2]` も真である。{{F:numeric-type-confusion-widens-acceptance}}。
- **修正範囲を決めた非対称性を裁定へ明文化した。** 旧受理集合には束縛済み schedule が
  1 つも無い (非 null price は以前は必ず拒否された) ため、**束縛経路の中で課す要求は
  定義上 A0 を縮められない**。逆に共通経路を強くすると `block_order` が `true` の
  全 null schedule が新たに拒否され A0 が縮む。この非対称性のおかげで、
  fix 2 巡目で型混同の族をまとめて閉じ、3 巡目へ持ち越さずに済んだ。{{D:bind-path-only-hardening}}。
- 冗長な条件 2 件と module-load rollback の失敗注入テストは nit / backlog とした。
  前者は単独 clause の変異が相方に mask されるため、**変異では SURVIVED を期待し erratum に残す**。
- 実装子・fix 子は 3 本とも pytest 実走不能 (sandbox の構造的制約)。
  **本 wave のテスト結果はすべて親の実測**である。
- 親は受理集合そのものを独立 probe で測った (repo 外に置いた使い捨て)。20 項目すべて期待どおりで、
  特に**呼び手が別の値を期待値だと自称しても通らない**ことを確認した。
  段 3 が指摘した「自己追認になっていないか」への直接の答えである。
- テスト file の削除行が 0 から増えたので、**HEAD の全 11936 行が順序どおり保存されているか**を
  検査した。欠落ゼロ。差分上の削除は hunk 再整列の産物であり、既存テストの改変ではなかった。
- 設計判断は {{D:frozen-price-binding-trust-root}} と {{D:bind-path-only-hardening}}。

## 次の一手差分

### 更新

- [T-1434] **P1・[T-189] 事前登録文書の実装・実走**: D674 で 7 論点の処遇が確定している。
  (4) 装置の横断的 refactor のうち **price_version の非 null 拒否 2 箇所の解消は完了した**
  (2026-08-25、凍結 snapshot への束縛として実装)。到達度の正本は同文書 §5.2 と §5.3 の表。
  **残余は 3 つ** — (a) task manifest が既定値のままで CLI 入力口が無い、
  (b) adjudication 層の task-specific oracle 対応 (§8 の oracle ledger 待ち)、
  (c) 費用の正規化計算 (version の束縛と cost 計算は別物)。
  (5) replayer は機構が着地し acceptance は `unbound` 登録済み (D767) で、意味的 disposition は
  [T-1638] が持つ。§8 の独立 oracle ledger は未作成のままで、これが揃うまで台帳の
  `oracle_finding_count` は `not-established` である。
  base: 2d039a472570bc155aed022de8c8f03fafc47dd1e5b29593de934cfe0dfd6674

### 新規

- {{T:price-cost-normalization}} **P2・新規**: 凍結 price snapshot の SKU 単価から、
  arm 間で比較可能な正規化 cost を計算する層を実装する。本 wave は version の provenance を
  装置へ束縛しただけで、cost の値は生成しない。台帳に price version が載ることと
  cost 系の副指標が使えることは別である。事前登録 §10 の SKU mapping が入力仕様。
- {{T:schedule-bytes-toctou}} **P2・新規**: schedule が hash 用と validation 用で別々に読まれ、
  同一 UID の書き手が A→B→A と差し替えると、A の SHA を receipt に残しつつ B の内容で
  検査・集計できる。supervisor・replay・make-packets の 3 入口で
  「一度だけ読み、その同じ bytes から descriptor SHA・schedule SHA・JSON・validation を導く」形へ
  直す。本 wave 以前から存在し price 束縛が悪化させるものではないため scope 外とした。
- {{T:schedule-less-packet-uncertified}} **P2・新規**: schedule descriptor を持たない
  legacy 互換の packet 生成経路には price 束縛も一様性検査も無い。塞ぐと旧受理集合が縮むため、
  本 wave では docs で uncertified と明示するに留めた。専用 mode を設けるか、
  legacy 限定と機械的に宣言させるかを決める。
