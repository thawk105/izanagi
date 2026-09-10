## 総括

判定は hold。静的レビューのみ実施し、pytest・build は未実行。最大の問題は、T-1310 前提、受入経路、共有 reflux consumer、単位 C の所有範囲が未接続な点である。

### 所見1 [real] T-1310 の先行必須範囲が過大

H1/H2 の完全値は `docs/phase3-8b-descriptor-design.md:115-116` に既にあり、off の canonical bytes と hash も `s2-plan.md:29-33` で確定できる。一方、実装側は `p3_autonomous_workload_trial.py:188-192,687-695` が rr50/95/100 と 100k/4 のままで、`trial_registry.py:51-54` も rratio しか持たない。`p3_autonomous_workload_trial.py:752-758` から registry へは到達するが、成功した実走は `:2983-2985` の unknown workload で止まる。

T-1310 無しで閉じられるのは canonicalizer、off artifact、厳密 verifier、未解決時の fail-closed gate まで。on/swapped の成功 resolver、p3 の六 sink、正例 acceptance は閉じられない。

成果物影響: off artifact は成立するが、正式 six-cell の campaign/report/invocation 成果物はまだ生成不能。

### 所見2 [real] 共有 registry admission が既存 fixture を一括で壊す

計画は `s2-plan.md:75-93` で `admit_registered_launch` 内から `bind_trial_arm` を呼ぶ。これは p3 専用ではなく、`test_trial_registry.py:130-151` の `_registered_repo`、同 `:1382-1392`、`:1597,1627,1675,2008,2044`、`test_reflux_origin_binding.py:332` も同じ API を使う。これらの一時 repository は arm-input artifact を持たず、resolver callback も `s2-plan.md:77` で禁止されている。p3 fixture の `WORKLOADS` monkeypatch (`test_p3_autonomous_workload_trial.py:5207-5229`) だけでは足りない。

成果物影響: registry/reflux の既存テストと fixture repository 全体に、正式 profile と arm artifact の投入が必要になる。

### 所見3 [real] acceptance では新 assert が発火しない

計画 `s2-plan.md:132` は historical `measurement_head` から arm input を再解決すると述べるが、現行 acceptance は `trial_registry.py:2295-2362` の `_expected_registered_launch_admission_record` を使い、` :2545-2556` で比較する。この builder は宣言された `trial.arm` だけを記録し、`bind_trial_arm`、sealed digest、descriptor bytes を呼ばない。新設予定の `assert_campaign_binding` (`trial_registry.py:1894-1903`) も acceptance 経路から呼ばれていない。

成果物影響: 実装が builder を更新しなければ全 acceptance が余分な arm_execution で赤になり、単純に report 値を写せば label-only 攻撃を受ける。

### 所見4 [real] run-start v4 と role payload v3 の境界が未定義

計画は `s2-plan.md:106` で run-start だけを v4 にすると記す。しかし現行の `p3_autonomous_workload_trial.py:121-122` の `SCHEMA_VERSION` は role payload (`:1594`) と run-start (`:3080`) の双方に使われ、completeness は `autonomous_trial_completeness.py:1135-1138` で producer の単一 version と比較する。全体を v4 にすると `test_p3_autonomous_workload_trial.py:1019-1021` など role payload の既存契約まで変わる。

成果物影響: run-start だけを v4 にする別定数・checker 更新がなければ journal の検査が成立しない。

### 所見5 [real] exact key set の拡張と所有が未接続

registered record に `arm_execution` を追加するなら、現行の 7/8 key 閉包 `trial_registry.py:95-100` と `autonomous_trial_completeness.py:78-85` は、origin binding の有無も含めて少なくとも4形へ拡張が必要である。既存の exact test は `test_autonomous_trial_completeness.py:1996-2003` にある。計画の単位 A は registry、単位 C は completeness を所有するため、`s2-plan.md:168-176` の素集合主張と衝突する。

成果物影響: registered run の launch_admission、journal、report の schema が一致せず、受入 chain が全件停止する。

### 所見6 [real] reflux の downstream hash consumer が棚卸しから漏れる

`OriginProducerInputs.enforcement_arm` を p3 側で digest に置換する計画 (`s2-plan.md:107`) は、standalone API を変えなくても実値を変える。formal receipt は `reflux_formal_consumer.py:194,368-384,893-1001` でその値を保存し、result-evidence は `reflux_result_evidence.py:80-98,249-256` で launch admission record hash を検査する。p3 の result-evidence fixture も `test_p3_autonomous_workload_trial.py:6225-6241,6531-6533`、共通 builder も `orchestrator/tests/reflux_origin_fixture_builder.py:417-418` にある。

成果物影響: formal receipt、launch admission hash、result-evidence の bytes が連鎖的に変わり、古い fixture は origin acceptance で拒否される。

### 所見7 [real] `### 7` のテスト列挙には漏れがある

