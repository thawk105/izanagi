## 対応表

| ID | 判定 | 根拠 |
|---|---|---|
| S1 | closed | [repo README:17](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-repro-rest/output/insights/2026-09-27/t2853-repro-rest/README.md:17)–18 と同:89 は、調査結果を glue v3・投入 script・投入台帳の3箇所に限定し、他の保存経路の不在は主張していない。[保存先 README:7](/work/1/SFC/tanab/izanagi-repro-archive/t2853-20260927/README.md:7) も同じ範囲。 |
| N1 | closed | 1巡目で残った §0 の「試走 v2 は trace 保全を指定していない」は、[repo README:17](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-repro-rest/output/insights/2026-09-27/t2853-repro-rest/README.md:17)–18 で限定された記述に修正された。 |
| M1 | closed（regression なし） | [repo README:25](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-repro-rest/output/insights/2026-09-27/t2853-repro-rest/README.md:25)、同:119–126、150–160 は、試算による「不要」を暫定とし、投入単位の全 job で再判定すると記す。 |
| M2 | closed（regression なし） | [repo README:25](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-repro-rest/output/insights/2026-09-27/t2853-repro-rest/README.md:25)、同:122、155、160 は正典の試算 **8.88〜9.83** と、floor を除く標本だけの参考値 **4.18〜4.62** を区別している。 |

glue v3、[投入 script:27](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2850-trace-concurrent-verify/trial-v2/submit_all.py:27)–38、[投入台帳:1](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2850-trace-concurrent-verify/trial-v2/jobs-trial-v2.jsonl:1)–18 では `TRACE_ARCHIVE` の指定を検出しなかった。[archive 全体の README:18](/work/1/SFC/tanab/izanagi-repro-archive/README.md:18) も今回の写しに trace を含まないとの記述にとどまる。3文書を通して、T-2850 の未調査の保存経路や複製まで否定する断定は見つからなかった。

## 新規所見

なし。

## 総括

GO。指定資料と3文書の静的照合では、S1・N1 は closed、M1・M2 の再発や修正による新たな矛盾は見つからなかった。書き込みは行っていない。