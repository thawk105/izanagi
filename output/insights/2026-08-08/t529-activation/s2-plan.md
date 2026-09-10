静的読解上の判定は「条件付き GO」です。ファイル変更・pytest 実行は行っていません。条件は、provisional P3 を採らず、確定済み D228/T-627 に従う遷移検査まで activation loader に含めることです。

## Provisional 裁定の扱い

- P1 は採用する。pegasus g2 は登録するが、初期 activation は両 env g1 とする。これにより committed floor protocol の live admission を維持する。
- P2 は採用する。実在する pegasus g2 を指す serial 2 を一時 record directory でロードする正例を置く。
- P3 は採用しない。[D228](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/docs/decisions.md:10663) は no-op/skip/downgrade 拒否を規則化し、[T-627](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/docs/archive/worklog-phase3-0807-299.md:409) は「実 schema 確定まで置かない」とした。この wave で schema が確定する以上、停止条件は満たされる。別 wave へ再延期すると、canonical で hash-chain が正しい no-op/downgrade record を受理して D228 に反する。
- P4 は採用する。module import は generation の純構造検査までとし、activation/calibration の I/O は最初の `REGISTRY` 操作・`lookup()`・historical resolve・writer gate まで遅延する。

P3 の修正は確定裁定を覆すものではないため、ユーザー再裁定は不要と判断する。

## 実装対象と file:line 計画

### 1. 新 leaf

新規 module は `orchestrator/campaign/env_contract_activation.py` とする。

公開 API は次で固定する。

```python
def canonical_record_bytes(document: Mapping[str, object]) -> bytes: ...

def build_activation_record(
    *,
    activation_serial: int,
    previous_activation_state_sha256: str | None,
    active_contracts: Sequence[ActiveContract],
) -> dict[str, object]: ...

def validate_activation_records(
    records: Sequence[tuple[str, bytes]],
    *,
    registered_contracts: Mapping[
        str, tuple[tuple[int, str], ...]
    ],
) -> ActivationState: ...

def load_activation_state(
    directory: Path,
    *,
    registered_contracts: Mapping[
        str, tuple[tuple[int, str], ...]
    ],
) -> ActivationState: ...

def issue_process_receipt(
    state: ActivationState,
) -> ActivationReceipt: ...

def assert_process_receipt(
    receipt: ActivationReceipt,
    *,
    state: ActivationState,
) -> None: ...
```

予定行域:

- `:1-35` — stdlib import、schema/file-name regex、`ActivationRecordError`。campaign/calibrator import は禁止。
- `:36-115` — frozen `ActiveContract`、`ActivationRecord`、`ActivationState`、process seal 付き `ActivationReceipt`。
- `:116-170` — duplicate-key・NaN 拒否 JSON decoder、canonical serializer。
- `:171-245` — exact key/type、slug、hex64、active row の昇順・重複検査、state hash 再計算。
- `:246-325` — filename/serial、連番、predecessor hash、registry membership、同一 env 集合の検査。
- `:326-365` — D228 遷移検査。各 env の delta ∈ `{0,1}`、同 generation なら hash 同一、少なくとも一つが `+1`。
- `:366-415` — directory の no-symlink regular-file 読込と全 chain の集約、ever-active 集合の生成。
- `:416-455` — process-local receipt 発行・PID/seal・serial/state hash の assertion。

AST 閉包ではこの module を env 固有 literal 免除なしで追加する。env 固有値は引数の catalog からしか得ない。

### 2. activation record

格納先は次とする。

```text
orchestrator/campaign/env_contract_activations/
└── 00000001.json
```

filename は `f"{activation_serial:08d}.json"`。8桁を超える serial は自然に桁を増やし、loader は数値順に並べる。directory 内の不正名、symlink、非 regular file、serial gap は拒否する。

exact schema:

| key | 制約 |
|---|---|
| `schema_version` | exact `str`、`"env-contract-activation/v1"` |
| `activation_serial` | exact positive `int`、`bool` 拒否 |
| `previous_activation_state_sha256` | serial 1 は `null`、以後 lower-hex64 |
| `active_contracts` | 非空 list、`env_tag` 昇順、全登録 env と exact 同一集合 |
| `activation_state_sha256` | lower-hex64 |

各 `active_contracts` 要素は exact に `env_tag`、`generation`、`contract_sha256` の3 keyだけを持つ。

canonical/hash 規則:

