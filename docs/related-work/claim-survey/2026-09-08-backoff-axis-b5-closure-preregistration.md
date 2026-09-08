# 2026-09-08 — 軸 B5 の後継凍結物 (1/2): 部分登録が閉じられなかった 3 点を閉じる手順の事前登録 (凍結)

- **作成日:** 2026-09-08
- **入力 commit:** `34af5a571def179d1c841ce6e8a1cbcaeb9e9771` (local main、本 wave の base)
- **入力 digest:** 下記 input path の内容は入力 commit の blob そのものである。
  - `docs/related-work/claim-survey/2026-09-07-backoff-axis-b5-search-preregistration.md` = `f7e3190f9ce92345fd4a91caecae8cd6bf7a5666` (以下「部分登録」)
  - `docs/related-work/claim-survey/2026-09-05-backoff-axis-registration.md` = `901ba833306e5e20ce902995b0c20b046089eb09` (以下「軸登録」)
  - `docs/related-work/README.md` = `b5153305186918436bd9b53c9516f8658968b211`
  - `docs/related-work/claim-survey/2026-09-01-axis3-registration-preflight.md` = `cfc6157520335c6f82332c54145c5f75f1c21326` (seal の先例)
  - `docs/related-work/claim-survey/2026-09-02-axis1-search-amendment.md` = `6eb3150406fa99720d6690f710ea6da0f5de8089` (期待 AST 規則の正本)
  - `docs/related-work/claim-survey/2026-08-27-axis3-index-measurements.md` = `c490613dab0e3734df7482e8a2a0cf500746637a`
  - `orchestrator/axis1_search/catalog.py` = `dfae508f11570e0dfd5fc52c6db18faf256a344c` (生成器の先例。本 wave の生成器はこれを import しない)
- **入力 path:** 上記 7 file、および `docs/related-work/claim-survey/README.md` / `docs/paper-story-backoff/2026-09-05.md`
- **文献 cutoff:** 部分登録 §2.2 を継承する (上限 `2026-12-31`、下限なし)
- **規則の正本:** `docs/related-work/README.md` の「7.7 主張軸別の調査状態と、不在主張の成立条件」
- **軸の定義元:** 軸登録 §1、部分登録 §1

> **凍結物である。** 書いた後は上書きしない。更新は新しい日付のファイルで行う。
> 進行中の可変状態の正本は `docs/worklog.md` の末尾エントリであり、ここではない。

---

## 0. この文書は何であって、何でないか

**これは「閉じ方」の登録である。値の確定ではない。**

部分登録 §0 は、検索の実行を認可しない理由を 3 つ挙げた。

1. 候補 3 群の主キー (DOI または arXiv ID) が 1 つも確定していない (部分登録 §4.2)
2. query catalog の bytes と SHA-256 が seal されていない (同 §3.3、§5.3)
3. 補助探索のうち引用・著者経路の起点が確定していない (同 §4.5)

本文書は、この 3 点を**どの順で・何を根拠に・どの成果物で**閉じるかを、**値を確定する前に**固定する。
値そのもの (確定した主キー、catalog の SHA-256、起点の具体値) は本文書には無く、
後継凍結物 (2/2) `2026-09-08-backoff-axis-b5-closure-record.md` が持つ。

**本文書を書いた時点で、候補 3 群の anchor の識別子を索引・書誌 API へ 1 本も照会していない。**
外部 request を出したのは §6 の「非 anchor の ID による応答形の観測」だけである。
**軸 B5 の主 query・control・補助探索の結果は 1 件も見ていない。**

**本文書は部分登録の bytes を 1 byte も変えない** (D1208)。部分登録の文面に対する訂正は
§2.5 の erratum / 意味的 amendment として本文書が持ち、部分登録側へは書かない。

**軸 B5 の成熟度は本文書の後も `RW0` のままである。** 本文書は世界の不在を支持せず、
検索の実行も認可しない。3 点が閉じた後も、部分登録 §5.3 の registration preflight
(parser・fixture・schema・実行器の bytes の束縛) と live preflight、および人間の実行認可が残る。
本体論文の軸 1〜5 の状態は動かさない。

## 1. 3 点を閉じる分担と、成果物の凍結順

| 順 | 成果物 | 何を閉じるか | 誰が書くか |
|---|---|---|---|
| 1 | 本文書 (後継凍結物 1/2) | anchor 集合の凍結 (§2.2)、主キー確定の手順 (§2.3)、索引別 control 集合と ID lookup の 3 値 (§2.4)、部分登録への erratum (§2.5)、catalog の生成契約・読み・seal 手順 (§3)、補助探索 3 経路の形の登録 (§4) | 親 (docs) |
| 2 | 生成器 `orchestrator/axis_b5_search/catalog.py` + test、生成物 `docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-search-catalog.json` | 点 2 の catalog bytes | 生成器と test は Codex author (D95)。catalog は親が生成器を実走して得る |
| 3 | 後継凍結物 2/2 `2026-09-08-backoff-axis-b5-closure-record.md` | 点 1 の主キーと locator、索引別 ID lookup の結果、点 2 の SHA-256、点 3 の anchor ごとの stream の確定 | 親 (docs) |

**この順は commit 順でもある。** 本文書の commit より前に anchor の識別子を照会せず、
catalog の commit より前に SHA-256 を書かない。順序を守れなかった場合は、その成果物を
使わず、新しい日付の後継物でやり直す。

## 2. 候補 3 群の有限 anchor 集合 (凍結) と主キー確定の手順

### 2.1 選定規則

軸登録 §3 が名指しした 3 群 (Cicada 原論文 / 確率近似・有限差分勾配法の適応 step・適応窓 /
STM の適応 contention manager) を、部分登録 §4.2 のとおり slot `G1-CICADA` / `G2-SA` / `G3-STM` とする。

