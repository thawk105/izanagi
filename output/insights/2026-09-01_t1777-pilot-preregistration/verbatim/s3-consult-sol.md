## D1296 の 9 項目の照合

1. `refuted` — 60 対/workload は欠落していない。本文計画は `reps=60`、`pair_index=0..59` を固定し、policy も `pilot_pairs_per_workload=60`、各 workload の `reps=60` とする。根拠: `s2-plan.md:46,57,114`、`paper_story_a1_paired.v3-pilot.json:176,218-224`。

2. `refuted` — 5 対×12 block と variant 先行 6 / baseline 先行 6 は欠落していない。sizer も 12 block の lead 数を各 6 と実検査する。根拠: `s2-plan.md:58,115-116`、`paper_story_a1_paired.v3-pilot.json:170-175`、`size_paper_story_a1_balanced.py:473-487`。

3. `refuted` — 凍結 seed による組内順は、3 workload の root seed、preimage、order bit、all-identical redraw を含めて閉じている。driver も counter 0..15 で導出し、16 到達時に fail-closed する。根拠: `s2-plan.md:52-66,117`、`paper_story_a1_paired.py:1486-1524`。

4. `real` — 記録量の約束が閉じていない。sizer が受け付ける observation row は `arm, block, block_position, ended_at_ns, group, pair_index, started_at_ns, tps` の正確な 8-key set だけだが、プランは広い `receipt keys:1568-1584` を参照し、本文候補では `group` を observation field として明記していない。`pair_index` も規模説明にはあるが、8 field の閉じた列挙にはなっていない。本文にはこの 8 個を過不足なく列挙すべきである。根拠: `s2-plan.md:9,46,118-122`、`size_paper_story_a1_balanced.py:74-85,434-437`、`paper_story_a1_paired.py:1581-1584`。

5. `refuted` — 対 SD からの `sigma_pair` は、60 個の variant-minus-baseline 差、df=59、片側カイ二乗上側係数まで固定されている。根拠: `s2-plan.md:80-81,123`、`paper_story_a1_paired.v3-pilot.json:183`、`size_paper_story_a1_balanced.py:459-496`。

6. `refuted` — block 平均からの実効 `sigma_block` は、連続 5 対の平均を 12 個、df=11、`sqrt(5)` と片側上側係数まで固定されている。根拠: `s2-plan.md:82,124`、`paper_story_a1_paired.v3-pilot.json:182`、`size_paper_story_a1_balanced.py:488-497`。

7. `refuted` — 大きい方を採る規則は `planned_sigma=max(sigma_pair,sigma_block)` と明示され、実装も同じである。根拠: `s2-plan.md:83,125`、`paper_story_a1_paired.v3-pilot.json:177`、`size_paper_story_a1_balanced.py:498`。

8. `real` — 判定式・floor・3 条件・80% は書かれているが、判定手順はまだ事前登録として閉じていない。`--search-trials` と `--certification-trials` は必須引数で default がなく、seed と採用 n の双方に影響するうえ未裁定である。また Clopper–Pearson の attempt 別 alpha `1/(60*j*(j+1))` と、4090 まで認証 n が無い場合の `no-passing-n` 終了も本文案に明記されていない。プラン自身が trial 数を blocker と認識しているのは正しいが、未解決のままでは発効不能である。根拠: `s2-plan.md:131-137,224-230`、`size_paper_story_a1_balanced.py:133-137,630-728,878-881`。

9. `refuted` — pilot を最終推定へ混ぜない約束は落ちていない。policy、pilot変換物、sizer input のすべてが `final_estimate_eligible=false` を要求する。根拠: `s2-plan.md:14,129,178`、`paper_story_a1_paired.v3-pilot.json:2-5,37`、`size_paper_story_a1_balanced.py:411-418,524-530`。

したがって、9 項目中で本文化前に修正が必要なのは **#4 と #8** である。

## 限定文言の検査

1. `refuted` — D1295 項目 5 の限定は、単に「5-rep 均衡スケジュール下」と呼ぶだけではない。estimand の逐語、残留効果の無い定常状態の直接効果との同一視禁止、時間隔交絡・残留効果が消えた証拠ではないという限界を隣接して書く計画なので、直接効果との読み違えを明示的に拒否できる。`variant-minus-baseline` が物理的な先行-minus-後行ではないことも明確である。根拠: `s2-plan.md:148-158,175-177`、`paper_story_a1_paired.v3-pilot.json:58-60`、`paper_story_a1_paired.py:4334-4348`。

## 権威の含意

1. `refuted` — `formal=false`、`promotion_prohibited=true`、`result_authority=pilot-sizing-input-only`、`final_estimate_eligible=false` の値そのものはすべて正しく射影されている。pilot 自身へ `resolved-*` 分類を与えない点も driver と一致する。根拠: `s2-plan.md:25-29,168`、`paper_story_a1_paired.py:3174-3179`。

2. `real` — 受理・拒否の両側の含意はまだ弱い。本文は明示的に「受理できるのは、3 workload がすべて valid/complete な pilot から作る sizing input と、その登録済み式による sigma・certificate・採用 n だけ」とすべきである。反対側は「差の符号・大きさ、性能優劣、pilot の分類、部分的または invalid な workload、正式結果、promotion、最終推定には使えない」と閉じる必要がある。現 driver は `complete=true` のときだけ `sizing-pilot.json` を作るが、プランはこの受理条件を本文項目にしていない。根拠: `s2-plan.md:14,174-179`、`paper_story_a1_paired.py:1825-1869,5944-5954`。

