## 所見 1: test seam は real registry への委譲を防がず、偽 capture を正規 capability として封印できる

- (a) `_launch_floor_attempt_for_test()` は registry の真正性や launcher origin を検査せず、real adapter へ委譲する fake を通じて偽の測定結果を proof chain へ記録できる。
- (b) [orchestrator/campaign/s8b_floor_attempt_launcher.py:1072](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-review/orchestrator/campaign/s8b_floor_attempt_launcher.py:1072)、[orchestrator/campaign/s8b_floor_attempt_launcher.py:1090](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-review/orchestrator/campaign/s8b_floor_attempt_launcher.py:1090)、[orchestrator/campaign/s8b_attempt_registry.py:3088](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-review/orchestrator/campaign/s8b_attempt_registry.py:3088)、[orchestrator/tests/test_s8b_floor_attempt_launcher.py:188](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-review/orchestrator/tests/test_s8b_floor_attempt_launcher.py:188)
- (c) 正当な v2 claim、marker、slot を用意し、test seam に `registry=attempt_registry`、または全メソッドを real adapter へ転送する fake registry を渡す。`capture_measure_point` と probe だけを偽実装にすると、reserve、classify、begin は real adapter が発行するため、handle の厳密型、私有 token、weakref、fingerprint、attempt key の 5 点はすべて正しく通る。その後 `record_sealed_for_test()` は real `record_sealed_attempt_terminal()` を呼び、偽 capture 由来の terminal 行と evidence file を公開する。reflection も private issuer の直接呼出しも不要である。現行テストの赤は seam の防壁ではなく、fake 自身が行 195 で意図的に送出しているだけである。
- (d) certified wrapper だけが得られる launcher-origin capability を reserve state と handle fingerprint に束縛し、sealed terminal 発行時にも照合する。test seam はその capability を取得できない形にする。real adapter へ転送する fake を正面から使った負例も追加する。
- (e) 重大度: `blocker`

## 所見 2: terminal builder 後に protocol を再読するため、builder が E1 の閾値と測り直し理由を選べる

- (a) `protocol_sha256` の検査後も可変な `reservation.protocol` を保持し、untrusted terminal builder の実行後に `session_cv_max` を再読している。
- (b) [orchestrator/campaign/s8b_floor_attempt_launcher.py:608](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-review/orchestrator/campaign/s8b_floor_attempt_launcher.py:608)、[orchestrator/campaign/s8b_floor_attempt_launcher.py:1004](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-review/orchestrator/campaign/s8b_floor_attempt_launcher.py:1004)、[orchestrator/campaign/s8b_floor_attempt_launcher.py:1022](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-review/orchestrator/campaign/s8b_floor_attempt_launcher.py:1022)、[orchestrator/campaign/s8b_terminal_evidence.py:727](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-review/orchestrator/campaign/s8b_terminal_evidence.py:727)、[orchestrator/campaign/s8b_terminal_evidence.py:768](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-review/orchestrator/campaign/s8b_terminal_evidence.py:768)
- (c) 予約時の protocol を `{"reps": 3, "session_cv_max": "0.1"}` として正しい digest を束縛する。分散の大きい測定後、builder が closure 内の通常の dict を変更して `session_cv_max="1.0"` とし、その閾値で `valid=True`、`excluded_reason=None`、`terminal_status="observed"` の record を返す。leaf は変更後の閾値を使って同じ `observed` を再導出する一方、`attempt_binding.protocol_sha256` は元の binding からコピーする。adapter は durable claim と元の digest が等しいことしか確認せず、evidence の閾値をその digest へ再束縛しないため、実際には anomaly だった session が observed として通る。同じ再読により `perf_preflight_receipt_sha256` も builder 後に変更できる。
- (d) protocol と perf receipt を副作用前に canonical bytes として一度だけ snapshot し、`_ReservationPolicy` と adapter handle に保持する。builder 後の evidence はその snapshot から構築し、`session_cv_max` と receipt digest を durable binding へ再照合する。
- (e) 重大度: `blocker`

