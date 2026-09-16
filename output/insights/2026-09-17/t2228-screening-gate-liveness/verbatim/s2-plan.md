## 投入 argv

**P1 は正規 CLI への到達形として成立するが、そのままでは brief の「投入元 worktree は指定領域以外へ書かない」を満たさない。** CLI が投入元 `external/ccbench` に一時的に patch を適用するためである。この衝突を親が段 4 で解決するまでは、以下を投入承認済みのコマンドとは扱わない。

環境を具体化した P1 は次の形になる。先頭の `-B` は dispatcher の import による bytecode 書込みを避けるための追加である。ここでは実行していない。

```bash
python3 -B tools/pegasus/dispatch_compute.py \
  --task generic \
  --walltime 01:30:00 \
  --queue-wait-timeout 3600 \
  --overall-grace 3600 \
  -- /usr/bin/env \
  PATH=/usr/bin:/bin:/opt/nec/nqsv/bin:/system/tool/bin \
  IZANAGI_OFFICIAL_OUTPUT_ROOT=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2228-screening-liveness/attempt-20260917a-official \
  CMAKE_PREFIX_PATH=/work/SFC/tanab/ss2pl-study-deps/gflags-install:/work/SFC/tanab/ss2pl-study-deps/glog-install \
  http_proxy=http://10.120.96.1:8080 \
  https_proxy=http://10.120.96.1:8080 \
  TMPDIR=/scr \
  python3.10 -I -B \
  orchestrator/campaign/backoff_sweep.py \
  write-heavy --screening --screening-fixed-us 2
```

子 interpreter は `python3.10` と明示する。dispatch が検査する interpreter と、generic argv 内の裸の `python3` は別の名前解決だからである。手元では `/usr/bin/python3` も `/usr/bin/python3.10` も同じ実体だったが、これは計算ノードでの観測ではない。dispatch の候補は `dispatch_compute.py:408–412`、検査と PATH 設定は `892–913`、generic argv の直接実行は `1660–1674`。

以下の行番号は現 worktree のもの。

| 入力 | 採用値・扱い | production の読取・根拠 |
|---|---|---|
| `IZANAGI_OFFICIAL_OUTPUT_ROOT` | 上記の未使用 attempt 専用絶対パス | [layout.py:412](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-liveness/orchestrator/campaign/layout.py:412)。環境値は422行、絶対パス・symlink・`.git` 祖先・所有者検査は323–367行。存在済みで空でない root も許すため、今回の新規性は親が未使用パスで確保する。 |
| `CMAKE_PREFIX_PATH` | 上記2 prefix、**環境値なので `:` 区切り** | `buildcache.py:2624–2636`、正準化は1881–1885行。prepare は明示 prefix 引数なしなので subprocess の環境を継承する。 |
| `http_proxy` / `https_proxy` | ともに `http://10.120.96.1:8080` | `buildcache.py:3799–3807` が環境を継承して CMake を起動。実際の URL 消費は CMake/Git 側で、Python の `getenv` ではない。取得先は `external/ccbench/cmake/ThirdParty.cmake:35–55`。A-5 の先例は32、210–213行。 |
| `TMPDIR` | `/scr` | `patchharness.py:116,362` が直接読む。関門の一時 base は `backoff_sweep.py:440–443`、`screening_driver.py:198–202` の `TemporaryDirectory`。stdlib の読取は `/usr/lib/python3.10/tempfile.py:302–304`。 |
| `IZANAGI_BENCH_LOCK` | **指定しない**。既定の `$HOME/.izanagi/bench.lock` | [lock.py:24](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-liveness/orchestrator/campaign/lock.py:24)。29–34行で解決・親 directory 作成。A-5 の job 固有 lock と異なり、既定を使う同一ユーザーの bencher と共有できる。 |
| `PATH` | A-5 と同じ固定値 | A-5:199。compiler 選定は `buildcache.py:1863–1867` で Pegasus の `gcc/g++`、続いて manifest を観測する。 |
| `HOME`・locale 等 | generic の基底環境を継承 | `dispatch_compute.py:349–359,1442–1452`。これ以外の親環境を暗黙に引き継ぐ計画にはしない。 |

`-I` は `os.environ` を消さない。書込みを伴わない stdlib の小検査で、`isolated=1`・`ignore_environment=1` の下でも指定した任意の環境値を読めることを確認した。Python 自身の設定用環境変数を無視することと、production の `os.environ.get(...)` は別である。`-B` は明示して維持する。

