# [T-1603][T-1604][T-1630] 8b production 配線 — 変異台帳と検出力の実測

`authority: none` / `default_effect: no-state-change`

可変状態の正本は `docs/worklog.md` 末尾と現行 phase doc である。本文書は測定記録
(measurement record) であり、裁定台帳ではない。

- 起点: 段 4 裁定の変異事前登録 15 件。裁定正本は D734 / D739 / D740 / D760 と本 wave の新規決定。
- 測った checkout: branch `worktree-dev-wave-t1603-t1604-t1630-8b-production`、
  変異束縛 commit `a15c4c069b802d538badac0aafca42c7a045a05a`。
- 変異 spec: `izanagi-dev-wave-mutation-spec/v1`、
  sha256 `406ee99201bb69b2c14747a87ba465fe9981d0345cd7433382efe85bc5a5a689`。
- 実行環境: Pegasus 計算ノード dispatch (`--runner-mode dispatch --detached`)。
  runner argv は `python3 tools/run_tests.py` に対象 3 file と
  `-q -p no:randomly -rf --force-dispatch` を渡す形で固定した。

---

## 1. 結果

baseline PASSED。12 変異すべて KILLED で、期待 node 集合と実測 node 集合は完全一致した。
SURVIVED、MISMATCH、TIMEOUT、PARSE_ERROR はいずれも 0 件である。

| ID | 単一変異 | 層数 | 期待 node 数 | 結果 |
|---|---|---|---|---|
| MUT-1 | core: manifest 3 鍵の「全部か 0 か」gate を落とす | 1 | 2 | KILLED |
| MUT-2 | core: binding codec と manifest 鍵の重複拒否を落とす | 1 | 1 | KILLED |
| MUT-3 | core: 未宣言の `manifest_sha256` を黙って受理する | 1 | 1 | KILLED |
| MUT-4 | core: `manifest_path=None` の明示拒否を落とす | 1 | 1 | KILLED |
| MUT-5 | core: `freeze_id` を profile に関係なく必須へ戻す | 1 | 96 | KILLED |
| MUT-6 | adapter: create-only の 2 層 (事前検査と link 競合) を同時に落とす | 2 | 2 | KILLED |
| MUT-7 | adapter: 分類 claim の identity 比較を落とす | 1 | 3 | KILLED |
| MUT-8 | adapter: claim 内蔵 receipt の digest 再構成検査を落とす | 1 | 1 | KILLED |
| MUT-9 | adapter: 発行済み handle の identity 検査を落とす | 1 | 1 | KILLED |
| MUT-10 | adapter: profile gate の statuses 比較を落とす | 1 | 2 | KILLED |
| MUT-11 | adapter: consumed marker の exact 鍵集合 gate を落とす | 1 | 1 | KILLED |
| MUT-12 | adapter: publish 前の holdout-safe preflight を落とす | 1 | 1 | KILLED |

合計 112 node。MUT-5 だけが正例側の過剰拒否を測る変異で、他の 11 件は負例が受理へ反転することを測る。

---

## 2. 変異が検出力の穴を 3 件暴いた (本 wave で最も重要な実測)

**最初の probe では MUT-7 / MUT-8 / MUT-11 が SURVIVED した。** 敵対レビュー 3 本
(段 3 の 2 レンズと段 6 の 2 レンズ、および統合後の焦点再レビュー) はいずれもこれを
見つけていない。変異走行だけが見つけた。

`DW-M02` に従ってまず他層による mask を疑い、実コードを読んで確認した結果、
**mask ではなく「その gate の固有の力を撃つ負例がテストに無い」= テストの穴**だった。

| ID | なぜ生き残ったか | 固有の力があるのはどの場合か |
|---|---|---|
| MUT-11 | 鍵の**欠落**は後続の field 別 exact 比較でも落ちる | marker に**余分な鍵**が足された場合だけ |
| MUT-7 | claim の path が slot address 由来なので address 系 field は必ず一致する | address に含まれない `schema_version` / `event` / `schedule_row_sha256` の食い違いだけ |
| MUT-8 | durable receipt file との比較は別層で拾う | claim 内蔵 receipt と digest field の**相互**不整合だけ |

**mask なら変異を作り替えるが、テストの穴なら負例を足すのが正しい。** 実装は正しかったので
1 byte も変えず、テスト 1 file へ 3 関数 5 node の負例を足した。各負例は例外の型と
逐語メッセージまで検査し、同じ node 内で改竄前の正例が通ることも確認する。

負例を足した後の probe で SURVIVED は 0 件になり、MUT-7 は 3 node、MUT-8 と MUT-11 は
各 1 node を落とすようになった。**足した負例がちょうど狙った gate だけを撃っている**ことが、
node 数の一致で確かめられている。

---

## 3. 2 層 gate を持つ 1 件は両層同時に変異させた

MUT-6 (create-only) は同じ入力を拒否する層が 2 つある。

- `_publish_create_only` の事前検査 (destination が既に在るときの拒否)
- 同関数の `os.link` が `FileExistsError` を返したときの競合検査

片層だけを落としても他層が拾うため、変異は生き残る。片層だけの変異は「他層の mask」であって
検出力の証拠にならないので、両層を 1 つの変異として累積適用した。各置換は適用後に一意性を
再検査している。

---

## 4. 注記 — 落ちる node が広い変異が 1 件ある

MUT-5 は node 数 96 と際立って多い。これは検出力が広いのではなく、
**変異した gate が 8b genesis の構築そのものを支えている**ためである。
`freeze_id` を profile に関係なく必須へ戻すと、8b は genesis 鍵にそれを持たないので
以後どの 8b テストも genesis を作れなくなり、正例が一括で落ちる。
gate 1 つ・原因 1 つ・node 多数である。node 数の多さを検出力の広さと読み替えてはならない。

---

## 5. anchor の再照準と probe

段 4 の事前登録は散文なので、実装後の commit に対して anchor (old 逐語) と期待 node を
取り直した。手順は次のとおり。

1. 12 件の anchor を実体から抜き出し、各 `old` が対象 file 内で厳密に 1 回だけ現れることを
   検査した。複数置換を持つ MUT-6 は、先行置換を適用した後の本文で一意性を再検査した。
2. 全件を SURVIVED 期待で登録した probe spec を作り、計算ノードで走らせて失敗 node を実測した。
   probe 生成器は repo の外に置き、repo へは 1 byte も残していない。
3. probe で SURVIVED した 3 件について、mask の有無を実コードで確認し、テストの穴と判定して
   負例を足した (第 2 節)。
4. 負例追加後に probe を回し直し、SURVIVED 0 件を確認した。
5. 実測した失敗 node をそのまま期待 node の完全集合として最終 spec へ写し、本走した。

**段 4 の事前登録は 15 件だったが、本走は 12 件である。** 差の 3 件は、実装が裁定どおり
「導出しない」「requirement を持たない」形になった結果、単一理由で撃てる gate が
存在しなくなったものである (repetition 導出の不在、resume の row 非追加、
import 不在検査の positive control)。これらは不在契約であり、変異でなく
positive control テストとして実装側に入っている。

---

## 6. この台帳が保証しないこと

- 変異は**実装した gate の検出力**しか測らない。実装していない防壁 (trusted launcher、
  scheduler accounting collector) の不在は変異では見えない。
- 12 件すべて KILLED であることは、adapter が D510 決定 4 を閉じたことを意味しない。
  呼び手は adapter を通さずに出力を読めるし、core を直接 import できる。
- 本 wave 完了後も共有 admission root の registry と受領証は 0 件である。
  変異は「作った gate が効く」ことを測っただけで、production 経路が動いたことは測っていない。
