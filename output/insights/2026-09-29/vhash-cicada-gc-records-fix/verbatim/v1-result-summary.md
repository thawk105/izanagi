# 確認走行 V1 の結果 (job v1、request 36317.nqsv、bnode005、2026-09-29 23:25:24〜23:27:42 JST、Elapse 143 秒、起動器 rc=1 = FIX_F_ASAN の期待外のため)

原本: runs/v1/result-CUSTOM.json、raw = runs/v1/raw/CUSTOM/。起動器 stage5/launch_gcfix_run.py (sha256 62f23a09…)、spec-v1.json。計測木 gcfix-m1 (main 8fe87f852)。
fix patch = stage5/fix-cicada-gc-records.patch sha256 2c9cb880… (= wave commit 278daafee の patches/fix-cicada-gc-records.patch と同一 bytes)。

| build | run | 結果 | 事前登録の期待 | 判定 |
|---|---|---|---|---|
| F_T0 (F 無 patch) | F×t4×10 | 10/10 rc=1、gc_records の ERR | t4 で既知 ERR ≥ 1 | 満たす |
| F_T0 | F×t8×10 | 10/10 rc=1、gc_records の ERR | t8 で既知 ERR ≥ 1 | 満たす |
| FIX_F_T0 (F + fix) | F×t4×10 | 10/10 rc=0 | 全 rc=0 | 満たす |
| FIX_F_T0 | F×t8×10 | 10/10 rc=0 | 全 rc=0 | 満たす |
| C_FIX_T0 (pin C + fix) | F×t4×3 | 3/3 rc=0 | 全 rc=0 | 満たす |
| ONELEVEL_F_T0 (変異 M2) | F×t4×10 | 10/10 rc=1、gc_records の ERR | ERR ≥ 1 なら KILLED | KILLED |
| ONELEVEL_F_T0 | F×t8×10 | 3/10 rc=1 (ERR)、7/10 rc=0 | 同上 | KILLED |
| FIX_F_ASAN (F + fix、Debug・ASan) | F×t4×3 | 3/3 rc=1、AddressSanitizer: heap-use-after-free | rc=0 かつ ASan 報告 0 | **満たさない** (下記、修理と無関係の既存欠陥) |

ASan の報告 (3 件とも同じ形): WRITE of size 8 at `TxExecutor::writeSetClean()` (include/transaction.hh:345、`rcdptr_->continuing_commit_.store(0)`) ← `TxExecutor::abort()` (transaction.cc:754)。freed by 同じ `abort()` の transaction.cc:750 (`delete we.rcdptr_`、INSERT した tuple の削除)。allocated by `TxExecutor::insert()` (transaction.cc:313) ← insert_history (Payment) 2 件・insert_neworder (NewOrder) 1 件。
= abort() が insert した tuple を delete した後、writeSetClean() が同じ write set 要素の tuple に書き込む use-after-free。gc_records とも delete とも無関係で、insert を含む tx が abort すれば起きる (pin C の stock でも同じコード)。ASan は最初の報告で止まる (-fno-sanitize-recover) ので、gc_records 経路の寿命の検査はこの走行では判定不能。
