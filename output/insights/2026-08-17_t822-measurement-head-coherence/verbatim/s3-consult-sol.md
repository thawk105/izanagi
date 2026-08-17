静的検査のみ。pytest は実行しておらず、緑とは報告しない。

### 1. 単位 A は恒真ではない

自己判定: refuted（恒真疑いを反証）

所見 / 6 report の `measurement_head` 不一致は実 producer 経路で発生可能であり、単位 A は有効である。

根拠 / `load_launch_binding` は trial 起動ごとに現在 HEAD を解決する (`trial_registry.py:1178-1188`)。その値は run-start と report に写される (`p3_autonomous_workload_trial.py:2343-2349, 3097-3103`)。HEAD 移動検査は単一 run の preflight 後だけである (`p3_autonomous_workload_trial.py:2947-2955`)。acceptance は各 head の祖先性を個別検査し、`history_checked` は重複 walk を省くだけで一致を要求しない (`trial_registry.py:2477, 2505-2512, 2590-2599`)。

構成できる赤入力 / HEAD `H0` で 3 trial を起動し、manifest と registry に触れない無関係 commit `H1` を作り、残り 3 trial を起動する。両 head は有効な祖先で registry bytes も同一なので現行 acceptance を通過しうる。

影響 / 親 P-2 と provisional P4、段 2 の単位 A 実装判断を支持する。

提案 / acceptance 側と standalone receipt parser 側の双方に完全一致検査を入れる。registry 負例は実在する祖先 commit 2 個で作り、単なる架空 SHA の schema 負例で代用しない。

### 2. 親 P-1 の caller 一般化と P-4 は不正確

自己判定: real

所見 / acceptance からの Layer-3 呼び出しが 0 件という核心は正しいが、「producer と test だけ」は誤りで、P-4「全 acceptance fixture が空 cells」も反証される。

根拠 / `verify_autonomous_trial_files` も `campaign_output_root` 指定時に Layer-3 chain を呼ぶ (`autonomous_trial_completeness.py:2401-2431`)。一方、`assert_trial_registry_acceptance` 内には呼び出しがない (`trial_registry.py:2408-2715`)。fixture は `_base_report` では空だが (`test_trial_registry.py:326-362`)、`_complete_report` が 1 cell に置換する (`test_trial_registry.py:518-593`)。originless fixture も実 producer から 1 cell を生成する (`test_reflux_originless_compatibility.py:41-64`)。

影響 / 「cells 非空条件では全テストで発火しない」という brief の根拠は使えない。`do_build`、空 cells、非空 cells を別々に扱う必要がある。

提案 / 段 4 では P-1 を「acceptance caller は 0 件」に限定し、P-4 は撤回する。

### 3. 現行コードのまま単位 B を必須化すると正式受理集合は空になる

自己判定: real

所見 / 段 2 の現状認識は正しい。正式 1-cell report は acceptance と Layer-3 chain の両方を同時に通れない。

根拠 / acceptance は cell workload を `rr80` または `rr20` に限定する (`trial_registry.py:2600-2617`)。Layer-3 chain は同じ値が producer の `WORKLOADS` に含まれることを要求する (`autonomous_trial_completeness.py:2271-2298`)。現行 `WORKLOADS` は `ycsb-a/b/c` のみである (`p3_autonomous_workload_trial.py:188-192`)。空 cells は chain の loop が 0 回で通る (`autonomous_trial_completeness.py:2225-2262`) が、段 2 案の非空検査で拒否される。

影響 / producer を変更せず acceptance だけへ B を入れると、正式 positive は構成不能である。

提案 / chain の workload・campaign identity 検査だけを抜く案は `autonomous_trial_completeness.py:2291-2342` の保証を失うため、(i) の閉鎖とは数えない。

### 4. ただし「B は実装不能」は過剰に悲観的である

自己判定: refuted

所見 / 正式 workload を production profile として実装する経路は存在する。ただし段 2 の「`WORKLOADS` に 2 件追加」だけでは、都合のよい偽 formal positive になる。

