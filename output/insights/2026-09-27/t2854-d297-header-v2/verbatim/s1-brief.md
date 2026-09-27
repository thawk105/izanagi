# 段 1 brief — [T-2854] (1) D297 検査器の header 差分受理規則 v2 の実装

- 研究前進: TPC-C 段 1 (silo・mocc の campaign 認定、D2212 項 2・D2260 項 1) を止めている C2' `40a7f4ac` の pin 前進判断の材料。完了判定 = 改訂後の検査器で C `68106660` → C2' を GCC 11.4 / 12.3 で判定し、結果・実費・pin 波及を記録 (pass でも pin は進めない)。
- 既裁定: D2255 項 1〜5 (規則 v2 = R1〜R7、保証名、残る穴、費用の扱い)、D2260 項 1 (承認・Codex author へ委任・2 node 時間以上はユーザー確認)、D297、D780 項 1 の文言継承と項 2 維持、D2207 (mocc の trace.hh 1 行例外は不変)、D2244 項 4 (C2' は pass まで D297 合格を名乗らない)、D2150 (iii) (GCC 11.4 / 12.3 の 2 版)、D95 (実装面は Codex author)。
- scope: `tools/check_trace0_preprocess_identity.py` へ header の M・mode 不変差分の新分岐 (R1〜R7) と、その test・変異。実 CCBench の C → C2' を計算ノードで GCC 2 版判定。scope 外: pin 前進・gitlink・push、D780 項 2 の別防壁、選定外 genome 空間、clang、仮想リスク向けの gate・台帳・一般化。
- 不変条件: 規律 1・2 を緩めない。.cc の単体比較 (16 文脈・mocc 例外)・A/D/R/C・mode 変更・非 C/C++ の拒否は bytes の挙動を変えない。既存 test の期待値を変えない。header と .cc の同居は両方の合格を要する。比較の予定集合を先に固定し実行済み集合と厳密一致。consumer 0 件・依存列挙の失敗・TRACE 実効値の未確認・不透明 argv・旧新 database の不一致は拒否。
- 成果物: 検査器の新分岐 + test (合成 fixture) + 変異 matrix (設計審査 §6 の 7 件を段 4 で登録) + 計算ノード判定 1 job の結果 JSON (job dir) + insight・fragment。

## 変更面の実アンカー
| 面 | anchor |
|---|---|
| 現行の header 一律拒否 | `tools/check_trace0_preprocess_identity.py:180-201` (`_validate_diff`) |
| 検査本体・CLI | 同 `:651-725` (`check`)、`:728-755` (`_parser`・`main`) |
| .cc 比較 (不変) | 同 `:516-648` (`_compare_file`) |
| 既存 test (header 拒否を固定) | `orchestrator/tests/test_check_trace0_preprocess_identity.py:624-635` |
| production configure (読むだけ・再利用候補) | `orchestrator/campaign/buildcache.py:1949-2030` (`_v2_commands`、target `ycsb_<protocol>.exe` は `:1962`) |
| genome 空間 | `orchestrator/campaign/genome.py:106-220` (`SPACES`・`space_for`) |
| 生成物 | `external/ccbench/cmake/ThirdParty.cmake:58-78` (`config.h` は masstree の SOURCE_DIR 側に `masstree_build` が作る。autotools は CMake でなく環境の既定 compiler) |
| third-party の offline 配置 | `tools/pegasus/fetch_third_party.py` `hydrate` |
| 既存の呼び出し元 (挙動不変を要する) | `tools/pegasus/mocc_trace_pilot.sh`、`orchestrator/tests/test_mocc_trace_job_contract.py`、`test_mocc_trace_pair.py` |

## 親の provisional 裁定 (攻撃対象)
- (P1) header 分岐は新しい明示入力 (計算ノード用の引数一式) を与えたときだけ動く。与えなければ header は従来と同じ文言で拒否する (既存 test・既存 caller の挙動不変)。
- (P2) 1 回の起動 = 1 compiler (既存 `--cxx` と対の C compiler)。GCC 2 版は 2 回起動 (D2150 (iii) の先例)。report に compiler を記録。
- (P3) configure argv は production の `_v2_commands` を呼んで得る (自前で組み直さない) + `-DCMAKE_EXPORT_COMPILE_COMMANDS=ON`。stock configure の genome 表現は production の stock build に合わせる (要確認)。
- (P4) 選定 configure 集合 = stock + consumer を含む production target の protocol の genome 空間の全 genome。production target の判定は production の命名 (`ycsb_<protocol>.exe`) と同じ出所から取る — 並走 [T-2866] が tpcc を production に入れると R4 で広がる。
- (P5) TRACE=1 の依存照会は argv の `-DTRACE=` token を置換し、`-dM` で実効値を確認する (TRACE=1 の別 configure は作らない)。
- (P6) 生成物は configure ごとに masstree source を複製して `masstree_build` で作る (共有すると構成・compiler 間で混ざる)。
- (P7) test は小さな合成 CMake project (生成 header の custom target を含む) を実 cmake・実 g++ で使い、seam で stub しない。login では header 分岐の実走 test は skip せず計算ノードの受入で走る前提。
- (P8) .cc だけの差分の report bytes は変えない (schema も据え置き)。header 分岐の report は追加 field。

## 並列分割方針
実装は 1 file (検査器) + 1 test file の一枚岩。実装子 1 本。変異は親。
受入・実測環境: 受入は `tools/dev_wave_wait.py acceptance`、C → C2' の判定は `dispatch_compute.py --task generic` 1 job (見積りが 2 node 時間以上ならユーザー確認)。

## 前提実測 (生死確認、計算ノード 1 走、詳細 = job dir s1-live-summary.md)
- 31808.nqsv bnode009 Elapse 170 秒。stock-gcc11・stock-gcc12・silo genome 1 点で configure・masstree 生成物・`-MG` なし依存列挙 (失敗 0)・TRACE 実効値 (21/21)・旧新 database 一致・前処理 42/42 一致がすべて成立。consumer 21 entry。
- 単価: 旧新対 1 configure ≈ 54 秒直列 → C → C2' 全 34 対 ≈ 0.52 node 時間。wave 全体 中央 ≈ 1.4 node 時間 (2 node 時間未満、判定再走時に再評価)。
- TRACE token なしは third-party (mimalloc・gtest) の 18 entry だけ。
