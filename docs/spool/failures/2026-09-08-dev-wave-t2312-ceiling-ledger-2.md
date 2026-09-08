---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-08
wave: dev-wave-t2312-ceiling-ledger
seq: 2
---

## 再発

### F35

- **再発: 2026-09-08** — [T-2312] (静的 backoff の符号化上限) を entry 1330 が実装・記録して
  着地させたのに、その同じエントリの次の一手が同項を `- [T-2312] (1329)` として carry し、
  1367 まで運ばれた。carry 鎖の実体本文は「1000 µs 以上の静的点は原理的に測れない」であり、
  着地後の main では偽である。型は従来 3 形態のうち**完了節への自 ID 明示漏れ**そのもので、
  新しい角度は無い。新しいのは被害の大きさで、**ユーザーがこの stale carry を根拠に
  「停止した先行 wave の成果を回収して着地させよ」という dev-wave を 1 本起こした**。
  検出は従来どおり dev-wave 段 1 の前提実測 (`DW-S01`) で、子を 1 本も起動する前に止まった
  (実装 commit `91a5bfca3` と記録 commit `ded2598bb` の main 包含、および編集面 17 file の
  main との内容照合)。機械防壁は無いままである。
