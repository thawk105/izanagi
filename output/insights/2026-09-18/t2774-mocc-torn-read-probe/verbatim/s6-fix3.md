## 総括

[probe/t2774_probe.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2774-unit2-probe/probe/t2774_probe.py) を修正しました（704 行、untracked）。

| 仕様 | 判定 | 結果 |
|---|---|---|
| 1 | closed | rc／verdict／certified／serializable／cycles の整合条件を是正。aggregate counters 検査を維持 |
| 2 | closed | `summarize --reclassify` を追加。元 JSON は変更せず、`inputs` に再分類フラグと status 変更一覧を記録 |
| 3 | closed | 回帰例を追加。既存 12 例の期待値を維持 |
| 4 | closed | 指定コマンドを実行。Q4 の `p058-plain` 走 1 が **failure → indeterminate** |

検証結果：

- `selftest: PASS 13/13 cases`
- `ast.parse: PASS`
- timeout・error・空 trace・矛盾・成果物欠落の検査：PASS
- 従来 summarize：B2 の両 arm とも N/m/k = 14/14/0

[Q4 再集計結果](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2774-unit2-probe/scratch/fix3/q4-reclass.json)では、50 走中 17 走が `failure → indeterminate` になりました。

SHA256：
`2e2ddea834f782abb7a671b42d8a57f82ac8b82d7ac90d23965ad3ca3fd41c00`

書込みは runner と自分の scratch のみ。所有外への変更は無し。`run`・build・benchmark・patch dry-run は今回未実行です。tracked file、patch、arms-q2.json、実走成果物は変更していません。禁止された Git 操作も実行していません。
