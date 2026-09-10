結論は、job-local な `FETCHCONTENT_BASE_DIR` を一つ作り、依存 prebuild と全 floor cell build へ明示注入する案です。cell ごとの `_deps` 案は、現行 `build_v2` では configure 用 staging が oracle より後に作られ、最後に削除されるため成立しません。

## プラン

### 1. 物理 tree の一本化

| 案 | 実コード上の実体 | 評価 |
|---|---|---|
| job-local 共有 base | `<base>/masstree-src` を依存 prebuild と全 cell configure が共有 | 採用。oracle と binary build を同じ実体へ束縛できる |
| cell ごとの `_deps` | v2 では `<contract-dir>/.staging-*/_deps/masstree-src` | 不採用。oracle 時点では未作成、cache hit では作成されず、fresh build 後は staging ごと削除される |

`orchestrator/campaign/s8b_floor_campaign.py:1941-2028` を次のように変更する。

1. production で `sort_best` が一つでもある場合、`tools/pegasus/floor_campaign.sh:97-101` が create-only で用意する `$TMPDIR` 配下へ `tempfile.mkdtemp()` で一つだけ base を作る。絶対 path、非 symlink directory、実効 UID 所有、repo 外、正規化済み realpath を要求する。production では `$TMPDIR` 不在を閉じた preflight failure とし、汎用 `/tmp` へ暗黙 fallback しない。
2. 現在の `third_party_cache_root` と `_resolve_floor_oracle_dependency()` (`s8b_floor_campaign.py:1582-1611`) は、外部共有 cache を oracle 専用に選ぶ経路なので廃止する。単体テスト用には `fetchcontent_base_dir` の明示注入 seam を置くが、CLI や環境変数から共用ディレクトリを受け取る production 経路は作らない。
3. base は環境変数として export せず、各 CMake configure に `-DFETCHCONTENT_BASE_DIR=<canonical-base>` を一個だけ渡す。他 campaign が偶然同じ `_deps` を使うことを避ける。
4. oracle root は固定的に `<base>/masstree-src` とする。`FETCHCONTENT_SOURCE_DIR_MASSTREE` を含む `FETCHCONTENT_SOURCE_DIR_*` は一切渡さない。

`FETCHCONTENT_BASE_DIR` は I1 に抵触しない。CMake 3.22.1 の `FetchContent.cmake:443-454,764-803` は、Declare の URL/tag を維持したまま source/build/subbuild の親だけを変え、`FetchContent.cmake:1217-1228` が `<base>/masstree-{src,build,subbuild}` を導出する。外部 source を権威として差し込む `FETCHCONTENT_SOURCE_DIR_*` とは異なり、`ThirdParty.cmake:42-47` の repository と SHA pin を迂回しない。

### 2. 二本目以降の configure が再 fetch しない根拠

`external/ccbench/cmake/ThirdParty.cmake:52-55` は各 top-level configure で `FetchContent_Populate(masstree)` を評価する。populate 済み global property は別 configure 間では共有されないが、共有 base により次が永続する。

- subbuild は `<base>/masstree-subbuild`、source は `<base>/masstree-src` になる (`FetchContent.cmake:1217-1228`)。
- clone script は、概ね  
  `<base>/masstree-subbuild/masstree-populate-prefix/src/masstree-populate-stamp/`  
  以下の `masstree-populate-gitinfo.txt` と `masstree-populate-gitclone-lastrun.txt` を比較し、同一なら clone を省く (`ExternalProject.cmake:1303-1308,1358-1368,2705-2729`)。
- update step 自体は `ALWAYS` (`ExternalProject.cmake:3034-3040,3084-3094`) だが、raw SHA が既存 HEAD と一致すれば fetch 前に return する (`ExternalProject-gitupdate.cmake.in:23-69`; fetch は `:95-102`)。
- `masstree_build` の outputs は同じ source tree 内の `config.h` と archive であり (`ThirdParty.cmake:57-78`)、存在する限り二本目の target buildでは custom commandを再実行しない。

