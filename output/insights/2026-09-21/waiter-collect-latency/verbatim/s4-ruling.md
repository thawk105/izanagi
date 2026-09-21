# 段 4 裁定 — 計算ノード job の END → 待ち手の回収遅延 (2026-09-21 08:00 JST)

## 段 3 所見の裁定 (codex read-only 1 本、`codex/s3-consult-out.md`)

| # | 所見 | real / refuted | 採否 | 処置 |
|---|---|---|---|---|
| 1 | must-fix: 「周期由来は約 1/4」は別標本の中央値の和で、寄与率にならない | real | 採用 | 同一 producer 群 (待ち手 receipt json あり、n=34) で 4 区間に分解し直した (`verbatim/same_sample.txt`)。spool を観測できた 13 本 (受入 9 / 変異 4) で周期由来の上限 = spool→receipt + done→waiter は中央値 5 秒・最大 9 秒、END→待ち手戻り合計 (中央値 26・最大 52) に対する寄与率は中央値 17%・最大 25% (producer ごとの比の中央値・最大)。焦点走 21 本は spool が欠測なので寄与率を出さず、END→receipt 11〜14 秒 (spool + 収集 poll が未分離) と done→waiter 0〜5 秒を別々に示す。「上限」と書くのは spool→receipt が sleep だけでなく収集・検証・receipt 公開を含むため |
| 2 | must-fix: 効果見積りは定数ごと・直列経路の積算で | real | 採用 | 変更候補は 2 定数 (`dispatch_compute.py` `DEFAULT_POLL_INTERVAL_S = 5.0`、`dev_wave_wait.py` `_PRODUCER_POLL_SECONDS = 5`) で別物。dispatcher poll は直列 attempt ごとに掛かる (変異 67 attempt の t2797 で観測上限 156 秒)、producer 待ち手 poll は producer ごと (中間 attempt では戻らない)。観測上限 (poll → 0) は wave あたり平均 48 秒・最大 161 秒 (`verbatim/effect_estimate.txt`、観測できた job だけの積算)。一様位相の条件付き期待値で 5 → 1 秒なら 1 待機段あたり 2 秒: dispatcher だけで t2797 の変異列 67 × 2 = 134 秒、t2810 で 68 秒。compute 待ち手 (15 秒) は本標本に出現せず見積り不能 |
| 3 | must-fix: 標本の網羅性と 154 分との比較 | real | 採用 | 「254 本」は残存資料から観測できた本数に改める。被覆表 (`verbatim/coverage.txt`): 焦点走/単発 37/37、受入 20/20、変異 producer 11/18 (attempt 159/225; branch-residue-cleanup 5 producer 38 attempt と t2344 2 producer 28 attempt は evidence が撤去済み worktree 側で欠測)。12 wave は着地時刻順の直近 12 本で、wall-decomp の 12 本とは 8 本入れ替わっている (共通 = t2344 / t2803 / t2804 / t2807 の 4 本。wall-decomp の story は verbatim の file 名どおり paper-story-20260920b で、本 wave の paper-story-20260921 とは別 wave)。154 分は旧標本の平均なので削減率は参考比較と明記。brief の「t2817 を入れ fig13 を外す」は list_landed.py の現在の上位 12 との差の説明であり、旧標本との差ではない (brief の書き方の誤りとして insight に注記) |
| 4 | should: 配送・処理費への因果帰属が強すぎる、焦点走の receipt 列は log 終端 mtime | real | 採用 | 観測点の表に「焦点走/単発の receipt 相当 = 会計本文を中継した log の終端 mtime」と明記。END→spool は「NQSV の stderr file の mtime が END の 9〜11 秒後」という観測事実だけを書き、別時間帯・混雑度への一般化は書かない。受入 +9 秒・変異 +28 秒は「receipt 相当以後の未分離区間 (source に固定 sleep は見つからず、区間内部の時刻が無いので処理費とも断定しない)」に改める |
| 5 | should: wall-decomp §4 の「END 後の後処理 6 秒」と今回の t2804 final の END→receipt 10〜14 秒は整合しない | real | 採用 | 未解決の不一致として insight に残す (旧「END」の観測点が未確認)。加算しない。「隙間 7.5 秒」と今回の receipt→次 qsub 中央値 7 秒は対象集合が違うので矛盾とは書かない |

見つからなかった攻撃面 (END の選択、対応付け、隠れた二重 poll、混雑時の END 後長期化、親の起床周期との混同、既裁定・テスト、P5 の切り分け) は所見どおり受け入れる。既裁定 D1791 / D664 / D2140 / D2191 の本文は consult の射影に含めなかったので、親が直接読んで衝突が無いことを確認した (D664 は test 側の待ち短縮、D2140 は END より前、D2191 は provenance 監査の 480 秒、D1791 は完了述語)。

