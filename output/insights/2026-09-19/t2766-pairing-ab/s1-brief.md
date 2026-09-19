# 段 1 brief — [T-2766] shard 内 pairing の実受入 A/B 対比較

wave `dev-wave-t2766-pairing-ab`、branch `worktree-dev-wave-t2766-pairing-ab`、着手 tip = local main `a99425b66` (2026-09-19 21:34 JST、着手直前に `--ff-only` で取り込み)。専用 handoff は repo 外 `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2766-pairing-ab/HANDOFF.md`。

## 研究前進 (土台)

受入全走の最遅 shard の wall (直近 40 session の shard-0 は 285〜446 秒、最忙 worker は item 2 個で 217〜377 秒) が 1 wave あたり 6〜7 分を占め、300 秒目標 (T-2273) に対して pairing は「相方 ≈ 20 秒 (5.8 %)」の除去を狙う最小差分 (order だけ、受理集合・unit 境界・group・hold 不変)。完了判定 = 同一 tip の実受入で有効な A/B 対を 3 組以上取り、事前登録の規則で中央値差・対の数・方向を記録し、採否の裁定パッケージ (効果あり) か見送り (効果未確立) のどちらかを書く。どちらの結果も成果物であり、効果が示せなければ land しない (D104 決定 3、T-2766 起票文)。

## scope と確定済みユーザー裁定

- D2148 項 6 (2026-09-18): shard 内 pairing を同一 tip の実受入で 3 対以上比較する。replica の 52〜69 秒差は採用効果ではない。計算ノードで実測し、受理集合は維持する。e2e の分割・縮約、別系列への移動、成分粒度の変更、D2068 却下 3 案、新 slot / FIFO は採らない (scope 外)。
- 依頼 (command 引数): A/B 交互 3 対以上・計算ノードで対比較。結果は中央値差と対の数で記録し、改善認定は同 job (= 同一の対) でだけ行う。実装を採用済みとして本番に入れない。実装面は Codex author (D95)。
- 既存被覆 (純増だけ書く): T-2710 は replica shard-0 (1 ノード、同時 3 shard 無し、cold cache) で B を probe plugin により実現し、配布 (48 worker の受信 collection が意図順と一致、最長 node の worker の 2 個目が cost 0.0) を確認済み。本 wave の純増 = (i) 実受入 (3 shard、`tools/dev_wave_wait.py acceptance` 経由、warm cache) で B を発火させる opt-in 経路、(ii) 同一 tip の対比較 3 組以上、(iii) B 発火の直接観測 (D104 決定 4)、(iv) 順序依存 test の不在検査 (B が全走緑)。

## 不変条件

1. 受理集合・成分粒度・hold・group・unit 境界を変えない (規律 2、D2068 / D2121 / D2128)。opt-in 未設定 (A) の順序は現行と byte 同一 (負例で固定)。
2. 実装は opt-in (既定 off、exact token でだけ発火、他の非空値は `pytest.UsageError` で fail-closed。`IZANAGI_RUN_GROWTH_HELD_TESTS` と同型)。default を変えない。
3. 測定中は自分の他 job を同時に走らせない (D357)。A/B は逐次・交互で、1 対 = 隣接 2 走。同 wave worktree から投入し、走行中は worktree に 1 byte も書かない。
4. 判定規則は結果を見る前に固定する (§事前登録)。D357 の 10 % 規則は 1 走同士 (= 1 対) の差に適用し、中央値差には適用しない。3/3 一致を有意差判定にしない。
5. 実装の bytes は Codex author が書く。親は brief・裁定・commit・受入投入・集計・記録だけ。

## 割れうる前提 (親の provisional 裁定・攻撃対象)

