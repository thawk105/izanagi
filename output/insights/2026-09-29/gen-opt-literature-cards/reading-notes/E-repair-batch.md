# E-repair-batch 読みメモ (gen-opt md_2、2026-09-29)

指示めいた文字列: なし (7 本の本文を「ignore」「assistant」「you must」「disregard」「system prompt」などで検索し、作業の振る舞いを変えるよう求める文は見つからなかった)。

JSONL は 30 件 (`E-repair-batch.jsonl`)。引用 (各カード 1〜3 件) は、原典の頁ごとの抽出文に逐語で現れること、15〜60 語であることを、スクリプトで機械検査した。`loc` の頁は PDF の頁番号。

## 書誌・取得元・読んだ範囲

取得はすべて `curl -sSL -A "izanagi-literature-survey"`。SHA-256 は PDF の実体。

| # | 論文 | 取得元 | 取得時刻 (JST) | SHA-256 |
|---|---|---|---|---|
| 1 | MV3C (arXiv v1「Repairing Conflicts among MVCC Transactions」) | 取得済み `vhash-related-work-2026-09-29/src/mv3c_arxiv.pdf` (arXiv:1603.00542v1) | 取得済み (今回は再取得せず) | 0f7b7a2eeb3b987200c3fd6cae8b963e262e40b0d0ca30f86cb1db76aaec1fda |
| 2 | Transaction Healing | https://www.comp.nus.edu.sg/~chancy/sigmod16-occ-healing.pdf (`src/healing.pdf`) | 2026-09-29 10:02:37 | 399f297e5776c9a7e74d10dfa6eb60a289a825ecd95bbdad78bf656487c31f1f |
| 3 | IC3 (NYU TR2016-981) | https://cs.nyu.edu/media/publications/TR2016-981.pdf (`src/ic3.pdf`) | 2026-09-29 10:02:39 | 1a23dd2dd686c15c8f9aee9c88d05341e8ff79bd663ca9f382a06f991d4587d7 |
| 4 | Doppel | https://www.usenix.org/system/files/conference/osdi14/osdi14-paper-narula.pdf (`src/doppel.pdf`) | 2026-09-29 10:02:18 | 51f2e9f077e9c6f1532330134e32da88aaa5e4437278a2e74fafbbbfcf42caf9 |
| 5 | BOHM | 取得済み `bohm-pvldb2015.pdf` | 取得済み | ea7dff6561ff555fe5663924a3f2622fc93b8adad9cf875b9041738d5f5159cb |
| 6 | Lomet ほか (TCM) | 取得済み `lomet2012.pdf` | 取得済み | 3f3207d3fafc0e57504d6a65b68a06d80b7ca4af5edc450c0bc13645be90b00c |
| 7 | PWV | https://www.vldb.org/pvldb/vol10/p613-faleiro.pdf (`src/pwv.pdf`) | 2026-09-29 10:02:55 | a50d7bafd39334841be2074c65e2bb8cca371d9d128cf15ad7ddcab839573a47 |

取得の経緯と注意。
- 依頼文の URL 推測 (NUS の `healing-sigmod16.pdf`、NYU の `ic3-sigmod16.pdf`、vldb.org の `p506-faleiro.pdf`) は 404 または別物だった。検索で見つけた上の URL に切り替えた。
- **MV3C の取得済み PDF は SIGMOD 2017 版ではなく arXiv v1 (2016 年 3 月) の preprint で、題名は「Repairing Conflicts among MVCC Transactions」。** SIGMOD 2017 版の本文は取得していない。カードの `paper.title` にその旨を書いた。版の差 (節構成・評価・最適化の追加) は未確認。
- **IC3 の読んだ版は NYU の Technical Report (TR2016-981)。** SIGMOD 2016 の採録版との差は未確認。また依頼文の著者名 (Wang, Mu, Wang, Li) は誤りで、TR の著者は Zhaoguo Wang, Shuai Mu, Yang Cui, Han Yi, Haibo Chen, Jinyang Li。JSONL は TR の著者で記録した。
- Doppel の原典は OSDI 2014 の PDF。PWV の依頼文は PVLDB 10(5) 613-624 で、上の URL が該当する。

