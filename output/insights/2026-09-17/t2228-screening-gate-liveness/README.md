# [T-2228] screening 関門の生死確認 — 正規 CLI から最小 screening を計算ノードで 1 走し、baseline の stock 腕が関門を通過して新規 record (bench-done → commit) を得た

日付: 2026-09-17 / wave: `dev-wave-t2228-screening-liveness` / branch `worktree-dev-wave-t2228-screening-liveness`
基点 main: `1042a1bc95057fa03117d504cfa2b0fafaae60d0` (着手直前の local main、fresh worktree)。
authority: none / default_effect: no-state-change。**実装差分 (repo) はゼロ** — 成果物は本 insight と spool fragment だけ。

## 要点

1. **現行の正規入口 (CLI `backoff_sweep.main`) から `--screening --screening-fixed-us 2` の最小 screening を
   計算ノード (bnode010、request `2326.nqsv`) で 1 走し、baseline (`BACK_OFF=0` / `BACKOFF_FIXED=-1`、stock 比較あり) が
   screening 関門を通過して新規の WAL record (`build_start → build_done → verify_done → bench_done → commit`) を得た。**
   CLI は rc=0、dispatch は会計照合済み `child_rc=0`、`=== backoff sweep 完了 ===`、`committed=2 aborted=0`。
   D1784 (2026-09-08) が保留していた「screening 関門が緑になった」を、**本 README の §2 の限定つきで初めて名乗る。**
2. **緑は間接証拠である。** production 経路は関門の arm record を作って捨てる (`screening_driver.evaluate_candidate` が
   戻り値を捨て、赤は try/except の外で例外として process を止める。D1912 が `backoff_sweep.py` を名指し)。
   「関門が走って通した」は、実行コードの制御フロー (baseline は request 非空・`force=True`・関門呼び出しは build/bench の前・
   拒否は process 停止) と、その後にしか書けない新規 baseline record からの推論で支える。設計判断は
   本 wave の decisions fragment `screening-liveness-green-record` ({{D:screening-liveness-green-record}} 相当、
   land 時採番、`docs/decisions.md` 参照)。
3. **baseline の meaning 腕は `unestablished / meaning-witness-undeclared` である (コードから確定)。**
   `_backoff_fixed_declarations` は非負値にしか declaration を作らず、`fixed_declarations.get(-1)` は `None`。
   緑と名乗るのは **supply 腕 (stock 比較) の緑 + family admission** であって「両腕とも緑」ではない。
   成功 supply reason (`stock-inert-preprocess-identical` / `-root-location-only`) は WAL から識別できない。
4. **投入形は generic dispatch + job dir の最小 launcher + 正規 CLI。** A-5 job body は `--screening` を渡さず finalize が
   8 genome 全 commit を要求し submitter が 2 workload 固定なので、実装差分なしでは最小 screening を走らせられない。
   launcher (bash 121 行、Codex author、敵対レビュー 2 本 + fix 1 + 焦点再レビュー) は repo へ実行体として置かず
   (D1786)、`.txt` の写しを `launcher/` に残す。設計判断は本 wave の decisions fragment `screening-liveness-entry-form` ({{D:screening-liveness-entry-form}} 相当、land 時採番、`docs/decisions.md` 参照)。
5. **attempt a (`2319.nqsv`) は親の入力誤りで screening 関門に到達する前に止まった** (§3)。official root を job dir 配下に
   置いたが `/work/1/SFC/tanab/dev-wave-jobs/.git` (空 dir) が `.git` 祖先で `layout` が拒否。driver 段の関門は通過していた。
   本題未到達の親入力誤りとして 1 回だけ再投入した (attempt b)。「本題の 1 走」は attempt b である。

## 実行 identity (attempt b = 正)

