# 受入の赤と既知赤 waiver W2 (land 判断の記録)

## 経緯

1. 受入全走が **2 failed / 9127 passed / 20 skipped (560.13s、request 904892)**。
2. 親は帰属と再現性を実測したうえで `DW-STOP` に従い **land を停止**して報告した。
3. **ユーザー裁定 (2026-08-12、逐語「既存の赤は免除リストに入れて」)** により、
   既知赤 waiver W2 を新設して land する方針へ変更した。

## 親の手順漏れ (F101 の同型再発)

F101 の恒久対応は「**受入全走で赤を観測したら、停止判断の前に local main の worklog を
赤 node 名で検索し、成立している waiver / 既知赤の裁定が無いかを確認する**」である。
親はこれを実施せずに停止した。ユーザー指摘で是正し、検索を実施した結果:

- `grep "waiver" docs/worklog.md` → 0 件
- `grep "test_t793_report\|test_deny_only_report\|test_actual_head_d292" docs/worklog.md` → 0 件
- W1 (F96/F101) は `[T-407]` = `7f767ee8` の land で**失効済み**
- archive 395 の wave が「**赤いまま免除されているテストは 1 件も無い**」ことを確定済み

→ **現時点で有効な既知赤 waiver は存在しなかった。** よって W2 が新規である。
前回の F101 は「waiver が有るのに引かなかった」、今回は「waiver の有無を調べずに止めた」で、
**欠けた段は同一**である。failures へ再発として記録した。

## 赤の内容と帰属 (機械確認済み)

対象 2 node はいずれも `orchestrator/tests/test_t793_report.py`:

- `test_deny_only_report_contains_authority_and_both_submission_denials`
- `test_actual_head_d292_reference_is_reported_fail_closed`

両者は live な `docs/decisions.md` を読み、**D291 を supersede する決定 ID が `("D292",)`
ちょうど**であることを literal で固定している。2026-08-12 に **D305** が land され、
実際は `("D292", "D305")` になったため落ちる。

```
AssertionError: assert ('D292', 'D305') == ('D292',)
  Left contains one more item: 'D305'
```

| 検査 | 結果 |
|---|---|
| `docs/decisions.md` の最終変更 | `427da17c` (main 側の land fold)。**私の commit ではない** |
| テストを追加した commit `c820722a` | **main の祖先** (`merge-base --is-ancestor` rc=0) |
| D305 を入れた fold `427da17c` | **main の祖先** (rc=0) |
| 私の commit が触った path | `test_s8b_floor_campaign.py` と自分の記録ファイルのみ |
| `test_t793_report.py` が私の編集面を参照するか | **0 件** |
| 単独再走 (request 905031) | **2 failed / 7 passed、rc=1。同じ 2 node が再現** = フレークではない |

**production の受理挙動は変わっていない。** 変わったのは台帳の内容 (D305 の追加) と、
それを literal で固定していたテストの期待値との差である。

## 既知赤 waiver W2 (正本 = worklog 末尾エントリ)

- **対象 node は上記 2 件ちょうど。** これ以外の赤には一切適用しない。
- **適用の毎回検査 (4 点すべて)**:
  1. 受入全走の赤が**上記 2 node ちょうど**。他の赤が 1 件でもあれば適用せず停止。
  2. 失敗理由が `assert ('D292', 'D305') == ('D292',)` 系の**期待値集合の差**であること。
  3. 自 wave の差分が `test_t793_report.py` と `docs/decisions.md` を**触っていない**こと。
  4. 検査結果 (赤 node 名の集合と失敗理由) を worklog へ併記する (F101 の再発検知)。
- **失効**: 上記 2 node の期待値が是正された時点で**自動失効**。
- **並行セッション**: 同じ 4 条件を各自が検査したうえでのみ適用してよい。

## 是正の担い手と推奨 (本 wave の scope 外)

`test_t793_report.py` は **T-139/公表層 wave の所有**。凍結境界により本 wave は直さない。

### 親の当初推奨 (c) は誤りだった — 撤回する

親は当初「scan 対象を live な `docs/decisions.md` でなく凍結 bytes (`F_p`) へ固定する」を
推奨した。**これは fail-open を作る誤りである。** [T-827] セッションの反論を受けて
実装を読み直し、こちらの誤りと確認した。

| 根拠 (`orchestrator/publication/report.py`) | 内容 |
|---|---|
| `:22` `D291ReportError` | 「**HEAD decision scan** または report 構築に失敗した」 |
| `:26` `_SupersessionScan` | 「**HEAD 上で** D291 より後ろにある canonical supersession の走査結果」 |
| `:76` `_scan_d291_supersession` | 「後続 decision にある D291 参照を **fail-closed に列挙する**。…後続 decision section に `D291` が一度でも現れたら、**現在も承認済みとは断言しない**」 |
| `:114` `_read_head_decisions` | 名前と実装のとおり HEAD を読む |

**この走査は意図的に「HEAD を見張る fail-closed な番人」**である。`F_p` へ固定すると
**凍結後に追加された decision を構造的に一切見られなくなり、常に `none_found` を返す
恒真ゲート (検出力ゼロの fail-open) になる。**

親の誤りの中身は、**目的が逆向きの 2 つを同じ「`F_p` を読め」で揃えようとした**ことである。

- **payload の trust root** (D305 が定める) — **再現性**のため過去 (`F_p`) に固定する
- **supersession の見張り** (この走査) — **検出**のため現在 (HEAD) を見る

D305 を後者へ適用すると後者の存在理由が消える。しかも**テストが壊れたのは番人が
正しく働いた結果**であり、壊れているのは期待値の側だけである。

### 正しい解

**exact な `status` は維持し、`"D292" in decision_ids` を必須にしつつ、
完全一致は要求せず decision 番号の昇順・重複なしという構造的性質を検査する。**
[T-827] の `292151a5` (branch `worktree-dev-wave-t827-slow-tests`、18+/5-、実走 9 passed) が
この形である。**番人の検出力を落とさずに脆さだけを外す**ので、次に D291 を参照する決定が
入っても再発しない。

親が当初挙げた (a)「期待値へ D305 を足す」も、次の決定で再発するので採らない。
