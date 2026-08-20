静的判定は、1=refuted、2=real（位置要件のみ）、3=refuted、4=refuted、5=real（テスト品質上の軽微な指摘）です。

1. **refuted**

`_NQSV_GROUP_NAME_RE` は裁定の正規表現と一字一句一致しています。[実装差分:10](/home/SFC/tanab/.claude/jobs/96a60f2f/tmp/dev-wave/impl-diff-dispatch-compute.patch:10)

分岐も `findall(tail) != [DEFAULT_PROJECT]` そのもので、docstring も「submit ID・policy account・必須 field の連言」に更新されています。[実装差分:28](/home/SFC/tanab/.claude/jobs/96a60f2f/tmp/dev-wave/impl-diff-dispatch-compute.patch:28)

2. **real（厳密な挿入位置のみ）**

分岐は `len(request_ids) != 1` の直後ですが、その後に `_normalize_request_id()` と `observed != expected` の一致検査が残っています。したがって「Request ID 検査」を一致判定まで含む意味に取ると、直後ではありません。

既存4フィールド検査の条件・挙動は変更されておらず、差分外の意図しない変更もありません。

修正案：Group Name 分岐を `if observed != expected: return False` の直後、既存の `required`／4フィールド検査の直前へ移動する。

3. **refuted**

実データの相対順序は、`Request ID` → `Group Name` → `Started` → `Ended` → `Elapse` です。[実データ:3](/work/1/SFC/tanab/izanagi/.claude/worktrees/t222-scheduler-group/output/insights/2026-07-30_pegasus-compute-node-dispatch/probe-874129-accounting.txt:3) [実データ:8](/work/1/SFC/tanab/izanagi/.claude/worktrees/t222-scheduler-group/output/insights/2026-07-30_pegasus-compute-node-dispatch/probe-874129-accounting.txt:8)

4ケースは次のとおり、すべて他の必須条件を満たしています。

| ケース | `findall()` 結果 | 単一の reject 理由 |
|---|---|---|
| 不一致 | `[OTHER]` | policy account 不一致 |
| 欠落 | `[]` | Group Name 欠落 |
| 重複 | `[SFC, SFC]` | 1件ではない |
| 混在 | `[SFC, OTHER]` | exact 一致でない |

`Request ID`、Started、Ended、Elapse は各ケースで揃っており、テスト分離も成立しています。

4. **refuted**

正例の `Group Name:             SFC` は実データと同じ空白幅です。`SFC` は1-basedで25列目にあり、`Group Name:` 後は13個の空白です。fixture と正例の位置も Request ID の直後、Started の前で一致しています。[テスト差分:64](/home/SFC/tanab/.claude/jobs/96a60f2f/tmp/dev-wave/impl-diff-test-file.patch:64)

5. **real（非 blocker）**

追加行はテスト対象の現行順序では冗長です。[テスト差分:72](/home/SFC/tanab/.claude/jobs/96a60f2f/tmp/dev-wave/96a60f2f/tmp/dev-wave/impl-diff-test-file.patch:72)

`tail` が通常の連続した末尾領域なら、`Request ID:` が残っている時点で、その後ろにある `Group Name:` も必ず残ります。したがって、既存の `Request ID` assertion と独立した tail 保持検査にはなっていません。

修正案：期待される保持済み suffix 全体（Group Name の値・位置を含む）を比較するか、Group Name の保持可否を独立に変化させられる境界専用 fixture を追加する。独立条件を作れないなら、この assertion は削除してよいです。

## 総括

blocker級はありません。実装条件、実データ順序、4つの拒否ケース、空白幅は妥当です。軽微な指摘は、Group Name 分岐をID一致検査後へ移すことと、tail assertion の冗長性です。