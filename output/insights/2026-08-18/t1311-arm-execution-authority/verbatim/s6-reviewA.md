NO-GO

## 総括

must-fix は 4 件ある。特に、第 7 sink は保存 payload の `workload_descriptor` を検証しておらず、「台帳は off、provider stdin は on」を表す成果物を受理できる。また `84ce492c` により digest chain が通常の completeness と独立 CLI から外れ、trial-registry acceptance でしか発火しなくなった。pytest は実行していない。721 passed は親の実測としてのみ扱う。

### 1. [real / must-fix] label を含む全成果物を再生成すると on/off 交換が通る

manifest parser は H1/H2 × 3 arm の集合だけを検査し、`trial_id` と arm の独立した固定対応を要求しない。[trial_registry.py:464](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1311-arm-authority/orchestrator/campaign/trial_registry.py:464)

具体的には、同一 holdout の on/off recordについて次を行える。

1. `arm` を交換する。
2. 交換後の arm digest から各 `campaign_id` を再生成する。
3. manifest SHA、registry、report、journal、campaign.lock、proposal、invocation、provider artifact、terminal projectionを再生成する。

producer は交換後の `binding.arm` を resolver へ渡す。[trial_registry.py:1220](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1311-arm-authority/orchestrator/campaign/trial_registry.py:1220)  
acceptance も同じ `trial.arm` を同じ `resolve_arm_input()` へ渡して期待値を作る。[trial_registry.py:2490](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1311-arm-authority/orchestrator/campaign/trial_registry.py:2490)  
digest chain も launch record の宣言 arm から binding digest を再計算するだけである。[autonomous_trial_completeness.py:761](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1311-arm-authority/orchestrator/campaign/autonomous_trial_completeness.py:761)  
campaign sink は交換後の campaign.lock 内部整合性を再導出するため、再生成された campaign を拒否しない。[autonomous_trial_completeness.py:552](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1311-arm-authority/orchestrator/campaign/autonomous_trial_completeness.py:552)  
最終 receipt も manifest の arm をそのまま記録する。[trial_registry.py:2879](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1311-arm-authority/orchestrator/campaign/trial_registry.py:2879)

manifest SHAだけを更新し、古い campaign IDを残す狭い攻撃は `assert_campaign_binding()` で拒否される。しかし全 sink を再生成する本来の交換攻撃には、独立した trial identity → arm authority がない。

成果物影響: acceptance receipt の `trials[].arm` と6セルの on/off意味が交換されたまま受理され、レポート比較の解釈が反転する。

### 2. [real / must-fix] 第 7 sink は実 payload の descriptor を照合していない

roleへ送る実入力は `workload_descriptor` と `descriptor_binding` の両方を持つ。[p3_autonomous_workload_trial.py:1873](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1311-arm-authority/orchestrator/campaign/p3_autonomous_workload_trial.py:1873) その canonical bytes が保存され、そのまま stdin に渡される。[claude_projected_provider.py:253](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1311-arm-authority/orchestrator/campaign/claude_projected_provider.py:253)

一方、独立 verifier は payload を再読するものの、`payload["descriptor_binding"]` の宣言 digestしか検査しない。[autonomous_trial_completeness.py:682](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1311-arm-authority/orchestrator/campaign/autonomous_trial_completeness.py:682) `payload["workload_descriptor"]` の canonical digestを計算して `content_digest` と比較する処理がない。

具体的な生存入力は次である。

- cell、campaign、proposal、invocation、run-start、terminalは off digest。
- provider payload の `workload_descriptor` だけを on descriptorにする。
- `descriptor_binding` は off のままにする。
- payload hash、event、provenance、payload validation receipt、journal/report hashを再生成する。

validation receipt側も `workload_descriptor_sha256` が SHA-256形式であることしか確認せず、cell digestとの一致を要求しない。[autonomous_trial_completeness.py:1083](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1311-arm-authority/orchestrator/campaign/autonomous_trial_completeness.py:1083)

さらに新設テストの正例は、`workload_descriptor` 自体がない payload を受理している。[test_autonomous_trial_completeness.py:1055](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1311-arm-authority/orchestrator/tests/test_autonomous_trial_completeness.py:1055)

成果物影響: roleが on descriptorを読んで生成した proposalを、off入力由来として report・台帳・acceptance receiptへ残せる。

### 3. [real / must-fix] `84ce492c` で registered completeness 経路の一部から chain が消えた

現在 `assert_autonomous_trial_completeness()` は digest chain を呼ばない。[autonomous_trial_completeness.py:2532](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1311-arm-authority/orchestrator/campaign/autonomous_trial_completeness.py:2532)

