## 所見

### 1. [severity: must-fix] argv 検査だけでは T-1094 相当の source 注入を阻止できない

- **実測:** `FETCHCONTENT_BASE_DIR` 自体は全 FetchContent の配置親を変えるだけで、`FETCHCONTENT_SOURCE_DIR_MASSTREE` のように population を迂回しない。`CMAKE_PREFIX_PATH` も gflags、glog 等の `find_package()` 探索に使われ、masstree source を直接差し替えない。この限定では、プランは T-1094 を文字どおり復活させていない。
- **実測:** 一方、継承された `CMAKE_TOOLCHAIN_FILE` は新規 configure で自動的に読み込まれる。現行 `_run()` は明示 `env` がなければ親環境を継承するが、プランの防壁は返却された `configure_argv` に `FETCHCONTENT_SOURCE_DIR_*` がないことしか確認しない。
- **攻撃シナリオ（推測）:** toolchain file が CCBench configure のときだけ `set(FETCHCONTENT_SOURCE_DIR_MASSTREE <別root> CACHE PATH "" FORCE)` を行う。prebuild と oracle は `<base>/masstree-src` を使う一方、cell binary は別 root から作れる。argv は無傷で、予定された post-check も oracle 側 root の不変しか見ないため、別 root の binary が admission される。
- **成果物影響（DW-G05）:** 誤った `sort_best` binary が certified 受理集合に入り、report と台帳が oracle の root を実際の build root として誤参照する。
- **提案:** prebuild と全 cell configure で CMake 環境を共通に正規化し、少なくとも `CMAKE_TOOLCHAIN_FILE` を拒否または hash 固定する。条件付き toolchain 注入を用いた negative test と、実効 `masstree_SOURCE_DIR` を CMake cache、compile flags、link input から確認する検査を追加する。argv の文字列検査だけを合格条件にしない。同型は F199 `[恒真ゲート]`、F121 `[防壁の射程誤認]`。
- [根拠 `/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-15-rulings-full-33rulings.md:18-21`; `s2-plan.md:75-77,167`; `/usr/share/cmake-3.22/Modules/FetchContent.cmake:443-454,1138-1175,1217-1228`; `/usr/share/cmake-3.22/Help/envvar/CMAKE_TOOLCHAIN_FILE.rst:8-12`; `/usr/share/cmake-3.22/Modules/CMakeDetermineSystem.cmake:119-128`; `orchestrator/campaign/buildcache.py:1408-1429,1873-1889`; `docs/failures.md:5351-5374,3671-3691`]

### 2. [severity: must-fix] `sort_best` 修復が全 cell と全 FetchContent へ拡張されている

- **実測:** brief の scope は `sort_best` cell だけだが、プランは一つでも `sort_best` があれば全 `build_fn` に同じ base を渡す。さらに `FETCHCONTENT_BASE_DIR` は masstree 専用ではなく、mimalloc と googletest の source、build、subbuild にも作用する。
- **攻撃シナリオ（静的帰結）:** job-local path が全 cell の configure argv と v2 identity に入るため、非 sort の 10 cell まで job ごとに cache miss、binary path、`cached` 値、参照 hash が変わる。masstree だけを検証する post-checkでは、共有された他依存の実体を覆えない。
- **成果物影響（DW-G05）:** T-1128 を実装しなかった場合と比べ、scope 外の非 sort cell の binary 参照、cache 状態、場合によって受理集合まで変わる。
- **提案:** base を渡す対象を `sort_best` cell に限定する。全 cell 共有を維持するなら、T-1128 の scope 拡張として明示裁定を取り、mimalloc、googletest と非 sort 成果物への影響も検証対象に加える。
- [根拠 `s1-brief.md:20-25`; `s2-plan.md:14-19,34,67-73`; `/usr/share/cmake-3.22/Modules/FetchContent.cmake:443-454`; `external/ccbench/cmake/ThirdParty.cmake:35-136`; `orchestrator/campaign/buildcache.py:750-770,1343-1353`; `orchestrator/campaign/s8b_floor_campaign.py:2318-2338`]

### 3. [severity: must-fix] 廃止予定の共有 cache が submitter では依然 mandatory である

- **実測:** プランは `third_party_cache_root` production 経路を廃止するが、編集面に `tools/pegasus/submit_floor.sh` を含めていない。現行 submitter は外部 cache が絶対 path の既存 directory でなければ launch 前に拒否し、環境変数として export する。テストもこの挙動を固定している。
- **攻撃シナリオ（静的帰結）:** job-local base だけで完結する正しい T-1128 run でも、無関係になった旧 cache がないという理由で submit 前に停止する。これは T-1129 の検査ではなく、効力を失った恒真でない前提の残骸である。
- **成果物影響（DW-G05）:** 有効な入力の受理集合が空になり、binary、report、台帳が一件も生成されない。
- **提案:** submitter と `test_pegasus_floor_tools.py` を consumer 閉包へ追加し、旧引数、存在検査、export を同じ wave で除去する。これは T-1129 実装ではなく、T-1128 の stale consumer 除去である。同型は F89 `[説明と実装の食い違い]`、F200/F255 `[手順漏れ]`。
- [根拠 `s2-plan.md:15,108-116`; `tools/pegasus/submit_floor.sh:9-12,62-65,95-110,435`; `orchestrator/tests/test_pegasus_floor_tools.py:1068-1101`; `docs/failures.md:2819-2834,5377-5400,6477-6492`]

