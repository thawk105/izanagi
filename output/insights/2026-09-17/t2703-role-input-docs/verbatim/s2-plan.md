## 前提の実測

指定の必読資料 7 本はすべて読めた。以下は指定 worktree の静的読取りに基づく案であり、書込み・pytest・checker 実行はしていない。行番号は編集前。

brief の主要な事実は現物と一致する。補正・留意点は次のとおり。

- `pipeline.py` の `CorrectnessWorkload` は現物では **L147–152**。200 records / t4 / skew0.9 / rr50 / rmw=true / max_ope5 / extime1 / reps1。
- `PerfConfig` 自体の既定は `extime=3, reps=5`（L184–190）。段 4 の `default_perf()` が **extime1 / reps2 に明示上書き**する（`p3_s4_loop.py:1565`）。この区別を文書に残す。
- `_closed_verify_workloads()`（`loop.py:153`）は mode 未指定または legacy で追加 verify を返さない。他 mode まで「verify 1 run」と一般化しない。
- throughput は `calibrator/analyze.py:252` の `statistics.median`。有効 throughput が 2 件なら算術平均。counters / walltime / maxrss の代表 rep とは別。
- `external/ccbench/include/ycsb.hh:22` の `ycsb_max_ope=10` は「1 transaction の総操作数」。既存説明の「平均 10 操作」「rr50 はトランザクションの 50%」も置換対象節内で正す。
- `_extend_t304_role_name_baseline` の本体は L661–696、呼出しは **L699**。新 helper はその呼出し直後、`_assert_same_structure`（L702）の前に置く。
- L372 の baseline JSON を AST から取り出して解析した。critic 旧 SHA は journal に **`[旧SHA, 1]` が 6 行**、report に **`[[旧SHA, 6]]` が 1 行**ある。既存 source 追随 helper は critic を更新していない。
- `git show 4c6f03048 -- .claude/agents/planner-v4.md` で、T-304 が planner 例から `last_delta_pct` を削除したことを確認した。D1860 の「role 例と live runbook の形を維持する」という前提は現在成立しない。今回は D2104 項 4 に従って runbook を追随させる。
- **M2 の期待結果は修正が必要。** `test_codex_agents.py:27` が checker を import し、`tools/check_codex_agents.py:44` が import 時に `load_role_specs(REPO)` を実行する。ledger をファイル上で旧 SHA に戻すと、個別 test node に到達する前に collection error になる。

## 編集案

以下の diff は `-` が置換前、`+` が置換後の逐語。追加のみの箇所は置換前が空。4 role の frontmatter L1–7 と JSON 例の key 集合は不変とする。

**1. `src/coder-leakproof-context.md:53–75`**

見出し L53 の直後へ適用版を挿入し、L55–75 を置換する。

````diff
 ## Measurement Setup (coder が参考にする workload 定義)

+適用版: 2026-09-17 改訂以降の走行用。`orchestrator/campaign/p3_s4_loop.py::default_perf()`、`pipeline.py::CorrectnessWorkload` / `PerfConfig`、`loop.py::_closed_verify_workloads()` の legacy mode に一致する。
+
-### Standard Contention Workload (テスト用)
+### Standard Contention Workload (段 4 の既定の配線確認用)
 ```
-1m_records / t48_threads / skew0.9_zipfian_access / rr50_readratio /
-rmw0_readmindwrite / max_ope10_ops_per_tx / extime3_execution_time_seconds
+100k_records / t4_threads / skew0.9_zipfian_access / rr50_readratio /
+rmw0_read_modify_write / max_ope10_ops_per_tx / extime1_execution_time_seconds / reps2
 ```

 解説:
-- `1m`: 100万レコード の key-value store
-- `t48`: 48 スレッド で実行 (hardware: 96 core × 2 NUMA)
-- `skew0.9`: 80% の access が top-20% の key に集中 (高 contention)
-- `rr50`: トランザクションの 50% が read、50% が write
-- `rmw0`: read-modify-write の composability チェックなし
-- `max_ope10`: 各 TX が平均 10 操作 (YCSB の operation count)
-- `extime3`: 計測時間 3 秒/run
+- `100k`: 100,000 レコード
+- `t4`: 4 スレッド
+- `skew0.9`: Zipf 分布の skew パラメータ 0.9
+- `rr50`: transaction 内の操作の read 比率 50%
+- `rmw0`: read-modify-write を無効にし、write は blind write
+- `max_ope10`: 1 transaction あたり 10 操作 (CCBench の既定値)
+- `extime1`: 1 rep の実行時間 1 秒
+- `reps2`: 1 測定 round あたり 2 rep
+
+これは `default_perf()` の配線確認用設定であり、性能比較用 calibration ではない。`PerfConfig` 自体の既定は `extime=3, reps=5` だが、ここでは `extime=1, reps=2` を明示指定する。calibrator が別の設定を確定した走行では、その走行の `PerfConfig` を用いる。

 ### Measurement Methodology (coder の提案値は以下で検証される)

