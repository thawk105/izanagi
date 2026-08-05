# 段 1 brief 追補 — toolchain 実測 (2026-08-05、段 2 実行中に親が実測)

`brief.md` は段 1 時点の記録として書き換えない。本追補が (P1) の**制約条件**を実測で足す。
実測手順 = `probe-toolchain-check.cc` を `g++ -std=c++17 -O2` で build して実行 (repo 外、login node)。

## 実測環境

`g++ (Ubuntu 11.4.0-1ubuntu1~22.04.3) 11.4.0` (login node)。**計算ノードの compiler と同一とは限らない** —
本追補の値は login node の実測であり、計算ノードでの再確認は段 5/6 の probe 実走時に nm/build ログで行う。

## 実測 1 — 前回 mode2 の false sharing は構造的に起こりうる

| 量 | 実測値 |
|---|---|
| `sizeof(std::mutex)` | **40** |
| `alignof(std::mutex)` | **8** |

`std::array<std::mutex, 2>` は **80 byte・8 byte 境界**である。cache line (64 byte) を跨ぐ配置になり、
**2 つの mutex が同一 line を共有しうる**。D126 §4 の仮説 (ii) は構造的に成立可能だと確認できた。
ただし**これが W2 の逆転の原因であることは依然として未実証**である (帰属は主張しない)。

## 実測 2 — `std::hardware_destructive_interference_size` は使えない

`__cpp_lib_hardware_interference_size` が **未定義** (GCC 11.4)。
padding は**リテラル 64 の `alignas(64)`** で書くこと。`alignas(64)` は実測で機能した
(`sizeof(PaddedMutex)=64`、`sizeof(std::array<PaddedMutex,2>)=128`)。

## 実測 3 — 「key の末尾 8 byte」だけの O(1) stripe は退化する (親の初案の欠陥)

親が最初に想定した「key 末尾 8 byte を読んで mix する」形を実測したところ:

| key の形 | 2 分割の実測 |
|---|---|
| YCSB 相当 (8 byte 固定 big-endian、100000 件) | **50003 / 49997** — 均等 |
| 可変長 (`warehouse/<i>/district`、100000 件) | **0 / 100000** — **完全に退化** |
| 空 key | 落ちない (stripe 0) |

原因は明白で、**共通 suffix を持つ key 族では末尾固定窓が定数になる**ためである。
`transaction.cc` は tpcc/bomb からも include されるので、`lockWriteSet` に入れる stripe 関数は
可変長 key で退化しない形にすること。**probe が実走するのは `ycsb_silo.exe` だけ**なので
受理条件には影響しないが、退化した stripe は「2 stripe にしたのに 1 stripe と同じ」という
**測定を無意味にする**経路である。

**(P1) の追補:** stripe 関数は O(1) を保ったまま、少なくとも
(a) 先頭側の窓、(b) 末尾側の窓、(c) key 長 を混ぜること。段 2 のプランと段 3 のレンズは
**提案された stripe 関数が YCSB 8 byte key で実際に 2 分割へ均等に散るか**を必ず検査すること。

**成果物影響:** stripe が退化すると modeX は mode1 と同等になり、`mode1 < modeX` が成立せず
正例の生成経路が再び持てなくなる。逆に退化に気づかないまま「代替 X も不成立」と記録すると、
**候補の設計ではなく実装欠陥を理由に不成立と誤って結論する**。
