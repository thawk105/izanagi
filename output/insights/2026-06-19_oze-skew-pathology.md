# 発見: oze (eager serialization-graph) は skew で病理的に遅い (read ごとのグラフ DFS が爆発)

- **発見日:** 2026-06-19 (Phase 1 タスク5b, baseline 取得中, env=linux-baremetal)
- **種別:** CCBench `oze` プロトコルの**性能特性** (バグでなく設計固有の病理)
- **重大度:** 低-中 (baseline 取得で oze だけ skew0.9 で測れない。Phase 2 で oze を扱う際の前提)
- **還元判断:** 上流 PR 不要 (バグでない)。Phase 2 の baseline 設計への申し送り

## 観測

確定 calibration (1m/48thread/skew0.9/rratio50/rmw=false) で YCSB 7 protocol の baseline を測ると、
**oze だけ 81 tps / CV 53%** (他は 327K–1.05M tps, CV<1.5%)。約 1万分の1で実質 livelock。

特性化 (oze, 1m, rratio50, rmw=false):

| 条件 | tps | abort_rate |
|---|---|---|
| thread=1,  skew=0.9 | 244 | 0.2% |
| thread=4,  skew=0.9 | 1,930 | 12.8% |
| thread=48, skew=0.9 | 206 | **99.34%** |
| thread=48, skew=0 (uniform) | **122,761** | 0.02% |

- **skew=0 (uniform) では正常** (122K tps)。**skew=0.9 で病理的**。
- thread=1 でも skew0.9 は 244 tps と異常に遅い (abort 0.2% = 競合でない) → スループット律速は
  abort でなく**処理コストそのもの**。thread=48 では abort 99% が乗って完全 livelock。

## 機構 (ソース確認)

oze は eager な serialization graph を持つ MVCC。read 経路 `get_visible_version`
(`cc/oze/transaction.cc:164`) が版の可視性を `is_invisible` → **`is_invisible_dfs`
(`cc/oze/include/transaction.hh:363-430`) で依存グラフを DFS 全走査**して判定する
(各ノードの `readBy_` + `writtenBy_` 辺を再帰、`seen` map で訪問管理)。

- **read ごとにグラフ DFS** なので、skew0.9 で hot key にグラフが密集すると 1 read のコストが
  グラフサイズに比例して膨らむ → thread=1 でも 244 tps の処理律速。
- thread を増やすとグラフがさらに密になり検証失敗 → abort 99% で livelock。
- uniform は hot key が無くグラフが疎なので DFS が軽く正常。
- `is_invisible_dfs` 内の `std::cout` は `#if DEBUG_MSG` で囲われ build は `DEBUG_MSG=0` →
  **print バグではなく真にアルゴリズム的**コスト。`MERGE_ON_READ=0` (eager merge は off)。

## 含意 (Phase 2 への申し送り)

- **oze は確定 calibration (skew0.9) で baseline を取れない。** uniform なら測れる (122K tps)。
- Phase 2 で全 protocol baseline を揃えるとき、oze は (a) uniform で測る、(b) skew 病理を
  明示フラグ、のどちらか。skew 帯での CC 比較から oze を外す判断材料。
- これは「グラフベース eager 直列性検査は密競合グラフでスケールしない」という既知の一般則の
  CCBench 上の実例。oze の設計目的 (直列性の eager 厳密検査) と性能のトレードオフ。
