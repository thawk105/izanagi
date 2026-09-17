## 所見対応表 (所見 → closed / partial / regressed、根拠 file:line)

`integrated-v2.diff` と現物の `git diff` は完全一致。指定13ファイルを静的検査した。

| 所見 | 判定 | 根拠 |
|---|---|---|
| reviewA must-fix 1 | **closed** | `.claude/agents/planner-v4.md:52`、`.claude/agents/coder-v4-autonomous-trigger-gating.md:62` は凍結を8cに限定。planner `:55` は第2世代以降の `critic_feedback` を明記。coder本文に同語は存在しない。 |
| reviewA must-fix 2 | **closed** | `.claude/agents/critic.md:26` は待機コストを「候補仮説」とし、他指標との照合・判断不能時の `uncertainty` を要求。確定帰属を除去している。 |
| reviewA nit 1 | **closed** | `docs/phase3-s4b-runbook.md:52` は変更した4 roleを明記。広すぎるワイルドカードを除去し、`critic-experiment.md` も含む。 |
| reviewA nit 2 | **closed** | `.claude/agents/critic.md:14`、`.claude/agents/critic-experiment.md:40` とも「改訂以降に開始する走行」「以前に開始した走行は当時の版」を明記。 |
| reviewA nit 3 | **partial** | `src/coder-leakproof-context.md:55` の `default_perf()` は残存。指定資料 `ruling.md:24` の明示案には適合するが、同 `:12` の内部関数名禁止に対する例外の明文化は確認できない。実装違反ではなく裁定記録の残件。 |
| reviewB nit 1 | **closed** | planner `:52`、trigger-gating `:62` で「8c 自動 trial では」と限定。手動経路の射影説明を分離した。 |
| reviewB nit 2 | **partial** | 指定資料内に報告文の訂正を確認できない。`output/insights/2026-08-26/t1697-closed-critic-invocation/verbatim/liveness-probe-real-cli.txt:4` に旧SHAが残り、`docs/phase3-b4-reflux-ablation-preregistration.md:158` は記入済み、`:166` のprompt／projection欄は未記入。存在ゼロ・§5全体未記入とは言えない。 |

## 新規所見 (must-fix / nit、成果物影響 1 行)

**新規must-fix／nit、fixによるregressionは検出なし。** 残る2件は裁定・調査報告の表現上のnitで、今回のpayload説明やSHA追随を破損するものではない。

8cの実装では `orchestrator/campaign/p3_autonomous_workload_trial.py:338` がplannerの次世代入力に `critic_feedback` を許可し、`:4216` が第2世代以降に付与する。coderの許可集合 `:341` とpayload構築 `:4253` には同フィールドがない。修正文はこの区別と一致する。

`docs/decisions.md:17162` のD410決定2は、source metricsから再構築する診断4値に加え、uncertainty／reverseのboolとsource generationを運ぶ。plannerの「supervisor が機械射影した診断値」はその要約として整合し、自由文を運ぶという誤記もない。

## 検算した量化語

| 表現 | 検算結果 |
|---|---|
| 「数値指標がすべて null」 | **一致。** `p3_autonomous_workload_trial.py:146` の初期5指標はすべて `None`。`:2013` の射影後もperf側5値・leading側2数値はnull。`contention_level` はdescriptor由来なので、「全フィールドnull」ではない。 |
| 「workloadごとに1回だけ」「世代を跨いで更新しない」 | **一致。** `:4102`〜`:4110` で初期値から射影・deep copyし、`:4116` の世代ループより外側に置く。`:2043`、`:2055`、`:2067` の組立関数は更新済みmetricsを捨て、凍結値を返す。 |
| 「whiteboardだけ」 | **誤った限定は除去済み。** planner `:54`〜`:55` はwhiteboardと第2世代以降のfeedbackを列挙。coderへのfeedback到達は主張していない。 |
| 「毎 iteration」 | **一致。** `docs/phase3-s4b-runbook.md:33`・`:49` が1周ごとの射影を定義。sort `:36`・`:41` が同型を採用し、trigger `:45`・`:47` が継承する。値の固定・最新値への更新という新規規定は加えていない。 |
| 「評価済みの全 workload」 | **限定は適切。** `.claude/agents/critic.md:36` は仮想例であり、未測定workloadへの一般化を明示的に禁止。実測済み全件についての報告ではない。 |
| 「他10本不変」 | **一致。** adapter全14本をHEADとbytes比較し、変更4本・不変10本。統合差分はMarkdown 7本＋adapter 4本＋Python 2本＝13本。 |

SHAは完全長で比較し、4件とも **現物role SHA＝ledger＝adapterの両SHA欄** を確認した。以下は表示のみ短縮。

| role | SHA先頭 | ledger行 | adapter両欄の行 |
|---|---|---|---|
| trigger-gating | `2cc08b30573a` | `review_ledger.py:38` | 同名JSON `:166`・`:185` |
| critic | `fea81c65909a` | `review_ledger.py:40` | 同名JSON `:96`・`:115` |
| critic-experiment | `95718801d7f2` | `review_ledger.py:42` | 同名JSON `:151`・`:170` |
| planner-v4 | `2e69b76d836c` | `review_ledger.py:51` | 同名JSON `:124`・`:143` |

`orchestrator/tests/test_reflux_originless_compatibility.py:707` の3タプルは、new側が対応ledgerと全件一致し、old側もHEADの旧ledgerと全件一致した。4 adapterの埋込みrole本文も現物と一致。変更箇所は本文、両SHA欄、semantic digestに限定される。

pytest・checkerの再実行はしていない。親のchecker rc=0は依頼文による報告として区別した。

## 総括

**GO — must-fix 2件は解消し、量化語・SHA追随も整合。裁定・報告表現のnit 2件はpartialとして残る。**