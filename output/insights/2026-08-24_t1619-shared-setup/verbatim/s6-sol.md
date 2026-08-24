## 総括

must-fix は 0 件で、land を止める所見はない。
`exactly_matches_head` の左右は別 root・別 commit を評価しており、恒真化していない。
5 件の assert は現在の決定的な評価器に対して同じ集合を観測する。ただし再評価による非決定性の検出機会は減る。
変異の可視性表は正しいが、m04 の置換先 status は明示すべきである。

## 5 件の同値性

| test | 判定 |
|---|---|
| `snapshot_has_zero_satisfied_predicates` | status、evidence 非空、SHA 長の assert は不変。入力だけが fixture の同じ評価結果になった。`implementation.diff:64-75`、`orchestrator/tests/test_s8c_preregistration_predicates.py:189-197` |
| `snapshot_exactly_matches_head` | 左辺は一時 repo の commit を fixture で評価した値、右辺は実 repo の `"HEAD"` を test 内で新規評価する。退化なし。`orchestrator/tests/test_s8c_preregistration_predicates.py:138-177,200-206` |
| `gap_reason_snapshot` | C01-C12 の status/reason 辞書は変更前後で同じ評価結果から作られる。`implementation.diff:90-104`、`orchestrator/tests/test_s8c_preregistration_predicates.py:209-251` |
| `c12_registry_reports_unwired` | 同じ全結果から C12 を選ぶため観測集合は同じ。`implementation.diff:109-120`、`orchestrator/tests/test_s8c_preregistration_predicates.py:254-262` |
| `c12_allocation_binding_helper_reports_unwired` | 変更前の `_result` も全件評価後に C12 を選択しており、共有 tuple からの選択と値は同じ。`orchestrator/tests/test_s8c_preregistration_predicates.py:133-135,281-289` |

fixture は引き続き module scope である。5 test は共有値を変更せず、評価器も呼出しごとに cache と結果 list を新規生成するため、新しい順序依存はない。`orchestrator/tests/test_s8c_preregistration_predicates.py:170-177`、`orchestrator/campaign/s8c_preregistration_evidence.py:3135-3149,3209-3210`

fixture の評価例外が5件へ波及しても、同一 root/commit の同じ処理なので原因の識別情報は失われない。通常の評価例外は status/reason へ閉じられる。`orchestrator/campaign/s8c_preregistration_evidence.py:3163-3208`

独立 oracle は収集 report から group node を作り、別 literal と完全一致を比較する。decorator を1件消すとその node だけ実集合から消え、missing 差分で赤くなるため恒真ではない。`implementation.diff:13-19,24-38`。ただし射影には `_collect_xdist_group_report` と `_assert_xdist_group_contract` の未変更本体が含まれず、その内部までは再検査できなかった。

可視性表もコードと一致する。評価器は working tree から import される一方、repository 内容は resolved commit を `cat-file` で読む。契約だけは snapshot へ working-tree bytes が再注入される。`orchestrator/tests/test_s8c_preregistration_predicates.py:21-24,151-166`、`orchestrator/campaign/s8c_preregistration_evidence.py:682-705,3111-3126`

[severity: should-fix] [攻撃シナリオ] m04 の「別の status」に `SATISFIED` を選ぶと、登録済み3 nodeに加えて zero-satisfied test も赤くなり、期待完全集合と一致しない。 [根拠 `/work/1/SFC/tanab/dev-wave-jobs/t1619-shared-setup/s4-addendum-mutation.md:44`; `orchestrator/tests/test_s8c_preregistration_predicates.py:194`; `orchestrator/campaign/s8c_preregistration_evidence.py:2381-2384`] [提案] m04 を `EVIDENCE_UNDEFINED` から `UNSATISFIED` への置換と明記する。

[severity: nit] [攻撃シナリオ] 評価器が呼出し回数依存で、最初の数回だけ正しい場合、変更前の各 test による追加評価では検出できても、共有後は検出できない可能性がある。現在の評価器は呼出しごとに状態を新規生成するため、現実装での値の差はない。 [根拠 `implementation.diff:69-71,99-101,115-117,131-134`; `orchestrator/campaign/s8c_preregistration_evidence.py:3135-3149,3209-3210`] [提案] 意味保存の範囲を決定的評価器に限定したことを記録する。非決定性も契約対象なら、安い専用 test で同一 commit の複数評価を比較する。

変異の具体的な安全な注入点は、m01 が共通 contract ref の SHA 生成 `orchestrator/campaign/s8c_preregistration_evidence.py:3124-3126`、m03 が C11 終端 reason `:2305-2308`、m04/m05 が C12 終端 status/reason `:2381-2384` である。m02 は working-tree 契約 bytes の snapshot 注入 `orchestrator/tests/test_s8c_preregistration_predicates.py:166` を利用できる。