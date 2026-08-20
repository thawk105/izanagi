---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-20
wave: enumerated-roaming-gizmo
seq: 1
---

## 新規

### {{F:author-child-cannot-dispatch-measurement}}. 段5 実装子 (workspace-write) に計算ノード dispatch を要する実測をさせ、権限不足で 530 秒・32 model call を空費した [手順漏れ] [コンテキスト浪費]

- 事象: 段4 裁定で「実装前に snapshot の bytes 内訳・copy wall time を実測するゲートを通す」ことを
  段5 実装子 (`--stage author`、`sandbox=workspace-write`) の prompt へ書いた。子は測定を試みたが
  `qstat -Q` が `ESYSCAL`/`EACCTAUTH: Unknown user-id` で rc=1 となり、計算ノード dispatch も
  bounded local 実行の preflight も完了しなかった。子は実装へ進まず作業ツリーを clean に保って
  正直に報告したが、`wall_clock_s=530.3`、`model_calls=32`、`cached_input_tokens=2,535,424` を
  費やした後だった。
- 根本原因: Codex 子の sandbox は socket 経由の scheduler 通信を構造的に拒む
  (既存 memory `codex-child-cannot-dispatch-or-write-outside`、`run-tests-bounded-local-bypasses-dispatch-latch`
  が同型の制約を既に記録していたが、本 wave の段5 prompt 設計時にこれを prompt へ反映しなかった)。
  `tools/run_tests.py` 経由のテスト実走・実測は親が行うものであり、実装子に委ねてよい作業ではない。
- 恒久対応: 既存 memory (`run-tests-bounded-local-bypasses-dispatch-latch`,
  `codex-child-cannot-dispatch-or-write-outside`) を、本 wave のように「実装子に測定ゲートを
  持たせる」設計をする際に必ず参照する。`docs/dev-wave/workers.md` の `DW-S05-C` へ
  「実装子に計算ノード dispatch や `tools/run_tests.py` 実走を要する事前測定をさせない、
  親が測定した数値を prompt へ渡す」旨を追加する候補を段8 へ送る (docs 予算が満杯のため
  即時反映はしない可能性が高いが、候補として記録する)。
- 再発検知: 実装子 prompt に「dispatch」「qstat」「tools/run_tests.py の実走」を要求する文言が
  無いかを、段5 prompt 作成直後に目視で確認する (機械検査は未整備)。