- **軸登録 §3 が括弧内で名指ししたもの (Cicada 原論文、Kiefer–Wolfowitz 型の hill climbing、
  加速確率近似、SPSA の gain 選択、polymorphic / adaptive contention management、
  adaptive transaction scheduling) を必ず含める。** 名指しは work を一意に指さないので、
  各名指しに対して登録者が知る一次文献を 1〜2 件ずつ採り、その選択は §6 の事前知識として開示する。
- `G2-SA` には、軸登録 §3 が「確認すべき点」に挙げた「勾配推定の分散に応じて窓幅 (標本数) を
  動的に決める規則」の代表として、適応 sampling (標本数選択) の一次文献を 2 件加える。
  条件 C 相当を扱う候補が群に 1 つも無いと、`G2-SA` が `方法論的祖先` として何を検査するのかが
  無くなるためである。
- `G3-STM` には、contention manager 概念の導入元、走行中観測で待ち方を決める系譜、
  正しさ・進行保証 (条件 D) 側の 1 本、走行中観測に基づく scheduler の 1 本を含める。
- **検索式に語彙的に掛かりやすいかどうかで選ばない。** 包含 control (部分登録 §4.3) は
  「登録した式が既知の関連文献に届くか」を測るものであり、届きやすいものを選べば control が
  恒真になる (D351 の逆向きの reward hack)。**したがって、登録語彙で届きにくいと静的に見込まれる
  anchor も外さない。** 包含 control が不発なら、それは登録語彙の限界を示す正当な結果であり、
  部分登録 §5.3 のとおり軸は `未完走` になり、§5.4 の意味的 amendment (語彙の追加) へ進む。
  **不発を理由に anchor を差し替えて control を通すことは、この経路の外にあり、許さない。**
- **集合は本文書で閉じる。** 追加・削除・差し替えは部分登録 §5.4 の意味的 amendment とし、
  新しい日付の後継物・新しい control ID・全枝の再実行・独立レビューを要する。
  **lookup または検索の結果を見た後の変更は、旧契約を `未完走` に固定し、見た結果を開示し、
  新しい ID で全枝を再実行する** (部分登録 §5.4 の逐語継承)。同じ ID の上での差し替えは無い。
  **結果を見て代表を選ばない** (部分登録 §4.2 項目 2)。
- 各 anchor の手掛かり (著者・題・venue・年) と「記憶している識別子」は登録者の事前知識であり
  (§6)、**主キーではない**。主キーは §2.3 の手順で一次書誌資料から確定したものだけである。

### 2.2 anchor 集合 (16 件、閉集合)

主キー欄は本文書では**すべて未確定**である。確定値は後継凍結物 2/2 が持つ。
「届くと想定する枝と語」は、題名と登録理由だけから登録者が静的に付けた見込みであり
(要旨は未読)、control の期待値ではない。**想定なし**と書いた anchor も control から外さない (§2.1)。

