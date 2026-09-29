# 検索の事前登録 — 並行性制御の最適化の文献カード化 (gen-opt md_2)

- 登録: 2026-09-29 JST、OpenAlex の論文検索を 1 本も実行する前 (venue の source ID の照会だけ実施済み)。
- 登録者: md_2 wave の親 (manager)。
- この file は登録後に内容を変えない。変更は末尾の「改訂」節に追記し、新しい ID と理由・時刻を残す。

## 1. 何を主張し、何を主張しないか (主張 → 根拠の対応)

| 主張 ID | 主張の種類 | 根拠 | 検索との関係 |
|---|---|---|---|
| A | カードの中身 (前提・効果・実装の要点・効くと見込まれる workload) | 原典本文。節・図・表の番号を添える | 検索は論文を見つける経路にすぎず、中身の根拠にしない |
| B | 「CCBench にある / 無い」 | `external/ccbench` の現行 pin (`68106660686232781bca3be792a750d3e19d7a8a`) の source。走査した file と語をカードごとに記録する | 検索と無関係。**内部の不在** (母集合 = pin の `cc/` と `include/`) であり、世界の不在ではない |
| C | カードにした文献の母集合の作り方 | §2 の経路 R1〜R4 の記録 | 母集合は網羅でない。「文献に無い」「新しい」は本 wave では主張しない |
| D | 段 A の試し候補の上位 3 と別枠 | §5 の選定規則をカードに当てた結果 | 検索と無関係 |

本 wave は `docs/related-work/README.md` 7.7 の「世界の不在」を一切主張しない。カード集合に無い最適化について
「文献に無い」とは書かず、「本 wave のカード集合に無い (範囲: 本登録の R1〜R4)」とだけ書く。

## 2. 母集合を作る経路

- **R1 (起点)**: CCBench が実装する protocol の原典 (Silo、TicToc、MOCC、Cicada、ERMIA、SSN、MVTO、2PL 系は
  "Staring into the Abyss" PVLDB 2014 を原典として扱う) と、CCBench 論文 (PVLDB 13(13) 2020) 自身。
  「CCBench にある」側のカードを作るため。
- **R2 (izanagi の既存資料)**: `docs/related-work/cc-candidates-2026-09-17.md` の候補表で母集合内 (単一ノード in-memory の
  汎用 CC) の行、`docs/related-work/literature-map/izanagi_literature_map.csv` の CC 行、
  `output/insights/2026-09-29/vhash-related-work/README.md` §11.1 の本文を読んだ論文のうち CC の最適化を提案するもの。
- **R3 (索引検索、OpenAlex)**: §3 の検索式 Q01〜Q09。
- **R4 (参考文献の追跡)**: 次の anchor の関連研究節と参考文献から、§4 の包含条件を満たす論文を拾う。
  anchor = CCBench (PVLDB 2020) §7・§8、"Staring into the Abyss" (PVLDB 2014)、
  "Opportunities for Optimism in Contended Main-Memory Multicore Transactions" (STOv2、PVLDB 2020)、
  "An Empirical Evaluation of In-Memory Multi-Version Concurrency Control" (PVLDB 2017)、Cicada (SIGMOD 2017) の関連研究節。

## 3. 索引検索 (R3) の登録

- 索引: OpenAlex works API (`https://api.openalex.org/works`)。DBLP は使わない (2026-09-29 に bot 判定 HTML を
  HTTP 200 で返した記録がある — memory / F1057)。arXiv API は使わない (母集合の外に置く)。
- 要求の形: `filter=title_and_abstract.search:<式>,publication_year:2008-2026`、`per-page=200`、`cursor=*` で終端まで。
  `select=id,display_name,publication_year,primary_location,locations,type,cited_by_count,doi`。要求間 1 秒以上。
  User-Agent に利用者のメールアドレスを入れない。
- 成否の判定: 応答が JSON で `meta.count` と `results` を持つこと。状態コードでは判定しない。
  各 page の実要素数は `results` の個数。distinct `results[].id` の数を `meta.count` と照合する。
- 打ち切り: `meta.count` が 5,000 を超える式は取得せず「未完走 (過大)」と記録し、判定に使わない。
  式の構文エラー (JSON でない・error field) は走行無効とし、直した式を新しい ID で登録してから走らせる。
