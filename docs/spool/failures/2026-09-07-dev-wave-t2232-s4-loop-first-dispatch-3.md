---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-07
wave: dev-wave-t2232-s4-loop-first-dispatch
seq: 3
---

## 新規

### {{F:pegasus-submit-recipe-omits-submodule-pin}}. 手順書の投入 recipe が実行体の前提条件を 1 つ書き落とし、逐語で実行すると決定的に拒否された [手順漏れ] [テスト代表性]

- 事象: `tools/pegasus/README.md` §7 の tagged qsub command を逐語で実行して段 4 loop の job body を
  投入すると、job body が `refuse "CCBench P3 S4 campaign pin mismatch"` (rc=2) で必ず止まる。
  job body も driver (`patchharness.assert_pinned_clean`) も CCBench の working tree が
  `p3_s4_loop.PIN` に exact 一致することを要求するが、recipe は「固定 SHA の専用 checkout」としか
  書いておらず、**submodule を PIN へ checkout する手順が無い**。main の gitlink
  (`511c9538e...`) は PIN (`028f34d`) の子孫であり、両者は一致しない。
- 根本原因: recipe を書いた wave は新規 Pegasus 実行体のため一度も投入せず (F660)、検証を
  login node の stub harness と契約テストで止めた。契約テストは job body の**本文**を固定するが、
  README の recipe を実行したときに前提が揃うかは検査しない。両者の間に検査の空白がある。
  gitlink は当該 wave の実装 commit の時点から前進しておらず、**recipe は着地時点から
  逐語実行できなかった**。pin の前進による腐りではなく、書き起こし時の欠落である。
- 恒久対応: 誤った pin のまま走ることは構造的に起きない — job body の rc=2 refuse と driver の
  `assert_pinned_clean` が二重に fails-closed で止め、本 wave でも実際に止めた。
  欠けているのは recipe 本文だけであり、その是正は
  {{T:pegasus-readme-submodule-pin-step}} で裁定待ちとして返した。
- 再発検知: 新しい job body を admission registry へ登録する wave は、README の投入 recipe を
  **逐語で 1 回実行して rc を記録する**。実行できない事情があるなら、recipe が要求する前提を
  1 つずつ列挙して job body の必須検査と突き合わせ、突き合わせた件数を段 1 brief に書く。
  0 件と書くならその根拠を示す。

## 再発

### F580

- **再発: 2026-09-07** — 段 4 loop の job body を初めて実際に投入したところ、(2) と同一症状
  `Could NOT find gflags` で masstree の FetchContent 事前構築が止まった (job `981655.nqsv`、
  host `bnode116`、Elapse 9S)。この job body は同 F の (1) にあたる `IZANAGI_RESERVATION_*`
  8 変数の export は正しく行っており、reservation 束縛も claim root の provisioning も通った。
  欠けていたのは依存の供給経路だけである。兄弟 job body `tools/pegasus/floor_scoping.sh` は
  policy の pin から gflags/glog を build / install し `CMAKE_PREFIX_PATH` を通しており、
  本 F の再発検知が求める「同種の既存 job body を 1 本名指しして、そこが行っていて自分が
  行っていない手順を列挙する」を実装 wave が段 1 brief で行っていれば、段 2 で見えていた。
  帰属と対応案は {{D:s4-job-body-lacks-gflags-supply}}、実装は
  {{T:s4-job-body-gflags-prologue}} で裁定待ち。
