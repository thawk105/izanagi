# T-1774 / T-1731 — JSONL の行分割を改行だけに限る (逐語凍結)

authority: none
default_effect: no-state-change

D971 の実装 wave の逐語凍結。可変状態の正本は `docs/worklog.md` 末尾と `docs/decisions.md` で、
この directory は査読・監査のための凍結スナップショットである。

- branch: `worktree-dev-wave-t1774-jsonl-line-split`
- 実装 commit: `bdc1b0cb42ffb7fb3fd2ab492b94847912019d8b`
- 変異走行の固定 commit: 上と同じ

## 中身

- `verbatim/brief.md` — 段 1 brief (親)。段 4 と段 6 の裁定が 2 箇所を訂正している。
- `verbatim/s2-plan.md` — 段 2 プラン (codex, read-only)。
- `verbatim/s3-A.md` / `verbatim/s3-B.md` — 段 3 敵対相談 2 本 (正しさ境界 / 整合・実効性)。
- `verbatim/ruling.md` — 段 4 裁定 (親)。確定した plan v2。
- `verbatim/s5-author.md` — 段 5 実装子 (codex, workspace-write) の完了報告。
- `verbatim/s6-R1.md` / `verbatim/s6-R2.md` — 段 6 敵対レビュー 2 本。
- `verbatim/ruling-s6.md` — 段 6 レビュー裁定 (親)。実測した受理差の表を含む。
- `verbatim/s6-fix.md` — 段 6 fix 子の完了報告。
- `verbatim/s6-refocus.md` — 段 6 統合後の焦点再レビュー。所見ごとの対応表。
- `mutation-spec-probe.json` — 全件 SURVIVED 期待の probe spec (観測 node 収集用)。
- `mutation-spec-final.json` — 本走 spec。6 負例 + 過剰拒否を検出する正例 1 本。
- `mutation-ledger.json` — 本走の台帳。baseline PASSED、7/7 KILLED、SURVIVED 0、MISMATCH 0。

## 実測値の要点

- 変更前後の受理差は、新規受理が U+0085 / U+2028 / U+2029 の 3 文字だけで、
  U+000B / U+000C / U+001C / U+001D / U+001E は変更前後とも拒否で差が無い。
  新規拒否は上記 8 文字を区切りに使った非 LF 区切り入力だけである。
- 封印済み codex event artifact `attempt-*.events.jsonl` 3,678 件を走査し、
  CR を含む file は 0 件だった。
- 親の焦点走は 8 file で 444 items、440 passed / 4 skipped、rc=0。
- 新規テスト file の直接実行は rc=0、12 passed。
