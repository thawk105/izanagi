## 1. 実装内容

- [s8b_sort_swo_receipt.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_sort_swo_receipt.py:1)
  - portable SWO PASS receipt v1 を新設。
  - identity 5 項目、raw receipt 全体の `receipt_sha256`、raw compiler version の SHA-256 射影を実装。
  - host path、raw `compiler_version`、unknown key、receipt 移植を拒否。
- [s8b_binary_admission.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_binary_admission.py:45)
  - `PORTABLE_SORT_BEST_BUILT_KEYS` と `portable_built_keys_for` を追加。
  - central validator 冒頭で configuration 条件付き exact-key gate を実施し、sort receipt を新 validator へ委譲。
- [s8b_floor_contract.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_floor_contract.py:32)
  - result v4、manifest v3、admission receipt v1 を実装。
  - 11-key receipt validator、canonical POSIX relative path、件数束縛を追加。
  - [enumerate_cells](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_floor_contract.py:387) に `sort_best` 必須 gate を追加。
- [s8b_holdout_admission.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_holdout_admission.py:84)
  - 構造化例外、read-only shared lock、[inspector](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_holdout_admission.py:1545) を追加。
  - campaign-filtered digest、claim/main/attempt/consumed の完全照合、missing と zero-byte の独立 reason を実装。
  - missing は `unverifiable`、到達済みの zero-byte・改竄・coverage 不一致は `mismatch` とした。
- [s8b_floor_evidence_fixture.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/tests/s8b_floor_evidence_fixture.py:33)
  - deterministic raw SWO attempt、独立 portable 射影、tmp admission filesystem builder を新設。
  - ledger digest は production inspector/projector を使わない独立 canonical JSON 実装。
- 指定された4テストファイルを更新・新設し、8縮退分岐、central exact-key、identity 移植、host値排除、独立 digest を固定した。

docs、所有外ファイル、commit、git 操作には触れていない。

## 2. 実走した nodeid と結果

pytest nodeid の実走は **0件**。緑0件、テスト赤0件、infra失敗3回。

指定4ファイルの wrapper 走を2回、単独の `test_s8b_sort_swo_receipt.py` を1回試みたが、すべて `qstat -Q preflight rc=1` により dispatch infrastructure failure、rc=16 で停止した。Pegasus login node の headroom は約1.15 GiBで、規律に反して pytest を直接起動する迂回はしていない。

補助検査として以下は成功したが、pytest の緑には数えていない。

- AST・import 検査: 9ファイル成功
- tmp filesystem と純関数による手動焦点 smoke: 20 function cases 成功
- NFC・結合文字検査: 9ファイル成功

したがって状態は「実装済み・pytest未実走」であり、closed とは申告しない。

## 3. 期待赤

U1/U2 未実装により予想される赤は次の9ファイル。

- `test_s8b_floor_campaign.py`
- `test_s8b_floor_stats.py`
- `test_s8b_ratified_verify.py`
- `test_s8b_ratified_freeze.py`
- `test_s8b_holdout_freeze.py`
- `test_s8b_materialization.py`
- `test_s8b_freeze_io.py`
- `test_s8b_oracle_driver.py`
- `test_s8b_oracle_report.py`

これらは xfail・skip 化していない。pytest が起動できなかったため、期待赤以外の回帰赤の有無は未判定。

## 4. 受理・拒否差分

| 面 | 変更前 | 変更後 |
|---|---|---|
| SWO receipt | portable 契約なし | exact 19-key、5 identity、raw receipt commitment が必須 |
| compiler情報 | portable 射影なし | raw version/path を拒否し、version SHA-256 のみ受理 |
| binary central gate | extra top-level key を単体 validator が見逃す | sort/non-sort 双方で条件付き exact key |
| sort receipt | 欠落・非sort混入を central validator が扱わない | sortは必須、非sortは存在自体を拒否 |
| schema | result v3 / manifest v2 | result v4 / manifest v3 のみ |
| freeze cells | stock のみ必須 | stock に加えて `sort_best` 必須 |
| ledger状態 | `_read_ledger` は欠落とzero-byteをともに `[]` | inspector が missingとzero-byteを別reasonで拒否 |
| live evidence | read-only inspectorなし | root・claim・両ledger・marker・digestをfail-closed検査 |
| 他campaign追記 | digest契約なし | `campaign_run_id` 外の行はdigest不変 |

裁定 §0 に従い、「実成果物0件」「bytes pinなし」は根拠に使用していない。実在する2件はlegacy v2で既に現行から拒否済み、generator pinは実在する前提で扱った。

## 5. 所有外への波及可能性

- U1 producer: `s8b_floor_campaign.py` は conditional portable/runtime key、SWO射影、admission inspector、result fieldへの接続が必要。
- U2 consumers: `s8b_floor_stats.py`、`s8b_ratified_freeze.py`、`s8b_holdout_freeze.py`、`s8b_oracle_driver.py` は新schema、conditional key、live inspector入口への対応が必要。
- `s8b_oracle_report.py` は ratified reverify の拒否伝播確認が必要。
- 共有 fixture consumer: `s8b_v2_freeze_fixture.py`、floor/stats/ratified/freeze/oracle系テスト。
- `test_pegasus_floor_tools.py` は `enumerate_cells` の新 `sort_best` gateへ静的波及する可能性がある。
- U1/U2では新共有 fixtureの独立 digestを維持し、production inspectorで期待値を生成してはならない。

## 6. 保証境界 docstring

- module: [s8b_sort_swo_receipt.py:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_sort_swo_receipt.py:1)
- projector: [s8b_sort_swo_receipt.py:130](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_sort_swo_receipt.py:130)
- validator: [s8b_sort_swo_receipt.py:204](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_sort_swo_receipt.py:204)
- admission module: [s8b_holdout_admission.py:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_holdout_admission.py:1)
- inspector: [s8b_holdout_admission.py:1545](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_holdout_admission.py:1545)

## 総括

完了した契約: U0のSWO receipt、conditional binary gate、schema/admission validator、read-only inspector、独立共有fixtureを実装した。

残した赤: pytestはdispatch障害で未実走。U1/U2由来の期待赤9ファイルと、その他の回帰有無は親の全走で確認が必要。

U1/U2への申し送り: conditional helperと共有fixtureを使用し、producer発行・live consumer入口を接続すること。自己申告receiptの自己照合やproduction digestによる期待値生成は避けること。