# T-2737 author probe (2026-09-18)

成果物はこの README、`t2737_gate_probe.py`、`patches/` の試作 patch 2 本。
`work/` は clone、作成補助スクリプト、前処理出力、実走 receipt の作業領域で、配布する 4 成果物には含めない。
親が必要な receipt を別途回収する。tracked file は変更せず、commit / git add / stash / branch 操作はしていない。

**shadow-T は TPCC owner TU の機構診断である。stock の YCSB target / owner TU を必要とする D2120 の比較は未成立。**
本 probe の完走 rc=0 は gate admission の緑を意味しない。採否、性能、runtime correctness は結論しない。

## 試作の固定範囲

- 現行 patch を network-free clone に apply し、既存ファイルの `git diff HEAD` と新規ファイルの unified diff を結合した。`git add -N` も使っていない。両版の clone/apply を実走済み。
- DLR marker は `DLR1` 固定。stock DLR 分岐を数値 `SS2PL_DLR` に変え、IMPL=0/DLR=2 は明示的に拒否する。KIND の新しい意味論は追加しない。
- lock / study / WFG header は include guard。rwlock の既存 pragma と依存 include は保持し、class のみ条件化。study 依存 include は無条件、宣言・定義は IMPL=1 内。WFG owner include は無条件、宣言は WFG 内。`wfg.cc` の CMake source 条件は維持した。
- common の legacy flags と transaction header の include 位置・constructor 出力を復元。`begin/update/delete_record/read_lock/write_lock/unlockList` は、IMPL=0・WFG=0・非 YCSB の分岐に stock の本文を配置した。それ以外は現行の study/YCSB/診断経路を保持する。DLR の名称置換以外は stock 本文を再実装していない。
- revS は非 YCSB の abort 増分を復元。abort-unconditional はこの 5 行ブロックを除去した負例対照。patch 後イメージの検算と、実際に apply した 19 changed paths の比較で、差がこのブロックだけと確認した。index hash と hunk 行番号は派生差分として変わる。
- F1 fix: `insert()` の既存 tuple 検査を両 patch で stock 逐語 `if (tuple != nullptr) { return Status::WARN_ALREADY_EXISTS; }` に復元した。他の patch 行は変更していない。`ERR` の `__LINE__` は上流への行追加で stock 97 / revS 154 となる。人為的な行番号同期は今回の fix 対象外なので、`#line` 指令では消さない。
- 現行 patch に元からある test hunks は継承したが、新しい test hunk や repo の test 変更は加えていない。

以下の phase1 一致は F1 修正前の結果（修正後の再実走は末尾）: 静的 diff は `work/phase1-source-review.json`。`wfg.cc` / `ycsb_ss2pl.cc` / `util.cc` は現行 patch の適用木と byte 同一。
transaction と関連 header 計 6 本は include と pragma を除いた局所ソースについて、YCSB phase1 define 下の `c++ -E -P` 出力が一致した。
marker は現行 DLR0 / revS DLR1 を各々与えた。study 本文・WFG 呼出しを保つことの局所確認であり、依存閉包や linked binary の挙動の証明ではない。非 YCSB の abort 復元は明示した変更である。

## author 段の login 実走（F1 修正前の履歴）

node は `pegasus02`。`c++` は `/usr/bin/x86_64-linux-gnu-g++-11` (11.4.0)、CMake は `/usr/bin/cmake` (3.22.1)。
以下の変数はすべて絶対パスに展開する。cwd は R。

```sh
R=/work/1/SFC/tanab/izanagi/.codex/worktrees/t2737-probe
P="$R/probe-t2737"
python3 -B "$P/t2737_gate_probe.py" --repo-root "$R" --selftest
```

author 時点の selftest rc=0。次の既存 15 項目は tmp / clone / configure を使わない合成入力で、すべて PASS。
現行 selftest は F2 の入口検査 2 項目を加えた 17 項目で、`tempfile.TemporaryDirectory` を使用する（末尾参照）。clone / configure / helper 本体は呼ばない。

