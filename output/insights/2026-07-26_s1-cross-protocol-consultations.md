# [T-109] クロスプロトコル対応 wave の逐語 (2026-07-26)

本文は codex 子の出力そのままである。親の裁定は
`output/insights/2026-07-26_s1-cross-protocol-gate-survey.md` を正本とする。
3 本すべて NO-GO。親へ渡した入力 (brief / 親反論) も同 wave subdirectory に置いた。

| 節 | 原文 sha256 | bytes |
|---|---|---|
| 段 2 プラン起草 (codex gpt-5.6-sol / reasoning=max / sandbox=read-only) | `ce1f43747cda24bfe17bce3db190757ec2cb8ef02e4f309ea8ed1aeb4c691bc7` | 29390 |
| 段 3 敵対レンズ A — 正しさ境界 (同上) | `c5a0cb440827d86565c6413d8f71abbaa000ed3a3a44575b7afab11226e98f81` | 14979 |
| 段 3 敵対レンズ B — 整合・実効性 (同上) | `759fa25afe9d754de5eac40425753246a7e56c5d269f504ed6ad11d5146bbcce` | 17804 |

---

## 段 2 プラン起草 (codex gpt-5.6-sol / reasoning=max / sandbox=read-only)

# 静的結論

判定は **現 brief のままでは NO-GO** である。mocc の C/R/W hook と現行 RWLOCK 向け write-lock 被覆は設計できるが、実装開始前に次の二点を親／人間が裁定する必要がある。

1. `patches/mocc-trace-hook.patch` は D16 の「trace-hook は `izanagi-trace` branch」という明文に反する。D16 は trace-hook の out-of-tree patch 案を明示的に却下しているため、今回だけの例外は新裁定なしには導けない。`docs/decisions.md:248-275`、`patches/README.md:29-32`
2. 要求された `patchharness.applied() → buildcache.build()` は、dirty な `cc/mocc/transaction.cc` が `source_digest` の allowlist 外なので現状必ず停止する。`orchestrator/campaign/buildcache.py:564-577`、`orchestrator/campaign/source_digest.py:62-71,299-335`

以下は、この二点を明示した条件付き実装プランである。テスト・ビルド・correctness run は実行しておらず、緑は主張しない。

# 1. mocc trace-hook の挿入点

行番号は現行 pin `d706650` の追加前行をアンカーにする。`orchestrator/campaign/pin.py:26-28`

## 1.1 挿入範囲

| 目的 | `#if TRACE` の開始／終了アンカー | 実装内容 |
|---|---|---|
| trace header | 開始=`external/ccbench/cc/mocc/transaction.cc:11` の直後、終了=`:13` の直前 | `#if TRACE` → `#include "../../include/trace.hh"` → `#endif`。header 自体も全体が `#if TRACE` 内だが、brief の「追加コードはすべて囲う」を満たすため include 側も囲う。`external/ccbench/include/trace.hh:25-124` |
| txn 開始時 shadow reset | 開始=`transaction.cc:889` の直後、終了=`:891` の直前 | `izanagi_trace::clear_shadow()`。validation の lock loop より前に置く。 |
| writer 所有の記録 | 開始=`transaction.cc:900` の直後、終了=`:902` の直前 | successful `lock(tuple,true)` 後、`CLL_` に同一 tuple・`mode_==true` の native writer entry がある場合だけ `record_lock()`。`LockElement` の tuple/mode は `cc/mocc/include/lock.hh:159-168`。 |
| C/R/W と入口 lock 検査 | 開始=`transaction.cc:1034` の直後、終了=`:1036` の直前 | txid 採番、C/R/W emit、全非 INSERT write の入口 lock 検査。 |
| lock 保持継続検査 | 開始=`transaction.cc:1037` の直後、終了=`:1038` の直前 | switch による `memcpy` / delete より前に、非 INSERT ごとに raw writer state と shadow を再検査。 |
| shadow 解放 | 開始=`transaction.cc:1014` の直後、終了=`:1015` の直前 | `unlockCLL()` の `CLL_.clear()` 後に `clear_shadow()`。abort・success・reconnoiter の共通出口になる。 |

## 1.2 commit 行 `C`

mocc の commit TID は `writePhase()` の

```cpp
Tidword maxtid = max({tid_a, tid_b, tid_c});
mrctid_ = maxtid;
```

で確定する。`external/ccbench/cc/mocc/transaction.cc:1017-1034`

したがって `:1034` の直後で `next_txid()` を一度だけ呼び、`emit_commit(thid_, txid, maxtid.epoch, maxtid.tid)` を出す。`next_txid()` と C schema は `external/ccbench/include/trace.hh:37-47,78-82`。Silo の正本も `maxtid` 確定直後に同じ順序で採番・emit している。`external/ccbench/cc/silo/transaction.cc:579-595`

## 1.3 read 集合 `R`

R の版は live tuple から再ロードしてはならず、read 時に保存した `ReadElement::tidword_` を使う。

- cold OCC path は payload 前後の tidword 一致を確認し、`expected` を read set に保存する。`external/ccbench/cc/mocc/transaction.cc:218-266`
- hot/RLL path も lock 後に `expected` を読み、同じ constructor へ渡す。`external/ccbench/cc/mocc/transaction.cc:182-216,258-266`
- `ReadElement` はその `Tidword` を `tidword_` に保存する。`external/ccbench/cc/mocc/include/mocc_op_element.hh:15-23`
- validation も保存版の epoch/tid と live 版を比較している。`external/ccbench/cc/mocc/transaction.cc:910-922`

よって `:1034` 後の trace block 内で、各 `re` について `re.tidword_.epoch` / `re.tidword_.tid` を emit する。mocc の `Tidword` は `absent:1, tid:31, epoch:32` なので trace の `(epoch,tid)` へ恒等写像できる。`external/ccbench/cc/mocc/include/tuple.hh:14-31`

## 1.4 write 集合 `W`

全 write の新版は同じ `maxtid` で、各 tuple へ `__atomic_store_n(..., maxtid.obj_)` される。`external/ccbench/cc/mocc/transaction.cc:1033-1063`

したがって W は Silo と同じ `UPDATE→U / INSERT→I / DELETE→D` 写像で、版は `maxtid.epoch, maxtid.tid` とする。Silo の正本は `external/ccbench/cc/silo/transaction.cc:601-607`、W schema は `external/ccbench/include/trace.hh:91-96`。`absent` は write 種別ごとに変化するが epoch/tid は不変である。`external/ccbench/cc/mocc/transaction.cc:1040-1063`

## 1.5 abort / retry の shadow clear

主 clear は `unlockCLL()` の末尾、現行 `transaction.cc:1014-1015` 間に置く。

- abort は `unlockCLL()` を呼んでから set を消す。`external/ccbench/cc/mocc/transaction.cc:961-979`
- success は全 write 後に `unlockCLL()` を呼ぶ。`external/ccbench/cc/mocc/transaction.cc:1062-1071`
- reconnoiter 終了も同じ出口を使う。`external/ccbench/cc/mocc/transaction.cc:1104-1111`
- YCSB retry は early abort と commit failure の双方で `abort()` を呼んでから retry する。`external/ccbench/include/ycsb.hh:149-165`

さらに validation 冒頭でも clear する。これは前回 caller が異常終了した場合の防御であり、Silo の lock loop 入口 reset と同型である。`external/ccbench/cc/silo/transaction.cc:145-153`

## 1.6 lock 被覆を移植できる範囲

### 移植できる部分

現行 stock の `RWLOCK` に限り、**非 INSERT write の commit 時 write-lock 被覆**は移植できる。

- hot update/delete は温度閾値または RLL により操作中に writer lock を取る。`external/ccbench/cc/mocc/transaction.cc:353-377,460-486`
- cold OCC write も含め、全非 INSERT write は validation で必ず `lock(tuple,true)` に収束する。`external/ccbench/cc/mocc/transaction.cc:888-903`
- write set は tuple pointer 順に sort される。`external/ccbench/cc/mocc/include/mocc_op_element.hh:48-50`、`external/ccbench/cc/mocc/transaction.cc:891-895`
- stock の writer live state は `rwlock_.ldAcqCounter()==W_LOCKED` で確認できる。`external/ccbench/cc/mocc/include/lock.hh:137-156`

