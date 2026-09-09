## 現状の把握

結論として、pacing は全送信が集中する `_send_with_raw_commit` の直前へ置き、1 起動中は単一 `HostLimiter`、再開時は bundle 内の永続状態を引き継ぐ構成が最小かつ安全である。

- live の実送信はすべて [_send_with_raw_commit](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:5551) を通る。呼び出し元は availability、通常 preflight、`_run_stream`、preflight resume、final resume の 5 箇所だけである。
- 現状は [begin_attempt](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:5564) が transport より先に永続化される。この前に sleep を挿入しなければ、待機中の停止が `unconfirmed_attempt_intent` になる。
- `clock` は `run_preflight`、`run_ready`、`resume_bundle` から `WireBudget`、intent、受領時刻、checkpoint まで、timezone 付き `datetime` として流れている。軸 1 の数値 clock をそのままコピーはできないが、datetime 差分で実装すれば同じ注入経路を利用できる。別の monkeypatch seam は不要。
- [capture_page_evidence](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:2944) は応答 header を重複も含めて全件保存済みである。
- preflight report の schema は独立 JSON file ではなく、[PREFLIGHT_REPORT_SCHEMA](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:77) として source 内にある。
- U11 の hard stop は amendment §6 と登録記録 §6.1 の双方が `run-ready --live` に限定している。契約 §3 の live preflight はその前段なので、今回の実走対象にできる。
- P2 の 3.0 / 1.0 / 45.0 秒は同一ノード・同一 host の実績値であり、この wave では緩めずそのまま採用する。DBLP の 30 秒回復例があっても、凍結された下限 45 秒を優先する。

## 実装プラン (file:line 粒度)

以下の行番号は現在の source を基準とする。

1. import と固定値

   - [related_work_search.py:10](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:10) 付近へ `fcntl` と `time` を追加する。
   - [related_work_search.py:224](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:224) の endpoint 定義直後へ、host key の固定表を置く。
     - `export.arxiv.org: 3.0`
     - `api.openalex.org: 1.0`
     - `dblp.org: 45.0`
   - 値は CLI option や catalog 値にせず source literal とする。速度目的の上書き経路は作らない。

2. 軸 1 と同型の永続 limiter

   - [_write_bytes_immutable](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:3629) の直後へ、軸 1 の `_locked_runtime_update` と `HostLimiter` を移植する。
   - 状態は live bundle の `state/host-limiter.json` に置き、次を保持する。
     - runtime schema version
     - host ごとの最終 issue 時刻
   - file は `flock`、mode `0600`、read-modify-fsync の順で更新する。破損・未知 version・naive datetime は送信前に fail closed とする。
   - bundle を伴わない simulation はメモリ内 host map を使う。
   - 軸 3 の既存 `clock` は aware `datetime` なので、その差分を秒へ変換する。永続値は小数秒を落とさない UTC ISO 8601 とし、再開時に最大 1 秒早くなる丸めを避ける。
   - `HostLimiter.acquire(host, minimum_interval)` は sleep 秒、issue 時刻、同 host の直前 issue からの観測間隔を返す。

3. sleep と WAL intent の決定的順序

   - [_send_with_raw_commit](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:5551) に共有 limiter と任意の観測 sink を受ける引数を加える。
   - 現在の [begin_attempt 呼び出し](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:5564) より前へ、次の順序で挿入する。

     1. request URL から host を再導出する。
     2. host が固定表にあることと request の index が対応することを検査する。
     3. `limiter.acquire(...)` を実行し、必要なら `sleeper` で待つ。
     4. 待機完了時刻と観測間隔を記録する。
     5. その後にだけ `writer.begin_attempt(...)` を実行する。
     6. 既存どおり budget consume、transport send、response raw commit へ進む。

   - これにより sleep 中の停止では intent が存在しない。limiter 状態更新後、intent 前に停止した場合は次回に余分に待つだけで、安全側になる。
   - [record_raw_response](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:5599) より後ろへ sleep を置かない。
   - [LiveHTTPTransport.send](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:2555) 自体には pacing を入れない。そこで入れると bundle/WAL 順序と注入 seam が分離する。

4. `sleeper` と limiter の伝播

   - [run_preflight](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:6152) に `sleeper: Callable[[float], None] = time.sleep` を追加する。[WireBudget 構築位置](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:6205) 付近で limiter を一度だけ作り、availability 送信と通常 loop の両方へ渡す。
   - [_run_stream](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:6701) に limiter を必須で渡し、全 page が同一 instance を使うようにする。
   - [run_ready](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:6842) に同じ `sleeper` seam を追加する。ready loop の外で limiter を一度構築し、[全 `_run_stream` 呼び出し](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:6915) へ渡す。枝・control・page をまたいで host 状態を共有できる。
   - [_resume_preflight_from_wal](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:8114) は limiter を引数で受け、内部 `send_and_commit` から中央 helper へ渡す。
   - [_resume_final_request_sequence](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:8393) にも同じ limiter を渡す。
   - [resume_bundle](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:8509) に `sleeper=time.sleep` を追加し、bundle root の永続状態から limiter を一度構築する。それを preflight resume、現在 stream の final resume、残り ready loopのすべてへ渡す。
   - `tools/run_axis3_search.py` は編集しない。[CLI の各呼び出し](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/tools/run_axis3_search.py:195) は新しい既定値 `time.sleep` を使用する。CLI option や sealed argv contractを増やさない。