| 項目 | 値 |
|---|---|
| dispatch | `python3 -B tools/pegasus/dispatch_compute.py --task generic --walltime 01:30:00 --queue-wait-timeout 3600 --overall-grace 3600 -- bash <job dir>/run_screening_liveness.sh <official root> 1042a1bc9… 511c9538…` (`launcher/run-dispatch.sh.txt`) |
| request / nonce | `2326.nqsv` (`0:2326.nqsv`)、nonce `034c245a448cb7ad63d6fdad53c84987`、request sha256 `8c8944a62a127582e1a3670e1ffa99abf5f3319897b56336ecf66cf2054d93d0` |
| 投入 / 開始 / 終了 | 01:39:31 投入 → 01:43:26 launcher 開始 → 01:43:29 CLI 起動 → 01:48:53 CLI 終了 (rc=0) → 01:49:07 dispatcher 終了 (rc=0)。CLI 5 分 24 秒、全体 9 分 36 秒 |
| 計算ノード / uid / interpreter | `bnode010`、uid 31609、`/usr/bin/python3.10` (`-I -B -u`) |
| 実行木 | wave worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-liveness`、HEAD `1042a1bc9…`、CCBench `511c9538e4e8efa54b45cda62e72389ed3b706ec` (launcher が起動前に一致と tracked-clean を検査) |
| CLI argv | `/usr/bin/python3.10 -I -B -u orchestrator/campaign/backoff_sweep.py write-heavy --screening --screening-fixed-us 2` |
| env (launcher が供給、A-5 と同値) | `PATH=/usr/bin:/bin:/opt/nec/nqsv/bin:/system/tool/bin`、`TMPDIR=/scr/t2228-screening-<mktemp>`、`IZANAGI_BENCH_LOCK=$TMPDIR/bench.lock`、`IZANAGI_OFFICIAL_OUTPUT_ROOT=/work/1/SFC/tanab/izanagi-job-evidence/t2228/attempt-20260917b-official`、`CMAKE_PREFIX_PATH=/work/SFC/tanab/ss2pl-study-deps/gflags-install:/work/SFC/tanab/ss2pl-study-deps/glog-install`、`http_proxy`/`https_proxy=http://10.120.96.1:8080` |
| toolchain (WAL `build_done`) | cc `/usr/bin/x86_64-linux-gnu-gcc-11`、cxx `/usr/bin/x86_64-linux-gnu-g++-11` (Ubuntu 11.4.0)、cmake `/usr/bin/cmake` |
| campaign | `backoff-sweep-silo-write-heavy-sweep-5e637735`、`campaign.lock` sha256 `a02f446d11772d415a8b9f32cc551a78ce0225ffa00056ea18fb131896191632` (8110 bytes)、WAL sha256 `74d653891e6d3fbd23f90974b091e2e2d353b5021fd68e97b0cb7d54ea7bc7fb` (14970 bytes、10 record) |
| campaign.lock の identity_preimage | `workload=write-heavy`、`screening_fixed_us=2`、`sweep_us=[2,5,10,25,50,100]`、`records=1000000`、`threads=48`、`measurement_env=pegasus`、`ccbench_commit=511c953`、screening policy `{baseline_ref: 84319b1127a6, floor: 0.009536…, k: 1.5, high_abort_factor: 2.0}`、`contract_loader_blob_sha256s` に `buildcache.py: 404a36fa…` (実測時の production sha と一致) |
| launcher | `run_screening_liveness.sh` sha256 `009a4d8a21c5d1c8694c40343b1079f286aa1bc6101cfa28f9f0ac95a48b888f` (121 行; v1 `66f28ca8…` は attempt 前の fix で置換) |
| production sha256 | `evidence/production-sha256.txt` (`backoff_sweep.py 5d55cbbb…`、`screening_driver.py 34160fe3…`、`condition_meaning_gate.py 9fef1f9c…`、`buildcache.py 404a36fa…`、`patchharness.py 0ce1fe71…`、`layout.py d76b29d0…`、`p2_2.py 9b30a7ad…`、`dispatch_compute.py 3b4a5c53…`)。**production は 1 byte も変えていない** |
| 原本 | official root `/work/1/SFC/tanab/izanagi-job-evidence/t2228/attempt-20260917b-official/` (WAL・campaign.lock はここ。repo へは複製しない)、dispatch request dir は wave worktree `output/pegasus-dispatch/034c245a44…/` と job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2228-screening-liveness/attempt-b/` |

## 1. 段別結果 (attempt b)

| 順 | 段 | 結果 | 根拠 |
|---|---|---|---|
| 1 | dispatch infra | 通過 (`stage=child`、`child_rc=0`、receipt `outcome={kind: child, rc: 0, accounting_verified: true}`) | `evidence/attempt-b/result.json`、`receipt.json` |
| 2 | launcher 前提検査 / python | 通過 (HEAD・pin 一致、両 tree tracked-clean、official root 未存在、`/scr` 書込可、`PY=/usr/bin/python3.10`) | `job.stdout.txt` 1-15 行 |
| 3 | 単独性 (割当ノード上、CLI 起動前) | 通過。loadavg `0.99 12.64 11.08`、`nproc 48`、上位 process は dispatcher の python3.10 (2.3%) と kernel thread (<1%)、`pgrep -af 'ycsb_.*\.exe'` 0 件、他 uid の非 kernel process に `%CPU>=50` なし | `job.stdout.txt` 16-1266 行 |
| 4 | env 供給 | 通過 (8 command 実在、値は上表) | `job.stdout.txt` 1267-1283 行 |
| 5 | CLI 起動 → 単独性 (production `_assert_single_tenant`) → site/契約/較正 → driver 段 prepare + 関門 → attestation → between-run floor → **baseline の screening prepare + 関門** | 通過 (例外なし。次段の `build_start` 01:44:37 は CLI 起動 01:43:29 の 68 秒後) | 制御フロー (`backoff_sweep.run_workload` 396-467 行、`_run_screened_workload` 287-339 行、`screening_driver.evaluate_candidate` 609-617 行) + WAL |
| 6 | baseline build (trace / perf) | `build_start` 01:44:37 → `build_done` 01:45:56 (79 秒)。`trace_cached=false`、`perf_cached=false`、perf bin sha256 `ccedcc07c1466a0a0f175c96740c6752dce0314ce65ddfcc30c0e6699f733c8b`、`toolchain_record_sha256 61f75635…`、`build_admission_receipt_sha256 767b6ad7…`。configure argv は `-DCCBENCH_BACKOFF_FIXED=-1 -DCCBENCH_BACK_OFF=0 -DCCBENCH_NO_WAIT_LOCKING_IN_VALIDATION=1 -DCCBENCH_NO_WAIT_OF_TICTOC=0 -DCCBENCH_WAL=0 -DCCBENCH_TRACE=0` | WAL 1-2 行目 |
| 7 | baseline correctness (legacy) | `verify_done` 01:46:12: `serializable (630017 commits, 246639 aborts, 0 anomalies)` | WAL 3 行目、stdout 1290 行 |
| 8 | baseline bench | `bench_done` 01:46:29: **median 2,388,009 tps、CV 2.48%** | WAL 4 行目 |
| 9 | baseline commit | `commit` 01:46:29 (attempt `0bf4e7528b71d9858ea6c57a77f38303`、variant `84319b1127a6`) | WAL 5 行目 |
| 10 | 候補 (`BACKOFF_FIXED=2`) の screening prepare + 関門 | 通過 (baseline commit 01:46:29 → 候補 `build_start` 01:47:03、34 秒) | 制御フロー + WAL |
| 11 | 候補 build / screening bench / correctness / commit | `build_done` 01:48:20、`bench_done` 01:48:37 (**3,406,076 tps、CV 2.73%**、screening 棄却なし)、`verify_done` 01:48:52 (`613962 commits, 221914 aborts, 0 anomalies`)、`commit` 01:48:52 (attempt `f4e1bb26…`、variant `82ea3a7b8618`) | WAL 6-10 行目 |
| 12 | 終了判定 | `=== backoff sweep 完了 ===`、`committed=2 aborted=0`、`全 genome 計測成功`、CLI rc=0 | stdout 1296-1302 行 |
| 13 | 終了後の tree 状態 (launcher) | superproject / CCBench の `status --porcelain --untracked-files=no` 空 (rc=0)、CCBench の `worktree list` は本体 1 件のみ (stock 一時 worktree 撤去済み) | stdout 1303-1319 行 |
| 14 | 終了後の tree 状態 (親、login で再実測) | HEAD `1042a1bc9…`、`status --untracked-files=all` 0 行、CCBench `511c9538…`・0 行、worktree list 本体 1 件、orphan hold なし | 段 7 の実測 |

WAL の抜粋 (原本 `…/runs/wal.jsonl`、field は ts / variant / stage / genome / build_attempt_id / median_tps / cv):

```
1789577077.36 84319b1127a6 build_start  silo|BACKOFF_FIXED=-1,BACK_OFF=0,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0  0bf4e7528b71d9858ea6c57a77f38303
1789577156.22 84319b1127a6 build_done   -  0bf4e752…
1789577172.57 84319b1127a6 verify_done  -  0bf4e752…
1789577189.44 84319b1127a6 bench_done   -  0bf4e752…  median_tps=2388009  cv=0.02480547591262411
1789577189.46 84319b1127a6 commit       -  0bf4e752…  cv=0.02480547591262411
1789577223.35 82ea3a7b8618 build_start  silo|BACKOFF_FIXED=2,BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0  f4e1bb26c0f995c0466f1407a05dc417
1789577300.19 82ea3a7b8618 build_done   -  f4e1bb26…
1789577317.04 82ea3a7b8618 bench_done   -  f4e1bb26…  median_tps=3406076  cv=0.027329902425688203
1789577332.53 82ea3a7b8618 verify_done  -  f4e1bb26…
1789577332.58 82ea3a7b8618 commit       -  f4e1bb26…  cv=0.027329902425688203
```

**「screening 関門が緑になった」と名乗る 6 条件 (decisions fragment `screening-liveness-green-record`) の照合:**
(1) 未使用 official root と request の対応 — root は launcher が未存在を検査してから CLI が作成、request の argv に同 path (✓)。
(2) `campaign.lock` が write-heavy / `screening_fixed_us=2` / pegasus 契約を示す (✓)。
(3) baseline の `build_start.payload.genome` が `BACK_OFF=0, BACKOFF_FIXED=-1` (✓)。
(4) 同じ variant `84319b1127a6`・同じ attempt `0bf4e752…` に新規 `bench_done` と後続 `commit`、`build_done` の toolchain / binary hash / argv あり (✓)。
(5) `result.stage=child`・`child_rc=0`、receipt `outcome.kind=child`・`rc=0`・`accounting_verified=true` (✓)。
(6) stdout の campaign ID・結果と WAL が一致し、production・dispatcher・launcher の sha256 を記録 (✓)。

## 2. 緑の意味の限定 (最も重要)

| 主張してよい | 主張してはいけない |
|---|---|
| 当該環境・当該コード (HEAD `1042a1bc9`、CCBench `511c953`) で、正規 CLI から baseline の stock supply 腕と family admission まで到達し通過した | 両腕とも緑、全 macro の意味が確立した (baseline の meaning は `unestablished`) |
| baseline の新規 measured commit (2,388,009 tps) が得られた | 今回の supply 成功 reason が `root-location-only` だった (WAL からは `identical` と識別できない) |
| stock owner TU の preprocess 比較が現行の判定式を満たしたと**推論**する (arm record は未保存) | 関門の緑を直接記録した |
| 1 workload (write-heavy)・2 genome (baseline + fixed=2)・1 走の経路を観測した | 通常 7 値 family、他 workload、他 driver (`s6_sort_sweep` / `s8a_trigger_sweep` / `backoff_repro` / `s1`) も通る |
| 候補 (fixed=2) も build・screening bench・legacy correctness・commit まで通った | 「fixed=2 が baseline より速い」を性能主張として使う (1 走・screening 規模・既存 prefix の依存 binary。§5) |
| 実測時点の到達性が確認された | 将来 HEAD、別依存環境、A-5 環境との等価性 |
| driver 段の関門 (D1666) も同 job で再び通過した (attempt a/b とも、traceback / WAL の位置から) | adaptive backoff が実行時に動作した |

- 環境供給 (official root・prefix・proxy・TMPDIR・PATH) は関門の判定式・既定値・stock 比較・admission 条件を 1 行も
  変えないが、**到達性を変える**。D1784 の「制御された拡張」を環境も含めた不変性へ読み替えない (規律 2)。
- 本 record は「当時・そのコード・その道具」の事実として残す。現行コードとの差だけで無効にならず、逆に将来コードの
  保証にもならない (規律 7)。
- 前回 (2026-09-07、一次資料 §1) の screening 赤 `BACKOFF_FIXED:supply-effectuation=red/preprocess-failed` は、
  `-DFETCHCONTENT_BASE_DIR` 未供給で owner TU の preprocess が `config.h` 不在で落ちたものである。本走は D1784 の供給
  (`screening_driver.py` 197-214 行) が効いた状態で同じ経路を通り、前段で止まらず build へ進んだ。

## 3. attempt a (`2319.nqsv`、bnode026) — 本題未到達の親入力誤り

- 01:34:55 launcher 開始 → 前提検査・python・単独性 (loadavg `0.16 0.03 0.04`、競合 0、他 uid の busy 0)・env 通過 →
  01:34:58 CLI 起動 → `=== backoff sweep … 2 genome ===` → **01:35:32 `ValueError: official output_root は repository 外でなければならない`**
  (traceback: `run_workload:469` → `_run_screened_workload:339` → `prepare_screening_campaign:484` → `campaign_layout:250` →
  `_validate_external_output_root:352`)。CLI rc=1、dispatch rc=1 (`child_rc=1`)。
- 原因: official root を job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2228-screening-liveness/attempt-20260917a-official`
  に置いたが、`/work/1/SFC/tanab/dev-wave-jobs/.git` (空 directory、2026-08-04 作成) が `.git` 祖先として `_has_git_ancestor`
  に当たった。brief の「job dir に `.git` 祖先が無いことは確認済み」は親が `ls -la | head -5` で切った不十分な実測だった
  (不在の断定を実測せずに書いた型)。段 3 レンズ B の R4 と段 6 レビュー B が「親確認済み」を前提にしていたので、
  レビューでは出なかった。
