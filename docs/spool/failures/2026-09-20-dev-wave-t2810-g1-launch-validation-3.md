---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-20
wave: dev-wave-t2810-g1-launch-validation
seq: 3
---

## 再発

### F10

- **再発: 2026-09-20** (near miss、実害なし、[T-2810] で発見・補完) — 同型 (pin 前進で参照が腐る構造) が **実 repo を root にする held test の期待値**で実現した。ccbench pin 前進 ([T-2304]、D2184) は admission policy の epoch を動かし、`test_s8b_oracle_driver._ACTIVATED_G1_REFUSALS` (凍結 v2 g1 の live P3 拒否集合、held 6 node が exact 照合) の第 2 要素を `journal-state-invalid` から `manifest-invalid` (policy 照合) へ静かに変えた。held node は受入全走で走らない (growth hold) ため pin 前進 wave の受入は緑のままで、D2184 の「現行 policy に束縛された test の golden を epoch 1 段進めた」にも含まれなかった。次 wave が `IZANAGI_RUN_GROWTH_HELD_TESTS` の診断焦点走で発見し、live P3 の実測値へ更新した。同型: 値 pin (refusal 文字列など) は path / key 検索の pin 閉包 (DW-O09) に出ず、policy sha 等の間接依存で古くなる。policy epoch を動かす wave は held 真値の再実測を帰結に含める (memory `ccbench-pin-advance-execution-facts` に記載)。

### F100

- **再発: 2026-09-20** (near miss、実害なし) — 凍結 v2 g1 の launch validator 修復 wave の親が、段 5 実装子の進捗確認で `cd /work/1/SFC/tanab/izanagi/.codex/worktrees/t2810-unit-impl 2>/dev/null && echo …` (読み取りだけ) を Bash に含め、harness の追跡 cwd が author の子 worktree へ移った。`EnterWorktree(path=<自分の wave worktree>)` で即復帰 (HEAD・clean 不変)。書き込みは発生していない。同型: 他 worktree の file を見るときは絶対 path で `ls` / `cat` し、`cd` を前置しない (memory `worktree-discipline` の「cwd の罠」、本台帳の 2026-09-18 3 件と同じ手順で復帰)。
