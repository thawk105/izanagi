以下の「実測」は静的読解・ファイル SHA-256 計算だけを指す。pytest、build、実行確認はしておらず、緑は主張しない。親 brief は `/home/SFC/tanab/.claude/jobs/70fa1240/tmp/wave-t342-344/s1-brief.md` と略記する。

## 1. 現行の受理・拒否挙動

前提として、現行 `BuildAdmission` は caller が class と receipt の有無を直接構築できる自己申告型である（`orchestrator/campaign/build_admission.py:29-42,45-62`、`docs/decisions.md:6241-6256`）。

| identity 面 | 変更前の実測挙動 |
|---|---|
| legacy cache key | `BuildAdmission` 型であれば入口は通るが、key に admission がないため、異なる申告 class が同じ entry を共有できる（`orchestrator/campaign/buildcache.py:122-136,672-747`）。 |
| v2 preimage | build 前に admission の型検査はあるが、identity preimage に admission がなく、同じ genome/source/toolchain は同じ digest になる（`orchestrator/campaign/buildcache.py:465-489,534-537`）。 |
| completion manifest | exact-key 検査はあるが admission receipt が key 集合に含まれず、receipt のない旧 manifest も現行 schema として受理される（`orchestrator/campaign/buildcache.py:276-336,555-570,635-646`）。 |
| campaign preimage/replay | canonical preimage に admission がなく、campaign ID/lock は class 非依存。terminal stage は source/admission の再検証より先に skip でき、receipt のない WAL も再利用される（`orchestrator/campaign/ident.py:76-103`、`orchestrator/campaign/loop.py:145-167,169-213`）。 |

## 2. 公開 API の確定案

### 2.1 型と signature

段4で以下を凍結する。`BuildAdmission` と関連 capability は `init=False` の sealed frozen object とし、production caller に直接 constructor を公開しない。

```python
# orchestrator/campaign/source_digest.py

@dataclass(frozen=True)
class SourceEvidence:
    schema_version: str
    ccbench_commit: str
    genome_sha256: str
    src_token: str
    source_bytes_sha256: str
    tracked_clean: bool
    tracked_diff_sha256: str
    tracked_paths: tuple[str, ...]

def resolve_evidence(
    genome: Genome,
    ccbench_commit: str,
    *,
    ccbench_dir: str = "",
    cxx: str = "g++-13",
) -> SourceEvidence
```

```python
# orchestrator/campaign/build_admission.py

class BuildProvenance(StrEnum):
    STOCK_BASELINE = "stock-baseline"
    CODER_AUTHORED = "coder-authored"
    MACHINE_GENERATED = "machine-generated"
    HUMAN_REVIEWED = "human-reviewed"

class GeneratorId(StrEnum): ...
class ReviewId(StrEnum): ...

@dataclass(frozen=True, init=False)
class CoderBuildAuthority: ...

@dataclass(frozen=True, init=False)
class BuildAdmissionPolicy:
    def as_preimage(self) -> Mapping[str, object]: ...

@dataclass(frozen=True, init=False)
class BuildRunContext:
    @property
    def policy(self) -> BuildAdmissionPolicy: ...

@dataclass(frozen=True, init=False)
class GeneratorReceipt: ...

@dataclass(frozen=True, init=False)
class ReviewReceipt: ...

@dataclass(frozen=True, init=False)
class BuildAdmission:
    @property
    def provenance(self) -> BuildProvenance: ...
    def as_cache_identity(self) -> Mapping[str, object]: ...
    def as_wal_receipt(self) -> Mapping[str, object]: ...

def add_coder_build_authority_argument(
    parser: argparse.ArgumentParser,
    *,
    dest: str = "coder_build_authority",
) -> None: ...

def build_run_context(
    *,
    generator_id: GeneratorId,
    coder_authority: CoderBuildAuthority | None = None,
) -> BuildRunContext: ...

def attest_generator_output(
    context: BuildRunContext,
    source: SourceEvidence,
    *,
    generator_input_sha256: str,
) -> GeneratorReceipt: ...

def verify_review_receipt(
    review_id: ReviewId,
    source: SourceEvidence,
    *,
    receipt: Mapping[str, object],
) -> ReviewReceipt: ...

def derive_build_admission(
    context: BuildRunContext,
    source: SourceEvidence,
    *,
    generator_receipt: GeneratorReceipt | None = None,
    review_receipt: ReviewReceipt | None = None,
) -> BuildAdmission: ...

def require_build_admission(
    value: object,
    *,
    expected_policy: BuildAdmissionPolicy,
    expected_source: SourceEvidence,
) -> BuildAdmission: ...

def validate_build_admission_receipt(
    value: object,
    *,
    expected_policy: BuildAdmissionPolicy,
    expected_source: SourceEvidence | None = None,
) -> Mapping[str, object]: ...
```