5. N3 の request 間隔記録

   - [_preflight_row_base](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:5839) の手前へ、issue 観測列を report 用に正規化する helper を追加する。
   - report の新 field は `pacing_observations` とし、wire attempt 順に次を持たせる。
     - `attempt_number`
     - `stream_id`
     - `index`
     - `host`
     - `request_intent_at`
     - `minimum_interval_seconds`
     - `observed_interval_seconds`。同 host の最初だけ `null`
   - 通常実行では `_send_with_raw_commit` が集めた観測から生成する。resume では [WAL の committed intent](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:4162) の `intent_at` と request URL から再導出する。
   - report を作る 3 箇所、[_derive_preflight_report_from_wal](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:6081)、429 stop report、[通常 report](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:6406) に同じ field を入れる。
   - [validate_preflight_report](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:6442) で件数を `wire_attempt_count` と一致させ、evidence と stream/index/host/attempt 順を照合する。同 host の 2 件目以降は観測間隔が固定下限以上でなければ拒否する。
   - [_validate_preflight_report_against_bundle_material](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:7972) に committed intents を渡し、report の pacing 列が WAL 再導出値と完全一致することを検査する。

6. 受理集合を変えない境界

   - [_probe_response](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:5694) は変更しない。特に非 200 を `unavailable` にする 5695-5702 行を維持する。
   - arXiv window 超過、lookup failure の `blocked` 判定である 5779-5786 行も変更しない。
   - [validate_preflight_report](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:6470) の `ready/unavailable/blocked` 語彙、6528-6531 行の status 対応、6554-6590 行の 429 stop accounting を維持する。
   - [_run_stream の非 200 処理](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py:6739) も変更しない。
   - `_validate_preflight_wal_attempt_sequence` の既存 retry 上限・resume 規則を変更せず、新しい自動 retry は一切加えない。
   - したがって pacing が変えるのは transport 呼び出し時刻だけであり、同じ response 列に対する受理集合は完全に同一である。
   - `Retry-After` は証拠として保存するだけで、429 を 200 相当にしたり、同一起動内で再送して成功 response に置換したりしない。最初の OpenAlex 429 は既存どおり exact 1 request で停止する。

## schema と成果物への影響

- source 内の `PREFLIGHT_REPORT_SCHEMA` には変更が必要である。
  - `required` へ `pacing_observations` を追加する。
  - `properties.pacing_observations` へ、上記 7 propertyを持つ `additionalProperties: false` の object array を追加する。
  - required field の追加なので `PREFLIGHT_REPORT_VERSION` は `axis3-search-preflight-report/v2` へ上げる。
- [axis3_search_page_evidence.schema.json:37](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/schemas/axis3_search_page_evidence.schema.json:37) は変更不要である。
  - `Retry-After`、`RateLimit-*`、`X-RateLimit-*` は report の `preflight_evidence[*].alternative_provenance.observed_response_headers[*]` に exact name/value、重複保持で既に入る。
  - `preflight_evidence_sha256` と report digest がその header 列を束縛する。
- [axis3_search_checkpoint.schema.json:89](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/schemas/axis3_search_checkpoint.schema.json:89) も変更不要である。
  - 最初の OpenAlex 429 の `Retry-After` は既存 `checkpoint.retry_after`、残量は `checkpoint.quota_remaining` に入る。
  - 全応答の N3 記録の正本は report evidence であり、checkpoint は停止点の補助情報に限定する。
- catalog、query ID、語、枝、cutoff、request factory、判定語彙は変更しない。catalog bytes は同一になるはずだが、再 `register` で再生成して同一性を検査する。
- `tools/run_axis3_search.py`、page evidence schema、checkpoint schema は bytes を変えない。ただし closure の source digest が変わるため旧 seal は使用不能になる。
- `2026-08-27-*` 2 文書と `2026-09-01-*` 2 文書は編集対象外であり、1 byte も変更しない。

## test 計画

この test module は class 分割されていないため、関連する module-level test の隣へ追加する。

- [test_related_work_search.py:271](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/tests/test_related_work_search.py:271) の `_fixed_clock` 隣へ、現在時刻を保持する fake clock と、呼ばれた秒数を記録して fake clock を進める fake sleeper を置く。実時間 sleep は一度も実行しない。
- [test_response_received_time_is_recorded_after_request_intent](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/tests/test_related_work_search.py:699) の隣へ次を追加する。
  - 同 host の 2 回目で期待秒数だけ fake sleeper が呼ばれる。
  - sleeper 内で writer に pending intent がまだないことを確認する。
  - sleeper が例外で process crash を模擬した場合、transport の 2 回目が呼ばれず、`attempt_intent` も生成されない。
