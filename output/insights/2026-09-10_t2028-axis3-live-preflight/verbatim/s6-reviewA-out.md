## 裁定 7 点の検算

| 項目 | 判定 | 検算結果 |
|---|---|---|
| §3.1 pacing | **real: 部分不適合** | 固定値、wait-before-intent、永続化はある。しかし production の実送信時刻は正確な `send` 直前ではなく、resume 時の状態欠落も fail-open。 |
| §3.2 retry | **real: 不適合** | 429/503 の最大 3 attempt と 4 回目拒否は実装済み。一方、transport 例外は再試行されず、429→200 を `ready` に洗濯できる。 |
| §3.3 pending materialization | **refuted** | 送信経路は `BaseException` を捕捉して `materialize_pending_attempt()` を呼ぶため、例外型による取りこぼしはない。[related_work_search.py:5896](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:5896) |
| §3.4 DBLP cooldown | **real: 部分不適合** | 同一プロセスでの 2700 秒 sleep はあるが、3 回失敗後の cooldown 中に中断すると resume が残時間を引き継がない。 |
| §3.5 budget/deadline | **refuted** | 状態非変更の `check()` があり、limiter wait後、`begin_attempt` より前に実行される。[related_work_search.py:5801](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:5801) [related_work_search.py:5856](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:5856) |
| §3.6 N3 | **real / refuted** | `observed_interval_seconds` の値が gate になる懸念は refuted。ただし resume report は実発行時刻でなく秒精度の intent から値を再構成しているため、記録値が不正確。 |
| §3.7 test | **refuted: 緩和なし、ただし不足あり** | 既存期待値は維持され、新設 6 test も恒真ではない。ただし production timestamp、transport retry、失敗洗濯、cooldown resume を通していない。 |

## must-fix (real)

1. **transport 例外が retry 対象になっていない。**

   `_send_with_raw_commit` は例外時に materialize して即再送出し、`finish_retries` は返却済み response の status だけを扱うため、送信例外は 1 回で preflight 全体を落とす。[related_work_search.py:5896](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:5896) [related_work_search.py:6575](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:6575) [related_work_search.py:6636](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:6636) テストも「1 call 後に OSError を再送出」を正としており、retry を検査していない。[test_related_work_search.py:940](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/tests/test_related_work_search.py:940)

   影響: 接続切断 1 回で report が作られず、live bundle は `unconfirmed_attempt_intent` のまま再開不能になる。

2. **429/503 の後に 200 が来ると、その row が `ready` になる。**

   retry loop は `response/evidence/probe` を最新 attempt で上書きし、row と validator は最新 evidence だけから status を導出する。[related_work_search.py:6642](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:6642) [related_work_search.py:6745](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:6745) [related_work_search.py:6904](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:6904) これは「429・503 はその query を未完走」とする凍結契約に反する。[2026-08-27-axis3-search-preregistration.md:1046](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/docs/related-work/claim-survey/2026-08-27-axis3-search-preregistration.md:1046)

   副作用なしの最小再現でも evidence `[429, 200]` に対し report status は `ready`、`declared_total` は 0 になった。

   影響: preflight の `ready` 集合が拡大し、本走で本来未完走の row が送信対象になる。

3. **production の「最終発行時刻」は実際の `LiveHTTPTransport.send` 直前ではない。**

   時刻取得は `limiter.issue()` で行われるが、その後 `LiveSearchSession._send_with_receipt()` に入り、型検査と transport identity 検査を経てから実際の `.send()` が呼ばれる。[related_work_search.py:5885](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:5885) [related_work_search.py:2829](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:2829) [related_work_search.py:2835](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:2835) 新設 test は `NonProductionTransport` の直接送信だけを観測するため、この差を殺さない。[test_related_work_search.py:820](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/tests/test_related_work_search.py:820)

   影響: wrapper 内処理時間の変動分だけ実送信間隔が記録値より短くなり、固定床を下回る経路が残る。

4. **resume 後の pacing observation が実発行時刻ではなく WAL intent から捏造される。**

   `_pacing_observations_from_intents` は `intent_at` の差を `observed_interval_seconds` にし、その値を最終 report へ入れる。[related_work_search.py:6183](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:6183) [related_work_search.py:6195](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:6195) [related_work_search.py:6447](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:6447) 裁定は `intent_at` の秒精度から exact 再導出できないと明示している。[plan-v2.md:117](/home/SFC/tanab/.claude/jobs/1a05f945/tmp/t2028-artifacts/plan-v2.md:117)

   影響: resume を含む preflight report の N3 観測値が、実際の送信間隔ではない値へ変わる。

5. **resume が DBLP cooldown と limiter state を fail-closed に継承しない。**

   3 attempt 消化済みの DBLP tail は `retry_stream_id=None` となるため、resume は cooldown を置かず次の未試行 row を送る。cooldown は同一 invocation 内で新たに失敗した場合にしか実行されない。[related_work_search.py:8584](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:8584) [related_work_search.py:8709](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:8709) [related_work_search.py:8720](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:8720)

   さらに limiter state は `O_CREAT` で開き、空ファイルを新規状態として受理するため、resume 時に欠落していても拒否されない。[related_work_search.py:5601](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:5601) [related_work_search.py:5633](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:5633) [related_work_search.py:9028](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:9028)

   影響: cooldown 中の crash、または state 欠落後の resume で、次の DBLP request が 2700 秒または45秒の床より早く発行される。

