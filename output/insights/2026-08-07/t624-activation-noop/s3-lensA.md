結論は、段 2 プランのままでは **NO-GO** です。裁定 (a) の論理式自体は妥当ですが、それを consumer 0 の public predicate として land できる根拠にはなっていません。

### [M1] `DW-G04` を満たしていない

(a) 主張: 「D196/B(a) の禁止対象ではない」は必要条件にすぎず、実装許可の証明ではありません。T-624 brief には、この predicate を真に発火させる activation record の artifact path または計測 ID がありません。`94a4` / `892707.nqsv` は calibration 素材であり、before/after の env→generation mapping を持つ activation artifact ではありません。

(b) 根拠: `DW-G04` は「書けなければ設計メモに留める」と明記します（[core.md:60](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/docs/dev-wave/core.md:60)）。brief 自身も activation record 未実装を認めています（[s1-brief.md:48](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/output/insights/2026-08-07_t624-activation-noop/s1-brief.md:48)）。前 wave が確認した `94a4` も「prospective g2 素材」に限定されています（[s4-adjudication.md:22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/output/insights/2026-08-07_t529-impl-reraise/s4-adjudication.md:22)、[同:31](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/output/insights/2026-08-07_t529-impl-reraise/s4-adjudication.md:31)）。B(a) が T-529 限定なのは、T-624 が `DW-G04` から免除されることを意味しません。

(c) 成果物影響: 単位 2 を land しても certified 選択・レポート・試行台帳の no-op 受理集合は一要素も狭まりません。変わるのは source identity 値だけです。「no-op を拒否する gate」が成果物には存在しないままになります。

### [M2] D176 の先例とは同型でなく、むしろ名ばかりの保証に近い

(a) 主張: D176 は「任意の test-only predicate を置いてよい」と裁定していません。既存 `is_valid_successor` は実在する `GenerationEntry` / `GENERATIONS` と validator の call chain に組み込まれています。新 predicate は schema も consumer もなく、さらに registry 未登録 env・存在しない generation さえ受理します。

(b) 根拠: `is_valid_successor` は候補世代 validator から呼ばれ（[env_contract.py:308](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/orchestrator/campaign/env_contract.py:308)）、その validator は module 初期化に結線済みです（[env_contract.py:316](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/orchestrator/campaign/env_contract.py:316)、[同:344](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/orchestrator/campaign/env_contract.py:344)）。対してプランは consumer 0、registry/generation 実在検査なしを明記します（[s2-plan.md:215](/work/1/SFC/tanab/dev-wave-jobs/t624-activation-noop/s2-plan.md:215)、[同:218](/work/1/SFC/tanab/dev-wave-jobs/t624-activation-noop/s2-plan.md:218)）。D176 が型分離を却下した理由は「生成権限を証明しない名ばかりの保証」です（[decisions.md:8680](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/docs/decisions.md:8680)）。

(c) 成果物影響: 計画された受理集合では `{"ghost": 999} → {"ghost": 1000}` が `True` です。将来これを名前どおり単独 gate として使えば、試行台帳・レポートが存在しない契約世代を参照し、certified proof chain が解決不能になります。使わなければ現在と同じく何も拒否しません。

### [M3] `DW-G05` と絶対規律 5 を identity 副作用で迂回している

(a) 主張: T-126 `code_identity` や silo `runtime_modules_sha256` の変化は、predicate の保護効果ではありません。任意のコメント追加でも変わる provenance 値であり、これを成果物影響として scope 正当化に使うと `DW-G05` が恒真になります。

(b) 根拠: brief は「成果物影響ゼロ」を明記します（[s1-brief.md:36](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/output/insights/2026-08-07_t624-activation-noop/s1-brief.md:36)）。`DW-G05` は影響を書けない scope を送るよう要求します（[core.md:65](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/docs/dev-wave/core.md:65)）。絶対規律 5 は各 component の効果を ablation 可能にするよう求めます（[CLAUDE.md:83](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/CLAUDE.md:83)）。プランが挙げる実変化は identity と source-drift 拒否だけです（[s2-plan.md:245](/work/1/SFC/tanab/dev-wave-jobs/t624-activation-noop/s2-plan.md:245)、[同:248](/work/1/SFC/tanab/dev-wave-jobs/t624-activation-noop/s2-plan.md:248)）。

(c) 成果物影響: 次回 T-126 の `code_identity` / `series_identity` と silo の `runtime_modules_sha256` は変わり、旧 source で submit 済みの silo collect は拒否されます。一方、certified 選択・no-op 受理集合・proof 参照は不変です。これは純増の運用負債であり、機能効果ではありません。

### [M4] `DW-O13` 違反に加え、暫定 P3 を未裁定のまま決定へ昇格している

(a) 主張: activation state の実 schema・field がない段階で、`Mapping[str,int]`、同一 key 集合、env 追加・削除拒否を凍結してはいけません。裁定 (a) が確定したのは no-op 拒否条件であり、新 env migration の禁止ではありません。