根拠 / テストは `rr80/rr20` を `WORKLOADS` に追加すると、実 producer の `_prepare_campaign_identity` で正式 campaign ID を導出できている (`test_p3_autonomous_workload_trial.py:5197-5225`)。CLI parser も既に holdout 名を許容する (`p3_autonomous_workload_trial.py:3298-3309`)。

一方、正式 freeze は両 holdout を 1,000,000 records / 48 threads とする (`output/s8b-freeze/holdout_freeze.json:40-48, 307-315`)。producer の campaign、perf、descriptor の 3 sink はすべて 100,000 / 4 を固定している (`p3_autonomous_workload_trial.py:637-695`)。C01 evaluator も 1,000,000 / 48 と ratified freeze 消費を要求し (`s8c_preregistration_evidence.py:417-434`)、現行 snapshot は `workload-projection-mismatch` である (`test_s8c_preregistration_predicates.py:121`)。

さらに正式 3 軸値を source に直書きすると、実 repository scan の既知 hit 0 件契約を変える (`test_s8b_repo_scan_invariant.py:21-35`)。

影響 / 単純な workload 追加は producer の受理集合を広げるうえ、正式 scale と freeze を偽る。

提案 / ratified freeze から formal profile を導出し、3 sink、campaign identity、Layer-3 再導出を同じ profile に束縛する。探索 CLI の既定は別定数で `ycsb-a/b/c` のまま保つ。この scope 拡張を段 4 で採るなら B は実装可能である。

### 5. Layer-3 の提案 fixture は実 chain の証明にならない

自己判定: real

所見 / `s2-plan.md:86` が移植元に挙げる fixture は、原関数を呼んでも内部の重要検査を stub 化している。

根拠 / `test_layer3_report.py:944-1034` は `_producer_module`、environment contract、fresh Layer-3 rebuild、campaign admission をすべて monkeypatch し、fresh report を persisted report 自身として返す (`test_layer3_report.py:956-987`)。従って call-count 6 回でも、WAL 再構築や producer campaign identity を通した証拠にならない。

実際に赤になる入力 / より実体に近い `_layer3_campaign` は production campaign identity、WAL、Layer-3 builder を使う (`test_autonomous_trial_completeness.py:2168-2328`)。persisted `median_tps` を変える既存負例は real chain で拒否される (`test_autonomous_trial_completeness.py:2341-2353`)。

影響 / 提案 fixture のままでは「関数名には到達したが保証本体は発火していない」偽緑を作れる。

提案 / component 負例には `_layer3_campaign` 相当を使い、少なくとも 1 本は formal profile 対応後の `run_trial` が生成した campaign/report を acceptance へ渡す。fresh rebuild と admission verifier は差し替えない。

### 6. 単位 B の変異帰属と既存テスト変更には弱体化がある

自己判定: real

所見 / 段 2 案で注意すべき緩和・意味変更は次の 4 系統である。

根拠 /

- `test_p6_partial_terminal_outcomes_are_reported_not_dropped` などは zero-cell provider failure を positive としている (`test_trial_registry.py:596-624, 1093-1126`)。全てを one-cell build fixture に替えると、status の期待値は同じでも旧入力クラスの回帰検査を消す。
- originless compatibility は実 producer の no-build bundleを正式 acceptance へ通す (`test_reflux_originless_compatibility.py:31-72`)。build fixture への置換または acceptance 呼び出し削除は契約変更である。
- `rr80/rr20` の追加は `run_trial` の unknown-workload 拒否集合を広げる (`p3_autonomous_workload_trial.py:2983-2985`)。
- C09 snapshot を `UNSATISFIED` から `EVIDENCE_UNDEFINED` へ変える案 (`s2-plan.md:214-221`) は `SATISFIED` ではないが、missing consumer の期待を弱める変更である。

