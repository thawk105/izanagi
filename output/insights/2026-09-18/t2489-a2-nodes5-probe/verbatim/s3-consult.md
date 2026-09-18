**条件付き go。** 1 key 変更による確実な実行不能は見つかりませんでした。ただし、投入コマンド、費用上限、同値性判定、時間見積りは修正が必要です。静的検査のみで、pytest・投入・実機確認は行っていません。

以下、`pipeline.py`・`lock.py`・`verify_fanout_worker.py`・`paper_story_a2_certification.py` は `orchestrator/campaign/` 配下、投入 script・job body は `tools/pegasus/` 配下を指します。

1. **must-fix — 記載された投入コマンドだけでは実行できない。**

   `--attempt-id` に加え、`--ccbench-root`、`--dependency-prefix-source`、`--third-party-source-root` が必須です。値は空で初期化され、欠落すると投入前に exit 2 になります（投入 script:21–24、172–175）。brief のコマンドが省略表記なら、投入前に実際の絶対パス入りコマンドを確定してください。

2. **must-fix — P2 の「2 request」を原子的な投入と扱わない。**

   workload ごとに qsub → 診断保存 → request ID 保存 → qstat を順次実行し、両方が終わって初めて group submission receipt を作ります（投入 script:266–330、417–420）。したがって、**rr5 だけ受理され、rr50 の投入や可視性確認で終了する経路**があります。A-6 の単一 workload 成功では検証できない点です。

   片側成功時は、残った request ID・qsub 診断・実行費用を記録し、同じ attempt を無条件再投入しない手順が必要です。create-only の制約もあります（`paper_story_a2_certification.py:3723–3725`）。queue の ENA/ACT 確認は、10 ノードの同時開始や待ち時間を保証しません（投入 script:148–163）。

3. **nit — P1 の policy・HEAD・環境変数の筋は通っている。ただし識別子を混同しない。**

   - `nodes` は正の整数を許容し、protocol preimage に scheduler は含まれません（`paper_story_a2_certification.py:344–355、448–457`）。1→5 だけなら protocol hash 不変、policy bytes hash は変化します（同:643–648）。
   - submit 時の HEAD が `IZANAGI_A2_EXPECTED_HEAD` に入り、job body が照合します。使い捨て commit の HEAD で正しく、親の基準 commit を手動注入する必要はありません（投入 script:165、272；job body:290–297）。
   - A-2 は `IZANAGI_A2_POLICY_PATH` を渡さず既定の A-2 policy を読みます。A-6 だけ追加する設計と一致します（投入 script:273–275；`paper_story_a2_certification.py:384–390`）。
   - **enforcement closure の63パスに A-2 policy JSON は入りません**（`campaign_lock.py:49–113`）。ただし binding の commit は新 HEAD になります。worker は commit と closure digest の両方を照合します（`contract_loader_binding.py:518–532`；worker:196–206）。

   同じ submit-tree を完走まで固定すれば、この変更だけによる closure mismatch は見当たりません。途中の checkout・commit・tree 撤去は避ける必要があります。

4. **must-fix — 「共有 home 上だから cluster-wide 排他が実測済み」は断定過剰。強い推測として記録する。**

   既定パスと flock は確認できます（`lock.py:24–34、42–54`）。job body は `IZANAGI_BENCH_LOCK` を設定しません。ただし、それだけでは実際の環境変数、同一 inode、マウント側の cross-node flock 動作まで証明しません。

   時刻列は非常に強く整合します。t2364 の cell 1 では：

   - rr5 performance 完了 **21:23:35**
   - rr50 rep 0 完了 **21:26:16**：差161秒
   - rr50 performance 完了 **21:36:42**
   - rr5 bench 完了 **21:36:59**：差17秒

   cell 2 と t2228 も同型なので、偶然の遅延より共有 lock 仮説が有力です。ただし WAL に acquire/release がなく、独立した立証ではありません。

   別説明として、verify 後の `rmtree` は WAL emit 後に走り、初回 settle は bench 計時前です（`pipeline.py:2176–2178、1408–1415`）。I/O 遅延・page cache・trace flush が区間へ混入する余地があります。これらだけで繰り返す相互対応を説明するのは弱い推測ですが、WAL だけでは排除できません。

