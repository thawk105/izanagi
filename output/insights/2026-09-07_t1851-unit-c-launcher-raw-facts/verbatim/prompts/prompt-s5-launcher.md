単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/s4-adjudication.md

## 必読事項の射影

次を上から順に読む。いずれも絶対パスである。**読めなければ即停止**し、読めなかった path を報告して終われ。

1. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/s4-adjudication.md` — 親の段 4 裁定。**4 節 (plan v2 — C1a) と変異事前登録が本作業の契約**であり、段 2 plan と食い違う点はこちらが正しい。3 節の契約 v2 は次 wave (C1b) の対象で、本作業では実装しない
2. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/artifacts/t1851-unit-c/s2-plan.md` — 段 2 plan。「2. launcher の流れ」「7. 赤になる既存 test」「8. test 計画 (launcher)」が土台
3. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/artifacts/t1851-unit-c/s3-lens-a.md` と `s3-lens-b.md` — 段 3 の敵対所見。裁定で「採用 (C1a)」とされた所見 (A2 / B2、A9、B4、B9) の (d) 修正案を実装に反映する
4. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/s1-brief.md` — 親 brief (anchor と件数は裁定 7 節の訂正が優先)
5. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/refs/decisions-verbatim.md` — 確定裁定の逐語 (特に D1113 / D1522)

作業 repository は `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-c-launcher` (branch `impl-dev-wave-t1851-unit-c-launcher`、base `04f06d032`) である。コードはすべてこの worktree の中で読み書きする。

## 所有 path (これ以外は 1 byte も変更しない)

- `orchestrator/campaign/s8b_floor_attempt_launcher.py`
- `orchestrator/tests/test_s8b_floor_attempt_launcher.py`

`s8b_attempt_registry.py`、`attempt_registry_core.py`、`s8b_attempt_profile.py`、`s8b_floor_campaign.py`、`calibrator/`、`test_ccbench_spawn_sites.py`、docs、他の test file は所有外である。所有外に必要な変更が見つかったら実装せず完了報告に書け。docs の編集と commit はしない。

## 依頼 — C1a: 起動層の raw facts 面

裁定 4 節の 1〜8 を実装する。順序は 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8。

### 受理・拒否の現状 (scope 前) と、本作業で変わる点

- 現状: `launch_floor_attempt()` は post-probe だけを所有し、caller 提供の `classification_authority` をそのまま台帳へ書き、`rep_observations` は caller 指定を拒否するが私有 sink も持たず、v2 profile / marker を区別しない (v2 は adapter の `[s8b-v2-terminal]` で terminal 時に落ちる)。production caller は 0 件。
- 本作業後: (受理が変わる) pre-probe 競合と capture 例外を terminal まで閉じる、私有 sink を持ち open 後に snapshot する、分類 authority は launcher 定数。(拒否が増える) v2 profile または marker 非 None を副作用前に拒否、`mode` / protocol digest / `use_perf` / `reps` の不整合を副作用前に拒否、probe 結果の余分 key を拒否。
- 変えないもの: `_CERTIFIED_MEASUREMENT_KEYWORDS` (caller の `rep_observations` は拒否のまま)、`_owned_post_probe` の argv と spawn site (同じ関数を pre / post で 2 回呼ぶ。rename しない。`test_ccbench_spawn_sites.py:212` の pin を壊さない)、`FloorPostProbeCapability` の封印検査、adapter / core / profile。

### 実装の要点

1. `FloorAttemptReservation` へ `protocol: Mapping[str, object]`、`mode: str`、`perf_preflight_receipt: Mapping[str, object] | None`、`consumption_marker: object | None` を足す (必須、default なし)。`slot_id` は 4 軸 | 5 軸 tuple。`_reserve` は `consumption_marker=request.consumption_marker` を adapter の `reserve_attempt_slot` へ渡す。
2. 副作用前の検査は 1 つの関数 (例: `_checked_reservation_policy(reservation, measurement) -> _ReservationPolicy`) にまとめ、genesis / reserve / subprocess のいずれよりも前に呼ぶ。`canonical_protocol_sha256` は `orchestrator.campaign.s8b_floor_contract` から、`use_perf_from_receipt` は `orchestrator.calibrator.perf_preflight` から import する (循環なしはレンズが実測済み)。`protocol` / receipt / marker を `_contains_callable` で検査する。
3. v2 早期 gate は `profile.schema is profile8b.S8B_V2_SCHEMA_PROFILE` (`orchestrator.campaign.s8b_attempt_profile` を import) または `consumption_marker is not None` で `FloorAttemptLauncherError("[s8b-launcher-v2-terminal] v2 attempts require the sealed terminal evidence API")`。fake profile (test) は `schema` attribute を持たない可能性があるので `getattr(profile, "schema", None) is S8B_V2_SCHEMA_PROFILE` の形にし、marker 非 None は型を問わず拒否する。
4. 分類 authority: module 定数 `_CLASSIFICATION_POLICY` (canonical JSON 化できる dict: `schema` / `precedence` / `probe_argv` / `probe_timeout_s`) と `_CLASSIFICATION_AUTHORITY` (`authority_id="s8b-floor-attempt-launcher/pre-output-classification/v1"`、`authority_policy_sha256=sha256(canonical bytes)`)。public `launch_floor_attempt` の `classification_authority` 引数を削除し、内部で定数を使う。`_launch_floor_attempt_for_test` は `classification_authority` の注入を残す (省略時は定数)。
5. 流れは裁定 4 節 5 のとおり。`_DurablyClassifiedMeasurement(captured=None, ...)` を許し `open()` は None を返す。capture の例外 (`RuntimeError` / `subprocess.TimeoutExpired` / `OSError`) は `failure={"stage": "capture", "exception_type": ..., "errno": ..., "message": ...}` にし、post-probe は finally 相当で必ず走る。open の例外は `stage: "open"`。`_pre_observation_failure_reason(probe_before, probe_after, launch_failures)`: `probe_before.competing or (probe_after is not None and probe_after.competing)` → competing、`launch_failures` 非空または `failure.stage == "capture"` → launch_failure、それ以外 None。`_external_evidence_sha256` の payload は `{schema_version: "s8b-floor-pre-output-evidence/v2", probe_before, probe_after (null 可), launch_failures, capture_failure (null 可)}`。`_post_probe` は exact 4 key (`rc` int、`stdout` / `stderr` str、`competing` bool) を要求し余分 key を拒否する。
6. `OpenedFloorAttempt` は `measurement`、`failure`、`probe_before`、`probe_after`、`launch_failures`、`pre_observation_failure_reason`、`external_evidence_sha256`、`repetition_evidence: tuple[Mapping, ...]`、`expected_use_perf: bool`、`reps_expected: int` を持つ (frozen)。`open_error` / `post_probe` は残さない。
7. 私有 sink: `_capture` が allowlist 検査後に `rep_observations=<launcher 私有 list>` を足す。snapshot は `open()` の後に `tuple(dict(x) for x in sink)` で取り、open 失敗時は空 tuple。
8. test: `_Token` を `ScalePoint` 同形 (attribute `throughputs` / `notes` / `rep_observations`、`open()` 時に渡された sink へ rep dict を append) へ変え、fake `capture(*args, **kwargs)` が kwargs の `rep_observations` が launcher 私有 list であること (caller kwargs に無い) を観測する。`_reservation()` helper へ必須 field を足す。既存 12 node を新 signature へ追随 (期待値を緩めない: seal 順序・reason precedence・空 output 拒否・genesis replay・real adapter genesis・keyword allowlist・callable post_probe 拒否は全部維持)。新設 node は裁定 4 節の変異表 M1〜M12 を観測する node を必ず含め (表の node 名を使う)、各負例は「他の gate に遮られない」形 (他の入力は valid) にする。D1522: 上流が拒否する形でも、下層の実体 (`_checked_reservation_policy`、`_post_probe`、`_pre_observation_failure_reason`、`_external_evidence_sha256`) を直接呼ぶ検査を置く。real adapter を使う既存 node (`test_real_adapter_creates_and_exactly_reuses_complete_genesis`) は v1 profile + marker None で通す。

### 規模上限

production +150〜220 / −40 行、test +250〜400 行。超えそうなら止めて報告する。

## 検査・報告 (DW-S05-C)

- 実走できる範囲で `PYTHONPATH=. python3 orchestrator/tests/test_s8b_floor_attempt_launcher.py` (自走 harness) と `python3 -m pytest orchestrator/tests/test_s8b_floor_attempt_launcher.py orchestrator/tests/test_ccbench_spawn_sites.py -q` を試し、緑には実走 nodeid・範囲を併記する。実走不能なら `closed` と申告せず「実装済み・未実走」と書き、理由を書け。
- テスト新設の単位は、親の名指しを網羅と見なさず制約 meta-test (file 列挙 meta-test、`test_ccbench_spawn_sites` の在庫、`test_check_docs` 系) を自ら洗い出す。新規 test file は作らない。
- fixture へ現行 hash を差し込むなど、テストを甘くして緑にしない。機構の正例・負例は実体を名指しし依存先を stub しない (recorder fake は launcher の契約検査のため例外)。
- 期待値へ揮発 payload を焼き込まない。
- 完了報告に、所有外 caller (`s8b_attempt_registry.py` の launcher import、`test_ccbench_spawn_sites.py:212`)・共有 fixture・consumer test の波及可能性を静的列挙する。
- 指示外の受理集合変更をしない。
- commit しない。docs を編集しない。

## 制約

- 出力へ結合文字 U+0300〜U+036F を使わない。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ。無出力が最悪である。
- 出力の最後に `## 総括` 節を置き、変更 file と行数、新設 test node 数、実走結果 (nodeid 範囲と passed / failed 件数)、所有外への波及、未実装項目を 10 行以内で書け。
