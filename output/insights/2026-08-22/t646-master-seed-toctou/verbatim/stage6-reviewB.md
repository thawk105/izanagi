## 判定

実所見は0件です。差分と関連テストを静的に攻撃確認しました。

1. **負例 fixture — refuted**

   [`test_s8b_holdout_freeze.py:1683`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t646-master-seed-toctou/orchestrator/tests/test_s8b_holdout_freeze.py:1683>) で protocol の `master_seed` だけを canonical bytes として未 commit 書込みしています。`git show <fixture["head"]>:...` との比較も [`:1771`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t646-master-seed-toctou/orchestrator/tests/test_s8b_holdout_freeze.py:1771>) で確認されています。

   schedule、result、manifest、admission evidence、journal はすべて変更後 protocol/hash/schedule から再構成されており、旧検査でも protocol 内部整合性・manifest・journal・admission の各検査を通る構成です。したがって新しい HEAD 比較だけが拒否理由になります。tautological とは崩せません。

2. **副作用ゼロ — refuted**

   新設比較は parse・schedule より前の [`s8b_holdout_freeze.py:1362`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t646-master-seed-toctou/orchestrator/campaign/s8b_holdout_freeze.py:1362>) にあり、candidate writer は [`:1867`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t646-master-seed-toctou/orchestrator/campaign/s8b_holdout_freeze.py:1867>) で初めて呼ばれます。検証経路は読み取り専用です。`output` と親 directory の前後 assert（[`test...:1776`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t646-master-seed-toctou/orchestrator/tests/test_s8b_holdout_freeze.py:1776>)）で、SUT が作り得る candidate artifact を網羅しています。

3. **既存テスト・head 利用箇所 — refuted**

   `_validate_floor_inputs` の caller は [`s8b_holdout_freeze.py:1723`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t646-master-seed-toctou/orchestrator/campaign/s8b_holdout_freeze.py:1723>) の `build_v2_g1_candidate` のみです。既存正例 [`test...:1797`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t646-master-seed-toctou/orchestrator/tests/test_s8b_holdout_freeze.py:1797>) は protocol が HEAD blob と一致したまま、known_axes、generator、design_source、measurement closure まで通過します。closure drift 系テストも protocol を変更しないため、期待する既存エラー経路は壊れません。

4. **DW-O26 波及 — refuted**

   `orchestrator/tests` 全体で `build_v2_g1_candidate` / `generate_v2_g1_candidate` を呼ぶ他ファイルはありません。外部参照は scan API、定数、legacy `verify`、`_verify_source` などに限られ、今回の private signature 変更の影響を受けません。CLI も同一 module 内の [`s8b_holdout_freeze.py:1917`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t646-master-seed-toctou/orchestrator/campaign/s8b_holdout_freeze.py:1917>) から `generate_v2_g1_candidate` を通ります。

5. **T-647 scope — refuted**

   fix は HEAD blob と worktree bytes の比較だけで、bench 実行・計測契約・budget semantics を変更していません。新設 fixture も synthetic result/evidence の再構成 בלבדで、correctness-only scope 外へ踏み込んでいません。

6. **正例 — refuted（条件付き注意）**

   `candidate_repository` は protocol と関連 artifact を commit した HEAD を作り（[`s8b_v2_freeze_fixture.py:457`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t646-master-seed-toctou/orchestrator/tests/s8b_v2_freeze_fixture.py:457>)）、既存テストが build/generate の成功を pin しています（[`test...:1797`](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t646-master-seed-toctou/orchestrator/tests/test_s8b_holdout_freeze.py:1797>)）。したがって「worktree bytes == captured HEAD blob」の受理分岐は実際に検証されています。

   ただし、master seed を変更して新 commit を作る二段階の「reseal 遷移」そのものは再現していません。これは追加強化余地ですが、今回の比較条件の正例欠落とは判定しません。

## 総括

- real: 0件
- refuted: 負例の非 tautology、副作用ゼロ、既存テスト互換、波及なし、T-647 非侵入、HEAD 一致正例存在