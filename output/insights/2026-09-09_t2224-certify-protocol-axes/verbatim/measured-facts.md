# [T-2224] 親が段 1〜2 で実測した事実 (2026-09-09、login node pegasus02)

すべて親が自分で走らせた実測である。**これらの実測とその一般化も攻撃対象である。**
「実測」と書いてあっても、母集合・条件・一般化の射程が正しいとは限らない。

## M1. 4 protocol とも ycsb 実行体はビルドできる (既定値での生死実験)

CCBench pin `511c9538` を 1 回 configure (`-DCMAKE_BUILD_TYPE=Release -DENABLE_SANITIZER=OFF
-DCCBENCH_TRACE=0 -DCMAKE_PREFIX_PATH=/work/1/SFC/tanab/izanagi-a2-deps`) し、rc=0。
その後 4 target を順にビルドして全部 rc=0:

| protocol | build rc | 所要 | 実行体 |
|---|---|---|---|
| silo | 0 | 33 秒 | `<build>/cc/silo/ycsb_silo.exe` |
| mocc | 0 | 8 秒 | `<build>/cc/mocc/ycsb_mocc.exe` |
| tictoc | 0 | 6 秒 | `<build>/cc/tictoc/ycsb_tictoc.exe` |
| cicada | 0 | 6 秒 | `<build>/cc/cicada/ycsb_cicada.exe` |

**この実測は「Options.cmake の既定値のまま」であり、protocol ごとの軸を非既定値にした
ビルドは含まない。** 依存の gflags/glog は既存 install の再利用、masstree/mimalloc は
login node の network 経由の FetchContent。計算ノードでの再現は測っていない。

## M2. 軸がコンパイラへ届くか (configure だけで `flags.make` の実 define を読む)

各 protocol の `SPACES` 軸を **すべて既定と違う値**で要求し、生成された
`<build>/cc/<p>/CMakeFiles/ycsb_<p>.exe.dir/flags.make` の `CXX_DEFINES` を読んだ。

- silo: 要求 `BACK_OFF=0, NO_WAIT_LOCKING_IN_VALIDATION=0, NO_WAIT_OF_TICTOC=1, WAL=1`
  → 実 define も同じ 4 値。未使用変数警告なし。**4/4 到達**
- mocc: 要求 `BACK_OFF=0, KEY_SORT=1, TEMPERATURE_RESET_OPT=0` → 実 define も同じ。**3/3 到達**
- tictoc: 要求 `BACK_OFF=0, NO_WAIT_LOCKING_IN_VALIDATION=0, NO_WAIT_OF_TICTOC=1,
  PREEMPTIVE_ABORTS=0, TIMESTAMP_HISTORY=0` → 実 define も同じ。**5/5 到達**
- cicada: 要求 `BACK_OFF=0, INLINE_VERSION_OPT=0, INLINE_VERSION_PROMOTION=0, REUSE_VERSION=0,
  WRITE_LATEST_ONLY=1` → CMake が
  「Manually-specified variables were not used by the project: CCBENCH_INLINE_VERSION_OPT」
  と報告。実 define の `INLINE_VERSION_OPT=0` は cicada 専用 cache 変数
  `CCBENCH_INLINE_VERSION_OPT_CICADA` の既定 0 由来。**4/5 到達**

**この実測は configure までで、ビルドの成否は見ていない。**

## M3. cicada は `INLINE_VERSION_OPT=1` でビルドできない

正しい cache 名 `-DCCBENCH_INLINE_VERSION_OPT_CICADA=1` を渡すと実 define は
`-DINLINE_VERSION_OPT=1` になるが、**build rc=2**。
`cc/cicada/include/transaction.hh:207` の `write(s, key, TupleBody(ver->body_));` が
POSIX の `write(int, const void*, size_t)` に解決され
`error: cannot convert 'Storage' to 'int'`。既定 0 のため誰も踏んでいなかった上流の死にコード。

## M4. 条件関門は現行 pin では silo でも赤 (最重要)

`tools/pegasus/certify_calibration.sh:380-394` の `run_condition_gate` と同じ形で
`orchestrator.campaign.condition_meaning_gate` を実走した。source-root は pin の detached
worktree、stock-root は `external/ccbench`、silo の configure-arg を渡した。

結果: **rc=2、`admitted=false`、2 アームとも red。**

- `supply-effectuation` / `configure-failed`:
  evidence の detail が `CMake Warning: Manually-specified variables were not used by the
  project: CCBENCH_BACKOFF_FIXED`
- `runtime-meaning` / `materialized-branch-invalid`:
  detail が `unique BACKOFF_FIXED conditional is unavailable`、
  witness_id `backoff-fixed-finite-pointwise`

原因の読み: `CCBENCH_BACKOFF_FIXED` は `patches/silo-backoff-fixed.patch` が
`cmake/Options.cmake` と `include/backoff.hh` へ供給する define である。launcher は
`certify_calibration.sh:534` で素の detached worktree を作るだけで patch を materialize しない。
`condition_meaning_gate.py` の `_DEFINE_SPECS["BACKOFF_FIXED"]` は
owner=`cc/silo/transaction.cc`、target=`ycsb_silo.exe`、patch=`patches/silo-backoff-fixed.patch`、
`inert_values=("-1",)` で silo 固定。

`run_condition_gate` は `set -Eeuo pipefail` 下の裸の関数呼び出し
(`certify_calibration.sh:545`) なので、赤は job を rc=2 で中断する
(bash の同型スニペットで正例確認済み: 後続行に到達しない)。

