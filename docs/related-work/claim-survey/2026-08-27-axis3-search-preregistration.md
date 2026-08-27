# 2026-08-27 — 軸 3 (説明可能性) の文献検索 事前登録 (凍結)

- **作成日:** 2026-08-27
- **入力 commit:** `343b8f5a` (本 wave の base)
- **入力 digest:** 下記 input path 群の内容は入力 commit `343b8f5a` の blob そのものである。
  索引の実測は同 commit の
  `docs/related-work/claim-survey/2026-08-27-axis3-index-measurements.md` が持つ。
- **入力 path:** `docs/related-work/README.md` の 7.6 と 7.7 /
  `docs/related-work/claim-survey/2026-08-26-inventory.md` /
  `docs/related-work/claim-survey/2026-08-27-axis1-search-preregistration.md` /
  `docs/related-work/claim-survey/2026-08-27-axis3-index-measurements.md` /
  `docs/paper-story/2026-08-26.md` の §3 /
  `docs/decisions.md` の D350・D351・D384・D1015・D1016・D1121・D1122・D1123・D1155
- **文献 cutoff:** 本文書が定義する。§2 を見よ。
- **規則の正本:** `docs/related-work/README.md` の
  「7.7 主張軸別の調査状態と、不在主張の成立条件」

> **凍結物である。**
> **この文書に検索結果を書き戻してはならない。** 実行の記録は別の日付の凍結物が持つ (§10)。
> 進行中の可変状態の正本は `docs/worklog.md` の末尾エントリであり、ここではない。

---

## 0. この文書は何であって、何でないか

**これは登録であって、正式な検索実行ではない。** 本文書は軸 3 について、7.7.4 が要求する
母集合定義・索引・検索式・cutoff を固定したものである。

**ただし「結果を一切見ずに固定した」とは言えない。**
本文書は**索引の構文と取得量を測る pilot を経てから登録している。**
その pilot には、**本文書が登録する DBLP の枝 query と query-equivalent なものが 8 本含まれ、
その返却件数が親へ露出した** (§11.2 に全件を列挙する)。
**したがって本文書は「cardinality pilot 後の登録」であり、純粋な pre-result preregistration ではない。**
**将来この登録を根拠に主張を書くときは、この限定を落としてはならない。**

**正式な完走記録は 1 件も作っていない。** どの query についても §7 の完走述語を満たす
走行を行っておらず、レコードの採否判定も 1 件も行っていない。

**本文書は軸 3 の成熟度を動かさない。軸 3 は `RW0` のままである** (§1.4)。

**本文書は世界の不在を作らない。** 7.7.3 により `RW0` の軸は新しい不在方向の表現を
一切使えない。§11.2 が開示する露出済み cardinality についても、
**それを未検出の証拠として使ってはならない。**

**本文書は 7.7 の下位にある。** `claim-survey/README.md` が定めるとおり、
ここに置いた判定は `docs/related-work/README.md` と同格の正本ではなく、
**矛盾したら `docs/related-work/README.md` が勝つ。**
7.7.4 自身が「`RW3` を名乗るには、次を事前に登録し、実行後に記録を残す」と書いて
軸別の登録を日付付き成果物へ委譲している。

**§5.1・§7・§8.5 は一般手続きの新しい正本ではなく、D1121 / D1122 / D1123 の
軸 3 への具体化である。** 一般規則としての正本はそれらの決定であり、本文書ではない。
**本文書と決定が食い違ったら決定が勝つ。**
(なお「主キー正規化・完走述語・amendment 規則を軸別文書ではなく 7.7 本体へ集約すべきか」は
D1015 の射程に関わる論点であり、本 wave の scope 外として worklog へ送った。)

**§13.1 に、`RW3` を名乗る前に閉じなければならない blocking な未決項目を列挙する。**
**§13.2 は、記録するが `RW3` の前提ではない観測項目である。**
**現時点の本登録だけでは `RW3` に到達できない。**

## 1. 軸 3 と分類契約

### 1.1 軸 3 とは何か

軸 3 = `docs/paper-story/2026-08-26.md` の §3 の 3「説明可能性」。同節は軸 3 を**二層**で書く。

- **事実層:** 双射検査。**対象とした campaign 群について**成立しており、
  bench-first screening campaign は対象外、値の改変に対する深い一致検査も未強化。
- **仮説層:** 機序を言語化する層。設計凍結のみで未実装。

**片層だけを覆う包含条件を書くと、母集合が軸の定義より狭くなる。** 本登録は両層を覆う。

### 1.2 包含条件

- **A — 対象 (`A_scope`):** 自動生成・探索・選択・最適化されたプログラム、実装、
  システム構成、またはそれらを評価する実験 campaign を対象にする。
- **B — 事実層・証拠束縛:** artifact、設定、workload、実行、測定値、主張の間を
  機械可読な provenance、proof chain、lineage、trace などで束縛する。
- **C — 事実層・一致検査:** B の束縛について、再実行、完全性・整合性検査、
  値や artifact の改変検出、双射、replay verification などを扱う。
- **D — 仮説層:** 観測された性能・挙動について、原因、ボトルネック、寄与、機序、
  とくに「なぜ速い / 遅いか」を言語または構造化表現として生成・検証する。
- **X — 主題性 (`X_axis_primary`):** B / C / D のいずれかが、その論文の
  **主要な研究課題または主要な貢献**である。

### 1.3 判定語彙の真理条件

7.7.5 の判定語彙を、軸 3 について次のとおり一意に定める。
**`matched_conditions` (B / C / D のどれを満たしたか) を必ず記録する** (§10)。

| 語 | 真理条件 |
|---|---|
| `検出` | `B ∨ C ∨ D` が成立する。強さは下表で分ける |
| `近傍` | `B ∨ C ∨ D` は成立しないが、B / C / D のいずれかの**構成要素だけ**を満たす。すなわち、説明・証拠束縛・一致検査を扱うが、その対象が「自動生成・探索・最適化された artifact またはその評価実験」でも「機構として本節が要求する束縛・検査・機序生成」でもない場合 |
| `除外` | `検出` でも `近傍` でもない。**理由コードを必ず付ける** |
| `要裁定` | メタデータまたは一次資料が足りず、上の 3 つを決められない |
| `未完走` | **query または軸の状態であって record の判定ではない** (§7.3) |

**強さ (`grounding_strength`) は `検出` の内部で分ける。**

| 値 | 条件 |
|---|---|
| `直接接地` | `X_axis_primary` が成立する |
| `部分接地` | `¬X_axis_primary ∧ (B ∨ C ∨ D)` |
| `非接地` | `¬(B ∨ C ∨ D)` |

- **`A_scope` は `scope_match` という別属性として記録し、強さの判定には使わない。**
  Izanagi と対象が一致するかは、軸への接地の強さとは別の問いである。
- **`layer` を `fact` / `hypothesis` / `both` として別に記録する。**
- **極性**は 7.7.5 の 5 語 (`競合` / `方法論的祖先` / `外部補強` / `反面教師` /
  `正しさ側の道具`) をそのまま使う。
- **`要裁定` を不在側へ倒してはならない。題名だけで A〜D を確定しない。**
  **索引が返した題名の語が別分野の同綴語と衝突していても、それだけで `除外` にしない。**

**個別論文が両層を同時に満たすことは要求しない。**
登録母集合は事実層 query 群と仮説層 query 群の双方を完走しなければならない。
これが担保するのは「**登録した F / H 語列の片側を実行上落とさない**」ことだけであり、
**意味的な事実層・仮説層の全語彙被覆を含意しない** (D384)。

### 1.4 なぜ本登録で軸 3 は `RW0` のままなのか

7.7.3 の `RW1` は「**候補文献や横断掃引の成果はある**が、検索式・母集合・全除外記録を
再現できない」を条件とする。**本文書は正式な完走記録を 1 件も作っておらず、
判定した候補が 0 件である。**

**軸 3 が既に持っている資産は `RW1` を与えない。** `2026-08-26-inventory.md` は
索引 26 エントリの本文を全文走査し、軸 3 に接地する 4 エントリと精読ノート 1 本を記録した。
**しかしこれは 7.7.2 が言う「内部の不在」の実測であって、外部文献の横断掃引ではない。**
同棚卸し自身が、その走査を実行したうえで次の 2 文を書いている。

> 空白域 3 は軸 3 (説明可能性) に踏み込むが、**軸 3 は `RW0` である。**
> 7.6 の 3 番目を軸 3 の調査済みの証拠として使ってはならない。

> **軸 3 を目的とした検索を一度も行っていない。** 証拠連鎖・provenance・実験再現性の
> 系譜を `RW0` から動かすには、7.7.4 の母集合登録から始める必要がある。

さらに同棚卸しの表は、`RW1` の 3 軸 (1・2・5) と `RW0` の 2 軸 (3・4) を、
接地エントリ数でも精読ノート数でもなく「**軸を目的とした一次資料の深掘り**」の有無で分けている
(軸 2 は 5 エントリ・1 本で `RW1`、軸 3 は 4 エントリ・1 本で `RW0`)。
26 エントリ走査は 5 軸すべてに一律に行われた棚卸しなので、これを探索資産に数えると
軸 4 も同時に `RW1` になり、表が成立しない。

**`RW0` と `RW1` の許可表現の差は 1 点だけである。**
7.7.3 は**どちらの段階でも新しい不在方向の表現を禁じる。**
差は「既存の限定付き文を、出典節・掃引日・監査前である旨とともに**逐語引用**できるか」であり、
`RW1` だけがこれを許す。**本文書はどちらの段階でも内容が変わらない。**

## 2. cutoff — 索引固有の日付欄へ共有の暦境界を当てる

D1121 に従う。**日単位の同一 cutoff は 3 索引に課せない** — DBLP には日付の範囲指定が無い。

> **上限境界 = 暦年境界 2026-12-31。** 各索引は自分の日付欄にこの同じ暦境界を当てる。
>
> - **arXiv:** `submittedDate` が `199101010000` 以上 `202612312359` 以下
>   (下限は arXiv 開設の 1991-08 より前に置いた閉区間であり実質的に下限なし。
>   開いた下限の構文は未実測なので登録しない)。
> - **OpenAlex:** `to_publication_date=2026-12-31`。下限は置かない。
> - **DBLP:** 年 facet を使わず全年を取得し、record の `year` が 2026 以下であることを
>   client 側で判定する。`year` を持たない record は捨てず `要裁定` とする。
>
> **上限境界が落とすのは、その暦境界より後の日付を持つレコードだけである。**
> 取得日より後で 2026-12-31 以前の日付を持つレコードは境界の内側であり、
> 取得の瞬間に索引へ存在すれば母集合に入る。

**この境界は work 単位で一様ではない。** 同じ研究が索引ごとに違う年で記録されていれば、
一部の索引の record だけが残る。この非一様性は §5 の work-family 台帳で可視化する。

**母集合の定型名は次とする。**

> **「arXiv の要旨、OpenAlex の題名・要旨、DBLP の書誌・題名という索引別の操作集合に、
> 共有の暦境界を当てた登録取得集合の和」**

**「同一 cutoff の 3 索引の和集合」という短縮を使ってはならない** (D1121)。

## 3. 概念ブロックと query catalog

### 3.1 概念ブロック (74 語)

各語に**固定 ID** を与える。ID は 1-origin、ブロック字 1 文字 + 2 桁ゼロ詰めである。
**query ID から送信語を復元するときは、下表の語をそのまま (ハイフンを含めて) 使う。**

**T — 対象 (12 語)**

| ID | 語 | ID | 語 |
|---|---|---|---|
| `T01` | `program synthesis` | `T07` | `autonomous research` |
| `T02` | `code generation` | `T08` | `auto-tuning` |
| `T03` | `software optimization` | `T09` | `algorithm configuration` |
| `T04` | `configuration tuning` | `T10` | `compiler optimization` |
| `T05` | `design space exploration` | `T11` | `query optimization` |
| `T06` | `automated experimentation` | `T12` | `program repair` |

