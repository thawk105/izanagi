## 計算ノードで落ちる箇所

以下、`probe.py`／`probe.pbs` は指定の t316 probe、`test.py` は `test_t316_sandbox_probe.py`、`plan` は `s2-plan-out.md`、`receipt` は `0:999027.nqsv/receipt.json` を指す。静的検査のみであり、pytest・hydrate・prepare の実走結果ではない。

[B-1] refuted — Python 3.10 と `-I` が hydrate の直接の障害になる、という疑いは否定できる。

`fetch_third_party.py:52` の `_driver_module` は必要な二つの import root を自分で挿入する。`PYTHONPATH` は不要。fetch CLI、`silo_ladder_rung1.py`、`buildcache.py` 全体を `ast.parse(..., feature_version=(3,10))` で構文検査し、3.10 非対応構文は検出されなかった。

`probe.pbs:20` は Python 3.10 を選び、`:24` で版を検査する。receipt の `observations.S6.toolchain.tools.python3` は `/usr/bin/python3.10`、`Python 3.10.12`、inside/outside とも rc=0。plan の `sys.executable -I -B` は適切。ただし構文検査は、推移的 import 全体の実行成功を証明しない。

[B-2] refuted — 指定 PATH では git／cmake／compiler が解決しない、という疑いは当該受領証では支持されない。

receipt の `observations.S6.toolchain.tools` は次を記録し、全て inside/outside rc=0。

| tool | 実体 |
|---|---|
| cmake | `/usr/bin/cmake`、3.22.1 |
| C | `/usr/bin/x86_64-linux-gnu-gcc-11` |
| C++ | `/usr/bin/x86_64-linux-gnu-g++-11` |

git は toolchain field の対象外だが、`source_identities.*.status`／`replace_refs` と `execution_binding` の成功が、同じ probe 環境での実行を裏づける。なお host PATH は正確には **shim＋INTERPRETER の dirname＋`/usr/bin:/bin`**（`probe.pbs:102`）。sandbox PATH と同一表記ではない。

`observed_toolchain_manifest` は先頭行取得と全文取得を別々に行う（`buildcache.py:1218,1227,1276`）。既存 toolchain dict の流用を避ける plan は正しい。

[B-3] refuted — `site=None` が bnode031 を拒否する、という疑いは否定できる。

`site_policy.py:17,40` の `^bnode[0-9]+$` に `bnode031` は一致し、`PEGASUS_COMPUTE` になる。`buildcache.py:1896,2077` の既定 jobs は affinity に従う。receipt の `observations.S1.exclusivity_evidence.cpu_affinity` は 0〜47 なので、同じ affinity なら **`-j 48`**。テストでは `conftest.py:239` の中和後は OTHER、既定は16。

ただし masstree 内部は `ThirdParty.cmake:71` の **数値なし `make -j`**。外側の `-j 48` が内部 make の並列度上限まで保証するわけではない。

[B-4] real — prepare の configure は本番共有 configure と同じ環境抑制を持たない。

`buildcache.py:2069` の固定 argv には、probe の `:1855` にある `CCBENCH_CCACHE=OFF`、launcher 空指定、toolchain file 空指定、CXX flags 空指定がない。`CMakeLists.txt:22` は ccache を既定 ON とし、見つかれば launcher を設定する。したがって **prepare も同じ configure 条件になる、という一般化は不可**。

一方、`dependency_prefix` は `buildcache.py:2056,2067` で正準化され `-DCMAKE_PREFIX_PATH=...` になる。outside install 後に渡す順序なら、`CMakeLists.txt:33` の gflags/glog 探索に使える。receipt の既存 outside configure も同じ install prefix で rc=0。

是正：固定 helper のまま進める場合、追加 define がないことを既知の差として残し、実走の prepare 到達で確認する。現資料から「必ず落ちる」とは判定しない。

[B-5] refuted — scratch の兄弟に作る空 staging が hydrate に拒否される、という疑いは否定できる。

`fetch_third_party.py:143` は cache と staging の包含関係を拒否する。`/scr/<S>` と `/work/.../cache` は重ならない。`:524` は既存の実 directory を受理し、`:632` は各 source が未配置なら作成へ進む。空の `TemporaryDirectory` で成立する。

receipt の scratch `/scr/t316-0_999027.nqsv-wr6pkekl` と requested `/scr/izanagi_wt_oqsc8t8u/wt` は、当該実行で `/scr` 直下に一時 directory を作れた証拠である。

[B-6] refuted — source override を S に向けるだけで FetchContent が必ず S へ書く、とはいえない。

`ThirdParty.cmake:54,112,136` は masstree／mimalloc／googletest の FetchContent 呼び出し。source override と binary directory は別であり、`FETCHCONTENT_BASE_DIR` 未指定なら後者は各 build の `_deps` に分かれる。S を binary base にする必要はない。

