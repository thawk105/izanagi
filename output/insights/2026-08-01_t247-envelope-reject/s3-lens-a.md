結論は **NO-GO**。プランは submit/job の表面だけを狭め、実際の cap 消費元と公開 consumer を受理集合の外に残しています。

受理層は 4 分類・6 実効点です。(1) submit script、(2) job script、(3) `contract.py`→driver の実運用 timing、(4) prologue identity、(5) collector/public verifier、(6) テスト。プランが変更対象にしたのは (1)(2)(6) の一部だけです。

## 所見

1 / blocker / `orchestrator/qualification/contract.py:225-244`、`orchestrator/qualification/submission.py:161-167`、`orchestrator/qualification/t126_driver.py:563-568,683-690,766-773,1109-1131`、`s2-plan.md:111,127`

実際の member/gap/attestation/finalize は予約 JSON ではなく `t126_control_v1.json` の `timing` から消費されます。しかし `validate_protocol` は prologue/attestation/finalize を個別固定せず、正数かつ総和 29100 だけを見ます。例えば prologue=900、attestation=1199、finalize=1 は全条件を通り、予約 JSON を canonical のままにすれば計画後の両 script も通ります。

影響: 通常の submit→job 経路で attestation/finalize の実運用値が変わるため、「個別 cap を固定した」という成果物の timing 値と受理集合が成立しません。

Scope: 内。ユーザーが明示した consumer 層であり、`contract.py` は必読対象です。実証: 条件式と和 `900+16×900+7×1800+1199+1=29100` による静的証明。pytest 未実行。

2 / blocker / `orchestrator/qualification/identity.py:112-167`、`orchestrator/qualification/t126_driver.py:800-843,1277-1284`、`orchestrator/qualification/collector.py:1439-1518`、`tools/pegasus/collect_t126_qualification.py:32-45`、`s2-plan.md:127`

consumer は予約 policy の値を検証せず、「live mapping が記録 commit の JSON mapping と同じか」と blob hash だけを検証します。coherent に commit された drift policy は consumer の予約検査を通り、計画後の submit/job だけが拒否します。`contract.py` の identity path 登録は意味論検査の代替ではありません。

影響: 旧版・別 producer の成果物を public verifier が valid とし得る一方、新 submit/job は同じ policy を拒否し、producer と consumer の受理集合が分裂します。

Scope: 内。プランから漏れたのは operational contract、prologue consumer、collector/public consumer の3点です。実証: semantic predicate が存在しないことは静的に確認。coherent drift の full public receipt 実行は未実証。

3 / blocker / `tools/pegasus/submit_t126_qualification.sh:209-220`、`s1-brief.md:16-17,47`、`s2-plan.md:148-154`、`orchestrator/tests/test_t126_pegasus_tools.py:1209-1225`

現行 submit の受理集合は「個別 cap 任意」ではありません。member=900、gap=1800 の下で、`prologue+attestation+finalize=2100` という平面です。計画の負例 `(1500,0,600)` はその一方向しか撃ちません。実装が prologue 比較だけを追加してもこのテストは緑ですが、`(900,1199,1)` は総和を保ったまま受理されます。静的 freeze test は production guard を通りません。

影響: attestation/finalize の比較が欠落した実装でも D96 境界テストが偽緑となり、宣言した一点受理集合より広い集合が残ります。

Scope: 内。実証: 上記2ベクトルと既存条件による静的反例。少なくとも独立な compensated drift 2方向、できれば各 pair の表駆動負例が必要です。

4 / must-fix / `tools/pegasus/submit_t126_qualification.sh:189-227`、`tools/pegasus/t126_qualification.sh:453-465`、`s1-brief.md:21-24`、`s2-plan.md:51-55,93-96`

submit 側は同じ `readarray < <(producer)` を残すため、target-aware wrapper が正常な3行を出して rc=73 で終わると producer status を捨て、canonical 値として通過します。job 側だけは計画後に拒否します。「L453 の1件のみ」は print-before-raise に狭く定義すれば正しいものの、producer status 切断という defect family では submit L189 も該当します。

影響: 同じ reservation reader failure を job は拒否し submit は受理するため、両 script の failure 受理集合が一致しません。

Scope: 内。対象 reservation block 自体です。実証: Bash の status 切断は静的に確定。実環境での late failure 発生は未実証。

5 / must-fix / `tools/pegasus/submit_t126_qualification.sh:191-198`、`tools/pegasus/t126_qualification.sh:453-462`、`s2-plan.md:27-32,70,133-138`

submit は重複 key を `no_dups` で拒否しますが、job は通常の `json.load` なので last-wins です。プランは job に duplicate hook を指定せず、dict override fixture も重複 JSON を生成できません。最終出現値だけ canonical な重複 policy は job/consumer が受理し submit が拒否します。

影響: 「job/submit を同じ8 keyへ揃えた」という参照が全 JSON 受理集合では偽になり、旧 submit・別経路に対する job 防壁が緩いままです。

