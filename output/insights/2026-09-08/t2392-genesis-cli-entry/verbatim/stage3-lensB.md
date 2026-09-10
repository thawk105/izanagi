## 裁定文の読み方への攻撃

1. **real — 停止条件は4項目の連言と読むのが自然。**  
   D1775 はまず CLI 入口を「足す」と決め、その例外として「commit・argv・入力・lifecycle が記録されているなら足さない」としています。[D1775-verbatim.md:4](/home/SFC/tanab/.claude/jobs/631b6865/tmp/t2392/D1775-verbatim.md:4) 4項目から argv を除外する文言はありません。実測が `true / false / true / true` なら、通常の逐語適用では例外の前件は偽です。

2. **refuted — 「既存2入口も argv を記録しないから argv は数えない」は裁定文から導けない。**  
   「既存2入口と同じ層」は追加先を指定する句であり、記録項目の比較基準ではありません。また、D1775 は「記録されていない場合に足さない」を明示的に却下しています。[D1775-verbatim.md:17](/home/SFC/tanab/.claude/jobs/631b6865/tmp/t2392/D1775-verbatim.md:17) 親の読み方は、「新入口が不足項目を改善できる場合だけ数える」という別の有効性条件を裁定へ追加しています。

3. **real — D1769 が支持するのは事前確認であって、argv の除外ではない。**  
   D1769 は「out-of-band 呼出しが必ず provenance を失うと未確認のまま追加しない」という理由で引用されています。[D1775-verbatim.md:10](/home/SFC/tanab/.claude/jobs/631b6865/tmp/t2392/D1775-verbatim.md:10) 今回は argv が保存されないことまで確認済みなので、「不足未確認」という前提はもう成立しません。  
   一方、予定された subcommand も argv を保存しないため、追加の実効性を疑う材料にはなります。しかしそれはD1775の停止条件ではなく、ユーザーに再裁定してもらうべき新しい論点です。

## 足さなかった場合に起きること

1. **real — genesis を作る実行手順は両文書にない。**  
   事前登録文書は完全な attempt registry を実走前に要求し、正式起動ではその registry を消費すると定めています。[phase3-8c-preregistration.md:222](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/docs/phase3-8c-preregistration.md:222) [phase3-8c-preregistration.md:542](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/docs/phase3-8c-preregistration.md:542)  
   しかし、どのコマンドで genesis を作るか、slots をどう渡すか、誰が実行するかは書かれていません。runbook の具体的コマンドはすべて未登録 exploratory 起動です。[phase3-s8c-autonomous-trial-runbook.md:61](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/docs/phase3-s8c-autonomous-trial-runbook.md:61)

2. **real — コードが要求する commit 順序にも運用説明が不足している。**  
   verifier は genesis blob が内容 commit `P` に既に存在し、その hash が発効 binding と一致することを要求します。[trial_registry.py:1462](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:1462) したがって実際には、少なくとも「manifest と slots を用意 → genesis を生成 → genesis を含めて `P` を commit → binding-only の `C`」という順序が必要です。文書の起動形は `P` を manifest 導入 commit、`C` を binding-only commit と説明しますが、`P` 前の genesis 生成工程を示していません。[phase3-8c-preregistration.md:547](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/docs/phase3-8c-preregistration.md:547)

3. **判定不能 — 実際の担当者を特定できない。**  
   現在公開されている生成面は Python 関数 `create_attempt_registry_genesis(...)` だけです。[trial_registry.py:2471](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:2471) CLI parser には `register` と `accept` しかありません。[trial_registry.py:6502](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:6502)  
   段2調査も射影された production source 内の caller を0件としていますが、repo全体は判定不能と留保しています。[stage2-plan.md:3](/home/SFC/tanab/.claude/jobs/631b6865/tmp/t2392/artifacts/t2392-genesis-cli-entry/stage2-plan.md:3) したがって未知の caller がなければ、将来の実行責任者が手順書にない import・one-liner・臨時 script のいずれかで直接呼ぶことになります。

4. **real — out-of-band 呼出しであること自体は受入に拒否されない。**  
   受入は、`P` にある genesis bytes、その hash、registry の厳格な replay、lifecycle、receipt の prefix hash を検査します。[trial_registry.py:6282](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:6282) [trial_registry.py:6460](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:6460) caller や argv は検査対象ではありません。従って、直接 Python 呼出しが正しい bytes を生成して `P` に入れれば、その呼出し方だけを理由に受入が落ちることはありません。