- 同じ位置へ limiter 永続化 test を加える。
  - 1 個目の limiter で issue した後、同じ state file を使う別 instance を作る。
  - 2 個目が残り間隔を待つことを確認し、resume 時に pacing が初期化されない退行を殺す。
  - arXiv、OpenAlex、DBLP の exact 下限と、異なる host が相互に待たないことも確認する。
- [test_full_catalog_preflight_report_round_trips_without_wal](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/tests/test_related_work_search.py:1075) の隣へ report test を追加する。
  - pacing 観測が 1929 件ある。
  - attempt/evidence 順が一致する。
  - 各 host の 2 件目以降が 3.0 / 1.0 / 45.0 秒以上である。
  - interval を下限未満へ改変し report digest も再計算した mutant が `validate_preflight_report` で拒否される。
- 既存 full-catalog fixture と unresolved preflight には fake sleeper を引数で渡すだけにする。`wire_attempt_count=1929`、blocked 193 など既存期待値は一切変えない。
- [test_run_ready_reissues_page_zero_orders_indices_and_never_completes_axis](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/tests/test_related_work_search.py:1114) の隣へ、2 page の `_run_stream` が同じ limiter を使い、DBLP なら 45 秒待つ test を追加する。`complete` や判定結果の期待値は既存どおりにする。
- [test_mutation_m6_openalex_429_sends_exactly_one_request_and_checkpoints](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/tests/test_related_work_search.py:1362) に隣接して、report evidence に重複 `Retry-After` と rate-limit header が exact に残り、送信は 1 本のままであることを検査する。
- [test_preflight_wal_pending_intent_blocks_without_send](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/tests/test_related_work_search.py:2299) の隣へ resume test を追加する。
  - committed prefix の issue 時刻から limiter 状態を復元する。
  - `_resume_preflight_from_wal` の次送信も fake sleeper を通る。
  - 未試行 stream の継続規則と `unconfirmed_attempt_intent` の既存期待を変えない。
- bundle validation test では `pacing_observations` を WAL intent から独立に再導出し、自己再 digest した改変 report を拒否する。

この段では read-only 指示に従い pytest は実行しない。親の実装段で `tools/run_tests.py` 経由の対象 test と必須 checker を実行する。

## seal 再発行と commit 順序

1. `related_work_search.py` と test だけを実装し、対象 test、`check_codex_agents.py`、`check_docs.py` を通す。外部 request はまだ出さない。
2. source と test を同じ実装 commit に入れる。page/checkpoint schema と CLI を変更しない場合も、closure 8 fileすべてについて作業ツリー bytes と現在の `HEAD:<path>` が一致することを確認する。
3. 実装 commit 後に `check_ai_provenance.py` を実行する。
4. 新日付の出力先へ canonical CLI の `register` を実行する。これにより新しい source digest、closure digest、seal digest、registration-input commit が発行される。
5. 新 seal に対して `validate-registration` を実行し、`head_verified: true` と `valid: true` を確認する。
6. 新 catalog、registration inputs、seal、validation 結果を登録成果物 commit に入れる。この commit で HEAD は動くが、closure 8 file の blob が変わらなければ seal は失効しない。
7. live preflight の直前に、再度 closure 8 file の作業ツリー bytes と現 HEAD blob の一致を検査する。その後だけ `preflight --live` を repo 外の恒久 bundle path で開始する。
8. 実走後、新しい `2026-09-09-axis3-live-preflight.md` と通常の可変記録を別 commit にする。raw bundle は repo 外に維持する。
9. 旧 4 凍結文書はどの commit にも変更として含めない。

## 残るリスクと親への質問

- limiter の state file は同じ bundle の開始・再開を連結するが、別 bundle や別 wave の process までは直列化しない。N4 の共有単位が未確定なので、親には「約 19.5 時間の実走中、同じ login node から同じ 3 host へ送る別 producer がないか」を確認してほしい。これを新しい repository gate へ一般化する提案はしない。
- 最初の OpenAlex request が 429 なら、report に `Retry-After` と rate-limit header は残るが、同 host の連続 request がないため最初の `observed_interval_seconds` は `null` になる。これを「OpenAlex の間隔を実測済み」と過大評価してはならない。
- `Retry-After` は自動 retry の入力にしない。再開は既存の query 全体再走上限と、人間が cooldown 残存中に開始しないという契約に従う。
- process が sleep 後かつ `begin_attempt` 後、raw response 前に落ちる既存の不確定領域は残る。今回閉じるのは「sleep 中の停止だけで pending intent が生じる」経路である。

## 総括

最小差分は、軸 1 型の host limiter を軸 3 の `_send_with_raw_commit` 前へ置き、`clock` と `sleeper=time.sleep` を全 public 実行・resume 経路から共有し、WAL intent に対応する host 別間隔を preflight report v2へ記録することである。

この変更は送信時刻だけを変える。429 を成功へ置換せず、非 200 の `unavailable`、既存 `blocked`、最初の OpenAlex 429 の exact-one stop、query 集合と全判定規則は変更しない。実装・編集・commit・test 実行は行っていない。