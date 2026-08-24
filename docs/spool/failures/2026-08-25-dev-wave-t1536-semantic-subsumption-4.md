---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-25
wave: dev-wave-t1536-semantic-subsumption
seq: 4
---

## 新規

### {{F:codex-evidence-invalid-without-content-cause}}. `evidence_status=invalid` には内容に原因が無い 3 つ目の型があり、receipt からは発火条件を特定できない [恒真ゲート]

- 事象: 段 3 の敵対レンズ 1 本が `codex_exit_code=0` / `validator_rc=0` /
  `metering_status=complete` / `termination_verified=true` / 成果物 9,879 bytes 完全
  (`check_codex_output.py` rc=0、`## 総括` あり) でありながら、receipt が
  `evidence_status=invalid` / `accepted=false` / `launcher_rc=1` になり `-o` が書かれなかった。
  719.5 秒・41 model call・入力 434 万 token。
- **既知 2 原因を実測で否定した。** F217 (web 検索イベントの重複キー) —
  `attempt-0001.events.jsonl` に `web_search` を含む行は **0 件**、重複キーを拒否する
  strict parser で全行が通る (失敗 0 行)。F223 (非 NFC) — events.jsonl も rollout も
  **非 NFC 行 0 件**、prompt と成果物も NFC 正規である。
- 根本原因: 特定できていない。`tools/codex_worker_launch.py` の `_evidence_status()` は
  `stdout_invalid` / `stdout_pending` / rollout の `invalid` / `pending` /
  `session_meta_count != 1` / `context_count < 1` の**いずれか**で invalid を返すが、
  **どれが発火したかを receipt にも launcher-diagnostics にも記録しない**
  (診断 JSON を `pending` / `invalid` / `rollout` / `session_meta` / `context_count` で
  検索して 0 hit)。事後に rollout を検査すると `session_meta=1` / `turn_context=1` /
  strict parse 全通過で健全だった。**内容側の条件はすべて満たされている**ため、
  発火したのは読み取り時点の条件 (pending 系) と考えられるが、外からは確定できない。
- 恒久対応: 未実施。`_evidence_status()` がどの条件で invalid を返したかを receipt の
  attempt record へ 1 field 記録する改修を裁定パッケージへ回す
  (tool の出力契約を変えるため既成事実にしない)。それまでの回避は下記の再投入である。
- **回避 (実測で成功):** **同じ prompt を別の `--job-id` で 1 回だけ再投入する。** job-id は
  prompt の内容 hash から導かれるため、明示的に `--job-id` を渡さないと同一 job になる。
  本 wave では再投入が `launcher_rc=0` で成功した。**不採用の成果物を採用へ回してはならない** —
  内容検査が緑でも launcher の赤を迂回することになる。
- **再投入は同じ結論を返さない。** 本 wave では保全した 1 回目と再投入版が
  2 点で異なる結論を出した (ある変異を semantic kill と数えるか、harness 修理が族一般化条件を
  満たすか)。親は両方を一次資料へ当てて裁定し、片方ずつ採否を分けた。
  **不採用になった成果物を保全して読む価値はあるが、それを唯一の根拠にしてはならない。**
- 再発検知: `evidence_status=invalid` を見たら、まず F217 (events.jsonl の `web_search` 行数と
  strict parse) と F223 (events.jsonl / rollout の NFC) を**実測で**判定する。
  両方 0 件なら本エントリである。

## supersede 追記

- F223 **supersede: 2026-08-25** — `evidence_status=invalid` の原因は web 検索と非 NFC の 2 つだけではない。内容側の条件をすべて満たしても invalid になる 3 つ目の型を {{F:codex-evidence-invalid-without-content-cause}} に記録した。invalid を見たら 3 つとも判定する。
