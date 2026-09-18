## 判定と確認範囲

**NO-GO：親の終端待機・判定に must-fix 1件。pilot 自体に、静的に確定できる次の停止段は見つかりませんでした。**

指定資料を読み、統合後3ファイルの SHA-256 が author 報告と一致することを確認しました。pytest・build・PBS 投入・ファイル変更は実施していません。

以下、`pilot`＝`tools/pegasus/mocc_trace_pilot.sh`、`contract`＝`orchestrator/tests/test_mocc_trace_job_contract.py`。行番号は統合後の現物です。

## must-fix

**MF1 — job-result 到着後、終端 accounting を待つ手順がありません。**

- **根拠:** `tools/dev_wave_wait.py:2028–2033,2068–2069` は非空 done file だけで戻ります。pilot は `3554–3569` で job-result を生成した後、`3576–3578` で worktree を削除します。一方、[judge_liveness.py](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2780-mocc-pilot-discriminator/judge_liveness.py:34) の `34–39` は `pbs-job.stderr` の存在だけを確認し、初期状態を `"terminal"` にしています。
- **放置時の影響:** 正常 job でも、done 到着から PBS stderr 配送までの間に判定すると `success=false, state="terminal"` になります。stderr が終了前から存在する環境では、逆に cleanup 前の状態を完走と認めます。
- **是正案:** done による待機終了後も、当該 request の終端 accounting が確認できるまで親が待ち、その後に failure・receipt を評価してください。待機中は `not-terminal`、期限到達は「未完了」とする。既存の accounting 判定を利用すればよく、pilot への新 gate は不要です。

裁定 §4 の「stderr が存在」という逐語条件は実装されています。ただし、その括弧書きの「終端」を、現状の待機との組合せでは確定できません。

## should

**S1 — 投入直後の一度だけの `ls` は、staging directory 名の実測にならない場合があります。**

- **根拠:** [launch-liveness.sh](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2780-mocc-pilot-discriminator/launch-liveness.sh:18) は qsub 後に一度だけ列挙します。directory を作るのは実行開始後の pilot:`64,76–79` です。
- **放置時の影響:** queue 待ちなら `staging-ls.txt` は不在エラーまたは対象を含まない一覧になり、「実測した directory を待った」という記録が成立しません。
- **是正案:** 起動後に対象 directory の出現を確認して一覧を取り直す。待機先の予定形は `job-staging/0:<N>.nqsv/job-result.json` で整合しています。queue timeout 時には未実測と記録してください。

**S2 — 焦点走を「login 実走完了」と記録しないでください。**

- **根拠:** [focus-1.log](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2780-mocc-pilot-discriminator/focus-1.log:2) の `2–14` は local の `scope-outcome-cap-oom` 後、`5893.nqsv` への dispatch と child rc=0 を記録しています。`56` は **1591 passed / 3 skipped、114.92秒**です。
- **放置時の影響:** insight の実行場所・費用・成功経路の主張が一次ログと異なります。
- **是正案:** 「login で開始、local が上限到達、compute へ dispatch して焦点走成功」と記録する。これは受入全走でも、MOCC pilot の生死確認でもありません。

**S3 — M8 の赤を、登録した field assertion の検出実績として扱えません。**

- **根拠:** `contract:4838` の正常終了 assertion が、patch binding を見る `4843` より先です。pilot:`3521–3539` が欠落 binding を拒否するため、author 報告:`61` の説明は現物と一致します。
- **放置時の影響:** 「receipt field assertion が M8 を殺した」という insight の主張が成立しません。
- **是正案:** 正式 harness では receipt writer の出力を後段拒否と分けて観測するか、検出箇所を job-result writer と明記し、登録理由との差を記録してください。赤にするために本番検査を削る必要はありません。

## nit

**N1 — 新 marker の一意性検査が三重です。削除推奨1件。**

- **根拠:** `contract:1522–1524,1611–1613` が既に一意性・順序を検査し、`2960–2963,4455–4458` に同じ4 marker が重複登録されています。
- **放置時の影響:** 成果物は変わりません。保守箇所だけ増えます。
- **是正案:** 既存二つの tuple に追加した重複8行を削り、新規契約 test の検査を残す。
- **削除しても:** receipt の束縛・生死確認の完走・M1〜M8 の検出条件は変わりません。

**N2 — compute worktree 作成の done は、作成成功を表しません。**

- **根拠:** [mk-compute-worktree.sh](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2780-mocc-pilot-discriminator/mk-compute-worktree.sh:4) の `4,11–17` は `set -u` だけで、add・初期化・lock の非0後も done を書きます。
- **放置時の影響:** 今回確認した HEAD は両 worktree とも `f93281e55c59e8a69fda2fc4295986929e123e2a` で、具体的な誤投入は確認していません。ただし done 単独から準備成功とは言えません。
- **是正案:** 各非0で終了し、成功後だけ done を書く。少なくとも親は既存の各 rc と記録された HEAD を確認してください。

## 実行鎖・manifest・receipt の照合

