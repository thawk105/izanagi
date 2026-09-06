単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/s4-adjudication.md

## 必読事項の射影

次を上から順に読む。いずれも絶対パスである。**読めなければ即停止**し、読めなかった path を報告して終われ。

1. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/s4-adjudication.md` — 親の段 4 裁定 (4 節 plan v2 — C1a、変異 M1〜M12)。本 fix の契約
2. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/prompt-s5-launcher.md` — 実装子の契約 (所有 path、禁止事項、DW-S05-C の検査・報告)。**本 fix は同じ権限境界・禁止事項・規模上限を全文継承する**
3. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/artifacts/t1851-unit-c/s6-review-a.md` と `s6-review-b.md` — 段 6 レビュー 2 本 (どちらも NO-GO)。親は全所見を real と裁定した。所見の (d) 修正案を実装に反映する
4. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/s5-s6-fix1-integrated-snapshot.patch` — 現在の統合差分 (実装子 + fix1)。本 worktree にはこれが適用済み

作業 repository は `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-unit-c-fix2` (branch `fix-dev-wave-t1851-unit-c-2`、base `04f06d032` + 統合 patch 適用済み、未 commit) である。コードはすべてこの worktree の中で読み書きする。

## 所有 path (これ以外は 1 byte も変更しない)

- `orchestrator/campaign/s8b_floor_attempt_launcher.py`
- `orchestrator/tests/test_s8b_floor_attempt_launcher.py`

`test_official_perf_closure.py` (fix1 が登録した guard 文字列は launcher の `_checked_reservation_policy` 内の `if` 条件を ast.unparse した逐語に束縛されている。**その 2 つの `if` 条件の式は変えるな**。変えるなら実装せず報告して止まる)、adapter / core / profile / campaign / calibrator、他の test file、docs は所有外。

## 依頼 — 段 6 所見の fix (9 件)

各所見に対し、実装後の完了報告へ **closed / partial / regressed の対応表**を書け (所見番号は「A-1」「B-3」の形)。

