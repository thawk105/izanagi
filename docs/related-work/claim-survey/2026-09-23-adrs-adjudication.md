# 2026-09-23 — `2510.06189` (ADRS / Barbarians at the Gate) を一次資料で判定した記録 (凍結)

- **作成日:** 2026-09-23
- **入力 commit:** `65fd1422f` (本 wave の base、`65fd1422fa1cfa6289c3c194078ff8e604b69857`)
- **入力 digest:** 下記 input path 群の内容は入力 commit `65fd1422f` の blob そのものである。
  一次資料だけは repo の外にあり、取得元 URL・取得日・取得した bytes の sha256・整形後の文字数で束縛する。
- **入力 path:** `docs/related-work/README.md` の 7.0 と 7.2 と 7.6 と 7.7 /
  `docs/related-work/claim-survey/2026-08-26-inventory.md` の 3 /
  `docs/related-work/claim-survey/2026-08-26-cir-cvn-adjudication.md` /
  `docs/related-work/claim-survey/2026-09-03-sysinsight-adjudication.md` の 2.1 と 4 /
  `output/insights/2026-09-21/vldb-direction/gap-analysis.md` の 2 /
  `output/insights/2026-09-22/comsys2026-manuscript/manuscript.tex` の第 1 節 (位置づけの 1 文)
- **一次資料:** arXiv `2510.06189` (Cheng, Liu, Pan ほか 17 名、*Barbarians at the Gate: How AI is Upending Systems Research*)。
  abstract ページの投稿履歴は v1 2025-10-07、v2 2025-10-08、v3 2025-10-10。
  取得元 https://arxiv.org/abs/2510.06189 (45,513 B、sha256 `c33a7a0f08fdc22e50e4ec89e4b0ccd8f00b1e2f6e39e3b7a358c04f95f89693`) と
  https://arxiv.org/html/2510.06189 (本文は `2510.06189v3` を指す、422,177 B、sha256 `d2af4dcafe04266cd9416823d708ba37a9f20d2176b96d7dc6af7905aae0ea1b`)。
  取得日 2026-09-23。HTML から script / style / math 要素を除きタグを落として整形した本文は 128,449 文字。
- **文献 cutoff:** 変わらない。本記録は新しい掃引を行っておらず、
  `docs/related-work/literature-map/` の cutoff (2026-07-10) を動かさない。
- **規則の正本:** `docs/related-work/README.md` の
  「7.7 主張軸別の調査状態と、不在主張の成立条件」
- **依頼:** D2227 項 5 (位置づけの 1 文の 3 条件に ADRS が当たるかを正典で判定し、結果で 1 文を残すか書き直す。判定対象は 3 条件と関連する主張に絞る)。

> **凍結物である。** 書いた後は上書きしない。更新は新しい日付のファイルで行う。
> 進行中の可変状態の正本は `docs/worklog.md` の末尾エントリであり、ここではない。

---

## 0. 何を決めたか、何を決めていないか

**決めたこと:** ComSys 原稿と論文ストーリーが使う位置づけの 1 文

> 本調査では、LLM が、トランザクションの並行性制御を対象として、アクション空間自体をコードで拡張する (固定した原始操作語彙の中で生成するのではなく) 既存例を発見していない。

の 3 条件に ADRS が当たるかを、一次資料を読んで条件ごとに決めた。**判定は `近傍` (条件の一部だけ満たす) である。**
あわせて `docs/related-work/README.md` 7.2 へ ADRS のエントリを足し、7.0 の逆引き索引に 1 行を足し、7.6 の 2 に短縮形の注意を 1 文足した。

**決めていないこと:**

- **軸 1 の検索記録の成熟度は `RW1` のまま動かない。** 本記録は 1 件の一次資料を読んだだけで、
  索引・検索式・母集合の登録 (7.7.4) を一切行っていない。**これは新しい検索ではない。**
- **本記録は新しい世界の不在を一切作らない。** 本記録が自分で測って書く「無い」は、すべて
  この 1 論文という列挙可能な母集合の中の不在 (7.7.2 でいう内部の不在) である。
  「ADRS を加えても 1 文の反例は無い」「ADRS 以外に近い研究は無い」とは書かない。
- **`2026-08-26-inventory.md` の軸 1 分類 pilot の 29 行を変えない。**
  ADRS はその凍結された母集合に含まれていないため、件数保存則にも触れない。本記録の判定は pilot の表の外の 1 件である。
- **`docs/paper-story/` の版は書き換えていない** (凍結物)。
- **ADRS の他の事例 (クラウドの spot 選択、MoE の expert 配置、LLM-SQL ほか) は判定していない。** 判定対象は 1 文の 3 条件と、それに関わる 5.4 節 (transaction scheduling) だけである。
- **実装面の差分はゼロである。**

## 1. 判定に使った規則

