## 総括

**NO-GO。** 静的再レビューでは、再試行後の report 集計と、429 後の親の再開に成果物を変える欠陥が残る。生死確認の 3 系列も未実施である。  
`focus-3.log` は **1594 passed / 6 skipped（36.85 秒）**。これは実 job と評価 1 回の成功を示さない。作業ツリーは `git status --short` で clean だった。以下の行番号は現作業ツリーを指す。

## 対応表

| 項目 | 判定 | 根拠 |
|---|---|---|
| F1／R1-1／R2-1 | closed | launcher の直下 field と driver の照合が一致する（`tools/pegasus/silo_policy_contrast_launch.py:186-189`、`orchestrator/campaign/p3_s4_loop_policy.py:774-802`）。 |
| F2／R1-2／R2-2 | partial | 終了関数と driver・launcher の呼出しはある（`silo_policy_contrast.py:150-191`、`p3_s4_loop_policy.py:881`、`silo_policy_contrast_launch.py:159-162,198-202`）。同時呼出しと再試行後の報告には下記所見が残る。 |
| F3／R1-3 | closed | 完成 proposal の preview、veto 後の reject 記録、job 側の再照合がある（`tools/silo_policy_contrast_round.py:157-180`、`p3_s4_loop_policy.py:190-202,835-865,1001-1025`）。 |
| F4／R1-4／R2-3 | partial | 親は今回増えた `proposed/rejected` だけを見る（`silo_policy_contrast_parent.py:62-71`）。429 が終端記録後に起きた再開は下記所見。 |
| F5／R1-5／R2-4 | closed | fixture は `ContrastLedger.create/append` を使う（`orchestrator/tests/test_silo_policy_contrast_round.py:10-19`、`test_silo_policy_contrast.py:6-23`）。焦点走も緑。 |
| F6／R1-6 | closed | seed 番号を slot index から作り、既存履歴行を飛ばす（`p3_s4_loop_policy.py:805-821`）。 |
| F7／R1-7 | closed | job 1 完了時の stock 不成立で終了し、`next_unit` は終了を読む（`silo_policy_contrast.py:166-170,200-205`）。 |
| F8／R1-8 | partial | score の variant・digest を照合する（`silo_policy_contrast_report.py:74-79`）。再試行の旧行も照合対象になる。 |
| F9／R2-5・6 | closed | A と未終端 slot は台帳 state、番号は共通関数を使う（`silo_policy_contrast.py:96-147`、`silo_policy_contrast_launch.py:67-75`、`p3_s4_loop_policy.py:1012-1018`）。 |
| F10／R2-7 | closed／refuted | driver は生成器の `tagged` を import する（`p3_s4_loop_policy.py:36,85`）。台帳を独立させる部分は裁定どおり refuted。 |
| F11／R2-8 の報告項目 | closed | 拒否の subtype・rule を記録し、arm 別に集計する（`silo_policy_contrast_round.py:169-175`、`silo_policy_contrast_launch.py:108-113`、`silo_policy_contrast_report.py:122-141,215-220`）。 |
| F12 | closed | 演算子を先に一様選択し、比較だけ operand 型を選ぶ（`silo_policy_contrast_generators.py:76-96`）。 |
| F13 | closed | seed に digest を作り、critic 材料に性能・品質を含める（`p3_s4_loop_policy.py:729-735`、`silo_policy_contrast_round.py:48-59`）。 |
| F14 | partial | 親の指示は保存済み role 出力の再利用を求める（`silo_policy_contrast_parent.md:7-11`）。終端記録済みの再開は安全でない。 |
| F15 | partial | 親は `modelUsage` を読むが、`models` を付けるのは outage・empty・role-failure だけ（`silo_policy_contrast_parent.py:49-76`）。通常の proposed/rejected には付かない。 |
| F16 | closed | digest 不一致を `slot-start` より前に拒否する（`p3_s4_loop_policy.py:760-766,855-857`、`orchestrator/tests/test_p3_s4_loop_policy.py:66`）。 |
| G1 | closed | 非対照 preview の拒否文言を復元（`p3_s4_loop_policy.py:133-137`）。 |
| G2 | closed | 焦点走は緑。該当テストは `test_p3_s4_loop_policy.py:66`。 |
| G3 | closed | `run_campaign` の呼出しは stock 関数と候補関数の 2 箇所（`p3_s4_loop_policy.py:446,493`）。静的 10 µs は前者を呼ぶ（同`:711-715`）。既存 stock は `fixed10=False` の経路（同`:424-455`）。 |
| R1 の M1〜M14 | partial | M5 は F16、M12〜M14 の fixture は F5 で改善。焦点走は緑だが、生死確認と変異実行の結果は無い（`focus-3.log:51`）。 |
| R2-8 の実測・発効束 | partial | 草稿は生死確認と Elapse 実測を発効前に要求する（`docs/silo-policy-generator-contrast-preregistration.md:378-381`）。提示物にその実測は無い。 |
| R2-9 | partial | 全焦点走は 36.85 秒（`focus-3.log:51`）。新規テストだけの所要は分からない。 |

