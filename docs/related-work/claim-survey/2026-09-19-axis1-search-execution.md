# 2026-09-19 — 軸 1 検索の実行記録 — 新 epoch `AX1-20260902-E1` の OpenAlex、登録 78 leaf の全列挙 (取得証拠あり 77・未走 1)と 2 本目論文への導線 (2026-09-18 (b) の追補、request 0 件)

**これは実行記録であって、登録でも改訂でもない。** 登録の正本は
`2026-09-02-axis1-search-amendment.md`、query program の正本は
`2026-09-02-axis1-search-catalog.json`、1 窓目の実行記録は
`2026-09-03-axis1-search-execution.md`、2 窓目は `2026-09-05-axis1-search-execution.md`、
3 窓目は `2026-09-07-axis1-search-execution.md`、4 窓目 (残量消化と打ち切り) は
`2026-09-08-axis1-search-execution.md`、5 窓目 (打ち切り後の再開) は
`2026-09-17-axis1-search-execution.md`、6 窓目 (未走 2 leaf の初回取得) は
`2026-09-17b-axis1-search-execution.md`、独立 2 走目の停止 (D2120 項 14) を反映した記録手番は
`2026-09-18-axis1-search-execution.md`、`Q6-SY2026` を未走のまま置く裁定 (D2150 項 4) を反映した記録手番は
`2026-09-18b-axis1-search-execution.md` である。
本文書は凍結物であり、後から上書きしない。内容を更新したいときは新しい日付の実行記録を足す。

**軸 1 は `未完走` であり、成熟度は `RW1` のままである。論文は世界の不在を主張しない。**

**本記録は request を 1 本も出さず、bundle にも触れず、検査器も再走していない。新しい裁定も反映していない。**
先行記録 2 本 (2026-09-18 / 2026-09-18 (b)) は、材料の範囲を区分の**件数** (材料に数える 61・数えない 16・未走 1) と、
`complete` 8 leaf・落ちた 16 leaf・未走 1 leaf の**名前**で持つが、pass 1 完了・2 走目は裁定で停止の 53 leaf は件数だけで名前を
持たない。本記録は 2026-09-18 (b) の**追補**として、OpenAlex の登録 78 leaf (取得証拠あり 77 + 未走 1) を 1 行 1 leaf で全列挙し (§2)、枝ごとの内訳 (§3)、
限定 (§4)、未走 query (§5)、2 本目論文 (`docs/paper-story-backoff/`) が参考材料として引くときの読み方 (§6) を 1 か所に置く。
数値・leaf 名・検査器の状態はすべて repo 内の凍結済み一次資料の逐語から採った (§0)。

## 0. この記録の身元

