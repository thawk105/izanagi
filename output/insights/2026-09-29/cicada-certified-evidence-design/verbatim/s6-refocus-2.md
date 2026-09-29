## 対応表

| 所見 | 判定 | 根拠 |
|---|---|---|
| R1 | **closed** | B の主案は版の外の事象台帳で、終了時に版を再参照しない。世代番号方式は実装時に選ぶ代替案として分離された（`README.md:60`、`decisions/2026-09-29-dev-wave-cicada-certified-evidence-design-2.md:12`）。段 4 裁定 `s4-ruling.md:10,22` と整合する。 |
| R2 | **partial** | M の read 側、A の read・write 両側は必須と明記された（`README.md:64-69,147`）。ただし read 側の照合は件数一致だけで、呼び出しと登録の対応を保証しない。下記 F1。 |
| R3 | **closed** | 主張を観測した読みの 1SR に限定し、版選択規則への適合を検査しないと明記された（`README.md:45-54,160`、`decisions/2026-09-29-dev-wave-cicada-certified-evidence-design-2.md:13`）。 |
| R4 | **closed** | B・U それぞれの壊し方、違反件数の増加、異常終了の除外が完了条件に入った（`README.md:175-179`）。 |
| R5 | **closed** | trace の byte にディレクトリ分を明記し、計算時間を 0.22〜0.36 node 時間に統一した（`README.md:116-119,131`、`worklog/2026-09-29-dev-wave-cicada-certified-evidence-design-1.md:26`）。 |
| N1 | **closed** | 母集団は `read_internal` と独立した公開 `read()` の成功呼び出し全部になった（`README.md:69`、`decisions/2026-09-29-dev-wave-cicada-certified-evidence-design-2.md:12`）。現行コードでは再読・read-own-write が `read_internal` の手前で分岐し、それ以外の成功 read が同関数へ進む（`external/ccbench/cc/cicada/transaction.cc:156-189`）。迂回した成功 read も母集団に入る。 |
| N2 | **closed** | worklog の旧見積りも 0.22〜0.36 node 時間へ更新された（`worklog/2026-09-29-dev-wave-cicada-certified-evidence-design-1.md:26`）。 |
| N3 | **partial** | 代替案は読解上の「見込み」となり、再確認が採用条件になった（`README.md:60,100`、`decisions/2026-09-29-dev-wave-cicada-certified-evidence-design-2.md:15`）。一方、確認済み事項には「走行中に版 object が解放されないこと」と断定が残り（`README.md:194`）、陰性結果という限定（`README.md:206`）と食い違う。decisions の「この範囲でだけ成り立つ」も見込みより強い（同 fragment `:12`）。 |

## 新しい所見

- **F1｜must-fix｜read 側の件数一致では双方向照合にならない。** `README.md:69` は外部 read 件数と新規 read set 登録件数を比べるが、成功 read A の登録漏れと別の余分な登録 B が同じ tx にあれば一致する。また外部 read が返した body と、対応する登録版との一致も規定していない。これでは `README.md:47` の「reads-from が忠実」という前提を確保できない。各成功 read の key・返却 body・対応する read set 要素を呼び出し単位で照合し、余分な登録も拒否する設計へ直す。decisions fragment `:12` の「双方向照合」も同じ条件に揃える。

- **F2｜should｜scan への拡張を断定しすぎている。** `README.md:69` は `scan()` も同じ形で数えるとするが、現行 `scan()` は一呼び出しで複数の body と read set 要素を返し得る（`external/ccbench/cc/cicada/transaction.cc:429-460`）。`README.md:97,205` では scan を対象外としている。将来の案と明示し、照合単位は呼び出しではなく返却要素ごとに別途設計すると記す。

## 総括

**NO-GO。** N1 の母集団は修正されたが、F1 のため R2 の双方向照合は未完成。N3 の断定と F2 の拡張記述も揃える必要がある。