不要な設定は次のとおり。

- `ENV_TAG=pegasus`：A-5:570–577 のローカル変数であり、export ではない。CLI は `p2_2.py:235–253` で実 site から契約を解決する。
- A-5 の `IZANAGI_RESERVATION_*` 8変数：A-5:399–406 が export するが、この screening 分岐は reservation reader を呼ばない。reader 自体は `reservation.py:120–128,159–174`。A-5 の予約証跡を generic が代替する、という意味にはしない。
- `A5_*`・`JOB_SCRIPT_SHA256`・`PBS_NODEFILE`：A-5 job body の入力。対象 CLI の入力ではない。`PBS_JOBID` も site 分類条件ではないことが `site_policy.py:30–41` に明記されている。
- `IZANAGI_THIRDPARTY_SOURCE_ROOT`：A-5:514 の依存 source 準備用。今回は既存 install prefix を使う。
- `IZANAGI_PEGASUS_THIRDPARTY_CACHE`：前回 probe は使うが、この CLI の prepare 呼出しは source directory を渡していない。設定だけで offline 取得にはならない。
- `IZANAGI_S4_EVIDENCE_ROOT`：この経路では効かない。
- `CC/CXX`・`LD_LIBRARY_PATH` 等：追加しない。現経路の compiler は site と manifest から決まり、既存 prefix の link 成否は実測対象とする。

A-5 にない追加の必須環境変数は確認できなかった。between-run floor は official root ではなく、repo の `output/env/pegasus/calibration` から読むため、`--calibration-dir` も不要である。根拠は `screening_driver.py:285–298,473–478` と `layout.py:600–603`。

**P1 と不変条件の衝突箇所：**

- `backoff_sweep.py:433,437–438` は投入元の CCBench を `patchharness.applied` に渡す。
- `patchharness.py:255–263` はその tree に `git apply` し、終了時に revert する。
- stock checkout も `patchharness.py:362–374` で元 repository の worktree 管理情報を更新する。
- generic の read-only mount は request directory だけである。`dispatch_compute.py:273–281,1669–1674` は投入元 tree を保護しない。

したがって、**終了後に clean に戻ることは「投入中に書かない」の代替にならない**。必要なのは A-5:449–470 と同じ目的の隔離済み実行 tree への変更であり、環境値だけでは解消できない。新 launcher の実装は本プランに含めず、P1 の修正事項として親へ返す。

## A-5 との差分表

A-5 は [job body](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-liveness/tools/pegasus/a5_second_boot_backoff_sweep.sh:179) を指す。

| 段 | P1 との関係 | 判定・record の意味への影響 |
|---|---|---|
| 前提検査 | **代替＋欠落** | generic は request hash、compute hostname、scheduler 終端・会計照合を持つ。一方、A-5:179–238 の入力・HEAD・command 検査、261–406 の allocation・boot・reservation 証跡は同等には残らない。関門判定式は同じでも実行 identity の証拠は薄くなる。 |
| Python 選定 | **代替** | A-5:199–208 は選んだ実体を直接使う。generic は3.10を検査するが任意 argv は別実行。上記 argv は子も3.10に明示する。 |
| env 消去 | **代替** | A-5:221–231 の unset に対し、generic は allowlist だけを残す。必要値を `/usr/bin/env` で再供給する。 |
| scratch tree 準備 | **欠落** | A-5:449–483 は superproject と CCBench を隔離する。P1 は投入元を patch するため、brief の不変条件に抵触する。 |
| 依存 build | **代替** | A-5:524–568 の pinned-clean source 検査と静的 build を、既存 prefix 参照へ置換。依存 binary の同一性は示せない。 |
| `ENV_TAG` 検査 | **代替** | A-5:570–577 の明示検査に対し、CLI の site resolver、required contract、calibration、attestation が働く。単に env を名乗る経路ではない。 |
| output root 作成 | **代替** | A-5:240–255 は未作成 root を0700で作る。P1 は `layout.py:248–251,323–367,412–447` で検査後、226–230行の `makedirs` で必要 directory を作る。新規性・mode0700の保証は同じではない。 |
| TMPDIR | **代替** | A-5:257–258 は job 固有0700 directory。P1 は `/scr` 直下で tempfile の一意名を使う。関門式は同じだが、一括保存・後追い調査の単位は異なる。 |
| bench lock | **代替** | A-5:259 は job 固有、P1 は既定共有 lock。`pipeline.py:1386–1407` の競合検知は双方に残る。どちらも scheduler の排他 allocation を証明するものではない。 |
| sweep 起動 | **代替** | A-5:581–583 は screening 無指定の8 genome。P1 は `main` 経由で baseline と fixed=2 の2 genome。対象の意図的な限定である。 |
| finalize | **欠落** | A-5:607–608,641–653 は8 genome 全 commit・abortゼロを要求するため流用不可。親が本 wave の WAL・rc・stdout を判定する。A-5 完了証明とは呼ばない。 |

