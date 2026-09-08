# 2026-09-08 — 軸 B5 の後継凍結物 (2/2): 部分登録が閉じられなかった 3 点を閉じた記録 (凍結)

- **作成日:** 2026-09-08
- **入力 commit:** `64681dda7c40dc8aecc52378cc131602adef204a` (本 wave の commit 2 = 生成器・test・catalog。後継凍結物 1/2 は commit 1 `caae3b683f2799bfd18babbff2dfcb7d5df194f2`)
- **入力 digest:** 下記 input path の内容は入力 commit の blob そのものである。
  - `docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-closure-preregistration.md` = `f60479f37533c5983bf9d71e8f193e129b1fac31` (以下「1/2」)
  - `docs/related-work/claim-survey/2026-09-07-backoff-axis-b5-search-preregistration.md` = `f7e3190f9ce92345fd4a91caecae8cd6bf7a5666` (以下「部分登録」)
  - `orchestrator/axis_b5_search/catalog.py` = `b850e7b96a5e638b6bc0d880a8cb9d91fbefce94` (生成器)
  - `orchestrator/tests/test_axis_b5_search_catalog.py` = `069552c7295e4c0c57648045296a06859bc61a29`
  - `docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-search-catalog.json` = blob `4f85b3c261537150d78cc8f8cd503bf41e81c3e3`、**file bytes の SHA-256 = `7eb8385e35bd24edac8a227a72ba5bc6b568ca8bc7cac2c8250af8b4ea4c346f`**
- **入力 path:** 上記 5 file、および `docs/related-work/claim-survey/2026-09-05-backoff-axis-registration.md` / `docs/related-work/README.md`
- **文献 cutoff:** 部分登録 §2.2 を継承する (上限 `2026-12-31`、下限なし)
- **規則の正本:** `docs/related-work/README.md` の「7.7 主張軸別の調査状態と、不在主張の成立条件」
- **生証拠の所在:** `output/insights/2026-09-08_t2380-b5-closure/` (`probe/` = 非 anchor の応答形観測、`resolve/` と `resolve2/` = anchor の書誌解決と ID lookup の全応答、`codex/` = 段 2・3・6 の逐語、`mutation/` = 変異台帳)

> **凍結物である。** 書いた後は上書きしない。更新は新しい日付のファイルで行う。
> 進行中の可変状態の正本は `docs/worklog.md` の末尾エントリであり、ここではない。

---

## 0. 総合判定

部分登録 §0 が挙げた「実行を認可しない 3 つの理由」の状態を、1/2 が登録した手順で確定した。

| 点 | 1/2 の手順 | 結果 |
|---|---|---|
| 1. 候補 3 群の主キー | §2.3 (一次書誌資料)、§2.4 (索引別 control 集合と ID lookup) | **16 anchor すべての DOI を固定した** (§1)。OpenAlex は 16/16 `収録`、arXiv は member `G2-08` が `収録`。**DBLP は本環境から `不達`** (anchor 固有 request 未送信、§2)。3 slot とも主キーは配置された |
| 2. query catalog の seal | §3 | 生成器 (Codex author) を親が実走し、**catalog の file bytes の SHA-256 を上記のとおり固定した** (§3) |
| 3. 引用・著者経路の起点 | §4 (形) → 本文書 §4 (確定) | **16 anchor の OpenAlex W-ID と、第一・最終著者の A-ID (延べ 29、異なり 24) を確定し、stream 61 本 (後方引用 16、前方引用 16、著者 29) を列挙した** (§4) |

**それでも軸 B5 は `RW0` のままである。** 本文書は世界の不在を支持せず、検索の実行を認可しない。
実行の前にはなお、(a) 部分登録 §5.3 の registration preflight (parser・fixture・schema・実行器の bytes の束縛。実行器は未実装)、
(b) live preflight (3 索引すべての member について ID lookup を再実施。**DBLP が `不達` のままなら走行を開始できない**)、
(c) 人間の実行認可、が残る。本体論文の軸 1〜5 は動かしていない。

**本 wave で送った外部 request は 1/2 §5 の範囲内である。** catalog の query・control・venue stream・補助探索の stream は 1 本も送っていない。

## 1. 候補 3 群の主キー (点 1)

### 1.1 手順どおりの確定

1/2 §2.3 の手順 1〜7 を 16 anchor に適用した。**「記憶している識別子」は 16 件とも一次資料と一致し、訂正は 0 件**であった。

- 手順 1 (doi.org): 16 件とも HTTP 302 で出版社 landing page へ解決した (表 A の `Location`)。
- 手順 2 (Crossref `works/<DOI>`): 16 件とも HTTP 200。`title`・`author.family`・`container-title`・`issued`・`type` を表 A に写した。
  **`G1-01` と `G3-07` は Crossref が題を `title` と `subtitle` に分けて登録している** (`Cicada` + `Dependably Fast Multi-Core In-Memory Transactions`、
  `Preventing versus curing` + `avoiding conflicts in transactional memories`)。題の照合は `title` + `subtitle` の連結で行い、一致と判定した。
  `G3-07` の第一著者の姓は Crossref で `Dragojević` (発音区別符号つき) であり、1/2 §2.2 の手掛かりと同じ綴りである。
- 手順 3 (arXiv `id_list=`): `G2-08` のみ。HTTP 200、entry 1 件、`id` = `http://arxiv.org/abs/1710.11258v1`、題と著者 3 名が一致。
- 手順 4 (同一性): 16 件とも題 (大文字小文字・句読点の差を許す)・著者姓の列・venue・年が矛盾なく、**主キーを固定した。`要裁定` は 0 件。**
- 手順 5 (版): 表 A の `type` 列。`G3-03` は Springer の LNCS 章として `book-chapter` で登録されている (DISC 2005 の論文集)。
  `G2-08` の preprint は arXiv `1710.11258`、照会時点の最新版 `v1`。他 15 件は arXiv ID を持たない。
