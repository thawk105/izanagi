# 段 4 裁定 — [T-2590] + [T-2081] (親、2026-09-17 01:05 JST)

入力: `s1-brief.md` (P1〜P7)、`s2-plan.md`、`s3-a.md` (凍結・規律・受理集合)、`s3-b.md` (実効性・全層整合)。裁定 inbox 再走査: local main は 1042a1bc9 のまま、T-2590 / T-2081 の新裁定なし。

## 1. 所見の裁定

| # | 所見 (出所) | real / refuted | 採否 | 扱い |
|---|---|---|---|---|
| A1 | 分岐置換が pilot 履歴 binding を壊す反例なし (A) | refuted | — | I1/I2 維持。段 6 で test 8 (公開 pilot binding の正例) により実測 |
| A2 | 「1 bit も変わらない」は実装前に確定不能。履歴検証 (`binding_matches` 3 digest) と現 checkout 照合 (D:7519 `_verify_current_source_paths`) は別 (A) | real | 採用 | 完了判定の文言を「pilot 公開 binding に対する `_validate_source_binding` / consumer 判定が変更前と同じ」に限定。「変更後 checkout で過去束を再 materialize できる」とは記録しない |
| A3 | sized の受理集合は拡大と縮小の両方 (契約なし sized binding 5/10 path が拒否へ、v2 契約入り binding が受理へ、hydrate なし sized submit が拒否へ) (A) | real | 採用 | decisions fragment と insight に表のまま記録。実装は変えない。現行 sized は D:7127 で全拒否なので「従来通っていた本走が落ちる」ではない |
| A4 | 両契約入り / 契約なし binding が正規 consumer を抜ける穴 (A) | refuted | — | 正規経路は D:4847 の閉包完全一致で拒否。helper 単体は一契約性を保証しない — この限界を insight に書く。追加 gate は作らない |
| A5 | sized の attempt 非固定が pilot を緩める (A) | refuted | — | pilot の attempt-0004 照合 (D:3411 / 7127 / 2636) は残す (plan どおり) |
| A6 | D1323 の反例 (親 status ignore / 元 checkout untracked / materialized root の差分) (A) | refuted | — | 3 経路とも構成不能。閉じの根拠として insight に逐語で残す |
| A7 | T-2081 の閉じは実測前 (A) | real | 採用 | 段 7 の記録は「既存 5 境界の sized 適用を test で確認」とし、静的根拠・stub 置換部分・実観測を区別して書く。「sized で実証済み」「新 gate を実装」とは書かない |
| A8 | hydrate 外部 dir は pin なしだが `_verify_pristine_floor_dependency_sources` が pin + status を検査、pilot と同一経路 (A) | refuted | — | insight に「pilot と同一」と記録 |
| A9 | 追補 README の保証範囲: tree 比較は `.git` を除く、元 checkout の untracked は登録どおり無視し pin から隔離生成 (A) | real | 採用 | README 草稿に限定 2 文を追記 (親 docs)。検査追加なし |
| A10 | 変異台帳は「台帳」候補だが事前登録の実施記録に限る (A) | real (nit) | 採用 | 変異台帳は insight 配下の記録のみ。運用の受理台帳・参照先にしない |
| A11 | plan:16 の逐語訂正指示は現物と不一致 (A / B) | real (nit) | 採用 | 親が段 3 前に訂正済み (near miss、handoff の改善候補)。裁定参照の訂正履歴は作らない |
| A12 | `0ba074…` は live pin でない (A / B) | refuted | — | brief どおり |
| A13 | 「pilot attempt 1〜3 は infra 失敗」は粗い: 0001/0002 = bench 前停止、0003 = 条件関門の拒否 (依存供給不足 + source 意味不整合) (A) | real | 採用 | P3 の根拠を「sized には追補前の attempt が存在せず、契約が束縛するのは source であって attempt ではない」に置き直す。失敗分類は insight に正しく書く |
| A14 | ident / wal の sized 登録 (A / B) | refuted | — | 変更不要 |
| B1 | 追加の pilot 限定分岐なし (B) | refuted | — | 変更面はアンカー表のまま。D:1350 / 2143 / 8563 / tools の PILOT_STUDY_ID は sizing 入力の識別で現状維持 |
| B2 | sized fixture に `sizing_inputs` の 2 file (sizing-pilot.json、sizing-certificate.json) の実 bytes が要る (B) | real | 採用 | 実装子への指示に入れる。submit 限定 test は既存 fixture どおり `_load_policy_for_study` を stub してよい |
| B4 | runtime 検査は順序を強制しない。順序不変は tuple 比較 test で示す (B) | real | 採用 | test 1 は tuple の順序込み exact |
| B7 | root 不一致の期待 error は 2 分: 非 canonical → `amended-source-admission-mismatch`、canonical だが configure `-S` と別 → `trace0-source-route-incomplete` (D:5323) (B) | real | 採用 | test 7 の負例をこの 2 分で書く。production の検査は増やさない |
| B9 | M8 を pilot 条件の削除で作ると v2 に `attempt` が無く `KeyError` (B) | real | 採用 | M8 は「D:7127 付近に literal `attempt-0004` 照合を study 非依存に掛ける」変異に確定 |
| B11 | materializer を stub する test は `materialized(..., study_id=sized)` の呼出し引数を assert する (B) | real | 採用 | test 6 は stub が受けた `study_id` を記録し sized を assert。TJ:2203 の AST 検査に `study_id` 引渡しを足す |
| B12-M7 | D:5219 を v1 限定へ戻すと正例 (FETCHCONTENT 付き argv) が argv 長で先に落ちる。正例 node と負例 node を分ける (B) | real | 採用 | test 7 を `..._accepts_amended_configure` (正例) と `..._rejects_admission_mismatch` (負例) の 2 node に分け、M7 の期待 KILLED は正例 node |
| B13 | 現行 sized は 7133 行でなく 7127 行で先に落ちる (B) | real | 採用 | brief P1 の文言を訂正 (staging だけ直しても 7127 で止まる、両方直す) |
| B14 | `configuration` ラベルは今回の hash 原像に入らない (B) | refuted | — | sized は `a1-balanced5-sized-v1` (plan) |