### 4. [severity: must-fix] 新しい private runtime field が binary store の exact-key gate を必ず落とす

- **実測:** プランは built record に `_fetchcontent_base_dir` を追加するが、指定編集範囲は portable projection 周辺だけである。実装には `_ccbench_root` だけを許す exact-key 集合と、同 field だけを除去する projection が別位置にある。
- **攻撃シナリオ（静的帰結）:** 計画どおり field を追加すると、fresh build 後の `store_binaries` が exact-key mismatch を投げる。現在のテスト計画は argv projection までで、fresh build、store、portable record の一連経路を通さない。
- **成果物影響（DW-G05）:** oracle と build が成功しても binary store、manifest、report、台帳は生成されず、受理集合は 0 件になる。
- **提案:** runtime fresh/stored key 集合、private field 検証、portable 化前の除去を同時更新し、`prepare → build → store → project` の通しテストを追加する。同型は F200/F255 `[手順漏れ]`。
- [根拠 `s2-plan.md:98,108-116,174`; `orchestrator/campaign/s8b_floor_campaign.py:2971-2989,3026-3045`; `orchestrator/tests/test_s8b_floor_campaign.py:6006-6034`; `docs/failures.md:5377-5400,6477-6492`]

### 5. [severity: must-fix] brief の DW-G05 は存在しない durable PASS 証明を前提にしている

- **実測:** `sort-swo-oracle-dependency.json` は oracle 実行前に書かれる dependency attempt markerであり、SWO PASS recordではない。実際の `oracle_attempt` は `PreparedCell` に返るが、floor の binding と built recordには取り込まれない。phase marker callbackも検査完了前に呼ばれる。
- **攻撃シナリオ（推測）:** marker 書込み直後の停止と、oracle PASS 後の停止が durable evidence 上で区別できない。プランが同一 root を実現しても、PASS receipt と admission binary の対応を reportや台帳から再検証できない。
- **成果物影響（DW-G05）:** certified 選択の根拠参照に、SWO PASS、dependency identity、admission binaryを結ぶ durable edge が残らない。brief の「marker が comparator 検証を主張する」は事実誤認である。
- **提案:** `oracle_attempt` または閉じた PASS receipt を built/admission recordへ束縛し、root、HEAD、config hash、binary admissionとの一致を保存時に検証する。これを本 wave に含めないなら、brief とplanの成果物主張を「runtime fail-closed」に狭め、markerをPASS証明と呼ばない。同型は F157 `[誤前提][手順漏れ]`、F89 `[説明と実装の食い違い]`。
- [根拠 `s1-brief.md:27-35`; `orchestrator/campaign/s8b_floor_campaign.py:2019-2028,2039-2115,2161-2176`; `orchestrator/campaign/s1_direct_comparison.py:681-722`; `orchestrator/campaign/s8b_materialization.py:112-135`; `orchestrator/campaign/sort_swo_oracle.py:1488-1503`; `s2-plan.md:92,98`; `docs/failures.md:4499-4523,2819-2834`]

### 6. [severity: must-fix] post-build drift は閉じて停止するが、構造化された失敗記録にならない

- **実測:** prebuild configure/build failureには detail code と永続化経路を計画している。一方、post-build HEAD、inode、config drift は「fail-closed」と rejection testだけで、preflight 永続化区間の外にある。現行 CLI はこの種の `FloorCampaignError` を汎用 errorへ落とす。
- **攻撃シナリオ（推測）:** oracle 後に source が置換されると binary admission は止まるが、台帳には「どの identity が、どの時点で、なぜ失効したか」が残らない。既存 markerだけを見れば未実行、reject、driftを区別できない。
- **成果物影響（DW-G05）:** 受理集合は安全に縮む一方、trial ledger の値と参照が構造化 reason から汎用 errorへ変わり、正しさ失敗を再現・集計できない。
- **提案:** postflight 専用の閉じた detail codeと attempt artifactを追加し、永続化完了後に停止する。negative testは単なる例外だけでなく、exact payload、binary非受理、report非生成を検査する。同型は F309 `[恒真ゲート][防壁の射程誤認]`。
- [根拠 `s2-plan.md:57-59,77-79,170-173`; `orchestrator/campaign/s8b_floor_campaign.py:1758-1770,5118-5123`; `docs/failures.md:7512-7529`]

### 7. [severity: should] 一 job probe を floor 全体の利用可能性へ一般化できない