```text
body_i = record_i から activation_state_sha256 だけを除いた object
C_i    = json.dumps(body_i, sort_keys=True, separators=(",", ":"),
                    ensure_ascii=True, allow_nan=False).encode("utf-8")
H_i    = SHA-256(C_i)
record_i.activation_state_sha256 = hex(H_i)
record_(i+1).previous_activation_state_sha256 = hex(H_i)
file_i = canonical JSON(full record_i) + b"\n"
```

初期 record の canonical bytes は次になる。

```json
{"activation_serial":1,"activation_state_sha256":"f78072854651b316e1f2d78c2dfc58bfd995160515ed721a80a267ced54cd3ed","active_contracts":[{"contract_sha256":"1b2ee85346a4c867754bda497b23d649e66027011167cfb0f9c7f9a1a5fa1dc7","env_tag":"linux-baremetal","generation":1},{"contract_sha256":"e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01","env_tag":"pegasus","generation":1}],"previous_activation_state_sha256":null,"schema_version":"env-contract-activation/v1"}
```

末尾に LF を一つ加える。上記 state hash は、同じ canonical 手順による静的算出値である。

### 3. `env_contract.py`

[env_contract.py:231-275](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/env_contract.py:231):

- `_build_registry()` 内で pegasus g2 を追加する。
- calibration ref:
  - path: `output/env/pegasus/calibration/registered/calibration-94a4b79fa31bba3c.json`
  - sha256: `94a4b79fa31bba3c725bd9c18990ae60bea86dbcdb6eff19822a58a75fe5c5a9`
- contract hash golden: `1346c20b5519be4b4d3aef19adc5a93ce2804ad4e0428dc5095635f54187ad1c`
- g1 contract を `dataclasses.replace()` し、calibration ref だけを変える形にして successor 制約を明瞭にする。

[env_contract.py:316-326](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/env_contract.py:316):

- `len(sequence) != 1` loop を削除。
- `validate_generations()` は `_validate_generations_without_bootstrap_fuse()` への構造検査委譲だけにする。
- private helper は既存テスト互換のため残す。

[env_contract.py:342-352](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/env_contract.py:342):

- import 時には `GENERATIONS` の生成・構造検証と全登録世代 index の構築だけを行う。
- `REGISTRY` は `MappingProxyType(_ActivationRegistryView())` とする。内側は read-only `Mapping` で、`__getitem__`、`__iter__`、`__len__`、`items()` 等が初回だけ authority cache をロードする。
- これにより `MappingProxyType` という公開形を維持しつつ、import 時 I/O を避ける。
- raw backing dict は module 属性へ露出しない。

新規予定 `:353-475`:

- `GENERATIONS` を env-neutral な `env_tag -> ((generation, contract_sha256), ...)` catalog へ射影。
- mutex と PID を持つ process-local cache。並行する初回 lookup でも検証を一回にする。fork 後は PID 不一致として再ロードする。
- activation chain の全 ever-active entry を `calibration_verify.load_verified_calibration()` へ渡す。
- required mode は registered filename、bytes hash、v2 schema、env/clock/policy、`quality.status=="accepted"` を要求する。
- legacy は共有 leaf の grandfather SHA と、record/catalog が束縛する exact g1 contract hash の組合せだけを許す。
- current row から `MappingProxyType[str, ExecutionEnvironmentContract]` を作る。
- state と同時に process receipt を一件だけ発行する。

[calibration_verify.py:81-159](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/calibration_verify.py:81) 自体は変更しない。activation 固有の registered-path と accepted-status 条件は `env_contract.py` の統合層で追加し、共有 admission の既存受理集合を変えない。

[env_contract.py:355-380](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/env_contract.py:355):

- hash format、登録 index の存在、一意性を従来順で検査する。
- その後に `contract_sha256 in activation_state.ever_active_contract_sha256s` を要求する。
- 未登録 hash は従来どおり「未知」、登録済み未 active の g2 は「登録済みだが ever-active でない」と区別する。
- `expected_env_tag` 検査と返り値 `GenerationEntry` は維持する。

[env_contract.py:383-410](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/env_contract.py:383):

- `lookup()` の署名、戻り型、unknown-env error を維持。
- `REGISTRY` の lazy view を唯一の current seam とする。
- `lookup_required_attestation_contract()` も同じ snapshot を使う。
- `current_activation_receipt() -> ActivationReceipt` と
  `assert_current_activation_receipt(receipt: ActivationReceipt) -> None`
  を追加する。

### 4. 発行 tool

`tools/issue_env_contract_activation.py` を新設する。