`GeneratorId` は production entry point ごとの閉じた enum とし、registry が module path と実ファイル digest を決める。caller が自由文字列の generator 名や class を渡す API は作らない。

### 2.2 class 導出規則

`derive_build_admission()` は次の順序を固定する。

1. `src_token == STOCK` かつ `tracked_clean is True` なら `STOCK_BASELINE`。
2. exact-schema、既知 `ReviewId`、対象 `source_bytes_sha256` が一致する review receipt があれば `HUMAN_REVIEWED`。
3. registered generator、generator input、実 source digest が一致する generator receipt があれば `MACHINE_GENERATED`。
4. 上記に該当せず、同一 `BuildRunContext` の parser-issued token があれば `CODER_AUTHORED`。
5. それ以外、または generator/review receipt が同時に与えられた曖昧系は拒否。

`AuditorVerdict` は diff の一致を確認するだけで human review/security boundary ではないため、`ReviewReceipt` へ変換しない（`orchestrator/campaign/auditor_gate.py:29-75`、`docs/decisions.md:6263-6267`）。

### 2.3 CLI authority

`add_coder_build_authority_argument()` の private `argparse.Action` だけが `CoderBuildAuthority` を発行する。現行の `store_true` は廃止し、`True`、偽 dataclass、別 run の token を `require_build_admission()` が exact type/seal/context で拒否する。

token の乱数 nonce はメモリ内だけに保持する。cache/WAL/campaign policy には安定射影である `{"kind": "cli-opt-in"}` と policy SHA を記録し、nonce は永続化しない。これにより、再起動後も新しい CLI token を持つ同一 policy で正規 resume できる。

### 2.4 receipt の正規形

cache/WAL 共通の receipt は exact-key map とする。

```json
{
  "schema": "build-admission/v1",
  "class": "...",
  "policy_sha256": "...",
  "source": {
    "ccbench_commit": "...",
    "genome_sha256": "...",
    "src_token": "...",
    "source_bytes_sha256": "...",
    "tracked_clean": true,
    "tracked_diff_sha256": "...",
    "tracked_paths": []
  },
  "generator_receipt_sha256": null,
  "review_receipt_sha256": null,
  "authority_kind": null,
  "receipt_sha256": "..."
}
```

未知 key、欠落 key、class と evidence の不整合、outer SHA の不一致をすべて拒否する。

現行 `assert_worktree_within_allowlist()` は allowlist 外の tracked change だけを拒否し、allowlist 内が dirty かどうかを返していない（`orchestrator/campaign/source_digest.py:662-699`）。これを source capability の clean 証明として直接流用してはならない。

## 3. file:line 粒度の変更計画

### 3.1 capability・cache・campaign の中核

- `orchestrator/campaign/build_admission.py:1-71`
  - 現行の公開 constructor、bool receipt、caller-supplied class を置換する。
  - §2 の sealed types、closed generator/reviewer registry、parser action、class 導出、receipt canonicalization/validation を実装する。
  - `BuildAdmission(BuildProvenance.X, ...)` は production から呼べなくする。

- `orchestrator/campaign/source_digest.py:541-659`
  - `compute()`、`baseline()`、`src_token()` の結果を `SourceEvidence` 構築へ統合する。
  - genome canonical SHA、実 source bytes SHA、normalized `src_token` を同じ snapshot から作る。
  - 非 build consumer 向けの `resolve(): str` は compatibility wrapper として残す。

