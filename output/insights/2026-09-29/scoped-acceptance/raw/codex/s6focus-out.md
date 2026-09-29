## 対応表

判定は指定 commit の静的検査による。修正後のテスト結果を示すものではない。

| 対象 | 判定 | 根拠 |
|---|---|---|
| r1#1 引用文字列走査の見逃し | closed | 分類・選択とも blob 全体の bytes 部分文字列照合に変更。`don't` の回帰例も追加。 |
| r1#2 MS5 の単一理由性 | partial | 裁定後の「dir 鍵の層を丸ごと外す」変異には対応。元の「祖先 path 鍵だけを外す」変異を独立に検出する保証はない。 |
| r1#3 MS6 の再導出 test | partial | 適格 tip で偽装した選択を拒否する例を追加。ただし land は lock 前にも同じ検証を行うため、この例だけでは **lock 内**再導出を検証したとは言えない。 |
| r1#4 MS9 の v5 test | closed | 正しい v5 authority と field 集合から、余分な scoped field だけを加える例に変更。 |
| r1 の T status | closed | blob→symlink の型変更を拒否する独立例を追加。 |
| r2#1 `README.md` 等の過剰除外 | partial | 汎用 basename と入れ物 dir の鍵を削り、実在 10 件中 5 件が縮小可になった。一方、後述の見逃しを生む。 |
| r2#2 固定集合の大きさ | partial | 集合は維持。所要時間の比較資料は指定資料にない。 |
| r2#3 合成 repo 構築の費用 | partial | 構築は残る。全受入への時間寄与は未測定。 |
| 焦点走 1：`test_dev_wave_land.py` の 4 件 | closed | いずれも追加 `scoped=` 引数による TypeError。関数と v5 呼び出しが元の 3 引数に戻った。**再実走は未確認。** |
| 焦点走 1：`test_p3_b4_wiring_probe.py` の 1 件 | partial | 赤の原因は作業木に残った `docs/dev-wave/core.md` と decision fragment。fix1 のコード変更はこの原因に対応していない。 |
| 親の実測：実在 land 0/10 → 5/10 | partial | 5/10 は原データと一致するが、全受入に倒れる 5 件と新しい見逃し条件が残る。 |

## 新たな所見

**門入力と consumer test をともに見逃す入力がある。** 例えば `output/insights/2026-10-01/README.md` の追加・変更では、鍵は実質 full path だけになる。[`_keys()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-scoped-acceptance/tools/scoped_acceptance.py:108) は `README.md` を除き、日付までの祖先 dir も鍵にしない。production reader が `Path("output/insights")` の下を列挙して各日の `README.md` を読む場合、本文に full path は現れず、分類は適格になり得る。同じ形の `test_reader.py` も、full path と引用形の単独 `"insights"` を持たなければ [選択条件](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-scoped-acceptance/tools/scoped_acceptance.py:258)から漏れる。直接 gate の `check_docs.py` が列挙する insight placeholder は直下の `*.md` であり、この階層の README の意味検査を代替しない。これは**構成可能な反例**であり、指定資料だけから既存の特定 reader による実害までは立証していない。

同種の境界は `docs/spool/*` にもある。fragment の鍵は full path と basename だけなので、入れ物 dir を列挙する consumer test は basename を書かなければ選ばれない。fold と直接 gate が検査する性質には防壁があるが、その consumer 固有の意味検査まで覆うとは言えない。[MF3 の正例](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-scoped-acceptance/orchestrator/tests/test_scoped_acceptance.py:202)は適格性だけを確かめている。

汎用語除外も境界を広げる。たとえば許可される `docs/worklog/entry.md` を `Path("docs") / "worklog"` から読む場合、basename を参照しない reader では `worklog` が汎用語として落ち、連結された祖先 path も本文にない。blob 全体の部分文字列照合は、**生成された鍵が本文にない**場合を救えない。逆にコメント中の偶然一致による全受入は増えるが、これは受理を狭める方向である。

## 検算

[`classify-fix1.txt`](/work/1/SFC/tanab/tmp/scoped-acceptance-2026-09-29/probe/classify-fix1.txt) の 10 行は `True` が **5 件**、`False` が **5 件**。`True` 行の選択 file 数は **13、8、8、13、8**、node 数は **142、148、149、149、149**。したがって「8〜13 file」は正確で、「約 149 node」は概数として妥当だが、範囲は **142〜149 node** である。

`False` 5 件の理由は、先頭 2 件が `missing inventory` と除外対象の `docs/archive`、3 件目が `docs/archive`、4 件目が `docs/archive` と `docs/failures.md`、最後が許可外の `.log` に加えて `docs/phase3.md` と insight への production 参照である。記録された理由に照らす限り、これらを全受入に倒す判断は妥当である。

land の v5 経路は、[`d26ee8605..b58ee226a` の差分](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-scoped-acceptance/tools/dev_wave_land.py:904)で確認した。`_verify_forward_main_runner_blob` は元の **3 引数**で、v5 の 2 呼び出しも 3 引数。scoped 用比較は別関数へ分離された。v5 の共通検証本体は維持され、v5 schema に余分な scoped field を与えても exact field 検査で拒否する。静的差分上、v5 の検査が緩んだ箇所は見つからなかった。

## 総括

fix1 は焦点走の TypeError と引用走査の見逃しをコード上で解消し、実在 10 件中 5 件を縮小可にした。ただし **汎用 basename・入れ物 dir を除いたことで、列挙型 reader の門入力と test を同時に見逃す入力が残る**。lock 内再導出のテスト代表性、固定集合と合成 repo の所要も未決である。今回は指定どおり静的検査のみ行い、テストは実行していない。