静的レビューの結果、must-fix は 1 件です。pytest、収集 meta-test、duration 台帳検査は環境指示どおり実走していません。指定ファイル全体の AST parse、差分照合、制御フロー追跡のみ実施しました。

### 所見 1 — 複合故障時の retryable 分類が回帰する

- 所見: 非帰属枝から runner 検査を移したことで、単独故障の分類は維持されていますが、複数の異常が同時にある場合の優先順位が変わっています。これは裁定の「既存分類を保つ」に反します。
- 根拠: 旧実装では checker の Git process failure を retryable と判定した後に main runner を取得していました。差分上も checker failure が先、main runner lookup が後です（`s6/impl.diff:565-570`）。現実装では main/tip runner の取得と不一致拒否が checker lookup より先です（`tools/dev_wave_land.py:1065-1088`, `tools/dev_wave_land.py:1093-1108`）。裁定は既存分類の維持を要求しています（`s6/s4-adjudication.md:94-100`）。
- 影響: 静的推論上、例えば non-attributable-only で「runner divergence」と「checker lookup rc=128」が同時に起きた場合、旧実装は `retryable_same_request=True`、新実装は runner divergence を先に検出して `False` になります。通常の quiescent land では `release_safe` も `False` から `True` へ反転し、lease の保持・解放が変わります（`tools/dev_wave_land.py:5034-5042`, `tools/dev_wave_land.py:5527-5539`, `tools/dev_wave_land.py:5622-5625`）。
- must-fix か nit か: **must-fix**。
- 成果物への具体的影響: 直さない場合、同じ複合故障に対する land JSON report の `retryable_same_request` と `release_safe` がそれぞれ `true/false` から `false/true` へ変わり、受入 lease の参照状態も retained から released へ変わります。
- 推奨対応: waiter と tip runner の従来検査、非帰属 checker の process failure 判定、共通 main/tip runner 検査の順になるよう分割してください。runner divergence と checker rc=128 を同時注入する回帰テストも追加してください。

### 所見 2 — 既存の受理経路は、意図された縮小を除き維持される

- 所見: 以下の各経路は main/tip runner が同一 blob なら新しい共通検査を通ります。divergent child-green と divergent bootstrap/fold receipt の拒否は裁定どおりの意図的縮小です。
- 根拠:

| 経路 | 新しい結果と判定 |
|---|---|
| child-green | 同一 blob なら通る（`orchestrator/tests/test_dev_wave_land.py:1563-1588`）。異なる blob は全 verdict 共通で拒否され、裁定どおり（`s6/s4-adjudication.md:102-107`）。 |
| non-attributable-only | 同一 runner と checker なら通る（`orchestrator/tests/test_dev_wave_land.py:1451-1469`）。runner divergence は旧実装でも拒否対象だったため、単独故障の受理集合は不変（`tools/dev_wave_land.py:1089-1129`）。 |
| already-landed | receipt 検証は already-landed 分岐より前に実行される（`tools/dev_wave_land.py:5035-5042`, `tools/dev_wave_land.py:5392-5418`）。同一 runner の既存 receipt は通る。旧 divergent child-green receipt は新たに落ちるが意図的縮小。 |
| forward-main merge | 検査対象は `tested_main`/`tested_tip` のままで、`landing_tip` ではない（`tools/dev_wave_land.py:4909-4922`, `tools/dev_wave_land.py:5035-5042`）。既存の clean forward merge は通る（`orchestrator/tests/test_dev_wave_land.py:6728-6776`）。landing tip 側 runner が未検査なのは既知の scope 外（`s6/s4-adjudication.md:31`）。 |
| fold recovery | active plan 分岐より前に同じ receipt を検証する（`tools/dev_wave_land.py:5035-5055`）。同一 runner の shape A/B recovery は通る構造（`orchestrator/tests/test_dev_wave_land.py:5800-5834`, `orchestrator/tests/test_dev_wave_land.py:5965-6017`）。旧 divergent receipt は recovery 前に拒否されるが、未追跡 divergent receipt も拒否するという裁定に一致（`s6/s4-adjudication.md:65-77`）。 |
| bootstrap receipt | main に launcher が無い場合の tip bootstrap は維持される一方、runner には例外を設けず main/tip equality を要求する（`tools/dev_wave_land.py:1021-1045`, `tools/dev_wave_land.py:1065-1088`）。既存正例は main に runner があるため通る（`orchestrator/tests/test_dev_wave_land.py:1047-1059`）。 |

