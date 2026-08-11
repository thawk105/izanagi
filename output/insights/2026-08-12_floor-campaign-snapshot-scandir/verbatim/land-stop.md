# 段 9 — land 停止の記録 (DW-STOP)

## 結論

**land しない。** 受入全走が赤で、その赤は **main 由来**であり本 wave では直せない。
成果は branch `worktree-dev-wave-floor-campaign-speed` に commit 済みで、
ユーザーが赤の解消後に land できる。

## 受入全走の結果 (計算ノード dispatch、request 904892、570s)

**2 failed / 9127 passed / 20 skipped (560.13s)**

- **本 wave の対象 file (`test_s8b_floor_campaign.py`) は赤ゼロ** (216 テスト全緑)。
- 赤 2 件はいずれも `orchestrator/tests/test_t793_report.py`:
  - `test_deny_only_report_contains_authority_and_both_submission_denials`
  - `test_actual_head_d292_reference_is_reported_fail_closed`

## 赤の原因 (機械確認済み、本 wave と無関係)

両テストは `docs/decisions.md` を読み、**D291 を supersede する決定 ID が `("D292",)`
ちょうど**であることを固定している。しかし **2026-08-12 に D305 が land され**、
実際は `("D292", "D305")` になった。

```
AssertionError: assert ('D292', 'D305') == ('D292',)
  Left contains one more item: 'D305'
```

D305 = 「D291 payload の trust root は `F_p` の実 bytes に固定し、caller が payload を
注入する公開経路を作らない (2026-08-12)」。**D291 payload を扱う決定自身が、
D291 の supersession scan に引っかかる**という構造である。

### 帰属の機械確認

| 検査 | 結果 |
|---|---|
| `docs/decisions.md` の最終変更 | `427da17c` (main 側の land fold)。**私の commit ではない** |
| `test_t793_report.py` を追加した commit | `c820722a`。**main の祖先** (`merge-base --is-ancestor` rc=0) |
| D305 を入れた fold | `427da17c`。**main の祖先** (rc=0) |
| 私の 4 commit が触った path | `orchestrator/tests/test_s8b_floor_campaign.py` と自分の記録ファイルのみ |
| `test_t793_report.py` が私の編集面を参照するか | **0 件** (grep で確認) |

### 再現性 (DW-O18)

単独再走 (計算ノード、request 905031) で **2 failed / 7 passed、rc=1**。
受入と**同じ 2 node** が落ちた。**フレークではなく恒常的な赤**である。

→ **main そのものが赤であり、いま受入を走らせるどの wave も同じ 2 件で落ちる。**

## 親が直さない理由

`test_t793_report.py` は **T-139/公表層 wave (t793) が所有する実装面**であり、
同 wave は本 wave の稼働中も動いていた。凍結境界により親は実装面を直接編集せず、
他 wave 所有の file を書き換えると衝突する。よって修正は所有者に委ねる。

## 必要な修正 (所有者向け、参考)

`test_t793_report.py:38` と `:64` の期待値が **D291 を supersede する決定の集合を
literal で固定**している。D305 の追加でその集合が増えた。選択肢:

- (a) 期待値へ D305 を足す (最小)。ただし**次に D291 を参照する決定が入るたびに再発**する。
- (b) 期待値を「D292 を必ず含む」等の**単調な性質**へ変える (再発しない)。
- (c) scan 対象を凍結 bytes (`F_p`) に固定する — D305 自身が要求している設計と整合する。

**親の推奨は (c)**。D305 は「payload は `F_p` の実 bytes を毎回読んで導出する」と決めており、
test が live な `docs/decisions.md` を読んでいること自体が D305 と食い違っている。
これは**説明と実装の食い違い**型であり、(a) の対症療法では同じ赤が繰り返す。

## 本 wave の成果 (branch に commit 済み)

| commit | 内容 |
|---|---|
| `9e39c77a` | 実装 (`os.scandir` + 並列 hash) |
| `26deeedf` | fix 1 (canary 置換 / fail-closed / reference 独立性 / thread 8→4 / 定義域明記) |
| `88ef3a8f` | main 取り込み |
| `803021f3` | fix 2 (並列 hash 撤去) |
| `e18dd081` | 記録 (worklog fragment / insights / 裁定パッケージ / 変異 spec・台帳 6 本) |
| `e0eb3f8b` | main 取り込み (受入 lease 内) |

- `check_docs` 緑 / 全史 provenance 監査 緑 (2593 件、新規違反なし) / fold dry-run rc=0
- 変異 12 件すべて検出 (SURVIVED 0)。M10 のみ変異設計の欠陥で MISMATCH → M10b へ分割して KILLED
- **既存 212 node の id は 1 つも変わっていない** (消失 0 / 増加 4 = 正例のみ)

## 再開コマンド (赤の解消後)

```
/dev-wave worktree-dev-wave-floor-campaign-speed を受入から再開して land する
```

fresh context で branch を再利用し、新しい main を取り込んで受入を 1 走してから land する。
