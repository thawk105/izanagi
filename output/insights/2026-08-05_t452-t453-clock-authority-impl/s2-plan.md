行番号は現 worktree（base `f009da3`）の変更前アンカーである。artifact bytes、registry の calibration path/SHA、`contract_sha256` は変更しない。

## 実装単位と順序

暫定 A → B → C は採らず、B → A → C の直列にする。A の `schema_v2.py:238-239` を先に `<100.0` 化すると、B 前の `env_attestation.py:433-440` が作る observed sentinel `100.0` が即座に schema 違反になるため、A 単独では緑にならない。

| 順序 | 実装単位 | 主成果 | 次単位への受け渡し |
|---|---|---|---|
| 1 | B: observed compatibility | observed 専用型、probe-output v2、v1 strict parser、版付き hash projection、全 call site の型移行 | observed は tolerance-free、v1 は履歴 replay 可能、expected schema はまだ `(0,100]` |
| 2 | A: policy authority | 単一定数、CLI/shell 入力面撤去、producer 注入、expected schema `<100.0` | producer が常に policy 値を持つ expected artifact を発行 |
| 3 | C: trust closure + T-453 | loader/issuer/consumer/receipt/registry/self gate、silo canonical 化、N2 の歴史化 | current admission が全経路で同じ受理集合になる |

素集合ではない。少なくとも以下が重複するため、並列 cherry-pick は不可とする。

- `schema_v2.py`: B の型追加と A の上限変更
- `env_attestation.py`: B の型・parser・projection と C の loader/issuer
- `cli.py`: B の observed serializer と A の policy 注入
- `certify_calibration.sh`: B の v2 消費と A の旧 env/argv 撤去
- `execution_guard.py`、silo、関連テスト: B の型移行と C の admission closure

B/A の中間 commit は replay/移行用であり、C 完了までは certified campaign を開かない。

## file:line 変更点

### 単位 B — observed 型分離、v2、legacy replay、hash projection

- `orchestrator/calibrator/schema_v2.py:218-239`
  - 現 `EffectiveClockProfile` を expected 専用として残す。
  - 直後に `ObservedEffectiveClockProfile` を追加し、field を exact に `samples_mhz/method/governor` のみにする。数値 sentinel や optional tolerance は持たせない。
- `orchestrator/calibrator/schema_v2.py:257-289`
  - `AttestationProfile` は expected 専用のまま残す。
  - 同じ CPU/core/cache/NUMA/TSC/visibility 型を再利用し、clock だけ observed 型を取る `ObservedAttestationProfile` を追加する。
- `orchestrator/calibrator/schema_v2.py:494-501`
  - `_CLOCK_KEYS` は expected の 4 key 用として維持し、observed 用 exact 3-key 集合を別名で置く。`_profile():530-555` は calibration expected parser のまま変更しない。

- `orchestrator/campaign/env_attestation.py:29-31`
  - probe 方式の `PROBE_VERSION = "1"` と出力 schema version を分離する。
  - `PEGASUS_PROBE_OUTPUT_V1/V2` を定義するが、T-419 scope の測定方式・`PROBE_VERSION` は変更しない。
- `orchestrator/campaign/env_attestation.py:47-49`
  - `HardwareProbe` の戻り型を `ObservedAttestationProfile` に変更する。
- `orchestrator/campaign/env_attestation.py:390-445`
  - `probe()` の戻り値を observed 型へ変更し、`:433-440` の `tolerance_pct=100.0` を完全に削除する。
- `orchestrator/campaign/env_attestation.py:450-505`
  - `normalize_profile()` は expected 専用として残し、docstring と型検査を明示する。
  - 隣に `normalize_observed_profile()` を追加し、clock が exact 3 key であることを検査する。
  - `parse_probe_output()` をここへ置き、raw bytes/text を duplicate-key 検出付きで読む。成功 top-level は exact `{schema_version,ok,observed_epoch,profile}`、失敗は exact `{schema_version,ok,observed_epoch,error}` とする。
  - v1 成功は clock key が exact 4 個かつ `type(tolerance_pct) is float` かつ `==100.0` の場合だけ、tolerance を捨てて observed 型へ射影する。JSON `100`、`2.0`、余分な key は拒否する。
  - v2 成功は exact 3 key とし、`tolerance_pct` が存在すれば値が `2.0` でも `100.0` でも拒否する。
  - profile を持たない v1/v2 failure document も typed failure として返す。