- `orchestrator/campaign/source_digest.py:662-713`
  - `git diff --binary HEAD` により staged/unstaged を含む tracked diff と path 集合を canonicalizeする。
  - allowlist 外変更は従来どおり拒否し、同時に `tracked_clean` と diff SHA を返す。
  - 新しい build 経路は `resolve_evidence()` のみを使う。
  - build/cache hit の直前と直後で evidence 全体を再取得し、token だけが同じ dirty no-op も TOCTOU として拒否する。現行 token-only recheck は `buildcache.py:750-777`。

- `orchestrator/campaign/buildcache.py:122-136,672-747`
  - legacy `cache_key()` に admission receipt digest を全 class で無条件追加する。
  - legacy entry に exact-schema の admission sidecar を追加し、hit 時に欠落・不一致なら拒否する。旧 namespace を探索する fallback は作らない。
  - fresh build は一時 entry で executable と sidecar を完成させてから publish する。

- `orchestrator/campaign/buildcache.py:220-238,465-646`
  - v2 preimage に `build_admission.as_cache_identity()` を必須 key として追加する。
  - completion manifest schema を更新し、同じ admission map を top-level 必須 field にする。
  - preimage、manifest、現在の `SourceEvidence` の三者を exact equality で照合する。
  - `_recheck_src_token()` は `_recheck_source_evidence()` に置換する。

- `orchestrator/campaign/ident.py:76-103`
  - `search_config["build_admission"] = context.policy.as_preimage()` を canonical preimage の必須部分にする。
  - ID と lock が同じ preimage を使う現行構造を維持する。別の「ID に入らない admission lock」は作らない。

- `orchestrator/campaign/ident.py:114-175`
  - lock の exact-key 検査に admission policy を含める。
  - resume 時は現 run context の policy SHA と lock の policy SHA を比較し、欠落・不一致を拒否する。

- `orchestrator/campaign/pipeline.py:48-54`
  - `variant_id` 自体は変えない。campaign policy と attempt receipt が replay binding を担う。

- `orchestrator/campaign/pipeline.py:422-478,529-610`
  - `evaluate()` は scalar の自己申告 `BuildAdmission` ではなく `BuildRunContext` と sealed generator/review capability を受ける。
  - source 解決後に `derive_build_admission()` を呼び、cache/build 境界で `require_build_admission()` を再検証する。
  - source evidence と admission receipt を同じ build attempt に固定する。

- `orchestrator/campaign/pipeline.py:560-564`
  - `BUILD_START` に `build_attempt_id` と exact `build_admission` receipt を記録する。
  - `BUILD_DONE`、`COMMIT` にも同じ attempt ID/receipt SHA を伝播する。
  - source 解決前に止まった identity/pre-build error は receipt なしを許すが、その attempt から `BUILD_DONE`/`COMMIT` が存在したら拒否する。

- `orchestrator/campaign/loop.py:94-122`
  - `run()` に `BuildRunContext` と source ごとの sealed capability resolver を渡す。
  - admission policy を config に入れてから campaign ID/lock を決める。

- `orchestrator/campaign/loop.py:131-213`
  - terminal skip より前に lock policy、overlay、WAL attempt receipt、現在の source evidence を検証する。
  - receipt 欠落/mismatch は「再実行可能な miss」にせず identity error にする。既存 WAL を上書きして正当化しない。

- `orchestrator/campaign/loop.py:221-226`
  - `evaluate()` へ context、source evidence、sealed capability を渡す。

- `orchestrator/campaign/model.py:112-150`、`orchestrator/campaign/wal.py:566-601`
  - replay state に attempt ID、receipt SHA、policy SHA を保持する。
  - 現行の stage ごとの last-record 集約だけでなく、`BUILD_START → BUILD_DONE → COMMIT` を attempt ID 単位で検証する。

- `orchestrator/campaign/screening_driver.py:130-156`
  - scalar admission の透過渡しを context/capability 渡しへ変更する。

### 3.2 全 direct caller の配線

各行の直接 constructor を廃止する。stock も定数 capability を渡さず、必ず実 `SourceEvidence` から導出する。

