## 所見

- **F1 — must-fix — [launch_gate_liveness.py](/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_5-gate-liveness/author1-out/launch_gate_liveness.py:130)**: fix job は CI 比較の全体 build を先に `check=True` で実行する。pin 自体の build が失敗すると例外で終了し、修正案の trace run に到達しない。放置すると **(d) の数値が得られない**。**推奨:** trace run を先に完了し、CI 比較は失敗も結果に記録して続行する。

- **F2 — must-fix — [launch_gate_liveness.py](/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_5-gate-liveness/author1-out/launch_gate_liveness.py:136)**: CI 比較にも `STOCK_G.cmake_defines()` と `CCBENCH_TRACE=0` を渡している。上流 [build.yml](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-gen-opt-gate-liveness/external/ccbench/.github/workflows/build.yml:68) は両方を指定しない。放置すると **(d) に添える「上流 CI 相当」の主張が、実際に試した構成より広くなる**。**推奨:** CI 比較用の configure 引数を分け、上流の既定値で pin と pin＋修正を同条件で build する。

- **F3 — must-fix — [launch_gate_liveness.py](/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_5-gate-liveness/author1-out/launch_gate_liveness.py:183)**: 照合器の rc と JSON を保存するだけで、`indeterminate` や D1/D2b の違反でも job は成功終了する。stock の到達可能性が欠けたら smoke として止める事前登録とも異なる。放置すると **(a)〜(d) の判定不能または赤を、成功した job と取り違え得る**。**推奨:** job と workload ごとの事前登録条件を評価し、失敗理由を result.json に残して非 0 終了する。

- **F4 — should — [gate_check.py](/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_5-gate-liveness/author1-out/gate_check.py:203)**: D2b(ii) の `not-exercised` を「同じ key への複数回の書きがない」で決めている。しかし最後の書きと S の比較は、書きが 1 回でも実施できる。放置すると **(c)(d) で実際に検査した D2b(ii) を未発生と表示する**。**推奨:** ii の発生条件を「書きのある取引」にし、複数回の書きは別の発生件数として示す。

- **F5 — should — [instr-silo-gate-witness.patch](/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_5-gate-liveness/author1-out/patches/instr-silo-gate-witness.patch:8)**: `<vector>` の追加が `#if TRACE` の外にある。報告された「TRACE 枝を除いた bytes は pin と一致」は、この行を除去対象に含めた検査の意味に限られ、裁定の「すべて `#if TRACE` の内側」とは一致しない。放置すると **(a)〜(d) の数値自体より、非 TRACE build が pin と同一という一次資料の主張が不正確になる**。**推奨:** include も `#if TRACE` 内へ移す。

- **F6 — should — [test_gate_check.py](/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_5-gate-liveness/author1-out/test_gate_check.py:45)**: `test_valid_and_abort_attempt_excluded` の fixture には abort 行も abort 試行の手順もない。また退避済みの test は `parents[1]` を repo root とみなすため、この配置では単独再実行できない。放置すると **(a)〜(d) に使う照合器の abort 非混入を test 済みと主張できず、退避物の再検査も失敗する**。**推奨:** repo root を明示引数で渡し、abort を含む正例を追加する。

- **F7 — should — [launch_gate_liveness.py](/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_5-gate-liveness/author1-out/launch_gate_liveness.py:125)**: 依存物準備の `_prepare_build_dependencies` は、それ自体が stock の全体 build を 1 回行う。各 job の trace build と fix の CI build 2 回を合わせると、3 job で計 **8 build** になる。`-j` は計算ノードの利用可能 CPU 数で、2 node 時間内という見積りは示されていない。放置すると **(a)〜(d) が予算内に揃わない可能性がある**。**推奨:** この build 数と並列度で所要・資源の見積りを先に記録する。

- **F8 — should — [launch_gate_liveness.py](/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_5-gate-liveness/author1-out/launch_gate_liveness.py:186)**: tar.gz 作成後も trace dir を残す。生 trace が大きい場合、同一内容を二重に保持する。放置すると **(a)〜(d) の途中で容量不足となり、後続 run の結果を失い得る**。**推奨:** archive の作成と sha256 確認後に trace dir を削除する。

- **F9 — should — [s4-ruling.md](/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_5-gate-liveness/s4-ruling.md:21)**: 裁定は CCBench の TRACE 出力で `S` が未使用と確認するよう求めるが、既存 MOCC は `witness_<thid>.log` に `S` を使う。`gate_<thid>.log` とは別 file なので今回の parse 衝突は見えないものの、逐語の確認条件は成立しない。放置すると **一次資料で「S は未使用」と誤記する**。**推奨:** file を限定した名前空間として裁定と一次資料に明記する。

## 正しいと確認した点

計装の RMW 刻印は `val_` のコピー後、`update` 前に置かれ、S は writePhase の memcpy 入力から採られる。Q は commit 成功後に出力され、txid と thid の対応経路も整合する。B1 は一貫読みを維持し、commit 直前に実際の read set を調べる。修正案は read の探索順と再 update の body を変更し、既存の `op_`・`rcdptr_`・key を保つ。parse.py の key・write op・txid の型と照合器の使用も一致する。親の厳密適用検査と 13 件の自走 test は通過している。**build と計算ノードでの測定結果はまだない。**

## 総括

**NO-GO。** F1〜F3 を直してから投入する。現状では fix の測定が CI 比較で遮断され得て、判定不能や違反を成功 job として返し、CI 相当の構成も上流と異なる。