# 検索の記録 (md_23)

登録: `search-registration.md` (commit `a28f9111d`、2026-09-30 19:47:26 JST)。本 file は走行の記録と判定を持つ。

## 1. R4 補助探索 (母集合の外。N4・N5 の不在の根拠に数えない)

実行: ADRS 系の原典を読んだ Claude の子 (2026-09-30 19:49〜19:57 JST)。時刻は子が区切りごとに取った `date` と呼び出し順から割り当てたもので、1 分未満は推定。
#19・#20 は arXiv API を WebFetch 経由で叩いた (子の script 実行が worktree の保護で拒否されたため)。**登録した索引検索 (R2) とは別の走行で、R2 の代わりにしない。**

| # | 時刻 | 経路 | 検索語 |
|---|---|---|---|
| 1 | 19:50 | WebSearch | `ADRS github transaction scheduling OpenEvolve evaluator get_opt_seq_cost` |
| 2 | 19:50 | WebSearch | `LLM generated concurrency control algorithm transaction processing evolutionary search` |
| 3 | 19:50 | WebSearch | `AlphaEvolve OpenEvolve database concurrency control lock manager` |
| 4 | 19:51 | WebSearch | `LLM synthesizes concurrency control protocol serializability checker throughput` |
| 5 | 19:51 | WebSearch | `"concurrency control" LLM agent evolve code OCC 2PL benchmark TPC-C YCSB 2026` |
| 6 | 19:51 | WebSearch | `Glia AI systems design automated LLM agents` |
| 7 | 19:52 | WebSearch | `LLM evolutionary code search database system component buffer pool replacement policy OpenEvolve` |
| 8 | 19:52 | WebSearch | `LLM-driven synthesis of database index structure code evolution learned index AlphaEvolve` |
| 9 | 19:52 | WebSearch | `LLM agent rewrites DBMS kernel code performance optimization transaction lock contention arXiv` |
| 10 | 19:53 | WebSearch | `large language model generate concurrency control code in-memory database throughput serializable evolved` |
| 11 | 19:53 | WebSearch | `"ADRS" concurrency control OR "lock manager" OR "transaction" LLM evolved policy 2026` |
| 12 | 19:53 | WebSearch | `PolicySmith LLM synthesize heuristics systems caching congestion control Dwivedula` |
| 13 | 19:53 | WebSearch | `LLM evolutionary search RocksDB compaction policy OR LSM-tree OR B-tree code generation evaluation` |
| 14 | 19:53 | WebSearch | `LLM-guided program evolution query optimizer join order heuristic PostgreSQL AlphaEvolve-style` |
| 15 | 19:53 | WebSearch | `Vulcan instance-specialized verifiable systems heuristics LLM-driven search` |
| 16 | 19:54 | WebSearch | `LLM concurrency control policy search Polyjuice policy table large language model transactions` |
| 17 | 19:54 | WebSearch | `NeurDB learned concurrency control evolutionary algorithm filtering refinement phase` |
| 18 | 19:54 | WebSearch | `LLM transaction scheduling database follow-up OpenEvolve SMF makespan deterministic database batch` |
| 19 | 19:54 | arXiv API | `abs:"concurrency control" AND (abs:LLM OR abs:"large language model")` (11 件、該当なし) |
| 20 | 19:54 | arXiv API | `(abs:OpenEvolve OR abs:AlphaEvolve OR abs:ShinkaEvolve OR abs:"AI-Driven Research") AND (abs:database OR abs:transaction OR abs:DBMS OR abs:index OR abs:lock)` (7 件) |
| 21 | 19:55 | WebSearch | `LLM generated contention management backoff abort policy transactional memory OR database evolved code` |
| 22 | 19:55 | WebSearch | `"AI-driven" discovery concurrency control protocol database LLM agents verify serializability fuzzing 2026` |
| 23 | 19:55 | WebSearch | `audreyccheng adrd github AI-driven research for databases buffer query rewrite index selection` |
| 24 | 19:56 | 閲覧 | ADRS ブログ一覧 ucbskyadrs.github.io/blog/ の全 25 本の題目 (DB 関連は Bespoke OLAP・取引 scheduling・LLM-SQL・Bauplan の 4 本) |
| 25 | 19:56 | WebSearch | `LLM generates variants of Silo TicToc 2PL concurrency control CCBench evaluation` |
| 26 | 19:57 | WebSearch | `automatic synthesis of concurrency control with large language models workload-specific throughput anomaly checker` |

子の報告: LLM と並行性制御の組み合わせで当たったのは、いずれも「LLM agent **のための**並行性制御」(ATCC 2603.13906、CoAgent 2606.15376、S-Bus 2605.17076、2606.17182) だった。
「LLM が取引の並行性制御の判断を実装するコードを生成し性能を評価した研究」は、この 26 本の範囲では見つからなかった (子の記述。不在を一般化しない)。

## 2. R2 索引検索 (OpenAlex・arXiv)

取得 script: Codex author (子木 `md23-author`、最終 commit `ce3e91059`) が書き、親が repo の外 (`/work/SFC/tanab/tmp/md23-gen-opt-novelty-2026-09-30/probe/fetch_search.py`) へ写して login で実行した。
生の応答 (entity body の bytes・header・URL) は repo の外の `search/out/raw/<run>/<式>/` に、台帳は `search/out/ledger-<run>.json` にある (repo には入れていない)。