scope 外の real 所見: なし。裁定パッケージへ返す設計択一: なし (全 P は plan と 2 レンズの検算で保たれた)。

## 2. plan v2 (確定)

plan (`s2-plan.md`) を次の補正込みで採用する。

- 契約表: `paper_story_a1_source.py` に `PILOT_STUDY_ID` / `SIZED_STUDY_ID`、`SIZED_CONTRACT_PATH` / `SIZED_CONTRACT_SHA256` / `SIZED_SOURCE_PATHS`、`CONTRACTS = {study_id: (path, sha256, source_paths)}` の固定 2 要素。既存の `CONTRACT_PATH` / `CONTRACT_SHA256` / `SOURCE_PATHS` は pilot 値のまま。登録 API・3 study 目の枠組みは作らない。
- 関数: `load_contract(repo_root, study_id=PILOT_STUDY_ID)`、`binding_matches(files, *, study_id=PILOT_STUDY_ID)`、`SourceContext(repo_root, base, root, *, study_id=PILOT_STUDY_ID)`、`materialized(repo_root, *, base=None, study_id=PILOT_STUDY_ID)`。`validate` / `prepare_dependencies` / `configure_dependencies` は不変。`configuration` ラベルは pilot `a1-attempt-0004` のまま、sized は `a1-balanced5-sized-v1`。
- v2 契約 JSON `orchestrator/campaign/paper_story_a1_source.v2.json`: key は `schema_version` (`paper-story-a1-source/v2`)、`study_id`、`canonical_head`、`patch`、`patch_sha256`、`policy`、`policy_sha256`、`preregistration`、`preregistration_sha256`、`amendment`、`amendment_sha256` の 11 個。`attempt` なし。値は plan のとおり (policy = v3-sized.json `a6228bcd…`、preregistration = sized README `6047eff0…`、patch/canonical_head = v1 と同一、amendment = `output/insights/2026-09-17/t2590-a1-sized-source-amendment/README.md` とその実 sha)。
- driver: D:2243 (`study_id in CONTRACTS` で当該 source_paths を末尾追加)、D:2636 (`study in CONTRACTS and (sized or attempt-0004)` で契約検算 + hydrate 必須)、D:3409 (両 study で契約 load + hydrate dir 実在、attempt 名照合は pilot のみ)、D:4860 (relative_paths に含まれる契約 path で study を選び `binding_matches`)、D:5219 (`any(contract path in files)` で発火)、D:7126 (`load_contract(repo_root, study_id)`、study 一致、pilot のみ attempt 照合、エラー文は pilot 用を維持し study 不一致は `A1 source amendment study differs`)、D:7137 (`materialized(repo_root, study_id=study_id)`)。`_trace0_commands_match` (D:4979-5060) と D:8563 は不変。
- job script: J:74-81 / 450-455 / 984-989 は pilot / sized の 2 値選択で契約 path と追補 path だけ切り替え、共通の module・patch は各箇所 1 出現 (`count == 3` 維持)。順序は 契約 → module → patch → 追補。J:1361 は 2 policy path の OR、本体 1362-1371 は不変。
- 追補 README (親 docs): `draft-sized-amendment-README.md` に A9 の限定 2 文を足して `output/insights/2026-09-17/t2590-a1-sized-source-amendment/README.md` へ置き、実装子より前に docs commit する。順序: README commit → 実装子が README の sha を実 file から取り v2 JSON を書く → v2 JSON の sha を module 定数へ → 親が両 sha を独立検算。
- tests (plan の 1〜10 を B2 / B4 / B7 / B11 / B12 で補正): 既存 test の期待値は変えない。新規 test は clone / build を増やさない。sized fixture は sized policy・prereg・v2/module/patch/追補・`sizing_inputs` の 2 file を実 bytes で配置。
- T-2081: 新規 gate・bytes 級検査なし。sized policy で `_assert_ccbench_acceptance` の 3 境界を Git 応答 stub で正例 1 + 負例 3 (tracked dirty / HEAD 不一致 / HEAD 解決失敗)、`_parent_porcelain` 空でも submodule dirty で拒否、sized の `SourceContext` が pipeline の trace/perf 双方の validate に届く軽量 fixture。記録は「既存機構の sized 適用を test で確認」。
- 実装単位: Codex author 1 本 (P7)。所有 path = `orchestrator/campaign/paper_story_a1_source.py`、`orchestrator/campaign/paper_story_a1_source.v2.json` (新規)、`orchestrator/campaign/paper_story_a1_paired.py`、`tools/pegasus/paper_story_a1_paired.sh`、`orchestrator/tests/test_paper_story_a1_job_contract.py`、`orchestrator/tests/test_paper_story_a1_paired.py`。それ以外は編集禁止。
- 成果物影響 (DW-G05): 放置時は sized の受理集合が空のまま (D:7127) で A-1 但し書き 1 を外す唯一の証拠が取得不能。本変更で sized の amended source が受理集合に入り、pilot の受理集合・pilot 公開成果物の判定は不変。