## 裁定

**実装しない (段 5・6 の実装子は起動せず、`4 → 7 → 8 → 9`)。** 理由:

1. 依頼の条件「遅延の大部分が周期由来なら」は成立しない。同一 producer 群で周期由来の上限は中央値 17%・最大 25% (n=13)、絶対値で中央値 5 秒・最大 9 秒。焦点走でも END→待ち手戻りは 13〜19 秒で、うち poll の内側に入りうるのは最大 10 秒 (dispatcher 5 + 待ち手 5)。最大の固定費は NQSV の会計本文 (stderr file) が END の 9〜11 秒後に現れることで、こちらの code に周期は無い。
2. 効果見積り: 2 定数の poll を 0 にしても観測上限は wave あたり平均 48 秒・最大 161 秒 (旧標本の平均 154 分に対し参考比較で 0.5% / 1.7%)。5 → 1 秒の条件付き期待値は dispatcher で最多例 134 秒 (t2797、変異 67 attempt)、producer 待ち手で 1 producer 2 秒。分単位に届くのは変異 attempt が 60 本を超える wave の dispatcher poll だけで、それでも wave 所要の 1〜2%。
3. 依頼の括弧書き (下限 3 分 / 上限 30 分) は親の起床周期の規則 (D1685、memory 正本) で、process 内部の 5 / 15 秒 poll には当てはまらない。内部 poll を 3 分以上に伸ばす方向は遅延を増やすだけで、縮める方向は上の効果しか無い。
4. 周期を変える実装は D664 (待ち短縮は実測なしで採用しない) の精神と、`test_dev_wave_wait.py` (5 秒期待、5023 / 5590 行付近) / `test_dev_wave_wait_compute.py` (15 秒と timeout、321〜355 行付近) / `test_pegasus_dispatch_compute.py` (poll 引数、269 / 3863 行付近) / runbook §7.3 の `経過 + 15 > 上限` の記述に触れる。効果 1〜2% のために触る価値が無い。

**書くもの:** insight `output/insights/2026-09-21/waiter-collect-latency/README.md` + `verbatim/` (観測表・集計・被覆・同一標本分解・効果見積り・script 逐語 + sha256・brief・consult・本裁定・review)。spool fragment = worklog 1 本。decisions fragment は作らない (設計判断を新設せず、依頼の条件が成立しなかった実測結果の記録である。再訪条件は insight に書く)。

**再訪条件 (insight に記す):** (a) 変異 attempt が 1 wave で 100 本を超える運用が常態化し dispatcher poll の積算が 5 分を超える、(b) `dev_wave_wait.py compute` (15 秒) を使う campaign job の END→回収を別途測って周期が支配的と出る、(c) NQSV の stderr spool 到着が 10 秒から大きく伸びる (別時間帯・混雑度の標本で)。

## DW-M01 / 変異

実装面の差分ゼロ (docs-only) なので変異 matrix は免除 (DW-S04)。受入全走は免除しない (段 9 の land 前に `tools/dev_wave_wait.py acceptance` で投入)。実 repo を読むテスト = insight の README を読む test は無い (output/insights は inventory test の対象外か段 7 前に焦点走で確認)。

## 段 6 相当 (docs-only の read-only review 1 本)

DW-C00「一次資料から事実を再調査・再抽出する docs-only は段 6 の独立 read-only レビュー 1 本を残す」に従い、insight README 起草後に codex review 1 本 (数値と限定文を verbatim と 1 対 1 で照合) を掛け、must-fix は親が README を直して焦点再レビュー (DW-O16、上限 3 巡)。

## DW-O12 (裁定手順と実行手順の差)

段 3 は brief の予定どおり 1 本。段 2 は省略 (brief 記載どおり)。差なし。

## 訂正 (段 6 焦点再レビュー 1 巡目、2026-09-21 08:2x JST)

- 上の「観測上限は wave あたり平均 48 秒・最大 161 秒 (0.5% / 1.7%)」は、効果試算 script が t2797 の自前 wrapper (`wait-acceptance-final2.done`、2 秒) を正本待ち手の分として含めていた誤りを含む。receipt json の待ち手 34 本に限ると合計 578 秒 (dispatcher 492 + 待ち手 86)、平均 48.17 秒、最大 159 秒 (t2797)、参考比較 0.52% / 1.72%。裁定 (実装しない) は変わらない。
- 「こちらの code に周期は無い」「最大の固定費」は観測を超える帰属なので、insight では「stderr file の mtime − END は 9〜11 秒で、内訳は観測だけでは確定しない。file を書くのは NQSV 側、dispatcher は出現を待つ側」に限定した。