6. **preflight 用変更が final bundle の retryability を壊しており scope 外。**

   `_derive_finalize_eligibility` は retryable tail を非終端にする条件を `kind == "preflight"` に限定した。そのため final bundle の 429/503 tail は `terminal_tail` として finalize 可能になる。[related_work_search.py:3883](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:3883) [related_work_search.py:3896](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:3896) `run_ready` はこの判定で bundle を finalize する。[related_work_search.py:7343](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:7343)

   影響: 本走の retryable failure bundle が finalized になり、従来可能だった resume/retry が失われ、実行記録が途中で固定される。

## nit

該当なし。上記はいずれも report、bundle、実行記録、受理集合または実送信時刻を変えるため nit には落とさない。

## refuted

- **materialize の例外型取りこぼし:** refuted。送信・limiter 永続化・response mapping の例外を `BaseException` で捕捉して materialize する。[related_work_search.py:5884](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:5884) [related_work_search.py:5913](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:5913)

- **sleep または budget check が intent 後:** refuted。host wait、状態非変更 check、`begin_attempt`、`consume` の順である。[related_work_search.py:5856](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:5856)

- **3 回目拒否または4回目受理:** refuted。3 回目は受理され、4 回目は `bundle_preflight_sequence` で拒否される。[related_work_search.py:6289](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:6289) [test_related_work_search.py:2926](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/tests/test_related_work_search.py:2926)

- **`observed_interval_seconds` の値が受理 gate:** refuted。validator は件数、順序、host、固定最小間隔だけを照合し、observed 値を参照しない。44.87 へ変更して report digest を再計算した正例も通す。[related_work_search.py:6850](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:6850) [test_related_work_search.py:1321](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/tests/test_related_work_search.py:1321)

- **直接の非 200 分類、未解決 factory、通常件数の変更:** refuted。非 200 自体は引き続き `unavailable`、未解決 factory は `blocked` である。[related_work_search.py:6038](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:6038) [related_work_search.py:6734](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:6734) 通常 fixture は `wire_attempt_count=1929`、`rows=2122`、`blocked=193`、transport 1929 call を保持する。[test_related_work_search.py:1298](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/tests/test_related_work_search.py:1298) [test_related_work_search.py:1308](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/tests/test_related_work_search.py:1308) [test_related_work_search.py:1361](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/tests/test_related_work_search.py:1361)

- **初回 OpenAlex 429 の同一 invocation 内 exact-one stop:** refuted。`finish_retries` より先に専用分岐へ入り、そのまま return する。[related_work_search.py:6660](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:6660) [related_work_search.py:6709](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:6709) テストも2件目の scripted responseを未消費に固定する。[test_related_work_search.py:1620](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/tests/test_related_work_search.py:1620)

- **凍結境界の変更:** refuted。HEAD^→HEAD の変更は許可された3ファイルだけ。catalog producerを新旧 sourceで独立実行した結果、双方とも 2,818,599 bytes、SHA-256 `7dd14814ecd3a924d61ebfee707d604556624db639240318a95ce49e44185a58` で byte exact 一致した。行数も双方2122。[related_work_search.py:1753](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:1753) [test_related_work_search.py:380](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/tests/test_related_work_search.py:380) `tools/run_axis3_search.py`、schema 4 本、凍結文書、語、10枝、cutoff、query ID、factory state は無変更。

- **scope 外の resolver、control evaluator、DBLP 題名 lookup、body/wall-clock ceiling、pending recovery強化:** refuted。これらの実装差分はない。実際の scope 外混入は must-fix #6 の final eligibility 変更だけ。

- **新設 test が恒真、skip、fixture差し替えで既存期待を回避:** refuted。新設 test は具体的な timing、call数、WAL拒否、materialized pathを検査し、skip/xfail追加もない。ただし must-fix に挙げた分岐は未カバー。

- **report v1 前提 consumer の残存:** refuted。repo 内に `axis3-search-preflight-report/v1` の参照はなく、CLI の preflight、run-ready、resume、bundle validation はいずれも現 source の producer/validator/loaderへ委譲している。[run_axis3_search.py:195](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/tools/run_axis3_search.py:195) [run_axis3_search.py:240](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/tools/run_axis3_search.py:240) [run_axis3_search.py:279](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/tools/run_axis3_search.py:279) [run_axis3_search.py:308](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/tools/run_axis3_search.py:308)

## 総括

**must-fix 6 件。現状のまま live preflight を発火させるべきではない。** 最大の問題は、transport 例外 retry が未実装であること、429/503 を後続200で `ready` に洗濯できること、resume が実発行時刻と DBLP cooldown を正しく継承しないこと。

レビュー途中で親側から commit `b96b685db444` が作成されたが、当初観測した未コミット3ファイル差分と HEAD^→HEAD は同一で、現在の作業ツリーは clean。pytest は実行せず、静的検査と書込みなしの fake transport 最小再現のみ行った。