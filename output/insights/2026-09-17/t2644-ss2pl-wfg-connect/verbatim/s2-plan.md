## 前提の検算

指定された必読資料はすべて読めた。以下の行番号は変更前の現物を指す。略記は次のとおり。

- `patch` = [patches/ss2pl-lock-protocol-study.patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2644-ss2pl-wfg-connect/patches/ss2pl-lock-protocol-study.patch)
- `runner` = [tools/pegasus/run_ss2pl_lock_study.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2644-ss2pl-wfg-connect/tools/pegasus/run_ss2pl_lock_study.py)
- `test` = [orchestrator/tests/test_ss2pl_lock_study.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2644-ss2pl-wfg-connect/orchestrator/tests/test_ss2pl_lock_study.py)

**接続方針 P1〜P7 は採用できる。ただし、実際の排他 lock mode と計器の mode 表現の不一致も修正する必要がある。**

検算結果は以下のとおり。

| 項目 | 現物の結果 |
|---|---|
| stdout event 不在 | `patch:2432–2481` は複数行の file 用 JSON。watchdog は durable file しか書かない |
| field 名の断絶 | node は `waiting_lock_id` / `requested_mode`、edge は `waiter` / `holder` / `requested_mode`。検証器との不一致を確認 |
| holder 証拠 | 現 JSON に `held_locks` がない。`runner:2372` の実証枝を通せない |
| 出力先 flag 不在 | `runner:2857` は workload flag だけ。`patch:2196–2198` の必須検査で起動失敗する |
| 軸行の時機 | `external/ccbench/common/runner.hh:299` の worker join 後、`:316` で軸行を出す。hang では到達しない |
| workload 行 | `patch:2654` 付近の `displayWorkloadParameter()` は watchdog 開始前。`external/ccbench/include/ycsb.hh:206–211` が必要な 5 flag を `endl` 付きで出す |
| `_json_events` | `runner:2240–2252` は各行を `strip()` してから `{` を調べる。厳密には「元の行の先頭が `{`」である必要はない |
| 既存 3 test | `test:1404–1477` は `holder_holds_lock:true` を使う合成証拠。期待値は保持するが、今回の実 holder 経路の証明には追加 test が必要 |
| P6 の出力枚数 | 「必ず計 3 枚」ではない。途中で閉路が変われば、最後の連続 3 回一致までに 4 枚以上出る |
| アンカーのずれ | `runner.hh:98–100` は現在 `RunnerOptions` のコメント。sleep→quit→join は `:296–299`。`:316` は正しい |
| file サイズ | patch は 2,733 行・84,697 bytes。指定の「約 105 KB」と異なる。runner は 3,251 行・136,433 bytes、test は 1,481 行 |

追加の意味上の不一致は次の経路で確認した。

- `patch:1567,1572` 等は read 操作について計器へ `SS2PLWfgMode::read` を渡す。
- 一方、study lock の `install_owner()` は `patch:523–527` で `LockKind == 0` の read も `writer_` に格納する。
- C++ の `incompatible()` は `patch:2302–2311` で KIND=0 の全組合せを非両立とする。
- Python の `_edge_is_incompatible()` は `runner:2365–2369` で read/read を両立とする。

したがって、field 名の変更だけでは phase1 の実閉路が read/read 辺を含むと拒否される。**JSON の mode は workload 操作種別ではなく、実際に要求・保持する lock mode と定義する。** study の排他 lock では `"write"` に正規化し、RW lock では元の read/write を保持する。検証器の変更は不要であり、受理条件も緩めない。

この段では file 作成・編集、pytest、build、benchmark、patch 適用は実施していない。

## 計器の stdout event の設計

変更位置は `patch:2432–2481` の `cycle_json()` と、その隣に置く出力 helper、`:2494–2521` の `watchdog_main()` とする。

**受理形は top-level の `event:"wfg_snapshot"` と `nodes` / `edges` を採る。** `wfg_snapshot` key に snapshot をネストする形は使わない。これなら `runner:2347–2355` の第 2 枝がそのまま受理し、`_observed_conflict_count()` も top-level counter を読める。

