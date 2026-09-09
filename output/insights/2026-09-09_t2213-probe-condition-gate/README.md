# [T-2213] adaptive const probe の build 地点を条件関門へ正配線する — 実装せず裁定へ返した

- wave: `dev-wave-t2213-probe-condition-gate` / branch `worktree-dev-wave-t2213-probe-condition-gate`
- 起点 main: `cbcdb6c91`
- 日付: 2026-09-09
- 結論: **本 wave では実装しない。** 依頼が名指した 3 要素のうち 1 つが構造的に存在せず、
  もう 1 つは実走しないと成否が決まらず、その実走はこの計算機の login node では行えない。
- 実装面の差分: 0 件。本 wave は docs だけを書いた。

## 依頼と、確かめよと言われたこと

`tools/pegasus/probes/t2187_adaptive_const_probe.py` の build 地点 2 箇所を、
`orchestrator/campaign/backoff_sweep.py` と同じ型の条件関門 (supply effectuation +
runtime meaning + family admission) へ正配線し、繰延べ台帳から当該 entry を外す。
依頼は「台帳 entry の理由文が解除条件を持つので、まずそれを読んで満たしているか確かめる」
と指示していた。

## 台帳 entry と解除条件 (読んだ結果)

繰延べ台帳の実体は `orchestrator/tests/test_ccbench_spawn_sites.py` の
`_DEFERRED_GATE_MEMBERS`。probe の entry は 2 件ある。

| # | sink | 理由文の要旨 | 解除条件の有無 |
|---|---|---|---|
| 1 | `<module>._certify_main._build_trace_binary` (buildcache) | certify mode の A+B+C stack の build。「**condition-gate family admission は本 wave の scope 外**」 | あり (scope) |
| 2 | `<module>.main` (buildcache) | performance / diagnostic build は certify の exact cell 契約と分離される | なし |

entry 2 は当初から在ったものではなく、[T-2265] の commit `6cca0bc69` が後から足した。

**文言としての解除条件 (entry 1 の「本 wave の scope 外」) は、本 wave がそれを scope に
入れた時点で満たされる。** しかし理由文に書かれていない技術的な前提が 2 つ満たされていない。
以下はすべて親が現物のコードで確認した。

## 満たされていない前提 1 — runtime meaning はこの driver の macro に存在しない

`orchestrator/campaign/condition_meaning_gate.py` を読んだ結果:

- 実行時意味の witness registry `CONDITIONAL_BRANCH_WITNESSES` に載っているのは
  `BACKOFF_NOINLINE` と 11 個の `IZANAGI_BREAK_*` だけである。
- `MeaningWitnessDeclaration` は `__post_init__` で macro を 1 つの値にしか許さない。
- したがって `declare_define_runtime_meaning()` は、この driver が使う 13 個の macro
  (`BACKOFF_INCR_MILLI`, `BACKOFF_MAX_US`, `BACKOFF_UPDATE_US`, `BACKOFF_COUNT_WINDOW`,
  `BACKOFF_COUNT_CAP_US`, `BACKOFF_STEP_ADAPT`, `BACKOFF_STEP_MIN_MILLI`,
  `BACKOFF_STEP_MAX_MILLI`, `BACKOFF_DYN_CEILING`, `BACKOFF_TRACE`,
  `BACKOFF_TRACE_TERMINAL_US`, `BACKOFF_STEP_POLICY`, `BACKOFF_STEP_POLICY_SEED`)
  すべてについて `None` を返す。
- `None` は `unestablished` の record になる。
- `require_condition_gate_family()` の受理規則は
  `meaning_not_red = all(record.terminal_status in {"green", "unestablished"})` である。
  **`unestablished` は受理される。** `use_class` を `certified-selection` にしても変わらない。

**つまり、依頼どおりに配線しても、runtime meaning の腕は 13 macro 全件について
何も言わないまま admission を通る。** 3 要素のうち supply effectuation と family admission は
実物になるが、runtime meaning は名前だけになる。成果物 (certified receipt、性能 JSON、
診断 JSON) が「3 要素の関門を通った」と読まれる一方、条件が実行時の挙動を変えた証拠は
1 件も無い状態になる。これは絶対規律 3 (正しさシグナルを後付けにしない) の趣旨に反し、
下流の裁定材料としては空である。

この腕を本物にするには、macro ごとの実行時 witness (刻み・上限・更新間隔・count 窓・
step 適応・ceiling・trace 有無・policy・seed) を新設し、witness class 自体を拡張する必要がある。
これは **他の driver も使う共有の正しさ防壁の改造**であり、「本題の結線だけ」という
依頼範囲を大きく超える。