- 争点の成否は、一次資料に**正の記述があるか**で決める。語の不在だけを根拠にしない。
- 内部の不在を書くときは母集合と走査語を同じ場所に置く (7.7.2)。
- 1 文の 3 条件を判定の単位にし、あわせて軸 1 の pilot が定めた包含条件 A〜D (`2026-08-26-inventory.md` §3) を属性として記録する。
  1 文の反例になるのは、**3 条件すべてに正の証拠がある**研究である。
- 「トランザクションの並行性制御」の中身は、SysInsight の判定 (`2026-09-03-sysinsight-adjudication.md` §2.1) が使った 3 要素 (競合検出・待機・abort) で読む。
  取引の実行順序を決める scheduling を並行性制御に含めるかという**定義の選択は一次資料からは決まらない**。外部の DB の知識 (古典的な scheduler の用法など) は一次資料の主張として採らない。

**引用の性質について。** 本記録で `>` を使った英文は arXiv HTML (v3) からの**転記**であり、「逐語」ではない。
整形で空白・改行を正規化し、数式要素 (計算量の記号) は落ちている。語列は変えていない。

---

## 2. 条件ごとの判定

| 1 文の条件 | 判定 | 根拠 (一次資料の正の記述) |
|---|---|---|
| LLM が | **満たす** | 5.4 節: `a two-model ensemble of 80% Gemini 2.5 Pro and 20% OpenAI o3` を OpenEvolve の生成器にする |
| トランザクションの並行性制御を対象として | **一部だけ満たす** | 対象は取引の実行順序を決める scheduling (`given a set of transactions, find a schedule that minimizes the conflicts`)。競合を減らす目的は並行性制御と隣接するが、進化させた方策が返すのは順序である。方策は順序を決めるために競合の費用を見積もるが、実行中の取引の競合を検出して待たせる・中断させる判断を書く正の記述は無い |
| アクション空間自体をコードで拡張する (固定した原始操作語彙の中で生成するのではなく) | **一部だけ満たす** | 方策は任意の Python コードとして生成され、固定した原始操作語彙に閉じない (図 7 の offline 方策は整列・挿入・対交換・無作為再始動を組み合わせる)。ただし拡張されるのは順序を計算する手続きで、対象へ出す動作の種類 (取引の順序) は変わらない |

**結論: `近傍`。** 3 条件のうち「LLM が」だけを満たし、残る 2 条件は一部だけ満たす。**3 条件すべてに正の証拠がある研究ではないので、1 文の反例ではない。**
ただし、取引の順序決定を並行性制御に含め、方策のコードを書くことをアクション空間の拡張と読む広い読みでは、3 条件の境界に最も近い研究である。
この読みの選択は一次資料からは決まらず、**「反例ではない」は 1 文の条件の狭い読みに依存する**ことを落としてはならない。

軸 1 の包含条件 A〜D (属性の記録、pilot の表の外の 1 件):

| A (対象が並行性制御) | B (設計・アクション空間をコードで生成・拡張) | C (ワークロード条件づけ) | D (正しさ検証器をループ内に持つ) | 強さ | 極性 |
|---|---|---|---|---|---|
| △ (取引の scheduling。定義による) | ✓ (「生成」。対象の動作語彙は拡張しない) | ✗ (5 trace の makespan の合計を 1 つの方策で最小化する。ワークロード記述子を条件にした生成は無い) | ✗ (評価器は makespan を計算する模擬器。直列化可能性を検査する正の記述は無い) | 部分接地 | 競合 (最も近い近傍) |

### 2.1 対象 — 取引の scheduling であって、並行性制御の判断ではない

> This research problem Cheng et al. (2024) aims to find efficient schedules to reduce conflicts for transactional workloads.

> The problem we aim to solve is: given a set of transactions, find a schedule that minimizes the conflicts and improves the throughput.

> In the online setting, we assume that the transaction order is fixed once the schedule is determined (i.e., committed transactions cannot be rollbacked).

図 7 の 2 つの方策 (online で再発見された SMF と、offline で進化した方策) は、いずれも `return total_cost , schedule` / `return best_cost , best_seq` で**順序を返す**。
方策は順序を組むために、未配置の取引を置いたときの makespan の増分 (競合の費用) を見積もる (`compute_incremental_cost`、`get_opt_seq_cost`) が、
実行中の取引の競合を検出して待たせる・中断させる判断は現れない (図 7 の転記の全行を目視で確認)。

**直列化可能性は問題の制約として 1 回名指されるだけである。**

> transaction scheduling is a complex optimization problem, where we need to consider groups of operations, dependencies across operations, and correctness constraints (e.g., serializability).

### 2.2 評価 — 単位時間の模擬器の makespan

> We use the Python simulator from the SMF paper Cheng et al. (2024), which assumes that each operation takes one unit of time. The simulator calculates the makespan of a given transaction schedule and also provides statistical bounds on the makespan of the schedule for a given workload.

> We measure total makespan over five traces from the OLTP benchmarks used in the original paper (Epinions, SmallBank, TPC-C, TAOBench, YCSB) with 500 transactions each.

