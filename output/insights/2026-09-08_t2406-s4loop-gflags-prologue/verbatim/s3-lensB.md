## 実効性の所見

- `[should] command -v`: `command` は shell builtin。gcc/g++ は sanitized PATH 上の `/usr/bin` から解決される想定だが、親が示す login node の realpath は bnode の実測ではない。欠落時は `refuse` ではなく rc=1 で終了する。
- `[real] cmake`: job 981655 は同じ PATH で CMake configure まで到達しており、少なくとも bnode116 では実在した。
- `[should] realpath`: `/usr/bin/realpath` の bnode 実測は射影資料にない。さらに配列代入内の2個の `$(realpath ...)` は最後の substitution の rc が代入全体の rcになるため、CC側だけの失敗がCXX側成功で隠れ、空の compiler 指定へ進み得る。事前に2本を別々に解決して外側で失敗処理すべき。
- `[conditional] git`: `GIT_OPTIONAL_LOCKS=0` は `rev-parse` と read-only の `status` を妨げず、既存 job も同設定で Git 検査を通った。ただし `/work/SFC/tanab/github/gflags` と glog 自体を bnode から検査した一次 artifact はなく、可視性、所有者、clean 状態は job 開始時の再検査頼み。
- `[real] mkdir`: fresh な job 別 scratch の配下なので build dir の create-only `mkdir` は整合する。install dir は CMake install が作るため事前作成不要。
- `[should] timeout`: いずれかの configure/build/install が timeout すると `timeout` は通常124を返し、`set -e` が直ちに EXIT trap を起動する。`compute-result.json` には `driver_rc:124` が入り、rc=2の refusal message は出ない。通常の CMake 失敗も1などの生 rcで、「driver_rc」が prologue の失敗を表す点は明記が必要。
- `[should] command substitution`: 提案本文中の Python/Git substitution は単独代入なので失敗 rcが親へ伝わり `set -e` で停止するが、`refuse` 自体を `$(...)` 内へ置いても親 shell を直接終了させない。既存コードは `repo=$(...) || refuse`、`if ! value=$(...); then refuse; fi` と外側で処理している。この形を移植側にも使わないと rc=2境界が揃わない。
- `[should] -j 48 / 60秒`: D1773は兄弟経路の実機成功を述べるが、射影された一次資料には gflags/glog の job ID、時間、stdout/stderrがない。job 981655はこの prologueを実行していないため、gen_Sで60秒以内という一般化を支えない。放置時は契約テストが緑でも prologue timeout で停止し得る。
- `[real] umask/TMPDIR`: 0700の scratchと `umask 077` は同じjob内のCMake、Python、driverによる利用を妨げない。

## 順序と依存の所見

- `[real] 挿入位置`: [job body](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2406-s4loop-gflags/tools/pegasus/p3_s4_loop_pegasus.sh:317) の `claim_root` 後では、`resolve_python`、`PY`、scratch、`TMPDIR`、shim、最終PATH、`cd "$repo"`、EXIT trapはすべて準備済みであり、prebuild呼出しより前である。
- `[must-fix] marker不足`: 段2が追加する marker 列は prologue 内部順序を固定するが、依存している `export TMPDIR=$scratch` と `export PATH="$SANITIZED_PATH"` を固定しない。両 markerを `POLICY=...` より前へ加えないと、初期化を後ろへ動かす mutantが通り得る。
- 推奨列は、既存の `resolve_python`、`export TMPDIR=$scratch`、`export PATH="$SANITIZED_PATH"`、repo検査、qstat、claim、policy、gflags install、glog install、prefix export、`prebuild_source_root`、prebuild Python の順。
- `[nit] 位置の選択`: qstat/reservation/claimの前へ移せば依存欠落を早く検出できるが、現位置も機能上は正しい。現位置では prologue失敗時にも reservation artifactとclaim rootが残る、という差だけがある。

## 契約テストとの相互作用