- 影響: 所見 1 の分類回帰を除き、既存の正しい receipt が落ちる経路は静的には見つかりませんでした。
- must-fix か nit か: nit（修正要求なし）。
- 推奨対応: 親の全走で already-landed、forward-main、fold recovery、bootstrap 正例を実測してください。

### 所見 3 — 非帰属枝の型・初期化・`None` 処理は安全

- 所見: 共通部への移動による未初期化参照や `None` 到達はありません。
- 根拠: `tip_runner_entry` と `main_runner_entry` は直後の guard で双方の `None` を排除してから添字参照されています（`tools/dev_wave_land.py:1065-1086`）。checker 用の 4 変数は分岐前に初期化され（`tools/dev_wave_land.py:1089-1092`）、non-attributable-only のときだけ値を設定し、最終条件でも verdict の短絡評価と `None` 検査を経ています（`tools/dev_wave_land.py:1093-1127`）。
- 影響: 型の絞り込みや変数寿命による例外はありません。問題は値の安全性ではなく所見 1 の検査順だけです。
- must-fix か nit か: nit（修正要求なし）。
- 推奨対応: 所見 1 の順序修正時にも、この guard と checker の明示的な初期化を維持してください。

### 所見 4 — launcher の後始末は維持されるが、メモリと診断に小さな波及がある

- 所見: blob 読取は main、tip、main の 3 回となり、suite 成功時の protocol と排他生成は維持されています。一方、blob 3 個分の参照が同時に残る時間帯と、早期失敗が waiter 上で `acceptance-command` と分類される点は nit です。
- 根拠: 3 回の読取は `tools/acceptance_launcher.py:436-446`。`tip_source` は比較後も解放されず、3 回目取得時には `source`、`tip_source`、`main_source` の参照が残ります。`open("xb")` と signal handler 復元は不変です（`tools/acceptance_launcher.py:199-233`）。outcome、completion、receipt の成功順も不変です（`tools/acceptance_launcher.py:450-475`）。
- 影響: 所要は Git process 1 回分、最大保持量は概ね runner blob 1 個分増えます。実時間と実メモリは未計測です。main/tip 不一致は log、outcome、completion、receipt の前に rc=70 で終了します（`tools/acceptance_launcher.py:436-439`, `tools/acceptance_launcher.py:540-546`）。waiter は outcome の EOF を framing error とし、`acceptance-command`、全体 rc=70、retry なしとして扱います（`tools/dev_wave_wait.py:485-489`, `tools/dev_wave_wait.py:3773-3782`, `tools/dev_wave_wait.py:4019-4028`）。session は abort、未公開 receipt temp は削除されます（`tools/dev_wave_wait.py:4003-4013`）。取得成功後の第三読取失敗で log が残る点は、旧 M3 後読取失敗と同じです。
- must-fix か nit か: nit。
- 推奨対応: equality 確認後に `del tip_source` して peak memory を戻すことを推奨します。また early rc=70 の stage、source_rc、temp/log 残存を固定する waiter 統合テストがあると診断契約が明確になります。

### 所見 5 — 共有 fixture の全 consumer は分類でき、既定 tip digest は不変

- 所見: `_Repo._acceptance_receipt` の直接 caller は `_Repo.request` だけです。指定 test file 全体の AST 走査では `request` は 185 call、175 owner function にあり、その内訳は top-level test 167、helper 8 でした。
- 根拠: 185 call は次で全件分類できます。

  - 176 call: 新引数を指定しない synthetic receipt。`runner_digest_revision or tested_tip` により従来どおり tip digest（`orchestrator/tests/test_dev_wave_land.py:243-271`, `orchestrator/tests/test_dev_wave_land.py:354-357`）。
  - 6 call: 明示指定。対象は `test_land_rejects_child_green_runner_blob_divergence`、`test_land_accepts_child_green_matching_main_and_tip_runner_blobs`、`test_land_rejects_non_attributable_runner_blob_divergence`、両 runner-path-absence test、`test_land_runner_gate_uses_tested_main_after_main_reaches_tip`（同 file `:1523-1779`）。
  - 2 call: real waiter receipt を直接渡す E2E（同 file `:1944-2029`, `:2032-2129`）。
  - 1 call: `make_acceptance_receipt=False`。
  - helper 8 件は `_assert_standard_v5_positive_control`、`_assert_tip_launcher_positive_control`、`_assert_bootstrap_positive_control`、`_assert_non_authoritative_provenance_rc_retains`、`_call_rollback_fold`、`_fold_main_locked_with_failed_ref_rollback`、`_forward_merge_request`、`_land_main_fold_for_resync`。