- `orchestrator/campaign/env_attestation.py:508-518`
  - `profile_to_dict/profile_sha256` は expected 専用として維持する。
  - `observed_profile_to_dict(profile, *, projection_schema)` と `observed_profile_sha256(...)` を追加し、version 引数を必須にする。
  - v1 projection は `tolerance_pct:100.0` を再注入して旧 preimage を再現し、v2 projection は 3 key のままにする。projection の正本はこのファイル一箇所とし、`run_probe.py` や T126 に複製しない。
- `orchestrator/campaign/env_attestation.py:521-554`
  - expected と observed を同一型で分岐する `_comparison_values(..., expected=...)` を、型別の expected/observed projector に分ける。receipt の observed clock は引き続き exact `{samples_mhz}`。
- `orchestrator/campaign/env_attestation.py:600-631`
  - `compare_profiles(expected: AttestationProfile, observed: ObservedAttestationProfile)` に変更する。issuer の数値比較自体はこの単位ではまだ現行相当とし、C で policy equality を閉じる。

- `orchestrator/calibrator/cli.py:337-342`
  - 任意 dataclass/`dict` を通す `_profile_dict` を observed 専用 serializer 呼出しへ置換する。probe fixture から tolerance を忍ばせる経路も閉じる。
- `orchestrator/calibrator/cli.py:526,539,599`
  - 3 回の probe 戻り値を observed として扱う。`:549-551` で expected profile を作るまでは tolerance を持たせない。

- `tools/pegasus/run_probe.py:24-32`
  - 任意 Mapping を許す `_jsonable` を廃止し、observed 専用 serializer だけを受理する。
- `tools/pegasus/run_probe.py:48-100`
  - import/probe/write の成功・失敗全 payload を `pegasus-probe-output/v2` にする。成功 profile の effective clock は exact 3 key。
- `tools/pegasus/certify_calibration.sh:571-575`
  - live probe input が v2 であることと observed clock の exact 3 key を確認してから acquisition receipt 用 profile を読む。旧 v1 は履歴 parser 専用であり、新規 job 入力には受けない。

- `orchestrator/qualification/t126_driver.py:439-455`
  - `:443-445` の誤った `verified.calibration` 渡しを `verified.attestation_profile` に修正する。
  - `:454` は expected 用 `profile_sha256` ではなく、明示的な v2 projection の `observed_profile_sha256` を使う。

- `orchestrator/tests/test_env_attestation.py:77-99`
  - probe の期待型を observed 型にし、clock に `tolerance_pct` 属性が無いことを固定する。
- `orchestrator/tests/test_env_attestation.py:168-261`
  - expected→observed 射影 helper を追加し、全 compare mutation を observed 型へ適用する。`:252` の observed tolerance 書換えは削除する。
  - v1/v2 parser、19 success replay、3 failure replay、v1/v2 hash projection の検査をこのファイルへ追加する。
- `orchestrator/tests/test_calibrator_certify.py:195-260`
  - `_profile()` と `_pegasus_shaped_probe()` の sentinel `100.0` を削除し、observed 型を返す。
- `orchestrator/tests/test_execution_guard.py:203-357`
  - `probe_fn=lambda: verified.attestation_profile` を expected→observed 射影 helperへ置換する。receipt bytes の observed clock shape は従来どおり `{samples_mhz}`。
- `orchestrator/tests/test_pegasus_tools.py:650-718`
  - run-probe fixture を observed 型に限定し、成功・import failure とも v2 schema、成功 clock は tolerance-free と確認する。
- `orchestrator/tests/test_s8b_floor_campaign.py:603-625,1366-1375,3446-3478`
  - required probe fixture と failure mutation を observed 型へ変更する。
  - real-seal fixture の synthetic clamp は残し、`:3471-3477` では expected clock を `replace` して sentinel を入れず、observed clock を構築する。
- `orchestrator/tests/test_s8b_oracle_driver.py:1495-1499,1530-1534,1587-1590,2062-2067`
  - issuer に expected profile をそのまま返す fixture をすべて observed 射影へ変更する。
- `orchestrator/tests/test_t126_qualification_driver.py:327` 付近
  - `_attest()` を直接呼ぶ検査を追加し、compare の第1引数が expected profile、第2引数が observed profileであること、hash が v2 projection であることを固定する。

### 単位 A — policy module、入力面撤去、producer、schema 上限

- `orchestrator/calibrator/effective_clock_policy.py:1`（新規）
  - `EFFECTIVE_CLOCK_TOLERANCE_PCT: Final[float] = 2.0` のみを権威として置く。
  - env 別 mapping、setter、fallback、環境変数参照、別名定数を置かない。

- `orchestrator/calibrator/cli.py:32-40`
  - 定数の値 import ではなく policy module を importし、利用時に module-qualified で参照する。metamorphic test の monkeypatch が全層へ届く形にする。
