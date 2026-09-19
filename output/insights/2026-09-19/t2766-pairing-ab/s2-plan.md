# 段 2 plan (親起草、軽量版) — [T-2766] opt-in pairing と実受入 A/B 対比較

前提は `s1-brief.md`。file:line は tip `a99425b66` の現物。

## P1. opt-in pairing (Codex author、`orchestrator/tests/conftest.py`)

1. 定数 (`conftest.py:1019-1021` の近傍): `_ACCEPTANCE_PAIRING_ENV = "IZANAGI_ACCEPTANCE_PAIRING_V1"`、`_ACCEPTANCE_PAIRING_TOKEN = "t2766-min-cost-partners"`、`_ACCEPTANCE_PAIRING_PROPERTY = "izanagi_acceptance_pairing_v1"`。窓は既存 `_ACCEPTANCE_INITIAL_DISTRIBUTION_UNITS` (96) と `96 // 2` (48) から導き、nproc を参照しない (G10/G11)。
2. 判定関数 `_acceptance_pairing_opted_in() -> bool` (`_growth_holds_opted_in` `conftest.py:1885-1897` と同型): 未設定 / 空 → False、exact token → True、他の非空値 → `pytest.UsageError` (fail-closed)。
3. 後段関数 `_pair_initial_distribution_units(ordered_units) -> list` (`_reorder_acceptance_items_by_duration` `conftest.py:1783-1830` の `ordered_units` 確定直後、`reordered` を作る前に opt-in 時だけ呼ぶ):
   - `realized = sorted(ordered_units, key=lambda u: -len(u["items"]))` (xdist 3.8.0 `loadscope.py` `schedule()` の安定 sort と同一式。`loadscopereorder=False` の走は `_acceptance_options_allow_reordering` `conftest.py:1836-1862` が既に reorder 自体を止める)。
   - `len(realized) < 96` なら pairing せず `ordered_units` をそのまま返す (小さい focus 走で無害。property も付けない)。
   - `head = realized[:48]`、候補 = `realized[48:]`。partner = 候補を `(effective_cost, realized 内位置)` 昇順に並べた先頭 48 (effective_cost = known なら `cost`、未知なら既存の `unknown_cost`)。`rest` = 候補から partner を除いた realized 順。`paired = head + partner + rest`。
   - 検算: `sorted(paired, key=-len)` が `paired` と同一 (scope 列で比較) でなければ `pytest.UsageError("acceptance pairing infeasible: cardinality reorder would change the intended queue")` で fail-closed (B と名乗る走が黙って A に落ちるのを防ぐ)。
   - 返り値の各 unit に `pairing_rank` (paired 内位置) と `pairing_partner` (bool) を付け、呼び出し側が各 item の `user_properties` に `(_ACCEPTANCE_PAIRING_PROPERTY + "_rank", str(rank))` と partner なら `(_ACCEPTANCE_PAIRING_PROPERTY + "_partner", "1")` を extend する (hold の `user_properties.extend` `conftest.py:2225-2231, 2251-2257` と同型)。opt-in でない走は property を一切足さない。
   - `_replace_acceptance_items` (`conftest.py:1763-1780`) の identity multiset 検査はそのまま通す。
4. 既存の A 経路は byte 同一の順序を保つ: opt-in False のとき `_reorder_acceptance_items_by_duration` の挙動・返り値・副作用は現行と完全一致 (負例で固定)。

## P2. env 伝播 (Codex author、`tools/pegasus/dispatch_compute.py:118-131`)

`TASKS["tests"].env_allowlist` に `"IZANAGI_ACCEPTANCE_PAIRING_V1"` を 1 行追加 (comment 1 行: T-2766 の測定 opt-in、既定 off)。`orchestrator/tests/test_pegasus_dispatch_compute.py:6260-6269` `test_tests_task_env_allowlist_is_exact` の集合に同 key を追加。`_child_environment` (`:1661-1671`、inherit) と `_run_internal_acceptance_shard` (`tools/run_tests.py:1460-1530`、`os.environ.copy()`) は変更なし。

## P3. test (Codex author、`orchestrator/tests/test_acceptance_schedule_order.py`)

