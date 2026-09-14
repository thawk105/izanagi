# 親の分析 1 — `configure-failed` の原因 (2026-09-14、実装面の変更ゼロで特定)

実測 1 (`measurement-1.md`) が出した `supply=red/configure-failed` の原因を、repo 内の一次資料と
コードだけで特定した。**計算ノードの再投入も、コードの変更も行っていない。**

## 機構 — gate は rc=0 でも stderr 非空を失敗にする

`orchestrator/campaign/condition_meaning_gate.py:1617-1622` (`_run_process`):

```python
if completed.stderr:
    raise ConditionMeaningGateError(
        failure_reason,
        f"successful process wrote stderr={completed.stderr[-500:]!r}; "
        f"argv={_bounded_process_argv_detail(run_argv)}",
    )
```

`_configure_compile_commands` (同 file 1683-1730) が `failure_reason="configure-failed"` でこれを呼ぶ
(1713-1715)。
**つまり CMake が configure に成功しても、stderr へ 1 byte でも書けば `configure-failed` になる。**

## 事実 1 — 素の CCBench に `BACKOFF_FIXED` の CMake option は存在しない

`external/ccbench/cmake/Options.cmake:20` にあるのは `CCBENCH_BACK_OFF` だけである。
`CCBENCH_BACKOFF_FIXED` は同 file にも `CMakeLists.txt` にも無い (grep hit 0)。
この変数は **izanagi の patch が供給する**ものである。

## 事実 2 — t316 は CCBench が使わない変数を 3 件渡している

`tools/pegasus/probes/t316_sandbox_backend_probe.py:1846-1862` の `configure` が渡す 22 引数のうち、
`external/ccbench` の CMake が一切参照しないもの (grep hit 0):

- `IZANAGI_GFLAGS_SRC_HEAD`
- `IZANAGI_GLOG_SRC_HEAD`
- `RULE_LAUNCH_COMPILE`

`_require_condition_gate` (同 file 1932-1956) は `-DCCBENCH_BACKOFF_FIXED=-1` だけを除いて
残りをそのまま `configure_args` として gate へ渡す。gate は requested 側で
`-DCCBENCH_BACKOFF_FIXED=-1` を足し直す (`_configure_defines`、1664-1681)。

## 事実 3 — この失敗型は 2026-09-02 に A-2 driver で実測・記録済み

`output/insights/2026-09-02/a2-condition-gate-patched-root/README.md:14-18` の逐語:

> 1. **patch 未適用 (直した).** 素の木に `CCBENCH_BACKOFF_FIXED` / `_NOINLINE` が無いため、cmake が
>    "Manually-specified variables were not used by the project" を **stderr** へ書く。
>    `condition_meaning_gate._run_process` は rc=0 でも stderr 非空を失敗にするので
>    `configure-failed`。

同 README の「一般化できる教訓」は、他 driver にも同じ未実行が残っている可能性を名指しで予告している:

> **義務化された関門は、driver ごとに実際に通したことがあるとは限らない.** 関門は T-1999 / D1198 で
> driver 全体へ義務化されたが、A-2 経路では 1 層目で落ちていたため 2 層目以降が一度も実行されて
> いなかった。層を 1 つ剥がすたびに次が出た。同じ形の未実行が他 driver にも残っている可能性がある
> (`backoff_sweep` / `backoff_repro` / `s1_direct_comparison` の inert 経路は未実測)。

## 事実 4 — 同じ警告本文が別の計算ノード記録に残っている

`output/insights/2026-09-10/t2515-rr95-rr5-calibration/job-evidence/988706-rr95-condition-gate.jsonl`
に、condition gate が捕らえた stderr の逐語がある:

```
Manually-specified variables were not used by the project:\n\n    CCBENCH_BACKOFF_FIXED\n    IZANAGI_GFLAGS_SRC_HEAD\n    IZANAGI_GLOG_SRC_HEAD\n
```

**3 件すべてが t316 の渡す変数と一致する。**

## 事実 5 — 緑へ到達した driver は未使用変数を 1 件も渡していない

`output/insights/2026-09-07_t2320-backoff-sweep-gate-layer2/liveness/liveness.json` の
`supply_records[0]` (計算ノード bnode039、driver = `orchestrator/campaign/backoff_sweep.py`、
`terminal_status=green`、`reason_code=stock-inert-preprocess-root-location-only`):

```
requested_configure_argv = [cmake, -S <wt>, -B <requested>,
  -DCMAKE_EXPORT_COMPILE_COMMANDS=ON,
  -DCMAKE_CXX_COMPILER=/usr/bin/x86_64-linux-gnu-g++-11,
  -DFETCHCONTENT_BASE_DIR=...,
  -DCCBENCH_BACKOFF_FIXED=-1]
```

引数は 10 個で、izanagi 固有変数も `RULE_LAUNCH_COMPILE` も無い。**この driver は patch 適用木
(`izanagi_wt_*/wt`) を `-S` に渡している。**

## 導かれる結論 (暫定、段 3 / 段 4 で攻撃する)