したがって、宣言 metadata が同一、HEAD が raw pin、subbuild stamp が残存、configure が逐次、という条件では既存 clone を再利用して network fetch しない。ただしこれは手元の CMake 3.22.1 の静的根拠なので、計算ノードで後述の一 job probe を land gate とする。

並行性について、floor cell は `s8b_floor_campaign.py:2039-2115` の同期 `for` 内で `prepare`、`build_fn` を一件ずつ完了させる。他 campaign との衝突は campaign claim だけに依存せず、PBS job ごとに異なる `$TMPDIR` と、その中の一意な base で防ぐ。共有 base は masstree 以外の FetchContent build dir も共有するため、将来 cell build を並列化する場合はこの設計を再審査する。

### 3. oracle 前の masstree build

実行順を次に固定する。

`phase-preflight marker → toolchain binding → pinned CCBench checkout → configure → masstree_build → dependency verification → oracle → cell build → dependency再検証 → binary admission`

- `s8b_floor_campaign.py:1980-2028` で toolchain binding 後、既存 dependency verification の位置へ prebuild を挿入する。
- `patchharness.checkout(ccbench_pin)` (`orchestrator/campaign/patchharness.py:346-379`) で exact pin の使い捨て CCBench worktreeを作る。cell patch は masstree materialization に不要である。
- `orchestrator/campaign/buildcache.py:1076-1097` 付近へ、例えば `prepare_masstree_fetchcontent()` という限定 helper を置く。呼び出すのは floor campaign、実際に `_run()` で CMake を起動するのは helper とする。
- helper は共通 configure argv builder を `build_v2` と共有し、次を実行する。

  - `cmake -S <pinned-ccbench> -B <prebuild-dir>`
  - `-DFETCHCONTENT_BASE_DIR=<base>`
  - `-DCMAKE_BUILD_TYPE=Release`
  - `-DENABLE_SANITIZER=OFF`
  - binding 済みの `CMAKE_C_COMPILER`、`CMAKE_CXX_COMPILER`
  - 現行 `build_v2` と同じ `CMAKE_PREFIX_PATH` の明示値または環境継承
  - 続いて `cmake --build <prebuild-dir> --target masstree_build -j <site-jobs>`

意味上の最小集合は `-S`、`-B`、`FETCHCONTENT_BASE_DIR`、CXX compiler、および `CMakeLists.txt:33-34` の gflags/glog 解決に必要な prefix である。C compiler、Release、sanitizer は target固有には不要でも、cell configure と同じ toolchain 契約に揃えるため渡す。genome define と `CCBENCH_TRACE` は `masstree_build` に不要なので渡さない。

helper を floor module 内へ置かない理由は、`orchestrator/tests/test_s8b_floor_campaign.py:2893-3001` が `buildcache.py` 以外で `"--build"` を持つ関数を direct CMake materializer として閉集合検査するためである。helper は `buildcache._run()` (`buildcache.py:1873-1889`) を使い、heavy execution site gate を迂回しない。

configure failure と target failureは、例えば `floor-dependency-fetchcontent-configure-failed` と `floor-dependency-fetchcontent-build-failed` の二つだけを `_FLOOR_DEPENDENCY_PREFLIGHT_DETAIL_CODES` (`s8b_floor_campaign.py:184-204`) に追加する。outcome は既存閉集合の `invalid-path` を使い、新しい自由形式 outcome は増やさない。いずれも既存 `_persist_floor_oracle_preflight_failure()` へ流し、`OracleStatus.UNAVAILABLE`、oracle 未実行、cell build 未実行を保つ。

### 4. 全 cell build への注入と cache identity

`orchestrator/campaign/buildcache.py` は次の範囲を変更する。

