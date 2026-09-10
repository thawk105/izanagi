## 総括

plan の4変更面という骨格は最小です。ただし、そのまま実装すると過剰追加を許す論理の曖昧さ、投げ文への規則複製、予算超過時の期待値更新という3件の real finding があります。ここを直した plan v2 なら採用できます。新しい checker、台帳、スコア、節は不要です。

### F1 — REAL: 許可条件の論理範囲が曖昧

- 根拠: [s2-plan.md:16](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-avoid-overengineering/s2-plan.md:16)、[s2-plan.md:24](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-avoid-overengineering/s2-plan.md:24)、[s2-plan.md:32](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-avoid-overengineering/s2-plan.md:32)
- 「既存機構の再利用・局所修正では足りない」が「現在の受入要件」にだけ係るとも読めます。その場合、実在する欠陥が一つあれば、局所修正で足りても framework 等を採用できます。
- これは「局所修正で足りるなら広い仕組みを採らない」という brief の不変条件と不整合です。[s1-brief.md:11](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-avoid-overengineering/s1-brief.md:11)
- 成果物影響: 今回追加する規則自体が、実在欠陥を口実にした過剰実装を止められません。
- 最小代案:

> 追加手段そのものがユーザーの明示要求である場合を除き、実在する正しさ欠陥の解消または既存の受入要件の充足に必要で、かつ既存機構の再利用・局所修正では足りないと確認できる場合だけ、追加実装・追加防壁を候補、scope、または採用推奨へ入れる。仮想リスクだけでは追加せず、この規則で既存安全規律を弱めない。

各面では「候補」「scope」「採用推奨」の動詞だけを合わせれば足ります。

### F2 — REAL: byte budget の自動追随を許している

- 根拠: brief は lint 更新を成果物候補にし、plan は byte budget が反応した場合の期待値更新を認めています。[s1-brief.md:13](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-avoid-overengineering/s1-brief.md:13)、[s2-plan.md:55](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-avoid-overengineering/s2-plan.md:55)、[s2-plan.md:59](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-avoid-overengineering/s2-plan.md:59)
- しかし既存契約は、まず現行 byte・最長行予算へ収め、収まらなければ既存節への統合や縮約を要求しています。上限引き上げは単なる期待値更新ではありません。[current-skill-self-improvement.md:45](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-avoid-overengineering/current-skill-self-improvement.md:45)、[current-skill-self-improvement.md:50](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-avoid-overengineering/current-skill-self-improvement.md:50)
- 成果物影響: 反過剰実装の文言を足すために文書予算を膨らませる、または不要な fixture を変更する自己矛盾が起きます。
- 最小代案: byte・行長予算が赤なら文面を縮め、予算値は変えない。今回 address edge は変えないため address lint の期待値も変更しない。意図した byte 差だけを検知する whole-file pin は、現行予算内へ収めた後に限り最小更新できます。[current-skill-self-improvement.md:82](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-avoid-overengineering/current-skill-self-improvement.md:82)

### F3 — REAL: next-tasks が規則全文を各投げ文へ複製する

- 根拠: plan は候補選定だけでなく、採用した全投げ文へ同じ判定条件を省略せず書かせます。[s2-plan.md:7](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-avoid-overengineering/s2-plan.md:7)、[s2-plan.md:32](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-avoid-overengineering/s2-plan.md:32)
- 既存出力規則は、すでに効果・裁定根拠・規律2・scope 外を投げ文へ載せます。[current-claude-next-tasks.md:165](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-avoid-overengineering/current-claude-next-tasks.md:165)、[current-claude-next-tasks.md:172](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-avoid-overengineering/current-claude-next-tasks.md:172)、[current-codex-next-tasks.md:53](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-avoid-overengineering/current-codex-next-tasks.md:53)
- さらに投げ先の dev-wave は `DW-G05` を段1・4・6で読みます。[current-claude-dev-wave.md:66](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-avoid-overengineering/current-claude-dev-wave.md:66)、[current-claude-dev-wave.md:74](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-avoid-overengineering/current-claude-dev-wave.md:74)
- 成果物影響: すべての投げ文が肥大化し、personal 定義と `DW-G05` の二重正本が意味ずれを起こします。
- 最小代案: next-tasks には候補除外規則だけを置き、「投げ文にも同じ条件を書く」を削除する。候補の具体的な効果と裁定根拠は既存出力形式で示し、下流の一般規則は `DW-G05` に委譲します。

### F4 — REAL、ただし plan 側は封じている: rulings の成果物影響説明が不正確

- 根拠: brief は rulings が仮想リスクを「ユーザー判断へ昇格」させるとしています。[s1-brief.md:12](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-avoid-overengineering/s1-brief.md:12)
- 現行 rulings は既存正本にあるユーザー裁定待ちを収集するもので、新しい裁定を作る入口ではありません。[current-claude-rulings.md:12](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-avoid-overengineering/current-claude-rulings.md:12)、[current-claude-rulings.md:33](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-avoid-overengineering/current-claude-rulings.md:33)
- plan が「索引から落とさず、不採用を推奨する」とした点は正しいです。[s2-plan.md:24](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-avoid-overengineering/s2-plan.md:24)
- 成果物影響: brief の説明を文字どおり実装すると、索引をフィルタして裁定待ちを隠す方向へ逸脱しえます。
- 最小代案: brief の理由だけを「既に索引された裁定で、仮想リスク案の採用を推奨しうる」に読み替える。plan の索引完全性条項は残します。

### F5 — REFUTED: 新しい G 節や入口変更が必要

- brief の新 G 節案は既存被覆と重複します。[s1-brief.md:8](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-avoid-overengineering/s1-brief.md:8)、[s1-brief.md:16](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-avoid-overengineering/s1-brief.md:16)
- plan はこれを退け、既存 `DW-G05` へ統合しています。[s2-plan.md:5](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-avoid-overengineering/s2-plan.md:5)
- Codex dev-wave も Claude dispatcher を全文実行します。[current-codex-dev-wave.md:17](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-avoid-overengineering/current-codex-dev-wave.md:17)
- 成果物影響: plan どおりなら `DW-G06`、Claude/Codex dev-wave 入口変更は不要です。より小さい代案はありません。

### F6 — REFUTED: personal 定義を repo commit と誤認している

- plan は repo 内2ファイルを一つの commit、repo 外2ファイルを別の personal 変更として明確に分離しています。[s2-plan.md:59](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-avoid-overengineering/s2-plan.md:59)、[s2-plan.md:61](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-avoid-overengineering/s2-plan.md:61)、[s2-plan.md:74](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-avoid-overengineering/s2-plan.md:74)
- next-tasks は共通 dispatcher がなく、Claude と Codex で起動構文も異なります。[current-claude-next-tasks.md:169](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-avoid-overengineering/current-claude-next-tasks.md:169)、[current-codex-next-tasks.md:54](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-avoid-overengineering/current-codex-next-tasks.md:54)
- 成果物影響: personal 定義を repo へ移す、共通化機構を新設する、personal 変更を commit OID の成果に含める必要はありません。

最小 plan v2 は、4変更面を維持し、F1の文言へ修正、next-tasks の投げ文複製を削除、byte/address 予算更新の事前許可を削除する形です。その他の checker、テスト、台帳、節、入口変更は増やさないのが妥当です。