## 語彙の不一致

1. `real` — 分類名は一致しない。sizer の `CONDITIONS` は `bounded-within-floor` と `resolved-beyond-floor/{improvement,regression}` を使う一方、driver の `CLASSIFICATION_RULES` は `bounded-below-floor`、`resolved-above-floor`、`unresolved` を使う。後者は v2 policy の検証にだけ使われ、pilot の結果分類は `pilot-sizing-input-only` へ迂回する。根拠: `size_paper_story_a1_balanced.py:54-58,560-590`、`paper_story_a1_paired.py:199-215,900-947,3174-3179`。

2. `refuted` — プランの語彙選択は正しい。本文の sizing 動作特性には sizer/certificate の `bounded-within-floor`、`resolved-beyond-floor`、`unresolved` を使い、driver の旧分類名を主表記にしてはならない。条件 ID は policy の `zero`、`positive-six-percent`、`negative-six-percent` を主とし、sizer の `positive-two-floor` / `negative-two-floor` は明示的な alias としてだけ併記する。根拠: `s2-plan.md:133-139`、`paper_story_a1_paired.v3-pilot.json:131-152`。

## 恒真な保証

1. `refuted` — `bench_max_rounds=1` は謳うだけの保証ではない。policy 検証、実行 option の exact check、`run_campaign` への引渡し、receipt と arm evidence の再検証がすべて 1 以外を拒否する。したがって旧「最大3回の内部再測定」はこの配置では解けたと書いてよい。根拠: `paper_story_a1_paired.py:1273-1284,1872-1914,1619-1620,1760,3646-3648,5061-5085`。

2. `real` — `rep_notes` の限界を「v3 invalid_rules にないから消えた」とするプランは実装と食い違う。driver は v3 でも `rep_notes != []` を `rep-notes-not-empty` として workload invalid にする。これは policy の16文字列外にある隠れた受理規則であり、事前登録の閉じた判定規則になっていない。旧感度分析を単純に落としてはならない。根拠: `s2-plan.md:171,189`、`paper_story_a1_paired.v3-pilot.json:38-55`、`paper_story_a1_paired.py:3644-3645`。

3. `real` — 少なくとも射影された driver だけでは、16 invalid rule のうち「両 arm が最初の bench block 前に build・verify 済み」「各 block 前の競合テナント probe」「settle が schedule 開始時に正確に1回」を artifact から拒否できるとは確認できない。arm validator は各 arm 内の stage 順だけを検査し、driver 自身の `_assert_single_tenant()` は workload ごとに1回で、schedule receipt に probe 回数・時刻はなく、settle も true の確認だけである。これらを本文で「機械的に拒否される」と断言するには、親が別の実装証拠を示す必要がある。根拠: `paper_story_a1_paired.v3-pilot.json:41-44`、`paper_story_a1_paired.py:1568-1584,1619-1625,3525-3558,5041`。

## その他の所見

1. `real` — 限界節は、pilot から sized study への分散・baseline scale の移送可能性を十分に明記していない。sizer の動作特性は pilot-derived sigma と baseline mean を固定した正規モデルであり、D1295 の配置変更は正規性、定常性、pilot と本走の同分布性を証明しない。「実現成功確率の保証ではない」まで書くべきである。根拠: `s2-plan.md:179`、`size_paper_story_a1_balanced.py:611-616,763-770`、先例 `README.md:108-116`。

2. `refuted` — pilot 後にしか存在しない `pair_sd_tps`、各 sigma、採用 n、k、実現成功率を本文へ先取りする計画にはなっていない。空欄も作らず certificate にだけ記録する方針で正しい。根拠: `s2-plan.md:162-164`。

3. `refuted` — 本文自身または policy の hash を本文へ書く自己参照は明示的に禁止されている。記載予定の sizing root-seed digest は policy hash ではないため、この禁止には抵触しない。根拠: `s2-plan.md:7,141-145,160-162`。

4. `refuted` — プラン本文には verifier・invalid・rerun を緩める提案や、性能出力からの再走裁量はない。規律2/3への直接の緩和は認められない。ただし上記の隠れた `rep_notes` gate と未立証 invalid rule を解消するまでは、機械契約との一致を宣言できない。根拠: `s2-plan.md:99-108,165-168`、`CLAUDE.md:67-76`。

## 総括

- 最優先で trial 数、attempt 別 CP alpha、`no-passing-n` を計測前に機械可読正本へ凍結する。現状は発効不能。
- 16 invalid rule のうち pre-bench 両 arm verify、block ごとの tenant probe、exact-once settle の実拒否証拠を閉じる。
- `rep_notes` は現 driver で invalid になるため、「限界が消えた」という記述を撤回する。
- authority 節を、complete pilot の sizing-only 受理と、効果・分類・最終推定等の拒否の両側で閉じる。
- observation の exact 8 fields と、sizer 語彙・モデル移送限界を本文へ明記する。静的検査のみで、テストは実行していない。