-1. **Build:** BACKOFF_FIXED を提案値で設定・build
-2. **Verify:** verifier が correctness trace (abort 率・cycle 異常検査) を取得 (1 run)
-3. **Bench:** 3 runs of standard workload (先述)、各 run の 1m throughput をリポート
-4. **Result:** 3 run 中央値が baseline と比較される
+1. **Build:** 提案を反映した variant を trace 有効の verify 用と trace 無効の bench 用に build する。
+2. **Verify:** legacy mode では `CorrectnessWorkload` の既定 (200 records / 4 threads / skew0.9 / rr50 / rmw=true / max_ope5 / extime1 / reps1) で trace を取得し、verifier で正しさを検査する。mode 未指定も同じであり、追加 verify を有効にした mode はこの説明の対象外。
+3. **Bench:** verify を通過した variant を上記 workload で 1 round あたり 2 rep 測定する。既存の安定性判定により round を再測定する場合がある。
+4. **Result:** 採用 round の有効な throughput 値を `statistics.median` で集約する。有効値が 2 件ならその算術平均であり、この throughput 代表値を baseline との比較に用いる。
````

K0/K1/B-4 はこの inline 文書に追加しない。非遡及の具体的なアーム名は後述の runbook 適用版へ置く。勝ち筋値・利得・新しい最適化機序は追加しない。

**2. `.claude/agents/critic.md:14,26,27,36`**

```diff
-- **genome 別の leading indicators** (緑 = committed のみ): throughput / abort_rate / latency_ns / llc_miss_rate / ipc
+- **genome 別の leading indicators** (緑 = committed のみ): throughput_tps / abort_rate / llc_miss_rate / ipc

-1. **どの設計選択が効いているかを限界効果で読む。** 例: BACK_OFF 0→1 で throughput が半減しても abort_rate がほぼ不変で latency が急増しているなら、backoff のコストは「contention 低減の失敗」でなく「衝突が無くても待つ latency」と帰属する。abort_rate が下がっているのに throughput も下がるなら別の機序 (cache/IPC) を疑う。
-2. **指標を組み合わせる。** throughput 単独でなく (abort_rate, latency, llc_miss_rate, ipc) の組で機序を推定する。throughput が同じでも abort_rate と latency の内訳が違えば別の挙動。
+1. **どの設計選択が効いているかを限界効果で読む。** 例: BACK_OFF 0→1 で throughput が下がるのに abort_rate がほぼ不変なら、abort 率の改善は観測されず、待機コスト増を仮説とする。llc_miss_rate / ipc を併せて読み、機序を断定できない場合は uncertainty に残す。
+2. **指標を組み合わせる。** throughput_tps / abort_rate / llc_miss_rate / ipc の組で機序を推定する。throughput が同じでも abort_rate / llc_miss_rate / ipc が異なれば、別の挙動の可能性がある。

-- **avoid**: 探索から外してよい方向 + 理由 (例「BACK_OFF=1 は全 workload で latency 律速、再訪不要」)
+- **avoid**: 探索から外してよい方向 + 理由。評価済みの範囲で throughput_tps / abort_rate / llc_miss_rate / ipc を根拠に示し、未測定の workload へ一般化しない。
```

L9 の後へ追加：

```text
適用版: 2026-09-17 改訂以降の走行用。指標列は `orchestrator/critic/digest.py::INDICATORS` に一致する。

CCBench の通常出力の `latency[ns] = 1e9 × thread_num / throughput` は throughput の恒等変換であり、独立した latency 計測ではない。digest に latency 列はなく、独立の帰属根拠として使わない。
```

**3. `.claude/agents/critic-experiment.md:36–38`**

