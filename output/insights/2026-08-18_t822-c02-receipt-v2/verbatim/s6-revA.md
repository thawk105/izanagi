### 所見 1

- **主張**: 理由 gate を常時許可へ変える協調変異が負の対照をすべて通り、descriptor のない partial receipt から `c02-arm-binding-unproven` を落として受理集合を広げられる。
- **根拠**: v2 parse は t468 理由だけを必須とする (`orchestrator/campaign/s8c_acceptance_receipt.py:332`)。最終防壁は `_arm_execution_authorizes_reason_drop` の返値だけに依存する (`orchestrator/campaign/s8c_acceptance_receipt.py:714`, `orchestrator/campaign/s8c_acceptance_receipt.py:868`)。しかし負の対照は同関数を `False` へ monkeypatch するため (`orchestrator/tests/test_s8c_acceptance_receipt_v2.py:242`)、実装を `return True` へ変えても変異を覆い隠す。partial test は producer が理由を付けることしか確認せず、理由を除いた partial bytes の full verify を行わない (`orchestrator/tests/test_trial_registry.py:1520`)。これは条件式から静的に構成した経路である。
- **成果物影響**: この防壁の回帰を見逃すと、descriptor proof のない partial receipt が t468 理由だけで verified になり、受領証の受理集合と理由集合が不正に広がる。
- **GO / NO-GO**: **NO-GO**

### 所見 2

- **主張**: 五つの負の対照のうち pairwise 衝突と descriptor 乖離は後段にも拒否理由を残しており、単一理由性を満たさない。
- **根拠**: pairwise 対照は receipt の digest と binding だけを変え、report と journal を整合させず parse だけを呼ぶ (`orchestrator/tests/test_s8c_acceptance_receipt_v2.py:208`)。pairwise 検査を除いて full verifier を通すと descriptor 再導出が拒否する (`orchestrator/campaign/s8c_acceptance_receipt.py:677`)。descriptor 乖離対照も receipt の content digest だけを変える (`orchestrator/tests/test_s8c_acceptance_receipt_v2.py:227`)ため、再導出を除いても report exact 一致 (`orchestrator/campaign/s8c_acceptance_receipt.py:687`) と binding digest 再計算 (`orchestrator/campaign/s8c_acceptance_receipt.py:692`) が拒否する。従って赤は受理集合の変化でなく、最初に出る診断文字列への依存である。
- **成果物影響**: このまま KILLED と記録すると、pairwise または descriptor gate が消えても full receipt の受理集合が変わらない変異を、その gate 固有の検出力として台帳へ誤記する。
- **GO / NO-GO**: **NO-GO**

### 所見 3

- **主張**: C02 evaluator は実効データフローでなく live に見える名前と文字列を数えるため、衝突する namespace を生成しながら `completion-proof-not-machine-checkable` へ到達できる。
- **根拠**: `_live_called_names` は call target の束縛先を解決せず名前だけを収集する (`orchestrator/campaign/s8c_preregistration_evidence.py:312`)。namespace 検査も arm と digest を含む任意の f-string が存在すればよく、その値が return や proposal path に流れることを要求しない (`orchestrator/campaign/s8c_preregistration_evidence.py:1524`)。従って未使用の `f"arm-{arm}.exec-{digest}"` を評価してから共有文字列を返す実装は通る。また `_live_nodes` は同一 block の直接 `return` しか後続を打ち切らず (`orchestrator/campaign/s8c_preregistration_evidence.py:556`)、`if True: return` 後の call も数える。C02 のテスト形は `not-called`、`if False`、nested のみである (`orchestrator/tests/test_s8c_preregistration_predicates.py:1260`)。
- **成果物影響**: proposal path が arm 間で衝突する source でも C02 レポートが `arm-binding-consumer-unreachable` を失い、証拠契約が認める source 受理集合を広げる。
- **GO / NO-GO**: **NO-GO**

### 所見 4

- **主張**: 契約名の実在メタ検査は各 chain の先頭しか検査せず、先頭以外の誤名や追加された不正 chain を黙って skip できる。
- **根拠**: helper は `chain.split(" -> ", 1)[0]` だけを取り (`orchestrator/tests/test_s8c_preregistration_invariant.py:181`)、その root が identifier かつ条件を満たす場合だけ checked 集合へ入れる (`orchestrator/tests/test_s8c_preregistration_invariant.py:184`)。C02 契約が名指す `resolve_arm_input`、`_expected_registered_arm_execution_record`、`_invocation_namespace` などの後続名 (`orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:60`, `orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:81`) は exact 21 tuple に含まれない。既存 chain の後続名だけを誤名へ変える、または不正 chain を追加しても checked 集合と missing 集合は不変である。
- **成果物影響**: 実在しない関数を名指す契約 bytes を凍結世代と proof 参照へ取り込んでもメタ検査が緑になり、契約受理集合が黙って広がる。
- **GO / NO-GO**: **NO-GO**

### 所見 5

- **主張**: 凍結 golden の逆射影は `arm_execution.input_schema_version` を期待値で検証せず消費している。
- **根拠**: receipt の `arm_execution` は key 集合と report／run-start との自己一致だけを確認して pop される (`orchestrator/tests/test_reflux_originless_compatibility.py:661`)。続く report と run-start の pop も key 集合しか確認せず (`orchestrator/tests/test_reflux_originless_compatibility.py:716`, `orchestrator/tests/test_reflux_originless_compatibility.py:753`)、`input_schema_version == "8b-v1"` の assert はない。三者を同じ不正値へ変えれば golden へ到達する。一方、本 verifier は `"8b-v1"` を要求している (`orchestrator/campaign/s8c_acceptance_receipt.py:269`)。巨大 golden literal 自体は HEAD と作業ツリーで同一 SHA-256 だった。
- **成果物影響**: input schema の協調回帰を逆射影が消去し、凍結 golden の受理集合が本 verifier より広いまま緑になる。
- **GO / NO-GO**: **NO-GO**

## 総括

**NO-GO**。

must-fix:

1. partial receipt から理由を落とした実入力で gate の fail-closed 性を検査し、常時 `True` 変異を殺す。
2. pairwise と descriptor 対照を report／journal まで協調整合させ、対象 gate 以外の拒否を除く。
3. C02 の call と namespace を実効 target・return／proposal path のデータフローへ束縛し、複合 early-return も dead と扱う。
4. 契約 chain の全関数 token と全 declared path を分類・exact pin し、skip を fail-closed にする。
5. golden 逆射影で `input_schema_version` を期待値付きで消費する。

なお、現 diff には SATISFIED を返す evaluator 経路はなく、空 allowlist 外の SATISFIED は ERROR 化され、receipt の `certifying=True` も構造的に拒否される。この静的レビューでは pytest を実走しておらず、既知の U3 由来赤は所見に含めていない。