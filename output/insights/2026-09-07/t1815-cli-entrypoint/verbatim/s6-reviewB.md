## 実行環境で壊れる経路

所見 1: 一時 Git repo と oracle/CLI が ambient Git 環境・global config を継承し、テストが非 hermetic である  
深刻度: must-fix  
根拠 ([test_s8c_cli_entrypoints.py:31](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1815-cli-entrypoint/orchestrator/tests/test_s8c_cli_entrypoints.py:31), [conftest.py:956](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1815-cli-entrypoint/orchestrator/tests/conftest.py:956)): `_git()` と CLI subprocess に `env=` がない。`init`/`add` は user identity を必要としないが、`init.templateDir`、`core.excludesFile` 等の config を読む。`commit` の `-c user.*` も `commit.gpgSign` や template hook を無効化しない。さらに `GIT_DIR`、`GIT_WORK_TREE`、`GIT_INDEX_FILE` は repo/index を差し替え、xdist worker 間の共有 index 競合も作れる。conftest の閉じた Git env はこの新 fixture には使われない。  
推奨: 放置すると fixture commit・oracle の参照先またはテスト受理結果が実行者環境で変わる。conftest と同型の allowlist envを作り、fixture の全 Git、親 process の `P.read_blob_at`/`activation_report_at`、4 CLI subprocess のすべてへ適用する。

所見 2: module-scope oracle は受入 xdist では最大4回評価され、裁定の「1回だけ」は直列走にしか成立しない  
深刻度: nit  
根拠 ([test_s8c_cli_entrypoints.py:68](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1815-cli-entrypoint/orchestrator/tests/test_s8c_cli_entrypoints.py:68), [decisions.md:29779](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1815-cli-entrypoint/docs/decisions.md:29779)): 4 parameter node は xdist group を持たず、各 node が独立 work unit になる。別 workerへ配れば workerごとに `tiny_repo` と oracle が1回ずつ、合計最大4回構築・評価される。1.31秒は直列自走 harness の値である。  
推奨: 現状は bounded で5分上限を脅かさないため、報告を「workerごとに1回、最大4回」へ訂正すれば足りる。厳密に全走1回へ寄せるなら、新groupと4 node集合を [test_real_repo_serialization.py:250](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1815-cli-entrypoint/orchestrator/tests/test_real_repo_serialization.py:250) および [同:312](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1815-cli-entrypoint/orchestrator/tests/test_real_repo_serialization.py:312) の inventoryへ追加する必要がある。conftest の real-repo lock inventoryへの登録は不要。

`cwd=_ROOT` は適切で、`python -m` は repo root を import path 先頭に置くため namespace package `orchestrator` を解決できる。`pytest.ini` は `testpaths`/`norecursedirs`だけでcwdを変えず、conftestにも固定cwdやGit index共有はない。一時dirもworker固有なので、ambient `GIT_*` を除けばworker間競合はない。

## meta-test と焦点走対象の是正

所見 3: consumer列挙は過不足なしだが、列挙した6 suiteを実際には焦点走していない  
深刻度: must-fix  
根拠 ([s5-author.md:69](/home/SFC/tanab/.claude/jobs/52db5317/tmp/t1815/codex-artifacts/t1815-cli-entrypoint/s5-author.md:69), [同:44](/home/SFC/tanab/.claude/jobs/52db5317/tmp/t1815/codex-artifacts/t1815-cli-entrypoint/s5-author.md:44)): `git grep` による consumer 集合は実装子の10 fileと一致し、過剰・欠落ともない。しかし未走は `test_s8c_preregistration_core.py`、`test_s8c_preregistration_invariant.py`、`test_s8c_preregistration_predicates.py`、`test_p3_autonomous_workload_trial.py`、`test_reflux_origin_binding.py`、`test_trial_registry.py` の6 file。  
推奨: 放置するとconsumer退行を検査していないまま受入レポートの参照集合が「確認済み」に見える。親の焦点走へこの6 fileを追加する。既走の `test_s8c_gate_report.py`、`test_t671_source_binding.py`、`test_artifact_admission.py`、`test_ccbench_spawn_sites.py` は維持し、過剰対象はなし。

所見 4: 「plain-runner と pytest collection でmeta-test網羅」という報告は範囲を言い過ぎている  
深刻度: nit  
根拠 ([test_plain_runner_coverage.py:44](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1815-cli-entrypoint/orchestrator/tests/test_plain_runner_coverage.py:44), [test_pytest_collection_config.py:423](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1815-cli-entrypoint/orchestrator/tests/test_pytest_collection_config.py:423)): 全 `test_*.py` を列挙する実meta-testは前者。後者の唯一のglobは名前に `verifier`/`oracle` を含む恒久除外候補だけを調べ、新ファイルのmembership自体は検査しない。実collection全体と台帳をjoinする検査は [test_acceptance_schedule_order.py:660](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1815-cli-entrypoint/orchestrator/tests/test_acceptance_schedule_order.py:660) で、未走である。  
推奨: `test_plain_runner_coverage.py` は正しい対象として維持し、collection/所要側へ `test_acceptance_schedule_order.py` を追加する。`test_pytest_collection_config.py` は保守的な追加対象としては妥当だが、全file inventoryの根拠には数えない。