- `[real] heredoc変換`: `"$PY" -I -B - "$POLICY" <<'PY'` は `<<< ''` へ置換後も `policy_output=$(...)` として `bash -n` 上有効。Python本文の文字列は走査面から除かれる。
- `[real] shell構文`: `readarray`、`case`、配列argv、command substitutionは既存jobにも既にあり、shlex走査を壊さない。追加本文にqsub tokenもない。
- `[real] -I`: policy readerはstdlibのjson/re/sysだけなので `-I -B` が適切。`orchestrator` をcwdからimportする prebuild heredoc、campaign PIN取得、driver `-m` に `-I` を付けてはならない。
- `[must-fix] retention未固定`: 段2の `prefix_assignments` は exact exportを1回に限定するが、その後の `unset CMAKE_PREFIX_PATH` を検出しない。export後にunsetする mutantでも正例が通り、D1773(d)の「driver本走まで保持」を破れる。
- 対応は、既存の初期 `unset CMAKE_PREFIX_PATH CMAKE_TOOLCHAIN_FILE` がexact 1回かつexport前であること、export後にunsetがないこと、exportがprebuildと両driver分岐より前であることを固定すること。これは拒否緩和ではなくD1773の受理形を狭く固定する修正である。
- `[should] refusal試験`: 新しい8 messageは明示的な `refuse` 箇所だけを覆う。Python parse、Git起動、realpath、timeoutの失敗がrc=2になることは証明しないため、P1を「prologue全失敗がrc=2」と説明してはいけない。

## compiler の一致

- `[real] current bnode contract`: [buildcache.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2406-s4loop-gflags/orchestrator/campaign/buildcache.py:1838) は `site_policy` が `PEGASUS_COMPUTE` のとき `("gcc","g++")` を返す。site判定はbnodeの先頭hostname labelであり、job bodyのhost条件と整合する。
- `observed_toolchain_manifest` は同じ環境PATHで `shutil.which` と realpathを使う。prologueも同じ sanitized PATHで `command -v` と realpathを使い、その後PATHを変えないため、実行時には同じ `/usr/bin` compiler実体を指す。
- 親がlogin nodeで得た `x86_64-linux-gnu-gcc-11` という具体値の一般化は不要かつ未証明だが、「prologueとprebuild/driverが同一compilerを解決する」という相対的な一致は成立する。
- `[must-fix if changed]` 異なるC++ compilerやlibstdc++ ABIでgflags/glogのstatic libraryを作ると、`std::string`等のsymbol ABI差によるlink失敗、または境界上の実行時不整合が起こり得る。現プランのPATH不変ならこの危険は顕在化しない。

## README の整合

- `[real] D1773文言`: 現在の「`CMAKE_PREFIX_PATH` は置かない」は削除必須。段2案の「wrapper/launcherは置かない」と「exact prefixだけをprebuild前からdriverまで保持」はF813の他の拒否を保ったまま両立する。
- `[must-fix] qsub cwd`: [README §7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2406-s4loop-gflags/tools/pegasus/README.md:338) は専用 `REPO_ROOT` を設定するが、qsub前にそこへ移動せず、job scriptを相対pathで指定する。実投入一次資料は明示的に `cd <REPO_ROOT>` していた。放置すると別checkoutのscriptを投入するか、file not foundになる。
- `[must-fix] submodule PIN`: §7は固定SHA checkoutだけを指示し、CCBenchを `p3_s4_loop.PIN` へdetached checkoutする手順がない。job 981655で既に「手順どおりなら必ずrc=2」と実証済みであり、T-2407のPIN checkout前提を手順へ反映する必要がある。
- `[should] stale F660`: 見出しと「計算ノードでは未実測」「main着地後にしか投入できない」はjob 981655後には不正確。host、sanitize、Python、reservation、claim、third-party複製は1回通過済みで、未実測なのは新prologue、prebuild成功、attestation、driver本走、walltime充足である。
- qsub fenceのstream routing、admission-site、契約bulletとは新しいpolicy内部読取やprefix exportは矛盾しない。

## 親の実測値の一般化