- `BuildResult` (`:620-637`) に additive default `fetchcontent_base_dir: str = ""` を追加する。
- `_v2_commands()` (`:1076-1097`) に canonical base を受ける keyword を追加し、非空時だけ `-DFETCHCONTENT_BASE_DIR=<base>` を正確に一個生成する。
- `_v2_identity()` (`:750-770`) の preimage に、非空時だけ canonical base を入れる。空の既定 caller では既存 preimageと digestを一 byte も変えない。
- `_v2_result()` (`:1100-1117`) と cache hit/fresh の両 return (`:1383-1386,1505-1509`) に同じ base を返す。
- `build_v2()` (`:1230-1509`) は相対 path、NUL、symlink base、非 directory を拒否する。

job-local path を cache preimage に入れないと、過去 job の別 masstree tree で作った binary が cache hit し、「今回 oracle が見た物理 tree で作った」と主張できない。job path は create-only なので、同一 base の cache hit は同じ job 内に閉じる。

`s8b_floor_campaign.py:2115-2125` では、sort cell が一つでもある run の全 `build_fn` 呼び出しへ同一 base を渡す。返却後、binary admission (`:2148-2160`) より前に次を要求する。

- `BuildResult.fetchcontent_base_dir` が期待する canonical base と一致する。
- `configure_argv` に期待する `FETCHCONTENT_BASE_DIR` token が正確に一個あり、`FETCHCONTENT_SOURCE_DIR_*` が一個もない。
- `_verify_floor_oracle_dependency_source()` を再実行し、oracle 前の HEAD、config hash、source directory の `st_dev/st_ino` と一致する。

`st_dev/st_ino` は runtime の置換検知だけに用い、portable artifact や oracle receipt の機体非依存 schema には入れない。post-build drift は Oracle PASS を使って先へ進めず、binary admission 前に campaign を fail-closed させる。

### 5. identity 主張

`_verify_floor_oracle_dependency_source()` (`s8b_floor_campaign.py:1427-1579`) は root suffix を `<base>/masstree` から `<base>/masstree-src` へ変える。それ以外の防壁は維持する。

- repo 外の canonical root、非 symlink directory: `:1448-1510`
- `git rev-parse --show-toplevel` と exact root 一致: `:1515-1564`
- HEAD と共有 policy pin の一致: `:1565-1572`
- regular `config.h` の sha256: `:1392-1424,1573-1579`

CMake の clone script は通常の `git clone` 後に raw SHA を checkout する (`ExternalProject.cmake:1310-1344`)。したがって masstree source の `.git` は directory で、HEAD は detached になる。`patchharness.checkout()` が作る CCBench worktree の `.git` file とは別物である。identity判定は `.git` の表現へ依存させず、git top-level と commit object を権威にする。

`ThirdParty.cmake:84-87` は同じ `masstree_SOURCE_DIR` を include root と archive path に使用する。oracle receiptも `dependency_root_realpath` と `config.h` hash を記録する (`sort_swo_oracle.py:1368-1385`)。よって、共有 base token、pre/post root identity、HEAD、config hashを合わせれば I6と同じ強さに加え、「oracle と build が同じ directory entry を使った」と主張できる。

ただし dirty/ignored generated filesや archive bytesの clean-tree identityまでは主張しない。これは T-1129 の範囲である。計算ノード probeで同一性を確認できなければ、root、HEAD、config hash、configure argvを診断として記録しても certified claimには採用せず、`same_root=false` として停止する。

### 6. portable record、予約枠、consumer

- `s8b_floor_campaign.py:248,2206-2242,2302-2343` に `${FETCHCONTENT_BASE_DIR}` placeholderを追加する。runtime recordに private `_fetchcontent_base_dir` を持たせ、`/scr/<job>/...` を durable `configure_argv` へ漏らさない。
- dependency prebuild は現在の予約式 (`:250-260,844-881`) に含まれていない。configure cap 900秒と target cap 900秒を一 run に一回だけ加え、式を  
  `shared_dependency_prebuild_s + cell_count * (...)`  
  に変える。journal (`:4349-4357`) に二つの cap と条件を記録する。sort cell がなければ加算はゼロとする。
