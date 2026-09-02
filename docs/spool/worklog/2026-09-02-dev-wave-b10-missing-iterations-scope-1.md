---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-02
wave: dev-wave-b10-missing-iterations-scope
seq: 1
title: B-10 正式走の欠測 7 反復の射程を確定した — 「7」は開始済み分だけの数で、登録格子に対しては 73 枠が埋まっていない (docs + insight、branch worktree-dev-wave-b10-missing-iterations-scope、実装面 0・変異 matrix 免除)
---

## 本文

- ユーザー依頼は、エントリ 1189 が 1 文で触れた欠測 7 反復の射程を既存記録だけで確定することだった。
  再実走はせず、成果物は insight と worklog のみ、`docs/paper-story/` は読むだけで触らない、
  仮想リスク向けの gate・検査・台帳・一般化は scope 外、と最初に確定していた。実装面の差分は 0。

- **敵対相談 2 本 (正しさ射程レンズ / 数量と帰属の整合レンズ) の所見はすべて real と裁定した
  (refuted 0)。** 親の provisional 裁定 3 件のうち 2 件が書いたとおりでは成立せず置き換えた。
  **親自身の実測にも誤りが 3 件あり、いずれも子の指摘で見つかった。**
  (a)「正式走の識別子は docs のどこにも引かれていない」は誤り — 親が検索から `docs/archive/` を
  除外していた。(b) read-heavy の撤去理由を scheduler 受領証だけで確定と書いたが、受領証の射程は
  「壁時計ではない」までで、撤去主体はエントリ 1187 の `qdel` 記録が確定する。
  (c)「欠測変種が入る下流集計は 1 件だけ」は誤りで、派生記述が 4 件ある。

- **最も重い所見: 「7」は開始済み attempt に条件づけた事後の数である。** read-heavy は登録された
  15 点のうち 4 点しか開始しておらず、未開始 11 点 x 6 = 66 枠が分母から落ちていた。分母は 3 つ
  あり、開始済み条件付きなら 294/287/7、登録された 3 workload の組なら 270/197/**73**、
  4 campaign の履歴なら 360/287/**73** である。**完全性の開示に「予定 294 / 欠測 7」を使えない。**

- **refuted ではないが、親は子より強い上界を出せた。** `verify_done` は検査器が返った後にだけ
  書かれ、反復の開始を記録するイベントは無いので「実行されずに終わった」とは書けない。ただし
  反復は厳密に逐次なので、完了記録が増えていない以上、空白の中で開始できたのは attempt あたり
  高々 1 件である。**7 枠のうち開始されたのは高々 2 件、少なくとも 5 件は一度も開始されていない。**

- **絶対規律 7 に従い、エントリ 1189 の bytes は 1 バイトも変えず、追記で 5 件を訂正した。**
  予定 294 の条件性、「実行されず」の強すぎる断定、壁時計帰属 (balanced は残余 0 秒で壁時計、
  read-heavy は残余 22250 秒で壁時計ではない)、「2 変種は 45 cell に含まれない」の単位誤り
  (`variant_id` は workload 共通で、同じ ID は 45 cell に各 3 record 実在する)、
  「何の正しさ主張も担っていない」の広義部分。あわせて `certified` の 4 条件は代表例であって
  全条件ではないことを追記した (`Integrity.clean()` は 12 項の連言)。**正しさゲートを強い側へ
  言い直す訂正であり、規律 2 を緩めていない。**

- **45 cell の `correctness_certified=true` は維持される。** 欠測はこの値を 1 件も降格させない。
  ただし 45 cell はもともと単一 request・1 workload・15 認証単位の記述的成果であり、
  欠測が新たに射程を狭めたのではない。2 族が indeterminate なのは、両 campaign が性能相を
  一度も走らせず 18 pair 全部が欠けているからで、7 枠が関わるのは各 3 pair だけである。
  一方で事前登録の `pair_action = invalidate-entire-family` の下では、他が揃っていても
  各 attempt に未完了枠が 1 件あれば族は indeterminate になる。**「無害だった」とは書けない。**

- **図には 1 件も入らない。** `fig2b` / `fig2c` の入力は別系列の sweep campaign で、正式走
  4 campaign はどちらの provenance にも現れない。

- 一次資料: `output/insights/2026-09-02_b10-missing-iterations-scope/README.md`
  (段 2 プラン・段 3 敵対相談 2 本・段 4 裁定の逐語は同 `verbatim/`)。

## 次の一手差分

### 新規

- {{T:b10-completeness-denominator}} **P2**: B-10 の完全性を開示するときの分母を、開始済み
  attempt に条件づけた 294 ではなく登録格子の 270 で書き直す。対象は現行 worklog エントリ 1189 の
  読み手全般と、次の正式系列の報告様式。`docs/paper-story/` への反映は別 wave が所有する。
- {{T:b10-derived-population-caveat}} **P2**: 欠測 attempt を含む母集団から出た派生記述 4 件に
  但し書きを付けるか裁定する。T-2191 の 70.0-87.0 マイクロ秒/commit と 15 認証単位、
  D1485 の「直列性検査 1 回 23 分」、`docs/b10-multinode-formal-run-design.md` の read-heavy
  5 時間・約 25 時間の外挿、正式走 insight の 1690 万 commit。あわせて同設計文書の
  「トレース切り捨ての疑いが残っている」がエントリ 1189 で決着済みなのに残っている点も直す。
