## 総括

1. **主張:** 現行 7200 秒予約は、追加 copy を 0 秒と置いても各 timeout の直列和を収容しない。

   **失敗シナリオ:** mocc で gflags / glog / CCBench の各処理が timeout 直前まで正常進行すると、較正開始前後で予約を使い切り、`remaining <= 0` または calibrator timeout になる。

   **根拠:** [certify_calibration.sh:451](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/tools/pegasus/certify_calibration.sh:451)、[同:516](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/tools/pegasus/certify_calibration.sh:516)、[同:600](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/tools/pegasus/certify_calibration.sh:600)、[同:689](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/tools/pegasus/certify_calibration.sh:689)。

   **深刻度:** blocker

2. **主張:** `--repo-root` と job の `PBS_O_WORKDIR` が束縛されず、正しい third-party path を渡しても別 checkout で job が走りうる。

   **失敗シナリオ:** repo 外から絶対 path の submitter を起動すると、submit は対象 repo を検査・hydrate するが、job は投入時 cwd を `REPO_ROOT` と解釈し、policy missing または source identity mismatch で停止する。

   **根拠:** [submit_certify.sh:30](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/tools/pegasus/submit_certify.sh:30)、[certify_calibration.sh:33](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/tools/pegasus/certify_calibration.sh:33)。

   **深刻度:** blocker

3. **主張:** pinned-clean 検査は書込み可能性を保証せず、masstree は source tree が読取り専用なら build できない。

   **失敗シナリオ:** hydrate root の `masstree` が mode 0555 の pinned-clean repositoryである。検査は通るが `cp -a` が 0555 を保存し、`autoreconf` または `configure` が `config.h` 等を作れず build が落ちる。

   **根拠:** [ThirdParty.cmake:66](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/external/ccbench/cmake/ThirdParty.cmake:66)、[stage2-plan.md:74](/home/SFC/tanab/.claude/jobs/0f285a5a/tmp/artifacts/t2535-certify-offline-fetch/stage2-plan.md:74)。

   **深刻度:** should-fix

4. **主張:** 「mocc は条件関門を踏まない」から「較正 record が出る」は導けない。

   **失敗シナリオ:** configure/build 成功後、perf event smoke が全候補で失敗する、load1 が20分静定しない、host visibility/attestation が不一致、または quality 判定が rejected になる。`acquisition-receipt.json` は存在しても較正 record は publish されない。

   **根拠:** [certify_calibration.sh:733](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/tools/pegasus/certify_calibration.sh:733)、[同:769](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/tools/pegasus/certify_calibration.sh:769)、[cli.py:240](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/orchestrator/calibrator/cli.py:240)、[同:851](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/orchestrator/calibrator/cli.py:851)。

   **深刻度:** should-fix

## FetchContent 依存の全列挙

1. **主張:** 現行 CMake graph で能動的に取得される依存は次の三つだけである。

   - `masstree`: `https://github.com/thawk105/masstree-beta.git`、commit `b3c5d054…`。`FetchContent_Populate` 後、custom command で source 内 build。
   - `mimalloc`: `https://github.com/microsoft/mimalloc.git`、tag `v2.3.2`、policy pin `02a2f5df…`。`FetchContent_MakeAvailable`。
   - `googletest`: `https://github.com/google/googletest.git`、commit `f8d7d77c…`。`FetchContent_MakeAvailable`。

   **失敗シナリオ:** `FETCHCONTENT_FULLY_DISCONNECTED=ON` の状態で三つの `SOURCE_DIR` の一つでも欠落・誤記すると、その依存を remote から補完できず configure が失敗する。

   **根拠:** [ThirdParty.cmake:35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/external/ccbench/cmake/ThirdParty.cmake:35)、[同:42](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/external/ccbench/cmake/ThirdParty.cmake:42)、[同:106](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/external/ccbench/cmake/ThirdParty.cmake:106)、[同:130](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/external/ccbench/cmake/ThirdParty.cmake:130)。

   **深刻度:** blocker if any override is absent

2. **主張:** `cc/*/CMakeLists.txt` に追加取得はない。全 protocol は `ccbench_add_protocol` のみで、helper が masstree / mimalloc をリンクする。googletest は ss2pl test 用だが top-level configure では無条件に MakeAvailable される。

   **失敗シナリオ:** 三依存のうち masstree / mimalloc は mocc target にも必要であり、「mocc なら一部を省ける」とすると build が成立しない。

   **根拠:** [ProtocolHelpers.cmake:32](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/external/ccbench/cmake/ProtocolHelpers.cmake:32)、[mocc/CMakeLists.txt:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/external/ccbench/cc/mocc/CMakeLists.txt:1)、[ss2pl/test/CMakeLists.txt:31](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/external/ccbench/cc/ss2pl/test/CMakeLists.txt:31)。

   **深刻度:** blocker if dependency staging is reduced by protocol

