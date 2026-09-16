# 段 6 敵対レビュー B (整合と実効性) — [T-1328]

静的レビューのみ。編集・テスト実行はしていない。両ツリーの HEAD は `9d52ef145`、比較基底の tracked 差分はなく、実装側の差分は指定の7件だった。`git diff --check` は出力なし。

以下の repo 内パスは実装ツリー起点。`author.md` は指定された段5報告を指す。

## must-fix (real 所見)

### 1. 既存4テストの移行が残る。うち2件は不足変数の補完だけでは直らない

**file:line:** `orchestrator/tests/test_pegasus_tools.py:397,423,439,461,1442`、`author.md:57-60`

**根拠:** 報告が挙げた最初の失敗原因はコードと整合する。しかし候補全滅・unsupported smoke の2件は、`CALIBRATE_PYTHON` を補っても、旧契約の `rc=2 / failure.stage=perf` を要求し続ける。さらに fixture の `REPO_ROOT` は `runner.py` の定数だけを置いた仮ツリーで、canonical probe を提供せず、literal perf の PATH も隔離していない。

**成果物への影響:** 新契約に正常適合した実装を既存テストが拒否し、fixture の import 失敗やホスト依存を製品不具合と混同する。

**推奨是正:** 親の統合修正として、下節の4件を新契約へ移行する。期待値の削除だけで閉じない。報告も「変数不足」は直接原因であり、2件には契約更新と fixture 補強が必要だと補足する。

### 2. 「既存テスト期待値の変更なし」は差分と矛盾する

**file:line:** `author.md:15`、`orchestrator/tests/test_official_perf_closure.py:44,451`

**根拠:** 既存 inventory に CLI・sweep を追加し、runner guard の期待値を `("not use_perf",)` から `("not use_perf", "use_perf")` に変更している。これは裁定どおりの正当な変更だが、報告の無限定な否定とは両立しない。

**成果物への影響:** レビュー記録が、どの既存検査を更新したかを誤って伝える。

**推奨是正:** 「裁定で指定された閉包・guard の期待値のみ更新。その他の既存期待値は変更なし」と訂正する。

## refuted (攻めたが成立しなかったもの)

- **認証 predicate・登録条件・rc を緩めた疑いは不成立。**  
  `report.py:106-123` の必須 counter・飽和・noise 判定は不変。`cli.py:1036-1057` は rejected を保存して rc=1、登録は `1059` 以降。wrapper も `certify_calibration.sh:977-1010` で rc を保存・伝播する。変更禁止7ファイルにも差分はない。  
  **成果物への影響:** no-perf は throughput を残せるが、accepted／registered にはならない。

- **shell テストが分岐を再実装している疑いは不成立。**  
  `test_pegasus_calibration_workload.py:682-697` は production の perf 選択開始から `calibrate_rc=0` 直前までをそのまま実行する。テスト側が作るのは入力・実行環境・perf fixture・期待 argv である。`699-738` の assertion も receipt、argv、selection、probe 回数までで、実 calibrator 起動や job 終端を主張していない。  
  **成果物への影響:** argv 生成の証拠として有効。`exec_calibrate.py → os.execv` と終端の実行証拠にはならず、報告もその限界を明記している。

- **Python 正負例が `_fake_calibrate` へ逃げている疑いは不成立。**  
  `test_calibrator_certify.py:1689-1705,1760-1765` は実 `sweep.calibrate` またはそれに委譲する観測 wrapper を指定する。`sweep.py:239-243` → `runner.py:1181-1182` で実 `measure_point → run_once` を通す。fixture は subprocess と環境・clock 等の外部観測に置かれている。  
  `test_calibrator_certify.py:401-408` の拡張は `bench_runner` 明示時だけ有効で、既存 nm／sha256sum と未指定時の挙動は維持される。  
  **成果物への影響:** 新規正例は3点×2 rep の伝播・保存を、負例は第2 rep の fatal 理由と停止位置を検証する。既存108件の実走結果そのものは本レビューでは追認しない。

