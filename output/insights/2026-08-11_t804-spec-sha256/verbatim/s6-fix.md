## 総括

実装は完了しました。docs・commit は変更していません。pytest は Pegasus scheduler 認証エラーにより開始前停止したため、**実装済み・未実走**です。緑は主張しません。

主な修正:

- judge に frozen な `ManifestScheduleProjection` を追加。
- `schedule_projection` を default なしの required keyword 化。
- manifest schedule 由来の `n_per_cell`・expected-cells と observations を完全照合。
- 正しい hash のまま別 schedule 相当に改変する metamorphic 負例を追加。
- judge CLI schema 負例へ実 verifier を通る manifest/spec と positive control を追加。
- injected `VerifiedManifest` の type・file hash・document hash・spec hashを各単独で検査。
- manifest 投影負例ごとに baseline verify を追加。
- `no-approved-spec` が先行していた回帰 3 件へ、検査対象と整合する approved-spec fixture を追加。
- 所有外の直接 caller [test_s8b_oracle_report.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t804-spec-sha256/orchestrator/tests/test_s8b_oracle_report.py:358) は、新 required keyword への機械的追随として helper だけ更新。

### 赤の内訳

親実測時の意図的な収束赤:

- manifest pin golden 2 件: 最終 bytes で更新済み。

回帰赤:

- binding driftguard: approved-spec fixture を明示。
- contract SHA mismatch: 変更後 contract を含む spec を承認代役にした。
- CLI rc=3: subprocess 内にも整合する approved-spec snapshot を渡した。

現在の実測赤件数は不明です。以下の範囲を実行しようとしましたが、pytest 起動前に `qstat -Q` が `EACCTAUTH Unknown user-id` で失敗しました。

- `test_s8b_oracle_judge.py` 全体
- manifest 投影負例
- driver injected-token 4 軸
- binding driftguard
- contract SHA mismatch
- CLI rc=3

規律どおり pytest へ直接迂回していません。

### 検査

- `python3 tools/check_codex_agents.py`: rc=0
- `python3 tools/check_docs.py`: rc=0
- `git diff --check`: rc=0
- 対象 test module 5 本の import: 成功
- required keyword 3 件の default 不在: 静的確認済み
- pin raw SHA・各 source hash: 実 bytes と一致

### pin golden

- judge: `6e90a77532e7ea68c14c2076268e38783180c6c142d23ed9ae7d09466201a0b2`
- report: `cc28c86074aead3747eadcaaf1a09a2eaf4bdaae0ca72cca4a9d4f32bfd5acbf`
- artifacts: `b29f3dd6d989044a39f568f9e3621d93a66101b038e9a1913c3500c5e522f614`
- materializer: `a18209eb4501fd8c549cfda2e0427503a3811ddb79566f79af0327bce03632e8`
- outcome-stage-contract: `f8a0bb2237dcaf3c643a78c04ca6b8cea2a8f83e3d306d85c781716b165c73af`
- `PIN_GATE_SPEC_SHA256`: `a64bce7df9181f4b25dcd825d752e1f6c93b7559ff5203ca514eafae70ef7540`

### 波及可能性

- production の `judge_oracle` caller は judge CLI 1 箇所のみで、更新済み。
- `test_s8b_oracle_report.py` の共有 `_judge` helper は追随済み。
- driver fixture は binding driftguard から共有されるため、approved-spec map/loader に依存する。
- `test_s8b_oracle_manifest_contract.py` は judge consumer inventory と source path を監視する。
- `s8b_verdict` は verdict artifact の consumer だが、裁定どおり未変更。
- `s8b_oracle_report.py`・`s8b_oracle_spec.py`・`s8b_oracle_artifacts.py` の既存 A/B 差分には、この fix では触れていません。