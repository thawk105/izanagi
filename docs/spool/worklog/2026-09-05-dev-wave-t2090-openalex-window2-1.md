---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-05
wave: dev-wave-t2090-openalex-window2
seq: 1
title: [T-2090] 軸 1 OpenAlex の 2 窓目を取得した — 独立 2 走目 8 本中 7 本が完走、Q3-SY1992 は 2 日後の 2 走目で申告総数ごと 1 件増えて不一致、初回取得 22 leaf を足して未走 44 (取得 + docs、branch worktree-dev-wave-t2090-openalex-window2、実装面 0・変異 matrix 免除)
---

## 本文

- 依頼は「[T-2090] 軸 1 OpenAlex の取得を次の窓で再開する。独立 2 走目 8 本と未走 leaf の初回取得。
  Q1/Q4/Q5 は除外。残量 200 で新規起動を止める。loop に重複除去を入れる。取得だけ」だった。
  登録 commit `4ec3eba04` を detach した repo 外の木を cwd にし、登録検査 `passed: true` を確かめてから
  30 本を起動した (81 request、停止時の残量 189)。
- **独立 2 走目 8 本のうち 7 本が `branch_complete`。** `Q3-SY1992` だけ `second_pass_digest_mismatch`
  で、pass 2 (9/5) に pass 1 (9/3) に無い work `W7208063655` (1992 年) が 1 件増え、申告総数も 187 → 188 に
  動いた。`2026-09-03b-axis1-cond5-confirmations.md` §7.1 が「未観測」と書いた登録第 2 走の安定性の
  初観測で、2 日間隔では 7/8 安定・1/8 不安定。不一致の leaf には後継 checkpoint が無く、再取得しか
  経路が無い。素材: 2 走目の間隔が判定を左右する — 同日内に 2 走を終える取得 program は [T-2258] / U11 の材料。
- **初回取得は `Q3-SY1997`〜`SY2018` の 22 leaf** (checkpoint 000009〜000030)。1997 年以降の年 shard は
  1 頁に収まらず、2002 年以降は 3〜4 request ある。未走は `Q3-SY2019`〜`SY2026` の 8 と `Q6` の 36 = 44 leaf。
  78 leaf の現状: 完走 8・pass 2 待ち 22・再開点なしの未完走 4 (Q1/Q4/Q5 + SY1992)・未走 44。
- **重複除去は台帳でなく bundle の証拠で行った。** 1 窓目の起動台帳には `Q3-SPRE1991` (5 頁) が無く
  (loop の前に手動起動)、台帳だけで除去すると再走していた。dry-run で 74 起動を確認してから走らせた。
- **駆動 loop の 1 回目は前窓の持続観測 (`remaining=60`) を今窓の残量と読んで 1 本も投げずに止まった。**
  閾値検査を緩めず、正規 runner で checkpoint 000001 の 2 走目を 1 本手動起動して観測を今窓の値 (949) に
  更新し、同じ loop を再起動した。発行規範 `remaining - 30 >= cost` は不変。
- 生死確認は `per-page=1` で 1 credit だった (`per-page=200` は 10 credit)。**消費 credit は頁の大きさに比例する。**
- 段 4 直前の裁定 inbox 再走査: D1564 (条件 5 は現状維持、D1331 の 3 確認を先に) は前提を覆さない。
  D1624 の優先順位に従い Q1/Q4/Q5 は再取得しなかった (Q1 は attempt 2 済み、Q4/Q5 は 24/31 request で
  窓に収まらない)。
- エージェント工数: codex 子 0 本 (軽量版。実装面 0・設計択一なし・受理集合不変なので段 2/3 と段 6 の
  review 子を省略)。取得の駆動 loop は repo 外 job dir の使い捨て script で、逐語を insight に置いた。
- 実装面の差分は 0 なので変異 matrix は免除 (DW-S04)。受入全走は免除せず親が実走した (結果は本エントリの
  land 時の受入 receipt)。
- 逐語・台帳・部分 mirror は `output/insights/2026-09-05_t2090-axis1-openalex-window2/`、凍結した
  実行記録は `docs/related-work/claim-survey/2026-09-05-axis1-search-execution.md`。
  live bundle は 1 窓目と同じ repo 外 root (143 MB、manifest SHA-256 `99f06ae7…`)。

## 次の一手差分

### 更新

- [T-2090] **P2・2 窓目まで取得済み・継続可 (AI)**: 軸 1 OpenAlex 78 leaf のうち完走 8・pass 2 待ち 22
  (checkpoint 000009〜000030)・再開点なしの未完走 4 (Q1/Q4/Q5 は条件 5、Q3-SY1992 は 2 走不一致)・未走 44
  (Q3 SY2019〜2026、Q6 SY1991〜2026)。次の窓 (翌 09:00 JST 以降) で 2 走目 22 本と未走 44 の初回取得を
  進める。再開情報は `output/insights/2026-09-05_t2090-axis1-openalex-window2/README.md` の
  「次の窓の再開情報」。重複除去は bundle の証拠で行い、最初の起動前は前窓の持続観測を残量と読まない。
  2 走目の間隔 (同日内か) は [T-2258] の裁定事項。`axis_complete` の production 経路は [T-2323] が持つ。
  base: b028cd804abd699d3f2c42d1cc9aab14d4821e07c39c68ce8b555ffa6e6d8e8b
