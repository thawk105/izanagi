結論は、独立 verifier を新規 leaf module と薄い entry に分離し、既存 calibrator 内の三重 gate は一切変更しない設計が適切です。判定 artifact には較正の生 bytes を canonical Base64 で内包し、receipt 単体から全判定を再計算できるようにします。

現状の重要点は次のとおりです。

- canonical 判定は [execution_guard.py:183](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-iii/orchestrator/campaign/execution_guard.py:183) で `input_valid && policy_matches && band_pass` を既に連言している。
- [schema_v2.py:740](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-iii/orchestrator/calibrator/schema_v2.py:740) は raw bytes を受け、duplicate key を含む exact schema を検査できる。
- 現行 `_published_self_comparison_receipt` は [cli.py:482](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-iii/orchestrator/calibrator/cli.py:482) で同一 process 内再読を行うが、raw preimage、schema 検査、content-address 検査を receipt に持たない。
- job 892707 には final receipt がまだなく、旧 attempt/job-staging への verifier artifact の事後追加はできない。
- 94a4 の SHA-256 は `94a4b79f...c5a9`、753f は `753f535a...5a49`。両方とも schema v2・`quality.status=accepted` で、clock 判定だけがそれぞれ pass/fail になる。

## file:line 実装計画

| path・挿入位置 | 変更 |
|---|---|
| `orchestrator/calibrator/verify_published.py` 新規、予定 246 行 | L1-29: import・schema literal、L30-48: error/exact-key helper、L49-75: Base64 chunk codec、L76-104: `publish.json` を locator として解決、L105-177: `build_verification(raw, basename)`、L178-207: receipt-only replay、L208-222: create-only JSON writer、L223-246: CLI `main`。 |
| `orchestrator/verify_published_calibration.py` 新規、15 行 | `calibrate.py` と同じ `sys.path` wrapper。`verify_published.main` だけを import する。 |
| `output/env/pegasus/calibration/verifications/94a4b79fa31bba3c/independent-verification-v1.json` 新規 | 94a4 の別 process 実行結果。`accepted=true`。旧 attempt には書かない。 |
| `output/env/pegasus/calibration/verifications/753f535a8d024727/independent-verification-v1.json` 新規 | 753f の固定負例。CLI は artifact を書いて rc=1。 |
| [certify_calibration.sh:745](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-iii/tools/pegasus/certify_calibration.sh:745) 直後 | 13 行追加。`calibrate_rc==0` の場合だけ別 `python3` process で verifier を起動し、wrapper の `job-staging/$PBS_JOBID/independent-verification-v1.json` へ書く。stdout/stderr も同 staging に残す。 |
| 同 [L747](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-iii/tools/pegasus/certify_calibration.sh:747) | post probe 条件を `calibrate_rc==0 && independent_verification_rc==0` に1行置換。 |
| 同 [L752-765](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-iii/tools/pegasus/certify_calibration.sh:752) | 14 行を20行へ置換。job result を `pegasus-job-result/v2` とし、既存 key に `independent_verification_rc: int|null` と `overall_rc: int` を追加。`calibrate_rc` は上書きしない。 |
| 同 [L770](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-iii/tools/pegasus/certify_calibration.sh:770) 直後 | 4 行追加。verifier 非0なら `write_failure <rc> independent-published-verification ...` 後、その rc で exit。削除処理は置かない。 |
| `orchestrator/tests/test_verify_published_calibration.py` 新規、予定約300行 | 下記の固定 vector、replay、schema/content-address、CLI process、Python 3.9 import surface を検査。 |
| [test_pegasus_tools.py:915](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-iii/orchestrator/tests/test_pegasus_tools.py:915) 直後 | 約24行追加。collector の staging manifest が verifier artifact の path/size/hash を束縛することを検査。 |
| [test_pegasus_tools.py:1130](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-iii/orchestrator/tests/test_pegasus_tools.py:1130) 直後 | 約72行追加。shell 順序と verifier reject 時の rc・published artifact 保持を実 entry で検査。 |
| [output/README.md:15](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-iii/output/README.md:15) | 1 行を3行へ置換し、`registered/`、`verifications/`、job staging の役割を区別。verification は登録・活性化 authority でないと明記。 |

以下は変更量ゼロとします。

