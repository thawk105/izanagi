---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-23
wave: dev-wave-t1472-provider-init-indeterminate
seq: 3
title: '[T-1472] oracle testの赤の原因が途中で入れ替わったことを実測し、残存分の修理を後続waveへ申し送る (記録のみ、branch worktree-dev-wave-t1472-provider-init-indeterminate)'
---

## 本文

- 本 wave の受入を 3 回止めていた `orchestrator/tests/test_sort_swo_oracle.py` の赤について、
  **原因が途中で入れ替わったことを実測した。** これは既知赤の除外を担当した wave の
  前提と異なるため、修理側の一次情報として残す。
  1. 04:49 と 07:51 の受入全走では 26 件が赤で、原因は
     `OracleEnvironmentResolutionFailure(detail_code='oracle-environment-dependency-unresolved')`
     — masstree の `config.h` 不在だった。
  2. 08:22 に `/work/1/SFC/tanab/izanagi-thirdparty-cache/masstree/config.h` が生成された
     (本 wave の作業ではない)。同 file を 08:43 に単独走させると
     **`10 failed, 52 passed in 4.57s`** で、**26 件から 10 件 (一意 node 7) へ減った。**
  3. 残った 7 node の原因は**別物**で、
     `_EvaluationUnavailable: candidate-run-signal-6` (SIGABRT)。
     コンパイルは通り、生成された oracle 実行ファイルが実行時に abort する。
     一次資料は
     `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1472-provider-init-indeterminate/verify-oracle.log`。
- **本 wave では実行を止める変更を行わなかった。** 一度は 7 node へ `@pytest.mark.skip` を
  入れたが、その間に除外機構が main へ着地し (`orchestrator/test_selection_contract.py`、
  D679 によりユーザー裁定で粒度は file 単位へ訂正済み)、同 file が受入全走から
  外れて main が `14284 passed / 0 failed` の完全緑になったため、**重複を避けて取り消した。**
  production (`orchestrator/campaign/sort_swo_oracle.py`) は一貫して 1 文字も変えていない。
- **反省 (経緯を残す):** `config.h` 生成を見つけた時点で、解決器が
  `OracleEnvironment` を返すことだけを確認し、「26 件は通るようになった可能性が高い」と判断して、
  恒久除外を実装中で受入走行中の別 wave へ「至急、止めるか読み直せ」と送った。
  **必要条件の確認で十分条件を断定した誤り**であり、ユーザーの指摘を受けて撤回した。
  実測すると 10 件は残っていた。同じ日に自分は別セッションへ
  「1 サンプルからの推論を断定として引くな」と留保を求めていた。
  auto-memory `verify-before-broadcasting-to-peers` に固定。
- 受入で踏んだ環境要因 2 件 (自分が立てた orphan hold、共有 config のロック競合) は
  seq 3 の failures fragment に記録済み。

## 次の一手差分

### 新規

- {{T:sort-swo-oracle-abort-repair}} **P1・新規**:
  `orchestrator/tests/test_sort_swo_oracle.py` の 7 node
  (`test_cpp_e2e_clean_generic_lambda_positive`、
  `test_cpp_e2e_high_storage_only_negative_kills_corpus_narrowing`、
  `test_cpp_e2e_rejects_corpus_mutation_with_dedicated_reason`、
  `test_cpp_e2e_rejects_same_process_call_count_dependence_with_witness`、
  `test_cpp_e2e_reports_each_axiom_and_exact_indices`、
  `test_cpp_e2e_stable_cross_allocation_pointer_positive`、
  `test_real_ctor_pointer_topology_and_triplicate_have_expected_matrix_meaning`)
  が `candidate-run-signal-6` (SIGABRT) で落ちる原因を特定して直し、除外から戻す。
  **除外を担当した wave の前提は `config.h` 不在だったが、それは 2026-08-23 08:22 に
  解消済みで、残存原因は別層の SIGABRT である** — 修理の起点はここになる。
  切り分けは、コンパイル済み oracle 実行ファイルが abort する箇所と、
  masstree のビルド設定の整合から始める。同 file の残り 46 node は通っているので、
  file 単位の除外は修理までの一時措置であり恒久化しない。
