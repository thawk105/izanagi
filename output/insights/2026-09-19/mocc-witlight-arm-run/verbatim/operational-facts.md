# 親が段 0〜1 で実測した運用事実 (2026-09-19 21:30〜21:55 JST、wave dev-wave-mocc-witlight-arm-run)

数値・行番号は現物から取った。推測は「未実測」と書く。

## 1. runner v5 (`t2779_probe-v5.py`、sha256 7907a545…、785 行) の要点

- `PIN = "e9e477ca1b55348ab4530de0b1cf663ce4555290"` (28 行)。
- `run_one` 335〜338: discriminator を回す条件は `binding["witness"]` が true かつ `binding["pin"] == PIN`。
  それ以外は `{"status": "not-run", "reason": "witness-off" | "pin-outside-t1943"}`。
- `validate_arms` 388〜416: arm の必須 key = `name` / `pin` (40 hex) / `patches` (絶対 path の list) / `witness` (bool)、任意 = `observational_only` (bool)、`defines` (`CCBENCH_*` の既知 key → `-?[0-9]+|ON|OFF`)。他 key は拒否。
- `run` 543〜561: arm ごとに `checkout(pin, base_dir=<worktree>/external/ccbench)` → `assert_pinned_clean` → `patches` を順に `apply_patch` (各 patch は `patch_files(patch) == ["cc/mocc/transaction.cc"]` を要求、適用前後で patch の sha 不変を要求) → `source_file_sha256` を binding に記録。
- `round_order(names, cycle)` 435〜437: `offset = (cycle-1) % len(names)` の単純回転。4 arm × 15 round では各 arm の位置回数が 4/4/4/3 (round 13〜15 が位置 1〜3 に偏る)。
- build は arm ごとに別 dir (`scratch/build-<arm>`)、同 source・同 defines の arm でも別 build。warmup は `names[0]` の source で `masstree_build` だけ。
- witness on の走は env `IZANAGI_MOCC_G2_WITNESS=1` + `IZANAGI_MOCC_G2_WITNESS_DIR=<raw>/witness` (299〜300)。
- G2 (cycle 正) の走は trace-manifest を作り生 trace を退避、witness on なら witness-manifest も作って discriminator を回す。

## 2. discriminator (`orchestrator/campaign/mocc_g2_discriminator.py`、repo 現行)

- pin を e9e477ca に固定していない。`_validate_manifest` は `source_oid` が 40 hex であること、trace-manifest と witness-manifest の `source_oid` / `binary_sha256` / `workload` が一致することを要求する (130〜136、485〜487)。
- witness 行の文法: `H <marker> 1`、`L <reader_txid> <key_hex> <epoch> <tid> (T <producer> | G -)`、`S <writer_txid> <key_hex> <epoch> <tid> <stored_producer>` (parse 330〜390)。
- `limits.write_store_order_verified_beyond_post_store_token: False` (T-2779 §3 の引用、本 wave 未再確認 → 段 2 で行番号を確認せよ)。

## 3. e9e477ca の `cc/mocc/transaction.cc` (逐語 `mocc-transaction-e9e477ca.cc`、sha256 79982b23…)

- include: 1〜17。`#if TRACE` 内は `"../../include/trace.hh"` の 1 行だけ (e9e477ca の commit message: 「Remove witness-only standard-library include lines … preserves the exact TRACE=0 include correspondence required by the identity checker」)。
- `include/transaction.hh` 3 行目が `#include <vector>`、31〜42 行で `read_set_` / `write_set_` / `CLL_` は `vector<…>`。`include/trace.hh` は `<atomic> <cstdint> <cstdlib> <fstream> <ios> <string> <unordered_set>` を include。
- witness helper (`#if TRACE` 23 〜 `#endif` 114、無名 namespace 24〜113): `izanagi_mocc_g2_enabled` (32〜、env を 1 回だけ読む static)、`izanagi_mocc_g2_stream` (47〜、thread_local ofstream)、`izanagi_mocc_g2_decode` (68〜、size 検査 → 8 byte memcpy → magic 比較)、`izanagi_mocc_g2_stamp` (78〜)、`izanagi_mocc_g2_emit_lineage` (84〜、L 行)、`izanagi_mocc_g2_emit_post_store` (100〜、decode 失敗で `std::abort()`、S 行を ofstream へ書式化)。
- `unlockCLL()` 1094〜1113 (CLL_ だけを解放して clear、`CLL_.clear()` 1112)。
- `writePhase()` 1115〜1213: `#if TRACE` ブロック 1134〜1157 (`izanagi_txid` 取得 1135、C 行、L 行 loop、W 行 loop)、write loop 〜1201 (UPDATE: stamp 1167 → memcpy、publish `__atomic_store_n` 1195〜1196、post_store 呼出 1199)、E 行 1204、`unlockCLL()` 1207、`RLL_.clear()` 1208、`gc_records()` 1209、`read_set_.clear()` 1210、`write_set_.clear()` 1211、`node_map_.clear()` 1212。`commit()` は 1215〜 (失敗分岐は 1220 の `return false`)。`abort()` は 1059〜 (`unlockCLL()` 1069)。1247〜1253 は `reconnoiter_end()` (訂正: 段 3 レンズ A N1、初稿の「1248 = abort 経路」は誤り)。

