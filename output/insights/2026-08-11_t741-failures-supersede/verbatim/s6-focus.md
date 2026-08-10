## F0〜F4 対応表

| 所見 | 判定 | 根拠 |
|---|---|---|
| F0 | **closed** | 挿入位置は対象 entry の最終非空行の LF 直後から算出され、payload は挿入行と LF のみになっている。[spool_fold.py:1731](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:1731)、[spool_fold.py:1763](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:1763)。空行なし・空行1行・EOF の byte-exact テストは [test_spool_fold.py:1533](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/orchestrator/tests/test_spool_fold.py:1533)、[test_spool_fold.py:1546](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/orchestrator/tests/test_spool_fold.py:1546)、[test_spool_fold.py:1561](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/orchestrator/tests/test_spool_fold.py:1561)。既存 bytes を削除・並べ替えない。 |
| F1 | **closed** | expected は追加 entry の先頭行から追加順に構成し、allocation 多重集合との一致も検査する。[spool_fold.py:2049](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:2049)、[spool_fold.py:2065](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:2065)、[spool_fold.py:1776](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:1776)。採番用 `symbols` sort は従来の `(wave, namespace, seq, offset, path)` のまま。[spool_fold.py:999](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:999)。逆順正例は [test_spool_fold.py:1467](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/orchestrator/tests/test_spool_fold.py:1467)。entry 本文途中の偽見出しも `actual` にだけ増えるため [spool_fold.py:1777](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:1777) で拒否され、強度は落ちていない。 |
| F2 | **partial** | HTML comment は空文字投影される。[spool_fold.py:366](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:366)、[spool_fold.py:447](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:447)。ラベル内部・前後の comment 拒否と fence 内 decoy 受理も固定済み。[test_spool_fold.py:1364](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/orchestrator/tests/test_spool_fold.py:1364)。ただし最終判定が raw な `visible.startswith("- **supersede:")` のため、下記の Markdown-equivalent な迂回が残る。[spool_fold.py:773](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:773)。 |
| F3 | **closed** | validate と fold はともに LF-only `split("\n")`。[spool_fold.py:788](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:788)、[spool_fold.py:1655](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:1655)。指定6文字は [spool_fold.py:62](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:62) で拒否され、拒否テストと通常 Unicode の byte-exact 保存テストは [test_spool_fold.py:1261](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/orchestrator/tests/test_spool_fold.py:1261)、[test_spool_fold.py:1277](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/orchestrator/tests/test_spool_fold.py:1277)。 |
| F4 | **closed** | 3テストとも fold 前に境界前提を assert する。空行なしは [test_spool_fold.py:1536](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/orchestrator/tests/test_spool_fold.py:1536)、空行1行は [test_spool_fold.py:1551](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/orchestrator/tests/test_spool_fold.py:1551)、EOF は [test_spool_fold.py:1565](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/orchestrator/tests/test_spool_fold.py:1565)。 |

私は pytest を実行していない。実行面は所与の「supersede/topology 29 passed」と「焦点3ファイル 556 passed / 既知の偽赤1件」に依拠した。

## 新規所見

### R4 の Markdown-equivalent prefix 迂回が残る

- **real / must-fix**
- 根拠: comment 除去後も検査は文字列先頭の完全一致だけである。[spool_fold.py:769](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:769)、[spool_fold.py:773](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:773)。再発 payload はそのまま抽出・挿入される。[spool_fold.py:1672](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:1672)、[spool_fold.py:1703](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:1703)。
- 残る例:
  - `  - **supersede: ...` — 1〜3文字の先行空白を持つ Markdown list item
  - `-\t**supersede: ...` — list marker 後を tab にした item
  - `- **super\u200bsede: ...` — ラベル内部のゼロ幅文字
- 成果物影響: canonical failures に見た目・Markdown上は supersede である行を「再発」として挿入でき、B2/R4 の意味分類迂回が残る。
- テストの不足箇所: 現在の negative cases は裸のprefixとHTML commentだけで、上記を含まない。[test_spool_fold.py:1367](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/orchestrator/tests/test_spool_fold.py:1367)。