**一次資料の裏取り**: `output/env/pegasus/calibration/job-staging/` の認定 attempt 12 件すべてに
`condition-gate.jsonl` が存在しない。`calibrate_rc=0` の 2 件 (`0:867876.nqsv` / `0:892707.nqsv`) は
関門導入 commit `0218acc61` より前である。**この関門は認定経路で一度も実走していない。**

## M8. `-DCCBENCH_BACKOFF_FIXED=-1` は現行 pin では bit 単位で無効 (段 3 起動後に追加)

build path を固定 (`$R/samepath-build` を毎回 rm して作り直す) して silo を 3 回ビルドした。

| 走 | 渡した flag | binary sha256 |
|---|---|---|
| A | `-DCCBENCH_BACKOFF_FIXED=-1` あり | `871b99766e71f3121285b0bbc6bb4ad99ea8cdc5d450da024664e8b4b952dec2` |
| B | なし | 同上 (完全一致) |
| A2 | あり (A の再現性対照) | 同上 |

A2 が A と一致するので「同一 path でのビルドは再現する」が成り立ち、A=B は再現ノイズに
埋もれた偽の一致ではない。別 path で作った先行実測では hash が違ったが、それは build dir の
path が実行体へ埋まるためで、flag に帰属しない (この点は先に誤読しかけた)。
実 compile define (`CXX_DEFINES`) の diff も空だった。

**含意**: (R1)「この flag を渡すのをやめる」は、認定バイナリを 1 bit も変えない。
`condition_meaning_gate.py` の `inert_values=("-1",)` という宣言とも整合する。
ただし genome canonical 文字列からは `BACKOFF_FIXED=-1` が消えるため、
将来 patch 入り source で測る系列との genome 同一性は別問題として残る。

## M9. 実機の成功 job も同じ未使用変数警告を出していた (一次資料)

`output/env/pegasus/calibration/job-staging/0:892707.nqsv/configure.stderr` の全文は

```
CMake Warning:
  Manually-specified variables were not used by the project:

    CCBENCH_BACKOFF_FIXED
    IZANAGI_GFLAGS_SRC_HEAD
    IZANAGI_GLOG_SRC_HEAD
```

この job は `calibrate_rc=0` で認定を完走している。つまり launcher は**以前からこの未使用変数を
渡し続けており**、当時は条件関門が存在しなかったので通っていた。M4 の読み (patch 未供給のまま
patch 由来 define を宣言している) は、login での再現だけでなく**実機の成功 job の一次資料でも
裏付けられる**。

同 job の `configure.stdout` (41 行) と `build.stdout` は masstree の
`bootstrap + configure + make + ar` が計算ノードで完走したことを示す。したがって計算ノードでも
CCBench の configure/build は成立する。

## M10. 同じ関門欠陥の独立 2 例目である (先行記録との突き合わせ)

wave 中に main が 5 commit 進み、そのうち
`output/insights/2026-09-09_t2397-a1-pilot-attempt-0003/README.md` (commit `91f034a0e`) が
**同じ条件関門による拒否を別 driver で記録していた。**

- 同一: §6.2 の `runtime-meaning` 赤。理由 code `materialized-branch-invalid`、detail
  `unique BACKOFF_FIXED conditional is unavailable`。原因も同じで、
  marker `silo-backoff-magnitude` は `patches/silo-backoff-fixed.patch` 側にあり、
  pin された CCBench の `include/backoff.hh` (3623 bytes) には出現数 0。
  同 insight は「§6.1 を直しても runtime-meaning は赤のままである」と明記している。
- **したがって M4 の runtime-meaning 部分は新規発見ではなく、独立 2 例目である。**
  driver は `orchestrator/campaign/paper_story_a1_paired.py` (A-1) と
  `tools/pegasus/certify_calibration.sh` (認定) で異なる。`DW-G03` の独立 2 例を満たす。
- 相違: `supply-effectuation` 赤の原因が違う。A-1 は関門へ configure 引数を 1 つも渡さず
  gflags が見つからない (F580 の 3 例目)。本 wave は引数を正しく渡した上で
  「`CCBENCH_BACKOFF_FIXED` は project に使われていない」で落ちる。**供給されていないこと自体が
  露出している**点が新しい。
- 認定経路に固有の新規事実は次の 2 点である。
  (i) 認定 attempt 12 件すべてに `condition-gate.jsonl` が無く、この関門は認定経路で一度も実走していない。
  (ii) M8 により、この flag を渡すことは現行 pin では bit 単位で無効である。

## M5. 凍結 pin 閉包

- `certify_calibration.sh` の whole-file sha256
  `45fbaf5b05c1f7db74a3f11ccde715917c3570c5bd588528b93f2c8f581ff2b8` を焼いた成果物は
  tools / orchestrator / docs / hooks / output のいずれにも 0 件 (output は grep rc=1 で完走確認)
- path key の pin: runbook の site 表、`test_hooks.py` の registry 表、`test_check_docs.py` の
  site 表。いずれも path と class を pin するだけ
- 本文 literal pin: `test_pegasus_calibration_workload.py` と `test_pegasus_tools.py` に多数

## M6. 登録済み較正 record

`output/env/pegasus/calibration/registered/` に 2 件。どちらも `genome` 欄なし、
`workload = {ycsb_rmw: "0", ycsb_rratio: "50", ycsb_zipf_skew: "0.9"}`、`threads=48`、`env_tag=pegasus`。

## M7. 編集面の重複

全 222 worktree を走査。`.codex/worktrees/rejected-witness-merge` が
`tools/pegasus/submit_certify.sh` と `orchestrator/tests/test_pegasus_calibration_workload.py` を
`M` で持つが、両 file とも現行 main と sha256 一致。競合編集ではない。
