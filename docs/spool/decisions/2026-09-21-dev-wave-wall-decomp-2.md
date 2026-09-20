---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-21
wave: dev-wave-wall-decomp
seq: 2
---

## {{D:mutation-probe-login-selfrun}}. 変異の期待 node は login self-run で観測し、dispatch probe は適用条件を満たさない test の fallback にする

**決定 (ユーザー依頼に基づく、docs のみ):** `DW-M08` の期待 node の観測は login self-run (変異ごとに注入 → test file の自走 harness → `DW-O19` に従い復元し sha256 も照合) を既定とし、dispatch final を 1 回走らせる。適用は自走の node 集合 (FAIL + ERROR) が `--collect-only` と一致し login 実行が許される test file に限り、pytest 専用 allowlist と、parametrize・conftest / autouse fixture・環境変数・import 副作用に依存する test は従来の dispatch probe (初回を probe と明記) へ戻す。KILLED 判定は変えない — dispatch final での期待 node 完全一致 (F33 / F71) が担い、観測誤りは MISMATCH か PARSE_ERROR の fail-closed に落ちる。併せて `DW-M05` に「final の待ちは job dir で確定済み本文と検査の準備に充てる (未測定欄・placeholder 禁止)」を置く。

**理由:**
- 直近 landed impl 7 wave の実測で、変異 probe の dispatch 走は実施 6 本平均 20.7 分 (13.6〜26.4)、うち qsub→ノードで script 開始までの待ちが 5〜17 分の外れ値として 84 job 中 8 件入る。fig13 wave の login self-run は 20 変異で 2 分、final は 20/20 一致した (1 file の実績)。
- self-run は観測法であって判定ではない。dispatch final の完全一致を残す限り、gate の受理集合は変わらない。
- 適用条件を事前に検査可能な形 (`--collect-only` との node 集合一致) で書かないと、自走と pytest で node が食い違う test を login へ投入して観測失敗か実行場所の規律違反を起こす (段 3 相談の所見)。

**却下した選択肢:**
- 全 test へ無条件に self-run を適用 — 二重 runner 契約 (F42) は harness の存在を検査するだけで pytest との同値性を保証しない。
- final も login で走らせる — `DW-M07` の dispatch 既定と login 拒否を変える gate の変更で、本 wave の scope 外。
- 変異 job の batching で probe を短縮 — harness の 1 job = 1 変異 receipt 束縛を変える構造変更で、裁定パッケージへ。
