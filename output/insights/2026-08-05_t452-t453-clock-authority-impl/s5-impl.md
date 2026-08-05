実装は B → A → C の順で完了しました。commit / git add は行っておらず、`output/`・registry・submodule も未変更です。Pegasus ログインノードのため pytest は実行していません。

## 受理・拒否挙動の対比

変更前:

- runtime 観測と expected calibration が同じ型で、観測側にも tolerance sentinel `100.0` が混入。
- tolerance は CLI / shell から任意に指定でき、schema は `100.0` も受理。
- loader・issuer・consumer は単一 policy との完全一致を要求しない。
- silo は median-to-median 比較のため、median が正常なら単一の大きな外れ値を受理。
- T126 `_attest` は型誤りにより常に fail-closed。

変更後:

- 新規観測は tolerance-free の `pegasus-probe-output/v2`。v1 は exact float `100.0` sentinel の strict legacy parser のみ受理。
- effective-clock policy は単一定数 `2.0`。CLI / shell 入力は拒否。
- expected schema は `0 < tolerance_pct < 100.0`。loader・issuer・consumer・self gate は policy との exact equality を要求。
- canonical 判定は expected median の ±2% 内に全観測標本がある場合だけ受理。silo live/raw も同じ述語を使用し、method / governor は別途 exact 比較。
- malformed JSON、duplicate key、typed failure は既存の failure class のまま fail-closed。
- T126 の受理集合は引き続き空。

Scope 上、expected artifact の `5.0` / `99.0` は履歴 parse 用に schema では受理しますが、current required loader では拒否します。既知の self-inconsistent calibration 1 件は削除せず、loader self-pass 要求も追加していません。

## phase B

- [schema_v2.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/calibrator/schema_v2.py): observed 専用 clock/profile 型を追加。
- [env_attestation.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/campaign/env_attestation.py): v1/v2 共通 duplicate-rejecting parser、strict v1 sentinel、source-schema-bound hash projection、expected/observed projector を実装。
- [run_probe.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/tools/pegasus/run_probe.py): import / success / probe / write の全分岐を v2 化し、failure payload を exact 化。
- [cli.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/calibrator/cli.py)・[execution_guard.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/campaign/execution_guard.py): observed 型へ全 call site を移行。
- [certify_calibration.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/tools/pegasus/certify_calibration.sh): pre-attestation を共有 v2 parser 経由に変更。
- 型・parser・corpus・producer・caller fixture は `test_env_attestation.py`、`test_calibrator_certify.py`、`test_execution_guard.py`、`test_pegasus_tools.py`、`test_s8b_floor_campaign.py`、`test_s8b_oracle_driver.py` に反映。
- `test_t126_qualification_driver.py` に裁定 R-2 の fail-closed 回帰テストを追加。

## phase A

- [effective_clock_policy.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/calibrator/effective_clock_policy.py): `Final[float] = 2.0` の単一 authority を新設。
- `cli.py` に policy 注入を実装し、旧 option と validation を削除。
- `schema_v2.py` の上限を `<100.0` に変更。
- [submit_certify.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/tools/pegasus/submit_certify.sh)・`certify_calibration.sh`: 旧 option/env/export を撤去し、legacy env は staging 前に拒否。
- 許可された [tools/pegasus/README.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/tools/pegasus/README.md) の CLI 契約を更新。
- `test_effective_clock_policy.py`、`test_schema_v2.py`、`test_calibrator_certify.py`、`test_pegasus_tools.py`、`test_env_contract.py` に authority・境界・hostile input 検査を追加。

## phase C

- `env_attestation.py`: loader / issuer の policy exact equality を実装。
- `execution_guard.py`: arbitrary-width private math と public admission predicate を分離し、receipt clock の expected/observed exact key を検証。
- `cli.py`: 取得時 self gate を canonical predicate に接続。
- [silo_ladder_rung1.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/campaign/silo_ladder_rung1.py): live/raw 両経路を共有 parser・loader・canonical predicate に接続。渡す map は明示的に `{samples_mhz,tolerance_pct}` / `{samples_mhz}` とし、parser 例外を既存 failure class へ変換。
- `test_calibrator_certify.py`: producer→loader→issuer→consumer→self gate の `2% fail / 3% pass` metamorphic test。
- `test_silo_ladder_rung1_driver.py`: 同じ +3% vector の live/raw metamorphic test、exact-key spy、malformed/duplicate/typed failure。
- `test_execution_guard.py`: 既存18 vectorsを移動・削除せず、`math_want` / `canonical_want` の二重 assertion 化。
- `test_env_attestation.py`・`test_env_contract.py`: equality edge、registry exact singleton、22論理/47物理 corpus を固定。
- `test_silo_ladder_rung1_evidence.py`: 歴史 evidence identity を pin し、旧 median 判定は true、current canonical 判定は false と固定。

## 検証結果

pytest nodeid は実行していません。ホストが `pegasus02` のため、親が `tools/run_tests.py` 経由で計算ノードへ dispatch する必要があります。

実行した軽量検査:

- `orchestrator/tests/test_plain_runner_coverage.py` 全3 node:
  - 初回 rc=1: `test_every_test_file_is_self_runnable_or_allowlisted` のみ失敗。新規 test file の harness 不足。
  - 修正後 rc=0: 3 passed。
- 全変更 Python ファイルの `python3 -m py_compile`: rc=0。
- `bash -n` (`certify_calibration.sh`, `submit_certify.sh`, `smoke_probe.sh`): rc=0。
- `git diff --check`: rc=0。
- `python3 tools/check_codex_agents.py`: rc=0。
- `python3 tools/check_docs.py`: rc=0。

残存する pytest の赤は未確認です。provenance 監査は commit 未作成かつログインノードのため未実行です。

## 波及可能性

親の全走で特に確認が必要です。

- loader caller: `campaign/loop.py`、`s8b_floor_campaign.py`、`s8b_oracle_driver.py`、`s8b_oracle_report.py`、`s8b_ratified_freeze.py`。
- observed 型 caller: floor/oracle の共有 fixture、execution receipt issuer、`smoke_probe.sh`、certification shell。
- 歴史 raw consumer: v1 corpus 22組と silo evidence。artifact bytes は変更していません。
- `test_schema_v2.py` の共有 `_valid_document()` は履歴 schema 正例として `5.0` を維持し、current required fixture のみ `2.0` に縮小。
- no-edit consumer regression:
  - `test_campaign.py`: loader/probe monkeypatch が observed 型契約に追随できるか。
  - `test_s8b_oracle_report.py`: real registry loader と receipt consumer。
  - `test_s8b_ratified_verify.py`: current calibration binding と verifier 再計算。
- current silo driver/runtime hash は歴史 evidence と意図的に不一致になるため、current eligibility は fail-closed になります。

## T126 R-2 確認

`t126_driver.py` は未編集です。`compare_profiles` の第1引数は引き続き `verified.calibration` で、後続 hash 呼出しも到達不能のままです。指定 docstring を持つ回帰テストを追加し、clean observed でも `QualificationDriverError` となる契約を固定しました。pytest 実測は親の計算ノード走行待ちです。

## 総括

- B→A→C の直列実装を完了。
- tolerance authority を単一 `2.0` に統合。
- probe v2、strict v1 parser、版束縛 hash projection を実装。
- loader / issuer / consumer / self / silo live/raw を fail-closed 化。
- T126 の常時 fail-closed は意図どおり保存。
- output・registry・submodule・許可外 docs は未変更。
- commit / add は未実行。
- 軽量静的検査は最終 rc=0。
- 残る最大の確認点は、計算ノード上の変更テスト群と no-edit 3 consumer の全走です。