# 所見

### 1. 違反値が `effective` に接続されていない

- 深刻度: must-fix（後続 wave）
- file:line: [s8c_preregistration.py:1843](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-s8c-section5-value-check/orchestrator/campaign/s8c_preregistration.py:1843), [s8c_preregistration.py:1869](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-s8c-section5-value-check/orchestrator/campaign/s8c_preregistration.py:1869)
- 具体例: `H1.n=1` は `FILLED` のまま `n-range` violation になるが、連言式は `section5_value_violations` を見ない。`prepare_revision` も違反を拒否しない。
- 影響: 条件 7 の evaluator が将来実装された際、evaluator が violation を消費しなければ、不正な契約値で発効し、正式な台帳・レポートへ進む可能性がある。8b の「事前登録そのものを未発効へ倒す」[規定](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-s8c-section5-value-check/docs/phase3-8b-descriptor-design.md:474)を満たさない。

現在は条件 7 が充足を返さないため直ちに誤発効はしないが、ユーザー依頼との差は残る。最小の是正は、条件 7 evaluator が violation、manifest の `n` exact 一致、judge、3 表をまとめて消費すること。連言式へ直接追加するなら凍結本文、DECIDER_VERSION、新世代 record の同時更新が必要。

### 2. 裁定パッケージ項目 2 に D458 の世代移行が明記されていない

- 深刻度: should-fix
- file:line: [s4-adjudication.md:187](/home/SFC/tanab/.claude/jobs/750a6f4d/tmp/wave-s8c-s5value/s4-adjudication.md:187), [phase3-8c-preregistration.md:293](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-s8c-section5-value-check/docs/phase3-8c-preregistration.md:293)
- 具体例: 条件 7 を `machine_checkable: true` にし evaluator が充足を返せるようにすると、`all_satisfied` と将来の受理集合が変わる。
- 影響: D458 に従う DECIDER_VERSION bump、新世代 record、裁定参照が無いままだと、旧 record が新しい判定意味で再利用され、将来の発効判定と凍結台帳の意味がずれる。

項目 2 は judge・完全 block・`n` exact・3 表を要求しており方向は正しいが、上記の世代移行を明示的に追加すべき。

### 3. violation が ActivationReport、CLI、report digest へ届かない

- 深刻度: should-fix（裁定待ち）
- file:line: [s8c_preregistration.py:194](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-s8c-section5-value-check/orchestrator/campaign/s8c_preregistration.py:194), [s8c_preregistration.py:1884](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-s8c-section5-value-check/orchestrator/campaign/s8c_preregistration.py:1884), [s8c_preregistration.py:2113](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-s8c-section5-value-check/orchestrator/campaign/s8c_preregistration.py:2113)
- 具体例: parser の `MarkdownContract` には violation が入るが、`ActivationReport` は `section5_findings` だけを保持し、CLI も `FILLED canonical-json` としか表示しない。
- 影響: 現在の発効集合・台帳は変わらない一方、将来の診断レポートでは不正値の理由が見えず、運用者が値セルを正当と誤認しうる。

裁定項目 3 は妥当な選択肢であり、Report へ載せるなら digest と capability の移行を別途裁定すべき。現 wave で `ActivationReport` を変更しなかった判断自体は D458 と整合する。

### 4. exact schema は 8b の凍結制約ではない

- 深刻度: nit
- file:line: [s8c_preregistration.py:888](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-s8c-section5-value-check/orchestrator/campaign/s8c_preregistration.py:888), [s8c_preregistration.py:903](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-s8c-section5-value-check/orchestrator/campaign/s8c_preregistration.py:903)
- 具体例: 8b は `n`、`delta_min`、`sd_max` の制約を凍結するが、root の `H1/H2` や block の exact key 集合までは凍結していない。追加 metadata を含む表現は `root-keys` で拒否される。
- 影響: 8c 側の表現を変更しない限り問題ないが、将来の正当な表現変更まで repo の受理集合から排除する。

裁定は exact schema を 8c 側の表現として採用しているため、現 wave の過剰拒否とは判定しない。ただし、その位置付けを validator の docstring 等へ明記すべき。

# 凍結契約との整合の判定

この差分単独では DECIDER_VERSION bump は不要。8c は「欄ごとの型・単位・範囲の検証は本手続きの対象外」とし、凍結対象も §5 の値ではなく欄名集合としている。

`FieldStatus`、`all_filled`、`ActivationReport` の field 集合は不変であり、`_assert_record_matches_contract` は従来の hash 群だけを照合する。`_record_document`、freeze history、`_activation_report_digest` も新 field を射影しないため、受理集合・拒否理由・射影された判定入力の意味は変わらない。新しい `code` は現状では拒否理由ではなく、parser の診断情報である。

8b との対応は次の通り。

- `n` の整数・2 以上、`delta_min` の有限・正、`sd_max` の有限・非負は値セルで検査できており過不足ない。
- 観測反復数との exact 一致は manifest 側の責務なので、validator に混ぜていないのが正しい。
- `unit` と `direction` は非空文字列までに留め、固定語彙や judge との意味整合を要求していないのが正しい。
- `sd_max=-0.0` を受理する実装は、有限な非負という 8b 制約に一致する。

# 波及の静的列挙

- parser API: `parse_preregistration_markdown`、`parse_preregistration_at`、`parse_preregistration_worktree` から violation に到達できる。
- freeze record: `_load_freeze_record`、`_record_document` は新 field を保存しない。§5 の値が凍結対象外なので整合する。
- `_assert_record_matches_contract`: 既存の protected hash だけを照合し、violation は無視する。現行設計では意図的だが、発効閂にはならない。
- history verification: `validate_condition_freeze_at` は parser を通るが、`_assert_record_matches_contract` と ruling 検査は従来通り。履歴検証の受理集合は変わらない。
- `prepare_revision`: parser は呼ぶが violation を拒否せず、従来の record を生成する。
- activation: `all_filled` は `Section5Finding` の status のみを見て、violation は使わない。
- digest/capability: `ActivationReport` が不変なので `_activation_report_digest` と `require_effective_preregistration` の期待 digest も不変。
- CLI: subcommand 集合は不変。通常表示・JSON 表示とも violation は出ない。
- テスト配置: core 側は値 validator と `parse_preregistration_at` を検査し、invariant 側の [test_s8c_preregistration_invariant.py:597](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-s8c-section5-value-check/orchestrator/tests/test_s8c_preregistration_invariant.py:597) は生き doc の閂を検査する。親の焦点走に invariant file が含まれるため、受入全走専用ではない。ただし production の `effective` を直接止める検査ではない。

## 総括

8b の値制約は値セル責務として正しく写され、manifest の `n` exact 一致も混入していない。  
この差分は診断 field の追加に留まり、D458 の bump は不要。  
一方、ユーザー要求の「違反値で未発効」は未達で、条件 7 evaluator への接続が後続の必須作業。  
裁定パッケージは概ね妥当だが、項目 2 に D458 の世代移行を追加すべき。  
pytest は実走しておらず、緑とは報告しない。