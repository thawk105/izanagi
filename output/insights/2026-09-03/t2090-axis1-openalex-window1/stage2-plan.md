## 実装プラン

- S1 の編集対象は [runner.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/orchestrator/axis1_search/runner.py:230) と [test_axis1_search_runner.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/orchestrator/tests/test_axis1_search_runner.py:1457) の 2 ファイルだけとする。S2・S3、完走条件 1〜6、validator、checkpoint、CLI は変更しない。

- `runner.py:241-244` の `QuotaObservation.permits_next` に失効判定を集約する。既存の `reserve` positional API を壊さないため、署名案は次とする。

```python
def permits_next(
    self,
    reserve: int = QUOTA_RESERVE_CREDITS,
    *,
    now_epoch: float | None = None,
) -> bool:
```

- 変更後の判定式は次とする。

```text
known =
    remaining is not None
    and credits_per_request is not None

balance_ok =
    known
    and remaining - reserve >= credits_per_request

window_elapsed =
    known
    and now_epoch が有効な epoch 秒
    and reset_seconds が bool でない 0 以上の int
    and observed_at_utc が UTC の ISO 8601 として解釈可能
    and now_epoch >= observed_at_epoch
    and now_epoch >= observed_at_epoch + reset_seconds

permits_next = balance_ok or window_elapsed
```

- `observed_at_utc` は現行 writer が出す末尾 `Z` の形式だけを失効根拠として認め、`datetime.fromisoformat` と `timezone.utc` で解釈する。`timedelta`、`datetime`、`timezone` はすでに `runner.py:12` で import 済みなので新しい依存は不要。変換時の `TypeError`、`ValueError`、`OverflowError`、`OSError` は捕捉して `window_elapsed=False` とする。

- `reset_seconds` は OpenAlex 応答の `x-ratelimit-reset` を `runner.py:535` で整数化した「観測時点から reset までの秒数」である。観測時刻は `runner.py:1786` の `observe_quota(response, request_id, clock())` から入り、`runner.py:511-535` が同じ値を `observed_at_utc` として保存する。したがって deadline は新 field なしで `observed_at_utc + reset_seconds` と再導出できる。

- 現在時刻は既存の wall-clock 注入 seam を使う。`_run_leaf_impl` の `clock` は `runner.py:1587` で既定値 `time.time`、公開入口も `run_leaf` の `runner.py:2361` と `resume_from_checkpoint` の `runner.py:2408` から同じ seam を渡す。次の全 gate を更新する。

  - `runner.py:1666`: 起動直後または次頁の発行前を `latest_quota.permits_next(now_epoch=clock())` にする。
  - `runner.py:1707`: retry 発行前も同じ式にする。
  - `runner.py:2123-2127`: 応答後、次 cursor を checkpoint へ止める判定も同じ式にする。

- `runner.py:1646` の初回 load と `runner.py:1706` の再 load はそのまま残す。後者は別 process が書いた、より新しい観測を発行直前に取り込む役割がある。

- `runner.py:716-720` の `_load_persisted_quota` は変更しない。失効した観測も証拠として読み出し、発行可否だけを `permits_next` が現在時刻との組で判断する。このため `runner.py:1706` の `loaded or latest_quota` が失効済み観測を復活させる問題も生じない。観測自体を `None` に変換せず、checkpoint や失敗結果に残せる。

- fail-closed は「失効を根拠とする追加受理」に対して維持する。

  - `remaining` または `credits_per_request` が無ければ、新旧とも偽。
  - 残量式が偽で `reset_seconds is None` なら偽。
  - 残量式が偽で `observed_at_utc` が壊れていれば偽。
  - `now_epoch < observed_at_epoch`、すなわち時計が巻き戻っていれば偽。
  - 負の reset、bool、異常に大きい値、無効な現在時刻も偽。
  - deadline ちょうどは `>=` により「窓が明けた」と扱う。

  既存の残量式が真の入力は、時刻情報にかかわらず従来どおり受理する。これにより変更は純粋な受理集合の拡大となり、失効情報の欠陥を理由に既存受理を狭めない。

- 持続化 shape は変更しない。`state/runtime.json` の root は `runner.py:620-626` の v1 のまま、quota は `runner.py:723-728` の既存 `asdict(observation)` のままとする。`observed_at_utc` と `reset_seconds` はすでに保存済みである。

- 旧 v1 shape は `runner.py:672-685` で従来どおり読む。`reset_seconds` 欠落は `.get()` により `None` となり、残量不足なら発行を止める。`observed_at_utc` が壊れた文字列なら失効判定だけが偽になる。必須キー自体の欠落で loader が例外停止する既存の fail-closed 挙動も変えない。

