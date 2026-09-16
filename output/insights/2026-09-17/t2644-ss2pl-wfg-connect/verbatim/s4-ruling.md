# 段 4 裁定 — [T-2644] (親、2026-09-17 01:05 JST)

入力: `s1-brief.md`、`artifacts/dev-wave-t2644-ss2pl-wfg-connect/s2-plan.md`、同 `s3-a.md` (正しさ境界)、同 `s3-b.md` (整合・実効性)。
裁定 inbox (`/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/`) を再走査: T-2644 / ss2pl / wfg に触れる更新なし (最新 2026-09-08)。

## 1. 所見の裁定 (real / refuted、採否、scope)

| # | 出所 | 所見 | 裁定 | 採否 |
|---|---|---|---|---|
| P-1 | plan 前提 | 排他 lock (`KIND=0`) で計器は read 操作を `read` と出すが、Python `_edge_is_incompatible` は read/read を両立と判定する → 実閉路が拒否されうる | **real** (親が patch:1567,1572,1593,2002,2013 と :2302-2311、:523-527 で検算) | 採用。JSON の mode は実 lock mode: `IMPL=1 && KIND=0` では全箇所 `"write"` (study lock は `writer_` に格納する排他 1 種のみ)、それ以外は既存 read/write。Python 側は変更しない |
| P-2 | plan 前提 | P6「必ず 3 枚」は誤り。途中で閉路が変われば 4 枚以上 | real | brief を訂正。P6 の意味は「連続 3 回一致で file を書いて watchdog が止まる」 |
| P-3 | plan 前提 | アンカー `runner.hh:98-100` は誤り。sleep→quit→join は `:296-299` | real | brief を訂正 |
| A-1 | レンズ A | `held_locks` は同一 registry コピーの写しで独立観測源ではない。I2 の「実証枝」は「同一 snapshot の保持一覧との照合枝」 | real | 採用 (表現)。`compatible:false` は残し、検証器の非両立再導出も残す |
| A-2 | レンズ A | P3 (閉路 tick だけ emit) で、閉路なし tick を挟んで同一 signature が再出現する経路は phase1 (`IMPL=1 KIND=0 DLR=0`) では構成できない — 取得は実 lock 成功後に registry へ、解放は registry 削除後に実 unlock、DLR0 は blocker が居る間 loop | real (論証) | P3 を **phase1 限定の論証付きで維持**。tick 検査は新設しない。insight に論証を書き、「検証器単体が任意の欠番入力を拒否する」とは主張しない |
| A-3 | レンズ A | counter は `begin()` の `register_worker` (patch:1512) で写された attempt 開始時の値。条件 3 は計器構造上冗長 (attempt と同時に変わる)。値は閉路中の thread が更新箇所へ進めないので正しい | real | **写しのまま維持** (本題の接続だけ)。insight と受領証の説明に「条件 3 は attempt 不変と冗長であり、独立な進行監視ではない」と明記。実更新時の同期は scope 外 |
| A-4 | レンズ A | 条件 4: 3 枚後の閉路解消と別原因 timeout は区別できないが、D791 逐語は「kill まで持続」を要求しない | real | P6 維持。説明は「連続 3 snapshot の閉路証拠と、同一走行の hard timeout」。kill までの持続観測へは強化しない |
| A-5 | レンズ A | 規律 1 は plan の配置で保持される見込みだが、変更後の不在性は未実測 | real | **probe は arm `S` (WFG=0) も `build_target` で 1 本 build し、production の `_wfg_absence_evidence` を新 patch で取り直す** (walltime を 01:00:00 に) |
| A-6 | レンズ A | plan の fixture は実出力と逐語一致しない (軸行は `ADD_ANALYSIS`/`BACK_OFF`/DLR marker を省略、workload 行は実物がタブ)。実 stdout を fixture へ写す手順が無い | real | 採用。段 6 で計算ノード 1 走の実 stdout から軸行・workload 行・event 3 行を fixture へ逐語で写して差し替える。閉路未観測なら「受理正例の実走 fixture は未取得」と記録し合成値で代用したと報告しない。**そのため runner は trial scratch へ stdout / stderr 本文を保全する** (B-10 と同じ是正) |
| A-7 | レンズ A | 既存 3 test の名前「actual_holder」は実 holder 観測の証拠ではない | real | 既存 test は変更しない。insight に一言 |
| B-1 | レンズ B | generic dispatch は clean env (`_CLEAN_CHILD_ENV_KEYS` :349-360) で `PBS_JOBID` を落とす。plan の probe は PBS 検査で停止する | **real** (親が dispatch_compute.py:349-360, 1442-1452 で検算) | 採用。probe は **PBS env を要求しない**。`pbs_jobid` は best-effort: `PBS_JOBID` env → `<repo-root>/output/pegasus-dispatch/*/compute-visible.json` のうち hostname 一致で最新のもの → `"unknown"`。hostname が `bnode` で始まらなければ clone/build/run へ進まず rc=2 (login で誤って走らせない)。実 job ID は dispatcher receipt から親が対応づける |
| B-3 | レンズ B | `clone_network_free` の第 1 引数は `Path(canonical["path"])` | real | 実装子へ明記 |
| B-5/B-6 | レンズ B | 64 KiB 超は pipe deadlock の理由にならない (communicate が drain)。flush 済み行の回収と完全な 3 行の生成は別条件 | real (説明) | insight へ。主張の射程を限定 |
| B-7 | レンズ B | scratch は wave job dir 下 (submission dir は read-only)。`python3.10 -B` 必須 | real | 採用。`--scratch-root /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2644-ss2pl-wfg-connect/scratch-<attempt>` |
| B-8 | レンズ B | 所要は未測定。condition gate は 4 軸 × requested/control の configure。40 分は静的に保証できない | real | walltime 01:00:00。probe は段階ごとの所要を JSON に残す |
| B-9 | レンズ B | probe は下位 production 経路を測るが study 全体は測らない。差の表 | real | insight に表として残す (F29) |
| B-10 | レンズ B | `_run_phase_trial` は stdout/stderr 本文を返さない | real | 採用。runner は trial dir に `stdout.txt` / `stderr.txt` を書き、受領証に path を残す (sha256 は既存 field と一致するはず) |
| B-11 | レンズ B | 受領証の型確定 (`Path`/bytes/例外 object を入れない)、probe は `validate_phase_matrix` を呼ばない、phase2 は依然 `acquisition_paths` 不在で ContractError | real | 採用。phase2 は scope 外のまま事実として記録 |
| B-12 | レンズ B | 変異帰属の訂正: counter drift は**正例**が赤 (負例 test は赤にならない)、node と edge の `request_mode` を同時に旧名化すると `None == None` で受理されうる (検証器の既存限界) | real | 変異 matrix を訂正 (§4)。検証器の限界は **scope 外** (本題の接続だけ)、carry 候補として起票 |
| B-13 | レンズ B | `_extract_snapshots` の top-level 枝削除が変異表から抜けている | real | 追加 (§4) |
| B-14 | レンズ B | 実装子へ渡す確定値の表 | real | §2 に採用 |

