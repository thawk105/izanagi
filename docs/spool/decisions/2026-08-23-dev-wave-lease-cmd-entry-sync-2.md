---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-23
wave: dev-wave-lease-cmd-entry-sync
seq: 2
---

## {{D:pegasus-runbook-lease-optional-followup}}. pegasus-runbook.md の受入 lease 規範は main 側で整合済み — follow-up タスクを起票しない

**決定:** `docs/pegasus-runbook.md` の受入 lease 関連記述を D662 (受入 lease 待ち行列廃止) へ
全面整合させる作業は、**本 entry の land 時点で main 側に着地済みである**。したがって
follow-up タスクを新規に起票しない。本 wave の scope は `.claude/commands/dev-wave.md` の
9 段状態機械 項 6 本文と、その機械 pin (`tools/check_docs.py`) の整合だけとする。

**理由:**
- 本 wave の段 3 敵対相談は、runbook の 958-961 / 980-988 / 1045-1051 / 1087-1104 / 1125-1129 行目
  付近の 5 箇所に「claim が `acquired` / `held-self` の場合だけ投入できる」という、D662 と矛盾する
  無条件の規範が残っていると指摘した。当時は T-1458 が未着地で `--lease-optional` の最終仕様を
  実装から確認できず、正確な改訂ができなかったため、follow-up として別 wave へ送る決定をした。
- **その後 main 側 commit `c5e81e0c` (`docs(dev-wave): DW-O27 と runbook §7.3 を待ち行列廃止後の
  現行契約へ揃える`) が同じ整合を完了させた。** 回収 wave (2026-08-23) が現行 main の runbook を
  読んで確認した — 958 行目付近は `acquired` / `held-self` / `held` (と旧版の `queued`) を投入し
  `stale-held` / `unavailable` を fail-closed とする現行契約に揃っており、1087 行目付近には
  「待ち行列 (待ち札) は無い。D662 で廃止し、2026-08-23 に `claim` から機構ごと除去した」が
  明記されている。
- 完了済みの作業を「未了」として台帳へ登録すると、pending task 集合が偽に増え、
  次に何を選ぶかの判断を誤らせる。回収 wave の独立監査がこれを blocker として指摘した。

**却下した選択肢:**
- **当時の文面のまま follow-up を起票する** — 完了済みの作業へ新しい T 番号が付く。
- **決定ごと台帳から落とす** — 「なぜ本 wave が runbook を触らなかったか」の理由が失われ、
  同じ scope 判断が将来また争点になる。決定は残し、結論だけを現況へ改める。

**残る負債:** 本 wave が固定した項 6 の文言は `--lease-optional` という **現在は後方互換の
no-op である flag** を代理指標として pin している (`DW-O27`)。「lease 取得可否で止めない」という
意味そのものを pin しているわけではない。意味ベースの pin への置換は
{{T:waiter-consumer-pin-hardening}} の射程に含める。
