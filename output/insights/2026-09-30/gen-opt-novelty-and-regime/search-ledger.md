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

(取得 script の完成後に走らせ、ここへ記録する)
