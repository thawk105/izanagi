**nodes=5 の整合変更は進行可能です。局所lockの恒久採用は現状では未成立で、まず局所実測と不採用材料の記録までに留める判断を推奨します。** plan は head 間の改善と既存 default 使用者との協調喪失を区別できています。ただし、その採用条件を既存運転が満たす根拠は見つかりませんでした。

以下、`plan.md` は指定の親成果物、行番号は変更前です。静的検査のみで、書込み・pytest・compute probe は行っていません。

1. **must / real：同居しない条件を確認できなければ、lock変更を恒久採用しない。**
   対象：`brief.md:4,10`、`plan.md:9,70,72`、`docs/pegasus-runbook.md:45–58`、`orchestrator/campaign/lock.py:24–54`。

   runbook は `Exclusive submit = OFF`、scheduler による専有保証なし、per-job cgroup 境界なしと明記しています。「48 CPU が割り当てられた」「開始時に競合processがなかった」だけでは、実行中の非同居条件になりません。

   具体的反例は、同一user・同一nodeで、候補headが `/scr/.../bench.lock`、既存default使用者が `~/.izanagi/bench.lock` を同時取得する場合です。既存A-1経路も `paper_story_a1_paired.py:7178,7428` で `run_campaign` を使用し、確認したlauncher／driverにはlock上書きがありません。環境未指定時はdefault側へ入ります。

   `pipeline.py:2399–2405` の競合process検査も代替になりません。異なるlockを取得した双方が、相手のベンチ起動前に検査を通過する反例があります。

   **成果物影響：** 新insightへ「候補head同士は改善」「defaultとの協調は消失」を別々に記録すること。対象運転の全期間について非同居を裏付けられない場合、nodes=5のみlandし、lock変更は不採用とする。全launcher改修や新gateへの拡大は `brief.md:7` に反します。「共有homeへ戻さない」を、不採用時にも候補を出荷する義務と解釈してはいけません。

2. **must / real：compute probe表に候補対defaultの同node交差対照が欠落。**
   対象：`plan.md:64–68`。

   planの旧home対照は**別node間**です。これは直列化の検証には役立ちますが、失われる同node協調を測っていません。最小matrixを次で閉じてください。

   | 保持側 → 挑戦側 | 場所 | 観測条件 |
   |---|---|---|
   | 候補 → 候補 | 同node、別process・別scratch | 保持中 `BenchBusy`、解放後成功 |
   | 候補 → 候補 | 別node | 保持中成功 |
   | default → default | 同node／別node | 保持中の拒否を対照として確認 |
   | 候補 → default | 同node | 同時取得できるかを直接確認 |
   | default → 候補 | 同node | 逆方向も確認 |

   default側では `IZANAGI_BENCH_LOCK` を除去し、同じ実HOMEを使い、`bench_lock(path=None, blocking=False)` を呼ぶ必要があります。候補側の環境が漏れると偽の排他成功になります。保持完了通知→挑戦結果→解放の順で同期し、環境文字列・所要時間だけを証拠にしないこと。

   **成果物影響：** この交差対照なしでは、採否判断に必要な回帰の実測が欠けます。

3. **should / real：実job bodyの継承確認とlock配置変異の帰属を具体化する。**
   対象：`plan.md:68,82–85`、`tools/pegasus/paper_story_a2_certification.sh:348–368`、`orchestrator/tests/test_paper_story_a2_job_contract.py:805–819`。

   probe自身が候補pathを設定する試験は、job bodyのexport削除・job固有path化を検出しません。また既存harnessはmkdir/cpをstubし、後段失敗を許すため、現状のままでは `run-workload` 呼出し到達を保証しません。

   最小案は、**実job bodyを実行し、選択されるPython wrapperが最後の `run-workload` 呼出しだけを捕捉する**方法です。他の呼出しは実interpreterへ転送し、その子processが継承環境のまま実 `default_lock_path()`／`bench_lock()` を使用します。外部保持processに対して拒否→解放後成功を確認し、A-2/A-6双方を通します。wrapper自身はlock環境を設定しません。

   2ノード予約で5ノードpolicyの実body前段を実条件のまま通すことはできません。継承だけのharnessではnodefile等のstub範囲を明記し、2ノードの実filesystem probeと証拠を分けるか、実条件の確認には短い5ノード予約を使います。性能workload全走は不要です。

   **成果物影響：** export削除・後置・`$scratch/bench.lock`変異を、このbody由来の試験へ帰属させること。harness結果を実scheduler予約や正式認証成功として記録しないこと。

4. **should / realだがplanで対処済み：nodes=5化による既存負例の手前mask。**
   対象：`paper_story_a2_certification.py:3664`、`test_paper_story_a2_certification.py:4908,4930,4969,4991,5223,5518`、`test_paper_story_a2_job_contract.py:754,1012`。

   host検証が先行するため、planの6呼出しへの兄弟4host追加は必要です。hostname固定も併用し、pin理由、staged verifierのcause/events、source-role predicate呼出しまで従来どおり到達させます。共通fixtureをnodes=1へ戻す修正は不可です。

   **成果物影響：** 単なる例外発生・非zero終了で受入せず、既存理由・観測assertionを維持すること。planの閉包に、この点の新たな漏れは確認しませんでした。

**refuted候補とscope確認**

- **「workerも局所head lockへ統一すべき」：今回の修正要求としてはrefuted。**
  `verify_fanout_worker.py:534–544` のtask固有lockは既存挙動です。全node排他の証拠にはなりませんが、今回のhead変更による新規回帰と混同せず、worker改修へ広げない判断は妥当です。
- **「nodes変異が5化で無効になる」：refuted。**
  `test_paper_story_a2_certification.py:3270` は `"2"` へ変異するため、5化後も負例です。
- **「`:5394` のrun_workload呼出しが閉包から漏れた」：refuted。**
  既に `verify_fanout_hosts=verify_hosts` とhostname固定があります。
- **nit：`test_p1_a2_default_policy_bytes_and_protocol_are_unchanged`（`:1864`）は改名候補。**
  policy bytesは変更しprotocolは維持するため、名称も分けると意図が明確です。成果物の受理挙動への影響はありません。

なお、policy SHA再計算とtracked参照検索をまとめた読取り専用コマンドは、PreToolUse hookがjob bodyパスをdispatch-required実行体と判定して拒否しました。したがって、plan記載の新SHA・全tracked hitの独立再確認は未完了です。実行承認は求めていません。

## 総括

**nodes=5はplanのpin・fixture閉包に沿って進行可能。局所lockは、交差対照とbody由来の継承確認を追加して実測し、非同居条件を立証できなければ不採用材料として残す。** head間probe成功を、default使用者・兄弟workerを含む同node排他の成立へ一般化してはいけません。
