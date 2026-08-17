# [T-1283] 待ち手/runner の tested main 側 blob 照合 — 実装せず再裁定へ返した wave の材料

wave `t1283-waiter-runner-main-blob` / 2026-08-17 / base main `2a3b5055` → 受入直前に `69a0b11c` へ更新 /
実装差分ゼロ (docs のみ)

ユーザー裁定 [T-1283] 択 (a)「待ち手と実行器も本流側 blob と照合する」を実装しようとして、
**その形では名指しの穴が閉じないか、閉じる形は恒久 land 不能を作る**ことが確定した wave の逐語。
設計択一はユーザー再裁定へ返した。経緯の正本は worklog、未閉鎖の記録は failures 台帳。

## 構成

- `verbatim/brief.md` — 段 1 brief (親)。(P1-1)〜(P1-5) の provisional 裁定を含む。
  文言 3 箇所 (「実行 bytes を main に要求」「両経路を覆う」「純増検出力」) は段 4 で撤回した。
- `verbatim/s2-plan.md` — 段 2 プラン (codex, plan, max)。案 γ を推奨し、
  sentinel による一度きりの seed 遷移が構造的に必要であることを最初に示した。
- `verbatim/s3-lensA.md` — 段 3 敵対相談 レンズ A (codex, consult, max, sol)。正しさ境界。
  **NO-GO**、所見 9 件 (must-fix 7)。A-01 が本 wave の結論を決めた。
- `verbatim/s3-lensB.md` — 段 3 敵対相談 レンズ B (codex, consult, max, luna)。整合・運用。
  **NO-GO**、所見 10 件 (must-fix 4)。
- `verbatim/s4-adjudication.md` — 段 4 裁定 (親)。所見の real/refuted、設計空間表、
  ユーザーへ返す択一 (a)〜(d)。

## この wave が確定させたこと

1. **検査を待ち手自身の中に置く限り、待ち手を書き換えた相手には効かない。**
   実行 bytes を tested main の blob へ束縛して自己再実行する案は、検査も再実行も同じ待ち手の中に
   あるため、書き換えた側が再実行を削除して main 側の hash を自己申告すれば land を通る (A-01)。
   land が独立に検証できるのは Git 由来の値だけである。
2. **受入の主経路は child-green である。** 2026-08-17 の受領証 25 本のうち 24 本が `child-green`
   (集計 predicate は worklog エントリに記録)。既存の main 束縛 (checker・runner) は
   `non-attributable-only` 経路の中にしかないので、発火するのは約 4% だけである。
3. **設計空間は 4 択に閉じる** — 恒久 land 不能を受け入れる / 候補外の trusted launcher を新設する /
   協調的な drift 防御だけを採り「閉じた」と書かない / 現状維持を明文化する。
   詳細と代償は `verbatim/s4-adjudication.md` の最終節にある。