| 項目 | 値 |
|---|---|
| 作成日 | 2026-09-19 (JST) |
| 登録 epoch | `AX1-20260902-E1` (不変) |
| 登録 commit | `4ec3eba04354f9ba86117a2dd488c72d007045e6` (1〜6 窓目・先行記録と同じ。本記録は登録検査を再走していない — request を出さず登録木を必要としないため) |
| 導出元 commit (本記録が読んだ repo の版) | local main `657e1e5a7860a0ff77fd02ab37a6cb58b64cc78c` (本 wave の base)。下の入力 path はこの commit の blob そのものである |
| 入力 path (1) — leaf の状態 | `output/insights/2026-09-17/t2035-axis1-openalex-window6/bundle-check.json` (SHA-256 `7a39126b35ee7981d2e2db48f3dc777c4bb6bf2985ae73c531197ecfc46f0bc1`、`status.leaf_diagnostics` の `@openalex` 78 件) と同 `leaf-states.txt` (SHA-256 `952bfd261c8e2dfe9b464667ddeaf304d75e3cb4fec1ec0a85363406a01f5aa7`)。6 窓目の走行後に検査器が出した出力で、2026-09-18 (b) §4 が bundle に対する offline 再走 (2026-09-18 10:41 JST) で byte 一致を確認したもの |
| 入力 path (2) — 区分の区別 | `2026-09-18-axis1-search-execution.md` §3 (SHA-256 `f4c7f2887f30440f1d0716d283f406d225c7c04085ea3b89ce5490620f89a3ab`)、`2026-09-18b-axis1-search-execution.md` §3・§4 (SHA-256 `631408794537d13532c0f4503f12c3ad910f64b1c53dd73835b891c4ecd2cc25`)、窓 4 の `output/insights/2026-09-08/t2090-axis1-openalex-window4/README.md` (`declared_total_drift` の 2 leaf)、窓 3 の `output/insights/2026-09-07/t2090-axis1-openalex-window3/cond5-detail.txt`・窓 5 / 6 の `evidence-detail.txt` (条件 5 で pass 1 が落ちた 5 leaf) |
| catalog | `docs/related-work/claim-survey/2026-09-02-axis1-search-catalog.json` |
| catalog SHA-256 | `8e23d63a799c8ab9d25151012c34bc738dbb422ac3dfb237999c359137c816ab` |
| 文献 cutoff | `2026-12-31` |
| run ID | なし (起動 0 件) |
| 索引 | OpenAlex のみ (arXiv / DBLP は本 epoch でまだ 1 request も出していない) |
| 生証拠 bundle | `/work/1/SFC/tanab/axis1-bundles/2026-09-03-t2090-openalex/bundle` (1〜6 窓目と同じ root)。**本記録は bundle に触れていない** |
| bundle manifest SHA-256 | `06fbef369ed0bfb071e896d65ee1c1a2321709f5cb8cc787374da7aafbed21dd` — **2026-09-18 (b) §0 の記載値の転記であり、本記録では現物を照合していない** |
| 検査器の再走 | なし。§2 の状態列は入力 path (1) の逐語 |
| 裁定 | 新しい裁定はない。反映済みの裁定は D2120 項 14 (2026-09-17、2 走目の停止・落ちた leaf の据え置き) と D2150 項 4 (2026-09-18、`Q6-SY2026` を未走のまま置く・77 leaf 分の限定付き)。2026-09-18 (b) の作成時点で未採番だった D 番号は、本記録の作成時点では `docs/decisions.md` の D2150 として採番済み |
| 逐語 | 新しい逐語はない。本記録の導出過程 (親の分類 script・相談・レビュー) は `output/insights/2026-09-19/t2035-axis1-materials-record/` |

## 1. 何を起動したか

何も起動していない。初回取得・中断 pass 1 の再開・独立 2 走目 (停止済み、D2120 項 14)・生死確認・件数 probe のいずれも 0 起動・0 request で、
無償枠の残量は観測していない。

## 2. OpenAlex の登録 78 leaf の全列挙 (取得証拠あり 77 + 未走 1)

区分の意味 (件数は 2026-09-18 (b) §3 と同じ。**材料に数える leaf を 61 から増やしていない**):

| 記号 | 区分 | leaf 数 | 材料 | 区分の出所 |
|---|---|---|---|---|
| A | `complete` (登録契約の 6 条件を leaf 単位で満たす) | 8 | 数える | 検査器 `state=complete` |
| B | pass 1 完了・2 走目は裁定で停止 (再開点は bundle に残るが起動しない) | 53 | 数える | 検査器 `resume_action=start_independent_pass` |
| C | 条件 5 (`distinct_work_id_total_mismatch`) で落ちた非 shard 枝 | 3 | 数えない | 検査器 `reason_code` |
| D | 独立 2 走目が不一致 (`second_pass_digest_mismatch`) | 6 | 数えない | 検査器 `reason_code` |
| E | `declared_total_drift` で pass 1 が落ちた (再開点なし) | 2 | 数えない | **検査器の最終コードでは F と区別できない** (`leaf_page_evidence_missing` + `resume_action=None` で同値)。窓 4 記録の `blocked_on_ruling` / `declared_total_drift` の逐語 |
| F | 条件 5 で pass 1 が落ちた (再開点なし) | 5 | 数えない | 同上。窓 3 (`Q3-SY2025` / `SY2026`)・窓 5 (`Q6-SY2021` / `SY2024`)・窓 6 (`Q6-SY2025`) 記録の `blocked_on_ruling` の逐語 |
| G | 未走 (`leaf_not_run`) | 1 | 材料なし | 検査器 `reason_code` |
| 合計 | | 78 | A + B = 61、C〜F = 16、G = 1 | |

