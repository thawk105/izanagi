# [T-1170] 自律試行 journal `run-start` の版を完全性 consumer が独立に持つ世代定数で読む改版追随 — 事実・裁定・実装・検証の一次資料

- authority: none
- default_effect: no-state-change
- 日付: 2026-09-18
- wave: dev-wave-t1170-run-start-schema-version (branch `worktree-dev-wave-t1170-run-start-schema-version`)
- 起点の裁定: D1898 (run-start は schema 版を上げる。版を上げる差分は新機能を使わない構成の正例を持つ。旧版 decoder は D1669 の条件が成立した場合だけ)、D1851、D1669、D2064 (決定 2・3)
- 基準: local main `d2ebef7a407dc6be61622ed596cf08b8b518f606` (= origin/main、着手直前)。実装 commit `1941828e1`
- 設計判断: 同 wave の decisions fragment (`docs/spool/decisions/2026-09-18-dev-wave-t1170-run-start-schema-version-2.md`、fold で D 番号が付く)

## 0. 結論

- **v5 へは上げない。** D1898 (2026-09-09) が求めた版上げは、T-304 (2026-09-16、`4c6f03048`) が role payload の key 改名で
  producer の共有定数 `SCHEMA_VERSION` を v3 → v4 へ上げた際に run-start 側にも実体化しており、v4 の run-start は 1 つの形
  (無条件 key + trial_binding 条件付き key、journal の seq/ts 込みで 16 / 23 key) しか持たない。本 wave はこの v4 を既存の版境界として
  利用した。T-304 の wave が本件を完了したと宣言したわけではないので、そう遡って記録しない。
- **消費側の世代を独立にした。** 完全性 consumer (`autonomous_trial_completeness._check_run_envelope`) は run-start の版を producer の
  生きた定数と照合していた。consumer 所有の独立リテラル `_RUN_START_SCHEMA_VERSION = "p3-autonomous-workload-trial/v4"` を追加し、
  これと照合する。拒否理由は `[run-envelope] run-start.schema_version unsupported: recorded=<記録の版>; generation=legacy|unknown;
  consumer_supported=<対応版>` (legacy は実在を確認した v3 の文字列 exact 一致だけ)。
- **受理集合は v4 のみで不変。** 旧版の変換・alias・decoder は足していない。producer・report 版検査は無変更。
- 依頼の前提を 2 点訂正した (§1)。

## 1. 依頼の前提の訂正 (段 1 実測、段 3 の 2 レンズが現物で裏取り)

1. 依頼が挙げる consumer 6 本のうち `attempt_registry_core.py` / `s8b_attempt_profile.py` / `s8b_floor_attempt_launcher.py` /
   `s8b_attempt_registry.py` の 4 本は lifecycle 台帳の `run_start_receipt_sha256` (launch 受領証の digest) しか触らず、journal
   `run-start` の版を読む consumer ではない (裏取り箇所: attempt_registry_core 883-889 / 1308-1312 / 1769-1777、s8b_attempt_profile 407-427、
   s8b_floor_attempt_launcher 526-535 / 1132-1136、s8b_attempt_registry 2582-2590)。6 本は `run-start|run_start` の grep hit をソートした
   先頭 6 件と一致する (起草経緯そのものは code から確定できない)。
2. journal `run-start` の版を直接照合する consumer は `_check_run_envelope` の 1 箇所。`trial_registry.py` (5967-5993) と
   `s8c_acceptance_receipt.py` (1496-1506) は binding field / arm_execution を読むが版を見ない。これらへの版 gate 追加は
   仮想リスク向けとして scope 外 (依頼文)。

## 2. 事実

- producer `p3_autonomous_workload_trial.py:142` の `SCHEMA_VERSION` は run-start event (5105-5139) と role payload (2926) の両方に使う 1 定数。
- v3 設定 `a506633ef` (2026-08-06) → v4 `4c6f03048` (2026-09-16)。この間に run-start へ 7 key が版据え置きで追加された
  (無条件: `generation_driver` / `gating_spec_sha256` / `honest_accounting_authority`、trial_binding 条件付き: `prereg_content_commit` /
  `prereg_effective_commit` / `slot_id` / `arm_execution`)。`4c6f03048` と HEAD で run-start の key 集合は一致 (T-1170 が指した drift は v3 の中にだけある)。