**F — 事実層の機構 (18 語)**

| ID | 語 | ID | 語 |
|---|---|---|---|
| `F01` | `proof chain` | `F10` | `experiment tracking` |
| `F02` | `evidence binding` | `F11` | `research object` |
| `F03` | `provenance` | `F12` | `build provenance` |
| `F04` | `data lineage` | `F13` | `run manifest` |
| `F05` | `traceability` | `F14` | `artifact manifest` |
| `F06` | `audit trail` | `F15` | `environment capture` |
| `F07` | `reproducibility` | `F16` | `checksum validation` |
| `F08` | `repeatability` | `F17` | `software bill of materials` |
| `F09` | `replicability` | `F18` | `reproducible build` |

**H — 仮説層の機構 (19 語)**

| ID | 語 | ID | 語 |
|---|---|---|---|
| `H01` | `mechanistic explanation` | `H11` | `counterfactual explanation` |
| `H02` | `causal explanation` | `H12` | `interpretability` |
| `H03` | `explanation generation` | `H13` | `explainability` |
| `H04` | `performance explanation` | `H14` | `sensitivity analysis` |
| `H05` | `root cause analysis` | `H15` | `feature importance` |
| `H06` | `bottleneck diagnosis` | `H16` | `critical path analysis` |
| `H07` | `performance attribution` | `H17` | `performance model` |
| `H08` | `explainable optimization` | `H18` | `what-if analysis` |
| `H09` | `causal profiling` | `H19` | `variance decomposition` |
| `H10` | `performance debugging` | | |

**O — 出力 (8 語)**

| ID | 語 | ID | 語 |
|---|---|---|---|
| `O01` | `explanation` | `O05` | `audit log` |
| `O02` | `rationale` | `O06` | `evidence bundle` |
| `O03` | `provenance graph` | `O07` | `proof certificate` |
| `O04` | `execution trace` | `O08` | `diagnostic report` |

**V — 正しさ・完全性 (9 語)**

| ID | 語 | ID | 語 |
|---|---|---|---|
| `V01` | `bijection` | `V06` | `artifact verification` |
| `V02` | `consistency check` | `V07` | `attestation` |
| `V03` | `integrity check` | `V08` | `mutation testing` |
| `V04` | `tamper detection` | `V09` | `end-to-end verification` |
| `V05` | `replay verification` | | |

**W — 性能文脈 (8 語)**

| ID | 語 | ID | 語 |
|---|---|---|---|
| `W01` | `performance` | `W05` | `workload` |
| `W02` | `latency` | `W06` | `scalability` |
| `W03` | `throughput` | `W07` | `many-core` |
| `W04` | `benchmark` | `W08` | `transaction processing` |

**community strata の由来。** F と H は単一 community の語彙では足りない。

| 由来 | 採った語 |
|---|---|
| scientific-workflow / 再現性 | `F07`〜`F11`、`F13`〜`F15` |
| SE / supply-chain | `F06`、`F12`、`F16`〜`F18`、`V07` |
| HCI / XAI | `H11`〜`H13`、`H15` |
| performance / MLSys | `H04`〜`H10`、`H14`、`H16`〜`H19` |
| 自動化された対象側 | `T08`〜`T12` |

**採らなかった語と理由。**

- `transparency` — 一般語すぎて機構を特定せず、`除外` を大量に生む。
- `explainable AI` — `H12` / `H13` で覆われ、かつモデル説明へ寄りすぎる。
- `replication` / `reproduction` — **本コーパスで多義だからである。**
  `replication` はデータ複製・状態機械複製の意味で分散システム文献に大量に現れ、
  再現性の意味とは別物である。**登録すると `除外` が大量に生じる。**
  再現性側の概念は `F07` (`reproducibility`) / `F08` (`repeatability`) /
  `F09` (`replicability`) / `F18` (`reproducible build`) を登録語として直接置くことで扱う。
  > **これは設計上の選択であって、「既存語が同じ集合を覆う」という主張ではない。**
  > **3 索引の語幹処理は互いに異なるので、`replicability` の登録が `replication` を
  > 覆うとは言えない** — arXiv は句を完全一致で当て、DBLP は前方一致なので
  > `replic*` は両方を拾うが、OpenAlex のステミングが同じ挙動をする保証は無い。
  > **この非対称による取りこぼしは §9 と §12 に限界として残す。**

**上記 3 件の判断は、§11 の cardinality 露出より前に行った。**

### 3.2 登録する枝

7.7.4 は「狭い積集合だけでなく、語彙差を拾う広い二項組合せも事前に登録する」と要求する。

| 枝 ID | 論理式 | 役割 |
|---|---|---|
| `Q1` | T ∧ F ∧ O | 事実層の狭い積集合 |
| `Q2` | T ∧ H ∧ O | 仮説層の狭い積集合 |
| `Q3` | T ∧ F | 事実層、O の語彙差を拾う広い二項 |
| `Q4` | T ∧ H | 仮説層、O の語彙差を拾う広い二項 |
| `Q5` | F ∧ V | 値改変・整合性の側から事実層を拾う |
| `Q6` | H ∧ W | 「なぜ速いか」を性能の側から拾う |
| `Q7` | F ∧ W | provenance・再現性を性能実験の側から拾う |
| `Q8` | H ∧ V | 説明の検証・正しさの側を拾う |
| `Q9` | F ∧ H | 事実層と仮説層を接続する研究を拾う |
| `Q10` | T ∧ V | 対象側から一致検査 (条件 C) を拾う |

### 3.3 canonical request bytes (3 索引共通の規約)

7.7.4 は「完全な query 文字列、escaping」を要求する。次を固定する。

- 文字符号化は UTF-8。
- percent-encoding は RFC 3986 に従い、**予約文字と非 ASCII だけ**を符号化する。
  16 進は**大文字**とする (`%22`、`%20`、`%5B`)。
- **二重符号化を禁じる。** 既に符号化された文字列を再度符号化しない。
- 空白の表現は索引ごとに固定する。**arXiv は `+`** (application/x-www-form-urlencoded)、
  **OpenAlex と DBLP は `%20`。**
- parameter の順序を固定する。arXiv は `search_query` → `start` → `max_results`。
  OpenAlex は `filter` → `per-page` → `cursor`。DBLP は `q` → `format` → `h` → `f`。
- 二重引用符は `%22`、`[` は `%5B`、`]` は `%5D`、`(` と `)` は符号化しない。

**表示上の改行とインデントは送信文字列の一部ではない。**
§3.4 と §3.5 のブロック定義は読みやすさのために改行してあるが、
**送信前に次の正規化を行った結果が送信文字列である。**

1. 改行 (`LF`、`CR`) を空白 1 個へ置換する。
2. 連続する空白を 1 個へ畳む。
3. 先頭と末尾の空白を除去する。
4. `(` の直後と `)` の直前の空白を除去する。

**この 4 段を適用した一行文字列を「復号形の正規形」と呼ぶ。**

**登録する期待 request (`canonical_template`) は query 単位の単一 URL ではなく、
「固定部分 + ページ遷移規則」として登録する。**
ページごとに位置パラメータが変わり、OpenAlex の `cursor` は
実行前に値が分からないためである。

| 索引 | 固定部分 (全ページ共通) | ページごとに変わる部分 | 照合規則 |
|---|---|---|---|
| arXiv | endpoint、`search_query` の符号化後 bytes、`max_results=200` | `start` | 固定部分は byte 一致。`start` は 0 から 200 刻みの等差であること |
| OpenAlex | endpoint、`filter` の符号化後 bytes、`per-page=200` | `cursor` | 固定部分は byte 一致。`cursor` は初回が `*`、以降は**直前の応答の `meta.next_cursor` と byte 一致**すること |
| DBLP | endpoint、`q` の符号化後 bytes、`format=json`、`h=100` | `f` | 固定部分は byte 一致。`f` は 0 から 100 刻みの等差であること |

**hash の対象 bytes を一意に定める。**

各 query ID について、**位置パラメータの値を placeholder へ置換した完全な URL**
(以下 `canonical_template`) を作り、その UTF-8 bytes の SHA-256 を登録する。

- placeholder は arXiv が `start={POS}`、DBLP が `f={POS}`、OpenAlex が `cursor={CUR}` とする。
  **placeholder は parameter を除去せず、区切りも保つ** — 値だけを `{POS}` / `{CUR}` へ置換する。
- parameter の順序は §3.3 の規約どおりで、**placeholder も本来の位置に置く。**
  例 (arXiv): `https://export.arxiv.org/api/query?search_query=<符号化後>&start={POS}&max_results=200`
- **`canonical_template` の bytes は percent-encoding 適用後のものとする**
  (二重符号化しない)。

**照合 (§7.1 の条件 0) は次の 2 段で行う。**

1. 実際に送った URL の位置パラメータの値を placeholder へ戻した文字列が、
   `canonical_template` と byte 一致し、その SHA-256 が登録 digest と一致する。
2. 位置パラメータの値が上表の遷移規則に従う。
   **OpenAlex の `cursor` の照合方向を固定する** — 直前応答の JSON から
   `meta.next_cursor` を UTF-8 文字列として取り出し、**§3.3 の規約で percent-encode した
   bytes** が、送信 URL の `cursor` parameter の bytes と一致すること
   (逆方向に復号して比較しない)。初回ページは `cursor` の値が `*` の符号化形であること。

**`normalized_request_match` はこの 2 段の結果を持つ** (§10)。
**「完全 request と `canonical_template` を直接 byte 比較する」ものではない。**

### 3.4 arXiv の完全 query (10 本)

endpoint は `https://export.arxiv.org/api/query`。ブロック文字列を次のとおり定義する。
`<TA>` などは略号であり、送信する `search_query` は略号を展開した文字列である。

```
<TA> = (abs:"program synthesis" OR abs:"code generation" OR abs:"software optimization"
        OR abs:"configuration tuning" OR abs:"design space exploration"
        OR abs:"automated experimentation" OR abs:"autonomous research"
        OR abs:"auto-tuning" OR abs:"algorithm configuration"
        OR abs:"compiler optimization" OR abs:"query optimization" OR abs:"program repair")

<FA> = (abs:"proof chain" OR abs:"evidence binding" OR abs:"provenance"
        OR abs:"data lineage" OR abs:"traceability" OR abs:"audit trail"
        OR abs:"reproducibility" OR abs:"repeatability" OR abs:"replicability"
        OR abs:"experiment tracking" OR abs:"research object" OR abs:"build provenance"
        OR abs:"run manifest" OR abs:"artifact manifest" OR abs:"environment capture"
        OR abs:"checksum validation" OR abs:"software bill of materials"
        OR abs:"reproducible build")

<HA> = (abs:"mechanistic explanation" OR abs:"causal explanation"
        OR abs:"explanation generation" OR abs:"performance explanation"
        OR abs:"root cause analysis" OR abs:"bottleneck diagnosis"
        OR abs:"performance attribution" OR abs:"explainable optimization"
        OR abs:"causal profiling" OR abs:"performance debugging"
        OR abs:"counterfactual explanation" OR abs:"interpretability"
        OR abs:"explainability" OR abs:"sensitivity analysis"
        OR abs:"feature importance" OR abs:"critical path analysis"
        OR abs:"performance model" OR abs:"what-if analysis"
        OR abs:"variance decomposition")

<OA> = (abs:"explanation" OR abs:"rationale" OR abs:"provenance graph"
        OR abs:"execution trace" OR abs:"audit log" OR abs:"evidence bundle"
        OR abs:"proof certificate" OR abs:"diagnostic report")

<VA> = (abs:"bijection" OR abs:"consistency check" OR abs:"integrity check"
        OR abs:"tamper detection" OR abs:"replay verification"
        OR abs:"artifact verification" OR abs:"attestation" OR abs:"mutation testing"
        OR abs:"end-to-end verification")

<WA> = (abs:"performance" OR abs:"latency" OR abs:"throughput" OR abs:"benchmark"
        OR abs:"workload" OR abs:"scalability" OR abs:"many-core"
        OR abs:"transaction processing")

<DA> = submittedDate:[199101010000 TO 202612312359]
```