## 新しい所見

1. **must-fix — 成功した再試行を report が欠測・不適合にする。** `silo_policy_contrast_report.py:58-63,74-81,108-114` は全 `slot-result` を数える。stock の失敗→成功は 2 行となり `stock_ok` が偽、score は 6 行となり欠測、参照も 6 行なら 5 件判定を失う。**影響:** 許された機械故障 retry が比較値や floor を失わせる。**最小の直し:** 論理 slot ごとに最終 attempt だけを射影し、その行で identity と件数を検査する。

2. **must-fix — 429 後に同じ A の終端が重複または欠落し得る。** round は `opportunity-end` を書いた後に戻る（`silo_policy_contrast_round.py:127-133,173-181`）。親は Claude 終了を `outage` と分類すると無条件で同じ a を再実行する（`silo_policy_contrast_parent.py:49-61`）。再開時に既存 auditor prompt があれば `finalize` を再実行する指示もある（`silo_policy_contrast_parent.md:8-9`）。逆に `prepare` が既終端を拒否すると親は role failure を重ねる（`silo_policy_contrast_round.py:82-87`、`silo_policy_contrast_parent.py:72-77`）。**影響:** A の二重計上、または有効な提案を持つ系列の欠測。**最小の直し:** 親が再起動前に台帳の確定終端を確認して返し、round の `check/finalize` も既存終端を冪等に扱う。

3. **should-fix — 提案成立時の model ID が台帳に残らない。** 親は `modelUsage` を抽出するが（`silo_policy_contrast_parent.py:49-54`）、round が作る `proposed/rejected` には `models` が無い（`silo_policy_contrast_round.py:131-132,173-180`）。**影響:** 草稿 §5.5 のモデル不一致を主要候補について後から監査できない。**最小の直し:** 親の成功時にその起動の model ID を確定終端へ結び付ける。

4. **should-fix — stock 不成立でも job 1 の seed 測定を続ける。** driver は 3 slot を順に測り終えてから終了判定する（`p3_s4_loop_policy.py:845-881`）。終了関数も 3 件の結果を要求する（`silo_policy_contrast.py:166-170`）。**影響:** stock が最初に不成立でも seed 2 session の費用を使い、生死確認ではその後の親・評価へ進めない。**最小の直し:** stock 結果の直後に不成立を確定し、残る seed を起動しない。

5. **should-fix — この worktree を checkout に指定した job は body で停止する。** launcher は `submit_checkout` を PBS に渡す（`silo_policy_contrast_launch.py:130-155`）が、body は `.claude/worktrees` 内を拒否する（`p3_s4_loop_pegasus.sh:287-290`）。**影響:** LLM×C++、LLM×IR、random×IR の job 1 と評価 1 の生死確認を、この checkout のままでは通せない。**最小の直し:** 実行用の許可された通常 checkout を指定し、固定 HEAD と必要な実装をそこに揃える。静的 10 µs の stock 既存経路の挙動変更、および preview で auditor veto が弱まる経路は、今回読んだ分岐では確認できなかった。