- repo 内の記録済み v3 run-start は `output/insights/2026-08-15_t1097-s8c-live-abc/verbatim/attempts.jsonl` 2 行目 (13 key 旧形) の 1 本。
  `orchestrator/` `tools/` の Python に同 artifact への直接参照は無い (動的な読み手・repo 外の用途の不在は証明していない)。
  v3 + 新形の記録は repo 内に無い。
- 完全性 test の `_start` fixture は v4 + 無条件 3 key + binding 無し = D1851 が求める「新機能を使わない構成」の正例そのもので、
  既存 test (`test_p1_complete_three_cell_fixture_passes` 等) が既に通していた。
- 旧文言 `does not match producer version` の pin は完全性 test の 2 node だけ。変更 2 file の sha256 は `output/` と台帳に pin されていない。
  `s8c_preregistration_evidence_contract.v1.json:398` は field path / 到達性の pin。両 file とも `CONTRACT_LOADER_RELATIVE_PATHS` に無い。
- role payload 側は `_ROLE_SCHEMA_VERSION` (completeness) と `s8c_generation_projection.ROLE_SCHEMA_VERSION` の独立二重定義で
  consumer が読める世代を持つ (D2064 決定 2)。run-start 側だけが producer の生きた定数を見ていた。

## 3. 段 4 裁定 (所見の裁定と plan v2)

`verbatim/ruling-t1170.md` に逐語。要点:

| 出所 | 所見 | 判定 |
|---|---|---|
| 段 3 レンズ B must-fix 1 (レンズ A nit 1 も同旨) | 変異 M1〜M3 は「比較右辺を producer 定数へ戻す」退行を検出できない (双方 v4) | real・採用: 独立性 test + 変異 M4 |
| plan / 両レンズ | brief F2 (16/23 key)・F3 (直接照合は 1 箇所)・F5 (読み手は確認できた範囲)・P1 (D1851 は形を変えない bump の禁止ではない)・P5 (直接の原因は consumer の参照) の訂正 | real・採用 |
| レンズ A nit 2 | 「構造化」は例外文言内の明示で、機械可読属性の追加ではない | real・記録の書き方に反映 |
| レンズ A nit 3 / B nit 3 | 世代診断は版 gate に到達した記録に対する保証 (report 版・journal hash・順序が先行) | real・記録に限定を書く |
| レンズ B nit 4 | decisions fragment 不要 | 一部採用: consumer 契約 (interface) の変更と v4 利用の事実が未記録なので短い D を書く |
| plan M0 | docstring 変異は `__doc__` が変わり非等価 | real・comment 変異へ |

## 4. 実装 (Codex author 1 本、commit `1941828e1`)

- `orchestrator/campaign/autonomous_trial_completeness.py`: 428-429 定数追加、2242-2254 版検査置換。
- `orchestrator/tests/test_autonomous_trial_completeness.py`: 既存 2 node の run-start 側期待を全文一致へ (report 側据え置き)、新規 4 node:
  `test_run_start_v4_without_binding_is_accepted` / `test_run_start_v3_legacy_shape_is_rejected` /
  `test_run_start_unknown_schema_version_is_rejected` / `test_run_start_schema_version_is_independent_of_producer`
  (producer 定数を `monkeypatch.setattr(A, "SCHEMA_VERSION", …)` で別値にしても v4 記録の判定が変わらず、その別値の記録は unknown で拒否)。
- author の自走: completeness 287 passed、統合正例 2 node passed、meta-test 6 node passed。

## 5. 検証

- 焦点走 (親、実装 commit `1941828e1`、completeness の importer 14 file): login bounded local は memory 上限 (2.4 GB) で終了し、
  自動で計算ノードへ dispatch (request 4989.nqsv、Elapse 105 秒)。**1638 passed / 5 skipped / 0 failed**、child rc=0。
  5 skip は既存の growth hold による未実行で、成功扱いではない。受入全走ではない。
- 段 6 敵対レビュー 2 本 (`verbatim/review-a-out.md`、`verbatim/review-b-out.md`): **must-fix 0 / 0**。code 修正 nit 0。
  レンズ B の docs 案訂正 3 点 (F332 追記の分類説明、D2064 決定 3 の適用範囲、読み手探索の範囲) を fragment に反映。fix 子は起動していない。
