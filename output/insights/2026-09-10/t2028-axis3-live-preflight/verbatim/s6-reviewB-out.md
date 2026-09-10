## 変異 6 件の帰属 (どのテストのどの assert が殺すか)

6件とも mutation 自体は殺される。したがって「指定6変異が生き残る」という疑いはすべて refuted。

| 変異 | 判定 | 落ちる箇所 |
|---|---|---|
| 1. 最小間隔を 0 | refuted | source literal の変更なら [`test_related_work_search.py:792`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/tests/test_related_work_search.py:792) の mapping 完全一致。計算だけ 0 にする変異でも sleep 列 [`:865`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/tests/test_related_work_search.py:865) または実送信間隔 [`:866`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/tests/test_related_work_search.py:866) が落ちる。 |
| 2. 発行時刻を `acquire` 時点へ戻す | refuted | `begin_attempt` が10秒進める fixture により、sleep 列 [`:865`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/tests/test_related_work_search.py:865)、送信間隔 [`:866`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/tests/test_related_work_search.py:866)、観測値 [`:870`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/tests/test_related_work_search.py:870)、永続時刻 [`:876`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/tests/test_related_work_search.py:876) が落ちる。 |
| 3. retry 上限を 3 から 4 | refuted | 3 attempt 後の `retry_stream_id is None` [`:2937`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/tests/test_related_work_search.py:2937) がまず落ちる。そこを通しても4回目の `pytest.raises` [`:2939`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/tests/test_related_work_search.py:2939) が落ちる。 |
| 4. transport 例外時の materialize を削除 | refuted | intent 実体ファイルの存在 assert [`:978`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/tests/test_related_work_search.py:978) が落ちる。ただし、これは実際の `resume_bundle` 成功を検査していない。後述の real 欠陥が残る。 |
| 5. 予算検査を `begin_attempt` 後へ戻す | refuted | attempt 上限側の `writer.attempt_intent is None` [`:913`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/tests/test_related_work_search.py:913)、deadline 側の同 assert [`:935`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/tests/test_related_work_search.py:935) が落ちる。 |
| 6. `observed_interval_seconds` 値 gate を追加 | refuted | `44.87` を入れた後の no-throw oracle [`:1335`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/tests/test_related_work_search.py:1335) が追加 gate の例外位置で失敗する。ここは明示的な `assert` ではなく「例外なく return」が oracle。 |

## 19.5 時間走行の場面別追跡

- **DBLP の接続切断: real failure。** `LiveHTTPTransport` は切断を `ContractError("live_transport")` にする [`related_work_search.py:2678`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:2678)。`_send_with_raw_commit` は materialize 後に再送出する [`:5896`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:5896)。一方 retry loop は返却済み `response.status` だけを見る [`:6642`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:6642) ため、transport 例外は1回目で CLI まで抜けて exit 2 になる [`run_axis3_search.py:408`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/tools/run_axis3_search.py:408)。**3 attempt、cooldown、次 row のいずれにも到達せず、残り row は `unavailable` にならない。report 自体が出ない。**

- **materialize 後の resume: real failure。** materialize は pending intent のファイルと state pointerを書くだけで、stateを確定・消去しない [`related_work_search.py:5227`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:5227)。新設テストも `state == "pending"` を期待している [`test_related_work_search.py:976`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/tests/test_related_work_search.py:976)。`resume_bundle` はその pending を見て `unconfirmed_attempt_intent` で停止する [`related_work_search.py:9017`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:9017)。

- **503 が切断の代わりに継続する場合: refuted/限定。** HTTP 503 なら合計3 attempt 後に row を `unavailable` とし、DBLP は2700秒待って次へ進む [`related_work_search.py:6745`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:6745)。ただし全1415 tail row を処理する前に30日 deadlineへ到達する。したがって「残り全 row が最終 report 内で `unavailable`」は refuted。

- **retry backoff 中の process death: refuted。** HTTP応答は `attempt_row` 内で commit されてから retry sleeperへ戻る [`related_work_search.py:6628`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:6628)。commit は pending を消す [`:5501`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:5501)。従って backoff 中には pending intent は残らない。resume は保存 attempt 数から retry を再開し、該当 backoff を最初から再度 sleep する [`:8671`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:8671)。これは過剰待ちになり得るが短縮にはならない。