3. **主張:** ネットワーク形状を持つ残存物はあるが、現行 CMake pathからは呼ばれない。

   - `third_party/shirakami` は `.gitmodules` に残るが、top-level の `add_subdirectory` 対象ではない。
   - `include(ExternalProject)` はあるが `ExternalProject_Add` はない。
   - masstree `bootstrap.sh` は `autoreconf -i` だけで fetch しない。
   - mimalloc `bin/bundle.sh` は download 実装を持つが CMake から呼ばれない。CMake の `git describe` も local metadata 参照だけである。
   - googletest の現行 CMake に追加 download はない。

   **失敗シナリオ:** 現行 graphについて、三 source を与えた後に残る能動的ネットワーク取得の反例は見つからなかった。

   **根拠:** [.gitmodules:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/external/ccbench/.gitmodules:1)、[CMakeLists.txt:74](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/external/ccbench/CMakeLists.txt:74)、[ThirdParty.cmake:18](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/external/ccbench/cmake/ThirdParty.cmake:18)、[masstree/bootstrap.sh:3](/work/1/SFC/tanab/izanagi-thirdparty-cache/masstree/bootstrap.sh:3)、[mimalloc/CMakeLists.txt:92](/work/1/SFC/tanab/izanagi-thirdparty-cache/mimalloc/CMakeLists.txt:92)。

   **深刻度:** 反例なし

## masstree の config.h 生成と書込み可能性

1. **主張:** `FETCHCONTENT_SOURCE_DIR_MASSTREE` の先は読取り専用にできない。

   **失敗シナリオ:** build target は source directory 内で `bootstrap.sh`、`configure`、`make`、`ar` を順に実行し、`config.h`、object、archive を同所に生成する。0555 source では失敗する。

   **根拠:** [ThirdParty.cmake:57](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/external/ccbench/cmake/ThirdParty.cmake:57)、[同:66](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/external/ccbench/cmake/ThirdParty.cmake:66)。

   **深刻度:** blocker

2. **主張:** 現在の cache の masstree は、親 brief の「汚れなし」を pristine の意味では満たさない。

   **失敗シナリオ:** 通常 `verify` は ignored artifact を見ない。実 cache には `config.h`、`configure`、多数の `.o`、`libkohler_masstree_json.a` が ignored file として実在する。cache を直接 `cp -a` すると古い生成物も複製される。

   **根拠:** [stage1-brief.md:41](/home/SFC/tanab/.claude/jobs/0f285a5a/tmp/wave/stage1-brief.md:41)、[fetch_third_party.py:393](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/tools/pegasus/fetch_third_party.py:393)、[同:400](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/tools/pegasus/fetch_third_party.py:400)。

   **深刻度:** should-fix in the brief; direct-cache design would be blocker

3. **主張:** 通常の hydrate → `cp -a` は現在の所有者条件では writable になるが、検査契約としては保証されていない。

   **失敗シナリオ:** 現 cache と実行 user はともに UID 31609、directory は 0755 なので通常走行は書ける。一方、既存 staging repository が別 ownerまたは 0555 でも hydrate の pinned-clean 検査は通りうる。`cp -a` は mode/owner 保存を試み、copy 自体の失敗または読取り専用 destination を作る。

   **根拠:** [fetch_third_party.py:616](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/tools/pegasus/fetch_third_party.py:616)、[同:670](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/tools/pegasus/fetch_third_party.py:670)、[stage2-plan.md:74](/home/SFC/tanab/.claude/jobs/0f285a5a/tmp/artifacts/t2535-certify-offline-fetch/stage2-plan.md:74)。

   **深刻度:** should-fix

## プランの file:line 照合

1. **主張:** 主要な編集 anchor は現行 file に当たるが、一部の行参照はずれている。

   **失敗シナリオ:** 行番号だけで機械編集すると、brief の submit `190–196` は実体 `189–195`、A-2 の copy は計画が指す `:340` ではなく `:353–355` にある。

   **根拠:** [stage1-brief.md:64](/home/SFC/tanab/.claude/jobs/0f285a5a/tmp/wave/stage1-brief.md:64)、[submit_certify.sh:189](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/tools/pegasus/submit_certify.sh:189)、[stage2-plan.md:147](/home/SFC/tanab/.claude/jobs/0f285a5a/tmp/artifacts/t2535-certify-offline-fetch/stage2-plan.md:147)、[paper_story_a2_certification.sh:353](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/tools/pegasus/paper_story_a2_certification.sh:353)。

   **深刻度:** nit

