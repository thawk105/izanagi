---
authority: none
default_effect: no-state-change
---

# [T-244] D121 P5 — provider 注入・role 間 session 共有・未予約 token の拒否 (逐語凍結)

本 wave の逐語スナップショット。**可変状態の正本ではない** — 状態の正本は `docs/worklog.md` の
末尾エントリと現行 phase doc であり、設計判断の正本は `docs/decisions.md` である。

## 何をした wave か

D121 決定 (7) の前提条件 P5 は 3 要件からなる。本 wave が実装したのは 2 件だけである。

| 要件 | 結果 |
|---|---|
| provider 注入の拒否 | **実装** — 実 Claude provider の試行に限り、caller 注入 `providers` を artifact 作成前に拒否する。`drive` / `preview` は未閉 (既存 2 テストが正当に注入しており、塞ぐと期待値変更が要る) |
| role 間 session 共有の拒否 | **実装** — 実行時 (4 role 共有 tracker) と成果物再検証 (`provenance.child_id` の非空・相互相異) の 2 層 |
| 未予約 token の拒否 | **未実装** — 要求されている token は origin/query slot の予約 receipt であり、発行主体の ledger は未実装 (同日の別 wave が敵対 2 レンズの NO-GO で差し戻した) |

**「P5 を満たした」とは名乗らない。** provider executable の真正性、process 境界、直接反復も閉じない。

## ファイル

| ファイル | 内容 |
|---|---|
| `brief.md` | 段 1 brief (親の provisional 裁定 (PROV-1)〜(PROV-5)。うち 3 件は段 4 で撤回された) |
| `s2-plan.md` | 段 2 プラン起草 (codex read-only)。**中核設計は段 4 で撤回済み** |
| `s3-lensA.md` | 段 3 敵対相談 レンズ A = 正しさ境界 (BLOCKER 4 / MAJOR 5 / MINOR 2) |
| `s3-lensB.md` | 段 3 敵対相談 レンズ B = 整合・実効性 (BLOCKER 3 / MAJOR 5 / MINOR 2) |
| `s4-adjudication.md` | 段 4 裁定 (real/refuted、plan v2、変異事前登録) |
| `s5-impl.md` | 段 5 実装子の完了報告 |
| `s6-revA.md` | 段 6 敵対レビュー レンズ A |
| `s6-revB.md` | 段 6 敵対レビュー レンズ B。**BLOCKER 1 件は親が実走で反証した** |
| `s6-fix.md` | 段 6 fix の完了報告 |
| `mutation-spec.json` | 変異事前登録 spec (9 変異。うち 1 件は冗長 gate として SURVIVED 期待) |
| `mutation-ledger.json` | 変異検査の実行台帳 |

## 段 3 が壊した中核設計 (記録として残す)

段 2 の起草は「呼び出し側が正式 token を提示したときだけ注入 seam を拒否する」設計だった。
レンズ A と レンズ B は**独立に**、token を発行できる面 (CLI) には注入口が無く、注入口のある面
(programmatic な公開関数) には issuer が無いため、**両者が交差せず gate が一度も発火しない**ことを
指摘した。親はこれを real と裁定し、正式判定を既存の provider 値へ移した。
同時に、journal と report へ receipt を書いて突き合わせる設計も落とした — レンズ B が下流 consumer を
全数調査し、それを読む consumer が 1 つも無いことを実測したためである。