- (P1) **B の発火経路 = 環境変数 opt-in。** `PYTEST_ADDOPTS` / `PYTEST_PLUGINS` は待ち手が claim 前に rc=2 で拒否し (`tools/dev_wave_wait.py` `_acceptance_environment_preflight`、runbook §7.3)、`run_tests.py` の `_is_acceptance_run` も default-deny に落ちるため使えない。login → 計算ノードへ渡る env は `tests` task の `env_allowlist` だけ (`tools/pegasus/dispatch_compute.py:118-131`、qsub は `-V` を付けない) なので、新 env `IZANAGI_ACCEPTANCE_PAIRING_V1` を allowlist に足す (exact pin `test_tests_task_env_allowlist_is_exact` を同時更新)。`hold_inventory` は静的列挙で影響なし。代案 (tracked flag file を B 用 commit で切替) は tip が変わり「同一 tip」を破るので不採用。
- (P2) **実装は land しない (impl branch に保存)。** 効果の有無にかかわらず本 wave は実装を main へ入れない。landing branch は main + 記録 (insight + spool fragment) だけとし、測定 tip は `impl-t2766-pairing-optin` として branch を残す (D104 決定 3、2026-09-16 の対計測 wave の precedent)。代案 = 既定 off の opt-in を land して再現性を main に置く。ユーザー文言「採用済みとして本番に入れない」の最も保守的な読みを採る。
- (P3) **B 発火の witness = junit `<property>`。** production の `report.json` の `worker_collection_digests` は順序非依存 (records / selected を sort した digest、`tools/acceptance_shards.py:895-921, 1013-1035`) で順序を証言しない。opt-in 時だけ conftest が各 item の `user_properties` に最終 unit 順位と partner 印を足し、junit.xml から「意図順」と「partner 集合」を再構成する。A では property を足さない。実配布 (どの worker が何を走らせたか) は production 出力に無く、`worker_occupancy` の最忙 worker の items / duration を記述的に併記する。
- (P4) **対の有効条件 = 両走の tested tip の非 docs 木が同一。** 待ち手は claim 直後に main を取り込む (runbook §7.3) ので隣接 2 走でも tip が変わりうる。`orchestrator/`・`tools/`・`hooks/`・`external/`・root の設定 file の tree hash が両走で一致すれば有効、不一致なら対を捨てて追加する。
- (P5) **段構成 = 軽量版 + 敵対相談 1 本 (2 レンズ) + 段 6 レビュー 1 本。** 段 2 は親が file:line で起草する。実装面があるので段 5 author と段 6 fix 子は必須、変異 matrix 必須。

## 事前登録 (結果を見る前に固定。段 4 で確定)

- 指標: W = 各 shard の JUnit `<testsuite time>`、W_max = 3 shard の最大 (受入 wall の代理)、W_0 = shard-0。O = `worker_occupancy` の最大 duration、F = W − O、最忙 worker の items 数。対ごとに ΔW = W_max(A) − W_max(B) (正 = B が短い)、ΔW/W_max(A)。
- 対の構成: 3 対以上、順序は対 1 = A→B、対 2 = B→A、対 3 = A→B (交互)。各走は前走の完了後に投入し、投入前に他 wave の受入 leader 数と load を記録する。rc≠0・赤 (非帰属の F945 型を含む)・receipt 不発行・(P4) 不成立の走を含む対は無効とし、同じ順序で対を追加する。投入上限 12 走。
- B の発火確認: B 各走の 3 shard の junit.xml に pairing property が存在し、partner 集合 = その shard の cost 順 realized order の 49 位以降で最小 cost の 48 unit (台帳 `acceptance_duration_ledger.json` と junit の nodeid から offline 再計算) と一致。A 各走には property が無い。不一致の B 走は無効。
- 判定 (D357 / D1260 / T-2710 事前登録と整合): (i) 有効 3 対以上で全対 ΔW > 0 かつ 中央値 ΔW / 中央値 W_max(A) ≥ 10 % → 「実受入で方向一致の観測差 (≥10 %)」、採否の裁定パッケージをユーザーへ返す (本 wave では採用しない)。(ii) 全対同符号だが中央値差 < 10 % → 「D357 の変化なし域、方向は一致」、見送りとして諮る。(iii) 符号不一致 → 「効果未確立」、見送り。いずれも中央値差・対の数・各対の値・W_0 と F の内訳を併記。
- 失敗走の扱い: 表に「除外 (理由)」で残す。置換は対単位。

## 成果物

