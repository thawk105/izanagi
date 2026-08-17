### A-01 — C12 allocation gate は未束縛・dead・nested の同名 call を到達済みと誤認する

- 分類: real
- 深刻度: must-fix
- 根拠: `orchestrator/campaign/s8c_preregistration_evidence.py:298`, `:351`, `:1550`。`_called_names()` は canonical binding を見ず、`ast.walk()` が拾った裸名・属性末尾名を採用する。静的検算では、未 import の裸 call、`if False:` 配下、未呼出し nested function 配下の3入力すべてで `_c12_allocation_binding_verdict()` が `None` を返した。正例 fixture 自体も `reservation` から import せず裸名を呼んでいる (`orchestrator/tests/test_s8c_preregistration_predicates.py:478`)。
- 具体的失敗: `reservation.py` に2定義だけ置き、`run_trial` 内では未束縛名、別 object の同名 method、または dead/nested call を置くと、実際の予約 consumer が走らなくても allocation gate を通過する。
- 成果物影響: C12 が `UNSATISFIED / allocation-enforcement-consumer-absent` から `EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable` へ前進し、ActivationReport の status・reason・evidence・digest と将来の受理集合を広げる。

### A-02 — cross-module walker は明白な非実行経路を call edge と数える

- 分類: real
- 深刻度: must-fix
- 根拠: `orchestrator/campaign/s8c_preregistration_evidence.py:532`, `:547`, `:1267`。`if False:` の body は除くが、`if True:` の `else`、`while False:`、無条件 `return` 後を除かない。静的検算でも `if True: ... else: target()` と `return; target2()` の両 call が `_live_nodes()` に残った。
- 具体的失敗: 正しい target call を `if True` の `else` または `return` 後だけへ移しても、C01/C04/C09/C12 の graph に canonical call が残る。
- 成果物影響: 対象条件の不在 reason が terminal undefined または後段 reason へ前進し、ActivationReport と digest、将来の受理集合が汚染される。

### A-03 — C09 は別条件が宣言した path の同名関数を正規 target と誤認する

- 分類: real
- 深刻度: must-fix
- 根拠: `orchestrator/campaign/s8c_preregistration_evidence.py:128`, `:1444`, `:1721`。C09 は target owner を固定せず、全12条件の `evidence_paths` 和に属する任意 path と関数名だけを確認する。
- 具体的失敗: producer が `env_contract.py` など別条件の宣言 path に置いた no-op `assert_campaign_layer3_chain` を import・callすれば、正規の `autonomous_trial_completeness.py` を呼ばなくても producer gate を通る。宣言外 decoy の既存負例ではこの cross-wire を検出できない。
- 成果物影響: C09 が `layer3-producer-unreachable` から後段または terminal undefined へ前進し、誤った blob が evidence と ActivationReport digest に入る。

### A-04 — decorator による callable 置換を無視して元関数本体を到達可能と扱う

- 分類: real
- 深刻度: must-fix
- 根拠: `orchestrator/campaign/s8c_preregistration_evidence.py:720`, `:730`, `:1279`。`_functions()` は `decorator_list` のある関数も無条件に canonical definition とし、walker は装飾後の runtime binding ではなく元の body を辿る。
- 具体的失敗: `@replace_with_noop` を付けた relay や target の元 body に consumer call を残すと、実行時は wrapper しか走らないのに到達済みとなる。
- 成果物影響: C01/C04/C09/C12 の不在判定が前進し、ActivationReport の reason・evidence・digest と将来の受理集合が広がる。

## 総括

最新方針の allocation-first 順序自体は、専用テストと D479 に合致する。実 tree では allocation gate が最初に停止し、独立 graph 検算でも `read_binding` / `check_reservation` は不到達、env/guard は到達だった。したがって、撤回前の「main 順では cross-module 判定が発火しない」は事実だが、順序反転の根拠にはならない。

追加確認結果:

- 上限超過・解決不能は ERROR または edge 不在へ倒れ、fail-closed。
- `DECIDER_VERSION` の v2→v1 変異は `test_decider_version_binds_cross_module_semantics_to_v2` が捕捉する。
- 静的評価可能な `.replace()` 48式は no-op 0。
- single-process 系負例の削除は新述語への移行自体では純減ではない。ただし新 allocation 正例が未束縛 call を正当化しており、A-01 により検出力が成立していない。
- pytest は実行していない。

must-fix: A-01, A-02, A-03, A-04

NO-GO