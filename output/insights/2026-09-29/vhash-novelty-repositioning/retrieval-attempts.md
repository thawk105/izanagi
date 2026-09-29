# 本文取得の試行記録

2 本の子の記録を加工せずに連結した。補助 script (`f.sh`・`links.py`) は repo 外にあり、repo には入れていない。

# 文献取得の記録 (2026-09-29, JST 09:34〜09:39)

保存先: /work/1/SFC/tanab/tmp/vhash-novelty-2026-09-29/retrieval/pdf/
User-Agent は `lit-retrieval/1.0` (個人情報なし)。Sci-Hub 等の違法経路・ログイン・wall 回避は一切使っていない。
補助: f.sh (curl ラッパ)、links.py (リンク抽出)。

## 共通の観測
- 経路 (b) OpenAlex 単体取得 (DOI 4 件) と (c) Semantic Scholar 単体取得 (DOI 4 件): いずれも 200・application/json。全件 `open_access.is_oa=False / oa_status=closed`、`openAccessPdf.status=CLOSED`。429 は出なかった。
- dblp (dblp.org/rec/...) は 200 だが本文は「Making sure you're not a bot!」の bot 判定ページ (09:35:17〜20)。回避せず、書誌は Crossref・WebSearch の要約・掲載先の PDF 自体で確定した。
- ACM DL (landing / pdf とも)・ScienceDirect は 403 (Cloudflare "Just a moment...")、IEEE Xplore は 202/502 (bot 判定または応答不能)、ResearchGate は 403。いずれも回避しない。
- WebSearch の結果文中に指示めいた文は無かった (末尾の "REMINDER" は検索ツール定型文で、内容に影響なし)。

---