| anchor ID | slot | 手掛かり (著者 / 題 / venue / 年) | 記憶している識別子 (未確認、手掛かり) | 群に入れる理由 | 届くと想定する枝と語 (静的) | 主キー |
|---|---|---|---|---|---|---|
| `G1-01` | `G1-CICADA` | Lim, Kaminsky, Andersen / Cicada: Dependably Fast Multi-Core In-Memory Transactions / SIGMOD / 2017 | DOI `10.1145/3035918.3064015` | CCBench の適応 backoff の算法の出自 (軸登録 §3) | `B5-Q4` (要旨に T 語と `backoff` があれば)。題名だけでは T/M/O 語なし | 未確定 |
| `G2-01` | `G2-SA` | Robbins, Monro / A Stochastic Approximation Method / Ann. Math. Statist. 22(3) / 1951 | DOI `10.1214/aoms/1177729586` | 確率近似と gain sequence の起点 | M `stochastic approximation`。C 語の想定なし | 未確定 |
| `G2-02` | `G2-SA` | Kiefer, Wolfowitz / Stochastic Estimation of the Maximum of a Regression Function / Ann. Math. Statist. 23(3) / 1952 | DOI `10.1214/aoms/1177729392` | 有限差分勾配型 hill climbing の起点 (軸登録 §3 名指し) | 想定なし (題名に M/C 語なし) | 未確定 |
| `G2-03` | `G2-SA` | Kesten / Accelerated Stochastic Approximation / Ann. Math. Statist. 29(1) / 1958 | DOI `10.1214/aoms/1177706705` | 差分符号の変化で step を適応させる加速確率近似 (軸登録 §3 名指し) | M `stochastic approximation`。C 語の想定なし | 未確定 |
| `G2-04` | `G2-SA` | Spall / Multivariate Stochastic Approximation Using a Simultaneous Perturbation Gradient Approximation / IEEE Trans. Autom. Control 37(3) / 1992 | DOI `10.1109/9.119632` | SPSA の原論文 | M `stochastic approximation`。C 語の想定なし | 未確定 |
| `G2-05` | `G2-SA` | Spall / Implementation of the Simultaneous Perturbation Algorithm for Stochastic Optimization / IEEE Trans. Aerosp. Electron. Syst. 34(3) / 1998 | DOI `10.1109/7.705889` | SPSA の gain 選択 (軸登録 §3 名指し) | M `SPSA` / O `gain sequence` (要旨にあれば)。C 語の想定なし | 未確定 |
| `G2-06` | `G2-SA` | Delyon, Juditsky / Accelerated Stochastic Approximation / SIAM J. Optim. 3(4) / 1993 | DOI `10.1137/0803045` | 適応 step の解析 | M `stochastic approximation`。C 語の想定なし | 未確定 |
| `G2-07` | `G2-SA` | Byrd, Chin, Nocedal, Wu / Sample Size Selection in Optimization Methods for Machine Learning / Math. Program. 134(1) / 2012 | DOI `10.1007/s10107-012-0572-5` | 勾配推定の分散で標本数 (窓幅) を動的に決める規則 = 条件 C 相当 | W `sample size`。C 語の想定なし (`B5-Q8` には C が要る) | 未確定 |
| `G2-08` | `G2-SA` | Bollapragada, Byrd, Nocedal / Adaptive Sampling Strategies for Stochastic Optimization / SIAM J. Optim. 28(4) / 2018 | DOI `10.1137/17M1154679`、arXiv `1710.11258` | 同上 (inner product test による標本数の適応) | W `sample size` (要旨にあれば)。C 語の想定なし | 未確定 |
| `G3-01` | `G3-STM` | Herlihy, Luchangco, Moir, Scherer / Software Transactional Memory for Dynamic-Sized Data Structures / PODC / 2003 | DOI `10.1145/872035.872048` | contention manager 概念の導入 (DSTM) | T `software transactional memory`。`B5-Q4` は要旨に `contention manager` があれば | 未確定 |
| `G3-02` | `G3-STM` | Scherer, Scott / Advanced Contention Management for Dynamic Software Transactional Memory / PODC / 2005 | DOI `10.1145/1073814.1073861` | backoff 系 contention manager を走行中観測で決める系譜 | `B5-Q4`: T `software transactional memory` ∧ M `contention management` (題名) | 未確定 |
| `G3-03` | `G3-STM` | Guerraoui, Herlihy, Pochon / Polymorphic Contention Management / DISC (LNCS 3724) / 2005 | DOI `10.1007/11561927_23` | 走行中に contention manager を適応的に切り替える (軸登録 §3 名指し) | M `contention management` (題名)。T は要旨次第 | 未確定 |
| `G3-04` | `G3-STM` | Guerraoui, Herlihy, Pochon / Toward a Theory of Transactional Contention Managers / PODC / 2005 | DOI `10.1145/1073814.1073863` | contention manager の正しさ・進行保証 (条件 D 側) | M `contention manager` (題名)。T は要旨次第 | 未確定 |
| `G3-05` | `G3-STM` | Yoo, Lee / Adaptive Transaction Scheduling for Transactional Memory Systems / SPAA / 2008 | DOI `10.1145/1378533.1378564` | adaptive transaction scheduling (軸登録 §3 名指し) | `B5-Q4`: T `transactional memory` / `transaction scheduling` ∧ M `adaptive transaction scheduling` (題名) | 未確定 |
| `G3-06` | `G3-STM` | Spear, Dalessandro, Marathe, Scott / A Comprehensive Strategy for Contention Management in Software Transactional Memory / PPoPP / 2009 | DOI `10.1145/1504176.1504199` | contention management 戦略の体系化と backoff の扱い | `B5-Q4`: T `software transactional memory` ∧ M `contention management` (題名) | 未確定 |
| `G3-07` | `G3-STM` | Dragojević, Guerraoui, Singh, Singh / Preventing versus Curing: Avoiding Conflicts in Transactional Memories / PODC / 2009 | DOI `10.1145/1582716.1582725` | 走行中観測に基づく transaction scheduler (Shrink) | T `transactional memory` 相当 (題名は複数形)。M/O は要旨次第 | 未確定 |

`G1-CICADA` は単一の work、`G2-SA` と `G3-STM` は群である (部分登録 §4.2 項目 2)。
部分登録 §4.2 の表が slot ごとに要求する包含枝 (`G1`: `B5-Q4` または `B5-Q10`、
`G2`: `B5-Q3` / `B5-Q6` / `B5-Q7` / `B5-Q8` の和、`G3`: `B5-Q4` / `B5-Q5` / `B5-Q10` の和、
DBLP は対応する二項直積の和) はそのまま継承する。

**構造的な懸念の開示:** `G2` の包含枝はすべて C block を含むが、上表のとおり `G2` の全 anchor に
C 語の想定が無い。したがって `G2` の包含 control は不発になる見込みが高く、その場合は §2.1 の
とおり軸が `未完走` になって語彙の amendment へ進む。これは本文書が選んだ経路であり、
anchor の差し替えでは解決しない。

### 2.3 主キー確定の手順 (一次書誌資料)

各 anchor について次を行い、結果を後継凍結物 2/2 に locator つきで書く。

1. **DOI の解決:** `https://doi.org/<DOI>` へ HEAD request を出し、HTTP 30x の `Location`
   (出版社の landing page) を記録する。解決しない DOI は主キーにしない。
2. **登録機関 record による書誌の相互確認:** `https://api.crossref.org/works/<DOI>` の
   `message.title` / `message.author` (family, given) / `message.container-title` /
   `message.issued.date-parts` / `message.type` を、§2.2 の手掛かり (題・著者・venue・年) と
   突き合わせる。Crossref が 404 を返す DOI は、その DOI の登録機関 (DataCite 等) の record で
   同じ項目を確認する。**登録機関 record が得られない DOI は、出版社 landing page に DOI・題・
   著者・venue・年がすべて表示されている場合に限り一次資料とし、そうでなければ `要裁定` とする。**
3. **arXiv ID の確認:** 手掛かりに arXiv ID を持つ anchor は
   `https://export.arxiv.org/api/query?id_list=<arXiv ID>&max_results=1` の `feed/entry` の
   `title` / `author/name` / `id` (版番号 `vN` を含む) を同様に突き合わせる。
4. **同一性の判定:** 題が一致し (大文字小文字・句読点・冠詞の差は許す)、著者姓の列が一致し、
   venue と年が矛盾しないときだけ、その識別子を主キーとして固定する。
   1 つでも食い違えば主キーを固定せず `要裁定` とし、その anchor の slot は
   **その anchor に関して未配置**のまま残す (他の anchor で slot が配置されることは妨げない)。