```text
shadow-accept-O                     PASS
shadow-accept-T+                    PASS
shadow-accept-T-                    PASS
shadow-reject-inert_values          PASS
shadow-reject-owner_tus             PASS
shadow-reject-expression            PASS
shadow-reject-non-SS2PL              PASS
shadow-reject-logic                 PASS
cell-count-45-and-unique            PASS
prediction-vocabulary              PASS
execution-order                    PASS
abort-pair-accept                  PASS
abort-pair-reject-extra-change      PASS
patch-no-final-newline              PASS
abort-if0-token-scan                PASS
```

login-precheck の実走 argv (最終 receipt にも完全な argv を保存):

```sh
python3 -B "$P/t2737_gate_probe.py" \
  --repo-root "$R" \
  --patch-current "$R/patches/ss2pl-lock-protocol-study.patch" \
  --patch-redesigned "$P/patches/ss2pl-lock-protocol-study-define-only.patch" \
  --patch-abort-unconditional "$P/patches/ss2pl-lock-protocol-study-define-only-abort-unconditional.patch" \
  --shadow-root "$P/work/shadow" --scratch-root "$P/work/scratch" \
  --gflags-prefix /work/1/SFC/tanab/ss2pl-study-deps/gflags-install \
  --glog-prefix /work/1/SFC/tanab/ss2pl-study-deps/glog-install \
  --thirdparty-root /work/1/SFC/tanab/dev-wave-jobs/t2644-deps/thirdparty-src \
  --jobs 48 --output "$P/work/login-precheck-final.json" --cells login-precheck
```

`work/login-precheck-1.json` は rc=1: pair 検算が現行 patch の `No newline at end of file` 記号を扱えず、clone/configure 前に停止した。
修正後の `work/login-precheck-2.json` は rc=0 (136.95 秒)。最終版の結果は末尾の確定結果欄に記す。
warm 済み staging を attempt ごとに `cp -a` した。`staging_state=preexisting`、masstree/config.h は 10,448 bytes、SHA256 `e9a4ecd3dfb9aef9c159e99cb2b7000651a2036ec909095f750b2c891404694a`。
これは pristine や warm-up 成功の証拠ではない。原本の config.h は前後一致した。

`tpcc_ss2pl.exe` の transaction entry を両木で同じ configure_args から取得し、`-E -P` の実 stdout を `cmp` した結果は **不一致 (cmp rc=1)**。
path の source root だけを置換した診断 diff は **4 行 (削除2・追加2、2 箇所)**。空白や行番号を正規化して緑にしていない。
先頭 20 行は次のとおり (原本 .ii、実 argv、全文 diff は attempt 配下と receipt に保存)。

```diff
--- stock
+++ revs
@@ -139728,7 +139728,7 @@
         break;
       }
       default:
-        do { perror("ERROR"); do { fprintf(stderr, "%ld %16s %4d %16s\n", (long int) pthread_self(), "<SOURCE_ROOT>/cc/ss2pl/transaction.cc", 97, __func__); fflush(stderr); } while (0); exit(1); } while (0);
+        do { perror("ERROR"); do { fprintf(stderr, "%ld %16s %4d %16s\n", (long int) pthread_self(), "<SOURCE_ROOT>/cc/ss2pl/transaction.cc", 154, __func__); fflush(stderr); } while (0); exit(1); } while (0);
     }
   }
   unlockList();
@@ -139851,7 +139851,7 @@
 Status TxExecutor::insert(Storage s, std::string_view key, TupleBody&& body) {
   if (searchWriteSet(s, key)) return Status::WARN_ALREADY_EXISTS;
   Tuple* tuple = Masstrees[get_storage(s)].get_value(key);
-  if (tuple != nullptr) { return Status::WARN_ALREADY_EXISTS; }
+  if (tuple != nullptr) return Status::WARN_ALREADY_EXISTS;
   tuple = new Tuple();
   tuple->init(std::move(body));
   Status stat = Masstrees[get_storage(s)].insert_value(key, tuple);
```