| 論点 | 現物で確認した結果 |
|---|---|
| hydrate | pilot:`1564–1591` は選択した絶対 interpreter を実 hydrate に渡します。hydrate 自体の非0は既存 ERR trap の `shell`。20秒以内の完了は未実測です。 |
| patch → build | `1738–1805` で専用 source を作り、T1943 限定で numstat・check・apply・digest を実行。`1812,1868,2017` の両 build は同じ `BUILD_SOURCE` を使います。 |
| `set -e` | patch の主要失敗は明示捕捉されています。前後の worktree add・build 等は失敗時に既存 ERR trap で停止しますが、今回の変更に起因する必須停止は見つかりません。 |
| verifier | `2348–2358` は T1943 だけ patched `BUILD_SOURCE` を渡します。general は従来どおりです。 |
| witness／manifest | `2131–2135` の witness 環境変数、`2212–2313` の trace／witness manifest は維持。両 manifest は同じ NEW_OID・実 binary SHA・workload を記録します。NEW_OID 単独を patched bytes の識別子とは扱えません。 |
| receipt source | shell argv の `2626` と tuple の `2658` が対応し、`3121` は実際に patch を当てた source を再読します。source 削除は receipt・job-result 作成後です。 |
| 5 artifact | `413–437` の分類・reason、`651–655` の general 専用漏れ検査、`3424–3428` の receipt 登録が揃っています。 |
| 空 stdout | validator:`613–625` は分類の一意性を検査し、非空を要求しません。通常空の stdout でも通ります。 |
| 途中失敗 | writer は `665` で先行しますが、T1943 validator は成功側の `2510–2515`。patch 失敗の exit／EXIT cleanup は validator を呼ばず、途中 artifact による二重の分類失敗は起きません。general の呼出は `3580–3585` です。 |

`judge_liveness.py:41–95` は failure 不在、job-result v2、receipt T1943 v2／completed、receipt digest 鎖、patch／source sidecar／numstat、gates、discriminator digest／conclusion を検査しています。**`artifacts.discriminator_sha256` は pilot:`3430` と一致**します。

gates は pilot:`3410–3437` が文字列で記録し、receipt writer:`3137` も文字列比較です。judge の `int(...)` は実際の `"0"`／`"1"` と整合し、正常出力を拒否しません。

verifier rc=1 は `2358,2365–2416` で捕捉・受理され、receipt:`3137` と judge:`82` も受理します。rc=0 も同様です。**両経路とも正常なら job script は `3587` の exit 0 に到達します。** rc=1 の fixture 被覆は `contract:3580,4881` にありますが、compute 実測とは別です。

## 過剰・削除と不足

削除推奨は N1 の重複 marker 登録だけです。

- **receipt の実 bytes 再照合は残す。** 削ると「適用直後と finalization 時の source が一致した」という束縛が失われます。
- **job-result の5 field 検査は残す。** 削ると binding 欠落 receipt でも job-result を生成でき、M8 の現在の停止箇所も変わります。
- **空 stdout artifact は残す。** 成功証明ではありませんが、check／apply の出力捕捉と裁定済み5 artifact 契約の一部です。
- **v1 拒否 test は残す。** `contract:4936–4950` は digest を再束縛したうえで旧 schema を拒否し、v2「置換」を検査しています。

本題3点の production 配線に欠落は見つかりません。残る不足は、親の終端待機と正式な実測結果です。

## 並行実行・author 報告・fragment

確認終盤の compute worktree は untracked を含む status 出力が空でした。HEAD も統合 commit と一致し、現時点では submit:`254–290` の clean gate を通す状態です。

compute と wave の submodule `git-common-dir` はそれぞれ別の `.../worktrees/<名前>/modules/external/ccbench` でした。pilot の source は job 固有 `/scr/<PBS_JOBID>/ccbench-source`、成果物は compute worktree の job-staging です。提示された分離なら、wave 側受入・checkout 外変異 spec との同一ファイル書込みや submodule worktree 登録の衝突は見つかりません。job-staging は submit の許可 prefix で、判定 source 捕捉も `output` を除外します。

実行5〜20分は見積のままです。queue 待ち・PBS予約60分・親の待機上限6時間を分けて記録してください。

author の未実走列挙は、その担当範囲の報告として妥当です。fixture の patch は fake git と模擬 bytes であり、実 patch／build／同一性 witness の実績ではありません。親の焦点走ログは集計だけなので、個別 witness／consumer の実行有無はこのログ単独では確定できません。

波及否定も整合します。`mocc_trace_pair.py:27,409` は general v4、`mocc_g2_repro_ledger.py:27,601` は歴史的 v3、`test_hooks.py:3180,3338` は `dispatch-required` のままで、今回の変更は不要です。

fragment の骨子は次の範囲で十分です。

- **decisions:** 裁定 §2項8の1件で十分。T1943 v2置換・旧v1非受理・general v4維持・verifier規則不変を記録する。
- **F1027:** 実装と再発検知結果を追記し、hydrate 通過と pipeline 完走を分ける。生死確認前に解消済みとしない。
- **worklog:** 終端確認付き生死確認・正式変異・受入・監査が揃ってから T-2780 を「完了」に置く。
- **insight:** 焦点走の実行場所と M8 の実際の検出箇所を訂正し、source digest を binary 生成元の独立証明とは書かない。

## 総括

**NO-GO — must-fix 1件。** 親の待機を、job-result 到着後の終端 accounting 確認まで接続してください。

**生死確認が finalization まで通る見込み: 不確実。** pilot 内に静的に確定した次の停止段はありません。実 hydrate・patched build・compute finalization の通過は未実測です。

**削除推奨: 1件** — 重複した marker 登録。