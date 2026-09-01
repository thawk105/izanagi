## 発火路の判定

結論は「現行 production 閉包には、根クラス 2 の path を作成 job の外で再解決する発火路はない」です。親の測定は狭い意味では正しいですが、理由は `dependency_prefix` だけではありません。

直接の呼び手は次の 4 箇所です。

1. `s8b_compiler_input.py:1090-1096`
   - `collect_compiler_input_manifest()` 内の自己検証。
   - production の collection は `buildcache.py:1393-1440` からだけ呼ばれ、それも `buildcache.py:2621-2630` の fresh build 内だけです。

2. `buildcache.py:2637-2646`
   - fresh build の再検証。
   - build 完了直後、`_discard_build_dir(staging)` の `buildcache.py:2765` より前です。根クラス 2 は staging 外なので生存中です。

3. `buildcache.py:1694-1705`
   - `_validate_v2_entry()` の cache-hit 検証。
   - `_validate_v2_entry()` の production 呼び手は `buildcache.py:2473-2492` だけです。
   - entry は `buildcache.py:2431-2454` で現在の preimage から digest を作った後に選ばれます。現在は `effective_dependency_prefix` の jobid 入り絶対 path が `buildcache.py:1314,2434` で preimage に入るため、通常の別 job は同じ entry を選びません。

4. `s8b_binary_admission.py:231-238`
   - production 呼び手は `s8b_floor_campaign.py:4374-4393` だけです。
   - `s8b_floor_campaign.py:4289-4302` の build が戻った直後、同じ job 内で発行します。削除されるのは build staging であり、`CMAKE_PREFIX_PATH` の job root ではありません。

`validate_portable_binary_record()` は `s8b_binary_admission.py:366-380` で manifest の構造と digest を再計算するだけで、live path の bytes は再検証しません。

`build_v2()` へ declaration descriptor を渡して root-class-2 manifest を作れる production 系列は、floor の `s8b_floor_campaign.py:4275-4302` と、oracle wrapper の `s8b_oracle_driver.py:1185-1235` です。それ以外の直接 `build_v2()` caller は descriptor-less で、この根タグを生成しません。

なお、外部コードが public `build_v2()` に古い `dependency_prefix` 文字列を意図的に再提示することは可能ですが、repository 内の production caller が終了済み job の値を保存、復元する経路はありません。

さらに、`dependency_prefix` を根相対化するだけでも別 job hit は発火しません。

- `buildcache.py:2251` の `admission_identity` が `buildcache.py:1315` で preimage に入ります。
- `BuildAdmission.as_cache_identity()` は `build_admission.py:362-363` で receipt 全文を返します。
- その source は `build_admission.py:662-666` に入り、`source_digest.py:164-174` の絶対 `source_root` を含みます。
- `buildcache.py:2226-2228` 自身も、正式 S8b 経路ではこの絶対 `source_root` のため cache hit が起きない、と記録しています。

したがって採るべき分岐は形式上は形 Bですが、「`dependency_prefix` だけを変えれば根クラス 2 の cross-job 再束縛が発火する」という前提は成立しません。

## 実装プラン (file:line)

### 形 A: 発火路が存在した場合の反実仮想

`dependency_prefix` identity は変更せず、以下だけを行います。

- `s8b_compiler_input.py:38-42`
  - 現在の `_V2_ROOTS` は変更しません。
  - `PREVIOUS_MANIFEST_SCHEMA = "s8b-compiler-input/v2"` を追加。
  - `MANIFEST_SCHEMA` を `"s8b-compiler-input/v3"` に更新。
  - `_V3_ROOTS = _V2_ROOTS | frozenset({"dependency-prefix"})` を追加。
  - v2 を read-only で残すため、既存 v2 の受理集合は変えません。

- `s8b_compiler_input.py:776-858`
  - `_normalized_v2_inputs()` と `_normalized_v2_manifest()` は旧 v2 専用として維持。
  - `_normalized_v3_inputs()` と `_normalized_v3_manifest()` を新設。
  - `_normalized_manifest()` は v1、v2、v3 を明示分岐。
  - v2 manifest に新タグを入れても拒否される状態を維持します。