| query ID | `search_query` |
|---|---|
| `AX3-Q1@arxiv` | `<TA> AND <FA> AND <OA> AND <DA>` |
| `AX3-Q2@arxiv` | `<TA> AND <HA> AND <OA> AND <DA>` |
| `AX3-Q3@arxiv` | `<TA> AND <FA> AND <DA>` |
| `AX3-Q4@arxiv` | `<TA> AND <HA> AND <DA>` |
| `AX3-Q5@arxiv` | `<FA> AND <VA> AND <DA>` |
| `AX3-Q6@arxiv` | `<HA> AND <WA> AND <DA>` |
| `AX3-Q7@arxiv` | `<FA> AND <WA> AND <DA>` |
| `AX3-Q8@arxiv` | `<HA> AND <VA> AND <DA>` |
| `AX3-Q9@arxiv` | `<FA> AND <HA> AND <DA>` |
| `AX3-Q10@arxiv` | `<TA> AND <VA> AND <DA>` |

**期待 echo:** arXiv は `<feed><title>` に
`arXiv Query: search_query=<送信文字列>&id_list=&start=<S>&max_results=<N>` を返す。
**`submittedDate:[A TO B]` は `submittedDate:"A TO B"` へ書き換えられる。**
期待 echo は、送信文字列のこの 1 箇所だけを置換した文字列とする。
**それ以外の差異が出た走行は無効である。**
根拠は測定記録の 6 syntax class (単一ハイフン句・OR ブロック・OR 内ハイフン句・
三分ハイフン・三 block AND・実 query 相当の長さ) の実測である。

ページングは `start` を 0 から `max_results=200` 刻みで進める。

### 3.5 OpenAlex の完全 query (10 本)

endpoint は `https://api.openalex.org/works`。ブロック文字列を次のとおり定義する。
**語は §3.1 と同一である。**

```
<TO> = ("program synthesis" OR "code generation" OR "software optimization"
        OR "configuration tuning" OR "design space exploration"
        OR "automated experimentation" OR "autonomous research" OR "auto-tuning"
        OR "algorithm configuration" OR "compiler optimization"
        OR "query optimization" OR "program repair")

<FO> = ("proof chain" OR "evidence binding" OR "provenance" OR "data lineage"
        OR "traceability" OR "audit trail" OR "reproducibility" OR "repeatability"
        OR "replicability" OR "experiment tracking" OR "research object"
        OR "build provenance" OR "run manifest" OR "artifact manifest"
        OR "environment capture" OR "checksum validation"
        OR "software bill of materials" OR "reproducible build")

<HO> = ("mechanistic explanation" OR "causal explanation" OR "explanation generation"
        OR "performance explanation" OR "root cause analysis" OR "bottleneck diagnosis"
        OR "performance attribution" OR "explainable optimization" OR "causal profiling"
        OR "performance debugging" OR "counterfactual explanation" OR "interpretability"
        OR "explainability" OR "sensitivity analysis" OR "feature importance"
        OR "critical path analysis" OR "performance model" OR "what-if analysis"
        OR "variance decomposition")

<OO> = ("explanation" OR "rationale" OR "provenance graph" OR "execution trace"
        OR "audit log" OR "evidence bundle" OR "proof certificate"
        OR "diagnostic report")

<VO> = ("bijection" OR "consistency check" OR "integrity check" OR "tamper detection"
        OR "replay verification" OR "artifact verification" OR "attestation"
        OR "mutation testing" OR "end-to-end verification")

<WO> = ("performance" OR "latency" OR "throughput" OR "benchmark" OR "workload"
        OR "scalability" OR "many-core" OR "transaction processing")
```

`filter` の値は `title_and_abstract.search:<ブロック式>,to_publication_date:2026-12-31` とし、
**ブロック式は上の括弧つき文字列を `AND` で連ねたものをそのまま置く。**
**複数ブロックのときも各ブロックの外側の括弧を残す。**

| query ID | `filter` の `title_and_abstract.search` 部 |
|---|---|
| `AX3-Q1@openalex` | `<TO> AND <FO> AND <OO>` |
| `AX3-Q2@openalex` | `<TO> AND <HO> AND <OO>` |
| `AX3-Q3@openalex` | `<TO> AND <FO>` |
| `AX3-Q4@openalex` | `<TO> AND <HO>` |
| `AX3-Q5@openalex` | `<FO> AND <VO>` |
| `AX3-Q6@openalex` | `<HO> AND <WO>` |
| `AX3-Q7@openalex` | `<FO> AND <WO>` |
| `AX3-Q8@openalex` | `<HO> AND <VO>` |
| `AX3-Q9@openalex` | `<FO> AND <HO>` |
| `AX3-Q10@openalex` | `<TO> AND <VO>` |

**期待 echo は literal 文字列として登録しない。typed AST として登録する。**

`meta.x_query.oql` を次の部分文法で構文解析する。**未知の token・構文が現れたら
その走行を `未完走` とする (fails closed)。**

```
oql          = "works where" , clause , { "and" , clause } ;
clause       = date_clause | search_clause ;
date_clause  = "date" , comparator , "(" , iso_date , ")" ;
comparator   = "<=" | "<" | ">=" | ">" | "=" ;
search_clause= field , "has" , "(" , expr , ")" ;
field        = "title/abstract" | "title" | "abstract" ;
expr         = or_expr | and_expr | term ;
and_expr     = group , "and" , group , { "and" , group } ;
or_expr      = term , "or" , term , { "or" , term } ;
group        = "(" , expr , ")" | term ;
term         = [ "stemmed" ] , quoted_phrase ;
quoted_phrase= '"' , { any_char_except_quote } , '"' ;
```

照合は次の構造について行う。

| AST が保持するもの | 照合 |
|---|---|
| 検索フィールド名 | 完全一致。`title/abstract` から `title` への drift を不一致とする |
| 引用句の原子性 | 完全一致。`"data lineage"` が `data AND lineage` へ分解されたら不一致 |
| `stemmed` 標識の有無 | 完全一致 |
| AND / OR の grouping 構造 (どの語がどのブロックに属するか) | 完全一致 |
| 日付の comparator と値 | 完全一致。`<=` から `<` への変更を不一致とする |
| 各ブロックの項の**重複度つき多重集合** | 完全一致。集合化して重複項を消さない |
| **可換 sibling の順序** | **無視する** |

**字句規則も固定する。**

- token 区切りは空白 (`SP`、`TAB`、`LF`、`CR`) とし、**連続する空白は 1 個として扱う。**
- `"` で囲まれた範囲は 1 つの `quoted_phrase` token とし、**その内側の空白は区切りにしない。**
- **escape 系列は認めない。** `quoted_phrase` の内側に `"` が現れたらそこで閉じる。
- 記号 `(` `)` `<=` `<` `>=` `>` `=` はそれぞれ 1 token とする。
- **入力を最後まで消費できなければ解析失敗とする** (末尾に余りがある状態を成功にしない)。
- **上の文法・字句規則で解釈できない token または構造が 1 つでも現れたら、
  その走行を `未完走` とする (fails closed)。警告にして先へ進めてはならない。**

**規範 parser は本登録の成果物ではない。実行段が用意する。**
**ただし用意すべきものと、その受入条件は本登録が固定する。**

- 実装 path と内容 SHA-256 を実行記録へ登録する。
- **正例 fixture:** 本登録の測定記録が観測した 7 本の `oql` をそのまま使う
  (単一句・2 語 OR・3 語 OR・2 ブロック AND・日付節が先の形・日付節が後の形を含む)。
  **7 本すべてが上の文法で解析でき、期待 AST と一致すること。**
- **負例 fixture:** 少なくとも次を含める — `title/abstract` を `title` に変えた形、
  `"data lineage"` を `data and lineage` へ分解した形、`<=` を `<` に変えた形、
  `stemmed` を落とした形、閉じ括弧を欠いた形、末尾に余分な token を付けた形。
  **6 本すべてが不一致または解析失敗と判定されること。**
- **本走の開始前にこの 13 本の fixture を通すことを必須とし、
  1 本でも期待どおりでなければ本走を開始しない** (§13.1 の B4)。
- **parser の内容 SHA-256 を本走の開始時に凍結する。**
  **本走の途中で parser を変更した場合、それは §8.5 の意味的 amendment とし、
  変更後の parser で全 OpenAlex query を再走する。**
  **変更前の走行を変更後の parser で判定し直して完走にしてはならない。**

**parser の identity (実装 path と内容 SHA-256) を実行記録へ残す** (§10)。
**raw の `oql` 文字列も全ページ保存する。**

**順序を無視する理由は実測である** — OpenAlex はブロック内の語を辞書順へ並べ替え、
節の順序も query の形によって変わる。literal 比較では正しい走行が無効になる。
**この向きは正しい走行を誤って無効にしない。**
**検出力が落ちる分は、§7.1 の条件 0 (`canonical_template` の一致) が補う。**
**echo の一致だけを修繕の根拠にしてはならない** (D1123)。

ページングは `per-page=200` と `cursor` 連鎖で行う。

### 3.6 DBLP — server 側の連言 (1523 本)

**DBLP は句検索も句の選言も書けず、要旨を索引しない。** 一方、**連言は書ける** —
複数語の `q` は各単語の前方一致の連言として解釈される。

**「各ブロックを全件取得して client 側で交差させる」設計は採らない。**
測定記録によれば `performance` 1 語で 188384 件 = 1884 request を要し、
測った 10 語だけで 2613 request になる。DBLP は 429 と SSL 切断を返す不安定な索引であり、
1 本でも復旧不能なら軸が `未完走` に落ちる設計は、成功確率が低く失敗コストが全損である。

**代わりに、ブロック間の語の組を server 側の連言 query として取得する。**
**母集合の DBLP 側は「これらの連言 query が返した操作集合の和」として定義する。**
**`S(x AND y) = S(x) ∩ S(y)` を設計の前提に置かない** — 前提にすると、
1 対の観測を全対へ一般化することになる。

- request は `q=<語1>%20<語2>&format=json&h=100&f=<0,100,200,...>`。
- query ID は `AX3-<枝>-<語1 の ID>-<語2 の ID>@dblp` (例: `AX3-Q7-F03-W01@dblp`)。
  語 ID は §3.1 の表で一意に定まる。

| 枝 | 積 | 本数 |
|---|---|---|
| `Q3` | T(12) × F(18) | 216 |
| `Q4` | T(12) × H(19) | 228 |
| `Q5` | F(18) × V(9) | 162 |
| `Q6` | H(19) × W(8) | 152 |
| `Q7` | F(18) × W(8) | 144 |
| `Q8` | H(19) × V(9) | 171 |
| `Q9` | F(18) × H(19) | 342 |
| `Q10` | T(12) × V(9) | 108 |
| **合計** | | **1523** |

**`Q1` と `Q2` は DBLP では別途取得しない。**
`Q1 = T ∧ F ∧ O ⊆ Q3 = T ∧ F` および `Q2 = T ∧ H ∧ O ⊆ Q4 = T ∧ H` が集合として成り立つため、
**`Q1` / `Q2` は DBLP 側の母集合の和に record を 1 件も追加しない。**

> **`Q1` / `Q2` の DBLP 側は「論理的に冗長な枝」と定義し、
> 別個の取得も client 側の再構成も digest も要求しない。**
> **枝別の件数は DBLP について報告しない。**
> client 側で `O` 条件を当てる設計は採らない — DBLP は要旨を索引しないため、
> `O` を当てる対象が題名だけになり、**未登録の matcher を実装することになるからである。**
> **枝別の DBLP 件数が将来必要になったら、三項連言 (T×F×O = 1728 本、T×H×O = 1824 本) を
> 新しい query ID として登録する amendment を要する。**

