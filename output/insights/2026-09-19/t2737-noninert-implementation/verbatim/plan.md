## 総括

**最小案は、`build_target()`の関門直前への既存helper接続と、patchのa〜d限定移植です。** eの条件付き`wfg.cc`は維持します。編集・build・pytestは実施していません。

親briefの方向は妥当ですが、[HANDOFF.md:26](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2737-noninert-codex/HANDOFF.md:26)のP1は未検証です。既存実測はf/gを含むrevS全体の結果であり、**a〜dだけの必要十分性を示していません**。今回の実物検証で閉じるべき中心命題です。

以下の行番号は現行ファイル基準です。patchの行番号は適用後C++ではなく、patchファイル内の位置です。

### 1. runnerの最小変更

対象は`tools/pegasus/run_ss2pl_lock_study.py`。

- **34行付近**：`buildcache`をimport。
- **2107〜2111行**：衝突検査後、`_require_condition_gates()`より前に`prepare_masstree_fetchcontent()`を呼ぶ。
- **1980〜2045行**：関門の要求生成・比較・admissionは変更しない。

helperの正本は`orchestrator/campaign/buildcache.py:2034`。全引数がkeyword指定で、必要な接続は次のとおりです。

| 引数 | runner側の値 |
|---|---|
| `ccbench_dir` | patched `source`の絶対パス文字列 |
| `fetchcontent_base_dir` | buildごとの専用ディレクトリを`mkdir`後、`resolve(strict=True)` |
| `expected_toolchain_manifest` | `observed_toolchain_manifest("cc", "c++")` |
| `dependency_prefix` | `gflags_prefix;glog_prefix` |
| `masstree_source_dir`等3本 | 関門と同じ`thirdparty_root`配下 |
| `configure_timeout_s`, `target_timeout_s` | 正整数、既存build段の残時間内 |

既存呼出し例は`tools/pegasus/probes/t316_sandbox_backend_probe.py:1897`と`:1920`。**baseの事前作成が必須**です。helperは共有stagingのmasstree側に`config.h`を生成するため、関門へ`FETCHCONTENT_BASE_DIR`を追加する必要はありません。

配置は`run()`だけに置くより`build_target()`内を推奨します。実物テストから直接呼んでも同じ準備経路を通り、既存signatureと3箇所のcallerを変えずに済みます。今回は準備済み管理や共有キャッシュを新設しません。

なおhelperはrunnerの`_run_checked()`を通りません。`StageDeadline`（122行）の残時間からconfigure/buildの予算を分配し、終了後も既存deadlineを確認する必要があります。固定timeoutだけでは現在の段上限を保存できません。

### 2. patchの限定移植

対象は`patches/ss2pl-lock-protocol-study.patch`。

| 位置 | 最小変更 |
|---|---|
| **19〜41行** | protocol CMakeの`_ss2pl_dlr_marker`分岐を削除し、`OPTIONS DLR1`固定へ戻す。 |
| **135〜187行** | `ss2pl_lock.hh`をinclude guard化。rwlock/study headerは無条件include、aliasだけ`IMPL==1`。`requires DLRn`エラーを除去し、試作の`IMPL==0 && DLR==2`拒否を移植。 |
| **194〜689行** | study headerをinclude guard化。依存includeを外側に残し、宣言・定義全体を`IMPL==1`で囲む。ロック本体は変更しない。 |
| **696〜715行** | WFG headerをinclude guard化。`<cstdint>`・`<string>`は無条件、宣言群を`#if SS2PL_WFG_DIAG`内へ。 |
| **1337〜1342行** | transactionのWFG header includeだけ無条件化。 |
| **1586、1645、1804、2020、2096行付近** | 旧DLR条件5組を`SS2PL_DLR == 0/1/2`による選択へ変更。`#ifdef DLR0`と`#if DLR0`の両方があるため全5組を対象にする。 |
| **追加hunk** | `include/rwlock.hh`の`ReaderWriteLock`クラスだけを`!defined(SS2PL_LOCK_IMPL) || SS2PL_LOCK_IMPL == 0`で囲む。 |

移植元は`output/insights/2026-09-18/t2737-ss2pl-gate-controls/verbatim/patch-revs.md`の1362行以降などです。ただし丸ごと置換はしません。

特に次を区別します。

- revSは`SS2PL_DLR`未指定時の旧`DLRn`フォールバックも削除しています。明示defineを渡す今回の4軸には不要なので、**既存フォールバックを残す案**を推奨します。
- test CMakeの`SS2PL_TEST_DLR_MARKER`（現行846行）はrevSにも残っています。protocol側固定化と混同して変更しません。
- **30行の`wfg.cc`条件、common/transaction headerのf/g復元、abort増分、`insert()`のbrace復元は変更しません。**
- patch適用・逆適用を確認できるよう、authorは適用木から正しいhunk位置・行数で再生成します。

### 3. P1と親briefの検査結果

`run_ss2pl_lock_study.py:48`のphase1は`IMPL=1, KIND=0, DLR=0, WFG=1`。関門は全define同時の比較ではなく、**4本の個別軸比較**です。

