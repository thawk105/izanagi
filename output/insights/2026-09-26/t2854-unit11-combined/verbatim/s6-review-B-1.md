## 所見表

| 優先度 | 所見 | 放置時の影響・最小修正 |
|---|---|---|
| must-fix | 該当なし | 静的検査で、合否や kill 判定を誤らせる確定的な欠陥は見つからなかった。 |
| should | **real:** [run_probe.py](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/probe/run_probe.py:714) は C4 の `passed` が偽でも、集約結果の `result_name` を `structure+witness+content pass` と記録する。 | C4 不合格の成果物にも「pass」が残る。両 run が合格した場合だけこの表示名を付け、失敗時は `fail` にする。合否そのものは `passed` により落ちる。 |
| nit | **real:** [run_probe.py](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/probe/run_probe.py:37) と [同ファイル](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/probe/run_probe.py:483) に、削除された D1/M2 用の `DIAG_MARKER` 計数が残る。 | 各 run の JSON に今回の判定で使わない値が増える。定数と stderr 計数を削除する。受理集合と kill 判定は変わらない。 |
| nit | **real:** [selftest.py](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/probe/selftest.py:1) の説明は旧「stage six」のまま。 | 自己試験の対象を読み違えやすい。単位 11 の 4 変異を指す説明に直す。判定値は変わらない。 |

## 不成立の攻撃

- **C0 の弱化は不成立。** [run_probe.py](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/probe/run_probe.py:231) は C→C1′→C3→C2′ の各親と、各段および C→C2′ の raw diff を照合し、[同ファイル](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/probe/run_probe.py:246) で C と C2′ の抽出 file 集合・blob も照合する。
- **C1、C3、C5 の弱化は不成立。** C1 は両木の 12 source／21 entry の集合を厳密照合し、21 件を比較する。C3 は指定の 4 binary を対象とする。C5 は各 protocol と C2′ source を `--protocol`、`--ccbench-root` に渡す。参照した CMake 宣言も両 protocol に対象 workload を含む。
- **4 変異の「別層が先に落とす」「等価になる」攻撃は、静的には不成立。** [spec](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/spec/mutation-spec.json:5) の各 anchor は親の [照合ログ](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/check_anchors.log:1) で C2′ 実 bytes 中 1 回と確認済み。H-set は両側の先頭 `schema`、H-line は TPC-C 9 件と他 12 件、S-table／M-type はそれぞれ単独の content 理由を kill 条件にしている。ただし**期待どおりの理由で実際に落ちることは、未走行のため未確定**。
- **見積りと「superproject の実装面差分ゼロ」の誤りは確認できなかった。** [裁定](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/s4-ruling.md:73) の node 時間は見積りであり、この拡張版の実測値ではない。確認した superproject の `git status --short` は空だった。

## 判定

**GO（静的レビュー）。** C4 の表示名は実走前に修正を推奨する。最終的な合格と 4 件の kill は、親の計算ノード実走結果で判定する。

## 総括

起点の主要な照合条件が消えた箇所は見つからなかった。確定した問題は、C4 失敗時にも「pass」と記録する表示の矛盾と、旧変異用の不要な診断項目である。