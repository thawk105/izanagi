# [T-2135] 段 1 brief

## scope

`orchestrator/campaign/genome.py` の `SPACES` へ tictoc と cicada の genome 空間を登録する。
軸は現行 CMake (`external/ccbench/cc/<protocol>/CMakeLists.txt` + `cmake/Options.cmake`) から
**直交操作できる**もの (= cache option 経由で -D で個別に振れるもの) だけを取り、bare define・
計測撹乱ノブ・死にフラグを除外した理由を `notes` へ書く。導出できない軸は登録せず、
できない理由を `notes` に残す。既存 test `test_tictoc_and_cicada_remain_unregistered` を
登録後の期待へ差し替える。

## 確定済みユーザー裁定

- 本題は登録と軸の導出だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外 (DW-G05)。
- 導出できない軸は無理に登録しない。できない理由を残す。
- 規律 2 を緩めない。Codex author = D95。
- これを終えるまで `docs/phase3.md` 段 6 dormant (b) は閉じない → 本 wave は phase3.md の
  dormant (b) を閉じる編集をしない。tictoc/cicada 登録は (b) の一部でしかなく、
  protocol 別 calibration と between-run floor の対象別再実測が残るためである。

## 不変条件

- verifier anomaly は即 reject。正しさゲートを緩める変更を入れない (規律 2)。
- trace-enabled correctness と trace-disabled performance の分離を維持する (規律 1)。
- 計測撹乱ノブ (`SLEEP_READ_PHASE` / `INSERT_*_DELAY_MS` / `WORKER1_INSERT_DELAY_RPHASE`) を
  探索軸にしない (規律 4)。
- 凍結成果物 (`output/s1-freeze/`, `output/s8b-freeze/`) の bytes を書き換えない。
- 測定は 1 件も行わない。本 wave は探索空間の**宣言**であって certified campaign ではない。

## 成果物の形

1. `genome.py` に `TICTOC_SPACE` / `CICADA_SPACE` と、必要なら制約述語。`SPACES` へ 2 件追加。
2. 除外理由 (bare define / 計測撹乱 / 死にフラグ / 導出不能) を各 `notes` へ逐語で書く。
3. `orchestrator/tests/test_campaign.py` の期待を差し替え + 新規軸・除外・制約の test。
4. worklog / decisions fragment (`docs/spool/`) と insight。

## 実アンカー表 (すべて親が base commit c6a94ec99 で実測済み)

| 対象 | 所在 | 実測した事実 |
|---|---|---|
| 登録先 | `orchestrator/campaign/genome.py:109` | `SPACES` は silo/mocc の 2 件 |
| 既存 test | `orchestrator/tests/test_campaign.py:246` | `test_tictoc_and_cicada_remain_unregistered` が KeyError を要求する |
| tictoc OPTIONS | ccbench `cc/tictoc/CMakeLists.txt` | NO_WAIT_LOCKING_IN_VALIDATION / NO_WAIT_OF_TICTOC / PARTITION_TABLE / SLEEP_READ_PHASE / PREEMPTIVE_ABORTS / TIMESTAMP_HISTORY |
| cicada OPTIONS | ccbench `cc/cicada/CMakeLists.txt` | INLINE_VERSION_OPT / INLINE_VERSION_PROMOTION / REUSE_VERSION / SINGLE_EXEC / WRITE_LATEST_ONLY / WORKER1_INSERT_DELAY_RPHASE / PARTITION_TABLE / INSERT_*_DELAY_MS |
| 直交操作の可否 | ccbench `cmake/Options.cmake:14-54` | 上記はすべて `CACHE STRING` = cache option。mocc の `RWLOCK` のような bare define は tictoc/cicada の OPTIONS に**無い** |
| BACK_OFF | `Options.cmake:20` (universal) / tictoc `transaction.cc:486,708` / cicada `transaction.cc:770,964` | 両 protocol で live |
| PARTITION_TABLE (tictoc) | tictoc の `.cc`/`.hh` に出現 **0** | 完全な死にフラグ |
| PARTITION_TABLE (cicada) | cicada `util.cc:331` のみ | print 専用 = 死にフラグ (silo と同型) |
| tictoc no-wait 対 | tictoc `transaction.cc:564 #if / 574 #elif / 624 #endif` | `#else` 句が**無い**。silo と同じ骨格 |
| cicada inline 対 | cicada `transaction.cc:128-135`, `include/transaction.hh:199-200` | `#if INLINE_VERSION_PROMOTION` は全 site で `#if INLINE_VERSION_OPT` の**内側** |
| 規律 2 の防壁 | `orchestrator/campaign/between_run_floor.py:110` | 述語は protocol 汎用・source 束縛。親の実測 = silo True / mocc・tictoc・cicada False |
| 凍結 pin | `output/s1-freeze/{known_axes,measurement}_freeze.json`, `output/s8b-freeze/holdout_freeze.json` | genome.py を `8e8abd7f…` で記録。現行 live は `10e91790…` で **base 時点で既に stale** (T-2115 の mocc 追加による)。live bytes を比べる pin は `.py` に 0 件 |
| freeze hold | `orchestrator/campaign/freeze_verification_hold.py:14` | `HELD = True` (21 件) |
| 消費者閉包 | `space_for` の production caller **0** (test のみ) | 登録は宣言であり測定経路を開かない |

## 割れうる前提 (親の provisional 裁定・攻撃対象)

- **(P1) tictoc も silo と同じ no-wait XOR 制約を持つ。** 骨格 (`#if/#elif`・`#else` 無し) は同一だが、
  silo の livelock は実測 (insight 2026-06-22) で確定した一方、tictoc では**実測していない**。
  構造からの推論だけで制約を書いてよいか、書くなら notes にどう限界を明記するかを攻撃せよ。
- **(P2) `INLINE_VERSION_PROMOTION=1 かつ INLINE_VERSION_OPT=0` は (0,0) と挙動同一で冗長。**
  含意制約 (PROMOTION ⟹ OPT) を置くのが正しいか、それとも PROMOTION を軸から落とすべきか。
- **(P3) cicada の `SINGLE_EXEC` と `WRITE_LATEST_ONLY` は最適化軸である。**
  これらが「測るものそのもの」(workload や正しさの意味論) を変えるなら軸にしてはならない。
  cicada は真の多版 MVCC で既存 playbook が通用しないため、ここが本 wave の中心的な調査点。
- **(P4) tictoc の `PREEMPTIVE_ABORTS` / `TIMESTAMP_HISTORY` は独立に振れる最適化軸である。**
  相互依存・dead branch が無いことは未確認。
- **(P5) 空間は YCSB workload での数として書けば足りる** (mocc の先例と同型)。

## 分割方針

- 段 2 = codex read-only plan 1 本。段 3 = 敵対相談 2 本 (レンズ A = tictoc 軸の導出と XOR の
  正当性、レンズ B = cicada MVCC ノブの意味論 = 最適化か測定対象の変更か)。
- 段 5 = D95 Codex author 1 本 (genome.py + test_campaign.py)。実装面は親が直接編集しない。
- 段 6 = 敵対レビュー 2 本 + fix + 変異 matrix + 受入全走。
- 設計択一が割れる (P1〜P4) ため**軽量版にしない**。段 2・3 と段 6 review 子を省略しない。
