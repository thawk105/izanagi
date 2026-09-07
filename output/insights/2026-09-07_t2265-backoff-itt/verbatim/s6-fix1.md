## 総括

F1〜F6 を実装しました。docs と PBS は未変更、commit も作成していません。凍結文書の SHA-256 は指定値のままです。

## F1〜F6 の対応 (file:line)

- F1: seed 付き certify を `_certify_main` 前で拒否。[driver](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265-itt-fix1/tools/pegasus/probes/t2187_adaptive_const_probe.py:3246)、[負例](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265-itt-fix1/orchestrator/tests/test_t2187_adaptive_const_probe.py:2164)
- F2: driver の基底 flag を含む全 flag 集合との exact 一致へ変更。[analysis](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265-itt-fix1/orchestrator/campaign/backoff_counterfactual_analysis.py:207)、[負例](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265-itt-fix1/orchestrator/tests/test_backoff_counterfactual_analysis.py:441)
- F3: 事前登録 hash、ccbench pin、patch A/B/C、順序付き stack、全 row の trace count を fail closed で検査。[pins](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265-itt-fix1/orchestrator/campaign/backoff_counterfactual_analysis.py:17)、[validation](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265-itt-fix1/orchestrator/campaign/backoff_counterfactual_analysis.py:115)、[負例](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265-itt-fix1/orchestrator/tests/test_backoff_counterfactual_analysis.py:459)
- F4: 3 定数を逐語値で固定し、90% 対 95% および `ln(1.03)` 対 `0.03` の合成 cluster 検査を追加。[tests](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265-itt-fix1/orchestrator/tests/test_backoff_counterfactual_analysis.py:372)
- F5: source 全文の `pending` 禁止 assertion だけを削除。64文字小文字 hex 検査は維持。[test](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265-itt-fix1/orchestrator/tests/test_t2187_adaptive_const_probe.py:2079)
- F6: 推定対象の `assigned_invert_rate` は維持し、各 run の全 event 比を独立した `assignment_rate_all_events` field に追加。[analysis](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265-itt-fix1/orchestrator/campaign/backoff_counterfactual_analysis.py:421)、[test](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265-itt-fix1/orchestrator/tests/test_backoff_counterfactual_analysis.py:244)

## 実走したテスト (nodeid と範囲。実走していないならそう書く)

pytest は実走できていません。

対象は解析テスト全体と次の F1 nodeid でした。

- `orchestrator/tests/test_backoff_counterfactual_analysis.py`
- `orchestrator/tests/test_t2187_adaptive_const_probe.py::test_public_certification_rejects_step_policy_seed_before_dispatch`

`tools/run_tests.py` 経由で通常 2 回、`--force-dispatch` 1 回を試しましたが、すべて `qstat -Q preflight rc=1`、runner `rc=16`、`child_started=false` でした。

静的には `git diff --check` 成功、解析 module/test の AST parse 成功です。

## 赤の内訳と帰属

テスト赤はありません。テスト process 自体が開始されていません。

3 回の失敗はいずれも Pegasus dispatch infrastructure に帰属します。凍結文書の SHA-256 は引き続き `ee7617f...f127a6` です。

## 現行の受理・拒否挙動と、変えた点

変更前は seed 付き certify が受理され seed が無視され、解析は genome の部分集合や caller 任意の事前登録 hash、未検査の build bindings を受理していました。

変更後は以下です。

- seed 付き certify は明示拒否。
- performance の seed 受理と policy 2 の seed 必須条件は不変。
- certify の exact 2 cell 契約は不変。
- genome は基底 flag を含む exact 集合だけを受理。
- 事前登録・ccbench・patch・trace count の束縛違反を拒否。
- 12 artifact 間の genome、buildcache key、binary SHA 一致は要求していません。
- trace 有効値から `median_tps` 腕比較を生成する経路は追加していません。

## 所有外 caller・共有 fixture・consumer test への波及 (静的列挙)

- `analyze_counterfactual()` の引数と公開 API は不変。公開 CLI は追加していません。
- driver が既に出力する top-level/row bindings を解析が消費します。
- PBS は seed を performance 分岐だけへ渡す現行動作のままです。
- 解析 fixture は driver と同じ基底 flag、patch、ccbench、trace count を持つよう更新しました。
- 解析結果へ `assignment_rate_all_events` が加わるため、完全な JSON schema equality を持つ所有外 consumer には加算 field の影響があります。
- driver は総行数 3528 を維持し、F1 より後ろの行番号を変更前と一致させました。行番号依存の deferred meta-test は未実走です。
- runner が worktree 内の `output/pegasus-dispatch/` に失敗 receipt を3件生成しました。

## 残る不確実性

Pegasus queue preflight 障害が解消後、上記 nodeid の実走が必要です。特に合成 cluster の境界値、全 artifact 間 trace count 負例、所有外 meta-test は未実走です。