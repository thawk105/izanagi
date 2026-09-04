## 変更前の候補選択挙動

基準 commit `764fdf202` では、`calibration/*.json` の直下 record を走査集合へ加え（`layer3_report.py:507-515`）、有効な v2 lock authority の pin も `_validated_pin_path` の path/file/SHA 検証後に同じ集合へ加えていました（同 `:515-527`）。

within-run は pin と直下 record の和集合から候補化され、records / threads / workload / protocol が一致すれば採用されました（同 `:541-568`）。between-run は pin-only path を除外し、直下 record のみを候補にしていました。`build_report` からの接続点は同 `:827-836` です。

## 実装した内容

| file:line | 変更内容 | 裁定のどの項目に対応するか |
|---|---|---|
| `orchestrator/campaign/layer3_report.py:25-26,77-83` | `SELF_INCONSISTENT_WITHIN_RUN_CALIBRATIONS: frozenset[tuple[str, str]]` を追加。Pegasus g1 の exact `(path, sha256)` 1 件だけを宣言し、D1537 と T-419 U-1/U-2 の削除条件を module docstring に記録 | B1 / A6、プラン v2-1 |
| `orchestrator/campaign/layer3_report.py:524-540` | `_validated_pin_path` を従来どおり先に完遂し、その後で契約 ref の完全一致を判定。missing 時も契約 ref に基づいて除外 | A2 / A3 / A4、プラン v2-2 |
| `orchestrator/campaign/layer3_report.py:549-583` | 対象系列では pin 由来・直下 record 由来とも `candidates["within_run"]` に追加しない。record の構造検証と between-run 経路は維持 | A2 / A4、プラン v2-2 |
| `orchestrator/campaign/layer3_report.py:610-630` | within-run の `contract_pin` にだけ `within_run_exclusion: "self-inconsistent-calibration"` を追加。既存 `status` は変更せず、between-run には理由 key を追加しない | B2、プラン v2-3 |
| `orchestrator/tests/test_layer3_report.py:3469-3510,3818-3892` | 裁定指定の既存 3 件だけを None / `no-matching-env-record` 期待へ変更 | テスト既存 3 件 |
| `orchestrator/tests/test_layer3_report.py:3513-3645` | 直下 copy・系列単位の負例 2 件、健全 g2 pin・宣言の実在束縛の正例 2 件を追加 | テスト追加 4 件 |

新 status、path 正規化、effective-clock の production 再検査は追加していません。

## 実走結果

pytest は未実走です。

- `python3 tools/run_tests.py orchestrator/tests/test_layer3_report.py -q`
  - runner rc=`16`
  - `child_started=false`
  - `qstat -Q preflight rc=1`
  - pytest は開始されていません。

- 指定 3 件、SHA fail-closed 1 件、追加 4 件の計 8 nodeidによる焦点走
  - runner rc=`16`
  - `child_started=false`
  - 同じ dispatch infrastructure failure のため全 nodeid が「実装済み・未実走」です。

計算ノードへの job は投入されていません。runner が作成した dispatch request/receipt 一式は除去済みです。代替の静的検査として `git diff --check` と両変更ファイルの `compile()` は rc=`0` でした。

## 波及の静的列挙

| test file | 参照 | 静的判断 |
|---|---|---|
| `orchestrator/tests/test_layer3_report.py` | `_calibration_floors` / `build_report` / `contract_pin` | 今回の唯一の変更対象。指定ケースと追加 4 件で閉じた |
| `orchestrator/tests/test_autonomous_trial_completeness.py` | `L3.build_report` | fixture は linux-baremetal。変更不要 |
| `orchestrator/tests/test_trial_registry.py` | `L3.build_report` | linux-baremetal fixture。変更不要 |
| `orchestrator/tests/test_t126_qualification_artifacts.py` | `layer3_report.build_report` | qualification rejection と通常 formal campaign の検査で、Pegasus g1 floor 選択に依存しない。変更不要 |
| `orchestrator/tests/test_s8b_oracle_driver.py` | docstring 内で `build_report` を非呼出しと明記 | consumer ではなく変更不要 |
| `orchestrator/tests/test_s1_report.py` | `s1_report.build_report` | Layer 3 と同名の別 API。変更不要 |

production の所有外 caller は `orchestrator/campaign/autonomous_trial_completeness.py` です。公開 `build_report` 接続は変更しておらず、Pegasus g1 authority campaign だけが意図した None へ縮小します。共有 `_campaign` fixture は `test_layer3_report.py` 内の private helper で、外部 fixture consumer はありません。

対象ファイルを直接名指しする外部 meta-test は静的検索で見つかりませんでした。追加 nodeid は ASCII のみで、parametrize ID や手書き xdist marker は追加していません。

## 期待赤

事前登録した pytest finding 集合は空です。今回の pytest に赤が出れば回帰として扱う必要があります。

親所有の docs/worklog/decisions/handoff/phase 更新は未 land のため、それらの未更新だけを文書検査上の期待赤としています。文書検査自体は本単独段では実走していません。

## 総括

Pegasus g1 の exact identity を consumer-local に宣言し、検証後に campaign 系列全体の within-run 候補を空にしました。
既存 status と between-run、g2、linux-baremetal、v1、env mismatch の経路は維持しています。
裁定指定の既存 3 件と追加 4 件を実装し、変更は指定 2 file だけです。
pytest は runner の dispatch preflight failureにより未実走で、静的構文検査のみ rc=0 です。
親側で対象ファイル全走と所有外 consumer、文書検査を実測してください。