- 手順 6 (名称 alias、主キーではない): `G1-01` = `Cicada`、`G3-01` = `DSTM`、`G3-02` = `Polka` (同論文の contention manager 名)、`G3-05` = `ATS`、`G3-07` = `Shrink`。

| anchor ID | 主キー (DOI) | doi.org (HTTP / Location) | Crossref `message.title` (+ `subtitle`) | Crossref `author` (family) | `container-title` / `issued` / `type` / `page` | 判定 |
|---|---|---|---|---|---|---|
| `G1-01` | `10.1145/3035918.3064015` | 302 / `https://dl.acm.org/doi/10.1145/3035918.3064015` | Cicada + Dependably Fast Multi-Core In-Memory Transactions | Lim, Kaminsky, Andersen | Proceedings of the 2017 ACM International Conference on Management of Data / 2017-5-9 / proceedings-article / 21-35 | 固定 |
| `G2-01` | `10.1214/aoms/1177729586` | 302 / `http://projecteuclid.org/euclid.aoms/1177729586` | A Stochastic Approximation Method | Robbins, Monro | The Annals of Mathematical Statistics / 1951-9 / journal-article / 400-407 | 固定 |
| `G2-02` | `10.1214/aoms/1177729392` | 302 / `http://projecteuclid.org/euclid.aoms/1177729392` | Stochastic Estimation of the Maximum of a Regression Function | Kiefer, Wolfowitz | The Annals of Mathematical Statistics / 1952-9 / journal-article / 462-466 | 固定 |
| `G2-03` | `10.1214/aoms/1177706705` | 302 / `http://projecteuclid.org/euclid.aoms/1177706705` | Accelerated Stochastic Approximation | Kesten | The Annals of Mathematical Statistics / 1958-3 / journal-article / 41-59 | 固定 |
| `G2-04` | `10.1109/9.119632` | 302 / `http://ieeexplore.ieee.org/document/119632/` | Multivariate stochastic approximation using a simultaneous perturbation gradient approximation | Spall | IEEE Transactions on Automatic Control / 1992-3 / journal-article / 332-341 | 固定 |
| `G2-05` | `10.1109/7.705889` | 302 / `http://ieeexplore.ieee.org/document/705889/` | Implementation of the simultaneous perturbation algorithm for stochastic optimization | Spall | IEEE Transactions on Aerospace and Electronic Systems / 1998-7 / journal-article / 817-823 | 固定 |
| `G2-06` | `10.1137/0803045` | 302 / `https://epubs.siam.org/doi/10.1137/0803045` | Accelerated Stochastic Approximation | Delyon, Juditsky | SIAM Journal on Optimization / 1993-11 / journal-article / 868-881 | 固定 |
| `G2-07` | `10.1007/s10107-012-0572-5` | 302 / `http://link.springer.com/10.1007/s10107-012-0572-5` | Sample size selection in optimization methods for machine learning | Byrd, Chin, Nocedal, Wu | Mathematical Programming / 2012-6-24 / journal-article / 127-155 | 固定 |
| `G2-08` | `10.1137/17M1154679` | 302 / `https://epubs.siam.org/doi/10.1137/17M1154679` | Adaptive Sampling Strategies for Stochastic Optimization | Bollapragada, Byrd, Nocedal | SIAM Journal on Optimization / 2018-1 / journal-article / 3312-3343 | 固定 |
| `G3-01` | `10.1145/872035.872048` | 302 / `https://dl.acm.org/doi/10.1145/872035.872048` | Software transactional memory for dynamic-sized data structures | Herlihy, Luchangco, Moir, Scherer | Proceedings of the twenty-second annual symposium on Principles of distributed computing / 2003-7-13 / proceedings-article / 92-101 | 固定 |
| `G3-02` | `10.1145/1073814.1073861` | 302 / `https://dl.acm.org/doi/10.1145/1073814.1073861` | Advanced contention management for dynamic software transactional memory | Scherer, Scott | Proceedings of the twenty-fourth annual ACM symposium on Principles of distributed computing / 2005-7-17 / proceedings-article / 240-248 | 固定 |
| `G3-03` | `10.1007/11561927_23` | 302 / `http://link.springer.com/10.1007/11561927_23` | Polymorphic Contention Management | Guerraoui, Herlihy, Pochon | Lecture Notes in Computer Science / 2005 / book-chapter / 303-323 | 固定 |
| `G3-04` | `10.1145/1073814.1073863` | 302 / `https://dl.acm.org/doi/10.1145/1073814.1073863` | Toward a theory of transactional contention managers | Guerraoui, Herlihy, Pochon | Proceedings of the twenty-fourth annual ACM symposium on Principles of distributed computing / 2005-7-17 / proceedings-article / 258-264 | 固定 |
| `G3-05` | `10.1145/1378533.1378564` | 302 / `https://dl.acm.org/doi/10.1145/1378533.1378564` | Adaptive transaction scheduling for transactional memory systems | Yoo, Lee | Proceedings of the twentieth annual symposium on Parallelism in algorithms and architectures / 2008-6-14 / proceedings-article / 169-178 | 固定 |
| `G3-06` | `10.1145/1504176.1504199` | 302 / `https://dl.acm.org/doi/10.1145/1504176.1504199` | A comprehensive strategy for contention management in software transactional memory | Spear, Dalessandro, Marathe, Scott | Proceedings of the 14th ACM SIGPLAN symposium on Principles and practice of parallel programming / 2009-2-14 / proceedings-article / 141-150 | 固定 |
| `G3-07` | `10.1145/1582716.1582725` | 302 / `https://dl.acm.org/doi/10.1145/1582716.1582725` | Preventing versus curing + avoiding conflicts in transactional memories | Dragojević, Guerraoui, Singh, Singh | Proceedings of the 28th ACM symposium on Principles of distributed computing / 2009-8-10 / proceedings-article / 7-16 | 固定 |

