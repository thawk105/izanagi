# 逐語の可逆正規化

git diff --checkに抵触した行末のASCII spaceだけを削除した。可視文字は不変。
復元は下表の1始まり行番号の改行直前へASCII spaceを2個戻す。行数は不変。
原文は回収jobのrecovered-insight/verbatimにもbyte同一で保全している。

| file | 行 | 原文byte数 | 原文SHA-256 |
|---|---|---:|---|
| s2-plan.md | 243、244、245 | 34208 | 93ed8f9854cc14e37fcb85da185c020a3cc7f3a10accf67c1f7592df7d79dd4c |
| s6-reviewB.md | 40 | 15959 | 9b3282913a0ecea73396dd93088c36448014e3881cdc0972e859956388c5311f |

`../evidence/recovery-focus-1.log`は14、65行の改行直前からASCII spaceを1個だけ除去した。
復元は両行へspaceを1個戻す。原文9342byte、SHA-256は
`354256b6acf911f33dd12ed13468d1c85f481d51b668230faa0dc7c8bd426a79`。
原文は回収jobの`focus-1.log`に保存している。
