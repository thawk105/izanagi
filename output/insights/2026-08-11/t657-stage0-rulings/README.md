# [T-657] 段 0 残余 3 束の裁定実施 — 逐語と変異台帳

wave: `dev-wave-t657-stage0-rulings` / branch: `worktree-dev-wave-t657-stage0-rulings`。
設計正本は `docs/calibration-freeze-authority-bundle-design.md` (本 dir には複製しない)。
worklog エントリが状態の正本であり、本 dir は逐語の凍結である。

## 何を実施したか

worklog 403 のユーザー裁定 5 点 (U-A1 = 未発効 activation window / rollback = forward
compensating generation / revocation = 下位 authority へ fallback しない fail-closed /
下位 X_f は上位 X の後 / §8 と §10 の矛盾 = 段 0 完了判定から段 5 を除外) を、設計正本と
段 0 の機構 (裁定 profile・required gate・契約検査) へ反映した。

## 実施しなかったもの (裁定へ返した)

| ID | 内容 | 理由 |
|---|---|---|
| R1 | 失効 record の namespace・schema・commit topology | 裁定が答えたのは fallback の可否だけ。設計正本 §12.3 が「親が決めない」に置いた項目のまま。段 3 の 2 レンズが独立に「越権」と構成した |
| R2 | 段 0 完了の到達可能性 | §10.2 の第 1 条件が先送り確定の S と B を数えるため、先送りを維持する限り `complete` は到達不能。裁定時点で未見の新事実 |
| R3 | 段 6 の完了 predicate | 設計正本は新しいユーザー択一の存在を述べていない。gate を新設して既成事実化しない |

## 逐語 (`verbatim/`)

| file | 内容 |
|---|---|
| `s1-brief.md` | 段 1 brief。provisional (P1)〜(P4)。うち P1・P2 は段 4 で撤回した |
| `s2-plan.md` | 段 2 プラン (codex, reasoning=max) |
| `s3-sol.md` / `s3-luna.md` | 段 3 敵対 2 レンズ。**両方 NO-GO**。blocker 5 件 |
| `s4-ruling.md` | 段 4 裁定。所見 12 件の real/refuted と採否、変異事前登録 M1〜M6 |
| `s5-report.md` | 段 5 実装子の完了報告 |
| `s6-sol.md` / `s6-luna.md` | 段 6 敵対レビュー。sol = GO、luna = NO-GO (blocker 3) |
| `s6-fix-ruling.md` | 段 6 レビュー所見の裁定 |
| `fix-report.md` | fix 1 巡目 |
| `focus-report.md` | 焦点再レビュー。**1 巡目の fix 自身が作った抜け道**を blocker として検出 |
| `fix2-report.md` | fix 2 巡目 (comment 除去 → 存在の拒否へ) |

## 変異

- `mutation-spec.json` — 本走 spec (M1〜M7)。
- `mutation-ledger.json` — 本走台帳。**7/7 KILLED、全件が事前登録と一致**、baseline 緑。
- `mutation-ledger-discovery.json` — 影響範囲の広い M3 / M6 の失敗 node 集合を実測した discovery 走。
  この走の MISMATCH 2 件は期待 node が過小だったためで、検出漏れではない。

**erratum:** 段 4 は M3 (却下案 `post-activation-lease` を enum へ戻す) を
「state pin に隠れて SURVIVED」と登録したが、実測は **KILLED / 28 node** だった。
新設した「設計 §8.1 の許容 selection 列 ↔ `_SELECTION_ENUMS`」照合が先に落とすためである。
enum の縮小それ自体に独立した検出力が無いという段 4 の判断は正しく、誤っていたのは
**どの層が先に落とすか**の予測である。

## 主張しないこと

本 wave は帳簿 (裁定 profile・gate 表・設計正本) を裁定へ整合させた。**selection literal を読む
resolver は存在せず、policy を実装したのではない。** production
(`orchestrator/campaign/**`、`tools/**`) と case file 10 件の bytes は変更していない。
段 0 の status は `incomplete` のままで、`require_stage0_complete` は引き続き fail-closed である。