- 変異 matrix: container worktree `.codex/worktrees/t1170-mutcontainer` (HEAD `1941828e1` = 実装 commit、code の fix 無し)、`tools/mutation_harness.py`、
  runner = `python3 tools/run_tests.py orchestrator/tests/test_autonomous_trial_completeness.py orchestrator/tests/test_p3_autonomous_workload_trial.py -q -rf --force-dispatch -p no:cacheprovider`
  (計算ノード dispatch、`--detached`)。probe 走 (全件 SURVIVED 登録、`mutation/spec-probe.json`、sha `301d46a2…`) で観測 node を集め、それを期待 node に写した
  本走 (`mutation/spec-final.json`、sha `d3b9ba58…`)。**本走 = baseline PASSED、KILLED 4 / SURVIVED 1 / MISMATCH 0 / TIMEOUT 0、期待 node と観測 node が
  完全一致** (`mutation/ledger-final.json`)。anchor は全件 file 内で一意。

  | ID | 変異 | 種別 | 観測 node (完全集合) |
  |---|---|---|---|
  | M0 | 新定数の comment の句点だけ変更 | 等価対照 | SURVIVED (0) |
  | M1 | run-start 版検査 block を `if False:` で無効化 (report 版検査は残す) | **fail-closed kill** (v99 / 欠落が版 gate を素通り) | `test_run_start_unknown_schema_version_is_rejected`、`test_run_start_schema_version_is_independent_of_producer`、`test_report_and_run_start_schema_versions_are_required[start]`、`test_role_schema_v4_and_report_schema_v3_are_required`、`test_run_start_v3_legacy_shape_is_rejected` (5) — 最後の旧形 node は拒否理由が後段 `generation_driver` 検査へ移ることの検出であり、受理拡大の検出ではない |
  | M2 | `_RUN_START_SCHEMA_VERSION` を v3 へ | **受理集合 kill** (v4 の記録が全部拒否) | completeness / producer test の v4 fixture を使う 209 node (`test_run_start_v4_without_binding_is_accepted`、`test_transport_admission_error_persists_verified_partial_report`、`test_fixture_trial_runs_ycsb_abc_and_binds_descriptor` を含む)。複数の診断期待も同時に壊れるため単一理由に集約しない |
  | M3 | legacy / unknown の割当てを交換 | 診断契約 pin (受理集合は不変) | M1 と同じ 5 node (全文期待の不一致) |
  | M4 | 比較右辺を `producer.SCHEMA_VERSION` へ戻す (定数は残す) | **独立性 kill** (本 wave が除いた依存の回帰) | `test_run_start_schema_version_is_independent_of_producer` (1) |

  test 自体は 1 走 38〜48 秒、queue 待ち込みで最長 425 秒 (probe M0)。probe 07:01〜07:17 JST、本走 07:19〜07:37 JST。

## 6. 裁定パッケージ候補 (scope 外、実装に混ぜていない)

- producer の run-start / role payload の schema 定数・系列の分離。
- report schema の consumer 所有化 (同 function で producer 定数照合が残る)。provider / budget も producer 定数に依存する。
- v3 の歴史閲覧需要が実在した場合の歴史 decoder (D1669) と、同じ v3 内の形の混在 (13 key 旧形 / field 追加後) の扱い。
- trial_registry / s8c_acceptance_receipt の run-start 読み取りに版検査の責任を置くか。

## 7. 工数

codex 子 6 本 (plan 1、consult 2、author 1、review 2、fix 0、全段 `gpt-6-astra` / `medium`)。親の実測: 焦点走 1 (dispatch)、変異 12 走 (probe 6 + 本走 6、dispatch)、
check_docs、三軸語走査、受入全走 1 (land 前)。

## 逐語

- `verbatim/brief-t1170.md` (段 1 brief)、`verbatim/plan-out.md` (段 2)、`verbatim/consult-a-out.md` / `verbatim/consult-b-out.md` (段 3)、
  `verbatim/ruling-t1170.md` (段 4)、`verbatim/author-out.md` (段 5)、`verbatim/review-a-out.md` / `verbatim/review-b-out.md` (段 6)。
- `mutation/spec-probe.json`、`mutation/ledger-probe.json`、`mutation/spec-final.json`、`mutation/ledger-final.json`。
