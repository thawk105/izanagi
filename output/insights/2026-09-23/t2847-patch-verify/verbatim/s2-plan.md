## (P1)〜(P6) の判定

**起動器から既存経路を呼ぶ案は成立する見込みです。ただし依存物の供給に加え、masstree の事前 build と、Pegasus に存在する compiler の明示が必要です。** 今回は静的検査のみで、configure・build・発火の成功は未確認です。

以下、`s2`、`s3`、`s5`、`t152` はそれぞれ依頼にある `orchestrator/campaign/<driver>.py` を指します。その他の略記は `orchestrator/campaign/` 配下です。

| 前提 | 判定 | 根拠・補正 |
|---|---|---|
| P1 | **real** | s3 の PIN は `pin.CURRENT_PIN`、stock は `buildcache.build`、変異は直接 CMake（`s3_lock_coverage.py:53,198,258`）。s5 も同じ（`s5_permutation_coverage.py:50,231,293`）。`pin.py:31` は `e9e477c`。読み取った submodule HEAD は `e9e477ca1b55348ab4530de0b1cf663ce4555290`。 |
| P2 | **real** | s2 は `PIN="dff0f1e"`（`:63`）、main は clean/pin 照合（`:347`）後に trace/perf build と較正を行う（`:356,381`）。現 HEAD では pin 不一致。変異部分は `_broken_build_and_verify`（`:295`）で独立している。 |
| P3 | **部分的** | SHA と prefix の必須性、checkout 利用は正しい（`t152:827,833,441`）。現 source の直接 stream 出力は P/C/E（`external/ccbench/cc/silo/transaction.cc:432,602,698`）で、I emitter 不在という期待と一致。ただし「各 check が偽」は過大。変異４本の checks は I 行を要求するため偽の見込み（`t152:689,702,715,729`）だが、stock・abort・BOMB checks は別条件（`:659,670,676`）。構造的失敗なく最後まで走った場合に `all_pass=false` を期待する。 |
| P4 | **部分的** | 指定４ driver に sort-nonswo の列挙・実行経路はない。一方、**`SORT_VARIANT` は登録済み**（`condition_meaning_gate.py:180`）、意味の witness もある（`:331`）。「gate 未登録だから走れない」は **refuted**。 |
| P5 | **部分的** | 直接 CMake が依存供給をしない点は real。しかし stock の `buildcache.build` も自動 hydrate しない。環境による供給は可能な見込みだが、hydrate だけでは不足。さらに既定 compiler が Pegasus と合わない。詳細は下記。 |
| P6 | **部分的** | 各 main の既定 JSON は tracked path。今回の s2 関数経路は JSON を書かず dict を返す（`s2:334,339`）。他３本は起動器内で出力関数の束縛を替えれば repo 外へ出せるため、tracked JSON を上書き・復元する必要はない。 |

P5 は実行箇所ごとに次のようになります。

| configure の入口 | 必要な供給・注意 |
|---|---|
| s2 `_broken_build_and_verify` | `s2:308` の `applied` 内で gate、configure、build。configure argv（`:312`）には prefix、FetchContent source dir、toolchain の明示がない。環境を継承する。 |
| s3/s5 `_build_broken` | 同様。`s3:205,208,209,220`、`s5:238,241,242,253`。 |
| s3/s5 main の stock | 呼ぶのは **legacy `buildcache.build`**（`buildcache.py:3412`）。実 configure は `:3530`、実行は `:3540`。依存 source dir・prefix の注入や `IZANAGI_PEGASUS_THIRDPARTY_CACHE` の参照はない。`_run` は env 指定がなければ親環境を継承する（`:3791,3804,3807`）。 |
| t152 `_build` | `CMAKE_PREFIX_PATH` を検証・正規化して argv に明示（`t152:273,452`）。FetchContent source dir は明示しないため別途供給が必要。 |
| t152 `_preflight_condition_gates` | prefix 付き configure args を渡す（`:228`）。使い捨て checkout に patch を当てて gate を実行（`:237`）。FetchContent の供給も必要。 |
| 各 `_require_condition_gate` | **内部で実 CMake configure を行う。** 共通 argv は `condition_meaning_gate.py:1813`、実行は `:1823`。環境を置換しない subprocess（`:1691`）なので prefix/toolchain を継承する。 |

