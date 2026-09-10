## 総括

最小差分は、repo 内 2 ファイルと repo 外 personal 定義 2 ファイルの計 4 ファイルです。

- dev-wave: 新しい `DW-G06` は作らず、既存 `DW-G05` に統合する。Claude 入口は既に `DW-G05` を段 1・4・6で読み、Codex 入口は Claude dispatcher に委譲するため、両入口の変更は不要。
- rulings: Claude 側の共通 dispatcher の既存「作法」に一度だけ追加する。Codex Skill は同 dispatcher を全文実行するため変更不要。
- next-tasks: 共通 dispatcher がないため、二つの personal 定義の「選定規則」に意味等価な短文を各一度置く。その一文で候補選定と投げ文への展開を両方命じる。
- checker、スコア、台帳、独立した新節は追加しない。

## exact insertion plan

### 1. dev-wave 共通規則

[docs/dev-wave/core.md](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-avoid-overengineering/docs/dev-wave/core.md:79) の `DW-G05 — 成果物影響` 内、現行 81〜84 行の末尾と `DW-S04` の間へ次を追記します。

> 追加実装・追加防壁を scope または must-fix に入れるのは、追加そのものがユーザーの明示要求であるか、実在が確認された正しさ欠陥または現在の受入要件を満たすために既存機構の再利用・局所修正では足りない場合だけとする。仮想リスクや将来の可能性だけで framework・一般化・互換層・gate・検査・台帳を足さない。この条件を、絶対規律 2/3、既存の正しさ防壁、明示されたユーザー要求、現在の受入要件を削除・弱化する根拠にしてはならない。

これにより既存の成果物影響判定と同じ発火点で、追加の必要性、局所修正優先、安全規律の例外を判定できます。

### 2. rulings 共通規則

[.claude/commands/rulings.md](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-avoid-overengineering/.claude/commands/rulings.md:47) の `## 作法` 内、既裁定検索と主経路距離を求める現行 bullet の直後、交差意見 bullet の前へ追加します。

> - 追加実装・追加防壁を推奨するのは、追加そのものがユーザーの明示要求であるか、実在が確認された正しさ欠陥または現在の受入要件を満たすために既存機構の再利用・局所修正では足りない場合だけとする。仮想リスクや将来の可能性だけの案は不採用を推奨する。ただし裁定待ちの実体は索引から落とさず、この条件を絶対規律 2/3 その他の既存安全規律を削除・弱化する根拠にしない。

索引の完全性は維持し、過剰な案には「不採用」を推奨する構造です。収集順や裁定記録方式は変えません。

### 3. Claude personal next-tasks

[/home/SFC/tanab/.claude/commands/next-tasks.md](/home/SFC/tanab/.claude/commands/next-tasks.md:104) の `## 選定規則` 内、「今すぐ着手可能」の現行 bullet が終わる 104 行直後、`非稼働` bullet の前へ追加します。

> - **過剰追加を出さない**: 追加そのものがユーザーの明示要求であるか、実在が確認された正しさ欠陥または現在の受入要件に対して既存機構の再利用・局所修正では足りない場合だけ候補にする。仮想リスク・将来可能性だけの追加は除外し、採用候補の投げ文にも同じ判定条件を省略せず書き、絶対規律 2/3 その他の既存安全規律を弱めないと明記する。

一つの bullet で選定と投げ文の両方を拘束するため、`## 出力形式` への重複追記は不要です。

### 4. Codex personal next-tasks

[/home/SFC/tanab/.agents/skills/next-tasks/SKILL.md](/home/SFC/tanab/.agents/skills/next-tasks/SKILL.md:37) の `## 選定規則` 内、「裁定済み」を実装済みと誤認しない旨の現行 bullet の直後、`稼働エージェント` bullet の前へ、Claude personal 定義と同じ文案を追加します。

意味と判定順を一致させますが、二つの personal 定義には共通 dispatcher がないため、ここだけは各一箇所の意味等価な記載が必要です。

## 変更不要とするファイル

- `.claude/commands/dev-wave.md`
  - 段 1・4・6で既に `DW-G05` を dispatch している。
- `.agents/skills/dev-wave/SKILL.md`
  - `.claude/commands/dev-wave.md` を共通 dispatcher として全文実行する。
- `.agents/skills/rulings/SKILL.md`
  - `.claude/commands/rulings.md` を共通 dispatcher として全文実行する。
- `docs/skill-self-improvement.md`
  - 既存 leaf への統合、全文複製禁止、新節を最後の手段とする規則、commit 境界が既に揃っている。
- 新規 checker、スコア、台帳、`DW-G06`、新しい文書節
  - いずれも追加しない。
- 既存テスト
  - 事前には変更しない。既存検査が具体的な期待値不一致を報告した場合だけ、既存 fixture または pin の該当行を機械的に最小更新する。

## 検査と commit 境界

repo 内変更は `docs/dev-wave/core.md` と `.claude/commands/rulings.md` を同じ docs-only commit に含めます。既存の byte budget または whole-file pin が実際に反応した場合だけ、その既存期待値の更新も同じ commit に含めます。

repo 外の二つの personal 定義は Izanagi の commit に混ぜません。別の personal 設定変更として適用し、Codex `next-tasks` Skill は既存 `quick_validate.py` で検査します。

親が行う検査は次のとおりです。

- repo 差分の対象が予定した 2 ファイルと、検査が要求した既存期待値だけであること
- `git diff --check`
- `python3 tools/check_docs.py`
- `python3 tools/check_codex_agents.py`
- 変更した personal Codex Skillへの `quick_validate.py`
- 4 箇所の文面を再読し、Claude/Codex で許可条件と安全例外が意味等価であること
- 関連 docs/skill tests と受入全走
- repo commit 後の `python3 tools/check_ai_provenance.py`

personal 定義は repo の `git status` や commit に現れないため、repo commit OIDと personal 2ファイルの検査結果を分けて完了報告します。