| caller | 現行箇所 | 新しい配線 |
|---|---:|---|
| `backoff_overthrottle.py` | `:71` | registered `BACKOFF_OVERTHROTTLE` generator receipt |
| `backoff_profile.py` | `:136` | registered `BACKOFF_PROFILE` generator receipt |
| `backoff_repro.py` | `:99` | registered `BACKOFF_REPRO` generator receipt |
| `backoff_sweep.py` | `:39,94,109,150` | run context と per-source generator receipt |
| `between_run_floor.py` | `:162` | clean + `STOCK` から自動導出 |
| `demo.py` | `:52,60` | 両方とも実 source evidence から stock 導出 |
| `p2_2.py` | `:139` | clean stock 導出 |
| `p3_kickoff.py` | `:87-107` | parser token、同一 context で coder/stock を evidence から分岐 |
| `p3_s4_red.py` | `:128-157` | parser token、coder/stock を evidence から分岐 |
| `p3_s4_loop.py` | `:633-678,798-817,848-878` | token を ID 計算前に context 化し、loop へ渡す |
| `p3_s4_loop_sort.py` | `:135-162,207-243,363-456` | parser token。auditor verdict は advisory metadata のまま |
| `p3_s4_loop_trigger_gating.py` | `:357-401,458-497,683-786` | parser token。auditor verdict を human receipt に昇格しない |
| `s1_direct_comparison.py` | `:38,479-552,757` | pinned measurement/source pair を検証する `ReviewId.S1_KNOWN_AXES` receipt |
| `s1_verify_extime_calibration.py` | `:343` | registered calibration generator receipt |
| `s2_verify_calibration.py` | `:297` | clean stock 導出 |
| `s3_lock_coverage.py` | `:190` | clean stock 導出 |
| `s5_permutation_coverage.py` | `:186` | clean stock 導出 |
| `s6_sort_sweep.py` | `:164-205,210-297` | stock は自動導出、sweep は registered generator receipt |
| `s8a_trigger_sweep.py` | `:204-249` | stock は自動導出、sweep は registered generator receipt |
| `s8b_floor_campaign.py` | `:963-984,978` | verified floor binding を human review receipt に変換 |
| `s8b_oracle_driver.py` | `:59,963-995,1355` | ratified oracle manifest/binding を human review receipt に変換 |
| `sanity_silo.py` | `:53` | clean stock 導出 |
| `qualification/t126_driver.py` | `:27-31,513-542` | live `SourceEvidence` から stock 導出し、full digest と `src_token` を混同しない |

特に5本の CLI はすべて `add_coder_build_authority_argument()` を使う。`p3_kickoff.py:124-153` の dirty no-op を「stock/cache hit」とみなす分岐は削除し、dirty なら coder token を要求して新しい admission namespace に入れる。

### 3.3 campaign overlay と consumer

新規 `orchestrator/campaign/legacy_admission_overlay_v1.json:1` に以下3 recordだけを置く。凍結 campaign 配下は変更しない。

| campaign | lock SHA-256 | WAL SHA-256 | build_start |
|---|---|---|---:|
| `p3-s4-loop-s4-autonomous-0b53a387` | `0b53a3876589a61ae35b318237751015acebb3761e612e4374f9944ffca7f7c9` | `2163b794fa3b1fce4de76a1b69262cadfc095bd986225a7266d6eacb6210a611` | 3 |
| `p3-s5-sort-loop-s5-sort-autonomous-3be89e0d` | `3be89e0ddad8e8b2b37d35168c49affe7889ea580831973dc0d6d9706aaa4f97` | `b901f23a502e4d3843454de807ca01666c145ee7d9d424a957bb366ef3e793a5` | 1 |
| `p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5` | `3f72ecd58a6df4018d136bcbb8abb276114ba8d302c64aaf792c473ae4b1de0c` | `a539648d29afce9be036eba519b53f21fd1f8e1fb7bfe24549f4ec3ceac31ea3` | 2 |

これは brief の実測件数（`s1-brief.md:34-40`）と各 `runs/wal.jsonl` の静的 SHA 計算結果である。各 record は path、campaign ID、lock SHA、WAL SHA、build count、`classification: "legacy-unclassified"` を exact schema で持つ。

