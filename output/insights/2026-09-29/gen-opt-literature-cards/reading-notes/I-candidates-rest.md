# 読みメモ: I-candidates-rest (Brook-2PL / Caracal / CormCC / Tebaldi / ESSN)

作業日 2026-09-29 (JST)。読み取りと記録のみ。JSONL は同じ dir の `I-candidates-rest.jsonl` (26 件)。

指示めいた文字列: なし (5 本とも本文に、作業の振る舞いを変えるよう求める文は見当たらなかった。Caracal の "ignore marker" は技術用語)。

## 取得と読んだ範囲

すべて `<作業 dir>/src/` に保存。テキストは `pdftotext` (Caracal・Tebaldi は `-layout` も)。取得は `curl -sSL -A "izanagi-literature-survey"`。

| 論文 | 取得元 URL | 取得時刻 (JST) | SHA-256 (PDF) |
|---|---|---|---|
| Brook-2PL (`src/brook2pl.pdf`) | https://arxiv.org/pdf/2508.18576 | 2026-09-29 10:08 | 27b494a54bdc3cebf7ed685b1f164529fa26049b7df9d4e30685cf35c1fbb1ac |
| ESSN (`src/essn.pdf`) | https://arxiv.org/pdf/2511.22956 | 2026-09-29 10:08 | b406fb53b9433c4d686dce6de83a7be3ec77775f5570bfc5b7c77ef90117eaba |
| CormCC (`src/cormcc.pdf`) | https://www.usenix.org/system/files/conference/atc18/atc18-tang.pdf | 2026-09-29 10:08 | ff19fe7cbb782e28a2e47bf6dcf27551f4e724085505b35e7c3bc102ea7f59fc |
| Caracal (`src/caracal.pdf`) | https://www.eecg.toronto.edu/~ashvin/publications/caracal.pdf | 2026-09-29 10:08 | 570923d2d167fbbbd1961df78309947deeb75d0e78d76e9f30afb7bd76e62b55 |
| Tebaldi (`src/tebaldi.pdf`) | https://nacrooks.github.io/bibliography/publications/2017-sigmod-tebaldi.pdf | 2026-09-29 10:08 | e5d349120139e120ce8fbd6c4c4b92596e3e77caa983f17bcb7dae158c0b67d1 |

5 本とも本文を取得できた (要旨のみの論文は無い)。Caracal と Tebaldi の URL は WebSearch の結果に出た著者頁で、同じ手順で保存した。

読んだ節:
- Brook-2PL: Abstract、§1-§4 (§4.1-§4.4 の本文と Fig. 9-13 の説明文)。未読: §5 Related Work、§6、Appendix A/B、Fig. 14 の詳細。
- Caracal: Abstract、§1-§5.5 (Fig. 5-10 の本文)。未読: §5.7-§5.8 の遅延・分散実験、§6。
- CormCC: 全体の本文 (§1-§6.6)。未読: 技術報告 [1] (分類器の詳細)。
- Tebaldi: Abstract、§1-§8.5。未読: §9 Related Work、§10。
- ESSN: Abstract、§1-§6.6。未読: それ以降の節 (§7 以降、Table 2 を含む関連づけ)。

引用は全て、保存した PDF の本文と空白を無視して照合済み (JSONL の `loc` 末尾の `[PDF p.N]` は PDF の頁番号で、Caracal・CormCC は原稿の頁数 (180-、809-) と異なる)。

## 依頼文・既存表 (cc-candidates-2026-09-17.md §3) と原典の差

- **Tebaldi の題名**: 依頼文の "Tebaldi: Efficient Coordination of Multiple Concurrency Control Mechanisms" ではなく、原典の題名は **"Bringing Modular Concurrency Control to the Next Level"** (著者 Su, Crooks, Ding, Alvisi, Xie)。DOI 10.1145/3035918.3064031 は PDF の本文にある。
- **Caracal の著者**: 依頼文の "Qian ほか" ではなく、原典は **Dai Qin, Angela Demke Brown, Ashvin Goel** (Toronto)。
- **Brook-2PL の venue**: 取得できた arXiv v1 の書式は "SIGMOD '26" で DOI 欄は `XXXXXXX.XXXXXXX` のまま。依頼文の PACMMOD・DOI 10.1145/3769767 は v1 PDF からは確かめられなかった (未確認、推測で埋めていない)。
- **Brook-2PL の b=×** (表の記述は abstract のみ): 原典で裏づけられた。解析は transaction 型 (stored procedure 相当) の事前登録が要り、table 単位 (§3.3)。ただし row 単位の read/write set の宣言は不要で (比較対象の Sorted Locks が「read/write set 既知」を仮定する、と §4.3 (Comparison Baseline) が違いとして書く)、事前解析していない transaction は Wound-Wait 2PL に戻る動的経路がある (§3.8)。表の「本文の代替経路は未照合」に対する答えは、この動的経路 (静的集合を優先、Static は abort しない)。実装は Java の自前 in-memory 系で 64 thread (§4.3)。
- **Caracal の b=?**: 原典で確定。batch (epoch) と write set (key・範囲) の事前宣言が要る。read set は不要 (§3.1)。GPL-2.0 は本文には無く、未確認のまま (本文に repo の記載を見つけていない)。
- **CormCC の「単一 protocol でない」**: 原典で確認 (partition ごとに PartCC・Silo OCC・VLL 2PL を割り当てる枠組み、§4、§5)。Plor の引用と整合。CormCC 論文中の比較対象 "Tebaldi" は自前試作の上に Tebaldi 風の混合を実装し直したもので、Tebaldi 原論文の系の数値ではない (§6.1、§6.3)。
- **Tebaldi の (a=? b=?)**: 原典で b は「事前宣言に相当するものは必要」。transaction 型→group の静的対応と、RP を使うなら table 依存の静的解析が要る (§3、§6)。SSI・TSO は batch が要る (§6)。read/write set の宣言は不要 (TSO の promises は任意)。repo は本文に無い。
- **ESSN の「ERMIA への実装・置換費用」**: 原典に ERMIA は出ない。評価は単一 thread の Python 履歴生成器・検査器で、throughput の測定は無い (§6.3)。CCBench の ermia との実装関係は本文から読み取れない。abort 率の改善は履歴検査上の数値。