A の 8 leaf のうち `Q2` は 1 走で完走する枝 (期待 pass `[1]`) で、独立 2 走まで完了しているのは年 shard の 7 leaf である。
B の 53 leaf の「材料」は pass 1 の台帳 1 本と全頁の生 response であり、**1 走の返却集合は完全とみなせない** (2026-09-18 §3)。
C〜F の 16 leaf は pass 1 の証拠を持つが、契約の条件で落ちているので材料に数えない。落ちた理由 (`reason_code`) を伴わずに引用しない。

| leaf (`AX1-20260902-E1-` と `@openalex` を省略) | 区分 | 検査器 `state` | `reason_code` | `resume_action` | checkpoint | 完了 pass / 期待 pass |
|---|---|---|---|---|---|---|
| `Q1` | C | `incomplete_with_evidence` | `distinct_work_id_total_mismatch` | — | — | `[1]` / `[1]` |
| `Q2` | A | `complete` | — | — | — | `[1]` / `[1]` |
| `Q3-SPRE1991` | A | `complete` | — | — | — | `[1, 2]` / `[1, 2]` |
| `Q3-SY1991` | A | `complete` | — | — | — | `[1, 2]` / `[1, 2]` |
| `Q3-SY1992` | D | `incomplete_with_evidence` | `second_pass_digest_mismatch` | — | — | `[1, 2]` / `[1, 2]` |
| `Q3-SY1993` | A | `complete` | — | — | — | `[1, 2]` / `[1, 2]` |
| `Q3-SY1994` | A | `complete` | — | — | — | `[1, 2]` / `[1, 2]` |
| `Q3-SY1995` | A | `complete` | — | — | — | `[1, 2]` / `[1, 2]` |
| `Q3-SY1996` | A | `complete` | — | — | — | `[1, 2]` / `[1, 2]` |
| `Q3-SY1997` | D | `incomplete_with_evidence` | `second_pass_digest_mismatch` | — | — | `[1, 2]` / `[1, 2]` |
| `Q3-SY1998` | D | `incomplete_with_evidence` | `second_pass_digest_mismatch` | — | — | `[1, 2]` / `[1, 2]` |
| `Q3-SY1999` | D | `incomplete_with_evidence` | `second_pass_digest_mismatch` | — | — | `[1, 2]` / `[1, 2]` |
| `Q3-SY2000` | D | `incomplete_with_evidence` | `second_pass_digest_mismatch` | — | — | `[1, 2]` / `[1, 2]` |
| `Q3-SY2001` | D | `incomplete_with_evidence` | `second_pass_digest_mismatch` | — | — | `[1, 2]` / `[1, 2]` |
| `Q3-SY2002` | B | `incomplete_without_complete_pass` | `leaf_page_evidence_missing` | `start_independent_pass` | `000014` (`pass_complete`) | `[1]` / `[1, 2]` |
| `Q3-SY2003` | B | `incomplete_without_complete_pass` | `leaf_page_evidence_missing` | `start_independent_pass` | `000015` (`pass_complete`) | `[1]` / `[1, 2]` |
| `Q3-SY2004` | B | `incomplete_without_complete_pass` | `leaf_page_evidence_missing` | `start_independent_pass` | `000016` (`pass_complete`) | `[1]` / `[1, 2]` |
| `Q3-SY2005` | B | `incomplete_without_complete_pass` | `leaf_page_evidence_missing` | `start_independent_pass` | `000017` (`pass_complete`) | `[1]` / `[1, 2]` |
| `Q3-SY2006` | B | `incomplete_without_complete_pass` | `leaf_page_evidence_missing` | `start_independent_pass` | `000018` (`pass_complete`) | `[1]` / `[1, 2]` |
| `Q3-SY2007` | B | `incomplete_without_complete_pass` | `leaf_page_evidence_missing` | `start_independent_pass` | `000019` (`pass_complete`) | `[1]` / `[1, 2]` |
| `Q3-SY2008` | B | `incomplete_without_complete_pass` | `leaf_page_evidence_missing` | `start_independent_pass` | `000020` (`pass_complete`) | `[1]` / `[1, 2]` |
| `Q3-SY2009` | B | `incomplete_without_complete_pass` | `leaf_page_evidence_missing` | `start_independent_pass` | `000021` (`pass_complete`) | `[1]` / `[1, 2]` |
| `Q3-SY2010` | B | `incomplete_without_complete_pass` | `leaf_page_evidence_missing` | `start_independent_pass` | `000022` (`pass_complete`) | `[1]` / `[1, 2]` |
| `Q3-SY2011` | B | `incomplete_without_complete_pass` | `leaf_page_evidence_missing` | `start_independent_pass` | `000023` (`pass_complete`) | `[1]` / `[1, 2]` |
| `Q3-SY2012` | B | `incomplete_without_complete_pass` | `leaf_page_evidence_missing` | `start_independent_pass` | `000024` (`pass_complete`) | `[1]` / `[1, 2]` |
| `Q3-SY2013` | B | `incomplete_without_complete_pass` | `leaf_page_evidence_missing` | `start_independent_pass` | `000025` (`pass_complete`) | `[1]` / `[1, 2]` |
| `Q3-SY2014` | B | `incomplete_without_complete_pass` | `leaf_page_evidence_missing` | `start_independent_pass` | `000026` (`pass_complete`) | `[1]` / `[1, 2]` |
| `Q3-SY2015` | B | `incomplete_without_complete_pass` | `leaf_page_evidence_missing` | `start_independent_pass` | `000027` (`pass_complete`) | `[1]` / `[1, 2]` |
| `Q3-SY2016` | B | `incomplete_without_complete_pass` | `leaf_page_evidence_missing` | `start_independent_pass` | `000028` (`pass_complete`) | `[1]` / `[1, 2]` |
| `Q3-SY2017` | B | `incomplete_without_complete_pass` | `leaf_page_evidence_missing` | `start_independent_pass` | `000029` (`pass_complete`) | `[1]` / `[1, 2]` |
| `Q3-SY2018` | B | `incomplete_without_complete_pass` | `leaf_page_evidence_missing` | `start_independent_pass` | `000030` (`pass_complete`) | `[1]` / `[1, 2]` |
| `Q3-SY2019` | B | `incomplete_without_complete_pass` | `leaf_page_evidence_missing` | `start_independent_pass` | `000031` (`pass_complete`) | `[1]` / `[1, 2]` |
| `Q3-SY2020` | B | `incomplete_without_complete_pass` | `leaf_page_evidence_missing` | `start_independent_pass` | `000032` (`pass_complete`) | `[1]` / `[1, 2]` |
| `Q3-SY2021` | B | `incomplete_without_complete_pass` | `leaf_page_evidence_missing` | `start_independent_pass` | `000033` (`pass_complete`) | `[1]` / `[1, 2]` |
| `Q3-SY2022` | B | `incomplete_without_complete_pass` | `leaf_page_evidence_missing` | `start_independent_pass` | `000034` (`pass_complete`) | `[1]` / `[1, 2]` |
| `Q3-SY2023` | B | `incomplete_without_complete_pass` | `leaf_page_evidence_missing` | `start_independent_pass` | `000035` (`pass_complete`) | `[1]` / `[1, 2]` |
| `Q3-SY2024` | B | `incomplete_without_complete_pass` | `leaf_page_evidence_missing` | `start_independent_pass` | `000036` (`pass_complete`) | `[1]` / `[1, 2]` |
| `Q3-SY2025` | F | `incomplete_without_complete_pass` | `leaf_page_evidence_missing` | — | — | `[1]` / `[1, 2]` |
| `Q3-SY2026` | F | `incomplete_without_complete_pass` | `leaf_page_evidence_missing` | — | — | `[1]` / `[1, 2]` |
| `Q4` | C | `incomplete_with_evidence` | `distinct_work_id_total_mismatch` | — | — | `[1]` / `[1]` |
| `Q5` | C | `incomplete_with_evidence` | `distinct_work_id_total_mismatch` | — | — | `[1]` / `[1]` |
| `Q6-SPRE1991` | A | `complete` | — | — | — | `[1, 2]` / `[1, 2]` |
| `Q6-SY1991` | B | `incomplete_without_complete_pass` | `leaf_page_evidence_missing` | `start_independent_pass` | `000037` (`pass_complete`) | `[1]` / `[1, 2]` |
| `Q6-SY1992` | B | `incomplete_without_complete_pass` | `leaf_page_evidence_missing` | `start_independent_pass` | `000038` (`pass_complete`) | `[1]` / `[1, 2]` |
| `Q6-SY1993` | B | `incomplete_without_complete_pass` | `leaf_page_evidence_missing` | `start_independent_pass` | `000039` (`pass_complete`) | `[1]` / `[1, 2]` |
| `Q6-SY1994` | B | `incomplete_without_complete_pass` | `leaf_page_evidence_missing` | `start_independent_pass` | `000040` (`pass_complete`) | `[1]` / `[1, 2]` |
| `Q6-SY1995` | B | `incomplete_without_complete_pass` | `leaf_page_evidence_missing` | `start_independent_pass` | `000041` (`pass_complete`) | `[1]` / `[1, 2]` |
| `Q6-SY1996` | B | `incomplete_without_complete_pass` | `leaf_page_evidence_missing` | `start_independent_pass` | `000042` (`pass_complete`) | `[1]` / `[1, 2]` |
| `Q6-SY1997` | B | `incomplete_without_complete_pass` | `leaf_page_evidence_missing` | `start_independent_pass` | `000043` (`pass_complete`) | `[1]` / `[1, 2]` |
| `Q6-SY1998` | B | `incomplete_without_complete_pass` | `leaf_page_evidence_missing` | `start_independent_pass` | `000044` (`pass_complete`) | `[1]` / `[1, 2]` |
| `Q6-SY1999` | B | `incomplete_without_complete_pass` | `leaf_page_evidence_missing` | `start_independent_pass` | `000045` (`pass_complete`) | `[1]` / `[1, 2]` |
| `Q6-SY2000` | B | `incomplete_without_complete_pass` | `leaf_page_evidence_missing` | `start_independent_pass` | `000046` (`pass_complete`) | `[1]` / `[1, 2]` |
| `Q6-SY2001` | B | `incomplete_without_complete_pass` | `leaf_page_evidence_missing` | `start_independent_pass` | `000047` (`pass_complete`) | `[1]` / `[1, 2]` |
| `Q6-SY2002` | B | `incomplete_without_complete_pass` | `leaf_page_evidence_missing` | `start_independent_pass` | `000048` (`pass_complete`) | `[1]` / `[1, 2]` |
| `Q6-SY2003` | B | `incomplete_without_complete_pass` | `leaf_page_evidence_missing` | `start_independent_pass` | `000049` (`pass_complete`) | `[1]` / `[1, 2]` |
| `Q6-SY2004` | B | `incomplete_without_complete_pass` | `leaf_page_evidence_missing` | `start_independent_pass` | `000050` (`pass_complete`) | `[1]` / `[1, 2]` |
| `Q6-SY2005` | B | `incomplete_without_complete_pass` | `leaf_page_evidence_missing` | `start_independent_pass` | `000051` (`pass_complete`) | `[1]` / `[1, 2]` |
| `Q6-SY2006` | B | `incomplete_without_complete_pass` | `leaf_page_evidence_missing` | `start_independent_pass` | `000052` (`pass_complete`) | `[1]` / `[1, 2]` |
| `Q6-SY2007` | B | `incomplete_without_complete_pass` | `leaf_page_evidence_missing` | `start_independent_pass` | `000053` (`pass_complete`) | `[1]` / `[1, 2]` |
| `Q6-SY2008` | B | `incomplete_without_complete_pass` | `leaf_page_evidence_missing` | `start_independent_pass` | `000054` (`pass_complete`) | `[1]` / `[1, 2]` |
| `Q6-SY2009` | B | `incomplete_without_complete_pass` | `leaf_page_evidence_missing` | `start_independent_pass` | `000055` (`pass_complete`) | `[1]` / `[1, 2]` |
| `Q6-SY2010` | B | `incomplete_without_complete_pass` | `leaf_page_evidence_missing` | `start_independent_pass` | `000056` (`pass_complete`) | `[1]` / `[1, 2]` |
| `Q6-SY2011` | B | `incomplete_without_complete_pass` | `leaf_page_evidence_missing` | `start_independent_pass` | `000057` (`pass_complete`) | `[1]` / `[1, 2]` |
| `Q6-SY2012` | B | `incomplete_without_complete_pass` | `leaf_page_evidence_missing` | `start_independent_pass` | `000058` (`pass_complete`) | `[1]` / `[1, 2]` |
| `Q6-SY2013` | B | `incomplete_without_complete_pass` | `leaf_page_evidence_missing` | `start_independent_pass` | `000059` (`pass_complete`) | `[1]` / `[1, 2]` |
| `Q6-SY2014` | E | `incomplete_without_complete_pass` | `leaf_page_evidence_missing` | — | — | `[1]` / `[1, 2]` |
| `Q6-SY2015` | E | `incomplete_without_complete_pass` | `leaf_page_evidence_missing` | — | — | `[1]` / `[1, 2]` |
| `Q6-SY2016` | B | `incomplete_without_complete_pass` | `leaf_page_evidence_missing` | `start_independent_pass` | `000061` (`pass_complete`) | `[1]` / `[1, 2]` |
| `Q6-SY2017` | B | `incomplete_without_complete_pass` | `leaf_page_evidence_missing` | `start_independent_pass` | `000062` (`pass_complete`) | `[1]` / `[1, 2]` |
| `Q6-SY2018` | B | `incomplete_without_complete_pass` | `leaf_page_evidence_missing` | `start_independent_pass` | `000063` (`pass_complete`) | `[1]` / `[1, 2]` |
| `Q6-SY2019` | B | `incomplete_without_complete_pass` | `leaf_page_evidence_missing` | `start_independent_pass` | `000064` (`pass_complete`) | `[1]` / `[1, 2]` |
| `Q6-SY2020` | B | `incomplete_without_complete_pass` | `leaf_page_evidence_missing` | `start_independent_pass` | `000065` (`pass_complete`) | `[1]` / `[1, 2]` |
| `Q6-SY2021` | F | `incomplete_without_complete_pass` | `leaf_page_evidence_missing` | — | — | `[1]` / `[1, 2]` |
| `Q6-SY2022` | B | `incomplete_without_complete_pass` | `leaf_page_evidence_missing` | `start_independent_pass` | `000066` (`pass_complete`) | `[1]` / `[1, 2]` |
| `Q6-SY2023` | B | `incomplete_without_complete_pass` | `leaf_page_evidence_missing` | `start_independent_pass` | `000067` (`pass_complete`) | `[1]` / `[1, 2]` |
| `Q6-SY2024` | F | `incomplete_without_complete_pass` | `leaf_page_evidence_missing` | — | — | `[1]` / `[1, 2]` |
| `Q6-SY2025` | F | `incomplete_without_complete_pass` | `leaf_page_evidence_missing` | — | — | `[1]` / `[1, 2]` |
| `Q6-SY2026` | G | `incomplete_without_complete_pass` | `leaf_not_run` | — | — | `[]` / `[1, 2]` |