**DBLP の連言は句ではない。** `q=proof chain` は句ではなく `proof*` と `chain*` の連言である。
この索引固有の意味論を登録意味とし、arXiv / OpenAlex と同じ句意味論であるとは書かない。
**過剰包含の方向に働く。**

**期待 echo:** `result.query` が `<語の各単語に * を付けて空白で連ねた文字列>` を返す。
**ただし `V09` (`end-to-end verification`) は例外で、`end* to end* verification*` を返す**
(中央の `to` に `*` が付かない)。**この 1 語の期待 echo は実測値を直接登録する。**
`T08` (`auto-tuning`) と `W07` (`many-core`) は 2 分ハイフンであり `auto* tuning*` /
`many* core*` を期待する。

**宣言的除外は行わない。** D1155 が許したのは索引の構文能力による不可能であって、
予算・実行コストによる断念ではない。**上表 1523 本は有限に列挙できるので、
実行して完走させるか、できなければ `未完走` とする。**

### 3.7 登録した query ID の総数

- arXiv: 10
- OpenAlex: 10
- DBLP: 1523
- **登録 query ID の合計: 1543**

**これは query ID の数であって HTTP request 数ではない。**
request 数は各 query の総件数とページ数に依存し、§8.3 の preflight が確定する。

### 3.8 結果を見てから語を足した場合

**別の query ID (`AX3-Q<n>b@<索引>`) を新規に起こし、追加の理由と時刻を書く。**
既存 ID の定義を書き換えてはならない。扱いは §8.5 の amendment 規則に従う。

## 4. 索引の実測

**実測の正本は `docs/related-work/claim-survey/2026-08-27-axis3-index-measurements.md` である。**
本文書はその結論だけを引く。**値の再掲で食い違いが生じたら測定記録が勝つ。**

| 索引 | 結論 |
|---|---|
| arXiv | echo は送信文字列を保存する (6 syntax class で確認、切り詰めなし)。到達性は間欠的で、`Rate exceeded.` の 429 は時間をおくと回復する |
| OpenAlex | echo は正規化された描画である。ブロック内の語は辞書順、節順は query の形に依存、同一 request には決定的。**AND ブロック自体の順序は未実測** |
| DBLP | 前方一致の連言。要旨を索引しない。2 分ハイフンは両片に `*`、**三分ハイフンは中央の `to` に `*` が付かない**。ページングは高 offset でも連続。単独語は最大 188384 件、連言は測った 16 組すべてが 224 件以下 |

**索引固有の過剰包含。** `V09` (`end-to-end verification`) を DBLP へ送ると、
題名に speaker verification (話者照合) を含む record が返る。
**これは索引の前方一致による語の衝突である。**
**題名の語が衝突しているという事実だけで `除外` を自動付与してはならない** (§1.3)。
判定は §10 の `screened_source_scope` に従って行い、本文が取れなければ `要裁定` とする。

**API の版。** 3 索引とも版番号を返さない。
**endpoint と応答 field 名で代用してよいという裁定は存在しない** (§13.1 の B3)。

## 5. 和集合、主キー、alias、重複除去

**本節は D1121 の軸 3 への具体化であり、一般手続きの新しい正本ではない。**

### 5.1 主キーの正規化 (全 record に適用する total な規則)

1. arXiv ID があれば `arxiv:<id>` (版接尾辞 `vN` は落とす)。
2. 無ければ DOI を正規化して `doi:<値>` — `https://doi.org/` と `http://dx.doi.org/` の
   前置を除去し、**小文字化する。**
   `10.48550/arxiv.<id>` の形の DOI は `arxiv:<id>` へ写像し、1 と同一視する。
3. どちらも無ければ `<索引名>:<索引固有 ID>` を主キーとし、
   **`要裁定` として印を付ける** (他索引の record と統合できないため)。

### 5.2 台帳は 2 段にする

- **record 台帳:** 索引が返したレコードを 1 つも落とさずそのまま持つ。完全性はここで数える。
- **work-family 台帳:** DOI・arXiv の DOI 欄・DBLP の `ee`・著者・版履歴の複数証拠で
  `work-family-id` を付ける。**共有識別子が無ければ自動統合せず `要裁定` とする。**
  **題名一致だけの重複除去を禁じる** (7.7.6)。

### 5.3 件数の単位

取得完全性は record 数、重複除去後は work-family 数、主張表は研究数で数え、
変換の対応表と未解決 family 数を残す。**単位の違う数を足さない。**

### 5.4 alias

旧題・新題・略称・改名前後を 1 つの alias レコードへ束ねる。**名称で引かない。**
主キーは arXiv ID または DOI とする。
**軸 3 固有の既知 alias は本登録時点で確認できていない。**
**alias 統合の判断は work-family 数と研究数を変えるため、実行段で発見したものは
`要裁定` として記録し、統合の可否を判定記録へ明示する** (§13.1 の B1)。

## 6. positive control と補助探索

### 6.1 control

**未知の交点ごとに既知アンカーを要求してはならない。** 交点枝は、そこに該当する研究が
在るかどうかを調べるために引くものである。完全一致アンカーの存在を必須にすると、
調べたい当のものを前提にすることになり、`RW3` が循環的に到達不能になる。

**したがって control を、演算子の集合論的性質に置く。**
**期待は「特定の論文が返ること」ではなく「集合の関係が成り立つこと」で書く。**
これにより、登録時点で完全に一意な実行式と採点規則を持てる。

記号: `n(q)` を query `q` の総件数フィールドの値とする。

| control ID | 索引 | 実行式 (完全な検索値) | 期待 |
|---|---|---|---|
| `C-OR-1@arxiv` | arXiv | `a` = `abs:"provenance" AND <DA>`、`b` = `abs:"data lineage" AND <DA>`、`u` = `(abs:"provenance" OR abs:"data lineage") AND <DA>` | `max(n(a),n(b)) <= n(u) <= n(a)+n(b)` |
| `C-OR-1@openalex` | OpenAlex | 同じ 3 式を `title_and_abstract.search` で | 同上 |
| `C-AND-1@arxiv` | arXiv | `c` = `(abs:"provenance" AND abs:"performance") AND <DA>` | `n(c) <= min(n(a), n(w))`、ただし `w` = `abs:"performance" AND <DA>` |
| `C-AND-1@openalex` | OpenAlex | 同上 | 同上 |
| `C-AND-1@dblp` | DBLP | `q=provenance%20performance` と `q=provenance`、`q=performance` | `n(c) <= min(n(a), n(w))` |
| `C-DATE-1@arxiv` | arXiv | `abs:"provenance" AND submittedDate:[199101010000 TO 202312312359]` と、同式の上限を `202612312359` にしたもの | 前者の件数が後者以下 |
| `C-DATE-1@openalex` | OpenAlex | `to_publication_date` を `2023-12-31` と `2026-12-31` にした 2 式 | 同上 |
| `C-DBLP-CONJ` | DBLP | x = `repeatability` (`F08`)、y = `provenance` (`F03`)。`S(x)` を全ページ取得し、題名に `provenance` の前方一致を持つ部分集合を作る。別に `q=repeatability%20provenance` を全ページ取得する | 両者の正規化主キー集合が**完全一致** |

**演算子 control は 8 本である** (`C-OR-1` 2 本、`C-AND-1` 3 本、`C-DATE-1` 2 本、
`C-DBLP-CONJ` 1 本)。

#### 6.1.1 anchor lookup — control とは別に数える

**次は「索引が anchor を持っているか」を確かめる lookup であって、
検索式の positive control ではない。** 混同しないよう別表にする。

既知アンカー 5 件: `2604.24658` (ARA) / `2507.06999` (D2I) / `2605.22721` (DecentMem) /
`2605.23109` (IDS) / `2605.15221` (Effective Harness Engineering)。

| lookup ID | 索引 | 完全な検索値 | 期待 |
|---|---|---|---|
| `L-ID-<n>@arxiv` | arXiv | `id_list=<arXiv ID>` (5 件それぞれ) | 正規化主キー `arxiv:<ID>` が返る |
| `L-ID-<n>@openalex` | OpenAlex | `filter=doi:10.48550/arxiv.<ID>` (5 件それぞれ) | 正規化主キー `arxiv:<ID>` が返る |
| `L-ID-<n>@dblp` | DBLP | `q=<当該 arXiv ID の文字列>` および `q=<当該論文の題名の語列>` (5 件それぞれ) | 当該 record が返る |

**合計 15 本。**

**OpenAlex と DBLP で 5 件が到達できるかは本登録時点で未実測である** (§13.1 の B2)。
**到達できない索引・anchor があれば、その事実を記録し、母集合から黙って外さない。**
**lookup の失敗は軸を `未完走` にしない** — anchor が索引に収録されていないことは
索引の性質であって、検索式の欠陥ではないからである。
**失敗した lookup の anchor は §6.1.2 の包含 control の検査対象から外れる。**
**ただし、ある索引で 5 件すべてが到達不能なら、その索引は positive control を持たないため
`未完走` とする (§6.1.2)。**

#### 6.1.2 anchor 包含 control — 登録した主 query 自身を通す

**anchor lookup は主検索フィールド (arXiv の `abs`、OpenAlex の `title_and_abstract`、
DBLP の書誌) を通らない。** 通る control を別に置く。

**追加の検索式を作らない。登録済みの主 query の和集合そのものを検査対象にする。**
新しい語を選ぶ設計にすると、その語の選び方で control の成否が変わり、
事後裁量が入るからである。

| control ID | 索引 | 検査対象 | 期待 |
|---|---|---|---|
| `C-ANCHOR@arxiv` | arXiv | `AX3-Q1@arxiv`〜`AX3-Q10@arxiv` の返却集合の和 | `L-ID-*@arxiv` で到達できた anchor の正規化主キーが**すべて**この和に含まれる |
| `C-ANCHOR@openalex` | OpenAlex | `AX3-Q1@openalex`〜`AX3-Q10@openalex` の和 | `L-ID-*@openalex` で到達できた anchor の主キーが**すべて**この和に含まれる |
| `C-ANCHOR@dblp` | DBLP | §3.6 の 1523 本の返却集合の和 | `L-ID-*@dblp` で到達できた anchor の主キーが**すべて**この和に含まれる |

**この control は 7.7.6 の「既知アンカーが検索結果に現れることを確かめる positive control」
そのものである。** 追加 request を要さず、実行段の裁量も無い。

> **失敗したときの意味は明確である。** その索引で到達できる anchor が、
> 登録した 74 語 10 枝のどれにも掛からなかったということであり、
> **語列が軸 3 の既知の接地文献すら拾えていない証拠である。**
> **その索引のその走行を `未完走` とし、§8.5 の意味的 amendment を要する。**
> **control の失敗を「その anchor は要旨に登録語を含まないだけ」と解釈して先へ進んではならない。**

> **空の control 集合を許さない。** ある索引で `L-ID-*` の 5 件すべてが到達不能なら、
> `C-ANCHOR@<索引>` は検査対象を持たない。
> **この場合その索引を `未完走` とする** — positive control を持たないまま
> 完走を名乗れないからである (7.7.6)。

**`C-DBLP-CONJ` の x/y を今固定した理由:** この対は**どの登録枝とも query-equivalent でない**
(登録枝はブロック間の積であり、`F08 × F03` はブロック内の対である)。
**実行段で「別の対」を選ぶ裁量を残さない。**

**control が期待どおりに発火しなかった場合、その索引のその走行は `未完走` とする。**
control の失敗を記録だけして先へ進んではならない。
**これは §6.1 の演算子 control 8 本と §6.1.2 の anchor 包含 control 3 本に適用する。**
**§6.1.1 の anchor lookup の失敗は例外であり、記録するが軸を `未完走` にしない**
(理由は同節)。