- `orchestrator/calibrator/cli.py:131-132`
  - `--effective-clock-tolerance-pct` action を削除する。
- `orchestrator/calibrator/cli.py:470-491`
  - `:485-488` の required/range 検証を削除する。
- `orchestrator/calibrator/cli.py:549-554`
  - observed dict から expected profile を作る際、`:551` の `args.effective_clock_tolerance_pct` を policy module の定数へ置換する。args 参照は残さない。
- `orchestrator/calibrator/cli.py:608-615,629-645`
  - self gate が policy 注入後、かつ candidate/publish の前である順序は維持する。

- `orchestrator/calibrator/schema_v2.py:235-239`
  - 上限条件を `tolerance >= 100.0` の拒否へ変更し、error 文言を「100 未満」にする。
  - schema は `5.0` や `99.0` を履歴 parse 用に受理し続ける。policy 完全一致をここへ入れない。

- `tools/pegasus/submit_certify.sh:5-10,17,20-44`
  - usage、`TOLERANCE`、旧 option branch、数値検証を削除する。
  - 旧 option や別名 option は unknown argument として、attempt/submission staging 作成前に rc 2。
  - legacy env `PEGASUS_EFFECTIVE_CLOCK_TOLERANCE_PCT` が既に設定されている場合は、無視せず preflight 前に明示拒否する。
- `tools/pegasus/submit_certify.sh:177-178`
  - qsub export から legacy env を除き、nonce だけを渡す。
- `tools/pegasus/certify_calibration.sh:150-166`
  - tolerance の数値取込みを削除する。legacy env が投入されていたら submit-binding failure として明示拒否する。
- `tools/pegasus/certify_calibration.sh:718-731`
  - calibrator argv から旧 option と env 展開を削除する。
- `tools/pegasus/README.md:74-77,86-90,101-105`
  - submit 例と凍結 CLI 一覧から option を除去し、値は Python policy module の単一権威であると記載する。

- `orchestrator/tests/test_effective_clock_policy.py:1`（新規）
  - AST で単一の `Final[float]` assignment、literal `2.0`、env/mapping/setter 不在を固定する。期待値は production 定数から生成しない。
- `orchestrator/tests/test_calibrator_certify.py:333-381`
  - `_invoke()` から tolerance parameter と旧 argv を除去する。
- `orchestrator/tests/test_calibrator_certify.py:531-636`
  - artifact の期待値を literal `2.0` にする。
  - 旧 `2.0/7.5` 引数保存テストは、policy 自動注入の正例と旧 option `2.0/100.0` の attempt 前拒否へ置換する。
- `orchestrator/tests/test_schema_v2.py:33-113,170-203`
  - 基本 schema fixture の `5.0` は維持する。
  - `99.99999999999999` は受理、`100.0`、`math.nextafter(100.0, inf)`、`1e300` は拒否する境界検査を追加する。
- `orchestrator/tests/test_pegasus_tools.py:200-216,952-982,1056-1087`
  - 旧 option/env の存在を期待する検査を、argv/export に存在しないことと hostile input の拒否へ反転する。
- `orchestrator/tests/test_env_contract.py:69-83,729-745`
  - env-neutral module inventory に新 policy module を追加する。

### 単位 C — trust boundary、receipt、registry、T-453、N2

- `orchestrator/campaign/env_attestation.py:21-23`
  - policy module を module-qualified import する。
- `orchestrator/campaign/env_attestation.py:564-597`
  - issuer の `_recorded_verdict()` は expected clock key を exact `{samples_mhz,tolerance_pct}`、observed を exact `{samples_mhz}` と確認する。
  - expected tolerance が current policy と不一致なら、サンプルが完全一致していても `fail`。
  - delta は artifact の任意値ではなく policy module の値から計算する。計算実装は `execution_guard` と共有せず、D155 の独立性を保つ。
- `orchestrator/campaign/env_attestation.py:643-693`
  - required calibration の schema/env_tag/clocks 検査後、`effective_clock.tolerance_pct == current policy` を確認し、不一致なら `VerifiedCalibration` を作る前に拒否する。
  - `mode=none` の grandfathered v1 経路にはこの検査を適用しない。

- `orchestrator/campaign/execution_guard.py:21-23`
  - policy module を module-qualified import する。
- `orchestrator/campaign/execution_guard.py:182-201`
  - 現在の任意 tolerance 数学を private `_effective_clock_band_math_passes()` として残す。
  - public canonical predicate は expected/observed exact key、expected tolerance と current policy の一致を確認し、delta を policy から計算して private helper を呼ぶ。
  - 数学 helper は arbitrary tolerance golden 用だけであり、admission caller から直接呼ばない。
