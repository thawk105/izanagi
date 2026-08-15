---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-16
wave: dev-wave-t851-fanout-exact-n
seq: 2
---

## 新規

### {{F:fanout-attestation-impossible}}. 正本 runbook が「無い」と実測記録した kernel field を、後発の gate が必須条件にした — 機構全体が一度も動かないまま land した [恒真ゲート] [テスト代表性]

- 事象: `tools/mutation_fanout.py` の admission は、measurement log の
  `max(samples)` を測定 cgroup の `memory.peak` と完全一致させることを要求する
  (`_attest_measurement_cgroup`)。この kernel (5.15) に `memory.peak` は存在せず、
  read が OSError になるため attestation は常に `False` を返す。**どの receipt も必ず拒否され、
  fan-out は 1 shard も起動できない。** receipt を作る producer 経路も CLI に無く、
  land から 5 日間、誰も本走を試みていなかったため発覚しなかった。
- 根本原因: `docs/pegasus-runbook.md` は 2026-08-01 実測として「この kernel に `memory.peak` は
  無い。専用 scope の `memory.current` を 3 反復以上 sampling して最大値を採る」を正本にしていた。
  gate はその 3 反復だけを取り込み (`MIN_CERTIFICATION_REPETITIONS = 3`)、
  runbook に無い kernel 再読を独自に足した。**正本を読んだ痕跡がある実装が、
  同じ正本が禁じた前提を持ち込んだ。**
- 検出できなかった理由: 既存テストは attestation callback を stub で差し替えるか、
  明示的に `False` を返す stub を渡す。**production の述語が実 kernel で真になりうるかを
  1 件も検査していない** (テスト代表性)。receipt も fixture で捏造するため、
  producer 不在も表面化しない。
- 恒久対応: {{D:fanout-unrunnable-here}} 決定 (2) — 環境依存の kernel interface を必須とする
  gate は、**その interface の実在を親が実データで 1 回通すまで完成と見なさない**
  (gate tool の live dogfood 規律と同じ扱い)。schema v2 を採る場合は、
  attestation が要求する各 kernel file の実在検査を、stub を使わない positive control として
  同じ commit に含める。
- 再発検知: fan-out を再設計する wave は、`_attest_measurement_cgroup` 相当の述語を
  **実 cgroup へ直接呼ぶ**テストを持つ。stub を渡す既存テストはこの検出力を持たない。
