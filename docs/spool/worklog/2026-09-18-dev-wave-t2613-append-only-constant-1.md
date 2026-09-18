---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-18
wave: dev-wave-t2613-append-only-constant
seq: 1
title: [T-2613] attempt registry の全 ref 履歴 gate の定数を実測して下げた — 1 呼出 1.78 億 process (旧版標本からの外挿 20〜62 日) → 37 process (35〜46 秒)、同じ 3 規則・受理集合不変、同時刻対照で採用条件成立 (コード + テスト + insight、branch worktree-dev-wave-t2613-append-only-constant、変異 matrix = baseline PASSED・負例 14/14 KILLED 期待 node 完全一致・等価 M0 SURVIVED・MISMATCH 0)
---

## 本文

- ユーザー依頼は「[T-2613] (D2044 項 19、ユーザー裁定) `tools/check_ai_provenance.py` の追記専用 gate (known-violation append-only history、全 commit 走査) の 1 回あたりの操作時間 (定数) の削減を実測する — per-call 費用を分解して定数項を計測し、削減案の効果を同時刻対照で示す。定数削減で足りないことを示すまで範囲の限定は設計せず、gate の意味・拒否条件は緩めない。実装差分は削減が実測で効く場合だけ (Codex author、D95)。着手直前の local main から fresh worktree を作る。規律 2 を緩めない。本題の実測だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」。
- **対象の訂正 (段 1 の新事実、段 4 で確定):** 依頼文が名指す `tools/check_ai_provenance.py` の known-violation 検査は path 限定の `git log` 1 回 (実測 1.2〜4.3 秒) で全 commit 走査ではなく、[T-2613] の起点 (archive worklog 1491) と D2044 項 19 が指すのは attempt registry の全 ref 履歴 gate `_assert_attempt_registry_history_append_only` (発行側 `orchestrator/campaign/trial_registry.py`、受入側 `orchestrator/campaign/s8c_acceptance_receipt.py`) である。next-tasks の起草 (job 40f94366) が file 名を取り違えていた。識別子側を採り、check_ai_provenance 側は対象外として実測値だけ残した。
- **閉じた。** 一次資料 = `output/insights/2026-09-18/t2613-append-only-constant/README.md`。設計判断 = {{D:attempt-history-gate-constant-reduction}}。
- 現行 gate の per-call 分解 (login node、load 28〜44): commit 11,703〜11,778 (全 ref、並行 session で増える)、`ls-tree -r` 1 commit 0.25〜1.19 秒、`cat-file blob` 1 process 0.04〜0.65 秒、到達可能 unique blob 49,123 件 / 7.37 GB、blob entry の延べ出現 ≈ 1.78 億 (AMTD first-parent 復元、等間隔 20 標本の `ls-tree` 件数と 20/20 一致)。**実 repo で完走不能** (旧版標本の窓内観測からの外挿 = 1.7×10^6〜1.5×10^7 秒、負荷依存)。
- 削減版 (commit `6616fa06c`、両 module): `rev-list` 1 + `cat-file --batch-check` 4 + tree object の `cat-file --batch` 3 + `log --stdin --root --diff-merges=separate --full-history --raw -z --no-renames --no-abbrev --no-show-signature --format=%H --diff-filter=AMT` 1 + 256 MiB chunk の `cat-file --batch` 28 = 37 process。R1 / R2 / R3・拒否文言・全 ref 走査は不変、範囲限定なし。
- **同時刻対照 (final-3、08:27〜08:30 JST、login node、load 48→14、事前登録 §3 + erratum E1):** 削減版 46.10 / 34.66 秒 (受入側 33.45 秒) vs 旧版外挿 E_min = 1.73×10^6 秒 (20.0 日)。N_max 46.10 < E_min/100 = 17,296 で性能条件成立。C 一致 (増分 0)、20/20 一致、5 区分被覆、全 git 呼出 rc=0、合成 repo 旧新比較 10/10、selftest 12/12。E1 = 「準備時 C ⊆ 走行時 C、増分 ≤ 0.1 %」への緩和で、final-1 / final-2 (4 走とも並行 session の commit で C が 1〜4 増え「同じ C」不成立) の結果を見た後に加えた (insight §3.2〜3.3 に明記)。
- 段 2 plan は brief を 11 点訂正 (N4 の外挿の意味、N6 は部品和、`--stdin` / `--root` / `-z` / `--diff-merges=separate` の補強)。段 3 レンズ A must-fix 4・B must-fix 5、全件 real・採用。段 6 レビュー A must-fix 4 (親 directory の gitlink 緩和、受入側契約、段 0 の tie-break、切断応答の順位迂回)・B must-fix 5 (窓外観測の外挿混入、旧 `_git` 不使用、受入側契約、期待 node の完全集合、受入側 stdin test)、全件採用し fix 1 本 (closed 10 / partial 1) + harness の E1 fix 1 本で閉じた。
- **F43 再発 (親の落ち度):** 段 5 author 2 本の prompt に `## 総括` を書かず両方 validator 不受理 (`f43_fragment`)。実装は正しく、未受理と明記して段 6 レビューに監査させた。新しい F を採らず既存 F43 への再発追記 (failures fragment)。
- 実走: 焦点走 3 本 (計算ノード dispatch: 406 / 971 / 1241 passed、failed 0、skipped 2 / 7 / 7 = 既存 hold)、harness 試走 1 + 本走 3 (login)、変異 probe (43 分) + 本走 (27 分、14/14 KILLED・M0 SURVIVED、insight §5)。受入全走は docs commit 後の最終 tip (結果は land の受領証)。
- 工数: codex 子 9 本 (plan 1、consult 2、author 2、review 2、fix 2、全段 `gpt-6-astra` / medium)。親の実測: 段 1 の git 直叩き 10 本、harness 5 走、変異 2 走、焦点走 3 走。
- 残余 (insight §4.3): 壊れた tree (同名 entry 重複、mode と object 種別の不一致) では旧版と文言・受理が異なりうる。帰属不能な process 異常の順序は保証しない。全 chunk が 300 秒以内である保証は無い (実測最大 3.76 秒)。

## 次の一手差分

### 完了

- [T-2613] 追記専用 gate (attempt registry 全 ref 履歴 gate) の per-call 定数を分解・計測し、同じ 3 規則のまま 37 process へ再構成した削減版を同時刻対照 (事前登録 + E1) で採用条件成立として実装した。範囲限定は設計していない (D2044 項 19 の順序)。
  remaining: none
  base: 2c753f2a4125a7bc387622882848c5e39615cb117c502b176c0855d4bb179039

### 新規

- {{T:attempt-history-gate-sufficiency}} **P3・新規**: attempt registry 履歴 gate の削減後 1 呼出 35〜46 秒 (login node、O(到達可能 unique blob bytes) + O(commit) が残る、{{D:attempt-history-gate-constant-reduction}}) が 8c の登録 launch・receipt 検証の運用に足りるかを、genesis 作成後の実呼出 (`p3_autonomous_workload_trial.py` の `load_attempt_registry`) の wall で判定する。足りないと実測で示した場合だけ D2044 項 19 の次段 (範囲限定の設計) へ進む。それまで設計しない。
