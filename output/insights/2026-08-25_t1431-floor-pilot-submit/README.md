# [T-1431] 床値 pilot の実投入と、停止点の確定

## 要約

D581 に従い床値 pilot を実投入した (request `944884.nqsv`)。前回 (`940170.nqsv`) と同じく
**12 セル中 3 セルの build が完了し、4 セル目 `rr20::sort_best` で停止した。計測到達セルは 0。**
admission チケットの消費は今回も 0 枚で、`retry_slots_per_cell=2` は全 12 セル満枠のままである。

**ただし今回は、前回わからなかった停止の実体が 1 回の走行で確定した。**
worklog 906 の [T-1578] が入れた耐久診断が発火し、握り潰されていた例外の本文が
計算ノード外へ残ったためである。

停止の実体は、コンパイル失敗ではなく **izanagi 側の build 後検査が、現行 CCBench pin では
出現しえない `CMakeCache.txt` の key を要求していたこと**である。

## 環境・実行パラメータ (D581 が求める記録)

- **実行環境**: Pegasus, queue=gen_S, nodes=1, elapstim_req=10:00:00。
  PBS 指示子は `tools/pegasus/floor_campaign.sh` の
  `-A SFC` / `-q gen_S` / `-l elapstim_req=10:00:00` / `-b 1`
- **投入元 commit**: `16086f120243644c5dcab2c56669cc3cd36ee992`
  (worktree `dev-wave-t1431-floor-pilot-submit` 経由)
- **submission nonce**: `09869a5443c533f892277a9882a2082a`、request ID = `944884.nqsv`
- **投入コマンド**: `tools/pegasus/submit_floor.sh --confirm-irreversible-pilot-holdout`
  (先に `--dry-run` で qsub argv を確認した)
- **ccbench pin**: `511c9538e4e8efa54b45cda62e72389ed3b706ec`
- **floor protocol**: `output/s8b-freeze/floor-protocols/e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01--511c9538e4e8efa54b45cda62e72389ed3b706ec.json`
  (`resolve-current-protocol` の live 解決結果、rc=0。前回試行と同一ファイル)
  - `contract_sha256=e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01`
  - `stock_configuration=stock_common`、`n_sessions=8`、`reps=5`、`retry_slots_per_cell=2`、
    `extime_s=5`、`env_tag=pegasus`、`schedule_algorithm=round-permutation/v2`
- **toolchain**: 計算ノード実測で `gcc 11.4.0` / `g++` 同版、`cmake 3.25.0`
  (`/system/apps/ubuntu/20.04-202210/oneapi/2022.3.1/intelpython/python3.9/bin/cmake`)
- **最適化 / build**: `buildcache.build_v2` 経由、trace-disabled (規律1)
- **ワークロード**: 未到達 (12 セル中 0 セルが計測開始に到達)
- **所要**: 03:22:07 JST 投入 → 03:24:54 JST 終了 (job 側 `Elapse` は 2 分台)

## 前回わからなかったことが、今回わかった

[T-1578] の `_floor_build_exception_diagnostic` が、握り潰されていた例外を
`sort-swo-oracle-postflight-failure.json` の `floor_failure_diagnostic.build_exception` へ
exact 5 key で残した。

```json
{"schema_version": "s8b-floor-build-exception/v1",
 "exception_type": "BuildCacheError",
 "message_tail": "CMakeCache.txt の masstree_SOURCE_DIR が一意な絶対 path でない",
 "message_tail_sha256": "ef1f7d4981bb83f832ad566fcd4515ab29b9edcd323e176a1c87f296fee97611",
 "message_truncated": false}
```

`message_truncated=false` なので、これは切り詰めのない全文である。

## 確定した根本原因

- 送出元は `orchestrator/campaign/buildcache.py` の
  `_masstree_source_root_from_cmake_cache`。呼び手は `build_v2` の
  `dependency_receipt is not None` 分岐で、floor の `sort_best` cell だけが通る。
- 旧実装は cell の build directory の `CMakeCache.txt` に
  `masstree_SOURCE_DIR(:型)?=<絶対 path>` がちょうど 1 行あることを要求していた。
- CCBench (pin `511c9538…`) の `cmake/ThirdParty.cmake` は 1 引数形式の
  `FetchContent_Populate(masstree)` を使う。この形式は `<name>_SOURCE_DIR` /
  `<name>_BINARY_DIR` / `<name>_POPULATED` を**呼び出し scope の通常変数にしか設定せず、
  `CMakeCache.txt` へは書かない**。
- したがって出現数は常に 0 で、`len(matches) != 1` が必ず成立する。
  **この述語は現行 pin では構造的に到達不能だった。**

### 親がログインノードで行った独立再現

計算ノードの走行と同じ cmake 3.25.0 / g++ 11.4.0 / 同 payload / 同 configure argv で、
pinned CCBench に `patches/silo-sort-variant.patch` を当て、freeze の
`rr20.sort_best.comparator` を marker `silo-writeset-sort` へ materialize した
(diff 検疫 passed=True)。その cell configure は **rc=0** で、生成された
`CMakeCache.txt` の実測は次のとおりだった。