schema は次を固定する。

```text
schema: "ss2pl-wfg/v2"
event: "wfg_snapshot"
tick: watchdog の全 tick を数える単調増加整数
cycle_found: true
conflict_count: snapshot.conflicts
no_wait_failure_count: snapshot.no_wait_failures
nodes:
  thread_id, attempt, wait_lock_id, request_mode,
  commit_count, abort_count,
  held_locks: [{lock_id, mode}, ...]
edges:
  waiter_thread_id, holder_thread_id, lock_id,
  request_mode, holder_mode, compatible:false
```

具体的な変更手順は以下とする。

1. `patch:2298` の mode 表現 helper を、実 lock mode を返すものへ変更する。`SS2PL_LOCK_IMPL == 1 && SS2PL_LOCK_KIND == 0` のとき `"write"`、それ以外は元の read/write。node の `request_mode`、edge の両 mode、`held_locks[].mode` に同じ helper を使う。acquisition counter の分類は変更しない。
2. `cycle_json()` の node は現在どおり閉路に属する thread だけとする。その各 node について、**同じ snapshot の `worker.held` を全件** `held_locks` に出す。閉路外 thread の node は追加しない。これで出力済みの全 edge の holder が node 内に存在する。
3. lock ID は全箇所で `"0x"` + `std::hex` の同じ表記にする。各 ID の直後に `std::dec` へ戻し、thread ID・counter を誤って 16 進表記にしない。
4. edge は現行同様、閉路 node 間の実 holder 辺だけ出す。`make_edges()` が同じ lock ID と非両立性を確認済みであることを根拠に `compatible:false` を付ける。
5. 現在の `held_mode = write` という検索失敗時の fallback は廃し、同じ snapshot の holder が持つ該当 lock を必ず参照する。見つからない場合に架空の write holder を出してはいけない。
6. JSON 本体は改行を含まない compact 形式で生成し、末尾に `\n` を 1 個だけ付ける。
7. watchdog の loop ごとに tick を増やす。閉路が非空なら、その tick の snapshot をシリアライズして出力する。出力位置は `consecutive >= 3` の durable 書込み判定より前とする。
8. 最後の tick では、stdout に出したものと同じ文字列を durable file に渡す。snapshot を取り直さない。内部の連続一致判定と watchdog 停止条件は P6 に従い維持する。

stdout helper は、既存の `cout_mutex` を取得し、さらに `flockfile(stdout)` から `funlockfile(stdout)` までに **1 回の `fwrite` と `fflush`** を行う形を推奨する。短い write と flush エラーを確認し、失敗時は既存の `ERR` 経路に入る。`RegistryMutex` は snapshot コピー時だけ保持し、stdout や fsync 中には保持しない。

原子性の論証は、`PIPE_BUF` ではなく対象プロセスの writer の排他に置く。

- `external/ccbench/include/debug.hh:7–10` の worker 向け `dump()` は `cout_mutex` 下で行全体と `endl` を出す。event も同じ mutex を使えば、その行の途中へ JSON を挿入しない。
- 読んだ YCSB/SS2PL の通常 worker 経路には直接の stdout 出力がなく、debug macro は stderr に出す。backoff の `cout` 群もコメント内である。
- 起動時の `cout` は watchdog 開始前に完了する。
- 同期した C/C++ 標準 stream を維持し、stdout の FILE lock を event 全体で保持する。今回 `sync_with_stdio(false)` は導入しない。
- 4 KiB 超の行では OS の pipe write 原子性は保証されない。単一 `fwrite` も単一 syscall を意味しない。しかし、同じ stdout へ書く対象 writer を排他すれば、内部 write が分割されても他の worker 出力は割り込まない。

この保証を、無関係な process が同じ fd へ直接 `write()` する場合まで一般化しない。

## file 出力の扱い

`patch:2432–2492` の schema は **`ss2pl-wfg/v2` に上げる**。field rename と `held_locks` 追加に加え、mode の意味を明確化するため、v1 のままにはしない。過去の v1 成果物は変更しない。