growth/flaky hold台帳は登録済みkeyの陳腐化だけを完全collection時に検査し、新規nodeを自動holdしない。固定4ファイル・1 commitのtiny repoはrepo成長比例でもないため、新規4 nodeのhold登録と `test_hold_inventory.py` 更新は不要である。`tools/check_docs.py` に `test_*.py` inventoryはなく本差分への特別な反応はないが、親のクラス2/3完了検査としての実行義務は残る。

## 変異の帰属検査

所見 5: M4は`PYTHONPATH=.`でmaskされ、期待した`[gate-path]`赤が環境依存になる  
深刻度: must-fix  
根拠 ([s5-author.md:26](/home/SFC/tanab/.claude/jobs/52db5317/tmp/t1815/codex-artifacts/t1815-cli-entrypoint/s5-author.md:26), [test_s8c_cli_entrypoints.py:146](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1815-cli-entrypoint/orchestrator/tests/test_s8c_cli_entrypoints.py:146)): 実装子の自走環境はrepo rootを`PYTHONPATH`へ入れており、CLI subprocessもそれを継承する。この状態では `sys.path.insert(...)` を削除しても `orchestrator` が既に解決可能で、M4が生存する。  
推奨: 放置すると変異台帳のM4が環境により sensitivity pin/SURVIVED の間で変わる。CLI subprocess環境から少なくとも`PYTHONPATH`/`PYTHONHOME`を除き、`cwd=_ROOT`だけでmodule起動を解決させる。これを所見1の閉じたenvへ統合する。

所見 6: M3/M4には別の構造検出層があり、「期待赤1 nodeの完全集合・他層なし」は無条件には成立しない  
深刻度: must-fix  
根拠 ([test_campaign_import_invariant.py:931](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1815-cli-entrypoint/orchestrator/tests/test_campaign_import_invariant.py:931), [growth_test_holds.py:279](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1815-cli-entrypoint/orchestrator/tests/growth_test_holds.py:279)): M3/M4はいずれも逐語`DIRECT_BOOTSTRAP`を壊すため、hold解除時には `test_real_campaign_package_has_canonical_direct_bootstrap` も赤になる。既定走ではこのnodeがgrowth holdでskipされるため、観測赤は`[gate-path]`だけだが、全suiteに対する単一層性ではない。  
推奨: 放置すると変異台帳の期待node集合と単一理由性の記録が実行modeで変わる。既定hold下の期待集合は`[gate-path]`、明示opt-in時はcampaign invariant nodeも追加、と条件付きで記録し、M3/M4を「構造gateと実process gateの冗長diagnostic pin」と明記する。

M1は`[prereg-path]`と`[prereg-module]`、M2は`[prereg-module]`だけで完全集合となる。alias blockを参照する別の構造pinは見つからず、M1/M2の単一理由性は成立する。M3も既定hold下では`[gate-path]`だけ、M4は所見5のenv修正後に同じ集合となる。

4変異とも成功/有効化を新たに受理せず、`effective=false`またはそれ以前のfail-closed終了のままである。したがってKILLEDではなくdiagnostic sensitivity pinとする分類自体は正しい。

## 所要と台帳

所見 7: 新規4 nodeが所要台帳に未登録で、1.31秒のsuite総時間だけでは登録できない  
深刻度: must-fix  
根拠 ([acceptance_duration_ledger.json:19521](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1815-cli-entrypoint/orchestrator/tests/acceptance_duration_ledger.json:19521), [update_acceptance_duration_ledger.py:83](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1815-cli-entrypoint/tools/update_acceptance_duration_ledger.py:83)): 現台帳は19517 entryで`test_s8c_cli_entrypoints` hitが0件。consumerは未登録nodeを初期distribution窓の既知値から導くunknown costへ倒す。updaterはJUnit testcaseごとの実測値を要求するため、4件総計1.31秒を手割りしてはならない。  
推奨: 放置すると所要台帳の4参照が欠け、受入schedulerの値と網羅率が実collectionからずれる。post-commit走を`tools/run_tests.py ... test_s8c_cli_entrypoints.py --junitxml=<repo外>/t1815.xml`で取得し、`python3 tools/update_acceptance_duration_ledger.py <repo外>/t1815.xml --repo <root> --add-only`を実行する。その後`test_update_acceptance_duration_ledger.py`と`test_acceptance_schedule_order.py`を焦点走する。現tipだけなら4 entry増、`nodeid_count=19521`になる。

## 総括

現状はNO-GO。productionの2 bootstrap自体には本レンズで追加欠陥を確認しなかったが、次の4点が受入前に必要である。

- Git/Python subprocess環境の閉鎖
- 未走consumer 6 fileの焦点走
- M4の`PYTHONPATH` mask解消とM3/M4の冗長gate記録
- 実測JUnitによる4 nodeの所要台帳追加

このレビューではpytestを実走しておらず、実装子報告の緑を独立確認済みとは扱っていない。ファイル変更も行っていない。