2. **主張:** `source.index(...)` の目印はプランの挿入位置では壊れない。

   **失敗シナリオ:** 現行反例なし。protocol `case` は意図的に二件あるが、二件目は一件目の終端後から探索する。`configure_argv=(` は gflags/glog 名にも部分一致するが、探索開始点が protocol define case 後なので CCBench の配列へ当たる。`# The current CCBench pin` と silo `if` は各一件である。

   **根拠:** [test_pegasus_calibration_workload.py:113](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/orchestrator/tests/test_pegasus_calibration_workload.py:113)、[certify_calibration.sh:546](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/tools/pegasus/certify_calibration.sh:546)、[同:576](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/tools/pegasus/certify_calibration.sh:576)、[同:582](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/tools/pegasus/certify_calibration.sh:582)。

   **深刻度:** 反例なし

3. **主張:** 計画された最小 CMake test は、production の最大リスクを実行しない。

   **失敗シナリオ:** fake dependency の `CMakeLists.txt` は configure 時に path を記録するだけなので、三つの SOURCE_DIR が解決できれば緑になる。production masstree は build 時に source tree へ書くため、同じ入力が読取り専用なら fake test は緑、実 build は赤になる。

   **根拠:** [stage2-plan.md:202](/home/SFC/tanab/.claude/jobs/0f285a5a/tmp/artifacts/t2535-certify-offline-fetch/stage2-plan.md:202)、[ThirdParty.cmake:66](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/external/ccbench/cmake/ThirdParty.cmake:66)。

   **深刻度:** should-fix

4. **主張:** submit dry-run の「clean fixture」は、計画どおりでは自己完結しない。

   **失敗シナリオ:** fixture は `tools/pegasus` をコピーするが、hydrate tool は `orchestrator.campaign.silo_ladder_rung1` を importする。pytest の cwd/PYTHONPATH から本 checkout が偶然見えなければ、hydrate は qsub 構築前に import error で落ちる。

   **根拠:** [test_pegasus_calibration_workload.py:467](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/orchestrator/tests/test_pegasus_calibration_workload.py:467)、[fetch_third_party.py:52](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/tools/pegasus/fetch_third_party.py:52)、[stage2-plan.md:135](/home/SFC/tanab/.claude/jobs/0f285a5a/tmp/artifacts/t2535-certify-offline-fetch/stage2-plan.md:135)。

   **深刻度:** should-fix

## submit から job への受け渡し

1. **主張:** NQSV の `-v variable[=value][,...]` 形式には合致し、現 worktree の path 長も 4000-byte 制限内だが、submitterと job の repo identity は渡されない。

   **失敗シナリオ:** repo 外 cwd から投入すると、third-party path 自体は届いても job は別 `PBS_O_WORKDIR` を repo として採用して先に停止する。

   **根拠:** [submit_certify.sh:189](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/tools/pegasus/submit_certify.sh:189)、[certify_calibration.sh:33](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/tools/pegasus/certify_calibration.sh:33)。login node の `qsub(1-N)` も `-v variable_list` と総長4000 bytesを規定していた。

   **深刻度:** blocker

2. **主張:** comma、`=`、newline は plan が投入前に拒否するため spec 分解はしないが、その分、正当な Unix path を受理しない。

   **失敗シナリオ:** repo root が `/work/project,a/repo` または `/work/project=a/repo` なら hydrate source は有効でも submit が停止する。空白は `qsub_cmd` array の一要素に保持され、job側も引用しているので、この面の反例はない。

   **根拠:** [stage2-plan.md:42](/home/SFC/tanab/.claude/jobs/0f285a5a/tmp/artifacts/t2535-certify-offline-fetch/stage2-plan.md:42)、[submit_certify.sh:195](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/tools/pegasus/submit_certify.sh:195)。

   **深刻度:** nit for the current fixed path