- [cli.py:406](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-iii/orchestrator/calibrator/cli.py:406)、[cli.py:482](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-iii/orchestrator/calibrator/cli.py:482)、[cli.py:643](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-iii/orchestrator/calibrator/cli.py:643)
- [effective_clock_policy.py:6](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-iii/orchestrator/calibrator/effective_clock_policy.py:6)
- [schema_v2.py:740](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-iii/orchestrator/calibrator/schema_v2.py:740)
- [execution_guard.py:183](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-iii/orchestrator/campaign/execution_guard.py:183)
- [collect_receipt.py:76](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-iii/tools/pegasus/collect_receipt.py:76)

新 module は `calibrator.cli` を import せず、schema leaf、policy leaf、D191 指定の canonical predicate だけを import します。Python 3.9 を考慮し、`X | None`、`match` 等の 3.10+ 構文は使いません。

## 判定 artifact schema

全 top-level key は exact とします。

```json
{
  "schema": "izanagi/independent-published-calibration-verification/v1",
  "subject": {},
  "policy_identity": {},
  "predicate_preimage": {},
  "checks": {},
  "accepted": true,
  "errors": []
}
```

各 key の完全な契約は次のとおりです。

- `schema`: 上記 literal の `str`。
- `subject`: exact object。

  - `basename`: published artifact の basename、`str`。
  - `encoding`: `"base64-rfc4648/chunks-76"`。
  - `bytes_base64_chunks`: exact raw bytes を RFC 4648 Base64 化した `list[str]`。各要素76文字、末尾のみ短くてよい。
  - `byte_count`: raw bytes 長、非負 `int`。
  - `sha256`: raw bytes の lowercase hex64 `str`。

- `policy_identity`: exact object。

  - `canonical_predicate`: `"campaign.execution_guard.effective_clock_comparison_passes"`。
  - `tolerance_authority`: `"calibrator.effective_clock_policy.EFFECTIVE_CLOCK_TOLERANCE_PCT"`。
  - `tolerance_pct`: verifier process が使用した有限 JSON number。現行は `2.0`。

- `predicate_preimage`: schema 成功時は exact object、失敗時は `null`。

  - `expected.samples_mhz`: raw artifact から schema validator 経由で得た有限 number の非空 list。
  - `expected.tolerance_pct`: raw artifact 内の有限 number。
  - `observed.samples_mhz`: expected と同じ全標本を複製した list。
  - `method`、`governor` は判定入力ではないためここへ混ぜない。raw bytes には保存されている。

- `checks`: exact object。

  - `content_address`: `{algorithm: "sha256", prefix_hex_chars: 16, expected_basename: str, passed: bool}`。
  - `calibration_schema_v2`: `{authority: "calibrator.schema_v2.validate_calibration_v2", passed: bool}`。
  - `quality_status_accepted`: `{actual: "accepted"|"rejected"|null, passed: bool|null}`。
  - `effective_clock_self_comparison`: `{authority: "campaign.execution_guard.effective_clock_comparison_passes", passed: bool|null}`。
  - `null` は上流 schema 不成立で未評価の場合だけに使う。

- `accepted`: `content_address.passed && calibration_schema_v2.passed && quality_status_accepted.passed && effective_clock_self_comparison.passed` の `bool`。
- `errors`: `list[object]`。各要素は exact `{stage: str, type: str}`。外部 raw 文字列を平文転記しないため、例外 message は保存しない。

SHA-256 の算出自体は生成時には必ず成功する自己成就値なので、受理条件には数えません。receipt replay 時に `subject.bytes_base64_chunks` から再計算し、記録済み `sha256`、`byte_count`、全 `checks`、`predicate_preimage`、`accepted` と exact 比較します。

同様に policy equality は canonical predicate 内の `policy_matches` が既に担います。別実装の第5 gateにはしません。

第三者の再計算手順は以下です。

1. Base64 chunks を連結・decodeし、再encodeが同一 chunks になることを確認。
2. raw bytes の長さ・SHA-256・期待 basename を再計算。
3. raw bytes を直接 `validate_calibration_v2` に渡す。
4. typed profile から expected/observed を再導出。
5. `effective_clock_comparison_passes` を呼ぶ。
6. receipt 全体を再生成し、入力 artifact と exact 比較する。

raw bytes を持つため、schema 検査・content hash・clock 入力のいずれも外部ファイルを再読しません。receipt 自身の hash は receipt 内へ書きません。

## shell 結線と rc

順序は次の形に固定します。

```text
calibrator process
  └─ publish + 現行 in-process self-comparison
       └─ rc=0
            └─ 独立 verifier process
                 ├─ accepted → rc=0 → post probe → job success
                 ├─ rejected → receipt 作成後 rc=1 → job failure
                 └─ locator/read/write/timeout → rc=2/124等 → job failure
```