```diff
-- **指標の組で機序を推定する。** throughput / abort_rate / latency_ns / llc_miss_rate / ipc の組。throughput が同じでも
-  abort と latency の内訳が違えば別挙動。throughput が落ちたとき、それが abort 増 (競合) なのか latency 増 (待ち) なのか
-  ipc 崩壊 (命令を発行できない) なのか cache miss なのかを切り分ける。
+- **指標の組で機序を推定する。** throughput_tps / abort_rate / llc_miss_rate / ipc の組。throughput が同じでも
+  abort_rate / llc_miss_rate / ipc が異なれば、別の挙動の可能性がある。throughput が落ちたときは、abort_rate の増加、
+  llc_miss_rate の増加、ipc の低下を併せて読み、機序を断定できない場合は uncertainty に残す。
```

L34 の後へ追加：

```text
適用版: 2026-09-17 改訂以降の走行用。online digest の指標列は `orchestrator/critic/digest.py::INDICATORS` に一致する。

CCBench の通常出力の `latency[ns] = 1e9 × thread_num / throughput` は throughput の恒等変換であり、独立した latency 計測ではない。online digest に latency 列はなく、独立の帰属根拠として使わない。
```

**4. `.claude/agents/planner-v4.md:17` と入力節末尾 L50**

```diff
-**目標:** 現行測定値 (abort 率・cache miss・IPC など) + 評価済み提案 (whiteboard、abstract のみ) から、
+**目標:** campaign (workload) ごとに 1 回射影し、iteration / 世代を跨いで更新しない凍結値 (`current_perf` / `leading_indicators`) + 評価済み提案 (whiteboard、abstract のみ) から、
```

L50 の後へ追加：

```text
適用版: 2026-09-17 改訂以降の走行用。`current_perf` / `leading_indicators` は campaign (workload) ごとに 1 回射影した snapshot であり、iteration / 世代を跨いで更新しない。

8c 自動 trial は `p3_autonomous_workload_trial.py::_INITIAL_ROLE_METRICS` (数値指標は全て `None`) を workload ごとに 1 回だけ `_role_metric_payloads()` へ渡して凍結する。`_planner_current_perf_payload()` / `_planner_leading_indicators_payload()` は世代ごとの測定結果で更新せず、その snapshot を渡す。`contention_level` は workload descriptor 由来である。手動 runbook では `<baseline>` を毎 iteration 同じ値で射影する。上の JSON は入力形の説明例であり、8c 自動 trial の初期数値を表すものではない。
```

「全 null」は初期数値指標に限定する。descriptor 由来の `contention_level` まで null と説明しない。JSON L30–45 は変更しない。

**5. `.claude/agents/coder-v4-autonomous-trigger-gating.md:62–63`**

```diff
-(baseline は本ループ自身の直近実測であり、これ以外の
-実験・偵察の数値は入力に存在しない。)
+適用版: 2026-09-17 改訂以降の走行用。`baseline` は campaign (workload) ごとに 1 回射影し、iteration / 世代を跨いで更新しない凍結 snapshot である。
+
+8c 自動 trial は `_INITIAL_ROLE_METRICS` (数値指標は全て `None`) から workload ごとに 1 回だけ射影して凍結し、`_coder_baseline_payload()` は世代ごとの測定結果を使わず同じ snapshot を渡す (D410 決定 1)。手動 runbook では本ループ自身の `<baseline>` を毎 iteration 同じ値で射影する。上の入力例の「実測」は手動射影の場合を示し、8c 自動 trial の初期数値を表すものではない。これ以外の実験・偵察の数値は入力に存在しない。
```

入力例 L40–55 は変更しない。

**6. runbook 2 本**

`docs/phase3-s4b-runbook.md:52`、`docs/phase3-s5-sort-runbook.md:44` ともに：

```diff
-  "current_perf": {"throughput_tps": <baseline>, "abort_rate_pct": <baseline>, "last_delta_pct": null},
+  "current_perf": {"throughput_tps": <baseline>, "abort_rate_pct": <baseline>},
```

それぞれ planner 入力 JSON の直前（s4b L49、sort L41 の前）へ同じ 2 行を追加する：

```text
適用版: 2026-09-17 の T-2703/T-2717/T-2705 改訂以降の走行には改訂した役割入力文書と本射影を適用する。凍結済みアーム (K0 / K1 / B-4) には遡及適用せず、記録は当時の文書・射影のまま保持する。
`<baseline>` と `leading_indicators` は campaign (workload) ごとに 1 回射影して凍結し、毎 iteration 同じ値を渡す。
```