全角 `ｓｕｐｅｒｓｅｄｅ` は ASCII の予約ラベルそのものではないため、現行R4の拒否対象とは判定しない。これまで拒否すると、R4以外の受理集合を維持する裁定E [s4-ruling.md:170](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t741-failures-supersede/s4-ruling.md:170) を越える。行頭tabも Markdown code block となる形は fence相当の decoyであり、拒否対象に広げるべきではない。

F3の禁止文字追加は裁定Eの範囲内と判定する。supersede は本waveの新規受理面であり、R2の1物理行契約に対する明示化である。またCRは元から file-level で拒否されている。[spool_fold.py:286](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:286)。既存の `新規`・`再発` の受理集合を追加縮小していない。

`git diff` 上、既存 tracked テストの削除・skip・期待値変更はない。段5 snapshotとの比較でも、fixが変更した期待値は段5で新設されたF0 byte-exactテストだけだった。fix追加テストに恒真化は見つからない。ただしF2は恒真ではなく、攻撃集合の不足である。

## 変異 M1〜M10 の生存判定

実走ではなくコード読解上の判定。

| 変異 | 判定 | kill 根拠 |
|---|---|---|
| M1 | **KILLED見込み** | list markerを含むbyte-exact比較。[test_spool_fold.py:1093](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/orchestrator/tests/test_spool_fold.py:1093) |
| M2 | **KILLED見込み** | F196/F197間へのexact splice。[test_spool_fold.py:1546](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/orchestrator/tests/test_spool_fold.py:1546) |
| M3 | **KILLED見込み** | EOF末尾LF後へのexact splice。[test_spool_fold.py:1561](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/orchestrator/tests/test_spool_fold.py:1561) |
| M4 | **KILLED見込み** | recurrence→supersedeの行順を固定。[test_spool_fold.py:1108](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/orchestrator/tests/test_spool_fold.py:1108) |
| M5 | **KILLED見込み** | substringである新行を受理する正例。[test_spool_fold.py:1353](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/orchestrator/tests/test_spool_fold.py:1353) |
| M6 | **KILLED見込み** | 不正暦日の拒否。[test_spool_fold.py:1239](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/orchestrator/tests/test_spool_fold.py:1239) |
| M7 | **KILLED見込み** | parserを迂回して注入した偽見出しをtopologyで拒否。[test_spool_fold.py:1408](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/orchestrator/tests/test_spool_fold.py:1408) |
| M8 | **KILLED見込み** | gate全体を無効化すれば裸の誤用caseが通るため赤になる。[test_spool_fold.py:1367](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/orchestrator/tests/test_spool_fold.py:1367)。ただし上記の別形態は生存。 |
| M9 | **KILLED見込み** | byte-exactとtopologyの冗長gate。[test_spool_fold.py:1093](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/orchestrator/tests/test_spool_fold.py:1093)、[test_spool_fold.py:1425](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/orchestrator/tests/test_spool_fold.py:1425) |
| M10 | **KILLED見込み** | supersede単独fragmentの正例。[test_spool_fold.py:1093](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/orchestrator/tests/test_spool_fold.py:1093) |

## GO / NO-GO

**NO-GO**

残る must-fix:

- R4判定を、HTML comment除去だけでなくMarkdown上同等の list prefixについて閉じる。
- 少なくとも「1〜3文字の先行空白」「marker後tab」「予約ラベル内部のゼロ幅文字」の拒否テストと、code fence・全角別語・通常proseを受理する負制御を追加する。

## 総括

F0・F1・F3・F4は閉じており、fixによる既存テスト期待値の改変、topology強度低下、通常Unicode本文のbyte欠落、恒真テストは見つからなかった。F2のHTML comment経路自体は閉じたが、同じ意味分類を迂回できるMarkdown/Unicode表記が残るため、現状のままlandは不可。