- 新規 `orchestrator/campaign/artifact_admission.py:1`
  - `classify_campaign()` と `require_admitted_campaign()` を実装する。
  - overlay に一致した artifact は admission-aware consumer で必ず拒否する。
  - 既知 ID/path なのに lock/WAL SHA や count が違えば改変エラーとし、通常 artifact へ fall through させない。
  - overlay 非掲載でも、完了 attempt に exact receipt がなければ拒否する。overlay を3件だけの denylistにはしない。

- `orchestrator/campaign/layer3_report.py:346-428`
  - lock/WAL を展開する前に shared validator を呼ぶ。
  - receipt のない旧 S8a campaign を report 生成対象にしない。

- `orchestrator/critic/digest.py:192-219,446-452`
  - workload/bench を読む共通入口で validator を一度だけ呼ぶ。
  - committed という理由だけで旧 workload を選ばない。

- `orchestrator/campaign/s6_sort_sweep.py:372-434`
  - `COMMIT` の有無だけで certified とする判定を、attempt receipt + policy + source evidence の一致へ変更する。

- `orchestrator/campaign/s8a_trigger_sweep.py:418-483`
  - S6 と同じ admission-aware certified 判定へ変更する。

- `orchestrator/campaign/autonomous_trial_completeness.py:879-999`
  - fresh layer3 経路は validator を継承する。
  - persisted report を直接比較する経路にも明示 guard を置く。

- `orchestrator/campaign/backoff_sweep_report.py:35-44`
  - critic loader の guard を必須化し、raw bypass を作らない。

### 3.4 qualification と独自 identity

- `orchestrator/qualification/artifacts.py:797-841`
  - `select_source_pair()` で lock/WAL pin に加えて `require_admitted_campaign()` を実行する。

- `orchestrator/qualification/artifacts.py:844-960`
  - 現在実質未使用の先頭 `BUILD_START` payload を decodeし、member source、attempt、admission receipt を照合する。

- `orchestrator/qualification/contract.py:38-66`
  - `artifact_admission.py` と overlay ledger を code identity path に追加する。

- `orchestrator/qualification/contract.py:454-549`
  - series identity の exact key に `build_admission_policy` を追加する。

- `orchestrator/qualification/t126_driver.py:387-426`
  - series preimage/schema に policy を追加するため series ID は更新する。

- `orchestrator/qualification/t126_driver.py:513-542`
  - `source_bytes_sha256` は member identity、normalized `src_token` は build/cache identity に分離する。
  - stock class は `SourceEvidence` から導出する。

- `orchestrator/qualification/t126_driver.py:861-907,1254-1286`
  - source pair 選択、submission identity、recorded identity のすべてで新 policy を exact 比較する。

- `orchestrator/qualification/identity.py:112-204`
  - Git/blob 再導出に admission policy と overlay reader identity を含める。

- `orchestrator/qualification/submission.py:167-173`
  - 新 series preimage を immutable identity file に保存する。

- `orchestrator/qualification/collector.py:355-390,460-512,1165-1208,1478-1516`
  - submission、attempt、result、collection の各再計算で同じ policy key を検証する。

- `orchestrator/campaign/s8b_oracle_manifest.py:659-675`
  - oracle campaign preimage に admission policy を追加する。

- `orchestrator/campaign/s8b_oracle_driver.py:963-995`
  - custom campaign lock にも同じ policy を入れ、generic campaign と同じ規則にする。

- `orchestrator/campaign/s8b_floor_campaign.py:963-984`、`s8b_materialization.py:49-86`
  - human receipt、materialization binding、campaign preimage を相互に SHA 束縛する。

編集禁止対象は明示的に所有外とする。

- `orchestrator/campaign/s1_known_axes_freeze.py` は無編集。
- 23個の凍結 manifest/campaign bytes は無編集。
- brief が列挙する4本の既存 source-pin drift は修正しない（`s1-brief.md:15-32`）。

## 4. 後方互換の扱い