P3 は「`compiler_input_dependency_prefix_roots` だけの変更」ではない。

1. `external/ccbench/CMakeLists.txt:33–34,71–75` が gflags/glog を探索して link する。prefix の違いは header・library の選択に効く。
2. `buildcache.py:2629–2632` の ambient prefix は、2681–2685行から `_v2_identity` へ入り、`1330` の `dependency_prefix` として **build digest・cache directory** を変える。
3. ambient 経路では configure 引数に prefix を明示せず、環境を継承する。`buildcache.py:2841–2854,3799–3807`。
4. `compiler_input_dependency_prefix_roots` は `source_snapshot_sha256` と `allow_external_compiler_inputs` が揃う場合だけ非空になる。対象 pipeline はそれらを渡しておらず、descriptor なし経路を通るため、**今回その field に2 rootが記録されるとの前提自体を支持できない**。`pipeline.py:1950–1963,2010`、`buildcache.py:3292–3297,2633–2636`。

同版の依存であっても、A-5 と同じ build bytes・性能条件とは断定しない。関門の生死確認という主張には使えるが、A-5 との性能比較には使わない。

## 緑 record の定義 (P2)

**P2 は、今回の実行に帰属する新規 baseline attempt を特定する条件で支持する。** 関門 arm record の直接保存とは区別する。

採用する間接証拠は次の組である。

- 新規 official root の `campaign.lock` が今回の workload・screening設定・契約を示す。
- baseline の `build-start.payload.genome` が `BACK_OFF=0, BACKOFF_FIXED=-1` を含む。
- 同じ variant・`build_attempt_id` の `bench-done` と、それより後の `commit` がある。
- dispatch が会計照合を完了し、`result.stage=child`、`child_rc=0`、`outcome.kind=child` を記録する。
- stdout の campaign ID、評価結果、終了表示が WAL と対応する。

| 抜け道候補 | 検査結果 |
|---|---|
| `evaluate_candidate` の early return | `screening_driver.py:592–597` は `not force` の terminal・非retryable状態だけ skip。baseline は `backoff_sweep.py:321–337` で `force=True`。 |
| `force=True` が関門を飛ばす | 飛ばさない。force が効くのは上記 skip 条件だけ。関門呼出しは609–617行、`evaluate` はその後の639–642行。 |
| WAL replay が過去 baseline を緑に見せる | `prepare_screening_campaign` は計測前の baseline bench 件数を保存し、計測後に増加と後続 commit を要求する。`screening_driver.py:489–498`。親も同一 attempt を照合する。 |
| WAL recovery が緑を追加する | `ident.py:472–507` は修復・中断 attempt 回復を行うが、baseline 測定の代用ではない。前記の新規 bench 条件は残る。 |
| baseline の request が空 | 空になるのは `genome.flags ∩ DEFINE_SPECS` が空の場合。`screening_driver.py:93–123`。baseline は `backoff_sweep.py:257,409` で `BACKOFF_FIXED=-1` を保持し、spec は `condition_meaning_gate.py:74–77` にあるため空にはならない。 |
| stock 比較なしで通る | default=-1 は `screening_driver.py:51–52`、stock判定は115行。275–282行で別 stock checkout を渡す。supply 側も inert を独立に判定し、stock 不在なら赤にする。`condition_meaning_gate.py:2551–2563`。 |
| build cache hit が関門を飛ばす | 関門は pipeline/build 呼出しより前なので飛ばさない。 |
| 関門拒否後に candidate abort だけ残して続行する | 関門は `try` の外。`screening_driver.py:609–618`。拒否は process を停止する。 |

