# 計算ノード job の END → 待ち手の回収遅延 — 直近 landed 12 wave の実測と、周期の局所修正の要否 (2026-09-21)

診断 wave (branch `worktree-waiter-collect-latency`、実装 0 行、job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-waiter-collect-latency/`)。
依頼の逐語は `verbatim/s1-brief.md` 冒頭、段 3 相談は `verbatim/s3-consult-A.md`、段 4 裁定は `verbatim/s4-ruling.md`。

## 1. 依頼と結論

- 依頼: dispatch した計算ノード job の END (NQSV の `Ended Request Time:`) から待ち手 (`tools/dev_wave_wait.py`、`*.done` の mtime) が結果を回収するまでの遅延を、直近 landed wave 12 本の job dir の log と `.done` の mtime から実測し、分布 (中央値・最大) と待ち手の周期の関係を出す。**遅延の大部分が周期由来なら**周期の局所修正 1 件を効果見積りの後に Codex author で実装する。待ち手の書き起こし ([T-740])・lease primitive・dispatch の queue 上限 900 秒 (C-2804) は変えない。
- 結論 (段 4 裁定、`verbatim/s4-ruling.md`): **観測標本では周期が主因との証拠がなく、依頼の実装条件 (遅延の大部分が周期由来) を満たすとは判断しない → 実装しない。** 観測できた producer 68 本で END → producer の `.done` は中央値 14 秒・p90 37・最大 56 秒、`.done` → 親の待ち手 (`dev_wave_wait.py producer`、poll 5 秒) の戻りは中央値 2・最大 5 秒 (n=34)。同一 producer 群で分解すると、周期 (dispatcher の収集 poll 5 秒 + 親の待ち手 poll 5 秒) の内側に入りうる区間の上限は中央値 5 秒・最大 9 秒で、END → 待ち手戻り合計 (中央値 26・最大 52 秒) への寄与率は中央値 17%・最大 25% (spool を観測できた 13 本、§4)。END → NQSV の stderr file の mtime は観測した 217 本すべて 9〜11 秒で、この区間の内訳 (NQSV の配送か file system の可視化か) は観測だけでは確定しないが、この file を書くのは NQSV 側で dispatcher はその出現を待つ側である (§3)。2 定数の poll を 0 にした場合の積算試算 (観測可能部分、代理値を含む) は wave あたり平均 48 秒・最大 159 秒 (§6)。spool が欠測の焦点走・単発 (同一 producer 群では 21 本 = 焦点走 18 + 単発 3、全観測では 37 本) と receipt 以後の未分離区間 (§3) については周期の有無を確定できない。

## 2. 段 1 — 12 wave の同定、資料、観測点、被覆

- 同定: `dev-wave-jobs/*/land*.{json,stdout}` が `status=landed` の着地時刻順 12 本 (着地 2026-09-20 22:54 〜 09-21 05:26 JST): t2797-b5-contrast / branch-residue-cleanup / t2817-acceptance-bottleneck-3 / t2810-g1-launch-validation / t2814-cleanup-command / wall-decomp / paper-story-20260921 / paper-abstract-conclusion-ja / t2344-closure-stage / t2803-provenance-receipt / t2804-provenance-timeout-contract / t2807-b8-prerun。wall-decomp が使った `list_landed.py` は `land*.json` だけを見るので `land-1.stdout` 形式の t2817 を落とす — 本 wave は着地時刻で入れた。wall-decomp の 12 本 (entry 1774) とは 8 本入れ替わっている (共通は t2344 / t2803 / t2804 / t2807 の 4 本。wall-decomp の「story」は `verbatim/dev-wave-paper-story-20260920b.filtered.txt` が示すとおり 09-20b 版で、本 wave の paper-story-20260921 とは別 wave)。brief の「t2817 を入れ fig13 を外す」は `list_landed.py` の現在の上位 12 との差の説明であり、旧標本との差ではない。
- 資料 (すべて job dir と repo 外の残存 artifact。撤去済み worktree 側の `output/pegasus-dispatch/` は読めない): 焦点走・単発 dispatch = 会計本文を中継した `focus*.log` / `run/*.log` / `live/*.stderr.txt` / `run-probe-*.log`。受入 = `acceptance-child-*.log` の `session_root` → `/work/1/SFC/tanab/.izanagi-acceptance-shards/<session>/shard-*/dispatcher.log` と `dispatch/<shard>/{result.json, *.e<req>, receipt.json}`。変異 = job dir に写された `mutation-*-results.json.dispatch-evidence/<hash>/` (result.json / `*.e<req>` / receipt.json / request.json)。producer の `.done`、親の待ち手の `*.wait-receipt.json` (`dev_wave_wait.py producer --receipt-file`) / `wait-*.done` (t2797 の自前 wrapper)。
- 観測点 (JST。観測値はすべて秒単位 — 会計本文は秒表記、mtime は観測上 `.000000000` だが粒度の保証ではない): END = 会計本文の `Ended Request Time:` / spool = NQSV の stderr file (`*.e<req>`) の mtime (会計本文を含む file。受入・変異だけ。焦点走の `.e` file は撤去済み worktree 側で欠測。mtime は file の最終書込み時刻であり login 側で最初に可視になった時刻の観測ではない) / receipt = dispatcher の `receipt.json` の mtime (受入・変異)、**焦点走・単発では会計本文を中継した log の終端 mtime を receipt 相当とした** / done = producer の `.done` の mtime / waiter = 親の待ち手の receipt json の mtime。script の逐語は `verbatim/collect_latency.py.txt` (対応付け規則: log の stem → `.done`、受入 shard は最後に END した shard を producer の代表、変異は最終 attempt だけ `.done` に対応、size 0 の `.wait.log` は待ち手の証拠にしない、門番 loop の `gate-loop-*.done` は外側 `.done`)、観測表は `verbatim/collect_latency.tsv` (254 行)。
- 被覆 (`verbatim/coverage.txt`): 観測できた compute job は **254 本 = 残存資料から観測できた本数であり、12 wave の全 compute job ではない**。焦点走/単発 37/37、受入 producer 20/20 (shard 58 本)、変異 producer 11/18 (attempt 159/225)。欠測 = branch-residue-cleanup の変異 5 producer 38 attempt と t2344 の変異 2 producer 28 attempt (evidence の写しが無く撤去済み worktree 側)。

## 3. 結果 — 段別の遅延 (全観測、`verbatim/summary.txt`)

| 区間 | n | min | 中央値 | 平均 | p90 | max |
|---|---:|---:|---:|---:|---:|---:|
| END → spool (NQSV の stderr file の mtime) | 217 | 9 | 10 | 10.0 | 10 | 11 |
| spool → receipt (dispatcher の収集 poll 5 秒の内側 + 収集・検証・receipt 公開) | 217 | 0 | 2 | 2.2 | 4 | 5 |
| END → receipt (相当) 全 compute job | 254 | 10 | 12 | 12.3 | 14 | 16 |
| 〃 焦点走 (log 終端 mtime) | 27 | 10 | 13 | 12.7 | 14 | 15 |
| 〃 単発 (probe / prerun / live) | 10 | 11 | 12 | 12.3 | 13 | 14 |
| 〃 受入 shard | 58 | 10 | 12 | 12.6 | 15 | 15 |
| 〃 変異 attempt | 159 | 10 | 12 | 12.1 | 14 | 16 |
| END → producer の `.done` (最後の compute job の END から) | 68 | 10 | 14 | 19.9 | 37 | 56 |
| 〃 焦点走 | 27 | 10 | 13 | 12.8 | 14 | 15 |
| 〃 単発 | 10 | 11 | 12 | 12.4 | 13 | 14 |
| 〃 受入 (最終 shard の END から) | 20 | 19 | 22 | 22.7 | 25 | 39 |
| 〃 変異 (最終 attempt の END から) | 11 | 29 | 39 | 38.9 | 49 | 56 |
| `.done` → 親の待ち手戻り (`dev_wave_wait.py producer` の receipt json) | 34 | 0 | 2 | — | 4 | 5 |
| 変異 attempt 間: receipt_i → 次 attempt の qsub (request.json mtime) | 148 | 4 | 7 | 8.6 | 14 | 31 |

- **END → stderr file の mtime は観測した 217 本すべて 9〜11 秒** (受入 58 本 = 10 秒 53 + 11 秒 5、変異 159 本 = 9 秒 21 + 10 秒 127 + 11 秒 11)。この区間の内訳 (NQSV の stderr staging・会計本文の追記・file system の可視化) は観測だけでは確定しない。file を書くのは NQSV 側 (job の `-e` 出力の staging) で、dispatcher はこの間 file の出現を待つ側である。dispatcher は `qstat` の END 状態を見た後、result.json・stdout/stderr・会計本文・compute marker が揃うまで 5 秒 poll で最大 60 秒待つ (`tools/pegasus/dispatch_compute.py` の収集 loop、`DEFAULT_POLL_INTERVAL_S = 5.0` / `DEFAULT_ACCOUNTING_GRACE_S = 60.0`) ので、END → receipt の 10〜16 秒はこの 9〜11 秒 + poll の位相 + 収集処理と整合する。焦点走の END → receipt 相当 10〜15 秒も同じ帯にあるが、spool が欠測なので分離できない。この標本 (同じ夜の連続帯) の外で同じ値になるかは言えない。
- 長い実行でも回収が短い例があり、実行時間だけでは END 後の区間を説明できない: `started` → `ended` が最長 11 分 7 秒の受入 shard (t2803 final3-1 shard-0、tsv 行 193) でも END → receipt は 10 秒、4 秒で終わる変異 attempt (t2797 final attempt 1、行 14) でも 11 秒、2〜3 秒の attempt でも 13〜14 秒。全件の相関は集計していない (例示のみ)。PRR 待ちは `started` より前なので、`started` → `ended` の長短だけでは混雑度を測れない。
- 受入 (最終 shard END → `.done` 19〜39 秒) と変異 (29〜56 秒) の receipt 以後の区間 (中央値 9 秒 / 28 秒) は、区間内部の時刻が無いので「receipt 相当以後の未分離区間」とだけ書く。段 3 で確認した source 範囲 (`tools/dev_wave_wait.py` の `acceptance` の `--poll-seconds` は no-op) ではこの区間を説明する固定 sleep が見当たらず、変異 runner (`tools/mutation_harness.py`) は attempt の終了を待つ箇所を見ただけで全経路は照合していない (段 3 所見 4)。

## 4. 同一 producer 群での分解と、周期の寄与率 (`verbatim/same_sample.txt`)

親の待ち手が receipt json で戻り時刻を残した producer 34 本 (焦点走 18 / 単発 3 / 受入 9 / 変異 4。自前 wrapper・直列 wait-all・receipt 不在は除く) を、同じ producer の中で 4 区間に分解した。周期由来の上限 = spool → receipt + `.done` → waiter (どちらも poll の sleep と処理を含む観測値なので「上限」)。

| 群 | n | END → waiter 合計 中央値 / max | 周期由来上限 中央値 / max | 寄与率 中央値 / max (producer ごとの比) |
|---|---:|---|---|---|
| spool を観測できた受入 + 変異 | 13 | 26 / 52 秒 | 5 / 9 秒 | 17% / 25% |
| 〃 受入 | 9 | 25 / 40 | 5 / 6 | 17% / 25% |
| 〃 変異 | 4 | 36 / 52 | 6 / 9 | 14% / 24% |
| 焦点走 + 単発 (spool 欠測、寄与率は出さない) | 21 | 15 / 19 | — | END → receipt 相当 13 / 14、`.done` → waiter 2 / 5 |

焦点走 + 単発でも END → 待ち手戻りは 13〜19 秒 (焦点走だけなら 14〜19、13 秒は単発) で、poll の内側に入りうるのは最大 10 秒 (dispatcher 5 + 待ち手 5)。brief に書いた「約 1/4」は別標本の中央値の和だったので、この表に置き換えた (段 3 所見 1)。

## 5. `.done` → 待ち手の戻り: 待ち手の種類別 (`verbatim/summary2.txt`)

| 待ち手 | n | min | 中央値 | p90 | max |
|---|---:|---:|---:|---:|---:|
| `tools/dev_wave_wait.py producer` (`_PRODUCER_POLL_SECONDS = 5`) | 34 | 0 | 2 | 4 | 5 |
| t2797 の自前 wrapper `wait-file.sh` (poll 20 秒。[T-740] からの逸脱、job dir 内で repo には入っていない) | 5 | 2 | 10 | 18 | 18 |
| t2807 の `wait-all.sh` (2 TAG を直列に `dev_wave_wait.py producer` で待つ。2 本目の検知は 1 本目の待ちが終わるまで始まらない) | 3 | 47 | 315 | 361 | 361 |

正本の待ち手は poll 周期 5 秒の内側 (0〜5 秒) で戻っている。自前 wrapper の 2〜18 秒はその 20 秒 poll の内側、直列待ちの 47〜361 秒は並列 job を直列に待った親の設計由来で、いずれも正本 producer 待ち手の 5 秒 poll とは別に扱う。親の起床は job dir からは見えない — 参考として t2814 wave の session transcript で待ち手の通知 → 次の assistant turn は 3〜18 秒 (9 例、`verbatim/transcript_wake_t2814.txt` の `gap` 欄。同 file の 2 行目は表示時刻の差 19 秒に対し gap 18 秒で 1 秒異なる — 丸め規則は未確認)。

## 6. 効果見積り (実装しない裁定の根拠、`verbatim/effect_estimate.txt`)

変更候補の定数は 2 つで別物: `tools/pegasus/dispatch_compute.py` `DEFAULT_POLL_INTERVAL_S = 5.0` (直列 attempt ごとに掛かる) と `tools/dev_wave_wait.py` `_PRODUCER_POLL_SECONDS = 5` (producer ごと。中間 attempt では戻らない)。`_COMPUTE_POLL_SECONDS = 15` (`compute` subcommand) は今回識別できた待ち手標本 (receipt json / 自前 wrapper / 直列 wait-all) に出現せず見積り不能。

下の表は**観測可能部分についての、代理値を含む積算試算**である: dispatcher poll 由来 = spool → receipt の実測和 (spool が欠測の焦点走・単発は `END → receipt 相当 − 10 秒` を代理値にした)、待ち手 poll 由来 = `dev_wave_wait.py producer` の receipt json で戻り時刻が取れた producer 34 本 (§4 と同じ集合) だけの `.done` → waiter の実測和 (自前 wrapper `wait-*.done`・直列 wait-all の 2 本目・receipt 不在は除外。初稿は t2797 の wrapper 2 秒を誤って含めていたので焦点再レビューで訂正した)。観測できなかった変異 attempt 66 本 (§2) は入っていない。

| wave | 直列経路の compute job (焦点走+単発 / 受入 / 変異 attempt) | dispatcher poll 由来 (実測和、焦点走・単発は代理値) | 待ち手 poll 由来 (receipt json のある producer の実測和、n) | 合計 |
|---|---|---:|---:|---:|
| t2797-b5-contrast | 73 (3 / 3 / 67) | 156 | 3 (1) | 159 |
| t2803-provenance-receipt | 23 (7 / 2 / 14) | 68 | 32 (11) | 100 |
| t2810-g1-launch-validation | 39 (3 / 2 / 34) | 89 | 0 (0) | 89 |
| t2804-provenance-timeout-contract | 35 (4 / 1 / 30) | 69 | 0 (0) | 69 |
| t2814-cleanup-command | 17 (2 / 1 / 14) | 32 | 12 (5) | 44 |
| t2344-closure-stage | 6 (4 / 2 / 0) | 21 | 14 (6) | 35 |
| branch-residue-cleanup | 5 (4 / 1 / 0) | 15 | 12 (5) | 27 |
| t2807-b8-prerun | 7 (6 / 1 / 0) | 16 | 9 (4) | 25 |
| t2817-acceptance-bottleneck-3 | 6 (2 / 4 / 0) | 12 | 0 (0) | 12 |
| wall-decomp | 3 (2 / 1 / 0) | 8 | 0 (0) | 8 |
| paper-abstract-conclusion-ja | 1 (0 / 1 / 0) | 5 | 0 (1) | 5 |
| paper-story-20260921 | 1 (0 / 1 / 0) | 1 | 4 (1) | 5 |

- 2 定数の poll を 0 にしても、この試算では観測された poll 由来区間の和までしか縮まない: wave あたり平均 48 秒 (12 wave 合計 578 秒 = dispatcher 側 492 + 待ち手側 86、/ 12 = 48.17)・最大 159 秒 (t2797)。旧標本 (wall-decomp の 12 wave、平均 154 分 = 9,240 秒) への参考比較で 48.17 / 9,240 = 0.52%、159 / 9,240 = 1.72% (本 wave の 12 本の所要は測っていない)。
- 一様位相を仮定した条件付き期待値で 5 → 1 秒なら 1 待機段あたり (5 − 1) / 2 = 2 秒: dispatcher だけで t2797 の変異列 67 × 2 = 134 秒 (134 / 9,240 = 1.45%)、t2810 で 34 × 2 = 68 秒 (0.74%)。変異 attempt 30 本で 1 分相当。producer 待ち手は 1 producer 2 秒。
- 依頼の括弧書き (下限 = 3 分未満の連打をしない、上限 = 30 分の無音を超えない) は親の起床周期の規則 (D1685、memory 正本) であり、process 内部の 5 / 15 秒 poll には当てはまらない。内部 poll を伸ばす方向は遅延を増やすだけ、縮める方向は上の効果しか無い。
- 周期を変える実装が触るもの (候補定数ごと): `_PRODUCER_POLL_SECONDS` なら `orchestrator/tests/test_dev_wave_wait.py` の `("sleep", 5)` の期待 (5023 / 5590 行付近) と D664 (test 側の待ち短縮を実測なしで採用しない) の精神。`DEFAULT_POLL_INTERVAL_S` なら `test_pegasus_dispatch_compute.py` の `poll_interval_s` 明示引数 (269 / 3863 行付近) と受入・変異 runner の全 dispatch。`_COMPUTE_POLL_SECONDS` (候補外) なら `test_dev_wave_wait_compute.py` の `clock.sleeps == [15]` (322〜355 行付近) と runbook §7.3 の `経過 + 15 > 上限` の記述。

## 7. 段 3 所見と段 4 裁定の対応 (`verbatim/s3-consult-A.md`、`verbatim/s4-ruling.md`)

codex read-only 1 本 (gpt-6-astra、medium、静的検査)。must-fix 3 / should 2、いずれも real・採用。「実装しない」を覆す所見は無し。

1. 寄与率を別標本の和で出していた → §4 の同一 producer 群の表に置換。
2. 効果見積りを「1 定数で 3〜4 秒/job」と書いていた → §6 の定数別・直列積算・条件付き期待値に置換。
3. 「254 本 = 全 compute job」「旧標本と 1 本差」→ §2 の被覆表と 8 本入れ替わり (共通 4 本) に訂正、154 分は参考比較。
4. 焦点走の receipt 列は log 終端 mtime、+9 / +28 秒は処理費と断定しない → §2・§3 の記述に反映。
5. wall-decomp §4 の「END 後の後処理 6 秒」(t2804 final) と本 wave の同 producer の END → receipt 10〜14 秒 (15 attempt すべて) は整合しない。旧「END」の観測点が未確認なので未解決の不一致として残し、加算しない。「隙間 7.5 秒」と本 wave の receipt → 次 qsub 中央値 7 秒は対象集合が違うので矛盾とは言わない。

## 8. 検査・受入 (記録 commit 時点)

- 実装面の差分ゼロ (insight + spool fragment のみ)。変異 matrix は免除 (DW-S04)。
- `python3 tools/check_docs.py`: 2026-09-21 08:22 JST (fix 3 前の README + verbatim を含む作業木) で「違反なし」rc=0 (`job dir/check_docs-1.log`)。記録 commit 直前 (spool fragment 追加後) に再走し、その rc は worklog fragment に記す。
- 三軸語・placeholder の走査 (`python3 -m orchestrator.campaign.s8b_holdout_freeze search`) は記録 commit 直前に走らせ、結果は worklog fragment に記す。
- verbatim 6 file (codex 出力 5 本と `coverage.txt`) は `git diff --check` の末尾空白抵触を避けるため行末空白だけを除去した (可視文字不変、原文 sha256・bytes・除去行は `verbatim/NORMALIZATION.md`、原文は job dir)。`scripts.sha256` の 7 本は正規化の対象外 (末尾空白なし)。
- 受入全走と land の結果は fold 後に確定するため本 README には書かない (worklog entry と land 記録が正本)。

## 9. 段 6 相当のレビュー (docs-only、read-only 1 本 + 焦点再レビュー 3 巡) の所見と処置

一次資料から数値を再抽出する docs-only wave なので DW-C00 に従い read-only review 1 本を残した (codex gpt-6-astra、静的照合)。逐語は `verbatim/s6-review-A.md`、焦点再レビューは `verbatim/s6-focus-A.md` (1 巡目) / `s6-focus-B.md` (2 巡目) / `s6-focus-C.md` (3 巡目)、親の対応表は `verbatim/s6-fix1-table.md` / `s6-fix2-table.md` / `s6-fix3-table.md`。

- review A (NO-GO、must-fix 4 / should 4 / nit 1。数表 §3〜§6 の転記は全項目一致): (1) §7 に「7 本入れ替わり」が残存 → 8 本に統一。(2) 「こちらの code に周期は無い」「NFS 1 秒粒度」の断定 → 観測の範囲に限定 (§1・§2・§3)。(3) 効果試算が無条件の観測上限ではない → 代理式と除外条件を明記し「観測可能部分についての、代理値を含む積算試算」と呼ぶ (§6)。(4) 「60 本を超える wave だけ分単位」「1〜2%」→ 30 attempt で 1 分相当、分子・分母付きの割合に (§6)。(5) 不在の量化 (固定 sleep / compute 待ち手) と変更影響範囲 → 確認した source 範囲・識別できた待ち手標本に限定し、影響は候補定数ごとに分けた。(6) 数例の対照から無相関 → 例示に限定。(7) 自前 wrapper も 20 秒 poll を含む → 記述を直した (§5)。(8) failures 非記載の理由 → 正本照合 (下記)。(9) 「焦点走 13〜19」は焦点走 + 単発、transcript の丸め → 直した。
- 焦点再レビュー 1 巡目 (NO-GO、closed 5 / partial 3 / regressed 1、新規 must-fix 1 / should 2): **効果試算に t2797 の自前 wrapper の 2 秒が混入** (除外条件と矛盾) → `effect_estimate.py` を receipt json の待ち手だけ (mtime 一致で逆引き、直列 wait-all 2 本目除外) に直して再走、t2797 = 159、合計 578、平均 48.17、最大 159 に訂正 (`verbatim/effect_estimate.txt` を再生成、§1・§6、`s4-ruling.md` 末尾に訂正節)。「焦点走 21 本」→ 焦点走 18 + 単発 3 (§1)。「秒切り捨て」の未裏付け説明 → 削除 (§5)。帰属の断定 → 「内訳は観測だけでは確定しない。file を書くのは NQSV 側、dispatcher は出現を待つ側」に (§1・§3)。
- 焦点再レビュー 2 巡目 (NO-GO、元 9 件 closed 8 / partial 1、新規なし): 残る #8 = 「段 8 では追記しない (誤検知の実測が無い)」が、要否未判断と両立しない → 非追記は依頼の scope (台帳の追加は scope 外) による扱いと書き、防壁の破れ・追記の要否はともに未判断のまま残した (§10)。
- 焦点再レビュー 3 巡目 (GO、後退なし): 派生値 (492 + 86 = 578、48.17、0.52% / 1.72%、134 / 68 の割合、END → spool の本数内訳、焦点走 14〜19 / 単発 13〜16) はレビュー側が原データから再計算して一致。
- 費用: codex 子 5 本 (consult 7 call / 140 秒、review 5 call / 148 秒、focus 6 / 139、4 / 94、4 / 86 秒)、計算ノード job 0。

## 10. 言わないこと・再訪条件

- 言わないこと: 別時間帯・混雑度でも END → spool が 10 秒である / NFS の mtime 粒度が 1 秒である (観測上 `.000000000` だが filesystem の保証ではない) / 受入 +9 秒・変異 +28 秒が全部処理費である / 観測できなかった変異 attempt 66 本の分布 / 12 wave の外への一般化 / 親の起床までの遅延 (transcript 9 例は参考値)。
- 再訪条件: (a) 変異 attempt が 1 wave で 100 本を超える運用が常態化し dispatcher poll の積算が 5 分を超える、(b) `dev_wave_wait.py compute` (15 秒) を使う campaign job の END → 回収を別途測って周期が支配的と出る、(c) NQSV の stderr spool 到着が 10 秒から大きく伸びる標本が出る。
- [T-740] の逸脱 (t2797 の `wait-file.sh`): `docs/failures.md` を照合した — 待ち手の書き起こしの再発群は F24 (log grep / 背景通知の偽完了 / `pgrep` 自己マッチ) の追記で、2026-09-01 の追記が「`.done` 相当の出現だけで判定する」形を正しい形と書いている。t2797 の wrapper は `.done` の出現で判定する形だが producer の生死を見ない (producer が `.done` を書かずに死ぬと上限まで待つ)。本 wave が観測したのは `.done` → 戻りの遅れ (最大 18 秒) だけで、誤検知・偽完了は観測していないが、F24 の 2026-08-26 追記 (正しい `.done` 待ち条件でも偽完了が起きた near miss) が示すとおり、観測された遅延分布だけでは near miss の不在は言えない。既存防壁 (T-740) の破れに当たるか、failures 台帳へ追記すべきかは、いずれも未判断のまま残す。本 wave が台帳へ追記しないのは依頼の scope (「gate・台帳・一般化の追加は scope 外」) によるもので、要否を判断した結果ではない。逸脱の事実と一次資料の所在 (t2797 job dir の `wait-file.sh`、`verbatim/summary2.txt`) を本 README §5 に残す。
