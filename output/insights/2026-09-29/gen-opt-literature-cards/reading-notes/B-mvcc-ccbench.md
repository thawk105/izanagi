# 読みメモ B-mvcc-ccbench (gen-opt md_2、2026-09-29)

指示めいた文字列: なし (5 本とも本文・抽出テキストを走査。作業の振る舞いを変えるよう求める文は見つからなかった)。

カード本体: `B-mvcc-ccbench.jsonl` (41 件)。引用 (quotes) は生成時に各 PDF の抽出テキストと突き合わせ、全件が原典に存在することを確認済み。
loc の末尾の「PDF p.N」は PDF 内の頁番号 (論文の印字頁ではない)。Wu 論文のみ、本文の印字頁 (PVLDB p.781-792) も併記した。
生成スクリプト (再検証用): `build_B.py` 同 dir。

## 書誌・取得元・SHA-256

| 論文 | 取得元 | 取得時刻 | SHA-256 |
|---|---|---|---|
| Cicada (SIGMOD 2017) | 取得済み `/work/1/SFC/tanab/tmp/vhash-related-work-2026-09-29/src/cicada-sigmod2017.pdf` (取得元 URL はこの job では未確認) | 前 job で取得 | 4f6c5118a51ffbae3c5795e457f5cca91012a07a7e96dada32c115bedf176dd4 |
| ERMIA (SIGMOD 2016) | 同 dir `ermia-sigmod2016.pdf` (同上) | 前 job で取得 | 0c9f8151e25da64241ad36f40c32fa7298f9b5bfa469644945d3fbe1b204b22a |
| SSN (VLDB J. 2017) | https://arxiv.org/pdf/1605.04292 (arXiv v5, 2017-05-04 版) | 2026-09-29T10:02:04+09:00 | 4603cc6a6e04a19abbe9d9ec033dfc1e0f641ec5e22a8e793155a0644816dd93 |
| Oze | https://arxiv.org/pdf/2210.04179 (v3、題名 "...for Long-running Update Transactions (Extended Version)") | 2026-09-29T10:02:16+09:00 | 5bcae2aaa7beb69ae2df7e2d29cbd28d10a9eea8f96375abba738d56767dc49b |
| Wu ほか (PVLDB 10(7), 2017) | 同 dir `wu-empirical-mvcc-pvldb10-2017.pdf` (取得元 URL は未確認) | 前 job で取得 | e0f3d3be03734d2afd5de7681a268a7aead0572e9f254e49ff4b4852ba787bd1 |

新規取得した 2 本の PDF は `src/ssn-arxiv1605.04292.pdf`、`src/oze-arxiv2210.04179.pdf` (抽出テキストは `src/ssn.txt`、`src/oze.txt`、他に `-layout` 版)。
既存 3 本の raw 抽出は `src/cicada.raw.txt`、`src/ermia.raw.txt`、`src/wu.raw.txt`。

注記:
- Oze は依頼文の題名 (…Real-world Long Transactions on BoM Benchmark) の版そのものは取れなかった。arXiv の同一著者・同一主題の拡張版 (題名が改題されたもの、著者 Nemoto, Kambayashi, Hoshino, Kawashima) を読んだ。Semantic Scholar の検索結果は旧題を同じ論文として示している (推測: 旧題は同論文の初期版の題)。PVLDB 版 (vol.18 p.2321) は取得していない。
- SSN は VLDB Journal 版そのものではなく arXiv v5 を読んだ。

## 読んだ節・読んでいない節 (論文ごと)

- Cicada: 読んだ = Abstract, §1, §2.1-2.4, §3.1-3.9, §4.1-4.6 (Fig.3-11, Table 2), §5, 付録 A・B。未読・流し読み = §3.7 の実装細部、付録 A 補題の全ケース、参考文献。
- ERMIA: 読んだ = Abstract, §1-§6 (Algorithm 1, Fig.1-12, Table 1)。未読 = 参考文献、Fig.12 のレイテンシ細部。
- SSN: 読んだ = Abstract, §1, §3.1-3.4, §4.1-4.2 (Algorithm 1-3), §5.1-5.3, §6.1-6.2, §7.6 (Fig.9), §8.1-8.5 の主要部。未読 = §3.3 の定理の証明本文、§7.1-7.5 のシミュレータ詳細、§8.1 の負荷細部、§9 以降、参考文献。
- Oze: 読んだ = Abstract, §1, §2 の要旨、§3, §4, §5.1-5.5 (Fig.8-14), §6-7。未読 = §2.1-2.5 の BoMB 定義細部、付録。
- Wu: 読んだ = 全節 (Table 1, Fig.1-25 の本文記述)。図の数値は本文中の記述だけを使い、グラフから目読みした値は書いていない。

