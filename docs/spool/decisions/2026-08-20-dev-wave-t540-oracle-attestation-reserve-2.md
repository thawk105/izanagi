---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-20
wave: dev-wave-t540-oracle-attestation-reserve
seq: 2
---

## {{D:oracle-reservation-probe-term-no-plus-one}}. oracle 完走予約式へ attestation probe 項を足す際は「+1」を使わない

**決定:** `orchestrator/campaign/s8b_oracle_driver.py` の完走予約式 2箇所
(`_reservation_required_s`・`_recheck_required_execution`) へ attestation probe 所要時間項
(`ORACLE_ATTESTATION_PROBE_S = 0.2`) を追加する際、どちらの式も `+1` を使わず
`len(schedule)`/`remaining_rows` だけを掛ける。

**理由:**
- `orchestrator/campaign/reservation.py` の `check_reservation`/`ensure_remaining` は
  いずれも「呼ばれた時点から先」だけを見積もる設計 (`remaining = deadline_epoch - now` /
  `monotonic_deadline - now`)。
- 初回予約検査 (`_prepare_v2_execution` 内、driver.py:925付近) は、903行の初回 attestation
  probe が実行された**後**に呼ばれる。この時点で 903行の probe が消費した時間は、
  `remaining` の計算に経過時間として既に自動反映されている。
- ここへ `(N+1)×0.2` を明示的に加算すると、903行分の probe 時間を二重計上することになり、
  scheduler 割当て (`requested_s`) が必要量ぎりぎりの境界ケースで、正当な実行を新規に
  拒否しうる (fail-closed を不必要に厳しくする、規律2の趣旨に反する過剰拒否)。
- recheck 側 (`_recheck_required_execution`) も同様に、`ensure_remaining` の直後
  (driver.py:1083付近) で今回分の probe が実行される。「これから発生する probe 回数」は
  ちょうど `remaining_rows` 回 (今回の1回 + 残り行の各1回) であり `+1` は不要。
- schedule 全体で見ると、903行の1回は「経過時間の自然な反映」、初回検査以降の N 回
  (各行 recheck の probe) は「明示的な安全マージン」でカバーされ、合計で N+1 回分の
  probe 時間を過不足なく見積もる。

**却下した選択肢:**
- 両式とも `(N+1)×0.2` を明示的に加算する (段2 codex plan の当初案) — ユーザー裁定
  「行数 N で最低 (N+1)×0.2 秒」の字面には近いが、二重計上により過剰拒否を生む。裁定の
  実質的な意図 (N+1 回分の probe 時間を下回らない安全性) は `+1` なしの実装でも満たされる
  (段4 裁定で reservation.py を実測し、代案の等価性を確認した上での判断)。