明示的に S へ書くのは `:66` の masstree custom command。OUTPUT は **archive と config.h の両方**、DEPENDS はなく、`:78` の custom target が両 OUTPUT に依存する。両方を prepare が生成済みなら、Makefile の依存関係上、custom target があるだけで生成コマンドが毎回走る構造ではない。

これは親の説明を支持する。ただし指定資料だけでは mimalloc/googletest 内部の全書込先までは検査できず、実際の inside build が最終確認になる。

[B-7] real — 「98秒＋十数秒なら予算内」は見積りであり、実測上限ではない。

指定 receipt のトップレベル `elapsed_ns` は **93.276秒**。98秒が別の外部計時なら、その出所を分ける必要がある。outside configure 自体は **0.701秒**。

`facts-offline-supply.md:35` の85秒は hydrate CLI の計時ではなく、hydrate 済み木の NFS 向け `cp -a`。`:39` の hydrate CLI 実測は Lustre 宛 **15.75秒**。`mocc_trace_pilot.sh:1534` の `timeout 20` は設定値であり、今回の5本の `/scr` 実測上限ではない。

作業見積りとしては、hydrate＋prepare に **約30〜60秒追加**は妥当な仮置き。ただし厳密な下限は追加処理時間が正であることだけで、成功所要の実証済み上限はない。plan の subprocess timeout 合計上限は通常 **1200＋300＋1200＝2700秒**だが、manifest・identity・関門・cleanup を含む S6 全体の上限ではない。

## 配線テストの偽の緑

[B-8] refuted — local cache repo から実 hydrate を通せない、という疑いは plan が解消している。

policy に local URL は使えない（`silo_ladder_rung1.py:894`、`fetch_third_party.py:84`）。しかし plan は cache の origin を policy と一致する HTTPS URL にする。

`_verify_cache` はその HTTPS origin を検査（`:541`）、clone は **local cache path** を `protocol="file"` で使用（`:652`）、staging の origin は local cache path と比較する（`:668,691`）。通常の非 bare repo で成立する設計であり、HTTPS origin の設定自体はネットワーク取得を起こさない。5本全て必要という plan の修正も正しい。

[B-9] refuted — prepare を飛ばす変異が必ず生き残る、という疑いは plan の fixture 変更後には当たらない。

現 fixture（`test.py:1793`）には masstree 生成物を要求する仕組みがない。しかし plan `:220` は build 時の `config.h` 生成、`:223` は stock `transaction.cc` の `#include <config.h>`、`:225` は configure 時には生成しないことを明示している。

実装時には出力先を **`${masstree_SOURCE_DIR}/config.h`** と明記すること。これと include directory が揃えば、prepare 省略は build より前の関門 preprocess で赤になる。prepare の実 return 観測だけでなく、生成前不在・生成後実在の assertion も維持すべき。

[B-10] real — plan の最小 fixture は package prefix 欠落と archive 欠落を見逃す。

現 dependency fixture は CMakeLists を `share` に install するだけ（`test.py:1836`）。plan は実 FetchContent を足すが、gflags/glog の `find_package` と package config の install は指定していない。したがって **prepare から dependency_prefix を落としても緑になり得る**。

また plan `:220` の OUTPUT は config.h だけ。本番の二つの OUTPUT（`ThirdParty.cmake:67`）を再現せず、archive 未生成による inside 再実行を検出できない。

最小是正：

- fixture dependency に小さい package config を install させ、CCBench fixture でその prefix からの `find_package(... REQUIRED)` を要求する。
- masstree custom command に archive 相当の第二 OUTPUT を追加し、両 OUTPUT の実在と inside で生成コマンドが再実行されないことを確認する。

[B-11] refuted — 既存 gate failure が prepare failure に化ける問題は plan が明示的に対処している。

`test.py:1810` の無条件 fatal error は、変更しなければ prebuild configure で先に発火する。plan `:240` は `/izanagi-masstree-prebuild$` だけを除外し、既存の「condition gate rejected」期待を維持すると指定している。期待値を prepare failure に変更して緑にするのは不可。

## spawn-site / build-sink

[B-12] refuted — この変更に新しい process-launch／build-sink 台帳登録が必要、という親 brief の一般化は誤り。

`test_ccbench_spawn_sites.py:30` の `_PRODUCTION_DIRS` は **orchestrator/calibrator と orchestrator/campaign のみ**。`:417` の再帰走査に `tools/pegasus/probes` は含まれない。さらに plan は既存 `_run_command` を利用するため、新たな raw subprocess launch site 自体を probe に作らない。

build-sink 走査には `tools/pegasus` が入る（`:594`）。しかし visitor `:815` が拾うのは `.build`／`.build_v2` 等で、`prepare_masstree_fetchcontent` は該当しない。呼出し引数にも `--build`／`--target` literal はない。helper 本体の `buildcache.py` は backend 除外対象（`:598`）。