Scope: duplicate hardening のコード追加は現裁定の scope 外候補。ただし非対称性を新 D に明記することは scope 内です。現行差は実証、最終 patch が hook を追加しないことは未実証。

6 / must-fix / `s1-brief.md:15-20,43-47`、`tools/pegasus/t126_qualification.sh:29-30,152,624-625,696-700`、`tools/pegasus/submit_t126_qualification.sh:144-159`

A/B/C は明記どおり fragment の結果で、full script の受理実測ではありません。特に C の policy `wmax=2` は job deadline にならず、deadline と job-result は `WMAX_FIXED_S=29100` です。policy の Wmax は qstat の下限比較にしか使われません。prologue=3 は member 実行前の prologue cap で拒否され得ます。また C は現行 submit の拒否集合です。

影響: 「wmax=2でmember kill→finalize消失」という成果物因果が成立せず、修正の脅威モデルと期待失敗地点が誤ります。

Scope: 親 brief 修正として内。固定 deadline の反証は実証。full script でどこまで到達するかは未実証。

7 / must-fix / `s1-brief.md:43-46`、`tools/pegasus/submit_t126_qualification.sh:584-600`、`orchestrator/qualification/collector.py:1124-1157,1214-1235,1414-1435`

qsub 後には series-global ledger が `bind_submitted` 済みで、collector は attempt 不在を `_recover_pre_attempt` で回収し、`prepare_outcome`→`finalize_outcome` を記録します。したがって hard kill が直ちに「attempt ledger の試行欠落」を作る、とはいえません。また submit の和・Wmax・walltime gate と identity hash gate は存在するため、「どの gate も検証していない」も過大です。欠けているのは個別 cap の意味論検査です。

影響: DW-G05 が誤った ledger 欠損と検証ゼロを成果物影響として記録し、実際の影響である unauthorized cap と consumer semantic gap を隠します。

Scope: 内。回収・ledger 記録経路は実証。運用上 collector が必ず起動されるかは未実証。

8 / nit / `orchestrator/qualification/t126_reservation_policy_v1.json:2-11`、`docs/decisions.md:4910-4925`、`tools/pegasus/t126_qualification.sh:53`、`orchestrator/qualification/t126_driver.py:568,1103`、`s2-plan.md:70,120`

D107 の reservation policy は9設定ですが、計画対象は8設定だけです。`t126_qualification_member_term_grace_s` は両 shell から未参照で、実際の driver は control protocol の値を使います。予約側の値は orphan です。プランはこれを scope 外と明記している点は正しいものの、「予約 envelope 全体」「同じ全 key」とは書けません。

影響: 新 D の射程を8-field projectionと限定しないと、term-grace を検証済みと誤参照する成果物・レビューが生じます。

Scope: コード修正は外、射程記述は内。実証済み。

9 / nit / `s1-brief.md:24,29-37`、`orchestrator/tests/test_t126_pegasus_tools.py:1209-1325,2689-2785,5116-5177`

親の「対象4 file の current sha256/blob literal pin 0件」と「両 mismatch 診断を期待する test 0件」は、hidden/binary・全現行 worktree を含む拡張走査でも反例がありませんでした。既存参照は identity の動的導出、path wiring、fixture commit の動的 hash です。ただし exact-hash 検索だけでは off-repo 成果物、変換済み digest、履歴上の pin までは証明しません。

影響: 現時点で再発行対象は見つかりませんが、親の「0件」は current repository/worktree に射程を限定しないと外部台帳まで証明した表現になります。

Scope: 内。repo 内 literal pin 0件は実証、off-repo・全履歴は未実証。

規律2については、プラン上は既存の job 3比較・配列長と submit の member/gap/総和/Wmax/walltime 条件をすべて残しており、明示的な緩和は見つかりません。ただし patch は未実装なので最終確認は未実証です。

## 総括

(a) blocker は次の3件です。

- #1: 実運用 cap の正本 `t126_control_v1.json` が依然として総和だけで通る。
- #2: identity/collector/public verifier が予約 policy の意味論を検証しない。
- #3: submit 境界テストが compensated drift の一方向だけで、欠落 guardを偽緑にできる。

(b) 親 brief 自体の誤りは、受理集合を「個別 cap 任意」としたこと、P2 の「8 key 全部」、P3 の「和は現時点でも独立」、P4 の静的 test 単独同定、fragment C から固定 deadline への誤一般化、DW-G05 の ledger 欠損・無検証表現です。P4とP3はプランが一部訂正しましたが、consumer とテスト基底の不足は残っています。literal pin 0件と拒否 test 0件は反証できませんでした。

(c) **NO-GO**。`contract.py` と予約 policy の関係を受理契約へ入れ、public consumer 経路を境界テストに含め、submit の compensated drift を独立な複数方向で固定するまで採用不可です。pytest は実行しておらず、所見は静的検査のみです。