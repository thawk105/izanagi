## 変異 M0〜M11 の帰属

以下は静的検算であり、変異・pytest の再実行結果ではない。パスは repo root 基準。

| 変異 | 現物 anchor | 名指し killer の赤化箇所 |
|---|---|---|
| M0 | `conftest.py:1360` の comment | 機能的に等価。SURVIVED 予測 |
| M1 | `conftest.py:1491` の reader 検査省略 | N1 両 parameter。B が `acquired` を返し、serialization `:2100` の `== "blocked"` が赤 |
| M2 | `conftest.py:1362` を `and not created` | N1 両 parameter の同 assert。既存 priority 模擬も `:2446` の `[6.0, 9.0]` が赤 |
| M3 | 同条件を `and created` | N2 両 parameter の `:2100`。P2 でも gate 待ちがなく `:4441` が赤 |
| M4 | `conftest.py:1379` の deadline 再起算 | deadline test 両 parameter。`:2220` の `waits == expected`、`:2221` の時計値が不一致 |
| M5 | `conftest.py:1387` の例外時 close 省略 | cleanup `[main-timeout]`。開いた gate fd の `os.fstat` が成功し、`:2170` の `pytest.raises(OSError)` が赤 |
| M6 | `conftest.py:1491` の保持なし条件除去 | P2 の build 内 reader `:4373` が gate に当たり、`:4419` の `assert not blocked` が赤 |
| M7 | `wave_land_window.py:627` の同値拒否削除 | `[tip-equals-main]` の `assert rc == 3` が赤 |
| M8 | 同 `:619` の status 拡大 | `[rollback-incomplete]` の同 assert が赤 |
| M9 | 同 `:625` の tip 検査削除 | `[tip-invalid]` の同 assert が赤 |
| M10 | 同 `:46` の固定文変更 | success `[normal]` の全文一致 `test_wave_land_window.py:1827` が赤 |
| M11 | 同 `:36` の landed allowlist 拡大 | landed `[fold-rollback-failed]` の `:1640` の rc 検査が赤 |

**所見**：M1 の reader が production 経路を避けているという疑いは反証される。
**分類**：refuted
**根拠**：`orchestrator/tests/test_real_repo_serialization.py:2013` は `with c._real_repo_locks(...)`、`:1999` は `return real_flock(fd, operation)`。差替えは保存先・key・テスト用 timeout と実 flock へ委譲する観測 wrapper。
**影響**：nit。M1 の赤を模擬 reader の結果と扱う理由はないが、実測 KILLED の追認ではない。
**推奨**：不要。M2 は N1 と既存模擬、M3 は N2 と P2 に検出経路があり、単一 killer への排他的帰属はしない。

## actor / handshake の頑健性

**所見**：`_gate_actor` の「every receive and reap is bounded」という説明は、異常時まで保証していない。
**分類**：plausible
**根拠**：`orchestrator/tests/test_real_repo_serialization.py:2042` の `select(..., 35)` 後に無期限の `readline()` があり、`:2053` の `process.wait(timeout=5)` が例外になると後続の pipe close が実行されない。
**影響**：nit。部分行後の停止や kill 後の回収遅延では、待ち時間超過・回収漏れがありうるが、現 actor の通常出力で発生する証拠はない。
**推奨**：pipe close は別の `finally` で保証し、説明を保証範囲に限定する。stderr 大量出力の実経路は確認できず、これを must-fix の根拠にはしない。

**所見**：B の第三の `blocked` や ExitStack の解放待ち循環を、現 relay の欠陥とする根拠はない。
**分類**：refuted
**根拠**：同 `:2001` は `fd not in reported` で通知を抑制し、gate 検査 fd は main 取得前に閉じる；`:2051` は未終了 child を `kill()` し、cleanup で `release` 応答を待たない。
**影響**：nit。対象 relay では gate と main による追加通知は高々一回で、B→W→A の回収順が release handshake の循環を作る構造ではない。
**推奨**：不要。ただし 30 秒の lock timeout・35 秒の受信 watchdog・5 秒の回収期限について、高負荷での非再現を静的検査だけで保証しない。

## 既存 test の期待更新

**所見**：priority 模擬の時刻変更を単なる期待値合わせとする疑いは反証される。
**分類**：refuted
**根拠**：`orchestrator/tests/test_real_repo_serialization.py:2410` の `gate_closed_at[fd - 2] = ...` が gate EX 成功時だけ入場を止め、`:2416` が cohort を選別する；`:2449` は gate/main の取得・UN・close 順を独立に固定する。
**影響**：nit。legacy は t=0 の cohort が t=6 に、common は t=3 の cohort が t=9 に終了するため、gate を外せば時刻・イベント列とも一致しない。
**推奨**：不要。245.0／0.05 の literal は残る。closure 9 parameter は登録、fixture の mode/lifetime、key、衝突辺、prewarm の契約を検査し、gate の fd 数や新しい取得時刻を期待していない。

## P2 の強化

**所見**：【must-fix 1】P2 は subprocess handshake を追加した後も、正常完了を実時間 2 秒未満に制限している。
**分類**：real
**根拠**：`orchestrator/tests/test_real_repo_serialization.py:4384` の timeout は `2.0`、`:4440` は `assert time.monotonic() - started < 2.0`；計測区間に `:4429` の holder 解放応答と `:4370`・`:4371` の別 actor 応答が入る。
**影響**：lock の順序・排他が正しくても、worker／actor のスケジューリング遅延だけで受入が赤になる。
**推奨**：2 秒未満の成功条件を削除し、テスト内の lock 予算は制御時計で検査する。外部 watchdog と、SH 解放 probe・`blocked == [True]`・mode／fd／参照数の assert を分離する。production deadline／retry は変更しない。