5. **must-fix — fan-out でも head は兄弟待ちの全期間 lock を保持する。兄弟側 lock は task 単位。**

   performance pass の `with bench_lock()` 内から `_run_fanout_pass()` を呼び、全 future の完了と結果取り込みを待ちます（`pipeline.py:2399–2428、2289–2322`）。共有 flock が効くなら、**rr5 の5本と rr50 の5本が同時に走るのではなく、5本ずつの pass が直列化**します。

   worker は `task_root/bench.lock` を使います（worker:459–462、532–544）。これはノード共通 lock ではありません。異なる task 同士の排他は保証せず、競合 probe も起動直前の観測です（同:545–569）。割当ノードが重ならない通常ケースでは問題になりませんが、重複割当・host alias・孤児プロセスをこの lock が解決するとは書けません。

6. **nit — durable cache・receipts の直接衝突は見当たらない。host alias は残る。**

   cache・campaign・compute result は `jobs/<workload>` ごとに分離されます（job body:42–58；`paper_story_a2_certification.py:3742–3743`）。condition receipt も workload 名入りです（同:1334–1335）。head scratch は PBS request を含み、worker scratch は PBS ID と task hash を含みます（job body:340–341；worker:305–321、459–462）。共有ストレージ帯域の競合は残りますが、同名ファイル衝突とは別です。

   `PBS_NODEFILE` の**同じ文字列の重複行は除去される**ので、それ自体は失敗原因ではありません。head と兄弟4件を要求します（job body:136–154）。ただし short hostname/FQDN を正規化せず文字列比較するため、alias による head 不一致・別名二重計数は残ります。Python 側も同じ性質です（`paper_story_a2_certification.py:324–340`）。これは A-2 固有の欠陥ではなく、今回の割当で再び露呈し得る経路です。

7. **must-fix — A-6 成功から A-2 の容量適合は言えない。head と兄弟の保存先も異なる。**

   兄弟は `/scr/.../<task_sha>/tmp`、head の trace は `tempfile` の環境既定先です。job body の `/scr` staging は head trace を `/scr` に移す設定ではありません（worker:532–542；`pipeline.py:2159–2160`；job body:340–376）。

   指定資料には A-2 trace の最大 bytes・inode・verifier の最大メモリと、今回の各保存先の空きの比較がありません。**write-heavy だから A-6 より大きいとも断定できません**。A-6 は performance rep あたり1533万〜1735万 commits、提示 A-2 は約230万〜440万ですが、commit 数だけでは trace bytes や検証メモリを換算できません（A-6 README:204–206、baseline 時刻列）。

   容量不足・OOM・copy/fsync 失敗は、worker 非零終了や欠落結果を通じて remote-unavailable に落ち得ます（worker:501–514、610–612；`pipeline.py:898–908`）。容量確認ができない場合は、適合確認済みとせず、未確認の実機リスクとして残してください。

8. **must-fix — 不変条件2は、失敗分類と終了保証を混同している。**

   欠落・MAC 不一致は `verify-remote-unavailable` ですが、正当に認証された worker の失敗は `trace-timeout`、`verify-probe-error`、`verify-competing-tenant` などを保持します（`pipeline.py:909–933、525–529`；worker:548–565、586–593）。すべてを remote-unavailable に丸めてはいけません。

   さらに ssh に総 timeout がなく、head は全 future を待ちます（`pipeline.py:839–848、2289–2311`）。120秒は trace subprocess の上限であり、verifier・ssh・cleanup の総上限ではありません（同:521–529、613–625）。hang では整った indeterminate 成果物を残す前に walltime 終了もあり得ます。

   **30〜50分は予測で、支出上限ではありません。** 2 request が各5ノードで6時間使えば予約量は60 node-hoursです。

