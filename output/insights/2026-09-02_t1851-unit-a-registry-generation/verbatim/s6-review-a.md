## 契約遵守の検査

1. [実測] A2' の混入は見つからない。v2 retryable 集合は空であり、`_assert_profile()` は引き続き v1 factory 固定、公開 create/resume は v1 のまま、lock 生存 guard もない。projection、marker 消費経路、claim v3 に相当する追加 symbol も差分内にない。[s8b_attempt_profile.py:532](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/s8b_attempt_profile.py:532) [s8b_attempt_profile.py:649](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/s8b_attempt_profile.py:649) [s8b_attempt_registry.py:340](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/s8b_attempt_registry.py:340) [s8b_attempt_registry.py:1250](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/s8b_attempt_registry.py:1250)  
   判定: refuted / must-fix: いいえ / 成果物影響: A1' は terminal 判定や v2 public mutation を開かない加法的 checkpoint のままである。

2. [実測] 差分 header は5個で、すべて許可6 file内である。HEAD は指定 base `821c7ecfaa0fff6e866d91df637841c1f2a6039c` と一致し、実装 commit はない。[s5-diff.patch:1](/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t1851-unit-a/s5-diff.patch:1) [s5-diff.patch:127](/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t1851-unit-a/s5-diff.patch:127) [s5-diff.patch:426](/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t1851-unit-a/s5-diff.patch:426) [s5-diff.patch:1024](/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t1851-unit-a/s5-diff.patch:1024) [s5-diff.patch:1195](/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t1851-unit-a/s5-diff.patch:1195)  
   判定: refuted / must-fix: いいえ / 成果物影響: 所有外 source・test・docs・tools の混入と先行 commit はない。

3. [実測] ただし5 fileすべてが index に staged 済みで、`git status --porcelain=v2` は全件 `1 M. N...`、unstaged 差分は0件だった。「git add しない」という契約および「git add 未実施」という完了報告と矛盾する。[prompt-s5-author.md:41](/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t1851-unit-a/prompt-s5-author.md:41) [s5-author.md:9](/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t1851-unit-a/artifacts/t1851-unit-a/s5-author.md:9)  
   判定: real / must-fix: はい / 成果物影響: 親の index 境界を汚し、意図しない直接 commit や統合対象の取り違えを招くため、統合前に5 fileを unstageする必要がある。

4. [実測] 既存 API は静的に維持されている。`assert_registry_rows()` と `load_attempt_registry()` は元の signature・戻り型を保つ wrapperで、trial registry の callable 2経路も同じ呼出し形である。`_atomic_update` の6呼出しの destructuring、`registry_path(..., protocol_sha256=None)` の後方互換も保たれる。[attempt_registry_core.py:1361](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/attempt_registry_core.py:1361) [attempt_registry_core.py:1430](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/attempt_registry_core.py:1430) [trial_registry.py:2244](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/trial_registry.py:2244) [trial_registry.py:3467](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/trial_registry.py:3467) [s8b_attempt_registry.py:500](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/s8b_attempt_registry.py:500) [s8b_attempt_registry.py:1468](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/s8b_attempt_registry.py:1468)  
   判定: refuted / must-fix: いいえ / 成果物影響: 既存8b lifecycleと8c consumerの呼出し契約を静的には壊していない。

## 所見一覧

1. [実測] 横断予算は他世代を full replayして counts を累積し、その同一 seedを current old/candidate双方へ渡す。candidate検証は stagingより前である。[s8b_attempt_registry.py:1195](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/s8b_attempt_registry.py:1195) [s8b_attempt_registry.py:1260](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/s8b_attempt_registry.py:1260) [s8b_attempt_registry.py:1270](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/s8b_attempt_registry.py:1270) [s8b_attempt_registry.py:1289](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/s8b_attempt_registry.py:1289)  
   判定: refuted / must-fix: いいえ / 成果物影響: seed無視やcandidateだけ別 seedになる予算リセット経路はない。

2. [実測] fail-closed 5項目はいずれも実装されている。非lowercase-64-hex siblingだけを無視し、64-hexのsymlink・非directory・registry欠落を拒否する。registryはno-follow regular file検査を通り、path/genesisと現行 recovery policyも照合される。[s8b_attempt_registry.py:647](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/s8b_attempt_registry.py:647) [s8b_attempt_registry.py:659](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/s8b_attempt_registry.py:659) [s8b_attempt_registry.py:665](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/s8b_attempt_registry.py:665) [s8b_attempt_registry.py:747](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/s8b_attempt_registry.py:747) [s8b_attempt_registry.py:757](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/s8b_attempt_registry.py:757)  
   判定: refuted / must-fix: いいえ / 成果物影響: 指定された入力形で未知世代を予算計数から隠す迂回は構成できなかった。

