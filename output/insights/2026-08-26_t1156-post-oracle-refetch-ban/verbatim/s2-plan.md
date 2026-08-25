## 閉包 (独立再導出)

### 値と別名の流れ

`sort_best` の依存 binding は次の経路で運ばれる。

1. `s8b_floor_campaign.py:3859-3873`  
   `_prepare_floor_oracle_dependency()` が `_FloorOracleDependencyBinding` を返し、`dependency_binding` に束縛する。

2. `s8b_floor_campaign.py:3907-3919`  
   `dependency_binding` は closure default `_dependency` へ別名束縛され、その `source_root` が `oracle_dependency_root` として `prepare_cell()` に渡る。

3. `s1_direct_comparison.py:682-693`  
   `oracle_dependency_root` は `OracleEnvironment.dependency_root` になり、`check_materialized_sort_swo()` が消費する。

4. `sort_swo_oracle.py:1796-1929, 2743-2808`  
   oracle は元 root を検証して private directory へ複製する。receipt 作成後の compile/run は private copy を読み、元 FetchContent base を再 populate しない。

5. `s8b_floor_campaign.py:3979-4003`  
   同じ `dependency_binding` は別名 `build_kwargs` に射影される。

   - `source_root.parent` → `fetchcontent_base_dir`
   - `cache_receipt()` → `fetchcontent_dependency_receipt`
   - `archive_sha256` → `fetchcontent_archive_sha256`
   - staged mode では三つの `*_source_dir`

6. `s8b_floor_campaign.py:4005-4016`  
   `build_fn` という別名で `buildcache.build_v2` に渡る。production wrapper は callable seam を拒否し、official core は `buildcache.build_v2` に固定する (`s8b_floor_campaign.py:6612-6621, 6731-6738`)。

### oracle 後に同じ材料へ触れる経路

| 経路 | 実コード | 性質 |
|---|---|---|
| build 前 archive 先行照合 | `buildcache.py:1932-1939` | archive の read。既存。 |
| cache-hit 中 archive 再照合 | `buildcache.py:2042-2053` | configure/build は走らないが、材料を read する。 |
| cache-hit argv 再生成 | `buildcache.py:2056-2065` → `_v2_result()` → `_v2_commands()` | 材料自体は読まない。現在の generator で provenance を再構成する。 |
| fresh configure argv 生成 | `buildcache.py:2087-2100` | 材料を読まないが、次の実行 argv を決める。 |
| fresh configure 実行 | `buildcache.py:2108, 2111-2114` | 主たる再 populate 経路。 |
| masstree populate | `external/ccbench/cmake/ThirdParty.cmake:42-55` | `FetchContent_Populate(masstree)`。 |
| mimalloc/googletest populate | `ThirdParty.cmake:106-136` | `FetchContent_MakeAvailable`。oracle 材料ではないが同じ base に触れる。新 flag はこれらも切断する。 |
| cell target build | `buildcache.py:2109, 2115-2118` | `ycsb_silo.exe` は `ccbench::masstree` にリンクする。 |
| masstree 再生成 | `ThirdParty.cmake:66-87`, `ProtocolHelpers.cmake:32-39` | archive または `config.h` が無ければ custom command が source tree 内で再生成する。P5 の残存経路。 |
| buildcache 事後照合 | `buildcache.py:2122-2151` | 実効 root、HEAD、`config.h`、archive を再観測する。 |
| floor 事後照合 | `s8b_floor_campaign.py:3379-3608, 4048-4066` | argv、toolchain、root inode、tracked status、HEAD、config、archive、payload policy を再観測する。 |
| artifact 記録 | `s8b_floor_campaign.py:4117-4139, 4293-4363` | argv と base path を記録・portable 化するだけで材料は読まない。 |

### brief 表との差

brief が落としている経路は次の通り。