既存 harness (`_Item` `:59`、`_durations` `:97`、`_OptionConfig` `:862`、`_run_scheduler_arm` `:1560-1612` = 実 `LoadGroupScheduling` + `_TracingWorkQueue`) を再利用し、G12 として:
- 正例: opt-in (monkeypatch で exact token) + 120 unit (cost 降順、cardinality は先頭数 unit が 2〜3、残り 1) で、`_run_scheduler_arm(48, ...)` の `dequeue_trace[48:96]` が候補中最小 cost の 48 scope と一致し、`[:48]` は不変、残りは元順。各 item の `user_properties` に rank / partner が付く。
- 負例 1: env 未設定 → `dequeue_trace` と `user_properties` が現行 (opt-in 無し) と完全一致 (before/after の逐語比較)。
- 負例 2: env に別の非空値 → `pytest.UsageError`。
- 負例 3: cardinality で不成立になる fixture (候補側に 2 item unit を混ぜ、head に 1 item unit がある) → `UsageError` で fail-closed。
- 境界: unit 数 < 96 → pairing なし・property なし。nproc 16 / 32 / 48 で `collection` 順が同一 (G10 と同型、worker 数非依存)。
- pin 更新: `test_pegasus_dispatch_compute.py::test_tests_task_env_allowlist_is_exact`。

## P4. 変異 matrix (DW-M01、段 4 で確定)

| # | 変異 (1 理由) | 期待 kill |
|---|---|---|
| M1 | partner 選択を `(cost, pos)` 昇順 → 降順 | 正例 (dequeue_trace[48:96]) |
| M2 | 窓 `[:48]` → `[:47]` (head の幅) | 正例 |
| M3 | opt-in 判定を恒真 (token 不問) | 負例 1 (未設定で順序が変わる) / 負例 2 |
| M4 | cardinality 検算を削除 | 負例 3 |
| M5 | property 付与を削除 | 正例 (user_properties) |
| M6 | allowlist の key を削除 | exact pin |

## P5. 測定 (親が実行、実装面の script は Codex author が job dir 用に書く)

- 投入形 (runbook §7.3): `python3 tools/dev_wave_wait.py acceptance --wave dev-wave-t2766-pairing-ab --lease-dir /work/1/SFC/tanab/dev-wave-jobs/land-lease --receipt-file <J>/acceptance-receipt-<k>.json --log-file <J>/acceptance-child-<k>.log --merge-message-file <J>/merge-msg.txt -- python3 tools/run_tests.py`。B は launcher script の中で `export IZANAGI_ACCEPTANCE_PAIRING_V1=t2766-min-cost-partners`。A は unset。launcher / detach は `.sh` 2 枚 (DW-C01)。
- 走ごとに: 投入直前の `git rev-parse HEAD` / `main`、他 wave の受入 leader 数 (`ps -eo args | grep dev_wave_wait.py acceptance` から自分を除く)、login load、`date` を job dir に記録。完了後に `python3 tools/wave_land_window.py release --lease-dir ... --wave dev-wave-t2766-pairing-ab`。session dir (`/work/1/SFC/tanab/.izanagi-acceptance-shards/<session>/`) は receipt の `session_root` から同定し、`shard-*/junit.xml` と `report.json` を job dir へ複製 (原本は残す)。
- 順序: 対 1 = A,B / 対 2 = B,A / 対 3 = A,B。無効対は同順序で追加。投入上限 12。測定中に他の自 job を走らせない (D357)。走行中は worktree に書かない。
- 前処理: 投入前に login で `python3 tools/run_tests.py --collect-only -q -p no:cacheprovider` を 1 回 (bytecode cache を warm、T-2710 §4)。
- 集計 script `t2766_ab_analyze.py` (Codex author、unit worktree の `probe-t2766/` に書き親が job dir へ退避): 入力 = 各走の receipt + 3 shard の junit / report + 台帳 + 走の env 記録。出力 = 対表 (W_max / W_0 / W_1 / W_2 / O / F / 最忙 worker items、ΔW、ΔW %)、B の witness 検証 (property の有無、partner 集合の offline 再計算との一致: junit の nodeid を `_acceptance_loadgroup_scope` で unit 化し、台帳 cost で cost 順 → cardinality 安定 sort → 候補中最小 48 = property の partner 集合)、(P4) の tree 一致判定 (各走の tested tip の `git ls-tree` で `orchestrator` `tools` `hooks` `external` と root の非 docs entry を比較)、事前登録の判定 (i)/(ii)/(iii)。JSON と Markdown の両方を出す。

## P6. 記録と land

- 測定 tip = 実装 commit の後の tip (docs commit を含んでよい。test tree は実装 commit と同一)。
- 測定後に `impl-t2766-pairing-optin` branch を測定 tip に作って残す。landing branch は main から `record-dev-wave-t2766-pairing-ab` を切り、insight (README・逐語・集計出力・s1〜s4) と spool fragment だけを commit → 最終受入 1 走 (A、default) → land。実装は main に入れない (P2)。
- README: 対表・判定・witness・除外走・限界。decisions fragment: 測定結果の事実と「採用は諮る / 見送り」のどちらかの提示 (採用の裁定はしない)。worklog fragment。