- **閉包更新の不足によって指定 meta-test が必然的に赤になる疑いは不成立。**  
  `test_official_perf_closure.py:501-523,910-917` の検出条件に対し、CLI・sweep のファイル追加と runner guard 更新は対応している。新しい一般化検査は追加していない。  
  `test_env_contract.py:51-53,1250-1263` の禁止 literal は新規コードに増えていない。`test_plain_runner_coverage.py:60-74` に関わる新規ファイル・harness 変更もない。`test_hooks.py:3038,3139` と `admission_registry.json:34-38` の dispatch 分類は維持される。所要台帳は `test_acceptance_schedule_order.py:704-715` の全体90%条件であり、追加 node の存在だけでは赤にならない。  
  **成果物への影響:** 指定面に追加の確定的破損は見つからない。ただし全 suite 緑や台帳被覆率を静的検査から保証するものではない。

**D494 先例との非対称も、次のとおり不具合とは判定しない。**

| 差異と根拠 | 判定・成果物への影響 |
|---|---|
| 先例逐語 `:9-14` は `stat -x, -- true`。今回 `certify_calibration.sh:889-898` は version と従来の `sleep 0.1` smoke | 既存候補選択の維持として正当。最終可用性は別途 canonical probe が決める。 |
| 先例 `:25-29` は PATH を export。今回 `:907-932` は Python directory を含む `CALIBRATE_PATH` を probe と測定に渡す | 正当。選択後の同じ PATH を双方に使う。 |
| 先例 `:40-42` は判定後に保存。今回 `:942-945` は保存後に判定 | 正当。今回なら `probe_error` receipt も保存され、abort は維持される。 |
| 先例 `:46` の shell による0/1検査が今回にはない | 現行の出力元は `int(use_perf_from_receipt(...))` と例外終了であり、具体的な不正出力経路は見つからない。追加 gate は要求しない。 |
| 先例 `:24` は deadline を再確認。今回 `:850-855` は候補選択前に remaining を計算 | 既存 wrapper の構造差。追加 probe 分も経過時間を消費するが、今回新設された無制限処理ではない。 |
| 今回 `:965-966` は unavailable 時だけ receipt 引数を渡す | 裁定どおり。perf 有り argv を維持し、no-perf の証拠だけを CLI に伝える。 |

## 所有外の赤 4 件の正しい直し方

### 1. `test_certify_perf_stage_is_policy_driven_fail_closed_and_precedes_calibrate`

**file:line:** `orchestrator/tests/test_pegasus_tools.py:381-401`

候補全滅の `write_failure` 要求を、**最終 PATH 確定 → canonical probe → receipt 判定 → argv 生成**の順序検査へ置換する。候補成功時だけ selection／symlink を生成し、`probe_error` は rc=2、unavailable は継続する契約を pin する。既存の policy・event・unsupported 検査は残す。

**成果物への影響:** 候補全滅停止の復活と、probe error の誤った継続を区別して検出できる。

### 2. `test_perf_stage_all_candidates_failed_writes_perf_failure`

**file:line:** `orchestrator/tests/test_pegasus_tools.py:411-441`

`CALIBRATE_PYTHON` を設定し、`REPO_ROOT` を実 repo に向ける。Python directory も含めて PATH を隔離し、literal perf を unavailable fixture にする。期待値は断片 rc=0、receipt unavailable、selection／symlink 不在、failure 不在へ変更する。argv まで抽出するなら receipt 引数の付加も確認する。literal available の対照では引数不在を確認する。

**成果物への影響:** 「候補全滅」と「perf unavailable」を同一視せず、D494 の増分を固定できる。

### 3. `test_perf_stage_rejects_not_supported_smoke_output`

**file:line:** `orchestrator/tests/test_pegasus_tools.py:444-464`

上記 fixture 修正に加え、`<not supported>` の保存と、その候補が選ばれない assertion は残す。その後の結果は literal perf の canonical probe に委ねる。literal unavailable なら断片 rc=0／no-perf、literal available なら perf 有り継続を期待する。unsupported smoke だけを理由とする `failure.stage=perf` は要求しない。

**成果物への影響:** unsupported 候補の除外を守りつつ、測定継続を誤って拒否しなくなる。

### 4. `test_calibrate_failure_survives_err_trap_and_writes_job_result`