- 影響: fixture の既定値によって挙動が変わる既存 test はありません。divergence 系だけが明示的に旧 launcher 相当の tip digest を選んでいます。
- must-fix か nit か: nit（修正要求なし）。
- 推奨対応: 現在の既定値を維持してください。

### 所見 6 — 名前と静的重複は正常、duration 台帳だけ未検証

- 所見: 追加・改名 test に名前衝突や同一 test body の重複はありません。duration 台帳適合だけは確認不能です。
- 根拠: 全体 AST parse は成功し、top-level test は launcher 側 13、land 側 214。各 file 内の重複名、両 file 間の同名、正規化した test body 重複はいずれも 0 件でした。新規 test は引数なしで、双方の独自 `_run()` の `test_` callable 規約にも合います（`orchestrator/tests/test_acceptance_launcher.py:437-454`, `orchestrator/tests/test_dev_wave_land.py:9649-9673`）。差分上の追加・改名 nodeid は author.md 記載どおり 8 件です（`s6/author.md:32-44`）。
- 影響: pytest の名前収集面に静的な違反はありません。ただし author 自身が 8 nodeid の duration 台帳未登録と meta-test 未実走を報告しています（`s6/author.md:45-62`）。台帳本体は射影対象外のため、90% gate を満たすとは確認していません。
- must-fix か nit か: nit。
- 推奨対応: 親で収集、duration coverage、重複検査の meta-test を実走し、閾値を割る場合は台帳を同時更新してください。

### 所見 7 — author.md の自己申告は 5 項目一致、retryable のみ不一致

- 所見: schema、field 数、canonical JSON、`_run_blob`、fixture 既定値は一致しました。retryable 分類の包括的な維持という申告だけは所見 1 の複合故障で成立しません。
- 根拠:

  - schema v5: launcher、land、wait の全てで維持（`tools/acceptance_launcher.py:22`, `tools/dev_wave_land.py:94`, `tools/dev_wave_wait.py:233`）。
  - root field: launcher の receipt literal と land の field set は双方 27 件（`tools/acceptance_launcher.py:365-397`, `tools/dev_wave_land.py:102-130`）。
  - canonical JSON: `_canonical_json_bytes` と `_receipt_bytes` は HEAD 版と AST 同一（`tools/acceptance_launcher.py:89-101`, `tools/acceptance_launcher.py:347-398`）。
  - `_run_blob`: HEAD 版と AST 同一で interpreter も素の `python3`（`tools/acceptance_launcher.py:199-233`）。
  - retryable: helper 自体は HEAD と同一（`tools/dev_wave_land.py:742-747`, `tools/dev_wave_land.py:821-835`, `tools/dev_wave_land.py:898-905`）だが、呼出順は所見 1 のとおり変化。
  - fixture 既定 tip digest: 維持（`orchestrator/tests/test_dev_wave_land.py:354-357`）。

- 影響: author.md の「retryable 分類は維持した」という記述は単独故障に限定すれば正しいものの、全入力については過大です。
- must-fix か nit か: nit。コード上の修正要求は所見 1 の must-fix に集約します。
- 推奨対応: 修正後、author 報告も「複合故障時を含め既存優先順位を維持」と検証可能な表現へ更新してください。

## 総括

- must-fix は 1 件: 非帰属枝の複合故障で retryable と release-safe の優先順位が変わる。
- 直さない場合、land JSON report と acceptance lease の保持・解放結果が旧実装から反転し得る。
- child-green、non-attributable、already-landed、forward-main、fold recovery、bootstrap の単独正常系は静的には維持される。
- divergent child-green と divergent bootstrap/fold receipt の拒否は裁定どおりの意図的縮小。
- launcher の protocol、`open("xb")`、receipt temp cleanup に破れはないが、peak memory と早期 rc=70 の診断は nit。
- fixture の既定 tip digest は不変で、全 185 call を分類済み。
- test 名と静的重複は正常。duration 台帳と pytest は未実走であり、親の検査が必要。