**7. `orchestrator/codex_roles/review_ledger.py:37–47`**

既存 Reviewed コメントを保持し、各対象 entry の直前に追加する。

```diff
-    "coder-v4-autonomous-trigger-gating": "2b46df2e4a5cbafcd3780b4cca54b3d81f3a73d9999cc6c859f1107aa398835a",
-    "critic": "cd1c365204fd1a68260d0454b4599bfd8cea12c5d845fb24f4e21f154733df15",
-    "critic-experiment": "fc20aa7ef1bf9af45eaa2e56313b8b5221a3ff2a2413110fa333ba470ff9456e",
+    # Reviewed 2026-09-17: T-2703/T-2717/T-2705; baseline の世代間凍結と適用版を明記。
+    "coder-v4-autonomous-trigger-gating": "<NEW_SHA_coder-v4-autonomous-trigger-gating>",
+    # Reviewed 2026-09-17: T-2703/T-2717/T-2705; digest の独立指標と適用版を訂正。
+    "critic": "<NEW_SHA_critic>",
+    # Reviewed 2026-09-17: T-2703/T-2717/T-2705; online digest の独立指標と適用版を訂正。
+    "critic-experiment": "<NEW_SHA_critic-experiment>",
```

```diff
-    "planner-v4": "c47cf0ff81bb88d1ad65d5b0b92ac35feb40f49e4d2a8eef9007b48c286bf5f9",
+    # Reviewed 2026-09-17: T-2703/T-2717/T-2705; current_perf / leading_indicators の凍結と適用版を明記。
+    "planner-v4": "<NEW_SHA_planner-v4>",
```

placeholder は親の Markdown 編集が確定した後、各ファイルの実 bytes の SHA-256 に置換する。

**8. `orchestrator/tests/test_reflux_originless_compatibility.py:699` 直後**

置換前は空。既存 helper・既存呼出し・比較処理は維持する。

```python
def _extend_t2703_role_source_baseline(
    baseline: dict[str, list[list[object]]],
) -> None:
    """Follow the reviewed T-2703/T-2717/T-2705 role source pins."""
    journal_rows = baseline["journals/*/*/provenance/role_file_sha256"]
    for role, old, new in (
        (
            "planner",
            "c47cf0ff81bb88d1ad65d5b0b92ac35feb40f49e4d2a8eef9007b48c286bf5f9",
            "<NEW_SHA_planner-v4>",
        ),
        (
            "critic",
            "cd1c365204fd1a68260d0454b4599bfd8cea12c5d845fb24f4e21f154733df15",
            "<NEW_SHA_critic>",
        ),
        (
            "coder",
            "2b46df2e4a5cbafcd3780b4cca54b3d81f3a73d9999cc6c859f1107aa398835a",
            "<NEW_SHA_coder-v4-autonomous-trigger-gating>",
        ),
    ):
        replaced = 0
        for row in journal_rows:
            if row[0] == old:
                row[0] = new
                replaced += 1
        assert replaced == 6
        report_rows = baseline[
            f"reports/*/cells/*/generations/*/roles/{role}/"
            "provenance/role_file_sha256"
        ]
        assert report_rows == [[old, 6]]
        report_rows[0][0] = new


_extend_t2703_role_source_baseline(_PRE_WAVE_ORIGINLESS_BASELINE)
```

新値は ledger から runtime import せず、確定した literal をここにも記載する。critic-experiment は `p3_autonomous_workload_trial.py:262–270` の `ROLE_FILES` に入らず、この baseline の追随対象ではない。

**9. `.codex/role-adapters/{critic,critic-experiment,planner-v4,coder-v4-autonomous-trigger-gating}.json`**

親が Markdown と ledger の確定後に `expected_adapters()` で再生成する。手作業で JSON の hash だけを書き換えない。各ファイルの置換は次の 4 field に限定される見込み。

```text
review_ledger.source_file_sha256: 旧 source SHA → <NEW_SHA_role>
source.sha256:                   旧 source SHA → <NEW_SHA_role>
semantic_digest:                旧 digest     → renderer が算出した新 digest
developer_instructions:         旧本文の埋込み → 上記訂正後本文の埋込み
```

実際の全文は renderer 出力で一意に決まる。全 14 adapter を期待 bytes と照合し、対象外 10 本に差分がないことを親が確認する。

## pin 閉包と adapter の変化