### 1.2 主キーの一覧 (alias record)

| anchor ID | slot | 主キー (DOI) | preprint (arXiv ID) | 名称 alias |
|---|---|---|---|---|
| `G1-01` | `G1-CICADA` | `10.1145/3035918.3064015` | なし | Cicada |
| `G2-01` | `G2-SA` | `10.1214/aoms/1177729586` | なし | — |
| `G2-02` | `G2-SA` | `10.1214/aoms/1177729392` | なし | — |
| `G2-03` | `G2-SA` | `10.1214/aoms/1177706705` | なし | — |
| `G2-04` | `G2-SA` | `10.1109/9.119632` | なし | SPSA |
| `G2-05` | `G2-SA` | `10.1109/7.705889` | なし | SPSA |
| `G2-06` | `G2-SA` | `10.1137/0803045` | なし | — |
| `G2-07` | `G2-SA` | `10.1007/s10107-012-0572-5` | なし | — |
| `G2-08` | `G2-SA` | `10.1137/17M1154679` | `1710.11258` (v1) | — |
| `G3-01` | `G3-STM` | `10.1145/872035.872048` | なし | DSTM |
| `G3-02` | `G3-STM` | `10.1145/1073814.1073861` | なし | Polka |
| `G3-03` | `G3-STM` | `10.1007/11561927_23` | なし | — |
| `G3-04` | `G3-STM` | `10.1145/1073814.1073863` | なし | — |
| `G3-05` | `G3-STM` | `10.1145/1378533.1378564` | なし | ATS |
| `G3-06` | `G3-STM` | `10.1145/1504176.1504199` | なし | — |
| `G3-07` | `G3-STM` | `10.1145/1582716.1582725` | なし | Shrink |

## 2. 索引別 ID lookup の結果 (点 1 の続き、1/2 §2.4)

1/2 §2.4 (a) の control 集合 (OpenAlex 16 / arXiv `G2-08` / DBLP 13) は変えていない。

- **OpenAlex:** 16 件とも request `works/https://doi.org/<DOI>?select=id,doi,title,publication_year,ids,authorships,referenced_works_count` が HTTP 200 で `id` を返し、`収録`。
  W-ID は表 B。`title` は 16 件とも Crossref の `title` (+`subtitle`) と一致し、`publication_year` は Crossref の `issued` の年と一致した。
- **arXiv:** member `G2-08` は `収録` (§1.1 手順 3 と同じ応答)。他 15 件は arXiv ID を持たないので request を出さず「鍵なし」。
- **DBLP:** **anchor 固有の request は 1 本も送っていない。** 1/2 §6 の共有 endpoint の環境 preflight (3 入口、UA と Accept 不問で anti-bot challenge) をもって
  `不達` とし、16 件すべての DBLP 欄にその旨を書いた。これは 16 件の個別応答ではない。
- **早期確認の位置づけ:** 上記は 1/2 §2.4 (d) の早期の収録確認であり、live preflight を代替しない。live preflight は 3 索引すべての member について
  ID lookup を再実施し、その時点の 3 値を実行記録に書く。本記録の時点では、**DBLP の 13 member が `不達` であるため、1/2 §2.4 (c) のとおり
  DBLP の走行と軸全体は開始できない状態にある** (member の `非収録` は 0 件)。
- 包含 control が無い (slot, 索引) の組: `G1` × arXiv、`G3` × arXiv、`G2-01`〜`G2-03` × DBLP (1/2 §2.4 (c)、§7)。