- `orchestrator/campaign/execution_guard.py:204-222`
  - `_json_value` の一般 Mapping 許可は cache/NUMA 等のため残す。
- `orchestrator/campaign/execution_guard.py:264-277`
  - comparison field が `effective_clock.samples_mhz` の場合だけ、generic recursion 前に expected exact `{samples_mhz,tolerance_pct}`、observed exact `{samples_mhz}` を検査する。これが forged receipt を閉じる最小変更点。
  - repo 内に保存済み `s8b-execution-receipt/v2` は見つからないため、壊れる歴史 receipt bytes はない。
- `orchestrator/campaign/execution_guard.py:284-346`
  - `probe_fn` annotation を observed 型へ変更する。発行後の `validate_receipt_v2` 再検査は維持する。

- `orchestrator/calibrator/cli.py:381-391`
  - self helper は canonical predicate を通す。expected tolerance の policy 不一致も fail する。
- `orchestrator/calibrator/cli.py:608-615`
  - 外れ値がどの index にあっても rejection reason を追加し、`:629` 以降へ到達させない。

- `orchestrator/campaign/silo_ladder_rung1.py:15-40`
  - probe-output parser、expected serializer、canonical effective-clock predicate を import する。
- `orchestrator/campaign/silo_ladder_rung1.py:252-267`
  - runtime binding に `orchestrator/calibrator/effective_clock_policy.py` と `orchestrator/campaign/execution_guard.py` を追加する。新 evidence は tolerance の意味論まで hash-bound される。
- `orchestrator/campaign/silo_ladder_rung1.py:1928-1999`
  - current contract は `load_verified_calibration()` で読む。
  - `:1953-1960` は v2 parser で live probe を読む。
  - `:1962-1965` の median-to-median 比較を canonical predicate に置換する。method/governor の既存 exact 比較は維持する。
- `orchestrator/campaign/silo_ladder_rung1.py:3393-3451`
  - raw replay は document が束縛する calibration bytes と probe bytesを読む。probe は v1/v2 parser へ通す。
  - `:3401-3419` の median 比較を canonical predicate に置換する。
  - historical raw の検証と current registry の照合は混ぜず、current 性は引き続き `validate_current_bindings()` が所有する。
- `orchestrator/campaign/silo_ladder_rung1.py:3496-3527`
  - allow-through branch は追加しない。既存の driver hash と runtime-module binding の不一致を fail-closed のまま使う。
  - 本変更後、旧 evidence は `:3511-3518` で driver/runtime binding が不一致となり、自動的に current eligibility を失う。
- `orchestrator/campaign/silo_ladder_rung1.py:4713,4770-4778,4817-4826`
  - collect/verify-result が raw canonical failure と current-binding failureをそのまま fatal とする順序を維持する。

- `orchestrator/tests/test_execution_guard.py:118-176`
  - clock comparison を含む receipt fixture を追加し、observed への `tolerance_pct:2.0` と `100.0`、expected の欠落/余分 key を拒否する。
- `orchestrator/tests/test_execution_guard.py:179-200`
  - admission 用 `_required_binding()` だけ tolerance を literal `2.0` に上書きしてから raw/SHA を作る。schema 共通 fixture の `5.0` は変更しない。
- `orchestrator/tests/test_execution_guard.py:336-357`
  - constant-pass issuer の forged receipt を consumer が拒否する独立性検査を observed 型へ移行して維持する。
- `orchestrator/tests/test_execution_guard.py:360-482`
  - arbitrary tolerance の既存 18 vectors は private math helper で同じ期待値を維持する。
  - canonical admission 用には別の policy vectors を追加し、非 policy tolerance をすべて拒否する。

- `orchestrator/tests/test_calibrator_certify.py:531-577`
  - self-comparison helper を48 index 全てで parameterizeし、`[2101.0] * 48` の任意 index を `3080.0` に置換した入力を全て false とする。
  - CLI integration は index `0/24/47` を最低限通し、candidate/publish/registered が作られないことを確認する。
- `orchestrator/tests/test_calibrator_certify.py:580-636`
  - policy `2.0` の clean profile だけが publish され、その artifact が canonical self predicate を通ることを確認する。
  - 同ファイルへ `test_policy_wiring_metamorphic_moves_producer_loader_issuer_and_consumer_together` を追加する。central policy を literal `3.0` に monkeypatch し、producer artifact=`3.0`、SHA 再計算済み loader 受理、median `100.0` に observed `102.5` の issuer/consumer pass を確認する。一方、literal `2.0` artifact/map は同じ patched run で全層が拒否する。期待データは production 定数から生成しない。

