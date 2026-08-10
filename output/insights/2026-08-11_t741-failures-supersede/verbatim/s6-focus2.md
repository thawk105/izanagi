## must-fix の判定

**closed**

- 行頭空白0〜3個とmarker直後のspace/tabを検出する正規表現になっている。[tools/spool_fold.py:62](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:62)
- 指定5種のゼロ幅文字を行全体から除去した後に判定している。[tools/spool_fold.py:65](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:65)、[tools/spool_fold.py:779](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:779)
- HTML commentは空文字投影が維持され、その投影結果へ新しい判定を適用している。[tools/spool_fold.py:372](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:372)、[tools/spool_fold.py:775](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:775)
- 空白1・2・3個、marker後tab、ゼロ幅5種、HTML comment分割が拒否期待に固定されている。[test_spool_fold.py:1367](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/orchestrator/tests/test_spool_fold.py:1367)

## 負制御の判定

4件とも**受理維持**。

- fence内decoy: fence中の行を空投影する制御が維持され、受理期待もある。[tools/spool_fold.py:430](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:430)、[test_spool_fold.py:1397](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/orchestrator/tests/test_spool_fold.py:1397)
- 行頭空白4個以上: 正規表現が最大3個に限定され、4個の正例をvalidateとfoldの両方で確認する構造。[tools/spool_fold.py:63](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:63)、[test_spool_fold.py:1408](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/orchestrator/tests/test_spool_fold.py:1408)
- 全角`ｓｕｐｅｒｓｅｄｅ`: ASCII literalに一致せず、受理期待あり。[test_spool_fold.py:1410](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/orchestrator/tests/test_spool_fold.py:1410)
- 通常prose中の言及: 行頭reserved prefixではなく、受理・挿入維持を確認する期待になっている。[test_spool_fold.py:1411](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/orchestrator/tests/test_spool_fold.py:1411)、[test_spool_fold.py:1417](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/orchestrator/tests/test_spool_fold.py:1417)

## 回帰の有無

**F0・F1・F3・F4の回帰は見つからない。恒真化も見つからない。**

fix 2のproduction差分はR4用定数追加と判定置換だけである。[s6-fix2.log:2529](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t741-failures-supersede/s6-fix2.log:2529)

- `FAILURE_SUPERSEDE_ITEM_RE`は維持。[tools/spool_fold.py:57](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:57)
- 挿入位置は最終非空行直後のまま。[tools/spool_fold.py:1738](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:1738)、[tools/spool_fold.py:1770](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:1770)
- recurrence→supersedeの順序は維持。[tools/spool_fold.py:2053](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:2053)
- topology検査は維持。[tools/spool_fold.py:1777](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:1777)、[tools/spool_fold.py:2077](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:2077)
- 行区切り禁止集合とLF-only分割は維持。[tools/spool_fold.py:68](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:68)、[tools/spool_fold.py:795](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:795)、[tools/spool_fold.py:1663](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:1663)
- F4の3境界前提assertも残っている。[test_spool_fold.py:1550](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/orchestrator/tests/test_spool_fold.py:1550)、[test_spool_fold.py:1565](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/orchestrator/tests/test_spool_fold.py:1565)、[test_spool_fold.py:1580](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/orchestrator/tests/test_spool_fold.py:1580)

`git diff`上、対象trackedテスト3ファイルは追加のみで削除0行。skip/xfail追加もない。fix 2が変更したのは本waveで新設済みのR4テストだけである。[s6-fix2.log:2476](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t741-failures-supersede/s6-fix2.log:2476)

追加テストはproductionの正規表現や変換表を参照せず、具体的入力とissue code、受理後bytesを独立に検査しており、実装の写経にはなっていない。[test_spool_fold.py:1367](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/orchestrator/tests/test_spool_fold.py:1367)、[test_spool_fold.py:1393](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/orchestrator/tests/test_spool_fold.py:1393)、[test_spool_fold.py:1417](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/orchestrator/tests/test_spool_fold.py:1417)

## 残る迂回

**must-fix: HTML文字参照によるASCIIラベル偽装が残る。**

例:

```markdown
- **super&#x73;ede: 2026-08-10** — 誤用
```

Markdown表示では文字参照が`supersede`へ復号されるが、現在の投影はHTML comment除去と指定5コードポイントの除去だけで、文字参照を復号しない。[tools/spool_fold.py:775](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:775) そのため正規表現に一致せず、recurrence payloadとしてそのまま抽出・挿入される。[tools/spool_fold.py:1689](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:1689)、[tools/spool_fold.py:1705](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:1705)

成果物影響は、canonical failuresへ表示上同一のsupersede行を`再発`経路で混入でき、R4の意味分類を迂回すること。reserved prefixの投影だけを文字参照復号する是正ならR4内であり、裁定Eを超えない。

## GO / NO-GO

**NO-GO**

1回目NO-GOで指定された3経路とHTML comment経路は閉じたが、同じR4分類を迂回するHTML文字参照経路が残る。

## 総括

fix 2の指定修正、4件の負制御、F0・F1・F3・F4、trackedテスト保護、恒真化はいずれもコード読解上問題なし。ただし表示上同一の予約ラベルを文字参照で偽装できるため、land前にもう1点塞ぐ必要がある。pytestは実行しておらず、緑は主張しない。