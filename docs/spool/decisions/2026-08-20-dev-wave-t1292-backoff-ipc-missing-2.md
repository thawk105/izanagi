---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-20
wave: dev-wave-t1292-backoff-ipc-missing
seq: 2
---

## {{D:g04-display-fix-not-new-capability}}. DW-G04 は既存コードの表示バグ是正には適用しない (backoff_sweep_report.py IPC欠測表示)

**決定:** `orchestrator/campaign/backoff_sweep_report.py` のIPC欠測表示バグ修正に
DW-G04 (条件付き機能の発火gate) は適用しない。既存の常時実行関数 (`report_workload`/`_md`)
が既に読んでいる値 (`g.li.get("ipc")`) の表示を正すだけであり、外部callerが無いと永久に
発火しない新規受理経路・権限機構・供給/結線ではない。

**理由:**
- `docs/decisions.md` のDW-G04先例20件超 (D120、D196/D215/D225等) はいずれも「外部caller
  が無いと永久に発火しない新規capability」(新規受理経路、権限activation、供給/結線) を
  対象としており、「既存の常時実行コードパスが表示するデータ整形を正す」型の事例は無い。
- 修正対象のコード分岐は本fixの前後を問わず、このモジュールが呼ばれるたび毎回実行される。
  追加されるのは新しいcapabilityではなく、既存経路内の1個のif/elseによるデータ表示の場合分け
  であり、DW-G04が警戒する「呼び手不在で永久に死ぬコード」とは性質が異なる。

**却下した選択肢:**
- 「新規テストで単体検証できるから発火条件を満たす」という論法での非適用主張 —
  段3敵対相談レンズが指摘したとおり、既存D120/D196/D215の先例は実在artifact/計測IDを要求
  しており、単体テストの検証可能性だけでは満たさない。この論法は根拠として使わない。
- 発火実績ゼロ (実campaign 5本・bench_done 26件でIPC欠測は現状0件) を理由に実装せず設計
  メモへ留める — 「未測定」が「measured 0」と誤読される研究上のリスクは、実際にIPC欠測が
  起きた時点で修正が無いと偽表示を出し続ける。既存の常時実行経路の表示不整合は発火実績を
  待たず正すべきと判断した。