- cycle file は stdout event と**同じ serializer・同じ文字列**を使う。
- `terminal_json()` は `schema:"ss2pl-wfg/v2"`、`event:"wfg_terminal"`、`cycle_found:false`、既存 counter、`nodes:[]`、`edges:[]` とする。tick を共通 field にする場合は terminal では `null` とし、未観測の snapshot tick を作らない。
- 共通する schema/counter の出力は小さい helper にまとめてもよい。cycle の node/edge serializer を stdout 用と file 用に二重実装しない。
- terminal は今回 stdout に新規配線しない。phase2 counter 接続まで scope を広げない。

`patch:2414–2431` の temporary file→fsync→rename→directory fsync は維持する。file は最終 snapshot の副次成果物であり、これを 3 枚に複製して検証器へ入れることは禁止する。

## 起動時の軸行

`patch:2653` の `chkArg();` 直後、`displayWorkloadParameter()` より前に次を追加する。

```cpp
#if SS2PL_WFG_DIAG
  ShowOptParameters();
#endif
```

`util.cc` には新しい軸行 literal を追加しない。既存 `ShowOptParameters()` を再利用する。

- `patch:2216–2229` の関数は 4 軸を同じ行に出し、末尾が `endl` なので起動時に flush される。
- `runner:2173–2185` は最初に全 4 軸が揃った行を返す。正常終了時に同じ軸行が再度出ても既存 parser で受理できる。
- `WFG_AXIS_LITERAL` の検査は実行時の行数ではなく、preprocessed source 中の literal の位置・個数、および binary string を調べる。既存関数を呼ぶだけなら literal は増えない。
- WFG=0 では追加呼出しが前処理で消えるため、性能 arm の実行時出力も増えない。実際の不在性は後段の既存検査で確認する。

`bomb_ss2pl.cc` と `tpcc_ss2pl.cc` には今回は追加しない。runner が実行する target は YCSB であり、共通 `chkArg()` に置くと他 workload へ変更が広がる。両 workload の hang 時軸行不足は残ると記録する。

## runner の変更

変更対象は `runner:2846–2903` の `_run_phase_trial()`。`_workload_argv()` と `_run_performance_once()` は変更しない。

出力先には、binary の親 directory 下で作る**永続する一意な trial directory**を使う。

```text
<binary-parent>/ss2pl-wfg-<phase>-<point>-t<trial>-<mkdtemp-suffix>/final.json
```

`tempfile.mkdtemp(dir=binary.parent, prefix=...)` を使い、`TemporaryDirectory` による自動削除はしない。path は絶対化する。同じ phase/point/trial の再実行でも directory が異なるため、古い final JSON や `.tmp` と衝突しない。

argv は次の構成にする。

```text
binary
_workload_argv(... threads=48, extime=10)
-ss2pl_wfg_output=<absolute-final-path>
```

`_run_process()` は cwd を変更しないので絶対 path が適切である。`start_new_session=True` は process group の終了処理に使われ、file path の解釈には影響しない。

終了後、`_admit_output()` より先に final file を収集し、受領証へ次を追加する。

```text
wfg_output:
  path
  status: present | missing | invalid_json | read_error
  sha256: file の生 bytes の SHA-256、読めなければ null
  json: decode できた最終 object、なければ null
  error: decode/read 失敗時の説明、通常は null
```

SHA は再シリアライズした JSON ではなく、実際の file bytes から計算する。file は scratch に保全する。`missing` は SIGTERM 前に durable 書込みへ到達しなかった可能性を表し、閉路証拠の有無と同一視しない。

stdout による既存の admission、snapshot 抽出、`timed_out` 判定を維持する。file を追加の受理条件にも代替証拠にもせず、収集失敗は副次成果物の状態として記録する。既存 admission が例外になる場合はそのまま失敗し、probe が scratch path と例外を残す。

性能 arm は `runner:2740` の独立した argv 組立を使うため、この flag を渡さない。phase2 は WFG=1 なので同じ出力先 flag を渡してよい。