**file:line:** `orchestrator/tests/test_pegasus_tools.py:1424-1460`

既存 rc=7 ケースには `USE_PERF=1` を明示し、既存の rc・job identity assertion を維持する。no-perf 対照として `USE_PERF=0`、`PERF_PREFLIGHT_RECEIPT`、stub rc=1 を与え、receipt 引数、最終 rc=1、`job-result.calibrate_rc=1`、`failure.stage=calibrate` を確認する。

**成果物への影響:** 失敗 rc が ERR trap に潰されない契約を、今回増える no-perf 終端にも固定できる。stub 検証であり実 `os.execv` の証明とは呼ばない。

## consumer の取り残し

**production consumer の新形式未対応は、調査範囲ではなし。テスト consumer の取り残しは上記4件。**

なお、指定の `orchestrator/env_contract.py` は存在せず、実体の `orchestrator/campaign/env_contract.py` を確認した。

| consumer／参照経路 | 根拠・成果物への影響 |
|---|---|
| `calibrator/cli.py:755-774` → `calibrator/schema_v2.py:632-650,797-798` | 新しい top-level field は追加していない。counter／saturation の null、既存 host map の `perf`、notes 追記で表現し、noise 未測定も既存の空配列形式へ変換する。rejected JSON を読める。 |
| `calibrator/schema_v2.py:529-531` | accepted に saturation と非空測定を要求する。no-perf 成果物の誤昇格を許さない。 |
| `campaign/certified_writer_admission.py:167-175` → `campaign/env_attestation.py:1028-1041` → `campaign/calibration_verify.py:116-141` | 2段先まで確認。新しい perf receipt を直接解釈する経路ではなく、契約が参照する既存較正を検証する。 |
| `campaign/env_contract.py:606-631` → `campaign/calibration_verify.py:116-141` → `calibrator/schema_v2.py:791-810` | registered path と accepted 要求を維持。no-perf rejected の利用不可は意図された境界で、形式未対応ではない。 |
| `tools/pegasus/collect_receipt.py:118-141,171-178` → 同 `:76-90` | rc は整数なら扱え、両 staging を再帰 manifest 化する。rc=1 と追加 receipt を回収対象に含められる。 |
| `tools/pegasus/submit_certify.sh:159-193,205-229` | submission identity・予約・qsub を扱い、後から作られる perf receipt の consumer ではない。変更不要。 |

## 裁定パッケージ候補 (scope 外だが real)

**perf なしの測定証拠を、正式較正として何に使えるようにするか。**

**file:line:** `calibrator/analyze.py:48-57`、`calibrator/report.py:106-123`、`campaign/env_contract.py:606-631`

現契約では全 sweep を終えても認定較正取得は回復しない。正式利用には別の保証内容と裁定が必要で、本 wave の must-fix には含めない。

費用はコードから確定できる。`cli.py:146-150` と `sweep.py:135` の既定値では **100万・200万・400万・800万・1600万 records の5点×3 rep＝15 subprocess**。`analyze.py:48-57` が全点の miss rate 欠損で選択不能を返すため、`sweep.py:121-130` の早期飽和終了は成立しない。正常完走なら15回すべて走り、`sweep.py:272-275` で noise 前に戻る。fatal・隔離違反等では途中停止する。

**成果物への影響:** build 等に加えて15回の初期化・測定を消費し、残るのは却下証拠。`extime=3` の指定合計は45秒だが、実時間には初期化等が加わる。予約は `policies/calibration_v1.json:5-6` の7200秒のままで、実課金や実経過時間が2時間とは断定できない。段5報告にもこの具体的費用を追記すべきである。

## 総括

production の変更は、D352 に沿う測定継続・証拠保存という裁定範囲と整合する。  
認証条件の緩和、実経路を迂回する新規テスト、production consumer の形式破損は見つからない。  
統合前に既存4テストの契約移行と、報告の「期待値変更なし」の訂正が必要。  
正常 no-perf 走は5点×3 rep を消費して rejected・rc=1・未登録となる。  
本レビューは静的検査であり、実 job・テスト・変異の成功を認定しない。