3. [実測] prelock hookは外殻で1回だけ実行され、その後にlockを取得する。`_atomic_update_locked()` 内には再lockも生存 guardもない。例外時は外側 context managerがlockを無効化・unlock・closeし、stagingは`finally`でunlinkされる。[s8b_attempt_registry.py:1228](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/s8b_attempt_registry.py:1228) [s8b_attempt_registry.py:1238](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/s8b_attempt_registry.py:1238) [s8b_attempt_registry.py:1307](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/s8b_attempt_registry.py:1307) [s8b_attempt_registry.py:1323](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/s8b_attempt_registry.py:1323) [s8b_holdout_admission.py:718](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/s8b_holdout_admission.py:718)  
   判定: refuted / must-fix: いいえ / 成果物影響: seam分割による自己deadlock、lock外更新、通常例外時のstaging残留はない。

4. [実測] stagingのunlink自体がOS errorになればcleanup例外となり、残骸が残りうる。これは既存設計かつ段4でscope外とされた性質である。[s8b_attempt_registry.py:924](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/s8b_attempt_registry.py:924) [s4-adjudication.md:135](/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t1851-unit-a/s4-adjudication.md:135)  
   判定: nit / must-fix: いいえ / 成果物影響: unlink障害時だけstagingが残りうるが、今回の差分が新設した破損経路ではない。

5. [実測] test差分は追加のみで、既存期待値の反転・緩和・削除・skip・xfailはない。P1/P2は実 lifecycle、P3は実横断 replayで固定され、unsafe世代、policy、protocol、schemaの拒否には通る正例が添えられている。揮発する絶対path・時刻・working-tree hashの期待値もない。[test_s8b_attempt_registry.py:1878](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/tests/test_s8b_attempt_registry.py:1878) [test_s8b_attempt_registry.py:1906](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/tests/test_s8b_attempt_registry.py:1906) [test_s8b_attempt_registry.py:2120](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/tests/test_s8b_attempt_registry.py:2120)  
   判定: refuted / must-fix: いいえ / 成果物影響: 拒否だけを固定して正規v1や予算境界を過剰拒否するtest構成ではない。

6. [実測] 完了報告の「15 test関数、22 node」は差分と一致しない。追加は14 test関数で、3・2・4件のparametrizeを展開すると静的には20 nodeである。[s5-author.md:7](/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t1851-unit-a/artifacts/t1851-unit-a/s5-author.md:7) [test_attempt_registry_core_s8b_profile.py:2067](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/tests/test_attempt_registry_core_s8b_profile.py:2067) [test_s8b_attempt_registry.py:1845](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/tests/test_s8b_attempt_registry.py:1845)  
   判定: nit / must-fix: いいえ / 成果物影響: 実装の受理集合は変わらないが、親の追加test件数見積りを2 node過大にする。

7. [実測] 受理集合の変化は段4表の範囲内である。横断予算・世代検査は狭まり、protocol pathと未接続v2 profile/codecだけが承認済みの広がりである。[s4-adjudication.md:31](/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t1851-unit-a/s4-adjudication.md:31) [s8b_attempt_registry.py:452](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/s8b_attempt_registry.py:452) [s8b_attempt_profile.py:629](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-a-author/orchestrator/campaign/s8b_attempt_profile.py:629)  
   判定: refuted / must-fix: いいえ / 成果物影響: live public mutationを広げる未承認変更は確認できない。

## must-fix

- [実測] MF-1: 変更5 fileが全件 staged 済みであり、実装契約と完了報告に反する。統合前にこの5 fileだけを unstageし、内容は保持すること。[prompt-s5-author.md:41](/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_t1851-unit-a/prompt-s5-author.md:41)  
  判定: real / must-fix: はい / 成果物影響: index境界を正常化しないままでは、親の統合commitへ意図せず直接取り込まれる。

## 総括

- must-fix は1件。
- 最重は、実装差分5 fileが禁止されていた staged 状態にある契約違反。
- A2' の実装混入、所有外file変更、先行commit、未承認の受理拡大は確認しなかった。
- API、横断予算、lock seam、fail-closed規則は静的には段4裁定どおり。
- pytestは実行しておらず、緑は主張しない。