`spec.py:587–590` は role source の実 bytes と `SOURCE_FILE_SHA256` を照合する。ledger 更新なしでは adapter 再生成にも進めない。

`render_adapter()` の変化根拠は以下。

| field | 根拠 |
|---|---|
| `review_ledger.source_file_sha256` | `spec.py:820` が ledger 値を格納 |
| `source.sha256` | L806 が source 全文を hash、L840 が格納 |
| `semantic_digest` | L771 の source pin と L790–791 の本文を hash |
| `developer_instructions` | L795–800 が本文を埋込み、L869 が格納 |

`ROLE_MANIFEST_SHA256` は不変。`spec.py:55–68` の `_ROLE_KEYS` / `_CLAUDE_KEYS` に本文 SHA はなく、L565 が exact keys、L566 が **manifest role entry 自体**の canonical hash を検査する。本文 SHA の検査は別の L583–590 にある。今回 manifest・frontmatter・schema・projection instructions は変更しないため、manifest pin を更新する根拠はない。

同様に `DESCRIPTION_SHA256`、`SCHEMA_SHA256`、`ROLE_IO_CONTRACTS`、`DEVELOPER_INSTRUCTION_TEMPLATE_SHA256` は不変。native 0 / static 14 / runtime blocked を維持する。

「実装差分ゼロ」をファイル差分の意味では満たせない。ledger 冒頭 L3–5 は source 更新に独立 review 更新を要求し、adapter 再生成だけでは drift を承認できない設計である。D118 残余 (b) の逐語も「是正は `orchestrator/codex_roles/review_ledger.py` の source hash 更新と `.codex/role-adapters/*.json` の再生成を伴う。」（`docs/decisions.md:5672–5673`）と明記する。さらに現行 source bytes が originless baseline に残るため、互換 fixture の追随が必要。「schema・受理規則・実行制御を変えない」は満たせるが、役割入力本文・prompt bytes・その hash は意図的に変わり、LLM の応答まで同一とは主張しない。

## 変異事前登録案

すべて、訂正後の無変異 baseline が通ることを親が確認してから行う。変異ごとに一つの変更だけを入れ、復元してから次へ進む。

| ID | 単一の変異 | 期待結果・検出箇所 |
|---|---|---|
| M1 | 新 helper の末尾呼出し 1 行だけ除去 | `orchestrator/tests/test_reflux_originless_compatibility.py:test_originless_default_preserves_every_nonvolatile_leaf_and_closed_key_set` が FAIL。追随しない 3 role の source SHA と現行出力が不一致 |
| M2 | ledger の `critic` 1 entry だけを旧 `cd1c3652…` 全 SHA に戻す | `spec.py:load_role_specs` が `SOURCE_FILE_SHA256 drift` で拒否。checker 非ゼロ終了、pytest では `test_codex_agents.py` の **collection error** |
| M0 | 追加した Reviewed コメントの文言だけ変更 | 等価。期待失敗 node は **なし**。下記 node は PASS のまま |

M1 の対照 node は `orchestrator/tests/test_reflux_originless_compatibility.py:test_originless_harness_rebuild_is_deterministic_control`。同じ現行 source からの再構築同士を比較するため、こちらの失敗は期待しない。M1 は「source pin 追随の欠落」を一理由として検査し、3 role 個別の寄与とは解釈しない。

M2 の本来の検査 node は：

```text
orchestrator/tests/test_codex_agents.py:test_review_ledger_independently_pins_all_fourteen_sources_and_io_contracts
```

ただし、ファイル変異を入れて新しい pytest process を起動する指定方式では、この node は実行されない。`test_codex_agents.py:27 → tools/check_codex_agents.py:44 → spec.py:587` が先に拒否するためである。**「この node の FAIL を KILLED 条件」と登録するのは不正確**。既存 harness が collection error を扱えない場合は、M2 を checker の終了状態と該当診断で判定する検査として扱い、通常の test-node kill と混ぜない。新しい検査を追加して回避しない。

M0 の観測対象は上記 ledger node、次の node、M1 の対象 node とする。

```text
orchestrator/tests/test_codex_agents.py:test_current_sources_render_byte_exact_and_native_is_empty
```

コメントは ledger 辞書値・renderer の hash 入力に入らないため、等価の `SURVIVED` を期待する。

## 焦点走の対象

