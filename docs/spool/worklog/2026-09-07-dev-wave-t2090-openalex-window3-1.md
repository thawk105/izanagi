---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-07
wave: dev-wave-t2090-openalex-window3
seq: 1
title: [T-2090] 軸 1 OpenAlex の 3 窓目を取得した — 未走 44 のうち 31 本を起動して 29 leaf の pass 1 を足し、最近年 2 leaf が条件 5 で落ちた。未走は 13 まで減り、2 走目待ちは 51 になった (取得 + docs、branch worktree-dev-wave-t2090-openalex-window3、実装面 0・変異 matrix 免除)
---

## 本文

- 依頼は「[T-2090] 軸 1 OpenAlex の 3 窓目を取得する。2 走目待ち 22 と未走 44。重複除去は bundle の
  証拠で行う。前窓の観測を織り込む。同日内でしか 2 走目を回せないなら裁定へ返す。使い切る手前で止める。
  取得だけ」だった。登録 commit `4ec3eba04` を detach した repo 外の木を cwd にし、登録検査
  `passed: true` を確かめてから 31 本を起動した (81 request、停止時の残量 189)。
- **無償枠は D1624 の優先順位どおり未走 leaf の初回取得に使い、独立 2 走目には 1 本も届かなかった。**
  未走 44 のうち 31 本を起動して 29 本が `pass_complete` (checkpoint 000031〜000059)。残り 13 本
  (`Q6-SY2014`〜`SY2026`) は次の窓へ持ち越す。78 leaf の現状: 完走 8・pass 2 待ち 51・再開点なしの
  未完走 6・未走 13。
- **最近年の 2 leaf が条件 5 で落ちた。** `Q3-SY2025` (9 頁) と `Q3-SY2026` (16 頁) が
  `distinct_work_id_total_mismatch` で `blocked_on_ruling` になり、後継 checkpoint が書かれない。
  現物の数値は SY2025 が申告 1678 / 返却 1681 / distinct 1676、SY2026 が申告 3034 / 返却 3035 /
  distinct 3031。**申告総数は 1 leaf の取得中の全頁で 1 度も動かず、頁境界の重複 (5 件 / 4 件) を
  除いてもなお distinct が申告総数に 2〜3 件届かない。** U11 の形だが重複だけでは説明が付かず、
  申告されながら 1 度も返らない ID が残る。D1331 の (a) に関わる観測で、snapshot 識別子が無いので
  機序は確定しない。D1623 は U11 に免除を与えないと裁定済みで、結果はその裁定のとおり。条件 5 は緩めていない。
- **検査器の leaf 診断はこの 2 leaf を条件 5 でなく `leaf_page_evidence_missing` と報告する。**
  独立 2 走を要する shard leaf は `expected_passes` が `[1, 2]` になり「pass 2 の証拠が無い」が先に立つ。
  走行時の理由は台帳側にしか残らない。非 shard の Q1/Q4/Q5 は `expected_passes` が `[1]` なので
  条件 5 が leaf 診断に出る。U11 の裁定材料として記録する。
- **2 窓目の駆動 script は 2 走目の重複除去が 1 件も効いていなかった。** checkpoint の `query_id` で
  `ledgers/<ID>.pass2.*` を glob していたが、`query_id` は shard 親 (`…Q3@openalex`) で台帳の file 名は
  shard の leaf ID で付く。正しい field は `leaf_query_id`。2 窓目は pass2 台帳が 0 件で実害が出ず、
  本窓の dry-run が 74 起動 (正しくは 66) を計画したことで露見した。放置すれば完走済み 8 leaf の
  2 走目を回し直していた。
- **本窓で取った leaf の 2 走目は回していない。** 初回取得が書く checkpoint は `second_pass.state` が
  `not_started` なので即座に 2 走目の候補になるが、それは同日内の 2 走目で、間隔の可否は [T-2258] の
  未裁定事項である。checkpoint の `quota.observed_at_jst` が当日のものを計画から外した。
  **依頼の「同日内でしか回せないなら裁定へ返す」には当たらない** — 2 走目待ち 22 本は pass 1 が 9/5 なので
  同日内は成立せず、実施は可能だった。単に予算が先に尽きた。
- 駆動 loop の起動前に `runtime.json` の持続観測が前窓 (9/5 13:11 JST、`remaining=189`) のままである
  ことを織り込み、2 窓目と同じく閾値検査を緩めずに正規 runner を 1 本手動起動して観測を今窓の値 (959) へ
  更新してから回した。発行規範 `remaining - 30 >= cost` は不変。生死確認は `per-page=1` で 1 credit。
- 頁数は枝と年で大きく違う。`Q6` の年 shard は 2006 年まで 1 頁・2007 年以降 2 頁、`Q3` の最近年は
  `SY2019`〜`SY2023` が 4 頁・`SY2024` が 6 頁・`SY2025` が 9 頁・`SY2026` が 16 頁。
  `Q3-SY2026` 1 本で 16 request (160 credit) を使う。
- 段 4 直前の裁定 inbox 再走査: D1624 (現 epoch 維持・窓は未走 leaf の初回取得へ)、D1564 / D1623
  (条件 4・5 を改訂しない) はいずれも前提を覆さない。優先順位は D1624 に従った。
- エージェント工数: codex 子 0 本 (軽量版。実装面 0・設計択一は D1624 が既裁定・受理集合不変なので
  段 2/3 と段 6 の review 子を省略)。駆動 loop と probe は repo 外 job dir の使い捨て script で、
  逐語を insight に `.txt` で置いた ([T-317] の凍結境界)。
- 実装面の差分は 0 なので変異 matrix は免除 (DW-S04)。受入全走は免除せず親が実走した。
- 逐語・台帳・部分 mirror は `output/insights/2026-09-07_t2090-axis1-openalex-window3/`、凍結した
  実行記録は `docs/related-work/claim-survey/2026-09-07-axis1-search-execution.md`。
  live bundle は 1 窓目と同じ repo 外 root (198 MB、manifest SHA-256 `7fd6a7a2…`)。

## 次の一手差分

### 更新

- [T-2090] **P2・3 窓目まで取得済み・継続可 (AI)**: 軸 1 OpenAlex 78 leaf のうち完走 8・pass 2 待ち 51
  (checkpoint 000009〜000059)・再開点なしの未完走 6 (Q1/Q4/Q5 と Q3-SY2025/SY2026 は条件 5、Q3-SY1992 は
  2 走不一致)・未走 13 (Q6-SY2014〜SY2026)。次の窓 (翌 09:00 JST 以降) で未走 13 の初回取得
  (約 26 request) と 2 走目 51 本を進める。2 走目は 1 窓に収まらないので複数窓に分かれる。
  再開情報は `output/insights/2026-09-07_t2090-axis1-openalex-window3/README.md` の「次の窓の再開情報」。
  重複除去は bundle の証拠で行い、checkpoint 側の key は `query_id` でなく `leaf_query_id` を使う。
  最初の起動前は前窓の持続観測を残量と読まない。2 走目の間隔 (同日内か) は [T-2258] の裁定事項で、
  checkpoint 000031〜000059 は 9/8 以降なら同日内にならない。`axis_complete` の production 経路は
  [T-2323] が持つ。
  base: 03d260f2159b5cd676b92d5e787b209c9b44baa29ef2b5573e99a0d61828953f