## 所見 3: terminal builder に渡した可変 probe と repetition evidence を、後から「私有 sink」として信頼している

- (a) launcher が分類に使った probe と観測値の可変参照を builder に公開し、builder 実行後の内容を terminal evidence の権威として再読している。
- (b) [orchestrator/campaign/s8b_floor_attempt_launcher.py:943](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-review/orchestrator/campaign/s8b_floor_attempt_launcher.py:943)、[orchestrator/campaign/s8b_floor_attempt_launcher.py:978](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-review/orchestrator/campaign/s8b_floor_attempt_launcher.py:978)、[orchestrator/campaign/s8b_floor_attempt_launcher.py:986](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-review/orchestrator/campaign/s8b_floor_attempt_launcher.py:986)、[orchestrator/campaign/s8b_terminal_evidence.py:663](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-review/orchestrator/campaign/s8b_terminal_evidence.py:663)、[orchestrator/campaign/s8b_terminal_evidence.py:739](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-review/orchestrator/campaign/s8b_terminal_evidence.py:739)
- (c) 分類前に `external_evidence_sha256` を計算した後、builder が `opened.probe_before["stderr"]` を変更し、campaign record にも変更後の probe を入れる。`competing` を変えなければ classification echo は同じなので core を通る。leaf は変更後の probe 同士だけを比較して新しい `probe_before_sha256` を作るが、分類 receipt 内の元の `external_evidence_sha256` とは照合しない。したがって実際に観測していない probe bytes と digest が封印される。`repetition_evidence` も tuple の内側が通常の dict で、同じ問題を持つ。
- (d) builder へ渡さない私有 canonical snapshot を probe、failure、launch failure、rep sink ごとに保持し、sealer はそれだけを読む。builder には別の深い copy または read-only view を渡す。分類 receipt の external evidence digest と terminal evidence の各 source digest も再照合する。
- (e) 重大度: `blocker`

## 所見 4: stateful Mapping は duration と binary digest の launcher gate にだけ正しい値を見せられる

- (a) launcher と leaf が `terminal.campaign_record` を別々に読むため、独自 `Mapping` が launcher gate と canonical evidence に異なる値を返せる。
- (b) [orchestrator/campaign/s8b_floor_attempt_launcher.py:838](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-review/orchestrator/campaign/s8b_floor_attempt_launcher.py:838)、[orchestrator/campaign/s8b_floor_attempt_launcher.py:850](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-review/orchestrator/campaign/s8b_floor_attempt_launcher.py:850)、[orchestrator/campaign/s8b_terminal_evidence.py:223](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-review/orchestrator/campaign/s8b_terminal_evidence.py:223)、[orchestrator/campaign/s8b_terminal_evidence.py:745](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-review/orchestrator/campaign/s8b_terminal_evidence.py:745)
- (c) builder は exact `FloorAttemptTerminal` を返すが、その `campaign_record` に custom `Mapping` を入れる。`get("duration_s")` と `get("binary_sha256_at_measure")` には launcher の正値を返し、`__iter__` と `__getitem__` には偽値を持つ exact 30-key record を返す。launcher の検査は通り、leaf の `dict(value)` は偽値側を snapshot する。raw bytes を偽 record に合わせれば leaf と adapter の後段検査も通り、偽 duration と binary digest が proof chain に入る。
- (d) terminal record を一度だけ strict canonical snapshot に変換し、その同一 snapshot に対して launcher facts を検査して、そのまま sealer へ渡す。複数回の duck-typed Mapping 読取りをしない。
- (e) 重大度: `blocker`

## 所見 5: crash-side durable identity 再検査から holdout、configuration、retry ordinal が抜けている

