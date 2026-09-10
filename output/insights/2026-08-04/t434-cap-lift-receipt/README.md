# [T-434] cap-lift receipt と consumer 結線の設計起草 (2026-08-04)

```
status: PROPOSED_UNRATIFIED
machine_effect: NONE
MAX_APPROVED_GENERATIONS: 1
depends-unratified: design-v2.md の設計択一 1〜10, [T-433], V1, [T-435]
```

dev-wave (背景 job、branch `worktree-dev-wave-t434-cap-lift-receipt`) の成果物一式。
ユーザー裁定 (worklog (175)) の「設計 wave が cap-lift receipt と consumer 結線の案を起草し、
裁定パッケージで返す」に対する回答。**実装差分ゼロ・起草のみ** (段 4 で「実装しない」を裁定、
遷移 `4→7→8→9`)。

| ファイル | 内容 |
|---|---|
| `design-v2.md` | **確定版設計案 + 裁定パッケージ (設計択一 10 件)。ユーザーはこれだけ読めばよい** |
| `s4-adjudication.md` | 段 4 裁定 — 全 24 所見 real、Q1/Q2 撤回・Q3 部分撤回の記録 |
| `brief.md` | 段 1 親 brief (逐語凍結。provisional 前提 Q1〜Q3 は段 4 で撤回・修正済み) |
| `s2-draft.md` | 段 2 codex 起草の初稿 (履歴。規範ではない — 事前登録正本の取り違え等を含む) |
| `s3-lensA.md` | 段 3 敵対レンズ A (恒真化・偽 receipt・self-attestation) 逐語 |
| `s3-lensB.md` | 段 3 敵対レンズ B (結線実在性・凍結整合・手続整合) 逐語 |
