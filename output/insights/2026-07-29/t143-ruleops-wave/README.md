# T-143 dev-wave 構造化記録

このディレクトリは T-143 の親 brief、Codex worker の最終応答、親裁定、変異試験の訂正記録を保存する。
worker の `.md` は各 job の最終応答を逐語で固定したもので、進行中の巨大な `.log`、入力 prompt、
一時 patch、完了 marker、commit message は凍結対象に含めない。

最終判定の正本は `s6-r3-rereview.md`、変異試験の無効な初回 M3 と訂正の正本は
`mutation-run1-erratum.md`、全体の要約と恒久台帳への入口は一階層上の
`2026-07-29_t143-ruleops.md` と `2026-07-29_t143-ruleops-mutation-ledger.json` に置く。

`s6-r3-adjudication.md` だけは `git diff --check` の恒久 gate に合わせ、原文末尾の空行を
1 行除いた。原文は 1,155 bytes、SHA-256
`6165140125e5b4fc855235a46729ede563cb8344166b95e7840086e33ae3bea7` であり、保存版末尾へ
改行 1 byte を足せば原文を復元できる。本文の可視文字は変更していない。