入口・保持検査は次の conjunction にする。

```text
live rwlock state == W_LOCKED
AND
izanagi_trace::holds_lock(tuple)
```

shadow は単に `lock()` が return したら記録するのではなく、validation 後の transaction-native `CLL_` に同一 tuple の writer entry がある場合だけ記録する。これにより「自分で直前に record したから常に true」という完全な恒真化を避ける。`CLL_` entry の形は `external/ccbench/cc/mocc/include/lock.hh:159-168`。

違反は既存の `emit_lock_violation()` を流用し、入口は `not-locked-at-entry`、write 直前は `lock-lost-before-write` とする。`external/ccbench/include/trace.hh:113-120`

### 移植できない部分

- **cold OCC read に read-lock 被覆 assert は置けない。** その経路は意図的に read lock を取らず、版の二重読みによって整合性を得る。`external/ccbench/cc/mocc/transaction.cc:218-257`
- **hot/RLL read の「この transaction が reader lock owner」という raw assert は同等強度では置けない。** `ReaderWriterLock` が公開するのは reader 数の aggregate counter だけで owner ID がない。`external/ccbench/cc/mocc/include/lock.hh:137-156`
- **INSERT は除外する。** mocc insert は新規 absent tuple を Masstree に置く経路で、非 INSERT の `rwlock_` validation lock を通らない。`external/ccbench/cc/mocc/transaction.cc:388-427,893-895`
- **MQLOCK へ同じ assert は移植できない。** 現行 mocc target は `RWLOCK` を固定定義し、MQLOCK を選ばない。`external/ccbench/cc/mocc/CMakeLists.txt:1-10`。MQLOCK の公開面は acquire/release API と queue metadata で、RWLOCK の `ldAcqCounter()==W_LOCKED` に相当する単純な current-owner predicate がない。`external/ccbench/cc/mocc/include/lock.hh:92-134`
- **RWLOCK でも完全な owner proof はできない。** raw counter 自体に owner field がなく、別 worker が lock を持つ場合まで区別できない。この限界は Silo の D38 にも明記されている。`docs/decisions.md:995-1001,1046-1050`

したがって「mocc hybrid 全体へ Silo assert をそのまま移植」とは書けない。主張可能なのは「現行 RWLOCK build の commit-stage non-INSERT write coverage」である。

# 2. `patches/mocc-trace-hook.patch` の形

これは **D16 例外が人間により承認された場合だけ**作る。

- unified diff は既存 patch と同じ `-U3`、すなわち通常 3 context 行とする。`patches/broken-silo-norw-validation.patch:1-8`、`patches/instr-silo-backoff-trigger-gating-tally.patch:1-9`
- path prefix は `a/cc/mocc/transaction.cc` / `b/cc/mocc/transaction.cc`。`external/ccbench/` を prefix に含めない。既存 patch も submodule root 相対である。`patches/broken-silo-norw-validation.patch:1-4`
- 適用先は `external/ccbench` を cwd とした現行 pin。
- `index` 行は real blob hash を使うか省略する。harness は `git apply` を `--index` なしで呼ぶため index 更新は行わない。`orchestrator/campaign/patchharness.py:192-200`
- main patch が touch するのは `cc/mocc/transaction.cc` だけ。共通 header は既に必要な C/R/W/X API を持つ。`external/ccbench/include/trace.hh:78-120`

harness の扱いは次のとおり。

1. `patch_files()` は `git -C <sub> apply --numstat <patch>` で submodule-relative path を得る。`orchestrator/campaign/patchharness.py:143-159`
2. `apply_patch()` は index を変更せず working tree に適用する。`orchestrator/campaign/patchharness.py:192-200`
3. `applied()` は pinned-clean を検査し、排他区間内で apply → body → `finally` revert を行う。`orchestrator/campaign/patchharness.py:234-251`
4. revert は tracked file を `git checkout -- .` で戻し、patch-created file も除去して clean を再検査する。`orchestrator/campaign/patchharness.py:202-231`

ただし配置判断そのものは現行 D16 と衝突する。D16 は trace-hook を `izanagi-trace` branch、broken control だけを `patches/` と定め、全 patch 維持案を却下している。`docs/decisions.md:250-275`

# 3. 使い捨て driver

## 3.1 要求された `buildcache` 連鎖の blocker

実シグネチャは次である。

```python
buildcache.build(
    genome, ccbench_commit, trace,
    cache_root="", cc="gcc-13", cxx="g++-13",
    jobs=16, ccbench_dir="", src_token=None,
) -> BuildResult
```

`orchestrator/campaign/buildcache.py:564-567`

target は `ycsb_{genome.protocol}.exe`、TRACE は `-DCCBENCH_TRACE={0,1}` として渡される。`orchestrator/campaign/buildcache.py:581-590`

しかし `build()` は configure より前に `assert_worktree_within_allowlist()` を無条件実行する。`orchestrator/campaign/buildcache.py:573-577`。allowlist は `cmake/Options.cmake`、`include/backoff.hh`、`cc/silo/transaction.cc` の三つだけなので、mocc patch はここで拒否される。`orchestrator/campaign/source_digest.py:62-71,299-335`

単純に allowlist へ mocc を足すだけでも不十分である。

- source digest は `EVOLVE_BLOCK_SOURCES` だけを hash する。`orchestrator/campaign/source_digest.py:187-194`
- trace hook は include 行も追加するため、mocc を digest 対象に加えると HEAD との include 一致検査に拒否される。`orchestrator/campaign/source_digest.py:197-215,338-349`
- TRACE 差分も pinned HEAD の既存 hook と完全一致することを要求するため、新規 mocc hook は trusted baseline として別設計しない限り拒否対象になる。`orchestrator/campaign/source_digest.py:236-269`
- build 出口でも `resolve()` を再実行するため、caller が任意の `src_token` を渡すだけでは回避できない。`orchestrator/campaign/buildcache.py:629-656`

したがって **現 scope で `applied() → buildcache.build()` を書く案は不成立**。gate の monkeypatch、偽 `src_token`、allowlist だけの拡張は提案しない。

## 3.2 scope 内の driver 案

提案配置は `orchestrator/campaign/mocc_trace_hook_smoke.py`。pipeline や `SPACES` へ登録せず、名前どおり one-shot smoke とする。

100 行以内の行予算案は以下。

- import・定数・`Genome`: 18 行
- `_fresh_build()`: 20 行
- `_run_verify()`: 16 行
- 4 control の case table と main: 38 行
- cleanup／終了コード: 8 行
- 合計: 100 行

フローは次とする。

```python
for case in controls:
    with applied(HOOK_PATCH, PIN, ccbench_dir):
        if case.broken_patch:
            apply_patch(case.broken_patch, ccbench_dir)
        binary = fresh_tmp_cmake_build(...)
        ncommit, rc, _ = pipeline._run_trace(
            binary, trace_dir, RUN_FLAGS, 2100, timeout_s=120.0
        )
        result = verify_trace_dir(trace_dir)
        check_case(case, ncommit, rc, result)
```

- `applied()` の実シグネチャは `applied(patch_path, pin_commit, ccbench_dir="")`。`orchestrator/campaign/patchharness.py:234-251`
- broken patch の layering は `applied()` body 内で `apply_patch()` する既存方式に合わせる。`orchestrator/campaign/s8a_trigger_coverage.py:194-202`
- fresh CMake build は既存 broken driver と同じく `Genome.cmake_defines()`、`-DCCBENCH_TRACE=1`、target `ycsb_mocc.exe` を使う。先例は `orchestrator/campaign/s3_lock_coverage.py:123-138` と `orchestrator/campaign/s8a_trigger_coverage.py:90-107`
- `pipeline._run_trace()` の実シグネチャと戻り値は `orchestrator/campaign/pipeline.py:167-194`
- `IZANAGI_TRACE_DIR` は `env=dict(os.environ, IZANAGI_TRACE_DIR=trace_dir)`、cwd も trace dir、`log/` を作る正本どおりに渡す。`orchestrator/campaign/pipeline.py:178-187`
- verifier の直接 API は `verify_trace_dir(trace_dir: str, max_report=20)`。`orchestrator/verifier/core.py:17-19`
- JSON 化が必要なら `result_to_dict(result)` を使う。`orchestrator/verifier/report.py:42-74`