9. **must-fix — P3 は「科学的条件の同値性」と「成果物の同一性」を分ける。**

   verdict 等の一致に加え、各 workload × stock/adopted × legacy/performance の対応、実 workload flags、source/genome/build admission、commit witness、proof surfaces、terminal commit/abort、性能標本の欠落・失敗を確認してください。単なる rep 件数一致では不足です（`pipeline.py:945–960、572–625`；`paper_story_a2_certification.py:3819–3843`）。

   正常完走なら検査は **4 cell × (legacy 1 + performance 5) = 24件**、遠隔結果は **4 cell × 4 = 16件**。WAL は rep 番号を直接持たず、取り込み順の証拠なので task/result と対応させます（`pipeline.py:2312–2322`；A-6 README:199–202）。

   commits・aborts の実数も確率的です。完全一致条件ではなく、各 run 内の witness 整合と観測量として扱います。source commit、policy hash、task hash、MAC、campaign identity も attempt 間の一致対象ではありません。

   また HMAC secret はメモリで生成して stdin に渡しており、ここには永続化経路がありません（`pipeline.py:2263、847`）。事後に「MAC を独立再検証した」とせず、**head が実行時に照合して受理した証拠**として記録してください。

10. **must-fix — WAL だけで「並列化分」と「lock 待ち短縮分」を厳密分離できない。二重計上もある。**

    rr50 の cell 1「bench 33.9秒」は **21:36:42→21:37:16** の区間長です。その中に rr5 の bench 約17秒が入る解釈が成立します。`bench_wall_s` は lock 待ちと初回 settle を除外します（`pipeline.py:1386–1415`）。提示された時刻表だけから「bench 実体34秒」と置くのは誤りです。

    同様に `verify_done` 間隔には前 rep の cleanup、最初の rep には lock 待ちが混入します。fan-out の兄弟4件は全 future 待ち後にまとめて emit されるため、その WAL 間隔は兄弟の個別実行時間ではありません（同:2176–2178、2302–2320）。

    見積りは、**同時開始・既存のrep時間維持・追加 overhead 小**という仮定で次のようになります。

    | 構成 | 静的な目安と判定 |
    |---|---|
    | nodes=5、共有 lock | `2×(rr5 約115秒 + rr50 約165秒)` に build/legacy・bench・remote overhead を加える。概ね12〜15分程度のモデルで、**24分は提示算式から再現できない** |
    | nodes=1、head ごとの lock | 遅い rr50 が支配し、約30〜32分。**31分は概ね整合** |
    | nodes=5、head ごとの lock | overhead 前は約8〜9分程度。**10〜15分は仮定付きの帯としてはあり得る** |

    いずれも実測予測の保証ではありません。今回1本で node-local lock の反実仮想は検証できません。共有 lock が維持される場合、pass の短縮が他方の待ち短縮を生むので、両者を独立した speedup として足し合わせないでください。

11. **must-fix — queue 費用は request ごとの和とし、待ち・予約・有効処理を分ける。**

    正式には **`Σ nodes_i × Elapse_i`** です。2本の Elapse が等しいときだけ `nodes × Elapse × 2` にできます。投入が逐次で開始時刻も異なり得ます（投入 script:266–330）。

    request ごとに submit/start/end、queue 待ち、実ノード一覧、Elapse、要求 walltime、終了状態、CPU time・最大メモリなど取得できる会計値を残してください。attempt 全体は最初の投入から最後の終了までの時間も必要です。5ノードのうち兄弟4ノードは head の build・legacy・bench・他 request の lock 待ち中も予約されるため、**elapsed 短縮と node-seconds 削減は別問題**です。片側失敗や hang の費用も除外しません。

## 総括

**条件付き go。** 完全な投入コマンド、片側投入時の記録手順、6時間×10ノードの費用リスクを確定すること。
P3・失敗分類・24分見積りを修正し、共有 lock は「強く整合する推測」として記録すること。
submit-tree を完走まで固定し、容量適合は確認済み／未確認を明示すること。
今回の結果で判定できるのは nodes=5 の1 attemptであり、node-local lock の効果や恒久採用までは判定しない。