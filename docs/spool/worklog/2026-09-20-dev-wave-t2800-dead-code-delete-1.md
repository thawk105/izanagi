---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-20
wave: dev-wave-t2800-dead-code-delete
seq: 1
title: [T-2800] 参照されない一回限りの tool を削除した — R1 の 6 file と R3 の 4 対 (13 file、Python 4,337 行 + pin 4 行 + README 1 行)、R3 の残る 11 対は 3 条件を確認できず残す (コード + docs、branch worktree-dev-wave-t2800-dead-code-delete)
---

## 本文

- **裁定 D2172 項 5 (第 24 回 /rulings 項 5) の実施。** R1 (a) の 6 file を削除、R3 (c) の 15 対のうち段 1 で「一回限り・結果凍結済み・現行機構の実装でない」を module ごとに確認できた 4 対 (`s6_canary_rename.py`、`insights_date_layout.py` + test、`migrate_output_gzip.py` + test、`plot_t2266_tail_mechanism.py` + test) を対で削除し、`test_ccbench_spawn_sites.py` の canary 4 site と `orchestrator/tests/README.md` の allowlist 1 行を追随させた。差分 15 file / 4,342 deletions (実装 commit `455b03f36`、author unit commit `8f6aee197`)。R2 / R4 は残し、R5 / R7 は見送り、R6 の相乗りは触る file に C の小組が無く発火せず。記録は `output/insights/2026-09-20/t2800-dead-code-delete/README.md`、分類の判断は {{D:dead-code-r3-classification}}。
- **段 1 の判定は 6 対削除・9 対保持だったが、段 2〜3 で 2 対を保持側へ移した。** (1) `backoff_requested_us` 対: 段 3 レンズ A が、専用 test に live な `dispatch_compute._child_environment()` の PBS 3 変数除去 (他 test に同等 assert なし、親が検算)・registry の包含 pin・残る patch の mu01 / mu02 検査があると指摘し、「module + 専用 test」の前提が崩れた。(2) `t1434_t1222_science_slice` 対: plan と両レンズが、専用 test の 1 関数が D2172 項 6 (派生値 pin 維持) の list-D に載り、項 5 が項 6 を上書きする逐語が無いと指摘した。両裁定を同時に満たす保持を選び、優先順位を新設しなかった。残る 9 対の保持理由は段 3 の両レンズ・段 6 の両レビューが現物で確認し、追加削除の反証は 0 対。
- **確認できなかった条件の内訳** (詳細は insight §3): 現行機構でないと言えない = counterfactual 2 本 (凍結事前登録が解析器に契約を課す、cohort2 は live probe の seed 表の照合先)、`backoff_sweep_report` (D12 材料レポート射影器)、`floor_liveness` (D546 の診断 consumer、producer は live)、`t1994_readonly_snapshot_qualification` (D2035 の errno 連言を `test_buildcache_v2` が直接検査)、`verify_paper_story_a1_balanced_sizing` (A-1 sized 事前登録の検証器、test は生成器と共有)。一回限り・結果凍結でない = `backoff_nonmonotonicity_analysis` (T-2583 / T-2635 が library として再利用)、`mocc_trace_pair_anchor` (D1110 の検証器、成果物不在は凍結の証拠でない)、`mutation_fanout` (D433 の実行不能条件を保持、完了した処理でない)。
- **実測**: 焦点走 7 file (計算ノード、request 12686.nqsv、Elapse 93 秒、14:30〜14:32 JST) = 557 passed / 8 skipped、87.80 秒。台帳 coverage は被覆済み node を除くので低下方向だが閾値を維持。閉包 47 pin は無傷。全史 provenance 監査 11,883 件・新規違反なし、`check_docs` 違反なし。変異 matrix (登録 worktree `mut-t2800-delete`、tip `455b03f36`、dispatch、14:34〜14:41 JST) = baseline PASSED (114.8 秒、12699.nqsv)、m0 等価 SURVIVED (12704.nqsv)、m2 spawn 行残し KILLED・m4 README 行残し KILLED (12713 / 12716.nqsv、期待 node と完全一致)、harness rc=0。受入所要台帳の stale 96 node / 6.349 worker 秒 (0.035 %) は残す (lookup 専用)。
- **手順の逸脱 1 件**: author 1 巡目に親が `git rm` を指示し、sandbox の `.git/worktrees/*/index.lock` 書込み拒否で無変更終了した (F359 の同型再発、約 1 分)。2 巡目は作業ツリーの `rm` + 4 行編集で完了し、起動器の終端契約が残差を unit commit へ記録、親が所有 path 限定 patch を `git apply --index` で展開した。
- **DW-O09**: 削除集合の path / stem / sha256 / blob sha を repo と output で走査。sha / blob の hit は歴史記録 (t2638 到達性台帳の T-1994 probe 4 本の blob、tail 図 provenance の生成器 sha) だけ。
- 工数: Codex 子 7 本 (plan 1、consult 2、author 2 (1 本は無変更)、review 2、すべて gpt-6-astra / medium)、計算ノード job 6 本 (焦点走 1、変異 5)。main は着手時 `947fd160a` → 記録前に `4726b6493` を取り込み (docs のみ、競合なし)。
- 段 8: dev-wave 改善候補は F359 への再発追記のみ (新しい F は採らない)。command 本文・reference の変更なし。

## 次の一手差分

### 完了

- [T-2800] D2172 項 5 の削除 wave を実施した。R1 6 file と R3 4 対を削除、R3 の残る 11 対は 3 条件を確認できず保持 (理由は insight §3、判断は {{D:dead-code-r3-classification}})。
  remaining: none
  base: 9e2eda9d1c3bad0b488562de1bfd7812f7a23bcaab52e8d42c4a9e15e8c7fdab
- [T-2276] `p2_5.py`・`s6_amendment_20260713_fence.py` は R1 (a) で削除、`s6_proposal_rounds_power.py` は R2 で事前登録 producer として保持 (D2172 項 5 R8 のとおり閉じる)。
  remaining: none
  base: d59c695914ca94012bada71af4233cf3bc2d915213ab7f5c9ebe5b521cc7d761

### 新規

- {{T:r3-two-pairs-left-by-overlap}} **P3・ユーザー裁定待ち**: R3 の残置 2 対の処置。(1) `tools/t1434_t1222_science_slice.py` + `orchestrator/tests/test_t1434_t1222_science_slice.py` (1,803 行) は module が 3 条件を満たすが、test の `test_pinned_jobs_requirements_are_exact` が D2172 項 6 (派生値 pin 維持) の list-D に載る — 択: (a) 項 6 の例外としてこの 1 関数 (または file) の削除を認める、(b) 残す。(2) `orchestrator/campaign/backoff_requested_us.py` + test (2,483 行) は test が live 被覆 3 群 (dispatch の PBS 除去、registry pin、patch の mu01 / mu02) を持つ — 択: (a) 被覆 3 群を別 file へ移してから対削除する wave を立てる (削除でない編集を含む)、(b) 残す。推奨 = (1) (b)・(2) (b) (研究に効かない、D205)。一次資料 `output/insights/2026-09-20/t2800-dead-code-delete/README.md` §7。
