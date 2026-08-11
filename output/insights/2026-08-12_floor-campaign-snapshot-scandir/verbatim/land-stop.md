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

- (a) 期待値へ D305 を足す (最小)。**次に D291 を参照する決定が入るたびに再発する。**
- (b) 期待値を「D292 を必ず含む」等の**単調な性質**へ変える。
- **(c) [推奨] scan 対象を live な `docs/decisions.md` でなく凍結 bytes (`F_p`) へ固定する。**
  D305 自身が「payload は `F_p` の実 bytes を毎回読んで導出する」と決めており、
  **test が live 台帳を読んでいること自体が D305 と食い違う**。これは
  「説明と実装の食い違い」型であり、(a) の対症療法では同じ赤が繰り返す。