読んだ節と読んでいない節 (論文別):
1. MV3C: 読んだ = Abstract, §1, §3.2-3.6, §4, §5.1-5.2, §7 (7.1, 7.2.1)。未読 = §2、§7.2.2 TPC-C の結果段落 (Fig. 9)、§8 以降。
2. Healing: 読んだ = Abstract, §1-§4 全体, §5 冒頭・§5.1・§5.2.1・§5.2.5, 付録 F-G。未読 = §5.2.2-5.2.4 の本文、§6、付録 A-E。
3. IC3: 読んだ = Abstract, §1, §2, §3.2, §3.4, §3.5, §4.1-4.5, §5.1, §6.3, §6.5。未読 = §3.1, §3.3, 付録の厳密な証明, §5.2-5.3, §6.1-6.2, §6.6-6.9, §7。
4. Doppel: 読んだ = §1-§5 (5.6 は冒頭)、§8.1-8.2, §8.4-8.7。未読 = §6-7, §5.6 後半, §8.3, §8.8 (RUBiS)。
5. BOHM: 読んだ = Abstract, §1, §3 全体, §4 の本文 (Fig. 5-9 の本文の言葉)。未読 = §2 の詳細、§5-6、図の数値。
6. Lomet: 読んだ = Abstract, §I-II, §III 冒頭, §V.A, §VI, §VII, §VIII.A-D。未読 = §III の場合分け表、§IV、付録 A の手続き。
7. PWV: 読んだ = Abstract, §1, §2.2-2.3, §3, §4.1-4.4, §5.1-5.3。未読 = §4.5-4.7, 証明の付録, §6。

## 論文ごとの最適化一覧と `requires_predeclared_sets`

事前宣言 (read/write set、template の静的解析、batch) を要するかを、論文ごとの結論で先に書く。

| 論文 | 要する? | 何を要するか |
|---|---|---|
| MV3C | 要する (template 注釈) | transaction プログラムを closure と predicate の依存グラフに分ける注釈 (利用者が手で付ける、または静的解析)。read/write set の宣言は不要。 |
| Transaction Healing | 要する (静的解析) | stored procedure の operation 依存を実行前に静的解析で取り出す (LLVM Pass)。ad-hoc transaction は通常の OCC 扱い。 |
| IC3 | 要する (最大) | stored procedure の piece 分解と SC-graph の静的解析。表名・列名を API で明示。可換演算は API で宣言。 |
| Doppel | 要さない | read/write set の宣言は無い。transaction は 1 shot の手続きで、値は型付き、演算は型ごとに定義される。分割対象は実行時に標本で自動選定。 |
| BOHM | 要する | write set を実行前に決める (宣言・解析・試走の推測)、transaction 全体を一括投入、batch 処理。read set は任意 (あると版参照の最適化が使える)。 |
| Lomet (TCM) | 要さない | 事前宣言なし。read-only 宣言による最適化 (§VIII.D、未実装) だけが宣言を要する。 |
| PWV | 要する (最大) | 決定的実行。read/write set (または保守的な範囲) を事前に知る。data-flow 解析で piece の DAG に分解。abort しうる文を制限。batch 処理。 |

### 1. MV3C (4 件)
- `mv3c-predicate-graph-repair` (protocol-core): predicate graph と closure による部分再実行。
- `mv3c-write-write-conflict-tolerance` (optimization): write-write conflict で早期 abort せず blind write を許す。副作用に版連結リストの伸び。
- `mv3c-attribute-level-validation` (optimization): 列単位の validation。OMVCC 由来。
- `mv3c-result-set-fixing` (optimization): 失敗した query の結果集合を修正。既定は無効。

注意: 評価の実装は **1 スレッドで transaction の片を交互に実行して並行を模擬したもの** (§7)。多コアの実測ではないので、`workloads_effective` の「効く」は多コアの throughput の主張ではなく、単一スレッド模擬での処理時間の主張として読む。図の値は本文に無いので数値はほぼ書けなかった。

### 2. Transaction Healing (5 件)
- `healing-transaction-healing` (protocol-core), `healing-access-cache`, `healing-false-invalidation-elimination`, `healing-validation-order-rearrangement`, `healing-independent-txn-merged-validate-write` (いずれも optimization)。
- 検証順序の並べ替えは付録 G の Fig. 20・Table 6 で ablation がある (約 25% 向上、deadlock 防止 abort 率 0.16 対 0.01 未満)。access cache と局所コピーは Table 1 で低 contention の overhead が測られている (Normal 1139K → 1087K → 2% 未満の低下)。

### 3. IC3 (5 件)
- `ic3-constrained-interleaving` (protocol-core), `ic3-optimistic-constraint`, `ic3-commutative-operation`, `ic3-rendezvous-piece`, `ic3-online-analysis-transitional-scgraph` (optimization)。
- Fig. 16 が factor analysis: 楽観的制約 +32%、可換演算 +40%、rendezvous piece +23% (TPC-C 1 warehouse か、それを変えた混合、64 core)。
- 効かない条件: 1 transaction が 1 表しか触らない workload (§3.4)。

### 4. Doppel (4 件)
- `doppel-phase-reconciliation` (protocol-core), `doppel-splittable-commutative-operations`, `doppel-contention-classification`, `doppel-adaptive-phase-scheduling` (optimization)。
- 効く: INCR1 の hot key 100% で OCC の 38 倍 (Fig. 8)。効かない・悪化: split 中の hot data の read が最大 20 ms 待つ (Table 3)。書き込みの少ない workload では split せず OCC と同等。