- `publish.json` は対象を選ぶ locator としてのみ使う。判定関数への入力は `basename + published raw bytes` だけ。
- `publish.json.target` は exact key と `calibration-[0-9a-f]{16}.json` を検査してから registered root と結合する。
- verifier reject でも JSON artifact を先に create-only で書き、次に rc=1 を返す。
- CLI usage、unsafe target、読取不能、output collision は rc=2。timeout の rcは wrapper がそのまま保持する。
- `calibrate_rc` は verifier 失敗時も0のまま記録し、`independent_verification_rc` と `overall_rc` で層を分ける。
- published registered fileへ `unlink`、`rm`、rename-backを行わない。
- 892707 の既存 `attempts/` と `job-staging/` は変更しない。固定 vector の独立判定は新しい中央 `verifications/` namespaceへ記録する。
- future job の verifier artifact は実行中の wrapper job-staging に書かれるため、[collect_receipt.py:171](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-iii/tools/pegasus/collect_receipt.py:171) の既存 manifest に自動収録される。

892707 には final receipt が存在しないため、「現在の94a4判定が final receipt に束縛済み」とは名乗れません。

## 既存テストへの影響

- [test_calibrator_certify.py:909](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-iii/orchestrator/tests/test_calibrator_certify.py:909) 以降の現行 in-process receipt exact testは変更しない。P6 の削除防壁として残る。
- [test_env_contract.py:840](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-iii/orchestrator/tests/test_env_contract.py:840) の `KNOWN_SELF_INCONSISTENT_CALIBRATIONS`、registry 2件、旧753f pinは一切変更しない。
- [test_env_attestation.py:979](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-iii/orchestrator/tests/test_env_attestation.py:979) は `output/env/pegasus` 全体を rglob するが、検出対象は平文の probe-v1 markerを含む `.json/.stdout` だけ。raw bytes を Base64 にするため新 verification JSON は集合へ入らない。
- `_V1_CORPUS_DOCS` は `attempts/*/calibration.md` だけを globする。中央 `verifications/*.json` は対象外で、3件の `calibration.md` と union count 48は更新しない。
- この wave では新しい certification job を走らせない。走らせると新 `calibration.md` が増え、exact集合を動かしてしまう。
- `collect_receipt.py` 自体は変更しないが、generic manifest が新ファイルを落とさない回帰テストを追加する。
- `check_docs.py` は git の untracked/deletion gateではない。`output/README.md` の整合確認として実行対象にはする。
- `run_tests.py` の受入 preflight は [run_tests.py:484](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-iii/tools/run_tests.py:484) の未stage tracked削除検査であり、untracked新規ファイルは検出しない。新 module、tests、中央 receipts は mutation harness・受入前に全て stage する必要がある。
- 削除予定は0件。`git status --porcelain=v1 --untracked-files=all` でも新規漏れを別途確認する。

## 新規テスト nodeid

- `orchestrator/tests/test_verify_published_calibration.py::test_registered_94a4_vector_accepts_and_replays_from_receipt_only`  
  94a4を rejectする、raw preimageを欠く、中央 artifact が再生成結果と違うと赤。

- `...::test_registered_753f_vector_rejects_only_clock_gate_and_replays`  
  753fを acceptする、schema/content/qualityまで誤ってfalseにする、clock gateを通らないと赤。

- `...::test_wrong_content_address_rejects_even_when_other_gates_pass`  
  basename比較を削る、digestでなく入力 basename から期待値を作ると赤。

- `...::test_schema_invalid_bytes_skip_canonical_predicate_and_reject`  
  strict validatorを `json.loads` に置換する、schema失敗後もpredicateを呼ぶと赤。

- `...::test_rejected_quality_is_not_accepted_with_self_consistent_clock`  
  schema-valid `quality.status=rejected` を公開較正として通すと赤。

- `...::test_canonical_predicate_result_is_the_only_clock_admission_signal`  
  monkeypatchした canonical predicate がfalseなのに inline帯計算・diagnostic件数で通すと赤。

- `...::test_receipt_replay_rejects_recorded_verdict_and_preimage_tampering`  
  replayが記録済みboolやpredicate preimageを信用すると赤。

- `...::test_subject_bytes_are_canonical_base64_chunks_not_plain_probe_corpus`  
  probe-v1 marker入りのschema-valid bytesを平文保存すると赤。

