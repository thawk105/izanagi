---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-17
wave: dev-wave-b2-delta-min-connection
seq: 1
title: [T-2743] B-2 delta_min の接続確認 — 事前登録の holdout 別パラメータと判定器の対比パラメータは現行 main で未接続、既裁定 D1481 / D1326 のまま新しい裁定は不要 (docs のみ、branch worktree-dev-wave-b2-delta-min-connection、実装面の差分 0 なので変異 matrix は DW-S04 により免除)
---

## 本文

- ユーザー依頼は「B-2 delta_min の接続確認 (第 20 回 /rulings 全件 項 12 (a)): D2049 で訂正した保持群ラベル (H1 = rr80、
  H2 = rr20、係数 0.03) が判定器側の対比パラメータと現物で接続しているかを、検査を足さずに read-only で確認し、対応表と
  結論を insight に書く。参照 artifact の照合 gate は新設しない (項 12 (b))。正本 = D2049 と entry 1533。実装差分ゼロ。
  差異が見つかれば直さずに構造化して裁定へ返す。規律 2 を緩めない」。
- **閉じた。結果は未接続。** 一次資料は `output/insights/2026-09-17/b2-delta-min-connection/README.md` (対応表 14 行、ラベル
  束縛の 2 本の鎖、既存被覆、設計メモ、検索範囲、限界)。逆割当も誤受理も確認していない。
- **裁定へ返す事項は無い。** 着手後の既存被覆検索で、分断の事実は entry 1147 (T-1875) と T-1874 裁定パッケージが記録済み、
  設計の方向は **D1481 (ユーザー裁定) が「判定側を holdout 別へ広げる」と確定済み**、着手順は D1326 と判明した。親 brief の
  初版はこの択一を「裁定事項」と誤って書いており、段 2 走行中に追補して段 3 で攻撃させた。段 2 plan は追補前の brief を読み
  「裁定へ返す候補」6 件を挙げたが、裁定済み 1 件を除き D1481 実装 wave の設計メモへ移した。項 12 (b) は不採用のまま。
- **着手時「台帳 ID 未採番」だった本件は、wave 中に main が entry 1596 へ進み D2104 項 12・T-2743 として採番された** (段 3
  luna が検出、親が main の `FOLDED.md` と worklog で検証)。worktree を ff-only で追随し、本エントリで T-2743 を閉じる。
  T-1874 / T-1875 は本文を変えない。
- **段 3 の敵対相談 2 本が親の断定 4 件を弱め、すべて採用した** (「2 回呼び分けは成立しない」の限定、「渡す先が無い」の限定、
  測定履歴の断定撤回、8b §10.2 / 8c §4 の「担保は欄が空であることだけ」の部分的陳腐化を参考記録)。採否の表は insight の
  `verbatim/s4-ruling.md`。
- **段 6 レビュー: A は must-fix 0 / GO、B は must-fix 1 / NO-GO → 親が直し、焦点再レビュー 1 本で closed を確認した。**
  B の must-fix は、親の設計メモが「`n` を holdout 別に許すか共通にするかは後続 wave が決める」と書き、**D2071 (2026-09-16)
  が「6 cell すべてで同一、holdout ごとに異なる `n` は受理しない」と確定済み**なのを見落としていた点。既裁定を後続の設計択へ
  戻す誤りで、設計メモと既存被覆表を D2071 に合わせた。A / B の nit (manifest の `n` は任意欄、registry の検査対象、束縛図の
  保証範囲、検索結果の要約、fragment の再掲縮小) も本文修正分は反映した。
- 実装面の差分は 0 (`output/insights/` と `docs/spool/` のみ)。Codex 実装子は起動せず (D95 決定 1)、変異 matrix は DW-S04 により
  免除。段 2・3・6 の read-only 子は規律 2 の面 (判定器の閾値) に触れるので省いていない。
- 工数: codex 子 6 本 (plan 1、consult 2、review 2、focus 1、全段 `gpt-6-astra` / `medium`、計 43 call / 2,078,623 token /
  992 秒)。親の実測は `check_docs.py` (違反なし)・`spool_fold.py --dry-run` (rc=0)・三軸語走査 (`s8b_holdout_freeze search`
  rc=0)・provenance 監査 (commit 後)・受入全走。
- 受入全走は本エントリの記録 commit を含む最終 tip に対して `tools/dev_wave_wait.py acceptance` 経由で投入する。その結果
  (verdict・tested_main / tested_tip・件数) は受入 receipt (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-b2-delta-min-connection/`
  の `acceptance-receipt-*.json`) と land 結果 JSON が正本で、記録 commit が tested tip に含まれる必要があるため本エントリには
  書かない。

## 次の一手差分

### 完了

- [T-2743] D2104 項 12 (a) の接続確認を現行 main で閉じた。結果は未接続 (判定器は 1 組、事前登録は H1 / H2 別、橋と
  production 呼び手は不在)。設計の方向は D1481、着手順は D1326、`n` は D2071 のまま。新しい裁定は不要。一次資料は
  `output/insights/2026-09-17/b2-delta-min-connection/README.md`。
  remaining: none
  base: 20fb04a60b2d0a95df7988ed9735a244740a02d4935b51887738d3849a2f8538