| anchor ID | OpenAlex request → HTTP | `id` (W-ID) | `title` / `publication_year` | 3 値 | arXiv request → 3 値 | DBLP |
|---|---|---|---|---|---|---|
| `G1-01` | `works/https://doi.org/10.1145/3035918.3064015` → 200 | `W2613970404` | Cicada / 2017 | 収録 | 鍵なし (arXiv ID を持たない、非 member) | 不達 (anchor 固有 request 未送信。共有 endpoint の環境 preflight が challenge) |
| `G2-01` | `works/https://doi.org/10.1214/aoms/1177729586` → 200 | `W1994616650` | A Stochastic Approximation Method / 1951 | 収録 | 鍵なし (arXiv ID を持たない、非 member) | 不達 (anchor 固有 request 未送信。共有 endpoint の環境 preflight が challenge) |
| `G2-02` | `works/https://doi.org/10.1214/aoms/1177729392` → 200 | `W2009797711` | Stochastic Estimation of the Maximum of a Regression Function / 1952 | 収録 | 鍵なし (arXiv ID を持たない、非 member) | 不達 (anchor 固有 request 未送信。共有 endpoint の環境 preflight が challenge) |
| `G2-03` | `works/https://doi.org/10.1214/aoms/1177706705` → 200 | `W1996235804` | Accelerated Stochastic Approximation / 1958 | 収録 | 鍵なし (arXiv ID を持たない、非 member) | 不達 (anchor 固有 request 未送信。共有 endpoint の環境 preflight が challenge) |
| `G2-04` | `works/https://doi.org/10.1109/9.119632` → 200 | `W2124289529` | Multivariate stochastic approximation using a simultaneous perturbation gradient approximation / 1992 | 収録 | 鍵なし (arXiv ID を持たない、非 member) | 不達 (anchor 固有 request 未送信。共有 endpoint の環境 preflight が challenge) |
| `G2-05` | `works/https://doi.org/10.1109/7.705889` → 200 | `W2128452997` | Implementation of the simultaneous perturbation algorithm for stochastic optimization / 1998 | 収録 | 鍵なし (arXiv ID を持たない、非 member) | 不達 (anchor 固有 request 未送信。共有 endpoint の環境 preflight が challenge) |
| `G2-06` | `works/https://doi.org/10.1137/0803045` → 200 | `W2065450730` | Accelerated Stochastic Approximation / 1993 | 収録 | 鍵なし (arXiv ID を持たない、非 member) | 不達 (anchor 固有 request 未送信。共有 endpoint の環境 preflight が challenge) |
| `G2-07` | `works/https://doi.org/10.1007/s10107-012-0572-5` → 200 | `W2061570747` | Sample size selection in optimization methods for machine learning / 2012 | 収録 | 鍵なし (arXiv ID を持たない、非 member) | 不達 (anchor 固有 request 未送信。共有 endpoint の環境 preflight が challenge) |
| `G2-08` | `works/https://doi.org/10.1137/17M1154679` → 200 | `W2766854590` | Adaptive Sampling Strategies for Stochastic Optimization / 2018 | 収録 | `id_list=1710.11258` → 200、entry 1、`http://arxiv.org/abs/1710.11258v1` → 収録 | 不達 (anchor 固有 request 未送信。共有 endpoint の環境 preflight が challenge) |
| `G3-01` | `works/https://doi.org/10.1145/872035.872048` → 200 | `W2105055683` | Software transactional memory for dynamic-sized data structures / 2003 | 収録 | 鍵なし (arXiv ID を持たない、非 member) | 不達 (anchor 固有 request 未送信。共有 endpoint の環境 preflight が challenge) |
| `G3-02` | `works/https://doi.org/10.1145/1073814.1073861` → 200 | `W1988800505` | Advanced contention management for dynamic software transactional memory / 2005 | 収録 | 鍵なし (arXiv ID を持たない、非 member) | 不達 (anchor 固有 request 未送信。共有 endpoint の環境 preflight が challenge) |
| `G3-03` | `works/https://doi.org/10.1007/11561927_23` → 200 | `W1759214032` | Polymorphic Contention Management / 2005 | 収録 | 鍵なし (arXiv ID を持たない、非 member) | 不達 (anchor 固有 request 未送信。共有 endpoint の環境 preflight が challenge) |
| `G3-04` | `works/https://doi.org/10.1145/1073814.1073863` → 200 | `W2106871513` | Toward a theory of transactional contention managers / 2005 | 収録 | 鍵なし (arXiv ID を持たない、非 member) | 不達 (anchor 固有 request 未送信。共有 endpoint の環境 preflight が challenge) |
| `G3-05` | `works/https://doi.org/10.1145/1378533.1378564` → 200 | `W2165791323` | Adaptive transaction scheduling for transactional memory systems / 2008 | 収録 | 鍵なし (arXiv ID を持たない、非 member) | 不達 (anchor 固有 request 未送信。共有 endpoint の環境 preflight が challenge) |
| `G3-06` | `works/https://doi.org/10.1145/1504176.1504199` → 200 | `W2122621236` | A comprehensive strategy for contention management in software transactional memory / 2009 | 収録 | 鍵なし (arXiv ID を持たない、非 member) | 不達 (anchor 固有 request 未送信。共有 endpoint の環境 preflight が challenge) |
| `G3-07` | `works/https://doi.org/10.1145/1582716.1582725` → 200 | `W2036987653` | Preventing versus curing / 2009 | 収録 | 鍵なし (arXiv ID を持たない、非 member) | 不達 (anchor 固有 request 未送信。共有 endpoint の環境 preflight が challenge) |

**1 回目の lookup との差:** OpenAlex の lookup は 2 回行った。1 回目 (`resolve/`) は `select` に `referenced_works_count` を含めない request で、
1/2 §2.4 の登録形と 1 field 違う。本文書の値は登録形どおりの 2 回目 (`resolve2/`) から取った。2 回で `id`・`title`・`publication_year`・
`authorships` は 16 件とも同一であった。1 回目の応答も生証拠として残す。

## 3. query catalog の seal (点 2)

- 生成器 `orchestrator/axis_b5_search/catalog.py` (blob `b850e7b96a5e638b6bc0d880a8cb9d91fbefce94`、Codex `role=author`) を親が
  `python3 -m orchestrator.axis_b5_search.catalog --output <path>` で実走し、tracked の
  `docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-search-catalog.json` (blob `4f85b3c261537150d78cc8f8cd503bf41e81c3e3`) と bytes が一致することを `cmp` で確かめた。
  `--verify` は正例で rc=0、末尾に 1 byte 足した複製で rc=1。
- **file bytes の SHA-256 = `7eb8385e35bd24edac8a227a72ba5bc6b568ca8bc7cac2c8250af8b4ea4c346f`** (`sha256sum` の値。seal 内部の別 digest は無い)。
- 自己検算 (親の抜き取り、生成物から直接): `queries` 1622 (arXiv 10 / OpenAlex 10 / DBLP 1602)、`controls` 14、`aux_venue_streams` 272、
  `blocks` 6 (12/19/10/21/13/10 = 85 語、互いに素)、`branches` 10。DBLP 1602 本の `request_template` に重複なし。
  `+` と `%2A` は出現しない。`B5-CTL-AND2023@dblp` の `request_template` と `first_page_url` は `B5-CTL-AND@dblp` と byte 同一。