## 3. 変異事前登録 (DW-M01、位置と期待 node。anchor の逐語は実装後に DW-M07 で再検証)

| id | category | 対象 | 操作 | 期待 |
|---|---|---|---|---|
| M0 | positive | `paper_story_a1_source.py` の `CONTRACTS` 定義行 | 等価 (tuple の括弧形や comment の付加など意味不変) | SURVIVED (harness の正例) |
| M1 | negative | `paper_story_a1_source.py` `CONTRACTS` | sized の要素を落とす | KILLED: `TJ::test_sized_source_closures_match_job_and_driver` ほか sized 経路 test |
| M2 | negative | `paper_story_a1_source.py` `load_contract` | 契約 JSON 自体の sha 検算を外す | KILLED: `TP::test_sized_source_contract_pins_bytes_and_four_bindings` |
| M3 | negative | `paper_story_a1_source.py` `load_contract` 検算 loop | 4 束縛のうち `amendment` の検算を外す | KILLED: 同上 (参照 file 改変の負例 node) |
| M4 | negative | `paper_story_a1_paired.py` D:2243 | sized の 4 path 追加を落とす (pilot のみへ戻す) | KILLED: `TJ::test_sized_source_closures_match_job_and_driver` |
| M5 | negative | `tools/pegasus/paper_story_a1_paired.sh` J:984 (terminal) | 条件を pilot 限定へ戻す | KILLED: `TJ::test_sized_source_closures_match_job_and_driver` (shell 区間評価) |
| M6 | negative | `tools/pegasus/paper_story_a1_paired.sh` J:1361 | staging 条件を pilot 限定へ戻す | KILLED: `TJ::test_sized_job_stages_hydrate_for_measurement` |
| M7 | negative | `paper_story_a1_paired.py` D:5219 | 発火条件を v1 契約限定へ戻す | KILLED: `TP::test_sized_consumer_accepts_amended_configure` (正例 node) |
| M8 | negative | `paper_story_a1_paired.py` D:7127 付近 | literal `attempt-0004` 照合を study 非依存に掛ける | KILLED: `TJ::test_sized_measurement_routes_amended_source_and_hydrate` |
| M9 | negative | `paper_story_a1_paired.py` D:2636 | sized の hydrate 必須を外す | KILLED: `TJ::test_sized_group_intent_requires_hydrate` |
| M10 | negative | `paper_story_a1_paired.py` D:4860 | binding 照合を v1 契約限定へ戻す | KILLED: sized 版 `test_a1_amendment_binding_rejects_single_changed_input` (driver の `_validate_source_binding` 経由) |

test 名は実装で確定する (親が実装後に spec へ写す)。期待 node は probe 走で観測 node を集めてから完全集合として登録する。既存 test でも落ちる変異は新規検出力に数えない。冗長 gate (`test_paper_story_a1_headline.py::test_existing_a1_non_touch_manifest_is_empty_from_base` 等) は較正走で実測して `--deselect`。

## 4. 実行順

1. 親: README 最終化 → repo へ配置 → docs commit (DW-O17)。
2. 親: impl worktree (`-b impl-dev-wave-t2590-…`、wave HEAD から) 作成・submodule 初期化・lock → `check_wave_startup.py --mode midflight`。
3. Codex author 1 本 (workspace-write、`--max-model-calls 400`)。
4. 親: 所有 path 限定 patch を wave worktree へ展開、焦点走 (3 A-1 file + `test_campaign.py` の source/build 境界 node + `test_paper_story_a1_headline.py`)、sha 独立検算、test 関数名集合の基底 ⊆ 現行。
5. 段 6: review 2 本 → fix → 変異 (probe → 較正 → 本走) → 受入。