workload は提案として `tuple=200, skew=0.9, rratio=50, rmw=true, max_ope=5, thread=1, extime=1, temp_threshold=100` とする。前半は既存 lock control と同じ。`orchestrator/campaign/s3_lock_coverage.py:60-66`。`TEMP_MAX=20` なので `temp_threshold=100` は cold OCC path を固定し、lockskip control が操作中の hot pre-lock で隠れないようにする。`external/ccbench/cc/mocc/include/tuple.hh:12`、runtime flag 定義は `external/ccbench/cc/mocc/include/common.hh:34-40`

厳密に `buildcache.build()` を必須とするなら、本 wave の scope を広げて「trusted trace baseline patch」を source identity に組み込む設計が先であり、driver はそれまで blocked とする。

# 4. positive control

## 4.1 最小の C/R/W control

提案する故障 patch は `patches/broken-mocc-write-version.patch`。

hook の W emit だけを裸マクロ `IZANAGI_BREAK_MOCC_WRITE_VERSION` で切り替え、ON 時に W の tid を `uint64_t(maxtid.tid)+1` として、C と確実に不一致にする。故障コード自体も既存 trace block 内、すなわち `#if TRACE` 内に限定する。

期待条件は次。

- 正例: txns/read/write がすべて非 0、`certified==true`、integrity clean。
- 故障例: `write_version_mismatch>0`、`certified==false`、`verdict=="indeterminate"`。
- W≠C は parser/core が専用カウンタへ配線する。`orchestrator/verifier/parse.py:20-25,51-56`、`orchestrator/verifier/core.py:31-35`
- integrity 不良は certified にならない。`orchestrator/verifier/model.py:137-142,177-195`
- CLI ならこの indeterminate は exit 3。`orchestrator/verifier/cli.py:81-86`

これは版写像移植そのものを壊す最も安い control である。

## 4.2 lock assert の operative control

lock assert まで採用するなら、上記だけでは「assert が恒真でない」証明にならない。最低でも次の二本を分離する。

1. `patches/broken-mocc-lockskip-validation.patch`
   - TRACE + `IZANAGI_BREAK_MOCC_LOCK_COVERAGE` のときだけ `validation():895` の `lock(tuple,true)` を skip。
   - cold single-thread run では raw state も CLL shadow も writer ownership を示さず、入口 X が出る。
2. `patches/broken-mocc-early-unlock-validation.patch`
   - TRACE + `IZANAGI_BREAK_MOCC_EARLY_UNLOCK` のときだけ write loop の保持検査直前で `w_unlock()` し、当該 CLL entry も除去して後段の二重 unlock を避ける。
   - `w_unlock()` は counter を increment する実装なので、CLL を残したまま後で再 unlock する案は不正である。`external/ccbench/cc/mocc/lock.cc:968-995`
   - 保持検査だけが `lock-lost-before-write` を出すことを要求する。

Silo の既存 control も、正例 stock と lockskip/early-unlock の赤を別々に要求している。`patches/README.md:101-123`、`orchestrator/campaign/s3_lock_coverage.py:190-218`。X は cycle ではなく integrity 違反として indeterminate になる。`orchestrator/verifier/core.py:43-61`

したがって合格セットは次の四つ。

- 正しい hook: 緑になる正例
- W version mismatch: C/R/W mapping が赤になる
- lockskip: 入口 assert が赤になる
- early-unlock: 保持 assert が赤になる

# 5. (P6) holdout repo scan

静的判定は「**ファイル追加は scan report に影響するが、invariant 違反になるとは限らない**」。

- root の tracked file に加えて、gitignore されていない untracked regular file も列挙される。したがって新しい `patches/*.patch` と driver は scan 対象になる。`orchestrator/campaign/s8b_holdout_freeze.py:197-212`
- 追加により `file_count` は変化する。`orchestrator/campaign/s8b_holdout_freeze.py:345-352`
- ただし freeze verify は現在値の `file_count` を frozen 値と完全一致させず、無関係な追加による変動を許容している。`orchestrator/campaign/s8b_holdout_freeze.py:692-699,725-737`
- invariant が失敗するのは、同一ファイルが holdout の `rratio`、`skew=0.9`、`rmw=0` の三軸をすべて満たした場合である。`orchestrator/campaign/s8b_holdout_freeze.py:34-55,270-294`
- 実 repo test が固定するのも `rr80` / `rr20` の conjunction hit が空であることと、positive control が非 0 であることだけ。`orchestrator/tests/test_s8b_repo_scan_invariant.py:21-35`

提案 driver は `rratio=50`、`rmw=true` とし、patch/PBS script に holdout workload literal を書かない。これなら静的には holdout conjunction を新設しない。

親が追加後に実測すべきコマンドは次。

```bash
python3 orchestrator/tests/test_s8b_repo_scan_invariant.py
python3 orchestrator/campaign/s8b_holdout_freeze.py search
python3 orchestrator/campaign/s8b_holdout_freeze.py verify
```

各 CLI の実装は `orchestrator/campaign/s8b_holdout_freeze.py:841-875`。

# 6. mocc の stock 既定 genome

提案する明示 genome は次。

```python
Genome("mocc", {
    "BACK_OFF": 1,
    "KEY_SORT": 0,
    "TEMPERATURE_RESET_OPT": 1,
})
```

根拠:

| flag | stock | live 根拠 |
|---|---:|---|
| `BACK_OFF` | 1 | universal default。`external/ccbench/cmake/Options.cmake:13-23`。abort と leader work の双方に実分岐がある。`external/ccbench/cc/mocc/transaction.cc:981-991,1085-1089` |
| `KEY_SORT` | 0 | mocc target へ渡される。`external/ccbench/cc/mocc/CMakeLists.txt:5-9`。YCSB operation sort を切り替える。`external/ccbench/include/ycsb.hh:78-83` |
| `TEMPERATURE_RESET_OPT` | 1 | mocc 固有 default。`external/ccbench/cmake/Options.cmake:41-49`。per-record reset と global reset の両枝が実在する。`external/ccbench/cc/mocc/transaction.cc:827-838`、`external/ccbench/cc/mocc/util.cc:196-220` |

`Genome` は protocol 名を検証せず、TRACE だけを予約名として拒否するので直接構築できる。`orchestrator/campaign/model.py:35-59`

除外は次のとおり。

- `RWLOCK`: stock で固定 ON だが CMake cache genome 軸ではない。`external/ccbench/cc/mocc/CMakeLists.txt:1-10`
- `TRACE`: correctness/perf build の別引数であり genome に入れられない。`orchestrator/campaign/model.py:45-50`
- `ADD_ANALYSIS`: 計測 instrumentation。default 0。`external/ccbench/cmake/Options.cmake:13-19`
- `KEY_SIZE` / `VAL_SIZE`: workload sizing で最適化軸ではない。`external/ccbench/cmake/Options.cmake:20-23`。探索 genome から instrumentation/sizing を除外する規約は `docs/ccbench-anatomy.md:40`
- `MASSTREE_USE`: backend 構造の指定であり、この mocc 実装では lookup/update が Masstree を無条件使用する一方、0 が変える主要箇所は thread init である。`external/ccbench/cc/mocc/transaction.cc:139,346,395-406`、`external/ccbench/cc/mocc/ycsb_mocc.cc:36-38`。有効な最適化二値として扱わない。
- `INSERT_READ_DELAY_MS` / `INSERT_BATCH_DELAY_MS`: default unset。`external/ccbench/cmake/Options.cmake:35-39`。read delay の実装はコメントアウトされ、残る参照は表示だけ。`external/ccbench/cc/mocc/transaction.cc:609-610`、`external/ccbench/cc/mocc/util.cc:230-235`
- `temp_threshold`: live だが runtime gflag で、build genome ではない。`external/ccbench/cc/mocc/include/common.hh:34-40`

# 7. PBS ジョブ構成

提案ファイルは wave-only の `tools/pegasus/mocc_trace_hook_smoke.sh`。floor/oracle/certification へ登録せず、Python smoke driver を呼ぶだけにする。

