pytest・変異 harness は実行していない。Pegasus ログインノード上で、全文読取り、静的経路追跡、および書込みを伴わない Bash probe だけを行った。

1. 深刻度: blocker

- 根拠: `s2-plan.md:76-96,148-154`、`tools/pegasus/submit_t126_qualification.sh:209-224`、`docs/failures.md:388-416,1200-1211`
- 所見: submit 負例は `prologue/attestation/finalize = 1500/0/600` の1点だけで、三比較の一括削除しか殺さない。`prologue` だけを消しても attestation が、attestation だけを消しても prologue が拒否し、finalize は入力が 600 のため未検査である。
- さらに、prologue と finalize の比較を同時に消す変異では、計画の負例は attestation=0 により拒否されたままだが、`1500/600/0` は和 2100 を保って受理される。同様に attestation と finalize を消すと `900/1200/0` が受理される。受理集合を実際に広げる変異が計画 test を通過する。
- 実証区分: 条件式の静的真理値表で実証済み。変異実走は未実施。
- 成果物影響: 二比較の欠落で compensating cap drift が submit・qsub・receipt へ流れるのに、変異台帳が KILL を誤って主張し得る。
- scope: 内。submit の個別 cap 凍結と変異証明は本 wave の中核。

2. 深刻度: blocker

- 根拠: `s2-plan.md:12-24,32,47,140-151`、`tools/pegasus/t126_qualification.sh:453-468,484-493,624-625,696-705`、`orchestrator/tests/test_t126_pegasus_tools.py:3693-3718`
- 所見: job 正例は最初の dependency `git rev-parse HEAD` で止まるため、3 出力と配列 index の対応を一度も観測しない。例えば Python の出力順を walltime/wmax から wmax/walltime へ交換しても、正例は marker 到達、8 負例は出力前拒否、late-failure 負例は status guard で停止し、すべて計画どおりに見える。
- 同じ穴は `WALLTIME_S=${RESERVATION_VALUES[1]}` と `WMAX_S=${RESERVATION_VALUES[0]}` の交換にもある。実運用では scheduler 検査が walltime=29100、wmax=36000 を見るため正しい予約を過剰拒否する。prologue との交換なら cap を 36000 秒へ緩め得る。
- 実証区分: production 経路と計画停止点から静的実証済み。変異実走は未実施。
- 成果物影響: canonical policy でも job が予約検査後に拒否される、または prologue cap が緩み、正例・負例 test はそれを検知しない。
- scope: 内。書換える producer と既存 downstream mapping の結合検査が必要。

3. 深刻度: blocker

- 根拠: `s1-brief.md:49-51`、`s2-plan.md:142-144,193`、`orchestrator/tests/test_t126_pegasus_tools.py:2924-2939,3144-3170`、`tools/pegasus/submit_t126_qualification.sh:162,189,243,286,349`、`tools/pegasus/dispatch_compute.py:389-409,491-498`、`output/insights/2026-07-31_t126-f32-closure-wave/s6-ruling-package.md:131-140`、`docs/worklog.md:1214-1215`
- 所見: 宣言された受入経路は、既知の T-248 により現在赤になる。dispatch は Python 3.10 本体のディレクトリを PATH へ足すだけなので、孫の bare `python3` は計算ノード既定 3.9 へ戻る。既存実測では `_run_submit` 系の M8b が目的 gate より後で失敗済みである。
- 新 submit 負例は単純な JSON 条件で早期拒否されるため、3.9 上でも単独では通り得る。一方、exact-policy 正例群は後段で既知の赤になるので、焦点 node の成功を全受入の成功と数えられない。
- 実証区分: 過去の sanctioned dispatch 実測で実証済み。今回は再実行していない。
- 成果物影響: T-247 の guard が正しくても、brief が要求する計算ノード全走を緑として確定できず、受入記録が偽緑または既知赤の握り潰しになる。
- scope: 実装修正は scope 外の T-248、しかし T-247 の受入前提として scope 内。T-248 を先行させるか、blocked と記録する必要がある。

4. 深刻度: must-fix

- 根拠: `s2-plan.md:133-142,150-151`、`tools/pegasus/t126_qualification.sh:15-28,315-444,470-493`、`orchestrator/tests/test_t126_pegasus_tools.py:790-840,3693-3718`、`docs/failures.md:730-755`
- 所見: late-failure fixture の wrapper 経路が不足している。Python wrapper は版数 probe、monotonic、receipt/EARLY_ID を委譲し、予約 parser の一回だけを「3行後 rc=73」にし、その後の policy parser は再び委譲しなければならない。git wrapper も source archive と tree 照合を委譲し、dependency の `rev-parse HEAD` だけで marker を作る必要がある。
- injection marker の一意性・呼出し回数、marker の実作成可能性、各 run 固有の scratch/marker path も assert すべきである。曖昧な引数判定や `#!/usr/bin/env python3` wrapper は自己再帰や前段停止を作る。
- `submission.py:73-81` の symlink 拒否は `_run_bound_job_terminal` 経路では呼ばれないため、plan の regular wrapper の理由付けもこの job test には適用されない。
- 実証区分: 経路は静的確認済み。未実装 fixture の実挙動は未実証。
- 成果物影響: 目的 parser へ到達しない rc を「producer status を拒否した」と誤帰属し、late-failure test が偽 KILL になる。
- scope: 内。新設 subprocess test の信頼性。

5. 深刻度: must-fix

