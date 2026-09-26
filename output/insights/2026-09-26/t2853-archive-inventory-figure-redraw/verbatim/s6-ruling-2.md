# 段 6 裁定 2 — [T-2853] (1') fix 1 後の親の実測所見 (焦点再レビューの結果は §3 に追記)

- 対象: fix commit d6290aecee4fd2242b17914f380774813d5ed098。

## 1. 親の所見 P-M1 (must-fix、real・scope 内)

- 事実 (親の実測): `orchestrator/campaign/pin.py` の `CURRENT_PIN = "6810666"` (7 桁の短縮 SHA)。`b10_backoff_shape_sweep.py`・`axis_silo_function_policy.py`・`axis_trigger_gating.py`・`axis_mocc_temperature.py`・`backoff_profile.py`・`backoff_sweep.py`・`between_run_floor.py`・`p3_s4_loop_sort.py` がこれを pin にし、旧 driver は `"dff0f1e"` を使う。`output/campaigns/*/campaign.lock` の `ccbench_commit` 30 件はすべて 7 桁。
  build 側の照合 `buildcache._verify_ccbench_commit` (buildcache.py:3822-) は `head.startswith(declared)` の前方一致で受理する。
- 欠陥: fix 1 の照合 `source_head != evidence.ccbench_commit` は完全一致なので、短縮 pin の経路では本番の保全が恒常的に failed になる。
- 放置時の影響: 今後の論文根拠の実験 (現行 pin を使う driver) の inventory がすべて `failed` になり、R1 の入力一式が完成品として残らない (本題の不成立)。また記録する `ccbench_pin` が短縮形だと R1 の checkout が曖昧になりうる。
- 処置: 照合を build 側と同じ前方一致 (`source_head.startswith(evidence.ccbench_commit)`、空の宣言は不一致) にし、inventory の `ccbench_pin` には解決済みの完全 SHA (`source_head`、40 hex) を記録する。宣言値は `ccbench_pin_declared` に並べる (R1 の手順書が宣言と実体の対応を示せるように。field は 1 つだけ)。

## 2. 変異の追加登録 (DW-M01、fix 前)

| ID | 変異 | 期待 | kill 点 |
|---|---|---|---|
| M12 | pin の照合を前方一致から完全一致に戻す | KILLED | 新 test `test_r1_short_pin_records_full_head` (evidence の `ccbench_commit` を実 HEAD の先頭 7 桁にした入力で inventory が complete、`ccbench_pin` が 40 hex の実 HEAD、`ccbench_pin_declared` が 7 桁) |

M11 (pin の照合を外す) は `test_r1_pin_drift_marks_failed` (実 HEAD と違う 40 hex) のまま有効。

## 3. 焦点再レビュー 1 巡目の結果

焦点再レビュー 1 巡目 (`codex/s6-focus-1.md`、check_codex_output rc=0) は NO-GO。対応表: A-M1・B-M1 partial (短縮 pin の通常経路で HEAD 照合が恒常的に失敗 = P-M1 と同一)、A-S2・A-S3・B-S2 closed、B-N3 not-addressed (裁定どおりの nit)、焦点走 1 回目の赤 10 件 closed (静的)。
新規 must-fix 1 件は P-M1 と同一 (独立に同じ反例: `pin.CURRENT_PIN = "6810666"`)。代案の `rev-parse --verify <pin>^{commit}` による解決は、build 側 (`buildcache._verify_ccbench_commit`) が前方一致で受理している以上、前方一致と同じ受理集合になる (tag は build 側で既に拒否される)。**§1 の前方一致を採用**し、build 側と同じ規則にそろえる。
patch hash の取得は `_tracked_diff_sha256` と同じ argv・sanitized env・source root (realpath) であることもレビュー子が確認した。M1〜M11・C0 の kill 点は静的に成立 (probe は未実走)。

## 4. fix 2 (commit a8282c4fe) と焦点再レビュー 2 巡目

- fix 2 (`codex/s6-fix-2.md`、受理 rc=0): 前方一致の照合、`ccbench_pin` = 解決済み完全 SHA、`ccbench_pin_declared` = 宣言値、新 test `test_r1_short_pin_records_full_head`。基準 74e6d2f23 からの追加行 production 64・test 191 (上限 120・280 の内)。
- 焦点再レビュー 2 巡目 (`codex/s6-focus-2.md`、受理 rc=0): **GO、新規所見なし**。短縮 pin の must-fix は closed、1 巡目の closed 項目に regression なし。短縮 SHA・完全 SHA・別 commit の短縮形で保全と build 側の受理が一致し、空の宣言は SourceEvidence が既に拒否することをレビュー子が確認。
- DW-O16 の巡数: 焦点再レビュー 2 巡で閉じた (上限 3 巡の内)。