- `s8b_compiler_input.py:967-1096`
  - collector に `origin_dependency_prefix_roots` と `current_dependency_prefix_roots` を追加。
  - 分類順を `snapshot`、`fetchcontent-masstree`、`dependency-prefix`、`filesystem` とします。
  - external path が origin prefix 要素のどれか 1 個だけの配下にある場合に限り、`root="dependency-prefix"` とその要素からの相対 path を記録します。
  - prefix の basename、配列 index、順番を manifest の root identity にしません。

- `s8b_compiler_input.py:861-964`
  - validator に `current_dependency_prefix_roots` を追加。
  - `dependency-prefix` entry は、現在の prefix 要素集合のうち相対 path が安全な regular file として存在する要素がちょうど 1 個の場合だけ hash 検証します。
  - 0 個、2 個以上、symlink、非 regular、bytes 差はすべて拒否します。
  - `filesystem` tag で現在の dependency root 内を指す偽装を `s8b_compiler_input.py:925-937` 相当の canonical-root 検査で拒否します。

形 Aでも schema は v3 に上げます。v2 の root 集合をそのまま拡張すると既存 v2 completion が新しい意味で解釈され、また旧 v2 entry が新 manifest の fresh build を遮るためです。D1338 の「schema を identity に pin して移行時だけ miss」に従う形です。

### 形 B: 現行コードに対する選択形

形 Aの全変更に加え、次を行います。

- `buildcache.py:1816-1839`
  - 現行の canonical absolute 要素列は configure 用と live validation 用に保持します。
  - `_dependency_prefix_cache_identity()` を新設し、descriptor-bound build に限って、実測形の「同一 parent 配下にある 2 個の sibling prefix」を parent 相対の要素列へ射影します。
  - 順序は保持します。manifest の再束縛だけを集合照合にします。
  - sibling 条件を満たさない未実測形は従来どおり絶対 identity のままとし、推測で portable 化しません。

- `buildcache.py:1287-1321,2431-2451`
  - `_v2_identity()` へは configure 用の `effective_dependency_prefix` ではなく、上記の root-relative identity を渡します。
  - 各 identity 要素は少なくとも
    `{"root":"dependency-prefix","path":relative,"tree_sha256":digest}`
    とします。
  - `tree_sha256` は既に import 済みの
    `s8b_expected_materialization.snapshot_tree_digest()` を使い、header だけでなく install tree 全体を束縛します。

tree digest は省略できません。`test_s8b_compiler_input.py:212-218` の実測形では gflags/glog の `.a` も link input ですが、`_parse_link_txt()` は `s8b_compiler_input.py:268-285` で `.o` だけを収集し、compiler manifest は library bytes を持ちません。path だけを除去すると、同じ header、異なる library の entry を同一 identity にして受理集合を広げます。

- `buildcache.py:2431-2454,2493-2524,2667-2707`
  - identity 作成時の prefix tree digest を保存。
  - cache hit の return 前と fresh publish 前に同じ digest を再取得し、変化していれば拒否。
  - invalid hit を fresh build へ降格する経路は作りません。

- `buildcache.py:653-684`
  - `BuildResult` に runtime-only の
    `compiler_input_dependency_prefix_roots: tuple[str, ...] = ()`
    を追加。
  - 絶対 root は completion や durable receipt に保存しません。

- `buildcache.py:1393-1439`
  - `_collect_compiler_inputs()` の signature introspection に origin/current dependency roots を加え、collector へ伝搬。
  - external policy が有効なのに fake/collector が新しい binding 引数を持たない場合は、従来と同じく fail closed。

- `buildcache.py:1588-1723`
  - `_validate_v2_entry()` に current dependency roots を追加し、cache-hit validator へ渡します。

- `buildcache.py:2379-2387`
  - 「現在の canonical base」の正本はここで得る `effective_dependency_prefix` の要素列です。
  - explicit 値と ambient `CMAKE_PREFIX_PATH` の双方を、実際に identity/configure に使った同じ分岐から取得します。
  - CMakeCache や receipt 時点の環境変数を再読しません。

- `buildcache.py:2467-2535,2606-2666,2733-2765,2799-2810`
  - hit/fresh validator に roots を渡す。
  - completion は v3 manifest と digest だけを保存。
  - fresh/hit の `BuildResult` に同じ current root tuple を載せます。

- `buildcache.py:2816-2968`
  - `build_v2()` の入力 signature は増やしません。すでに受け取っている `dependency_prefix` または ambient 値から導出します。
  - descriptor-less caller の identity、completion、既存期待値は変更しません。

