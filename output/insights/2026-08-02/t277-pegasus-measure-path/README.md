# [T-277] Pegasus 計測パスを開く — 一次資料

2026-08-02 の dev-wave (branch `worktree-dev-wave-t277-pegasus-measure`) が生んだ逐語一式。
可変状態の正本は `docs/worklog.md` の該当エントリ、設計判断の正本は `docs/decisions.md` の D122。
本 dir は凍結資料であり、訂正注記のみ追記できる。

## 何をした wave か

ユーザー裁定 (worklog (102) / archive (96) 択一 2 = (a)) の 4 項目のうち、**受理集合・env 契約解決・
build identity・attestation/no-resume を実装し、`/scr` namespace と claim/reservation による
`single_process` 強制は新事実つきで裁定へ返した**。成果物名は「Pegasus 計測パスの routing・
build identity・受理 gate の実装」であり、**live 計測の開通ではない**。

## ファイル

| ファイル | 中身 |
|---|---|
| `brief.md` | 段 1 親 brief (scope S1〜S5、不変条件、provisional 裁定 (P1)〜(P4)、前提実測) |
| `s2-plan.md` | 段 2 codex プラン (file:line 粒度) |
| `s3-lensA.md` / `s3-lensB.md` | 段 3 敵対レンズ 2 本 (ともに NO-GO) |
| `s4-adjudication.md` | **段 4 親裁定 (plan v2 と変異事前登録の正本)** |
| `s5-unitA.md` / `s5-unitB.md` | 段 5 実装子 2 本の完了報告 |
| `s6-revA.md` / `s6-revB.md` | 段 6 敵対レビュー 2 本 (ともに NO-GO、BLOCKER 4 件が収束) |
| `s6-fix.md` / `s6-fix2.md` / `s6-fix3.md` | fix 3 巡 |
| `s6-refocus.md` | 段 6 焦点再レビュー (3 度目の NO-GO、RF-1 / RF-2) |
| `s6-fix4.md` | B-f 全面撤去 |
| `s6-mutharness.md` | 変異 harness の設計と anchor 一意性検査 |
| `mutation-ledger.md` / `.json` | **変異本走の台帳 (10/10 KILLED、正例 SURVIVED)** |

## 読む順序

1. `brief.md` → `s4-adjudication.md` (裁定が plan と brief を上書きしている箇所がある)
2. `s6-revA.md` / `s6-revB.md` / `s6-refocus.md` (何が real と裁定されたか)
3. `mutation-ledger.md` (防壁が実際に効くことの証拠)

## 注意 (この資料を後から読む人へ)

- **親 brief の (P3) は撤回済み。** `certify_calibration.sh` の既存実績を生死確認の代替に
  しようとしたが、configure 条件も入口も異なるため成立しない (`s3-lensA.md` A-9)。
- **B-f (兄弟 driver への COMPUTE 拒否) は実装後に全面撤去した。** 理由は 3 つ —
  ユーザー裁定の項目でない / S-1 凍結ソース閉包を破る / 部分形が迂回可能な保証になる。
  経緯は `s6-refocus.md` の RF-1・RF-2 と `s6-fix4.md`。
- 子の完了報告は**自己申告**である。親が独立に裏取りした事実だけを worklog と D122 の根拠にした。