`bench-done` の writer は `pipeline.py:1516`、`commit` は2571–2575行。`evaluate` は verification 完了後に bench と commit へ進む。`pipeline.py:2705–2720`。

**緑の範囲には重要な限定がある。** screening baseline へ渡す declaration は `fixed_declarations.get(-1)` であり、生成される mapping は非負値だけなので `None` になる。`backoff_sweep.py:88–131,325–327`。したがって screening baseline の meaning 腕は、現コードでは `unestablished / meaning-witness-undeclared` である。`condition_meaning_gate.py:3335–3341`。

family admission は supply が緑かつ meaning が緑または unestablished なら通る。`condition_meaning_gate.py:4098–4108`。P2 が示すのは **baseline stock supply の緑と family admission** であり、「両腕とも緑」ではない。

実装差分ゼロの追加証拠については、**P1 の既存出力に関門実行を直接記録するものは無い**。

- 関門戻り値は `screening_driver.py:609–617` で破棄される。
- stdout の `built`・`verify`・`bench` は後続段の証拠で、関門固有の開始終了時刻ではない。`pipeline.py:2082,2131–2135,1517`。
- `IZANAGI_S4_EVIDENCE_ROOT` の読取は `p3_s4_loop.py:460`。対象経路では効かない。
- dispatch の request hash・hostname・interpreter・child rc は実行帰属を補強するが、関門 record や production 全体の hash を保存するものではない。`dispatch_compute.py:1689–1697,4142–4146`。

また、rc=0 は `screen-slower-than-floor` による候補棄却を許す。`backoff_sweep.py:535–547`。終了表示の「全 genome 計測成功」を「2 genome とも certified commit」と読み替えない。

## 段別の赤の分類表

実際の順序は、**登録 calibration 照合 → driver 関門 → strict attestation → between-run floor → baseline 関門 → build → correctness → bench**。baseline は verify-first、候補は通常 bench-first である。