checkpoint 列は bundle 内の `checkpoints/<番号>.json` (state は `pass_complete`)。checkpoint の run ID (`t2090-openalex-20260903` = 1・2 窓目、
`…-20260907` = 3 窓目、`…-20260908a` = 4 窓目、`t2035-openalex-20260917a` = 5 窓目、`…-20260917b` = 6 窓目) から leaf ごとの取得日が引ける
(2026-09-18 §3)。**本記録は leaf ごとの取得日・頁数を再構成していない** — 一次資料が 6 窓の insight に散り、checkpoint は repo 外の
bundle にあるため。必要なら上の引き方で bundle から読む。

## 3. 登録 leaf の枝別内訳

**これは登録した leaf の取得状態の集計であって、候補判定の数でも文献の網羅性を表す数でもない。** 「調べ終えた件数」と読み替えてはならない
(`docs/paper-story/2026-09-17.md` §8 C-4 の「取得件数を『調べ終えた件数』へ読み替えてはならない」を引き継ぐ)。

| 枝 | 登録 leaf | A | B | C | D | E | F | G | 材料に数える (A + B) | 数えない (C〜F) | 未走 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `Q1` (非 shard) | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| `Q2` (非 shard) | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 |
| `Q3` (年 shard: `SPRE1991` + `SY1991`〜`SY2026`) | 37 | 6 | 23 | 0 | 6 | 0 | 2 | 0 | 29 | 8 | 0 |
| `Q4` (非 shard) | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| `Q5` (非 shard) | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| `Q6` (年 shard: `SPRE1991` + `SY1991`〜`SY2026`) | 37 | 1 | 30 | 0 | 0 | 2 | 3 | 1 | 31 | 5 | 1 |
| 合計 | 78 | 8 | 53 | 3 | 6 | 2 | 5 | 1 | 61 | 16 | 1 |

