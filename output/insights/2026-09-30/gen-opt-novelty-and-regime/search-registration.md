# 検索の事前登録 — gen-opt の新しさの地図 (md_23)

- 登録: 2026-09-30 JST、本 wave の索引検索 (OpenAlex・arXiv) を 1 本も実行する前。登録者: md_23 wave の親 (manager)。
- 規則の正本: `docs/related-work/README.md` 7.7 (不在主張の成立条件)。本登録はその規則を本 wave の主張へ当てたもの。
- この file は commit 後に内容を変えない。変更は末尾の「改訂」節に追記し、新しい ID・理由・時刻 (date / mtime で採る) を残す。
- 既存の検索記録との関係: `output/insights/2026-09-29/gen-opt-literature-cards/` (md_2) は「CC の個々の最適化」を OpenAlex Q01〜Q09 で集めた。
  本登録は対象が違う — **CC を自動で特化・合成・選択する研究** (学習・探索・LLM・組み合わせ) を集める。md_2 のカード 295 枚は
  §4 の「既知の手作りの機構」の照合にだけ使い、md_2 の検索を再走しない。

## 1. 主張と、それを支える根拠・検索式 (結果を見る前に固定)

| 主張 ID | 主張の種類 | 根拠 | 支える検索式 |
|---|---|---|---|
| N1 | 最も近い先行研究の表: 何を自動化し、どの空間で探し、正しさをどう保証し、どの条件で何に対して何倍か | 原典本文 (節・図・表番号つき)。検索は論文を見つける経路にすぎない | 名指しの起点 (§2 の R1) + §3 の全式の `検出`・`近傍` |
| N2 | 各先行研究の表現範囲 (方策・構成が選べる動作の集合) | 原典本文の定義節 | 検索と無関係 |
| N3 | N2 の範囲の外にあり、izanagi の関数単位の合成なら作れる仕組みの型の列挙 (無ければ無いと書く) | N2 と izanagi の hook の定義 (`orchestrator/campaign/silo_function_policy_api.hh` と coder spec)。各型が手作りの既知機構か (md_2 のカード集合の範囲で) を併記 | 検索と無関係 (内部の分析) |
| N4 | 世界の不在 (限定つき): **LLM・プログラム合成・進化的なプログラム探索が、取引の並行性制御の判断 (競合の検出・待ち・abort・順序付け) を実装するコードを生成し、取引処理の性能を評価した研究** は、索引と式と cutoff を明記した範囲で未検出 | 検索の全件判定 | QL3, QL4, QL5, QL6 (OpenAlex) と A1, A2, A4 (arXiv) |
| N5 | 世界の不在 (限定つき): N4 の条件に加えて **生成物の直列化可能性 (または宣言した分離水準) を探索の反復の中で機械検査した研究** は、同じ範囲で未検出 | N4 と同じ走行の判定 (N4 の `検出`・`近傍` を追加条件で読み直す) | N4 と同じ |

- N4・N5 は `docs/related-work/README.md` 7.7.3 の RW2 (1 索引ごとの query-result 全件確認) までしか名乗らない。DBLP を使わない (§3.3) ので RW3 は名乗らない。
  表現は「索引 X を検索式 Y で cutoff Z まで確認した範囲では未検出」に限り、索引名・式 ID・cutoff を落とした短縮を書かない。
- 支える式のどれかに `要裁定` が残る間、その主張は「未確定」とする (`要裁定` を不在側へ倒さない)。
- 支える式のどれかが `未完走` なら、その主張はその索引について「未完走」とし、完走した索引だけの範囲で書く。
- N1 の表に載せる基準 (「近い先行」): (a) 取引の並行性制御 (または取引の実行順序) の設計・選択・構成・調整を、学習・探索・LLM・規則のいずれかで
  **自動化** するか、workload に合わせて CC を **組み合わせて特化** する枠組みを提案し、(b) 取引処理の throughput を実測している。
  (a) だけ・(b) だけのものは `近傍` として一覧に残す。

## 2. 母集合を作る経路

- **R1 (名指しの起点、md_23 が指定)**: Polyjuice (OSDI 2021、arXiv 2105.10329)、CCaaLF→NeurCC (arXiv 2503.10036、SIGMOD 2026)、
  Tebaldi (SIGMOD 2017)、CormCC (取引型・partition ごとに CC を組み合わせる。書誌は検索で確定する)、ADRS / Barbarians at the Gate (arXiv 2510.06189)。
  既存記録にある近傍: ATCC (arXiv 2603.13906)。名前は手がかりであり、実在と内容は原典で確かめる。