- checkpoint の quota は別の複製である。`checkpoint.py:521-535` と schema `axis1_search_checkpoint.schema.json:170-198` は変更不要であり、新 field も schema version 更新も不要。

## 採らなかった案と理由

- `_load_persisted_quota` で失効済み観測を `None` にする案は採らない。

  - 「観測なし」と「古い観測あり」を同じ値に潰す。
  - `runner.py:1706` の `or latest_quota` が古い in-memory 観測を復活させうる。
  - 新しい HTTP が quota header を返さず失敗した場合、checkpoint/result から最後の観測証拠が消える。
  - load 時刻ではなく、実際の各発行 gate の時刻で判断する方が意味に合う。

- `state/runtime.json` に `reset_at_utc` を追加する案は採らない。既存の 2 field から一意に再導出でき、shape・migration・旧 bundle 互換処理を増やす理由がない。

- 3 箇所の runner gate に timestamp parse を個別実装する案は採らない。`1666`、`1707`、`2127` で判定がずれる危険がある。

- `time.time()` を `permits_next` 内で直接呼ぶ案は採らない。既存の `clock` seam を迂回し、境界・巻き戻りを決定的にテストできなくなる。

- `time.monotonic()` は採らない。永続化された ISO UTC は process をまたぐため、process-local な monotonic clock と比較できない。`HTTPSOnlyTransport` の `runner.py:84` にある monotonic clock は通信経過時間用であり、quota 窓には使えない。

## 受理集合の変化 (署名 + 通る正例)

新たに受理される入力の署名は次である。

```text
QuotaObservation(
    remaining = r,
    credits_per_request = c,
    reset_seconds = s,
    observed_at_utc = t,
    ...
).permits_next(reserve=R, now_epoch=n)

where:
    r, c are present
    r - R < c                         # 旧判定は偽
    s is an integer and s >= 0
    t is valid UTC
    n >= epoch(t)                     # 巻き戻りでない
    n >= epoch(t) + s                 # 記録した窓が明けた
```

通る正例:

```text
observed_at_utc       = 2026-09-02T00:00:00Z
observed epoch        = 1788307200
reset_seconds         = 3600
remaining             = 35
credits_per_request   = 10
reserve               = 30
now_epoch             = 1788310800  # 2026-09-02T01:00:00Z
```

旧式は `35 - 30 >= 10` が偽。新式は deadline ちょうどなので真となり、次窓の最初の request を発行できる。

## テスト計画 (nodeid)

既存の枠 gate 関連 nodeid は次のとおり。既存テスト本文・期待値は変更しない。

- `orchestrator/tests/test_axis1_search_runner.py::test_quota_reserve_stops_before_exhaustion`

  応答直後の `runner.py:2127` が低残量かつ未失効の観測で止まることを縛る。

- `orchestrator/tests/test_axis1_search_runner.py::test_quota_reserve_persists_across_leaf_sessions`

  `reset_seconds=None` の低残量観測が別 session の `runner.py:1666` でも HTTP 0 のまま止める。

- `orchestrator/tests/test_axis1_search_runner.py::test_429_pauses_quota_but_503_is_service_failure`

  retry 前の `runner.py:1707` を通り、quota 情報が不完全な 429 観測を fail-closed にする。

- `orchestrator/tests/test_axis1_search_runner.py::test_resume_merges_digest_verified_prefix_with_real_openalex_parser`

  十分な残量の持続観測が resume を妨げない既存正例。

- `orchestrator/tests/test_axis1_search_runner.py::test_failure_without_quota_headers_preserves_known_values`

  quota merge が既知の残量・request cost を失わないことを縛る隣接テスト。

- `orchestrator/tests/test_axis1_search_runner.py::test_partial_bundle_reports_checkpointed_leaf_and_completes_validation`

  quota 停止 checkpoint が partial bundle として扱われる既存期待を縛る。

追加 nodeid 案:

- `orchestrator/tests/test_axis1_search_runner.py::test_unexpired_persisted_quota_stops_before_http`

  有効な `observed_at_utc`、低残量、`reset_seconds=60`、`now=deadline-1` を事前保存し、`paused_quota`、`request_count == 0`、transport call 0 を確認する。

- `orchestrator/tests/test_axis1_search_runner.py::test_expired_persisted_quota_allows_first_request_of_next_window`

  同じ観測で `now=deadline` とし、transport call が 1 回発生して `quota_reserve` による開始前停止にならないことを確認する。これが S1 の正例。

- `orchestrator/tests/test_axis1_search_runner.py::test_persisted_quota_without_reset_stops_before_http`

  低残量、`reset_seconds=None`、十分後の現在時刻でも HTTP 0 を確認する。