### 5. BOHM (5 件)
- `bohm-separated-cc-and-execution` (protocol-core), `bohm-partitioned-cc-threads`, `bohm-batching`, `bohm-read-set-version-annotation`, `bohm-batch-low-watermark-gc` (optimization)。
- 効く: SmallBank 低 contention 40 thread で 3M 対 1M txn/s 超 (§4.3 の本文)、長い read-only を混ぜたときの版走査の省略。効かない: 10RMW の高 contention で locking に劣る、低 contention で OCC に及ばない (版作成の overhead)。

### 6. Lomet ほか TCM (4 件)
- `tcm-timestamp-range` (protocol-core), `tcm-block-instead-of-abort`, `tcm-range-deadlock-detection`, `tcm-read-only-transaction-optimization` (optimization)。
- 評価は 100 行・20 client・Core2 Duo (2 core) の小さな benchmark 1 種のみ (3305 対 3656 txn/s、abort 率 1.018% 対 0.428%)。block の再開規則は実装せず block は abort にしているので、「abort の代わりに block する」効果は測られていない。多コア・大規模の主張の根拠にならない。

### 7. PWV (3 件)
- `pwv-early-write-visibility` (protocol-core), `pwv-rvp-commit-protocol`, `pwv-coarse-grained-conflict-specification` (optimization)。
- 効く: 40 core、abort 文が無いとき OCC・Locking・RC の 15・7・3 倍 (Fig. 3b)。悪化: abort 文の位置 (commit position) が後ろになるほど低下 (Fig. 4b)。

## `effect_category` の内訳 (30 件)
- cpu-cache: 5 (Doppel の core と splittable、BOHM の core・partitioned・batching。Doppel の分割は hot record の cache line 競合の回避)
- delay-on-conflict: 10 (IC3 の 4 (core・楽観的制約・可換演算・rendezvous)、TCM の 2、Healing の 2 (検証順序・融合。境界事例)、PWV の core、Doppel の phase scheduling)
- version-lifetime: 2 (BOHM の read set 版参照付与と低水位標 GC)
- none: 13 (repair 系 (MV3C の 4、Healing の 3 = core・access cache・偽 invalidation)、IC3 の online analysis、Doppel の分類、TCM の deadlock 検出と read-only 最適化、PWV の RVP と coarse)

「repair 系」は、validation 失敗後の再実行量を減らす技法で、3 分類に当てはまらないので none とした (MV3C と Healing)。none の根拠は各カードの `effect_category_note` に書いた。

## JSONL に入れなかった候補 (理由つき)
- IC3 の deadlock-prone SC-cycle の除去 (§3.3): 本文を読んでいないため。§1 に「deadlock-prone な SC-cycle を piece の結合で除く」とあるのみ。
- IC3 の user-initiated abort への対応 (cascading abort、accessor list の abort bit、§4.4): 数値評価が無く、機構の拡張のため (読んだ本文の範囲で §4.4 は 1 段落)。
- IC3 の secondary index の実装 (§5.3)、durability (§6.6): 未読。
- Healing の epoch ベース commit protocol (§4.3): Silo の流用であり、独自の技法ではない。範囲クエリと phantom の扱い (§4.7): Silo 流の leaf version の流用。
- MV3C の interoperability (§4)、garbage collection の記述 (§6): OMVCC の流用で、独自の最適化として独立に説明されていない。
- Doppel の RUBiS 移植 (§6-7)・§8.8: 未読。
- BOHM の実行 thread 間の再帰的な依存解決 (§3.3.1): core に含めた。
- Lomet の SI・Read committed・分散 transaction の討論 (§VIII.B, C, E): 未実装・未評価の討論で、最適化として独立には出していない。read-only の最適化 (§VIII.D) だけは題名付きの項なのでカードにした (「討論のみ」と明記)。
- PWV の推測実行による read/write set の決定 (§3.1 付近)、intra-transaction parallelism: core に含めた。§4.5-4.7 の議論は未読。

## 読み取りで気づいた点 (カード外)
- 「事前宣言を要するか」を横に並べると、多コアの実測を持つ 4 本 (Healing・IC3・BOHM・PWV) はすべて実行前の静的解析・宣言・batch のいずれかを要し、Doppel だけが要さない (代わりに演算の可換性の宣言が要る)。TCM は要さないが、多コアの評価がない。
- MV3C は本文の評価が多コアでないため、他の多コア論文と数値を並べて比べない方がよい。
- PWV の最適性の証明 (Section 1 に主張) は、読んだ範囲に本文の所在が無い。