3. **主張:** `PROTOCOL_EXPLICIT` の既存非対称とは衝突しない。

   **失敗シナリオ:** 反例なし。source root は常時 export、protocol は明示時のみ export。未定義 protocol は job の `${IZANAGI_CALIBRATION_PROTOCOL-silo}` に落ちる。計画された source-root 必須検査も `${VAR:-}` を使う限り `set -u` より先に構造化失敗へ落とせる。

   **根拠:** [submit_certify.sh:189](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/tools/pegasus/submit_certify.sh:189)、[certify_calibration.sh:150](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/tools/pegasus/certify_calibration.sh:150)、[同:162](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/tools/pegasus/certify_calibration.sh:162)。

   **深刻度:** 反例なし

## 時間予算

1. **主張:** cache の実サイズは以下だったが、これは copy 時間の証拠ではなく、job がコピーする hydrated payload の正確なサイズでもない。

   - masstree: 39,750,203 bytes、割当表示 39 MiB
   - mimalloc: 17,159,901 bytes、18 MiB
   - googletest: 19,765,492 bytes、20 MiB
   - 合計: 76,675,596 bytes、約73.1 MiB apparent／77 MiB allocated

   masstree の39 MiBには hydrate が持ち込まない ignored build artifact が含まれる。

   **失敗シナリオ:** 77 MiBという静的値だけを根拠に `C <= 290` とすると、filesystem congestion、metadata copy、三回の Git statusを一度も測らないまま予算内と認定することになる。

   **根拠:** cache 三 directory の `du -sb` 実測、および [fetch_third_party.py:636](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/tools/pegasus/fetch_third_party.py:636)、[stage2-plan.md:222](/home/SFC/tanab/.claude/jobs/0f285a5a/tmp/artifacts/t2535-certify-offline-fetch/stage2-plan.md:222)。

   **深刻度:** should-fix

2. **主張:** plan の「CCBench=900 envelope に copy・verifyを含める」は実コードの timeout 境界と一致しない。

   **失敗シナリオ:** copy・verifyは `timeout 900 configure` より前で無制限、configure と build はそれぞれ別の900秒 timeoutである。したがって CCBench区間は `C + 1800` 秒まで正常進行しうるのに、式は900しか数えない。

   **根拠:** [stage2-plan.md:218](/home/SFC/tanab/.claude/jobs/0f285a5a/tmp/artifacts/t2535-certify-offline-fetch/stage2-plan.md:218)、[certify_calibration.sh:600](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/tools/pegasus/certify_calibration.sh:600)。

   **深刻度:** blocker

3. **主張:** 正しい下限は、copy+verify の実効 cap を `C` として mocc `7870+C` 秒、silo `8170+C` 秒である。さらに未計上の probe/perf/hash等の overhead がある。

   **失敗シナリオ:** 現行 6610 は gflagsを60秒、glogを120秒、CCBenchを900秒と数えるが、実体はそれぞれ `3×60`、`3×120`、`2×900`。差は1260秒で、moccでも `6610+1260=7870 > 7200`。

   **根拠:** [certify_calibration.sh:444](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/tools/pegasus/certify_calibration.sh:444)、[同:508](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/tools/pegasus/certify_calibration.sh:508)、[同:689](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/tools/pegasus/certify_calibration.sh:689)、[calibration_v1.json:5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/tools/pegasus/policies/calibration_v1.json:5)。

   **深刻度:** blocker

   数値として、仮に `C=290` を採るなら最低でも mocc は8160秒＝`02:16:00`、silo は8460秒＝`02:21:00`。ただし現プランには copy/verify timeout が無いため、現状の `C` は有限に束縛されていない。

## 親 brief への反証 (mocc で完了判定に到達するか)

1. **主張:** mocc が回避するのは silo 専用 condition gate 一つだけである。

   **失敗シナリオ:** build後に perf候補が全滅すると [certify_calibration.sh:794](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/tools/pegasus/certify_calibration.sh:794) で終了する。さらに calibrator 内では cooldown、dynamic attestation、host visibility、receipt、isolation、quality、publish self-comparisonの全てが mocc にも適用される。

   **根拠:** [certify_calibration.sh:586](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/tools/pegasus/certify_calibration.sh:586)、[cli.py:839](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/orchestrator/calibrator/cli.py:839)、[同:993](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/orchestrator/calibrator/cli.py:993)。

   **深刻度:** should-fix in the brief’s causal claim

2. **主張:** mocc 固有の静的到達不能条件は見つからない。したがって代替 protocolを要求する根拠もない。

   **失敗シナリオ:** protocol固有反例なし。mocc CMake は ycsbを持ち、receipt targetから `mocc` を復元でき、define集合は `SPACES["mocc"]` に所属する。workload/perf/attestation処理には silo 固定分岐がない。

   **根拠:** [mocc/CMakeLists.txt:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/external/ccbench/cc/mocc/CMakeLists.txt:1)、[certify_calibration.sh:557](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/tools/pegasus/certify_calibration.sh:557)、[cli.py:409](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/orchestrator/calibrator/cli.py:409)、[同:455](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/orchestrator/calibrator/cli.py:455)。

   **深刻度:** 反例なし。ただし実走未確認