### 6.2 control の通過は根拠にならない (D351)

**D351 は「gate の通過を根拠にしてはならない」と裁定している。**
したがって control に加えて次を課す。

> **感度監査:** §6.3 の補助経路で得た候補も全件を台帳へ入れる。
> **包含条件を満たす候補が主 query の和集合に無ければ、その走行を無効とする。**

**感度監査は「通過が完全性を支持する」検査ではなく、「不一致なら無効化する」一方向検査である。**

**通過してしまう反例を 2 つ登録する。**

1. `Q4′ = T ∧ H ∧ O` を、本来の `Q4 = T ∧ H` の代わりに登録したとする。
   演算子 control も個別ブロック control もすべて通る。しかし `configuration tuning` と
   `root cause analysis` を扱い、O ブロックの語を 1 つも使わない正しい hit は落ちる。
   その論文が 5 anchor の 1-hop 引用にも、対象著者にも、登録 venue にも含まれなければ、
   補助監査も通過する。
2. `Q7 = F ∧ W` を `Q7′ = T ∧ F ∧ W` へ狭めたとする。演算子 control と
   T / F / W の個別ブロック control は別 request なのですべて通る。
   しかし `reproducibility` と `benchmark` を扱い T ブロックの語を使わない
   正しい部分接地 hit は落ちる。

**これは構造的証明ではなく、有限の感度監査である。** D384 が言うとおり有限観測は
普遍性を含意しない。文献検索には、コード検索の厳格 parser に相当する
「安価側と高価側が同じ意味論を通る」構造がない。
**この限界を落として `RW3` を語ってはならない。**

### 6.3 補助探索の有限化

補助経路は結果を見る前に有限値で固定する。
**上限を件数で切らない。切ると順序の指定が必要になり、その順序が受理集合を変えるからである。**

| 経路 | 起点 | 索引 | 範囲 |
|---|---|---|---|
| 後方引用 (参考文献) | §6.1 の既知アンカー 5 件 | OpenAlex `referenced_works` | 1 hop、**全件** |
| 前方引用 (被引用) | 同上 | OpenAlex `cites` filter | 1 hop、**全件** (全ページを cursor で辿る) |
| 著者 | 同 5 件の第一著者と最終著者 | OpenAlex `author.id` filter | **全件** (全ページを cursor で辿る) |
| venue 年次一覧 | 下表の 14 venue | DBLP の venue API | 2015〜2026 年、venue×年あたり**全件** |

**件数上限と選択順序を登録しない代わりに、すべて全件取得する。**
**これにより server-side sort の意味論に依存しなくなる** — sort が何であれ、
全ページを取れば集合は同じである。**cursor が尽きるまで辿ることを完走条件とする** (§7.4)。

**venue の community strata:**

| community | venue |
|---|---|
| DB | SIGMOD / PVLDB / PODS |
| workflow・provenance | IPAW / TAPP / WORKS |
| performance | SIGMETRICS / ICPE / SC |
| SE | ICSE / ASE / ISSTA |
| systems | OSDI / SOSP |

**軸 1 の DB 系 4 venue をそのまま使わない理由:** 軸 3 の系譜は
provenance・再現性・説明生成にまたがり、DB 以外の community にありうる。
DB 系だけの補助監査は、その community bias をそのまま再現し、偽陰性を検出しにくい。

**venue 年次一覧は 7.7.6 が要求する補助経路である。** §9 が言う「母集合の外」は
**網羅を保証しない**という意味であって、補助経路として引かない理由にはならない。
venue 由来の候補は主 query 由来と区別して台帳に入れ、§6.2 の感度監査の入力にする。

**途中で hop 数・起点・年範囲・venue を増やしてはならない。** 増やす場合は §8.5 の amendment に従う。

## 7. 完走述語

**本節は D1122 の軸 3 への具体化であり、一般手続きの新しい正本ではない。**

### 7.1 HTTP query (`completion_kind = http`)

各 query ID について、次の全部が成立したときに限り `完走` とする。

0. **request 一致:** **全ページについて**、実際に送った request が §3.3 の登録と一致する。
   - **固定部分**の bytes が登録値と完全一致し、その SHA-256 が登録 digest と一致する。
   - **位置パラメータ**が §3.3 の表の遷移規則に従う
     (arXiv は `start` が 0 起点 200 刻みの等差、DBLP は `f` が 0 起点 100 刻みの等差、
     OpenAlex は初回 `cursor=*`、以降が直前応答の `meta.next_cursor` と byte 一致)。
   - **この条件は echo とは独立であり、echo の一致で代替してはならない** (D1123)。
     **OpenAlex の AST 照合が可換順序を無視する分の検出力は、この条件が補う。**
1. **解釈照合:** 索引が返した解釈後クエリが登録した期待値と一致する。
   arXiv と DBLP は正規化後の文字列一致 (連続空白を 1 個へ、URL エンコードを復号、
   arXiv の `submittedDate` の角括弧と二重引用符の差だけを許容)。
   **OpenAlex は §3.5 の部分文法で構文解析した AST の一致とし、未知構文は `未完走` とする。**
2. **連続性:** arXiv は `startIndex` が 0 から `max_results` 刻みで欠落なく連続し、
   OpenAlex は cursor が前ページの `next_cursor` と一致して連鎖し、
   DBLP は `@first` が 0 から 100 刻みで連続する。**全ページの位置値を保存する。**
3. **件数の一致 (索引ごとに、非最終ページと最終ページで定義が違う):**

   **「最終ページ」とは `位置 + 実要素数 == 総件数` が成立するページを指し、
   それ以外を非最終ページとする。**

   - **arXiv**
     - 非最終ページ: `要求 max_results == opensearch:itemsPerPage == 実要素数`。
     - 最終ページ: `opensearch:itemsPerPage == 実要素数 <= 要求 max_results` かつ
       `startIndex + 実要素数 == totalResults`。
   - **DBLP**
     - 非最終ページ: `要求 h == @sent == 実要素数`。
     - 最終ページ: `@sent == 実要素数 <= 要求 h` かつ `@first + 実要素数 == @total`。
     - **`@sent` と要求 `h` の突き合わせが切り詰めの検出点である。**
   - **OpenAlex**
     - 全ページ: `実要素数 == min(要求 per-page, meta.count - 既取得数)`。
     - **`meta.per_page` を完走の判定に使わない。** 保存はするが gate には入れない
       (§10)。最終ページで `meta.per_page` が要求値を返すのか実返却数を返すのかは
       **未実測**であり、どちらを仮定しても誤りうるためである。
       **実返却数と `meta.count` だけで判定する。**

   **非最終ページで実要素数が要求件数に満たない場合は、その時点で不一致とする**
   (索引側の黙った切り詰めがここに現れる)。
4. **主キー重複なし:** §5.1 の正規化主キーが、ページ内・ページ間で重複しない。
5. **総数一致:** unique record 数が、索引が返した総件数フィールドの値と一致する。
   **総件数がページ間で変わった場合は不一致とし、§8.2 の再走規則に従う。**
6. **正常終端:** **全ページ**について HTTP status が 200 であり、
   content type が索引ごとの期待 MIME と一致し、
   最終 URL の scheme・host・path が要求 URL と完全に一致し (**同一 host だけでは足りない**)、
   必須要素が存在する。
   **期待 MIME:** arXiv は `application/atom+xml`、OpenAlex は `application/json`、
   DBLP は `application/json`。**いずれも charset 引数の有無は許容し、type/subtype で照合する。**
   **HTTP status・content type・最終 URL・応答 byte 数を全ページ分保存する。**

### 7.2 補助探索 (`completion_kind = auxiliary`)

**補助探索の各 request にも query ID を与え、§7.1 の条件 0・2・3・6 を適用する。**
加えて、**cursor またはページ列が尽きるまで辿ったことを条件に含める** (§6.3)。
**補助経路が 1 つでも完走しなければ、感度監査は成立しない。**

### 7.3 軸全体の完走

```
all(arXiv AX3-Q1..Q10)
AND all(OpenAlex AX3-Q1..Q10)
AND all(DBLP 1523 本)
AND all(§6.1 の演算子 control 8 本)
AND all(§6.1.2 の anchor 包含 control 3 本)   # 到達できた anchor が主 query の和に含まれること
AND §6.1.1 の anchor lookup 15 本を実行し結果を記録した   # 失敗は許すが未実行は許さない
AND all(auxiliary)                    # §6.3 の全補助経路
AND 感度監査が無効化しない
AND record-level `未完走` が 0 件
AND 全 record に §1.3 の判定 (`検出` / `近傍` / `除外` / `要裁定`) が付いている
```

**論理積であり、部分積ではない。**

**`未完走` は query と軸の状態であって record の判定ではない** (§1.3)。
**全 record を `未完走` と記録して条件を満たす抜け道を塞ぐため、
軸完走には record-level の `未完走` が 0 件であることを要求する。**

**`要裁定` を不在側へ倒さない。** `要裁定` が残る場合、その record は母集合に残り、
少なくともその候補を含む不在結論は書けない。**`要裁定` の存在は軸完走を妨げないが、
不在主張の範囲を狭める。**

### 7.4 6 条件を全部満たしても全件取得にならない場合がある

**同数の入れ替えは検出できない。** offset 方式で、開始時の集合が `{a,b,c,d}` で
最初のページが `{a,b}` を返し、ページ間に索引側が `{x,b,y,d}` へ同数で置換され、
次の連続 offset が `{y,d}` を返したとする。解釈 echo は同じ、位置は連続、各ページ 2 件、
主キーは重複なし、unique 数と総件数はともに 4、正常終端である。
**しかし取得集合 `{a,b,y,d}` はどちらの snapshot とも一致せず、
開始時の `c` と終了時の `x` を落としている。**

3 索引とも snapshot token を提供しないので、これを構造的に排除することはできない。
**登録する緩和策は次の 2 つで、どちらも有限の監査であって証明ではない。**

- 全ページの応答証拠 (位置値・宣言件数・実要素数・主キー列・HTTP status) を保存する。
- **複数窓にまたがった query は、独立した連続 2 走の主キー集合 digest が一致することを
  要求する。** 一致しなければ `完走` にしない。

**0 件そのものは走行無効の理由にしない。** 正しい query が真に空集合を返すこともある。
誤設定は条件 0・1 と §6 の control で検査する。

## 8. 停止条件と amendment (結果を見る前に固定する)

**本節は D1123 の軸 3 への具体化であり、一般手続きの新しい正本ではない。**

### 8.1 停止条件

**軸全体の停止条件は §7.3 の論理積と同一である。**
1543 本の HTTP query を取り終えただけでは終わりではない — **control、補助探索、
全 record の判定までを含む。** 枝を足さない。
**「新しい候補が出る間だけ続ける」型の停止条件を禁じる。**

### 8.2 再試行と再走の上限

- **1 request あたりの再試行:** 最大 3 回 (バックオフ 3→6→12 秒。DBLP は 15 秒起点)。
  超えたらその query は `未完走`。
- **query 全体の再走:** **最大 1 回。**
  §7.1 の条件 5 で総件数がページ間で変わった場合、その query を page 0 から 1 度だけ
  連続再走する。**2 度目の不一致では追加の再走を行わず `未完走` とする。**
  **「一致する snapshot が出るまで再走する」ことを禁じる。**
- **実行順:** 索引順 (arXiv → OpenAlex → DBLP)、その中は query ID の辞書順とする。
  **順序を固定するのは、途中で止まったときにどこまで進んだかを一意にするためである。**

### 8.3 予算と pacing

**失敗の単位は軸全体ではなく query である。**
失敗した query は page 0 から再走し、**完走済みの別 query の証拠は保持する。**
軸全体の論理積は最後に評価する。
**代償:** query 間で取得時刻が異なり、索引の snapshot は共有されない (§12)。