- `orchestrator/tests/test_env_attestation.py:264-334`
  - loader 正例 fixture は literal `2.0`。
  - `5.0/99.0` を入れ、raw と contract SHA を再計算した well-formed artifact を負例にする。
- `orchestrator/tests/test_env_attestation.py:249-261`
  - issuer へ tolerance `5.0`、expected/observed samples とも `[100.0]` を与え、数値上は通るが policy 不一致で fail する検査を追加する。

- `orchestrator/tests/test_env_contract.py:58-63`
  - `KNOWN_SELF_INCONSISTENT_CALIBRATIONS` は exact 1 件のまま維持する。
- `orchestrator/tests/test_env_contract.py:399-463`
  - required entry 件数 `1`、registry 総数 `2`、全 required tolerance が literal `2.0` であることを固定する。
  - 入力可能な test helper に schema-valid/policy-valid/self-fail の `[2101.0]*47+[3080.0]` を渡し、constant-pass mutation を殺す。
  - 現登録 artifact の self-failure が既知集合と exact に一致することを維持する。

- `orchestrator/tests/test_silo_ladder_rung1_driver.py:745-764`
  - runtime binding の期待集合へ policy と execution guard を追加する。
- `orchestrator/tests/test_silo_ladder_rung1_driver.py:1149-1169`
  - synthetic raw bundle を probe-output v2 + tolerance-free observed に変更する。
  - all-green fixture の observed clock は全標本を expected の policy band 内に置く。期待 verdict は true のままであり、入力を新 contract に適合させる変更である。

- `orchestrator/tests/test_silo_ladder_rung1_evidence.py:44-47`
  - production ではなく test-only に、旧 evidence の exact identity を置く。
  - tuple は evidence path/SHA `38f5de…a484b37`、raw probe path/SHA `e0e377…a5a3c2`、calibration SHA `753f535…ce5a49`、旧 driver SHA `92affa…355f8` を全て含める。
  - current eligibility の一時例外集合と、永久に保持する historical identity は別名にする。前者は T-419 U-2 後に空にできるが、後者は artifact 改変検知用として残せる。
- `orchestrator/tests/test_silo_ladder_rung1_evidence.py:895-980`
  - `:945-963` の独立再導出を二つに分ける。
    1. legacy v1 median 式で recorded `effective_clock_match=True` が当時の実装に対して正しかったことを確認する。
    2. literal `2.0` と全 samples による独立 canonical 式で false を導出する。
  - recorded bool を false に書き換えず、「歴史上 true / current canonical false」を同時に固定する。
- `orchestrator/tests/test_silo_ladder_rung1_evidence.py:1172-1433`
  - committed evidence の exact SHA と旧 binding を確認したうえで、`validate_raw_bundle()`、`validate_current_bindings()`、`verify-result` が current として拒否することを期待する。
  - driver SHA だけを current に差し替えた test copy も runtime-module mismatch で拒否し、driver 一箇所だけに依存した非 current 判定にしない。
  - `output/.../silo_ladder_rung1.json` と raw probe bytes は一切編集しない。

## 新設する検査と負例