- 非 shard 4 枝 (`Q1` / `Q2` / `Q4` / `Q5`、年で分けずに cutoff まで一括) のうち材料に数えるのは `Q2` だけである。
- `Q3` の材料に数えない 8 leaf = 2 走不一致の `SY1992` / `SY1997`〜`SY2001` (6) + 条件 5 で pass 1 が落ちた `SY2025` / `SY2026` (2)。
- `Q6` の材料に数えない 5 leaf = `declared_total_drift` の `SY2014` / `SY2015` (2) + 条件 5 で pass 1 が落ちた `SY2021` / `SY2024` / `SY2025` (3)。未走 1 = `SY2026`。
- 年 shard 枝の 2025 年・2026 年分は 4 leaf とも材料に無い (2026-09-18 (b) §3)。cutoff `2026-12-31` までを登録した枝のうち直近 2 年分について、
  `Q3` / `Q6` の検索式で何が返るかを本材料は語れない。
- `Q3` / `Q6` 枝の aggregate (全 leaf 完走・互いに素・和の一致) はどちらも `否` のまま (2026-09-18 (b) §2)。

## 4. 材料に共通する限定 (先行記録から逐語で引き継ぐ)

2026-09-18 §3 と 2026-09-18 (b) §3 の限定をそのまま引き継ぐ。どの表現を作るときも同じ場所に置く。

