# [T-2850] 試走 v2 の集計と本比較の規模 — 欠測・費用の照合、事前登録 §8 の計算、本比較の見積り、案 (a) の判定 (2026-09-27)

- 依頼 (逐語): `verbatim/request.md`。段 1 brief `verbatim/s1-brief.md`、段 2 plan `verbatim/s2-plan.md`、段 3 相談 `verbatim/s3-consult-a.md` (統計・事前登録適合)・
  `verbatim/s3-consult-b.md` (案 (a)・運用・過剰)、段 4 裁定 `verbatim/s4-ruling.md`。開始 gate `verbatim/startup-gate.log` (rc=0、起点 local main `ad114fba0`)。
- 記録した規則値: `docs/search-repetition-trial-preregistration-addendum-3.md` (追補 3)。
- **repo のコード変更なし。** 集計は repo 外の job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2850-trial-v2-followup/` で行った
  (job-costs.json・aggregate.json・failures.json・section8.json・estimate_main.json・breakdown.json)。script の逐語は `verbatim/scripts.md`。
  harness の集計は試走の固定 commit `299aa022e` の checkout (`trial-v2/trees/tree-01`) の `t2849_comparison_harness aggregate` で出した (不一致 0)。
- **score は本書に載せない。** 親は aggregate の出力で score を見たが、使ったのは cell ごとの ln score の標本 SD だけである (追補 3 冒頭の開示)。
  Codex の子には score を除いた資料 (section8.json・failures-noscore.json など) だけを渡した。

## 1. 欠測と費用の照合 (依頼 (1))

| 項目 | 値 |
|---|---|
| job Elapse の総和 | **103,310 s = 28.70 node 時間** (18 job)。見積り 22.2〜40.5 の内側、上限 200 の 14% |
| 系列の job Elapse | random 4,155・4,203・4,264 / sweep 4,148・4,109・4,247 / bo 4,455・4,408・4,415 / evolution 4,506・4,558・4,486 / llm 18,376・12,198・14,095 s (系列 1・2・3) |
| block job | 2,177・2,359・2,151 s |
| queue 待ち (別欄) | 9〜2,856 s |
| 暦 | 投入 2026-09-26 22:34 JST → 非 LLM は 00:33 までに終了、最後の LLM 系列 03:40 JST |
| 終端 | 15 系列すべて series-end `b-complete` (B = 10)、block job 3 本も `b-complete`。E_B の score 15/15、fallback 0 |
| 機械故障の retry | 0 (1 系列 18 slot の物理 attempt がすべて 1 回) |
| `verify-local-unavailable` | 0 |
| LLM の週次上限 (429) | 0 (親 36 起動すべて rc = 0、`out.json` の `is_error` 0 件、状態 dir に 429 の構造化 field なし) |
| 品質欠測 | 探索系列 0。block 2 の参照点 5 session 中 1 件 (その block の参照点比だけが欠ける) |
| LLM の提案拒否 | 36 機会中 6 件 (系列 1:1・2:4・3:1)、すべて planner の axis 名の揺れ (`role-output`、A を消費)。[T-2869] と同型 |
| bench の測り直し round | 300 session 中 5 件 (2 round 4・3 round 1) |

**所要の内訳 (300 session の `subprocess_wall_s` 計 71,480 s):** 正しさの検査 38,690 s (54%)、bench 周辺 (静定待ち・bench) 24,812 s、build 2,979 s。
旧 block 1 (直列検査) では約 91% が検査だった。slot の和と job Elapse の総和の差 31,830 s は、ほぼ LLM 親の提案待ち (計 31,202 s) と job ごとの準備 (約 30 s × 18)。

## 2. 事前登録 §8.1 の入力 (依頼 (2)) — 値は追補 3 §2

- s_{wh,m} = random 0.02385・sweep 0.03079・bo 0.01123・evolution 0.01537・llm 0.00708、**s_plan = 0.03894** (random–sweep)。「算出しない場合」(a)(b)(c) は非該当。
- **T_c(wh) = 3,052 s** (非 LLM 12 系列の B 到達時刻 2,832〜3,248 s の中央値、未到達 0)。LLM 系列の B 到達は 10,915〜17,071 s。
- c(wh, m) の計 39,795.8 s = **11.05 node 時間 / block**。session 所要の中央値は課題の 300 session で 250.07 s (score session だけなら 250.40 s)。
- **ℓ(wh) = 9,594.9 s** (系列ごと 13,904・7,703・9,595 s、機会 11・14・11)。

段 3 相談 a は T_c・s・n₁/n₂・c・ℓ を資料から独立に検算し、式どおりと確認した。指摘された §8.1(c) の判定の書き方 (総費用で代用していた) は直した (値は不変)。

## 3. 本比較の見積り (依頼 (3))

**推奨 (追補 3 §4): Q = {S1-wh}、C_max が 110.5〜663.3 node 時間なら n = 10 (第 2 段)。** 事前登録の提案値 C_max = 510 ではこれになる。

| 量 | 値 | 出所 |
|---|---|---|
| node 時間 (計画値 C(10)) | **110.5 node 時間** | 実測の c (E_T の再計測 5 session を全系列に加算) |
| node 時間の幅 | 93.2 (E_T の再計測が 1 件も要らない・中央値) 〜 123.6 (各 cell の最大 Elapse + E_T を全系列) | 実測の外挿 |
| 上乗せ要因 | LLM 系列が A = 30 を使い切ると最大 +43 node 時間 (20 機会 × 780 s × 10 系列、事前登録 §9.1 の仮定)。retry・品質の測り直しは含まない | 仮定つきの換算 |
| job 数 | 60 (系列 50 + block job 10) | — |
| LLM の直列時間 | 10 × ℓ = **26.7 時間** (系列ごとの幅から 21.4〜38.6) | 実測の外挿 |
| LLM の機会 | 約 110 (試走は系列あたり 11〜14、うち拒否 0〜4) | 実測の外挿 |
| 暦 (理想の下限) | 26.7 / 4 = **6.7 時間** (D2216 の p = 4) | 事前登録 §8.3 |
| 暦 (見込み) | LLM 系列は 4 本ずつ段階投入 (4 + 4 + 2) で 1 本 3.4〜5.1 時間 (試走) → 約 10〜15 時間。非 LLM と block job 50 本は node の空き次第で並行 (試走では 18 job が投入から 48 分以内に開始) | 実測の外挿 |
| 暦の上限 | **算出不能** (queue の混雑と LLM の週次上限 429 に依存。試走 v2 は 36 機会で 429 0 件、B-5 v1 は 22 機会で 429 に達した先例あり) | — |
| trace の保全量 | 未測定。MOCC の write-heavy stock 1 slot で 522 MB (D2261 の単価実測) から、1,000 session で数百 GB〜数 TB の桁。保全先の /work は空き 81 TB (quota なし) | 換算 |

- 他の Q (追補 3 §3): {wh, bal} は n = 11 で式 243.2、直列検査の換算 378〜392 node 時間。rh を含む案は換算で 800 node 時間を超える。bal・rh は固定 commit では直列検査 + 静定上限 20 秒で、
  追補 2 §7 の追補 (検査の同時化と静定上限) がまだ無い。
- D2219 項 6 の再提示条件 (暦が 2027-01-10 を超え、かつ各 block で最も長い job が LLM 系列) は、暦の見込みが数日以内なので成立しない。
- **研究上の注意 (ユーザーの判断材料):** 本比較の空間は B-5 と同じ S1 (backoff 値 1 個) である。D2259 は B-5 v2 を「値 1 個での LLM 対照は査読の決め手になりにくい」として見送った。
  T-2850 の問い (空間の構造によってどの探索法が効くか、費用・成果曲線) は B-5 と別だが、S1 だけの本比較で言えることは S1-wh に限られる (追補 3 §4)。

## 4. 案 (a) (LLM の待ちを node の外へ) の判定 (依頼 (4)) — 設計しない

- 残る待ち: 10 × ℓ = 26.65 node 時間 (C(10) の約 24%)。試走の中央値の外挿で、回収できる量の実測ではない (最初の提案待ちと追加 job の準備は残る)。
- 導入費: 未測定。実行方法の変更 (評価ごとの job、LLM だけの分割、1 node への複数系列の同居のどれでも) は本登録 §3.1・追補 2 §5 の先例により試走 v2 の分散と T_c を引き継げず、
  試走のやり直しが要る (現方式の実績 28.70 node 時間は参考)。これに実装・検査・smoke と追加 job の準備が加わる。LLM だけを分けると系列内の node の混在と経過時間の意味が手法間で揃わない。
- 段 2 の plan・段 3 相談 b ともに「設計しない」に同意した。段 3 相談 b の指摘で、根拠を「再試走だけで節約を超える」(断定) から「節約が導入費を上回ることを実測で示せない」に改めた。

## 5. 投入 glue v4 (依頼 (5)) — repo 外

- 置き場: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2850-trial-v2-followup/glue-v4/` (glue v3 の写しからの差分、Codex author)。
- `schedule.py main --blocks N --tasks S1-wh --cohort-root <abs>` が本比較の spec (cohort `t2850-main-v1`、R = 100 + b、鍵 `t2850-main-order-v1|<b>`) を出し、
  `submit.py --trace-archive-root <abs>` が qsub の env に `IZANAGI_TRACE_ARCHIVE_ROOT` を入れる。LLM 親の同時 4 本は投入者の手順で守る (glue は強制しない)。
- 保全口の経路: job body (`tools/pegasus/p3_s4_loop_pegasus.sh`) は env を消さず harness を起動し、harness の子は `os.environ` を継承する。MOCC 疎通 (D2261) で
  同じ経路の保全が 552 反復すべて complete になった実走の先例がある。

## 6. 本 wave が閉じないもの

- 本比較の投入 (ユーザーの計算確認の後)。C_max・最終の Q と n・保全先の実 path は発効の決定に書く。
- [T-2869] (axis 名の揺れによる提案拒否) の修正。本登録 §3.1 により、登録契約との具体的な食い違いを示せたときだけ、影響系列を明示した追補で扱う。
- bal・rh の同時検査の harness 拡張、案 (a) の設計。
