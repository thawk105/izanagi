## 実装結果

B-10 report phase を、3 系列とも live 事前登録ではなく campaign lock の記録済み identity に束縛しました。commit／branch／push、docs 編集、現物 report 実走は行っていません。

変更ファイル:

- [b10_backoff_shape_sweep.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/campaign/b10_backoff_shape_sweep.py:546)
- [test_b10_backoff_shape_sweep.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/tests/test_b10_backoff_shape_sweep.py:2526)
- [test_ccbench_spawn_sites.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/tests/test_ccbench_spawn_sites.py:872)
- [write-heavy lock fixture](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/tests/fixtures/b10_backoff_shape_locks/write-heavy.campaign.lock)
- [balanced lock fixture](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/tests/fixtures/b10_backoff_shape_locks/balanced.campaign.lock)
- [read-heavy lock fixture](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/tests/fixtures/b10_backoff_shape_locks/read-heavy.campaign.lock)

fixture は現物と `cmp` で byte 一致し、SHA-256 は順に `0a32c22b…1674`、`087e46df…6b9`、`5abdfe11…80b7` です。

## 関数ごとの受理入力変更

| 関数 | 変更前 | 変更後 |
|---|---|---|
| `load_preregistration` | live v5 文書、patch、current analyzer を一体検証 | live phase の受理集合は不変。current analyzer 検証だけ共有 helper 化 |
| `_load_current_analysis_identity` | 存在せず | clean tree、HEAD、`ANALYSIS_REL` の committed blob 一致のみ受理 |
| `_preregistration_spec_from_historical_lock` | 存在せず | exact key 集合、v4 schema、固定 spec digest を満たす lock 内 spec のみ受理 |
| `_legacy_*_binding` | 使用しない live `Preregistration` 引数を受けた | 引数なし。系列別 literal は不変 |
| `_assert_report_lock_binding` | 通常 decoder の v1/current grammarと binding 一致 | pre-T733 exact-24 v2、24 blob 実照合、系列別 binding、固定 identity、v4 spec、calibration、campaign literal を受理し `HistoricalSeriesIdentity` を返す |
| 3 個の `_validate_legacy_*_records` | 固定 record digest＋live spec の順序／cell | 固定 record digest は不変、順序／cell は対応する lock 内 spec |
| `_historical_report_identity` | 存在せず | exact 3 系列と共通 spec/calibration/measurement identity のみ受理 |
| `_require_report_prereg_commit` | 存在せず | 3 系列共通の歴史 commit `77b33e37…` のみ受理 |
| `_collect_report_inputs` | live prereg/calibration を入力 | 各 lock を先に検証し、3 系列 identity、共通 spec/calibration、135 records を返す |
| `_verification_completeness` | `Preregistration` | 本体不変で引数型だけ `HistoricalReportIdentity` |
| `_write_reports` | live binding、現行 formula、applied tree を v2 に記録 | locked measurement identity と current analyzer を分離した provenance v3 |
| `run_formal(report)` | live prereg/calibration、patch checkout/applied-tree 後に report | patch より前で分岐し、locked inputs だけで report writer へ到達 |

## R1〜R7・N1〜N3

- R1: 歴史 decoder、exact-24 grammar、24 committed blob、固定 identity、系列 binding/spec、campaign literal を検査。
- R2: 3 lock の calibration を exact key 集合から復元し、相互一致後に residual と writer へ渡す。
- R3: report 分岐を patch read／checkout／applied-tree より前へ移動。
- R4: provenance を v3 に上げ、`measurement_identity` と `report_analyzer` を分離。Markdown も分離表示。
- R5: `run_formal(phase="report")` の到達テストを追加し、live prereg/calibration/patch 系を fail stub 化。
- R6: 現物 3 lock の raw snapshot と raw SHA 検査を追加。外部 record／receipt／WAL は保証しない旨も明記。
- R7: report CLI 値と submission receipt を歴史 prereg commit に束縛。
- N1: path の系列間比較は追加せず、各系列の `PREREG_REL` 比較だけ。spec 相互比較は診断用と明記。
- N2: `analysis_code_sha256` drift と系列 binding 交換を個別にテスト。
- N3: current analyzer 検査を共有 helper 化。報告上も B2 は「lock gate を除いたデータフロー」、M6 は「D1771 が採用した authority」として扱っています。docs は禁止どおり未編集です。