| gate / nodeid | 具体的な負例 | 殺す変異 |
|---|---|---|
| `test_effective_clock_policy_is_single_literal_authority` | AST 上で assignment が複数、mapping/setter/env 参照、literal が `2.0` 以外 | 層ごとの直書き・別正本 |
| `test_policy_wiring_metamorphic_moves_producer_loader_issuer_and_consumer_together` | policy を `3.0` に変更中、旧 literal `2.0` artifact/map。正例は median `100.0` / observed `102.5` | policy import 不使用、import-time 値コピー、どれか一層だけ追従 |
| `test_certify_parser_option_surface_is_exact` | action の option-string/dest に旧 flag または `--clock-window` を追加 | alias・分割表記で入力面を復活 |
| `test_cli_rejects_legacy_tolerance_override_before_attempt[2.0/100.0]` | 旧 option を各値で指定 | legacy option 再受理 |
| `test_submit_certify_rejects_legacy_tolerance_input[...]` | 旧 option `2.0/100.0`、別名 `--clock-window 2.0`、legacy env `2/100` | shell 別名・env 搬送復活 |
| `test_expected_clock_tolerance_upper_boundary` | `100.0`、`nextafter(100,+inf)`、`1e300`。正例 `99.99999999999999` | `==100` だけを拒否する退行 |
| `test_probe_output_v1_accepts_only_exact_float_sentinel` | v1 clock の `100`、`2.0`、`99.0`、3 key、余分 key、欠落 key | loose legacy parser |
| `test_probe_output_v2_rejects_tolerance_field` | v2 observed に `tolerance_pct:2.0` または `100.0` | observed への policy field 復活 |
| `test_probe_output_v1_corpus_replays_exactly_19_success_and_3_failure` | corpus 件数欠落、success の projection/hash 不一致 | replay 対象の見落とし |
| `test_observed_hash_projection_preserves_v1_preimage` | v1 projection が sentinel を戻さない、v2 projection に sentinel が入る | 同一 schema 名で hash 意味変更 |
| `test_self_gate_rejects_outlier_at_every_index[0..47]` | `[2101]*48` の各 index を `3080` に置換 | first/last slice で外れ値除外 |
| `test_loader_rejects_well_formed_nonpolicy_tolerance[5.0/99.0]` | schema-valid、SHA 再計算済み artifact | loader equality 削除 |
| `test_issuer_rejects_nonpolicy_tolerance_even_when_samples_equal` | expected tolerance `5.0`、双方 `[100.0]` | issuer が artifact tolerance を信用 |
| `test_canonical_consumer_rejects_unauthorized_tolerance[3/5/99]` | expected/observed samples は完全一致 | consumer equality 削除 |
| `test_canonical_policy_boundary` | median `100`; `101.999999` は pass、`102.000001` は fail | `<`/`<=`、percent 計算の退行 |
| `test_receipt_rejects_observed_clock_policy_injection[2/100]` | observed `{samples_mhz:[100],tolerance_pct:X}` | `_json_value` の任意 key 許可を悪用 |
| `test_receipt_rejects_expected_clock_key_drift` | expected の tolerance 欠落、`method` 余分 key | receipt expected shape の開放 |
| `test_registry_policy_and_self_gate_are_nonvacuous` | required count 0、または `[2101]*47+[3080]` を constant-pass | 空 loop・`passes=True` |
| `test_silo_canonical_rejects_median_only_outlier` | expected `[2101]*48`、observed `[2101]*47+[3047.574]` | T-453 の median 比較残存 |
| `test_historical_silo_evidence_is_exact_and_not_current` | exact digest 以外の stale evidence、または旧 evidence を current-pass と扱う | 広い歴史 allowlist、current gate の例外化 |

## 移行 matrix

### canonical golden vectors

`test_execution_guard.py:360-482` の任意 tolerance 数学は削除せず private helper に移す。canonical admission は policy `2.0` のみとなる。

| vector | 現在 | 変更後（数学 helper / canonical admission） | 正当化 |
|---|---:|---:|---|
| odd-all-inside, tol 2 | true | true / true | policy-valid、受理集合不変 |
| even-inclusive-boundaries, tol 10 | true | true / false | 数学は保存、非 policy admission を廃止 |
| pegasus-shaped-one-outlier, tol 2 | false | false / false | 全標本述語を維持 |
| mean-drift-same-median-inside, tol 20 | true | true / false | 任意幅の数学は保存、current admission は縮小 |
| mean-drift-same-median-outside, tol 20 | false | false / false | 既存負例を維持 |
| expected-not-mapping | false | false / false | shape gate 不変 |
| observed-not-mapping | false | false / false | shape gate 不変 |
| expected-samples-not-list | false | false / false | shape gate 不変 |
| observed-samples-not-list | false | false / false | shape gate 不変 |
| expected-empty | false | false / false | empty 拒否を維持 |
| observed-empty | false | false / false | empty 拒否を維持 |
| tolerance-bool | false | false / false | bool 拒否を維持 |
| nonnumeric-sample | false | false / false | 数値検査を維持 |
| near-zero-tolerance-inside | true | true / false | 数学は保存、非 policy 値を admission から除外 |
| near-zero-tolerance-outside | false | false / false | 既存負例を維持 |
| zero-tolerance-exact | true | true / false | schema/policy 外の数学だけ保存 |
| hundred-tolerance-boundaries | true | true / false | 恒真化に近い current 受理を閉じる |
| hundred-tolerance-outside | false | false / false | 既存負例を維持 |

### test fixture / literal