- 生の応答本文は repo の外 (`/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md2-literature-cards/raw/`) に置き、
  repo には SHA-256 と件数・判定だけを置く。

| ID | 式 (title_and_abstract.search) |
|---|---|
| Q01 | `"concurrency control" AND ("in-memory" OR "main-memory" OR "main memory")` |
| Q02 | `"concurrency control" AND (multicore OR "multi-core" OR "many-core" OR manycore)` |
| Q03 | `"optimistic concurrency control" AND (contention OR abort OR aborts OR validation)` |
| Q04 | `(multiversion OR "multi-version" OR MVCC) AND ("in-memory" OR "main-memory" OR "main memory") AND (transaction OR transactions)` |
| Q05 | `(transaction OR transactions) AND ("high contention" OR hotspot OR "hot records" OR contended) AND ("in-memory" OR "main-memory" OR multicore OR "multi-core")` |
| Q06 | `"concurrency control" AND ("garbage collection" OR "version management" OR "version chain")` |
| Q07 | `"concurrency control" AND (reordering OR batching OR "transaction scheduling" OR "transaction repair")` |
| Q08 | `"concurrency control" AND (timestamp OR timestamps) AND ("in-memory" OR "main-memory" OR multicore OR "multi-core")` |
| Q09 | `("two-phase locking" OR 2PL OR "lock manager") AND ("in-memory" OR "main-memory" OR multicore OR "multi-core")` |

### 3.1 venue の選別 (取得後、判定前に機械で行う)

いずれかの `locations[].source.display_name` (無ければ `primary_location`) が次の正規表現に一致する hit だけを
判定に回す (大文字小文字は無視):
`VLDB|Management of Data|SIGMOD|Operating Systems Design|Operating Systems Principles|EuroSys|European Conference on Computer Systems|Data Engineering|Innovative Data Systems`。
一致しない hit は「venue 外」として件数だけ残す (判定しない)。source が 1 つも無い hit は「venue 不明」として件数を残す。
SIGMOD Record・VLDB Journal・ICDE Workshops のような同名の非対象誌も正規表現に掛かりうるが、機械では落とさず判定で除外する。

### 3.2 判定 (題名、必要なら要旨)

判定語は 7.7.5 に合わせる: `検出` = §4 の包含条件を満たす / `近傍` = 一部だけ満たす / `除外` (理由コード) /
`要裁定` (題名・要旨で決められない)。理由コード: `dist` 分散・geo / `disk` ディスク・SSD 主体 / `hw` GPU・FPGA・HTM・
NVM・RDMA が前提 / `learn` 学習型 CC / `verify` 検証・テスト手法 / `theory` 分離水準・理論 / `bench` 評価・benchmark
のみで最適化を提案しない / `other` DB 以外・CC 以外 / `nonvenue` 対象外の同名誌 (SIGMOD Record、VLDB Journal ほか)。
**決定論的・事前宣言・一括処理の手法は除外しない** (本 wave の主題「取引の並べ替え・一括処理」に入る)。
カード上で「前提が合わず Silo に入らない」側に分ける。

## 4. 包含条件 (カードにする論文)

(1) 単一ノードの多コア・インメモリ (main-memory) の取引処理を対象とし、(2) 並行性制御の機構 (待ち、abort の削減、
timestamp、validation、版の管理と GC、取引の並べ替え・一括処理、lock 実装) を提案または独立の技法として評価し、
(3) serializable を主張する (SI など他の水準は、その旨をカードに書いて含める)。

## 5. 読む順番と上限 (結果を見る前に固定)

1 論文あたり機構の節まで読む (評価は表・図番号を引く分だけ)。上限は 45 本。順番:
1. R1 の全部。
2. R2 のうち §4 を満たすもの。
3. R4 の anchor 自身 (STOv2、MVCC 評価 2017、Abyss)。
4. R3 の `検出` のうち、主会場 (PVLDB・SIGMOD・PACMMOD) で 2019 年以降のもの。発表年の新しい順。
5. R3 と R4 の残りの `検出`。OpenAlex の `cited_by_count` の多い順。
上限に達したら残りは「対象・未カード化」として書誌だけを一覧に残す。