- 得られた事実: traceback の位置 (`run_workload:469` は `_require_backoff_condition_gate` の後) から、driver 段の
  prepare + 関門は attempt a でも通過している。screening 関門には到達していない。
- 終了後: launcher の出力と親の再実測で両 tree clean、stock 一時 worktree 撤去済み、orphan hold 解放済み。
- 裁定 (段 4 裁定 4 の適用): 本題 = screening 関門であり、そこへ到達する前の親入力誤りは「本題未実行」に当たる。
  official root を前回 probe と同じ `izanagi-job-evidence/t2228/` 配下 (全祖先の `.git` 不在を今度は 1 段ずつ実測) に直して
  **1 回だけ**再投入した。緑が出るまで投げ直す運用ではない。

## 4. 単独性の確認の形と限界

- gen_S は `Exclusive submit = OFF` で専有を保証しない (runbook §1)。依頼の「単独性を確認してから投入」は batch では
  割当前に満たせないので、**同じ job 内で CLI 起動前に割当ノードを観測し、競合があれば計測を開始しない**形にした (launcher §3)。
  拒否述語は (a) `pgrep -af 'ycsb_.*\.exe'` (production の一次ゲート F3 と同じ) が自 PID 以外に 1 件でもある、
  (b) 自 uid 以外・kernel thread (pid/ppid 2) 以外の process に `%CPU >= 50` がある。load average は実測分布が無いので
  拒否条件にせず記録のみ (DW-O13)。
