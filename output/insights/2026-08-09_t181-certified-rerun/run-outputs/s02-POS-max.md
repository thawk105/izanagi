結論は **NO-GO** です。指定9資料をすべて読了し、D96も同一変更 closure の確認に必要な範囲を読みました。編集・pytest・runner実行はしておらず、緑は主張しません。

## 前回所見の対応表

| 前回所見 | 判定 | fix後の裏取り | 結論 |
|---|---|---|---|
| A-1 `splitlines()` 偽CAB | `closed` | [code:94–137](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/tools/check_ai_provenance.py:94) はbytes I/Oと `split(b"\n")`、strict UTF-8、異常record拒否。[test:403–456](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/orchestrator/tests/test_check_ai_provenance.py:403) はCR/VT/FF/NEL/LS/PSと異常bytes/recordを固定。[policy:17–19](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/docs/ai-provenance.md:17)、[D98:4350–4354](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/docs/decisions.md:4350) と一致。 | bare CR・Unicode separatorによる件数相殺は閉じた。 |
| A-2 cwd `/` とlocal config | `closed` | [code:80–110](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/tools/check_ai_provenance.py:80) はfresh private directory、その子cwd、ceiling、config env遮断。[test:323–363](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/orchestrator/tests/test_check_ai_provenance.py:323) はhostile ancestor repo、呼出ごとの別cwd、同期cleanup後の不存在を固定。[D98:4352–4354](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/docs/decisions.md:4352)。 | ancestor local configは遮断され、`subprocess.run()` 完了後は `proc` の結果だけを使うためcleanup後cwd参照もない。 |
| A-3 / B-1 canonical parserの旧履歴遡及 | `regressed` | legacy AI parserの分離自体は [code:140–148](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/tools/check_ai_provenance.py:140)、[test:276–288](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/orchestrator/tests/test_check_ai_provenance.py:276) で閉じた。しかし [code:174–175](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/tools/check_ai_provenance.py:174) が常にCAB parserを実行し、履歴側も [code:376–382](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/tools/check_ai_provenance.py:376) で後からfindingだけ捨てる。[D98:4354–4362](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/docs/decisions.md:4354) の非遡及宣言と不一致。 | pre-policyでも新しいtemporary/parser failureがrc=2になる新回帰。後述R-1。 |
| A-4 ancestry・rename | `closed` | [code:243–249](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/tools/check_ai_provenance.py:243) は `--full-history --no-renames`。[test:600–764](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/orchestrator/tests/test_check_ai_provenance.py:600) は別lineage、削除、rename-in/out、merge retain/drop、0→2→1、ambient `diff.renames` を固定。[D98:4358–4362](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/docs/decisions.md:4358)。 | 宣言と実コマンド・境界fixtureは一致。 |
| B-2 M1単一理由 | `closed` | [test:291–320](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/orchestrator/tests/test_check_ai_provenance.py:291) はlegacy AI結果を `base=[]` に固定したまま、`--no-divider` の有無でCAB findingの空/非空だけを変える。[code:140–175](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/tools/check_ai_provenance.py:140)、[D98:4350–4356](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/docs/decisions.md:4350)。 | exact文言pinも含むが、変異時はCAB拒否→受理になるため診断だけの赤ではない。 |
| B-3 M2単一理由 | `partial` | hostile localのfixtureは単一aliasで有効。[test:323–363](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/orchestrator/tests/test_check_ai_provenance.py:323)。一方 [test:365–400](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/orchestrator/tests/test_check_ai_provenance.py:365) はsystem/global/envの3 aliasを同時投入する。 | production隔離は正しいが、ambient全透過変異の単一理由controlは未閉鎖。後述R-2。 |
| B-4 独立needle literal | `closed` | 独立literalは [test:16–18](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/orchestrator/tests/test_check_ai_provenance.py:16)、productionとの一致と実policy exact 1件は [test:539–542](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/orchestrator/tests/test_check_ai_provenance.py:539)。実policyは [policy:17–19](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/docs/ai-provenance.md:17)。 | F9型の自己追認は閉じた。 |
| B-5 導入commit自身 | `closed` | epochをsplit CABにするfixtureは [test:64–85](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/orchestrator/tests/test_check_ai_provenance.py:64)、単独range拒否は [test:583–597](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/orchestrator/tests/test_check_ai_provenance.py:583)。[D98:4361–4362](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/docs/decisions.md:4361)。 | off-by-one境界は閉じた。 |
| B-6 fence拒否 | `closed` | backtick/tilde両方を [test:202–227](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/orchestrator/tests/test_check_ai_provenance.py:202) がCAB単独負例として固定。[D98:4344–4348](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/docs/decisions.md:4344)。 | planの字句受理集合と一致。 |

## 新regression候補への攻撃結果