## 過去 job との差

1. **主張:** 892707 と今回の provisional mocc は、offline token追加だけの同一較正ではない。

   **失敗シナリオ:** 新 recordを892707の再取得として比較すると、protocol本体、axis、binary targetが同時に変わっており、飽和点・noise floorの差をoffline供給だけへ帰属できない。

   **根拠:** [892707 acquisition receipt:12](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/output/env/pegasus/calibration/job-staging/0:892707.nqsv/acquisition-receipt.json:12)、[stage2-plan.md:92](/home/SFC/tanab/.claude/jobs/0f285a5a/tmp/artifacts/t2535-certify-offline-fetch/stage2-plan.md:92)、[certify_calibration.sh:557](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/tools/pegasus/certify_calibration.sh:557)。

   **深刻度:** should-fix for result interpretation

   Token単位の差は次のとおり。

   | 面 | 892707 | 今回の provisional mocc |
   |---|---|---|
   | argv[0] | `cmake` | `CMAKE_PATH` の realpath |
   | offline供給 | なし | `FETCHCONTENT_BASE_DIR`、`FULLY_DISCONNECTED`、三 `SOURCE_DIR` の計5 token |
   | `TRACE` | `0` | `0` |
   | `BACK_OFF` | `0` | `1` |
   | `BACKOFF_FIXED` | `-1` | 削除 |
   | `NO_WAIT_LOCKING_IN_VALIDATION` | `1` | 削除 |
   | `NO_WAIT_OF_TICTOC` | `0` | 削除 |
   | `WAL` | `0` | 削除 |
   | `KEY_SORT` | なし | `0` |
   | `TEMPERATURE_RESET_OPT` | なし | `1` |
   | build target | `ycsb_silo.exe` | `ycsb_mocc.exe` |

   892707 の CCBench HEAD は `d706650c…`、現行は `511c9538…`。その commit間差分は silo transactionだけなので moccには直接掛からないが、892707自身は silo binaryである。offline五 tokenだけなら同じ三 pinを選ぶ意図だが、masstree `config.h` bytesや最終 binary同一性はこのプランでは証明されない。

2. **主張:** 892707 の189秒完走は、新しい時間上限の証明にならない。

   **失敗シナリオ:** 旧 jobは silo、別HEAD、remote FetchContent経路、copy/verifyなしであり、新しい三repo copyとmasstree再生成時間を含まない。

   **根拠:** [892707 scheduler stderr](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/output/env/pegasus/calibration/job-staging/0:892707.nqsv/certify_calibration.sh.e892707)、[892707 receipt:40](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/output/env/pegasus/calibration/job-staging/0:892707.nqsv/acquisition-receipt.json:40)。

   **深刻度:** should-fix

## 裁定パッケージ候補 (scope 外の real 所見)

1. **主張:** 6610 / 6910 の既存不一致だけでなく、三つの独立 build command群を一つの capとして数える式全体が現コードと一致しない。

   **失敗シナリオ:** T-2535で copy分だけを加算しても、gflags / glog / configure+buildの直列和不足が残り、凍結式は依然として実効上限にならない。

   **根拠:** [certify_calibration.sh:7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/tools/pegasus/certify_calibration.sh:7)、[同:689](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/tools/pegasus/certify_calibration.sh:689)。

   **深刻度:** blocker。式全体の再凍結をT-2535へ含めないなら独立裁定が必要

2. **主張:** `--repo-root` と `PBS_O_WORKDIR` の既存分離は、offline供給とは独立した launcher contract欠陥である。

   **失敗シナリオ:**正しい source rootをNQSVへ渡しても、投入 cwdがrepoでなければ jobは別木を実行する。

   **根拠:** [submit_certify.sh:30](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/tools/pegasus/submit_certify.sh:30)、[certify_calibration.sh:33](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2535-certify-offline-fetch/tools/pegasus/certify_calibration.sh:33)。

   **深刻度:** blocker。T-2535で直さないなら invocation prerequisiteの裁定が必要

編集、commit、pytest、計算ノード投入は行っていない。静的通読、login node上のread-only cache計測、現地 `qsub(1-N)` の構文確認だけである。