5. **版:** 主キーは出版版 (DOI) と preprint (arXiv ID) を区別して記録する。`message.type`
   (`journal-article` / `proceedings-article` / `book-chapter`) と、arXiv は照会時点の最新版番号を
   record に残す。DOI と arXiv ID の両方を持つ anchor は 7.7.6 に従い同じ record (alias record) に
   束ね、索引別 ID lookup では索引が鍵として引ける方の識別子を使う。
6. **名称 alias:** 7.7.6 に従い、system 名・略称 (`Cicada`、`DSTM`、`Polka`、`ATS`、`Shrink` など、
   登録者が知るもの) を同じ record に**名称 alias として**置く。名称 alias は主キーではなく、
   ID lookup にも包含 control にも使わない。
7. **「記憶している識別子」が誤っていた場合:** 正しい識別子の候補は Crossref の
   `works?query.bibliographic=<題>` などの名称検索で**見つけてよい** (7.7.6 の「手掛かり」)。
   固定は上記 1〜5 を満たした場合だけであり、誤っていた事実と見つけ方を後継凍結物 2/2 に残す。

### 2.4 索引別 control 集合と ID lookup

部分登録 §4.2 項目 3 の「3 索引それぞれについて、固定した主キーで ID lookup が到達することを
実行前に確かめる」を、次の順で実施する。**ID lookup は収録の確認であって control ではない**
(部分登録 §4.2、§4.3)。

**(a) 索引別 control 集合を lookup の前に固定する。** 集合の membership は、§2.2 の手掛かりが持つ
鍵型と、索引の収録範囲についての登録者の事前知識だけで決め、**lookup や検索の結果で変えない。**
各 member に control ID `B5-ANC-<anchor ID>@<索引>` を与える (部分登録 §4.3 の包含 control の ID)。

| 索引 | member の規則 | member (control ID の anchor 部分) | 非 member とその理由 |
|---|---|---|---|
| OpenAlex | DOI を持つ anchor 全部 | 16 件全部 | なし |
| arXiv | arXiv ID を手掛かりに持つ anchor | `G2-08` | 他 15 件: arXiv ID を持たない (本文書が登録する request 形 `id_list=` は arXiv ID だけを鍵にする) |
| DBLP | DOI を持ち、venue が計算機科学の書誌である anchor | `G1-01`、`G2-04`〜`G2-08`、`G3-01`〜`G3-07` (13 件) | `G2-01`〜`G2-03`: Ann. Math. Statist. は DBLP の収録範囲外 (登録者の事前知識。`G2-05` の IEEE TAES が収録範囲内かは確信が無く、非収録なら (c) のとおり `未完走` になる) |

**(b) lookup の request と応答の 3 値。** anchor × 索引ごとに次の**どれか 1 つ**で記録する。

| 索引 | request (主キー別) | `収録` の形 | `非収録` の形 |
|---|---|---|---|
| OpenAlex | `https://api.openalex.org/works/https://doi.org/<DOI>?select=id,doi,title,publication_year,ids,authorships,referenced_works_count` | HTTP 200、JSON の `id` (`https://openalex.org/W...`) | HTTP 404 |
| arXiv | `https://export.arxiv.org/api/query?id_list=<arXiv ID>&max_results=1` | HTTP 200、`feed/entry` 1 件 | HTTP 200、`opensearch:totalResults` = 0、entry 0 件 |
| DBLP | `https://dblp.org/search/publ/api?q=<DOI を percent encoding>&format=json&h=5` | HTTP 200、`application/json`、`result.hits.hit` に当該 DOI を持つ record | HTTP 200、`application/json`、`result.hits.@total` = 0 |

- **`収録`:** 索引が主キーで当該 record を返した。索引固有 ID (OpenAlex `W...`、arXiv ID、
  DBLP key) と locator を記録する。
- **`非収録`:** 索引は正常に応答した (上表の形) が record が無い。
- **`不達`:** 通信失敗、timeout、上表以外の HTTP status、期待 content type 以外の応答
  (anti-bot challenge の HTML を含む)、整形されていない body。索引の可用性の失敗である。
- 非 member の anchor × 索引の組は、鍵が無ければ request を出さず「鍵なし」と記録し、
  鍵があれば (DBLP の `G2-01`〜`G2-03`) 記録のために照会してよいが control には数えない。

**(c) 帰結 (部分登録 §4.2 項目 3 の帰結をそのまま保つ):**

- member の lookup が **`不達` または `非収録`** なら、部分登録のとおり**当該索引のその走行と
  軸全体を `未完走` とし、当該 slot の control は未配置**とする。走行を開始できない。
  **`非収録` を見て member から外すことはしない** (外せば control が空になる)。
  是正は §2.1 の意味的 amendment (新しい ID、開示、独立レビュー) だけである。
- 実行時 (部分登録 §4.3) は、各 member が slot の包含枝の和集合に含まれることを control とする。
  不発なら当該索引のその走行を `未完走` とする。部分登録 §5.2 の
  `all(§4.3 の anchor 包含 control が発火)` は、この member 集合 (`B5-ANC-*`) の全部について
  発火することと読む。
- member が無い (slot, 索引) の組 (`G1` × arXiv、`G3` × arXiv、`G2` のうち `G2-01`〜`G2-03` × DBLP)
  には包含 control が**無い**。これは結果を見て外したものではなく鍵型と収録範囲による構成上の
  不在であり、**限界として後継凍結物 2/2・実行記録・`RW3` の主張に併記する。** その索引を
  母集合から外すことも、その索引の主 query・演算子 control を省くこともしない。

**(d) 本 wave で実施する範囲と、実行 wave が繰り返す範囲:**

- 本 wave (後継凍結物 2/2) は、OpenAlex と arXiv の ID lookup を上表の request で行い、3 値を記録する。
- DBLP は §6 の観測どおり本環境から challenge を返すので、**anchor 固有の request は送らない。**
  後継凍結物 2/2 の DBLP 欄には「anchor 固有 request 未送信。共有 endpoint の環境 preflight
  (§6) が challenge = `不達`」と、証拠の粒度をそのまま書く。16 件の個別応答があるかのようには書かない。
