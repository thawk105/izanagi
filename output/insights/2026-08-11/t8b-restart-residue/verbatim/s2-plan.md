## 総括

A-1 はそのまま実施可能です。`compilers_for_current_site()` を `build_cells()` ごとに一度だけ解決し、同じ `(cc, cxx)` を source evidence と `build_v2` の双方へ渡します。

A-2 は P4 の一部を修正する必要があります。現行 `BuildResult` には toolchain manifest がありません（[buildcache.py:165](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-residue/orchestrator/campaign/buildcache.py:165)）。一方、`build_v2` の completion manifest には存在し（[buildcache.py:764](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-residue/orchestrator/campaign/buildcache.py:764)）、戻り値組立て関数も同じ値を受け取ったうえで捨てています（[buildcache.py:518](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-residue/orchestrator/campaign/buildcache.py:518)）。したがって、`BuildResult` に additive な `toolchain_manifest` を載せ、床値 driver が呼出し直後に検査するのが最小かつ TOCTOU のない代案です。

親 brief M-6 の「consumer が存在しない」は逐語には refuted です。[silo_ladder_rung1.py:3550](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-residue/orchestrator/campaign/silo_ladder_rung1.py:3550) に raw calibration を読む既存 consumer があります。ただし、床値 `build_v2` manifest と calibration authority を照合する経路がない、という本件の blocker は real です。この所有外 consumer は今回変更しません。

### 編集面の地図

| 所在 | 計画 |
|---|---|
| 新設 `orchestrator/campaign/s8b_floor_toolchain.py:1` | 下記の純粋な authority 導出・manifest 照合を置く。filesystem、env、subprocess は読まない。 |
| [buildcache.py:165](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-residue/orchestrator/campaign/buildcache.py:165) | `BuildResult.toolchain_manifest: Optional[Dict[str, Dict[str, str]]] = None` を末尾に追加。legacy `build()` は `None` のまま。 |
| [buildcache.py:518](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-residue/orchestrator/campaign/buildcache.py:518) | `_v2_result()` が既に受け取る `toolchain` の独立 copy を `BuildResult` へ載せる。fresh/cache-hit は共にこの helper を通る（[buildcache.py:696](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-residue/orchestrator/campaign/buildcache.py:696)、[buildcache.py:795](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-residue/orchestrator/campaign/buildcache.py:795)）。cache key、completion schema、ビルド挙動は変えない。 |
| [s8b_floor_campaign.py:83](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-residue/orchestrator/campaign/s8b_floor_campaign.py:83) | 新 module を import。 |
| [s8b_floor_campaign.py:1059](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-residue/orchestrator/campaign/s8b_floor_campaign.py:1059) | `build_cells(..., contract, toolchain_authority, build_fn=None)` に変更。冒頭で `resolved_cc, resolved_cxx = buildcache.compilers_for_current_site()` を一度だけ呼ぶ。 |
| [s8b_floor_campaign.py:1075](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-residue/orchestrator/campaign/s8b_floor_campaign.py:1075) | `resolve_evidence(cxx=resolved_cxx)`。 |
| [s8b_floor_campaign.py:1089](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-residue/orchestrator/campaign/s8b_floor_campaign.py:1089) | `build_fn(cc=resolved_cc, cxx=resolved_cxx)`。 |
| [s8b_floor_campaign.py:1099](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-residue/orchestrator/campaign/s8b_floor_campaign.py:1099) | contract namespace 検査直後に `result.toolchain_manifest` を authority と照合。欠落、型不正、不一致は cell 記録・計測へ進めない。 |
| [s8b_floor_campaign.py:2850](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-residue/orchestrator/campaign/s8b_floor_campaign.py:2850) | 既存 loader が返した同一 `verified_calibration` から authority を一度だけ導出。新たな calibration 再読込みはしない。 |
| [s8b_floor_campaign.py:3065](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-residue/orchestrator/campaign/s8b_floor_campaign.py:3065)、[同:3119](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-residue/orchestrator/campaign/s8b_floor_campaign.py:3119) | fresh と build-required resume の両 callsiteへ同じ authority を渡す。 |

新 module の署名は次とします。

```python
@dataclass(frozen=True)
class DerivedToolchainAuthority:
    cc_realpath: str
    cxx_realpath: str
    cc_version_first_line: str
    cmake_version_first_line: str

class ToolchainBindingError(RuntimeError):
    ...

def derive_toolchain_authority(
    verified: calibration_verify.VerifiedCalibration,
) -> DerivedToolchainAuthority:
    ...

def assert_toolchain_manifest_matches(
    authority: DerivedToolchainAuthority,
    manifest: object,
) -> None:
    ...
```