## 満たされていない前提 2 — inert 要求の成否が未実測で、login node では測れない

`evaluate_define_supply_effectuation()` は、要求値が既定値と等しいか
`DefineSpec.inert_values` に載っている場合、比較対象を **patch を当てていない clean な
stock 木**にする。前処理結果が位置情報だけの差でなければ
`stock-inert-mismatch` の赤になる。

この driver の cell は必ず 1 つ以上の inert 値を含む (例: `BACKOFF_MAX_US=1000`)。
したがって「A+B+C patch を当てた木の前処理結果が、inert 値において clean stock と
位置差だけか」が緑/赤を決める。**この問いは誰も実測していない。**
この 13 macro でこの関門を走らせた driver が今まで無いからである。

親は既存 CLI (`python3 -m orchestrator.campaign.condition_meaning_gate`) を使って
実測を試みた。手順は probe と同じで、pin `511c9538e4e8efa54b45cda62e72389ed3b706ec` の
`--shared` clone に A→B→C を適用した木を `--source-root`、wave worktree の clean な
pinned 木を `--stock-root` にした。結果は次のとおり (逐語は
`verbatim/liveness-cli-stdout.json`)。

```
rc=2
supply-effectuation の evidence.detail =
  process returned rc=1; stderr=CMake Error ... Could NOT find gflags
  (missing: gflags_LIBRARY_FILE gflags_INCLUDE_DIR)
```

**これは失敗ではなく、実測された事実である** — 条件関門は ccbench の CMake configure を
本物で走らせるので、ccbench の依存一式 (gflags / glog / masstree) を必要とする。
`docs/pegasus-runbook.md` によれば計算ノードに gflags / glog は無く、pinned source から
/scr へ使い捨て static build する (certify が自動実行)。login node にも無い。

したがって **前提 2 は計算ノードの job の中でしか確かめられない。**
同型の未解決項が既に台帳に在る — [T-2505] は「t316 driver 自身が
`stock-inert-preprocess-root-location-only` の緑に到達する環境を、commit を束縛した
計算ノード probe で実測する」ことを求めており、現在の根拠は別 driver の記録であって
実経路の実測ではない、と書いている。本件は同じ形である。

## 副産物 — 配線の形自体は既に repo に在る

依頼は `backoff_sweep.py` を参照実装として挙げたが、より近い先例が
`orchestrator/campaign/screening_driver.py` に在る。同 file は
`_condition_requests_for_genome()` / `_require_requests_match_genome_build_arguments()` /
`_condition_gate_base_configure_args()` / `_run_condition_gate_for_genome()` を持ち、
**genome の flags から要求を導出する**という、親が段 1 で立てた不変条件と同じ形を
既に実装している。将来この配線を行う wave は `backoff_sweep.py` ではなく
こちらを型にするのが近い。ただし `expected_toolchain_manifest` と
FetchContent base の受け渡しが要る。

## 併走 wave (T-2417) について

起動時の重複検査で `dev-wave-t2417-policy-arm-perf` が生きていることを実測した
(対象 3 file すべてで merge 競合中、job の段 6 fix 子が同日 07:21 に完了)。同 wave は
probe を 315 行変更し、繰延べ 2 entry の行番号を更新し、entry 2 の理由文へ
「trace 無効の policy 腕契約経路も同じ sink を通る。」を追記している。
本 wave は実装面を 1 行も変えていないので、この併走は結果に影響していない。
将来この配線を行うときは、同 file を触る wave と直列化するのが安い。

## 親が犯した誤り (子が訂正した)

- 段 1 brief で失敗台帳の番号を `F1402` と書いたが、関門が発火しない 8 型の正本は **F794** である。
- 段 1 brief は sink 2 を「trace 無効の性能 build」とだけ書いたが、診断 mode では
  同じ sink が `BACKOFF_TRACE=1` の計測用 binary も作る。
- 段 1 brief の不変条件 3 (`DEFINE_SPECS` との積集合で要求を作る) は過大だった。
  積集合を取るだけでは registry 外の flag が黙って落ちる。
- 繰延べ台帳の sink 1 は、現行の閉包検査では到達不能と分類されており、
  entry を消して緑になってもそれは関門が効いた証拠にならない。

## この insight が保証しないこと

- 前提 2 (inert 要求が緑になるか) は**未実測**である。赤になると断定していない。
  login node で configure が依存不足で止まったという事実だけを実測した。
- 本 wave は凍結成果物を作っていない。測定値も出していない。