## ジョブ構成

1. `#PBS -A SFC`, `#PBS -q gen_S`, `#PBS -b 1`。walltime は提案値 `02:00:00` とし、既存 certification job の一 node・2時間構成を踏襲する。`tools/pegasus/certify_calibration.sh:1-5`
2. `PBS_JOBID` / `PBS_O_WORKDIR` を検査し、`TMPDIR=/scr/${PBS_JOBID//:/_}` を create-only 作成する。`tools/pegasus/certify_calibration.sh:15-31`
3. `:` を raw job ID のまま `/scr` path に入れない。CMake が PATH の `:` を list separator として扱うためである。`docs/pegasus-runbook.md:298-304`
4. module は load しない。`module -t list` を記録し、PATH 上の system `gcc/g++/cmake` の realpath と version を保存する。`tools/pegasus/certify_calibration.sh:343-357`、`tools/pegasus/README.md:49-53`
5. `tools/pegasus/policy.json` の pinned source/head を読み、gflags と glog が clean か照合する。pin は `tools/pegasus/policy.json:14-17`。
6. gflags を static/PIC で `/scr` に build/install。`tools/pegasus/certify_calibration.sh:359-421`
7. glog を gflags prefix 参照付きで static/PIC build/install。`tools/pegasus/certify_calibration.sh:423-486`
8. `CMAKE_PREFIX_PATH="$GFLAGS_INSTALL_DIR:$GLOG_INSTALL_DIR"` を export する。既存 floor wrapper の seam は `tools/pegasus/floor_campaign.sh:832-840`。直接 CMake argument にする場合は semicolon 区切りが既存例。`tools/pegasus/certify_calibration.sh:499-506`
9. current pin の detached CCBench worktree と fresh build dir を `/scr` に作る。`tools/pegasus/certify_calibration.sh:488-509`
10. smoke driver に detached worktree、system compiler paths、hook/broken patches を渡し、正例＋故障例を run。trace/build は `/scr` の一時物とし、verifier の構造化結果と build argv だけを job stdout/stderr に残す。
11. detached worktree を削除する。`tools/pegasus/certify_calibration.sh:764-768`

計算ノードに gflags/glog がないこと、永続 pinned source から `/scr` で使い捨て build することは実機確定事項である。`docs/pegasus-runbook.md:301-304`

投入は **人間が行う**。runbook の「重い処理は compute node」は実行場所の規定であり AI への投入権限ではない。`docs/pegasus-runbook.md:245-252`。D87 は明示的に「AI は qsub しない」としている。`docs/decisions.md:3798-3800`

# 親 brief への攻撃

## P1〜P7

| 項目 | 判定 |
|---|---|
| P1 | **根拠不足。** 現行 must 表は S1 と stock 専用経路の択一を残しており、S1 は現在 non-blocking。`docs/phase3.md:206-212`。D32 は cross-protocol 移植を主実験後へ降格し、着手時の一歩目を catalog card と定めている。`docs/decisions.md:709-729`。今回の plan 依頼だけからこの裁定を上書きしたとは推論しない。 |
| P2 | **一部妥当、一部過大。** mocc の恒等写像と write-heavy 代表性は支持される。`external/ccbench/cc/mocc/include/tuple.hh:14-31`、`docs/ccbench-anatomy.md:63-67`。ただし [T-023] は無条件承認ではなく、headline 2／段7で mocc を採るか ablation を承認した場合の保留トリガである。`docs/phase3.md:441-444`。シード序列は性能ベース選定、今回の順位は移植コストなので直接矛盾ではない。 |
| P3 | **部分移植のみ。** current RWLOCK の non-INSERT commit-write coverage までは可能。cold OCC read、hot read owner、MQLOCK、INSERT には同等 assert を置けない。根拠は前節の `transaction.cc:182-266,888-903` と `lock.hh:92-168`。 |
| P4 | **誤り。** Pegasus が build/debug 用であることは AI の qsub 権限を意味しない。D87 は AI の qsub を明示禁止する。`docs/decisions.md:3798-3800`。 |
| P5 | **誤り。** 「gate 待ちなら一時 patch」という例外は D16 にない。D16 は trace-hook を branch に置き、全 patch 案を却下している。`docs/decisions.md:250-275`。新しい人間裁定なしの読み替えは不可。 |
| P6 | **無条件命題として誤り。** untracked patch/driver も列挙され file_count が変わる。`orchestrator/campaign/s8b_holdout_freeze.py:197-212,345-352`。ただし同一ファイルで holdout 三軸 conjunction を作らなければ invariant は維持可能。`:270-294,412-432`。 |
| P7 | **不完全。** mocc 固有 CMakeLists だけでは universal `BACK_OFF` を拾えない。`external/ccbench/cmake/Options.cmake:13-23,60-68`。stock genome は `BACK_OFF=1, KEY_SORT=0, TEMPERATURE_RESET_OPT=1` の三軸を明示すべき。 |

## 「親が実測した事実」への攻撃

- trace emit が現状 Silo/si の二本だけという実質的主張は支持される。`external/ccbench/cc/silo/transaction.cc:584-607`、`external/ccbench/cc/si/transaction.cc:540-554`
- ただし「verifier に silo の出現 0」は字面では誤りで、Silo への言及がコメントにある。`orchestrator/verifier/dsg.py:52-55`。機能的な protocol 非依存性は、入力が trace dir だけである `orchestrator/verifier/core.py:2-19` によって支持される。
- `IntegrityIssues.is_clean()` という名称・引用は誤り。実体は `Integrity.clean()` であり、brief が列挙した四項目以外にも genesis、malformed key、lock、permutation を要求する。`orchestrator/verifier/model.py:101-142`
- 「buildcache は protocol 汎用」は target 生成についてのみ正しい。dirty mocc source の identity/allowlist まで汎用ではなく、この wave の patch は拒否される。`orchestrator/campaign/buildcache.py:573-590`、`orchestrator/campaign/source_digest.py:62-71,299-335`
- `Genome("mocc", ...)` の直接構築は支持される。`orchestrator/campaign/model.py:35-59`
- tictoc の wts 前進はソース上は実在する。`external/ccbench/cc/tictoc/transaction.cc:425-440`。ただし「版 ID が不安定」は実測事実ではなく、この metadata 更新から導いた設計上の推論である。
- freeze／承認定数の既存テスト結果は今回再実行していない。さらに patch/driver 追加後は repo scan の入力集合自体が変わるため、親の過去結果だけでは P6 の証拠にならない。`orchestrator/campaign/s8b_holdout_freeze.py:197-212`

# 未確定事項

1. D16 を更新して prototype trace-hook の一時 out-of-tree patch を許すか、原則どおり `izanagi-trace` branch に置くか。
2. `buildcache.build()` を必須にするため trusted trace baseline/source identity を拡張するか、既存 broken-driver と同じ fresh TMPDIR build を認めるか。
3. 正例 mocc run が `txns>0, reads>0, writes>0, certified=true` になることの実測。
4. W mismatch、lockskip、early-unlock がそれぞれ期待した単独カウンタで赤になることの実測。
5. patch/driver 追加後の holdout `search` / `verify` / repo-scan invariant。
6. Pegasus 上で policy の gflags/glog source が pin 一致・clean であり、system compiler で `ycsb_mocc.exe` が build できること。
7. MQLOCK を将来対象にする場合の owner predicate と専用 positive control。
8. PBS 投入は D87 に従い、人間が明示的に `qsub` すること。

今回行ったのは静的読解だけであり、pytest・build・correctness run は実行していない。

---

## 段 3 敵対レンズ A — 正しさ境界 (同上)

**NO-GO**

以下は静的検査のみ。pytest・build・correctness run は実行しておらず、緑は主張しない。

## A-1. 観測者効果の分離

### 所見 A-1 — must-fix: 手動 CMake 経路が観測者効果ゲートを迂回する

