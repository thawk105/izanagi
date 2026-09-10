## 1. 変更した file と行

[orchestrator/tests/test_artifact_admission.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1143-epoch-closure/orchestrator/tests/test_artifact_admission.py:44)

- 44〜57 行: production から独立した literal 12 path tuple `_EXPECTED_E1_CLOSURE_PATHS` を追加。
- 329〜357 行: fixture の file 作成、`git add`、expected epoch payload を新 tuple へ切替。
- meta assert は追加せず。既存の `test_t671_source_binding.py` が exact equality を検査しており、重複させると変異の赤理由が複数になるため。

## 2. 所見への対応

`partial`

fixture と expected epoch の production tuple 従属は静的に解消済みです。AST 検査で以下を確認しました。

- literal tuple は 12 件で、現行 production と順序込み一致。
- 対象 helper 2 件に `CONTRACT_LOADER_RELATIVE_PATHS` 参照なし。
- production tuple から verifier path を外しても fixture file は残る構造。

ただし pytest は infrastructure failure により 0 件実行だったため、worker 契約に従い `closed` とは申告しません。

## 3. production を 1 byte も変えていないことの確認方法と結果

- `git diff --quiet b20c5459 -- orchestrator/campaign orchestrator/verifier`: rc=0
- `git diff --quiet b20c5459 -- docs output`: rc=0
- `git diff --name-only b20c5459`: 対象 test file 1 件のみ
- HEAD: `b20c5459` のまま。commit なし。
- `git diff --check`: 成功。

## 4. 実走した検査

次の 7 function、parametrize 展開後 10 node を `tools/run_tests.py --force-dispatch` へ投入しました。

- `test_certified_acceptance_admits_exact_e1_fixture`
- `test_certified_acceptance_rejects_e1_stale_exact_map_mismatch`
- `test_certified_acceptance_rejects_each_verifier_drift_fail_closed` の 4 path
- `test_certified_acceptance_distinguishes_current_closure_unavailable`
- `test_historical_epoch_display_is_independent_of_live_closure_bytes`
- `test_historical_view_cannot_cross_certified_type_boundary`
- `test_lock_only_epoch_api_does_not_read_wal`

結果は `qstat -Q preflight rc=1`、runner rc=16。pytest node は 1 件も実走しておらず、緑には数えていません。

補助検査は以下が成功しました。

- `python3 tools/check_codex_agents.py`: rc=0
- `python3 tools/check_docs.py`: rc=0
- 独立 tuple と production の静的 AST 比較: 一致、12 件

## 5. 波及可能性の静的列挙

- 所有外 production caller: 変更なし。campaign admission、lock codec、contract binding の受理・拒否条件には波及しません。
- 共有 fixture: `_committed_closure_repo()` と `_expected_fixture_epoch()` は同 file 内だけで参照され、他 test module からの参照はありません。
- consumer test: 上記 7 function が fixture 変更の直接影響範囲です。
- `test_v2_committed_admission_ignores_dirty_live_loader_disk` など、production tuple 自体を検査する別 fixture は変更していません。
- 成果物への影響は runtime 動作ではなく、M1〜M4 が fixture 構築エラーではなく certified gate の不検出を理由に失敗できるようになる点です。

## 総括

独立 literal 12 path tuple を追加し、問題の fixture 従属を切りました。  
production、verifier、docs、output は変更しておらず、commit もありません。  
静的検査では所見の原因を解消しています。  
pytest は dispatch infrastructure failureで未実走のため、判定は `partial` です。