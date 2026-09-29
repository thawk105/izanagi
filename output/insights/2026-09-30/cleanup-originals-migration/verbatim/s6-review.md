## 総括

**GO。** commit `817d8bd10` の差分と指定の一次資料を静的に照合し、記録の値や所在を誤らせる must-fix は見つからなかった。91 本・11 branch、退避の内訳、archive の 7 組 2,593 file は資料と一致する。撤去前後の時制と、main 非祖先の本数には表現を明確にしたい箇所がある。

## must-fix

なし。

## should-fix

- [集約 insight §3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cleanup-originals-migration/output/insights/2026-09-30/cleanup-originals-migration/README.md:70) の「main の祖先でない木 22 本」は、**退避時に検査した 89 本の内数**と明記したい。退避対象外の `t2853-r2-plot-fix1/fix2` も今回の `git merge-base --is-ancestor … main` では非祖先だった。対象 91 本全体の値として読むと 24 本になる。

## nit

- [集約 insight 冒頭](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cleanup-originals-migration/output/insights/2026-09-30/cleanup-originals-migration/README.md:5) の「撤去した木・branch」は、同文書 §0・§6 が示す land 後の撤去予定より時制が早い。「撤去対象の木・branch」が明確。

## 確かめたこと

`ruling.md`、指定された退避 JSON・archive 照合ログ・対象表・pin 検査・凍結語走査ログ、commit の変更 44 file、spool の共通・両 ledger README を開いた。`targets-final.json` と `trees.tsv` は 91 行（A 80、B 11）で path と退避先が一致。退避 JSON は 89 本（流用 55、新規 34）、新規 tar 29 本・計 631,004 B。bundle は対象 11 branch 中、main 非祖先 10 heads を収録。archive ログは 7 組・2,593 file 一致、欠け 0。追記先 26 README はいずれも元の本文への末尾追記で、凍結物の変更は差分に無い。追記が残すと記す K2 複製、T-2850・T-2868 の job dir 内資料などは実在した。T-2871 の前日 tar は 12 entry で WAL 2 本を含む。

テストは実走していない。撤去後の状態、archive の全 file の独立した再ハッシュ、job dir 内の全 file は検査していない。