- **pre-policyでのcanonical parser実行: real。** findingを捨てるだけでparser実行は避けていません。例外は [code:391–393](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/tools/check_ai_provenance.py:391) でrc=2になります。
- **fresh ceiling・cleanup・race: refuted。** cwdはceilingの子、処理は同期、cleanup後はcwdを再利用しません。呼出ごとに別directoryであることもテストされています。
- **LF bytes split: refuted。** bare CRおよび全指定Unicode separatorをLFとして扱わず、偽CAB keyを生成しません。
- **full-history/no-renames・needle・導入commit・merge/rename: refuted。** コード、D98、独立literal、各境界fixtureが揃っています。
- **M1: refuted、M2: real/partial。** M1はCAB受理判断が変化します。M2の複合ambient fixtureは診断件数だけが変わる変異を許します。
- **budget/registry/dispatch: refuted。** 現物はread-only計測で **8,832 bytes / 9,000 bytes**。[registry:162–164](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/tools/check_docs.py:162) は独立し、[consumer:1466–1474](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/tools/check_docs.py:1466) に合流、[allowlist:231–233](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/tools/check_docs.py:231) は非拡張です。9,000/9,001境界は [test:417–448](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/orchestrator/tests/test_check_docs.py:417)、D98宣言は [D98:4364–4367](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/docs/decisions.md:4364)。

D96の内容closureは現snapshotに揃っています。新D、policy、実装、provenance境界テスト、budget境界テストが同じ未commit差分にあります。[D96:4271–4279](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/docs/decisions.md:4271)、[D98:4337–4342](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/docs/decisions.md:4337)。ただし全6 tracked fileはまだ未commitなので、「同一commitでland済み・緑確認済み」という履歴上のclosureは未成立です。これは現段階では手続上の残条件であり、独立のコードregressionとは数えません。

## 残存finding

### R-1 — pre-policy履歴もCAB parser失敗へ依存する

- severity: **HIGH / must-fix**
- real/refuted: **real**
- 成果物変化: legacy parserなら受理されるpre-policy commitが、temporary directory作成失敗、canonical parser error、異常record等で **rc=0からrc=2** へ変わります。default/rangeのcommit provenance受理集合を非遡及宣言より狭めます。
- 根拠: `validate_message()` が無条件にCAB parserを呼び、履歴側はその後にepochを調べています。既存pre-policy正例 [test:562–580](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/orchestrator/tests/test_check_ai_provenance.py:562) はparser成功時しか検査していません。
- 最小fix: 履歴loopで `_has_co_authored_by_policy(commit)` を先に決め、適用commitだけCAB parserを呼ぶ。`validate_message(..., check_cab=False)` 等へ分離し、pre-policy rangeでは `_parsed_trailers` を「呼ばれたら例外」にしてもrc=0、post-policyと`--message-file`では同じ例外がrc=2になる境界テストを追加する。

### R-2 — M2 ambient fixtureが過剰決定

- severity: **HIGH / must-fix（mutation証拠）**
- real/refuted: **real**
- 成果物変化: ambient遮断を全面除去する変異では、fixtureのFoo/Bar/Baz三つが同時にCABへ正規化され、`raw=1, parsed=3` のまま拒否し得ます。その場合テストの赤は期待診断 `parsed=0` との差だけで、CAB受理集合は変化しません。一方、実ホストにaliasが一つだけなら同じ回帰は `raw=1, parsed=1` となりsplit CABを誤受理します。現M2をkillと数えると、この受理集合変化を証明したことになりません。
- 最小fix: system/global/`GIT_CONFIG_COUNT`を一fixture一aliasへ分割し、他channelを明示的に消す。各nodeはbase/scope正常を固定し、隔離除去時にCAB findingの非空→空、可能なら`--message-file`のrc=1→0が唯一変わる形にする。hostile local ceiling fixtureは現状の単一alias形を維持する。

## 総括

**NO-GO。残must-fixは2件です。** A-1、A-2、A-4、B-2、B-4、B-5、B-6は、fix後コード・境界テスト・policy・D98の間で静的に閉じています。特にLF byte分割、fresh temporary ceiling、`--full-history --no-renames`、独立needle、導入commit自身、merge/rename、fence、8,832/9,000 byte budget、独立registry、dispatch allowlist非拡張は整合しています。

一方、A-3/B-1はlegacy AI parserの意味論分離だけなら閉じましたが、履歴loopがepoch判定前にCAB parserを必ず実行するため、pre-policy commitまで新しいtemporary/parser失敗でrc=2へ変える回帰が残ります。またB-3はproduction隔離そのものではなく、M2のmutation証拠が三つのaliasを同時投入する過剰決定fixtureであり、診断文言の赤とCAB受理集合の変化を分離できていません。したがって現snapshotを段7へ送るべきではありません。R-1でepoch前実行を除去し、R-2を一channel一aliasの受理集合controlへ分割した後に、focused reviewと親のmutation・受入実走をやり直す必要があります。D96の必要ファイルは同じ未commit差分に揃っていますが、最終fix・境界テスト・D98・policy・budget変更を同一commitに保ち、親が実測した緑を確認するまで履歴上のclosureとは扱えません。