そのため次の registered対応経路では chain が発火しない。

- producerの報告生成時検査。[p3_autonomous_workload_trial.py:2683](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1311-arm-authority/orchestrator/campaign/p3_autonomous_workload_trial.py:2683)
- 独立ファイル verifier／CLI。[autonomous_trial_completeness.py:2957](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1311-arm-authority/orchestrator/campaign/autonomous_trial_completeness.py:2957)
- `_assert_snapshot_completeness()` 内部。[trial_registry.py:2124](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1311-arm-authority/orchestrator/campaign/trial_registry.py:2124)

`_assert_snapshot_completeness()` の唯一の現 callerである正式 acceptance は、後段で `assert_execution_digest_chain()` を呼ぶため最終的には覆われる。[trial_registry.py:2835](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1311-arm-authority/orchestrator/campaign/trial_registry.py:2835) しかし producer自己検査と独立 CLI は覆われない。

同 commit で T-1311 testは public completeness ではなく standalone helperを直接呼ぶ形へ変更された。[test_autonomous_trial_completeness.py:853](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1311-arm-authority/orchestrator/tests/test_autonomous_trial_completeness.py:853) これは既存期待値の反転やskipではないが、production integrationを弱めたままテストを緑にする変更である。

成果物影響: digest不整合の registered reportが producer自己検査と独立 completeness CLIでは「完全」と判定され、trial-registry acceptanceまで到達しない利用者のreport受理集合が広がる。

### 4. [real / must-fix] 親裁定に反して `OriginProducerInputs.enforcement_arm` を削除している

親裁定はこの fieldを削除せず、issued binding由来の値へ変えるよう明記していた。現行 dataclassには fieldがない。[p3_autonomous_workload_trial.py:332](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1311-arm-authority/orchestrator/campaign/p3_autonomous_workload_trial.py:332)

terminal consumerへ渡す値を capabilityから導出した点自体は正しい。[p3_autonomous_workload_trial.py:1139](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1311-arm-authority/orchestrator/campaign/p3_autonomous_workload_trial.py:1139) ただし既存 constructor契約を消しており、裁定された移行形になっていない。

成果物影響: 従来形の formal producerは constructorで停止し、terminal report・formal receipt・台帳を一件も生成できなくなる。

### 5. [refuted / nitなし] on/offが同一 bytesになる resolver退行

各 armのcanonical bytesを個別にhashし、3 digestの集合サイズを検査している。[s8c_arm_inputs.py:465](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1311-arm-authority/orchestrator/campaign/s8c_arm_inputs.py:465) onとoffだけが同一でも集合サイズは2となり、`arm-input-resolution` で拒否される。実装テストも `descriptor_for_holdout` をneutral descriptorへ潰す反例を構成している。[test_s8c_arm_inputs.py:126](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1311-arm-authority/orchestrator/tests/test_s8c_arm_inputs.py:126)

成果物影響: なし。同一bytesへ潰れたセルはlaunch前に拒否される。

### 6. [refuted / nitなし] fix群による一般的なskip・test削除

対象commit列には test関数の削除、`skip`、`xfail` の追加、期待例外の成功化は見当たらない。`af7a09ac` は検査順序の移動、`84c5e716` の scopeなし時 `None` 復帰も `_run_workload` 自身のsealed scope要求で正式経路を開かない。[p3_autonomous_workload_trial.py:2729](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1311-arm-authority/orchestrator/campaign/p3_autonomous_workload_trial.py:2729)

ただし `84ce492c` のintegration弱体化は所見3として realである。

成果物影響: 所見3以外のfix群による追加の受理集合変更は確認できない。

### 7. [refuted / nitなし] invocation ID経由のrole payload漏洩

role payloadのclosed key setには `invocation_id` がない。[p3_autonomous_workload_trial.py:263](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1311-arm-authority/orchestrator/campaign/p3_autonomous_workload_trial.py:263) `_invoke()` は invocation IDとpayloadを別引数でproviderへ渡し、provider stdinにはpayload bytesだけを送る。[p3_autonomous_workload_trial.py:1737](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1311-arm-authority/orchestrator/campaign/p3_autonomous_workload_trial.py:1737) [claude_projected_provider.py:268](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1311-arm-authority/orchestrator/campaign/claude_projected_provider.py:268)

既知の `workload` token漏洩は残るが、このwave以前の行であり、invocation namespace追加による悪化ではない。

成果物影響: invocation ID由来の新しいrole入力漏洩はない。既裁定の `workload` 漏洩による6セル解釈リスクのみ継続する。