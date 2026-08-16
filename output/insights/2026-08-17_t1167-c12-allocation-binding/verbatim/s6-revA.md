[severity: must-fix] [M1 変異が生存する] `required_functions` から `read_binding` を削除しても、実 HEAD tripwire は両 call 不在のため、negative control は `check_reservation` 不在のため従来どおり失敗し、全新設検査を通過する。成果物影響: env/guard が通る「`check_reservation` だけ」の木で C12 report が `UNSATISFIED/allocation-enforcement-consumer-absent` から `EVIDENCE_UNDEFINED/completion-proof-not-machine-checkable` へ前進し report digest が変わる（certified 選択は false のまま） [根拠 orchestrator/campaign/s8c_preregistration_evidence.py:568, orchestrator/tests/test_s8c_preregistration_predicates.py:504, /work/1/SFC/tanab/dev-wave-jobs/wave-t1167-c12-allocation-binding/s4-ruling.md:143] [提案] baseline から `read_binding` call だけを exact-count 付きで除く独立負例を追加し、M1 を単一理由で kill する。

[severity: must-fix] [M6 正例が未実装] 実 HEAD helper テストは現在の未配線結果だけを固定し、通過側は synthetic `TOKEN_ONLY_C12` supervisor しか検査していないため、裁定が要求した「実 HEAD の production tree に両 call を追加して過剰拒否しない」反証になっていない。成果物影響: 実配線後も C12 report が誤って `UNSATISFIED` に残る回帰を見逃し、ActivationReport の status/reason/digest と gap ledger が期待する `EVIDENCE_UNDEFINED` へ更新されない（certified 選択は false のまま） [根拠 orchestrator/tests/test_s8c_preregistration_predicates.py:147, orchestrator/tests/test_s8c_preregistration_predicates.py:445, /work/1/SFC/tanab/dev-wave-jobs/wave-t1167-c12-allocation-binding/s4-ruling.md:148] [提案] 実 HEAD supervisor bytes の `run_trial` へ両 call を一意 anchor で加えた overlay を作り、実 `reservation.py` blob とともに helper が `None` を返す正例を追加する。

## 総括

最大のリスクは、事前登録済み M1 が静的に生存し、allocation 診断集合を密かに広げられる点である。  
C12 に `SATISFIED` 経路は見つからず、certified 受理集合は現状広がらない。  
gap ledger は C12 行だけが変更され、g4 の hash・世代連鎖は静的に整合していた。消える保証の注記と版 literal 更新にも追加所見はない。  
pytest は指定どおり実走しておらず、緑は主張しない。