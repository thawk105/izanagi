# [T-194] 段 4 裁定と変異事前登録 (DW-M01)

## 段構成の裁定 (DW-C00)

- 本 wave は **軽量版**とする。根拠 = (a) 正しさ防壁 (correctness gate / verifier / freeze) に触らない、
  (b) 受理集合 (dispatcher の rc、テストの pass/fail) を不変条件で明示保護する、
  (c) 設計択一は診断出力の体裁に限られ、成果物の値を動かさない
- ただし段 2 (codex プラン起草) と段 3 (敵対相談) を省く代償として、**段 6 の敵対レビュー 2 本は省かない**。
  (P1)(P2)(P3) を明示的な攻撃対象としてレビュー子へ渡す
- ユーザー裁定により実装子・レビュー子は claude で代替する (codex レートリミット)。
  実装面 (コード・テスト・変異 harness) を親が直接編集しない境界は維持する

## provisional 裁定の確定 (段 6 レビューで再攻撃させる)

- (P1) **採用**: rc≠0 は収集済み全量、rc=0 は末尾 4 KiB。診断量の分岐であり rc 判定には触れない
- (P2) **採用**: 子 stdout→親 stdout、子 stderr→親 stderr
- (P3) **採用**: 中継は `[Pegasus dispatch]` prefix の境界行で囲む

## 条件 dispatch の評価 (段 1 前に完了)

- `DW-O08` freeze 族: 不成立。ただし `git submodule update --init` は実行済み
- `DW-O09` / `DW-O10` 凍結 bytes: **不成立**。`output/pegasus-dispatch/` は `FROZEN_MANIFEST` 23 件に
  含まれず、`pegasus-dispatch-receipt/v1` の機械 consumer は自テストのみ (実測 grep)
- `DW-O13` gate 新設: 不成立。中継は受理集合を変えない診断面
- `DW-O20` clean-tree gate: 成立・実施済み (external handoff 付き `check_wave_startup.py` = rc 0)

## 変異事前登録

本 wave の変更対象は診断出力そのものである。`DW-M03` の「診断文字列だけの赤を kill にしない」に
従い、`DW-M08` の別枠 = **diagnostic sensitivity pin** と、真の **kill** (受理集合・fail-closed 挙動が
動くもの) を分けて登録する。anchor (old 逐語) は実装確定後に `DW-M07` で固定してから本走する。

| # | 変異の意味 | 種別 | 期待 |
|---|---|---|---|
| M1 | rc≠0 経路の中継呼び出しを no-op 化する | pin | 赤時に子 stdout が親へ出ることを見るテストだけが赤 |
| M2 | rc≠0 でも緑枠 (4 KiB) に切り詰める | pin | 赤時の全量中継を見るテストだけが赤 |
| M3 | rc=0 の枠上限を撤廃し全量を流す | pin | 緑時の枠を見るテストだけが赤 |
| M4 | 子 stderr の中継先を親 stdout へ替える | pin | stream 対応を見るテストだけが赤 |
| M5 | 中継部の例外捕捉を外す | **kill** | 中継が例外を投げる fixture で rc が child_rc から変わる |
| M6 | infra 失敗経路 (accounting grace 満了) の中継を削除する | pin | infra 経路の中継テストだけが赤 |
| M7 | 中継を receipt 永続化の前へ移す | **kill** | 中継例外時に receipt が永続化されない (fail-closed 後退) |

- 検出力の証明 (`DW-M08` の新旧両走の代替): 変更前 HEAD には中継コード自体が無く変異を注入できない。
  よって「新設テストを除外した状態で M1〜M7 を走らせ、既存 905 行のテストでは全変異が生存する」ことを
  harness に記録させ、新テストだけが検出する差分を示す
- `DW-M01` の単一理由性 (その位置より前に同じ入力を拒否する検査が無いこと、赤理由が一つに絞れること) は、
  実装確定後に harness が置換一意性 (`DW-M04`) と第一失敗 node (`DW-M08`) を記録して確認する
- 復元は `read_text() == 元ソース` の内容比較で検査する (`DW-M05`)