受領証の `argv` は現行どおり `argv[1:]` を記録する。既存 admission は argv の完全一致や path を比較せず、cache・compile definitions・runtime axes・workload flags・binary SHA を検証する。一意な出力 path は受理集合を変えない。

## test 案

追加先は `test:1477` の後、`if __name__ == "__main__"` より前とする。既存 `:1432–1477` の 3 test は変更しない。

(a) **新 serializer が出す形式を逐語で模した固定文字列**

以下を、新しい compact serializer の field 順・空白規約に合わせた fixture とする。既存 `_persistent_cycle_snapshots()` から JSON を生成せず、独立した固定文字列にする。実 C++ 出力との一致は計算ノード probe で確認する。

```text
#ShowOptParameters(): SS2PL_LOCK_IMPL 1: SS2PL_LOCK_KIND 0: SS2PL_DLR 0: SS2PL_WFG_DIAG 1
#FLAGS_ycsb_max_ope: 10
#FLAGS_ycsb_rmw: 0
#FLAGS_ycsb_rratio: 50
#FLAGS_ycsb_tuple_num: 100
#FLAGS_ycsb_zipf_skew: 0
{"schema":"ss2pl-wfg/v2","event":"wfg_snapshot","tick":1,"cycle_found":true,"conflict_count":2,"no_wait_failure_count":0,"nodes":[{"thread_id":0,"attempt":7,"wait_lock_id":"0x20","request_mode":"write","commit_count":10,"abort_count":2,"held_locks":[{"lock_id":"0x10","mode":"write"}]},{"thread_id":1,"attempt":9,"wait_lock_id":"0x10","request_mode":"write","commit_count":20,"abort_count":3,"held_locks":[{"lock_id":"0x20","mode":"write"}]}],"edges":[{"waiter_thread_id":0,"holder_thread_id":1,"lock_id":"0x20","request_mode":"write","holder_mode":"write","compatible":false},{"waiter_thread_id":1,"holder_thread_id":0,"lock_id":"0x10","request_mode":"write","holder_mode":"write","compatible":false}]}
{"schema":"ss2pl-wfg/v2","event":"wfg_snapshot","tick":2,"cycle_found":true,"conflict_count":2,"no_wait_failure_count":0,"nodes":[{"thread_id":0,"attempt":7,"wait_lock_id":"0x20","request_mode":"write","commit_count":10,"abort_count":2,"held_locks":[{"lock_id":"0x10","mode":"write"}]},{"thread_id":1,"attempt":9,"wait_lock_id":"0x10","request_mode":"write","commit_count":20,"abort_count":3,"held_locks":[{"lock_id":"0x20","mode":"write"}]}],"edges":[{"waiter_thread_id":0,"holder_thread_id":1,"lock_id":"0x20","request_mode":"write","holder_mode":"write","compatible":false},{"waiter_thread_id":1,"holder_thread_id":0,"lock_id":"0x10","request_mode":"write","holder_mode":"write","compatible":false}]}
{"schema":"ss2pl-wfg/v2","event":"wfg_snapshot","tick":3,"cycle_found":true,"conflict_count":2,"no_wait_failure_count":0,"nodes":[{"thread_id":0,"attempt":7,"wait_lock_id":"0x20","request_mode":"write","commit_count":10,"abort_count":2,"held_locks":[{"lock_id":"0x10","mode":"write"}]},{"thread_id":1,"attempt":9,"wait_lock_id":"0x10","request_mode":"write","commit_count":20,"abort_count":3,"held_locks":[{"lock_id":"0x20","mode":"write"}]}],"edges":[{"waiter_thread_id":0,"holder_thread_id":1,"lock_id":"0x20","request_mode":"write","holder_mode":"write","compatible":false},{"waiter_thread_id":1,"holder_thread_id":0,"lock_id":"0x10","request_mode":"write","holder_mode":"write","compatible":false}]}
```

test 名候補は `test_wfg_stdout_fixture_accepts_actual_holders`。実関数の `_json_events()`→`_extract_snapshots()`→`validate_deadlock_evidence(timed_out=True)` を通し、event/snapshot が各 3 件、indexes が `[0,1,2]`、`holder_holds_lock` 不在を確認する。同じ入力で `timed_out=False` は拒否されることも確認する。

