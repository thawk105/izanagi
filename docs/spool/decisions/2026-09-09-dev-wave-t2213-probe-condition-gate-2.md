---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-09
wave: dev-wave-t2213-probe-condition-gate
seq: 2
---

## {{D:t2187-probe-condition-gate-deferral-maintained}}. adaptive const probe の条件関門は、実行時意味の witness と inert 実測が揃うまで配線しない

**決定:** `tools/pegasus/probes/t2187_adaptive_const_probe.py` の build sink 2 件は、
繰延べ台帳へ載せたまま維持する。次の 2 つが揃うまで配線しない。

1. この driver が使う 13 macro について、実行時意味の witness が
   `orchestrator/campaign/condition_meaning_gate.py` に存在すること。
2. patch stack を当てた木の inert 要求が supply effectuation の緑に到達することを、
   計算ノードの job で実測してあること。

配線する wave は、解除の証拠として検査の緑を使わない。関門呼び出しを除去する変異が
当該 sink だけを赤にすることを示す。

**理由:**

- 関門の受理規則は `require_condition_gate_family()` の
  `meaning_not_red = all(status in {"green", "unestablished"})` である。実行時意味の
  witness registry `CONDITIONAL_BRANCH_WITNESSES` にはこの driver の 13 macro が
  1 つも載っておらず、`declare_define_runtime_meaning()` は全件 `None` を返す。
  結果は全件 `unestablished` になり、そのまま admission を通る。
  配線しても実行時意味の腕は何も言わない。成果物が「3 要素の関門を通った」と
  読まれる一方で、条件が実行時の挙動を変えた証拠は 1 件も無い状態になる。
  絶対規律 3 (正しさシグナルを後付けにしない) に照らして、この状態で
  繰延べを解除するのは記録の格上げでしかない。
- 要求値が既定値または `DefineSpec.inert_values` に載る値のとき、supply の対照は
  patch を当てていない clean stock 木になり、前処理結果が位置差でなければ
  `stock-inert-mismatch` の赤になる。この driver の cell は必ず inert 値を含むため、
  緑になるかどうかが配線の成否を決める。これはこの 13 macro で一度も走らせたことがなく、
  未実測である。
- 関門は ccbench の CMake configure を本物で走らせるので、ccbench の依存一式を要する。
  親が既存 CLI で実測したところ、login node では `Could NOT find gflags` で configure が
  止まった。pinned source から /scr へ使い捨て static build する経路は計算ノードの
  job の中にあり、この実測は login node では行えない。
- 繰延べ台帳の certify 側 entry は、閉包検査が当該 sink を到達不能と分類するため
  現状まったく抑止していない ({{F:enclosing-scope-build-sink-hides-macros-from-closure}})。
  したがって「entry を消して検査が緑」を解除の証拠にできない。

**却下した選択肢:**

- 3 要素のうち supply effectuation と family admission だけを配線し、実行時意味を
  `unestablished` のまま通す — 未実測の inert 比較が赤に転べば driver が 1 cell も
  build できなくなる。論文の主要 driver を、実測しないまま止めうる変更にはできない。
- 実行時意味の witness class をこの wave で新設する — 他の driver も使う共有の
  正しさ防壁の改造であり、macro ごとの実行時 witness の設計・負例・変異が要る。
  依頼の「本題の結線だけ」を大きく超える。
- 繰延べ entry の理由文だけを実態に合わせて書き換える — 同 file を編集中の稼働 wave が
  在り、情報としての価値は台帳と insight で足りる。実装面へ触れる利得が競合の費用に見合わない。