また、明示 `do_build is True` guard は発火入力を持つが、独立の受理集合変化にはなりにくい。既存 completeness は no-build cell に exact `not-applicable` decision を要求し (`autonomous_trial_completeness.py:1992-2006`)、その形は後続 Layer-3 admission 検査を通らない (`autonomous_trial_completeness.py:2170-2195`)。guard を外しても同じ bundle は後段で拒否される。

影響 / fixture の意味変更を「期待値は反転していない」とだけ扱うと、規律 2 の監視範囲を狭める。no-build guard の mutation は accepted/rejected 集合ではなく診断 gate の順序だけを pin する可能性がある。

提案 / zero-cell partial と originless no-build の旧 positive をどう扱うかは段 4 の明示裁定にする。変更するならテスト名・契約も変更し、fixture 育成に偽装しない。B の mutation は empty-cell bypass と persisted-WAL corruption を主たる独立 kill にする。

### 7. 単位 C を閉じる最小の非恒真検査は現行 artifact から構成できない

自己判定: real

所見 / 「arm field が一つもない」という字面だけなら `enforcement_arm` があるため不正確だが、acceptance に使える arm 実走証拠はない。段 2 の C 非実装判断を支持する。

根拠 / `enforcement_arm` は caller が渡す文字列 (`p3_autonomous_workload_trial.py:330-340`) で、formal consumer の全実行検査が終わった後に receipt へ記録されるだけである (`reflux_formal_consumer.py:950-1003`)。validator は非空文字列しか要求しない (`reflux_formal_consumer.py:884-917`)。

`_campaign_for` は arm を受けず、identity は `trial_id` と workload から作る (`p3_autonomous_workload_trial.py:637-668`)。proposal path は workload と generation のみ (`p3_autonomous_workload_trial.py:2741-2753`)。planner、coder、auditor、critic invocation ID にも arm がない (`p3_autonomous_workload_trial.py:1963-1969, 2613-2617, 2664-2674, 2721-2731`)。

構成できるすり抜け入力 / manifest 内の同一 holdout の `on` と `off` ラベルだけを交換し、manifest hash、registry、launch admission、receipt の宣言コピーを再生成する。trial_id、campaign_id、proposal、invocation、実行 descriptor は不変である。manifest は trial_id と arm の語彙的対応を要求しない (`trial_registry.py:444-482`)。

影響 / campaign ID の一意性は既に検査されるが、trial_id 由来の一意性であり arm の因果的実走証明ではない。`enforcement_arm` 照合も宣言値の往復になる。

提案 / arm が選ぶ凍結済み入力から sealed execution digest を導出し、descriptor、campaign identity、proposal bytes/path、全 invocation、run-start、terminal report の各 sinkで同じ digest を消費させる。それ以前は C を閉じたと呼ばない。

### 8. standalone receipt verifier は B/C を迂回できる

自己判定: real

所見 / acceptance 層だけに Layer-3 と arm 検査を追加しても、手書き tracked receipt が同じ保証を再導入できない。

根拠 / receipt verifier は report と journal を opaque bytes として hash 照合するだけで、report 内容、Layer-3、arm 実走を検証しない (`s8c_acceptance_receipt.py:570-630`)。既存 positive test は report を単なる `report-N\n`、`measurement_head` を実在しない `"1"*40` として receipt を commit し、それでも verifier を通す (`test_s8c_acceptance_receipt.py:62-120, 161-169`)。

影響 / 単位 A の receipt 内 head 一致検査は有効だが、B/C を report hash の内側へ置くだけでは「acceptance が発行した receipt」であることを standalone verifier は証明しない。

提案 / receipt verifier が referenced report の semantic proofを再検証するか、acceptance issuer の検証可能な sealed proofを receipt に加える。corrupt Layer-3 と foreign arm bundle を含む手書き tracked receipt の負例が必要である。

### 9. C09/C02 証拠契約は実装閉鎖を表現できない

自己判定: real

所見 / 段 2 の実名修正だけでは証拠契約層は閉じない。