**本取得の前に preflight を必ず行い、次の表を実行記録へ書く。**

| 列 | 中身 |
|---|---|
| `query_id` | 登録 ID |
| `declared_total` | preflight の初回応答が返した総件数 |
| `pages` | **`max(1, ceil(declared_total / page_size))`** |
| `needs_second_pass` | 複数窓にまたがるか (§7.4) |
| `max_requests` | `1 + pages × (1 + needs_second_pass) × (1 + rerun 上限) × (1 + 再試行上限)` |

**`max_requests` の各項の意味を固定する。**

- 先頭の `1` は **preflight の 1 request** である (本走とは別に数える)。
  **preflight 自身の再試行は §8.2 の 1 request 上限 3 回に従い、
  その分は `max_requests` に含めず、予算表へ別列 `preflight_retries` として持つ。**
- **`pages` は `max(1, ...)` とする** — **0 件の query でも本走の 1 request が要る。**
  preflight の応答を本走へ再利用しないためである。
- `needs_second_pass` = 0 または 1。`1` のとき**全ページを最初から辿り直す**
  (部分的な差分取得ではない)。
- `rerun 上限` = 1 (§8.2 の query 全体再走)。**rerun は 2 走ぶんの traversal を丸ごと反復する**
  (一部を置換するのではない)。したがって係数は 2 である。
- `再試行上限` = 3 (§8.2)。**1 request あたりの上限であり、traversal 全体の反復ではない。**

**したがって 1 query の traversal 回数の上限は `(1 + needs_second_pass) × 2` であり、
その各ページが最大 4 回 (初回 + 再試行 3) 送られる。**

**複合 control / lookup は「1 ID = 1 request」ではない。**
**各 HTTP 検索値に個別の ID と予算行を与える。**

| 群 | 個別 ID の数 | 備考 |
|---|---|---|
| `C-OR-1@arxiv` / `C-OR-1@openalex` | 各 3 (`a` / `b` / `u`) = 6 | 3 つの検索値を別々に送る |
| `C-AND-1@arxiv` / `C-AND-1@openalex` / `C-AND-1@dblp` | 各 3 (`a` / `w` / `c`) = 9 | 同上。`a` は `C-OR-1` と同一の検索値なので**応答を共有してよい。共有した場合は予算行にその旨を書く** |
| `C-DATE-1@arxiv` / `C-DATE-1@openalex` | 各 2 = 4 | 境界違いの 2 式 |
| `C-DBLP-CONJ` | 2 (`S(x)` の全ページ + 連言の全ページ) | `S(x)` は全件取得なので `pages` が要る |
| `L-ID-*@arxiv` / `@openalex` | 各 5 = 10 | 1 anchor 1 request |
| `L-ID-*@dblp` | 10 | **1 anchor につき ID 検索と題名検索の 2 本** |
| `C-ANCHOR@*` | 0 | **追加 request を要さない** (主 query の返却集合を再利用する) |

**合計 41 個の個別 request stream。** それぞれに `declared_total` / `pages` /
`max_requests` の行を持たせる。

**予算表は次の全 request stream を行として持つ。**

| 群 | stream 数 |
|---|---|
| §3.4〜§3.6 の登録 query | 1543 |
| §6.1 / §6.1.1 の control と lookup (上表の内訳) | 41 |
| §6.1.2 の anchor 包含 control | 0 (追加 request なし) |
| §6.3 の補助経路 — 後方引用 | 5 |
| §6.3 — 前方引用 | 5 |
| §6.3 — 著者 (5 件 × 第一著者・最終著者) | 10 |
| §6.3 — venue 年次一覧 (14 venue × 12 年) | 168 |
| **合計** | **1772** |

**補助経路はいずれも全件取得なので `pages` は preflight で確定する。**

**preflight の初回応答を本走の 1 ページ目として再利用しない。**
本走は必ず page 0 から取り直す。**これは snapshot の起点を一意にするためである。**
**この非再利用のぶんが `max_requests` の先頭の `1` である。**

**予算の上限と超過時の扱いを、結果を見る前に固定する。**

> **上限:** 全 query の `max_requests` の総和が **200000 request** を超える場合、
> または本取得の開始から **30 暦日**を超えて完走しない場合、**軸を `未完走` とする。**
> **枝を削って上限に収める操作を禁じる。** 収まらないなら `未完走` であり、
> 設計を変えるなら §8.5 の意味的 amendment を要する。

**OpenAlex の pacing。** 測定記録によれば、本 wave の約 13 request の後に HTTP 429 が返り、
`Retry-After` は 79725 秒 (約 22.1 時間) を示した。軸 1 の凍結記録が示す
「1 窓 100 request」には達していない。

> **「無償枠が IP 単位で複数の実行主体に共有されている」は、この観測と
> 同日に別 wave が同一ノードから OpenAlex を測っていた事実からの推論であって、
> 直接の観測ではない。** 直接観測したのは request 数・status・`Retry-After`・時刻・
> 送信元ノードだけである。**共有の単位は実行段の preflight で観測して確定する。**

- **実行前の availability preflight で `Retry-After` を読み、値が残っている間は本走を開始しない。**
- **最小 request 間隔と cooldown を実行段の preflight で測り、記録する** (§13.2 の N3)。
- API キー、email、前払い残高は加えない。

### 8.4 失敗の扱い

- **429・503・空ボディ・通信失敗・再試行上限到達は、その query を `未完走` にする。**
  完走した query だけを取り出して軸の成熟度を名乗ってはならない (§7.3 の論理積)。
  部分結果から書いてよいのは、**完全に完走した単一 query ID についての内部的な取得報告だけ**で、
  そこに不在の表現を置いてはならない。
- **索引スナップショットの不一致:** §7.4 に従う。補えない範囲は限界として記録する。

### 8.5 死んだ式の扱い (非意味的修繕と意味的 amendment の境界)

- **非意味的修繕:** **`canonical_template_sha256` が同一である**変更だけを指す。
  正規化 request は endpoint・検索フィールド・filter 本体・sort・page size・
  位置パラメータの遷移規則・取得フィールドの射影からなる。
  **解釈後クエリの一致だけを根拠にしてはならない** — DBLP の `result.query` は
  `h` と `f` を含まず、OpenAlex の AST 照合は可換順序を無視するためである。
  ページングの変更は §7.1 の条件 2 が定める遷移規則に従うものだけを許す。
- **意味的 amendment:** それ以外すべて。語・ブロック・枝・cutoff・フィールド・page size・
  位置遷移・control・補助経路の変更を含む。旧走行を `未完走` に固定し、
  **新しい日付の amendment 文書・新しい query ID・全枝の再実行・独立レビュー**を要求する。
  **旧結果を見た後の改訂であることを amendment に明記する。**

## 9. 母集合の外 (網羅を保証しない)

7.7.4 の列挙をそのまま保持する。**この一覧を成果物から落としてはならない。**

> SIGMOD / PVLDB / OSDI / SOSP などの venue 本体の年次一覧、ACM Digital Library、書籍、
> 技術報告、学位論文、非英語文献、索引化されていない実装・アーティファクト。

**venue 年次一覧は §6.3 で補助経路として引くが、それは網羅の保証にならない** — 対象 venue と
年範囲を有限に固定しているためである。母集合の外であることは変わらない。

本文書はこれに次を足す。

- **2026-12-31 より後の日付を持つレコード** (§2 の上限境界で 3 索引から落ちる)。
- **DBLP の要旨** — DBLP は要旨を索引しないので、DBLP の枝は書誌・題名にしか当たらない。
  **関連語が要旨だけにあり DBLP にしか収録されない work は母集合から落ちる。**
  DBLP 側の未検出は「DBLP の文献」ではなく
  「**DBLP の書誌・題名に登録語の前方一致が現れた文献**」にしか及ばない。
- **DBLP の `Q1` / `Q2` の枝別件数** (§3.6 で冗長枝としたため報告しない)。
- **§6.3 の venue strata と anchor の外にある引用・著者・venue。**
- **本文書が登録しなかった概念語。** §3.1 の 74 語は有限であり、語を変えれば結果は変わりうる。
  **`transparency` / `explainable AI` / `replication` / `reproduction` は意図して採らなかった。**
- **登録した検索フィールド以外の本文。** 3 索引とも全文検索ではない。

## 10. 実行の記録 (別の凍結物が持つ)

**本文書に実行値を書き戻してはならない。** 実行は新しい日付の凍結物
(`claim-survey/<日付>-axis3-search-execution.md` を想定) が持ち、次を保存する。

**query ID ごと:**

| field | 中身 |
|---|---|
| `query_id` | 登録 ID |
| `completion_kind` | `http` / `auxiliary` |
| `request` | 送信した完全な request (**全ページ分**) |
| `canonical_template` | §3.3 の placeholder 付き完全 URL (登録値) |
| `canonical_template_sha256` | 上の UTF-8 bytes の SHA-256 (登録値) |
| `normalized_request_match` | §3.3 の 2 段照合の結果 (placeholder 復元後の byte 一致 / 位置パラメータの遷移規則。**ページごとに記録する**) |
| `interpreted_query_raw` | 索引が返した解釈後クエリの生文字列 (全ページ) |
| `interpreted_query_ast` | OpenAlex のみ。§3.5 の文法で解析した AST |
| `parser_identity` | OpenAlex のみ。AST parser の**実装 path と内容 SHA-256** (§3.5 の受入条件と同じ束縛) |
| `parser_fixture_result` | OpenAlex のみ。§3.5 の正例 7 本・負例 6 本の結果 |
| `expected_interpreted_query` | §3.4〜3.6 が登録した期待値 |
| `retrieved_at` | 取得の開始日時と終了日時 (UTC と JST) |
| `api_identification` | endpoint と、応答に実在した必須 field 名の一覧 |
| `declared_total` | 索引が返した総件数。ページごとに再取得して変化の有無も残す |
| `pages` | ページごとに 位置値 / 要求件数 / 宣言件数 / 実要素数 / HTTP status / content type / 最終 URL / 応答 byte 数 / 主キー列 |
| `retrieved_unique` | 重複除去前の unique record 数 |
| `primary_key_digest` | unique 主キー集合の digest |
| `second_pass_digest` | §7.4 の 2 走目の digest |
| `rerun_count` | §8.2 の query 全体再走の回数 (上限 1) |
| `completion` | §7.1 の各条件の成否 |
| `failure` | 429 / 503 / 空ボディ / 予算切れ / 再試行上限 の別 |

**control ごと:** `control_id` / 完全 request / 期待 (集合関係の式) / 実際の値 / 発火の成否。

**record ごと:**

| field | 中身 |
|---|---|
| `primary_key` | §5.1 の正規化主キー |
| `source` | 索引名 / query ID / ページ番号 / 主 query か補助経路か |
| `index_date_value` | 索引固有の日付欄の値 |
| `judgement` | `検出` / `近傍` / `除外` / `要裁定` (**`未完走` は入らない**) |
| `matched_conditions` | B / C / D のうち満たしたものの集合 |
| `grounding_strength` | `直接接地` / `部分接地` / `非接地` |
| `X_axis_primary` | 真偽 |
| `scope_match` | `A_scope` の真偽 |
| `layer` | `fact` / `hypothesis` / `both` |
| `polarity` | 7.7.5 の 5 語 |
| `exclusion_reason` | `除外` のときのみ。理由コード |
| `screened_source_scope` | `title` / `abstract` / `fulltext` のどこまで見たか |
| `screened_inputs` | 全文確認した入力の path と digest |
| `screening_terms` | 走査に使った語 |

**`screened_source_scope` を必須にする理由:** 7.7.5 は「走査は本文全体に対して行う。
索引の列も各エントリ冒頭の `接地:` 行も本文の部分集合でしかない」と定める。
**部分フィールドの走査を全件走査と記録できないようにする。**
本文が取れず判定できないものは `要裁定` とする。**題名だけで除外しない。**

