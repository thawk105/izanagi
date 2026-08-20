---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-21
wave: dev-wave-t1437-mocc-macro-protocol
seq: 1
title: '[T-1437] source_digest の macro 供給表を source 単位で protocol 分離し、mocc/silo 両方の resolve() fails-closed 停止を解消した (コード+テスト、branch worktree-dev-wave-t1437-mocc-macro-protocol、変異matrix = baseline PASSED・5/5 KILLED・SURVIVED 0・MISMATCH 0、受入 verdict=child-green)'
---

## 本文

- **同日regressionの発見。** `orchestrator/campaign/source_digest.py` の
  `EVOLVE_BLOCK_SOURCES` (silo/mocc混在の固定tuple) に対し defines が `genome.protocol`
  単一からしか作られていなかったため、`Genome("silo",...)`/`Genome("mocc",...)` の**両方**で
  `source_digest.resolve()` が対称にfails-closed停止していたことを実機再現で確認した。
  原因は本日land済みの commit `ae958491` ([T-755] mocc trace-hook用の編集面拡張) — 長期潜伏
  バグではなく着手前日中に導入されたregressionだった。段1briefの実機再現スクリプト
  (`Genome("silo",{})`が`cc/mocc/transaction.cc`で`['MQLOCK','RWLOCK','TEMPERATURE_RESET_OPT']`
  未知、`Genome("mocc",{})`が`cc/silo/transaction.cc`で対称に未知)が [T-1431] の実エラーと
  逐語一致した。
- **root cause 3点**: A (主因、source単位でprotocolを分けず defines を genome.protocol
  単一から作る設計)、B (裸オプション `RWLOCK`/ss2plの`DLR1` を `_SUPPLY_RE` が拾えない、
  DW-G03の独立2例で一般化)、C (`MQLOCK` は repo 全体で供給源ゼロの真の死コード、
  `CONTEXT_MACROS`を流用せず専用 registry + 自己検証で対応、{{D:source-digest-supply-precision}}
  参照)。
- **段3敵対相談 (2レンズ) が独立に、非対称CMake option命名 (cicada/ozeの
  `INLINE_VERSION_OPT=${CCBENCH_INLINE_VERSION_OPT_X}`型) で値が脱落する新規バグと、
  `EVOLVE_BLOCK_SOURCE_PROTOCOLS`の直接dict lookupが`KeyError`(RuntimeErrorでない)になる
  欠陥を発見した。** 親裁定でいずれも同一commitで閉じた。
- **段6敵対レビューが1件のmust-fix (MQLOCK registryのセミコロン区切りlist供給源
  `"FOO;MQLOCK"`の見逃し) を発見、fixで対応した。そのfix自体がthird_party (googletest) の
  無関係なgenerator expression token (`$<INSTALL_INTERFACE:GTEST_LINKED_AS_SHARED_LIBRARY=1>`)
  に誤反応し3テストregressionを起こした** (親が`tools/run_tests.py`の実機実行で検出、codex子は
  Pegasus dispatch認証エラーで自己検証不能だった)。scopeを`macro名がtokenにliteralに含まれる
  場合だけ停止`に狭めるfix2で解消。
- **変異matrix**: 事前登録5点をprobe走 (expected_status=SURVIVED) で実測した結果、机上予測
  (M2/M3は単一node) は当たったが、M1/M4/M5は予測より広いnode集合を示した — 段5 fixが
  fake mocc fixtureへ実の条件指令 (`#ifdef RWLOCK`等) を追加したため、既存の周辺guard系
  テストも副次的にroot cause Aのregression guardとして機能するようになっていた
  (想定外の良い副作用)。実測値で本登録し最終スコア走 = baseline PASSED・5/5 KILLED・
  MISMATCH 0。
- **受入全走で新規regression 13件を発見** (`test_check_trace0_preprocess_identity.py`、
  [T-1437]着手前は緑)。原因は`tools/check_trace0_preprocess_identity.py`が呼ぶ`_head_defines`
  のtest fixtureが`ccbench_universal_definitions`関数本体を`target_compile_definitions(...)`
  直書き形式で書いており (実`cmake/Options.cmake`の`set(...PARENT_SCOPE)`形式とは別の、
  同等に正当なCMake慣習)、新設パーサが後者しか認識しなかったため。**このconsumerを段5/6の
  焦点走 (test_campaign.pyの`-k`フィルタのみ) で見落としていた —
  DW-O26の「変更したproduction fileを参照するconsumer testも含める」を、production file自体の
  grep網羅はしたが、そのconsumerの**test fixtureの内部構造**までは検算しなかったための
  取りこぼし。** fix3 (パーサ一般化、`target_compile_definitions`も認識) で解消、
  焦点確認80 passed・10 skipped・0 failed。
- **受入全走 attempt1 は rc=70 (restart-required) で一度失敗した** — 待ち手が2.5時間超
  lease順番待ちしている間に他waveが`tools/dev_wave_wait.py`自体をmainへlandし、待ち手が
  束縛したbytesとtipの内容が不一致になったための正しいfail-closed停止 (leaseは適切に
  解放済み)。fix3後のattempt2で`verdict=child-green`。
- **codex実装/fix子はPegasus queueへdispatchできない既知制約 (`qstat -Q preflight rc=1`
  または`rc=16`) を計3回再現した** (段5実装1回、段6 fix3で1回、いずれも親が
  `tools/run_tests.py`で自ら焦点実行を代替)。段8改善候補として記録。
- 設計判断は {{D:source-digest-supply-precision}} を参照。

## 次の一手差分

### 完了

- [T-1437] 実装 (source_digest.py + test_campaign.py) が commit `2a34b7b0` (root cause A/B/C) と
  `85affd92` (universal definitions parser 一般化) で完結し、変異matrix (baseline PASSED、
  5/5 KILLED) と受入全走 (`verdict=child-green`、tested_tip `678381f2`) が緑になったため完了する。
  remaining: none
  base: 59d71b2ba63f8fbd32f38e5f84efef8d4f5ac6465e223f14d42133d9e7f7fe22

### 更新

- [T-1431] **P1・[T-1437]解消により再開可能 (2026-08-21)**: D581に従い床値pilotを実投入したが、
  mocc protocolの実ソースビルド準備段階 (`source_digest.resolve`) でfail-closed停止し実測値は
  0件のままだった。[T-1256]は解消済みと実証済み。admissionチケットは1枚も消費していない
  (`retry_slots_per_cell=2`を12セル分フル保持のまま)。**[T-1437]がsource_digestのmacro供給表
  protocol分離を実装・受入完了した** (branch `worktree-dev-wave-t1437-mocc-macro-protocol`,
  {{D:source-digest-supply-precision}})。本insightの投入パラメータ
  (`output/insights/2026-08-20_t1431-floor-pilot-measurement/README.md`) をそのまま再利用して
  床値pilotを再投入できる (admission・toolchain・protocolは健全と確認済み)。
  base: fbbfb52e361a837577bb6f5609357a64b57c8dde26e6e4591536a6407719d6bb
