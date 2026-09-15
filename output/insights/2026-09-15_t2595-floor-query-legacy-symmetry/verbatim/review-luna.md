## fixture の実体性

**refuted — fixture が今回の検査を迂回している、という疑い。**

- [`test_s8b_holdout_admission.py:1825`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2595-floor-query-legacy-symmetry/orchestrator/tests/test_s8b_holdout_admission.py:1825) の `_issued_cell` は実 reservation・finalize を通す。`_reserve` は同ファイル **231 行付近**で protocol resolver を差し替えるが、admission の認可・consume・候補計数は差し替えない。
- 同ファイル **1900–1998 行**の registry helper は実 `create_attempt_registry_genesis`・`reserve_attempt_slot`・`record_attempt_recovery` を使い、registry と standalone receipt を作る。scheduler の観測自体は合成データである。
- [`同ファイル:44`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2595-floor-query-legacy-symmetry/orchestrator/tests/test_s8b_holdout_admission.py:44) の `_pin_test_recovery_authority` が替えるのは **`_FLOOR_RECOVERY_AUTHORITIES` の許可集合だけ**。今回の条件は authority 検証より前の候補有無で拒否するため、この差し替えによって「通って当然」にはならない。
- 新テストは実 query・consume・inspection を呼ぶ。registry replay を成功扱いにする stub は追加していない。

## registry 変形の妥当性

**refuted — 壊した行が候補から落ち、ケースが空振りする、という疑い。**

[`s8b_holdout_admission.py:5476`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2595-floor-query-legacy-symmetry/orchestrator/campaign/s8b_holdout_admission.py:5476) の候補判定は、次の **OR** である。

1. 座標が対象 slot と一致する。
2. `start_event_sha256` が対象 start を指す。
3. receipt の対象 hash が対象 start を指す。

したがって、テスト **3565 行**で `configuration_id` を壊しても、維持された hash 参照により候補に残る。候補数は `valid-one=1`、`corrupt-one=1`、`valid-plus-corrupt=2`。

**refuted — `chained_event_row` が実在しない／hash を繋がない、という疑い。**

[`attempt_registry_core.py:264`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2595-floor-query-legacy-symmetry/orchestrator/campaign/attempt_registry_core.py:264) は index・previous hash を設定し、自己 hash を再計算する。追加側の **3573 行**は末尾 hash と `len(rows)` を渡しており、連結方法は正しい。

なお、`corrupt-one` は座標変更後の自己 hash を再計算しない。しかし候補 reader は canonical JSONL を読む段階で chain replay を行わない（production **5370–5395 行**）。これは候補計数前に不正行を捨てないことを検査する目的と整合する。

使用済み planned trigger は既存ループの **5851 行**で除外され、新設 **5886 行**へ到達する。例外文言も完全一致で検査しており、別 gate による拒否で緑になる構造は確認されなかった。

## 正例の代表性

**refuted — legacy retry／resume の production 退行を既存テストが検出できない、という疑い。**

[`test_s8b_floor_campaign.py:815`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2595-floor-query-legacy-symmetry/orchestrator/tests/test_s8b_floor_campaign.py:815) の helper は実 `_run_campaign_core` を呼び、retry query／cut-6 query を差し替えていない。

既存の対象は以下。

| テスト | 現物 | 検査内容 |
|---|---|---|
| `test_partial_reps_invalidates_session_and_burns_retry_then_nulls_pair` | 同ファイル:9780 | retry ordinal `[1, 2]`、無効 session、floor の null 値 |
| `test_retry_sequence_is_metamorphic_to_other_cells_values` | 同ファイル:9833 | 他セルの値を変えても retry 列が不変 |
| `test_resume_does_not_reissue_retry_slot_after_retry_start_crash` | 同ファイル:10928 | 実 crash 後に resume し、completed・ordinal `[1, 2]`・重複なし |

production は [`s8b_floor_campaign.py:6072`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2595-floor-query-legacy-symmetry/orchestrator/campaign/s8b_floor_campaign.py:6072) で実 query を採用し、**6179 行 → 6406 行**で retry を構築する。resume は **6593 行**で既存 retry start の `_replay_cut6_start` を通してから `_retry_round` に進む。

したがって、裁定が新しい campaign resume 正例を不採用にした判断は妥当。ただし、これらは**registry 不在の保存性**の証拠であり、新しい混在拒否が production で発火する証拠ではない。

## 波及と import 経路

**refuted — 二重収集・名前衝突・fixture 汚染。**

admission テストを module として利用する参照は次の 3 ファイル。

- `test_s8b_floor_stats.py:69`：`admission_cases` として import。**1219 行以降**で既存 helper を利用。
- `test_s8b_attempt_registry.py:39`：同様に import。**257・576・589 行**などで既存 helper を利用。
- `test_s8b_floor_attempt_launcher.py:29`：同様に import。**1664–1676 行**の既存差し替えは `finally` で復元する。

