# [T-2850] 試走 v2 後段 — 段 1 brief (2026-09-27 JST、起点 local main ad114fba0、branch worktree-t2850-trial-v2-followup)

- 研究前進: VLDB 差分分析 P3 (探索の独立反復の費用・成果曲線) の本比較の規模を、事前登録 §8 の規則で試走 v2 の実測から確定し、
  計算確認に出せる形にする。完了判定 = 追補 3 が local main に着地し、本比較の node 時間・LLM 直列時間の見積りと案 (a) の判定がユーザーへ提示されている。
- scope (依頼 5 項):
  (1) 欠測と job Elapse の総和を集計し見積り 22.2〜40.5 と照合 (親が実測済み、下記)。
  (2) §8.1 の T_c・s_{t,m}・s_plan・c(t,m)・ℓ(t)・系列の所要と §8.2 の n を追補 3 に書く。
  (3) 本比較の node 時間・LLM 直列時間・暦の見積りを示す。投入はユーザー確認後 (D2212 項 4)。本 wave は qsub しない。
  (4) 案 (a) は「残る待ちの node 時間 > 導入費」のときだけ設計する。判定そのものを段 2・3 で攻撃させる。
  (5) 本比較の job env に IZANAGI_TRACE_ARCHIVE_ROOT (絶対 path) を入れることを追補 3 で登録し、投入 glue (repo 外 v4) を用意する。
- 確定済みユーザー裁定: D2254 (試走 v2 発効、固定 commit 299aa022e)、追補 1 §4 (試走は S1-wh だけ)、D2249 追加項 (時間帯の区切りなし)、
  D2212 項 4 (2 node 時間以上は都度確認)、D2259 (B-5 v2 見送り — 同じ S1 空間の LLM 対照は査読の決め手になりにくいとの判断)。
- 不変条件: 規律 1・2 (verifier・anomaly 即 reject・Tier0・同時検査の全件検査は不変)。事前登録・追補 1・2 の bytes を変えない。
  §8.1 の入力に手法間の差と曲線を使わない (score は cell ごとの ln score の SD にだけ使う)。[T-2851] の留保条件を生成・選択に使わない。
  p3_s4_loop.py の flock 範囲 ([T-2104] 担当) に触れない。仮想リスク向けの gate・検査・台帳は足さない。
- 実測 (親、repo 外 job dir `dev-wave-t2850-trial-v2-followup/`、固定 commit の木 tree-01 の harness `aggregate`、不一致 0):
  job Elapse 総和 103,310 s = 28.70 node 時間 (見積り内)。15 系列すべて scored・b-complete、fallback 0、retry 0。
  verify-local-unavailable 0、LLM 429 0 (親 36 起動すべて rc=0・is_error なし)、探索の品質欠測 0 (block 2 の参照点 1 session だけ品質欠測)。
  LLM の提案拒否 6 件 (A を消費、B は 10 到達) はすべて planner の axis 名の揺れ ([T-2869] と同型)。
  s_{wh,m}: random 0.02385・sweep 0.03079・bo 0.01123・evolution 0.01537・llm 0.00708 → s_plan 0.03894 (random-sweep)。
  T_c(wh) = 3,052 s (非 LLM 12 系列すべて B 到達)。ℓ(wh) = 9,595 s (7,703〜13,904)。Σ_m c(wh,m) = 39,796 s = 11.05 node 時間/block。
  §8.2: |Q|=1 → n1 = 60 (663 node 時間) / n2 = 10 (110.5)。|Q|=2 → n2 = 11、|Q|=3 → n2 = 12。
- (P1) 親の provisional 裁定・攻撃対象: C_max = 510 (事前登録の提案値) なら、Q = {S1-wh}・n = 10 (第 2 段) を推奨。wh+bal (n = 11) は
  規則どおりの c で 243、B-5 v1 の直列検査の換算で 378〜392 node 時間。rh を含む案は換算で 800 超。
- (P2) 親の provisional 裁定・攻撃対象: 案 (a) は、全 arm を評価ごとの job に割る形では実行方法の変更 (追補 2 の先例) になり §3.1 により
  試走 v2 の分散を本比較に使えず、試走のやり直し (約 20 node 時間) が導入費に入る。節約 26.7〜27.1 node 時間 (wh・n = 10) と釣り合い、
  条件不成立 → 設計しない。LLM だけを割る形は計測条件 (系列内の node 混在) が手法間で非対称になる。
- (P3) 親の provisional 裁定・攻撃対象: 本比較の系列番号 R = 100 + b (b = 1..n)、cohort `t2850-main-v1`、投入順の鍵 `t2850-main-order-v1|<b>`、
  固定 commit は試走と同じ 299aa022e (harness・生成器・pipeline は現 main と同一 bytes)、walltime は試走と同じ、LLM 親は同時 4 本以下で投入側が絞る。
- 成果物: `docs/search-repetition-trial-preregistration-addendum-3.md`、insight `output/insights/2026-09-27/t2850-trial-v2-analysis/`、
  spool fragment (worklog・decisions)、repo 外 glue v4 (schedule main・submit の保全 env・LLM 同時本数の制御)。
- 分割: 段 2 codex plan (案 (a) の判定と glue v4 の設計)、段 3 codex 相談 2 本 (統計・事前登録適合 / 案 (a)・運用)、段 5 codex author (glue v4、repo 外へ退避)、
  段 6 read-only レビュー 1 本 (一次資料からの再抽出の検算)。
- 受入・実測環境: repo の変更は docs だけ → 受入全走 1 回 (DW-S04)。glue v4 の test は login で親が pytest。計算投入は無し (本 wave 合計 < 2 node 時間)。
