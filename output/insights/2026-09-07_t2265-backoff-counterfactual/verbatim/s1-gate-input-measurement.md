# DW-O13 — 改訂する exact 述語のゲート入力の実在と到達可能性 (親の実測)

測定日時: 2026-09-07 10:55 JST / base commit f486ff13c / 測定器:
`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-backoff-counterfactual/gate_input_probe.py` (read-only、repo 外)

## 改訂対象の述語

`tools/pegasus/probes/t2187_adaptive_const_probe.py:2495-2515` の
`_validate_backoff_trace_contract`。**既存 exact 述語の改訂で受理形を増やすので新設に当たる** (DW-O13)。

同型の shell 側述語が `tools/pegasus/probes/t2187_adaptive_const_probe.pbs:135-140` にある
(`CELLS_RAW != TRACE_CELLS_RAW` なら rc=2)。**2 層あるので片方だけ直すと不整合になる。**

## 述語が読む field と、現行で実際に取りうる値 (実測)

**訂正 (2026-09-07 11:25 JST、段 3 luna v2 の指摘):** 述語は raw 文字列と parse 済み tuple を**別々に**
比較する。下表で `args.*` は文字列、`cells` / `workloads` / `threads` は tuple であり、同じ値ではない。
実装は両方を連言で要求するので、**片方だけ直す改訂は受理域に穴を開ける。**

| field | 型 | 現行の実値 |
|---|---|---|
| `args.cells` | str | `cw:1:1:1000:2560:10000:10240:0:100:100:0,cw-as:1:1:1000:2560:10000:10240:1:1:4:0,cw-as-dyn:1:1:1000:2560:10000:10240:1:1:4:1` |
| `cells` | tuple[Cell, ...] | 上の文字列を `parse_cells` した 3 要素。`TRACE_CELLS` と exact 一致を要求 |
| `args.workloads` | str | `write-heavy,balanced,read-heavy` |
| `workloads` | tuple[str, ...] | `('write-heavy', 'balanced', 'read-heavy')` |
| `args.threads` | str | `24,48` |
| `threads` | tuple[int, ...] | `(24, 48)` |
| `args.rep_index` | 0 |
| `args.reps_per_job` | 1 |
| `args.extime` | 3 |

## 要求する値の到達可能性 (実測)

- 11 field cell `cw:1:1:1000:2560:10000:10240:0:100:100:0` → **ACCEPT** (extended=True)
- 12 field cell `...:1:1` → **REJECT** (`cell 0 must have five or eleven nonempty colon-separated fields`)
- 12 field cell `...:1:2` → **REJECT** (同上)

**したがって、反実仮想の腕を診断 trace 経路へ通す値は現行では到達不能である。** 到達させるには
`parse_cells` の受理形拡張が先に必要で、それが本 wave の実装対象そのものである。
到達不能な値を要求する述語を先に置いてはならない (DW-O13) ので、
**述語の改訂と parser の拡張は同一 commit に入れる。**

## PBS 側の判定 (実測)

`t2187_adaptive_const_probe.pbs:127-134` は `colon_text -eq 10`、すなわち **11 field のときだけ**
`HAS_EXTENDED_CELL=1` にする。実測: 既存 trace cell の colon 数 = 10、12 field cell の colon 数 = 11。
→ 12 field の非 trace 走行は `NEEDS_DYNAMIC_OUT` に反映されない (trace 走行は `BACKOFF_TRACE==1` で
別経路から 1 になるので隠れる)。

## 採用する述語の形

**訂正 (段 3 sol v2 の指摘):** 「受理域を緩めない」は集合論的に誤りだった。2 本目の literal を足すことは
**診断入力言語の受理集合の拡大**である。正しい言い方は次のとおりで、以後この表現を使う。

> **正しさゲート (correctness gate) は緩めない。** 直列性の認証が受ける 2 cell の exact 契約
> (`_certification_contract`) は 1 byte も変えない。**診断入力言語の受理集合は、
> exact literal ちょうど 1 本ぶんの制御された拡張を行う。** 拡張分は台帳に記録する。

**受理域を「緩め」ず、2 本目の exact literal を足す。**

- 受理: 現行の `TRACE_CELLS_TEXT` そのまま、**または** 新しい反実仮想用の exact literal 1 本
- 拒否: それ以外の全部 (混在、順序違い、label 違い、workload / threads / rep_index / reps_per_job /
  extime のいずれかが違うもの)

正例 (余裕を取る): 新 literal ちょうど 1 本。
負例 (発火自体が目的なので小さい差にする): 新 literal の末尾 1 文字違い、cell を 1 つ落としたもの、
既存 literal と新 literal を連結したもの、threads を `24` だけにしたもの。