したがって `_DeferredGateMember` の追加も不要。台帳の形は `relative_path, owner, reason, sink_kind, sink_scope, sink_lineno`（`:903`）だが、本変更に対応する新規項目はない。検査が通ることを prepare の意味的被覆の証拠にはできない。

## 束縛拡張の副作用

[B-13] real — 共通 fixture に二つの bytes を追加しないと正常系 binding が壊れる。

`test.py:1538` の `bound_bytes` は独立した7件の literal。Python 側だけ9件にすると `_execution_binding` の SHA 採取（`probe.py:2408`）で新 file が不在になる。

影響を数えると、共通 helper の利用者は **3 test 関数、現状20 node**：

- shell dirty gate：9種類×staged/unstaged＝18。
- runtime spool 正常：1。
- Python bytes を spool にした拒否：1。

plan の変更箇所は共通 helper、shell parameter、正常系 SHA assertion。shell parameter に二件足すと22 node、共通 helper 利用者全体は24 nodeになる。別途、plan の新規テストが加わる。

本番直前は既存7 path に加えて **`buildcache.py` と `fetch_third_party.py` の staged／unstaged 差分をなくす**必要がある。PBS は clean だけでなく HEAD blob との bytes 一致も検査する（`probe.pbs:63,71`）。変更した probe／PBS を含む確定 commit と `EXPECTED_COMMIT` を一致させること。推移的 import 全体の束縛ではない。

## hydrate の timeout

[B-14] real — 通常の hydrate hang は止められるが、walltime 前の受領証終端を無条件には保証できない。

plan の `min(1200, remaining_s-1)` と `probe.py:620` の新 session、`:641` の `_kill_tree` は、通常の停止可能な Git 子プロセスには有効。失敗を `third-party-hydrate` に帰属させる設計も適切。

ただし `_kill_tree` は子孫を一度列挙する（`:577`）。kill 後の `communicate()` は timeout なし（`:645`）、TemporaryDirectory の撤去も時間制限なし。従って残り1秒を確保するだけでは、終了処理までの厳密な上限にはならない。policy の300秒 reserve も、PBS 起動時刻ではなく probe 開始後5100秒からの相対設計である。

[B-15] real — prepare の timeout は子孫停止を保証せず、manifest には timeout 自体がない。

`buildcache.py:3799` は `subprocess.run(..., timeout=...)` を使うが、process group／子孫停止処理はない。timeout で直接の cmake が終了しても、その配下の make／compiler が残り、S 撤去と競合する余地がある。hydrate の `_run_command` と同じ停止契約ではない。

さらに `:1196,1230` の version subprocess は timeout なし。plan は後者を認識しているが、prepare の子孫寿命は未整理。

是正：少なくとも timeout の受入検査は `failure_stage` だけでなく、子孫停止と S 撤去まで確認する。共有 helper 変更禁止を維持するなら、厳密 deadline／全子孫 cleanup は保証対象外として明記する必要がある。

## (P1)〜(P6) の実効性

[B-16] refuted — P1〜P5 全体が成立しない、という結論にはならない。

| 裁定 | 判定 | 実効性の条件 |
|---|---|---|
| P1 | 支持 | `sys.executable -I -B`＋実 CLI。5 cache repo と正しい origin が必要。 |
| P2 | 支持 | plan の TemporaryDirectory が hydrate〜両 build を囲めば、通常終了・例外時に S を撤去する。 |
| P3 | 条件付き支持 | outside install 後、一度だけ prepare。両 masstree OUTPUT が必要。固定 configure 差と timeout の限界は B-4／B-15。 |
| P4 | 支持 | 二つの束縛一覧と fixture を同期。新規 gate／spawn 台帳は不要。 |
| P5 | 条件付き支持 | identity は hydrate 後・prepare 前の記録。生成済み入力全体の digest と説明しない。成功 argv は helper 戻り値から取得する。 |
| P6 | 条件付き支持 | 通常時の予算余裕は見込めるが、実測上限・厳密終端保証にはならない。 |

P2 の寿命について、**brief の配置指定だけでは不十分だが、plan は解消している**。`probe.pbs:91` の cleanup は shim しか消さず、`probe.py:2696` も scratch だけを消す。S の撤去責任は新しい contextmanager にある。通常の例外 unwinding では requested checkout と同等の寿命になるが、SIGKILL／walltime 強制終了ではどちらも contextmanager の撤去保証はない。

## 総括

- **[B-15] real** — prepare の timeout は子孫停止を保証せず、manifest の無 timeout 処理も残る。
- **[B-10] real** — 最小 fixture は dependency_prefix 欠落と masstree archive 欠落を見逃す。
- **[B-4] real** — prepare は ccache／launcher 等の抑制条件が異なり、既存 configure 成功をそのまま移せない。
- **[B-14] real** — hydrate の timeout 後の回収・撤去は無制限で、walltime 前の終端保証にはならない。
- **[B-7] real** — NFS コピー85秒と `timeout 20` は今回の hydrate 実測上限ではなく、追加30〜60秒は未検証の見積り。