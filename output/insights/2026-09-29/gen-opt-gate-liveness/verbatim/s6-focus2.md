## 対応表

| 所見 | 判定 | 根拠 |
|---|---|---|
| N1 | closed | 判定器の rc 0・1・3 は、`results[0].verdict` のある JSON を確認した後、記録して事前登録評価へ進む。その他の rc と JSON 不正は例外となり rc 1。[起動器](/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_5-gate-liveness/fix2-out/launch_gate_liveness.py:243)、[判定器 CLI](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-gen-opt-gate-liveness/orchestrator/verifier/cli.py:105) |
| F3 | closed | B1 は判定結果にかかわらず事前登録評価を続け、fix は `serializable` かつ `certified` を要求する。両 workload のループも継続する。[起動器](/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_5-gate-liveness/fix2-out/launch_gate_liveness.py:118)、[同](/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_5-gate-liveness/fix2-out/launch_gate_liveness.py:264) |

## 新しい所見

なし。fix 2 が変更した箇所から、(b)(d) の読みを損なう新たな誤りは見つからなかった。

## 総括

**GO（静的点検）。** [fix-2.md の rc・JSON 対応表](/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_5-gate-liveness/fix-2.md:5)は実コードと一致する。B1 の non-serializable／indeterminate でも、両 workload の記録、照合器、事前登録評価が続く。fix の非 certified 判定は事前登録不一致となり、他の失敗がなければ rc 4 になる。CI build 失敗は rc 1、到達可能性失敗は rc 3 が優先する。[起動器](/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_5-gate-liveness/fix2-out/launch_gate_liveness.py:287)

`try` 内の例外では `result.json` を保存する。起動時の `try` より前の例外は対象外。[起動器](/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_5-gate-liveness/fix2-out/launch_gate_liveness.py:141) [同](/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_5-gate-liveness/fix2-out/launch_gate_liveness.py:297) 実走済み [stock 結果](/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_5-gate-liveness/runs/s1-stock/result.json:126)は両判定器 rc 0・事前登録一致で、今回の差分によって読みは変わらない。B1・fix 自体の実走確認はまだない。