| 順 | 段 | 赤の識別子・保存場所 | 根拠 |
|---|---|---|---|
| 1 | dispatch infra | rc=16。`submission-disabled`、`orphan-hold`、`queue-wait-timeout`、`overall-timeout`、`result/log/accounting-grace-expired`、`receipt-persist-failed` 等。receipt の outcome と stderr を保存。 | `dispatch_compute.py:43–64,3483–3501,3992–4008,4112–4164` |
| 2 | interpreter・launcher | result の `stage=interpreter/hostname/cwd/bootstrap/child-launch`、child_rc=16。CLI 自身の import/argparse 失敗は traceback または rc=2 と区別する。 | `dispatch_compute.py:874–907,1563–1564,1678–1697`、`backoff_sweep.py:511–524` |
| 3 | 単独性 | `RuntimeError: 競合する ccbench ベンチが稼働中...` と PID。probe 自体の失敗は別例外として記録。WAL 前なので WAL 不在は正常な結果。 | `p2_2.py:291–310`、`backoff_sweep.py:396` |
| 4 | site・contract・登録 calibration | site 許可集合外、authorization 不一致、calibration hash/schema/動作点不一致の `RuntimeError`。 | `p2_2.py:144–176,220–253,313–345` |
| 5 | driver 前処理・patch | pin/dirty tree/`git apply`/stock checkout の `RuntimeError`、TMPDIR の `OSError`。関門未到達として記録。 | `patchharness.py:186–211,255–263,362–369` |
| 6 | driver prepare | `MasstreeFetchContentError`、stage=`configure` または `target`。本文に `masstree FetchContent ... 失敗` と下位エラー。gate の赤 record とは区別する。 | `buildcache.py:2093–2104`、`backoff_sweep.py:444–451` |
| 7 | driver gate | `RuntimeError: condition gate rejected the driver before build/measurement: ...`。macro・status/reason を保存。 | `backoff_sweep.py:218–227` |
| 8 | strict attestation | `ExecutionGuardError: strict attestation probe failed: ...`、`attestation comparisons failed: ...`、receipt再検算失敗。 | `backoff_sweep.py:317–319`、`execution_guard.py:617–623`、`screening_driver.py:339–347` |
| 9 | between-run floor・campaign identity | `ValueError`：JSON不読・schema不一致・非canonical genome・一致数が一意でない・CV不正。output root不正、`IdentityMismatch`、WAL framing/repair失敗もこの位置で分ける。 | `screening_driver.py:371–415,473–487`、`layout.py:323–367`、`ident.py:575–610` |
| 10 | baseline screening prepare | driver prepare と同じ例外型。ただし traceback が `screening_driver._run_condition_gate_for_genome` を通る。candidate-abort の捕捉外。 | `screening_driver.py:197–210,609–618` |
| 11 | baseline screening gate | `ConditionMeaningGateError`、code=`screening-build-route-mismatch` または `condition-family-rejected`。本文に `BACKOFF_FIXED:supply-effectuation=red/<reason>` 等。 | `screening_driver.py:154–158,240–249` |
| 12 | baseline build | WAL `abort.reason=build-error`、`error` に configure/compile/link/toolchain の詳細。その他捕捉例外は `eval-exception: <型>: <本文>`。 | `pipeline.py:2024–2059`、`screening_driver.py:645–660` |
| 13 | baseline correctness | WAL `trace-timeout`、`trace-run-nonzero-exit`、`trace-empty`、`trace-no-abort-counts`、`trace-no-commit-witness`、`trace-batch-commits-unattributed`、`trace-parse-error`、または verifier verdict。 | `pipeline.py:525–665` |
| 14 | baseline bench | WAL `bench-probe-error`、`bench-competing-tenant`、`bench-no-throughput`、`bench-cv-undefined`。rep失敗詳細は `rep_notes`。 | `pipeline.py:1393–1407,1438–1473` |
| 15 | baseline 完了確認 | `ValueError: baseline を同一campaign内で新規実測できなかった`、`最新実測がCOMMITされていない`、median/abort率/時刻不正。先行 WAL abort が根因で、この例外は出口の確認失敗。 | `screening_driver.py:489–508` |
| 16 | 候補単独性・screening gate | 再度の単独性検査と、候補 `BACKOFF_FIXED=2` の prepare/gate。識別子は上記と同じ。baseline WAL があってもここで process 非ゼロになりうる。 | `backoff_sweep.py:360–378` |
| 17 | 候補 build・screening bench | build/bench の赤は同上。`screen-slower-than-floor` は仕様上の未認証棄却で、infra赤・関門赤ではない。 | `pipeline.py:2350–2386` |
| 18 | 候補 correctness・終了 | 棄却されなかった候補は correctness を通す。予期しない abort は最終 rc=1。`stale-baseline` はscreening無効化であり、それ自体は赤ではない。 | `pipeline.py:2326–2345,2388–2390`、`backoff_sweep.py:535–547` |

関門の下位 reason には `configure-failed/configure-timeout`、`preprocess-failed/preprocess-timeout`、`stock-tree-unavailable`、`stock-inert-mismatch` 等がある。`condition_meaning_gate.py:1714,2266–2270,2555–2558,2703`。下位 process が rc=0 でも stderr を出すと赤になる経路もある。`1581–1622`。

driver/screening の拒否本文から消える arm detail は復元可能と書かない。ネットワーク起因かどうかは、保存された traceback・stderr が支持する場合にだけ付記する。

## 所要と walltime

**01:30:00 は通常成功時の予算として妥当。ただし上限保証ではなく、P5 の回数と timeout 解釈は修正が必要。**

| 段 | 回数・見積り |
|---|---|
| 起動・単独性・calibration・attestation | 数秒から数分の予算。今回未測定。 |
| FetchContent prepare | driver 1回＋baseline 1回＋候補1回の**計3回**。20.2秒の先例を単純外挿すれば約61秒。取得条件が違うので保証値ではない。 |
| driver gate | 2 request。configure/preprocess/meaningを含め1–3分程度を仮置き。 |
| screening gate | baseline・候補に各1 request。合計1–4分程度を仮置き。 |
| 完全 build | 各 genome の trace/perf 別 build、**計4 build**。1 build を1–5分と置けば4–20分。既存prefixでのlinkは未実測。 |
| baseline correctness | legacy は200 records・4 threads・extime=1・1 rep。trace実行と検証を合わせ数秒から数分。 |
| throughput | 1,000,000 records・48 threads・extime=3・5 reps。時間窓だけなら1 round 15秒、2 genomeで30秒。初期化・終了処理は別。 |
| 再測定・settle | 最大3 roundsなので時間窓合計は最大90秒。baseline の settle は1回最大20秒、再測定時にも発生しうる。 |
| 候補 correctness | screening棄却なら実施しない。進んだ場合はlegacy検証。 |