- 部分登録 §4.2 項目 3 の「実行前」は、実行 wave の live preflight を指す。**live preflight は
  3 索引すべての member について ID lookup を改めて行い、その時点の 3 値を実行記録に書く。**
  本 wave の結果は早期の収録確認であり、live preflight を代替しない。live preflight で DBLP が
  `不達` のままなら、(c) のとおり軸は走行を開始できない。

### 2.5 部分登録への erratum (意味的 amendment を含む)

部分登録の bytes は変えない。次を本文書が持つ。

**E-1 (§4.2 項目 3・§4.3・§5.2 の control 集合の定義、意味的 amendment):** 部分登録 §4.2 項目 3 は
「3 索引それぞれについて、固定した主キーで ID lookup が到達すること」を要求し、包含 control の
対象 anchor 集合を索引ごとに定義していない。文面どおりに「全 anchor × 全索引」と読むと、
§6 の観測 (arXiv の `id_list=` は arXiv ID だけを鍵にし、OpenAlex は本文書が登録する 2 つの
request 形では arXiv ID を鍵にできない) から、arXiv ID を持たない anchor を 1 つでも含めた時点で
arXiv の lookup が構造的に成立せず、軸全体が `未完走` に固定される (D1207 が言う「完走述語が
索引の性質に対して構造的に成立しない」型)。本文書 §2.4 (a) は、**索引別の control 集合を
lookup の前に鍵型と収録範囲だけで固定し、その member について部分登録の帰結
(不達・非収録なら当該索引の走行と軸全体を `未完走`、slot の control は未配置) をそのまま保つ**
形に改めた。**受理集合の向き:** member でない組に包含 control が無いぶん、部分登録の
「全 anchor × 全索引」の読みより**広い**。広げた範囲はその 1 点に限り、`不達` の帰結、
`非収録` の帰結、演算子 control、主 query、母集合はいずれも広げていない。
member の集合は結果を見ずに固定し、**結果を見て member から外すことを禁じる。**
この amendment の射程は部分登録 §4.2 項目 3、§4.3、§5.2 の `all(§4.3 …)` の 3 箇所である。
新しい control ID (`B5-ANC-<anchor ID>@<索引>`) を与える。主 query の ID は変えない
(主 query は 1 本も走っていないため、D1207 の「新しい query ID」は control にだけ当てる)。
**この amendment は軸 B5 の検索結果を 1 件も見る前に行った** (§0、§6)。
独立レビューは本 wave の段 3 / 段 6 の敵対レビューが担い、逐語は
`output/insights/2026-09-08_t2380-b5-closure/` に置く。

**E-2 (§4.2 項目 3 の「実行前」の時点):** 「実行前に確かめる」の時点を、実行 wave の
live preflight と定める (§2.4 (d))。本 wave の lookup は早期確認であり、代替ではない。

**E-3 (§4.5 の補助探索 3 経路の「後継凍結物」の分担):** 部分登録 §4.5 は anchor に依存する 3 経路の
stream ID・request template・ページング規則を「§4.2 の gate が閉じた後の後継凍結物」が確定するとした。
本文書 §4 は主キー確定より前に**形 (anchor の識別子を変数に持つ template)** を登録し、
anchor ごとの stream の**確定**は主キー確定後の後継凍結物 2/2 が行う。順序の変更ではなく分担の明示である。

## 3. query catalog の生成契約と seal の手順

### 3.1 生成器

- **path:** `orchestrator/axis_b5_search/catalog.py` (package `orchestrator/axis_b5_search/`)。
  Codex `role=author` が書き、親は実走だけを行う (D95)。
- **入力 (すべて凍結文の逐語):** 部分登録 §3.1 の 6 block 85 語 (列挙順・表記・ハイフンを保つ)、
  §3.2 の 10 枝と block 順、§3.3 の展開規則 1〜7 と template、§3.5 の二項直積 7 枝、
  §4.1 の control 14 本 (X = `backoff`、Y = `update interval`)、§4.5 の venue 8 件 × 年 1993〜2026。
- **network・時刻・環境変数・応答件数を入力にしない。** 同じ入力 commit で同じ bytes を出す。
- 既存の `orchestrator/axis1_search` を import しない (別の登録 epoch の束縛を混ぜない)。
- CLI: `python3 -m orchestrator.axis_b5_search.catalog --output <path>` が生成し、
  `--verify <path>` が「file の bytes == 生成 bytes」を要求して不一致なら非 0 で終わる。
  2 つの option は排他で、どちらか 1 つが必須。不一致と読取不能はどちらも rc=1。
  診断文の文言は seal の対象ではない。

### 3.2 catalog の形

- **出力 path:** `docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-search-catalog.json`
- **bytes:** `json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n"` を UTF-8 で書く。
  `sort_keys` は object の key だけを並べ替え、配列の順序は §3.4 項目 4 で固定する。
- **top-level field (この 11 個だけ):** `schema_version`、`registration_path`、`registration_blob`、
  `closure_preregistration_path`、`cutoff`、`blocks`、`branches`、`queries`、`controls`、
  `aux_venue_streams`、`expected_cardinalities`。
- **entry の形:**
  - `blocks[]`: `block_id`、`terms[]` (`term_id`、`term`)
  - `branches[]`: `branch_id`、`block_ids`
  - `queries[]`: `query_id`、`index`、`branch_id`、`term_groups`、`request_template`、`first_page_url`
  - `controls[]`: `control_id`、`index`、`term_groups`、`request_template`、`first_page_url`、`shares_request_with`
  - `aux_venue_streams[]`: `stream_id`、`index`、`venue`、`year`、`request_template`、`first_page_url`
  - `term_groups` は語 ID の配列の配列で、group 内が OR、group 間が AND を表す (§3.4 項目 1・2)。
    DBLP の主 query は `[[<語X の ID>], [<語Y の ID>]]` (前方一致の連言)。
