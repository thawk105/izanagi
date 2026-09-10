## 総括

- **NO-GO。**
- completeness 単体では、全 workload が存在する `[failed, admitted]` を受理でき、failure 最終配置の防壁が破れている。
- critic 破棄と generation-accounting の状態が束縛されず、critic 不在なのに `"generation-complete"` と記録できる。
- campaign identity 不在の免除が exact fallback shape を要求せず、独立再導出を迂回できる。
- producer は段 4 裁定が禁止した failure 経路での accounting append を実装しており、再裁定なしでは land できない。
- pytest・実走は行っていない。4 ファイルの全差分・全削除行を読み、AST parse と `git diff --check` のみ確認した。

## must-fix

### 1. 全 workload 存在時に非最終 failure cell が completeness を通過する

- 主張: `_check_workload_coverage` は `len(actual) == len(requested)` なら failure 配置を検査せず return する。`assert_autonomous_trial_completeness` 側の共通検査は failure 件数と `partial` status しか見ないため、`[failed, admitted]` の混成 trial が全 workload を持つ場合は受理される。最終配置を拒否するのは後段の campaign-chain だけであり、completeness 単体 consumer には効かない。
- 根拠: `orchestrator/campaign/autonomous_trial_completeness.py:1689-1712,1988-1992,2203-2206`。新設テストも suffix が残る場合しか撃っていない: `orchestrator/tests/test_autonomous_trial_completeness.py:2570-2617`。
- **成果物への影響: completeness のレポート受理集合へ、failure の後に admitted cell が続く `partial` report が追加され、試行台帳と report の cell 順序が producer 不可能な状態でも正当と扱われる。**
- 直し方: failure index の `[len(cells) - 1]` 完全一致を `assert_autonomous_trial_completeness` の共通 artifact-admission gate で要求する。requested と actual が同長の `[failed, admitted]` を completeness 単体へ渡す拒否テストを追加する。

### 2. critic 破棄と generation-accounting の状態が一致しなくても通る

- 主張: disposition `count == 1` は最終 critic 欠落へ束縛されるが、対応する accounting event の `state` とは束縛されない。journal の状態を `"partial-generation"` から `"generation-complete"` または `"pending-pre-invoke-failure"` へ変えて hash を更新しても、現在の verifier は閉集合内として受理する。
- 根拠: critic 欠落判定は `orchestrator/campaign/autonomous_trial_completeness.py:1531-1547`、accounting state は三値の membership しか検査しない同 `:1822-1825`。producer が意図する値は `orchestrator/campaign/p3_autonomous_workload_trial.py:1819-1824`。
- **成果物への影響: report は critic を破棄したと記録する一方、試行台帳は同 generation を完了済みと記録でき、虚偽の generation 状態とその `attempt_journal_sha256` が受理される。**
- 直し方: failure disposition `count == 1` の最終 generation に対応する accounting eventへ `"partial-generation"` 完全一致を要求する。状態を `"generation-complete"` と `"pending-pre-invoke-failure"` へ変える拒否テストを追加する。

### 3. identity 不在免除が exact fallback cell に閉じていない

- 主張: campaign-chain は `campaign_id` と `campaign_root` の取得値がともに `None` なら直ちに免除する。両 key の不在、空 generations、supervisor-error、campaign metadata 不在という producer の fallback shape を要求しない。直接呼び出しでは明示的な `null` key も通る。
- 根拠: `orchestrator/campaign/autonomous_trial_completeness.py:2221-2223`。completeness の early-error metadata 緩和も余剰 campaign metadata を禁じない: 同 `:1408-1453`。正例テストは最小 shape だけで、境界を固定していない: `orchestrator/tests/test_autonomous_trial_completeness.py:2513-2541`。
- **成果物への影響: campaign identity を report から落とした failure cell が独立 admission と persisted Layer 3 の検査を受けず、成功 campaign の参照を隠した report が campaign-chain の受理集合へ入る。**
- 直し方: fallback を exact producer shape に閉じ、identity key は値が `None` ではなく key 自体が不在であることを要求する。`campaign_id=None`、`campaign_root=None`、余剰 descriptor、成功 cell から identity を除去した各変異を拒否する。