- `buildcache.py:1932-1939` の configure 前 archive read。
- `buildcache.py:2042-2053` の cache-hit archive read。
- `s8b_floor_campaign.py:3379-3608` の、buildcache 側とは独立した floor postflight。
- `cmake --build` から `masstree_build` へ至る archive/config 再生成経路。
- masstree 以外の `FetchContent_MakeAvailable(mimalloc/googletest)`。oracle 材料ではないが同じ base を mutate しうる。
- fresh return `buildcache.py:2240-2249` も `_v2_result()` を通るため、記録側 B は cache hit だけでなく fresh return にも存在する。

逆に、表 C と E は「oracle 判定後に材料へ触れる閉包」には過剰である。

- C の prebuild は `s8b_floor_campaign.py:3859-3873` で cell loop より前に一度だけ走る。既存テスト `test_s8b_floor_campaign.py:2361-2438` と `2441-2503` も `prebuild < oracle < build` を固定している。
- E は材料へのアクセス経路ではなく、argv 変更の互換性検査集合である。
- `pipeline.py:1074-1083` は `build_v2` の別の呼び手だが、base、receipt、archive を渡さないため今回の post-oracle 閉包には入らない。
- legacy `build()` は `buildcache.py:2254` 以降の独立 generator で、FetchContent base を受け取らない。

## 実装プラン (file:line)

### P1(a): FULLY_DISCONNECTED flag

`orchestrator/campaign/buildcache.py:45-49` に次の単一 token 定数を追加する。

```python
_FETCHCONTENT_FULLY_DISCONNECTED_DEFINE = (
    "-DFETCHCONTENT_FULLY_DISCONNECTED=ON"
)
```

`buildcache.py:1552-1571` の `_v2_commands()` で、`fetchcontent_base_dir` が非空の場合だけ次を一要素 list として追加する。

```python
fully_disconnected_define = (
    [_FETCHCONTENT_FULLY_DISCONNECTED_DEFINE]
    if fetchcontent_base_dir else []
)
```

配置は `-DFETCHCONTENT_BASE_DIR=...` の直後、`SOURCE_DIR` 群の前とする。

```python
... + prefix_define + fetchcontent_define \
    + fully_disconnected_define + source_defines + defines
```

`buildcache.py:1572-1593` の generator 自己検査に次を追加する。

```python
expected_count = 1 if fetchcontent_base_dir else 0
if configure.count(_FETCHCONTENT_FULLY_DISCONNECTED_DEFINE) != expected_count:
    raise BuildCacheError(...)
```

これにより base 束縛時は exact 1、非束縛時は exact 0 になる。`prepare_masstree_fetchcontent()` の argv には追加しない。そこは oracle 前に populate する経路だからである。

### P1(b): configure 直前の populate 検査

`buildcache.py:847-894`、既存の receipt/archive observer の直後に次の private helper を置く。

```python
def _assert_fetchcontent_dependency_prepopulated(
        fetchcontent_base_dir: object, *,
        expected_receipt: Optional[Mapping[str, object]],
        expected_archive_sha256: object,
) -> None:
```

処理は次の順序にする。

1. `_canonical_fetchcontent_base()` で base を再度 canonicalize。
2. `_validate_fetchcontent_dependency_receipt()` で expected HEAD/config を正規化し、`None` は拒否。
3. `_validate_fetchcontent_archive_sha256()` で optional archive binding を正規化。
4. `base/masstree-src` に `_observe_fetchcontent_dependency_receipt()` を適用し、HEAD と `config.h` SHA-256 の完全一致を要求。
5. archive binding がある場合は `_observe_fetchcontent_archive_sha256()` を適用し、完全一致を要求。
6. source 不在、Git probe 不能、非 canonical root、非 regular file、hash 中 drift は既存 helper の `BuildCacheError` をそのまま fail-closed に伝播させる。

呼び出しは `buildcache.py:2106`、`_run(configure, ...)` の直前に置く。`_v2_commands()` より前ではなく、argv と環境の構築が終わった後にする。

```python
if dependency_receipt is not None:
    _assert_fetchcontent_dependency_prepopulated(
        canonical_fetchcontent_base,
        expected_receipt=dependency_receipt,
        expected_archive_sha256=dependency_archive_sha256,
    )
```

site 有無の二枝 `buildcache.py:2107-2118` の外側、共通位置に一度だけ置く。

