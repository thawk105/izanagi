---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-27
wave: t2850-trial-v2-followup
seq: 1
title: [T-2850] 試走 v2 を集計した — job Elapse 計 28.70 node 時間 (見積り 22.2〜40.5 の内)、15 系列すべて score あり・欠測 0。事前登録 §8 の入力 (s_plan 0.03894・T_c 3,052 s・ℓ 9,595 s) と本比較の固定値を追補 3 に登録し、S1-wh の 1 課題・C_max 510 なら 10 系列 (110.5 node 時間) を推奨、LLM の待ちを node の外へ出す案は設計しない。本比較の投入はユーザーの計算確認待ち (docs + repo 外 glue v4、branch worktree-t2850-trial-v2-followup)
---

## 本文

- 依頼: 試走 v2 の後段 5 項 (欠測と費用の照合、§8 の計算と追補 3、本比較の見積り、案 (a) の条件判定、本比較での trace 保全の opt-in)。本 wave は計算を投入していない。
- 欠測: `verify-local-unavailable` 0、LLM 429 0 (親 36 起動すべて rc=0)、探索系列の品質欠測 0、retry 0。block 2 の参照点 1 session だけ品質欠測。
  LLM の提案 36 機会中 6 件が planner の axis 名の揺れで拒否された ([T-2869] と同型、A を消費、3 系列とも B=10 到達)。
- 親は harness の aggregate 出力で score を見た。使ったのは cell ごとの ln score の SD だけで、Codex の子には score を除いた資料だけを渡した (追補 3 冒頭に開示)。
- 段 2 plan 1 本・段 3 相談 2 本 (統計・事前登録適合 / 案 (a)・運用・過剰)・段 5 author 1 本 (repo 外 glue v4)・段 6 レビュー 1 本。段 3 の real 所見 6 件を採用
  (§8.1(c) の判定の書き方、未試走課題の換算を式の値と別欄にする、案 (a) の根拠を「実測で示せない」へ改める、glue の関数名衝突、LLM 同時 4 本を機械保証と書かない、暦の見積りの追加)。
- 設計判断は {{D:t2850-trial-v2-addendum3}}。

## 次の一手差分

### 更新

- [T-2850] **P1 (VLDB 差分分析 P3: 探索の独立反復の費用・成果の曲線) — 本比較の計算確認待ち**: 事前登録 v1 (D2231)・追補 1〜3。試走 v2 (cohort `t2850-trial-v2`、18 job) は
  2026-09-27 03:40 JST に終わり、job Elapse 計 28.70 node 時間、15 系列すべて score あり (追補 3 §1)。追補 3 に §8 の入力と本比較の固定値
  (cohort `t2850-main-v1`、系列番号 100 + b、固定 commit `299aa022e`、trace 保全の opt-in、LLM 親は同時 4 本以下) を登録し、課題の集合を S1-wh に決めた ({{D:t2850-trial-v2-addendum3}})。残りは 2 つ。
  (1) **ユーザーの計算確認**: C_max (事前登録の提案 510) を決める。110.5〜663.3 node 時間なら系列数 10 (第 2 段、C(10) = 110.5 node 時間、幅 93〜124、A = 30 の使い切りで最大 +43、
  LLM の直列時間 26.7 時間、暦の理想下限 6.7 時間・見込み 10〜15 時間)。確認後に発効の決定 (C_max・課題・系列数・保全先の実 path・追補 3 の raw SHA-256) を書き、
  repo 外の glue v4 (`dev-wave-jobs/dev-wave-t2850-trial-v2-followup/glue-v4/`) で投入する。LLM 系列は 4 本ずつ段階投入する。
  (2) MOCC (S2)・policy IR (S3) は、その空間の最初の生成より前の追補で足す。read-heavy・balanced を本比較に入れるなら検査の同時化と静定の上限を別の追補で決める (追補 2 §7)。
  **生成・選択には [T-2851] の留保条件を使わない**。材料 `output/insights/2026-09-27/t2850-trial-v2-analysis/README.md`。
  base: 8f9e26626a69acc7aa562887e4684c09c78a6bb4597d41f64e3ecd184bdfa5b5
