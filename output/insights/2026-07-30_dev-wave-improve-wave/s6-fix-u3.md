段6 U3 の全裁定を current bytes に実装しました。

変更ファイル:

- [buildcache.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve-u3/orchestrator/campaign/buildcache.py)
- [s2_verify_calibration.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve-u3/orchestrator/campaign/s2_verify_calibration.py)
- [s3_lock_coverage.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve-u3/orchestrator/campaign/s3_lock_coverage.py)
- [s5_permutation_coverage.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve-u3/orchestrator/campaign/s5_permutation_coverage.py)
- [s8a_trigger_coverage.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve-u3/orchestrator/campaign/s8a_trigger_coverage.py)
- [s8a_trigger_freq.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve-u3/orchestrator/campaign/s8a_trigger_freq.py)
- [test_campaign.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve-u3/orchestrator/tests/test_campaign.py)
- [test_buildcache_v2.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-improve-u3/orchestrator/tests/test_buildcache_v2.py)

所見の状態:

- scheduler F10 canonical import shadow: closed。resolved path、module object、spec origin、主要定義のcode identityを検証し、`sys.path` poisonを排除、canonical-lookingな`sys.modules` poisonも拒否します。
- contract F5 `s8a_trigger_freq` 遅延gate: closed。main先頭で観測し、pin/single-tenant/tempdir/patch/subprocess前に拒否。同じobservationを共有helperへ渡します。
- contract F10 helper mutation被覆: closed。4 helperを直接呼ぶ表駆動testを追加し、loginの副作用前拒否とcompute/OTHERのmock subprocess `-j 16`到達を検査します。
- buildcache valid-hit/login-miss順序、cache/freeze keys、既定`-j16`: 静的確認上は維持。

実施した軽量確認:

- 所有8 fileのAST parse: 成功
- 5 campaignのisolated importとcanonical identity: 成功
- 別worktreeによる`sys.path` poison control: canonical pathを選択
- canonical-lookingな`sys.modules` poison control: 拒否
- `git diff HEAD --check`: 成功

未実走:

- pytest、build、qsub、mutation、acceptance
- `check_codex_agents.py`、`check_docs.py`

login node制約により上記は実行しておらず、greenは主張しません。残riskはcompute nodeでのtargeted/full/mutation実走と統合後再レビューです。また共有Git indexがread-onlyで再stageできなかったため、修正は既存staged差分上のunstaged current bytesです。親は`git diff HEAD`から取得するか、統合側で所有8 fileをstageしてください。U1の未追跡2 fileは読み取りのみで変更していません。

## 総括

U3裁定項目はcurrent bytes上でclosed。動的検証のみpartialで、compute nodeでの親検査待ちです。
