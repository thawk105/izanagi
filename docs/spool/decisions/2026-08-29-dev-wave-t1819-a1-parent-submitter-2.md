---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-29
wave: dev-wave-t1819-a1-parent-submitter
seq: 2
---

## {{D:a1-ccbench-acceptance-set-owner}}. A-1 の CCBench 受理集合は再凍結と同じ変更単位で決める

**決定:** A-1 の submit へ「CCBench の HEAD が canonical pin と一致し tracked clean である」検査を
足すかどうかは、**投入器の欠陥修正 wave では決めない**。D1262 が定めた新しい日付版の凍結 policy を
作る変更単位で、その事前登録の一部として決める。本 wave は実装せず、裁定パッケージとして返す。

**理由:**

- 受理集合をどこに引くかは study の事前登録の内容であって、投入器の実装細部ではない。
  D1028 が「型と consumer を同じ変更単位で作る」と定めたのと同じ理由づけである。
- 段 3 の敵対相談 2 本がいずれも、提案されたままの実装に反対した。A-1 と A-2 の受理集合を
  同じにすべきという一般化には根拠がなく、A-2 は認証 study、A-1 は非認証の探索 study である。
- 提案された plan は build 境界と consumer 検査を覆っておらず、そのまま足すと compute の
  preflight 後に dirty 化した source を machine-generated source として受理でき、
  「strict clean」という保証が発火しない。謳うだけの保証を作ることになる。

**却下した選択肢:**

- 本 wave で足す — 効く全層を覆えないまま受理集合を縮め、凍結前提を横から変える。
- 何も記録せず閉じる — 実測した 2 経路 (親 status を `ignore=all` で通過する経路と、
  allowlist 内 dirty source が generator receipt 経由で valid な結果へ入る経路) が失われる。

## {{D:a1-submitter-lives-in-the-driver}}. A-1 の投入器は driver の subcommand に置く

**決定:** A-1 の正式投入器は login 側 shell ではなく driver の `submit` subcommand に置く現行設計を
維持する。`tools/pegasus/submit_*.sh` に対応する A-1 用 shell は作らない。

**理由:**

- A-1 の job body 自身が「親が直接 qsub する。この file は投入器ではない」と宣言しており、
  設計はもともとそう決まっていた。
- A-2 が login 側 shell に投入器を置くのは 2 workload の fan-out と group receipt の fan-in を
  shell が担うためで、1 job の A-1 には対応する必要がない。
- 正式投入経路が機械防壁を通ることを read-only probe が rc=0 で実測した。塞がっていない。
- shell を足すと投入器が 2 経路になり、create-only の一回性をどちらが担うかが曖昧になる。

**却下した選択肢:**

- A-2 を手本に shell 投入器を新設する — 使い手の居ない 2 本目の投入経路を作る。
- Pegasus admission 登録簿へ driver の subcommand を登録する — 登録簿は `tools/` 配下の
  実行体を分類する仕組みで、driver の subcommand は管轄外である。