- `s8b_binary_admission.py:183-242`
  - `issue_binary_admission_receipt()` に
    `current_compiler_input_dependency_prefix_roots=()` を追加。
  - `validate_compiler_input_manifest()` の新引数へそのまま渡します。
  - `validate_portable_binary_record()` は v3 を正規化しますが、live root を要求せず bytes 再検証もしません。

- `s8b_floor_campaign.py:4325-4336,4374-4393`
  - `result.compiler_input_dependency_prefix_roots` を `getattr(..., ())` で取得。
  - receipt issuer へ明示的に渡します。
  - `s8b_floor_campaign.py:4289-4302` の build 呼び出しには新しい root 引数を足しません。buildcache が実際に使った prefix から返す値でなければ、build と receipt の authority が分離するためです。

ただし、この形 Bでも正式 floor の cross-job hit は absolute `admission.source_root` に阻まれます。これを外すには descriptor-bound cache 専用の root-neutral admission projectionと completion 検証契約が別途必要です。既裁定はそこまで認可しておらず、現行の「exact admission を preimage と completion に保存する」契約にも触れるため、この plan へ無断では含めません。

## 述語ごとの正例・負例

- `_normalized_v3_inputs(value) -> list[dict[str, str]]`
  - 正例: `[{"root":"dependency-prefix","path":"include/gflags/gflags.h","sha256":"a"*64}]` は通る。
  - 負例: 同じ entry を v2 manifest に入れる、または `path="../gflags.h"` にすると落ちる。

- `_canonical_dependency_prefix_roots(value) -> tuple[Path, ...]`
  - 正例: canonical な異なる 2 root の列を保持して返す。
  - 負例: duplicate、相互包含、NUL、相対 path、snapshot/masstree と重なる root は落ちる。

- `_classify_compiler_input_root(absolute, snapshot, masstree, dependency_roots)`
  - 正例: root A の `include/gflags/gflags.h` は
    `("dependency-prefix","include/gflags/gflags.h",root_A)` になる。
  - 負例: 2 root の双方に包含される ambiguous path は落ち、filesystem へ fallback しない。

- `_hash_from_unique_dependency_prefix_root(roots, relative)`
  - 正例: 1 root だけに `include/glog/logging.h` があり hash が一致すれば通る。
  - 負例: 同じ relative leaf が 2 root に存在する、または唯一の leaf が symlink なら落ちる。

- `_dependency_prefix_cache_identity(elements, portable=True)`
  - 正例: `job-A/{gflags-install,glog-install}` と、内容が同じ
    `job-B/{gflags-install,glog-install}` は同じ root-relative identity になる。
  - 負例: glog install tree の `.a` だけが違えば `tree_sha256` が変わり、同じ entry を選ばない。

- `_assert_dependency_prefix_identity(roots, expected)`
  - 正例: build/cache-hit 前後で全 tree digest が同じなら通る。
  - 負例: configure 後に `lib/libgflags.a` が変われば publish/return 前に落ちる。

- `validate_compiler_input_manifest(..., current_dependency_prefix_roots=...)`
  - 正例: origin の basename、配列位置と異なる current root でも、要素集合の 1 個だけに relative file と同じ bytes があれば通る。
  - 負例: `filesystem` tag に偽装して current dependency root の絶対位置を記録した manifest は、digest を再封印しても canonical-root 検査で落ちる。

## テスト計画

現行被覆は、masstree の collect/rebind、bytes drift、missing、symlink、root-tag 偽装、v1 compatibility、cache-hit revalidation、receipt-time revalidationまであります。一方、dependency-prefix root、複数 base の一意選択、identity の job-root 除去、build-to-receipt の runtime root 伝搬は未被覆です。

追加する nodeid は次です。

`orchestrator/tests/test_s8b_compiler_input.py`

- `test_v3_manifest_classifies_dependency_prefix_root_relative_and_rebinds_setwise`
- `test_v3_dependency_prefix_rebind_is_independent_of_root_order_and_basename`
- `test_v3_dependency_prefix_rejects_missing_drift_and_symlink`
- `test_v3_dependency_prefix_rejects_ambiguous_current_root`
- `test_v3_filesystem_tag_cannot_alias_current_dependency_prefix_root`
- `test_v2_does_not_accept_v3_dependency_prefix_tag`