refuted: なし。scope 外で裁定パッケージへ返すもの: 検証器の `request_mode` 欠落受理 (既存限界、強化は別 wave)、phase2 counter 契約、`ss2pl_lock_study.sh` の `_source_path` 破損。

## 2. plan v2 — 実装子への確定値

### 2.1 計器 (patch、`wfg.cc` / `ycsb_ss2pl.cc`)

| 項目 | 確定値 |
|---|---|
| schema | `"ss2pl-wfg/v2"` (file も stdout も同じ) |
| stdout event | `{"schema":"ss2pl-wfg/v2","event":"wfg_snapshot","tick":<uint64>,"cycle_found":true,"conflict_count":<n>,"no_wait_failure_count":<n>,"nodes":[...],"edges":[...]}` を **compact 1 行 + `\n`**。watchdog の loop ごとに tick を加算 (閉路なし tick も加算、最初の tick = 1)。閉路が非空の tick で出力。出力位置は `consecutive >= 3` の判定より前 |
| node | `{"thread_id":<u32>,"attempt":<u64>,"wait_lock_id":"0x<hex>","request_mode":"<mode>","commit_count":<u64>,"abort_count":<u64>,"held_locks":[{"lock_id":"0x<hex>","mode":"<mode>"},...]}`。node は選択閉路の thread のみ。`held_locks` は同一 snapshot 内のその worker の held 全件 |
| edge | `{"waiter_thread_id":<u32>,"holder_thread_id":<u32>,"lock_id":"0x<hex>","request_mode":"<mode>","holder_mode":"<mode>","compatible":false}`。閉路 node 間の実 holder 辺のみ。holder の該当 lock が held に無ければ架空の write holder を出さず、その辺を出さない (現行 fallback を廃止) |
| mode | `IMPL=1 && KIND=0` では全箇所 `"write"`、それ以外は既存 `"read"`/`"write"`。取得 counter (`record_acquire`) の分類は変えない |
| lock id | 全箇所 `"0x"` + `std::hex`、直後に `std::dec` へ戻す |
| durable file | 最後に emit した**同じ文字列**を `durable_replace` (再 snapshot しない)。`terminal_json` は `{"schema":"ss2pl-wfg/v2","event":"wfg_terminal","tick":null,"cycle_found":false,<既存 counter>,"nodes":[],"edges":[]}` compact。terminal は stdout に出さない |
| 出力の原子性 | `cout_mutex` (external/ccbench/include/debug.hh) を取り、`flockfile(stdout)`〜`funlockfile(stdout)` の中で 1 回の `fwrite` + `fflush`。短い write / flush 失敗は既存 `ERR`。`RegistryMutex` は snapshot コピー時だけ保持 |
| 起動時軸行 | `ycsb_ss2pl.cc` の `chkArg();` 直後、`displayWorkloadParameter()` より前に `#if SS2PL_WFG_DIAG` / `ShowOptParameters();` / `#endif`。`util.cc` に literal を足さない。bomb / tpcc は変えない |
| watchdog 停止 | 現行どおり連続 3 回一致で file を書いて return (P6) |
| hunk | patch の hunk header 行数を正しく更新し、`git apply --check` が現行 pin で rc=0 |