(b) `test_wfg_stdout_legacy_fields_are_rejected`

同じ値を保ち、node の `wait_lock_id` / `request_mode` を旧名へ、edge の端点と要求 mode も旧名へ変更する。event wrapper は残して抽出自体は成功させ、検証器が `None` を返すことを確認する。個別 rename も parameterize すれば拒否理由を局所化できる。

(c) `test_wfg_stdout_missing_held_locks_is_rejected`

全 node の `held_locks` を削除し、`holder_holds_lock` を追加せず、拒否を確認する。別 case として holder lock ID 不一致・holder mode 不一致も確認する。

(d) `test_wfg_startup_axes_without_terminal_output`

起動時の軸行だけで `parse_runtime_axes()` が phase1 の 4 軸を返すことを確認する。さらに上記 workload 行を添え、`_admission_fixture(..., arm="phase1")` の cache/compile/binary 証拠とともに、実 `_admit_output(require_metrics=False)` を通す。終端 metrics や終端軸行を要求していないことを確認する。

(e) `test_phase_trial_passes_unique_wfg_output_and_collects_file`

実 `_run_phase_trial()` を呼ぶ。`_run_process` だけを外部実行境界として差し替え、渡された argv から出力 path を取り出して fixture の最終 JSON を書き、合成 stdout を返す。

- argv 組立、directory 作成、file 収集、SHA 計算、`_admit_output`、抽出、検証は実物を通す。
- 同じ phase/point/trial で 2 回呼び、path が異なることを確認する。
- flag は 1 個、絶対 path、受領証の path/JSON/SHA が一致することを確認する。
- file 不在 case でも stdout の閉路証拠は独立して受理されることを確認する。
- 性能経路にも argv を観測する test を置き、同 flag がないことを確認する。

DW-O14 に対して、この差し替えで検証するのは **argv 配線と受領証収集**であり、subprocess の timeout/flush 機構ではないと明記する。`_admit_output` や検証器を成功固定へ差し替えない。既存 `test:1101` の admission stub を新 test に流用しない。

追加で、mode 表現の説明を裏付ける fixture case として RW の read/read は拒否、排他 mode に正規化した write/write は受理を確認する。ただし C++ helper の実行検証は probe に残る。

## 1 走 probe の設計

probe は job directory の `t2644_wfg_probe.py` として保全し、repo へ commit しない。計器・runner・test の実装者が使う小さい production 呼出し driver とする。

起動は素の path を推奨する。

```text
python3.10 -B /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2644-ss2pl-wfg-connect/t2644_wfg_probe.py \
  --repo-root <repo-root> \
  --patch <repo-root>/patches/ss2pl-lock-protocol-study.patch \
  --scratch-root <scratch-root> \
  --gflags-prefix /work/SFC/tanab/ss2pl-study-deps/gflags-install \
  --glog-prefix /work/SFC/tanab/ss2pl-study-deps/glog-install \
  --thirdparty-root /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2644-ss2pl-wfg-connect/thirdparty-src \
  --clocks-per-us 2100 --jobs 48 --output <job-dir>/probe-result.json
```

`--repo-root` から runner の絶対 path を組み立て、`importlib.util.spec_from_file_location()` で import する。runner 自身が `runner:30–33` で正しい ROOT を `sys.path` に入れる。`-m tools.t2644_wfg_probe` は repo 内に一時配置する場合には使えるが、job directory に保全する案では不要である。

実走処理は次の順とする。