`orchestrator/tests/test_buildcache_v2.py`

- `test_v3_job_dependency_prefix_identity_is_root_relative_and_content_bound`
- `test_v3_dependency_prefix_tree_drift_changes_identity`
- `test_v3_descriptor_hit_rebinds_dependency_prefix_manifest_without_rebuild`
- `test_v3_dependency_prefix_hit_validation_failure_never_rebuilds`
- `test_v3_result_exposes_runtime_dependency_roots_without_persisting_them`
- `test_v3_schema_pin_does_not_select_v2_completion`
- `test_v3_distinct_source_roots_still_select_distinct_admission_identity`

最後の node は、`dependency_prefix` 修正後も正式 cross-job hit が発火しない事実を固定する回帰です。

`orchestrator/tests/test_s8b_binary_admission.py`

- `test_issue_v3_receipt_rechecks_current_dependency_prefix_roots`
- `test_issue_v3_receipt_rejects_missing_drift_and_ambiguous_root`
- `test_portable_validator_accepts_v3_after_live_dependency_roots_disappear`

既存期待値は変更しません。test helper の additive v3 branchと fake collector の新しい keyword 受け取りだけを更新します。

`orchestrator/tests/test_s8b_floor_campaign.py` を編集しない条件では、scope はテスト上閉じません。必要だが追加できない node は次です。

- `test_build_cells_passes_build_result_dependency_prefix_roots_to_receipt`

現行 `test_s8b_floor_campaign.py:3137-3182` は masstree root だけを spy しています。新しい keyword を production floor から削除する変異は、指定された 3 test fileでは検出できません。並行 wave がこの node を追加するか、その所有解除後に追補する必要があります。

## 焦点走の対象

静的な `rg` 参照で得た direct consumer 集合です。実走はしていません。

- `s8b_compiler_input.py`:
  `test_s8b_compiler_input.py`、`test_buildcache_v2.py`、`test_s8b_binary_admission.py`

- `s8b_binary_admission.py`:
  `test_s8b_binary_admission.py`、`test_s8b_floor_campaign.py`、
  `test_s8b_floor_stats.py`、`test_s8b_predicate_build_proof.py`、
  `test_s8b_ratified_verify.py`

- `buildcache.py`:
  `test_b10_backoff_shape_sweep.py`、`test_backoff_extended_sweep.py`、
  `test_backoff_overthrottle.py`、`test_backoff_profile_pegasus.py`、
  `test_backoff_requested_us.py`、`test_backoff_sweep.py`、
  `test_between_run_floor.py`、`test_build_site_gate.py`、
  `test_buildcache_v2.py`、`test_campaign.py`、
  `test_ccbench_spawn_sites.py`、`test_env_contract.py`、`test_hooks.py`、
  `test_p2_2_site_aware.py`、`test_p3_build_authority_cli.py`、
  `test_p3_exploration_namespace.py`、`test_p3_s4_loop_trigger_gating.py`、
  `test_paper_story_a1_paired.py`、`test_paper_story_a2_certification.py`、
  `test_pegasus_floor_scoping.py`、`test_pegasus_floor_tools.py`、
  `test_real_repo_serialization.py`、`test_s1_direct_comparison.py`、
  `test_s6_sort_sweep.py`、`test_s8a_trigger_sweep.py`、
  `test_s8b_floor_campaign.py`、`test_s8b_freeze_io.py`、
  `test_s8b_materialization.py`、`test_s8b_oracle_driver.py`、
  `test_s8b_predicate_build_proof.py`、`test_s8b_ratified_freeze.py`、
  `test_screening_opt_in.py`、`test_skip_classification.py`、
  `test_sort_swo_dependency_material.py`、
  `test_t126_qualification_driver.py`、
  `test_t1416_backoff_compiler_binding.py`

- `s8b_floor_campaign.py` を編集する場合:
  上記に加え `rg` で同 module を名指しする
  `test_floor_submit_receipt.py`、`test_growth_test_holds_contract.py`、
  `test_holdout_observation.py`、`test_official_perf_closure.py`、
  `test_s8b_approved.py`、`test_s8b_attempt_registry.py`、
  `test_s8b_floor_contract.py`、`test_s8b_holdout_admission.py`、
  `test_s8b_prediction_runner.py`、`test_s8b_protocol_builder.py`
  も対象です。

