結論は **NO-GO** です。静的検査と書込みなしの in-memory probe で、RA-1/RB-2 の root cause が残っていることを確認しました。

## 1. 所見対応表

| ID | 深刻度 | 対応 | 根拠 (file:line) |
|---|---|---|---|
| RA-1 | must-fix | partial | 不可視領域除去と exact `["max"]` は実装済みですが、regex は裸の `reasoning=` しか認識しません。[check_docs.py:276](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/check_docs.py:276)、[check_docs.py:3398](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/check_docs.py:3398)。負例も裸の `reasoning=high` に限定されています。[test_check_docs.py:4855](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/orchestrator/tests/test_check_docs.py:4855) |
| RA-2 | must-fix | closed | production 委譲が実装され、S02/S03 の `_run_check()` 統合負例が追加されています。[check_docs.py:3574](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/check_docs.py:3574)、[test_check_docs.py:4886](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/orchestrator/tests/test_check_docs.py:4886)。委譲削除 MR-01 も期待 node で KILLED です。[mutation-ledger.json:42](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t595-reasoning-ab/mutation-ledger.json:42) |
| RA-3 | must-fix | closed | S03 値欠落、両節の重複 max、`max+high` が固定され、判定も `values != ["max"]` です。[check_docs.py:3404](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/check_docs.py:3404)、[test_check_docs.py:4844](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/orchestrator/tests/test_check_docs.py:4844)、[test_check_docs.py:4855](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/orchestrator/tests/test_check_docs.py:4855) |
| RA-4 | should-fix | 不採用 (親裁定) | 親は共通 helper の既存挙動として別 ID 扱いを裁定し、helper は変更されていません。[s6-fix-prompt.txt:77](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t595-reasoning-ab/s6-fix-prompt.txt:77)、[check_docs.py:1685](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/check_docs.py:1685) |
| RB-1 | must-fix | closed | commit 本文は A/B 未実装・未実走、evidence 0、latch のみ、実効 effort 非 attest、成果物評価値不変を明記しています。[commit-msg.txt:17](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t595-reasoning-ab/commit-msg.txt:17)。未発火所見の carry は段4にも保持されています。[s4-ruling.md:66](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t595-reasoning-ab/s4-ruling.md:66) |
| RB-2 | must-fix | partial | RA-1 と同じ未閉鎖 root cause です。実際の起動キーは `model_reasoning_effort=` ですが、検査対象外です。[operations.md:8](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/docs/dev-wave/operations.md:8)、[check_docs.py:276](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/check_docs.py:276) |
| RB-3 | must-fix | closed | production-path 負例と MR-01 により、委譲一行の蒸発は検出されます。[test_check_docs.py:4899](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/orchestrator/tests/test_check_docs.py:4899)、[mutation-ledger.json:52](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t595-reasoning-ab/mutation-ledger.json:52) |
| RB-4 | should-fix | closed | finding は時不変の adoption-pin 文言へ変更され、定数自身とは独立した期待文字列で固定されています。[check_docs.py:266](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/check_docs.py:266)、[test_check_docs.py:4920](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/orchestrator/tests/test_check_docs.py:4920) |
| RB-5 | nit | 不採用 (親裁定) | rc 不変として現状維持の裁定です。[s6-fix-prompt.txt:82](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t595-reasoning-ab/s6-fix-prompt.txt:82)。pin finding と既存 H2 finding の重複は残っています。[check_docs.py:3394](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/check_docs.py:3394)、[check_docs.py:3635](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/check_docs.py:3635) |
| RB-6 | nit | 不採用 (親裁定) | 節別独立性のため定数を分離する親裁定です。[s6-fix-prompt.txt:84](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t595-reasoning-ab/s6-fix-prompt.txt:84)、[check_docs.py:264](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/check_docs.py:264) |

## 2. 冗長層の裏取り

親の「MR-04/MR-06 は fail-open 方向には冗長」という解釈は反証されます。実際の Codex 起動設定は `model_reasoning_effort="<値>"` です。[operations.md:8](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/docs/dev-wave/operations.md:8)