### 4. 段 4 裁定に反して failure handler が accounting event を追加している

- 主張: 裁定は failure 経路で accounting event を追加 append しないと明記するが、handler は pending critic ごとに `_append_generation_accounting` を呼ぶ。author 報告自身も解釈不一致として未解決を申告している。
- 根拠: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1175-cell-admission-report/ruling.md:80-85`、`orchestrator/campaign/p3_autonomous_workload_trial.py:1815-1824`、`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1175-cell-admission-report/author.md:71`。
- **成果物への影響: failure 後に試行台帳へ新しい `generation-accounting` が増え、event sequence、`attempt_journal_sha256`、および successful-harness admission failure のレポート受理集合が裁定済み仕様から変わる。**
- 直し方: 現裁定どおり append を除去して既に確定済み accounting の範囲だけを受理するか、successful-harness failure も対象にするなら親が受理集合と台帳意味論を再裁定してから実装・変異登録を更新する。

## nit / backlog

- 事前登録 M6「verifier 側の positive 条件だけを外す」は、`autonomous_trial_completeness.py:1990-1992` の先行する `failure requires partial` に遮蔽される等価変異である。現時点では成果物影響がないため must-fix ではないが、両層変異へ再照準する必要がある。
- 新しい failure shape テストは production の literal を参照しておらず、絶対 path、時刻、hash の焼き込みもない。
- 既存テストの削除・skip・xfail はない。変更された既存テストの「例外送出」「report 不在」期待は、裁定された挙動変更に限って反転されている。

## 反証された懸念

- identity が存在する failure cell では、persisted `layer3_report.json` の不在確認と `require_admitted_campaign(...CERTIFIED_ACCEPTANCE)` の `ArtifactAdmissionError` の両方を検査している。片方だけでは免除されない。
- `require_admitted_campaign` 周辺で捕捉するのは `ArtifactAdmissionError` だけであり、他例外を failure 免除へ倒す経路はない。
- 単純に admitted cell の decision だけを failure shape へ置換する攻撃は、persisted report 存在または独立 admission 成功で拒否される。
- identity を持つ failure の `continue` は cell loop 内であり、admitted peer へ trial 単位で波及しない。混成 peer の persisted report 欠落テストも有効である。
- failure decision と disposition は余剰 key、欠落 key、空 message、`KeyError` 型、`bool` count を exact 検査で拒否する。
- report と `run-finish.cell_admission_failures` は journal bytes の再読後に完全一致比較され、同じ可変 dict の参照だけを比較する恒真検査ではない。
- producer と verifier の status 判定は同じ `is_positive_cell_admission_decision` を共有する。failure report の `"complete"` は先行 gate でも拒否される。
- finalizer の catch は `AutonomousTrialError` 限定で、`KeyError` は伝播する。pending critic の pop は failure handler の一箩所だけで、後処理による欠落推測は復活していない。
- `layer3_report.py` は未変更で、certifying の `admission_status == "admitted"` 要求は維持されている。completeness 側も共通 helper へ移動しただけで同 literal を要求し、positive campaign は後段で validator receipt と完全一致する。

## 変異登録への追加提案

- **M9:** requested と cells が同長の `[failed, admitted]` を作り、completeness 単体が非最終 failure を拒否することを固定する。
- **M10:** disposition `count=1` の accounting state を `"partial-generation"` から `"generation-complete"` へ変更する。
- **M11:** 同 accounting state を `"pending-pre-invoke-failure"` へ変更する。
- **M12:** fallback failure cell に `campaign_id: null` または `campaign_root: null` を追加する。
- **M13:** admitted campaign cell の identity 参照だけを除去して failure shape と disposition を植え、fallback 免除へ倒れないことを固定する。
