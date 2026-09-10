U5 実装を working tree に残しました。コード・対象テスト以外は編集せず、git add / commit / branch 操作も行っていません。

変更対象:

- [s8b_floor_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-u5/orchestrator/campaign/s8b_floor_campaign.py)
- [s8b_materialization.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-u5/orchestrator/campaign/s8b_materialization.py)
- [s8b_oracle_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-u5/orchestrator/campaign/s8b_oracle_driver.py)
- [test_s8b_floor_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-u5/orchestrator/tests/test_s8b_floor_campaign.py)
- [test_s8b_oracle_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/t342-u5/orchestrator/tests/test_s8b_oracle_driver.py)

### 変更前後の受理・拒否挙動

変更前:

- wrapper:
  - unknown mode を拒否。
  - official + 非既定 seam を拒否。
  - default official は `_assert_official_permitted()` で拒否。
- core:
  - mode 値域だけを検査。
  - `_assert_official_permitted()` を呼ばない。
  - official + 任意 `build_fn` を受理でき、その結果が `mode == "official"` だけで refreeze eligible になり得た。

変更後:

- wrapper の既存 seam 拒否集合は維持。
- official permit gate を core 内へ移動。
- core は official + 非既定 `build_fn` を副作用前に拒否。
- official materializer は `buildcache.build_v2` に固定。
- floor build は `SourceEvidence` と freeze entry digest に束縛した review receiptから admissionを導出し、U2の `build_context/source_evidence` APIへ渡す。
- oracle は `pipeline.evaluate()` に `BuildRunContext` と source-bound capability resolverを渡す。

official materializer 注入拒否の test nodeid:

- `orchestrator/tests/test_s8b_floor_campaign.py::test_run_campaign_core_rejects_official_materializer_injection_before_side_effects`

### 検査結果

成功:

- 変更した production 3ファイル・test 2ファイルの `python3 -m py_compile`
- `git diff --check`

pytest は計算ノードdispatchを次の2範囲で試しましたが、どちらも実行前に `qstat -Q preflight rc=1` で失敗しました。

- `test_s8b_floor_campaign.py -k test_run_campaign_core_rejects_official_materializer_injection_before_side_effects`
- `test_s8b_oracle_driver.py -k test_success_wal_order_budget_and_evaluate_contract`

したがって実行済みpytest nodeidは0件で、greenとは主張しません。両変更test fileの上記以外、フルスイート、build、campaign実走、mutationは未実行です。

### 期待する赤と回帰

現在のU1/U2のみ適用済みtreeでは、registry静的testはU3未適用を検出して赤になる想定です。

- `test_materializer_registry_covers_all_python_build_launches`
- 未配線として検出する9箇所:
  - `backoff_overthrottle.py`
  - `backoff_profile.py`
  - `between_run_floor.py`
  - `p3_kickoff.py`
  - `s1_verify_extime_calibration.py`
  - `s2_verify_calibration.py` の2箇所
  - `s3_lock_coverage.py`
  - `s5_permutation_coverage.py`

これはU3の所有範囲です。それ以外の赤は回帰扱いですが、pytest未実行のため観測された回帰赤はありません。

### 所有外への静的波及

- 上記U3 callerは新しい `build_context/source_evidence` 配線が必要。
- `pipeline.evaluate()` の strict fake/fixtureは、旧 `admission=` から context + capability resolverへ追随が必要。
- `ReviewId.S8B_FLOOR/S8B_ORACLE` とU1 policy registryがS8b receipt identityの前提。
- registry testは今後追加されるdirect-CMake producerを検出し、admission gatewayか明示deny registryへの分類を要求する。
- U2 receipt digestによりS8b build cache identityは従来entryと共有されない。

## 総括

最重要の設計判断は、official coreがcaller注入のmaterializerを一切使わず、admission-awareな既定gatewayを自ら選ぶことです。wrapper迂回ではこの選択を変更できません。

一方、`eligible_for_refreeze` は依然としてreceipt chainではなくmode由来です。またcontent-addressed storeのresume取得、shell materializer、calibratorの任意binary path、in-process issuerの真正性も閉じていません。これらはdocstringで既知限界として明記し、防壁として数えていません。