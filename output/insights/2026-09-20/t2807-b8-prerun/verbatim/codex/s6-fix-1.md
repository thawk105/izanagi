## 総括

**制約の衝突により、編集前に停止しました。** 対象 runner は untracked ではなく、次のとおり tracked です。

```text
git ls-files --stage -- probe/verify_phase_runner.py
100644 4352385cd88af03f0d6a714aa50c2845ec737842 0	probe/verify_phase_runner.py
```

依頼の「tracked file を 1 byte も編集しない」と「対象を in-place で v4 へ」が両立しません。ファイルの変更・禁止された git 操作はしていません。

以下の partial は、該当箇所を確認したものの修正には着手していない意味です。行番号は現行 v3 です。

| 所見 | 状態 | 現行の該当行 |
|---|---|---|
| 1. bench 再生成撤去・複数 attempt 拒否 | partial | 884–942、1087–1130 |
| 2. 校正 bench 失敗による pass 阻止 | partial | 1048–1075、1284 |
| 3. 失格の優先評価 | partial | 1052–1075 |
| 4. job 段失敗 record の集計 | partial | 977–983、1172–1185 |
| 5. phase 別 hard timeout | partial | 690、856、919 |
| 6. 校正計画の純関数化 | partial | 864–875、1373–1381、1584–1596 |
| 7. selftest の自己参照・二重理由除去 | partial | 1407–1408、1645–1665 |
| 8. resume の判定集合照合 | partial | 715–722 |
| 9. 新規則の selftest 追加 | partial | 1318–1713 |

- **改版なし：1785 行**
- **SHA-256:** `8a44e23875655d24d515d56b9d334e93b2f7a3b6f8646e85d969060022036ce7`
- **selftest:** 今回は未実走（実行件数 0、要約行なし）。
- **`--help` 6 件:** prerun／calibrate／verify／reverify／summarize／selftest、すべて未実走。
- **その他未実走:** AST 構文確認、build、bench、verifier、計算ノード経路。
- **規則からの逸脱:** 新たな変更なし。現行 v3 の裁定済み問題は未修正です。

**対象 runner だけは tracked 編集禁止の例外として、in-place 修正してよいですか？** 確認が必要なのは、今回の依頼の「制約（必須）」が tracked file の編集を明示的に禁止しているためです。