135 record digest literal と3集合比較は不変で、集合全体の meta digest `97b0726e…4b00` を追加テストで固定しました。

## テスト結果

- `orchestrator/tests/test_b10_backoff_shape_sweep.py::*`
  - 全走: `187 collected / 184 passed / 3 failed`
  - 今回追加・変更した report 範囲を含む184件は通過。
- report selector:
  - `report_lock or report_identity or report_commit or run_formal_report or report_collector or report_discloses or legacy_record_digest_literals`
  - `22 passed / 165 deselected`
- `orchestrator/tests/test_ccbench_spawn_sites.py::*`
  - `44 passed`
- `py_compile` 対象3ファイル、`git diff --check`: 成功。
- 現物への `--phase report`: 禁止どおり未実走。

## 期待赤 finding 集合

全走の3件は次の事前指定集合だけです。

- `test_t1905_m2_job_root_passes_real_external_and_claim_capability_gates`
  - `/var/tmp` が read-only。
- `test_t1905_a5_non_forbidden_external_official_root_is_accepted`
  - `/var/tmp` が read-only。
- `test_t1905_a5_tmp_official_root_is_rejected_by_real_durable_policy`
  - sandbox の `/tmp/.git` により `/tmp` が repository 配下と判定される。

今回の report identity 差分による失敗ではありません。所有外領域なのでテスト変更はしていません。

## 静的波及

grep で確認した所有外 caller／consumer:

- `test_ccbench_spawn_sites.py`: subprocess 数は不変。前方追加でずれた `build_v2:3644` と `run_campaign:4460` の構造 pin だけ追随し、44件通過。
- `test_official_perf_closure.py`: module membership のみ。変更不要・未実走。
- `test_condition_meaning_gate.py`: `EXPECTED_HOLE_LINE` のみ参照。値は不変・未実走。
- `test_campaign.py`: `campaign.loop.run_campaign` 1箇所を pin。実箇所数は不変・未実走。
- `test_p3_build_authority_cli.py`、`materializer_admission.py`: `_compile_probe_harnesses` 登録のみ。不変・未実走。
- 新しい private identity／collector／writer API の所有外 caller は0件。
- 通常 `campaign_lock.py`、CLI syntax、job argv、docs、共有既存 fixture は未変更。

`_verification_source_disclosure` 本体と collector 内の呼出しは無変更です。`_verification_completeness` は型注釈1行だけ変更しました。

## 変異7点の見立て

| 変異 | 検出 | 「そのtestだけ」か |
|---|---|---|
| M1 通常 decoder へ戻す | exact-pre-T733 raw snapshot 正例 | いいえ。3 workload parameter と、それを使う collector／orchestration 正例も同じ入口で赤 |
| M2 24 blob 照合削除 | false-authority 負例 | はい。他 gate は authority commit/blob を見ない |
| M3 module literal 比較削除 | analysis-code drift 負例 | 厳密には series-exchange 負例も同じ dict 比較に依存するため2件赤 |
| M4 write-heavy に balanced literal | series-binding-exchange 負例 | raw write-heavy 正例と下流正例も binding mismatch で赤になる |
| M5 live calibration に戻す | `run_formal(report)` fail-stub 正例 | はい。この変異では同 orchestration node だけが `load_calibration` を呼んで赤 |
| M6 live prereg を再導入 | 同 orchestration fail-stub 正例 | はい。この変異では同 node だけが `load_preregistration` を呼んで赤 |
| M7 spec digest gate 削除 | locked-spec-drift 負例 | はい。binding literal は spec 本体を見ず、別の先行 gateもない |

親が単一赤を厳密要件にする場合、M1・M3・M4はテスト依存の重なりを考慮する必要があります。

## 総括

実装自体は閉じていますが、sandbox 全走は上記3件の環境 finding により完全 green ではありません。残した問題はその3件と、禁止された現物 report の未実走だけです。

親が段6で必ず見るべき点は、provenance v3 の measurement/analyzer 分離、M1・M3・M4の赤テスト重複、3 lock fixture の raw byte一致、並行 wave 保護領域が無変更であることです。差分は working tree に残しており、commit は作成していません。