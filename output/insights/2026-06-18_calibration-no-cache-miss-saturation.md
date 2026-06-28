# 発見: YCSB×masstree では LLC miss 率が飽和せず単調上昇する (飽和点が存在しない)

- **発見日:** 2026-06-18 (Phase 1 タスク4b の実機 calibration, env=linux-baremetal)
- **種別:** Izanagi 側の **calibration 方法論の前提誤り** (CCBench のバグではない。
  masstree index の正常な性質)
- **重大度:** 中 (calibrator の核心ロジックに影響。下限基準の追加で対処済 = D15)
- **還元判断:** 上流 PR 不要 (CCBench のバグでないため)。Izanagi 側の方法論修正で完結

## 何が起きたか

roadmap §4 / calibrator.md は「レコード数を倍々に上げると LLC miss 率が**飽和する点**
が在り、それを探す」を前提していた。実機 (Dell R760, Xeon Gold 5418N, 48 thread,
Silo/YCSB, numactl interleave + `-DLinux` pinning) で測ると**飽和しなかった**:

| records | miss率 (uniform skew=0) | miss率 (skew=0.9) |
|---|---|---|
| 1m  | 14.9% | 19.8% |
| 2m  | 22.7% | 23.2% |
| 4m  | 34.0% | 28.7% |
| 8m  | 41.1% | 33.1% |
| 16m | 44.4% | 36.5% |
| 32m | —     | 39.1% |
| 64m | —     | 40.6% (Δ=1.48pp, まだ未飽和) |

両 workload とも miss 率は単調上昇し、Δ は緩やかに減衰するのみで「膝」が出ない。

## なぜか (根本原因)

CCBench の index は **masstree** (B+tree 系の trie)。レコード数 N を増やすと**木が
深くなる** (深さ ∝ log N)。各 lookup が辿る内部ノードが増え、それらの cold node が
L3 に乗り切らず miss し続けるので、miss 率は N とともに上がり続け、漸近線に非常に
ゆっくり近づく。ハッシュ index なら working set が L3 を超えた時点で miss 率が
飽和するが、木では「飽和点」が実用レンジ (≤64m) に現れない。

## 2 つの含意

1. **飽和点は workload (skew) に依存する。** uniform は局所性ゼロで miss 率が高く
   速く上がる。skew=0.9 は hot key が cache に乗るぶん低めだが、それでも cold tail +
   木深化で飽和しない。throughput の向きすら逆 (uniform は N増で低下=cache律速、
   skew0.9 は N増で上昇=hot key 競合が薄まる)。→ calibration を入力完全非依存に
   できない。(env, thread, 代表 workload) でキーする (D13 改訂)。
2. **「飽和せず → 最大点」は規律4 と逆。** 飽和点が無いとき最大レコード数を採ると、
   最も makeDB が重く run が遅い点を選ぶ。一方 many-core cache 競合の再現 (下限) は
   ~1m で既に満たされる (miss 15-20% = 明確に cache-bound)。

## 対処 (D15, 実装済)

`find_saturation` に**下限基準**を追加: 飽和点が範囲に無ければ「working set (実測
maxrss) が L3 (本ホスト 90MB) を K 倍 (既定4) 超える最小 N」を採る。

実測結果 (skew=0.9, 48 thread): 1m で maxrss=597MB = L3 の **6.6×**、miss 20.4% で
cache-bound → **records = 1,000,000** を採用 (早期打ち切り)。noise floor の変動係数 (CV = 標準偏差/平均) 2.28%。

## 限界 (正直に記録)

maxrss は固定オーバヘッド (binary/masstree base ~200MB) を含むので working set の
**緩い上側代理**。本ホストでは 1m の時点で既に L3×4 を超えるため、下限基準は実質
「スイープ最小点で既に cache-bound」を確認する形になった。より厳密な下限が要るなら
(a) 固定オーバヘッドを差し引く、(b) スイープを 1m 未満に延ばす、が考えられるが、
1m の miss 率 20% が cache-bound を直接裏付けており、1m run は最安なので実用上十分。