t316 実経路が `configure-failed` になる原因は 2 つあり、**どちらも単独で赤にする**:

- **(A) 素の木に `CCBENCH_BACKOFF_FIXED` が無い。** gate が requested 側で必ずこの変数を足すため、
  patch 未適用木では必ず未使用警告が出る。これは事実 3 の層 1 と同型である。
- **(B) `IZANAGI_GFLAGS_SRC_HEAD` / `IZANAGI_GLOG_SRC_HEAD` / `RULE_LAUNCH_COMPILE` を渡している。**
  requested 側でも control 側でも警告が出る。

## 規律 2 に触れる点 — 「直し方」は自明ではない

事実 3 の README は、この族の修正について先に警告している (同 README「一般化できる教訓」逐語):

> **「関門だけを通す」修正は偽の緑を作りうる.** 当初の既定方針は「patch 由来の cache 変数を、
> 定義しない木へ渡さない」だった。それを採ると requested と control の configure が構成上同一になり、
> inert 比較が自明に緑になる。さらに関門だけを patch 文脈へ入れると、関門は patch 済みの木を検査し
> campaign は素の木を build するという乖離が生まれる。**検査した木と build する木を一致させる**
> ことが、この族の修正の不変条件である。

したがって「(B) を除けば緑になる」は採れない。(A) が残るうえ、(A) を「patch 木を関門にだけ渡す」で
回避すると、t316 が build する木 (素の木) と関門が検査する木が食い違う。

**本 wave は実測が目的であり、この直し方の設計択一は scope 外である。** 実測結果として
「到達しない」と、その原因の構造を記録するのが本 wave の成果物である。

## まだ実測していないこと

今回の job が出した CMake stderr の**逐語**は見ていない。receipt は reason code しか保持せず
(D1849)、probe の `RuntimeError` メッセージも `terminal_status/reason_code` しか載せない
(`t316_sandbox_backend_probe.py:1967-1972`)。上記は事実 1〜5 からの構成的推論である。

A-2 経路では同じ問題に対して既に手当てがある — 同 README「副産物」逐語:

> 拒否メッセージが各 record の `evidence.detail` を保持するようになった。以前は
> `macro:arm:reason_code` だけで、計算ノード側の実際の stderr が捨てられていたため、
> 原因の切り分けに login node での再現が必要だった。

**t316 の `_require_condition_gate` にはこの手当てが入っていない。** 段 4 の裁定候補。

---

# 段 4 裁定による訂正 (2026-09-14、追記)

段 3 の 2 レンズが本分析へ出した所見を親が現物で検算し、**すべて real と裁定した**。
本文は当時の記述のまま残し、訂正を以下に追記する (正本は `s4-adjudication.md`)。

1. **「原因を特定した」は成立しない。(A)(B) は有力な仮説である。** 今回の job が出した CMake の
   rc・stderr を見ていない。`configure-failed` は起動失敗・rc≠0・rc=0 かつ stderr 非空の
   いずれでも出る (`condition_meaning_gate.py:1604-1622`)。どれかは未確定である。
2. **requested 側と stock 側のどちらで落ちたかは未確定。** requested が先に configure され
   (`_configure_compile_commands` の呼び出し順)、requested が失敗すれば stock は実行されない。
   したがって「両側でも警告が出る」という本文の記述を**撤回する**。
3. **事実 4 の 3 件は (B) の 3 件と一致しない。** t2515 の jsonl が挙げるのは
   `CCBENCH_BACKOFF_FIXED` と provenance 変数 2 件であり、`RULE_LAUNCH_COMPILE` は含まれない。
   `RULE_LAUNCH_COMPILE` が実際に警告を出すことは**裏づけられていない**。
4. **事実 5 は対照実験ではない。** driver・source・compiler・configure 引数がいずれも異なる。
   「別 driver が計算ノードで緑へ到達した例」であって、今回の赤を (A)(B) へ分解する根拠ではない。
5. **引数の数は 23 件。** `configure` のリスト要素は 28 件、`configure[5:]` が 23 件、
   `-DCCBENCH_BACKOFF_FIXED=-1` を除いた `filtered_args` が 22 件である。本文の「22 引数を渡す」は
   `filtered_args` の数であり、`configure[5:]` の数としては誤りだった。
6. **情報欠落の理由は D1849 ではない。** `_condition_gate_receipt_summary`
   (`t316_sandbox_backend_probe.py:320-354`) は digest・status・comparison を保持する。今回それが
   残らなかったのは、admission 拒否が例外になり summary 生成へ戻らないためである。
   D1849 は診断情報全般の保存を禁じてはいない。
7. **無限定な表現を限定する。** 「必ず」「到達しない」は、
   **今回の 1 allocation・`bnode040`・束縛 commit `3b80b5a96` では未到達**へ限定する。
   恒久的な到達不能を主張しない。
8. **後続走の証拠は初回 job の証拠ではない。** 今後 detail を取得しても、それは再現走の証拠であり、
   失われた job `0:996644.nqsv` の stderr 逐語にはならない。