| 面 | 変更 | 旧 artifact |
|---|---|---|
| legacy cache key | **全 class で変わる** | 旧 key は探索しない。新 key 下へコピーされても admission sidecar 欠落で拒否。 |
| v2 preimage/digest | **全 class で変わる** | 旧 digest は到達不能。旧 manifest を新 digest 下へコピーしても必須 receipt 欠落で拒否。 |
| completion manifest | **schema/key 集合が変わる** | receipt 欠落・未知 schema は hard reject。migration/fallback なし。 |
| campaign canonical preimage/ID | **全 campaign で変わる** | 旧 directory は自動 resume されない。明示 path consumer でも overlay/positive validator が拒否。 |
| `variant_id` | 変えない | campaign policy と attempt receipt が上位 identity を担う。 |
| T126 series ID、S8b custom campaign ID | **変わる** | 旧 identity は admission 欠落として継続利用しない。 |

正当な運用の受理集合は次の形で維持する。

- clean + `STOCK` の baseline は token 不要で通る。ただし新 cache/campaign namespaceを一度構築する。
- registered generator が実 source に束縛した receipt を出す machine sweep は通る。
- 5本の coder driver は `--allow-coder-derived-build` が発行した token を持てば通る。
- pinned review materialと実 sourceが一致する S1/S8b human-reviewed 経路は通る。
- dirty coder を flag なしで通す経路、任意文字列 generator、receiptless legacy artifact は通さない。

provisional への判断は以下。

- **P3には反対。** stock だけ admission digest を key から除外すると、receipt のない旧 stock cache が引き続き受理され、T-343の「旧 entry は拒否」と矛盾する。legacy key は stock を含め無条件変更が必要（`buildcache.py:122-136`）。
- **P4は方向には賛成、記述は不十分。** preimage変更だけでは旧 entry は単に見えなくなるだけで、コピーされた旧 entry の欠落 receipt を検出できない。legacy sidecarとv2 completion manifestの両方に exact receipt validation が必要。
- **P5には反対。** 現行 `canonical_preimage()` はそのまま campaign ID の材料である（`ident.py:76-103`）。admission を preimage に束縛しつつIDを維持するのは、IDとlockを別 identityに分裂させる。campaign IDを変えるべきである。

また、現行 T126 control は receipt のない旧 P2-2 campaignを pinしている（`orchestrator/qualification/t126_control_v1.json:16-20`）。これは新 validator で意図的に拒否される。migration は作らず、親が新しい admitted P2-2 sourceを実測して新 protocol/pin を作る必要がある。

## 5. テスト計画

すべて nodeid 候補であり、ここでは実行していない。

