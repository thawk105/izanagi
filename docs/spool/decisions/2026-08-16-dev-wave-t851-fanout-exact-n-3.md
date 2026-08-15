---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-16
wave: dev-wave-t851-fanout-exact-n
seq: 3
---

## {{D:fanout-unrunnable-here}}. 変異 fan-out の本走はこの機体で実行不能と確定し、gate を緩めて成立させない

**決定 (1):** `tools/mutation_fanout.py` の exact-N 本走は、実装の巧拙と無関係に
**この機体では実行できない**。admission の `_attest_measurement_cgroup` が
測定 cgroup の `memory.peak` を必須にする一方、この kernel (5.15) の cgroup に
`memory.peak` は存在しない。生きた `populated 1` の cgroup へ当該述語を直接呼んで `False` を実測した。
`run_fanout` は既定引数で attestation を固定し CLI に override は無いため、
**どの admission receipt も必ず拒否される**。計算ノードは PBS ジョブに user systemd session が
無く `systemd-run --user --scope` が成立しない (D180) ので代替実行面にもならない。

**決定 (2):** **正しさゲートを緩めて本走を成立させることを禁じる。** 具体的には
attestation の緩和、`memory.peak` 不在の警告化、certification 反復数の引き下げ、
test stub の production 混入、CLI からの検査 bypass のいずれも採らない。
これは絶対規律 2 の直接適用である。attestation を正本 runbook の測定手順へ揃える
schema v2 は**受理集合を変える**ため、親の裁量では実施せずユーザー裁定へ返す。

**決定 (3):** 環境依存の kernel interface を必須とする gate は、
**その interface の実在を親が実データで 1 回通すまで完成と見なさない**。
stub を渡すテストだけで land した gate は、恒偽でも緑になる。

**理由:**
- 正本 `docs/pegasus-runbook.md` は 2026-08-01 実測として `memory.peak` 不在を明記し、
  代替手順 (専用 scope の `memory.current` を 3 反復 sampling して最大値) を正本にしていた。
  gate はその 3 反復だけを取り込み、runbook が禁じた kernel 再読を独自に足した。
  食い違っているのは設計思想ではなく実装と正本の対応であり、修正は局所である。
- 本走が成立しないこと自体が採用可否の答えである。gate を緩めて「走った」という記録を
  作れば、certified 選択の材料である proof chain に、実在しない検証を通ったという値が入る。
- 段 3 の敵対 2 本が independently 構成した receipt 偽造経路 (無関係 sleeper、
  `..` を挟んだ同一 scope の別表記、identity object の複写) は、同一 Unix user を
  攻撃者とする族であり、プロトタイプ基準で見送り済みの族に属する。
  本決定はこの族を再裁定しない。

**却下した選択肢:**
- **attestation をこの wave で schema v2 へ直す** — 受理集合を変える変更を、
  「本走を成立させたい」という動機のもとで親が独断で行うことになる。動機と変更方向が
  一致する場面こそ規律 2 が禁じる形である。
- **`memory.peak` の代わりに kernel から読んだ値を `memory_current_bytes` sample として
  書き足す** (段 2 プランの案) — その時刻に存在しない観測を記録へ足す捏造であり、
  schema を変えずに別統計量を同名 field へ詰める意味拡張でもある。
- **fan-out を即時撤去する** — 実装 3,400 行超と契約テストを捨てる判断は、
  修正が局所である以上、ユーザー裁定を経ずに親が決めることではない。
