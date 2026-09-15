# 段 4 裁定 追補 — 実測で判明した新事実 (2026-09-10)

段 6 の途中で計測 job を投入したところ、**私の変更とは無関係な既存経路の故障**が出た。
DW-S04 の「承認済み裁定の前提を覆す未見の新事実」に当たるので、ここで追加裁定する。

## 実測した事実

- 投入した 2 本 (`988653.nqsv` = rr95、`988654.nqsv` = rr5) は、どちらも計算ノードで
  **21 秒**で落ちた。`failure.json` は `stage=shell` / `rc=1` /
  `command failed at line 405`。405 行は `run_condition_gate` の実行行である。
- `condition-gate.stderr` の traceback は 2 本とも同一:
  `orchestrator/verifier/parse.py:71` の
  `SortPermutationMultisetState = bool | Literal["NOT_EVALUATED"] | None` が
  `TypeError: unsupported operand type(s) for |: 'type' and '_LiteralGenericAlias'` になる。
  実行中の interpreter は
  `/system/apps/.../oneapi/2022.3.1/intelpython/latest/lib/python3.9/` である。
- 原因は **interpreter の選び方**である。`certify_calibration.sh:393` の
  `condition_gate_argv` は素の `python3` で始まる。計算ノードの既定 `python3` は
  intelpython 3.9 で、repo のコードは 3.10 構文を使う。
- 同 script は **すでに python3.10 を smoke check して選ぶ処理を持っている** (824-841 行)。
  しかしそれは perf 選定の後、calibrator 起動の直前にあり、条件関門 (392-406 行、
  呼び出しは 590 行) より**後ろ**なので効いていない。
- 条件関門より手前の段 (依存 build、CCBench worktree 作成、静的 attestation、qstat 照会) は
  2 本とも成功している。job body の他の `python3` 使用は inline heredoc で repo の package を
  import しないため 3.9 で動く。壊れているのは 393 行だけである。
- **いつから壊れたか。** 3.10 専用の式は commit `3c9932591` (2026-08-20) が入れた。
  最後に成功した認証 calibration は `892707.nqsv` (2026-08-06)。この間に certification を
  通した者がいないため、今まで露見していない。

## 裁定

- **この修理は本題の scope 内である。** 依頼は「calibrator の既存経路で実測し accepted として
  登録するところまで」であり、その既存経路が壊れている。新しい gate・検査・台帳・一般化の
  追加ではなく、壊れている既存経路の修復である。修理なしでは成果物が 1 件も出ない。
- **条件関門は飛ばさない (規律 2)。** 関門を skip する、`|| true` にする、失敗を警告へ落とす、
  といった方向は採らない。**関門が正しい interpreter で走るようにするだけ**である。
- **最小差分は「選定ブロックの前倒し」。** 824-841 行の選定は自己完結しており
  (`CALIBRATE_PYTHON` と `calibrate_python_rejected` を設定し、失敗時に `write_failure` で
  fail-closed するだけ)、`$TMPDIR/bin` にも perf 選定にも依存しない。
  これを条件関門より前へ移し、`condition_gate_argv` の先頭を `"$CALIBRATE_PYTHON"` にする。
  選定の中身・smoke 内容・候補順・失敗時の挙動は変えない。
- **既存の受理集合・順序意味論は変えない。** 選定失敗時の `write_failure 2 interpreter` は
  そのままで、発火位置だけが早くなる。早くなること自体が退行にならないことを確かめる。
- **failures 台帳に記録する。** 「認証経路が 3 週間死んでいたのに誰も気づかなかった」は
  新しい失敗型である。段 7 で fragment を書く。

## 変異事前登録の追加 (DW-M01)

| ID | 位置 | 変異 | 期待 | 単一理由性の根拠 |
|---|---|---|---|---|
| M8 | `certify_calibration.sh` の `condition_gate_argv` | 先頭を `"$CALIBRATE_PYTHON"` から素の `python3` へ戻す | KILLED | 条件関門が repo package を import する interpreter を固定していることを見る検査だけが捕まえる |

M8 は計算ノードの実環境でしか本来の症状が出ないため、**静的検査で固定する**
(条件関門の argv が選定済み interpreter 変数で始まり、その選定が関門より前で
行われていること)。実環境の再現は投入し直した job の成否そのものが証拠になる。