**所見**：P2 の昇格・入れ子 reader・降格が一つの恒真的 assert に畳まれているという疑いは反証される。
**分類**：refuted
**根拠**：同 `:4423` の別 fd による EX probe が SH 解放を検査し、`:4441` が昇格時の競合を要求する；入れ子 reader の gate 待ちは `:4373`、降格の gate 待ちは fixture の write context 終了時に、それぞれ `:4419` の二度目の競合拒否へ到達する。
**影響**：nit。M6 の直接 killer は `:4419` であり、2 秒 assert ではない。fd 同一性、参照数 2→1、最終 state 空の検査も残る。
**推奨**：must-fix 1 の修正でも、この独立した赤化経路を保持する。

## 所有外 consumer の回帰

**所見**：【must-fix 2】昇格時の新設 gate の open 失敗が、外側 reader の SH を失わせる新しい経路を作っている。
**分類**：real
**根拠**：`orchestrator/tests/conftest.py:1364` の `LOCK_UN` が `:1366` の `_open_real_repo_lock(gate_path)` より先であり、`:1390` の cleanup は `if created:` に限定される；既存 state の `mode`・holders は read のまま残る。
**影響**：例えば common gate の open／検証が昇格中に失敗すると、外側 module reader が common SH を失ったまま生存し、sibling worktree writer と reader consumer の排他が崩れる。
**推奨**：gate の open・検証を SH 解放前に済ませ、SH 解放以降は gate fd cleanup の保護範囲に入れる。既存 SH 保持下で gate open を失敗させ、別 fd の EX が引き続き拒否される負例を追加する。一般的な昇格 timeout 後の state 毒化は別裁定のままでよい。

**所見**：通知の直接呼出しや interval consumer の署名・記録順が今回の変更で壊れるという疑いは反証される。
**分類**：refuted
**根拠**：`tools/wave_land_window.py:614` は `kind="landed"` を既定値に保持；`conftest.py:1553` は `_real_repo_locks` 進入後に取得時刻を読む；`test_run_tests_shards.py:1398` は同 context 全体を差し替える。
**影響**：nit。gate 待ちは記録区間に含まれず、取得完了後から解放後までという形式・順序は不変。candidate の write→read と campaign の read lifetime も呼出し面では不変だが、上記 open 失敗経路は別問題である。
**推奨**：この理由による consumer 修正は不要。所有外 consumer の実走結果は本レビューでは未確認。

## docs と pin

**所見**：README 冒頭の「writer の飢餓を防ぐ」は、plan v2 が認めた保証範囲より強い。
**分類**：real
**根拠**：`orchestrator/tests/README.md:258` は「writer の飢餓 (F976) は…防ぐ」と断定する一方、`s4-ruling.md` の裁定パッケージは gate 取得前の厳密な優先を保証しないとする。
**影響**：nit。gate 取得後の優先を、待機開始からの飢餓防止保証と誤読させる。
**推奨**：README を「writer が gate を保持する間、fresh reader の入場を止める」と限定する。追加の公平性機構は今回へ持ち込まない。

**所見**：byte pin 不一致と合成 fixture の項6への干渉という疑いは、読んだ現物では反証される。
**分類**：refuted
**根拠**：入口の読取計数は 9,519 bytes・最長121文字；`tools/check_docs.py:467` と `test_check_docs.py:55` は同文、`:2524` は `9_519`、上限／超過例は `9_520`／`9_521`。項6定数は独立している。
**影響**：nit。273 関数への fixture 伝播はあるが、今回の literal 更新による不一致は確認できない。runbook `:1261` の rc=0 送信／rc=3 非送信、`:1262` の rc=28 除外も実装述語と一致する。
**推奨**：pin の追加修正は不要。全273 consumer の実走通過を意味するものではない。

## scope の逸脱

**所見**：author の焦点走件数を、所有外 consumer・全体受入まで含む検証完了と解釈してはならない。
**分類**：real
**根拠**：`s5-a1.md` は「file 全走、所有外 consumer test、受入全走…未実走」、`s5-a2.md` も焦点外を未実走と明記する。現物の parameter 数は author 1 が22、author 2 が message 38＋docs 7＝45と整合する。
**影響**：nit。件数の誤記は確認できないが、この報告だけでは統合後の受入赤を除外できない。
**推奨**：親の統合検証と区別して記録する。差分に所有外の `dev_wave_land.py`／`acceptance_shards.py`／`dev_wave_wait.py` の変更、新しい環境変数・CLI flag、production deadline／retry 変更は見つからない。

## 裁定パッケージ候補

**所見**：gate 取得前の公平性と、取得待ち失敗後の一般的な昇格 state 回復は、今回の局所修正とは別に残る。
**分類**：real
**根拠**：`conftest.py:1270` の NB polling に待機登録はなく、`:1364` の SH 解放後に取得待ちが失敗すると既存 state は保持される；`s4-ruling.md` も両者を scope 外とする。
**影響**：gate 取得前の飢餓、および昇格 timeout 後に外側 reader が SH を失う既知の実行経路は残る。
**推奨**：既存の裁定パッケージへ維持する。must-fix 2 は新設 gate の open 失敗を SH 解放前へ移す局所修正に限定し、一般的な回復機構や deadline 延長へ拡大しない。

## 総括

**must-fix 2 件、NO-GO。**

1. P2 の実時間2秒未満という成功条件を除去する。
2. 昇格時の gate open・検証を SH 解放前に置き、新設失敗経路で外側 reader の排他を失わせない。

全必読資料を読み、静的検査のみ実施した。ファイル変更、pytest、変異実行は行っていない。
