## 総括

静的検査で、主要な反例を 6 件確認した。

- `pinned_clean=True` は第三者依存を束縛せず、広く解釈すると build 後には偽になる。
- silo 条件関門には masstree の事前 build がなく、offline source を置くだけでは `config.h` が生成されない。
- `FULLY_DISCONNECTED` と既定命名により、SOURCE_DIR token を落とす予定の負例は失敗しない。
- compute 側 pin 再検査の削除、実条件関門への伝播欠落、receipt provenance 欠落を殺すテストがない。
- mocc の完走は条件関門を一度も通らないため、壊れた silo 配線を隠せる。
- `submit_certify.sh` に hydrate/clone を追加すると、現行 `local-ok` の根拠と実際の login-side 処理が食い違う。

pytest・configure・build は実走していない。

## 認定 provenance の所見

1. **主張:** `ccbench.pinned_clean=True` は、第三者 source まで含む意味なら receipt 作成時点で偽になる。CCBench 本体だけの意味なら、新たな build 入力を何も証明しない。  
   **失敗シナリオ:** pristine な `masstree-src` を検査後、CCBench build が同 source directory 内で `bootstrap.sh`、`configure`、`make`、`ar` を実行し、`config.h`、object、archive を生成する。その後に receipt が無条件で `pinned_clean=True` を記録する。実際に compiler が読んだ private copy はもう pristine ではない。  
   **根拠:** `external/ccbench/cmake/ThirdParty.cmake:57-78`、`tools/pegasus/certify_calibration.sh:600-601,710-715`、`stage2-plan.md:151-157`。  
   **深刻度:** High

2. **主張:** acquisition receipt だけから第三者依存を再現できない。scratch path は provenance ではなく、一時的な所在文字列である。  
   **失敗シナリオ:** job 終了後に `/scr/<job>/fetchcontent` が消える、または同じ path が別内容で再利用される。receipt には masstree/mimalloc/googletest の commit、tree hash、hydrate receipt、主 repo commit がなく、残るのは消滅した path を含む `build_argv` だけである。consumer はその token を無視して genome を復元し、schema は文字列 list と `True` しか検査しない。  
   **根拠:** `tools/pegasus/certify_calibration.sh:695-715`、`orchestrator/calibrator/schema_v2.py:403-413,522-526`、`orchestrator/calibrator/cli.py:425-464`、`stage2-plan.md:104,247-250`。  
   **深刻度:** High

3. **主張:** CCBench 本体についても、現在の検査だけでは `pinned_clean=True` を偽にできる Git replace-ref 経路が残る。  
   **失敗シナリオ:** `external/ccbench` の object database に `refs/replace/<CCBENCH_HEAD>` を置く。`rev-parse HEAD` は gitlink と同じ OIDを返し、既存 checkout の tracked status も空のままだが、`git worktree add ... "$CCBENCH_HEAD"` の object 解決は replacement tree を materialize し得る。receipt は元 OIDと `True` を記録する。第三者 fetch verifier は replace refs を明示拒否するが、CCBench 側には同じ検査がない。  
   **根拠:** `tools/pegasus/certify_calibration.sh:536-544,710-713`、`tools/pegasus/fetch_third_party.py:370-376`。  
   **深刻度:** High

## 条件関門の所見

1. **主張:** 「判定式・受理集合は不変」は、whitelist と実到達集合を混同している。少なくとも判定可能な入力集合は拡張される。  
   **失敗シナリオ:** 同じ source/request が、変更前は FetchContent の DNS/population failure で evaluator より前に停止し、変更後は local source によって requested/control configure へ進む。`{silo,mocc,tictoc}` という名前集合は同じでも、受理・判定へ到達する具体的呼出し集合は同じではない。D1784 自身もこれを「制御された拡張」と記録している。  
   **根拠:** `stage1-brief.md:29-35`、`stage2-plan.md:245-248`、`docs/decisions.md:54076-54080`、`orchestrator/campaign/condition_meaning_gate.py:1661-1675`。  
   **深刻度:** High

2. **主張:** 本プランは D1784 の供給手順を再現していない。pristine source の copy だけでは silo 条件関門の preprocess に必要な `config.h` がない。  
   **失敗シナリオ:** pristine hydrate では ignored/generated artifact が拒否されるため、masstree `config.h` は存在しない。silo gate は実 build より先に `transaction.cc` を preprocess し、その include chain は `masstree_wrapper.hh` の `<config.h>` に到達する。screening は gate 前に `masstree_build` を実行するが、本プランは copyと検査しか行わない。現 pin では F934 が先に赤になり、F934 が別途消えても次に `config.h` 欠落が残る。  
   **根拠:** `stage2-plan.md:72-102`、`tools/pegasus/certify_calibration.sh:586-601`、`orchestrator/campaign/screening_driver.py:189-207`、`orchestrator/campaign/buildcache.py:2044-2079`、`external/ccbench/cc/silo/include/transaction.hh:9-16`、`external/ccbench/include/masstree_wrapper.hh:17-20`。  
   **深刻度:** High

