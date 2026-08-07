実装子 A の担当範囲 A1〜A5 と preflight helper を実装しました。コード・テスト以外は変更せず、commit / add / push も行っていません。

## 1. 変更ファイル

認可強制点:

- [execution_guard.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t609-impl-a/orchestrator/campaign/execution_guard.py): 5 条件を一か所で検査する `require_certified_writer_authorization` を追加。exact 型、registry 同値、runtime 完全一致、compute 上の exact-Pegasus、selector 同値を強制。
- [pipeline.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t609-impl-a/orchestrator/campaign/pipeline.py): 必須 keyword-only `authorization_contract` を追加し、全 sink 書込み・build より前に検査。
- [loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t609-impl-a/orchestrator/campaign/loop.py): 同じ必須引数を追加。layout 作成前に認可・required attestation を検査し、`evaluate` へ転送。
- [screening_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t609-impl-a/orchestrator/campaign/screening_driver.py): WAL repair 前に集中述語を呼び、`evaluate` へ転送。
- [s1_direct_comparison.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t609-impl-a/orchestrator/campaign/s1_direct_comparison.py): campaign 書込み前に登録済み契約を検査し、injected `evaluate_fn` へ転送。
- [t126_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t609-impl-a/orchestrator/qualification/t126_driver.py): Pegasus 契約を `pipeline.evaluate` へ転送。
- [s8b_oracle_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t609-impl-a/orchestrator/campaign/s8b_oracle_driver.py): plan の契約を injected `evaluate_fn` へ転送。

`run_campaign` の 12 module・15 呼出し:

- [backoff_repro.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t609-impl-a/orchestrator/campaign/backoff_repro.py)
- [backoff_sweep.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t609-impl-a/orchestrator/campaign/backoff_sweep.py)
- [demo.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t609-impl-a/orchestrator/campaign/demo.py)
- [p2_2.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t609-impl-a/orchestrator/campaign/p2_2.py)
- [p3_kickoff.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t609-impl-a/orchestrator/campaign/p3_kickoff.py)
- [p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t609-impl-a/orchestrator/campaign/p3_s4_loop.py)
- [p3_s4_loop_sort.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t609-impl-a/orchestrator/campaign/p3_s4_loop_sort.py)
- [p3_s4_loop_trigger_gating.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t609-impl-a/orchestrator/campaign/p3_s4_loop_trigger_gating.py)
- [p3_s4_red.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t609-impl-a/orchestrator/campaign/p3_s4_red.py)
- [s6_sort_sweep.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t609-impl-a/orchestrator/campaign/s6_sort_sweep.py)
- [s8a_trigger_sweep.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t609-impl-a/orchestrator/campaign/s8a_trigger_sweep.py)
- [sanity_silo.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t609-impl-a/orchestrator/campaign/sanity_silo.py): 契約を一度 lookup し、`numactl=list(contract.numactl)` も配線。

Helper:

- [certified_writer_preflight.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t609-impl-a/orchestrator/campaign/certified_writer_preflight.py): stdin 実行用の薄い CLI adapter。exit 0/3/4、stdout 無し、stderr JSON 1 行。
- [certified_writer_admission.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t609-impl-a/orchestrator/campaign/certified_writer_admission.py): floor/T126 の read-only admission を既存検証 leaf へ配線。receipt、source blob、T126 ledger/qsub binding、registry、calibration、compute site を検査。
- [s8b_floor_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t609-impl-a/orchestrator/campaign/s8b_floor_campaign.py): current protocol validator を public leaf 化。
- [contract.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t609-impl-a/orchestrator/qualification/contract.py): immutable blob 用 `load_protocol_bytes` を追加。既存 duplicate-key readerと `validate_protocol` を再利用。
- Helper は `REQUIRED_CODE_IDENTITY_PATHS` に追加していません。

テスト:

- [test_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t609-impl-a/orchestrator/tests/test_campaign.py): M1〜M5、P-1（evaluate/run_campaign）、12 module・15 call inventory、helper CLI 契約を追加。既存成功 fixture は認可を bypass せず registry 値を通すよう更新。
- [test_dev_wave_land.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t609-impl-a/orchestrator/tests/test_dev_wave_land.py): `loop.run_campaign` consumer を更新。
- [test_p3_build_authority_cli.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t609-impl-a/orchestrator/tests/test_p3_build_authority_cli.py): 3 個の direct evaluate fixture を更新。
- [test_s1_direct_comparison.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t609-impl-a/orchestrator/tests/test_s1_direct_comparison.py): direct evaluate fixture を更新。
- [test_s6_sort_sweep.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t609-impl-a/orchestrator/tests/test_s6_sort_sweep.py): injected run fixture を更新。
- [test_s8a_trigger_sweep.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t609-impl-a/orchestrator/tests/test_s8a_trigger_sweep.py): injected run fixture を更新。
- [test_s8b_oracle_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t609-impl-a/orchestrator/tests/test_s8b_oracle_driver.py): direct evaluate fixture を更新。
- [test_screening_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t609-impl-a/orchestrator/tests/test_screening_driver.py): screening consumer を登録済み runtime 値へ更新。
- [test_t126_qualification_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t609-impl-a/orchestrator/tests/test_t126_qualification_driver.py): 全 direct evaluate fixture に Pegasus authorization を追加。