- **(a) 主張:** C++ 挿入案自体は `#if TRACE` 内で、header/member の追加もない。しかし plan の手動 `fresh_tmp_cmake_build()` は TRACE=1 しか作らず、perf build の symbol 検査と diff-of-diffs を通らない。親 R-1 の「これらの gate は campaign identity 専用」という反論は誤りである。
- **(b) 根拠:** `plan.md:160-177`、`parent-rebuttal.md:28-38`。buildcache は build ごとに diff-of-diffs を呼び、TRACE=0 では `nm` 検査も行う。`orchestrator/campaign/buildcache.py:592-620,659-675,713-735`。一方、検査対象は現状 `include/backoff.hh` と Silo transaction に限られ、MOCC は含まれない。`orchestrator/campaign/source_digest.py:62-71,236-269`。先例の S5 は trusted HEAD の stock control だけ buildcache を使い、手動 build は broken 差分だけである。`orchestrator/campaign/s5_permutation_coverage.py:119-134,158-162`
- **(c) 放置時:** `#ifdef TRACE`、unguarded static、検証専用メタデータを誤って含む patch でも smoke の受理集合に入り、perf binary の byte/symbol 集合が変わる。

`patchharness.checkout()` は worktree 隔離だけで、この欠落を補わない。`orchestrator/campaign/patchharness.py:273-287`

## A-2. 版 ID 写像

### 所見 A-2 — must-fix: `absent` の消去は tombstone read を false-green にする

- **(a) 主張:** bitfield の抽出順そのものは正しいが、`absent` を意味的に捨ててよいという結論は誤り。MOCC の hot/RLL read は `absent` を検査せず、その版を read set に保存できる。
- **(b) 根拠:** cold OCC は `expected.absent` を拒否する。`external/ccbench/cc/mocc/transaction.cc:218-246`。対して lock path は単一 load 後に absent を確認せず保存する。`external/ccbench/cc/mocc/transaction.cc:258-266`。validation も epoch/tid しか比較しない。`external/ccbench/cc/mocc/transaction.cc:910-922`。plan はその epoch/tid だけを emit する。`plan.md:40-47`。verifier は DELETE を含む全 W を producer 登録し、op を区別せず read を結合する。`orchestrator/verifier/parse.py:116-126`、`orchestrator/verifier/dsg.py:49-70,81-105`
- **(c) 放置時:** DELETE 後の `absent=true` 版を読んでも D producer が存在するため `orphan_reads=0` となり、本来説明不能な値読みを `certified` 集合へ入れる。

具体的には、reader が Masstree pointer を取得後、delete writer の lock 解放を待って hot read に入ると、DELETE が stamp した版と古い payload を組み合わせて返し得る。

### 所見 A-3 — must-fix: INSERT/reinsert では同一キー版順が native commit 順と一致しない

- **(a) 主張:** `(epoch,tid)` は UPDATE/DELETE の連続上書きでは使えるが、INSERT を含む全 domain の恒等写像ではない。新規 tuple は旧 tombstone の版を継承せず、INSERT は `max_wset_` 計算から除外される。
- **(b) 根拠:** transactional insert の初期化は `tid=0, absent=true` のみで epoch を設定しない。`external/ccbench/cc/mocc/include/tuple.hh:85-89`。INSERT は新 tuple を索引へ置く。`external/ccbench/cc/mocc/transaction.cc:388-427`。validation は INSERT を skip する。`external/ccbench/cc/mocc/transaction.cc:891-903`。commit TID は worker-local `mrctid_` と current epoch から決まる。`external/ccbench/cc/mocc/include/transaction.hh:47-50`、`external/ccbench/cc/mocc/transaction.cc:1017-1034`。verifier は数値順を同一キー版順と仮定する。`orchestrator/verifier/dsg.py:16-18,61-72,107-114`
- **(c) 放置時:** worker A の高い `(E,100)` DELETE 後に worker B が `(E,1)` INSERT すると、verifier は I→D の逆向き ww 辺を作り、cycle の受理・拒否集合を変える。

さらに初期 epoch の pure INSERT は、read/write max が空なので `(1,0)` を commit に選び得る。verifier はこれを genesis commit として拒否する。`external/ccbench/cc/mocc/util.cc:81-83,185-203`、`orchestrator/verifier/dsg.py:52-60`

### 所見 A-4 — must-fix: scan は版 ID 以前に predicate dependency を落とす

- **(a) 主張:** 既存 tuple の scan read は `read_internal()` の保存版を使えるが、空範囲・gap の観測には版 ID がない。MOCC protocol 全体を verify 可能とする主張は成立せず、YCSB 点アクセス限定と明記する必要がある。
- **(b) 根拠:** scan は返された tuple だけを read set に加え、Masstree node version は `node_map_` で内部 validation するだけで trace に出さない。`external/ccbench/cc/mocc/transaction.cc:271-314,943-950,1145-1152`。trace schema は key-version の C/R/W のみ。`external/ccbench/include/trace.hh:17-23`。既知台帳も phantom skew が edge 0 で serializable になると明記する。`output/insights/2026-06-18_phantom-predicate-out-of-scope.md:8-45`
- **(c) 放置時:** TPC-C 等の scan workload では predicate cycle が DSG から消え、phantom anomaly を含む trace が `certified` 集合へ入る。

限定的には、Epotemp、`lock()`、`unlockCLL()`、`abort()` に TicToc 型の tidword 前進はない。温度は `epotemp_`、lock は別 counter/CLL を操作し、native tidword の実 store は初期化と writePhase に限られる。`external/ccbench/cc/mocc/transaction.cc:622-802,827-854,961-1015,1036-1063`。この点だけは brief を反証できない。

## A-3. 正しさゲート

### 所見 A-5 — must-fix: SI 型最小 hook は MOCC の gate を構造的に弱める

- **(a) 主張:** plan は verifier を変更せず、`Integrity.clean()` の9条件も緩めていない。しかし親 R-3 の「SI 型にして lock assert を移植しない」は、`lock_coverage_violations` の producer を消し、この項目を常時ゼロにする恒真ゲートである。
- **(b) 根拠:** 親案は C/R/W のみを要求する。`parent-rebuttal.md:57-63`。D38 は C/R/W だけでは lock 欠落・torn read が見えないため X emitter と2点検査を要求した。`docs/decisions.md:967-1001`。MOCC も non-INSERT を lock 後、payload 更新してから version stamp する。`external/ccbench/cc/mocc/transaction.cc:891-903,1036-1063`。clean は X を含む全9項目を要求する。`orchestrator/verifier/model.py:126-142`
- **(c) 放置時:** 同じ lockskip を Silo は `indeterminate`、MOCC は cycle が偶然出なければ `certified` とし、protocol 間で受理集合が非対称になる。

### 所見 A-6 — must-fix: plan の operative proof は hybrid 経路を踏まない

- **(a) 主張:** `W_LOCKED ∧ CLL-derived shadow` は lockskip/early-unlock で偽になり得るので論理的な恒真式ではない。ただし提案 control は `temp_threshold=100`、単一 thread で cold validation しか踏まず、MOCC 固有の hot/RLL/read-lock 経路を一切固定しない。
- **(b) 根拠:** `plan.md:183,207-224`。hot/RLL read は `external/ccbench/cc/mocc/transaction.cc:182-216,258-266`、hot update/delete は `:353-377,460-486`、canonical/RLL 再取得は `:736-790`。plan 自身も hot read owner assert を対象外にする。`plan.md:89-95`
- **(c) 放置時:** 温度昇格、RLL retry、read-lock 欠落だけを壊す実装が全4 control を通り、「hybrid を被覆した」という参照だけが残る。

## A-4. 正しさシグナルの構造化

### 所見 A-7 — must-fix: MOCC 固有の失敗理由が構造化されない

- **(a) 主張:** 新たに露出する `absent-read`、`reinsert-version-regression`、`hot/RLL-path` を表す record がない。既存 X も `not-locked-at-entry` / `lock-lost-before-write` の二理由だけで acquisition path を持たず、plan は JSON 化を任意扱いしている。
- **(b) 根拠:** `plan.md:175-181,295`。X parser は `(txid,key,reason)` を受けるが、core は総数と free-form notes に畳む。`orchestrator/verifier/parse.py:127-137`、`orchestrator/verifier/core.py:43-61`。JSON の typed anomaly は cycle edge 用である。`orchestrator/verifier/report.py:15-39,58-74`
- **(c) 放置時:** 温度経路、版退行、tombstone visibility のどれが壊れたかを次の variant 入力から参照できず、結果は false-green または汎用カウンタに潰れる。