## 6. 段 A 候補の選定規則 (md_2 の条件を固定)

候補にできるのは次の全てを満たすカード:
(a) CCBench の現行 pin に無い (Silo に無いだけでなく、同じ機構が他 CC のフラグ・関数として存在しない)。
    他 CC にあって Silo に無いものは「CCBench にある (Silo へ持ち込む移植候補)」として別に数える。
(b) 関数単位の空間 (`orchestrator/campaign/silo_function_policy_api.hh`・`silo_function_policy_coder_spec.md` の
    3 hook、観測 = abort 要因・同一 tuple の試行番号・乱数・worker 内の txn 間履歴) で書ける見込みがある。
(c) 今の検査器 (YCSB の点読み・点書きの trace から G2 を含む閉路を検査) で正しさを見られる。
(d) 勝ちそうな workload を YCSB の既存パラメタ (rratio・zipf skew・tuple 数・max_ope・rmw・thread 数) で作れる。
除外: 静的 backoff (固定の待ち時間。既知で済んでいる)。
順位付け: (b) を満たす見込みの強さ → 原典の性能根拠 (表・図番号つきの効果の大きさ) → (d) の作りやすさ、の順。
(b) を満たさないが (a)(c)(d) を満たすものは「関数単位の空間を広げれば書ける」別枠とし、何を広げるか
(観測の追加・hook の追加・機構の開放) を添える。

## 改訂

- 改訂 1 (2026-09-29 09:52 JST、Q01〜Q09 の 1 回目の走行の直後、hit の判定前): 1 回目は要求間隔 1.2 秒で
  Q01・Q02・Q04・Q05・Q06・Q08 が HTTP 429 で途中終了した (Q01 は 730 件中 200 件で停止)。7.7.6 に従いこの 6 本の
  1 回目を無効とし、1 件も判定しない。式は変えず、同じ ID の 2 回目の走行 (run2) として要求間隔 5 秒、429 のときは
  60 秒待って同じ page を最大 5 回まで取り直す形で再取得する。完走した Q03・Q07・Q09 の 1 回目 (run1) は有効とし、
  run2 では取り直さない。1 回目の生応答は `raw/run1/` に残す。
- 改訂 2 (2026-09-29 10:40 JST、R3 の venue 一致 98 件の判定と、R4 の anchor 3 本 (CCBench・Cicada・MVCC 評価 2017) の
  参考文献走査の後、カードを 1 枚も作る前): §4 を満たす論文が R1〜R4 の合計で §5 の上限 45 本を超える見込みになった。
  上限で落とす論文を §5 の順番で選ぶと、読む前に選別が入るので、**上限を撤廃し、§4 を満たす論文は全件カードにする**。
  本文を取得できなかった論文は、要旨・公開 source・izanagi の既存調査記録のどれから取ったかをカードに明記し、深さを
  「要旨のみ」「source のみ」として分ける。§5 の順番は読む順番としてだけ残す。§3.2 の判定語と理由コードは R3 に限らず
  R2・R4 の候補にも同じに当てる (例: 学習型 CC は `learn` で除外)。
- 訂正 (10:10 JST 追記): 改訂 1 と改訂 2 に書いた時刻は推定で、誤っていた。file の mtime による実時刻は次のとおり。
  登録と seal 09:47:35、1 回目の走行の終了 09:49:40、改訂 1 の追記 09:49:41〜09:50:02 の間 (直後の再取得 script の mtime が 09:50:02)、
  2 回目の走行の終了 10:01:44、venue 選別 10:02:20、要旨取得 10:04:04、改訂 2 の追記 10:06:40、R3 判定 file の書き出し 10:07:13。
  R3 の判定は改訂 2 の前に venue 一致一覧 (10:02:20) と要旨 (10:04:04) を読んで行い、判定 file への書き出しが改訂 2 の後になった。
  改訂 2 は読む上限の撤廃 (選別をしない方向) であり、判定規則と包含条件は変えていない。
  wave の開始 gate (10:59 ではなく 09:59:15) は 1 回目の走行 (09:49) より後に打った。
- 訂正の訂正 (10:11 JST): 直前の行の「10:59 ではなく」は誤記で、意味を持たない。開始 gate の時刻は 09:59:15 である。