3. **主張:** certify 側にも D1784 の「経路タグの内側では恒真」という罠がある。  
   **失敗シナリオ:** offline token は全 protocol の `configure_argv` に常時入り、条件関門は `protocol=silo` のときだけ呼ばれる。したがって silo gate の内側では token の存在は構築上恒真であり、計算ノード実測を mocc にするとその分岐自体を一度も観測しない。条件関門への転送を全面的に壊しても mocc の完走条件は満たせる。  
   **根拠:** `stage2-plan.md:92-102,190-196,301-305`、`tools/pegasus/certify_calibration.sh:576-601`、`docs/decisions.md:54092-54094`。  
   **深刻度:** High

## テスト弱体化の所見

1. **主張:** `-DCCBENCH_` filter は supply define の負例にならない。元の axis 契約は保つが、offline 配線の誤りには検出力ゼロである。  
   **失敗シナリオ:** `-DFETCHCONTENT_SOURCE_DIR_MIMALLOC=/wrong`、名前の typo、重複、`FULLY_DISCONNECTED=OFF` を入れても、このテストは全 token を filter 前に捨てて従来どおり緑になる。  
   **根拠:** `orchestrator/tests/test_pegasus_calibration_workload.py:252-264`、`stage1-brief.md:67-69`、`stage2-plan.md:178-184`。  
   **深刻度:** Medium

2. **主張:** exact argv pin は文字列退行は殺せるが、offline 契約の意味について独立 oracle ではない。  
   **失敗シナリオ:** 実装と期待値の双方へ同じ五 token を同じ順序で転記すると、SOURCE_DIR が CMake pin を迂回することや、三 SOURCE_DIR が実は冗長であることを「正しい契約」として固定する。文字列が一致しても source identity は証明されない。  
   **根拠:** `stage2-plan.md:92-100,125-133,174-176`、`orchestrator/tests/test_pegasus_calibration_workload.py:318-345`。  
   **深刻度:** Medium

3. **主張:** 条件関門テストは両層 stub のままなら恒真になる。  
   **失敗シナリオ:** shell helper の `run_condition_gate()` は counter/snapshot だけの stub であり、Python gate の `_configure_compile_commands()` が `captured.configure_args` を全部捨てる変異を入れても snapshot は同じ五 token を報告する。mocc 実測も gate を呼ばない。  
   **根拠:** `orchestrator/tests/test_pegasus_calibration_workload.py:137-166`、`stage2-plan.md:110-119,194-196`、`orchestrator/campaign/condition_meaning_gate.py:1661-1675`。  
   **深刻度:** High

4. **主張:** `test_certify_job_copy_keeps_hydrated_sources_pristine` は、production の pin/pristine verifier を検査しない。  
   **失敗シナリオ:** `_verify_pristine_floor_dependency_sources` 呼出しを削除しても、marker の copy、非共有 inode、upstream 不変はすべて成立する。さらにテスト自身が destination marker を変更して成功とするため、job-private source が pristine だという名前どおりの性質も検査していない。  
   **根拠:** `stage2-plan.md:84-88,198-200`。  
   **深刻度:** High

## FULLY_DISCONNECTED の所見

1. **主張:** `FETCHCONTENT_SOURCE_DIR_*` を指定すると、ThirdParty.cmake の `GIT_TAG` は source identity の検査に使われない。`FULLY_DISCONNECTED` も pin verifier ではない。  
   **失敗シナリオ:** policy pin と異なるが API-compatible な mimalloc checkout を SOURCE_DIR に置く。CMake はその既存 directory を使用し、宣言された URL/tag を照合せず configure/build を続ける。compute-side verifier が削除されるか verifier-to-use race が起きれば黙って通る。  
   **根拠:** `external/ccbench/cmake/ThirdParty.cmake:35-46,106-136`、`stage2-plan.md:84-100,151-155`。  
   **深刻度:** High