新テスト関数を各 module の `test_*` 名として再公開しておらず、module alias から新テストが二重収集される構造はない。追加の monkeypatch はテスト関数内だけで、共有 helper・autouse fixture・module 初期化処理は変更されていない。

production の直接 query consumer は `_Runner`。consume／inspection と共有 helper の意味は差分で変更されていない。

## 焦点走の過不足と meta-test

**refuted — 直接の変更経路・共有 helper 利用先が 12 ファイルから欠落している、という疑い。**

裁定が参照する段 2 plan の集合は、`orchestrator/tests/` 配下の以下である。

```text
test_s8b_holdout_admission.py
test_s8b_floor_campaign.py
test_s8b_floor_contract.py
test_s8b_attempt_registry.py
test_s8b_floor_attempt_launcher.py
test_s8b_floor_stats.py
test_s8b_holdout_freeze.py
test_s8b_oracle_driver.py
test_s8b_oracle_n_pilot.py
test_s8b_ratified_freeze.py
test_s8b_ratified_verify.py
test_s8b_terminal_evidence.py
```

変更した分岐を直接通るのは先頭 2 ファイル。前節の module import 利用先 3 ファイルも含まれている。残りは周辺回帰集合であり、12 ファイルすべてが新分岐を通るわけではない。

**real・nit — meta-test は 12 ファイルに含まれない。**

| 集合外のファイル | 今回との関係 |
|---|---|
| [`test_plain_runner_coverage.py:60`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2595-floor-query-legacy-symmetry/orchestrator/tests/test_plain_runner_coverage.py:60) | 全 test file の自走 harness を読む。追加先は **4421–4426 行**の pytest 委譲を維持しており、静的には契約を満たす。 |
| [`test_acceptance_schedule_order.py:660`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2595-floor-query-legacy-symmetry/orchestrator/tests/test_acceptance_schedule_order.py:660) | 実 collection と所要時間台帳の対応・90% coverage を検査。追加により nodeid が 4 件増える。 |
| `test_pytest_collection_config.py:423` | test file 集合を列挙するが、対象は verifier／oracle の除外契約。既存 file 内の関数追加では集合は変わらない。 |

追加 4 ケースは `acceptance_duration_ledger.json` に未収載。既存 consumer は未収載を `None` として扱う（`conftest.py:1676`）ため、**未収載だけで失敗とは判定できない**。90% 検査の実結果は未確認。

これらの集合外項目を、production 回帰の欠落や新しい必須 gate として扱う根拠はない。

## scope の膨張と不足

**refuted — プラン v2 を超える実装変更／採用項目の未実装。**

- production 差分は裁定の legacy ブロックと一致する。
- 採用 1 の 3 parameter、採用 2 の同一 trigger による retry1・retry2 consume を実装している。
- **3609–3612 行**の inspection 拒否確認は、同じ履歴に対する既存検査の確認であり、本題内。
- 不採用の campaign resume 新規テストは追加していない。
- 新規 file・共有 helper 変更・gate・台帳・framework の追加はない。

変異 4 件を撃つ構造は静的に成立する。変異の実測結果は本レビューでは確認していない。

## must-fix と nit の分別

**must-fix：確認されなかった。**

この差分を放置すると certified 選択・レポート・台帳の値／受理集合／参照が壊れる、と具体的に示せる新規欠陥は見つからなかった。

**nit：** 焦点走 12 ファイルだけでは、上述の collection／自走／所要時間 meta-test の結果までは証明しない。新規 4 nodeid の所要時間も未収載。成果物への影響を示せないため、must-fix にはしない。

## 裁定パッケージ候補 (scope 外の real 所見)

裁定済みの次の事項は現物でも残っている。今回の差分が導入した問題ではない。

- **real・backlog：round 非対称。** production **5741–5746 行**の legacy canonical 判定は completion の round を検査せず、query **5836 行**は検査する。
- **real・backlog：hash 型不正。** production **5485–5486 行**の集合 membership に list／dict が来ると `TypeError` になり得る。
- **real・backlog：production recovery writer 未接続。** `record_attempt_recovery` の非テスト参照は core 定義と `s8b_attempt_registry.py:3537` の内部委譲。今回の変更は collector の接続を実装していない。

追加の framework・gate・期待値変更は提案しない。

## 総括

**静的レビューで新規 must-fix は確認されなかった。** 候補計数は壊れた座標の行も捉え、新条件を迂回する stub はない。既存 production テストが legacy retry／resume の保存性を担い、実装範囲はプラン v2 に一致する。

pytest・変異テストは未実行。ファイル変更・commit は行っていない。