`buildcache.py:2630` の環境 prefix 処理、`:1963` の明示 prefix、`:1986` の source-dir 処理は **v2 側**です。今回 s3/s5 が呼ぶ `build()` の依存供給として引用してはいけません。cache 環境変数を解釈するのは `tools/pegasus/fetch_third_party.py:119` です。

環境による供給は次の組合せにします。

- `CMAKE_PREFIX_PATH=<gflags-install>:<glog-install>`：Unix の環境値はコロン区切り。gflags/glog の探索は `external/ccbench/cmake/Findgflags.cmake:5`、`Findglog.cmake:5`。CMake の公式仕様とも一致します。[CMAKE_PREFIX_PATH](https://cmake.org/cmake/help/latest/envvar/CMAKE_PREFIX_PATH.html)
- `CMAKE_TOOLCHAIN_FILE=<job内の絶対path>`：このファイルから３つの `FETCHCONTENT_SOURCE_DIR_*` を設定する。新規 build tree で明示指定がない場合、CMake 3.21 以降は環境値を既定として使います。[CMAKE_TOOLCHAIN_FILE](https://cmake.org/cmake/help/latest/envvar/CMAKE_TOOLCHAIN_FILE.html)

対象４ driver と共通 condition gate の上記 argv に、`-DCMAKE_TOOLCHAIN_FILE=` の空指定はありません。一方、再利用する MOCC helper の依存 install と `_common_configure_args` は空指定します（`s3_mocc_lock_coverage.py:204,266`）。後者は prefix/source dirs を argv に直接供給するため（`:267`）、環境 toolchain に依存させる必要はありません。

## 起動器の設計

job dir に **Python 起動器１本、実行中に生成する依存用 CMake ファイル１本**を置き、引数で `s3 / s5 / t152 / s2` を選びます。patch 適用、gate、verifier、checks は既存実装を呼びます。

準備の順序は次です。

1. repo の絶対pathを import path に加える。scratch/output は job dir 配下に置く。Python 版をジョブ内で確認する（`docs/pegasus-runbook.md:737`）。
2. `s3_mocc_lock_coverage._load_policy` と `_resolve_toolchain` を呼ぶ。既存 policy は `tools/pegasus/mocc_trace_v1_policy.json`。compiler の実体・version body の照合を維持する（`s3_mocc_lock_coverage.py:120,147`）。
3. `_prepare_dependencies(root, policy, cache_root, scratch, toolchain)` を呼ぶ。hydrate、gflags/glog source の照合、static install を既存処理に任せる（`:224`）。cache は CLI で絶対pathを受け取る。
4. **`silo_policy_coverage._prepare_build_dependencies` を呼ぶ。** fresh hydrate にない masstree `config.h` を、既存の stock build で生成する（`silo_policy_coverage.py:719`）。その stock checkout は patch を重ねない（`:546`）。生成物の実体は `external/ccbench/cmake/ThirdParty.cmake:57,66`。
5. 依存用 CMake ファイルには masstree/mimalloc/googletest の絶対 source dirs を設定する。prefix/toolchain 環境値を設定した後に driver を呼ぶ。マクロ、TRACE、最適化、判定条件はこのファイルに設定しない。

**compiler の補正も必要です。** `buildcache.DEFAULT_CC/DEFAULT_CXX` は gcc-13/g++-13（`buildcache.py:622`）ですが、runbook は Pegasus に g++-13 がなく、計算ノードに g++-12 があると記録しています（`docs/pegasus-runbook.md:729`）。環境 toolchain だけでは driver の明示 compiler argv を置き換えられません。

起動器による差し替えは、次に限定します。

| 対象 | 差し替え内容 |
|---|---|
| `s2.PIN` | `pin.CURRENT_PIN`。pin 照合を外さず、照合先だけ現 pin にする。 |
| s2/s3/s5 の `buildcache` 参照 | 元 module に委譲する薄い参照を渡し、`DEFAULT_CC/CXX` を検証済み compiler path にする。 |
| s3/s5 から呼ぶ `buildcache.build` | 元関数へ **明示 kwargs** `cc`, `cxx`, `cache_root=<job内fresh cache>` を渡す。admission/context/evidence はそのまま転送する。Python の既定引数は定義時に束縛されるため、`DEFAULT_*` の変更だけでは不足（`buildcache.py:3412`）。 |
| s3/s5 の `source_digest` 参照 | 元 `resolve_evidence` に明示 `cxx` を渡す薄い委譲。こちらも既定が g++-13（`source_digest.py:2413`）。 |
| s3/s5/t152 の `repo_output_root` | job 内 output を返す関数へ差し替える。 |
| s3/s5 の `ENV_TAG` | `pegasus`。既定は linux-baremetal（`s3:54`、`s5:51`）。 |
| t152 の設定 | 関数差し替えではなく、既存の `IZANAGI_T152_CCBENCH_SHA`, `IZANAGI_T152_CC/CXX` と prefix 環境値を設定（`t152:827`）。 |

この方式なら、build admission、source evidence の再照合、trace 検査も元の `build()` 内を通ります（`buildcache.py:3438,3557,3563`）。compiler は変更した事実を記録し、旧環境との同一性は主張しません。

patch の厳密さは変わりません。`patchharness.apply_patch` は `git apply`（`patchharness.py:204`）、`applied` は排他内の pin/clean 照合と終了時 revert（`:247`）、t152 の checkout は detached worktree（`:346,364`）です。offset 成功を fuzz 適用と混同しません。

s2 は `_assert_single_tenant`、`_assert_free_disk`、`assert_pinned_clean`、`_preflight_condition_gates` を既存どおり呼んでから変異関数２回へ進めます（`s2:345`）。返却後は **既存 gate3 の述語（`:411`〜`:419`）を同じ形で評価**します。新しい正しさ gate は設けず、較正全体の `all_pass` とも称しません。

## driver ごとの実行条件と期待の観測

| 対象 | 既存条件と観測 |
|---|---|
| **V01 norw** | `S2_FLAGS × extime=3` を渡す。100万 tuple、48 thread、zipf 0.9、rratio 50、rmw=false、max_ope 10（`pipeline.py:159`）。N、cycles≥1、verifier rc=1 を既存述語で確認（`s2:411`）。有限走で S なら未発生として記録し、成功へ丸めない。 |
| **V02 highkey** | 同じ S2 と legacy の２条件。legacy は `CorrectnessWorkload().flags` から extime を分離し、200 tuple、4 thread、rmw=true、max_ope 5、1秒（`pipeline.py:149`、`s2:397`）。S2 は N/cycles≥1、legacy は certified を期待（`s2:413`）。 |
| **V03 lockskip** | 200 tuple、zipf 0.9、rratio 50、rmw=true、max_ope 5、1秒。1 thread と4 thread（`s3:70`）。単独では cycles=0、X>0、I、入口/保持の両 reason（`:299`）。4 thread は X>0 を要求し、N 併発は許容（`:306`）。 |
| **V04 early-unlock** | 上と同じ1 thread 条件。cycles=0、I、X reason が `lock-lost-before-write` のみ（`s3:308`）。 |
| **V05 erase** | s3 の単独条件と同じ（`s5:68`）。cycles=0、I、P の size-changed>0、他 reason=0（`:331`）。 |
| **V06 swap** | 同じ条件。cycles=0、I、rcdptr-set-changed>0、他 reason=0（`s5:342`）。raw P 集計と verifier の照合も維持（`:159,351`）。 |
| **V09〜V12 write-intent** | 200 tuple、1 thread、zipf 0.9、rratio 0、rmw=false、max_ope 10、1秒（`t152:83`）。現 pin では I 行なしで S になりうる。旧 driver の変異 checks は I 行・I verdict・verifier rc=3 を要求するため、偽の見込み（`:689`）。 |

t152 main は変異だけでなく、stock single、2 thread の abort 条件、BOMB smoke を実行します（`t152:889`）。BOMB は S1/S3 を各1 worker、work_size=64、1秒の既存設定を維持します（`:107`）。これらを削る案にはしません。

s2 に渡す workloads は次です。

```python
legacy_flags = CorrectnessWorkload().flags
legacy = (
    {k: v for k, v in legacy_flags.items() if k != "extime"},
    int(legacy_flags["extime"]),
)
norw_workloads = {"s2": (dict(S2_FLAGS), 3)}
highkey_workloads = {"s2": (dict(S2_FLAGS), 3), "legacy": legacy}
```

2026-07-06 の highkey 記録に対応します。一方、2026-06-18 の norw は **50 tuple・4 thread・rmw=true・1秒**であり、この S2 再走と同条件ではありません（指定 insight `README.md:236,237`）。その1,310巡回を今回の期待件数にはしません。

成否と停止位置は区別します。

- **s2**：変異関数自体は verdict 不一致を例外にせず返します（`:329`）。判定は前述の gate3 述語。run 非zero、commit 証人不正、verifier JSON 不正は構造的失敗（`:165,171,215`）。
- **s3/s5**：preflight gate 拒否で stock より前に停止（`s3:245`、`s5:280`）。各変異 build 内でも再確認する。run/build/parse の例外は後続を止める。checks 不一致は全走後に JSON を書き、rc=1（`s3:293,328`、`s5:325,369`）。
- **t152**：全 preflight、stock と変異４ build の後に走る（`:846,856,873,889`）。構造的失敗は `_entrypoint` で rc=2（`:950`）。判定不一致は JSON を公開して rc=1（`:940`）。**rc=1だけを見て I の盲点を観測したとは扱わず、４本それぞれの run/trace/verifier を読む。**

## 出力の扱い

既定の tracked JSON は次です。

| driver | 既定 path |
|---|---|
| s2 main | `output/env/linux-baremetal/calibration/s2_verify_t48_skew0p9_rr50_rmw0.json`（`s2:423`）。同名 Markdown も出す。 |
| s3 | `output/env/linux-baremetal/calibration/s3_lock_coverage.json`（`s3:318`）。 |
| s5 | `output/env/linux-baremetal/calibration/s5_permutation_coverage.json`（`s5:359`）。 |
| t152 | `output/env/pegasus/characterization/t152_write_intent_coverage.json`（`t152:931`）。 |

**job 外へ逸らす案を推奨します。** `layout.repo_output_root` を import 後に変更するだけでは、各 driver の `from .layout import repo_output_root` の束縛は変わりません（`s3:46`、`s5:43`、`t152:37`）。各 driver の同名参照を直接差し替えます。

s2 は返却 dict と既存 gate3 判定を job dir に保存します。旧較正 JSON の形式や「較正済み」という意味を流用しません。stdout/stderr、起動 argv、compiler、依存準備結果も job の生出力として残します。

なお既存 driver は trace を清掃します（`s2:333`、`s3:233`、`s5:268`、`t152:582`）。この最小案で残るのは **driver JSON とログ**です。完全な raw trace 保存や、s2/s3 が返さない全 integrity 項目まで収集したとは書けません。

## 投入手順

起動器の想定名を `launch_patch_verify.py` とします。下記は author が作成後に使う argv 案です。`<PYTHON_ABS>` と `<CACHE_ABS>` は親が実在する絶対pathに確定します。

```text
<PYTHON_ABS> tools/pegasus/dispatch_compute.py --task generic --walltime 00:20:00 -- <PYTHON_ABS> /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-patch-verify/launch_patch_verify.py s3 --third-party-cache <CACHE_ABS>

<PYTHON_ABS> tools/pegasus/dispatch_compute.py --task generic --walltime 00:20:00 -- <PYTHON_ABS> /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-patch-verify/launch_patch_verify.py s5 --third-party-cache <CACHE_ABS>

<PYTHON_ABS> tools/pegasus/dispatch_compute.py --task generic --walltime 00:35:00 -- <PYTHON_ABS> /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-patch-verify/launch_patch_verify.py t152 --third-party-cache <CACHE_ABS>

<PYTHON_ABS> tools/pegasus/dispatch_compute.py --task generic --walltime 00:35:00 -- <PYTHON_ABS> /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-patch-verify/launch_patch_verify.py s2 --third-party-cache <CACHE_ABS>
```

**s3 → s5 → t152 → s2 の直列**とします。小さい既知の X/P 条件で依存供給を確認し、build 数の多い t152、trace 規模の大きい s2 へ進みます。各 job の終了・submodule 復元を確認してから次を投入します。t152 の予想された checks 不一致と、構造的失敗は分けて扱います。

generic は環境 allowlist が空（`dispatch_compute.py:155`）、cwd を repo root に固定し、bnode 以外では子を起動しません（`:1838`）。したがって **環境設定は起動器内**で行います。

`/usr/bin/env VAR=... <python> ...` を先頭に置くことも dispatcher の string-list 検査上は可能です（`:1573`）。ただし今回の prefix/toolchain path は依存準備後に決まるため、起動器内設定の方が小さくまとまります。

`hooks/guard_bash.py` が generic 内側 argv を綴りによって拒否しうる点は runbook に明記されています（`docs/pegasus-runbook.md:634`）。**上記 argv の受理は未実測**です。拒否されたら別綴りを抜け道にせず、同 runbook `:594` と `hooks/README.md` の正規手順に従います。

## sort-nonswo

**V07 は「その他：指定４ driver に実走経路なし・未実走」とする案を支持します。ただし理由を gate 未登録にはしません。**

指定 driver の patch 列挙は s2 `:84`、s3 `:63`、s5 `:60`、t152 `:64` で、sort-nonswo は含まれません。s5 に登録されているのは erase/swap だけです。

`SORT_VARIANT` は CMake cache 経路として登録済み（`condition_meaning_gate.py:180`）。しかし裸の破壊マクロを前提とする s5 の `_require_condition_gate` に名前を差し替えるだけでは、対応した実 build・発火条件・checks 一式にはなりません。

repo の patch 名参照で見つかった test は static validation isolation の対象列挙（`orchestrator/tests/test_silo_validation_isolation.py:24`）等で、patch を CCBench に適用して trace/verifier まで走らせる専用経路は確認できませんでした。sort oracle の `check_materialized_sort_swo`（`sort_swo_oracle.py:3216`）も、V07 の CC 実走の代替には数えません。

既存記録は16要素以上で release/ASan とも hang（`patches/README.md:430`）。指定 insight の期待も未定義動作による複数の可能性であり、固定 verdict ではありません（`README.md:188`）。今回、新しい sort 実行器は追加しません。

## 所要の見込み

各 job で依存物を fresh に準備する保守的な案です。以下の「build」は CMake build 呼出し数で、各 build 内の依存コンパイルを別件には数えません。

| job | CCBench build | 別途依存 build | condition gate configure |
|---|---:|---:|---:|
| s3 | 準備stock 1＋driver stock 1＋変異2＝**4** | gflags/glog＝2 | preflight 2件＋変異内2件、それぞれ requested/control＝**8** |
| s5 | 同じく **4** | 2 | **8** |
| t152 | 準備stock 1＋driver stock 1＋変異4＝**6**。driver stock は YCSB/BOMB の2 target | 2 | preflight 4件＋変異内4件、それぞれ2 configure＝**16** |
| s2 | 準備stock 1＋変異2＝**3** | 2 | preflight と変異内で計4 gate。supply/meaning が configure を共有しないため **16** |

gate の requested/control は `condition_meaning_gate.py:1999,2004`。s2 の非共有呼出しは `s2:105,108`、meaning 側の追加 configure は `condition_meaning_gate.py:3375` です。これに各 CCBench/依存 build の configure が加わります。

時間について確認できた旧実測は、s2 の norw verifier **127.60秒**、highkey S2 **126.16秒**、legacy **12.32秒**です（`output/env/linux-baremetal/calibration/s2_verify_t48_skew0p9_rr50_rmw0.json:142,171,194`）。現 pin・Pegasus・現 verifier の時間へそのまま転用しません。

**推測**として初回要求 walltime を 20＋20＋35＋35＝110分としました。build 時間の現環境実測はなく、これは十分性を保証する値ではありません。再走・開発検査を含めて２ node 時間以上になる見込みなら、brief 第3項に従い、親が job Elapse の実測単価で再見積りしてユーザー確認を行います。要求 walltime が110分というだけで、その境界を満たしたとは扱いません。

## 未確認点

- 計算ノード上の CMake が3.21以上か、選択 compiler と policy の照合が通るか、cache が必要な５依存を満たすか。
- 環境 toolchain 経由の source-dir 供給が、全 gate の requested/control configure と前処理で通るか。
- t152 の現 pin における compile、BOMB smoke、４変異の実 verdict。I emitter 不在だけから完走や certified を保証できない。
- s2 の schedule 依存の発火、現 verifier の所要・メモリ・trace 容量。
- 上記 generic argv の hook 受理、queue の利用可能性。
- raw trace は既存 driver が削除するため、後から全 verifier 出力を再取得することはできない。

11本の厳密な apply 成功は既存資料で確認できますが、今回再実行していません（指定 `raw/apply-check-e9e477ca.txt:5`〜`:11`、`:13`〜`:16`）。これを build・発火の証拠にはしません。

## 総括

採用案は、**既存依存準備＋stock 準備 build＋環境 toolchain/prefix＋compiler の明示的な委譲**を job 外起動器にまとめ、s3/s5/t152 の既存 main と s2 の変異関数・既存 gate3 述語を使うものです。

10本を４ job で実走し、sort-nonswo は経路不在による未実走理由を付けます。tracked 実装・verifier・tests の編集、checks の削除、gate の緩和を前提にしません。