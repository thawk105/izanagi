---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-17
wave: dev-wave-t2035-axis1-openalex-window5
seq: 1
title: [T-2035][T-2037] 軸 1 OpenAlex の取得を D1760 の打ち切り後にユーザー指示で再開し 5 窓目を取得した — 未走の pass 1 を 7 本進め、12 日を隔てた独立 2 走目は 5 本とも不一致 (docs のみ、branch worktree-dev-wave-t2035-axis1-openalex-window5、実装面の差分ゼロ)
---

## 本文

- **ユーザーの直接指示 (`/dev-wave` 引数) で、D1760 が打ち切った軸 1 OpenAlex の窓ごとの取得を再開した**
  ({{D:axis1-openalex-fetch-resumed}})。D1760 の射程のうち「`RW1` 据え置き・世界の不在を主張しない・
  既存証拠の bytes 不変・同じ登録 commit と epoch を引き継ぐ・arXiv / DBLP 不変」はそのまま維持し、
  変えたのは「以後の窓は回さない」だけである。指示は既存の [T-2035] / [T-2037] を名指ししており、
  4 窓目の記録が置いた「再開時は新 T を起こす」注記はこの名指しが上書きした。
- **段 1 で D1760 を発見して brief に出した。** 依頼が名指す T の主題照合 (D1836) は「既裁定 = 打ち切り」を
  指しており、依頼と台帳が真逆だった。ユーザーの直接発話は信頼できる中核なので依頼を優先し、
  台帳側は decisions fragment で supersede を記録して整合させた。
- **12 起動 / 93 request、残量 999 → 69。** 未走 9 leaf のうち 7 本 (`Q6-SY2018`〜`SY2024`) の pass 1 を
  起動し、5 本 `pass_complete`、`SY2021` / `SY2024` が条件 5 (`distinct_work_id_total_mismatch`、いずれも
  1 件不足) で `blocked_on_ruling`。最近年は頁数が単調に増え (2018 年 5 頁 → 2024 年 24 頁、申告総数 4669)、
  初回取得 7 本だけで 84 request を使った。1 窓では初回取得が終わらず、未走は `SY2025` / `SY2026` の 2 本。
- **申告総数は全頁一定だが、頁境界を跨ぐ重複が 7 leaf 中 6 leaf にある。** 頁内の重複は 0。cursor 分頁の
  最中に並びが動いて同じ work が 2 頁に現れ、通るか落ちるかは押し出された work が別の頁に再出現するか
  (重複だけで済む) 消えるか (distinct が 1 件足りない) の差だった。4 窓目の `declared_total_drift` は
  本窓では出ていない。
- **12 日を隔てた独立 2 走目は 5 本とも `second_pass_digest_mismatch`。** loop が残量 159 で止まった後、
  閾値を下げて回すと計画順で先に来る `Q6-SY2025` (20 頁超) が取得器の自己施錠 (残量 40 未満で発行不能) を
  招くため、親が 2 走目の先頭 5 本 (計 9 request) を checkpoint の argv どおり 1 本ずつ起動した。
  申告総数が同じ `Q3-SY2000` でも ID が 2 件入れ替わり、5 本すべてで共通 ID の順序も変わった。
  2 窓目 (2 日隔てて 8 本中 1 本不一致) より格段に高く、残る 2 走目待ち 48 本 (pass 1 は 9/5・9/7・9/8) も
  同じ運命になる見込みが強い。**「同じ登録 request を日を隔てて 2 度投げて同じ集合が返る」完走条件は、
  生きた索引に対して日数が経つほど成立しない。** 2 走目を続けるかは裁定事項であり、本 wave は方針を
  変えていない。
- **裁定待ちの 2 leaf (`Q6-SY2014` / `SY2015`、`declared_total_drift`) は走らせていない。** 駆動 loop の
  除外集合に明示的に置き、`SY2015` が残した `continue_cursor` の checkpoint `000060` が再開経路 (段 A0)
  に乗らないようにした。段 A0 の経路自体は依頼どおり残した。
- **駆動 script は Codex `role=author` の実装子に書かせた** (4 窓目と同じ [T-317] の択 (b))。4 窓目の逐語を
  土台に、差分は docstring の窓番号・path 定数 2 行・除外集合への 2 leaf 追加だけ。親の独立 diff で
  この 3 点以外の差分ゼロを確認し、fix は 0 巡。dry-run は期待どおり計画 62 件 (再開 0 / 未走 9 /
  2 走目 53)、除外 2 leaf は不在。登録検査は detach 木で `passed: true`。
- **条件は緩めていない。** 取得器の `blocked_on_ruling` をそのまま記録した。取得器・検査器・発行規範・
  条件 5 の扱いには触れていない。repo の実装面の差分は 0。
- 打ち切り時点からの変化 (OpenAlex 78 leaf): 完走 8 (不変)・pass 2 待ち 53 (−5 不一致 +5 新規)・
  再開点なしの未完走 8 → 15 (2 走不一致 1 → 6、条件 5 の pass 1 落ち 2 → 4)・未走 9 → 2。
  検査器は `bundle_validation_complete: true` / `exact_identity_map: true` / `passed: false` /
  `reason_code: leaf_not_run` (rc=2)。生証拠 bundle は 296 MB、manifest SHA-256 は
  `a6a42514e6d5…` (走行前 `f3aeb91f…` = 4 窓目の走行後値と一致)。
- エージェント工数: codex 子 1 本 (author、`gpt-6-astra` / `medium`、fix 0 巡)。段 2/3 と段 6 の
  review 子は省略 (軽量版: 設計択一が割れない・受理集合不変)。実装面の差分は 0 なので変異 matrix は
  免除 (DW-S04)。受入全走は免除せず親が実走した。
- 逐語・台帳・部分 mirror は `output/insights/2026-09-17/t2035-axis1-openalex-window5/`、
  凍結した実行記録は `docs/related-work/claim-survey/2026-09-17-axis1-search-execution.md`。

## 次の一手差分

### 更新

- [T-2035] **P2・取得継続中 (5 窓目まで)**: OpenAlex `Q6` の年 shard は 2024 年で 24 頁 (申告総数 4669) と
  大きく、未走は `Q6-SY2025` / `SY2026` の 2 本 (それぞれ 20 頁前後の見込み、1 窓で収まる)。
  頁境界を跨ぐ重複が常態で、条件 5 の不足 1 件で落ちた `Q6-SY2021` / `SY2024` の扱いは裁定待ち。
  記録は `docs/related-work/claim-survey/2026-09-17-axis1-search-execution.md`。
  base: c3679e3d9110a954364ca9cbfc591d1bbb4d66bd36239584eda019c72e3bf7e3
- [T-2037] **P2・裁定待ち**: 再開点からの継続は 5 窓目で再開したが、12 日を隔てた独立 2 走目は 5 本とも
  `second_pass_digest_mismatch` になり、残る 2 走目待ち 53 本 (うち 48 本は pass 1 が 9/5〜9/8) も同じ
  運命になる見込みが強い。2 走目を続けるか、完走条件 (同一集合の再現) を生きた索引に対してどう置くかは
  裁定事項 ({{D:axis1-openalex-fetch-resumed}} の裁定パッケージ)。`declared_total_drift` の 2 leaf
  (`Q6-SY2014` / `SY2015`) の扱いも同じ包みに載せる。
  base: 123619f768f58daa91c5d60f9735eac5bea2c9a056a8a5f1d8ba7d4959d83fe3
