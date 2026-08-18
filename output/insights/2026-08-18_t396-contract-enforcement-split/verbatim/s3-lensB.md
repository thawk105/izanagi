静的監査結果。worktree は clean。pytest、checker、ビルドは未実走であり、緑とは判定していない。

### 所見 1 — 機械非検査項目は明示的許可ではないが、live prompt として誤読余地が残る

- **判定への影響**: 現在の受理集合は変わらない。ただし coder が機械検査だけを満たし、残余禁止を破る誘因が残る。auditor が見逃せば、候補の certified 選択や材料レポートが不正なものになり得る。
- **根拠**: [s1-brief.md:25](/home/SFC/tanab/.claude/jobs/a3bc3ac6/tmp/t396/artifacts/dev-wave-t396-contract-alignment/s1-brief.md:25)、[s1-brief.md:26](/home/SFC/tanab/.claude/jobs/a3bc3ac6/tmp/t396/artifacts/dev-wave-t396-contract-alignment/s1-brief.md:26)、[s2-plan.md:93](/home/SFC/tanab/.claude/jobs/a3bc3ac6/tmp/t396/artifacts/dev-wave-t396-contract-alignment/s2-plan.md:93)、[s2-plan.md:95](/home/SFC/tanab/.claude/jobs/a3bc3ac6/tmp/t396/artifacts/dev-wave-t396-contract-alignment/s2-plan.md:95)、[auditor.md:34](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-contract-alignment/.claude/agents/auditor.md:34)、[auditor_gate.py:198](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-contract-alignment/orchestrator/campaign/auditor_gate.py:198)
- **区分**: should-fix

現案は各項目に「禁止は不変」「auditor が拒否する」と書いており、直接の許可ではない。しかし、冒頭に次を置くと読み間違いをさらに抑えられる。

> この節の全項目は coder が生成時に守る必須禁止である。機械検査か auditor 目視かは執行主体の分類であり、機械が検査しないことは許可を意味しない。

### 所見 2 — 親が adapter を代行編集する fallback は D95 に反する

- **判定への影響**: `.codex/role-adapters` の更新を親が直接行えば、内容自体が正しくても wave の実装手続と provenance が無効になる。成果物の値そのものは直ちには変わらないが、GO 判定と land 資格を失う。
- **根拠**: [s1-brief.md:68](/home/SFC/tanab/.claude/jobs/a3bc3ac6/tmp/t396/artifacts/dev-wave-t396-contract-alignment/s1-brief.md:68)、[s2-plan.md:174](/home/SFC/tanab/.claude/jobs/a3bc3ac6/tmp/t396/artifacts/dev-wave-t396-contract-alignment/s2-plan.md:174)、[decisions.md:4244](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-contract-alignment/docs/decisions.md:4244)、[decisions.md:4249](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-contract-alignment/docs/decisions.md:4249)、[decisions.md:4258](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-contract-alignment/docs/decisions.md:4258)
- **区分**: must-fix

adapter 書込みは Codex author child に所有させるべきである。書込み不能なら、親が代行せず停止してユーザー裁定を求める。D149 の過去事例は、この wave の D95 を自動的に上書きする一般例外ではない。

### 所見 3 — pin 閉包は識別子 key と path の両方で不足なし。ただし pin は意味の証明ではない

- **判定への影響**: role 名 key、source path、adapter 内の source hash、semantic digest の更新先は閉じている。manifest、description、schema、template、IO contract を更新する必要はない。
- **根拠**: [review_ledger.py:21](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-contract-alignment/orchestrator/codex_roles/review_ledger.py:21)、[manifest.json:733](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-contract-alignment/orchestrator/codex_roles/manifest.json:733)、[coder adapter:165](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-contract-alignment/.codex/role-adapters/coder-v4-autonomous-sort.json:165)、[spec.py:790](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-contract-alignment/orchestrator/codex_roles/spec.py:790)、[spec.py:837](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-contract-alignment/orchestrator/codex_roles/spec.py:837)、[check_codex_agents.py:241](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-contract-alignment/tools/check_codex_agents.py:241)
- **区分**: should-fix

