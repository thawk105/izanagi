結論は、**項目6はこの wave では実装しない**です。`s8c_result_judge.py` と canonical な attempt registry の存在は確認できますが、provenance を生成して judge へ渡す production artifact path は存在しません。したがって、現時点の変更は実質的にテスト専用になります。

### 1. P1: judge / registry の所在

判定: `refuted`

`between_run_floor.py` は D510 judge ではありません。A2 の between-run noise floor 用独立 driver であり、`orchestrator/campaign/between_run_floor.py:2-12,77-117` に D510 の paired contrast・3表・attempt registry はありません。

一方、`s8c_result_judge.py:2-8` は stage 8c の sealed result judge と明記され、git 履歴も T-1352 の C07 consumer 新設を示します。paired contrast は `s8c_result_judge.py:763-893`、3表は `:896-1000,1437-1462` にあります。attempt registry も `trial_registry.py:2672-2726,2778-2837,2984-3005` にあり、D510 用の canonical registry です。

別名の実装も確認しましたが、以下は D510 の代替ではありません。

- `s8b_oracle_judge.py:27-38,452-464`: 旧8b oracle 判定
- `s8b_verdict.py:611-615`: 旧8b combined verdict
- `s8b_holdout_admission.py:1806-1835,3796-3825`: floor admission ticket ledger

したがって、「別の D510 judge / attempt registry を親が見落とした」という攻撃は成立しません。

ただし、handoff の `:30-35` が `s8c_result_judge.py` を「777行」と記しているのに対し、現行ファイルは1512行です。実装の存在自体は正しいものの、親 brief の行番号・規模情報は更新漏れです。

### 2. 実運用の judge 呼出し経路

判定: `real`

`grep -rn "s8c_result_judge\." orchestrator/` と定義・import の静的確認では、実行時の production caller は見つからず、参照は主にテスト・契約・静的 evaluator に限られます。`orchestrator/tests/test_s8c_result_judge.py:22,183,301,718-743` には直接呼出しがありますが、production code から `judge()` を呼ぶ経路は確認できません。

また、親 brief が示す `729-777` 付近の CLI `main()` は現行ソースにはありません。同じ範囲は `_sample_covariance`、相関係数、`_evaluate_contrast` の内部処理です。`judge()` 本体は `s8c_result_judge.py:1012-1070` にありますが、CLI entrypoint ではありません。

C07 側の `s8c_preregistration_evidence.py:2776-2803` も、`verify_floor_bytes -> judge -> publish_result_table` という構造を AST で検査する静的 evaluator です。同箇所の docstring 自身が、動的 dispatch と実バイト対応は静的には証明できないと述べています。

### 3. producer は「無い」のではなく、judge 接続が無い

判定: `refuted`（字義どおりの「producerなし」について）

`p3_autonomous_workload_trial.py:2-13` は bounded workload trial の実 producer であり、`p3_autonomous_workload_trial.py:3228-3339,4416-4448` で terminal report、attempt journal、measurement head、arm binding digest、observation digest などを出力します。

したがって、stage2 plan `:103-105` の「実際に provenance を生成する8c producerも確認できない」という表現は広すぎます。

ただし、次の限定付き主張は成立します。

判定: `real`

現行 producer は、stage2 plan が提案する `measured_at`、環境・実装・toolchain identity、relation label を `_ObservationContext` へ渡しておらず、`s8c_result_judge.judge()` も呼びません。`p3_autonomous_workload_trial.py:1732-1737` には schedule authority が無ければ推測せず停止する経路もあります。

従って、**「8c producer は存在する」ことと「D510 C07 judge が発火できる artifact path が存在する」ことは別**です。後者はありません。

### 4. DW-G04 と「実装する」案の整合性

判定: `real`

現行 `_ObservationContext` は `s8c_result_judge.py:150-155` の medians、replicate values、blocks だけです。`_build_observation_context()` も `:456-515` で raw observation、attestation、coverage を検証するだけで、提案された provenance を供給する既存 artifact を読みません。

さらに、stage2 plan は `:105` で producer 不在を認めながら、`:123` では judge とテストだけを実装するよう推奨しています。この二つは DW-G04 の発火 gate と整合しません。

provenance を必須化すれば、直接 `judge()` を呼ぶ古い入力は `s8c_result_judge.py:1031-1047` の fail-closed 経路で `INDETERMINATE` になります。これはテストや将来の直接 caller には影響しますが、現状 production caller が無いため、実運用の成果物・受理集合は変わりません。

この変更は、producer と versioned artifact schema が先に存在しない限り、DW-G04 により設計メモに留めるべきです。

### 5. 項目7を理由に項目6を今実装する必要があるか

判定: `real`  
推奨: **実装しない**

