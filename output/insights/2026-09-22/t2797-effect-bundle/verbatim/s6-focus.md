**NO-GO（文書の残件あり）。** 最終 critic が正常 score に混入する主要経路は解消しています。ただし、toolchain の照合元と、handshake の終了理由の断定に不整合が残ります。

対象は `562b1c1e0` まで。静的検査・保存資料の再計算のみを実施しました。f1 の **2,732 passed / 14 skipped** は確認しましたが、fix 後のテスト結果・変異 KILLED は未確認です。f2 は判定に使用していません。

以下、`E` は `output/insights/2026-09-22/t2797-effect-bundle`、`D` は `orchestrator/campaign/b5_generator_contrast.py`、`T` は `tools/b5_llm_round.py` を表します。

| 所見 ID | 判定 | 根拠 file:line | 残る問題 |
|---|---|---|---|
| A-1／R2 | **partial** | `E/bundle/b5-llm-parent-template.md:25`・`:34`・`:37`、`D:551`・`:672`・`:744`・`:817` | 次 request がある場合だけ critic を実行する修正は成立。ただし「必ず proposal-wait-timeout」は成立せず、先に `allocation-exhausted` で終わりうる。**影響:** score 欠測は維持されるが、登録した終了理由と台帳が食い違う。 |
| A-2／R3 | **closed** | `E/bundle/b5-llm-parent-template.md:31`・`:33`・`:34`、`T:294`・`:334`・`:368`、`D:754`・`:786`・`:800` | planner/coder の不合格を修正・再呼出しせず reject。子側 A-only 拒否では slot を待たず、同じ k の次 a へ進める。予算終了時の分岐もある。 |
| A-3／R9 | **partial** | `E/README.md:50`、`E/bundle/b5-effective-bundle.draft.json:51`・`:59`、`tools/pegasus/p3_s4_loop_pegasus.sh:203`・`:218`・`:640` | 要求値と不一致時の欠測処置は明記された。しかし Python hash の保存先は **compute-result.json** で、指定された prebuild receipt にはない。**影響:** 文書どおりの照合では Python 適合を確認できず、誤った欠測化または確認漏れになる。 |
| A-4／R10 | **closed** | `E/README.md:89`、`E/bundle/b5-effective-bundle.draft.json:161`、`T:382`・`:395` | fitness・anomalies・median・反復数／列・CV・rounds・settled・abort・LLC・IPC の欠測表示変更を列挙。実装の変更範囲と一致する。 |
| A-5／R11 | **partial** | `E/README.md:168`・`:185`、`E/bundle/cost-model.txt:1`・`:13` | session 費用の整数秒切り上げは明記され、元の指摘は解消。ただし README の **36.6倍**は、原値 `2238804 / 61261 = 36.545338…` を直接小数1桁へ丸めた **36.5倍**と異なる。**影響:** 表示倍率だけの小差で、40倍推奨・秒数上限は変わらない。 |
| B-1／R1 | **closed** | `T:422`・`:445`・`:455`・`:469`・`:483`、`orchestrator/tests/test_b5_llm_round.py:192`・`:223`・`:240` | 版の異常は `version_notes` へ分離。model 欠落・混在・不一致、role 不一致、壊れた入力は引き続き false。MB9 は新 test の true／空 reasons の assertion に到達する。 |
| B-2／R2 | **partial** | `E/bundle/b5-effective-bundle.draft.json:141`、親 template `:26`・`:38`、`D:702`・`:704`・`:757` | A-1 と同じ。最終 critic の問題は解消したが、「every critic mismatch」が timeout 終了になるという断定は強い。**影響:** 欠測結果は維持されるが終了理由が不一致になる。 |
| B-3／R4 | **closed** | `E/bundle/b5-effective-bundle.draft.json:18`・`:220`・`:227`、`E/README.md:215` | 承認対象を land commit と限定された発効 commit に固定。実装等31件・束内12件の hash が一致。draft 自身の列挙なし、束内 data file の漏れなし。 |
| B-4／R5 | **closed** | `orchestrator/tests/test_ccbench_spawn_sites.py:2850`、`orchestrator/tests/test_b5_contrast_launch.py:376` | spawn-sites file は base `8fd2a2f5c` と **bytes 一致**。新設構文目録検査だけが除去され、launcher の機能検査は保持されている。 |
| B-5／R7 | **closed** | `E/README.md:159`・`:169`・`:181`・`:186` | 780 s／機会の仮定、2,700 s 近くまで待つ場合を覆わないこと、旧 walltime で打ち切られた job の Elapse は増えることを明記。無条件の最大値・消費不変という主張は解消。 |
| B-6／R8 | **closed** | `E/bundle/b5-effective-bundle.draft.json:193`、`E/README.md:151`、`D:607`・`:650`・`:667` | 初回 attempt の skip と retry を区別。前者は B が増えず、後者は `submitted_once` により保持されるという実装と一致。 |
| B-7／R6 | **closed** | `orchestrator/tests/test_b5_contrast_launch.py:307`・`:329`・`:335`・`:348` | LLM本数・順序頻度・先後均衡を各1回に整理。検査条件の削減はない。MA5→coordinates、MA6/7→six_orders_twice、MA8→stage_job_counts の静的到達を確認。 |