根拠 / C09 は存在しない `accept_trial` を探索する (`s8c_preregistration_evidence.py:459-470`)。さらに direct call 名と `"no-build"`、`"certifying"` の文字列だけを見るため、全 report への必須到達を証明しない。token-only fixture でも到達後は `EVIDENCE_UNDEFINED` になる (`test_s8c_preregistration_predicates.py:387-401, 650-674`)。contract 自身は「static reachability で十分」と記す (`s8c_preregistration_evidence_contract.v1.json:339-368`) が、実装は `SATISFIED` を返せず、全 satisfiable 集合も空である (`s8c_preregistration_evidence.py:609-620`)。

C02 は `manifest.cells[*].arm`、`bind_trial_arm`、`accept_trial` など実在しない面を記し、`machine_checkable=false` である (`s8c_preregistration_evidence_contract.v1.json:45-72`)。evaluator は source に `declared-only` があるかを見るだけである (`s8c_preregistration_evidence.py:623-636`)。

影響 / C09 を `EVIDENCE_UNDEFINED` へ更新しても、B が証拠契約層で閉じたことにはならない。C02 は future arm fieldを足しても自動では追随しない。

提案 / C09 は実 entrypoint、無条件到達、全 6 report、empty/no-build policy を表す contract と負例へ更新する。C02 は producer capability が完成するまで undefined のまま保ち、完成時に実在 sinkへ全面改訂する。contract hash の更新は凍結境界として扱う。

### 10. P-6 の pin は実在するが、P3 は C 閉鎖後には自己矛盾する

自己判定: real

所見 / 現在 C が未証明なので `c02-arm-binding-unproven` を残す判断は正しい。しかし将来 C を本当に閉じた後も残すなら、receipt 自身が「arm binding は未証明」と宣言し続ける。

根拠 / v1 verifier は `c02-arm-binding-unproven` と `t468-approval-authority-absent` を必須にする (`s8c_acceptance_receipt.py:23-28, 225-231`)。さらに `certifying=false` を構造的に固定する (`s8c_acceptance_receipt.py:275-280`)。originless golden も 2 語を pin する (`test_reflux_originless_compatibility.py:234`)。

影響 / pin の存在は P-6 を支持するが、pin 更新を避けることは C の閉鎖根拠にならない。C を閉じて理由語だけ残すと、実装と receipt の主張が不一致になる。

提案 / C を閉じる wave では receipt v2 を導入し、`t468-approval-authority-absent` を残して `certifying=false` を維持しつつ、C02 理由だけを外す。v1 を維持するなら C は未閉鎖と記録する。

### 11. 全層 scope は acceptance だけでは不足する

自己判定: real

所見 / 単位別に必要な層が異なる。

根拠 / A は acceptance と standalone receipt の二層で閉じられる。B は formal producer profile、acceptance、standalone receipt semantic verification、C09 contractが必要である。C は arm authority producer、campaign/proposal/invocation sink、completeness verifier、acceptance、receipt schema/verifier、C02 contractが必要である。

影響 / A だけ land して [T-822] 全体を完了扱いすると、既裁定の 3 件中 2 件を「実装したふり」にする。

提案 / 段 4 の裁定パッケージを、(1) formal profile と freeze 追随を B に含めるか、(2) originless no-build/zero-cell positive を明示的に supersede するか、(3) C の canonical arm authority と receipt v2 をどの wave で作るか、の 3 点に分ける。

## 総括

- 単位 A は実 producer で mixed head を構成でき、直ちに実装可能である。
- 単位 B は現行のままでは受理集合が空になるが、production formal profile を作る回避経路は存在する。
- 段 2 推奨の Layer-3 fixture は重要な内部検査を stub 化しており、発火証拠に使えない。
- 単位 C は現在の artifact から非恒真な最小検査を構成できず、producer authority が先に必要である。
- receipt verifier と C02/C09 契約を取り残したままでは、B/C を閉じたとは呼べない。
- よって A は GO、現行案の B/C と [T-822] 完了宣言は NO-GO である。