- `resolve_oracle_environment()` (`sort_swo_oracle.py:1102-1218`) は変更しない。floor は既に `prepare_cell` へ dependency rootを明示注入できる (`s1_direct_comparison.py:592-597,681-685`) ため、既定候補列を変える必要がない。
- したがって、引数なし callerである `p3_s4_loop_sort.py:174-176`、module import時の `test_sort_swo_oracle.py:20`、引数が既定 `None` になりうる通常の S1経路、resolver直接テスト `test_sort_swo_oracle.py:257,380,404,444` は不変である。
- `build_v2` の新引数は空を既定とするため、別 production callerの `pipeline.py:887-894` も既存挙動を保つ。

### 7. 編集面と凍結 pin 閉包

実装編集面は次の5ファイルに限定する。

1. `orchestrator/campaign/buildcache.py`
2. `orchestrator/campaign/s8b_floor_campaign.py`
3. `orchestrator/tests/test_buildcache_v2.py`
4. `orchestrator/tests/test_build_site_gate.py`
5. `orchestrator/tests/test_s8b_floor_campaign.py`

`external/ccbench/cmake/ThirdParty.cmake`、`s1_direct_comparison.py`、`sort_swo_oracle.py`、`test_sort_swo_oracle.py` は編集しない。

静的検算結果は次のとおり。

- `s1_direct_comparison.py` の実 sha256 は `38ed8790807e3f1aa7516fd286b365dfe2dc45c18f05fb4566970a587db75e7f` で、`test_s8b_oracle_manifest.py:86-87` の materializer literal と一致した。
- 同テストの `PIN_GATE_SPEC_RAW` (`:66-99`) を独立 hash した値は `PIN_GATE_SPEC_SHA256` (`:61-63`) と一致した。S1を編集しないため両方とも更新不要である。
- 現在の s8b floor sha256 は `df4119891707eef54226ade96f7ff336cc78d7a71ffc69246d2c26829ce0a044`、buildcache は `6855d71b77ec8f6e35fbae5317f59db329dba098140e79b4342c8e17665f0bea`。限定検索ではこれらを固定 literal とする側はなかった。
- ただし親 brief §4 I3 の列挙外に、`buildcache.py` は T-126 の required code identity に含まれる (`orchestrator/qualification/contract.py:38-76`)。実行時に commit blobを hashして記録・再検証する (`qualification/identity.py:130-144`) ため golden更新は不要だが、新 commitのqualification identityは当然変わる。
- `test_env_contract.py:83-100` は buildcache と floor moduleを環境固有 literal禁止面として読む。bytes pinではないが、`/scr` や機体固有 pathをソースへ直書きしない必要がある。
- `s8b_oracle_manifest.py:53-60,430-468`、`test_s8b_oracle_report.py:53-60,216-224`、`test_s8b_oracle_driver.py:73-80,1700-1712` は実行時計算であり、追加の golden literalではない。

## 親 brief の訂正