- **期待 AST (部分登録 §3.4) と期待 DBLP echo (同 §3.5) は catalog に置かない。** 期待 AST は
  `blocks` / `branches` / `cutoff` から部分登録 §3.4 の構成規則で一意に導出でき、control の AST は
  `term_groups` から導出できる。期待 echo は §3.4 項目 10 の規則で導出する。導出コードは実行 wave の
  実行器が持ち、その bytes は部分登録 §5.3 の registration preflight で束縛する。
- **anchor、ID lookup の結果、引用・著者経路の stream は catalog に置かない。**
- **ID 規約:** 主 query は部分登録 §3.3 規則 7 のまま。control は §4.1 の `B5-CTL-<役割>@<索引>`。
  venue stream は §4.5 の `B5-AUX-VENUE@dblp/<venue>-<year>`。

### 3.3 seal の手順

1. 親が生成器を実走して catalog を書き、`--verify` で bytes の一致を確かめる。
2. catalog の file bytes の SHA-256 を、生成器の blob (commit 2 の `catalog.py` の blob) と
   catalog の blob と併せて後継凍結物 2/2 に書く。seal 内部の別 digest は持たない
   (軸 3 の先例が区別した「seal 本体の canonical digest」は今回導入しない)。
3. 件数の自己検算 (arXiv 10 / OpenAlex 10 / DBLP 1602 / control 14 / venue 272) と、
   部分登録 §3.3 の照合例 `B5-Q10@dblp/T01-O01` の bytes 一致を、生成器の test と親の実測の
   両方で確かめる。
4. **部分登録 §5.3 の registration preflight 全体 (parser・fixture・schema・実行器の bytes の束縛)
   は本 wave の範囲外である。** 実行器は存在しない。catalog の seal は、その preflight が
   束縛する対象の 1 つを先に固定するものである。

### 3.4 凍結文から一意に読めない箇所の読み (登録)

生成器が決定的に bytes を作るために必要で、部分登録の文面から一意に読めない箇所を、
段 2 のプラン起草と段 3 の敵対相談で列挙し、親が次のとおり読みを固定した。
**本節に無い読みを生成器が採ることは許さない。**

1. **単一 operand の control** (`B5-CTL-X@*`、`B5-CTL-Y@*`) は 1 語の singleton block として
   規則 3・4 を当てる。percent encoding 前の式は、arXiv が
   `(abs:"backoff") AND submittedDate:[199101010000 TO 202612312359]`、OpenAlex が
   `title_and_abstract.search:(backoff),to_publication_date:2026-12-31`。
2. **`X OR Y`** (`B5-CTL-OR@*`) は 1 group 2 語 (`(abs:"backoff" OR abs:"update interval")`、
   `(backoff OR update interval)`)。**`X AND Y`** (`B5-CTL-AND@*`、`B5-CTL-AND2023@*`) は
   singleton group 2 個 (`(abs:"backoff") AND (abs:"update interval")`、
   `(backoff) AND (update interval)`)。`term_groups` はそれぞれ `[["M01","C01"]]` と
   `[["M01"],["C01"]]`。DBLP の `B5-CTL-X@dblp` は `[["M01"]]`、`B5-CTL-Y@dblp` は `[["C01"]]`、
   `B5-CTL-AND@dblp` と `B5-CTL-AND2023@dblp` は `[["M01"],["C01"]]`。
3. **`B5-CTL-AND2023@arxiv`** の日付節は `submittedDate:[199101010000 TO 202312312359]`
   (下限は部分登録 §2.2 の技術的下限のまま)、`B5-CTL-AND2023@openalex` は
   `to_publication_date:2023-12-31`。`B5-CTL-AND2023@dblp` の `request_template` と
   `first_page_url` は `B5-CTL-AND@dblp` と byte 同一で、`shares_request_with` = `"B5-CTL-AND@dblp"`。
   他の control の `shares_request_with` は JSON の `null`。
4. **配列の順序:** `blocks` は T、M、O、C、W、V。各 `terms` は部分登録 §3.1 の列挙順。
   `branches` は `B5-Q1`〜`B5-Q10`。`queries` は arXiv の `B5-Q1`〜`Q10`、OpenAlex の同、
   DBLP の `B5-Q4`〜`Q10` の枝順で、枝内は左の語を外側・右の語を内側に回す。
   `controls` は部分登録 §4.1 の表の順 (arXiv 5、OpenAlex 5、DBLP 4)。`aux_venue_streams` は
   venue を外側 (部分登録 §4.5 の列挙順)、年を内側 (1993→2026)。
   **この順は直列化の順であって実行順ではない。** 実行順は部分登録 §5.3 (索引順、query ID の辞書順)
   で一意に決まっており、実行器は catalog の配列順をそのまま使わず §5.3 の順へ並べ替える。
5. `schema_version` = `izanagi-axis-b5-search-catalog/v1`。`registration_path` =
   `docs/related-work/claim-survey/2026-09-07-backoff-axis-b5-search-preregistration.md`、
   `registration_blob` = `f7e3190f9ce92345fd4a91caecae8cd6bf7a5666` (部分登録の blob。
   **小文字 40 桁・接頭辞なし**)。`closure_preregistration_path` =
   `docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-closure-preregistration.md`。
   `cutoff` = `2026-12-31`。
6. `expected_cardinalities` の key と値: `blocks` 6、`terms` 85、`branches` 10、`arxiv_queries` 10、
   `openalex_queries` 10、`dblp_queries` 1602、`queries` 1622、`controls` 14、`aux_venue_streams` 272。
