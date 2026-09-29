## 検算結果

**判定は GO（下記の should を修正推奨）です。** README の3つの表を受領証、scheduler 記録、窓 JSONL、summary と照合しました。識別子、時刻、Elapse、行数、hash、件数、窓別最大値、集約値に不一致は見つかりませんでした。

6 窓は各126行で、各窓124 session、248 measurement、62 complete sample、drop 0 です。rep rc は各窓1,240件すべて0、throughput は各窓1,240件すべて有限の正値でした。`evidence_check.py` は実在する `rep_returncodes` と `throughputs` を読んでおり、分離も w1 の最終 `finished_at` から w2 の最初の `started_at` までで計算しています。分離は rr95 **231.75648 h**、rr50 **231.76598 h**、rr5 **231.64046 h** で、README の丸め値と一致します。

summary の各窓62差分の最大値、3つの `upper`、集約の `floor_exact = [436449544102615, 4503599627370496]` も一致しました。372差分中の最大は rr50 w2 の sample index 14、値は **0.09691126658997518** です。「1標本で決まる」は記録された標本最大値という意味で成立します。成果物10本は投入元と wave worktree で bytes が一致します。

w2 と finalize の投入記録は同じ `H` を示し、finalize の投入は最後の w2 終端より後です。成果物 commit `f315186c8` は `H` を親とする10ファイルの commit で、3段終了後に HEAD を進めたという記録は runbook §7.8 と前 wave の申し送りに整合します。fragment の H2、`更新` item、`base:` の形にも違反は見つかりませんでした。HANDOFF は brief を w2 投入後に書いた時刻を明示しており、事前に書いたとは主張していません。静的な読み取り検査のみで、job・pytest は実行していません。

## 総括

**GO。** 数値や受理条件を変える must-fix はありません。

| 番号 | 判定 | 重要度 | 根拠 | 放置時の影響 |
|---|---|---|---|---|
| 1 | real | should | [README.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-pair-w2/output/insights/2026-09-29/t2288-floor-pair-w2/README.md:116) は「D2138 の表から切り出してその順で渡した」と記す。一方、`aggregate.meta` は時刻と rc のみで argv を残さず、集約成果物は渡された3組の**値**を relpath 順で記録する。 | 集約値・hash は変わらないが、期待 spec 列を**どこから取得したか**という README と fragment の手順主張は、指定された一次資料だけでは独立に確認できない。実行 argv の記録を示すか、値の一致を確認したという表現に狭めるとよい。 |
| 2 | real | nit | [README.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-floor-pair-w2/output/insights/2026-09-29/t2288-floor-pair-w2/README.md:22) の `** 採用裁定` は強調記号が閉じていない。 | 値・主張は変わらず、表示だけが崩れうる。 |

**読めなかった資料:** なし。
