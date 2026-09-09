---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-09
wave: dev-wave-t2224-certify-protocol-axes
seq: 3
---

## 新規

### {{F:script-wrapped-heavy-command-evades-login-guard}}. 背景 script に包んだ重量 command が login 判定をすり抜けた [手順漏れ] [恒真ゲート]

- 事象: 親が生死確認のため CCBench を login node でビルドした。`cmake --build` を直接叩くと
  `hooks/guard_bash.py` が「Pegasus ログインノードでは重い処理を実行できません」と拒否することは、
  後から実測で確認した。しかし実際の起動は dev-wave の背景投入の定型
  (`nohup setsid bash <script>`) で行ったため、guard が見るコマンド本文に `cmake` が現れず、
  分類されないまま login で 4 protocol 分の build と 3 回の再ビルドが走った。
- 根本原因: guard は Bash tool へ渡されたコマンド**文字列**を分類する。script の中身は見ない。
  `DW-O01` が定める背景投入の形は必ず `bash <script>` になるため、**script に包めばあらゆる重量
  command が分類対象から外れる**。防壁の射程と、規定の起動導線が構造的に食い違っている。
- 恒久対応: 実行場所の判定は script の中身に対しても効く必要がある。実施形は
  {{D:certify-protocol-axis-table-stays-independent}} の範囲外なのでユーザー裁定へ返す。
  本 wave では、以後の実測を `tools/pegasus/dispatch_compute.py --task generic` の計算ノード経路へ
  載せ替え、login で取得した値には取得経路が正規でないことを成果物へ明記した。
- 再発検知: なし (宣言だけの対応にしないため、実体を持つ検査はユーザー裁定の後に置く)。

### {{F:mandated-condition-gate-cannot-pass-on-unpatched-pin}}. patch 由来 define の条件関門が、patch を materialize しない driver では構造的に通らない [恒真ゲート] [誤前提]

- 事象: 認定 launcher `tools/pegasus/certify_calibration.sh` と同じ argv で
  `orchestrator.campaign.condition_meaning_gate` を実走したところ rc=2、`admitted=false` で、
  2 アームとも red だった。`supply-effectuation` は `configure-failed` で detail が CMake の
  「Manually-specified variables were not used by the project: CCBENCH_BACKOFF_FIXED」、
  `runtime-meaning` は `materialized-branch-invalid` で detail が
  「unique BACKOFF_FIXED conditional is unavailable」である。
  `run_condition_gate` は `set -Eeuo pipefail` 下の裸の関数呼び出しなので、job は configure 前に
  rc=2 で止まる。
- 根本原因: `CCBENCH_BACKOFF_FIXED` は `patches/silo-backoff-fixed.patch` が
  `cmake/Options.cmake` と `include/backoff.hh` へ供給する define である。launcher は pin された
  CCBench の素の detached worktree をビルドし、patch を materialize しない。
  **供給していない define を渡しているので、供給と実効化を見る関門は正しく拒否している。**
  D1198 が義務化した関門の射程に、patch を当てない driver が入っていた。
- **独立 2 例目である。** 同じ `runtime-meaning` 赤を
  `output/insights/2026-09-09_t2397-a1-pilot-attempt-0003/README.md` §6.2 が A-1 driver
  (`orchestrator/campaign/paper_story_a1_paired.py`) で先に記録している。原因 (marker が patch 側に
  あり pin された CCBench に無い) も同一で、driver だけが異なる。
  `supply-effectuation` の原因は 2 例で異なり、A-1 は関門へ configure 引数を渡していない
  (F580 の 3 例目)、本件は引数を正しく渡した上で macro 自体が供給されていない。
- 一次資料: 認定 attempt 12 件 (`output/env/pegasus/calibration/job-staging/`) すべてに
  `condition-gate.jsonl` が無く、この関門は認定経路で一度も実走していない。
  `calibrate_rc=0` の 2 件は関門導入 commit `0218acc61` より前である。
  job `0:892707.nqsv` の `configure.stderr` には当時から同じ未使用変数警告が出ている。
- 恒久対応: 認定 launcher が `-DCCBENCH_BACKOFF_FIXED=-1` を渡し続けるかはユーザー裁定へ返した
  (実測では、この flag の有無で silo バイナリの sha256 は完全一致する)。
  本 wave は新 protocol へこの define を広げないことを
  {{D:certification-records-only-values-that-reach-the-compiler}} で固定した。
- 再発検知: `orchestrator/tests/test_pegasus_calibration_workload.py` の
  `test_certify_keeps_backoff_fixed_and_condition_gate_silo_only` が、この define と関門呼び出しが
  silo 分岐の内側にだけあることを固定する (変異 M6 で KILLED を確認)。