2. **主張:** 「SOURCE_DIR token を一つ除けば negative configure が失敗する」という新規テスト設計は成立しない。  
   **失敗シナリオ:** copy block は最初から三 source を `$FETCHCONTENT_BASE_DIR/<name>-src` に置く。その状態で一つの SOURCE_DIR token を除いても、`FULLY_DISCONNECTED=ON` は同じ既定 `<base>/<name>-src` を既存 population として使うため configure は継続する。予定された負例は baseline から赤になる。  
   **根拠:** `stage2-plan.md:74-100,202-206`、`docs/archive/worklog-phase3-0826-978-979.md:8-12`。  
   **深刻度:** High

3. **主張:** submit→compute の共有 staging には差替え窓があり、compute 再検査後にも未束縛の verifier-to-use 窓が残る。  
   **失敗シナリオ:** submit の hydrate 完了後、queue 待ち中に staging root を差し替える。通常の wrong-pin 差替えは job-private copy 後の verifier が止めるが、その verifier 終了後に同一 UID の別 process が private `*-src` を atomically 差し替えると、条件関門と measurement CMake は再検査なしで新しい source を使う。CMake 自身は pin を照合しない。  
   **根拠:** `stage2-plan.md:28-59,63-102,151-155`、`tools/pegasus/certify_calibration.sh:586-601`。  
   **深刻度:** High

4. **主張:** argv 上の `FULLY_DISCONNECTED=ON` は実効値 ON の証拠ではない。  
   **失敗シナリオ:** ambient toolchain が同 cache variable を `FORCE OFF` にすると、exact argv test と receipt は ON token を保持したまま、CMake の実効値は OFF になる。この型は既に同じ CMake 3.22.1 環境で再現済みである。  
   **根拠:** `docs/archive/worklog-phase3-0826-978-979.md:13-16`、`stage2-plan.md:92-104,190-206`。  
   **深刻度:** Medium

## 親 brief への反証

1. **主張:** 実測 1 の名前解決成功を、Git/network acquisition の成功へ一般化できない。  
   **失敗シナリオ:** A record の lookup は成功しても、HTTPS proxy、TLS、Git transport、接続先 IP、rate limit のいずれかで clone は失敗する。また一時点・一 login node の lookup は将来の submit 時点を束縛しない。  
   **根拠:** `stage1-brief.md:37-40`。  
   **深刻度:** Low

2. **主張:** 実測 2 の「verify rc=0だから汚れなし」は偽である。  
   **失敗シナリオ:** policy pin と HEAD は一致し、tracked/untracked status は空だが、`.gitignore` 対象の generated archiveや `config.h` が残っている。通常 verify はそれらを列挙しないため rc=0になる。  
   **根拠:** `stage1-brief.md:41-44`、`tools/pegasus/fetch_third_party.py:393-409`。  
   **深刻度:** High

3. **主張:** 実測 4 の「新規実行体がなければ registry 変更不要」は path inventory と実行分類を混同している。  
   **失敗シナリオ:** `submit_certify.sh` は現在 `legacy-admitted (未実測)` で、主 gate は qsub と記録されている。そこへ login-side の三 repository hydrate/clone を加えると process tree と入力量が変わる。同じ path のままでも既存 evidence は新しい処理を証明しない。repo 自身も、clone を行う submitter は入力無上限で `unknown` 相当になり得ると記録している。  
   **根拠:** `stage1-brief.md:47-50`、`stage2-plan.md:28-40`、`tools/pegasus/admission_registry.json` の `submit_certify.sh` entry、`tools/pegasus/README.md:6-7,37-40`。  
   **深刻度:** High

4. **主張:** 実測 5 の「consumer が無視するから壊れない」は、genome 復元だけに限った事実を provenance 全体へ一般化している。  
   **失敗シナリオ:** wrong/missing/transient SOURCE_DIR token が receipt に入っても genome は同一になり、schema と accepted calibration を通る。つまり consumer が無視する性質は互換性だけでなく、第三者 build input の監査不能も作る。  
   **根拠:** `stage1-brief.md:51-53`、`orchestrator/calibrator/cli.py:425-464`、`orchestrator/calibrator/schema_v2.py:403-413`。  
   **深刻度:** High

5. **主張:** 「moccなら F934 を踏まない」を完了根拠へ広げると、既定経路と条件関門配線の失敗を隠す。  
   **失敗シナリオ:** completion 実測で `--protocol mocc` を明示し忘れると submitter と job の既定は silo であり、F934 を踏む。明示して mocc が完走しても、silo の offline gate forwarding と masstree prebuild は一度も実行されないため、それらが壊れた実装でも完了判定を満たす。  
   **根拠:** `stage1-brief.md:77-78`、`tools/pegasus/submit_certify.sh:19-20,189-192`、`tools/pegasus/certify_calibration.sh:162,586-588`、`docs/failures.md:24163-24176`。  
   **深刻度:** High

## 変異帰属が成立しない検査

