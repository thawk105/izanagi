# [T-399][T-400] signal mitigation 実測 wave — dev-wave 逐語 (2026-08-04〜05)

- `authority: none`
- `default_effect: no-state-change`

可変状態の正本は `docs/worklog.md`。本ディレクトリは一次資料の凍結のみ。

| ファイル | 内容 |
|---|---|
| `brief.md` | 段 1 brief (survey 結論と scope。(P1)(P2)(P3) は段 4 で修正された) |
| `s4-adjudication.md` | 段 4 裁定 — 段 3 の blocker 9 / must-fix 10 の裁定、変異 G1〜G8 事前登録 |
| `verdict-preregistration.md` | 実測前凍結の判定式。erratum-1 (欠測 3 語彙)、erratum-2 (安全終端の操作化訂正) を併置 |
| `mutation-spec.json` | B-057 変異 spec (実測併合後の最終版) |
| `mutation-ledger-final.json` | 変異本走 G1〜G8 = 8/8 KILLED・期待 node 一致 |
| `mutation-ledger-v2-erratum.json` / `-v4-erratum.json` | 期待集合の実測併合前の初回台帳 (DW-M02) |
| `RESULT.md` | T-399 の凍結式判定 — mitigation 捕捉可能 = 成立、十分性 = UNKNOWN (R_restore_bound 待ち) |

probe evidence の正本は
`output/insights/2026-08-03_t361-t362-cluster-probes/evidence/20260804T125421Z-5e03df98c93b444e/`
(再評価 receipt と `superseded_evaluation` を含む)。

## 段 8 メモ (実装見送りの候補)

敵対レンズ prompt に F 番号を書く前に台帳見出しと照合する 1 文を `DW-S03` へ足す案は、
`docs/dev-wave/**` 集約予算 25,200 bytes に対し現在 25,196 bytes で**入らない**ため見送った
(上限引き上げは提案しない — T-127 / (169) V5 と同じ処置)。本 wave の実害は lens A の nit 1 件
(F36/F38 の取り違え指摘) に留まる。