- `orchestrator/tests/test_axis1_search_runner.py::test_malformed_persisted_quota_timestamp_stops_before_http`

  低残量、正の reset、壊れた `observed_at_utc` で HTTP 0 を確認する。

- `orchestrator/tests/test_axis1_search_runner.py::test_persisted_quota_clock_rollback_stops_before_http`

  低残量、正しい時刻と reset を持つが `now < observed_at` とし、HTTP 0 を確認する。

この段では pytest を実走しておらず、緑とは報告しない。

## 波及 (呼び出し元の全列挙)

`permits_next` の呼び出しは合計 3 箇所で、すべて `runner.py` 内にある。

1. `runner.py:1666` — 各頁の初回発行前。
2. `runner.py:1707` — 各 retry の発行前。
3. `runner.py:2127` — 成功頁の後、次 cursor を発行せず checkpoint 化する判定。

関連する直接 consumer は次の 3 ファイルである。

- `orchestrator/axis1_search/runner.py`

  `QuotaObservation` 定義 `230-244`、生成 `511-539`、runtime 復元 `672-685`、merge `688-713`、load `716-720`、persist `723-730`、checkpoint 用変換 `1360-1378`、上記 3 gate、`__all__` の `2445`。

- [__init__.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/orchestrator/axis1_search/__init__.py:54)

  `QuotaObservation` を `63` で import、`99` で公開 re-export している。名前や class shape は変えないので編集不要だが、`permits_next` の追加 keyword は公開 API に波及する。

- `orchestrator/tests/test_axis1_search_runner.py`

  `QuotaObservation` を `24`、`_persist_quota` を `31` で直接 import。持続観測の fixture は `1676-1689` と `2311-2324` にある。

transitive な production caller は [run_axis1_search.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2090-openalex-fetch/tools/run_axis1_search.py:158) の `run_leaf` と `resume_from_checkpoint` の 2 箇所だけで、署名変更はないため編集不要。

`validator.py`、`checkpoint.py`、`tools/check_axis1_search.py` は runtime quota gate を呼ばない。checkpoint に複製された quota の検証 shape も変わらない。

## 親 brief への反論

- M5 は本質的に正しい。`permits_next` は `runner.py:241-244` で残量と request cost しか見ず、reset は取得 `535`、復元 `681`、保存 `725-728` されるだけである。ただし gate 列挙が不完全で、`runner.py:2127` に 3 個目の `permits_next` 呼出しがある。また `1646` 自体は gate ではなく load である。

- M6 は production CLI 経路について正しい。checkpoint の commit は `runner.py:2333` で resume に渡り、CLI は `tools/run_axis1_search.py:118-119` で CLI 値との不一致を拒否し、`validator.py:766-769` が `HEAD == registration_commit` と登録 path の clean を要求する。ただしこの保証は runner 内部の絶対 invariant ではない。公開 `resume_from_checkpoint` は `runner.py:2402-2424` で caller 提供の `preflight` を受け、直接 API から `preflight=True` を渡せる。M6 は「正規 CLI 経路では」と限定すべきである。

- M7 の結論は正しい。`tools/run_axis1_search.py:52-75` と `tools/check_axis1_search.py:51-70` の登録集合に runner、両 CLI、tests が含まれる。旧 base と byte 比較されるのは `validator.py:20-25` の 3 prefix だけである。ただし「clean だけ」は少し省略が強い。`HEAD == registration_commit` と clean の組合せにより runner/CLI は登録 commit の bytes に間接的に固定される。正確には「旧 predecessor bytes には固定されず、新しい登録 commit の clean bytes に固定される」であり、S1 を commit してその SHA を登録 commit にする結論は成立する。

- M9 の live-code closure 3 点という結論は正しいが、記載された `git grep -ln` が 3 file だけを返すという含意は現物と食い違う。同じ検索は現在 8 tracked file を返し、上記 3 file に加えて `output/insights/` の歴史記録 5 file も命中する。それら 5 file は実行 consumer ではないので、正確な表現は「検索結果 8 file のうち live-code consumer は 3 file」である。

- M9 の runtime/checkpoint 分離は正しい。runtime root は `runner.py:620-626`、checkpoint quota は `checkpoint.py:521-535` と checkpoint schema `170-198` にあり、runtime state の schema ではない。

## 総括

失効は load 時のデータ消去ではなく、`QuotaObservation.permits_next` に集約し、3 個すべての発行 gate から既存の `clock` を渡す。これにより、低残量でも `observed_at_utc + reset_seconds` を過ぎた観測だけが新たに受理される。reset 欠落、壊れた時刻、時計巻き戻りは追加受理されず、runtime/checkpoint の shape、完走述語、S2・S3 は一切変えない。