## 論文ごとの最適化 (JSONL に入れた 26 件)

### Brook-2PL (5 件、arXiv:2508.18576)
1. `brook2pl-slw-graph-deadlock-free-2pl` (protocol-core) SLW-Graph、SLW-cycle 無しなら deadlock 不能 (Theorem 3.1)。
2. `brook2pl-lock-manipulation` lock を前へ移す・atomic に併合・可換注釈 (§3.5)。
3. `brook2pl-read-write-constraint` R→W を最初から排他 lock 1 つに (§3.3)。
4. `brook2pl-partial-chopping` 早期 lock 解放 (§3.6、Theorem 3.2)。
5. `brook2pl-dynamic-transaction-priority` 静的集合を優先する動的 transaction の共存規則 (§3.8)。

JSONL に入れなかった候補: contention score による graph 選択 (§3.7、式 1) は 1 の一部として扱った (単独の ablation が無い)。

### Caracal (7 件、SOSP 2021)
1. `caracal-epoch-deterministic-cc` (protocol-core) epoch・initialization/execution の 2 phase・pending version。
2. `caracal-batch-append` (§3.3、Fig. 8)。
3. `caracal-split-on-demand` (§3.4、Fig. 8-10)。
4. `caracal-version-array` ソート済み version array + 二分探索 (§3.2)。
5. `caracal-insert-append-range-update` initialization の 2 段分割 (§3.2)。
6. `caracal-gc-minor-major` (§3.5)。
7. `caracal-early-write-visibility` (§3.2、§3.7)。

JSONL に入れなかった候補: 行 cache (transaction ごとに index の探索結果を持つ、§4.3)、inline 化 (Cicada 由来、§4.3)、preemptive な piece scheduler (§4.2、split-on-demand の実装部品として 3 に含めた)、Calvin 型の reconnaissance transaction (§3.7、既存技法)。単独の効果数値が無いため。

### CormCC (3 件、USENIX ATC 2018)
1. `cormcc-mixed-cc-framework` (protocol-core) 協調なしの混合 CC (§4)。
2. `cormcc-mediated-switching` online 切替 (§4.3、Fig. 16)。
3. `cormcc-protocol-classifier` 二値分類器 (§5。詳細は技術報告で未読)。

JSONL に入れなかった候補: key→protocol の lookup table (1 の一部)。

### Tebaldi (6 件、SIGMOD 2017)
1. `tebaldi-hierarchical-mcc` (protocol-core) CC の木・consistent ordering・4 phase の 2 pass。
2. `tebaldi-batching-for-consistent-ordering` (§4、§6)。
3. `tebaldi-root-ssi-readonly-optimization` (§6)。
4. `tebaldi-tso-promises` (§6)。
5. `tebaldi-phase-batched-rpc` (§7、分散前提)。
6. `tebaldi-gc-epoch` (§7)。

JSONL に入れなかった候補: Runtime Pipelining と SSI・TSO・2PL の各 CC そのもの (既存の単一 CC で Tebaldi の新規技法ではない)。CC 合成の 3 戦略 (adopt・constrain・procrastinate、§4) は 1 の一部と 2 に含めた。

### ESSN (5 件、arXiv:2511.22956)
1. `essn-exclusion-test` (protocol-core) 除外条件 π(t) ≤ ξ(t)。
2. `essn-kto-begin-ordered-commit-stall` KTO の一般化・commit-stall・stall-bypass。
3. `essn-previous-edge-only-metadata` 3 stamp・chain 走査なし (Table 1、Algorithm 1)。
4. `essn-read-time-shortcut` (§5.3)。
5. `essn-read-from-policy` (design-dimension、§6.3、§6.5)。

## 注意点 (読み手向け)

- 分類の `effect_category` は、原典が 3 分類の語で説明しているもの (Caracal split-on-demand の cache coherence traffic、Caracal GC の cache 局所性) を除き、根拠欄に「近似」または「3 分類外」と書いた。ESSN の cpu-cache は、論文が「version object を小さく保つ」と述べることに基づく分類で、cache の測定は無い。
- `requires_predeclared_sets` の意味: Brook-2PL は transaction 型・table 単位の事前解析が要る (true)。row 単位の read/write set の宣言は要らない。Caracal は write set (key・範囲) の宣言と epoch の batch が要る (read set は不要)。CormCC は false (conflict の事前知識は不要と本文が述べる) だが、PartCC を候補に含めると stored procedure の引数から partition を特定する注釈が要る。Tebaldi は transaction 型→group の静的対応と、SSI・TSO の batch が要る (true)、read/write set は不要。ESSN は false。
- 効果の数値はすべて表・図番号を付した。図の中の数値 (棒グラフの値など) は本文に書かれたものだけを採った。
- 評価環境の違い: Brook-2PL は Java の自前系・分散でない、Caracal は C++17 の 32 core 単一 node、CormCC は Doppel 基盤の 32 core、Tebaldi は 20 台の分散 KV (network 込み)、ESSN は単一 thread の Python 検査器。数値を CCBench の環境へ持ち込むときはこの差に注意。