### 2.2 runner (`_run_phase_trial` のみ)

| 項目 | 確定値 |
|---|---|
| trial dir | `tempfile.mkdtemp(dir=binary.parent, prefix=f"ss2pl-wfg-{phase}-{point}-t{trial}-")` (自動削除しない、絶対 path) |
| argv | `[binary, *_workload_argv(...), f"-ss2pl_wfg_output={trial_dir}/final.json"]`。`_workload_argv` と `_run_performance_once` は変更しない |
| 本文保全 | `_run_process` の戻り後、`trial_dir/stdout.txt` と `stderr.txt` に `stdout` / `stderr` (str) を UTF-8 で書く |
| 受領証 | `"wfg_output": {"path": str, "status": "present"|"missing"|"invalid_json"|"read_error", "sha256": str|None, "json": object|None, "error": str|None}` と `"stdout_path": str`, `"stderr_path": str`。sha256 は file の生 bytes。`invalid_json` は UTF-8 decode 失敗を含む。`Path` / bytes / 例外 object を入れない |
| 受理集合 | 既存の `_admit_output` / `_extract_snapshots` / `validate_deadlock_evidence` / `timed_out` を変えない。file は受理条件にも代用証拠にもしない |

### 2.3 test (`orchestrator/tests/test_ss2pl_lock_study.py`、`:1477` の後)

(a) `test_wfg_stdout_fixture_accepts_actual_holders` — 計器の新 serializer を逐語で模した固定文字列 (起動時軸行 = **現物の `ShowOptParameters()` の全形式** `#ShowOptParameters(): ADD_ANALYSIS 0: BACK_OFF 1: DLR0 : SS2PL_LOCK_IMPL 1: SS2PL_LOCK_KIND 0: SS2PL_DLR 0: SS2PL_WFG_DIAG 1: MASSTREE_USE 1: KEY_SIZE 8: KEY_SORT 0: VAL_SIZE 8` の形を `util.cc:56-84` から組む、workload 行はタブ区切り `#FLAGS_ycsb_tuple_num:\t100` 等 5 行、event 3 行)。実 `_json_events` → `_extract_snapshots` → `validate_deadlock_evidence(timed_out=True)` で受理、`snapshot_indexes == [0,1,2]`、event に `holder_holds_lock` 不在。同入力で `timed_out=False` は None。**段 6 で実 stdout 由来へ差し替える前提** (実装子は「合成」と docstring に書く)。
(b) `test_wfg_stdout_legacy_fields_are_rejected` — parametrize: `wait_lock_id→waiting_lock_id` (node)、`waiter_thread_id/holder_thread_id→waiter/holder` (edge)。各単独で None。**`request_mode` 単独の旧名化は含めない** (両側欠落は検証器が通す既存限界、B-12)。
(c) `test_wfg_stdout_missing_held_locks_is_rejected` — `held_locks` 削除、holder の lock_id 不一致、holder の mode 不一致 の 3 case で None。
(d) `test_wfg_startup_axes_without_terminal_output` — 起動時軸行 + workload 行だけの stdout で `parse_runtime_axes` が phase1 の 4 軸を返し、既存 `_admission_fixture(..., arm="phase1")` 相当で `_admit_output(require_metrics=False, require_thread_commits=False)` が通る。
(e) `test_phase_trial_passes_unique_wfg_output_and_collects_file` — 実 `_run_phase_trial` を呼び、`_run_process` だけを差し替え (argv から `-ss2pl_wfg_output=` を必須抽出し、その path に fixture の final JSON を書き、合成 stdout を返す)。2 回呼んで path が異なる、flag が 1 個、受領証の `wfg_output.path/sha256/json` と `stdout_path` の内容一致、file 不在 case でも stdout 証拠は受理。性能経路 `_run_performance_once` の argv に同 flag が無いことも実関数で観測。
(f) `test_wfg_exclusive_mode_write_is_accepted_and_read_read_is_rejected` — mode 正規化の契約: 同じ閉路で全 mode `write` は受理、`read`/`read` は None。