- **実測:** worklog 560 と insight は `bnode030` の一 job、一 profileだけであり、floor 本走、別 node、D152 cloneを測っていない。プランは旧値を再実測値として扱わず、新しい一 job probeを land gateにする点までは正しい。
- **攻撃シナリオ（推測）:** 別 node、CMake binary、generator、module環境、proxy状態で clone/update挙動が異なると、probe成功を根拠にした「floorで利用可能」という説明だけが先行する。実装が fail-closedなら誤受理は避けられるが、別 jobでは `sort_best` が0件になり得る。
- **成果物影響（DW-G05）:** 他環境では accepted set と report cell数が0へ変わる可能性があり、一 jobの値を一般的なfloor可用性として台帳へ書けない。
- **提案:** probe結論を node、CMake実体と版、generator、module/profile、job IDに限定する。production recordにも同じ環境identityを残し、不一致時は構造化UNAVAILABLEにする。
- [根拠 `docs/worklog.md:1921-1971`; `output/insights/2026-08-15_t1094-fetchcontent-floor/README.md:15-34,97-105`; `docs/pegasus-runbook.md:744-757`; `s2-plan.md:144,150-158`]

### 8. [severity: nit] T-1129、T-1130 は現プランでは実装されていないが、fallback は未承認である

- **実測:** raw SHA checkoutでは detached HEADが残るため、P4のHEAD照合は commit identityに限れば成立する。ただし `config.h`、archive、ignored/generated bytesはHEADでは覆えない。プランはこの限界を明記し、`third_party_source_contract` とD152 cloneを編集面に含めていないため、現時点では T-1129、T-1130 とも触れていない。
- **攻撃シナリオ（推測）:** probe失敗時の `FETCHCONTENT_FULLY_DISCONNECTED=ON` を「再検討」ではなく実装許可と読み替えると、既存 sourceを前提にdownload/updateを止める別の権威変更になる。ignored bytesを照合しないまま採用すれば、T-1129 の防壁を実装せずに依存してしまう。
- **成果物影響（DW-G05）:** 現プランだけなら変化なし。fallbackを無審査で追加した場合は、検査されない source bytesから作られたbinaryが受理候補になる。
- **提案:** `FULLY_DISCONNECTED` は本planの許可範囲外と明記し、必要になった時点で再度敵対検証する。P4は「HEAD照合はcommitだけに効く」と限定する。F319 `[恒真ゲート]` の再発を避ける。
- [根拠 `s2-plan.md:90-94,108-116,158`; `external/ccbench/cmake/ThirdParty.cmake:35-88`; `/usr/share/cmake-3.22/Modules/ExternalProject.cmake:1303-1368`; `/usr/share/cmake-3.22/Modules/FetchContent.cmake:1176-1192`; `output/insights/2026-08-15_t1094-fetchcontent-floor/README.md:49-95`; `docs/failures.md:7705-7730`]

### 9. [severity: nit] 親 brief の A2、A7、A9、A11、A12 は実ファイルと一致しない

- **実測:** verifier開始行、floor cache root、resolver終端、v2/legacy staging lifecycle、digestへのcell ID包含についてbriefに誤りがある。段2 planの訂正表は実ファイルと一致している。
- **攻撃シナリオ（推測）:** 実装者がbriefのA11を再び正本扱いすると、oracle前には存在せずbuild後に削除される最終build dirの `_deps` へ束縛し、`sort_best` を0件にする。
- **成果物影響（DW-G05）:** planの訂正を採用すれば影響なし。briefを採用するとdependency root解決が失敗し、certified受理集合が0件になる。
- **提案:** 段4以降は `s2-plan.md:127-144` の訂正を実装アンカーとして固定する。編集面が所見3により増えるため、F301 `[凍結 pin]` のpath-keyed閉包検索も新しい編集集合でやり直す。
- [根拠 `s1-brief.md:65-77`; `s2-plan.md:127-144`; `orchestrator/campaign/s8b_floor_campaign.py:1427-1579,1953`; `orchestrator/campaign/s1_direct_comparison.py:621-622`; `orchestrator/campaign/buildcache.py:750-770,1388-1429,1471-1472,1614-1642,1676-1677`; `docs/failures.md:7372-7390`]

## 判定

**NO-GO** — ambient CMake toolchainからT-1094相当のsource差し替えが可能なままargv検査を防壁としており、さらにsubmitter、binary store、durable oracle receiptのconsumer閉包が欠けている。

## 総括

- 最大の危険は、`FETCHCONTENT_BASE_DIR` そのものではなく、実効CMake変数を見ずargvだけを検査する恒真ゲートである。
- 条件付きtoolchain注入により、oracle rootとbinary build rootを再び分離できる。
- 実装前に必ず潰すべき一件は、この環境注入経路を拒否し、実効 `masstree_SOURCE_DIR` を検証する防壁である。
- 全cellへのbase注入は `sort_best` 限定scopeを越え、非sort成果物とcache identityまで変える。
- 旧third-party cacheを要求するsubmitterと、新private fieldを拒否するstore gateが編集面から漏れている。
- 現在のdependency markerはSWO PASS証明ではなく、briefのDW-G05には事実誤認がある。
- T-1129とT-1130は現プランでは実装されていないが、`FULLY_DISCONNECTED` fallbackは別審査が必要である。
- worklog 560と新probeはいずれも一jobの事実に限定し、floor全体へ一般化してはならない。
- 本判定はread-only静的検査による。Web検索とpytestは実行していない。