- **索引は OpenAlex だけ。** 登録した 3 索引のうち arXiv / DBLP は本 epoch で 1 request も出していない。
- **検索式は catalog `2026-09-02` の 6 枝** (`Q1`〜`Q6`、`Q3` / `Q6` は年 shard) で、cutoff は `2026-12-31`。
- **取得日は 2026-09-03〜2026-09-17 の 6 窓に散る** (生きた索引に対する取得であり、取得日ごとに集合が違いうる)。
- **材料は返却 work ID の集合 (とその生 record) であって、候補判定ではない。** 検査器のスキーマで `classification` / `work_family_ledger` /
  `controls` / `supplemental_search` / `sensitivity_audit` の 5 層は未実装で、「どの返却が軸 1 に接地するか」の判定は本材料に含まれていない。
  7.7.6 の偽陰性対策 (positive control) も通っていない。
- **B の 53 leaf は 1 走の返却集合であり、完全とみなせない。** 実測した独立 2 走目の不一致 6 本 (2 日で 1/8、12 日で 5/5) と残る 53 本についての
  見込みは 2026-09-18 §4 のとおりで、一般命題にしない。
- **この材料で `RW2` (1 索引について検索式・全ページ・総件数・全候補判定が再現可能) を主張することはできない。**
- **不在の文は 1 つも作らない。** 7.7.3 の `RW1` は「新しい不在方向の表現を作らない。既存の限定付き文を逐語で引用するだけ許す」であり、
  本記録もそれに従う。本記録の表を「2025・2026 年の研究は未検出」「77 leaf を調査済み」のような文へ変換してはならない。