## 最適化の一覧 (JSONL に入れたもの)

### Cicada (14 件)
protocol-core: multi-clock timestamp、serializable multi-version validation。
optimization: best-effort inlining、early abort と write-latest-version-only、PENDING への spin-wait、write set の競合度ソート、early version consistency check、ソート/precheck の適応的省略、incremental version search、rapid GC、contention regulation (山登り backoff)、abort 後の clock boost、multi-version index の遅延更新、read-only の thread.rts 利用。

Table 2 (contended YCSB、28 thread) の ablation: No-wait -13.2%、No-latest -4.9%、No-sort -12.7%、No-precheck -9.5%。個別に外した効果であって、加算的とは論文が言っていない。

### ERMIA (5 件)
protocol-core: SI+SSN。optimization: indirection array、3 本 epoch の epoch manager、fetch-and-add 1 回の log manager、TID table。
論文に ablation の表・図は無く、Fig.11 (cycle 内訳) の本文記述と、Silo との比較 (Fig.1,2,5-9) が根拠。

### SSN (8 件)
protocol-core: exclusion window test。optimization: latch-free parallel commit、readers bitmap、pstamp/sstamp の 1 語同居、active safe snapshot、read-only の c(T)=snapshot 時刻、read-mostly の cold read 追跡省略 (SI+SSN-R)、階層追跡 (評価なし)。

### Oze (6 件)
protocol-core: 分散 MVSG。optimization: order forwarding (Fig.13: throughput 約 3%、abort 率約 20% 改善)、OCC/MVSG の動的切替、並列 validation、precision locking 変形、epoch による graph/version の GC。

### Wu ほか (8 件、すべて design-dimension)
CC protocol (MVTO/MVOCC/MV2PL/SI+SSN)、version storage (append-only/time-travel/delta)、chain の向き (O2N/N2O)、非 inline 属性の共有、core ごとの memory 領域、tuple-level GC の VAC/COOP、GC 粒度 (tuple/transaction)、index pointer (logical/physical)。
論文の結論の所在: §8 (PVLDB p.791) の 4 つの findings が version storage、CC protocol (MVTO が幅広く堅い)、GC (transaction-level が最良)、index (logical pointer が常に高い)。

## JSONL に入れなかった候補 (理由つき)

- Cicada: 読み書きの単独 record read を transaction 抜きで行う最適化 (付録 B)。論文が『どの実験でも使っていない』と明記していて評価が無い。thread-local hash による read-own-writes と重複アクセス検査の省略 (§3.2)。小さな実装の細部で数値なし。wraparound 対策の version 再挿入 (§3.1)。性能技法というより正しさの保守。
- ERMIA: 大きな object の書き込みを secondary storage へ逃がす (§3.3 の 4 番目)、fuzzy checkpoint と logical logging による recovery (§3.7)、phantom 対策 (Silo の tree node version 検証の継承)。前者 2 つは CC の性能主張に関係が薄く、後者は継承のみ。
- SSN: 単一 version 系への lock ベース SSN (§4 冒頭で future work と明記)、gap lock 型の phantom 保護 (§6.2)。設計の記述のみで評価が無く、階層追跡だけカード化した。early exclusion window 検査 (§4 冒頭、read/write 中に abort) は独立の節・評価が無いので exclusion window test のカードの実装欄に含めた。
- Oze: 単一の集中 MVSG 版 (Oze-CM)。比較用の変種で最適化ではない。BoMB 自体は benchmark。
- Wu: 論文 §3.5 が挙げる『未 commit の version の投機的 read』『未 commit の reader がいる version の eager 更新』(Hekaton 由来)。論文は集中データ構造がボトルネックになると述べるが、図表による評価は無い。time-travel 単独の技法 (version storage のカードに含めた)。

## 気づいた点 (事実のみ)

- Cicada は ERMIA の SI+SSN を比較対象とし、TPC-C 1 warehouse で ERMIA が 12 thread を超えると崩れると述べる。Oze 論文は Cicada と ERMIA(SSN) を BoMB で比較し、両者とも長い更新 transaction を commit できない (Fig.8, Fig.9) と述べる。
- Cicada の Table 2 の数値は 28 thread・16 要求/txn・skew 0.99 の単一条件。別 workload での ablation は無い。
- Wu 論文の N2O が優位という結論 (Fig.12) は、Cicada の version リスト (最新から最古の順) と同じ向き。ただし Cicada は inlining と rapid GC で連鎖走査を補う別構成で、両論文の直接比較は無い。
- SSN 論文の safe snapshot の abort 率 (Fig.9) は Python 製の discrete event simulator の値で、実 DB の値ではない。