受理条件は、production floor 呼び出しでこの helper が return したなら、`masstree-src` は canonical Git root として存在し、その HEAD、`config.h` SHA-256、archive SHA-256 が oracle 前の binding とすべて一致する、という向きである。  
拒否条件は、source 不在、観測不能、または HEAD、config、archive のどれか一つでも不一致なら、`_run(configure, ...)` より前に `BuildCacheError` が raise される、という向きである。

通る正例は、canonical base `B` の `B/masstree-src` が expected HEAD `H` を持ち、`sha256(config.h) == C`、`sha256(libkohler_masstree_json.a) == A` で、呼び手が `{masstree_head: H, config_sha256: C}` と `A` を渡す場合である。

### 恒真化しない具体例

- `B/masstree-src` を rename または削除する。`_observe_fetchcontent_dependency_receipt()` が source root を再照合できず raise する。
- receipt は元のまま `config.h` に別 bytes を書く。observed receipt が expected receipt と一致せず raise する。
- expected archive SHA は元のまま archive に別 bytes を書く。observed archive SHA が一致せず raise する。

親の CMake 3.22 実測では source 不在でも flag 単独の configure は rc=0 になるが、この設計では CMake を起動する前に第一例が raise する。したがって flag 単独の恒真経路を positive control が直接破る。

### cache identity

`_v2_identity()` は現状、configure policy を preimage に含めない (`buildcache.py:1139-1182`)。P4 を維持すると旧 entry を hit した際、実際には flag なしで作られた binary に対して、更新後の `_v2_result()` が flag 付き argv を「この binary を作った configure」として返す。

推奨プランは次の通り。

- `buildcache.py:45-49` に `fully-disconnected-prepopulated/v1` の policy ID を追加。
- `buildcache.py:1139-1182` の `_v2_identity()` に optional `fetchcontent_population_policy` を追加し、base 束縛 build だけ preimage に入れる。
- `buildcache.py:1959-2006` で base 束縛時にこの policy ID を渡す。
- 非 base build の preimage は byte-for-byte 同じに保つ。

これで旧 base-bound cache entry は新 digestから外れ、fresh configure で新防壁を実行する。一方、A1、A2、pipeline の非 base identity は変わらない。

### 既存の事後検知

以下は一切削除、短絡、条件緩和しない。

- `buildcache.py:1932-1939`
- `buildcache.py:2042-2053`
- `buildcache.py:2122-2151`
- `s8b_floor_campaign.py:3379-3608`
- `s8b_floor_campaign.py:4048-4066`

事前検査だけでは helper と CMake 起動の間の TOCTOU、configure と build の間の drift、`masstree_build` 再生成、cache-hit 中 drift を閉じられない。したがって「事前禁止を足し、事後検知を引かない」が必要である。

### 凍結成果物への影響

**Yes: configure argv の変更は現行凍結 manifest 23 件の bytes を変えない。**

実 path は次の通り。

```text
output/s1-freeze/known_axes_freeze.json
output/s1-freeze/measurement_freeze.json
output/s8b-freeze/holdout_freeze.json
output/s8b-freeze/floor_protocol.json
output/insights/2026-07-16_s8b-floor-protocol-package.md
output/insights/2026-07-16_s8b-freeze-v2-design-material.md
output/insights/2026-07-16_s8b-floor-protocol-consultations.md
output/insights/2026-07-16_s8b-freeze-consultations.md
output/insights/2026-07-16_s8b-ruling-prep-consultations.md
output/s8b-freeze/selector_predictions.json
output/s8b-freeze/selector-runs/envelope_rr20_on.json
output/s8b-freeze/selector-runs/envelope_rr20_swapped.json
output/s8b-freeze/selector-runs/envelope_rr80_on.json
output/s8b-freeze/selector-runs/envelope_rr80_swapped.json
output/s8b-freeze/selector-runs/journal.jsonl
output/s8b-freeze/selector-runs/payload_rr20_on.json
output/s8b-freeze/selector-runs/payload_rr20_swapped.json
output/s8b-freeze/selector-runs/payload_rr80_on.json
output/s8b-freeze/selector-runs/payload_rr80_swapped.json
output/s8b-freeze/selector-runs/raw_rr20_on.txt
output/s8b-freeze/selector-runs/raw_rr20_swapped.txt
output/s8b-freeze/selector-runs/raw_rr80_on.txt
output/s8b-freeze/selector-runs/raw_rr80_swapped.txt
```

