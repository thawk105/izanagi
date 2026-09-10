# [T-1905] B-10 の 1 セル試し打ち phase と balanced 45 セルの限定受理 — wave 記録

**判定は書かない。** 本 wave は実行面 (driver / 投入 script / job script / test) と記録だけを扱い、
B-10 の 3 族 Holm 判定にも read-heavy の性能値にも触れていない。試し打ちの成果物は
正式系列の一部でも事前登録の判定にも入らない (設計 §5.2)。

## 0. 何をしたか

- D1617 (2) の実施: driver `orchestrator/campaign/b10_backoff_shape_sweep.py` に `trial-cell` phase を足し、
  block-1 の登録順で最初の登録 shape cell (現 spec では index 3 `constant-mu2`) を 1 変種だけ
  build → 全 verify path → 認証 → perf binary の SHA 照合 → 測定 → cell 記録 → trial 専用 report まで
  同一 job・同一 checkout で通す。campaign 同一性は `search_tag=trial` と submission nonce で formal から分け、
  `report` は write-heavy 旧系列 (e3de15eb)・balanced 旧系列 (143a3f74)・read-heavy 現行 formal の
  3 campaign しか読まない。成功述語は exact 1 record + 今回書いた record digest + WAL certified attempt
  (`build_attempt_id`、perf SHA) + 今回の submission identity (request ID / nonce / receipt SHA) の論理積。
- D1617 (2) の後段: balanced 45 セル (campaign `b10-backoff-shape-silo-balanced-formal-143a3f74`、
  driver bytes sha256 `f6246360c784813a581d7e104f116c07838106022fb9245f5de50b338e9ea0ec`) を D1597 の形
  (campaign ID・旧 analysis commit `c7ed5658…`・旧 analysis sha・旧 binding sha `588aaa9c…`・45 件の
  内容 digest の exact 集合・45 cell exact) で集約に残す専用 validator。write-heavy の限定受理
  (execution_host 不在を要求) とは共通化しない。**取り直していない。**
- D1617 (1): D1509 決定 2 の改訂は decisions fragment に記録 (満たしたとは書かない)。

## 1. 一次資料

| 何 | 所在 |
| --- | --- |
| balanced 完走の現物 | `/work/1/SFC/tanab/izanagi-job-evidence/b10-backoff-shape/submissions/c42191d4f1e6ecdbd5b7eb7f3100df50/` (974207.nqsv、job-result driver_rc=0、失敗記録なし) |
| balanced 45 record | `/work/1/SFC/tanab/izanagi-job-evidence/b10-backoff-shape/official-output/campaigns/b10-backoff-shape-silo-balanced-formal-143a3f74/runs/b10-backoff-shape-blocks/` (45 file、全件 correctness_certified・missing=false・perf SHA あり・execution_host=bnode015) |
| balanced lock / WAL | 同 campaign の `campaign.lock` (束縛 7 key、analysis_commit を含まない)、WAL 135 record・15 変種・truncated なし |
| 試し打ちの投入受領証 | `/work/1/SFC/tanab/izanagi-job-evidence/b10-backoff-shape/submissions/b7539bc8ddebac8ec4cca7f1eac500bd/submit-receipt.json` (977483.nqsv、trial-cell / read-heavy、source `2a338449bb2798b729c5bc2f9bfe76463a7fe347`、24 時間枠、2026-09-05 00:25 JST 投入) |
| 投入元の固定 checkout | `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1905-b10-trial-cell/submit-tree` (detached 2a338449b、submodule 初期化済み、clean)。**job 完了まで触らない。** |
| codex 子の成果物 | `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1905-b10-trial-cell/` (stage2-plan、stage3-lensA/B、stage5-author、stage6-reviewA/B、stage6-fix、stage6-focus、各 receipt.json) |
| 変異 spec / 台帳 | 本 dir の `mutation-spec-probe.json`、`mutation-ledger-probe.json`、`mutation-spec-final.json`、`mutation-ledger-final.json` |

## 2. 変異 matrix (tip 2a338449b、runner = test_b10_backoff_shape_sweep.py + test_ccbench_spawn_sites.py、dispatch)

probe (全件 SURVIVED 期待で観測 node を集める) → 本走 (KILLED 期待 + 観測 node の完全集合)。
本走: **18 negative すべて KILLED (期待 node 完全一致)、等価変異 m15 は登録どおり SURVIVED**、baseline 緑。

