## 所見対応表

- fix-1: closed（実装済み・未実走）— `s8c_schedule.py:167,210`、テスト `test_s8c_schedule.py:175,192`
- fix-2: closed（実装済み・未実走）— `s8c_schedule.py:499,533`、テスト `test_s8c_schedule.py:248`
- fix-3: closed（実装済み・未実走）— `test_s8c_schedule.py:302,311,320`、`test_s8c_preregistration_predicates.py:2311`
- fix-4: closed（実装済み・未実走）— `test_s8c_preregistration_invariant.py:41-42`

## 変異が赤になる論証

- m03: 外部 initial-state digest を1 bit反転する `test_verify_schedule_rejects_external_initial_digest_bitflip` が、shared 呼出し削除後に `ScheduleError` を得られず赤になる。
- m07: 5 cell の `Schedule` を bytes 経由せず shared verifier へ渡すテストが、6 cell 構造違反を検出して赤になる。
- m08: 6 cell で ordinal を重複させた直接構築テストが、全単射違反を検出して赤になる。
- m10: consumer 不在の一時 commit を `_evaluate_c05` へ渡すテストが、`EVIDENCE_UNDEFINED / schedule-consumer-undefined` 以外の結果で赤になる。

## 不変性の自己確認

- `NEGATIVE_CONTROL_CASES` は既存7件のまま。C05 は別集合。
- `test_satisfiable_predicate_requires_negative_control` の exact 集合と `exercised == 7` は不変。
- `_MACHINE_EVALUATORS` は7件、`SATISFIABLE_CONDITION_IDS` は空集合のまま。
- gap snapshot の C05 は `EVIDENCE_UNDEFINED / schedule-schema-absent` のまま。
- 契約 JSON、凍結 record、`DECIDER_VERSION`、既存期待値は未変更。
- `s8c_schedule.py` に禁止された import/string はなし。commit は作成していない。

## 実走状況

pytest、mutation、受入走、`check_codex_agents.py`、`check_docs.py` は未実走です。AST parse、diff check、禁止文字列検査のみ実施しました。

## 波及

既存の期待値と既定の呼び出し形は維持しています。新しい任意 digest は `consume_schedule` まで転送されます。production wiring、registry、artifact、docs は変更していません。着手前から存在した `s8c_preregistration_evidence.py` の親差分は保持しています。

## 総括

fix-1〜fix-4 を許可された4ファイルへ実装しました。  
外部 digest、直接 Schedule 検証、consumer 不在分岐の検出テストを追加しました。  
既存の C05 未発効状態と不変集合は維持しています。  
実走とmutation確認は親へ引き継ぎます。