- `masstree_SOURCE_DIR` の出現数 = **0**
- `POPULATED` の出現数 = **0**
- 実在するのは
  `FETCHCONTENT_BASE_DIR:PATH=<base>` と
  `FETCHCONTENT_SOURCE_DIR_MASSTREE:PATH=<base>/masstree-src` (各 1 行、いずれも絶対 path)
- `CMAKE_GENERATOR:INTERNAL=Unix Makefiles` が 1 行

また `CMakeFiles/masstree_build.dir/DependInfo.cmake` の
`CMAKE_MULTIPLE_OUTPUT_PAIRS` には、生成器が解決した
`<base>/masstree-src/config.h` と `<base>/masstree-src/libkohler_masstree_json.a` の
絶対 path 対が 1 行で入っていた。

### コンパイル自体は通っていた

各セルの build marker の時刻 (UTC) は次のとおりである。

```
18:23:22.900920  rr20::backoff_fixed_best
18:23:51.331633  rr20::ident_all
18:24:18.704819  rr20::p2_2_flag_opt
18:24:48.071955  rr20::sort_best
```

成功した 3 セルは各 約 28 秒。`sort_best` は build marker の 5.9 秒後に失敗記録が出ている。
これは `sort_best` だけ共有 base に mimalloc / googletest が用意済みで、
その分だけ短いことと整合する。configure と build は成功し、その後の検査で落ちた。

## 前回の 2 つの blocker の現状

| blocker | 状態 | 根拠 |
|---|---|---|
| A (一次要因): build 失敗理由が永続化されない | **解消** | 本試行で診断が発火し、原因が 1 回で確定した |
| B (潜在要因): 固定した `archive_sha256` が再現不能 | **解消** | [T-1579] が run 内比較へ張り替えた。今回の `dependency_archive_sha256` は `4d5bfc80…` で前回の `0a6514a0…` と異なり、旧実装なら発火していた |

## 本 wave が入れた修正

権威を 2 証跡の一致へ張り替えた (設計判断は decisions 台帳)。

- **A (cache 入力)**: `FETCHCONTENT_SOURCE_DIR_MASSTREE` があればその値、
  無ければ `<FETCHCONTENT_BASE_DIR>/masstree-src`
- **B (解決結果)**: `CMakeFiles/masstree_build.dir/DependInfo.cmake` の
  `CMAKE_MULTIPLE_OUTPUT_PAIRS` が記録した 2 path の親ディレクトリ

`realpath` 後に A = B を要求し、呼び手の「実効 root は staged base の
`<base>/masstree-src`」という exact 比較はそのまま残した。三者一致である。
生成器は `CMAKE_GENERATOR` の exact 照合で `Unix Makefiles` に固定し、
証跡の欠落・重複・相対 path・NUL・親不一致はすべて fail-closed とした。

A だけでは足りない理由は、CMake の変数解決で通常変数が cache 変数を shadow するためである。
ambient な toolchain file が `set(FETCHCONTENT_SOURCE_DIR_MASSTREE <別 root>)` を
cache 指定なしで行うと、実効値は別 root になるのに `CMakeCache.txt` には argv 由来の値が残る。
B は生成器が展開した結果なので、その差し替えが必ず現れる。
これは D425 が名指しで警戒していた経路であり、段 3 の敵対レンズ 2 本が独立に指摘した。

## 一回性 key の消費について

**確認済み: 本試行もチケットを 1 枚も消費していない。** admission root
(`.git/izanagi/s8b-holdout-admission-v1`) 配下に 2026-08-16 より新しい file は 0 件だった
(`attempt-ledger.jsonl` / `ledger.jsonl` / `claims/` / `consumed/` はいずれも 2026-08-16 のまま)。
cell 単位の attempt ticket を消費する段より前で停止したためである。
次回の再投入も `retry_slots_per_cell=2` を全 12 セルぶん保持した状態から開始できる。

## 記録しておく副次事実

- `fetchcontent_archive_sha256` は build cache の preimage (キー) に入る
  (`buildcache.py` の `_v2_identity`)。この値は masstree の in-tree build 成果物の hash で
  run ごとに変わるため、**`sort_best` cell の build cache は job を跨いで必ず cold** である。
  本 wave の scope 外だが、床値 campaign の所要見積りに効く。
- `masstree_source_root_sha256` は preimage には入らず completion manifest の値である。
  したがって本修正は build cache のキー空間を変えない。

## 証拠の所在

計算ノード側の一次資料は、将来の official 床値 job の起動証明を止める holdout clean-scan の
汚染を避けるため repo 外へ退避した。

- 退避先: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1431-floor-pilot-submit/evidence-bundle/`
  (`job-staging/` = checkpoint と失敗 record、`attempts/` = 投入 receipt、
  `run-dir/` = journal、`s8b-build-cache/` = 3 完了 + 1 失敗、`claims/`)
- 親のログインノード再現: 同 job dir の `repro/`
- 段 2〜6 の子成果物と裁定: 同 job dir の `stage2-plan.md` / `stage3-sol.md` /
  `stage3-luna.md` / `stage4-ruling.md` / `stage5-author.md` / `stage6-sol.md` /
  `stage6-luna.md` / `stage6-fix.md`
