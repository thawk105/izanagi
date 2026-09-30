## 所見

**1. 引用文字列の走査が、コメント中のアポストロフィで後続の参照を見逃す。重大度: must-fix。**
根拠: [scoped_acceptance.py:121](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-scoped-acceptance/tools/scoped_acceptance.py:121) はコメントも含む bytes を連続走査し、閉じない `'` の後では `"` で囲まれた文字列を抽出しない。同じ走査結果を production 分類と test 選択に使う（同ファイル [224 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-scoped-acceptance/tools/scoped_acceptance.py:224)、[276 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-scoped-acceptance/tools/scoped_acceptance.py:276)）。再現入力: tested main の `tools/reader.py` と `orchestrator/tests/test_reader.py` に `# don't`、続けて `PATH = "docs/notes/story.md"` を置き、tip で `docs/notes/story.md` を変更する。両参照が抽出されず、分類は適格、test は未選択となる。**放置時の影響:** production の門入力を変えた tip が、その consumer test を走らせず縮小受領証で land できる。推奨: コメントや不均衡な引用符で参照を落とさない保守的な走査へ直し、この入力を分類・選択・land の回帰例にする。

**2. MS5 の test は祖先 dir 接頭辞を外す変異を殺せない。重大度: nit。**
根拠: [test_scoped_acceptance.py:131](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-scoped-acceptance/orchestrator/tests/test_scoped_acceptance.py:131) の `"docs/notes"` は、接頭辞鍵を消しても残る dir 名鍵 `"notes"` に一致する（[scoped_acceptance.py:111](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-scoped-acceptance/tools/scoped_acceptance.py:111)）。再現入力: MS5 どおり接頭辞鍵だけを削除して同 test を評価すると、その選択 assert は依然成立する。**放置時の影響:** 将来この鍵が欠落しても、汎用名だけから成る祖先 dir を参照する test が縮小集合から漏れ得る。推奨: `docs/spool/worklog/entry.md` と引用文字列 `"docs/spool/worklog"` の組で単一理由の test を置く。

**3. MS6 の land test は再導出の有無を試せていない。重大度: nit。**
根拠: [test_scoped_acceptance_land.py:98](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-scoped-acceptance/orchestrator/tests/test_scoped_acceptance_land.py:98) は `tools/changed.py` を混ぜて `plan` を差し替えるが、land は再導出より先に独立した `tools/` 差分検査で拒否する（[dev_wave_land.py:1233](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-scoped-acceptance/tools/dev_wave_land.py:1233)）。再現入力: MS6 として lock 内 `plan` 再導出・照合を除去しても、この tip は先行検査で拒否される。**放置時の影響:** 再導出が後に欠落すると、許可 docs tip の偽の分類・選択を land が信じ、縮小受理集合が広がり得る。推奨: `tools/` 差分のない適格 tip で受領証の選択を偽装し、再導出だけが拒否理由となる test を足す。

**4. MS9 の v5 取り違え test も独立条件で拒否される。重大度: nit。**
根拠: [test_scoped_acceptance_land.py:125](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-scoped-acceptance/orchestrator/tests/test_scoped_acceptance_land.py:125) は schema 名だけを v5 に変え、authority kind を scoped のまま残す。v5 は field 検査の後にも authority kind を検査する（[dev_wave_land.py:1026](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-scoped-acceptance/tools/dev_wave_land.py:1026)）。再現入力: MS9 の「v5 に scoped field を許す」変異だけを入れても、同 test は authority kind 不一致で拒否される。**放置時の影響:** v5 の exact field 検査が緩んでも、この test は検知せず v5 の受理集合拡大を見逃し得る。推奨: authority kind などを正しい v5 値に揃え、余分な scoped field だけで拒否される入力にする。

## 変異の実効性

静的判定では、MS1・MS2・MS4・MS7 は対象条件を直接 assert している。MS3 は mode・削除・symlink・gitlink を扱うが、T status の独立例はない。MS5・MS6・MS9 は上記の先行または重複条件により、登録された意味での kill にならない。MS8 は直接 gate 非 0 の test があるものの、rc 検査を外した後に runner まで緑で進む入力かは静的には確定できない。[failures.md の F28](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-scoped-acceptance/docs/failures.md:1172) にある「恒真ゲート」「テスト代表性」と同型の懸念である。

## 総括

**must-fix は引用文字列走査の見逃し 1 件。** これにより、門入力を変更した docs tip が縮小受入で main に入り得る。レビューは指定どおり静的検査のみで、テスト・実走はしていない。