追加の静的契約面として、`orchestrator/qualification/contract.py:39-77` が
`buildcache.py` を code identity に含めます。したがって
`test_t126_qualification_contract.py` と `test_t126_pegasus_tools.py` も確認対象です。

また、

- `test_ccbench_spawn_sites.py:92-99` は `buildcache.py` の process site 数を固定
- `test_env_contract.py:83-100` は `buildcache.py` と `s8b_floor_campaign.py` を env-neutral module に登録
- `orchestrator/qualification/contract.py:61` は `buildcache.py` を名指し

しています。新しい subprocess、Pegasus 固有 literal、`/scr` literalを production moduleへ追加しない設計にします。

## 変異事前登録の候補

以下は、提案した nodeを追加した場合に限り登録可能です。

1. `orchestrator/campaign/s8b_compiler_input.py`
   - old: `_V3_ROOTS = _V2_ROOTS | frozenset({"dependency-prefix"})`
   - 置換: `_V3_ROOTS = _V2_ROOTS`
   - 赤理由: 正しい v3 dependency tag が root membership だけで拒否される。前段の shape/digest は正しく、後段へ到達しないため単一理由です。

2. `orchestrator/campaign/s8b_compiler_input.py`
   - old: `root = "dependency-prefix"`
   - 置換: `root = "filesystem"`
   - 赤理由: origin root 配下の正例が誤分類される。fixture は両 tag で hash 可能なので、分類期待だけに帰属できます。

3. `orchestrator/campaign/s8b_compiler_input.py`
   - old: `if len(matches) != 1:`
   - 置換: `if not matches:`
   - 赤理由: 2 root に同じ relative fileと同じ bytesを置いた負例だけが誤受理されます。schema、path、hash は全て正しく、他の拒否層はありません。

4. `orchestrator/campaign/s8b_compiler_input.py`
   - old: `special_roots.extend(current_dependency_roots)`
   - 置換: `special_roots.extend(())`
   - 赤理由: current dependency root を `filesystem` tag で指す再封印済み manifest が誤受理されます。root-tag canonicality が唯一の拒否点です。

5. `orchestrator/campaign/buildcache.py`
   - old: `dependency_prefix=identity_dependency_prefix,`
   - 置換: `dependency_prefix=effective_dependency_prefix,`
   - 赤理由: source/admission、prefix tree bytes、他の preimage を固定した 2 runtime-root fixtureで hit が missになります。差は job-root absolute pathだけです。

6. `orchestrator/campaign/s8b_binary_admission.py`
   - old:
     `current_dependency_prefix_roots=current_compiler_input_dependency_prefix_roots,`
   - 置換:
     `current_dependency_prefix_roots=None,`
   - 赤理由: 正しい v3 receipt正例が issuer 内の live validationでだけ落ちます。issuer前段の admission、binding、snapshot検査は同じ入力で通ります。

floor の keyword 伝搬を消す変異は、所有中の `test_s8b_floor_campaign.py` を変更できない限り kill nodeがないため登録候補にしません。また root-neutral cache admission は未裁定なので候補にしません。

## 総括

現行 production 閉包では、根クラス 2 の記録 pathを作成 jobの外で再解決する経路はありません。形式上は形 Bですが、親の provisional 結論には二つ不足があります。

- `dependency_prefix` の絶対 pathを外すだけでは、`admission.source_root` の job-local 絶対 pathが cross-job cache hitを引き続き阻止します。
- prefix pathだけを捨てると、compiler manifestに入らない gflags/glog library bytesを同一視し、受理集合を広げます。安全な identityには install tree digestが必要です。

root tag、v3 schema、runtime root伝搬、content-bound dependency identityまでは file:line粒度で設計できます。しかし正式 floorで再束縛を実際に発火させるには、root-neutral cache admissionという追加裁定が必要です。また floorの build-to-receipt bridgeを検査する testは並行 wave所有ファイルにしか置けず、現在の制約ではテスト閉包も成立しません。

したがって、このまま段 5へ進めるべきではありません。親は「root-class-2 manifestを durable化するだけでよい」のか、「cross-job再束縛を実際に発火させるため cache admissionもportable化する」のかを裁定し、後者なら別の受理境界変更として明示的に認可する必要があります。静的検査のみで、pytestは実行していません。