1. **主張:** compute-side pristine verifier の削除を殺す予定テストがない。  
   **失敗シナリオ:** `_verify_pristine_floor_dependency_sources(...)` 呼出しを削除する。copy marker test、minimal CMake test、submit hydrate tests、argv tests はすべて各自の fixture 上で成立する。  
   **根拠:** `stage2-plan.md:84-88,186-214`。  
   **深刻度:** High

2. **主張:** 条件関門 consumer が configure args を捨てる変異を殺せない。  
   **失敗シナリオ:** `condition_meaning_gate._configure_compile_commands()` の `configure_args.append(argument)` を削除する。shell snapshot は stub 呼出し前の array を観測するだけで、mocc 実測は gate 自体を呼ばない。  
   **根拠:** `orchestrator/campaign/condition_meaning_gate.py:1661-1675`、`orchestrator/tests/test_pegasus_calibration_workload.py:137-166`、`stage2-plan.md:194-196`。  
   **深刻度:** High

3. **主張:** receipt の `pinned_clean=True` と第三者検証の因果を殺す検査がない。  
   **失敗シナリオ:** pin verifier を常時成功へ変えても receipt producer は同じ literal `True` を書き、schema test は bool 型だけを受理する。新規テストは receipt field と検証結果を結び付けない。  
   **根拠:** `tools/pegasus/certify_calibration.sh:710-715`、`orchestrator/calibrator/schema_v2.py:409-413`、`stage2-plan.md:186-214`。  
   **深刻度:** High

4. **主張:** hydrate stdout の exact consumer validation は、予定された正負テストに帰属しない。  
   **失敗シナリオ:** submitter の stdout key集合、operation、resolved_path、source順序検査を削除する。positive は実 helper が正しい stdout を出すので通り、dirty/head mismatch は helper 自身が stdout 消費以前に失敗するため、やはり wrapper validation の削除を検出しない。  
   **根拠:** `stage2-plan.md:42-51,208-214`。  
   **深刻度:** Medium

5. **主張:** real CCBench の FetchContent 接続破壊は minimal project test に帰属しない。  
   **失敗シナリオ:** `external/ccbench/cmake/ThirdParty.cmake` の dependency 名、target wiring、masstree custom build が壊れても、独立に作った三つの最小 `CMakeLists.txt` は configure できる。特に silo gate の `config.h` 欠落は再現しない。  
   **根拠:** `stage2-plan.md:202-206`、`external/ccbench/cmake/ThirdParty.cmake:42-78,106-136`。  
   **深刻度:** High

## 裁定パッケージ候補 (scope 外の real 所見)

1. **主張:** `pinned_clean` の意味が「CCBench checkout限定」か「全 compiler input」か未定義で、どちらでも現在の成果物主張に穴がある。  
   **失敗シナリオ:** narrow 解釈なら第三者依存が provenance から消え、broad 解釈なら build 後の masstree mutationで false になる。  
   **根拠:** `orchestrator/calibrator/schema_v2.py:403-413,445-469`、`tools/pegasus/certify_calibration.sh:710-715`。  
   **深刻度:** High

2. **主張:** `submit_certify.sh` の grandfather `local-ok` が、新しい hydrate/clone 子処理まで覆うかは既存 evidence から決まらない。  
   **失敗シナリオ:** registry を変更せず landing すると、未実測の新 process tree を旧「qsub submitter」の class で許可した状態になる。  
   **根拠:** `stage2-plan.md:28-40`、`tools/pegasus/admission_registry.json`、`tools/pegasus/README.md:37-40`。  
   **深刻度:** High

3. **主張:** mocc 完走を T-2535 完了と数えると、silo 条件関門の offline 接続は未実証のまま完了できる。  
   **失敗シナリオ:** mocc job が receipt と較正 record を生成する一方、silo branch は F934と未生成 `config.h` で引き続き赤である。それでも brief の job 1本という完了判定は満たされる。  
   **根拠:** `stage1-brief.md:8-12,77-78`、`tools/pegasus/certify_calibration.sh:586-601`、`docs/failures.md:24163-24176`。  
   **深刻度:** High

4. **主張:** CCBench本体の replace-ref 耐性は第三者 verifier より弱く、`pinned_clean` の既存前提自体が不成立になり得る。  
   **失敗シナリオ:** replacement objectから fresh worktree を作りながら、receipt の `head_sha` は gitlink OID、`pinned_clean` は true のままになる。  
   **根拠:** `tools/pegasus/certify_calibration.sh:536-544,710-713`、`tools/pegasus/fetch_third_party.py:370-376`。  
   **深刻度:** High