実装を停止しました。指定の 2 ファイルは変更しておらず、commit もありません。

既存テスト [`test_octopus_with_multiple_trusted_parents_rejects_signature_visible_only_from_untrusted_parent`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_git_state.py:725) が補遺と矛盾します。

このテストの graph は次の形です。

- `first_trusted` は `cutoff` の祖先。
- merge の parents は `(first_trusted, cutoff, untrusted)`。
- したがって `T = {first_trusted, cutoff}`。
- 極大元は `cutoff` だけ。
- merge tree は `cutoff^{tree}` そのものなので `diff(cutoff, merge) = ∅`。
- pending fragment もないため、補遺どおりなら受理されます。
- しかし既存期待値は `landed-fold-owned-path` による拒否です。

つまり、補遺の「一意な極大元との差分だけ」を実装すると、この既存テストは必ず赤になります。期待値変更も、仕様外の例外分岐追加も禁止されているため、指示どおり無変更で停止しました。

意図された分岐の疑似コードは以下です。

```text
if parent数 < 2:
    commit全体を走査
else:
    diff_parents = 全parents
    if cutoffあり:
        T = cutoffの祖先であるparents
        if Tに一意な極大元Pがある:
            diff_parents = [P]
    diff(parent, commit) を diff_parents について走査
```

線形候補選択＋検証なら、`p = parent数`, `t = |T|` として `_is_ancestor` は最悪  
`p + 2(t - 1) <= 3p - 2` 回です。

実測例では `T={ea6ca43, e805d69}`、かつ `ea6ca43` は `e805d69` の祖先なので、極大元は `e805d69`。意図された実装なら `diff(e805d69, 4c17674)` だけを調べるため、main 取り込み由来の旧 fold 署名は現れず受理されます。

新設テストは 0 件です。pytest は Pegasus ログインノード規律により未実走です。

## 総括

- 必読 4 点を確認済み。
- 既存テストと補遺の論理矛盾を検出。
- 指示に従い実装・テスト追加を停止。
- 編集・commit ともになし。
- テストは未実走。