## A-5. positive control の検出力

### 所見 A-8 — must-fix: W≠C control は native 版写像を壊していない

- **(a) 主張:** plan は正例も要求しているので「負例だけ」ではない。しかし正例は cold UPDATE/read が非ゼロというだけで、W-only `tid+1` 変異は parser の自己整合検査を鳴らすだけである。native tuple stamp との写像検査ではない。
- **(b) 根拠:** `plan.md:191-203,219-224`。parser は W版とC版を比較後、W版を捨て、DSG は C commit を producer 版として使う。`orchestrator/verifier/parse.py:116-126`、`orchestrator/verifier/dsg.py:61-70`

既存 Silo controls との検出力差は次のとおり。

| control | 実際に壊すもの | 根拠 |
|---|---|---|
| norw/highkey | native read validation を外し実 G2 を作る | `patches/broken-silo-norw-validation.patch:9-23`、`patches/broken-silo-highkey-validation.patch:8-36` |
| lockskip/early-unlock | native lock 獲得・保持を破る | `patches/broken-silo-lockskip-validation.patch:9-17`、`patches/broken-silo-early-unlock-validation.patch:9-16` |
| permutation erase/swap/non-SWO | write set の実体・sort 契約を壊す | `patches/broken-silo-permutation-erase.patch:9-17`、`patches/broken-silo-permutation-swap.patch:9-19`、`patches/broken-silo-sort-nonswo.patch:25-44` |
| trigger misattr | native abort 理由の構造化帰属を壊す | `patches/broken-silo-trigger-misattr.patch:9-21` |
| 提案 MOCC W mismatch | trace の W 表示だけを壊す | `plan.md:191-203` |

- **(c) 放置時:** C/W の両方を同じ誤写像にする変異、I/D reincarnation、hot/RLL、scan を壊した hook が正例・負例とも通り、検出力を過大評価する。

最低でも「CとWを同じだけ誤写像し、後続 native read が orphan になる」変異、正しい cold/hot/RLL 対照、主張対象に含めるなら I/D 対照が必要である。

## 横断 blocker

### 所見 A-9 — must-fix: D16 の一時例外は存在しない

- **(a) 主張:** 親 R-2 の「却下対象は全改変 patch 方針だけ」という区別は許可を生成しない。分類表自体が trace-hook を `izanagi-trace` branch に置き、patches README も追加開発は branch commit + gitlink 前進と明記する。
- **(b) 根拠:** `docs/decisions.md:248-275`、`patches/README.md:6-15,29-32`。一方 brief は patch 配置と gitlink 不変を同時要求する。`brief.md:54-64,86-89`
- **(c) 放置時:** patch 配置なら承認済み provenance 分類を、branch 配置なら凍結 gitlink 参照を変え、どちらでも現行受理境界の外へ出る。

残る選択肢は、明示的な一時 patch 例外を新裁定するか、gitlink/freeze の再承認後に branch へ置くか、本 wave の実装を止めるかの三つだけである。

## 親反論 R-3 の個別裁定

| 項目 | 裁定 |
|---|---|
| 1 | **誤り。** SI が簡潔なことは MOCC の正本である根拠にならない。D38 と MOCC separate-lock 構造から、C/R/W-only は弱い。 |
| 2 | **限定的に正しい。** `maxtid` と store は writePhase 内。ただし emit 前後だけでは absent/reincarnation を解決しない。`external/ccbench/cc/mocc/transaction.cc:1017-1071` |
| 3 | **観測位置は正しいが推論は誤り。** `ReadElement::tidword_` は保存版だが absent も保存しており、plan はそれを落とす。`external/ccbench/cc/mocc/include/mocc_op_element.hh:15-23` |
| 4 | **過大。** DB初期値は `(1,0)` だが transactional insert は別 overload で epoch を設定しない。`external/ccbench/cc/mocc/include/tuple.hh:74-89` |
| 5 | **誤り。** `BACK_OFF` は universal define かつ abort/leader の live 分岐。`external/ccbench/cmake/Options.cmake:13-23,60-68`、`external/ccbench/cc/mocc/transaction.cc:981-991,1085-1089` |
| 6 | **静的には支持。** file_count は変わるが verify は完全一致を要求せず、holdout violation は三軸 conjunction のみ。`orchestrator/campaign/s8b_holdout_freeze.py:270-294,345-365,683-737` |

## 親 brief 自身の誤り

### P1〜P7

- **P1:** 現行正本は S1 を non-blocking とし、S1移植と stock専用経路の択一を未決のまま残す。さらに D32 は移植着手の一歩目を catalog card と定める。`docs/phase3.md:206-212`、`docs/decisions.md:709-729`
- **P2:** write-heavy 代表という部分は正しいが、「恒等写像」は UPDATE-only に限定しなければ偽。[T-023] も条件付きである。`external/ccbench/cc/mocc/transaction.cc:891-903,1017-1063`、`docs/phase3.md:441-444`
- **P4:** AI の `qsub` は明示禁止。`docs/decisions.md:3789-3800`
- **P5:** gate待ち trace-hook の一時 patch 例外は D16 にない。`docs/decisions.md:250-275`
- **P7:** mocc 固有 CMakeLists だけでは universal `BACK_OFF` を落とすため、live 軸2本という結論は誤り。`external/ccbench/cc/mocc/CMakeLists.txt:1-10`、`external/ccbench/cmake/Options.cmake:13-23,60-68`

P3 の「そのまま移植できない可能性」と、P6 の三軸 conjunction に関する限定命題自体には反証なし。

### 段1「実測事実」

- **事実2は誤り:** 大文字 `Silo` が1件あるうえ、verifier は C/R/W だけでなく X/P/A も読む。`orchestrator/verifier/dsg.py:52-55`、`orchestrator/verifier/parse.py:127-156`
- **事実3は誤り:** 実体は `Integrity.clean()` で9項目。さらに整合した誤写像、tombstone read、版退行は列挙4カウンタだけでは fail-closed にならない。`orchestrator/verifier/model.py:101-142`、`orchestrator/verifier/dsg.py:49-114`
- **事実4は過大:** target/cache key は protocol 汎用だが、source identity の allowlist と observer-effect baseline は MOCC patch を扱えない。`orchestrator/campaign/buildcache.py:573-620`、`orchestrator/campaign/source_digest.py:62-71,299-349`
- **事実6は誤り:** bitfield 抽出は恒等でも、native version identity/order は absent read と INSERT/reinsert で verifier の前提を満たさない。`external/ccbench/cc/mocc/include/tuple.hh:14-31,74-89`、`external/ccbench/cc/mocc/transaction.cc:243-266,891-903,1017-1063`

事実1・5、および凍結コードが gitlink 前進を拒否するという事実7には、静的反証はない。

---

## 段 3 敵対レンズ B — 整合・実効性 (同上)

**NO-GO**

実装開始条件を満たしていない。独立 blocker は、D16 例外の未裁定、DW-G04 の発火条件不成立、T-088 の承認対象を変える手順、そして smoke の偽陽性を許す証拠不足である。以下は read-only の静的検査であり、pytest・build・correctness run は実行していない。

## 所見 B-1 — must-fix: 凍結ファイルの直接編集はないが、失敗時隔離が保証されていない

**(a) 主張**

平常経路だけ見れば、プランの追加先は凍結 23 件、`genome.py`、gitlink、承認定数のいずれとも重ならない。read-only の SHA-256 照合でも、現時点の 23 件は manifest 記録値と一致し、`genome.py` の現在値も freeze 内の `8e8abd…` と一致、実 gitlink も `d706650…` のままである。

しかし「1 byte も動かさない」は失敗経路を含む不変条件である。driver は caller 指定の `ccbench_dir` に `applied()` を直接掛けており、隔離 worktree を自分で生成・強制しない。引数省略時は共有 `external/ccbench` が対象になる。さらに revert の `git checkout -- .` が失敗した場合、実装自身が「working-tree が汚染されたまま」と明記して停止する。patch 以外の untracked build 残骸も clean 判定から除外される。