- **`resume --live` の limiter: 部分 refuted、cooldown は real。** limiter は初走で `<bundle>/state/host-limiter.json` を使い [`related_work_search.py:5778`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:5778)、resume も同じ path を開く [`:9028`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:9028)。従って最後の実送信時刻と最小間隔は引き継ぐ。一方、状態 schema は `last_issued_at` しか持たない [`:5621`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:5621)。2700秒 cooldown は単なる `sleep` [`:6765`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:6765) なので、cooldown 中に死ぬと resume は残時間を無視し、最小45秒だけで次 row を送れる。

- **2本目以降の OpenAlex 429: refuted。** exact-one stop は最初の availability 429 の分岐だけ [`related_work_search.py:6660`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:6660)。後続429は合計3 attempt、実際に使う backoff は3秒・6秒、最終 row 状態は `unavailable/http_429`、cooldownなしで次 rowへ進む。

- **所要時間の導出。** 静的 catalog 再構築 [`related_work_search.py:1753`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:1753) と exact preflight order [`:6326`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:6326) から、1929本は OpenAlex 23、arXiv 373、DBLP 1533、その末尾1415本がDBLP連続だった。

  - 全件1回成功: 各 request について `t=max(current, previous_host_issue+floor)` を順に適用すると `69,975秒 = 19時間26分15秒`。30日までの余裕は `2,592,000-69,975=2,522,025秒 = 29日4時間33分45秒`。
  - 全件3回目で成功: `5,787 request`、backoff sleep `72,549秒`、limiter sleep `138,732秒`、合計 `211,281秒 = 2日10時間41分21秒`。deadline余裕は `27日13時間18分39秒`。
  - request 上限: `1929×3=5,787` なので、20万に対し `194,213` request、`97.1065%` の余裕がある。
  - cooldown の構造上限: DBLP 1533本のうち「後続 complete row がある」最大1532本で発火可能。`1532×2700=4,136,400秒 = 47日21時間`。1415本の連続 tail 内だけでも `1414×2700=3,817,800秒 = 44日4時間30分`。
  - deadline を実際に適用すると、exact catalog orderで発火可能なのは最大929回。tail開始時点までの最短が6300秒、tail最初の失敗 row の3回目が6435秒、以後3回目は `2790秒 = 45+45+2700` ごと。tailだけが失敗する場面では、927回目の3回目が `6435+926×2790=2,589,975秒`、cooldown終了が `2,592,675秒`。次の row は deadline を675秒超過して拒否されるため、927 rowだけが `unavailable`、残り488 rowは reportへ到達しない。
  - 真の wall-clock 最悪値は有限に証明できない。`response.read()` 全体の wall ceiling/body ceiling がなく [`related_work_search.py:2674`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:2674)、これは確定 scope 外とも明記されている [`plan-v2.md:154`](/home/SFC/tanab/.claude/jobs/1a05f945/tmp/t2028-artifacts/plan-v2.md:154)。さらに最後の許可済み応答後の cooldown は deadline 検査なしで2700秒を追加できる。

## must-fix (real)

1. **transport 例外 retry が未実装。** 契約は送信失敗を retry 対象にしている [`plan-v2.md:68`](/home/SFC/tanab/.claude/jobs/1a05f945/tmp/t2028-artifacts/plan-v2.md:68) が、実装は例外を即再送出する。  
   成果物影響: 最初の DBLP 切断で preflight report が発行されず、row の `unavailable` evidenceも残らない。

2. **materialized transport failure bundle は依然 resume 不可能。** テストは `_validate_bundle_for_resume` の構造検査までしか呼ばず [`test_related_work_search.py:980`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/tests/test_related_work_search.py:980)、production の `resume_bundle` が pending を拒否する現物経路を通していない。  
   成果物影響: bundle の再開結果は `status=blocked, reason=unconfirmed_attempt_intent` のまま。

3. **cooldown が永続化されず、resume で短縮される。** 3回目の失敗 commit と2700秒 sleepの間に死ぬと、WALはその row 完了済みなので resume は次 rowへ進み、host limiter の45秒床しか残らない。  
   成果物影響: 次 attempt の `request_intent_at` が契約上の cooldown 終了より最大2700秒早くなる。