| id | 変異 | 赤になった test (単一理由性の注記) |
| --- | --- | --- |
| m01 | digest 集合の exact 比較を部分集合へ | `…rejects_nonexact_sets_directly[missing]` + 行番号 pin 3 node (drift mask) |
| m02 | balanced campaign ID 検査を恒偽 | `test_balanced_legacy_rejects_other_campaign_id` |
| m03 | execution_host 欠落を許す | semantic gate `[execution-host-missing]` + 行番号 pin 3 node |
| m04 | workload 検査を WORKLOADS 一般へ | semantic gate `[workload-wrong]` |
| m05 | 旧 binding を現行 binding へ | `test_143a3f74_balanced_adapter_accepts_only_pinned_series` (正例の過剰拒否 = 受理集合が変わる) |
| m06 | balanced 分岐を現行 validator へ | default 結線 test + collector AST test + 行番号 pin 3 node (二重) |
| m07 | trial cfg を formal identity へ (search_tag と nonce 両行) | `test_trial_run_uses_one_genome_and_summary_contract_is_one_vs_fifteen` + 行番号 pin 3 node |
| m08 | trial genome を全 15 へ | 同上 (1 genome の AST pin) |
| m09 | perf SHA の WAL 照合を外す | `…rejects_each_incomplete_binding[perf-sha-mismatch]` |
| m10 | nonce 照合を外す | `…rejects_each_incomplete_binding[nonce-mismatch]` |
| m11 | main の rc を常に 0 | `test_trial_main_return_code_is_exact_success_predicate[False-1]` |
| m12 | job script の phase regex から trial-cell を外す | `test_verify_perf_launcher_contract_and_walltime_are_consistent` |
| m13 | balanced digest 集合へ 46 件目 | `test_143a3f74_balanced_adapter_accepts_only_pinned_series` + 行番号 pin 3 node |
| m14 | 試し打ち cell を登録順 index 0 (`none`) へ | 導出値 test + 既存 record 拒否 test (fixture が導出 cell を使う、二重) |
| m16 | balanced validator の既定 digest 集合を write-heavy 集合へ | `test_balanced_legacy_validator_default_is_the_frozen_balanced_set` |
| m17 | search_config の `scale` 文字列を変更 | `test_trial_config_is_separate_from_formal_and_nonce_specific` |
| m18 | 既存 record 拒否を恒偽 | `test_trial_rejects_preexisting_self_hashed_record_even_with_matching_wal` |
| m19 | 書込 digest との照合を外す | `test_trial_success_predicate_requires_this_invocations_written_record_digest` |
| m15 (positive) | `{…}` → `set(…)` の等価変異 | SURVIVED (harness の SURVIVED 検出の正例) |

行番号 pin 3 node (`test_ccbench_spawn_sites.py` の `_DEFERRED_GATE_MEMBERS` 由来) は driver の行数を
変える変異すべてで赤になる冗長 gate であり、変異の意味は見ていない (DW-M03 の「冗長 gate と明記」)。

## 3. 段 3 / 段 6 の所見 (要約、全文は codex 成果物)

- 段 3 レンズ A/B が独立に real とした 2 点 (trial 専用 report の欠落、固定 campaign ID の再投入汚染と
  自己申告成功) を採用。レンズ B の裁定候補「`none` は backoff 実動経路を踏まない」も採り、cell 規則を
  最初の登録 shape cell へ変えた。
- 段 6 レビュー A: NO-GO (事前配置の自己 hash record で測定を省いた成功、trial report に workload 無し、
  変異 spec の帰属)。fix 1 子で閉じ、焦点再レビュー GO。レビュー B: GO (must-fix なし)。
- 採らなかった所見: trial-cell を read-heavy 限定にする (D1480 条件 2 は残り workload 一般の条件。
  report の workload 明示と投入手順で誤認経路を塞ぐ)、試し打ち用の短い壁時計枠 (pin が広がる)。

## 4. 投入と結果

- 2026-09-05 00:05 JST、trial-cell / read-heavy を 977483.nqsv として投入 (gen_S は QUE 275 / RUN 65、
  queue 待ち 2 分)。00:07 開始、01:00 終了、Elapse 3,177 秒 (bnode094)。
- 試し打ちの結果 (一次資料は submissions/b7539bc8…/job-attempts/977483.nqsv/ と
  campaigns/b10-backoff-shape-silo-read-heavy-trial-6cef7cf6/):
  `job-result.json` driver_rc=0、失敗記録なし、campaign done 1 committed / 0 aborted、
  verify[legacy] 1 回 + verify[performance] 5 回すべて serializable (0 anomalies)、
  record `block-1--03--constant-mu2.json` は correctness_certified・missing=false・
  perf SHA `139edad3…` = certified attempt `e738e04f…` の perf_bin_sha256・execution_host bnode094、
  trial report `reports/trial/b7539bc8….json` は `success_predicate=true`、`phase=trial-cell`、
  `workload=read-heavy`、record digest `89498e54…`。**D1480 条件 2 を満たした。**
- 固定 checkout は試し打ち後も superproject・submodule とも status 0 行 (build cache は ignored)。
- 2026-09-05 01:06 JST、verify-perf / read-heavy を **977647.nqsv** として投入
  (nonce `4537eb096a8ded8119e0bc92944f3171`、source `2a338449b`、24 時間枠)。01:06 に RUN 開始。
  完走待ち。**判定は書かない。**
- report phase は 3 campaign が揃った後、同じ driver bytes (sha256 b15c3548…) の checkout から 1 回だけ走らせる。