MR-04 単独では次が通ります。

```markdown
`model_reasoning_effort="high"`<!-- `reasoning=max` -->
```

- 実命令の `high` は regex に認識されません。
- `_visible_markdown_text()` を外すと comment 内の `reasoning=max` だけが抽出され、`values == ["max"]`、finding 0 です。
- 現行実装では comment が除去され、`values == []` となり赤です。
- 同じ反例は fence でも成立します。

MR-06 単独では次が通ります。

```markdown
`model_reasoning_effort="high"`
> `reasoning=max`
```

引用除去を外すと引用内の max だけが抽出され、finding 0 です。両変異とも元の節句より短く、25,187/25,200 bytes の予算にも掛かりません。

さらに、現行実装自体にも次の反例があります。

```markdown
`model_reasoning_effort="high"`（例: `reasoning=max`）
```

書込みなし probe では S02/S03 とも finding `[]` でした。59-byte の現行起動句を57-byteの上記へ置換するため、予算も赤になりません。可視の max が「実命令か例示か」を判別せず、実際の起動キーの high を見ないためです。規範的な high 指示を blockquote に置き、非引用側へ max の例示を残す形も通ります。

MR-07/MR-08 の KILLED は、visibility 層と strict 層を同時に壊した既存の裸 `reasoning=high` fixture に対する結果です。[mutation-ledger-round2.json:58](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t595-reasoning-ab/mutation-ledger-round2.json:58)、[mutation-ledger-round2.json:110](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t595-reasoning-ab/mutation-ledger-round2.json:110)。単独 MR-04/MR-06 の SURVIVED を冗長とする根拠にはなりません。[mutation-ledger.json:199](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t595-reasoning-ab/mutation-ledger.json:199)、[mutation-ledger.json:288](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t595-reasoning-ab/mutation-ledger.json:288)

**must-fix:** 値集合ではなく段2/3の規範的な起動句を pin し、実キー high＋comment/fence/引用 max、可視 max 例示 decoy を負例化して、MR-04/MR-06 を単独で kill する必要があります。

**成果物影響:** 放置すると段2/3を実際の起動構文で high にした文書が受理され、敵対レビューの検出力低下を通じて certified 選択・材料レポートの受理集合が広がります。

## 3. 新たな回帰

指定された正当な編集については、通常の節加筆、および現行 max を残した comment・fence・blockquote 内の high 例示は、S02/S03 とも finding 0 でした。不可視化と引用除去が過剰拒否を防いでいます。[check_docs.py:3398](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/check_docs.py:3398)

一方、可視 inline の「禁止例: `reasoning=high`」や indented code の例示は赤になります。これは fix による docs 受理集合の縮小ですが、certified 選択・材料レポート・台帳値は変わらないため、DW-G05 に従い must-fix にはしません。

blockquote は例示にも規範指示にも使えるため、全引用を無条件で除外する現在の扱いは前節の fail-open と不可分です。

## 4. 記録の正直さ

`git log -1 --format=%B` は [commit-msg.txt](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t595-reasoning-ab/commit-msg.txt:1) と一致しました。RB-1 が要求した主要な否定文は17–20行に揃っており、A/B 実装・実走や成果物評価値の前進を主張していません。親実走を実装子実走と混同する記述もありません。

ただし12行目の「2件を fix で塞いだ」は、上記反例を踏まえると root cause の完全閉鎖としては過大です。[commit-msg.txt:12](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t595-reasoning-ab/commit-msg.txt:12)。技術的 must-fix と同時に訂正すべき記録面であり、別 root cause には数えません。

## 総括

残る must-fix は **1件**（RA-1/RB-2 共通の規範起動句・decoy root cause。commit 文言訂正を含む）。  
MR-04/MR-06 は冗長層ではなく、単独で fail-open 反例を構成できます。  
現行実装にも実キー high＋可視 max 例示の受理経路があります。  
したがって commit `cf110ad1` は現状のまま **land 不可**です。