この一覧に build result、runtime manifest、configure argv、`buildcache.py`、テストファイルは含まれない。23 ファイル内を照合しても `configure_argv` または FetchContent token の pin は無い。

## exact 述語 consumer の照合

brief の三項だけでは閉じていない。完全 argv の consumer は A1/A2 で閉じるが、filtered exact predicate とテスト側の位置固定 consumer が別にある。また `_portable_argv` は exact predicate ではない。

| consumer | 実条件 | 判定 |
|---|---|---|
| `_v2_commands()` 自己検査 `buildcache.py:1572-1593` | BASE define の prefix count、SOURCE_DIR filtered list の一致 | 新 token はどちらの prefix にも一致しないため壊れない。新 flag 自身の exact count を追加する。 |
| A1 `paper_story_a1_paired.py:1338-1377` | `len == 10 + defines`、index 0/2/4/7/8/9、全 vector 一致 | base を渡さないため P2 なら一 byte も変わらず、壊れない。全 build に flag を足す案なら確実に壊れる。 |
| A2 `paper_story_a2_certification.py:1308-1346` | policy grammar から `expected` を合成して全 vector 一致 | base を渡さないため壊れない。 |
| A2 grammar golden `paper_story_a2_certification.v1.json:52-80` | fixed/toolchain/prefix/controlled defines 以外を認めない | 非 base generator の出力が不変なので変更不要。 |
| floor postflight `s8b_floor_campaign.py:3442-3489` | SOURCE_DIR filtered list と BASE filtered list `[expected_define]` | FULLY token は両 filter 外なので壊れない。brief E の実質的な漏れ。 |
| `_portable_argv()` `s8b_floor_campaign.py:4191-4223` | 非空 `list[str]`、各 token の root 置換、raw root 残留拒否 | 長さ、順序、集合を固定していない。新 tokenをそのまま保持するので壊れない。brief が exact consumer と呼ぶのは不正確。 |
| portable validator `s8b_floor_campaign.py:4258-4262` | 各 argv が非空 `list[str]` | 壊れない。 |
| ratified validator `s8b_ratified_freeze.py:1726-1733` | 各 argv が非空 `list[str]` | 壊れない。 |
| submission semantic validator `_semantic_validator.py:1046-1049` | `CCBENCH_TRACE` macro だけ抽出 | 新 token は無視され、壊れない。 |
| buildcache tests `test_buildcache_v2.py:727-735, 1095-1102, 1139-1147, 1219-1226` | BASE/SOURCE/PREFIX の filtered exact list | 新 tokenは filter 外で壊れない。 |
| A1 test `test_paper_story_a1_paired.py:1084-1094` | 長さ 16、index 9 | 非 base fixtureなので壊れない。 |
| A2 golden test `test_paper_story_a2_certification.py:429-450` | policy grammar object の完全一致 | 非 base grammarなので壊れない。 |
| floor portable tests `test_s8b_floor_campaign.py:10411-10483` | 一つは `configure_argv[-1]`、一つは literal vector 完全一致 | どちらも手作り入力で `_v2_commands()` の出力ではないため現変更では壊れない。producer-derived golden ではない。 |

したがって、brief の「A1、A2、portable の三つで閉じる」は誤りである。正確には、完全 vector の production predicate は A1/A2、filtered exact predicate は `_v2_commands` と floor postflight、portable は位置非依存の射影器である。

## positive control テスト設計

主な追加先は `orchestrator/tests/test_buildcache_v2.py` とする。

### (b) の正例と三負例

`test_buildcache_v2.py:343-374` の dependency fixture 群の直後に置く。

```python
def test_v2_post_oracle_prepopulate_check_accepts_exact_material(...):
```