`ExecutionEnvironmentContract` は変更しません。field 集合は既存テストが exact 6 件で固定しています（[test_env_contract.py:1050](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-residue/orchestrator/tests/test_env_contract.py:1050)）。Pegasus g1/g2 と linux-baremetal の hash golden（[test_env_contract.py:1108](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-residue/orchestrator/tests/test_env_contract.py:1108)）も変更しません。

## A-2 の検査契約

### Authority の導出

床値 campaign は既に [s8b_floor_campaign.py:2850](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-residue/orchestrator/campaign/s8b_floor_campaign.py:2850) で `env_attestation.load_verified_calibration()` を呼んでいます。同関数は [env_attestation.py:1023](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-residue/orchestrator/campaign/env_attestation.py:1023) から `calibration_verify.load_verified_calibration()` に委譲します。

この loader は以下を済ませます。

- repository-relative path と repo 外 escape の拒否（[calibration_verify.py:91](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-residue/orchestrator/campaign/calibration_verify.py:91)）
- raw bytes の SHA-256 と `calibration_ref.sha256` の完全一致（[calibration_verify.py:105](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-residue/orchestrator/campaign/calibration_verify.py:105)）
- duplicate key を含む exact calibration/v2 schema、env tag、clock、policy の検査（[calibration_verify.py:116](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-residue/orchestrator/campaign/calibration_verify.py:116)）

したがって別 loader は作らず、この戻り値だけを純関数へ渡します。`pegasus_floor_scoping._assert_matches_calibration()` は raw `json.load()` だけで SHA-256 を検査しないため（[pegasus_floor_scoping.py:82](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-residue/orchestrator/campaign/pegasus_floor_scoping.py:82)）、踏襲しません。

純関数は次を行います。

1. `calibration/v2` と typed `CalibrationV2` がなければ拒否する。したがって toolchain authority を持たない grandfathered v1 は床値 build を通さない。
2. `acquisition_receipt.ccbench.build_argv` から、完全一致 prefix の C/CXX compiler tokenをそれぞれ「ちょうど1件」要求する。欠落・重複を拒否する。
3. C の build token と `acquisition_receipt.toolchain.compiler_path` を逐語一致で交差検証する。
4. `compiler_version.splitlines()[0]` と `cmake_version.splitlines()[0]` を authority にする。strip・case folding・basename 化はしない。
5. calibration path を現在ノードで再度 `realpath()` しない。記録 bytes にある acquisition-time realpath 自体が authority だからである。

実 g1/g2 は別計算ノード `bnode011` / `bnode048` で取得されていますが、双方とも C/CXX path が完全一致しています（[g1:3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-residue/output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json:3)、[g1:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-residue/output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json:29)、[g2:3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-residue/output/env/pegasus/calibration/registered/calibration-94a4b79fa31bba3c.json:3)、[g2:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-residue/output/env/pegasus/calibration/registered/calibration-94a4b79fa31bba3c.json:29)）。

同一 package が別ノードで別 realpath になることは一般にはあり得ます。しかし calibration は package ID、compiler binary hash、代替 path の等価関係を持ちません。その場合に version-only へ緩和する根拠はないため、exact realpath 拒否が fail-closed な挙動です。必要なら別 calibration 世代で権威を取り直すべきです。

### Attempt manifest の検査

manifest は top-level exact `{cc,cxx,cmake}`、各 role exact `{requested,realpath,version_first_line}` の非空文字列を要求します。その上で次だけを比較します。

- `cc.realpath`
- `cxx.realpath`
- `cc.version_first_line`
- `cmake.version_first_line`

`cxx.version_first_line` は calibration authority がないため比較しません。`cmake.realpath` も calibration に path がないため比較しません。両 field は manifest の構造としては必須ですが、値の認可判断には使いません。

純関数の不一致は `ToolchainBindingError`。床値境界では cause を保持して `FloorCampaignError` に包みます。

### 逐語例