- **R2 (索引検索)**: §3 の式。
- **R3 (参考文献の追跡)**: R1 の各論文の関連研究節と参考文献から、§1 の「近い先行」を満たすものを拾う。
- **R4 (補助探索)**: Web 検索エンジンによる語検索 (親または子の WebSearch)。**R4 は母集合の外** — N4・N5 の不在の根拠に数えない。
  見つかった論文は N1 の表に載せうる (見つけた経路を `補助探索` と明記)。R4 の検索語と日時は ledger に残す。

## 3. 索引検索 (R2) の登録

### 3.1 OpenAlex

- 要求: `https://api.openalex.org/works?filter=title_and_abstract.search:<式>,publication_year:2010-2026&per-page=200&cursor=*`
  を cursor 終端まで。`select=id,display_name,publication_year,primary_location,locations,type,cited_by_count,doi,ids`。要求間隔 5 秒。
  User-Agent に利用者のメールアドレスを入れない。
- 成否: 応答が JSON で `meta.count` と `results` を持つこと (状態コードでは判定しない)。各 page の実要素数は `results` の個数。
  cursor 終端までの distinct `results[].id` を `meta.count` と照合する。重複 occurrence は消さず記録する。
- 429: `retryAfter`+5 秒待って同じ page を最大 5 試行。取れなければその式は `未完走`。`未完走` の式は、10 分後に 1 式ずつ同じ ID で再走する (run2)。
  run2 も完走しなければ `未完走` のまま確定し、該当主張は §1 の規則に従う。
- 打ち切り: `meta.count` が 5,000 を超える式は取得せず `未完走 (過大)` と記録し、判定に使わない。
  式の構文エラー (JSON でない・error field) は走行無効とし、直した式を新しい ID で登録してから走らせる。
- venue 選別: QL1・QL2 だけ、md_2 の §3.1 と同じ正規表現
  (`VLDB|Management of Data|SIGMOD|Operating Systems Design|Operating Systems Principles|EuroSys|European Conference on Computer Systems|Data Engineering|Innovative Data Systems`、
  大文字小文字無視、`locations[].source.display_name` のいずれか、無ければ `primary_location`) に加えて `USENIX|Annual Technical Conference|CIDR|Conference on Innovative Data Systems`
  に一致する hit だけを判定に回す。一致しない hit は件数だけ残す。QL3〜QL6 は preprint が主なので venue 選別をせず全件判定する。

| ID | 式 (title_and_abstract.search) | 狙い |
|---|---|---|
| QL1 | `"concurrency control" AND (learned OR learning OR "reinforcement learning" OR "machine learning" OR neural)` | 学習で CC を特化 (Polyjuice・NeurCC 系) |
| QL2 | `"concurrency control" AND (hybrid OR mixed OR modular OR composable OR composition OR federated OR "partition-based" OR adaptive)` | CC の組み合わせ・切替 (Tebaldi・CormCC 系) |
| QL3 | `("concurrency control" OR "transaction processing" OR "transaction scheduling" OR serializability OR serializable) AND ("large language model" OR "large language models" OR LLM OR LLMs OR "language model" OR "language models")` | LLM × 取引処理 |
| QL4 | `("concurrency control" OR "transaction processing" OR "transaction scheduling" OR serializability OR serializable) AND ("program synthesis" OR "code generation" OR "genetic programming" OR "evolutionary search" OR "evolutionary algorithm" OR synthesize OR synthesized OR synthesizing)` | 合成・進化 × 取引処理 (LLM 以前を含む) |
| QL5 | `("large language model" OR "large language models" OR LLM OR LLMs) AND (database OR DBMS OR "database system" OR "database systems" OR "storage engine") AND (evolve OR evolving OR evolutionary OR "algorithm discovery" OR AlphaEvolve OR OpenEvolve)` | LLM で DB 内部を進化 (語彙差を拾う広い組) |
| QL6 | `("large language model" OR "large language models" OR LLM OR LLMs) AND ("systems research" OR "algorithm discovery" OR "evolutionary search" OR AlphaEvolve OR OpenEvolve OR FunSearch) AND (scheduling OR scheduler OR transaction OR transactions OR concurrency)` | ADRS 系 (LLM の進化で系のアルゴリズム) |

### 3.2 arXiv

- 要求: `http://export.arxiv.org/api/query?search_query=<式>&start=<k>&max_results=100&sortBy=submittedDate&sortOrder=ascending`、
  要求間隔 5 秒。cutoff: `submittedDate:[199101010000 TO 202609302359]` を式に AND で付ける。
- 成否: Atom XML で `opensearch:totalResults` が実在すること。各 page の実要素数は `feed/entry` の個数 (`itemsPerPage` を使わない)。
  非最終 page は実要素数 100、最終 page は位置と実要素数から `totalResults` に到達すること。
  空ボディ・`totalResults` 不在・到達しない走行は無効とし、同じ ID で 10 分後に 1 回再走する。それでも無効なら `未完走`。