revS×T−×S×IMPL の実 gate は `stock-inert-mismatch`、meaning は `unestablished / meaning-witness-undeclared`。
1 cell のみなので family admission は作っていない。runner の abort 所有権は revS を拒否 (transaction=1, workload=2)、abort-unconditional を受理 (0,2)。
`_study_lock_header_declarations` は両版を受理。予測された静的拒否と gate red は probe 内部例外に数えない。

`python3 -B probe-t2737/work/check_phase1_projection.py` は最終 rc=0 (局所 6 比較一致、raw 3 比較一致)。初回は現行 lock header の DLR marker を渡し忘れ rc=1、marker を各版どおり補って再実走した。
pytest nodeid は無し。許可された probe selftest / configure / 前処理を直接実走した。plain build、masstree warm-up、trial、計算ノード 45 cell はすべて **未実走**。

## compute 投入の推奨形 (未投入)

親が 4 成果物を J/probe 以下へ同じ相対配置で退避し、J/thirdparty-src に保存用 pristine staging を準備した後に使う。
この argv の cwd は投入 worktree R。shadow/scratch/output は dispatcher の read-only submission directory の外に置く。

```sh
R=/work/1/SFC/tanab/izanagi/.codex/worktrees/t2737-probe
J=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2737-ss2pl-gate-controls
cd "$R"
python3 -B "$R/tools/pegasus/dispatch_compute.py" --task generic --walltime 00:40:00 -- \
  python3 -B "$J/probe/t2737_gate_probe.py" --repo-root "$R" \
  --patch-current "$R/patches/ss2pl-lock-protocol-study.patch" \
  --patch-redesigned "$J/probe/patches/ss2pl-lock-protocol-study-define-only.patch" \
  --patch-abort-unconditional "$J/probe/patches/ss2pl-lock-protocol-study-define-only-abort-unconditional.patch" \
  --shadow-root "$J/shadow" --scratch-root "$J/scratch" \
  --gflags-prefix /work/1/SFC/tanab/ss2pl-study-deps/gflags-install \
  --glog-prefix /work/1/SFC/tanab/ss2pl-study-deps/glog-install \
  --thirdparty-root "$J/thirdparty-src" --jobs 48 \
  --output "$J/receipts/probe-result.json" --cells recommended
```

CLI では T− を ASCII `T-` と表す。個別 ID は `patch.registry.arm.axis.staging` (例 `revs.T+.phase1.kind.warm`)。
45 cell の表は `cells_and_order()` が定義し、実走 receipt は選択 cell ごとに予測・条件・観測を保持する。
推奨順は pristine 8 → helper warm-up 1 回 → 対応 warm 8 → KIND 固定 target 対 (T+ 1、T− 4) → abort 対照4 → plain build2 → 残り20。
4 軸揃った組だけ、同じ shadow module の record で family を評価する。別登録簿・staging 間で record を混ぜない。

## 実装上の境界と未確認点

- repo gate bytes から許可した完全一致 block 置換だけで 9 shadows を生成し、既存ファイルが不一致なら停止する。正準 module/package/source_digest の identity、patch 解決先、全 record の canonical JSON を保存する。
- 保存用 staging は使う前に attempt/staging へ複製し、pristine の config.h 不在を確認する。warm-up は指定の `observed_toolchain_manifest` → `prepare_masstree_fetchcontent` のみ。probe に生の masstree target build 呼出しは無い。
- configure-failed 時は別 build directory で requested/control 各側を最大1回ずつ診断 configure し、stdout/stderr 全文を保存する。元の gate 判定は変更しない。
- 39 分を超えてから新しい action は開始せず、budget 未実施を明記する。開始済み action は subprocess timeout (gate 既定、warm-up 300/600、plain build 1800 秒) を持つため、40 分以内の完走は保証しない。各 action / cell と最上位例外で atomic 保存し、強制終了時は直前の receipt を回収する。
- PBS_JOBID は env → 同 hostname の最新 compute-visible → unknown の順に得た **候補**。親が dispatcher receipt と照合する。計算ノードモードは bnode 以外で拒否する。
- S が不一致のため、条件付き I 予測は現状 M に倒れる。両版 red だけでは abort 単独の因果対照が成立したとはいえない。KIND の従属、stock YCSB target 不在、runtime meaning 未宣言は残る。
- `collect_inert_witness` と stock-lock 不在性の本走は未実走。宣言差分一致 flag が false になり得るが、それ自体を契約例外とは扱わない。plain S の WFG 不在性検査は compute build 成功後に実行する。
- 所有外 caller、共有 fixture、consumer test への repo 内波及は **0 件**。新しい import / 登録 / caller は tracked file に追加していない。`git grep -n -E 't2737_gate_probe|probe-t2737/|ss2pl-lock-protocol-study-define-only'` を実走し、rc=1、該当なしを確認した。試作 patch を将来 production に採用した場合の波及は別作業であり、本成果からゼロとは主張しない。