(b) 根拠: `DW-O13` は設計前に入力 field の実在確認を要求します（[operations.md:74](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/docs/dev-wave/operations.md:74)）。D75 は「schema に存在しない入力を前提に gate を書いた」ことを既知失敗として記録しています（[decisions.md:3033](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/docs/decisions.md:3033)）。D197 は state 全体の識別子を決めただけで、mapping field schema は定義していません（[decisions.md:9530](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/docs/decisions.md:9530)）。にもかかわらずプランは P3 を decisions 案へ確定事項として移しています（[s2-plan.md:200](/work/1/SFC/tanab/dev-wave-jobs/t624-activation-noop/s2-plan.md:200)）。

(c) 成果物影響: 将来 env を追加すると、before に key がなく after に g1 key があるため必ず拒否されます。試行台帳・レポートは新 env の activation 参照を発行できず、後続で例外経路を作るか受理集合を再変更する二度手間になります。

### [M5] 前提実測 C は事実として偽で、既知 F30 を再発している

(a) 主張: `env_contract.py` の bytes pin は 0 件ではありません。path+SHA の historical binding に加え、`env_contract_sha256` という role 名 key の pin があります。段 2 の探索は path と hash の同一行 hit に依存し、既知の見落とし型を繰り返しています。

(b) 根拠: failures 台帳は、この exact role-key pin を既に記録しています（[failures.md:585](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/docs/failures.md:585)）。実 artifact にも `env_contract_sha256` が存在します（[manifest.json:105](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/output/env/pegasus/t419-probe-causality/0_888740.nqsv/manifest.json:105)）。silo artifact は path と SHA を隣接 field で保持しています（[silo_ladder_rung1.json:67](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json:67)）。したがって plan の「hit 0」は成立しません（[s2-plan.md:251](/work/1/SFC/tanab/dev-wave-jobs/t624-activation-noop/s2-plan.md:251)）。

(c) 成果物影響: 既存 t419 manifest/result は旧 `env_contract_sha256` 参照を保持し、今後生成する同 artifact の値は新 SHA になります。historical/live の分類なしでは再現参照が分岐します。段 2 の波及棚卸しと受入候補には t419 層が欠落しています。

### [S1] scope 外・裁定パッケージ候補: 実効 gate の縦断 slice

(a) 主張: 実効的な no-op 拒否には、ActivationRecord の実 schema/producer、mapping 射影、registry・generation 実在検査、serial/hash chain、全入口 consumer/receipt、構造化された拒否結果が必要です。段 2 はその全てを scope 外にし、関係述語だけを「実装」と数えています。

(b) 根拠: 段 3 契約は gate が効く全層を scope 検査するよう要求します（[workers.md:16](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/docs/dev-wave/workers.md:16)）。プラン自身が欠落層を列挙しています（[s2-plan.md:215](/work/1/SFC/tanab/dev-wave-jobs/t624-activation-noop/s2-plan.md:215)）。これらの authority/receipt 層は D196 の裁定境界内です（[decisions.md:9492](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/docs/decisions.md:9492)）。

(c) 成果物影響: 縦断 slice が揃うまで、certified 選択・レポート・試行台帳の受理集合には no-op 拒否が現れません。部分結線すれば入口ごとの迂回と proof 参照不一致を生みます。これは本 wave で実装せず、依存完了後の裁定パッケージへ返すべきです。

### [S2] scope 外・裁定パッケージ候補: env membership migration

(a) 主張: env 追加・削除を永久拒否するのか、別種の migration とするのかは未裁定です。P3 から自動導出してはいけません。

(b) 根拠: brief 自身が新 env の遷移表現を未定義としています（[s1-brief.md:40](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/output/insights/2026-08-07_t624-activation-noop/s1-brief.md:40)）。plan も同じ未了を認めています（[s2-plan.md:221](/work/1/SFC/tanab/dev-wave-jobs/t624-activation-noop/s2-plan.md:221)）。

(c) 成果物影響: 方針未決のまま same-key gate を凍結すると、新 env を含む activation record は台帳・レポートで一律拒否されます。別 migration を認めるなら、その schema と合流条件を先に裁定する必要があります。

### [N1] 実測 B からの一般化は成立しない

(a) 主張: public 関数追加を限定した二ファイルの実測は、実装予定本文・全 identity consumer・全受入が壊れない証明ではありません。plan 自身も後段の全受入が必要と認めています。

(b) 根拠: 親の記録は二ファイル限定です（[s1-brief.md:49](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t624-activation-noop/output/insights/2026-08-07_t624-activation-noop/s1-brief.md:49)）。段 2 は別途、通常の全受入まで必要としています（[s2-plan.md:253](/work/1/SFC/tanab/dev-wave-jobs/t624-activation-noop/s2-plan.md:253)）。

(c) 成果物影響: この推論単独から具体的な値・受理集合・参照の変化は特定できないため、must-fix ではなく nit とします。本レビューでは pytest を実行していません。

## 総括

**NO-GO。** 単位 2 は `DW-G04`・`DW-G05`・`DW-O13`・絶対規律 5 を満たさず、land 不可です。  
単位 1 も裁定 (a) の逐語的明文化までに限定し、未裁定の same-key/env migration 規則を混入させてはいけません。  
実装は実 activation artifact と全 consumer 層を scope にできる wave まで設計メモに留めるべきです。  
静的検査のみで、pytest は実行していません。