設計上必然の赤は、`test_trial_registry.py:1448-1549,1826-1889` の exact launch record、`test_reflux_origin_binding.py:349-459,579` の rederivation、`test_p3_autonomous_workload_trial.py:5192-5236,5355-5377,6375-6552` の six-cell/origin fixture、`test_autonomous_trial_completeness.py:2178-2205` の current/historical golden である。originless baseline (`test_reflux_originless_compatibility.py:234-263,581-627`) は計画どおり旧 baseline を保持しつつ current epoch を追加すべきである。

実装が間違っている赤は、exploratory の exact report (`test_p3_autonomous_workload_trial.py:5559-5567`)、`"arm" not in report` (`:5417-5429`)、standalone formal receipt の exact key (`test_reflux_formal_consumer.py:671-692`)、historical pin (`test_artifact_admission.py:216-223`) を反転または緩和する場合である。

成果物影響: 現行値と historical 値を混同すると、旧 epoch の証拠を上書きするか、exploratory を正式 arm 証拠として誤認する。

### 所見8 [real] P5 の import と所有境界が実質的に素集合でない

実際の import graph は `trial_registry.py:30-33` が completeness を import し、p3 は `p3_autonomous_workload_trial.py:47,50-55` で registry と completeness の双方を import する。resolver が T-1310 adapter として p3 を import し、registry が `s8c_arm_inputs` を import すると循環する。さらに acceptance (`trial_registry.py:2408-2723`) は単位 A のファイルにありながら単位 C の責務である。

A は p3/completeness を import しない leaf resolver と registry core に限定し、acceptance とその test は A または C のどちらか一方へ移して直列化すべきである。

成果物影響: import cycle または同じ exact key/acceptance builder の競合により、単位 B/C の成果が結合できない。

### 所見9 [refuted] 凍結 bytes の直接変更は計画上ない

計画は `s2-plan.md:100-101,178` で `s8c_preregistration_evidence_contract.v1.json` と `output/s8c-preregistration/condition-freeze/` を編集対象外にし、新 artifact を `arm-inputs/` に置く。契約の arm field paths と C02 の entrypoint は `s8c_preregistration_evidence_contract.v1.json:46-70` に既存し、condition-freeze の hash ledger は `condition-freeze.v1.g5.json:1` に pin されている。

成果物影響: 計画どおりなら frozen bytes の bump は不要で、arm-inputs は別 artifact 世代として扱える。

### 所見10 [real] ただし frozen semantics と hash pin の扱いが未裁定

`docs/phase3-8c-preregistration.md:247-259` は、受理集合・拒否理由・射影入力の意味を変える場合に世代記録と decider version を要求する。run-start v4、registered record の新字段、C01 の到達結果変更を frozen projection の意味変更と扱うか、計画は明記していない。また `test_p3_autonomous_workload_trial.py:51-76`、`test_autonomous_trial_completeness.py:2178-2205`、`test_reflux_originless_compatibility.py:234-263` は識別子と hash を固定している。

成果物影響: semantics change と判定された場合、本 wave 外の condition-freeze 世代追加が必要になり、現計画のままでは完了不能になる。

### 所見11 [refuted] invocation ID の現行制約には収まる

provider の実制約は `claude_projected_provider.py:42,253-255` の lowercase `[a-z0-9._-]`、最大128文字である。計画の `arm-{arm}.exec-{64hex}.{workload}.g{n}.{role}` は、固定 H1/H2、最大 generation 10、swapped、auditor でも約98文字で、文字種も適合する。

ただし workload 名の長さ自体は `autonomous_trial_completeness.py:790-792` で制限されないため、将来 profile を増やすなら helper 内で128文字を明示検査すべきである。

成果物影響: 現行 H1/H2 では invocation、raw、payload filename の衝突は発生しない。

### 所見12 [refuted] constructor 1件という棚卸しは正しいが、削除影響は1行ではない

`OriginProducerInputs` の実 constructor は `test_p3_autonomous_workload_trial.py:6490` の1件だけで、計画 `s2-plan.md:145` の件数主張は正しい。一方、dataclass 自体は `p3_autonomous_workload_trial.py:330-340`、型検査は `:851-857`、formal consumer への引渡しは `:962`、public boundary は `:2869,2927-2929,3250`、`dataclasses.replace` は test `:6547` に残る。

成果物影響: constructor だけを削っても runtime token 検査や receipt input が不整合になり、origin path が壊れる。

### 所見13 [real] 1 wave の規模を超えている

変更対象は主要実装だけで p3 3436行、registry 2786行、completeness 2457行、関連 test だけで約2万行に及ぶ。計画は `s2-plan.md:9-132` で artifact、registry、reflux、p3 六 sink、proposal再読込、acceptance、mutation を一括している。

先に pure off canonicalizer/verifier と fail-closed registry API、次に T-1310 profile と p3 six sink、最後に completeness/acceptance と historical baseline に分けるべきである。

成果物影響: 現計画の一波では positive execution chain と acceptance のどちらかが未検証のまま残る可能性が高い。