| nodeid 候補 | 塞いだ迂回路の証拠 |
|---|---|
| `test_build_admission.py::test_stock_requires_stock_token_and_tracked_clean` | `STOCK` tokenだけの自己申告では stock にならない。 |
| `test_build_admission.py::test_dirty_noop_stock_digest_derives_coder` | source digestがstockと同じでもdirtyならstock cacheへ入れない。 |
| `test_build_admission.py::test_registered_generator_receipt_derives_machine` | callerのenum指定ではなく、source-bound receiptだけがmachineになる。 |
| `test_build_admission.py::test_auditor_verdict_cannot_be_review_receipt` | AI auditorをhuman reviewへ昇格する迂回路を塞ぐ。 |
| `test_build_admission.py::test_review_receipt_is_exactly_source_bound` | 別sourceのreview receipt再利用を拒否する。 |
| `test_build_admission.py::test_coder_requires_parser_issued_run_token` | `True`、偽 object、別run tokenを拒否する。 |
| `test_build_admission.py::test_cli_nonce_is_not_serialized` | nonce固定・漏洩を避けつつ新process resumeを可能にする。 |
| `test_build_admission.py::test_source_evidence_toctou_is_rejected` | key計算後のdirty no-op/source差替えを塞ぐ。 |
| `test_build_admission_callers.py::test_no_production_direct_build_admission_constructor` | 23 direct callerの配線漏れを静的に検出する。 |
| `test_buildcache_v2.py::test_legacy_key_binds_admission_for_stock_and_nonstock` | P3型のstock例外を作れないことを示す。 |
| `test_buildcache_v2.py::test_legacy_hit_requires_exact_admission_sidecar` | receiptless旧legacy entryのコピー受理を塞ぐ。 |
| `test_buildcache_v2.py::test_v2_preimage_binds_exact_admission` | class/policy/source receipt差でdigestが変わる。 |
| `test_buildcache_v2.py::test_completion_manifest_rejects_missing_or_mutated_receipt` | preimageだけ合わせた旧manifest再利用を塞ぐ。 |
| `test_campaign.py::test_campaign_id_changes_with_admission_policy` | campaign preimageへの束縛を確認する。 |
| `test_campaign.py::test_resume_rejects_committed_stage_without_receipt` | 現行のreceiptless terminal skipを塞ぐ。 |
| `test_campaign.py::test_resume_rejects_mismatched_attempt_receipt` | 別source/classのreceipt replayを塞ぐ。 |
| `test_campaign.py::test_resume_accepts_exact_receipt_with_fresh_cli_token` | coder driverの正当な再起動resumeを維持する。 |
| `test_campaign.py::test_prebuild_rejection_may_lack_receipt_but_cannot_commit` | すべてのBUILD_STARTへreceiptを要求してprebuild errorを壊さず、後続commit偽装は拒否する。 |
| `test_artifact_admission.py::test_actual_three_legacy_campaigns_are_classified_unclassified` | overlayのID・lock・WAL・件数を実bytesに固定する。 |
| `test_artifact_admission.py::test_overlay_hash_mismatch_fails_closed` | 同名campaign差替えのfall-throughを塞ぐ。 |
| `test_artifact_admission.py::test_unlisted_receiptless_campaign_is_rejected` | 3件denylistだけで済ませる迂回路を塞ぐ。 |
| `test_layer3_report.py::test_real_legacy_s8a_campaign_is_rejected` | 旧S8aから新しいadmission-aware reportを作れない。 |
| `test_critic_digest.py::test_receiptless_committed_workload_is_rejected` | commit-only critic選択を塞ぐ。 |
| `test_s6_sort_sweep.py::test_certified_requires_exact_attempt_receipt` | S6のcommit-only certified判定を塞ぐ。 |
| `test_s8a_trigger_sweep.py::test_certified_requires_exact_attempt_receipt` | S8aの同じ迂回路を塞ぐ。 |
| `test_t126_qualification_artifacts.py::test_current_pinned_p2_2_source_is_rejected` | overlay未掲載の旧qualification artifactもfail closedになる。 |
| `test_t126_qualification_artifacts.py::test_admitted_source_pair_is_accepted` | 新しいclean stock qualification運用が通る。 |
| `test_t126_qualification_driver.py::test_series_identity_binds_admission_policy` | submission/collector間でpolicyを差し替えられない。 |
| `test_p3_build_authority_cli.py::test_all_five_drivers_issue_opaque_authority` | 5 CLIの一部だけboolのまま残る配線漏れを塞ぐ。 |
| `test_p3_build_authority_cli.py::test_stock_machine_and_opted_in_coder_paths_remain_accepted` | stock baseline、machine sweep、opt-in coderの正当運用をまとめて保持する。 |

変更が必要な既存期待値：

- `test_campaign.py:4858-4902` のreceiptなしCOMMIT resume成功期待は、まさにT-343の迂回路なので拒否期待へ変える。
- `test_layer3_report.py:20,54-72` の実S8a旧campaign render成功期待は、T-344により `legacy-unclassified` 拒否へ変える。
- `test_buildcache_v2.py:511-533` の admissionなし exact preimage/manifest期待は、新identity schemaでは誤り。
- `test_campaign.py:1431-1581` と `test_build_admission.py:1-74` の直接constructor前提は、capability factory/derivation前提へ変更する。
- `p3_kickoff.py:124-153` 対応テストのdirty no-op stock/cache-hit期待は、tracked-clean要件に反するため coder/new namespace期待へ変える。
- qualification fixtureのreceiptなし `BUILD_START`（`test_t126_qualification_artifacts.py:178-213`）は、positive fixtureへreceiptを追加する。欠落版はnegative testとして残す。

## 6. 実装単位の分割案

編集所有を次の素集合にする。