## author 段の確定結果（F1 修正前の履歴）

最終 selftest **rc=0 / 15 PASS**。上記 argv の最終 login-precheck は **rc=0 / complete / 408.36 秒**。
receipt は `work/login-precheck-final.json`、attempt は `work/scratch/attempt-97c7ed19dcb74877980bb649429fcd00/`。
S は **cmp rc=1 / 残差4行**、実 IMPL cell は **stock-inert-mismatch** (57.64 秒)。上記 20 行 diff と一致した。
abort 所有権は revS 拒否 / abort-unconditional 受理、study header 抽出は両版受理、9 shadow の生成・identity・patch 解決先検査は完了した。
receipt に記録した probe・3 patch・runner・gate の全 SHA256 が完走後の実ファイルと一致することを確認した。
`git status --porcelain` は rc=0、出力は `?? probe-t2737/` のみ (tracked 無変更)。
plain build、warm-up、trial、計算ノード cell は未実走。S 一致未達以外に、裁定の復元範囲や45 cell の推奨順を変更していない。

## F1 fix の再実走 (2026-09-18)

両 patch の `insert()` hunk を stock 本文に復元した。revS は patch 909 行の
`@@ -345,19 +593,55 @@` 内 913 行、abort-unconditional は 905 行の
`@@ -345,19 +588,55 @@` 内 909 行。削除・追加の対を stock の context 1 行に戻し、
hunk の old/new 行数・他の patch bytes は変えていない。probe 本体は無変更。

selftest は上記と同じコマンドで再実走し **rc=0 / 15 PASS**。
`python3 -B probe-t2737/work/check_phase1_projection.py` は **rc=1**。
補助スクリプトの入出力 receipt 名だけを `login-precheck-f1.json` /
`phase1-source-review-f1.json` に変更し、新しい適用木を比較した（判定処理・期待値は無変更）。
局所 6 比較中 5 一致、raw 3 比較は全一致。transaction の唯一の差は:

```diff
-  if (tuple != nullptr) return Status::WARN_ALREADY_EXISTS;
+  if (tuple != nullptr) { return Status::WARN_ALREADY_EXISTS; }
```

この共通行の stock 復元は YCSB/IMPL=1 にも現れるため、現行 patch との phase1 前処理
bytes 一致は維持されなかった。return 文を囲む brace だけの差であり、study lock / WFG
呼出しの変更はない。ただしこの局所検査を binary 挙動の証明とは扱わない。
「当該行の復元のみ、他行変更なし」と「phase1 bytes 一致」の同時達成はできず、
条件分岐追加や比較結果の正規化は行っていない。repo の test / 期待値は無変更。

login-precheck は上記 argv の `--shadow-root` を `$P/work/shadow-f1`、
`--output` を `$P/work/login-precheck-f1.json` に変更して再実走。
既存 shadow は旧 patch に束縛されているため保存し、新規 shadow を生成した。

pegasus02 上で **rc=0 / complete / 98.28 秒**。
attempt: `work/scratch/attempt-d9e05ed0edef4823bb14c8587a202ca1/`。
S は **cmp rc=1 / path 差以外の残差2行（削除1・追加1、1箇所）**。
`ERR` の `__LINE__` 展開値 stock 97 / revS 154 のみが残った。

