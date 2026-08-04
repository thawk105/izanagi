S1・S2′・S3 を指定範囲内で実装しました。docs／frozen artifact／issuer／pin は変更せず、commit もしていません。

変更前後の受理挙動は次のとおりです。

- runtime consumer は従来どおり、期待値の中央値から inclusive な許容帯を作り、観測値の全要素が帯内なら受理します。Mapping、exact list、非空列、bool を除く数値 tolerance という型条件や、例外時 `False` も不変です。
- 変更前の CLI は、既存品質条件を満たせば自己不整合な effective clock でも publish できました。
- 変更後は `旧 accepted 集合 ∩ effective-clock self-pass` のみ publish します。失敗時は `effective-clock-self-comparison-failed` を積み、通常品質 rejection と同じ staging を残します。
- runtime consumer、issuer、既存 artifact loader の受理集合は変更していません。`tolerance_pct=100` の広い受理挙動も scope どおり維持しています。

S2′では `linux-baremetal` も registry loop の走査対象に含めました。ただし mode=none の v1 artifact は attestation profile を持たないため、v1／profile 不在を明示検査して自己比較から除外しています。将来 required へ変わると none 分岐を通れず、必ず canonical 述語の検査対象になります。

テスト実走は完了していません。`pegasus02` から正規経路で dispatch しましたが、`qstat -Q` が `Unknown user-id (uid: 31609)` で失敗し、pytest の収集前に停止しました。したがって緑は主張しません。親 docs 未 land を理由に事前予想した赤は 0 件です。

## 総括

- 変更ファイルと関数:
  - [cli.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/cli.py:381): `_effective_clock_self_comparison_passes`、`_certify_main` の publish 前 gate。
  - [execution_guard.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/campaign/execution_guard.py:158): `_independent_comparison_passes` から canonical 関数を共有。
  - [execution_guard.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/campaign/execution_guard.py:182): `effective_clock_comparison_passes`。
  - [test_calibrator_certify.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_calibrator_certify.py:492): self-fail rejection と正例 publish。
  - [test_execution_guard.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_execution_guard.py:360): explicit `want` 付き golden vector。
  - [test_env_contract.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_env_contract.py:436): registry 全走査と現 Pegasus path/SHA の exact 1 件例外。
- 走らせた nodeid と結果:
  - pytest nodeid: 0 件。4 ファイル全範囲の dispatch を試みたが、PBS 認証 preflight で停止。
  - 対象予定: `test_calibrator_certify.py`、`test_execution_guard.py`、`test_env_contract.py`、meta-test `test_plain_runner_coverage.py`。
  - `py_compile`: 変更した5ファイルすべて成功。
  - `git diff --check`: 成功。
  - 旧述語との静的比較: 304 入力で一致。これは pytest 実走の代替ではありません。
- 現行挙動と差:
  - consumer の受理・拒否挙動は不変。
  - CLI publish のみ自己不整合 artifact を追加拒否。
  - rejection は例外経路でなく既存品質 rejection 形。registered rename より前に発火。
- 静的な波及可能性:
  - 所有外 caller: `campaign/loop.py`、`s8b_floor_campaign.py`、`s8b_oracle_driver.py`、`s8b_oracle_report.py`、`s8b_ratified_freeze.py`。
  - 共有 fixture: `test_schema_v2._valid_document`、certify の `_profile`、`env_contract.REGISTRY`。
  - consumer test: `test_execution_guard.py` に加え、`test_s8b_floor_campaign.py`、`test_s8b_oracle_driver.py`。
  - `silo_ladder_rung1.py` の別 consumer と `env_attestation.py` の issuer は未変更。
- 未解決事項:
  - PBS 認証を直した環境で、上記4ファイル全範囲の実走が必要。
  - U-1 probe 是正、U-2 再取得／pin 更新、U-3 tolerance 権威束縛、U-4 別 consumer は scope 外。
  - pre-existing の untracked `output/insights/...` は触れていません。docs編集・add・commit・stashも未実施です。