定数は `p2_2.py:54–57`、correctness は `pipeline.py:150–152`、3 rounds は2594行、settle は `calibrator/runner.py:271–290`。

20.2秒は供給 insight の末尾が引用する **D1666 の単一観測**であり、今回の測定値ではない。全体は通常 **10–30分程度**を事前予算とし、90分には余裕があると予測する。

ただし、prepare は1回につき configure/target 各900秒、3回で最大90分分の個別 timeout を持つ。`buildcache.py:2093–2103`。関門の120秒は family 全体でなく **各 subprocess** の timeout。`condition_meaning_gate.py:1581–1603`。通常 build の `timeout_s` は既定 `None`。`buildcache.py:3232`。したがって「関門各2分＋build各5分以内」とは保証できない。

待ち方は、**dispatcher 1本を終端まで保持する**。別 watcher や同条件の再投入は増やさない。

- queue待ち：3600秒。
- 初期期限：`submitted_at + 5400 + 3600`。`dispatch_compute.py:3932–3935`。
- **最初の正常な RUN 観測時に** `run_observed_at + 5400 + 3600` へ再設定。3977–3987行。
- queue最大待ちを含め、監視段は概ね最大3時間30分。その後に既定60秒の成果物収集猶予等がある。4021–4024行、70行。
- `overall-grace` は PBS walltime を延長しない。compute 実行の外側上限は90分のまま。

## 成果物の写し方

以下で `W` は現在の worktree、`O` は argv の official root、`N` は dispatcher が生成した nonce、`C` は実際の campaign ID とする。`C` は結果から取得し、事前に歴史 campaign ID を流用しない。

| 原本 | 導出・扱い |
|---|---|
| `W/output/pegasus-dispatch/N/request.json` | root は `dispatch_compute.py:3401–3404`、nonceとファイル名は3506–3537行。env値は今回 `args` の `/usr/bin/env` 引数内に入る。 |
| 同 directory の `result.json` | `dispatch_compute.py:1536,1689–1704`。child rc、hostname、interpreter、request hashを保存。 |
| 同 directory の `receipt.json` | `dispatch_compute.py:3317–3325`。fallback は `W/output/pegasus-dispatch/receipt-fallback-N.json`、3327行。 |
| `izdw-<N先頭10文字>.o<reqid>` と `.e<reqid>` | job名は828–831行。探索候補は1713–1733行で `dispatch.sh` stem、数値ID・server付きIDにも対応。**receipt の `scheduler_logs.*.path` が指す実ファイルを写す。** |
| 同 directory の `dispatch.sh`、`interpreter_probe.py` | 生成時の実行 envelope として保存。3527–3557行。 |
| `O/campaigns/C/runs/wal.jsonl` | `layout.py:248–251,203–208`。baselineだけの抜粋に加え、可能ならこの最小campaignの全文を保存する。 |
| `O/campaigns/C/campaign.lock` | `layout.py:195–196`。identityと契約authorityの生成は `ident.py:583–602`。 |
| execution receipt | **この CLI に永続化先は無い。** `execution_guard.py:625–638` はdictを返し、`backoff_sweep.py:350–358` はsummaryに保持するが、`main:532–547` は出力しない。存在しない `execution-receipt.json` を成果物一覧に捏造しない。 |
| campaign の排他 `.flock` | `campaign.lock` と別物。`layout.py:61–67` に一般経路はあるが、この screening経路で作成を確認できない。必須成果物には数えない。 |

複写先は `output/insights/2026-09-17/t2228-screening-gate-liveness/evidence/` とする。

- JSON・JSONL・README はそれぞれ `.json`・`.jsonl`・`.md` でよい。
- stdout/stderr は `job.stdout.txt`・`job.stderr.txt`。
- 実行体の写しは `dispatch.sh.txt`・`interpreter_probe.py.txt` とする。
- production 4 file、すなわち `backoff_sweep.py`・`screening_driver.py`・`condition_meaning_gate.py`・`buildcache.py` の実測時 sha256 を記録する。dispatcher も不変条件の対象なので別項目で記録する。
- 原本path・byte数・sha256と、抜粋した場合の範囲をREADMEに残す。dispatch receipt にあるログは末尾だけの場合があるため、原本stdout/stderrの代用にしない。`dispatch_compute.py:1761–1780`。