1. **API/source capability**
   - `build_admission.py`、`source_digest.py`
   - `test_build_admission.py`、新規 `test_build_admission_callers.py`
   - 最初に実装し、§2のAPIを凍結する。

2. **generic cache/campaign identity**
   - `buildcache.py`、`ident.py`、`pipeline.py`、`loop.py`、`model.py`、`wal.py`、`screening_driver.py`
   - `test_buildcache_v2.py`、`test_campaign.py`、screening tests
   - 単位1に依存。

3. **通常 caller/CLI**
   - §3.2のうちS6/S8a/S8b/qualificationを除くproduction caller
   - 新規 `test_p3_build_authority_cli.py` と各driver固有test
   - 単位1・2に依存。

4. **overlay・通常 consumer・certification**
   - 新規 `artifact_admission.py`、`legacy_admission_overlay_v1.json`
   - `layer3_report.py`、`critic/digest.py`、`s6_sort_sweep.py`、`s8a_trigger_sweep.py`、`autonomous_trial_completeness.py`、`backoff_sweep_report.py`
   - 新規 `test_artifact_admission.py` と各consumer/sweep test
   - 単位1・2に依存。

5. **S8b・qualification特殊identity**
   - §3.4のS8b/qualification全ファイル
   - `test_t126_*`、`test_s8b_*`
   - 単位1・2・4に依存。

依存順は `1 → 2 → (3 と 4) → 5`。単位間で同じファイルを編集しない。

親が行うことは別扱いとする。

- `docs/decisions.md` D127、phase doc、worklog/handoffの更新。実装子はdocsを編集しない。
- 新しい admitted P2-2 sourceの実測と新T126 protocol/pinの確定。
- 計算ノードで関連pytestを実測し、その後 repository checker、commit、provenance監査を行う。
- 凍結bytes、`s1_known_axes_freeze.py`、既存4 source-pin driftは変更しない。

## 7. 親 brief への反論

- **P1は不足。** `src_token == STOCK` と tracked-clean はstockの必要十分条件にはできるが、現行allowlist関数はcleanを証明していない（`source_digest.py:662-699`）。またmachine/human/coderの優先順位、receiptのsource binding、曖昧receipt拒否が未定義である。

- **P2は安全境界としては過大評価。** parser-only tokenは事故防止には有効だが、同一Python process内の悪意あるコードがparser/factoryを呼ぶこと自体は防げない。さらにrun nonceをWALへ永続化すると正常resumeが不可能になるため、永続identityには安定したauthority-kindだけを入れる必要がある。

- **P3は誤り。** non-stockだけkeyを変えるとreceiptless旧stock entryが残る。T-343の「旧entry拒否」と両立しない。

- **P4は穴がある。** digest変更だけでは旧entryに検査が到達しないため、「拒否した」証拠にならない。旧entryを新namespaceへコピーするケースをmanifest/legacy sidecarで明示拒否する必要がある。

- **P5は実現不能。** 現行campaign IDはcanonical preimageそのものから導出される（`ident.py:76-103`）。preimageへadmissionを入れながらIDを保つ案はdual identityになる。またreceiptを全 `BUILD_START` に必須化すると、source解決前の正当なpre-build rejectionを壊す。必須なのは完了・commitへ到達したattemptである。

- **P6はfail-open。** 3件overlayだけを既定除外にすると、未掲載のreceiptless artifactが通る。現行T126のP2-2 pinが具体例である（`t126_control_v1.json:16-20`）。overlayにはpathとlock SHAも必要で、さらに全consumerでpositive receipt validationが必要である。

## 総括

- build class はcallerのenumではなく、`SourceEvidence`、registered generator、verified review、parser-issued tokenから一意に導出する。
- legacy/v2/campaignの全identityへadmissionを例外なく束縛する。したがってstockを含むcache keyとcampaign IDは変える。
- 旧3campaignは外部overlayで `legacy-unclassified` とし、同時にoverlay非掲載artifactにもpositive receipt検査を課す。

最も危険な残存迂回路は、shared readerを経由せず frozen report/WALを直接読む新consumerである。現在確認できた直接・間接consumerは配線対象に含めるが、将来のraw readを防ぐ静的テストも維持する必要がある。