- 部分登録 §3.3 の照合例 `B5-Q10@dblp/T01-O01` の `first_page_url` は
  `https://dblp.org/search/publ/api?q=transaction%20processing%20backoff%20time&format=json&h=100&f=0` で一致。
- 1/2 §3.4 の読み 1〜12 はすべて実装され、生成器の test (17 件、凍結文由来の独立 literal) と親の実走で確認した。
  読みの追加・変更は 0 件。
- 部分登録 §5.3 の registration preflight 全体 (parser・fixture・schema・実行器) は本 wave の範囲外のままである。

## 4. 補助探索 3 経路の確定 (点 3、1/2 §4 の形を anchor ごとに具体化)

起点は 16 anchor 全部 (1/2 §4)。OpenAlex の W-ID と、`authorships` の `author_position` が `first` / `last` の要素の `author.id` を表 C に写した。
**16 件とも `authorships` の先頭が `first`、末尾が `last` (単著 3 件は `first` のみ) で、1/2 §4 の `要裁定` 条件に当たるものは無い。**

- 後方引用 `B5-AUX-REF@openalex/<anchor ID>`: 16 本。request は `works/<W-ID>?select=id,referenced_works,referenced_works_count`。
- 前方引用 `B5-AUX-CITES@openalex/<anchor ID>`: 16 本。request は `works?filter=cites:<W-ID>,to_publication_date:2026-12-31&per-page=200&cursor={CUR}`。
- 著者 `B5-AUX-AUTH@openalex/<anchor ID>-first` / `-last`: 29 本 (単著 `G2-03` / `G2-04` / `G2-05` は `-first` のみ)。
  request は `works?filter=author.id:<A-ID>,to_publication_date:2026-12-31&per-page=200&cursor={CUR}`。
  **異なる A-ID は 24 件**で、5 件の A-ID (`A5066890566` = `G2-04`/`G2-05` の単著者、`A5066189979` = `G3-01` の最終著者と `G3-02` の第一著者、
  `A5079254515` = `G3-02`/`G3-06` の最終著者、`A5049321288` = `G3-03`/`G3-04` の第一著者、`A5015726068` = `G3-03`/`G3-04` の最終著者) が
  2 本の stream で同じ request bytes を持つ。部分登録 §4.1 の `B5-CTL-AND2023@dblp` と同じ扱いで、**同じ bytes は 1 回だけ取得し、
  両 stream ID がその 1 回の取得を参照する。**
- stream の総数は 16 + 16 + 29 = 61 本 (取得回数は著者の共有により 56 回)。
- 上限と採用 (前方引用 200、著者 100、全順序 = DOI または OpenAlex ID、同順位は W-ID) は 1/2 §4 のまま。

| anchor ID | W-ID | `authorships` の `author_position` 列 | 第一著者 A-ID | 最終著者 A-ID | 著者 stream |
|---|---|---|---|---|---|
| `G1-01` | `W2613970404` | first, middle, last | `A5050218314` | `A5085479490` | `-first` (`A5050218314`) と `-last` (`A5085479490`) の 2 本 |
| `G2-01` | `W1994616650` | first, last | `A5110883277` | `A5065560698` | `-first` (`A5110883277`) と `-last` (`A5065560698`) の 2 本 |
| `G2-02` | `W2009797711` | first, last | `A5110860590` | `A5049527866` | `-first` (`A5110860590`) と `-last` (`A5049527866`) の 2 本 |
| `G2-03` | `W1996235804` | first | `A5082829165` | `A5082829165` | `-first` の 1 本 (`A5082829165`)。単著のため最終著者 = 第一著者 |
| `G2-04` | `W2124289529` | first | `A5066890566` | `A5066890566` | `-first` の 1 本 (`A5066890566`)。単著のため最終著者 = 第一著者 |
| `G2-05` | `W2128452997` | first | `A5066890566` | `A5066890566` | `-first` の 1 本 (`A5066890566`)。単著のため最終著者 = 第一著者 |
| `G2-06` | `W2065450730` | first, last | `A5059841305` | `A5039659947` | `-first` (`A5059841305`) と `-last` (`A5039659947`) の 2 本 |
| `G2-07` | `W2061570747` | first, middle, middle, last | `A5110661221` | `A5032317649` | `-first` (`A5110661221`) と `-last` (`A5032317649`) の 2 本 |
| `G2-08` | `W2766854590` | first, middle, last | `A5083156016` | `A5081856145` | `-first` (`A5083156016`) と `-last` (`A5081856145`) の 2 本 |
| `G3-01` | `W2105055683` | first, middle, middle, last | `A5086347882` | `A5066189979` | `-first` (`A5086347882`) と `-last` (`A5066189979`) の 2 本 |
| `G3-02` | `W1988800505` | first, last | `A5066189979` | `A5079254515` | `-first` (`A5066189979`) と `-last` (`A5079254515`) の 2 本 |
| `G3-03` | `W1759214032` | first, middle, last | `A5049321288` | `A5015726068` | `-first` (`A5049321288`) と `-last` (`A5015726068`) の 2 本 |
| `G3-04` | `W2106871513` | first, middle, last | `A5049321288` | `A5015726068` | `-first` (`A5049321288`) と `-last` (`A5015726068`) の 2 本 |
| `G3-05` | `W2165791323` | first, last | `A5023107016` | `A5072539515` | `-first` (`A5023107016`) と `-last` (`A5072539515`) の 2 本 |
| `G3-06` | `W2122621236` | first, middle, middle, last | `A5017374713` | `A5079254515` | `-first` (`A5017374713`) と `-last` (`A5079254515`) の 2 本 |
| `G3-07` | `W2036987653` | first, middle, middle, last | `A5070096854` | `A5001418143` | `-first` (`A5070096854`) と `-last` (`A5001418143`) の 2 本 |