- **母集合の外** は 1〜6 窓目と同じ (§9)。

## 5. 未走 query の明記 — `Q6-SY2026@openalex`

- **未走のまま置く** (D2150 項 4、2026-09-18)。裁定待ちではない。取得器・catalog・bundle・検査器・完走述語は 1 byte も変わっておらず、
  検査器はこの leaf を `leaf_not_run` と報告し、それは正しい (契約上は未走)。
- 宣言的除外 (D1155 / D1207) でも完走条件の免除でもない — 件数 probe が 21,040 件を返した以上、索引が返せる query であり
  「取得できるが取っていない leaf」のままである。
- **21,040 件・106 頁・1060 credit は、6 窓目の起動前に出した件数 probe (登録 filter、`per-page=1`、証拠外) が返した申告総数
  `meta.count` と、そこからの換算 (200 件/頁、10 credit/request) であって、取得実績ではない。** 本材料はこの leaf について 1 頁も持たない。
- 取得するには取得器契約の変更 (U12 の窓またぎ設計 = D2150 項 4 の択 (b)) か catalog の amendment (択 (c)) を伴う新しい裁定が要る。
  どちらも本記録の範囲外。

## 6. 2 本目論文 (`docs/paper-story-backoff/`) が参考材料として引くときの読み方

本記録の置き場を claim-survey にしたのは、軸 1 が主論文 (`docs/paper-story/`) の主張軸 (`2026-08-26.md` §3 の 1「対象の空白」) であり、
文献検索の凍結物は 2 論文で共有する一次資料だからである (`docs/paper-story-backoff/README.md`「`docs/paper-story/` との関係」)。
2 本目論文の関連研究軸 B5 (`2026-09-05-backoff-axis-registration.md`、成熟度 `RW0`、D1936 項 16 で保留) とは別の軸である。