1. 引数 path を解決し、既存 `run()` と同じ clocks/jobs 制約を確認する。
2. 既存の PBS/bnode 制約を実走 entry でも確認する。`runner:3039–3042` の検査は `run()` にしかなく、下位関数を import して呼ぶだけでは発動しないためである。
3. `validate_required_commands()`、policy を使う `_validate_thirdparty()`、`verify_canonical_submodule()` を実行して結果を記録する。
4. UUID を含む新しい attempt directory を scratch 下に作る。`ccbench`、`condition-gate-stock`、`builds` をその下に置く。
5. `clone_network_free(canonical, stock_clone)` と `clone_network_free(canonical, patched_clone)` を各 1 回呼ぶ。stock clone には patch を当てない。
6. `_apply_patch(patched_clone, patch, reverse=False)` を呼ぶ。内部の `git apply --check` を省略しない。
7. `validate_abort_counter_ownership(patched_clone)` を実行し、その結果を記録する。snapshot counter を扱う probe なので、軽い既存検査を省く理由はない。
8. `PreprocessCache()` を 1 個作る。source state SHA は production と同じく次から作る。

```python
patched_source_state_sha256 = driver._sha256_bytes(
    f"patched\0{canonical['head']}\0{patch_sha256}".encode()
)
```

9. 実 `build_target()` を次の条件で呼ぶ。

```text
source=patched_clone
stock_source=stock_clone
build_root=attempt_root/builds
build_id="phase1"
arm="phase1"
backoff=1
target="ycsb_ss2pl.exe"
gflags_prefix / glog_prefix / thirdparty_root / jobs = 引数
preprocess_cache=上記 object
source_state_sha256=上記 SHA
```

`runner:1980–2037` の condition gate は 4 軸すべてを処理する。これを stub せず、`build_target()` 自身に実行させる。stock clone を patched clone で代用しない。

10. 実 `_run_phase_trial()` を 1 回呼ぶ。

```text
phase="phase1"
point="high-contention"
trial=0
workload={**WORKLOAD_DEFAULT, ycsb_tuple_num=100, ycsb_zipf_skew=0}
clocks_per_us=2100
occasion={occasion_id: 一意 ID, pbs_jobid: 実値, node: 実値}
```

11. result dict、build receipt、入力 SHA、canonical 情報、preprocess cache summary、所要時間を `--output` に保存する。例外時も例外種別・段階・scratch path を残す。raw durable file と probe 本体も job directory に複写し、probe の bytes/SHA を保全する。

`run()` 前段から省いてよいものは、性能 arm 全体の build、sweep/control matrix、plot、性能比較向け isolation 集計、inert witness の収集である。**この単発 probe では inert witness を省けるが、I1/D790 を証明したことにはならない。** wave 全体の既存受入では性能 build 不在性・inert witness を別途確認する。

省いてはいけないものは、source/patch/thirdparty の束縛、独立 stock clone、4 軸 condition gate、build admission、production `_run_phase_trial()` とその `_admit_output()`、実 timeout 記録である。

`--selftest` は次のように設計する。

- `--repo-root` だけで実行可能とし、scratch・依存 prefix・PBS を要求しない。
- clone/build/benchmark/file 書込みの前に分岐する。
- 上記合成 stdout の正例と、`held_locks` を削除した負例を実 parser/検証器へ通す。
- 成否を stdout と exit code で返す。`python3.10 -B <probe-path> --repo-root ... --selftest` を親が login で実行できる。
- selftest の成功は実 C++ 接続や PBS 実走の成功を意味しない。

時間は未測定である。目安は clone ×2、4 軸 gate、configure、target 1 本の build、60 秒の走行、収集で数分〜数十分。40 分枠を使う案は妥当だが、共有 filesystem と condition gate の時間に依存する。`build_target()` の build timeout 自体が 1,800 秒なので、40 分以内を静的に保証はできない。

## 変異 matrix の事前登録候補

node 名は上記の追加 test 名を使用する。ここで「fixture 変異」と「C++ 実装変異」を分けて登録する必要がある。