7. **percent encoding** は parameter の値だけに当て、`urllib.parse.quote(value, safe="-_.~")` を
   使う (`quote_plus` は使わない)。OpenAlex の `filter` 値だけ `safe="-_.~,"`。URL の `?` `=` `&` と
   `{POS}` / `{CUR}` は符号化した値の外側に文字列として置く。
8. **DBLP の `q`** は語を生の空白 1 個で連結してから一度だけ符号化する (`%20` を再符号化して
   `%2520` にしない)。`first_page_url` は `{POS}` = `0`。
9. **arXiv の `abs:"<語>"`** は語をそのまま二重引用符で囲む。語内の空白・ハイフンはそのまま。
   OpenAlex の複数語の term は引用符なしでそのまま置く (部分登録 §3.3 規則 4)。**bytes はこれで
   一意だが、索引がそれを phrase と解釈するか語の連言と解釈するかは未観測であり、live preflight の
   検証点である。観測結果で期待値を後付けしない** (部分登録 §2.3)。
10. **DBLP の期待 echo の導出規則 (catalog に置かない登録値):** 送信した各語を空白とハイフンで
    token に分け、各 token の末尾に `*` を付け、空白 1 個で連結する。大文字小文字は送信どおり。
    部分登録 §3.5 の 3 例 (`back-off` → `back* off*` 等) はこの規則の特殊例である。
    3 分ハイフンの語は登録語に無い。**この規則は 2026-08-27 の別語での観測からの外挿**であり、
    live preflight で違えば部分登録 §5.4 の意味的 amendment とする。
11. **venue stream** の `q` は literal `venue%3A<venue>%3A%20year%3A<year>%3A` (部分登録 §4.5 の
    template のまま。語 ID を持たない)。生成器の DBLP URL 組立ては符号化済みの `q` を受け取る
    契約とし、主 query・control の `q` は項目 8 で、venue の `q` はこの literal で作る。
12. **語 ID** は `<block 文字><列挙順の 2 桁 0 埋め>` (`T01`〜`T12`、`M01`〜`M19`、`O01`〜`O10`、
    `C01`〜`C21`、`W01`〜`W13`、`V01`〜`V10`)。

## 4. 補助探索のうち anchor に依存する 3 経路 — 形の登録

部分登録 §4.5 は、後方引用・前方引用・著者の 3 経路について「stream ID・request template・
ページング規則は §4.2 の gate が閉じた後の後継凍結物が確定する」とした。本節は E-3 のとおり
**形を登録し**、anchor ごとの stream の確定は後継凍結物 2/2 が行う。
経路・索引・上限・選択順序 (主キーの辞書順昇順) は §4.5 のまま変えない。

**起点集合は lookup の前に固定する:** 3 経路の起点は §2.2 の 16 anchor 全部である
(全 anchor が DOI を持ち、OpenAlex の control 集合の member である)。
起点 anchor が live preflight の OpenAlex lookup で `収録` でなければ、§2.4 (c) のとおり軸は
走行を開始できない。**起点を結果で減らすことはしない。**

| 経路 | stream ID | request template | ページングと完走 | 上限と採用 |
|---|---|---|---|---|
| 後方引用 | `B5-AUX-REF@openalex/<anchor ID>` | `https://api.openalex.org/works/<W-ID>?select=id,referenced_works,referenced_works_count` | 1 request。**経路固有の完走述語:** HTTP 200、content type が JSON、`referenced_works` が配列として存在し、その長さが `referenced_works_count` と一致 (部分登録 §5.1 の条件 5 相当)、条件 6 (正常終端)。条件 2・3 は 1 request なので該当しない | 全件 (配列全体) |
| 前方引用 | `B5-AUX-CITES@openalex/<anchor ID>` | `https://api.openalex.org/works?filter=cites:<W-ID>,to_publication_date:2026-12-31&per-page=200&cursor={CUR}` | 部分登録 §3.3 の `{CUR}` 規則 (初回 `*`、以後 `meta.next_cursor`) で**正常終端まで**取得し、§5.1 の条件 2・3・5・6 で `完走` を判定する | **上限 200 は採用集合の上限**である。取得した全 record を全順序 (横断主キー = DOI があれば DOI、無ければ OpenAlex ID、同順位は OpenAlex work ID) の昇順に並べ、先頭 200 件だけを候補として台帳へ入れる。採用外の record は生証拠 (応答 bytes) として残るが候補にせず、感度監査にも入れない |
| 著者 | `B5-AUX-AUTH@openalex/<anchor ID>-first` / `-last` | `https://api.openalex.org/works?filter=author.id:<A-ID>,to_publication_date:2026-12-31&per-page=200&cursor={CUR}` | 同上 | 同じ規則で先頭 100 件 |

- `<W-ID>` は §2.4 の OpenAlex ID lookup が返した `id` (`https://openalex.org/W...` の `W...`)。
- `<A-ID>` は同じ応答の `authorships` から、`author_position` が `"first"` の要素と `"last"` の要素の
  `author.id` (`A...`) を採る。**配列の先頭・末尾が `author_position` と一致しない、
  `author_position` が欠落する、`first` / `last` が 0 件または 2 件以上ある場合は `要裁定` とし、
  その anchor の著者 stream は確定しない。** 第一著者と最終著者が同一なら `-first` の 1 本だけとする。
- 「正常終端まで取得して採用集合だけを切る」読みを採る理由: OpenAlex は主キー (DOI) 順の
  server 側 sort を提供しないため、§4.5 の「主キーの辞書順昇順で先頭から採る」を server 側の
  打ち切りでは実現できない。**部分登録 §4.5 の「上限で打ち切った `完走`」は、取得が正常終端し
  採用集合が上限で切られた stream を指す**と読む。上限は候補数の上限であり、感度監査の候補数も
  この上限内に留まる (部分登録 §4.4 の範囲を広げない)。
- author ID は OpenAlex の著者同定に依存する。同定の誤りは限界として §7 に置き、
  名称による著者検索へ切り替えない (7.7.6)。