D510 自身が `docs/decisions.md:21254-21260` で、今回の発効は仕様のみであり、judge・evidence contract・registry follow-up 前の正式測定を禁止しています。`docs/phase3-8b-descriptor-design.md:545-555` も同じ epoch 境界を要求しています。

また、`s8c_preregistration_evidence.py:3075,3185-3193` の `SATISFIABLE_CONDITION_IDS` 空集合により、readiness の正式な受理集合は fail-closed です。現状の p3 report も `scientific_claim:false`（`p3_autonomous_workload_trial.py:3228-3250`）です。

ただし、親 brief の「正式系列の起動自体が不可能」という表現は広すぎます。

判定: `unclear`

`p3_autonomous_workload_trial.py:1123-1172` と `trial_registry.py:3926-3972` には、`certifying=False` の registered formal non-certifying admission mode があります。これは正式な性能主張を受理する経路ではありませんが、空の satisfiable set がすべての launch mode を止めるわけではありません。

したがって正確には、**certifying な正式受理は閉じているが、non-certifying pilot の実行まで全面禁止しているわけではない**です。それでも現行 pilot は C07 judge に接続されていないため、項目6を今追加しても実害防止ではなく、将来 producer に備えた予防的契約強化に留まります。規律5・DW-G02・DW-G04を合わせると、今回は設計メモへ戻すのが妥当です。

再開条件は、producer が以下を含む versioned artifact を生成し、実際に judge へ渡すことです。

- 測定時刻、環境・実装・toolchain identity
- continuous / recovered gap / intentional past comparison
- attempt registry slot、measurement commit、C02 digest への参照
- judge 呼出しと正式 acceptance consumer

### 6. C02 との将来衝突

#### 6.1 直接的な編集衝突

判定: `refuted`

C02 の現在の所有範囲は `test_s8c_preregistration_invariant.py:54-68` に列挙されており、主に `p3_autonomous_workload_trial.py` と `trial_registry.py` の invocation namespace、arm binding、digest、acceptance です。`s8c_result_judge.py:763-893` は数値的な paired contrast と block 完全性しか見ておらず、role payload digest や arm binding digest を読んでいません。

従って、C02 の実装が必ず `_evaluate_contrast()` を直接変更するとは言えません。現在の参照構造から見れば、直接の source overlap は低いです。

#### 6.2 将来の入力契約統合

判定: `unclear`

ただし、stage2 plan `:23-60` の `_ObservationProvenance` は、C02 の registry slot・content digest・arm binding digest と結び付いていません。現行 `judge()` の入力契約も `s8c_result_judge.py:1012-1017` の manifest、observations、prediction、params だけです。

将来 C02 producer が正式観測を judge に接続する場合、次のいずれかが必要になります。

- judge 入力契約を拡張する
- C02 artifact から judge 用 observation artifact へ変換する adapter を置く
- provenance schema に registry/digest の参照を追加する

この所有関係と互換性方針を決めずに、今 private な `_ObservationContext` だけを変更すると、将来の C02 成果物との統合時に再変更が発生します。親 brief の「現在の diff 衝突0件」は read-only では検証不能であり、仮に現在の衝突が0でも、将来統合の安全性までは示しません。

### 7. 分割候補1・2を同一実装単位にする必要性

#### 7.1 「検証だけでは実効的な挙動がない」は不正確

判定: `real`

stage2 plan `:109-113` は provenance 型検証だけでは実効的な挙動がないとしています。しかし、`_build_observation_context()` の検証失敗は `judge()` の `:1031-1047` で全条件を `INDETERMINATE` にするため、検証だけでも直接 caller の受理集合を狭める実効性があります。

したがって、技術的には次の第0単位を独立させられます。

1. `_ObservationProvenance` の型・必須性・fail-closed 検証
2. ペア近接性ラベルの導出、診断、主張強度への接続

#### 7.2 今すぐ第0単位を作るべきか

判定: `unclear`

producer が存在しない現状では、第0単位も production では発火せず、テスト上の契約強化に留まります。よって、今回の推奨は1・2を同一にすることでも、検証だけを先行実装することでもなく、**両方を延期すること**です。

将来 producer と artifact schema が確定した時点では、D603 の narrow 分割に沿って検証を第0単位にする余地があります。逆に producer 接続まで同一 wave で成立するなら、1・2を一つの vertical slice にするのは合理的ですが、「同一実装単位が唯一の最小解」という段2の根拠にはなっていません。

## 総括

P1の judge・canonical registry の所在認識は概ね正しく、別の D510 判定器・registry の見落としはありません。  
ただし、現行8c producerから judge へ至る実運用経路はなく、DW-G04の発火条件は未成立です。  
項目6はこの wave では実装せず、producer・artifact schema・C02 digest連携を先に設計するべきです。  
C02との直接衝突は低い一方、将来の入力契約と所有範囲は未定義で、分割1・2を同一化する必然性もありません。