- `[conditional] source pin/clean`: 一次資料は2 sourceのHEAD exact一致とtracked/untracked cleanを記録しており、その時点の値は支持する。一方「detached HEAD」の確認方法とartifactはなく、branchが同じSHAを指す場合を排除できない。将来のjob状態はprologue再検査でのみ保証される。
- `[conditional] policy golden`: golden testの存在はwhole-file pin方式を示すが、そのtestをこのtipで実行した結果は射影資料にない。「pin機構がある」は支持するが「現在goldenと一致」は実測結果なし。
- `[conditional] 他fileにwhole-file pinなし`: 段2は `git grep` 相当とだけ記し、検索patternや出力を残していない。負の全域主張としては再現性が不足する。なお契約testによる多数のliteral pinは存在する。
- `[real] _run env継承`: `prepare_masstree_fetchcontent` は `_run(..., env=None)` を呼び、`_run` はenv指定時だけsubprocessへenvを渡すため、通常のprocess environment、従ってexport済みprefixを継承する。
- `[conditional] build_v2 identity`: `dependency_prefix`が空の場合、`build_v2` はambient `CMAKE_PREFIX_PATH`を正準化してidentityへ入れる。callerが明示prefixを与えず、途中でunsetしないことが条件であり、段2の契約案は後者をまだ証明しない。
- `[conditional] CLI flagなし/唯一経路`: jobのdriver argvにprefix flagがないことは確認できるが、CLI全体にflagがないという負の主張の測定方法は示されていない。またbuildcache APIには明示prefix引数があるため、「envが唯一」は現在のdriver配線まで追跡して初めて成立する。

## (P1)〜(P7) の判定

- (P1) **条件付き**。8個の明示的 `fail 2` を同文 `refuse` に写す範囲ではreal。Python、Git、realpath、CMake、timeoutまでrc=2境界だと一般化すればrefuted。
- (P2) **real**。両sourceで `--untracked-files=all` を保つ。ただしstatus自体の失敗はrefuseに写らず生rcになる。
- (P3) **real**。bnode判定時のbuildcacheも同じPATH上のgcc/g++を選ぶ。login nodeで観測したcompilerの具体的realpathだけは条件付き。
- (P4) **real**。redirectを落としてもqsubの `-o/-e` がjob全体をevidenceへ送る。代わりにcommand別の失敗位置はstdout/stderrから推定する必要がある。
- (P5) **条件付き**。ambient prefixのidentity束縛とjob別pathによるcache非再利用はコードどおり。ただしprefixのdriverまでの保持を契約testで塞ぐ修正が前提。
- (P6) **real**。必要なruntime初期化後かつprebuild前である。TMPDIR/PATH markerの追加が必要。
- (P7) **条件付き**。queue不能時にland条件から外す判断は可能だが、静的testだけでは今回の主要リスクを潰せない。実効性を主張するには1本のcompute smokeが必要。
- P7の投入前提は、固定SHAのdetached専用checkout、T-2407のCCBench PIN checkout、hydrate済みmasstree/mimalloc/googletest root、repository外のfresh attempt/evidence root、qsub前の `cd "$REPO_ROOT"`、未terminalのfixture値またはproposalである。加えて新policy source 2本がbnodeから可視でpin/cleanである必要がある。

## 裁定パッケージ候補 (scope 外)

- 固定 `-j 48` と60/120秒をsite affinityや実測値へ変えるかはD1773の「そのまま移植」を越える。未変更ならnode差によるtimeoutリスクを残す。
- pin/clean検査後の共有gflags/glog sourceをscratchへsnapshotするかは新しい完全性設計である。未変更なら検査とbuildの間に別processがsourceを変える競合を残す。

## 総括

段2プランは、そのままでは受理できない。must-fixは、契約testでexport後のunsetを拒否してTMPDIR/PATH順序を固定すること、READMEのqsubを専用checkoutから確実に投入すること、CCBench PIN checkout前提を手順化することの3点である。

compilerの相対的一致とpolicy heredocの静的解析は成立する。一方、`-j 48` とtimeoutのbnode実績、sourceのdetached状態、prologueからdriver終端までの成功は未証明である。pytestや実機jobは実行しておらず、緑とは判定していない。