## 4. X/P 計装 patch (`instr-mocc-lock-coverage.patch`、repo `patches/`、sha256 e9e65b78…、不変)

- hunk: `@@ -11,9 +11,11 @@` (`#if TRACE` 内に `#include <set>` 追加 + `#line 17`)、`@@ -987,7 +989,31 @@` (validation)、`@@ -1154,7 +1180,26 @@` (writePhase の `#if TRACE` ブロック末尾に lock 検査 loop + `#line 1158`)、`@@ -1165,7 +1210,12 @@` (stamp 直後に `lock-lost-before-write` + `#line 1169`)、`@@ -1184,6 +1234,13 @@` (DELETE 側 + `#line 1187`)、`@@ -1192,6 +1249,14 @@` (publish 直前に `lock-lost-before-publish` + `#line 1195`)。
- 1154 hunk の文脈行 = 1154〜1156 (`thid_, izanagi_txid, izanagi_trace::key_to_hex(we.key_), op,` / `maxtid.epoch, maxtid.tid);` / `}`) と 1157〜1160 (`#endif` / 空行 / `// write (record, commit-tid)` / `for (auto itr = write_set_.begin(); …`)。
- X/P は out-of-tree patch なので OID 型の identity checker の対象外。TRACE=0 identity は driver `s3_mocc_lock_coverage._trace0_record` の binary objdump text 同一性 (`trace0_text_identical`) で担保 (D1686)。

## 5. `tools/check_trace0_preprocess_identity.py` (hook branch commit の identity 検査)

- CLI: `--repo <submodule worktree> --old <40hex> --new <40hex> --cxx <compiler>` (730〜733)。`--old` は `--new` の祖先であることを要求 (記憶 ccbench-pin-advance-materials-facts、T-2756 実測)。clang は判定不能、GCC で回す。
- `_compare_file` 537〜555: old/new の include 行文字列 (順序込み) が不一致なら、唯一の例外 = `cc/mocc/transaction.cc` の `#include "../../include/trace.hh"` 1 行の追加 (`_mocc_trace_include_addition_index`、421〜447) 以外は `CheckError("include 行文字列（順序込み）が不一致")`。**`#include <vector>` の追加はこの検査で拒否される。**
- pilot (`tools/pegasus/mocc_trace_pilot.sh` 1900〜1901) は `--old $BASE_OID --new $NEW_OID` = policy の `511c9538` → `e9e477ca` で回す。

## 6. 検出力 (親が計算、独立・同率 Bernoulli、等標本、片側 Fisher α=.05、on 率 < off 率の方向)

| K/arm | off 0.0417 対 on 0 | off 0.058 対 on 0 | off 0.119 対 on 0 | off 0.0417 対 on 0.014 |
|---|---|---|---|---|
| 56 | 0.084 | 0.224 | 0.812 | 0.041 |
| 60 | 0.105 | 0.268 | 0.856 | 0.050 |
| 120 | 0.564 | 0.831 | 0.999 | 0.199 |

K=60 で on=0 のとき、off の件数 k と片側 p: 1→0.500、2→0.248、3→0.122、4→0.059、5→0.029、6→0.014、7→0.0065。
0.0417 = T-2779 通常 arm 5/120、0.058 = T-2774 witness off 合算 7/120、0.119 = T-1892 5/42 (ユーザー決定の「80%、各 arm ≥56」の根拠 = T-2774 段 3 レンズ B はこの率で計算)。

## 7. 環境と先例

- wave worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-mocc-witlight-arm-run` (main a99425b66、clean、locked)。submodule git dir は worktree 専用 (`.git/worktrees/<wt>/modules/external/ccbench`、alternates なし)、`e9e477ca^{commit}` 解決、HEAD 511c9538、local branch は `izanagi-trace-t816-fn2` だけ。
- 主 checkout の submodule (`/work/1/SFC/tanab/izanagi/.git/modules/external/ccbench`) には `izanagi-t1943-mocc-g2-readfrom-witness` (先端 e9e477ca) があり、reflog は T-1943 wave が worktree の module dir から `git fetch <dir> refs/heads/X:refs/heads/X` で持ち込んだことを示す。GitHub 未 push (2026-09-17 実測)。
- T-2779 の実走: 1 block 90 走 (3 arm × 30 round) = Elapse 2222〜2233 秒 (build 3 + warmup 込み)。走 3.07 秒、verify 10.5〜22.7 秒。4 node 同時投入 (wave worktree + `.codex/worktrees/t2779-node{2,3,4}`)、generic dispatch walltime 02:30:00。
- 受入は門番契約 (leaders ≤ 1 ∧ load ≤ 60 + jitter)。