| 変異対象 | 変異 | 期待する KILLED node／観測 |
|---|---|---|
| stdout fixture | `compatible` を削除 | `test_wfg_stdout_fixture_accepts_actual_holders` の受理 assertion |
| stdout fixture | `held_locks` を削除 | 同正例。負例 test も拒否が保たれることを確認 |
| stdout fixture | `wait_lock_id` を旧名に戻す | 同正例 |
| stdout fixture | edge 端点を `waiter` / `holder` に戻す | 同正例 |
| stdout fixture | holder の lock ID/mode を不一致にする | 同正例 |
| stdout fixture | 2 枚目の commit/abort counter を増やす | counter drift の追加負例 |
| stdout fixture | 排他保持を論理 read/read として出す | mode 正規化の正例 |
| runner | 出力先 flag 付与を削除 | `test_phase_trial_passes_unique_wfg_output_and_collects_file` |
| runner | 同 trial の path を固定する | 同 test の再走非衝突 assertion |
| runner | file JSON/SHA を収集しない | 同 test の受領証 assertion |
| runner | 性能 argv に WFG flag を追加 | 性能 flag 不在 test |
| test fixture | 起動時軸行を削除 | `test_wfg_startup_axes_without_terminal_output` |
| test fixture | 必須 workload flag を削除 | 実 `_admit_output` を通す正例 |
| patch | stdout emit を削除 | 計算ノード probe で snapshot 不在。固定 Python fixture だけでは KILLED にならない |
| patch | 起動時 `ShowOptParameters()` を削除 | hang 実走の `_admit_output` が軸行欠落で失敗 |
| patch | serializer の field/held_locks を削除 | 実出力を使う probe。Python 側では対応する fixture 変異が契約感度を示す |
| patch | 実 mode 正規化を削除 | read/read 実競合を含む閉路の実出力で検証器が拒否。単発走で該当閉路が出る保証はない |

固定 fixture は C++ を変更しても自動では変わらない。したがって、**C++ patch の変異が Python test により直接 KILLED されたとは報告できない。** fixture 変異は serializer 契約への検証器の感度を示す間接証拠であり、実装への帰属は実 C++ 出力との一致確認に依存する。実 patch 変異について未実走なら「未測定」とする。

## 焦点テスト集合と影響範囲

実装後の焦点集合は次とする。実行は `tools/run_tests.py` 経由とし、この段では実行していない。

| 集合 | 対象 |
|---|---|
| 接続の新 test | 上記 stdout fixture、旧 field、holder、軸行、argv、durable receipt、mode の各 test |
| 既存 deadlock | `test:1432–1477` の 3 test |
| phase 回帰 | `test:1082–1165` の phase2 counter、phase matrix、自然終了、閉路ゼロの test |
| admission | `test:454–487` の workload/build binding、`:828–881` の parser/admission test |
| WFG 不在 | `test:490–554` の M3 と population test |
| build/condition | `test:34–74` の condition gate の順序・全軸・実 cache 由来の test |
| inert 関連 | `test:933–1080` の witness/default-stock 検査 |

runner の dispatch 分類は変えない。

- `orchestrator/tests/test_hooks.py:3088` は期待分類の entry。
- `:3399` は分類説明の期待値。
- `:4443` 付近の `test_bash_study_entries_require_compute_dispatch` が実 command 判定を確認する。

前 2 件は test node そのものではなく期待値表である。該当表を検査する既存 test と `test_bash_study_entries_require_compute_dispatch` を焦点集合に含める。probe を repo に残さないため、新しい恒久 registry entry は追加しない。

`orchestrator/campaign/condition_meaning_gate.py:159–176` は 4 軸の `DefineSpec` と patch path を保持する。path・macro・target は変わらないので編集不要。ただし patch bytes が入力になる実 condition gate は新 SHA で取り直す。静的な domain/spec 回帰は `orchestrator/tests/test_condition_meaning_gate.py:2585` の `test_v1_domain_and_claim_boundaries_are_exact` が関連する。

SHA pin は検算した。現 patch の SHA-256 は次である。

```text
a56a44ae9402fe57f48408a3e26c448f8d7dca1269bd2532246bf8ddde49c063
```

この完全一致文字列の tracked file 検索結果は、以下の履歴記録 3 件だけだった。

- `output/insights/2026-08-25_ss2pl-lock-protocol-study/raw/controls.json:1922`
- 同 `replication.json:1334`
- 同 `sweep.json:1334`

実行用 code の SHA 固定値は見つからない。3 件は過去の入力記録として変更しない。