```diff
--- stock
+++ revs
@@ -139728,7 +139728,7 @@
         break;
       }
       default:
-        do { perror("ERROR"); do { fprintf(stderr, "%ld %16s %4d %16s\n", (long int) pthread_self(), "<SOURCE_ROOT>/cc/ss2pl/transaction.cc", 97, __func__); fflush(stderr); } while (0); exit(1); } while (0);
+        do { perror("ERROR"); do { fprintf(stderr, "%ld %16s %4d %16s\n", (long int) pthread_self(), "<SOURCE_ROOT>/cc/ss2pl/transaction.cc", 154, __func__); fflush(stderr); } while (0); exit(1); } while (0);
     }
   }
   unlockList();
```

revS×T−×S×IMPL の `reason_code=stock-inert-mismatch`、gate evidence の
`root_diff_line_count=1`。これは上記 unified diff の削除・追加を数えた2行とは別の指標。
meaning は `unestablished / meaning-witness-undeclared`。S bytes 一致は未達である。

2版の symbolic postimage 検算は accepted=true（19 paths）。実際に適用した木も
`cc/ss2pl/transaction.cc` の abort 5行ブロックだけが違うことを再確認した。
abort 所有権は revS 拒否 / abort-unconditional 受理、study header 抽出は両版受理。
9 shadow の生成・identity・patch 解決先検査も完了。

F1 は **partial**: stock 本文復元と S 残差縮小は完了したが、要求された phase1
局所前処理一致は rc=1 のため達成していない。`#line` 同期は指定どおり実施しない。
`python3 tools/check_codex_agents.py` と `python3 tools/check_docs.py` は rc=0。
plain build、masstree warm-up、trial、計算ノード cell は未実走。
最終 `git status --porcelain` は `?? probe-t2737/` のみ。tracked file 無変更、commit / git add / stash / branch 操作なし。

## F2 fix と selftest 再実走 (2026-09-18)

親の計算ノード job 1（07:25 JST、request `5036.nqsv`）の受領証
`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2737-ss2pl-gate-controls/receipts/probe-result-1.json`
では、`warm_up.error` が `BuildCacheError: FETCHCONTENT_BASE_DIR は non-symlink directory 必須`。
未作成の attempt/fetchcontent を渡したため 0.019862574 秒で内部例外となり、
`warm_up.before/after` とも masstree/config.h は不在だった。親の所見では warm cell も
`preprocess-failed` となり、(iii) の対は取れていない。これは親の実走であり、上の未実走記載は各 author/fix 段自身の履歴である。

warm-up の helper 呼出し前に `base = attempt / 'fetchcontent'` →
`base.mkdir(exist_ok=True)` → `base.resolve(strict=True)` を追加し、その canonical path を
`kwargs['fetchcontent_base_dir']` に渡す。receipt の `warm_up.fetchcontent_base_dir` に実 path、
`warm_up.fetchcontent_base_checks` に呼出し前の `isdir` / `islink` /
`realpath_equals_abspath` の検査結果を保存する。正常時の期待値は順に true / false / true。
patch 2 本は変更していない。

pegasus02 で次を再実走し、**rc=0 / 17 PASS / 0 FAIL**。

```sh
python3 -B /work/1/SFC/tanab/izanagi/.codex/worktrees/t2737-probe/probe-t2737/t2737_gate_probe.py --repo-root /work/1/SFC/tanab/izanagi/.codex/worktrees/t2737-probe --selftest
```

追加した項目は `fetchcontent-missing-rejected` と `fetchcontent-mkdir-resolve-accepted`。
それぞれ TemporaryDirectory 内で不在 path の `BuildCacheError` と mkdir → resolve 後の受理を
実際の `buildcache._canonical_fetchcontent_base` で検査する。helper 本体は呼ばない。

F2 は **partial**: directory 作成漏れの修正と入口検査の負例・正例は完了。
修正後の計算ノード warm-up、config.h 生成、warm cell の回復と (iii) 対の成立は未実走・未確認。
login-precheck は指示どおり再実走していない。plain build / trial も本 fix では未実走。