| 場所 | 現在の期待値 | 変更後の期待値 | 正当化 |
|---|---|---|---|
| `test_schema_v2.py:33-113` | schema fixture `5.0` を受理 | `5.0` を引き続き受理 | schema と policy を分離し、履歴 parse を維持 |
| `test_schema_v2.py:170-203` | `0.0` 拒否 | 拒否のまま、`>=100` も拒否 | 既存負例を緩めず上限を狭める |
| `test_execution_guard.py:179-200` | admission fixture `5.0` | literal `2.0` | loader accepted set が current policy に縮小 |
| `test_execution_guard.py:203-357` | expected profile を observed として流用 | tolerance-free observed 型、verdict は同じ | 型 contract の変更であり期待判定は緩めない |
| `test_calibrator_certify.py:195-260` | probe fixture に sentinel `100.0` | clock は 3 key | observed が policy を持たないことを構造化 |
| `test_calibrator_certify.py:531-577` | probe sentinel は全 true、artifact `5.0`、outlier false | sentinel 検査廃止、artifact `2.0`、outlier false | producer authority を固定し、負例は維持 |
| `test_calibrator_certify.py:580-610` | published artifact `5.0` | `2.0` | current producer の受理集合変更 |
| `test_calibrator_certify.py:613-636` | CLI `2.0/7.5` をともに保存 | option は双方拒否、option 無しで `2.0` | 手入力による非 policy artifact の受理を廃止 |
| `test_env_attestation.py:77-99` | probe は expected 型 + `100.0` | observed 型、tolerance 属性なし | sentinel を構造的に排除 |
| `test_env_attestation.py:168-261` | expected fixture `5.0`、observed tolerance `0.1` は無視 | admission 用 expected `2.0`、observed tolerance 自体を構築不能 | issuer 入力 contract の縮小 |
| `test_env_attestation.py:264-334` | loader fixture `5.0` を受理 | default `2.0` を受理、`5/99` を拒否 | trust-boundary policy equality |
| `test_env_contract.py:58-63,436-463` | 既知 self-failure 1 件 | exact 1 件のまま | T-419 U-2 は scope 外 |
| `test_silo_ladder_rung1_evidence.py:945-963` | median 再導出 true | legacy median true / current canonical false | artifact の歴史的真実を保ち current admission を縮小 |
| `test_silo_ladder_rung1_evidence.py:1172-1433` | committed evidence が current/all-pass | exact historical evidence としてのみ妥当、current gate は拒否 | code/runtime binding が変わり current ではない |
| `test_s8b_floor_campaign.py:603-625` | required fixture `5.0`、expected を observed として返す | expected `2.0`、observed 射影 | loader と probe の新 contract |
| `test_s8b_floor_campaign.py:1366-1375` | expected 型を mutate した observed 負例 | observed 型の vendor mutation、side effect なしは同じ | 既存 fail-closed 期待を維持 |
| `test_s8b_floor_campaign.py:3446-3478` | clamp 後 sentinel `100.0` | 同じ clamp、tolerance-free observed | synthetic clamp の事実を保ち sentinel だけ除去 |
| `test_s8b_oracle_driver.py:1390-1406` | loader fixture の任意 tolerance | literal `2.0` | required admission の新 accepted set |
| `test_s8b_oracle_driver.py:1495-1590,2062-2067` | expected を observed として流用 | observed 射影、既存 verdict 不変 | 型 contract の適合 |
| `test_pegasus_tools.py:200-216` | 旧 option/env が argv/export に存在 | 不在かつ hostile 入力を拒否 | 入力権威の撤去 |
| `test_pegasus_tools.py:690-718` | probe-output v1 + sentinel | v2 + 3-key clock | 新規 producer の schema migration |
| `test_pegasus_tools.py:952-982` | job fragment に legacy env=`5` | legacy env は開始時拒否 | scheduler 経由の裏口を閉じる |
| `test_pegasus_tools.py:1056-1087` | dry-run に旧 option `1.5` | option 無しで成功、旧 `2/100` は失敗 | positive input surface を縮小 |
| `test_silo_ladder_rung1_driver.py:1149-1169` | v1/full expected profile、median gate true | v2/observed profile、全標本 band 内で true | all-green 期待は維持し入力を現契約へ移行 |
| `test_t126_qualification_driver.py:327` 付近 | `_attest` の型/hash 境界未検査 | expected/observed 分離、v2 hash | ripple の取りこぼしを防ぐ |
| `test_t419_probe_causality.py:173,527,533` | analysis literal `2.0` | 変更なし | probe 方式・再取得は scope 外 |

### v1 artifact corpus と固定 artifact

以下の JSON 22 件を replay corpus として明示する。`.stdout` の同内容コピーは bytes を変更せず、parser の正本 corpus には数えない。