| 例 | `cc.realpath` | `cxx.realpath` | `cc.version_first_line` | `cmake.version_first_line` | 結果 |
|---|---|---|---|---|---|
| 正例 | `/usr/bin/x86_64-linux-gnu-gcc-11` | `/usr/bin/x86_64-linux-gnu-g++-11` | `gcc (Ubuntu 11.4.0-1ubuntu1~22.04.3) 11.4.0` | `cmake version 3.25.0` | 通過 |
| 負例 1 | `/usr/bin/x86_64-linux-gnu-gcc-11` | `/usr/bin/x86_64-linux-gnu-g++-11` | `gcc (Ubuntu 12.3.0-1ubuntu1~22.04) 12.3.0` | `cmake version 3.25.0` | `FloorCampaignError("floor toolchain binding failed: cc.version_first_line mismatch: expected='gcc (Ubuntu 11.4.0-1ubuntu1~22.04.3) 11.4.0' observed='gcc (Ubuntu 12.3.0-1ubuntu1~22.04) 12.3.0'")` |
| 負例 2 | `/usr/bin/x86_64-linux-gnu-gcc-11` | `/usr/bin/x86_64-linux-gnu-g++-12` | `gcc (Ubuntu 11.4.0-1ubuntu1~22.04.3) 11.4.0` | `cmake version 3.25.0` | `FloorCampaignError("floor toolchain binding failed: cxx.realpath mismatch: expected='/usr/bin/x86_64-linux-gnu-g++-11' observed='/usr/bin/x86_64-linux-gnu-g++-12'")` |

正例の version authority は calibration の複数行文字列（[g1:59](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-residue/output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json:59)）の第1行です。これは `_tool_version()` が返す形（[buildcache.py:199](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-residue/orchestrator/campaign/buildcache.py:199)）と逐語比較できます。

## テスト計画

| 新設 nodeid | 殺す変異 |
|---|---|
| `orchestrator/tests/test_s8b_floor_toolchain.py::test_registered_pegasus_calibrations_derive_exact_authority[g1]` / `[g2]` | build argv でなく basename/default を authority にする、複数行全体を first-line manifest と比較する、CXX flag を読まない変異。 |
| `...::test_derive_rejects_invalid_compiler_flag_cardinality[missing-cxx]` / `[duplicate-cc]` | `next(..., fallback)`、先頭または末尾の曖昧な1件を採る変異。 |
| `...::test_derive_rejects_cc_receipt_cross_mismatch` | build argv と `toolchain.compiler_path` の交差検証を削る変異。 |
| `...::test_manifest_match_accepts_unbound_cxx_version_and_cmake_path` | authority のない CXX version / CMake path まで過剰束縛する変異。 |
| `...::test_manifest_match_rejects_authorized_mismatch[cc-path\|cxx-path\|cc-version\|cmake-version]` | 4 比較のいずれかを欠落させる変異。 |
| `...::test_manifest_match_rejects_missing_or_malformed_manifest` | `None`、欠落 field、余分 field、非文字列を素通りさせる変異。 |
| `orchestrator/tests/test_buildcache_v2.py::test_v2_build_result_exposes_exact_toolchain_manifest_on_fresh_and_hit` | fresh または cache-hit の片方だけ field を返す、configure argv から再構成する、completion と異なる copy を返す変異。 |
| `orchestrator/tests/test_s8b_floor_campaign.py::test_build_cells_forwards_one_site_compiler_pair_to_evidence_and_build` | `DEFAULT_CC/CXX` 残存、evidence/build で別 resolver 結果を使う、cc/cxx を入れ替える変異。 |
| `...::test_floor_toolchain_mismatch_rejected_in_both_modes[pilot]` / `[official]` | gate 自体を削る、official のみ／pilot のみで発火させる変異。official は既存の局所テスト seam だけを使い、production bypass は追加しない。 |
| `...::test_floor_rejects_v1_calibration_without_toolchain_authority` | legacy v1 を `DEFAULT_CC/CXX` や attempt 自己申告で補う変異。 |
| `...::test_floor_derives_authority_from_verified_loader_return_without_reread` | verified object を捨てて raw path を再読する、別 calibration を authority にする変異。 |

既存期待値は変更不要です。必要な fixture の形だけを補います。

