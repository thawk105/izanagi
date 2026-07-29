# T-146 dev-wave 構造化記録

このディレクトリは T-146 の親 brief、Codex worker の最終応答、親裁定、fix 前 snapshot の hash、
変異試験の機械可読台帳を保存する。worker の `result.md` は各 job の最終応答を固定したものである。

進行中の巨大な `run.log`、入力 prompt、完了 marker、commit message、pytest の一時 log、
一時 patch は凍結対象に含めない。
段7の凍結前にディレクトリ全体を D88 の exact-literal 3語で再帰走査し、hit 0 を確認したため、
可逆 defang と原文 erratum は発生していない。

最終実装判定の正本は `jobs/s6-focused-rereview/result.md`、段6裁定は
`s6-review-adjudication.md`、変異結果の正本は rc、FAILED / SKIPPED node、復元結果を含む
`mutation-ledger.json` である。全体要約は一階層上の
`2026-07-29_t146-probe-cleanup.md` に置く。

`jobs/s3-acceptance/result.md` と `jobs/s3-ownership/result.md` は `git diff --check` の恒久 gate に
合わせ、それぞれ空行1行から ASCII space 2 bytes を除いた。原文は順に 13,438 bytes /
SHA-256 `ccf6ef2eccd96916266aa399c73a5bbec1bbc5d76b5284270f28122afceb53b1` と
16,623 bytes / SHA-256 `bb0df1942b224887c95bfdb2ca1f6338c5b31eb0e21f0d588ac1ecef798ae0f5`。
各保存版の該当空行へ space 2 bytes を戻せば原文を復元でき、本文の可視文字は変更していない。
