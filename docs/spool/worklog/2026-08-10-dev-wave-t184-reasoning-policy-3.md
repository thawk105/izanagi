---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-10
wave: dev-wave-t184-reasoning-policy
seq: 3
title: [T-184] の工程別 reasoning policy を現行値のまま採用した — 段 2/3/5 は直接比較証拠の不在を明記した据え置き、段 5 の機械 pin は見送り裁定が生きており drift 実測 0 件で再訪条件も不成立 (docs のみ、実装差分ゼロ、branch worktree-dev-wave-t184-reasoning-policy)
---

## 本文

- **[T-181] の待機条件が充足したので、工程別 reasoning policy を採用済みとして確定した
  ({{D:stage-reasoning-policy-adoption}})。値は 1 つも変更していない。**
  2026-08-01 のユーザー裁定 (択 (a)) は「工程別 policy の採用は認証再走の後」であり、
  2026-08-09 の認証再走 + erratum 引き渡し裁定 (§51) でこの gate は開いた。
- **段 2 / 段 3 / 段 5 は「証拠が支持した採用」ではない。** 台帳に工程軸の field は無く、
  束縛された 2 prompt はいずれも段 6 focused review である。erratum は他工程への外挿を
  明文で禁じている。よって三工程は**直接比較証拠の不在を明記した保守的据え置き**として採用した。
  値を下げないのは D207 の帰結であって、本 A/B の帰結ではない。
  erratum が汚染と列挙した 8 field は根拠に使っていない。
- **当初計画していた `DW-S05-A` への機械 pin 追加は撤回した。** 段 3 の敵対相談 2 本が
  ともに NO-GO を返し、[T-667] が 2026-08-08 に「見送りで終端」と裁定済みであること
  (防御的堅牢化、D205 既定) が判明した。**再訪条件「当該節の drift の実測」を実測した結果、
  `docs/dev-wave/workers.md` を持つ全 19 commit (2026-07-24 `2cd329d5` 〜 2026-08-08 `f9e2756e`)
  で当該節の effort 抽出値は一貫して `reasoning=high` のみ、drift は 0 件**で条件は成立しない
  (`DW-S02` / `DW-S03` も `max` 不変)。D223 も同じ拡大を当時の scope 外として却下していた。
  親は不採用にせず、pin の可否をユーザー再裁定へ返す。
- **親 brief の誤りを 1 件訂正した。** 凍結台帳の pin 閉包を「bytes を pin する code は 1 箇所」と
  書いたが、正確には sha256 で bytes を pin するのは 1 定数で、同 directory の `run-outputs/` は
  filename key の parametrized consumer が別に 9 本ある。閉包は 10 ファイル。
  本 wave は bytes を 1 byte も変えていないため成果物影響はゼロ。
- **段 3 が返した scope 外の real 所見 2 件を裁定パッケージへ送った。** (i) 既存の
  `DW-S02` / `DW-S03` pin は literal 出現数方式のままで、F170 の恒久対応 (独立行 exact 検査) が
  段 6 の 2 節にしか適用されていない。規範文を引用・否定文・例示リンクへ置換する経路と、
  raw HTML block 本体へ別値を隠す経路が静的に指摘された (**親は production 経路で再現していない**)。
  (ii) resource envelope (`DW-O01` の launcher 結線と stage 別上限値) と retry policy。
  親の推奨はいずれも見送り / [T-183] 完了後の一体設計。
- 変異 matrix は `DW-S04` の明示免除 (実装差分ゼロの「実装しない」裁定) に該当するため実施していない。
  受入全走は免除していない。**1 走目 (request `898552.nqsv`、bnode021、1316.27 秒) は
  1 failed / 7843 passed / 20 skipped** で、赤 1 件は
  `test_codex_worker_launch.py::test_late_rollout_writer_does_not_change_sealed_receipt`。
  同一 checkout の単独再走は 1 passed / 3.35 秒で再現せず、docs のみの差分は当該 file へ
  到達しえないため `DW-O18` により帰属しない。F57 の再発として起票した。
  確認のための 2 走目は local main (`e91bf56d`) を取り込んだうえで実施する。
- 選択理由・実測・rollback・裁定パッケージ 3 件の正本は
  `output/insights/2026-08-10_t184-reasoning-policy-adoption.md`。

## 次の一手差分

### 更新

- [T-184] **P1・reasoning 面のみ採用済み ({{D:stage-reasoning-policy-adoption}}) → resource/retry 残**:
  段 2 / 段 3 = `max`、段 5 = `high` を直接比較証拠の不在を明記した保守的据え置きとして採用し、
  段 6 は D243 の追認とした。値は不変、機械 pin も増やしていない
  (段 5 の pin は [T-667] の見送り裁定が生きており、再訪条件の drift は実測 0 件)。
  **本項は完了していない** — resource envelope は設計択一として裁定へ、retry policy は
  [T-183] 未完了で依存が未充足。**reasoning 面の採用を [T-316] / [T-665]/[T-662] の
  待ち解除根拠にしてはならない** (それらが待つのは canonical stage matrix と起動前 policy)。
  base: c9841b797c10169a137377783a75052e9846d1d2b73d570aa8970957480aefc6