PBS 側も detached worktree の削除を正常終了末尾に置くだけで、失敗時の `trap` / prune 契約がない。したがってプランは「通常は動かさない」だけで、「動かし得ない」にはなっていない。

**(b) 根拠**

- 凍結集合と件数: `orchestrator/tests/test_frozen_artifacts.py:38-85,139-143`
- `genome.py` の source pin: `output/s1-freeze/known_axes_freeze.json:107-109,333-335,559-561`、`output/s8b-freeze/holdout_freeze.json:135-137,402-404`
- gitlink/pin: `orchestrator/campaign/s8b_approved.py:65-67`、`orchestrator/tests/test_s8b_approved.py:58-64`、`output/s8b-freeze/floor_protocol.json:1`
- caller 指定 tree に直接適用: `plan.md:162-173`
- `applied()` の共有 tree fallback: `orchestrator/campaign/patchharness.py:234-257`
- untracked 無視: `orchestrator/campaign/patchharness.py:14-22,125-140`
- revert 失敗時に汚染を残す: `orchestrator/campaign/patchharness.py:202-231`
- 本来の隔離 API: `orchestrator/campaign/patchharness.py:273-310`
- 正常末尾だけの worktree 削除: `plan.md:294-296`、`tools/pegasus/certify_calibration.sh:764-768`

**(c) 放置時の影響 —** revert 失敗で `external/ccbench` が tracked-dirty になれば T-088 の clean gate が受理集合を空にし、receipt と実 job ID が生成されない。

必須修正は、driver 自身が `checkout(PIN)` を所有し、共有/default tree を拒否すること、build・trace をすべてその一時領域配下へ閉じること、PBS の終了種別にかかわらず worktree remove/prune を行うことである。

## 所見 B-2 — must-fix: T-088 より先に実行すると、承認済み手番の参照値を変える

**(a) 主張**

親反論 R-3.6 の「repo scan はファイル一覧を凍結しないから解決済み」は詭弁である。確かに freeze verify は exact file count を固定しない。しかし floor launch certificate の `clean_scan_digest` は実際の repository file 一覧を preimage に含める。patch、driver、PBS script を commit すれば、T-088 receipt の `source_commit` と `clean_scan_digest` は承認時点から変わる。

さらに PBS の標準出力・標準エラーは、指定しなければ qsub したディレクトリへ戻る。プランは job stdout/stderr に結果を残すだけで `#PBS -o/-e` を定めていない。repo root から投入すれば `.o<ID>` / `.e<ID>` が `output/` 外の untracked file となり、`submit_floor.sh` が明示拒否する。

現在承認されている human turn は T-088 であり、新しい mocc smoke の qsub ではない。T-088 を先に実行するか、新 source commit・clean digest を含めて再承認を取る必要がある。

**(b) 根拠**

- 承認済み・未実行の T-088: `docs/worklog.md:637-640`
- 新規成果物と人間投入: `plan.md:149-158,191-224,280-300`
- repository file 一覧が digest に入る: `orchestrator/campaign/s8b_floor_campaign.py:1597-1639`
- qsub ログの戻り先: `docs/pegasus-runbook.md:81-106`
- floor は tracked clean、`output/` 外 untracked、未commit script を拒否: `tools/pegasus/submit_floor.sh:181-245`
- 親反論の過大主張: `parent-rebuttal.md:72-75`

**(c) 放置時の影響 —** T-088 receipt の `source_commit` / `clean_scan_digest` が承認対象と異なるか、PBS ログによって submit が rc=2 となり、承認済み job ID 取得手番が消滅する。

## 所見 B-3.1 — must-fix: lock auditor を生死実験へ混入して scope を拡張している

**(a) 主張**

brief の scope は mocc で C/R/W trace が verifier へ到達するかという生死実験一本である。それに対してプランは lock shadow、入口・保持の二検査、lockskip、early-unlock を追加し、正例を含む四ケースを合格条件にしている。これは D38 型の lock-path auditor を新 protocol へ移植する別機構であり、生死確認ではない。

親 R-3.1 の「SI 型の最小 C/R/W でよい」は、この wave の主張範囲に限れば正しい。ただし SI をテンプレートにしたことから MOCC の悲観経路まで正しいとは導けない。hot/RLL、INSERT、MQLOCK、owner proof は別の correctness package として扱うべきである。

**(b) 根拠**

- brief の実装範囲と scope 外: `brief.md:54-64`
- lock shadow と二検査: `plan.md:18-23,66-97`
- 二本の追加 broken patch と四ケース: `plan.md:205-224`
- SI の最小 hook: `external/ccbench/cc/si/transaction.cc:526-554`
- D38 の lock 固有 positive control と既知限界: `docs/decisions.md:986-1001,1023-1050`
- 親 R-3.1: `parent-rebuttal.md:59-63`

**(c) 放置時の影響 —** wave の受理集合が「C/R/W 正例＋W mismatch」の二ケースから lock auditor を含む四ケースへ勝手に狭まり、有効な最小 trace-hookまで lock 機構未完成を理由に不受理となる。

## 所見 B-3.2 — must-fix: 逆に S1 完了を名乗るには証拠層が欠落している

**(a) 主張**

manual fresh CMake 自体は buildcache gate の迂回ではない。`source_digest` の allowlist が守るのは共有 cache・campaign identity であり、binary を cache、WAL、COMMIT、fitness に入れない一回限りの correctness smoke は既存先例と同型である。この点ではプラン冒頭の「buildcache blocker」は過大で、親 R-1 は限定的に正しい。

だが親の結論も甘い。提案 driver は trace の C が非ゼロであることしか要求しない。`pipeline._run_trace()` は C 行数を返す一方、CCBench stdout の `commit_counts_` を返さないため、「実 commit N 件のうち一件だけ hook が出した」実装も verifier がその一件を整合的と見れば通る。TRACE=1 しか build せず、TRACE=0 symbol zero も検査しない。job 出力も build argv と verifier 結果だけで、pin、hook/broken patch hash、binary hashを束縛しない。

したがって本 wave が主張できる上限は、「正確な pin と明示 workload における cold-OCC・1 thread の一回で、非空 C/R/W が verifier に受理され、W-version 故障が拒否された」という prototype feasibility までである。mocc 全経路の correctness、S1 完了、cross-protocol 比較成立は主張できない。

**(b) 根拠**

- manual build 案: `plan.md:145-185`
- manual broken build の先例: `orchestrator/campaign/s5_permutation_coverage.py:119-180`
- allowlist の目的: `orchestrator/campaign/source_digest.py:299-335`
- buildcache の identity・TRACE=0 symbol gate: `orchestrator/campaign/buildcache.py:573-620`
- C 行数のみ返し stdout を捨てる: `orchestrator/campaign/pipeline.py:167-194`
- `commit_counts_` を解析する既存実装: `orchestrator/campaign/s2_verify_calibration.py:81-91,103-141`
- CCBench commit 集計: `external/ccbench/common/result.cc:48-49`、`external/ccbench/include/ycsb.hh:161-167`
- 提案の合格条件と出力: `plan.md:177-203,294-295`
- T-023 完了証拠: `output/insights/2026-07-19_backlog-triage.md:341-350,1806-1810`
- 性能標本が必要とする pipeline/COMMIT 証拠: `docs/phase3-main-experiment.md:341-345`

**(c) 放置時の影響 —** 部分的にしか C を出さない hook、または TRACE=0 に symbol を漏らす hookが「S1 成功」と偽受理され、完了証拠集合の commit-count equality・observer-effect・provenance が欠落する。

cross-protocol headline まで進むには、別途、S1 と stock-only 経路の択一、承認 protocol 集合、`SPACES` 登録、protocol/contention 別 calibration と between-run floor、pipeline/WAL/COMMIT 経由の certified 標本が必要である。`docs/phase3.md:206-212,290-299`、`docs/phase3-main-experiment.md:19-31,57-63`

## 所見 B-4 — must-fix: out-of-tree trace-hook は D16 の実質改訂である

**(a) 主張**

brief P5 と親 R-2 の「単発・承認待ちなら一時 patch は別物」という区別は成立しない。D16 は行き先を採否段階ではなく改変の性質で分類し、trace-hook を `izanagi-trace`、意図的 broken variant を patch と明記している。採用構造も trace branch commit と parent gitlink 前進まで含む。