5. **real — ただし「現在、正式受入が通る」という意味ではない。**  
   現文書では12条件中 C10 しか充足せず、正式起動は不可能と明記されています。[phase3-8c-preregistration.md:347](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/docs/phase3-8c-preregistration.md:347) [phase3-8c-preregistration.md:565](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/docs/phase3-8c-preregistration.md:565) 現行 receipt も `certifying: false` 固定です。[trial_registry.py:6466](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:6466) 上記は、他の前提が将来閉じた際にも genesis の呼出し provenance は受入条件にならない、という限定した結論です。

6. **real — 手順がないこと自体は運用上の欠落。**  
   正しい artifact を作れば機械受入できることと、再現可能な正式手順が存在することは別です。特に事前登録文書は「ここに書かれていない形で起動した実行を本系列に数えない」としています。[phase3-8c-preregistration.md:544](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/docs/phase3-8c-preregistration.md:544) genesis 作成がこの「起動」に含まれるかは明文化されていませんが、少なくとも正式系列の最初の不可逆な artifact を誰がどう作るかが未定義です。

## 「同じ層」の比較

1. **real — 既存2入口は単なる関数 alias 以上の入口契約を持つ。**

   | 入口 | 入口で固定されるもの |
   |---|---|
   | `register` | 必須4引数、manifest の exact-six 検証、HEAD に commit 済みの bytes、P/C/H binding、重複拒否を経て append。[trial_registry.py:6505](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:6505) [trial_registry.py:1732](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:1732) |
   | `accept` | 必須入力と report 群を受け、exact 6 report、committed registry、effective binding、attempt/lifecycle replay を検査。[trial_registry.py:6510](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:6510) [trial_registry.py:5845](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:5845) |
   | 計画中の `genesis` | 必須5引数、整数変換、strict JSON slots、manifest bytes からの hash 導出、registry path・retry理由の非公開固定を保証しうる。[stage2-plan.md:43](/home/SFC/tanab/.claude/jobs/631b6865/tmp/t2392/artifacts/t2392-genesis-cli-entry/stage2-plan.md:43) |

2. **real — raw argv provenance に限れば「1 bit も増えない」は正確。**  
   現在の `main(argv)` は `parse_args(argv)` するだけで、保存先がありません。[trial_registry.py:6502](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:6502) 計画された `genesis` も argv field や記録機構を足しません。したがって、P4を「raw argv の永続記録量」に限定すれば親の評価は成立します。

3. **refuted — 入口全体の保証が「1 bit も増えない」わけではない。**  
   現 callable は `manifest_sha256` を独立した引数として受け、manifest bytes から導出しません。[trial_registry.py:2471](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:2471) 計画どおりの CLI なら `load_trial_manifest` を通して digest を導出するため、誤った hash を genesis 作成時点で拒否できます。さらに argparse の必須引数・型検査、strict UTF-8 JSON・重複 key・非有限数の拒否、固定された呼出し形、`--help` で発見可能な正式入口が増えます。[trial_registry.py:606](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:606)

4. **real — その増分は provenance ではなく、入力構築と運用再現性の保証。**  
   creator 自体も canonical path、create-only、世代一致、閉じた retry reason を強制しています。[trial_registry.py:2415](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:2415) [trial_registry.py:2433](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:2433) [trial_registry.py:2484](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2392-genesis-cli-entry/orchestrator/campaign/trial_registry.py:2484) CLI が増やすのは raw argv の証跡ではなく、外部入力をその creator へ安全かつ一意に写す標準経路です。「provenance が増えない」と「追加価値がゼロ」は同値ではありません。

## 総括

- **real — P5はD1775の逐語から成立しない。** 4項目中 argv が欠ける以上、「記録されているなら足さない」の条件は満たされていません。
- **real — 足さない場合、正式系列の genesis は文書化されていない Python 直接呼出しへ落ちる可能性が高い。** それでも正しい bytes なら、呼出し方自体は受入で拒否されません。
- **real — CLI追加は raw argv provenance を改善しないが、引数契約、manifest hash の導出、入力形式の拒否、標準入口の実在という非 provenance の保証を増やす。**
- **判定不能 — 「不足を改善しない入口でも逐語どおり足す」のか、「実効的な provenance 増分がないので例外扱いする」のか。** 後者は合理的な設計判断ですがD1775にない条件です。親だけでP5を確定せず、D1775の4項目を連言として適用するかをユーザー再裁定へ返すべきです。