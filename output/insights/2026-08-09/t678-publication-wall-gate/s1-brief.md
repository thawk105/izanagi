# 段 1 brief — [T-678] 最終 publication 後の wall gate 再評価

## 依頼
launcher が最終 publication 後に wall gate を再評価しないため、receipt の staging / publication が
10〜20 秒級で停滞しても `accepted` で通る。publication 完了後にも wall gate を再評価する形へ直し、
テストで固定する。

## 出処
T-663 wave (worklog 324) の裁定パッケージ候補 S2。一次資料 =
`output/insights/2026-08-09_t663-launcher-flake-diagnostic/s4-adjudication.md` (S2)、
同 `s3-lensA.md` 所見 5。

## 実測 (親、2026-08-09、worktree `worktree-dev-wave-t678-publication-wall-gate`、base `bcda1c02`)
`tools/codex_worker_launch.py` の `_stage_receipt_write` 先頭へ `time.sleep(4.0)` を一時挿入
(tracked file の一時変異、`git diff --stat` = 1 file 1 insertion、`git checkout --` で復元、復元後 tree clean)。
`python3 tools/run_tests.py orchestrator/tests/test_codex_worker_launch.py::test_positive_p1_normal_job_is_accepted -n 1`
= **1 passed in 5.04s** (Pegasus dispatch request `896677.nqsv`)。
fixture の `max_wall="3"` に対し実経過が約 4.4 秒でも receipt は
`outcome=accepted` / `stop_reason=completed` / `launcher_rc=0` のまま。**穴は実在する。**
harness の外側 `timeout=10` もこの停滞を赤にしない。

## 現状のコード事実 (base `bcda1c02`)
- 最後の wall 再評価は `_run_supervised` の `_latch_final_job_limit` (`tools/codex_worker_launch.py:1739`)
  で、**`outcome == "accepted"` 分岐の中**にある。
- その後に `_audit_receipt_value` (`:1751`)、`_stage_receipt_write` (`:1758`)、
  `_atomic_create_json_reserved` (`:1759`) が続き、この 3 段の経過時間は gate に入らない。
- gate 入力は既存 field で足りる (`DW-O13`): `limits.max_wall_clock_s`、`actuals.wall_clock_s`、
  `attempts[-1].limit_trigger` / `.accepted`、`outcome` / `stop_reason` / `launcher_rc`。
  実 artifact (`/work/1/SFC/tanab/dev-wave-jobs/task-inventory/review-a/receipt.json`) で
  `schema_version=2` / `wall_clock_scope=launcher_start_to_receipt_fields_finalized` を確認済み。

## 不変条件
1. 受理集合は「宣言した wall 予算内で receipt field を確定できた job」へ**狭まるだけ**とする。
   予算内で終わる正常経路 (既存 fixture の全 positive test) の受理は不変。
2. receipt は create-only 公開のまま。N-3 順序 (receipt slot 予約 → output 公開) を崩さない。
3. `rc` と receipt の整合を崩さない。receipt が `accepted` なのに rc≠0、の組合せを作らない。
4. checker (`_validate_receipt`) の schema v2 束縛と既存実 receipt の互換を壊さない。
5. テストを甘くして緑にしない。既存 assert の期待値を反転・緩和・skip しない。

## 親の provisional 裁定 (攻撃対象)
- **(P1)** 再評価点は `_stage_receipt_write` の**後**、`_atomic_create_json_reserved` の**直前**に置く。
  receipt は create-only なので atomic create の**後**に受理を取り消す手段がなく、
  create 後の再評価は「receipt=accepted かつ rc≠0」を生んで不変条件 3 を破る。
  したがって「publication 完了後」の要求は「publication の費用 (staging / audit) を計上した上で
  公開直前に再評価する」として満たす。残余 (最後の staging と atomic create 自体) は
  scope 外として正直に記述する。
- **(P2)** `wall_clock_scope` の文字列は `launcher_start_to_receipt_fields_finalized` のまま据え置く。
  再評価は「field 確定時点」を後ろへ動かすだけで、文言は真のまま。schema_version は上げない。
- **(P3)** 再評価で `accepted` → `not_accepted` へ flip したときは、既に公開した output を unlink し
  `args.output_published_by_run` を戻し、新 receipt で `_audit_receipt_value` を再走してから公開する。
- **(P4)** 再構築 → 再 staging の反復は 1 回だけとし、無限後退させない。
- **(P5)** 単一実装単位 (production + test は同一族のため分割しない)。

## 成果物の形
- production 差分 (`tools/codex_worker_launch.py`) + テスト (`orchestrator/tests/test_codex_worker_launch.py`)。
- テストは最低 3 点を固定する: (a) staging 停滞で `not_accepted` / `stop_reason=max_wall_clock_s` / rc=1、
  (b) 正常経路は `accepted` のまま、(c) flip 時に published output が残らない。
- docs (worklog fragment、insights)。

## 成果物影響 (DW-G05)
放置すると、宣言 wall 予算を超えて完了した codex worker job が `accepted` receipt を出し続ける。
receipt の `limits_assertion="self_asserted"` による予算遵守主張と `actuals.wall_clock_s` が
矛盾したまま、受理 conjunct が 10〜20 秒級停滞を検出しない。
= この launcher の receipt を根拠に成果物 (子が生成した plan / review / 実装) を採用する経路で、
実際には予算違反の走行に採用判断が下りる。

**訂正 (親、段 2 投入後に判明した既知事実)。** `tools/codex_worker_launch.py` の
**production caller は repo 内に存在しない** ([T-595] 実測、
`output/insights/2026-08-07_t595-reasoning-ab-latch/s4-ruling.md`)。現行 `DW-O01` は raw
`codex exec` を起動し `.done` と exit code だけを見る。したがって現時点の成果物影響は
**(a) dogfood receipt (例 `/work/1/SFC/tanab/dev-wave-jobs/task-inventory/review-*/receipt.json`) の
受理主張が偽になること**と、**(b) [T-665]/[T-662] の候補案 (a)「`DW-O01` を launcher 経由へ集約」が
採られた時点で全 dev-wave 子成果の採用条件になること**の 2 点に限られる。
brief 初版はこの限定を書いていなかった。**この訂正は段 3 のレンズにも攻撃対象として渡す。**

## 環境
受入・テストは `tools/run_tests.py` の自動判定 (Pegasus: login 空きメモリ × queue 可用性)。
性能測定は含まない。