- `_write_fetchcontent_dependency()` で HEAD/config/archive を作る。
- exact receipt と archive SHA を渡す。
- helper が `None` を返すことを確認する。

```python
@pytest.mark.parametrize(
    "mutation",
    ["missing-source", "config-sha-mismatch", "archive-sha-mismatch"],
)
def test_v2_post_oracle_prepopulate_check_rejects_material_drift(...):
```

- `missing-source`: `masstree-src` を rename。
- `config-sha-mismatch`: expected receipt を保持したまま `config.h` を変更。
- `archive-sha-mismatch`: expected archive SHA を保持したまま archive を変更。
- 三例すべて `BuildCacheError` を要求する。

既存 `test_s8b_floor_campaign.py:3460-3495` は oracle **前**の missing config/archive、`test_buildcache_v2.py:851-941` は build **後**または build 中の drift を覆う。今回の「oracle 後かつ configure 前」という temporal vectorには純増検出力がある。

統合位置の非恒真確認として、`test_buildcache_v2.py:712` 付近に次も追加する。

```python
def test_v2_post_oracle_prepopulate_check_precedes_configure(...):
```

config を oracle receipt からずらし、`_run` spy の call 数が 0 のまま raise することを確認する。helper 単体だけでなく `build_v2` の実行線に接続されていることを証明する。

### (a) の本数検査

`test_buildcache_v2.py:712` の base argv テスト群の前に置く。

```python
def test_v2_commands_emits_fully_disconnected_only_for_bound_base():
```

同じ genome/toolchain から `_v2_commands()` を二回呼び、

- base 束縛: `configure.count(flag) == 1`
- base 非束縛: `configure.count(flag) == 0`

を確認する。

既存 `test_v2_fetchcontent_base_is_canonical_single_define_and_receipt_in_preimage` は BASE define と SOURCE_DIR 不在しか検査しないため、新 flag の multiplicity には純増検出力がある。

### A と B の生成器同一性

同じ付近に次を追加する。

```python
def test_v2_execution_and_fresh_hit_records_share_configure_generator(...):
```

- `_run` へ渡った fresh configure argv を捕捉。
- fresh `BuildResult.configure_argv` と完全一致させる。
- 二回目の cache-hit `BuildResult.configure_argv` とも完全一致させる。
- configure `_run` は fresh の一回だけであることを確認する。
- `_v2_commands` spy を使う場合は fresh execution、fresh result、hit result の三呼び出しが同じ policy token を生成したことも確認する。

既存テストは fresh/hit の `cached` 状態や BASE token を個別確認するが、実行 argvと両記録 argvの完全一致は確認していないため純増である。

### A1/A2 正例

新しい重複テストは追加しない。

- A1 は `test_paper_story_a1_paired.py:1070` の `test_production_wal_bytes_positive_fixture` が非 base `_v2_commands()` の exact grammar を通す。
- A2 は `test_paper_story_a2_certification.py:1199` の end-to-end positive と、`1166` の closed grammar mutation test が非 base exact grammar を通す。

同じ vector を新テストから再度流すだけでは純増検出力がない。上の flag 0 本検査と既存 A1/A2 positive の組み合わせで十分である。

### P4 を覆す場合の追加テスト

`test_buildcache_v2.py:1013-1039` 付近に次を置く。

```python
def test_v2_post_oracle_population_policy_changes_only_bound_base_identity():
```

- 非 base identity は policy導入前後で同一。
- base-bound identity は新 policy field の有無で異なる。
- receipt/archiveが同じでも旧 policy entryを hitしない。

### P3/P5 が scope に入る場合

- P3: `test_s8b_floor_campaign.py:2361-2438` は現状の順序しか検査しない。実際の late reentry を拒否する phase capability を導入するなら、`test_floor_dependency_prebuild_rejects_after_oracle_phase_started` を追加する。
- P5: configure 後に archiveを削除し、build `_run` が一度も呼ばれず拒否される `test_v2_rechecks_prepopulation_between_configure_and_build` を追加する。

この二つは親の裁定前に実装へ混ぜない。

## brief への反論

### P1