- [test_s8b_floor_campaign.py:238](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-residue/orchestrator/tests/test_s8b_floor_campaign.py:238) の fake build に一致する `toolchain_manifest` を追加。
- 同ファイルの synthetic fixture（[test_s8b_floor_campaign.py:127](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-residue/orchestrator/tests/test_s8b_floor_campaign.py:127)）では、legacy calibration を用いる既存の非対象テストを toolchain gate の詳細から隔離するため、純関数を局所 monkeypatch して固定 authority を返す。新しい authority/gate nodeid は実関数へ戻して検査する。
- [test_s8b_materialization.py:429](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-residue/orchestrator/tests/test_s8b_materialization.py:429) の `_FakeBuildResult` に manifest を追加し、[同:494](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-residue/orchestrator/tests/test_s8b_materialization.py:494) の直接 `build_cells()` 呼出しへ synthetic authority を渡す。portable manifest golden は変えない。
- `BuildResult` の既存直接構築（[test_campaign.py:9314](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-residue/orchestrator/tests/test_campaign.py:9314)、[test_s8b_oracle_driver.py:2668](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-residue/orchestrator/tests/test_s8b_oracle_driver.py:2668)）は default `None` により変更不要。
- 既存 `test_required_calibration_sha_mismatch_has_zero_side_effects`（[test_s8b_floor_campaign.py:1397](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-residue/orchestrator/tests/test_s8b_floor_campaign.py:1397)）の期待値は維持し、SHA 不一致が authority 導出前に拒否されることを引き続き担わせる。

## (P1)〜(P4) の採否

- **P1: refuted（修正版を採用）。** cc/cxx realpath と cc first-line は採用。CMake は calibration の複数行 full string と manifest の first-line をそのまま比較できないので、`cmake_version.splitlines()[0]` の逐語一致へ修正する。CXX version と CMake path は非束縛。
- **P2: real。** C/CXX build flag を各1件要求し、C は `toolchain.compiler_path` と交差検証する。ただし calibration path を現在ノードで再 realpath せず、記録された acquisition-time path を authority にする。
- **P3: real。** `build_cells()` 自体で照合すれば pilot/official に mode 分岐を作らず両方へ発火する。pilot は別 toolchain 実験用ではなく、同一 node class/toolchain/pin で費用・動作を校正する位置付けです（[floor protocol consultations:228](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-residue/output/insights/2026-07-16_s8b-floor-protocol-consultations.md:228)）。別 toolchain 試行が必要なら floor pilot を緩めず、別の非床値経路に分ける。
- **P4: refuted。** 「build 直後」は採用するが、「buildcache 無変更」は不可能。戻り値に manifest がないため、completion file の private schema を再読したり toolchain を再 probe したりせず、`BuildResult` の additive field として同じ in-memory manifest を返す。cache identity・completion bytes・legacy API は変えない。

## 波及

- `build_cells()` の production caller は同 module の fresh/resume-build 2 箇所だけです。所有外の直接 caller は [test_s8b_materialization.py:494](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-residue/orchestrator/tests/test_s8b_materialization.py:494) の golden test 1件です。
- `BuildResult` は pipeline/oracle 等にも共有されますが、新 field は default `None`、床値だけが消費します。legacy `build()` や oracle の受理意味論は変えません。
- portable floor artifact の key 集合（[s8b_floor_campaign.py:172](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-residue/orchestrator/campaign/s8b_floor_campaign.py:172)）と downstream consumer（[s8b_ratified_freeze.py:181](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-residue/orchestrator/campaign/s8b_ratified_freeze.py:181)）へ manifest を永続化しないため、artifact schema・consumer test は不変です。
- legacy `linux-baremetal` calibration/v1 には toolchain authority がありません。production floor build は新たに fail-closed で拒否されます。これを温存するには SHA-bound な v2 calibration が必要ですが、現 wave で contract ref を差し替えると hash/pin 不変条件を破るため代案にしません。
- `FROZEN_MANIFEST` 23 件（[test_frozen_artifacts.py:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-residue/orchestrator/tests/test_frozen_artifacts.py:38)）と exact 件数検査（[同:139](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-residue/orchestrator/tests/test_frozen_artifacts.py:139)）は変更しません。[floor_protocol.json:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-residue/output/s8b-freeze/floor_protocol.json:1) の `contract_sha256`、`ccbench_pin`、`freeze` も不変です。
- `_assert_official_permitted`（[s8b_floor_campaign.py:207](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-residue/orchestrator/campaign/s8b_floor_campaign.py:207)）と shell の `--mode official`（[floor_campaign.sh:961](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t8b-restart-residue/tools/pegasus/floor_campaign.sh:961)）は一切変更しません。
- B/C の docs は編集対象外です。

read-only の静的検査だけを行いました。calibration g1/g2 の SHA-256 は contract literal と一致することを `sha256sum` で確認しましたが、pytest は実走しておらず、緑は確認していません。