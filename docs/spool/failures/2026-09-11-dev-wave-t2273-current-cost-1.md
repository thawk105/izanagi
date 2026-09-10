---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-11
wave: dev-wave-t2273-current-cost
seq: 1
---

## 再発

### F57

- **再発: 2026-09-11** — T-2273着地再開の関連走と単独走でtest_limit_stop_is_never_acceptedの子終了codeが-15対期待0。fakeのterm_successがtoken_countを公開した後にSIGTERM handlerを登録する順序を確認した。初回mask案は準備中に停止猶予を使い切り-9となり撤回。Codex authorが同modeだけoutput/terminal/handler準備後にcount evidenceを公開する局所修正を行い、期待値と本番制限は不変。単独1passed、file直列211passed。並列file走の他mode3件は証拠待ちで赤だが直列では緑であり、この修正でF57全体が解消したとは主張しない。実体はorchestrator/tests/test_codex_worker_launch.pyの_write_fake_codex、証拠はoutput/insights/2026-09-10/t2273-current-cost/README.md。M1の子exit7変異は既存assertで検出された。