- **generic dispatch の入れ子 userns では他 uid が `65534` に見える** (親が login の `unshare --user --map-root-user` で実測)。
  他ユーザーの job も host root の daemon も同じ 65534 に潰れるため、`root` の名前除外は効かず、拒否は「同居 job の断定」
  ではなく再投入の契機である。通過は「その瞬間の述語を満たした」までで、全実行期間の単独性の証明ではない。
- production の `_assert_single_tenant()` (`p2_2.py:300-310`、competing `ycsb_*.exe`) は CLI 内で baseline・候補の
  各測定点の手前で走り、いずれも通過した。

## 5. A-5 (正規 job body) との差 — 等価ではない

| 段 | A-5 | 本走 | 結果の意味への影響 |
|---|---|---|---|
| 前提検査・予約証跡 | 入力・HEAD・allocation・boot・reservation を照合 | request hash・hostname・会計照合 + launcher の HEAD/pin/clean 検査 | 実行 identity の証拠は A-5 より薄い |
| 依存 (gflags / glog) | hydrate 済み source から job 内で静的 build | 既存 install prefix `/work/SFC/tanab/ss2pl-study-deps/{gflags,glog}-install` (v2.2.2 / v0.5.0 = pin と同版、2026-08-25 作成) | `completion.json` の `preimage.dependency_prefix` に prefix path が入り build identity を変える。**A-5 と同じ依存 binary とは断定しない**。link は本走で成功した |
| 実行木 | scratch の superproject + CCBench worktree | wave worktree を in-place (CLI が `patchharness.applied` で patch → revert、stock checkout を `$TMPDIR` の一時 worktree として登録・撤去) | 終了後に両 tree clean を launcher と親が実測 |
| TMPDIR / bench lock | job 固有 0700 dir / job 固有 lock | `mktemp -d /scr/…` (0700) / 同 dir の lock | 同等 |
| sweep 起動 | 8 genome、screening 無し | 2 genome、`--screening --screening-fixed-us 2` | 意図した限定 |
| finalize | 8 genome 全 commit・abort ゼロを要求 | WAL・rc・stdout を親が判定 | A-5 完了証明とは呼ばない |
| 実行 python | 検査した実体を直接使用 | `/usr/bin/python3.10` (realpath を stdout に記録) | 同等 |

