---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-10
wave: dev-wave-astra-medium
seq: 1
title: dev-wave の Codex worker を当面 GPT-6 Astra medium へ変更 (branch worktree-dev-wave-astra-medium)
---

## 本文

- ユーザー裁定: dev-wave で起動する Codex は、当面全段 `gpt-6-astra` / `medium` を使う。
  期限・自動復帰日は指定されていないため、次のユーザー指定まで継続する。
- 実装 worker の受領証で requested / recorded の双方が `gpt-6-astra` / `medium`、
  outcome=accepted、launcher_rc=0 を確認した。plan/consult の effort は caller 明示契約を保つ。
- 初回の関連走は 650 passed / 4 failed / 3 skipped。2 件は現行 docs を読む fixture を
  歴史 fixture と混同して旧値を取り残したもの。ほか 2 件は変更外の R33 宣言検査で失敗した。
  R33 の 2 件は個別再走で 2 passed。fixture 追随後の同じ関連 3 ファイルは
  654 passed / 3 skipped (154.91s) で通った。skip は既存の growth hold。
- 文書検査と Codex agent 検査、spool dry-run は rc=0。実装 worker は author と fix の 2 本。
  設定値の追随以外に scope を増やさず、dev-wave 改善候補はゼロ。

## 次の一手差分