D18/D20 が patch を追加した理由は、未確定の性能 variant／診断計器であり、default が stock と同一だからである。verifier 入力を新設する trace-hook はこの二類に該当しない。「gate 待ち」という lifecycle だけで分類を読み替えるのは D16 の実質改訂である。

現行 D16 に従って branch と gitlink を前進すれば T-088 の pin gate に衝突する。一時 patch にするなら decisions と `patches/README.md` に、単発例外、campaign 非流入、期限、昇格条件を明記したユーザー裁定が必要である。

**(b) 根拠**

- 性質別分類と trace branch: `docs/decisions.md:248-258`
- branch を選んだ理由、broken patch 死守: `docs/decisions.md:262-266`
- 採用構造と gitlink 前進: `docs/decisions.md:268-275`
- D18 の inert 性能 variant: `docs/decisions.md:299-317`
- D20 の inert 診断計器: `docs/decisions.md:341-343`
- patch 階層の正本: `patches/README.md:6-32`
- 親の例外論: `parent-rebuttal.md:42-55`
- floor gitlink gate: `orchestrator/campaign/s8b_floor_campaign.py:391-397`

**(c) 放置時の影響 —** patch 案は現行 decision 上の非準拠参照となり、branch 案は実 gitlinkを承認 SHA から動かして `floor_protocol.ccbench_pin` と承認定数の受理集合を空にする。

## 所見 B-5 — nit: PBS の環境理解は概ね整合するが、smoke の資源要求が未導出

**(a) 主張**

ログインノードの g++ を計算ノード依存と誤認する欠陥はプランにはない。compiler path/version は PBS job 内で再取得し、gflags/glog は pinned source から `/scr` に static buildする。`PBS_JOBID` の `:` 置換、`-b 1`、依存 prefix も既存手順と整合する。

単独性確認を追加するなら PBS で割り当てられた計算ノード上で行うべきだが、correctness-only smoke で throughput を受理値にしない限り pgrep の省略は blocker ではない。env contract、calibration、floor も throughput を成果物にしない本 waveには不要である。

残る nit は walltime 2 時間を certification job からコピーしただけで、四 build の上界から導出していない点である。既存 policy は smoke を 10 分、certification を 2 時間として区別している。

**(b) 根拠**

- 提案 PBS: `plan.md:280-300`
- compute node 上の pgrep と throughput 境界: `docs/pegasus-runbook.md:245-257`
- job ID、`/scr`、gflags/glog: `docs/pegasus-runbook.md:298-304`
- compute node 内での compiler 解決: `tools/pegasus/certify_calibration.sh:343-357`
- dependency build: `tools/pegasus/certify_calibration.sh:359-509`
- smoke/certify walltime の区別: `tools/pegasus/policy.json:5-8`

**(c) 放置時の影響 —** 過大 walltime は queue/resource 消費か無結果を招くが、correctness の受理値を偽って変えないため nit である。

## 所見 B-6.1 — must-fix: DW-G04 の発火条件は false

**(a) 主張**

brief P1 は親の provisional 裁定であり、DW-G04 が要求する「発火済み artifact path または measurement ID」ではない。S1 は現状 non-blocking、T-023 の `P_S1` と `P_mocc` は双方 false、ユーザー裁定も未済である。

したがってこの wave は現時点では設計メモまでしか許されない。D16 の置き場だけ解決して実装へ進むこともできない。

**(b) 根拠**

- DW-G04: `docs/dev-wave/core.md:52-55`
- S1 の現行 gate: `docs/phase3.md:206-212`
- T-023 の発火条件: `docs/phase3.md:441-444`
- predicate=false・未裁定: `output/insights/2026-07-19_backlog-triage.md:330-352`
- brief 自身が P1 を攻撃対象と定義: `brief.md:76-80`

**(c) 放置時の影響 —** false の条件付きタスクが「実装済み」へ移され、T-023 台帳の状態・参照と承認済み T-088 の実行順がユーザー裁定なしに変更される。

## 所見 B-6.2 — must-fix: 「100 行 driver」は算術上の偽装になっている

**(a) 主張**

プランは import、build、verify、四 control、cleanup だけでちょうど 100 行を使い切っている。この予算には、隔離 worktree の強制、CLI と compiler path 検証、C count equality、TRACE=0 build/symbol check、patch/binary hash、失敗時 cleanupが入っていない。

さらに成果物全体は hook patch、三本の broken patch、Python driver、PBS wrapperである。既存機構への SPACES/pipeline 恒久配線は避けているものの、四ケース lock auditor は「最安の一回限り driver」ではない。lock 系を別 package に切り離さなければ DW-G01 を満たさない。

**(b) 根拠**

- DW-G01: `docs/dev-wave/core.md:37-40`
- 100 行を使い切る予算: `plan.md:151-158`
- 四 control: `plan.md:187-224`
- PBS wrapper: `plan.md:280-300`

**(c) 放置時の影響 —** 二ケースの生死確認が四ケース・複数恒久 patch の機構受理へ拡張され、wave の受理集合と実装量が DW-G01 の最安条件から外れる。

## 親反論の採否

- **R-1: 限定採用。** manual fresh build は cache/COMMIT/WAL/fitness に流入させない限り gate 迂回ではない。ただし full S1 の provenance と completeness の代替にはならない。`parent-rebuttal.md:7-40`

- **R-2: 却下。** 「単発・一時」は D16 の分類軸ではない。例外採用にはユーザー裁定と decision 記録が必要。`parent-rebuttal.md:42-55`、`docs/decisions.md:248-275`

- **R-3.1: life/death に限り採用。** SI 型 C/R/W は最小 smoke に十分だが、MOCC の serializable／lock 経路一般を証明しない。`parent-rebuttal.md:59-63`

- **R-3.2〜4: 静的には支持。** `maxtid`、保存 read version、genesis `(1,0)` の選定はソースと整合する。`external/ccbench/cc/mocc/transaction.cc:1017-1071`、`external/ccbench/cc/mocc/include/mocc_op_element.hh:15-23`、`external/ccbench/cc/mocc/include/tuple.hh:74-82`

- **R-3.5: 誤り。** `BACK_OFF` は universal default であり MOCC の abort/leader work に実分岐を持つため、live 軸を二つだけとする主張は欠落している。`external/ccbench/cmake/Options.cmake:13-23,60-68`、`external/ccbench/cc/mocc/transaction.cc:981-991,1085-1089`

- **R-3.6: 却下。** exact file count は固定されないが、実ファイル一覧は launch digest に入り、PBS ログは T-088 submit を直接拒否させる。`parent-rebuttal.md:72-75`、`orchestrator/campaign/s8b_floor_campaign.py:1623-1639`

## 裁定パッケージ候補

1. **D16 prototype 例外**  
   一回限りの trace-hook patchを許すかを裁定し、許すなら campaign/cache 非流入、期限、昇格先、削除条件を decisions と `patches/README.md` に記録する。拒否なら本 wave は実装しない。

2. **T-088 優先順**  
   現在の承認済み source state で T-088 を先に実行するか、新規ファイル追加後の `source_commit` / `clean_scan_digest` を再承認するかを選ぶ。PBS ログは `output/` 配下へ明示 routingする。

3. **最小 trace-hook smoke**  
   scope は SI 型 C/R/W、正例、W-version mismatch の二ケースだけとする。driver が隔離 worktreeを所有し、C行数と `commit_counts_` の一致、pin/patch/binary hashを残す。

4. **T-023 完了 package**  
   発火後に visible/invisible・hot/cold path、commit equality、duplicate/orphan/missing=0、TRACE=0 symbol zero、committed provenanceを実装する。これは今回の生死実験とは別である。

5. **MOCC lock coverage package**  
   RWLOCK non-INSERT の入口／保持、lockskip／early-unlockを別 waveで扱う。INSERT、hot-read owner、MQLOCKはさらに別裁定とする。

6. **本物の cross-protocol package**  
   S1 対 stock-only 経路の択一、protocol集合とSPACES、protocol/contention別 calibration・between-run floor、pipeline/WAL/COMMIT、cross-run統計をまとめて裁定する。今回の correctness smoke に env contract・floor・throughputを混入させない。