## 6. scope 外の real 所見 (実装していない、裁定パッケージ候補)

1. **関門の arm record は screening 経路で保存されない** (D1912 の名指しどおり)。今回の緑は間接証拠に留まる。
   D1912 が DW-G03 (独立 2 例) で保留した横展開は本 wave では行わない。
2. **execution receipt (attestation) はこの CLI から永続化されない** (`main` が summary を出力しない)。
3. **generic dispatch の clean env は `PBS_JOBID` を子へ渡さない。** launcher の必須入力にしていた親の仕様誤りを段 6 の
   敵対レビュー 2 本が独立に検出し、fix 1 巡を要した。DW-O13 の型 (入力が実環境に存在するかを設計前に確認) の再発。
4. `/work/1/SFC/tanab/dev-wave-jobs/.git` (空 dir) が job dir 配下を official root として使えなくしている (§3)。
   撤去の可否は本 wave では扱わない。
5. 前回 (2026-09-07) probe の driver 段 prepare が proxy 未 export で通った理由は、計算ノードの継承環境の proxy と
   **推定**する (段 3 レンズ A)。本走は proxy を明示供給し、FetchContent (masstree / mimalloc / googletest) の取得に成功した。
6. 段 3 の両レンズが指摘した既知限界 (masstree autotools の CC/CXX 非束縛、関門と計測 build の `config.h` bytes 非束縛、
   `s6_sort_sweep` / `s8a_trigger_sweep` の同型未供給) は D1666 / D1784 の記録どおりで、本 wave では触れていない。