## 5. 生証拠の locator

request ごとの生応答 (`.body`) と meta (`.meta.json`: URL、method、HTTP status、全 response header、body の SHA-256、request 開始・完了時刻 UTC) を
`output/insights/2026-09-08_t2380-b5-closure/resolve2/` に置く。表 D はその body の SHA-256 と時刻である。1 回目の lookup (`resolve/`) と
非 anchor の応答形観測 (`probe/`) も同じ insight に置く。

| file | request | HTTP | body SHA-256 | started / finished (UTC) |
|---|---|---|---|---|
| `G1-01_doi_head.body` | `HEAD https://doi.org/10.1145/3035918.3064015` | 302 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 2026-09-07T22:56:30Z / 2026-09-07T22:56:30Z |
| `G1-01_crossref.body` | `GET https://api.crossref.org/works/10.1145%2F3035918.3064015` | 200 | `947c247df02d1c87d0203ceafb2f33893a2caac0f6b5c458433740a0fe2a2041` | 2026-09-07T22:56:32Z / 2026-09-07T22:56:32Z |
| `G1-01_openalex.body` | `GET https://api.openalex.org/works/https://doi.org/10.1145/3035918.3064015?select=id,doi,title,publication_year,ids,authorships,referenced_works_count` | 200 | `94766e548fe179fe0116ed32a6c6dc6b0023e77d4889ad315bb303c835189fc6` | 2026-09-07T22:56:34Z / 2026-09-07T22:56:34Z |
| `G2-01_doi_head.body` | `HEAD https://doi.org/10.1214/aoms/1177729586` | 302 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 2026-09-07T22:56:35Z / 2026-09-07T22:56:35Z |
| `G2-01_crossref.body` | `GET https://api.crossref.org/works/10.1214%2Faoms%2F1177729586` | 200 | `b9a1cd7be3ce96ae86593744dcb02c57a2a138cf7b04d2ce3d3ddd9873312427` | 2026-09-07T22:56:36Z / 2026-09-07T22:56:37Z |
| `G2-01_openalex.body` | `GET https://api.openalex.org/works/https://doi.org/10.1214/aoms/1177729586?select=id,doi,title,publication_year,ids,authorships,referenced_works_count` | 200 | `cd4b51a5ab1ef0d4cf3a3b57df36848b25408b84d09730f440d9c4eacd2f37cf` | 2026-09-07T22:56:38Z / 2026-09-07T22:56:39Z |
| `G2-02_doi_head.body` | `HEAD https://doi.org/10.1214/aoms/1177729392` | 302 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 2026-09-07T22:56:40Z / 2026-09-07T22:56:40Z |
| `G2-02_crossref.body` | `GET https://api.crossref.org/works/10.1214%2Faoms%2F1177729392` | 200 | `fe80da7a232980b44972d233f78c5de88bf1ccba4145257382bf1f2db2efef04` | 2026-09-07T22:56:41Z / 2026-09-07T22:56:42Z |
| `G2-02_openalex.body` | `GET https://api.openalex.org/works/https://doi.org/10.1214/aoms/1177729392?select=id,doi,title,publication_year,ids,authorships,referenced_works_count` | 200 | `a0d1dd10cd37c35bc5e013cdfe8411391f4afca6f543e77f22d16248201059ff` | 2026-09-07T22:56:43Z / 2026-09-07T22:56:44Z |
| `G2-03_doi_head.body` | `HEAD https://doi.org/10.1214/aoms/1177706705` | 302 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 2026-09-07T22:56:45Z / 2026-09-07T22:56:45Z |
| `G2-03_crossref.body` | `GET https://api.crossref.org/works/10.1214%2Faoms%2F1177706705` | 200 | `7cd0f21d7f4bf98757d015dc3dba3d8f5ed542609830d7eaf9b80487cf65a37a` | 2026-09-07T22:56:46Z / 2026-09-07T22:56:47Z |
| `G2-03_openalex.body` | `GET https://api.openalex.org/works/https://doi.org/10.1214/aoms/1177706705?select=id,doi,title,publication_year,ids,authorships,referenced_works_count` | 200 | `943c1bffb7d844b868136ae3703751c4669c122b4c6558f2226ba1df20159f3d` | 2026-09-07T22:56:48Z / 2026-09-07T22:56:48Z |
| `G2-04_doi_head.body` | `HEAD https://doi.org/10.1109/9.119632` | 302 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 2026-09-07T22:56:50Z / 2026-09-07T22:56:50Z |
| `G2-04_crossref.body` | `GET https://api.crossref.org/works/10.1109%2F9.119632` | 200 | `efdfc80f3123a77cf5df8ba541b86cd369f2afa26148ca14d5c5b20c0c0c2389` | 2026-09-07T22:56:51Z / 2026-09-07T22:56:51Z |
| `G2-04_openalex.body` | `GET https://api.openalex.org/works/https://doi.org/10.1109/9.119632?select=id,doi,title,publication_year,ids,authorships,referenced_works_count` | 200 | `7bf2c9fbd39327b067c0f981665df874f5f768bd8d1caebb366063ef1322bee1` | 2026-09-07T22:56:53Z / 2026-09-07T22:56:53Z |
| `G2-05_doi_head.body` | `HEAD https://doi.org/10.1109/7.705889` | 302 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 2026-09-07T22:56:54Z / 2026-09-07T22:56:54Z |
| `G2-05_crossref.body` | `GET https://api.crossref.org/works/10.1109%2F7.705889` | 200 | `f6a34b4fe56b9c1b3d0cdbaaa20ebacaa30a2c8b604af3bc991a6c5eb55703d2` | 2026-09-07T22:56:56Z / 2026-09-07T22:56:56Z |
| `G2-05_openalex.body` | `GET https://api.openalex.org/works/https://doi.org/10.1109/7.705889?select=id,doi,title,publication_year,ids,authorships,referenced_works_count` | 200 | `9cb13ef50cc76d44a937ff0bd4b5e834b1988593474097e3078530f24063edb5` | 2026-09-07T22:56:57Z / 2026-09-07T22:56:58Z |
| `G2-06_doi_head.body` | `HEAD https://doi.org/10.1137/0803045` | 302 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 2026-09-07T22:56:59Z / 2026-09-07T22:56:59Z |
| `G2-06_crossref.body` | `GET https://api.crossref.org/works/10.1137%2F0803045` | 200 | `412d9976c3f77e9ed2b9ee383c07e323172f73506ef8d59677c1a73d868a9126` | 2026-09-07T22:57:00Z / 2026-09-07T22:57:01Z |
| `G2-06_openalex.body` | `GET https://api.openalex.org/works/https://doi.org/10.1137/0803045?select=id,doi,title,publication_year,ids,authorships,referenced_works_count` | 200 | `6b2ba99897c22569659746ee4717d498ba04bcb62619cbc68686a362ab21909b` | 2026-09-07T22:57:02Z / 2026-09-07T22:57:02Z |
| `G2-07_doi_head.body` | `HEAD https://doi.org/10.1007/s10107-012-0572-5` | 302 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 2026-09-07T22:57:03Z / 2026-09-07T22:57:03Z |
| `G2-07_crossref.body` | `GET https://api.crossref.org/works/10.1007%2Fs10107-012-0572-5` | 200 | `c1ec938a8eed7ff4ff20bbf04345c4e7a0dc1e10936abe4316d56c040211c1fb` | 2026-09-07T22:57:05Z / 2026-09-07T22:57:05Z |
| `G2-07_openalex.body` | `GET https://api.openalex.org/works/https://doi.org/10.1007/s10107-012-0572-5?select=id,doi,title,publication_year,ids,authorships,referenced_works_count` | 200 | `a40f72bca7a5c0843cdfdf191df7dd9328a8e3e7829749f2388af8fef7777f8d` | 2026-09-07T22:57:06Z / 2026-09-07T22:57:06Z |
| `G2-08_doi_head.body` | `HEAD https://doi.org/10.1137/17M1154679` | 302 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 2026-09-07T22:57:08Z / 2026-09-07T22:57:08Z |
| `G2-08_crossref.body` | `GET https://api.crossref.org/works/10.1137%2F17M1154679` | 200 | `7894d18f4621f3229e14b6687d25e6ac63bcea0f4f204500d7e3a75c66d4744c` | 2026-09-07T22:57:09Z / 2026-09-07T22:57:09Z |
| `G2-08_openalex.body` | `GET https://api.openalex.org/works/https://doi.org/10.1137/17M1154679?select=id,doi,title,publication_year,ids,authorships,referenced_works_count` | 200 | `f8b409ba27c50900b635f7e91317008d94ee18c6f9282a66a105a3365399e034` | 2026-09-07T22:57:12Z / 2026-09-07T22:57:12Z |
| `G2-08_arxiv.body` | `GET https://export.arxiv.org/api/query?id_list=1710.11258&max_results=1` | 200 | `14e3f87eb4601e214caca11182339be68c322d8f89578c437f0a51a33618d0a4` | 2026-09-07T22:57:11Z / 2026-09-07T22:57:11Z |
| `G3-01_doi_head.body` | `HEAD https://doi.org/10.1145/872035.872048` | 302 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 2026-09-07T22:57:13Z / 2026-09-07T22:57:13Z |
| `G3-01_crossref.body` | `GET https://api.crossref.org/works/10.1145%2F872035.872048` | 200 | `fab40b704e2cc8ed17e2554c126b4447c07a8045815a651a34c559b6fea62ef8` | 2026-09-07T22:57:15Z / 2026-09-07T22:57:15Z |
| `G3-01_openalex.body` | `GET https://api.openalex.org/works/https://doi.org/10.1145/872035.872048?select=id,doi,title,publication_year,ids,authorships,referenced_works_count` | 200 | `2b9f8d28a68ee4e7514691fcd5cebda20c0739241d0767be86e3be9327eac07b` | 2026-09-07T22:57:16Z / 2026-09-07T22:57:17Z |
| `G3-02_doi_head.body` | `HEAD https://doi.org/10.1145/1073814.1073861` | 302 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 2026-09-07T22:57:18Z / 2026-09-07T22:57:18Z |
| `G3-02_crossref.body` | `GET https://api.crossref.org/works/10.1145%2F1073814.1073861` | 200 | `d06b46f4a1c8f83afe44096deb6b3c64beb0b380f28927d985bed5a4f6c7a7e2` | 2026-09-07T22:57:19Z / 2026-09-07T22:57:20Z |
| `G3-02_openalex.body` | `GET https://api.openalex.org/works/https://doi.org/10.1145/1073814.1073861?select=id,doi,title,publication_year,ids,authorships,referenced_works_count` | 200 | `aee3c7d42349fef0ff25f02e47f42fd49bc732690f5091135387792fd64dcf25` | 2026-09-07T22:57:21Z / 2026-09-07T22:57:21Z |
| `G3-03_doi_head.body` | `HEAD https://doi.org/10.1007/11561927_23` | 302 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 2026-09-07T22:57:22Z / 2026-09-07T22:57:22Z |
| `G3-03_crossref.body` | `GET https://api.crossref.org/works/10.1007%2F11561927_23` | 200 | `67299a1a57c459281077aa5bd2f3f8c162bb0fdf847bddfa6a13115c0272a0c7` | 2026-09-07T22:57:24Z / 2026-09-07T22:57:24Z |
| `G3-03_openalex.body` | `GET https://api.openalex.org/works/https://doi.org/10.1007/11561927_23?select=id,doi,title,publication_year,ids,authorships,referenced_works_count` | 200 | `1a3d037c0b7446eb9ed9050d7daedf833737398501979b5adcb2c89e9e6c677b` | 2026-09-07T22:57:25Z / 2026-09-07T22:57:26Z |
| `G3-04_doi_head.body` | `HEAD https://doi.org/10.1145/1073814.1073863` | 302 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 2026-09-07T22:57:27Z / 2026-09-07T22:57:27Z |
| `G3-04_crossref.body` | `GET https://api.crossref.org/works/10.1145%2F1073814.1073863` | 200 | `99a8fc9456d3a0287b1e89f9b462087f2a61849b56eff245d1abceaaebc01abb` | 2026-09-07T22:57:28Z / 2026-09-07T22:57:29Z |
| `G3-04_openalex.body` | `GET https://api.openalex.org/works/https://doi.org/10.1145/1073814.1073863?select=id,doi,title,publication_year,ids,authorships,referenced_works_count` | 200 | `0b83218d44d55d01bea5519652c376d8c70161014354679014b140e4df5f2453` | 2026-09-07T22:57:30Z / 2026-09-07T22:57:30Z |
| `G3-05_doi_head.body` | `HEAD https://doi.org/10.1145/1378533.1378564` | 302 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 2026-09-07T22:57:31Z / 2026-09-07T22:57:31Z |
| `G3-05_crossref.body` | `GET https://api.crossref.org/works/10.1145%2F1378533.1378564` | 200 | `071776537dda8ef14c7f60ab241c8e439de006ea8260f48b77d7fe0fdfe4bd23` | 2026-09-07T22:57:33Z / 2026-09-07T22:57:33Z |
| `G3-05_openalex.body` | `GET https://api.openalex.org/works/https://doi.org/10.1145/1378533.1378564?select=id,doi,title,publication_year,ids,authorships,referenced_works_count` | 200 | `a29f485b81247de5af152f76b5747048e8936a843ecf5b077d5a780565d9f6f3` | 2026-09-07T22:57:34Z / 2026-09-07T22:57:35Z |
| `G3-06_doi_head.body` | `HEAD https://doi.org/10.1145/1504176.1504199` | 302 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 2026-09-07T22:57:36Z / 2026-09-07T22:57:36Z |
| `G3-06_crossref.body` | `GET https://api.crossref.org/works/10.1145%2F1504176.1504199` | 200 | `f2e84714ba5d8370da7465bbef9f0a91fd1b2cc15ca62d6f60ef1002140ca9aa` | 2026-09-07T22:57:37Z / 2026-09-07T22:57:38Z |
| `G3-06_openalex.body` | `GET https://api.openalex.org/works/https://doi.org/10.1145/1504176.1504199?select=id,doi,title,publication_year,ids,authorships,referenced_works_count` | 200 | `0b564b6b729daf11b53db4f384e8afb335ae1aec5c9c3d43f83b1c1a67270be7` | 2026-09-07T22:57:39Z / 2026-09-07T22:57:39Z |
| `G3-07_doi_head.body` | `HEAD https://doi.org/10.1145/1582716.1582725` | 302 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 2026-09-07T22:57:40Z / 2026-09-07T22:57:40Z |
| `G3-07_crossref.body` | `GET https://api.crossref.org/works/10.1145%2F1582716.1582725` | 200 | `82caabc944bfed10435cfe08a9aaf6a6e5efffc0435bb8500c135d34ebfd5a79` | 2026-09-07T22:57:41Z / 2026-09-07T22:57:42Z |
| `G3-07_openalex.body` | `GET https://api.openalex.org/works/https://doi.org/10.1145/1582716.1582725?select=id,doi,title,publication_year,ids,authorships,referenced_works_count` | 200 | `70d16cbfbc3aed576288c1ff7ba44d4838f7c1e50bb74e8bcb48df8f526bbf84` | 2026-09-07T22:57:43Z / 2026-09-07T22:57:43Z |

## 6. 実行していないこと、限界

- **軸 B5 の検索は 1 本も実行していない。** 件数・応答・候補判定は 1 つも無い。
- **DBLP の anchor 固有 lookup は未実施**であり、DBLP 欄の `不達` は共有 endpoint の環境 preflight からの外挿である。
- OpenAlex / arXiv の `収録` は 2026-09-07 22:50〜23:10 UTC の観測であり、live preflight の時点の状態を保証しない。
- 主キーの一致判定は Crossref record と手掛かりの照合であり、本文は読んでいない (A/B/C/D の判定は未実施、判定語彙は `要裁定` のまま)。
- 1/2 §2.2 の「届くと想定する枝と語」と、`G2` の包含 control が不発になる見込み (1/2 §7) は本文書でも変わらない。
- 著者 stream の A-ID は OpenAlex の著者同定に依存する。同定の誤りは本文書では検出できない。
- registration preflight (実行器の bytes の束縛) と live preflight と人間の実行認可が残る (§0)。
