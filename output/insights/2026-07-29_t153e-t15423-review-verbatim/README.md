# [T-153(e)] + [T-154(2)(3)] dev-wave 逐語・変異台帳 (凍結、2026-07-29)

親の裁定要約は `docs/worklog.md` 2026-07-29 (58)、設計判断は D98 が正本。
実装 commit は `9b26b3bd3acc10df95ef6ef6684a91d2ff3fa2ec`。

| ファイル | 役 | sha256 (凍結時) |
|---|---|---|
| `brief.md` | 段1 brief (親) | `821634ecef736dfbbde4b9288126f37b8ea0917b893b4e7596e6efe4b821b452` |
| `plan.md` | 段2 Codex plan | `2d3eed82566ec8b96ff366472fa2d011afe4ed5795398b641bd1f0fa9743a7ad` |
| `consult-a.md` | 段3 敵対相談 A | `b3754725c62c684755ea1d6f7c338cf70403b2f94a57dd58b4a4580b10c17841` |
| `consult-b.md` | 段3 敵対相談 B | `4905d63a99767bd4018ac296733d3db81e41ed400c16acabb632802531263c89` |
| `adjudication-plan-v2.md` | 段4 裁定・変異事前登録 (親) | `9e8208325ed27979f75b7d1c4b20b90a9220fa286f6a47fe5e81ef7bad45e7b5` |
| `author.md` | 段5 実装報告 | `bcc80162edd748a9300c6e4446febe744d2c806b27fc3f22e9a0eb61d67b81c8` |
| `review-a.md` | 段6 敵対レビュー A | `beea33ee7bb10acc583db30ef32252683c41fa3fe0ac3626db426103f5f102cc` |
| `review-b.md` | 段6 敵対レビュー B | `04bbe6fc8feedca29b67f7ea9c29587e60539538592f8b9efe6db3f46f770f8c` |
| `fix1.md` | 段6 fix 1 報告 | `e581c63399f20dbda51f223b05fbf4dadcf5e38961c9650dad2aca3756a39997` |
| `focus1.md` | 段6 焦点再レビュー 1 | `901ad02256524bac35c56ae4e3a2b7c5fbc01a618670182885040c6912b82771` |
| `fix2.md` | 段6 fix 2 報告 | `ffdff13cbe4d98aa56fe4502be63beb0a5acfb36c35a818b76462bb6f6d847cd` |
| `focus2.md` | 段6 焦点再レビュー 2 (GO) | `a738cd2979b3569dd90563e8f0931cd8badbc4b4cebe66129695bbb194fbe978` |
| `mutation-ledger.md` | 統合 commit 後の mutation 8 本 | `afb6c9ca5c237cac251cfdb175642d87c92ba9f064e75a3558753c7b9c2b6736` |

相談・レビュー5本は
`codex exec -m gpt-5.6-sol -c model_reasoning_effort="max" -s read-only`、
実装・fix3本は同 `reasoning="high"`・`-s workspace-write`。全成果物は
`tools/check_codex_output.py` で機械検収済み。read-only review は静的判定であり、
テスト実測の正本は親の worklog と mutation 台帳である。

placeholder gate は凍結前の `check_docs` で0新規hitを確認し、defangは不要だった。
mutation は8/8 KILLED、復元後に integrated commit とのbyte一致を確認した。