- **B5 の完了・成熟度には数えない。** `docs/paper-story-backoff/2026-09-10.md` §8 の「後続の一般的な CC 合成文献調査を本軸の完了に数えず、
  『先行なし』『世界初』は書かない」はそのまま有効である。本記録は B5 の `RW0` を動かさない。
- 使える形は、軸 1 の登録・取得の**事実** (どの索引・どの検索式・どの期間・どの leaf に取得証拠があるか) を、限定 (§4) と同じ場所に置いて
  参考材料として引くことだけである。`RW1` の表現規律 (不在の文を新しく作らない) は 2 本目論文にも同じに掛かる。
- 導線は `docs/paper-story-backoff/README.md` の同節が本記録を basename で指す。凍結版 (`2026-09-05.md` / `2026-09-10.md`) は書き換えない。

## 7. 次に残るもの

2026-09-18 (b) §5 のとおりで、本記録は何も足しても減らしてもいない。

## 8. 凍結物への注記の限界 (D1208)

- 先行記録 2 本 (2026-09-18 / 2026-09-18 (b)) は凍結物なので、53 leaf の名前を書き足せない。本記録が後継物として持ち、届く経路は
  本記録・`README.md` の一覧行・`docs/paper-story-backoff/README.md` の導線の 3 つである。原記録だけを開いた読者には届かない。
- 2026-09-18 (b) §0・§6 の「D 番号は未採番」は、本記録の作成時点では D2150 として採番済みである。凍結物には書き込めないので本記録が持つ。

## 9. 母集合の外

窓 1〜6・先行記録と同じ。`docs/related-work/README.md` 7.7.4 の「母集合の外にあるもの」をそのまま引き継ぐ。