既存 `:1432-1477` の 3 test と他の期待値は変えない。

### 2.4 probe (`tools/t2644_wfg_probe.py`、実装子 B。commit しない — 親が実行後 job dir へ退避)

- 起動: `python3.10 -B tools/t2644_wfg_probe.py --repo-root <W> --patch <W>/patches/ss2pl-lock-protocol-study.patch --scratch-root <job dir>/scratch-<n> --gflags-prefix /work/SFC/tanab/ss2pl-study-deps/gflags-install --glog-prefix /work/SFC/tanab/ss2pl-study-deps/glog-install --thirdparty-root <job dir>/thirdparty-src --clocks-per-us 2100 --jobs 48 --output <job dir>/probe-result-<n>.json [--absence-arm S] [--selftest]`
- runner は `importlib.util.spec_from_file_location` で `<repo-root>/tools/pegasus/run_ss2pl_lock_study.py` を import (runner 自身が ROOT を sys.path に入れる)。
- `--selftest`: `--repo-root` だけで走る。依存 path の resolve・hostname 検査・書込みより前に分岐。合成 stdout の正例 (受理) と `held_locks` 削除の負例 (None) を実 parser / 検証器へ通し、rc 0/1。
- 実走: hostname が `bnode` で始まらなければ rc=2 で何もしない。`pbs_jobid` は B-1 の best-effort。`validate_required_commands()`、`_validate_thirdparty(root, policy)`、`verify_canonical_submodule(repo_root)` を実行し記録。UUID attempt dir 下に `condition-gate-stock`、`ccbench`、`builds`。`clone_network_free(Path(canonical["path"]), stock)` と同 `(…, clone)`、`_apply_patch(clone, patch, reverse=False)`、`validate_abort_counter_ownership(clone)`。`PreprocessCache()` 1 個、`patched_source_state_sha256 = _sha256_bytes(f"patched\0{head}\0{patch_sha256}".encode())`。
- `--absence-arm S` (既定 on): `build_target(clone, stock, build_root, build_id="S", arm="S", backoff=1, ...)` を先に 1 本 build し、record の `wfg_absence` を結果に残す (規律 1 の実測)。
- `build_target(..., build_id="phase1", arm="phase1", backoff=1, target="ycsb_ss2pl.exe", preprocess_cache=..., source_state_sha256=...)`。
- `_run_phase_trial(phase="phase1", build=record, workload={**WORKLOAD_DEFAULT, "ycsb_tuple_num": 100, "ycsb_zipf_skew": 0}, trial=0, point="high-contention", clocks_per_us=2100, occasion={...})` を 1 回。`validate_phase_matrix` は呼ばない。
- 出力 JSON: 入力 sha、canonical、thirdparty、段階ごとの所要秒、build record (S / phase1)、trial 結果 (`accepted_cycle`、`wfg_snapshots`、`timed_out`、`termination`、`wfg_output`、`stdout_path`)、例外時は type/message/stage/scratch path。**inert witness は省く** (D790 の証明はこの probe の射程外と明記)。
- 実走後、親が `stdout.txt` / `final.json` / probe 本体を job dir へ複写し sha256 / bytes を記録する。

### 2.5 docs (親、段 7)