- (a) adapter は `campaign_record.holdout_id`、`configuration_id`、`retry_ordinal` を real slot と比較せず、公開 reservation を権威にした draft を昇格できる。
- (b) [orchestrator/campaign/s8b_terminal_evidence.py:713](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-review/orchestrator/campaign/s8b_terminal_evidence.py:713)、[orchestrator/campaign/s8b_attempt_registry.py:1282](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-review/orchestrator/campaign/s8b_attempt_registry.py:1282)、[orchestrator/campaign/s8b_attempt_registry.py:1324](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-review/orchestrator/campaign/s8b_attempt_registry.py:1324)
- (c) real adapter から正当な `CapturedObservation` を得た後、9 binding field は real state と同じだが、`slot_id` の 1、2、5 番目だけを偽装した構造的 reservation を public `seal_terminal_evidence()` に渡す。campaign record の 3 field をその偽 slot に合わせると leaf は受理する。adapter は real slot を durable claim の `key` と比較するが、campaign record の該当 3 fieldとは比較しないため、binding、claim、raw digest の全 gate を通って偽 identity が公開される。private issuer の直接呼出しは不要である。
- (d) `_assert_terminal_durable_identity()` で evidence の `holdout_id == slot.freeze_holdout_key`、`configuration_id == slot.configuration_id`、`retry_ordinal == slot.attempt_ordinal` を明示的に検査する。real observation と偽 structural reservation の組を使う負例を置く。
- (e) 重大度: `blocker`

## 所見 6: OSError の subclass は launcher が捕捉してから evidence gate が拒否する

- (a) launcher の捕捉集合と evidence の型名集合が一致せず、正当な `FileNotFoundError` などの `OSError` terminal が失われる。
- (b) [orchestrator/campaign/s8b_floor_attempt_launcher.py:420](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-review/orchestrator/campaign/s8b_floor_attempt_launcher.py:420)、[orchestrator/campaign/s8b_floor_attempt_launcher.py:929](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-review/orchestrator/campaign/s8b_floor_attempt_launcher.py:929)、[orchestrator/campaign/s8b_floor_attempt_launcher.py:967](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-review/orchestrator/campaign/s8b_floor_attempt_launcher.py:967)、[orchestrator/campaign/s8b_terminal_evidence.py:60](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-review/orchestrator/campaign/s8b_terminal_evidence.py:60)、[orchestrator/campaign/s8b_terminal_evidence.py:313](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-review/orchestrator/campaign/s8b_terminal_evidence.py:313)
- (c) capture が `FileNotFoundError(2, ...)` を送出すると、launcher は `OSError` として捕捉するが `_failure_evidence()` は具体名 `FileNotFoundError` を保存する。leaf は exact 集合の `OSError` しか認めず、seal 時に拒否する。open 側はさらに広い `Exception` を terminalize しようとするため、`ValueError` なども同じ位置で拒否される。これは予定された launcher 捕捉入力の受理集合を縮める。
- (d) `TimeoutExpired`、`OSError`、`RuntimeError` の順で基底カテゴリ名へ正規化する。open 側も契約の 3 クラスへ捕捉を絞るか、集合外例外を terminal 化しない経路として明示する。
- (e) 重大度: `must-fix`

## 総括

- 判定: `no`
- 件数: blocker 5 / must-fix 1 / nit 0
- 攻撃したが破れなかった箇所:
  - S1 の `terminal-failure` と `not-consumed` は、どちらも `_assert_null_matrix()` の同じ枝を通る正例と負例があり、恒真 gate ではなかった。
  - S2 は old replay と candidate replay が独立に evidence loader を呼ぶ構造で、前段の赤による見かけの kill ではなかった。
  - `ValidatedTerminalEvidence` へ単に `object()` token を入れる偽造は、adapter consumer 側の token identity 検査で止まる。成功には reflection または private issuer の直接呼出しが必要で、この単独経路は契約 6.4 の除外内だった。
  - row と file の 11 項目には `finished_at` も含まれ、digest、canonical bytes、exact keys、binding、missing file、no-follow regular file の再検査も存在した。
  - `records`、`threads`、`workload`、`cell_id`、`attempt_id`、`mode` は durable claim との再照合があり、単純な terminal record 改変では破れなかった。
  - v1 は既定の `retryable_reason_field="failure_reason"`、既存 event keys、空の retryable reason 集合を維持しており、静的には既存 null matrix の受理集合を広げていない。
- 指示どおり pytest は実行せず、commit `d03b26773` と `d52b2f833` を静的に審査した。