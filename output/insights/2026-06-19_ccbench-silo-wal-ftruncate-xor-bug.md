# CCBench silo/ss2pl WAL: `ftruncate(10 ^ 9)` の XOR バグ (gcc-13 -Werror で build fail + 実害)

**発見:** Phase 2 P2-0 (silo 最適化フラグ全探索の verifier 大規模 sanity)。`WAL` フラグを
探索空間に入れて初めて WAL コードパスがコンパイルされ、露呈した。**パラメータ全探索の価値**
の最初の実例 (網羅したからこそ普段コンパイルされない経路のバグが出た)。

## 症状

`WAL` を有効 (`-DCCBENCH_WAL=1`) にして silo をビルドすると gcc-13 `-Werror` で fail:

```
cc/silo/ycsb_silo.cc:47:34: error: result of '10 ^ 9' is 3; did you mean '1e9'? [-Werror=xor-used-as-pow]
   47 |         trans.logfile_.ftruncate(10 ^ 9);
```

silo 12 genome 全探索のうち **WAL=1 の 6 genome 全て**が同一原因で build-error。

## 根本原因

`10 ^ 9` は C++ で **XOR 演算 = 3** (べき乗ではない)。意図は明らかに **10億 (1e9) バイト =
1GB のログファイル事前確保** (`ftruncate` で WAL ログを先に伸ばし、commit ごとのファイル拡張
syscall を避ける典型最適化)。

**`-Werror` を外しても実害が残る:** `ftruncate(3)` は 3 バイトのログファイルを作る。事前確保が
効かず、WAL 有効時の性能計測が歪む (ログ拡張コストが毎 commit 乗る、または小さすぎるログ)。
= 単なる -Werror の厳格さの問題ではなく **機能バグ**。WAL の性能を測る実験では特に致命的。

## 影響範囲 (5 箇所、全て同一 `10 ^ 9`)

- `cc/silo/ycsb_silo.cc:47`
- `cc/silo/sbomb_silo.cc:46`
- `cc/silo/tpcc_silo.cc:46`
- `cc/silo/bomb_silo.cc:47`
- `cc/ss2pl/bomb_ss2pl.cc:45`

いずれも `#if WAL` ガード内。WAL=0 (default) ではコンパイルされないため、過去の全ビルド
(worklog タスク0 / D16 の 34 binary、いずれも WAL off) では露呈しなかった。

## 修正案

`10 ^ 9` → `1000000000` (or `1'000'000'000` / `static_cast<off_t>(1e9)`)。5 箇所同一。
gcc-13 (CI と同じ。ccbench CLAUDE ハードルール4「Werror promotion 系は GCC 13 で確認」) で
-Werror クリーンを確認すること。`ftruncate` の引数型 (`off_t`) に注意。

## 還元判断: **完了 (PR #116、ccbench master にマージ済み)**

**追記訂正 (2026-07-15、ユーザー確認):** 本節の初版では master 還元を「ユーザー確認待ち」と
していたが、その後ユーザーが修正ブランチを push し、PR #116 が master にマージされた
(`10 ^ 9` → `1000000000`、5 箇所、origin/master `2574412`)。以下の 2026-06-20 対応記録にある
「master 還元は後日人間が判断」と、その前提となった当初の還元判断は、当時の状態を保存した履歴で
あり、現行状態ではない。

**当初の還元判断:** Izanagi 非依存の CCBench 本物のバグ。D16 の分岐では「pinning バグ修正→submodule master 還元」
の先例に倣い **master 還元候補** (trace-hook のような izanagi 専用計装ではなく、誰にとっても
正しい修正)。izanagi-trace ブランチは master を内包するので、master に修正を入れて izanagi-trace
に反映する形が筋。**push は人間** (この環境に ccbench push 認証なし)。CLAUDE.md「勝手に上流 PR
を出さない」。

**対応 (2026-06-20、ユーザー判断「izanagi-trace のみ修正」):** izanagi-trace に修正 commit
`6656e93` (5箇所 `10 ^ 9`→`1000000000`)。WAL=1 ビルドで gcc-13 -Werror クリーンを確認。
master 還元は後日人間が判断 (この時点では master は据え置き)。parent gitlink を 6656e93 に前進。
探索は WAL=0/1 両方を含む silo 12 genome で続行。

## 副次発見 (別現象、P2-2 で確定予定)

**両 no-wait=0** (NO_WAIT_LOCKING_IN_VALIDATION=0 かつ NO_WAIT_OF_TICTOC=0 = wait validation)
の silo は、trace build で **high/mid/low(uniform) の全 contention で trace 取得が timeout**
(切り分け済み、25s でも取れず)。contention 非依存なので「高 contention 病理」ではなく構成自体の
ハング (livelock 疑い)。verifier の問題ではない (trace が取れた genome は全て certified =
false-red ゼロ)。

P2-0 (verifier sanity) からは評価不能として除外 (sanity_silo.py でフィルタ、120s×4 の無駄待ち回避)。
**perf build (trace なし) で動くか = 構成病理か trace I/O 特有かの切り分けは P2-2 で行う**: 動けば
探索空間に残す (fitness 測定可能)、動かねば genome.py に両 no-wait=0 除外制約を追加する。