byte parity と source pin は、本文が同一であることしか証明しない。段 2 自身も、残余禁止を削除して pin を更新する mutation に semantic test がないと認めている。[s2-plan.md:285](/home/SFC/tanab/.claude/jobs/a3bc3ac6/tmp/t396/artifacts/dev-wave-t396-contract-alignment/s2-plan.md:285) の通り、5 分類の保持は実装者と auditor が diff で明示確認し、checker を意味証明として報告してはならない。

### 所見 4 — B は受理集合を変えないが、5 件の検出力を意図的に失う

- **判定への影響**: production gate は不変なので、現在の受理集合、certified 選択、材料レポートの値は変わらない。削除対象は 5 件の parameterized case で、bounded、range、data-dependent loop と integer-zero の false-literal fixture に対する将来の過剰拒否検出が消える。
- **根拠**: [test_coder_effect_gate.py:151](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-contract-alignment/orchestrator/tests/test_coder_effect_gate.py:151)、[test_coder_effect_gate.py:161](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-contract-alignment/orchestrator/tests/test_coder_effect_gate.py:161)、[test_coder_effect_gate.py:165](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-contract-alignment/orchestrator/tests/test_coder_effect_gate.py:165)、[test_coder_effect_gate.py:196](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-contract-alignment/orchestrator/tests/test_coder_effect_gate.py:196)、[decisions.md:4275](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-contract-alignment/docs/decisions.md:4275)
- **区分**: nit（裁定による意図的な検出力喪失）

現行 gate が受け止めるのは実行時の reject であり、将来の過剰拒否を検出する live test owner は残らない。固定 node 数や file 集合を検査する live meta test、docs の逐語参照は静的検索で見つからなかった。これは「テストを削除して緑にする」とは異なり、production predicate を変えず、B 裁定により pass 契約を未定義へ戻す削除である。ただし実走していないため、緑の確認はしていない。

### 所見 5 — C と D に関する親の判断は正しい

- **判定への影響**: C の重複起票や D の誤った再起票はなく、裁定台帳の参照値は変わらない。
- **根拠**: [archive worklog:153](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-contract-alignment/docs/archive/worklog-phase3-0816-568.md:153)、[archive worklog:474](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-contract-alignment/docs/archive/worklog-phase3-0816-568.md:474)、[worklog.md:2848](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-contract-alignment/docs/worklog.md:2848)、[insight README:169](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-contract-alignment/output/insights/2026-08-15_t396-hole-allowlist-refuted/README.md:169)
- **区分**: nit（問題なし）

C は T-1148 として既に分離起票され、D は docs 予算超過による見送りとして確定している。D344 を覆す記録もない。

### 所見 6 — D23、D96、D344 との直接衝突はない

- **判定への影響**: A は契約文の執行主体を分けるだけで、production gate、raw C++ 合成、typed IR/AST allowlist を変更しない。B も test oracle の削除だけなので D96 の新 D と境界 test の義務を発生させない。
- **根拠**: [decisions.md:416](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-contract-alignment/docs/decisions.md:416)、[decisions.md:4275](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-contract-alignment/docs/decisions.md:4275)、[decisions.md:15206](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-contract-alignment/docs/decisions.md:15206)、[s1-brief.md:23](/home/SFC/tanab/.claude/jobs/a3bc3ac6/tmp/t396/artifacts/dev-wave-t396-contract-alignment/s1-brief.md:23)
- **区分**: nit（問題なし）

D23 の raw preprocessor と非決定 builtin の禁止は段 2 案にも残っている。D344 の raw C++ 合成も維持される。

## 総括

NO-GO。計画をそのまま進めてはならない。  
must-fix は 1 件で、D95 に反する親の adapter 代行経路。  
should-fix は prompt の冒頭明示と、pin を意味証明と誤報告しない手続き。  
B は裁定どおりで、受理集合は不変だが、5 件の検出力喪失を材料レポートに残す。  
C の T-1148 分離起票と D の見送り確定は正しい。  
pytest、checker、ビルドは未実走である。