基本方針は正しい。ただし flag は禁止機構、事前検査は CMake 3.22 の silent success を閉じる機構であり、片方だけでは受理条件にならない。

また floor は `fetchcontent_archive_sha256` を必ず渡す (`s8b_floor_campaign.py:3983-3991`)。generic `build_v2` の archive optional compatibilityを残す場合でも、「三材料一致」の主張は floor 経路に限定して書くべきである。

### P2

正しい。base 非束縛時に token を追加すると、A1 の長さ/index/full-vector predicate と A2 の closed grammar を破壊する。

### P3

そのままでは誤り、または仕様不足である。

現コードに prebuild の oracle 後再入 callsite はなく、一度の prebuild が cell loop より前にある。既存順序テストもある。ここへ単なる `assert pre_oracle=True` のような引数を足すのは、呼び手が常に定数を渡せるため「謳うだけの gate」になる。

本当に機械拒否するなら、oracle 開始時に不可逆遷移する phase capabilityか durable marker を `_prepare_floor_oracle_dependency()` と共有しなければならない。これは P1 の局所変更とは別設計である。

### P4

反対する。

`_v2_identity()` は configure policyを束縛していない一方、cache hit は `_v2_result()` で現在の generatorから argvを再生成する。identityを変えないと、旧 flag なし entryを hitして、flag付き argvを「この binaryを作った configure」として記録する。

依存 bytesが同じでも、禁止 policyを実行したという provenanceは同じではない。少なくとも base-bound buildだけ policy IDをpreimageへ追加すべきである。

### P5

「別型だから本 wave と無関係」という技術判断には反対する。

`ThirdParty.cmake:66-78` の custom commandは、oracle binding対象である `config.h` と `libkohler_masstree_json.a` を source tree内に生成する。さらに cell targetは `ccbench::masstree` を介して `masstree_build` に依存する。したがってこれは「oracle 後に oracle 判定材料へ書く経路」そのものである。

ただし、今回の題名を厳密に「FetchContent再 populate禁止」に限定するなら、P5を別 waveへ送る政策判断は可能である。その場合も残存経路として明示し、既存 postflightを維持する必要がある。

## 未解決・親の裁定が要る点

1. **P4を覆してbase-bound cache identityへpolicy IDを入れるか。**  
   推奨は入れる。入れない場合、旧 cache hit の reconstructed argv が実際のhistorical configureと食い違う限界を明示承認する必要がある。

2. **P5の再生成を今回の「材料変更禁止」に含めるか。**  
   含めるなら、configure直前だけでなく configure成功後、build直前にも同じ helperを再実行する。ただし完全なrace排除にはsource treeの書込権限制御が必要で、それはD425が別審査にした権威変更へ踏み込む。

3. **P3にruntime phase gateを本当に要求するか。**  
   現状の単一prebuildと順序テストでよいなら追加不要。直接late reentryまで拒否するなら、oracleとprebuildが共有する非恒真なphase capabilityの仕様が必要。

4. **generic `build_v2` のarchive省略互換を残すか。**  
   production floorは常にarchiveを渡すので本scopeは閉じられる。API全体でも三材料一致を要求するなら、baseとarchiveの同時指定を必須化し、既存互換テストを更新する必要がある。

## 総括

実装の中心は `buildcache.py` の二点である。

- `_v2_commands()` にbase束縛時だけ `-DFETCHCONTENT_FULLY_DISCONNECTED=ON` をexact 1本追加する。
- fresh configureの直前にHEAD、`config.h`、archiveを再観測し、不在または不一致ならCMakeを起動せず拒否する。

既存postflightはすべて残す。A1/A2の非base argvと凍結23成果物は変わらない。briefの閉包はcache-hit照合、floor postflight、`cmake --build` の再生成を落としており、exact consumer三項も閉じていない。

特にP4のidentity不変とP5の再生成scope外は、そのまま採用すべきではない。前者は旧cacheの虚偽provenance、後者はoracle判定済みconfig/archiveへの実書込み経路を残す。

指示どおり静的検査のみで、pytestやCMakeは実走していない。