R2 の残件は、具体的には次の経路です。allocation 残時間が2,000秒なら、1,800秒以上を要求する `_allocation_available()` を通って request を公開できます。その後 critic の model 不一致で親が何も公開しなくても、約200秒後には `_handshake()` が `allocation-exhausted` を返せます。2,700秒の timeout より先です。修正は「通常は proposal-wait-timeout、allocation が先に不足すれば allocation-exhausted。いずれも score 欠測」と文書を限定すれば足り、新 gate は不要です。

critic・planner・coder に別々の2,700秒を与える記述はありません。親 template `:25` は request 公開から同じ期限に含めています。試走の10〜13分／巡は critic を含む観測値です（`output/insights/2026-09-20/t2797-b5-contrast/README.md:199`）。この時間で必ず完走するという保証への拡張は認めませんでした。

R9 は値そのものの誤りではありません。試走 job `13638.nqsv` の prebuild receipt の gcc/g++・cmake は要求値と一致し、Python hash も試走の `pilot/evidence/llm/compute-result.json:1` と一致しました。**照合元を「compiler/cmake は prebuild receipt、Python は同 job の compute-result.json」と分ける文書修正**が必要です。

再計算結果は以下のとおりです。

- `files_sha256` **31/31一致**、`bundle_files_sha256` **12/12一致**。`T` の hash は fix 後の `cc86667fa38e65d0abc9caa3c37d98367dcd19ffabfc8ff1ed09882a0c691731`。
- session 費用は write-heavy **510秒**、balanced **277〜727秒**、read-heavy **817〜1,007秒**、stress **2,457秒**。これから README `:174`〜`:177` の各 job 費用をすべて再現。
- 総費用は **1,298,964／1,677,204／2,238,804秒**、それぞれ **360.8233／465.89／621.89時間**。倍率は **21.203767／27.378006／36.545339倍**。
- 試走4 job の Elapse 合計 **61,261秒**、40倍 **2,450,440秒＝680.6778時間**、論理 session 数 **1,773**、k=3 の予約容量 **1,954.1625 node時間**は一致。k=2／3／4.06 の W・W_stock も Decimal 切り上げで一致。

攻撃が成立しなかった点も明記します。版の検査を外したことで model 照合まで弱くなる経路、新 test が実物を呼ばない疑い、schedule 整理による検査の弱化、hash の更新漏れ・束内列挙漏れ、最終 critic の不一致を残したまま score が成立する旧経路には、成立する反例を認めませんでした。fix による新しい driver gate・report 検査・台帳 field もありません。`version_notes` は裁定どおりの role 記録であり、台帳の追加条件ではありません。

## 総括

- **NO-GO。** 残件は文書修正で閉じられます。追加の実装 gate は不要です。
- **partial: A-1 / B-2** — allocation 不足による終了を除外して、必ず handshake timeout と断定している。
- **partial: A-3** — Python hash の照合元が誤っている。
- **partial: A-5** — 総費用倍率の表示に二段階丸め相当の小差が残る。上限判断への影響なし。
- **regressed: なし。**
- 変異の検出可能性は静的確認まで。fix 後のテスト成功・変異 KILLED は本レビューでは主張しません。