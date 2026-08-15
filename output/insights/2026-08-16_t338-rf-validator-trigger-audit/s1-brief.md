# 段 1 brief — [T-338] Q11 独立 validator (dev-wave t338-rf-validator, 2026-08-15)

## 依頼 (ユーザー command 引数、逐語要旨)

[T-338] の残件を実装する。裁定 11 問は全件確定済み (正本 = archive worklog (142)、パッケージ =
`output/insights/2026-08-03_t338-rf-statistical-design/package.md`)。残っているのは Q11 が指定した
実装 — 認証判定の統計量を、報告された値ではなく raw receipt から**独立 validator が再計算する経路**。
Q5 = 標準化効果 `d≈1.0` (約 11 cluster) が正例の目標。目標効果量は study ごとに事前登録で決め直すが、
**結果を見てから J を足すことは D126 決定 (4) の型で禁止** (足りなければ判定不能で終える) — この禁止が
機械的に効くことをテストで固定する。既存の統計実装は `orchestrator/campaign/s8b_floor_stats.py` 周辺。
実装は Codex author (D95)。規律 2 は緩めない — 再計算が一致しないときは fail-closed で判定不能にし、
報告値を採る経路を残さない。後続 scope ([T-339]) は実装せず境界を worklog へ明記する。

## 段 1 前提実測 (2026-08-15 23:33〜23:50 JST、main `330f67d0`)

1. 編集面の重なりなし。`s8b_floor_stats.py` / `test_s8b_floor_stats.py` を触る worktree branch 0 件。
2. RF 実装は main に存在しない (`recovery_fraction` / `rf_acceptance` / `pairing_valid` /
   `weak_denominator` / `fieller` / `delta_D` が `orchestrator/` `tools/` で 0 hit)。
3. **依頼が引く 2026-08-03 裁定より後に、実装可否を縛る裁定が 2 件ある。**
   D162 (08-05) 決定 (10) = 機械化は発火条件 3 点が揃うまで行わない (`DW-G04`)。
   D229 (08-07) 決定 (6) = 着手順序 `producer → pilot → validator/consumer → 本走`、
   「9 層原子的許可」も「D162(10) の書き換え」も却下済み。決定 (7) = 記録項目の確定は単独の裁定 gate。
4. **pilot は今も投入不可** — `orchestrator/preregistration/stress_check_simulation.py:738` が
   main HEAD で `pilot_ready: False` / 未充足前提 `[1,4,5,6,7,8,9]`。
5. 本日 (08-15) の裁定控え 33 件に本件の言及 0 件 (新裁定なし)。
6. Q11 推奨 3 は RF calculator / schedule validator / producer / attempt registry / consumer を
   **[T-339] の中身**として起票せよと書く。依頼はこの [T-339] 分を除外している。

## 親の provisional 裁定 (攻撃対象)

- **(P1)** 本 wave は Q11 の validator 経路を実装できない。`DW-G04` が要求する
  「発火条件を満たす既存 artifact path か計測 ID」を brief に書けないため。書けば fixture 限定の
  未結線 leaf になり、D147 / D163 決定 (1) が却下した型の再演になる。
- **(P2)** 「J を後から足す禁止」のテスト固定も単独では成立しない。本走の J は二段階設計で pilot から
  導く値で、pilot 未実走のため凍結対象の J が無い。prereg 凍結機構 (approval_payload / erratum) は
  文書 digest を束縛するが J を pin していない。
- **(P3)** したがって既定は「実装しない」裁定 (段 4 で `4→7→8→9`) と、実測 + 択一のユーザー返却。

## 不変条件 (緩めない)

- 規律 2: 正しさゲートを緩める変更を採らない。再計算不一致は fail-closed で判定不能。
- 報告値 (producer 自己申告) を受理入力に採る経路を新設しない (D162 決定 (2)(4)、D127)。
- 凍結 bytes・certified 選択・材料レポート・proof chain・既存受理集合を動かさない。
- [T-339] scope (計測 producer / attempt registry / schedule validator / RF calculator /
  [T-337] 適格性権威 / 層 3 次版 / consumer / 双射・変異検査) は実装しない。

## 成果物の形

- (P1)(P2) が支持されるなら: 実測 + 敵対 2 レンズ + 裁定パッケージ (docs のみ、実装差分ゼロ)。
- 反証されるなら: 発火条件を満たす artifact path / 計測 ID を明記した上で Codex author が実装。

## 成果物影響 (`DW-G05`)

実装しない場合、certified 選択・材料レポート・proof chain・凍結 bytes・受理集合は**不変**。
変わるのは [T-338] の状態が「実装待ち」から「pilot 前提の未充足が実測された実装待ち」へ確定すること。
誤って未結線 leaf を land した場合の害は、正例適格性の権威が「実装済み」と記録され、
pilot の記録項目確定後に validator を作り直す必要が生じること (D229 決定 (6) の残 risk そのもの)。
