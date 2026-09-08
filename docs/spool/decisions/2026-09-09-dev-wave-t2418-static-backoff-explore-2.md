---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-09
wave: dev-wave-t2418-static-backoff-explore
seq: 2
---

## {{D:t2418-explore-run-kind}}. 探索走は凍結格子へ点を足さず、専用 RUN_KIND と専用 campaign identity で分離する

**決定:** D1813 が定めた静的 backoff 右側の探索は、認証済み格子 `EXTENDED_SWEEP_US` へ点を
足す形では実装しない。`orchestrator/campaign/backoff_extended_sweep.py` に第 3 の RUN_KIND
`t2418-explore` を足し、専用の `spec_slug` / `trial` / `scale` / report schema / 成果物 stem を
与えて正式系列と分離する。反復数と walltime 枠は共有経路のまま (`p2_2.REPS` / `p2_2.EXTIME` /
PBS 18000 秒) にし、テスト側は共有定数を参照せず literal で固定する。
成果物は `search_config` / JSON report / `.dat` provenance の 3 か所へ同値で開示する —
`run_kind`、`claim_scope`、`exploratory`、`formal_series`、`exploration_values_us`、
`formal_grid_status`、`formal_stopping_criterion_status`、`meaning_witness_status`、
`declared_use_class`、`reps`、`extime_s`、`records`、`threads`。
正しさ防壁は先例と同じ強さに揃え、静的 amount ごとの binary 相異検査は全点の完全性まで
fail-closed で要求する。

**理由:**
- `EXTENDED_SWEEP_US` は事前登録された認証格子で、上端が test に pin され、report 側が長さ・
  集合・index・隣接関係を意味に使う。ここへ探索値を入れると正式系列の意味が変わる。
- D1813 の「探索値を正式標本へ混ぜない」は、campaign identity の分離で実装するのが最短である。
  先例 `t2266-tail` が同じ形を既に採っており、族一般化を要さない。
- 反復数と walltime を共有経路のままにすることが「既存 sweep と同じ枠」の実体である。
  ただし共有定数から期待値を作るテストでは、定数が変わったときに全体が追随して裁定に反したまま
  緑になるため、literal で固定する必要がある。
- 探索だからと binary 相異検査の完全性を省くと、先例より正しさ検査が弱くなる (絶対規律 2)。
- 「探索」という語は、標本への帰属を指す D1813 の用法と、campaign layout の use class を指す
  runbook の `IZANAGI_EXPLORATION_OUTPUT_ROOT` の用法で別物である。成果物へ
  `declared_use_class` を載せて機械可読に区別する。

**却下した選択肢:**
- 凍結格子へ 3 点を足す — 認証済み格子の意味を変え、D1813 の分離要求にも反する。
- 既存 `t2266-tail` を一般化して両方を扱う — 凍結済みの成果物名と consumer に触れる risk があり、
  族一般化の独立 2 例条件を満たさない。
- 探索走を exploration output root へ移す — durability policy と declared use class が変わり、
  「既存 sweep と同じ枠」から外れる。