| 軸 | a〜dで閉じる対象 | 実物検証の期待 |
|---|---|---|
| IMPL 1対0 | 条件includeによる依存閉包差 | `requested-default-preprocess-different` |
| KIND 0対1 | 現状でも成立。companion IMPL=1を維持 | 同上 |
| DLR 0対1 | `-DDLR0`対`-DDLR1`のargv差 | 同上 |
| WFG 1対0 | 条件includeによる依存閉包差 | 同上 |

`condition_meaning_gate.py:160`の登録簿はそのまま使います。meaningは`declaration=None`なので未成立のままです。受入対象は既存`raw-measurement` family admissionであり、runtime meaningの認証ではありません。

親briefの「診断再開の土台」（HANDOFF:14）は成立範囲として適切です。ただしrunnerは**3164行でSからbuildし、3184行で初めてphase1へ進む**ため、controlsを実行してphase1の成立証拠を取る計画にはできません。今回の確認はproductionの`build_target(arm="phase1")`を直接通します。

### 4. 既存テストと必要な実物検証

`orchestrator/tests/test_ss2pl_lock_study.py`の既存検証には次の限界があります。

| 位置 | 現在確認していること | 今回の証拠にならないこと |
|---|---|---|
| **35行** | `inspect.getsource`による呼出し順・文字列 | helperによるconfig.h生成、実関門成立 |
| **49行** | 実関数によるcache→軸要求変換 | CMake・前処理結果 |
| **491〜544行** | 人工WFG evidenceとcollector stubへの拒否 | 実binary・実TUの計器不在 |
| **558〜584行** | 小さな自作C++断片のabort所有権 | 適用後patchの所有権保存 |
| **1301行** | build等をstubしたqstat障害時の継続 | production build経路 |
| **1574行** | fake processによるWFGファイル収集 | 実計器呼出しの保存 |

`test_buildcache_v2.py:1917`と`:1980`も`buildcache._run`をstubしています。helperのargv構築検証であり、pristine準備成功の代替にはなりません。

親が`run_tests.py`経由で実施する実物検証は、次に絞ります。

1. **pristineからproduction経路を通す。**  
   config.h不在のstaging複製、stock clone、限定patch適用cloneを用意し、helper・gate・CMake・compilerをstubせず`build_target(arm="phase1")`を呼ぶ。生成config.h、4 supply record、4 meaning record、family admission、実binaryを確認する。

2. **計器呼出しを旧patchと比較する。**  
   旧patchと限定patchの両方をphase1条件で実configure/buildし、`_target_compile_entries()`（871行）と`_preprocess()`（1185行）で全target TUを前処理する。宣言名の存在だけでなく、関数body内の呼出し・引数・制御構造を比較する。主対象は以下です。
   - transactionの`publish_wait/acquired/failed/released`と呼出し箇所（patch:1385以降）。
   - `begin()`の`ss2pl_wfg_register_worker`（1512行）。
   - ycsbの`ss2pl_wfg_start/stop`（2697、2722行）。
   - study lock本体と`wfg.cc`本体。

   include/pragmaを除いた孤立6ファイルの比較だけでは不十分です。全TU差分ではパスや`__LINE__`由来の差を個別説明し、比較関門自体は緩めません。

3. **WFG=0と既存契約を実体で確認する。**  
   Sのplain buildに対して既存`_wfg_absence_evidence()`（2054行）を実行し、source list・nm・strings・全TU前処理の不在を確認する。これはSの関門認証とは分ける。適用木へ`validate_abort_counter_ownership()`と`_study_lock_header_declarations()`も実行する。

### 5. 変異候補と波及範囲

変異は一度に1種類とし、拒否箇所を区別します。

| 変異 | 対応する検証 |
|---|---|
| helper呼出し削除／関門後へ移動 | pristine経路がconfig.h欠落で失敗 |
| study headerを再び条件include | IMPLの依存閉包比較で拒否 |
| transactionのWFG headerを再び条件include | WFGの依存閉包比較で拒否 |
| protocolのDLR marker分岐を復活 | DLRのcompile-command比較で拒否 |
| phase1の`publish_wait`呼出しを1箇所削除 | 呼出し保存比較で拒否。関門だけで検出できるとは主張しない |
| `wfg.cc`を無条件sourceへ追加 | WFG=0の実不在検査で拒否 |

波及caller・consumerは以下です。

- runnerの`build_target`呼出し3箇所：3165、3176、3185行。signature維持なら修正不要。
- shell入口：`tools/pegasus/ss2pl_lock_study.sh:253`。CLI変更不要。
- receipt consumer：`tools/plotting/plot_ss2pl_lock_study.py:114`。既存schema維持。
- 共有`rwlock.hh`のconsumer：`external/ccbench/cc/d2pl/include/transaction.hh:10`。SS2PL macro未定義時に従来クラスが残ることを確認。
- patch内のbomb/tpcc、SS2PL unit testsも共通headerのconsumer。特にtest側DLR markerは維持して回帰確認。
- 登録簿・gate・buildcache helper本体・abort所有権・inert宣言差分は編集対象に追加しません。

新しいgate、台帳、controls迂回modeは不要です。受入結果は「phase1の4軸・実build・計器保存」と「controls全体未成立」を分けて記録してください。