`docs/cc-diagnostics.md`「必要な入力」「既知の不足」を接続後の事実へ (過去の観測報告は否定しない、phase2・launcher の不足は残す)。`patches/README.md:12` の行を更新。insight `output/insights/2026-09-17/t2644-ss2pl-wfg-connect/README.md` に: 6 件の断絶とその修正、4 条件それぞれの判定材料の出所 (A-1〜A-4 の限定つき)、probe と production の差 (B-9)、実データ (受領証の複写)、規律 1 の実測 (arm S の absence evidence)、fixture 差し替えの記録、scope 外の 3 件。decisions fragment 1 件 (伝達 = stdout event 一次 + 同 schema の durable file、mode = 実 lock mode、tick 検査は足さない、条件 3 の冗長性)。

## 3. 段 5 の分割と契約

- 実装子 A (author、workspace-write、worktree `.codex/worktrees/t2644-impl-a`、所有: `patches/ss2pl-lock-protocol-study.patch`、`tools/pegasus/run_ss2pl_lock_study.py`、`orchestrator/tests/test_ss2pl_lock_study.py`)。
- 実装子 B (author、workspace-write、worktree `.codex/worktrees/t2644-impl-b`、所有: `tools/t2644_wfg_probe.py`)。B は A の変更 (受領証 field 名) に依存するが、runner の関数 signature は変わらないので並列でよい。B は `wfg_output` / `stdout_path` を「あれば記録」の形で読む。
- 両者とも commit しない、docs を書かない、既存 test の期待値を変えない、pytest は走らせられない (import + 直接呼出しで fixture 成立と反実仮想を確かめる)。

## 4. 変異事前登録 (実装後に anchor を確定して spec 化、DW-M01)

実装面 = patch (C++、login で compile 不可) + runner + test。**C++ 側の変異は Python test で KILLED にできない** (fixture は固定文字列)。C++ の変異は登録せず、計算ノード 1 走の実出力と fixture の逐語一致 (段 6 の差し替え) で契約感度を示す。登録するのは Python 側:

| id | 対象 | 変異 | 期待 |
|---|---|---|---|
| m0 | test fixture | 等価変異 (fixture 生成の空白のみ) | SURVIVED (対照) |
| m1 | runner `_run_phase_trial` | `-ss2pl_wfg_output=` の付与を削除 | KILLED: (e) |
| m2 | runner `_run_phase_trial` | trial dir を固定 path にする (mkdtemp → 固定名) | KILLED: (e) の path 非一致 assertion |
| m3 | runner `_run_phase_trial` | `wfg_output.sha256` / `json` を None 固定にする | KILLED: (e) |
| m4 | runner `_run_phase_trial` | `stdout.txt` の書込みを削除 | KILLED: (e) の stdout_path 内容一致 |
| m5 | runner `_extract_snapshots` | top-level 枝 (`nodes`+`edges`+`event` に `wfg`) を削除し nested-only にする | KILLED: (a)(b)(c)(e)(f) の受理側 |
| m6 | test fixture (a) | 2 枚目の `commit_count` を +1 | KILLED: (a) の受理 assertion (正例側) |
| m7 | test fixture (a) | `held_locks` を全 node から削除 | KILLED: (a) |
| m8 | test fixture (a) | edge の `compatible` を削除 | KILLED: (a) |
| m9 | test fixture (d) | 起動時軸行を削除 | KILLED: (d) |
| m10 | runner `_run_performance_once` | 性能 argv に `-ss2pl_wfg_output=x` を追加 | KILLED: (e) の性能 flag 不在 assertion |

期待 node は実装後の実 test 名で確定し、probe 走 (全件 SURVIVED 登録) で観測 node を集めてから本走する。単一理由性は実装後の anchor で確認 (F820)。

## 5. brief の訂正

- P6: 「event は 3 枚出て終わる」→「連続 3 回一致で file を書いて watchdog が止まる。閉路が途中で変われば 4 枚以上出る」。
- I2: 「実証枝」→「同一 snapshot の保持一覧との照合枝」。独立性の範囲: 検証器は辺の端点・lock id・mode・非両立性を再計算できるが、registry の正しさ (取得後登録・登録削除後解放の順序) は信頼境界。
- I4: 「同 schema」→「既存 3 test は boolean 証拠 (`holder_holds_lock`) の合成、新 test は保持一覧の合成。期待値は変えずに共存」。
- アンカー: `runner.hh:98-100` → `:296-299`。patch は 84,697 bytes。
- 追加: 6 件目の断絶 (mode)。