`.py/.sh/.patch/.diff` 等は配置先が insight でも実装面に該当する。正本は [check_ai_provenance.py:75](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-liveness/tools/check_ai_provenance.py:75)。末尾 `.txt` にするのは実行用追加ではない証拠の写しとして保存するためである。

## README の骨格

| 見出し | 記す事実 |
|---|---|
| `## 要点` | CLIからbaseline stock supply/family admissionへ到達したか。新規baseline bench/commitの有無。失敗なら最初に止まった段と識別子。実装差分ゼロ。 |
| `## 実行 identity` | exact argv、環境値、実行tree、HEAD、CCBench pin、production sha256、request ID、nonce、hostname、interpreter、official root、campaign ID、取得できた時刻。P1から変えた事項。 |
| `## 段別結果` | 上の分類表に沿った到達／通過／拒否／未到達。baselineと候補を分け、variant・attempt ID・WAL stage・reason・rcを掲載する。 |
| `## 緑の意味の限定` | arm recordは未保存。WALとcall graphによる間接証拠。baseline meaningはunestablished。rc=0でも候補screening棄却を許す。adaptiveの実行時動作や全点familyを証明しない。 |
| `## scope 外の所見` | 実際に観測したprefix/link問題、保存されないexecution receipt、投入元patchとの衝突等。修正・横展開は実施していないこと。 |
| `## 既知限界` | 1 workload・2 genome・1走。A-5との差、依存binaryの非同一性、単独性観測の範囲、関門と計測buildのconfig.h非束縛、消えた一時証拠、未到達段。予測と実測を分離する。 |

赤でも同じREADMEを作り、未実行の下流段を「赤」や「緑」に埋めない。

## 事前予測

**以下は予測であり、今回の実測結果ではない。**

実行treeの不変条件を解決し、proxy・prefix・計算ノードの前提が成立すれば、**baseline stock supply が緑となり、family admissionを通過する可能性が高い**。

根拠は、前回の screening 赤が準備済み FetchContent base の未供給に対応し、現経路では必ず非Noneのmanifestを渡して prepare と base供給を発火させることである。`backoff_sweep.py:415–417,330,476`、`screening_driver.py:197–214`。

予測が外れる主な位置は次のとおり。

- **driver prepareより前**：単独性、site/登録calibration、pin/dirty tree、`/scr`へのアクセス。
- **driverまたはscreening prepare**：proxy・FetchContent・gflags/glog探索・masstree target。
- **screening gate**：preprocess、stock比較、compiler stderr等。D1784はこれらの緑を保証していない。
- **baseline build**：既存prefixでの完全link。configure/preprocess成功だけではここを保証できない。
- **correctness・bench**：legacy検証、競合検知、測定不能。これらが赤なら、関門を通っていてもP2の完全な証拠組は得られない。
- **候補段**：baseline commit後でもprepare/gate/build等でprocess非ゼロとなりうる。候補の `screen-slower-than-floor` は正常なscreening結果である。

screening baseline の meaning 腕については、**緑ではなくunestablishedになる**とコードから予測する。driver段のmeaning腕と混同しない。

## 総括

- **P1：要修正。** 正規CLIには到達するが、投入元CCBenchへの一時patchがbriefの書込み不変条件に抵触する。
- **P2：限定付き支持。** 新規baseline attemptのWAL＋会計照合済みrc=0＋stdoutは、stock supply緑・family admissionの間接証拠になる。
- **P3：影響範囲を訂正。** prefixは依存解決とbuild identityも変える。今回の経路でprefix roots fieldが非空になるとは限らない。
- **P4：条件付き採用。** `/scr`を既存一時領域として使えるが、A-5のjob固有directoryとは異なる。
- **P5：通常予算として採用。** 90分は妥当な見積りだが、個別timeoutから導ける完走上限ではない。
- **execution receiptの複写は現CLIでは不可能。** 未保存という限界を記録する。

指定6資料はすべて読了した。補助探索で指定した `orchestrator/campaign/identity.py` は存在せず、実ファイル `ident.py` を確認した。静的読取りと書込みを伴わないstdlib環境検査のみを行い、pytest・実測・編集・commit・branch操作・job投入は行っていない。