patch の hunk count を更新し、実装後に pin への `git apply --check` を確認する。新規 file の hunk、特に `wfg.cc` と `ycsb_ss2pl.cc` の行数更新を忘れない。親の docs 更新後には既存の docs/agent 検査、commit 後には provenance 監査を通常どおり行う。ここではそれらの成功を報告しない。

## リスクと未確定点

1. **watchdog の終了は benchmark の終了ではない。**  
   `patch:2511–2515` の連続一致後は watchdog だけが return する。worker が lock 待ちなら main は `runner.hh:299` で join 待ちを続ける。`ss2pl_wfg_stop()` は `ccbench::run()` 後なので hang 時には呼ばれず、runner の hard timeout が必要である。

2. **3 枚出たことと受理は別である。**  
   現 C++ `cycle_signature()` は選択された cycle の node 属性と counter を含むが、cycle 内の追加 edge 全体は含まない。内部判定で停止しても、Python が topology の変化を見つけて拒否する場合がある。P6 を維持する今回は、この場合を受理へ変更しない。

3. **P3 では tick の欠番を Python が拒否しない。**  
   閉路なし tick では event を出さないため、emit 列の隣接と watchdog tick の隣接は一致しない場合がある。tick を保全して可視化し、検証器への新しい連続性述語は追加しない。

4. **SIGTERM による buffer 喪失を防げる範囲。**  
   完了した `fflush` までの bytes は pipe に渡り、`communicate()` が回収する。SIGTERM/SIGKILL が書込み途中に来れば最後の行は欠け得る。`_json_events` はその行を無視する。flush 済み 3 枚が揃う前に終了した走行を受理してはいけない。

5. **大きい event の原子性は writer 排他に依存する。**  
   全 held lock を含むため 48 thread の閉路では 4 KiB を超え得る。単一 `fwrite` だけでは説明不足であり、`cout_mutex` と FILE lock、対象 worker の出力経路を根拠にする。自然終了時の main 終端出力との競合を含め、実 stdout に JSON 行の破断がないことは probe で確認する。

6. **registry の一貫性と実 lock 状態の一貫性は同義ではない。**  
   `take_snapshot()` は mutex 下で registry をコピーする。一方、実 lock 操作と `publish_acquired/released` は別の呼出しなので過渡的な観測窓がある。この wave は既存計器を接続するものであり、その観測窓を解消したとは主張しない。持続した同一証拠を独立検証する条件を保持する。

7. **起動時の workload 行は揃う。**  
   `displayWorkloadParameter()` は watchdog 開始前で、必要な 5 行を `endl` 付きで出す。DB 構築前にも出るため、hang 後の admission に利用できる。ただし argv の出力先 flag が欠ければ、その前の `chkArg()` で失敗する。

8. **phase2 は未接続のまま残る。**  
   出力先 flag と起動時軸行の追加で起動時の断絶は解消するが、`runner:2476–2494` が要求する stdout の `acquisition_paths` は依然出ない。正常終了して metrics が揃っても `_phase2_counters()` が `ContractError` を出す見込みである。terminal file に既存の取得回数があっても代用しない。

9. **実閉路が観測されない可能性。**  
   1 走で `accepted_cycle=None` でも、それだけでは接続失敗と判定しない。実 stdout、file 状態、timeout、snapshot 数、拒否材料を区別して記録する。受理された場合も、D791 に従い計装 build の証拠に限定する。

## 総括

実装は、①実 lock mode を表す compact v2 event と holder 証拠、②同一 serializer の durable file、③WFG 限定の起動時軸行、④trial ごとの出力先 flag と file 受領証、⑤実 parser/検証器を通す test の順で進める。

brief の主要アンカーと 5 件の断絶は確認できた。追加で、排他 lock の read 操作を `"read"` と出す現計器の意味上の不一致を修正対象に含める。検証器の受理条件、timeout 必須、性能 build からの計器除去は維持する。

完了の実証は計算ノード上の production 経路による 1 走で行う。固定 Python fixture だけでは C++ 出力・flush・起動時配線の成立まで証明できない。