| 項目 | 訂正 |
|---|---|
| A2 | verifierの定義開始は `s8b_floor_campaign.py:1427`。親の `1429` は signature途中からで、実範囲は `1427-1579` |
| A7 | `prepare_cell` が作る `cache_root` は `s1_direct_comparison.py:622,720` にあるが、floor buildはそれを使わず、独自の `out_root/s8b-build-cache` を `s8b_floor_campaign.py:1953` で使う |
| A9 | resolverの成功 returnは `sort_swo_oracle.py:1218`。ancestor loopは `:1140-1145` で、親の終端 `1210` と `1141-1146` はずれる |
| A11 | 「cellごとの最終 build dir配下に `_deps`」は誤り。fresh v2 configureは nonce staging (`buildcache.py:1388-1429`) で行い、stagingは `:1471-1472` で削除する。最終 bdirには clean copyされた binaryとcompletionだけが残る。また digestはcell IDそのものを含まない (`:750-770`) |
| A12 | legacyでも `:1561-1569` は cache hit用に再構成する表示 argv。fresh configureの実体は nonce staging (`:1614-1642`) で、`:1676-1677` で削除される |
| P1 | 「buildをcache treeへ寄せるには SOURCE_DIRが必要」は広すぎる。`FETCHCONTENT_BASE_DIR` ならCMakeのpin付きclone機構を維持したまま全 buildを一つのCMake管理treeへ寄せられる |
| P2 | 共有案を採用するが、再利用根拠は configure間の `masstree_POPULATED` 共有ではない。永続 subbuild、clone stamp、raw SHA updateの早期 returnである |
| P3 | helperの所在は任意ではない。direct CMake閉集合テスト `test_s8b_floor_campaign.py:2893-3001` により buildcache seamが適所。また親案にはprebuild分のwalltime予約とcache hit閉包が欠けている |
| P4 | HEAD/config主張は維持可能。ただしCMake cloneは `.git/` directory、raw SHA detached HEADであり、post-buildのroot inode/config再検証が必要。clean-treeやarchive hashはT-1129外 |
| P5 | 単体テストだけでは設計の生死は決まらない。実機CMake版で二本目configureがsourceを置換・fetchしないことと、代表binaryのinclude/archive pathを一 jobで確認する必要がある |
| P6 | 訂正なし。resolverを変更しないため列挙されたconsumerへの影響を回避する |
| §4 I3 | S1のgolden説明は正しいが、新編集面buildcacheにはT-126の実行時Git blob identityがある。literal更新は不要だが閉包上は記録すべき |

A1、A3〜A6、A8、A10は実コードと一致した。A13は今回再実測していないが、worklog 560の記録とコード上の旧root/new build stagingの分離に矛盾はなく、親の既存実測としてのみ採用する。

## 未決

設計択一は未決なし。共有 job-local base案を採用し、cellごとの `_deps` 案は現行 buildcache lifecycleでは不成立として棄却する。

land前に未確定なのは、計算ノード上のCMake実装が手元の3.22.1と同じ再利用挙動をするかという環境事実だけである。一つの単独dispatch jobで、repo外のprobeとして次を測る。

1. 一意な `$TMPDIR`、共有 base、二つの異なる CCBench checkout/build dirを作る。
2. Aでconfigureと`masstree_build`を実行し、sourceのrealpath、`st_dev/st_ino`、`.git`種別、detached HEAD、HEAD SHA、config/archive hash、clone stampを記録する。
3. Aのcloneのoriginを無効URLへ変えた後、Bを同じbaseでconfigureする。B成功、source inode不変、clone stamp不変なら再cloneもupdate fetchもなかったと判定する。
4. oracleを同じrootへ明示束縛して実行後、Bで代表 `sort_best` binaryを一つbuildする。
5. `CMakeCache.txt`、compile flags、`link.txt`からinclude rootとarchiveが同じ `<base>/masstree-src` を指すことを確認し、build後にHEAD、inode、config hashを再照合する。

これが失敗した場合は実装をlandしない。初回populate後の `FETCHCONTENT_FULLY_DISCONNECTED=ON` 追加を再検討して再probeするか、build_v2のconfigure lifecycleをoracle前後に分割する。存在しない最終cell `_deps` へ戻す案はfallbackにしない。

## テスト計画