- 上表の request 形 (`filter=cites:`、`filter=author.id:`、`select=referenced_works`) は
  登録値であり、本 wave では観測していない。live preflight で content type・ページング・filter の
  解釈を検証し、違えば部分登録 §5.4 の意味的 amendment とする。
- venue 年次一覧の 272 stream は部分登録 §4.5 で確定済みであり、本文書は変えない。

## 5. 本 wave が出す外部 request の範囲

- §2.3 の書誌解決 (doi.org、Crossref、arXiv `id_list`) と §2.4 の OpenAlex / arXiv の ID lookup。
- **catalog の query (主 query・control・venue stream) と §4 の stream は 1 本も送らない。**
- DBLP へは §6 の応答形の観測以外に request を出さない。challenge の JS を模倣しない。
- 1 request ごとに 1 秒以上あけ、User-Agent に連絡先を含める。

## 6. 登録前に見えていたもの (事前知識の開示) と、非 anchor による応答形の観測

- 登録者は §2.2 の「記憶している識別子」と名称 alias を事前知識として持っていた。いずれも一次資料で未確認である。
- 部分登録・軸登録の全文、軸 1 / 軸 3 の事前登録・改訂・実行記録の構造、軸 3 の索引実測。
- **anchor の識別子は 1 本も照会していない。** 応答形の観測には CCBench 自身の論文
  (DOI `10.14778/3424573.3424575`、`external/ccbench/README.md` に記載) と、arXiv `1706.03762`、
  および存在しない DOI `10.9999/b5probe.missing` / arXiv ID `9999.99999` を使った。
  生応答 (header・body・観測時刻) は `output/insights/2026-09-08_t2380-b5-closure/probe/` に置く。
  観測した事実は**次の exact request についてのもの**であり、索引全体の性質への一般化ではない:
  - OpenAlex `GET works/https://doi.org/10.14778/3424573.3424575` → 200 JSON (`id` = `W3094958164`)。
    `GET works/https://doi.org/10.9999/b5probe.missing` → 404。
    `GET works/arxiv:1706.03762` と `GET works/https://doi.org/10.48550/arXiv.1706.03762` → どちらも 404。
    **検証していない経路** (可能性の列挙であり、利用可能とは言わない): `filter=ids.arxiv:`、
    `filter=doi:10.48550/arXiv.<id>`、landing page URL による filter、既知 W-ID の `ids` / `locations`
    からの arXiv alias。§2.4 (a) の arXiv / OpenAlex の member 規則はこれらを使わない。
  - arXiv `GET api/query?id_list=1706.03762&max_results=1` → 200 Atom で entry 1 件。
    `id_list=9999.99999` → 200 Atom で `opensearch:totalResults` = 0、entry 0 件。
    `id_list=` に DOI を渡す request は出していない (API 仕様に DOI を鍵にする field が無いという
    知識に基づく)。
  - doi.org `HEAD 10.14778/3424573.3424575` → 302、`Location` = `https://dl.acm.org/doi/10.14778/3424573.3424575`。
    Crossref `GET works/10.14778/3424573.3424575` → 200 JSON、`works/10.9999/b5probe.missing` → 404。
  - **DBLP: `search/publ/api?q=<DOI>&format=json`、`doi/<DOI>`、`xml/release/` の 3 入口が、
    本ホスト (Pegasus login node) から 2026-09-07 22:05 UTC 前後の観測で、User-Agent
    (自前 / curl 既定 / ブラウザ風 / python-urllib) と `Accept` header (`application/json` /
    `application/xml`) に依らず HTTP 200 `text/html` の anti-bot challenge (Anubis、
    `algorithm=metarefresh`、`difficulty=1`、JS 駆動) を返した。** 2026-08-27 の軸 3 索引実測は
    同 API に到達していた。本 wave はこれを `不達` として扱い、challenge を模倣しない。
    一般化は「列挙した 3 入口が本ホストから観測時点で `不達`」までである。

## 7. この登録自身の限界

- **主キー・catalog の SHA-256・起点の値は本文書に無い。** 後継凍結物 2/2 が持つ。
- **軸 B5 は `RW0` のままである。** 本文書は世界の不在を支持せず、実行を認可しない。
- anchor 集合は登録者の事前知識に基づく有限集合であり、3 群の網羅ではない。
- §2.2 の「届くと想定する枝と語」は題名と登録理由からの静的な見込みであり、`G2` の包含 control は
  登録語彙の構造 (包含枝がすべて C を要求する) から不発の見込みが高い。不発は軸の `未完走` と
  語彙 amendment を意味し、anchor の差し替えでは解決しない (§2.1)。
- **包含 control が無い (slot, 索引) の組がある** (`G1` × arXiv、`G3` × arXiv、`G2-01`〜`G2-03` × DBLP)。
  これは鍵型と収録範囲による構成上の不在であり、`RW3` を名乗る場合もこの不在を併記する。
- E-1 は受理集合を広げる amendment である。広げた範囲は「member でない (slot, 索引) の組に
  包含 control が無い」の 1 点に限り、`不達` と member の `非収録` の帰結は広げていない。
- §2.4 の DBLP の request 形 (`q=<DOI>`) は、DBLP が `不達` のため本 wave で観測できていない
  登録値である。§4 の 3 経路の request 形も同じく登録値である。live preflight で形が違うと
  分かれば部分登録 §5.4 の意味的 amendment とする。
- §4 の「正常終端まで取得して採用集合だけを切る」読みは、被引用数が大きい anchor で request 数が
  増える。予算切れは部分登録 §5.3 のとおり当該 stream と軸を `未完走` にする。
- DBLP の member 規則 (§2.4 (a)) は収録範囲についての登録者の事前知識に依存する。
  誤っていれば当該 member が `非収録` になり、軸は `未完走` になる。