既存の assert、`pytest.raises`、skip、期待値は変更・緩和していません。

## 2. 検証結果

pytest は未実走です。次の targeted nodeid を `tools/run_tests.py` 経由で要求しました。

- `test_m1_pipeline_requires_authorization_before_any_sink_write`
- `test_m2_pipeline_rejects_forged_contract_even_when_runtime_matches_it`
- `test_m3_pipeline_rejects_authorization_selector_mismatch`
- `test_m4_pipeline_rejects_unresolved_none_numactl_for_pegasus`
- `test_m5_pipeline_compute_rejects_registered_linux_contract`
- `test_p1_pipeline_accepts_registered_contract_without_enabling_v2_build`
- `test_p1_run_campaign_accepts_registered_contract`
- caller inventory 1 node
- helper CLI 3 nodes

結果は `Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1` で、収集・実行前に停止しました。

続いて変更対象の9 test fileを同 runner へ渡しましたが、同じ dispatch 前停止でした。したがって緑は一件も主張しません。submodule marker 不在警告も出ましたが、既知の `external/ccbench` 未初期化由来であり回帰には数えていません。

実走できた非-pytest 検査:

- `git diff --check`: 成功。
- 全変更 module 23 個の `python3 -B` import と必須 signature 検査: 成功。
- 全 Python file の AST parse: 成功。
- `pipeline.evaluate` consumer の静的 closure: 意図的な M1 以外すべて配線済み。
- 認可述語 smoke: 正例1、M1〜M5相当の拒否5を確認。
- caller inventory smoke: 12 module・15 call を確認。
- helper exact stdin invocation:
  - 不正 receipt: exit 3、JSON 1 行。
  - 引数不足: exit 4、JSON 1 行。
- `python3 tools/check_codex_agents.py`: 成功。
- `python3 tools/check_docs.py`: `違反なし`。

## 3. 波及可能性

`pipeline.evaluate` の必須引数追加が直接影響する test file は全件次の7本です。

- `test_campaign.py`
- `test_p3_build_authority_cli.py`
- `test_s1_direct_comparison.py`
- `test_s6_sort_sweep.py`
- `test_s8a_trigger_sweep.py`
- `test_s8b_oracle_driver.py`
- `test_t126_qualification_driver.py`

間接 consumer は `test_dev_wave_land.py` の `loop.run_campaign` と `test_screening_driver.py` です。`test_campaign._mock_pipeline` は `test_t126_qualification_driver.py` から共有 fixture として import されます。

所有外で親/B側へ残る波及:

- `tools/pegasus/floor_campaign.sh`
- `tools/pegasus/t126_qualification.sh`
- `test_pegasus_floor_tools.py`
- `test_t126_pegasus_tools.py`

これらには helper の source-commit blob抽出、最初の管理対象書込み前の呼出し、非0停止、順序テストが必要です。権限境界に従い未編集です。

外部の未追跡 consumer が `pipeline.evaluate` / `run_campaign` / `evaluate_candidate` を直接呼ぶ場合も、新しい必須 keyword が必要です。

## 4. 受理・拒否差分

変更前は authorization 無しの `pipeline.evaluate` / `run_campaign` が受理され、legacy 経路では `numactl=None` も通りました。compute 上の exact-Pegasus 制約は限定された caller 側だけでした。

変更後は次だけが新たに拒否されます。

1. authorization の欠落・`None`・非exact型。
2. registry lookup結果と同値でない自作・drift契約。
3. `env_tag` / `clocks_per_us` / `numactl` の不一致。未解決 `numactl=None` を含む。
4. Pegasus compute 上の非Pegasus契約。
5. authorization と build selector `env_contract` の不一致。

登録済み契約と runtime が一致する経路は引き続き受理されます。`env_contract=None` は従来どおり legacy build、非`None`は従来どおり build-v2 selectorです。P-1 smoke でも legacy build選択が維持されています。

したがって受理集合の変化は段4 §5記載の縮小だけで、拡大はありません。認可事実をWAL/proof bytesへ永続化する変更もしていません。

## 5. 期待赤 finding

親 docs 未landに起因すると事前指定した期待赤集合は空集合です。docs は親所有で、今回の code/test API変更に未land文言を期待するテストは追加していません。実際に `check_docs.py` は成功しました。

非回帰として区別するのは次だけです。

- `qstat -Q` 失敗による runner の未実走。
- `external/ccbench` 未初期化に由来する将来のskip/赤。

これら以外に赤が出た場合は回帰として扱う必要があります。

## 6. 未実装・未確認

- A1〜A5とhelper本体に未実装項目はありません。
- B所有のshell配線・Bテストは未実装です。
- pytestは環境制約により未実走です。
- 正しい実receipt/calibrationを使ったcompute-node上のhelper P-2統合は未確認です。
- docs、worklog、handoff、commitは明示された権限境界により未変更です。
- 信頼境界を越えて検査省略や「検証済み」と記録させる文言には従っていません。

## 総括

Python層の certified writer authorization closure と read-only preflight helper は実装済みです。静的検査と直接smokeは成功していますが、pytestはdispatch基盤停止のため未実走です。親はB所有wrapperを配線したうえで、初期化済みsubmodule・実行可能な計算ノード環境で上記nodeidとconsumer test全体を実走してください。