`git grep` で直接参照を列挙し、provider・fixture・checker 経由を 2 段まで追った。親の焦点走には次を含める。すべて `orchestrator/tests/` 配下。

| test file | 根拠・位置づけ |
|---|---|
| `test_codex_agents.py` | ledger/source/adapter の直接照合、source JSON shape parity |
| `test_codex_role_runtime.py` | L560 で critic adapter を直接読む。launcher 経由も確認対象 |
| `test_reflux_originless_compatibility.py` | 今回変更する固定 baseline。L48 の `p3_test.t325_registered_trial`、trial provider 経由 |
| `test_p3_autonomous_workload_trial.py` | `ROLE_FILES`、`FixtureRoleProvider`、凍結 payload の実経路 |
| `test_autonomous_trial_completeness.py` | L5734 の `FixtureRoleProvider`、trial 完全性と provenance |
| `test_p3_b4_closed_critic.py` | L2023–2028 で実 critic source bytes を projection closure に含める |
| `test_claude_transport.py` | L1718 の helper が `A.FixtureRoleProvider(role)` を包む。`_provider_set` 経由もある |
| `test_role_session_isolation.py` | L540 の `_provider_set` と、L32 の completeness fixture 経由 |
| `test_s8c_preregistration_predicates.py` | L153 の `_snapshot_current_commit` が evaluator の evidence を HEAD から取得。commit 後の評価も必要 |
| `test_s8c_schedule.py` | authority の `role_files` digest 契約の回帰確認。実 role 本文の直接読取りではない |
| `test_effort_levels.py` | spec / launcher の policy 回帰確認。role 本文の直接読取りではない |
| `test_hooks.py` | L5047 で実 `.claude/agents` を参照。frontmatter 不変の確認対象 |
| `test_p3_s4_loop.py` | 手動ループ側の回帰確認。先例 T-2528 の焦点走対象 |
| `test_s8c_generation_projection.py` | payload key 集合・射影契約を変えていないことの回帰確認 |

主要な間接依存は次の形で閉じる。

```text
test_codex_agents
  → tools/check_codex_agents
  → spec.load_role_specs / expected_adapters

test_claude_transport の helper
  → A.FixtureRoleProvider
  → ROLE_FILES[role][0].read_bytes()（A:680）

test_reflux_originless_compatibility
  → test_p3_autonomous_workload_trial の fixture
  → A.run_trial / provider

test_role_session_isolation
  → test_autonomous_trial_completeness の fixture
  → A.run_trial / provider
```

`test_p3_build_authority_cli.py:114` の該当ヒットは test ファイル名の列挙であり、role bytes を読む根拠には数えない。selector 専用の s8b test 群も、今回変更する 4 role の参照とは分ける。

親は焦点走・受入全走を `tools/run_tests.py` 経由で行い、`check_codex_agents.py`、`check_docs.py`、差分検査も実施する。本 plan で緑を確認したものはない。

## 残件と scope 外

- trigger-gating 入力例 L42 の `leakproof_context` は file inline と書かれているが、8c は `s8c_generation_projection.LEAKPROOF_CONTEXT` の固定短文。今回変更しない。
- `coder-v4-autonomous.md` / `coder-v4-autonomous-sort.md` / `coder-v4-autonomous-k2.md` は変更しない。
- `src/coder-spec.md` の superseded な歴史記録節は変更しない。
- `src/coder-leakproof-context.md` の Measurement 節以外の説明・停止条件等は今回の整合保証に含めない。
- `latency_ns` payload key、schema version、`REPORT_SCHEMA_VERSION`、`DECIDER_VERSION`、代表 rep の上側中央選択は維持する。
- 凍結済みアームの prompt・射影・測定記録、過去 WAL、過去の人手射影は書き換えない。
- B-4 の未記入 projection / prompt hash を、この文書訂正だけで埋めない。
- CCBench、renderer、runtime gate、受理規則、新しい semantic pin・検証層は変更しない。
- 例・ledger・adapter 全面の協調 rollback を拒否する独立 semantic 防壁は追加しない。

## 総括

編集案は **文書訂正 → 4 source pin 更新 → 3 role の originless 追随 → 親による adapter render** で閉じる。frontmatter・payload key・manifest・schema は維持する。

実装前に plan へ反映すべき補正は、helper の挿入位置 L699 と、**M2 は個別 node FAIL ではなく import 時の拒否になる**点。新 SHA の確定、変異実測、焦点走・受入全走は親が行う。