## 7. 開発検査

- 段 2 plan 1 本 (`verbatim/s2-plan.md`)、段 3 敵対相談 2 本 (`s3-lensA.md` = 正規入口・環境等価性、`s3-lensB.md` = 証拠の恒真性・
  規律 2/7)。親の brief の誤り 5 件 (prefix の記録 field、「関門は無条件」、P5 の回数・上限、「sweep 再開できる」、
  「screening が赤のまま」) を両レンズが指摘し、段 4 (`s4-adjudication.md`) で訂正した。
- 段 5 author 1 本 (launcher v1)、段 6 敵対レビュー 2 本 (`s6-reviewA.md` / `s6-reviewB.md`、must-fix 2 件: `PBS_JOBID`、
  userns の root 除外)、fix 1 本 (`s6-fix1.md`)、焦点再レビュー 1 本 (`s6-focus.md`、closed 13 / partial 4 / regressed 0、GO)。
- 親の実測: `unshare --user --map-root-user` 内の `ps` で他 uid が `nobody` に見えること (login)、`.git` 祖先の 1 段ずつの不在、
  終了後の tree 状態 (§1 の 14 行目)。
- 変異 matrix: 実装面 (repo) の差分ゼロにつき免除 (DW-S04)。launcher は repo 外の一回限りの投入 script で、敵対レビューだけを
  守りとする (D1786 の「残る限界」)。