- 打ち切り: `totalResults` が 3,000 を超える式は `未完走 (過大)`。

| ID | 式 (search_query。空白は `+`、句は `%22` で送る) | 狙い |
|---|---|---|
| A1 | `all:"concurrency control" AND (all:LLM OR all:"large language model" OR all:"language models" OR all:synthesis OR all:evolutionary OR all:"genetic programming")` | LLM・合成 × CC |
| A2 | `(all:serializability OR all:serializable OR all:"transaction processing" OR all:"transaction scheduling") AND (all:LLM OR all:"large language model" OR all:"language models") AND (all:evolve OR all:evolutionary OR all:synthesis OR all:"code generation" OR all:discovery OR all:generate)` | LLM × 直列化・取引 × 生成 |
| A3 | `all:"concurrency control" AND (all:learned OR all:learning OR all:"reinforcement learning" OR all:neural)` | 学習型 CC |
| A4 | `(all:LLM OR all:"large language model" OR all:"large language models") AND (all:"systems research" OR all:"algorithm discovery" OR all:AlphaEvolve OR all:OpenEvolve OR all:"evolutionary search") AND (all:database OR all:transaction OR all:transactions OR all:scheduling OR all:concurrency)` | ADRS 系 |

### 3.3 使わない索引

- DBLP: 2026-09-29 に検索 API が bot 判定 HTML を HTTP 200 で返した記録がある (F1057)。本 wave は使わない。したがって RW3 は名乗らない。
- 母集合の外 (網羅を保証しない): SIGMOD / PVLDB / OSDI / SOSP などの venue 本体の年次一覧、ACM Digital Library、書籍、技術報告、学位論文、
  非英語文献、索引化されていない実装・アーティファクト、および R4 の Web 検索。

### 3.4 陽性対照 (偽陰性の検査)

走行後に次が該当式の結果に現れるかを記録する。現れなくても主張の成否は変えず、偽陰性の証拠として成果物に書く (陽性対照が出ても網羅の証拠にはしない)。

| 対照 | 期待する式 |
|---|---|
| Polyjuice (arXiv 2105.10329) | QL1 または A3 |
| CCaaLF / NeurCC (arXiv 2503.10036) | QL1 または A3 |
| ADRS (arXiv 2510.06189) | A4 (または QL6) |
| Tebaldi (SIGMOD 2017) | QL2 |
| CormCC | QL2 |

## 4. 判定

- 判定語 (7.7.5): `検出` / `近傍` / `除外` (理由コード) / `要裁定` / `未完走`。題名と要旨で判定し、要旨が無いものは Semantic Scholar の batch API か原典で補う。
  要旨が取れず題名で決められないものは `要裁定` とし、題名だけで除外しない。
- N4 の `検出` の条件 (3 つとも): (i) LLM・プログラム合成・進化的なプログラム探索が **コードまたはプログラムを生成**する、(ii) 生成物が
  **取引の並行性制御の判断** (競合の検出・待ち・abort・順序付けのいずれか) を実装する、(iii) **取引処理の性能** (throughput・latency・makespan) を評価する。
  2 つだけ満たすものは `近傍`。N5 は N4 の `検出`・`近傍` を (iv) **生成物の直列化可能性 (または宣言した分離水準) を探索の反復の中で機械検査する** で読み直す。
- 除外の理由コード: `other` (DB・取引以外) / `dist` (分散・geo が主で単一ノードの CC 判断を生成しない) / `hw` (専用 HW が前提) / `verify` (検証・テスト手法のみで生成しない) /
  `theory` (理論のみ) / `bench` (評価のみ) / `sql` (SQL 生成・質問応答など CC 以外の LLM×DB) / `knob` (設定値の調整のみでコードを生成しない。N1 の `近傍` には残しうる)。
- 生の応答は repo の外 (`/work/SFC/tanab/tmp/md23-gen-opt-novelty-2026-09-30/raw/`) に置き、repo には SHA-256・件数・判定だけを置く。
- 停止条件: 登録した全式の全 hit を判定したら索引検索を止める。結果を見て語を足すときは新しい ID で「改訂」節に登録してから走らせ、元の式の結果と混ぜない。

## 5. 原典を読む順番

1. R1 の全部 (Polyjuice・NeurCC・Tebaldi・CormCC・ADRS・ATCC)。
2. §3 の N4 の `検出`・`近傍` の全部。
3. R3 で拾った「近い先行」。発表年の新しい順。
4. QL1・QL2・A3 の `検出` のうち「近い先行」を満たすもの。発表年の新しい順。
読む深さ: 表現範囲の定義節・正しさの扱い・評価の主要表図。読まなかった節は表に書く。

## 改訂

(なし)
