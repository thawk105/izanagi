---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-25
wave: dev-wave-acceptance-pole-cost
seq: 2
---

## {{D:acceptance-pole-cost-only}}. 受入全走の直列 pole は費用側だけを下げ、直列性と分割数で解こうとしない

**決定:** 受入全走の wall-clock 短縮は、`real-repo` loadgroup の**直列性を緩めず、
その中の個々の node の費用を下げること**で行う。shard 数の増加と shard 間 balance の是正は、
現行の worker 数では律速を動かさないため既定の手段にしない。

**実測 (12 session、`/work/1/SFC/tanab/.izanagi-acceptance-shards/*/shard-*/report.json`):**
- shard-0 の 48 worker のうち 46 本は 119〜121 秒で揃って終わる。wall を決めているのは
  `real-repo` を 1 本で抱える worker で、12 session すべてで 227〜240 秒。
- 同じ 12 session で ideal (busy/48) は 97〜153 秒、shard-1 の pole は 71〜96 秒。
  遅い側と速い側の差は 181 秒ある。
- したがって pole > ideal が常に成立し、**shard を増やしても割付を直しても
  max(shard) は pole に張り付いたまま**である。K=3 へ投影した shard busy 平均は
  84.1 / 42.0 / 73.6 秒で、いずれも pole を大きく下回る。

**理由:**
- `real-repo` は「単一 pytest runner invocation 内で、親 repo status と共有 ccbench worktree の
  reader/writer を同じ loadgroup に閉じ込める」正しさ防壁である。速度を理由に分割すれば
  writer の patch 窓と reader が競合し、規律 2 (正しさゲートを緩める変異を許さない) に反する。
- 費用側を下げる手段は既に確立している。実 repo の高価な解決を process memo へ畳む型
  (受領証 memo と ratified freeze memo) は受理集合を変えずに効くことが実証済みで、
  本決定はその型を pole 内の残りへ適用し続けることを既定にする。
- 分割数を上げる案は、効かないだけでなく受入受領証の `env_projection` を変えるため
  受領証 pin に触れる。効果が見込めない変更で pin を動かすのは割に合わない。

**この決定が禁じないこと:**
- worker 数 (`IZANAGI_TEST_NPROC`) を下げた条件では K=3 が有利になりうる
  (K=2 の shard-0 平均下限 368.7 秒に対し K=3 は 252.3 秒)。worker 数側の再裁定は別に係属中で、
  本決定はその結論を先取りしない。
- K=3 の実走は artifact root の 241 report 中 0 件で**一度も測られていない**。
  「K=3 は絶対に速くならない」とは主張せず、未測定であることを明示する。

**却下した選択肢:**
- `real-repo` group を複数へ分割する — 直列性が防壁そのものであり、規律 2 に反する。
- 遅い node を既定の実行対象から外す — 検出力を失う。D312 が禁じる「閾値を満たすために
  検査を弱める」に該当する。
- shard 数を既定で 3 へ上げる — 実測に基づく効果が無く、受領証 pin を動かす副作用だけが残る。
