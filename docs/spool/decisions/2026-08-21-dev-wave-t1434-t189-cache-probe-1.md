---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-21
wave: dev-wave-t1434-t189-cache-probe
seq: 1
---

## {{D:t189-cache-control-measured-infeasible}}. T-189 provider cache 制御可能性を実測し、制御不可能と確定した

**決定:** Codex CLI (`codex exec`)・Claude CLI (`claude -p`) のいずれも、provider 側 prompt
cache の reset・namespace・cold/warm 明示制御を行う CLI 引数・環境変数を持たないと実測で確定した。
ローカルな isolation (`CODEX_HOME` の新規作成、`--no-session-persistence`) は provider 側 cache に
一切影響しない。Codex は「同一 thread を `resume` で継続するか否か」だけが cache の温度を左右し、
task 固有内容は独立呼出し (新規 thread) をまたいでは cache されない。Claude は逆に、一度送信した
内容はプロセス・session の独立性に関わらず TTL 内 (既定 `ephemeral_1h`) で確実に cache から読まれる。
T-189 §9 (段6所見 B5) が定める「制御できない場合 resource 指標を `not-applicable` とする」既定を
維持・確定する。`routing_evidence_status` (D640) は本決定だけでは変わらず `inconclusive` のまま。

**理由:**
- `codex exec --help`/`codex exec resume --help`/`codex exec fork --help`/`claude --help` の
  全オプションを走査し、cache 制御に該当する CLI フラグが存在しないことを確認した
  (Claude の `--exclude-dynamic-system-prompt-sections` は cross-user cache 再利用が目的で
  cold/warm 制御ではない)。
- Codex 8 回・Claude 3 回の実 CLI 呼出しによる直接測定が、新規 `CODEX_HOME`・新規 session・
  新規プロセスのいずれも provider 側 cache を reset しないことを一貫して示した (生ログ・詳細は
  `output/insights/2026-08-21_t1434-t189-cache-control-probe/`)。

**却下した選択肢:**
- `CODEX_HOME`/session ID の独立性を cache 分離の代替根拠として採用する — 実測で provider 側
  cache に一切影響しないと判明したため、これを cold 条件の根拠にはできない。
- 本 wave で resource `not-applicable` 抑止ロジック自体 (§12 判定表の評価器) を実装する — 判定器
  本体が未実装のまま抑止だけを作ると D640 がすでに却下した「未使用の飾り」を再発するため、
  本 wave でも見送る。