- `:1-40` — argparse。全 env の `--active ENV_TAG=GENERATION` を明示必須にする。
- `:41-75` — **parse 後**にだけ repo/authority loader を呼ぶ。import 自体では I/O しない。
- `:76-120` — 現 chain と候補 generation/calibration evidence を検証。
- `:121-150` — leaf の `build_activation_record()` と in-memory chain 再検証。
- `:151-190` — `O_CREAT|O_EXCL|O_NOFOLLOW`、write-all、file/directory fsync。既存 file は上書きしない。

calibration publisher から自動起動しない。発行後は maintainer が diff と較正 evidence をレビューし、commit して初めて trust root に入る。

## 遅延 lookup の後方互換

親 brief が数えた非 test の `lookup` 系70参照は個別変更しない。維持されるものは、署名、戻り型、g1 object、unknown-env の基本エラー、`REGISTRY` の read-only `MappingProxyType` である。

破れ得る点は次のとおり。

- 最初の lookup/registry iteration に activation record と calibration の I/O・検証コストが加わる。
- record 欠落・非canonical・hash-chain 不正・calibration 不正が、import 時でなく最初の利用時に `EnvContractError` となる。
- 一度成功した process は同じ snapshot を使い続ける。record を追加しても process restart までは見えない。
- 登録済みだが一度も active でない g2 は historical resolver でも拒否される。
- `GENERATIONS[-1]` を current と仮定する private/test code は破れる。
- `REGISTRY` や `_CONTRACT_SHA256_INDEX` だけを monkeypatch するテストでは不十分になり、activation directory、catalog/index、cache clear を同時に扱う必要がある。
- import failure を期待する bootstrap-fuse test は、lazy-load/activation-view test へ置換する。

## historical lane への効果

[s8b_ratified_freeze.py:2769-2800](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/s8b_ratified_freeze.py:2769) と [launch/reverify:3234-3254](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/s8b_ratified_freeze.py:3234) は production 変更不要。

- `launch_validate()` は `lookup()` を使うため、初期 record では引き続き g1 のみ受理する。
- `reverify_published_freeze()` は central resolver を使うため、initial g1 は受理し、未 active g2 は `protocol-invalid` で拒否する。
- serial 2 で g2 が active になった後は、live lane は g2、historical lane は g1/g2 の双方を解決できる。

[s8b_oracle_report.py:1193-1235](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/s8b_oracle_report.py:1193) と [s8b_oracle_report.py:1637-1645](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/s8b_oracle_report.py:1637) も central resolver の意味変更だけでよい。未 active g2 manifest は `ReportError` を経て各 row が `protocol_violation` となり、current lookup へ fallback しない。

## receipt と既存5条件の順序

[execution_guard.py:42-102](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/execution_guard.py:42) を次の順にする。

1. 既存 condition 1: `authorization_contract`、`env_tag`、`clocks_per_us` の exact 型。
2. 新 condition 0A: cached `ActivationReceipt` を取得し、同じ cached state に対して seal、PID、`activation_serial`、`activation_state_sha256`、object identity を assert。
3. 既存 condition 2: authorization contract と current registry の同値。
4. 既存 condition 3: env/clock/numactl の完全一致。
5. 既存 condition 4: compute site の exact required-attestation contract。
6. 既存 condition 5: build selector contract との同値。

型エラーの従来優先順を保ちつつ、current registry を権威として使う前に activation receipt を検査する。receipt 引数を全 caller へ増やさず、guard が process-local receipt を取得・再assertする。process receipt は成果物へ書かないため、既存 JSON/WAL bytes は変わらない。

## テスト計画