| artifact | 現在 → 変更後 | 正当化 |
|---|---|---|
| `.../job-staging/0:867865.nqsv/attestation-static.json` | v1/sentinel、median pass → v1 strict parse、canonical fail | N2、current accepted set の縮小 |
| `.../0:867866.nqsv/attestation-static.json` | 同上 → 同上 | 同上 |
| `.../0:867867.nqsv/attestation-static.json` | 同上 → 同上 | 同上 |
| `.../0:867868.nqsv/attestation-static.json` | 同上 → 同上 | 同上 |
| `.../0:867869.nqsv/attestation-pre.json` | 同上 → 同上 | 同上 |
| `.../0:867869.nqsv/attestation-static.json` | 同上 → 同上 | 同上 |
| `.../0:867870.nqsv/attestation-pre.json` | 同上 → 同上 | 同上 |
| `.../0:867870.nqsv/attestation-static.json` | 同上 → 同上 | 同上 |
| `.../0:867872.nqsv/attestation-pre.json` | 同上 → 同上 | 同上 |
| `.../0:867872.nqsv/attestation-static.json` | 同上 → 同上 | 同上 |
| `.../0:867874.nqsv/attestation-pre.json` | 同上 → 同上 | 同上 |
| `.../0:867874.nqsv/attestation-static.json` | 同上 → 同上 | 同上 |
| `.../0:867876.nqsv/attestation-post.json` | 同上 → 同上 | 同上 |
| `.../0:867876.nqsv/attestation-pre.json` | 同上 → 同上 | 同上 |
| `.../0:867876.nqsv/attestation-static.json` | 同上 → 同上 | 同上 |
| `output/env/pegasus/smoke/0:867860.nqsv/observation.json` | v1 success → v1 strict replay success | 履歴 replay、current admission には使用しない |
| `output/env/pegasus/smoke/0:867861.nqsv/observation.json` | 同上 → 同上 | 同上 |
| `output/env/pegasus/smoke/0:867862.nqsv/observation.json` | 同上 → 同上 | 同上 |
| `output/env/pegasus/silo_ladder_rung1/.../attestation-job.json` | v1 median pass → v1 parse、legacy true/current canonical false | N2 を bytes 改変なしで表現 |
| `output/env/pegasus/smoke/0:867857.nqsv/observation.json` | v1 failure/no profile → typed v1 failure | effective clock 無しでも replay 維持 |
| `output/env/pegasus/smoke/0:867858.nqsv/observation.json` | 同上 → 同上 | 同上 |
| `output/env/pegasus/smoke/0:867859.nqsv/observation.json` | 同上 → 同上 | 同上 |

次の expected artifact/literal は変更しない。

| artifact | 現在 → 変更後 | 正当化 |
|---|---|---|
| `output/env/pegasus/calibration/attempts/0_867874.nqsv/calibration.json:1493` | `2.0` → `2.0` | 既に policy 一致 |
| `output/env/pegasus/calibration/attempts/0_867876.nqsv/calibration.json:1493` | `2.0` → `2.0` | 同上 |
| `output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json:1493` | `2.0` → `2.0` | path/SHA と bytes を固定 |
| `output/env/pegasus/t419-probe-causality/0_888740.nqsv/{manifest,result}.json` | `2.0` → `2.0` | T-419 analysis は scope 外 |
| `output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json:8,568,573` | recorded `all_pass/effective_clock_match=true` → bytes 上は true のまま | 歴史記録を改竄せず current eligibility だけ外す |

## 未解決・親の裁定が要る点

1. 暫定 P3 の A → B → C を B → A → C に変更する裁定が必要。A 先行は observed sentinel が schema で壊れるため、独立 landing として成立しない。
2. N2 の既知例外は production admission ではなく、`test_silo_ladder_rung1_evidence.py` の exact test-only singleton とすることを裁定してほしい。`validate_current_bindings()`、loader、consumer、`KNOWN_SELF_INCONSISTENT_CALIBRATIONS` には例外を入れない。
3. legacy shell env は「無視」ではなく明示拒否を推奨する。無視を選ぶと、旧投入系が成功したように見えるため入力面撤去の negative control が弱くなる。
4. B/A の中間 commit を campaign 非 admissible とし、C まで連続 landing する運用確認が必要。
5. probe 方式、較正再取得、contract 世代、content-addressed path はこのプランでは扱わない。

## 総括

- 実装順は observed compatibility B → policy authority A → trust closure C の直列とする。
- policy の唯一の権威は新 leaf module の literal `2.0` である。
- observed から tolerance を型として除去し、v1 は厳密 sentinel parser と版付き projection で replay する。
- loader・issuer・consumer・self gate・registry はそれぞれ独立に policy 一致を検査する。
- receipt の observed clock は exact `{samples_mhz}` とし、tolerance 注入を拒否する。
- 旧 silo evidence は legacy verdict を保存した歴史資料とし、current binding と canonical gate の双方で拒否する。
- `KNOWN_SELF_INCONSISTENT_CALIBRATIONS`、artifact bytes、registry pin、contract hash は変更しない。