---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-20
wave: dev-wave-t1442-c06-reachability
seq: 2
---

## {{D:c06-reachability-explorer-alignment}}. C06 evaluator の reachability 検査を C03/C05/C07 と同型の idiom へ揃える

**決定:** `_evaluate_c06` の supervisor 側 reachability 検査を、ad hoc な
`_reachable_functions`/`_reachable_calls` (呼び出し名の文字列一致のみ、import 束縛を検証しない)
から `_ReachabilityExplorer`+`_declared_call` (import 束縛を実解決したうえでの cross-module
reachability 検査、`_evaluate_c05` と同型) へ置換する。supervisor/`run_trial` 不在時は無条件
skip をやめ明示的に `_c06_unsatisfied` を返す (`_evaluate_c03`/`_evaluate_c05` と同型)。
`_ledger_lock`/`_check_limit_state` の呼び出しを per-function `required_calls` dict +
`_live_called_names` で検査する (`_evaluate_c05` と同型)。契約 JSON の `reachable_from` 3文字列と
evaluator 側期待値の整合を確認する `_c06_reachable_from_verdict` を追加する (`_evaluate_c07`
の契約整合検査と同型)。手動の `_MAX_REACHABILITY_STATES` 検査は `_ReachabilityExplorer` 自身の
limit 超過検出に委ね削除する。

**理由:**
- D599 (2026-08-20) が挙げた C06 reachability 検査の3弱点 ((a) supervisor 不在時の無条件 skip、
  (b) 呼び出し名の文字列一致だけで import 束縛を検証しない、(c) `_ledger_lock`/
  `_check_limit_state` の存在のみ検査) は、同ファイル内の姉妹評価器がすでに個別に持つ idiom を
  そのまま転用でき、新規機構の発明を要しなかった (規律5「盛らない」、既存 idiom の再利用)。
- 弱点(b)は、supervisor 内に同名ローカル decoy 関数 (budget_consumer からの import ではない)
  があっても旧コードが名前集合の一致だけで通過させる実害を、旧コードに対する A/B 実測
  (decoy fixture、`test_c06_rejects_name_only_supervisor_decoy`) で確認した。
- 実 repo 現行状態への判定結果は変更しない (`EVIDENCE_UNDEFINED`/
  `completion-proof-not-machine-checkable` のまま。D599 が前提とする「C06 は SATISFIED を
  一切返さない」設計もそのまま)。`_check_limit_state`/`_ledger_lock` の呼び出し実在は
  `s8c_budget.py` の実コード (`:474,556,572,604`) で事前確認済み。

**却下した選択肢:**
- `_c06_reachable_from_verdict` を実コード上の呼び出し順序まで歩いて検証する設計へ拡張する —
  段3 敵対相談2レンズ (sol/luna) が独立に、`_evaluate_c07` の同型 idiom 自体も実は契約記述
  同士の membership 整合確認に留まり実コード順序は見ないことを指摘した。実コード順序の検証には
  `_evaluate_c07` の局所 dataflow 機構 (`_c07_expression_reaches_check` 系) の汎化か
  cross-call 引数追跡の新設を要し、規律5 に照らし見送った。実装した
  `_c06_reachable_from_verdict` はこの限定をコードのコメントに明記する。
- `_ledger_lock`/`_check_limit_state` 検査を `_ReachabilityExplorer` ベースへ引き上げる —
  両関数は `reserve_all_cells`/`settle` と同一 module 内で定義されており、現行コードは
  cross-module import の曖昧性を持たない。per-function dict 方式で現状十分と判断した。

**残る限界:** per-function `required_calls` dict 方式 (`_live_called_names`) は末尾識別子名だけを
比較するため、同一 module 内の同名ローカル decoy 関数 (例: `reserve_all_cells` 内にネストした
`_ledger_lock` という名の関数) や属性経由の呼び出し (`other._ledger_lock()`) を区別できない。
段3 (sol/luna)・段6 (reviewA/reviewB) の計4レンズが独立にこの限界を指摘したが、現行
`s8c_budget.py` は同一 module 内の bare-name 呼び出しのみで安全であり実害は無い。再訪条件は
「`s8c_budget.py` が `_ledger_lock`/`_check_limit_state` と同名の別 object を import または
局所定義する変更を受けたとき」とする。

**scope外:** 同じファイル内の `_evaluate_c12` が使う helper も C06 改修前と同じ
`_reachable_calls` 名前一致弱点を持つが、本決定は `_evaluate_c06` だけを対象とする
(次 task 候補として worklog に記録)。