| nodeid 候補 | 落とす誤実装 |
|---|---|
| `test_env_contract.py::test_generation_golden_has_exact_keys_and_all_generation_hashes` | g2 欠落、g1 drift、誤った g2 hash |
| `test_env_contract.py::test_validate_generations_accepts_registered_pegasus_g2` | bootstrap fuse の削除漏れ |
| `test_env_contract.py::test_registry_and_lookup_follow_activation_not_generation_tail` | `sequence[-1]` への逆戻り |
| `test_env_contract.py::test_registered_pegasus_g2_calibration_is_hash_bound_v2_and_accepted` | 誤 path/hash、rejected artifact の登録 |
| `test_env_contract.py::test_resolver_rejects_registered_never_active_g2` | registry 全体を historical authority とする誤実装 |
| `test_env_contract.py::test_activation_leaf_is_stdlib_only_campaign_import_free_and_env_neutral` | import 循環、env literal、非 leaf 化 |
| `test_env_contract_activation.py::test_initial_record_is_exact_canonical_hash_bound_and_selects_both_g1` | canonical/hash/schema/初期 pointer の誤り |
| `test_env_contract_activation.py::test_record_rejects_duplicate_unknown_noncanonical_and_bool_integer_fields` | permissive JSON/schema |
| `test_env_contract_activation.py::test_chain_rejects_gap_filename_mismatch_bad_predecessor_and_symlink` | rollback・chain 切断・別 file 差替え |
| `test_env_contract_activation.py::test_transition_rejects_noop_skip_downgrade_hash_swap_and_env_set_change` | P3 型の永久的な意味 gate 欠落 |
| `test_env_contract_activation.py::test_real_pegasus_g2_serial2_transition_is_accepted_and_switches_lookup` | **generation > 1 を無条件拒否する永久 fuse**。実 `GENERATIONS["pegasus"][1]` と実 94a4 artifact から serial 2 を作る |
| `test_env_contract_activation.py::test_serial2_preserves_g1_as_ever_active` | current だけを historical 集合にする誤実装 |
| `test_env_contract_activation.py::test_import_performs_no_activation_or_calibration_io` | 裁定 E/P4 違反 |
| `test_env_contract_activation.py::test_authority_validation_is_cached_once_per_pid` | lookup ごとの再読、thread race、fork 後の誤継承 |
| `test_env_contract_activation.py::test_forged_stale_and_cross_process_receipts_are_rejected` | field 一致だけで手製 receipt を許す実装 |
| `test_env_contract_activation.py::test_issue_cli_parses_before_load_and_writes_create_only` | parse 前 I/O、上書き発行 |
| `test_campaign.py::test_m0_activation_receipt_refusal_precedes_any_sink_write` | guard の receipt assert 欠落・書込み後検査 |
| `test_campaign.py::test_activation_receipt_check_precedes_registry_runtime_site_and_selector_checks` | receipt を既存条件の後ろへ移す誤実装 |
| `test_s8b_ratified_verify.py::test_public_reverify_rejects_registered_never_active_g2_without_current_fallback` | freeze historical lane の過剰受理 |
| `test_s8b_ratified_verify.py::test_public_reverify_accepts_g1_after_real_g2_activation` | historical lane を current-only に縮小 |
| `test_s8b_oracle_report.py::test_build_observations_rejects_registered_never_active_contract` | oracle report の未 active g2 受理 |
| `test_s8b_oracle_report.py::test_build_observations_accepts_ever_active_g1_under_real_g2_current` | oracle report の current fallback |

既存の [test_s8b_floor_campaign.py:4395-4425](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/tests/test_s8b_floor_campaign.py:4395) と [test_s8b_ratified_verify.py:702-725](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/tests/test_s8b_ratified_verify.py:702) は bootstrap-fuse assertion を除去し、activation cache を明示的に扱う fixture へ更新する。

## cache、monkeypatch、pin、凍結 bytes

- activation chain を差し替える各 test は、前後で authority cache を必ず clear する。monkeypatch teardown 後にも temp state が残らない fixture 順を固定する。
- production に cache reset API は出さず、private test helper のみにする。
- [qualification/contract.py:38-66](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/qualification/contract.py:38) の code identity に activation leaf、全 record、calibration verification の実 dependency を追加する。record directory と static set の完全一致 test を置く。
- [silo_ladder_rung1.py:254-272](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/silo_ladder_rung1.py:254) の runtime binding に leaf と全 activation JSON を追加する。
- [t419_probe_causality.py:3491-3541](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/tools/pegasus/probes/t419_probe_causality.py:3491) の dirty scope に leaf と record directory を追加する。
- `ExecutionEnvironmentContract` の field/canonical hash 実装 [env_contract.py:97-160](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/env_contract.py:97) は触らない。
- g1 pin、`floor_protocol.json`、silo evidence、[test_s8b_floor_campaign.py:3253](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/tests/test_s8b_floor_campaign.py:3253) は変更しない。
- process receipt は非永続なので既存 artifact schema/body hash/WAL hashへの波及はゼロ。pin set の変更は将来 run の source identity にだけ反映する。

## 総括

- 判定: **条件付き GO**。P1/P2/P4を採用し、P3だけD228/T-627に従って修正する。
- risk 1: lazy process cache のテスト間汚染と fork/thread 初期化競合。
- risk 2: ever-active 限定による historical 受理集合の意図しない縮小。
- risk 3: activation leaf/record を T126・silo・T419 の identity pin から漏らすこと。
- 単位A: pure leaf、schema、initial record、issuer tool、leaf tests。
- 単位B: g2 registry、lazy current/ever-active/cache、calibration evidence。
- 単位C: execution guard receipt assert と no-write tests。
- 単位D: freeze/oracle historical tests、identity pin 閉包、全静的検査。