- `...::test_cli_94a4_fresh_process_returns_zero_and_writes_receipt`  
  entryが同一process helperだけになる、rcまたは出力生成を壊すと赤。

- `...::test_cli_753f_fresh_process_returns_one_and_writes_receipt`  
  reject時にartifactを書かない、rc=0/2にすると赤。

- `...::test_cli_create_only_collision_preserves_existing_output`  
  outputを `"w"` で上書きすると赤。

- `...::test_module_import_surface_is_python39_and_does_not_import_calibrator_cli`  
  3.10+構文や重い `calibrator.cli` importを追加すると赤。

- `orchestrator/tests/test_pegasus_tools.py::test_certify_orders_independent_verifier_between_calibrate_and_post_probe`  
  verifierをpublish前・post後に動かす、calibrator自身から起動すると赤。

- `...::test_certify_independent_reject_is_fatal_records_rc_and_preserves_publish`  
  verifier rcを握り潰す、job-resultを誤記する、published fileを削除すると赤。

- `...::test_collect_receipt_manifest_binds_independent_verification_artifact`  
  staging manifestから新artifactを除外すると赤。

## 変異事前登録

| 破壊する1行 | 期待赤 nodeid | 冗長性 |
|---|---|---|
| `verify_published.py:155` の `accepted` 連言から clock checkを除く | `test_registered_753f_vector_rejects_only_clock_gate_and_replays` | CLI 753f nodeも赤。冗長。 |
| `verify_published.py:118` の期待 basenameを入力 basenameそのものにする | `test_wrong_content_address_rejects_even_when_other_gates_pass` | 非冗長。 |
| `verify_published.py:127` の `validate_calibration_v2(raw)` を `json.loads(raw)` にする | `test_schema_invalid_bytes_skip_canonical_predicate_and_reject` | 非冗長。 |
| `verify_published.py:146` の canonical callを `True` またはdiagnostic countへ置換 | `test_canonical_predicate_result_is_the_only_clock_admission_signal` | 753f nodeも赤。冗長。 |
| `verify_published.py:151` の quality checkを連言から除く | `test_rejected_quality_is_not_accepted_with_self_consistent_clock` | 非冗長。 |
| `verify_published.py:59` で rawをBase64でなくUTF-8平文保存する | `test_subject_bytes_are_canonical_base64_chunks_not_plain_probe_corpus` | exact corpus testも将来条件付きで赤。冗長。 |
| `verify_published.py:187` で replay結果を `receipt["accepted"]` から返す | `test_receipt_replay_rejects_recorded_verdict_and_preimage_tampering` | 非冗長。 |
| `verify_published.py:216` の create-only `"x"` を `"w"` にする | `test_cli_create_only_collision_preserves_existing_output` | 非冗長。 |
| `certify_calibration.sh` の `|| independent_verification_rc=$?` を `|| true` にする | `test_certify_independent_reject_is_fatal_records_rc_and_preserves_publish` | CLI reject nodeも赤だがshell配線は本nodeだけ。部分冗長。 |
| verifier失敗 branchへ published artifact削除を1行追加 | 同 `test_certify_independent_reject_is_fatal_records_rc_and_preserves_publish` | 既存in-process削除防壁とも意図は冗長、層は別。 |
| `collect_receipt.py:82` で verification filenameを除外する | `test_collect_receipt_manifest_binds_independent_verification_artifact` | 非冗長。 |

pytest、`run_tests.py`、`check_docs.py` は実行していません。read-only の静的検査、artifact SHA/JSON確認、git状態確認のみです。

## 総括

- (a) `calibrator/verify_published.py` + 薄い entry、raw bytes内包receipt、canonical predicate一本化を採る。
- 94a4はaccept、753fはclock gateだけでrejectする固定vector・中央verificationを残す。
- live jobではcalibrator成功後・post probe前に別processで実行し、job-staging manifestへ束縛する。
- (b) P2は変更: SHA算出を恒真な受理条件にせず、policy二重実装を除き、`quality.status=accepted`を足す。
- P3は精密化: 現行2件は中央backfill、future jobは実行中job-stagingへ同一schemaを出す。
- P4は分離方針を維持し、独立rcとoverall rcだけを明示する。P1・P5・P6は維持する。
- P5のため、892707にfinal receipt束縛済みとは名乗らない。
- (c) 帯再実装、diagnostic受理、旧attempt追記、登録・contract・pin変更、既知例外削除は実装しない。
- method α の取得証明、collectorのsemantic gate化、receipt自己hash、working-tree hash pinも実装しない。