## 実装結果

実装済み・未実走です。変更は指定された 2 file のみに残しています。

- [s8b_holdout_admission.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2107-t1851-b1-author/orchestrator/campaign/s8b_holdout_admission.py:253)
  - `+324 / -1` 行、現在 6752 行
  - `CellHoldoutAdmission.measurement_generation_claim_digest: str | None` を default なしで追加
  - `FloorAttemptConsumptionMarker` と `validate_floor_attempt_consumption_marker` を追加し `__all__` へ公開
  - current claim、主台帳、marker、4 軸 slot を再導出
- [test_s8b_holdout_admission.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2107-t1851-b1-author/orchestrator/tests/test_s8b_holdout_admission.py:2138)
  - `+404 / -0` 行、現在 4041 行
  - 正例、cut-6 正例、指定された負例を独立 node または parametrize node として追加

合計 `+728 / -1` 行です。`git status --short` は上記 2 file だけです。runner が生成した未起動 dispatch receipt は除去済みです。`git add`、`git commit` は行っておらず、HEAD は base `6ff06800de0e2a0a8ac261d2e20320e68db8ebb3` のままです。

## 不変条件

不変条件 1 は形 (b) を採用しました。

`FloorAttemptConsumptionMarker.use()` が使用時に marker・current claim・主台帳を root lock 内で再読込・再導出し、その同じ lock 内で保護対象 callback を実行します。発行後の marker 削除、extra key、claim 改竄、主台帳改竄をそれぞれ拒否するテストを追加しました。

形 (a) は採用していません。B1 が capability を返し、後続の単位 A が後から使用する契約なので、発行と使用を単一 lock 区間へ閉じるには層を統合する必要があり、現在の分割では成立しません。

capability は現行世代専用です。docstring に明記し、未登録 token と legacy inspector token からの発行入口は追加していません。

## Identity の権威

| `use` 引数 | admission 側の権威 |
|---|---|
| `root` | issued `_CellState.root` |
| `measurement_generation_claim_digest` | current claim を `_measurement_generation_claim_identity()` で再導出した値 |
| `attempt_id` | current claim の `attempt_ids`、正準 `session-start`、再導出 marker |
| `campaign_run_id` | current claim と完全一致する主台帳行 |
| `manifest_sha256` | current claim の `manifest_sha256` と主台帳 |
| `run_relpath` | current claim と主台帳 |
| `cell_id` | current claim と主台帳 |
| `freeze_holdout_key` | current claim の canonical `key` と主台帳。slot 第 1 軸 |
| `configuration_id` | current claim の canonical `key` と主台帳。slot 第 2 軸 |
| `repetition` | 正準 durable `session-start.round - 1`。slot 第 3 軸 |
| `attempt_ordinal` | planned は `0`、retry は検証済み `retry_ordinal`。slot 第 4 軸 |

`cell_effect_digest` と `measurement_generation_digest` も current claim から内部再導出しますが、呼び手の引数にはしていません。registry の classification claim digest は capability identity に流用しておらず、legacy の cell-effect digest も current claim digest の代用にしていません。

## Constructor 監査

repo 全体を Python AST で数え直しました。

- `CellHoldoutAdmission(...)`: 2 箇所
- 位置引数構築: 0 箇所
- keyword-only 構築: 2 箇所

fresh/resume 側は `row["measurement_generation_claim_digest"]`、inspector 側は current なら `claim_identities[cell_id]`、legacy なら `None` を明示します。

## 受理集合

scope 前は、既存 `consume_attempt_ticket` が issued token、frozen ticket、journal authorization を検査し、current marker を root lock 下で作成して attempt ledger へ追記します。既存 validator は current/legacy marker を dispatch し、legacy cut-6 回復経路も保持しています。

この挙動は変更していません。

- `consume_attempt_ticket` の既存処理は未変更
- 既存 marker validator と canonical builder は未変更
- legacy inspector、legacy cut-6 回復は未変更
- adapter と既存 caller は新 API をまだ呼ばない
- 新 API は current issued token、canonical marker、再導出可能な claim、該当主台帳 exactly one、正準 4 軸 slot にだけ閉じる
- marker があり attempt-ledger 行がない cut-6 状態は新 API でも受理する正例を追加

## 実走結果

指定 command は最終差分に対して実行しました。

```text
python3 tools/run_tests.py orchestrator/tests/test_s8b_holdout_admission.py -q -rf
```

結果は `rc=16` です。`qstat -Q preflight rc=1` により dispatch child が起動せず、実走 nodeid は 0 件でした。

- passed: 0 件
- failed: 0 件
- 実行済み nodeid: なし
- infrastructure failure: 1 件
- 親 baseline の `190 passed / 0 failed` は参照しただけで、今回の緑としては主張しません

targeted run と collect-only も同じ理由で child 未起動でした。AST parse、module import、`git diff --check`、constructor 全数監査、必須 helper 呼出しと test 名の静的 meta-check は成功しています。

## 所有外への波及

静的に確認した波及候補は次のとおりです。

- `s8b_floor_campaign.py`、`s8b_floor_stats.py`、`s8b_holdout_freeze.py`
  - 既存 consume/inspect API の caller。署名と挙動は変更していません。
- `s8b_attempt_registry.py`
  - admission module を import しますが、新 capability の caller 化は単位 A 所有として未実装です。
- `test_s8b_attempt_registry.py`
  - adapter と legacy marker の consumer test。変更していません。
- `s8b_floor_evidence_fixture.py`
  - legacy evidence bytes の共有 producer。変更せず、inspector token には `None` を射影します。
- `test_s8b_holdout_freeze.py`、`test_s8b_floor_campaign.py`、`test_s8b_floor_stats.py`
  - 既存 API の外部 test caller。新 field は serialized bytes に流れませんが、dataclass の repr・equality・hash shape は変化します。
- `__all__`
  - 2 名を追加しました。repo 内に star import は見つかりませんでした。

## 総括

指定 2 file の実装とテスト追加は完了し、受理集合と所有境界は維持しています。ただし Pegasus の dispatch infrastructure failure により pytest node は未実走です。したがって状態は「実装済み・未実走」であり、closed や green とは申告しません。