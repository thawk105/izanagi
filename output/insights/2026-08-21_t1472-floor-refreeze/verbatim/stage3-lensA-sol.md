静的検査のみ実施しました（pytest 未実行）。主要所見は `real` 4件、`unclear` 2件、`refuted` 2件です。

### 1. §10.4 の (c) を記録して `INDETERMINATE` にする解釈

判定: **unclear (要ユーザー判断)**

`docs/phase3-8b-descriptor-design.md:508-516` は (c) を区別しつつ「採らない」とし、D510 も `docs/decisions.md:21254-21256` で主張強度ラベルの分離を要求しています。プランの `stage2-plan-output.md:51,60,72,83` は、(c) を診断情報として残す一方、正式判定を `INDETERMINATE` にしています。

これは `_Status.INDETERMINATE` が結論で優先される既存仕様 (`s8c_result_judge.py:65-68,1003-1009`) と整合し、正式な `SATISFIED` には到達しません。ただし「(c) は採らない」を「診断記録も許可しない」と読む余地は残るため、(c) の診断保存可否は裁定が必要です。

### 2. provenance 起因の `INDETERMINATE` は既存意味論と一貫するか

判定: **refuted (誤り・杞憂)**

完全 block 不備は `s8c_result_judge.py:312-367` で `_InputContractError` となり、`judge()` が `:1033-1046` で全条件を同じ `_Status.INDETERMINATE` に倒します。対比内部でも欠測・block 不一致・非有限値は `:802-853`、集約は `:887-893` で同じ enum を使います。

したがって、プラン `stage2-plan-output.md:51,84` の provenance 不備を既存 fail-closed 経路へ流す設計に、別の失敗モードが混入する問題はありません。

### 3. `_ObservationProvenance` 必須化と既存 caller

判定: **real (実在する欠陥)**

直接の production caller は `s8c_result_judge.py:456-515` と同ファイル内の `judge():1034` だけで、private `_ObservationContext` の構築元を壊す問題自体はありません。

しかし、プラン `stage2-plan-output.md:51` は provenance を必須化し、旧形式の公開 `judge()` 入力 (`s8c_result_judge.py:1012-1018`) は `_build_observation_context()` で失敗して `:1036-1046` の全条件 `INDETERMINATE` になります。これはクラッシュではないものの、既存の有効入力の受理結果を変えます。handoff の「既存 judge の受理集合を変更しない」主張 (`t1472-floor-refreeze.md:112-113`) とは両立しません。

### 4. 「時間差の閾値を新設しない」は未達か

判定: **real (実在する欠陥)**

閾値を新設しない判断自体は妥当です。§10.4 `:514-516` は日数規模の差を許容しつつ信頼性を弱める規則であり、b を自動的に `INDETERMINATE` にする要求ではありません。

ただし、プラン `stage2-plan-output.md:71-82,97,115-119` は時間差とラベルを judge の diagnostics にだけ置きます。現行 `_table_bytes()` (`s8c_result_judge.py:1340-1353`) は floor metadata と result rows しか直列化せず、`publish_result_table()` (`:1453-1462`) も diagnostics を出力しません。従って「時間差を併記する」「主張強度ラベルを別にする」が公開成果物に到達しません。現時点でそれを消費する producer/report 経路もプラン自身が未確認です (`stage2-plan-output.md:101-105`)。

### 5. 「3表への影響はない」という主張

判定: **real (実在する欠陥)**

表名・schema の構造を変えないという狭い意味では正しいです (`s8c_result_judge.py:39,1347,1453-1462`)。対象テスト `orchestrator/tests/test_s8c_result_judge.py:774-816` にも直接の SHA pin はありません。

しかし bytes への影響がないという意味では誤りです。`_table_bytes()` の `official_conclusion` は `result.conclusion` (`:1349`) を使い、official rows は各 holdout の status (`:1362-1368`) を使います。(c) はプラン自身が `INDETERMINATE` に倒すため (`stage2-plan-output.md:83`)、official table の内容 bytes は変わります。malformed provenance では selection table も `:963-998` の condition status 経由で変わります。

### 6. provenance の自己申告による規律2違反

判定: **real (実在する欠陥)**

プラン `stage2-plan-output.md:55-60` が検証するのは、時刻形式・非空文字列・ペア一致だけです。現行 attestation (`s8c_result_judge.py:429-453`) は raw value の SHA と非空 issuer しか束縛せず、環境・実装・toolchain・`relation_kind` は束縛していません。

そのため caller は、raw 値の attestation を維持したまま、実際には `recovered_gap` や過去比較の観測へ `relation_kind="continuous"` を設定できます。プラン `:81-82` は continuous/recovered_gap とも既存の判定値を維持するため、最強の主張ラベルだけを偽装できます。信頼側 producer の署名・registry・attestation への provenance binding、または未束縛 provenance の正式判定拒否が必要です。

### 7. b の identity 一致要求

判定: **unclear (要ユーザー判断)**

プラン `stage2-plan-output.md:58-59` は (b) でも environment/implementation/toolchain identity のペア一致を要求します。一方、§10.4 `:515` は測定環境が異なる場合を「信頼性が弱まるものとして扱う」としており、必ず拒否するとは書いていません。

同一 identity を必須にするなら、環境変更を伴う復旧後測定を b として記録できず、仕様が想定する「弱い主張」としての報告を過剰拒否します。これは安全側の制限ではありますが、仕様上の意図を確定する裁定が必要です。

## 総括

`INDETERMINATE` の enum と集約優先順位は既存 fail-closed 意味論に沿っており、直接の private caller 破壊もありません。  
一方、diagnostics 限定では測定近接性ラベルと時間差が公開成果物へ出ず、3表の内容 bytes も (c)・不備入力で変化します。  
最大の欠陥は provenance が raw attestation に束縛されず、caller が continuous を自己申告できることです。  
(c) の診断記録可否と、復旧後の identity 不一致を許すかはユーザー裁定が必要です。