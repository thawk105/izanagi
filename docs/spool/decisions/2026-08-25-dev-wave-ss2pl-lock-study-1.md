---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-25
wave: dev-wave-ss2pl-lock-study
seq: 1
---

## {{D:ss2pl-lock-study-axes}}. SS2PL のロック規律スタディは 3 軸の inert patch にし、stock 実装との対照 arm を必須にする

**決定:** CCBench の SS2PL を「排他 / reader-writer」「待つ / No-Wait / Wound-Wait」の 2 軸で
変異させるとき、**3 本目の軸 `SS2PL_LOCK_IMPL` (0 = stock の `ReaderWriteLock`、1 = 合成した
study lock) を必ず持たせ、同じ意味論を stock 実装で測った点を対照 arm として置く。**
既定 (`IMPL=0, KIND=1, DLR=1`) は stock 逐語であり、patch は既定で inert である。
改変は submodule へ commit せず out-of-tree patch に置く (D16 第 4 類 / D18)。

**理由:**
- 2 軸だけだと、phase3 (排他 + Wound-Wait) と phase4 (RW + Wound-Wait) の差に
  **合成した lock 実装そのものの費用が混ざったまま分離できない。** 排他版でも
  reader bitmap・tuple latch・thread 別 control slot の費用を払い続けるため、
  「素の排他 2PL を RW 化した効果」とは呼べない。
- stock 実装で同じ意味論 (RW + No-Wait) を測った点を並べると、
  **S と C の差 = 合成 lock の実装費用**が直接読める。実測では 48 スレッドで
  stock 677,682 tps に対し合成 RW No-Wait が 538,021 tps で、実装費用は無視できない大きさだった。
  この対照が無ければ、その差が RW 化の効果に誤って帰属される。
- 既定を stock 逐語にすることで、patch を当てただけでは baseline が動かないことを構造で保つ
  (絶対規律 2 を patch 適用の側で守る)。

**却下した選択肢:**
- **2 軸のまま実装費用を無視する:** 比較図の差分が機構に帰属しなくなる。
- **stock と study lock で別々の patch を作る:** 2 つの patch の相互作用を検査する義務が増え、
  同一 build から両方を出せなくなる。
- **submodule へ commit する:** gitlink 前進は承認定数の再承認と freeze の再凍結を
  確定的に発生させる。価値が未確定の探索 variant にその費用を払わない。

## {{D:ss2pl-deadlock-evidence}}. デッドロックの証拠は wait-for graph の閉路の持続性で受理し、ハングを証拠にしない

**決定:** 「デッドロックが起きた」と記録してよいのは、次を**すべて**満たすときだけとする。

1. 同一の整合 snapshot 上で、各辺が「待ち手 -> その lock の実 holder」かつ両者の要求 mode が非両立。
2. 連続 3 snapshot で、閉路に属する全 node の thread id・attempt・待っている lock id・要求 mode が
   すべて同一であり、**辺の topology も同一**である。thread id だけの正規化では受理しない。
3. 閉路中の各 thread の commit counter と abort counter が 3 snapshot 間で不変。
4. 該当の走行が hard timeout で終わっている (自力で終了していない)。

証拠を採る計器は既定 OFF の compile-time スイッチに置き、性能ビルドから完全に消す。
**この証拠は計装ビルドのものであり、未計装ビルドでの発生率の証拠ではない**とレポートに明記する。

**理由:**
- 「プロセスが終わらなかった」は、デッドロック以外 (単なる遅さ、飢餓、外乱) でも成立する。
  閉路そのものを取らないと機構に帰属できない。
- snapshot を 1 枚だけ見ると、進行中の待ちを閉路と読み違える。thread id だけで正規化すると、
  holder が入れ替わりながら別の閉路が連続して存在する状態も同じ signature になる。
- 計器が発生確率を変えうるので、一般化の射程を証拠の側で限定しておく。

**却下した選択肢:**
- **timeout を証拠にする:** 上記のとおり機構に帰属しない。
- **worker 自身に閉路検出させる:** 全 worker が lock 内で停止すると検査の機会が消える。
- **外部 harness から推測する:** holder 情報が取れない。

## {{D:ss2pl-no-evolutionary-search}}. 決定論的に指定された変異には進化探索を使わず、射程の限定をレポートに書く

**決定:** ユーザーが変異内容を決定論的に指定した実験では、izanagi の進化探索を使わない。
ただしレポートには「**探索空間が存在しない**」とは書かず、次のように書く。

> 指定された変異は候補選択の問題を持たないため、本 wave では探索を scope 外とした。
> ただし RW lock の実装 (状態の詰め方、latch の有無、reader 表現、padding) には設計空間があり、
> 本 wave の結論は**一つの手設計実装**に限定される。設計空間が存在しない、最適化済みである、
> 探索しても情報が増えない、とは主張しない。

**理由:**
- 探索の配線は特定 protocol に閉じており、別 protocol へ広げる費用は実験の情報量に見合わない。
- 一方で「探索空間が無い」と言い切るのは誤りである。実装の設計空間は現に存在し、
  本 wave の実測でも、同じ意味論のまま待ち合わせ機構を変えるだけで
  48 スレッドの throughput が 2 桁変わった。**射程の限定を書かないと結論が過大になる。**

**却下した選択肢:**
- **探索を配線してから測る:** scope が数倍になり、必須 4 点の取得が遅れる。
- **「探索空間が無い」と書く:** 実測と矛盾する。