1. **A-1 (blocker) 検査済み capture kwargs の再読 (TOCTOU)。** `_checked_reservation_policy` が検査した exact kwargs の copy (`dict`) を `_ReservationPolicy` に保持し、`_capture` は `measurement.keyword_arguments` を再読せずその copy だけを使う (私有 sink はその copy に足す)。test: 可変 Mapping を `keyword_arguments` に渡し、pre-probe の中で元 Mapping の `reps` / `use_perf` を書き換えても fake capture が受け取る値が検査時の値のままである対照 node。
2. **A-2 (blocker) open 例外を `observed` として通せる。** `output.seal` の前に、`opened.failure is not None` かつ `terminal.terminal_status == "observed"` を `FloorAttemptLauncherError("[s8b-launcher-terminal] observed terminal contradicts a capture or open failure")` で拒否する。通る正例 = failure None + observed、failure あり + `terminal-failure`。既存 node `test_open_error_still_observes_and_terminalizes_after_classification` は `terminal-failure` を申告しているので期待値はそのまま。**M12 node (`test_open_failure_yields_empty_repetition_evidence`) の builder は `observed` を申告しているので、failure 時は `terminal-failure` を申告する形へ直す** (他の入力は valid のまま、snapshot が空 tuple である assertion は維持)。新設 node: open 失敗 + observed 申告が拒否され、registry の `terminal` が呼ばれないこと。
3. **A-3 (must-fix) D1522 の正例対照。** `_checked_reservation_policy` / `_post_probe` / `_pre_observation_failure_reason` / `_external_evidence_sha256` の直接 test それぞれに、同じ test 内で有効入力の成功を先に置いてから負例を与える。`_external_evidence_sha256` は期待 payload (`schema_version` = v2 literal、`probe_before`、`probe_after` null、`launch_failures` 射影、`capture_failure`) から test 側で digest を計算して等値を固定し、`capture_failure` だけを変えた差も固定する。`_pre_observation_failure_reason` は pre 競合 / post 競合 / launch_failures / capture failure / None の 5 例。marker の `_contains_callable` は先行する marker 非 None gate により到達不能なので、その検査行を削除する (docstring に「marker は非 None を先に拒否する」と書く)。
4. **A-4 = B-5 (must-fix) M5 の単一理由性。** `test_reservation_rejects_protocol_not_bound_to_binding` は `reps` を 3 のまま保ち、digest だけを変える別 field (例: `{"reps": 3, "session_cv_max": "0.10"}` のような追加 key、または binding 側の `protocol_sha256` を別 hex64 に差し替え) で不一致を踏む。
5. **B-1 (must-fix) 既存 kwargs 期待値の弱体化。** `test_mut_t1668_...` の fake capture の `assert set(kwargs) == {...}` を、元の exact 値検査 (`extime` / `reps` / `use_perf` の値) に戻したうえで、`rep_observations` が launcher 私有の `list` であること (caller kwargs に無い) を個別に検査する。
6. **B-2 (must-fix) fake の sink 別名。** `_bind_sink` / `_Token` を実体 (`calibrator/runner.py` の `open_measurement_point` :933-1049 が sink へ書く rep record の key 集合) と同形にする: 注入 sink は `_Token` の私有 field に保持し、`open()` 時にその sink へ実体と同じ key 集合の rep record を reps 件 append する。公開 attribute `rep_observations` は**別の list** (別内容でもよい) にし、launcher の `repetition_evidence` snapshot が注入 sink 由来であること (公開 attribute を読んでいないこと) を検査する node を置く。
7. **B-3 (must-fix) real adapter node が reserve 以降を通らない。** `test_real_adapter_creates_and_exactly_reuses_complete_genesis` を、v1 profile + marker None で **実 adapter (`s8b_attempt_registry`) の `reserve_attempt_slot` → `classify_attempt` → `begin_*_observation` → `record_attempt_terminal` まで**通す integration 正例へ拡張する (fake capture と fake probe は `_launch_floor_attempt_for_test` の注入、registry だけ実体)。実 adapter の要求 (root、claim、receipt) は `test_s8b_attempt_registry.py` の v1 helper の作り方を読んで同じ形で用意する (その file は変更しない)。予算内で terminal まで届かなければ、少なくとも `reserve_attempt_slot` を実体で通し、届かなかった段を報告に書く。
8. **B-4 (must-fix) authority node が public API を観測しない。** `test_certified_api_owns_classification_authority` に、`monkeypatch` で `launcher._PRODUCTION_DEPENDENCIES` を recorder + fake capture の `_LauncherDependencies` に、`launcher._owned_post_probe` を fake probe に差し替えたうえで **public `launch_floor_attempt`** を `floor_post_probe_capability()` 経由で呼び、recorder が受けた `authority_id` / `authority_policy_sha256` が launcher 定数と一致することを検査する形を足す (既存の signature 検査と定数検査は維持)。monkeypatch は launcher module 自身の属性に限る。
9. **M4 の再照準。** 親は M4 を「public `launch_floor_attempt` の `classification_authority=_CLASSIFICATION_AUTHORITY,` を別 authority へ差し替える変異」へ再登録する。上の B-4 node がそれを殺すことを確かめよ (定数の digest 検査だけでは殺せない)。

## 規模上限

実装子と合わせて production +150〜260 / −60、test +250〜520。超えそうなら止めて報告する。

## 検査・報告 (DW-S05-C を継承)

- 実走できる範囲で `PYTHONPATH=. python3 orchestrator/tests/test_s8b_floor_attempt_launcher.py` (自走 harness) を走らせ、緑には実走 nodeid・範囲を併記する。pytest wrapper が sandbox で動かないなら理由を書く。
- 既存テストの期待値を変えない (反転・緩和・skip・削除は禁止。fix 対象の B-1 は「緩和を元に戻す」向きだけ)。赤なら実装側が誤りとして報告する。
- fixture へ現行 hash を差し込むなど、テストを甘くして緑にしない。揮発 payload を焼き込まない。
- 完了報告に所有外への波及 (`test_official_perf_closure.py` の guard 逐語、`test_ccbench_spawn_sites.py:212`) を静的列挙する。
- commit しない。docs を編集しない。

## 制約

- 出力へ結合文字 U+0300〜U+036F を使わない。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ。無出力が最悪である。
- 出力の最後に `## 総括` 節を置き、所見 9 件の closed / partial / regressed、変更行数、新設・変更 node 数、実走結果を 12 行以内で書け。