4. **同一 bundle の2 process起動を `flock` は安全化していない。** limiter stateの lockは取得される [`related_work_search.py:5633`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:5633) が、送信終了直後に解放され、raw保存・分類・commitはその後 [`:5884`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:5884)。各 writer は独立した `journal_byte_count` を持ち、他 process が伸ばした WAL を「余剰」として truncate する [`:4874`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:4874)。  
   成果物影響: duplicate ordinal、WAL frame消失、invalid bundle、重複requestのいずれかになり得る。

## nit

- **real (test weakness):** 新設 pacing/materialize/budget tests は `_send_with_raw_commit` を通すが transport は `NonProductionTransport` [`test_related_work_search.py:824`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/tests/test_related_work_search.py:824)。retry/cooldown とN3は `run_preflight` を通る一方、新設6件には `LiveSearchSession`、`_send_with_receipt`、`resume_bundle` の正例・負例がない。特に materialize test は実際の resume 成功ではなく、逆に pending 残存を固定している。

- **real (test weakness):** cooldown test が検査する実送信順序は「最後の503から次 rowまで2700秒」だけ [`test_related_work_search.py:1714`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/tests/test_related_work_search.py:1714)。各 retry の送信時刻、3回が連続同一 streamであること、OpenAlex/arXiv backoffは検査していない。

- **real:** retry 上限が合計3 attemptなので、定数列の3番目である12秒・DBLP 60秒は到達不能 [`related_work_search.py:279`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:279)。上限を緩めるべきという意味ではなく、現契約では実際の inter-attempt backoff は最初の2値だけ。

- **real:** resumeで最後の planned DBLP rowを retryし尽くした場合も、後続 row の有無を見ず2700秒 sleepする [`related_work_search.py:8699`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:8699)。成果物値は変わらないが、最終化だけ45分遅れる。

- **real、ただし静的 provenance 限界:** 追加6 node は `0.42, 2.6, 5.4, 0.003, 1.7, 0.061` で全て正数 [`acceptance_duration_ledger.json:3`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/tests/acceptance_duration_ledger.json:3)。合計は `10.184秒`、5分まで `289.816秒` の余裕。node数も22163で整合する [`:22167`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/tests/acceptance_duration_ledger.json:22167)。ただし JSON 自体には producer receipt がないため、「正本 producer 由来」は実装子申告以上には静的証明できない。全 ledger の単純和は14,776.661秒だが、これは並列 acceptance の wall-clockではない。

## refuted

- **pacing 自体が helperだけの飾りという疑いは refuted。** `run_preflight` は1個の limiterを作り [`related_work_search.py:6567`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:6567)、全 attempt が `_send_with_raw_commit` を通る。そこでは wait、予算検査、intent、実送信直前時刻、sendの順になっている [`:5856`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:5856)。

- **予算検査が pending を作る疑いは refuted。** `budget.check` は `begin_attempt` より前 [`related_work_search.py:5858`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:5858)。

- **N3値が受理 gateになった疑いは refuted。** validatorは件数・identity・順序だけを比較し、`observed_interval_seconds` の値を読んで拒否していない [`related_work_search.py:6850`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:6850)。

- **別 bundle 間にも `flock` が効くという理解は refuted。** state path は bundle-localなので、別 bundleから同一 hostへ送る process同士には間隔保証も送信排他もない。これは確定プランの「別 producer を出さない」という運用排他 [`plan-v2.md:145`](/home/SFC/tanab/.claude/jobs/1a05f945/tmp/t2028-artifacts/plan-v2.md:145) に依存する。

- **追加6 nodeに0.0 placeholderがある疑い、および追加分だけで5分を超える疑いは refuted。** 追加分は全て正数、直列合計10.184秒。

## 総括

must-fix は4件。特に致命的なのは、契約上の主対象である transport 切断が一度も retry されず、materialize後の bundleも `resume --live` できない点である。現状のまま19.5時間走行へ投入すべきではない。

なお検査時点では対象差分は未commitではなく、`HEAD b96b685db` にcommit済みで作業木は clean だった。こちらから編集・実行・commitは行っていない。