論文全体の立場として、ADRS の verifier は性能の評価器である:

> verification reduces to running these software artifacts against predefined workloads and measuring performance.

**評価器が直列化可能性を検査する正の記述は無い。** これは D を ✗ とした根拠であり、「ADRS の方策は直列化可能性を壊す」とは言っていない
(順序を返す方策の出力を模擬器が実行する形なので、壊しうるかどうかは模擬器の意味論による。模擬器の実装は取得していない)。

### 2.3 結果 (1 文の判定には使わないが、原稿の記述の照合に使う)

> In the online setting, the best discovered policy is SMF. We note that OpenEvolve is able to rediscover this algorithm from a random scheduling baseline. It is likely that this is a case of contamination, i.e., the model was trained upon the SMF paper.

> In the offline setting, OpenEvolve discovers a novel algorithm than reduces makespan by 34% compared to SMF.

差分分析 (`output/insights/2026-09-21/vldb-direction/gap-analysis.md` §2) の要約「OpenEvolve で transaction scheduling を扱い、既存最良 SMF を再発見、offline で makespan −34%」は、上の 2 つの記述と一致する。

### 2.4 語の全件走査 (母集合を併記した内部の不在)

**母集合 = 上記 HTML v3 を整形した本文 128,449 文字の全体 (節・図の転記・参考文献・付録を含み、先頭切り出しをしていない) に対し、
小文字一致の件数は `concurrency control` 0 / `concurrency` 0 / `isolation` 0 / `abort` 0 / `deadlock` 0 / `two-phase` 0 / `2pl` 0 / `mvcc` 0 /
`silo` 0 / `ccbench` 0 / `polyjuice` 0 / `serializab` 1 (§2.1 の転記の 1 か所) / `transaction` 41。**
`lock` の 18 件 (部分一致を含む) は、クラウドの spot 選択の事例のコード識別子 6 件 (`lock_on_demand` 2・`is_locked`・`can_unlock`・`unlock`・`lock_margin`)、
MoE の事例のコード識別子 7 件 (`idx_in_block` 3・`block_id` 2・`is_even_block` 2)、`blocks` 3 件 (`building blocks` 1・同じ MoE のコードのコメント 2)、`blocking` 1 件、
`lock in working code` 1 件で、いずれも取引の lock ではない。
`commit` の 4 件は、§2.1 の `committed transactions cannot be rollbacked` 1 件、図 7 のコメント `Commit update global state` 1 件、参考文献 2 件である。
**この不在は、この 1 論文の中の不在である。世界の不在ではない。** 語の不在だけで判定しておらず、§2.1〜§2.2 の正の記述が条件を決めている。

---

## 3. 位置づけの 1 文への帰結

- **1 文は逐語で残す。** 1 文は「本調査では … 発見していない」という、1 文の根拠となった調査についての記述であり、ADRS はその調査の後に確認した研究である。
  本判定は 1 文を強めない — 「ADRS を含めても反例は無い」「調べ尽くした」とは読ませない。
- **原稿と版が「判定していない」と書いた箇所は、判定結果 (`近傍`、3 条件のうち LLM だけを満たし、残る 2 条件は一部だけ) に置き換えてよい。**
  置き換えるときは「狭い読みに依存する」ことと、ADRS が取引の実行順序の方策を LLM がコードで進化させた研究であることを同じ場所に書く。
- **破れる短縮形 (ADRS が反例になりうる):** 「LLM がトランザクション処理の方策をコードで合成した例はない」
  「LLM が OLTP の性能のためにコードを進化させた例はない」「LLM による取引の scheduling の合成は初めて」。
  1 文の 3 条件のうち「並行性制御を対象として」または「アクション空間自体の拡張」のどちらかを「取引に関わる」「コードを書く」へ緩めると、ADRS が当たる。
- **残る差別化 (1 文の範囲内):** 並行性制御の実装 (競合検出・待機・abort の判断) のコードを書き換えること、直列化可能性の検証を毎反復の関門にすること、
  実機の many-core 実装で測ること。これらは差別化の**記述**であって、優越の主張ではない。

## 4. この記録の限界

- **一次資料 1 件しか読んでいない。** 網羅率について何も言わない。
- **HTML v3 だけを読んだ。** v1 / v2 との差分、PDF 版との差分は確認していない。
- **SMF の原論文 (Cheng ほか、VLDB 2024) と模擬器の実装を読んでいない。** 模擬器が直列化可能性をどう扱うか、SMF が並行性制御とどう組み合わされるかは、ADRS の本文からは決まらない。
- **公開 artifact (OpenEvolve の設定・進化した方策の全文) を取得していない。** 図 7 の転記は論文に載った範囲である。
- **語の走査は文字列一致である。** 同義の言い換えは拾えない。
- **判定は親が行い、独立の read-only レビュー 1 本 (Codex) を受けた** (記録は `output/insights/2026-09-22/comsys2026-manuscript/README.md` の改訂 2)。