**work-family ごと:** `work-family-id` / 構成 record の主キー列 / 統合に使った証拠 /
未解決なら `要裁定`。**alias 統合の判断とその根拠を明示する。**

## 11. 登録前に親が目にしたもの (事前知識の開示)

**本文書を凍結する前に、親は次を目にした。**

### 11.1 索引の構文と取得量

測定記録 (`2026-08-27-axis3-index-measurements.md`) の全観測を目にしている。
arXiv・OpenAlex・DBLP の echo の形、ハイフンの扱い、ページングの挙動、
レート制限、および多数の総件数である。

**probe の projection:** arXiv と OpenAlex の probe は `max_results=1` / `per-page=1` で
実行しており、応答 body には record が最大 1 件含まれる。
**親が明示的に読み出したのは echo と総件数と rate-limit header だけだが、
題名・ID が親へ露出した可能性を否定できない。**
DBLP の集合等価性検査では、`repeatability` の **381 件の題名を機械的に走査した。**
`end-to-end verification` では **上位 3 件の題名を目にした。**

### 11.2 登録枝と query-equivalent な pilot の cardinality 露出

**次の 8 本は、本文書が §3.6 で登録する DBLP の枝 query と query-equivalent である。**
**pilot として実行し、返却件数が親へ露出した。**

| pilot として送った `q` | 対応する登録 query ID | 露出した `@total` |
|---|---|---|
| `provenance performance` | `AX3-Q7-F03-W01@dblp` | 26 |
| `provenance benchmark` | `AX3-Q7-F03-W04@dblp` | 18 |
| `reproducibility benchmark` | `AX3-Q7-F07-W04@dblp` | 46 |
| `traceability performance` | `AX3-Q7-F05-W01@dblp` | 19 |
| `causal explanation performance` | `AX3-Q6-H02-W01@dblp` | 2 |
| `many-core provenance` | `AX3-Q7-F03-W07@dblp` | 0 |
| `program synthesis provenance explanation` | `Q1` の三項組 (登録は冗長枝) | 0 |
| `code generation provenance rationale` | `Q1` の三項組 (登録は冗長枝) | 0 |

> **これらの `@total` を、対応する枝の未検出の証拠として使ってはならない。**
> **とくに 0 を「そのような文献は無い」と読んではならない。**
> `RW0` の軸は世界の不在を書けない。これらは pilot の副産物であって完走記録ではなく、
> §7 の完走述語を 1 つも満たしていない。

### 11.3 露出が設計へ与えた影響

**次の設計選択は、上記の観測を見た後に決めた。**

1. **DBLP の取得方式** — 単独語の総件数 (`performance` 188384 等) を見て、
   atomic 全件取得を捨て、server 側の連言へ変えた。
   **連言 16 組の総件数がすべて 224 以下であったことが、この選択の直接の根拠である。**
2. **`V09` の期待 echo の例外** — 三分ハイフンの echo を測って登録した。
3. **OpenAlex の期待 echo を AST にしたこと** — 語順の正規化を測って決めた。
4. **`C-DBLP-CONJ` の x/y** — 実測した対をそのまま control にした。
5. **予算と pacing の書き方** — `Retry-After` の値を見て決めた。

**語列 (§3.1) と枝 (§3.2) は上記の観測を根拠に変えていない。**
語列は 2 度広げており、いずれも**レビューの語彙指摘によるもので、索引の cardinality を
理由に選んだ語ではない。**

| 版 | 語数 | 変更 | 理由 |
|---|---|---|---|
| 起草 (段 2) | 48 | — | 6 ブロック × 8 語 |
| 初版 (段 3 反映後) | 62 | T を 4、F を 4、H を 5、V を 1 追加 | 段 3 の「community 固有語の欠落」指摘 |
| v2 (段 6 反映後) | 74 | F を 6 (`F13`〜`F18`)、H を 6 (`H14`〜`H19`) 追加 | 段 6 の「scientific-workflow / SE supply-chain / XAI / performance 系の標準語で落ちる研究型がある」指摘 |

**枝 (§3.2) は段 3 で `Q10` を足して以降変えていない。**
**ただし影響経路が無かったと断定はしない。**

### 11.4 文書と裁定

登録前に、`2026-08-26-inventory.md` の軸 3 節、`docs/paper-story/2026-08-26.md` の §3、
軸 1 の事前登録全文、および §入力 path の各決定を読んでいる。
既知アンカー 5 件は `docs/related-work/README.md` の該当エントリから採った。
段 2 の起草子と段 3・段 6 の各レビュー子の出力を読んでいる。

## 12. この登録自身の限界

- **正式な完走記録を 1 件も作っていない。** 網羅率についても不在についても何も言わない。
- **純粋な pre-result preregistration ではない** (§0、§11.2)。
  登録枝と query-equivalent な 8 本の cardinality が親へ露出している。
- **軸 3 は `RW0` のままである** (§1.4)。世界の不在を書く資格は無い。
- **§13.1 の blocking 項目が閉じるまで `RW3` に到達できない。**
- **OpenAlex の AND ブロックの順序が並べ替えられるか送信順が保たれるかは未実測である。**
  契約は可換 sibling の順序を無視する側に倒しており、**順序に意味がある drift を見逃す。**
  §7.1 の条件 0 で補うが、完全ではない。
- **OpenAlex の `meta.per_page` が最終ページで何を返すかは未実測である。**
  そのため完走の判定には使わず、保存項目に留めた (§7.1 の条件 3)。
- **DBLP の集合等価性は 1 対でしか確かめていない。** §3.6 はこれを設計の前提から外したが、
  `C-DBLP-CONJ` は依然 1 対の検査である。
- **DBLP の単独語の総件数を測ったのは 10 語だけである。** 内訳は次のとおり。
  - **測った 10 語の合計: 2613 request** (`evidence-bound` を含む。これは probe 語であり
    §3.1 の登録語ではない)。
  - **そのうち §3.1 の登録語である 9 語: 2612 request。**
  - **そのうち DBLP の取得に使うブロック (T / F / H / V / W) に属する 8 語: 2493 request。**
    `explanation` は登録語 `O01` だが、**`Q1` / `Q2` を冗長枝とした結果 O ブロックは
    DBLP の取得に使わない**ため、この 8 語には入らない。
  - **残り 66 語の総件数は測っていない。**

  atomic 全件取得を採らない判断は、**取得に使う 8 語だけで 2493 request、
  うち `performance` 1 語で 1884 request** という下限が支える。
  **これは全体量の見積もりではない。**
- **`replication` / `reproduction` を登録しなかったことによる取りこぼしは残る。**
  多義性を理由に外したが、3 索引の語幹処理は互いに異なるため、
  登録した `F07`〜`F09` / `F18` がこれらを覆うとは言えない (§3.1)。
- **3 索引とも API の版番号を返さない。** endpoint と field 名での代用を許す裁定は無い
  (§13.1 の B3)。索引の内容は本文書の凍結後に変わりうる。
- **arXiv の 301 の挙動は軸 1 が引く 2026-07-10 の記録によるもので、本 wave では再測していない。**
- **§6.2 の感度監査は有限の監査であって構造的証明ではない** (D384)。
  登録した 2 つの反例は、control も補助監査も通過しつつ正しい hit を落とす。
- **§7.4 の同数入れ替えは構造的に排除できない。**
- **§8.3 により query ごとに取得時刻が異なる。** 索引の snapshot は共有されない。
- **外部 raw 応答を保存していない** (測定記録の限界節)。実行段では §10 のとおり
  全ページの応答証拠を保存する。
- **本文書は軸 3 だけを登録している。** 軸 1 は別の凍結物が持ち、軸 2・4・5 は登録していない。

## 13. 未決項目 — blocking と non-blocking

**未決を 2 種類に分ける。混ぜてはならない。**

**いずれも「実行段の裁量」ではない。閉じ方は下表で固定してあり、
測った結果が期待と違えば同一 query ID での修繕ではなく §8.5 の意味的 amendment に倒す。**

### 13.1 blocking — 未了なら `RW3` に到達しない

| # | 未決項目 | 閉じ方 | 受理集合を変えうるか |
|---|---|---|---|
| B1 | alias 統合の判断 | 実行段で発見した alias を `要裁定` として記録し、統合の可否と根拠を判定記録へ明示する | **変えうる** (work-family 数・研究数) |
| B2 | OpenAlex / DBLP での anchor 5 件の到達性 | preflight で §6.1.1 の `L-ID-*` 15 本を実行し、到達不能な索引と anchor を記録する。**黙って母集合から外さない。** 到達できた anchor が §6.1.2 の包含 control の検査対象になる | **変えうる** (ある索引で 5 件すべてが到達不能なら、その索引は positive control を持たず `未完走` になる) |
| B3 | API 版番号の代用 | 「endpoint + 応答 field 名 + response header + raw digest を effective version とする」ことの可否を人間裁定へ出す。**裁定が無い間は `RW3` 不可と明記する** | **変えうる** (`RW3` の可否そのもの) |
| B4 | 規範 parser の受入 | §3.5 の正例 7 本・負例 6 本の fixture を本走前に通す。**1 本でも期待どおりでなければ本走を開始しない** | **変えうる** (OpenAlex の完走判定) |
| B5 | 予算表の作成 | §8.3 の preflight を全 1772 stream について行い、`max_requests` の総和が上限内かを判定する。**超過なら `未完走`** | **変えうる** (超過時は軸が `未完走`) |

### 13.2 non-blocking — 記録するが `RW3` の前提ではない

| # | 観測項目 | 記録の仕方 |
|---|---|---|
| N1 | OpenAlex の AND ブロック順序 | preflight で送信順を反転した 2 request を実行し、echo を比較して記録する。**契約は順序を無視する側で固定済みなので判定は変わらない** |
| N2 | OpenAlex の `meta.per_page` の最終ページ意味論 | 総件数が page size の倍数でない query を 1 本最後まで辿り、最終ページの `meta.per_page` と実要素数を記録する。**完走判定には使わない** (§7.1 の条件 3) |
| N3 | OpenAlex の最小 request 間隔と cooldown | `Retry-After` と rate-limit header を記録し、pacing を確定して実行記録へ書く (scheduling のみ) |
| N4 | 無償枠の共有単位 | preflight の観測で確定する。**推論のまま予算モデルに使わない** (scheduling のみ) |

**B3 は人間裁定を要する。** 7.7.4 は索引の「API または export の版」を固定するよう求めるが、
3 索引とも版番号を返さない。**代用を許す裁定が存在しないため、本文書は代用を既成事実にしない。**

## 14. 段 3・段 6 レビューの反映

本文書は起草 (段 2) の後、段 3 の 2 本と段 6 の 2 本、計 4 本の独立レビューを受けて
親が裁定した内容で書かれている。
**land 前の反映であり、実行記録との食い違いは生じない (正式な完走記録は 1 件も無い)。**

**段 3 の反映 (22 件)** は初版で行い、**段 6 が 23 件の must-fix を返した。**
段 6 の反映は次のとおり。

