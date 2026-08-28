## 総括

実在する問題は3件です。特に、brief の scope 矛盾と「必要性を証明する」要件の脱落は、この wave 自体を過剰実装抑制の名目だけで通せる逃げ道になります。一方、rulings の索引漏れと絶対規律2/3の弱化については、現 plan の明文で防げており refuted です。

### Finding 1 — real: next-tasks の scope が自己矛盾している

- 判定: **real**
- 根拠:
  - brief は next-tasks が不要な提案を「提案、採用」しない判断規則を scope にしています。[s1-brief.md:3](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-avoid-overengineering/s1-brief.md:3)
  - 同じ brief は「next-tasks の選定アルゴリズム」を scope 外としています。[s1-brief.md:15](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-avoid-overengineering/s1-brief.md:15)
  - plan は実際に候補を除外する選定規則を追加します。[s2-plan.md:30](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-avoid-overengineering/s2-plan.md:30) [s2-plan.md:38](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-avoid-overengineering/s2-plan.md:38)
- 成果物影響: 親が line 15 を優先すればユーザーが明示した next-tasks 面への効力が消え、plan を優先すれば brief の scope 外変更になります。どちらでも受理境界が一意になりません。
- 最小修正文案: brief line 15 の該当箇所を次に置換します。

> scope 外: next-tasks の母集合収集、既存の優先順位、件数配分、dev-wave の9段構成、rulings の収集順・交差相談の変更。

### Finding 2 — real: 「必要性を証明できる」が単なる自己申告へ弱まっている

- 判定: **real**
- 根拠:
  - brief の scope は「必要性を証明できない」追加を拒否することです。[s1-brief.md:3](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-avoid-overengineering/s1-brief.md:3)
  - D605 も、実測と仮説を区別して過剰実装を却下しています。[authority-excerpt.md:14](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-avoid-overengineering/authority-excerpt.md:14)
  - ところが三つの計画文案は「足りない場合だけ」と宣言するだけで、足りないことを示す根拠を要求していません。[s2-plan.md:16](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-avoid-overengineering/s2-plan.md:16) [s2-plan.md:24](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-avoid-overengineering/s2-plan.md:24) [s2-plan.md:32](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-avoid-overengineering/s2-plan.md:32)
  - 現行 `DW-G05` が要求するのは放置時の成果物影響であり、既存機構や局所修正では足りないことの説明ではありません。[current-dev-wave-core.md:81](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-avoid-overengineering/current-dev-wave-core.md:81)
- 成果物影響: 「局所修正では足りない」と根拠なしに書くだけで framework、gate、台帳などを scope や候補へ入れられます。これは今回閉じるべき逃げ道そのものです。
- 最小修正文案: 四つの挿入文で許可条件を次の共通表現にします。

> 追加そのものを命じるユーザー明示要求を出典付きで示せるか、実在が確認された正しさ欠陥または現在の受入要件について、既存機構の再利用・局所修正では足りないことを対象機構と不足内容を挙げて示せる場合だけとする。

新しい checker や証拠台帳は不要です。一文の理由を既存の成果物影響、推奨根拠、投げ文へ載せれば足ります。

### Finding 3 — real: rulings と next-tasks の非弱化例外から二つの不変条件が落ちている

- 判定: **real**
- 根拠:
  - brief は「絶対規律2/3、既存防壁、ユーザー明示要求、現在の受入要件」の四つを削らないと定めています。[s1-brief.md:9](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-avoid-overengineering/s1-brief.md:9)
  - dev-wave 文案には四つともあります。[s2-plan.md:16](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-avoid-overengineering/s2-plan.md:16)
  - rulings 文案の非弱化対象は絶対規律2/3と既存安全規律だけです。[s2-plan.md:24](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-avoid-overengineering/s2-plan.md:24)
  - next-tasks 文案も同じ二項だけで、Codex 側にも同文を入れる計画です。[s2-plan.md:32](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-avoid-overengineering/s2-plan.md:32) [s2-plan.md:38](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-avoid-overengineering/s2-plan.md:38)
- 成果物影響: 既存要求の削除や downscope は「追加実装を推奨する」行為ではないため、前半の許可条件では防げません。rulings が不採用を推奨したり、next-tasks の投げ文が受入要件を落としたりする余地が残ります。
- 最小修正文案: rulings と両 next-tasks の末尾を次に統一します。

> この条件を、絶対規律2/3、その他の既存安全規律、明示されたユーザー要求、現在の受入要件を削除・弱化する根拠にしてはならない。

### Finding 4 — refuted: 「不採用推奨」による pending ruling の索引漏れ

- 判定: **refuted**
- 根拠:
  - 現行 rulings は T-ID 差集合、T-ID なし、未 land fragment、inbox、handoff まで収集します。[current-claude-rulings.md:14](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-avoid-overengineering/current-claude-rulings.md:14) [current-claude-rulings.md:18](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-avoid-overengineering/current-claude-rulings.md:18)
  - ユーザー裁定待ちは全件索引する契約です。[current-claude-rulings.md:33](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-avoid-overengineering/current-claude-rulings.md:33)
  - plan は不採用推奨でも裁定待ちの実体を索引から落とさないと明記しています。[s2-plan.md:24](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-avoid-overengineering/s2-plan.md:24)
  - rulings は「推奨はする、決めない」ため、不採用推奨だけで pending 状態は終了しません。[current-claude-rulings.md:47](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-avoid-overengineering/current-claude-rulings.md:47)
- 成果物影響: 収集・索引契約は維持されます。追加修正は不要です。

### Finding 5 — refuted: 新規則だけで絶対規律2/3や既存安全防壁を迂回できる

- 判定: **refuted**
- 根拠:
  - dev-wave 文案は四つの保護対象を明示しています。[s2-plan.md:16](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-avoid-overengineering/s2-plan.md:16)
  - rulings と next-tasks も、少なくとも絶対規律2/3と既存安全規律の非弱化を明記しています。[s2-plan.md:24](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-avoid-overengineering/s2-plan.md:24) [s2-plan.md:32](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-avoid-overengineering/s2-plan.md:32)
  - `DW-G01` から `DW-G04` は残り、提案文の「場合だけ」は必要条件であって、既存 gate を置き換える十分条件ではありません。[current-dev-wave-core.md:59](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-avoid-overengineering/current-dev-wave-core.md:59)
- 成果物影響: 絶対規律2/3と既存防壁について追加修正は不要です。ただし、ユーザー明示要求と現在の受入要件については Finding 3 の補完が必要です。

親の最小修正は、brief の scope 外表現を狭め、四文案へ根拠提示を加え、rulings・next-tasks の非弱化対象を四項へ揃えることです。新しい checker、gate、台帳は要りません。read-only 指示に従い、テストは実行していません。