---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-29
wave: dev-wave-t2871-policy-loop-iter
seq: 3
---

## 新規

### {{F:test-double-copied-sibling-driver-flow}}. 結合検査の代役を兄弟 driver の fixture から写し、対象 driver の production の流れ (checkout 回数・評価回数・patch の巻き戻し) と食い違ったまま焦点走 3 巡で 1 つずつ露見した [テスト代表性] [手順漏れ]

- 事象: [T-2871] の結合検査 (方策 loop driver `main` を別 process で 2 回、実 claim・reservation・admission・auditor gate を通す) で、実装子が backoff 軸の pair fixture (`orchestrator/tests/test_p3_s4_loop.py` の 2 checkout・arm ごとの bench 台本) を写した。方策 driver は 1 checkout で候補 → stock を評価し、production の `patchharness.checkout` は process ごとに新しい隔離 worktree を作り、`applied` は抜けるときに source を戻す。代役がこれらを省いたため、焦点走 4・5 回目で実 admission (stock に非 STOCK の evidence)・模擬 bench 台本の枯渇・実 auditor gate (強制終了した候補の書込み残りで digest 不一致) が 1 巡に 1 つずつ正しく拒否し、fix が 3 巡 (fix-2〜4) かかった。偽緑ではなく赤で露見した。
- 根本原因: 実装子への prompt が対象 driver の production の流れ (checkout の回数と寿命、1 checkout あたりの評価回数、patch 適用の巻き戻し) を明示せず、「手本」として兄弟 driver の fixture を指した。兄弟 driver は同じ機構を検査していても流れが違う。
- 恒久対応: memory `test-double-must-follow-target-driver-flow` (結合検査を頼む prompt に対象 driver の production の流れを file:line で書き、兄弟 fixture を写すなら差分を列挙させる。代役の反復は login の `tools/run_tests.py <file> -k <pattern>` で回し、`--basetemp` を `/tmp` の外に置く)。記録 `output/insights/2026-09-29/t2871-policy-loop-iter/README.md` §3。
- 再発検知: 焦点走の赤が admission・auditor gate・模擬 pipeline の前提違いで出たら、まず代役と production の流れの差を列挙する。

## 再発

### F763

- **再発: 2026-09-29** — [T-2871] の変異 probe を login の実 pytest (`tools/run_tests.py` の自動判定) で走らせたところ、`/tmp` の空の `.git` のために `/tmp` 下の tmp_path が「repository 内」と判定され、結合検査 3 本が `IZANAGI_EXPLORATION_OUTPUT_ROOT は repository 外でなければならない` で偽赤になった (同じ test は同日 04 時台の wave worktree からの login 走では緑、偽赤は 05 時台の変異用 clone からの走行)。`--basetemp` を job dir 下に置いて解いた (`output/insights/2026-09-29/t2871-policy-loop-iter/README.md` §4)。