| # | 指摘 | 反映 |
|---|---|---|
| 1 | `直接接地` の定義が 7.7.5 より広い | §1.3 で `X_axis_primary` を分離し `scope_match` を別属性にした (段 3 で反映済み) |
| 2 | `検出` と `近傍` の真理条件が無い | §1.3 に真理条件の表を置いた |
| 3 | record schema に `matched_conditions` と `grounding_strength` が無い | §10 に追加した |
| 4 | 語列に ID が無く query ID から語を復元できない | §3.1 に 74 語すべての固定 ID を振った |
| 5 | 「48 語」が実際の語数と食い違う | 語数を 74 と明記し、DBLP の積を再計算した (1523) |
| 6 | OpenAlex のブロック文字列が展開されていない | §3.5 に 6 ブロックすべてを展開した |
| 7 | OpenAlex / DBLP の canonical encoding が無い | §3.3 に 3 索引共通の規約を置いた |
| 8 | OQL の文法・parser が登録されていない | §3.5 に部分文法を EBNF で登録し、未知構文を `未完走` とした。parser identity を §10 へ加えた |
| 9 | derived `Q1`/`Q2` の client predicate が未定義 | §3.6 で**冗長枝**と再定義し、再構成も digest も要求しないことにした。枝別件数は報告しない |
| 10 | control の実式・anchor が未固定 | §6.1 を集合関係 control に書き直し、13 control すべての完全な実行式と期待を固定した |
| 11 | `C-DBLP-CONJ` の対が「実行段で別の対」だった | x=`F08`、y=`F03` を今固定した。**どの登録枝とも query-equivalent でない** |
| 12 | 補助探索の cap が sort 意味論に依存する | §6.3 で cap を撤廃し全件取得にした。sort 依存が消えた |
| 13 | 補助探索に完走述語が無い | §7.2 を新設し、§7.3 の論理積へ加えた |
| 14 | 停止条件が取得だけで終わっている | §8.1 を §7.3 の論理積と同一にした |
| 15 | query 全体の再走上限が無い | §8.2 で最大 1 回に固定し、実行順も固定した |
| 16 | 全 record を `未完走` にすると論理積が真になる | §7.3 に record-level `未完走` = 0 件を加え、§1.3 で `未完走` を record 判定から外した |
| 17 | `expected_normalized_request` が gate に入っていない | §7.1 に条件 0 を新設し、§10 へ field を加えた |
| 18 | 条件 6 の MIME・path が未固定 | §7.1 の条件 6 に索引別 exact MIME と scheme/host/path 完全一致、全ページ status 200 を書いた |
| 19 | OpenAlex 最終ページの `meta.per_page` 前提が未実測 | §7.1 の条件 3 を索引別に分け、OpenAlex は実要素数を本体にした。未実測を §13.2 の N2 に登録した |
| 20 | 予算式に未確定項が残り、`1009` は request 数ではない | §3.7 で query ID 数と明記し、§8.3 に preflight 予算表・上限 200000 request・30 暦日・超過時 `未完走` を固定した |
| 21 | 語彙 strata の不足で落ちる研究型がある | §3.1 に F を 6 語、H を 6 語追加した (計 74 語) |
| 22 | 集合等価性を設計根拠に使いすぎ | §3.6 を「server が返した操作集合の和」に書き直し、等価性を前提から外した |
| 23 | IP 共有が §4 では推論、§8.3 では事実 | §8.3 を推論として書き直した |
| 24 | §4 の実測が凍結物として残っていない | `2026-08-27-axis3-index-measurements.md` を新設し、§4 はその結論だけを引くようにした |
| 25 | 登録枝と query-equivalent な pilot の露出が未開示 | §0 と §11.2 で 8 本すべてを開示し、不在の証拠に使うことを禁じた |
| 26 | 外部索引に対する 0 件を本文に書いていた | §4 と §7.4 から除き、§11.2 の露出記録へ移した |
| 27 | 題名だけで `軸 3 とは無関係` と判定していた | §4 を「索引の前方一致による語の衝突」に書き直し、自動的な `除外` 付与を禁じた |
| 28 | D1015 への適合が宣言だけ | §0 で本文書を D1121/D1122/D1123 の具体化と位置づけ、決定が勝つと明記した。7.7 本体への集約可否は worklog へ送った |
| 29 | API 版の代用を許す裁定が無い | §13.1 の B3 として人間裁定へ出し、裁定が無い間は `RW3` 不可と明記した |
| 30 | probe の projection と露出範囲が未開示 | §11.1 に記録した |

**焦点再レビューの反映 (段 6 第 2 巡)。** 上記 v2 に対して焦点再レビューが
29 件中 16 件を `closed`、12 件を `partial`、1 件を `regressed` と判定した。
第 2 巡で次を直した。

| # | 指摘 | 反映 |
|---|---|---|
| 31 | **regression:** §7.1 の条件 3 が「各ページで要求件数＝実要素数」と「最終ページは残件数でよい」を同時に要求し、総件数が page size の倍数でない正常走行が永久に未完走になっていた | 条件 3 を**非最終ページと最終ページに分割**し、最終ページの定義 (`位置 + 実要素数 == 総件数`) を明示した |
| 32 | `meta.per_page` の意味論が未実測なのに gate に入っていた | **完走判定から外し保存項目に降格した。** §13.2 の N2 へ移し「`RW3` の前提ではない」と明記した |
| 33 | §12 の「10 語中 8 語が登録語」が測定記録の算術と食い違う | 3 通りの母集合 (測った 10 語 = 2613 / 登録語 9 語 = 2612 / DBLP 取得ブロックの 8 語 = 2493) に分け、差の理由を明記した。測定記録側も同じ表に直した |
| 34 | §11.3 が語彙拡張を「段 3 の指摘」とし §14 #21 と矛盾する | 48 → 62 → 74 の 3 版の表を置き、どちらの拡張がどの段の指摘によるかを明記した |
| 35 | 表示上の改行・インデントが送信 bytes として未定義 | §3.3 に**復号形の正規形**を定める 4 段の正規化規則を置いた |
| 36 | `expected_normalized_request` が query 単位の単数 URL で、ページごとに変わる位置と OpenAlex の `cursor` を byte 一致できない | §3.3 を**固定部分 + ページ遷移規則**に分け、§7.1 の条件 0 を両方の照合に書き直した。固定部分の SHA-256 を登録項目にした |
| 37 | OQL の lexer・完全消費・parser 版・fixture が未登録 | §3.5 に字句規則と完全消費条件を足し、規範 parser の受入条件 (正例 7 本・負例 6 本の fixture を本走前に通す) を登録した。**parser 実装は実行段の成果物であり本登録の成果物ではない**と明記した |
| 38 | control 表が「13 本」と称して 14 行あり、OpenAlex/DBLP の anchor control が未定義 | control を 3 層に分けた — §6.1 の**演算子 control 8 本**、§6.1.1 の**anchor lookup 15 本**(失敗は軸を止めない)、§6.1.2 の**main-field control**。§7.3 の論理積も 3 層に分けた |
| 39 | 予算式が query 全体再走と preflight を積算せず、対象 ID の範囲も不明 | `max_requests` を `1 + pages × (1 + 2走) × (1 + 再試行3) × (1 + rerun1)` へ改め、予算表が持つ全 ID (登録 1543 + control + lookup + 補助経路) を列挙した |
| 40 | `replication` / `reproduction` の除外理由が「既存語で覆われる」という未実証の主張だった | **多義性 (データ複製との衝突) を理由とする設計上の選択**へ書き直し、「覆われる」という主張を撤回した。取りこぼしを §12 の限界へ足した |

**`partial` のまま残し、本 wave では閉じない項目。**

| 所見 | 扱い |
|---|---|
| RA-13 (D1015 — 一般手続きを 7.7 本体へ集約すべき) | **本 wave の scope 外。裁定パッケージとしてユーザーへ返す。** 集約は規則の正本 (`docs/related-work/README.md` 7.7) の改訂であり、かつ軸 1 の凍結物が同じ一般節を持つため、軸 3 だけを動かすと 2 つの凍結物が非対称になる。**単独の wave で既成事実にしない。** |
| RB-08 の「予算内に収まる事前根拠」 | **preflight を実行するまで原理的に書けない。** 上限 (200000 request / 30 暦日) と超過時に `未完走` とする規則は固定済みであり、収まるかどうかの判定は preflight の役割である。 |
| RB-09 / RA-05 / RB-05 の OpenAlex 側実測 | **OpenAlex が約 22 時間の `Retry-After` を返しており本 wave では測れない。** §13 へ登録した (B2 は blocking、N1〜N4 は non-blocking)。 |

**焦点再レビュー第 2 巡の反映 (段 6 第 3 巡)。** v3 に対する第 2 巡の焦点検証が
#31〜#40 の大半を `closed` としたうえで、新たに must-fix 4 件と should-fix 2 件を挙げた。
**算術と語彙の照合 (74 語、積 8 種、DBLP 1523、登録 ID 1543、
§3.4/§3.5 のブロック展開の 1 語ずつの照合、測定記録の 2613/2612/2493) は
第 2 巡で 0 件の不一致だった。**

| # | 指摘 | 反映 |
|---|---|---|
| 41 | **regression:** main-field control の語を実行段で選ぶ設計は事後裁量であり、全 lookup が失敗すると control 0 本でも論理積を通り、7.7.6 の positive control 要求を弱める | §6.1.2 を**anchor 包含 control** へ作り直した。**追加の検索式を作らず、登録済み主 query の和集合に anchor が含まれることを検査する。** 語の選択が消え、**ある索引で anchor が 1 件も到達できなければその索引を `未完走`** とした |
| 42 | `pages` が 0 件で 0 になり、複合 control / lookup が単数行で表現できず、二走と再走の乗算も未定義 | `pages` を `max(1, ...)` にし、二走・再走・再試行の各係数の意味を定義した。**control / lookup を 41 個の個別 request stream へ分解**し、予算表の総 stream 数を 1772 と明記した |
| 43 | `canonical_template` の hash 対象 bytes が一意でなく、cursor の比較方向も未定義 | §3.3 に **placeholder 付き `canonical_template`** を定義し、SHA-256 の入力を固定した。**cursor は「応答値を規約どおり符号化して送信 bytes と比較する」向きに固定した。** §10 の schema も置き換えた |
| 44 | §13 冒頭が全 7 項目を `RW3` の前提とする一方、#4 は前提でないとしていた | §13 を **§13.1 blocking (B1〜B5)** と **§13.2 non-blocking (N1〜N4)** に分割した |
| 45 | `parser_identity` が「path と版」で §3.5 の内容 SHA-256 と食い違う | §10 を内容 SHA-256 へ統一し、**本走中の parser 変更を意味的 amendment とする規則**を §3.5 へ足した |
| 46 | 測定記録 §3.5 の見出しが「15 組」で表は 16 行 | 見出しを 16 組へ直した |

**第 3 巡をもって段 6 の fix を終える** (`DW-O16` の 3 巡上限)。
**残る `partial` は下表のとおり親が裁定して閉じた。**

| 残件 | 裁定 |
|---|---|
| D1015 の一般手続き集約 (RA-13) | **scope 外。裁定パッケージとしてユーザーへ返す。** 規則の正本の改訂であり、軸 1 の凍結物との非対称を生むため単独 wave で既成事実にしない |
| 予算が上限内に収まる事前根拠 (RB-08) | **原理的に preflight 前には書けない。** 上限と超過時 `未完走` は固定済みで、判定は §13.1 の B5 が担う |
| OpenAlex 側の未実測 (RB-09 ほか) | **索引が約 22 時間の `Retry-After` を返しており本 wave では測れない。** §13.1 の B2 / §13.2 の N1〜N4 へ登録した |

**最終検証の反映 (段 6 第 4 巡)。** v4 に対する最終検証は #41〜#46 のうち 5 件を `closed`、
1 件 (#44) を `partial` とし、**land を止める理由を 1 件だけ挙げた。**

| # | 指摘 | 反映 |
|---|---|---|
| 47 | §0 と §13 の見出しが「§13 全体が `RW3` 前に閉じる項目」と読め、§13.2 の non-blocking と真逆になっていた | §0 の参照を §13.1 に限定し、§13 の見出しを「未決項目 — blocking と non-blocking」へ改めた |

**最終検証の算術照合はすべて一致した** — 74 語、積 8 種、DBLP 1523、登録 ID 1543、
予算 stream 1772、測定記録の 2613 / 2612 / 2493、連言 16 組、内部 `§N` 参照。
**旧未決番号の残存も無い。**
