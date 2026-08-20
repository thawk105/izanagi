---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-20
wave: dev-wave-t1421-c06-machine-checkable-promotion
seq: 1
---

## {{D:c06-past-commit-reason-drift-is-precedented}}. C06 昇格による過去 commit の reason code 遷移は新規回帰ではないと裁定する

**決定:** `_MACHINE_EVALUATORS` へ C06 を追加すると、過去 (昇格前) commit を現行コードで評価した
際の reason code が `budget-consumer-contract-undefined` から `completion-proof-not-machine-checkable`
へ変わる。これは段6 敵対レビューの一方が blocker として指摘したが、親が
`PredicateRegistry.evaluate_all`/`_evaluate_undefined` の実装を直接読んで検証した結果、
**新規回帰ではなく、C05/C07 等の既存 9 条件の昇格でも既に発生している既存挙動**と裁定した。

**理由:**
- `evaluate_all` の dispatch (`if condition.machine_checkable: ... else: _evaluate_undefined(probe)`)
  は評価対象 **commit 自身の契約 blob** の `machine_checkable` で production/undefined を振り分ける。
  historical commit の契約が false のままなら `_evaluate_undefined` へ入る。
- `_evaluate_undefined` 内の `if number in _MACHINE_EVALUATORS:` 分岐は、**現在のコード** (実行時の
  静的 dict) のメンバーシップで判定する。ここが commit ごとに変わらない以上、ある条件番号が
  一度でも `_MACHINE_EVALUATORS` に載れば、その条件番号を持つ historical (昇格前) commit の
  reason は全て汎用理由へ変わる。現在の dict には既に 1/2/4/5/7/9/10/11/12 が入っており、
  これらの昇格前 commit を現行コードで評価しても同じ遷移が起きる (実測はしていないが、
  コード構造上必然)。
- `test_current_repository_gap_reason_snapshot_requires_cross_wave_review` はこの遷移を意識的に
  吸収する設計 (テスト名の「cross wave review」どおり、reason 変化を drift ではなく明示レビュー
  対象として記録する)。段5 実装がこの test の C06 entry を正しく更新している。

**却下した選択肢:**
- レビュー所見が提案した「`number == 6` 分岐を map membership より前に置く」— C05/C07 など既存の
  昇格条件の挙動と非対称になり、過去の昇格を無断で書き換えることになるため不採用。

## {{D:c06-reachability-gap-deferred}}. C06 evaluator の reachability 検査の弱点は本 wave では修正せず後続 wave へ送る

**決定:** `_evaluate_c06` の reachability 検査には (a) `supervisor is None` 時のスキップ、
(b) reachable 呼出しの集合だけを見て順序・データフローを見ない、(c) `_ledger_lock`/
`_check_limit_state` は存在のみ検査、という既知の弱点がある。段2 codex plan・段3 敵対相談2レンズ・
段6 敵対レビュー2本が独立に同じ弱点を確認したが、**本 wave では評価器本体のロジックを変更せず、
registry 登録のみを行う**。

**理由:**
- `SATISFIABLE_CONDITION_IDS` は空集合のままであり、`evaluate_all` 自身が
  `is_satisfied(result.status) and identifier not in SATISFIABLE_CONDITION_IDS` を検知すると
  強制的に `ERROR/evaluator-internal-error` へ倒す防御的再チェックを持つ。したがって
  reachability 検査が甘いままでも、本 wave の昇格そのものが受理ゲートを緩めることはない
  (規律2 は侵害されない)。
- D533 は「評価器の実装だけを先に置くことは許すが、registry 登録は残りと切り離さない」と定めており、
  評価器本体の改善と registry 登録操作は元々別の変更単位として扱われる設計である。
- 名前付き negative control (`nc_c06_one_arm_reservation_removed`) 自体は正しく検出される
  (`_c06_field_path_verdict` の `_c06_expected_rows` 比較、変異 M3 で実測確認済み)。弱いのは
  reachability の一般性であり、登録済み negative control の検出力ではない。

**却下した選択肢:**
- 本 wave で reachability 検査を強化する — regulation5 (段階導入・盛らない) に反し、D529 が
  定義する昇格操作 (4点の不可分な変更) の scope を超える。
- 昇格自体を保留する (段6 レビューの一方の推奨) — 少数意見であり、上記の防御的再チェックにより
  実害がないため、11/12 条件が既に機械検査可能な中で C06 だけを人為的に留める理由がない。