- 実装 (Codex author、impl branch): `orchestrator/tests/conftest.py` の `_reorder_acceptance_items_by_duration` の後段 1 関数 + opt-in 判定 + property 付与、`tools/pegasus/dispatch_compute.py` allowlist 1 行、`orchestrator/tests/test_acceptance_schedule_order.py` に正例・負例・realized order (LoadGroupScheduling 実物で dequeue trace) の test、`test_pegasus_dispatch_compute.py` の exact pin 更新。
- 変異 matrix (DW-M01): partner 選択を max cost にする / 窓を 49〜96 以外にする / opt-in 判定を恒真にする / property を落とす、の 4 変異以上。
- 記録: `output/insights/2026-09-19/t2766-pairing-ab/README.md` (対表・判定・逐語)、spool fragment (worklog / decisions)。
- 受入: 測定 6 走以上 + landing tip の最終受入 1 走。

## 変更面 (実アンカー)

| 面 | file:line | 変更 |
|---|---|---|
| 並べ替え本体 | `orchestrator/tests/conftest.py:1783-1830` `_reorder_acceptance_items_by_duration` | `ordered_units` 確定後、opt-in 時だけ後段関数で 49〜96 位を入れ替え |
| 定数 | `orchestrator/tests/conftest.py:1019-1021` `_ACCEPTANCE_INITIAL_DISTRIBUTION_UNITS = 96` | 窓 = 先頭 48 固定 + 49〜96 位。48 は `96 // 2` から導く (nproc 非依存、G10/G11) |
| opt-in 判定 | `orchestrator/tests/conftest.py:1885-1897` `_growth_holds_opted_in` (同型) | exact token / 空 / 未設定 だけ受理 |
| hook | `orchestrator/tests/conftest.py:2201-2283` `pytest_collection_modifyitems` (yield 後) | 変更なし (後段関数は reorder 関数の中から呼ぶ) |
| xdist 実配布 | `xdist/scheduler/loadscope.py` `schedule()` (3.8.0): `-len(items)` 安定 sort → node i に unit i → `_reschedule` で pending ≤ 2 の node に次 unit | realized order = cardinality 安定 sort 後。後段関数は realized order 上で 49〜96 位を選び、再 sort で不変を検算、不成立は UsageError |
| env 伝播 | `tools/pegasus/dispatch_compute.py:118-131` `TASKS["tests"].env_allowlist` | `IZANAGI_ACCEPTANCE_PAIRING_V1` を追加 |
| pin | `orchestrator/tests/test_pegasus_dispatch_compute.py:6260-6269` | 集合に 1 key 追加 |
| shard 子 | `tools/run_tests.py:1460-1530` `_run_internal_acceptance_shard` (`os.environ.copy()`) | 変更なし (継承で届く) |
| witness | junit `<property>` (conftest の hold 系 `user_properties` と同型、`conftest.py:2225-2231`) | opt-in 時だけ付与 |
| 順序 test | `orchestrator/tests/test_acceptance_schedule_order.py:1560-1612` `_run_scheduler_arm` (実 `LoadGroupScheduling` + tracing queue) | 同型 harness で dequeue trace の 49〜96 位を検算 |

## 模擬 / 実の差と前提実測

- 直近 40 session (2026-09-18 17:04〜09-19 08:21) の実測: shard-0 が最遅 (W 285〜446、最忙 worker gw5 items 2)、shard-1 232〜310、shard-2 206〜240、F ≈ 67〜70 秒。regime は T-2710 と同じ (最忙 worker の item 2 個)。
- 台帳 (`acceptance_duration_ledger.json`、24,379 nodeid): 0.01 秒未満 12,885 件、0.0 が 51 件 → partner 48 unit の cost は ≈ 0。
- xdist 3.8.0 の `LoadScopeScheduling.schedule()` を実物で確認 (cardinality 安定 sort → 初期 1 unit → `_reschedule` で 2 個目)。
- queue: 21:33 JST 時点で他 wave の受入 leader 1、load 6.75、gen_S に RUN 6 本、QUE 0。
- 実受入で B を走らせた事実は無い (本 wave が初回)。T-2710 の B は replica のみ。