### 2.1 arXiv (A1〜A4、run1、2026-09-30 21:3x〜21:41 JST): 4 式とも完走

| 式 | totalResults | 取得した entry | distinct | 検出 | 近傍 | 除外 | 要裁定 (run1 の要旨判定) |
|---|---|---|---|---|---|---|---|
| A1 | 16 | 16 | 16 | 0 | 2 | 14 | 0 |
| A2 | 11 | 11 | 11 | 2 | 2 | 7 | 0 |
| A3 | 26 | 26 | 26 | 0 | 5 | 21 | 0 |
| A4 | 23 | 23 | 23 | 2 | 1 | 17 | 3 |

- 判定: 題名と要旨で Claude の子 (opus、21:4x〜21:5x) が登録 §4 の規則で判定した 76 行を `search-judgments-arxiv-run1.jsonl` に置く (親が件数を jq で検算して一致)。
  重複を除いた work 単位では、検出 2 本 (2510.06189 ADRS v3、2512.14806 Let the Barbarians In)、近傍 8 本、要裁定 3 本。
- 要裁定 3 本は原典の本文で解消した (Claude の子 sonnet、PDF を文字化して grep、2026-09-30 21:5x)。
  - **2605.09764 LEVI → 検出**: ADRS の 7 課題に "Txn Sched" を含む。Table 3 の逐語 "Offline transaction scheduling. Given a batch of transactions, the evolved heuristic reorders them to reduce key conflicts and shorten the makespan."。
    登録 §4 の (ii) は「順序付け」を含むので、ADRS と同じく検出とする (子は「CC プロトコルの実装ではない」として近傍を推したが、登録の文言に揃えた)。本文に serializ の一致 0 件 → N5 は満たさない。
  - **2605.19633 optimize_anything → 除外 (other)**: 課題に取引処理が無い (唯一の "transaction" は CUDA の memory transaction)。
  - **2608.05651 Relay, Don't Route → 近傍**: 評価課題に "TXN Scheduling" があるが、本文に課題定義・評価器・指標の記述が無く (ii)(iii) を本文で確かめられない。
    N5: 本文に記載なし。課題の出所 (ADRS の取引 scheduling) の評価器は ADRS の原典と公開 repo で直列化検査が無いことを確かめている (`prior-work.md` の ADRS 行) ので「満たさない」とする。
- 陽性対照 (登録 §3.4): Polyjuice 2105.10329 (A3)、NeurCC 2503.10036 (A3)、ADRS 2510.06189 (A2・A4) は現れた。
  **偽陰性の記録**: 最も近い LLM × DB の先行 2604.06566 (AI-Driven Research for Databases、R4 で発見) は A1〜A4 のどれにも現れなかった。
- 取得 script の小さな欠陥: hit 一覧の `index` 欄に索引名でなく式の番号が入る。判定には `query_id` を使ったので影響しない。

### 2.2 OpenAlex (QL1〜QL6): 未完走で確定

| run | 時刻 (JST) | 結果 |
|---|---|---|
| run1 | 21:3x〜21:41 | 6 式とも 1 page 目が HTTP 503 "Anonymous search is paused while the search cluster recovers from heavy load" → `invalid` (改訂 1 で無効) |
| run2 | 21:54 | 503 を再試行しない取得 script の欠陥で 1 秒で `invalid` (改訂 2 で無効) |
| run3 | 22:04〜22:24 | 503・429 を retryAfter+5 秒で合算 5 試行。QL1・QL2・QL5・QL6 は `incomplete-unavailable`、QL3 は 503 の後 "Gateway timeout ... query_timeout" で `invalid`、QL4 は 414 件中 200 件で `incomplete-unavailable` |

- 登録 (改訂 2) どおり、OpenAlex の枝は `未完走` で確定する。QL4 の部分取得 200 件は判定しない。
- したがって N4・N5 は arXiv の枝だけで書き、RW2 の表現は「arXiv を式 A1・A2・A4 で submittedDate 2026-09-30 まで確認した範囲」に限る。OpenAlex・DBLP は母集合に入っていない。

### 2.3 主張 N4・N5 の結論

- **N4 (LLM・合成・進化が取引の CC の判断を実装するコードを生成し、取引性能を評価した研究の不在): 不成立。** arXiv の A2・A4 で 3 本を検出した (2510.06189、2512.14806、2605.09764)。
  3 本とも ADRS の取引 scheduling 課題 (1 操作 1 単位時間の模擬器で、取引の並べ順を返す関数を進化させ makespan を評価する) である。
  登録の (ii) が「順序付け」を含むのでこれを検出に数えた。結果を見た後で (ii) を狭めない。
- **N5 (N4 に加え、生成物の直列化可能性を探索の反復の中で機械検査した研究の不在): arXiv を式 A1・A2・A4 で submittedDate 2026-09-30 まで確認した範囲では未検出 (RW2、arXiv の 1 索引)。**
  N4 の検出 3 本・近傍のいずれも (iv) を満たさない (要旨と、ADRS 系は原典の本文・公開 repo の評価器で確認)。OpenAlex は未完走、DBLP は不使用なので RW3 は名乗らない。
  無限定の「先行なし」「世界初」は書かない (7.7.3)。
