## 所見

- **real — 失敗分類の遅さは、R-5の「未発効条件」に明記すべき。**  
  `orchestrator/campaign/s8b_floor_campaign.py:4773-4840,4900-4910` は測定・性能出力処理後に理由を決め、`valid=False` を retry の契機にする。`docs/phase3-8b-descriptor-design.md:531-537` の出力前分類を満たしていないため、「epoch gateの残件」だけでなく、8b実装・受入検証完了まで正式測定不可とR-5本文で明示する必要がある。

- **refuted — novelty search が統計的独立性を保証する、という含意は誤り。**  
  `orchestrator/campaign/s8b_holdout_freeze.py:994-1001,1026-1027,1107-1109` が検査するのはリポジトリ上の既知化・conjunction hitだけで、再測定サンプルの独立性は検査しない。`docs/phase3-8b-descriptor-design.md:508-516` も事故復旧後の測定を時間差のある弱い比較として扱っている。

- **real — §10.5の「同じ構成・同じ反復の次slot」だけでは、再抽選バイアスを閉じていない。**  
  `docs/phase3-8b-descriptor-design.md:524-537` は後知恵によるretry選択を抑えるが、観測後に残った部分WALをどう扱うか、どのattemptを主解析値にするか、時間差を含む推定量をどう受理するかを定めていない。`orchestrator/tests/test_s8b_floor_campaign.py:6086-6112` が反証するのは他セル性能値によるretry列の変動だけで、独立性全般ではない。

- **real — `trial_registry.py` のliteral流用不可という結論は確認できる。**  
  `orchestrator/campaign/trial_registry.py:51-77,101-114,1869-1905,2616-2630,3432-3494` は8cのschema、path、`ARMS/HOLDOUTS`、`TrialManifest`、slot tupleを固定する。一方、8bは `orchestrator/campaign/s8b_holdout_admission.py:669-687` の6要素keyと独自attempt語彙を持つため、literal流用には8c契約の変更または意味を失う擬似フィールドが必要になる。

- **unclear — 「汎用化すると8c consumerを壊す」は条件付きであり、言い切りは強い。**  
  非互換にdefault path/schemaを変える場合は、`p3_autonomous_workload_trial.py:1284-1315` の8c固定path・slot選択や、`test_p3_autonomous_workload_trial.py:6498-6538,7040-7051` を壊す具体経路がある。ただし8c既定値を保持した名前空間付きparameterizationなら破壊は必然でなく、推奨文は「非互換な共通化変更は壊しうる」と限定すべき。

- **refuted — R-5(a)と§10.5は同一設計ではない。**  
  `docs/phase3-8b-restart-runbook.md:372-377` の(a)は、観測痕跡ゼロ時にadmission keyをsaltする限定的なidentity workaroundである。`docs/phase3-8b-descriptor-design.md:520-543` は元freeze identityを保ち、全slotを事前登録し、観測後の同一構成・同一反復だけをretryする別設計である。「弱い」は全crash点を覆わないという意味に限定すべきだが、現行推奨から外す判断は妥当。

- **real — 段2 plan §6の「揃う場合だけ許す」は、将来条件であることを明示し直すべき。**  
  `stage2-plan-output.md:211-218` は未実装・未認可も記しているが、`trial_registry.py:371-379,3143-3150,3247-3253` 自身がreceiptの存在だけではOS-level read-firstを証明しないと明記する。  
  添削案:  
  > 現HEADではR-5の復帰を許可しない。以下は、8b専用registry/consumerとtrusted launcherのread-first証明が実装・受入検証・同一epochで発効した後に初めて評価する将来条件であり、receipt/root/slot/classificationの存在だけでは十分でない。発効前のrunはlegacy/exploratoryとして扱い、formal結果へ昇格しない。

## 総括

失敗分類の出力後処理は実在する未解決欠陥で、既存の8c epoch gateだけでは8bを認可できない。  
novelty searchは統計的独立性を保証せず、§10.5にも観測後crashの統計的取扱いが残る。  
8c registryのliteral流用不可と(a)の別設計性は支持するが、共通化の破壊リスクは非互換変更に限定して書くべきである。