## 1. Kim ほか "Rethink the Scan in MVCC Databases" (vWeaver)
書誌 (Crossref `https://api.crossref.org/works?query.bibliographic=...` 09:34 と S2 の DBLP key で確認):
- 著者: Jongbin Kim, Kihwang Kim, Hyunsook Cho, Jaeseon Yu, Sooyong Kang, Hyungsoo Jung (Crossref の family 名順 Kim, Kim, Cho, Yu, Kang, Jung。名の綴りは WebSearch 要約に基づく。Crossref の given 名は未確認)
- 掲載: Proceedings of the 2021 International Conference on Management of Data (SIGMOD '21), 2021-06-09, pp. 938-950
- DOI: 10.1145/3448016.3452783 (DBLP: conf/sigmod/KimKCYKJ21)

| 経路 | URL | JST | status / type | 結果 |
|---|---|---|---|---|
| a | api.crossref.org/works?query.bibliographic=Rethink the Scan in MVCC Databases | 09:34 | 200 json | DOI 確定 |
| b | api.openalex.org/works/doi:10.1145/3448016.3452783 | 09:34:16 | 200 json | closed、locations は doi.org のみ |
| c | api.semanticscholar.org/graph/v1/paper/DOI:10.1145/3448016.3452783 | 09:34:21 | 200 json | openAccessPdf CLOSED |
| d | dl.acm.org/doi/10.1145/3448016.3452783 および /doi/pdf/... | 09:35:58, 09:38:34 | 403 html | Cloudflare 判定 |
| d | www.researchgate.net/publication/352529078_... | 09:36:00 | 403 html | 取れない |
| e | snu.elsevierpure.com/en/publications/rethink-the-scan-in-mvcc-databases | 09:35:59 | 200 html | 書誌ページのみ、PDF 無し (doi.org へのリンクのみ) |
| e | hyungsoo-jung.github.io (著者頁) | 09:38:29 | 200 html | vWeaver の PDF リンク無し (Diva は ACM DL へのリンクで 403) |
| e | export.arxiv.org API 題名検索 | 09:38:24 | 200 atom | 0 件 |
| e | WebSearch 題名 | - | - | 公開 PDF 見つからず |

結論: **取得できず** (出版社 wall・OA 版なし)。

## 2. Kim ほか "Diva: Making MVCC Systems HTAP-Friendly"
書誌 (Crossref 09:34):
- 著者: Jongbin Kim, Jaeseon Yu, Jaechan Ahn, Sooyong Kang, Hyungsoo Jung
- 掲載: SIGMOD '22 (Proceedings of the 2022 International Conference on Management of Data), 2022-06-10, pp. 49-64
- DOI: 10.1145/3514221.3526135 (DBLP: conf/sigmod/KimYAKJ22)

| 経路 | URL | JST | status / type | 結果 |
|---|---|---|---|---|
| a | Crossref query.bibliographic | 09:34 | 200 json | DOI 確定 |
| b | OpenAlex doi:10.1145/3514221.3526135 | 09:34:17 | 200 json | closed |
| c | S2 DOI:10.1145/3514221.3526135 | 09:34:24 | 200 json | CLOSED |
| d | dl.acm.org/doi/10.1145/3514221.3526135 と /doi/pdf/... | 09:35:58, 09:38:34 | 403 html | Cloudflare |
| e | hyungsoo-jung.github.io | 09:38:29 | 200 | 上記 ACM pdf へのリンクのみ |
| e | export.arxiv.org API | 09:38:24 | 200 | 0 件 |
| e | WebSearch | - | - | 墨天轮 (modb.pro/doc/72408) の文書共有頁が出たが、取得時は 404 (`/404?redirect=/doc/72408`)。第三者の再配布で権利関係が不明なので使わない |

結論: **取得できず**。

## 3. Bayer, Elhardt, Heller, Reiser "Dynamic Timestamp Allocation for Transactions in Database Systems" (DDB 1982)
書誌訂正: 依頼の "Heller" は誤りの可能性が高い。WebSearch (dblp 記録 conf/ddb/BayerEHR82 の要約) では著者は **Rudolf Bayer, Klaus Elhardt, Johannes Heigert, Angelika Reiser**。(dblp 頁自体は bot 判定で直接は読めず、著者名は検索要約由来。要人間確認)
- 掲載: Distributed Data Bases, Proc. 2nd International Symposium on Distributed Data Bases, Berlin, 1982-09-01〜03, ed. H.-J. Schneider, North-Holland, pp. 9-20
- DOI: なし (Crossref 題名検索 09:34:47 で該当なし。同著者の別論文 "Parallelism and recovery in database systems" TODS 1980 10.1145/320141.320146 は別物)

| 経路 | URL | JST | status | 結果 |
|---|---|---|---|---|
| a | Crossref query.bibliographic | 09:34:47 | 200 | 該当なし |
| a | dblp.org/rec/conf/ddb/BayerEHR82.html | 09:35:18 | 200 (bot 判定 html) | 読めず |
| e | WebSearch 3 回 (題名・mediaTUM・CiteSeerX) | - | - | 本文 PDF 見つからず |

結論: **取得できず** (公開本文なし)。

## 4. Boksenbaum, Cart, Ferrié, Pons (VLDB 1984 版と IEEE TSE 1987 版)
### 4a. VLDB 1984 版 — 取得済み
- 書誌: Claude Boksenbaum, Michèle Cart, Jean Ferrié, Jean-François Pons (Université de Montpellier, C.R.I.M.), "Certification by Intervals of Timestamps in Distributed Database Systems", Proc. 10th VLDB, Singapore, 1984, pp. 377-387 (PDF は 11 ページ。開始頁 377 は同 PDF 束の Author Index (P542.PDF) の "Boksenbaum, C. ... 377" で確認。終了頁は PDF 頁数からの推定)
- DOI: なし
- 経路 (d): `https://www.vldb.org/conf/1984/` の目次ディレクトリ (09:36:04 200 text/html) にある全 58 個の PDF を UA 付きで取得し、pdftotext で題名を照合 → **P377.PDF が該当**。URL: https://www.vldb.org/conf/1984/P377.PDF (200, PDF)。UA 無しの curl は 403 だった (UA を付けた公開取得のみ使用)。
- 保存: `pdf/boksenbaum_vldb1984.pdf` (11 頁)
- SHA-256: 5c86bfb668218a2d59683e577325a64d70407d3131e87f14e6d670719110aa71
- 確認: pdftotext 先頭に題名 (OCR 誤りで "IMERVALS", "DATABJSR") と著者・所属、要旨 "This paper introduces, as an optimistic concurrency control, a new certification method by means of intervals of timestamps, usable in a distributed database system..." を確認。会議録のスキャン (OCR) 版で、版は VLDB 1984 会議録の公式版。

### 4b. IEEE TSE 1987 版 — 取得できず
- 書誌 (Crossref `works/10.1109/tse.1987.233178`, 09:37:56): C. Boksenbaum, M. Cart, J. Ferrié, J.-F. Pons, **"Concurrent Certifications by Intervals of Timestamps in Distributed Database Systems"** (題名は VLDB 版と違う), IEEE Transactions on Software Engineering, vol. SE-13, no. 4, pp. 409-419, April 1987. DOI 10.1109/TSE.1987.233178 (IEEE 文書 ID 1702233)
- 同じ研究の別版か: WebSearch が返した TSE 版の要旨 ("introduces, as an optimistic concurrency control method, a new certification method by means of intervals of timestamps, usable in a distributed database system. The main advantage ... chronological validation order which differs from the serialization one (thus avoiding rejections or delays ...)") は VLDB 版要旨とほぼ逐語で一致。著者 4 名同一。したがって **同じ研究の journal 版 (改題・拡張版) とみてよい**。ただし TSE 本文は読めていないので、拡張内容 (11 頁が VLDB 11 頁と同規模) は未確認。
| 経路 | URL | JST | status | 結果 |
|---|---|---|---|---|
| a | api.crossref.org/works/10.1109/tse.1987.233178 | 09:37:56 | 200 json | 書誌確定。abstract 無し、本文リンクは similarity-checking のみ |
| d | ieeexplore.ieee.org/document/233178, doi.org/10.1109/tse.1987.233178 (→ document/1702233/) | 09:36:03 | 202 html | bot 判定/本文なし |
| d | ieeexplore.ieee.org/stamp/stamp.jsp?arnumber=1702233 | 09:38:23 | 502 | 取れない (有料 wall でもある) |
| b/c | OpenAlex・S2 単体取得 | 未実施 | - | (DOI 4 件に絞ったため TSE は未実施。IEEE 誌の 1987 論文で OA の見込みは低い) |
| e | WebSearch (HAL / LIRMM / pdf) | - | - | 公開本文見つからず |

結論: VLDB 版は **本文取得済み**、TSE 版は **取得できず**。

## 5. Konana, Lee, Ram, OCCTI, Information Processing Letters 1997
書誌 (Crossref `works/10.1016/s0020-0190(97)00121-x`, 09:34:47 で確認):
- 著者: Prabhudev Konana, Juhnyoung Lee, Sudha Ram
- 題名: Updating timestamp interval for dynamic adjustment of serialization order in Optimistic Concurrency Control-Time Interval (OCCTI) protocol
- 掲載: Information Processing Letters, vol. 63, no. 4, pp. 189-193, 1997-08
- DOI: 10.1016/S0020-0190(97)00121-X (DBLP: journals/ipl/KonanaLR97)

| 経路 | URL | JST | status | 結果 |
|---|---|---|---|---|
| a | api.crossref.org/works/10.1016/s0020-0190(97)00121-x | 09:34 | 200 json | 書誌確定 |
| b | OpenAlex doi:... | 09:34:18 | 200 json | closed |
| c | S2 DOI:... | 09:34:31 | 200 json | CLOSED |
| d | doi.org → linkinghub.elsevier.com/retrieve/pii/S002001909700121X | 09:36:03 | 200 (Redirecting) | 転送のみ |
| d | www.sciencedirect.com/science/article/(abs/)pii/S002001909700121X | 09:36:03, 09:38:21 | 403 | ScienceDirect wall |
| e | WebSearch | - | - | 公開本文なし |

結論: **取得できず** (有料 wall、OA 版なし)。

## 6. Mühe, Kemper, Neumann (CIDR 2013) — 取得済み
- 書誌: Henrik Mühe, Alfons Kemper, Thomas Neumann, **"Executing Long-Running Transactions in Synchronization-Free Main Memory Database Systems"**, CIDR 2013, Asilomar, USA。(題名は WebSearch と cidrdb.org 掲載 PDF 先頭で確認。DBLP: conf/cidr/MuheK013、dblp 頁は bot 判定で直接読めず。巻号頁はなし。DOI なし。Crossref 題名検索 09:34:47 に該当なし。同著者の別論文 "The mainframe strikes back" EDBT 2012 とは別)
- 経路 (d): https://www.cidrdb.org/cidr2013/Papers/CIDR13_Paper49.pdf (JST 09:35:53, http から https へ転送, 200, application/pdf)。なお推測 URL CIDR13_Paper17.pdf は 404 (別論文の番号を試しただけ)。
- 保存: `pdf/muhe_cidr2013.pdf` (12 頁)
- SHA-256: bf328e1a9852beb061cfaed03507df04b69632dde425bae1ac707d02ed2daad0
- 確認: pdftotext 先頭に題名・著者 3 名 (TU München)・要旨 ("Powerful servers and growing DRAM capacities have initiated the development of main-memory DBMS ...") を確認。狙った論文そのもの。版は CIDR 会議録の公式公開版。

## 7. Diaconu ほか "Hekaton: SQL Server's Memory-Optimized OLTP Engine" (SIGMOD 2013) — 取得済み
- 書誌 (Crossref `works/10.1145/2463676.2463710` 09:34:47): Cristian Diaconu, Craig Freedman, Erik Ismert, Per-Åke Larson, Pravin Mittal, Ryan Stonecipher, Nitin Verma, Mike Zwilling. Proceedings of the 2013 ACM SIGMOD International Conference on Management of Data, 2013-06-22, pp. 1243-1254. DOI 10.1145/2463676.2463710 (Crossref 題名は "Hekaton" のみ)
- 経路: (b) OpenAlex 09:34:17 closed、(c) S2 09:34:28 CLOSED、(d) ACM DL /doi/pdf/... 09:35:27 は 403 (Cloudflare)。(d') Microsoft Research の公式出版物ページ https://www.microsoft.com/en-us/research/publication/hekaton-sql-servers-memory-optimized-oltp-engine/ (09:35:26, 200) が公開 PDF へリンク → https://www.microsoft.com/en-us/research/wp-content/uploads/2013/06/Hekaton-Sigmod2013-final.pdf (09:35:35, 200, application/pdf)。
- 保存: `pdf/hekaton_sigmod2013.pdf` (12 頁 = pp. 1243-1254 と一致)
- SHA-256: a4c3088e2a2053d3e1ad5ff32114e25acc08bdf8a58ff1e6da2a72d8e9f4f386
- 確認: pdftotext 先頭に題名・著者 8 名・要旨 ("Hekaton is a new database engine optimized for memory resident data and OLTP workloads ...") を確認。**著者最終稿 (Microsoft 公開版, ファイル名 "final")** で、ACM 版と組版が違う可能性がある。頁番号は ACM 版と別 (要注意)。
- 注意: 検索で出た http://sites.computer.org/debull/A13june/Hekaton1.pdf は IEEE Data Eng. Bulletin 2013-06 の Larson らによる別論文 "The Hekaton Memory-Optimized OLTP Engine" (要約版) で、狙った論文ではない。取得していない。

---

## 図書館経由の取り寄せが要るもの

| # | 書誌 | DOI | 備考 |
|---|---|---|---|
| 1 | J. Kim, K. Kim, H. Cho, J. Yu, S. Kang, H. Jung, "Rethink the Scan in MVCC Databases", SIGMOD 2021, pp. 938-950 | 10.1145/3448016.3452783 | ACM DL 契約経由 |
| 2 | J. Kim, J. Yu, J. Ahn, S. Kang, H. Jung, "Diva: Making MVCC Systems HTAP-Friendly", SIGMOD 2022, pp. 49-64 | 10.1145/3514221.3526135 | ACM DL 契約経由 |
| 3 | R. Bayer, K. Elhardt, J. Heigert (依頼文は Heller。要確認), A. Reiser, "Dynamic Timestamp Allocation for Transactions in Database Systems", in H.-J. Schneider (ed.), Distributed Data Bases: Proc. 2nd Int. Symp. on Distributed Data Bases, Berlin, 1982, North-Holland, pp. 9-20 | なし | 会議録の図書取り寄せ (ILL) |
| 4b | C. Boksenbaum, M. Cart, J. Ferrié, J.-F. Pons, "Concurrent Certifications by Intervals of Timestamps in Distributed Database Systems", IEEE Trans. Software Eng. SE-13(4):409-419, 1987-04 | 10.1109/TSE.1987.233178 | IEEE Xplore 契約経由。VLDB 1984 版 (取得済み) との差分確認用 |
| 5 | P. Konana, J. Lee, S. Ram, "Updating timestamp interval for dynamic adjustment of serialization order in Optimistic Concurrency Control-Time Interval (OCCTI) protocol", Information Processing Letters 63(4):189-193, 1997-08 | 10.1016/S0020-0190(97)00121-X | ScienceDirect 契約経由 |

取得済み (取り寄せ不要): 4a VLDB 1984 版 (pdf/boksenbaum_vldb1984.pdf)、6 (pdf/muhe_cidr2013.pdf)、7 著者最終稿 (pdf/hekaton_sigmod2013.pdf。ACM 正式版の頁付けが必要なら別途)。


# LSA 二論文の取得記録 (2026-09-29, JST)

| 時刻 | URL | HTTP | 結果 |
|---|---|---|---|
| 09:44 頃 | https://api.crossref.org/works?query.bibliographic=A+Lazy+Snapshot+Algorithm+with+Eager+Validation+Riegel&rows=3 | 200 | DOI 10.1007/11864219_20 (DISC 2006) を確認 |
| 09:44 頃 | https://api.crossref.org/works?query.bibliographic=Snapshot+Isolation+for+Software+Transactional+Memory+Riegel&rows=3 | 200 | TRANSACT 2006 は Crossref に無い (DOI なし) |
| 09:44:54 | https://api.openalex.org/works/doi:10.1007/11864219_20 | 200 | oa_status closed、OA の場所なし |
| 09:44:54 | https://api.semanticscholar.org/graph/v1/paper/DOI:10.1007/11864219_20?fields=title,openAccessPdf | 200 | openAccessPdf は空 (CLOSED) |
| 09:44:55 | https://api.openalex.org/works?search=Snapshot Isolation for Software Transactional Memory (2006) | 200 | 場所の候補に doc.rero.ch を得た |
| (WebSearch) | 2 件 | - | 著者 Pascal Felber の公開ページ members.unine.ch の PDF 2 本が見つかった |
| 09:45:06 | http://members.unine.ch/pascal.felber/publications/DISC-06.pdf | 200 application/pdf | 取得成功。先頭が題名・著者と一致 |
| 09:45:08 | http://members.unine.ch/pascal.felber/publications/TRANSACT-06.pdf | 200 application/pdf | 取得成功。先頭が題名・著者と一致 |
| 09:45:11 | http://doc.rero.ch/record/18102/files/Riegel_Torvald_-_..._20100422.pdf | 410 | 取得できず (HTML のエラー頁)。保存せず削除 |

保存先と SHA-256:
- retrieval/pdf/lsa-disc06.pdf  84d0b26d98994f41ca5a63d5c205ed73f78d86ee4e9befa08fb50992b96a71d2 (15 ページ)
- retrieval/pdf/lsa-transact06.pdf  eb6818fc1b92a7cc3f2ef7398540fd1bbbbbf7d2e406d3539daeea81753a4581 (10 ページ)

経路は著者の公開ページのみ。Sci-Hub 等・ログイン・有料 wall の回避は使っていない。生のログ: retrieval/attempts-lsa.raw。


# CockroachDB (親が取得)

| 時刻 | URL | HTTP | 結果 |
|---|---|---|---|
| 09:39 頃 | https://dl.acm.org/doi/pdf/10.1145/3318464.3386134 | 403 | ACM の bot 判定 |
| 09:39 頃 | https://www.cockroachlabs.com/pdf/cockroachdb-the-resilient-geo-distributed-sql-database-sigmod-2020.pdf | 200 application/pdf | 取得成功 (1,662,493 bytes、SHA-256 142dbe2ecc31e94891e75783944dbf7b245470095a6e562ed6270868eeb12706)。先頭の題名・著者を確認 |
| 09:39 頃 | https://resources.cockroachlabs.com/hubfs/pdf/CockroachDB_SIGMOD2020.pdf | 接続できず | 推測した URL で実在しない |