- 根拠: `s1-brief.md:15-24,43-47`、`tools/pegasus/submit_t126_qualification.sh:209-220`、`tools/pegasus/t126_qualification.sh:29-54,624-625,696-705`、`docs/failures.md:418-449`
- 所見: 親の局所実測 A/B/C は refute できない。今回、同じ `sed` 範囲を `set -Eeuo pipefail` 下で `eval` し、A=`1500/0/600`、B=prologue 1500、C=`1/2/3` がいずれも rc=0 になることを再現した。`eval` と本体の差や ERR trap はこの局所結論を変えない。
- ただし「長さ guard が常に真」は過大である。JSON 欠損・構文不正・三 key の出力途中例外では 3 行にならず拒否される。正確には「三出力 key が存在する well-formed policy では mismatch の raise が外側へ伝播しない」。
- 「個別 cap 任意」も誤りで、現行 submit は `prologue + attestation + finalize = 2100` の平面だけを受理する。
- 成果物影響の因果も未実証である。job の deadline は policy の `WMAX_S` でなく `WMAX_FIXED_S=29100`、finalize reserve は 600 の hardcode である。policy の walltime/wmax は scheduler 下限検査、prologue だけが cap に直接使われる。C の断片実測だけでは「member kill・finalize reserve 消失」を実証していない。
- 実証区分: A/B/C と Bash status は今回実証。full job の ledger/receipt 影響は未実証。
- 成果物影響: 誤った受理集合と因果を新 D・worklog に残すと、どの drift が試行欠落を起こすかの参照が虚偽になる。
- scope: 内。親 brief と記録の是正対象。修正方針そのものを否定するものではない。

6. 深刻度: nit

- 根拠: `s1-brief.md:8`、`s2-plan.md:62,94`、`tools/pegasus/submit_t126_qualification.sh:162,189,243,349`、`tools/pegasus/t126_qualification.sh:416,453,470,577,605`
- 所見: 全9ブロックとも process-substitution producer の status は失う。通常の mismatch が print 前に起きる他8ブロックでは長さ・値 guard が多くを拒否するが、「必要行を全部出した後の producer failure」は残る。新 late-failure test が保証するのは job reservation reader 1か所だけである。
- 実証区分: Bash 5.1 probe で「3行＋rc73でも readarray rc=0」を実証。各 production block への fault injection は未実施。
- 成果物影響: 新 D が「両 script の producer status を束縛した」と書けば虚偽になり、submit reservation などは complete-output failure を引き続き受理する。
- scope: 構造改修は明示的 scope 外。残存限界の記載だけは scope 内。

7. 深刻度: nit

- 根拠: `orchestrator/tests/test_t126_pegasus_tools.py:1209-1225,1275-1340,1773-1792,3664-3680,704-710,3721-3728,498-519,607-610,3905-3909,5113-5176,5180-5240`
- 所見: plan の変更で必然的に赤になる既存 test は静的には0件である。
  - 本文文字列 assert は上記の freeze/header、policy wiring、submit/job wiring、binding diagnostics。
  - publisher 抽出 helper と既存 mutation anchor は変更範囲外。
  - `bash -n` は heredoc/括弧を壊した場合だけ赤。
  - script hash は fixture commit/live bytes から動的導出され、literal hash 更新は不要。
  - `_run_bound_job_terminal` の既存 caller はすべて `tools/pegasus/t126_qualification.sh:431-435` で予約検査前に止まる。
- したがって `test_reservation_policy_and_job_headers_freeze_wmax_and_walltime` は「壊れるから直接更新が必要」なのではなく、D96 の純増 coverage として更新するだけである。更新を忘れても既存 test は通る。
- 実証区分: 静的予告。pytest は未実施。
- 成果物影響: 既存回帰 test の緑を新 guard の発火証拠に数えると、guard 全削除でも検出できない。
- scope: 内。既存テスト破壊予告と証拠の帰属。

Bash・一時領域については、提案した P1 自体に blocker は見つからなかった。`if ! OUTPUT=$(...)` は assignment の status を捕捉し、ERR trap に依存せず `exit 2` へ正規化する。command substitution と here-string は名前付き一時ファイルを増やさない。submit の既存 staging は `submit_t126_qualification.sh:131-136` の EXIT trap 対象で、job の `/scr` は `docs/pegasus-runbook.md:230-236` によりジョブ終了時削除である。

## 総括

(a) blocker:

1. submit の単一 compensated-drift test が、受理集合を広げる二比較削除変異を検出しない。
2. job 正例が三出力の順序・配列 index 対応を観測せず、runtime cap mapping の変異が生存する。
3. sanctioned 全受入は未解決の T-248 により既知赤で、T-247 単独では宣言した完了条件を満たせない。

(b) 親 brief 自体の誤り:

- A/B/C の局所 rc=0 は正しい。
- 「長さ guard は常に真」「個別 cap は任意」は受理集合の過大表現。
- C の fragment から member kill・finalize reserve 消失まで導く因果は未実証。
- P2 の「8 key 全部」は9番目の term grace を除く限定表現が必要。
- P3 の「和は独立な検出力」は全個別値固定後には数学的に誤り。
- P4 の既存 freeze test 単独では script 境界 test にならない。

(c) 判定: **NO-GO**。P1 の Bash 書換え自体は採用可能だが、上記3 blockerを閉じ、T-248との実行順を確定するまでは、このプランを段5へ渡してはならない。