| nodeid候補 | 落とす欠陥 |
|---|---|
| `orchestrator/tests/test_buildcache_v2.py::test_v2_fetchcontent_base_is_canonical_single_define_and_in_preimage` | baseの未正規化、define重複、cache identityへの束縛漏れ |
| `orchestrator/tests/test_buildcache_v2.py::test_v2_fetchcontent_base_change_misses_cache_and_empty_default_preserves_identity` | 別物理treeのcache hitと、既存caller全体の不要なdigest破壊 |
| `orchestrator/tests/test_buildcache_v2.py::test_prepare_masstree_fetchcontent_configures_then_builds_exact_target` | oracle前prebuildの順序違反、全binary build、誤target |
| `orchestrator/tests/test_buildcache_v2.py::test_prepare_masstree_fetchcontent_never_emits_source_dir_override` | I1違反の`FETCHCONTENT_SOURCE_DIR_*`復活 |
| `orchestrator/tests/test_build_site_gate.py::test_masstree_prebuild_routes_both_commands_through_heavy_site_gate` | helperからの`subprocess`直呼びと実行場所gate迂回 |
| `orchestrator/tests/test_s8b_floor_campaign.py::test_production_floor_prebuilds_one_shared_dependency_before_oracle_and_all_cell_builds` | prebuild重複、oracle先行、cellごとのbase分裂。規律2のpositive経路 |
| `orchestrator/tests/test_s8b_floor_campaign.py::test_floor_shared_dependency_preserves_head_inode_and_config_through_build` | root置換、HEAD drift、config driftを見逃すidentity弱体化 |
| `orchestrator/tests/test_s8b_floor_campaign.py::test_floor_dependency_prebuild_failure_persists_unavailable_without_oracle_or_build` | prebuild失敗をPASS/skipへ落とす規律2違反。negative経路 |
| `orchestrator/tests/test_s8b_floor_campaign.py::test_floor_rejects_build_result_without_exact_fetchcontent_base` | 注入build seamがbaseを無視してもbinaryを受理する欠陥 |
| `orchestrator/tests/test_s8b_floor_campaign.py::test_floor_rejects_dependency_replacement_or_config_drift_after_build` | oracle後のTOCTOUと別tree binary admission |
| `orchestrator/tests/test_s8b_floor_campaign.py::test_floor_portable_argv_projects_fetchcontent_base` | `/scr/<job>`のdurable artifact流出とplaceholder衝突 |
| `orchestrator/tests/test_s8b_floor_campaign.py::test_floor_reservation_includes_one_shared_dependency_prebuild` | prebuild時間を予約せずwalltime envelopeを過小申告する欠陥 |
| `orchestrator/tests/test_s8b_floor_campaign.py::test_materializer_registry_covers_all_python_build_launches` | helperを許可外moduleへ置く、または新direct CMake起動を増やす欠陥 |
| `orchestrator/tests/test_sort_swo_oracle.py::test_no_optional_or_none_pass_api_and_no_unbounded_fixture_enumeration` | resolver既定候補や環境名を不用意に変更する回帰 |
| `orchestrator/tests/test_sort_swo_oracle.py::test_s1_sort_best_runs_same_oracle_before_source_materializer` | oracle gateの順序や明示environment注入を壊す回帰 |

今回は指示どおりpytestを実行しておらず、上記は静的検査に基づく計画である。

## 総括

- 推奨案は、一 jobにつき一つのcanonical `FETCHCONTENT_BASE_DIR`を依存prebuildと全floor buildで共有する方式である。
- oracle rootはCMakeが作る同じ `<base>/masstree-src` へ明示束縛する。
- cellごとの `_deps` 案は、実体が一時stagingにありoracle前には存在せず、build後に削除されるため棄却する。
- masstree prebuildはfloorが指示し、buildcacheの限定helperがsite gate経由で実行する。
- BASE_DIRはCMakeのrepositoryとSHA pinを維持するため、禁止されたSOURCE_DIR配線には当たらない。
- cache identity、configure argv、pre/post inode・HEAD・config hashの全てを同じbaseへ束縛する。
- resolver既定候補は変更せず、floor以外のconsumerを無影響に保つ。
- golden materializer hashとgate hashは影響なし。buildcacheのT-126実行時code identityだけが新commitに追随する。
- 最大のリスクは、計算ノードのCMakeで共有subbuildの再利用条件が異なる可能性であり、一 job probeをland gateとする。