- 受入全走: 記録 commit の後に 1 回 (結果は worklog と land の受領証)。
- codex 子: plan 1・consult 2・author 1・review 2・fix 1・focus 1 の計 8 本、全て `launcher_rc=0`、model は全段
  `gpt-6-astra`、reasoning は plan/consult `xhigh`、他は docs 権威由来。計算ノード job: 2 本 (attempt a 46 秒、attempt b 9 分 36 秒)。

## 既知限界

- 緑は間接証拠 (§2)。arm record・成功 reason・meaning の確立は記録されていない。
- 1 workload・2 genome・1 走。通常 7 値 family と他 workload の admission は未測定。
- 依存 binary は既存 prefix で、A-5 の job 内 build と同一ではない。性能値 (2,388,009 / 3,406,076 tps) は生死確認の副産物で、
  性能主張には使わない (同時刻の対照なし、1 走)。
- 単独性は起動前スナップショットと production の pgrep に限る (§4)。
- launcher は repo 外で単体検査を持たない。守るのは敵対レビュー 2 本 + 焦点再レビューだけ。
- attempt a の失敗は親の入力誤りで、screening 関門の性質ではない (§3)。

## 出所

- brief / plan / 相談 / 裁定 / author / review / fix / focus の逐語: `verbatim/`
- launcher の写し: `launcher/run_screening_liveness.sh.txt` (使用した v2、sha256 `009a4d8a…`)、`run_screening_liveness.v1.sh.txt`
  (レビュー前)、`run-dispatch.sh.txt` (投入 wrapper)
- dispatch の証拠: `evidence/attempt-b/` (request / result / receipt / compute-visible / job stdout・stderr 全文 / dispatch.sh・
  interpreter_probe の `.txt` / 時刻)、`evidence/attempt-a/` (同)
- production の sha256: `evidence/production-sha256.txt`
- WAL・campaign.lock・completion の原本: official root `/work/1/SFC/tanab/izanagi-job-evidence/t2228/attempt-20260917b-official/`
  (repo へ複製しない)。写しは job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2228-screening-liveness/attempt-b/official-root/`。
  build cache (`completion.json`、binaries) は wave worktree `external/ccbench/build-variants/contracts/e576e9cd…/` (追跡外)
