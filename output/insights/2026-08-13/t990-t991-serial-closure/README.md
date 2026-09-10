# [T-990] / [T-991] — 実 repo 直列正本の閉包漏れと read-only 検査の optional index lock

2026-08-13、branch `worktree-dev-wave-t990-t991-serial-closure`。
worklog エントリは同日 fragment (`docs/spool/worklog/2026-08-13-dev-wave-t990-t991-serial-closure-1.md`)。

## この directory の中身

- `verbatim/` — 親 brief・親の確定事実・子成果物の逐語。改変していない。
  - `brief.md` 段 1、`parent-findings.md` 段 2 再投入時の親確定事実
  - `s2a-plan.md` / `s2b-plan.md` 段 2 (閉包の残件 + T-991 / 新設検査の設計)
  - `s3-lensA.md` / `s3-lensB.md` 段 3 敵対相談 (正しさ境界 / 整合・実効性)
  - `s4-ruling.md` 段 4 裁定 (本 wave の正本)
  - `s5-author.md` 段 5 実装、`s6-revA.md` / `s6-revB.md` 段 6 敵対レビュー
  - `s6-fix.md` / `s6-fix2.md` 段 6 fix 2 巡
- `mutation-spec.json` — 事前登録した 8 変異。sha256
  `22c12f1c1630c04daeba7944952a624b89537fe9ef50dd55c6b818414529d397`
- `mutation-ledger2.json` — 最終 commit `c968a1a7` での本走台帳。
  KILLED 8 / MISMATCH 0 / SURVIVED 0、baseline PASSED。

## 読む順序

1. `verbatim/s4-ruling.md` — 何を採用し何を却下したかの正本。
2. `verbatim/s3-lensA.md` の所見 1 — 閉包漏れの 3 件目 (conftest が名指しで除外していた canary)。
3. `verbatim/s3-lensB.md` の所見 1 — 新設検査案が D335 に該当するという指摘。
4. `verbatim/s6-revA.md` の所見 1・8 — guard の subdirectory 回避と証拠の混成。

## 一次資料としての注意

- **段 2 の 1 本目 (plan) は model call 上限で SIGTERM され成果物ゼロだった。**
  その receipt は `dev-wave-jobs` 側に残るが、成果物が無いので verbatim には無い。
  再投入した 2 本が `s2a-plan.md` / `s2b-plan.md` である。
- **子はいずれも pytest を走らせていない。** 子の報告中の「未実走」はそのままの意味で、
  実走は親が計算ノードで行った。結果は worklog fragment に記載する。
- 段 6 レビュー A は `user_properties` の干渉を `refuted` としたが、受入全走で real に戻った。
  逐語は当時の判断のまま残してある (失敗台帳の該当エントリを参照)。
