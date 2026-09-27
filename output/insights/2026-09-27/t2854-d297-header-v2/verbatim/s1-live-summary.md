# 生死確認の親要約 (計算ノード 1 走)

- request 31808.nqsv、bnode009 (48 core)、Elapse 170 秒、driver 全体 164.8 秒、rc=0。driver = job dir `driver/liveness.py` (Codex author、sha256 63c7ecef…)、結果 = `evidence/live-1/liveness.json`。
- 入力: C `68106660` → C2' `40a7f4ac` (bundle sha256 99882fa7…)。変更 header = include/tpcc.hh・include/trace.hh。
- 構成 3 つ (stock-gcc11・stock-gcc12・silo genome 先頭 1 点 gcc11) × 旧新、すべて成立:

| 段 | 1 側あたりの秒 (3 構成で揃う) | 結果 |
|---|---|---|
| masstree source 複製 | 0.006 | build ごとに別 dir |
| configure | 0.69〜0.80 | rc=0、compile database 135 entry |
| `masstree_build` (config.h 生成) | 10.56〜10.59 | config.h 生成 (複製側) |
| 依存列挙 (`-MG` なし、135 entry × TRACE 0/1、48 並列) | 10.93〜11.05 | 失敗 0。TRACE token なし 36 = third-party (mimalloc-static 16 entry・gtest 1・gtest_main 1) × 2 |
| TRACE 実効値 (consumer に `-dM -E`) | 1.89〜2.10 | 21 / 21 が `#define TRACE 0` |
| 旧新 database (root 置換後) | — | 3 構成とも一致 |
| 前処理比較 (21 entry × 2 mode、8 並列) | 5.36〜5.78 (構成あたり) | 42 / 42 一致 (3 構成とも) |

- consumer は 3 構成とも 21 entry (設計審査 §2 の数と同じ。genome 1 点・GCC 12.3 でも変わらず)。
- 見積り (実測単価、直列): 1 configure の旧新対 ≈ 2 × (0.8 + 10.6 + 11.0 + 2.0) + 5.5 ≈ 54 秒。C → C2' の 17 configure × 2 compiler = 34 対 ≈ 31 分 (1 node 直列、≈ 0.52 node 時間)。configure 間の並列で wall は縮むが node 時間は同程度。
- wave 全体の計算見積り: 判定 ≈ 0.52 (再走 1 回を見込んで 1.04 まで)、受入 ≈ 0.25 × 2〜3、焦点走・変異 ≈ 0.3 → 上限側 ≈ 2.1、中央 ≈ 1.4 node 時間。判定の再走が要る時点で 2 node 時間の線を再評価する (超えるならユーザー確認)。
