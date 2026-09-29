### A1 inline 読みの件数だけでは trace の忠実性を確認できない

**重大度:** must-fix
**根拠:** `s1-brief.md:8`、`plan.md:3,11-13`、`external/ccbench/cc/cicada/transaction.cc:102-137`、`patches/instr-cicada-trace.patch:16-25`
**成果物への影響:** `R_INLINE>0` でも、scan が選んだ版と R に記録された版が一致するとは言えず、誤った履歴で「巡回なし」になりうる。
**推奨対処:** inline R/W 件数は到達確認と呼ぶ。選択時の版・時刻と登録時の値の差、slot 再利用を別に調べられない限り、一次資料の「trace の網羅」を限定する。既存 patch の bytes を保ったまま解決できないなら、trace patch 修正の要否を裁定候補にする。

### A2 親の「経路が分かれない」は読みの意味まで一般化できない

**重大度:** must-fix
**根拠:** `s1-brief.md:8`、`external/ccbench/cc/cicada/transaction.cc:153-183,430-457`、`patches/instr-cicada-trace.patch:80-95`
**成果物への影響:** 再読・自分の write set からの読みは追加 R にならない。また `read()` と `scan()` は版の body へのポインタを渡すため、版 ID が正しくても、後に参照した中身の取り違えは R/W の版 ID だけでは見えない。
**推奨対処:** 「成功した点読みごとに R」や「trace が値を証明した」と書かず、read set に登録された版への依存を記録する範囲と、body を観測しない限界を明記する。

### A3 mismatch のゼロも、非ゼロも、再利用の判定にはならない

**重大度:** must-fix
**根拠:** `s1-brief.md:11`、`plan.md:9,17,77-79`、`patches/instr-cicada-trace.patch:80-88`、`external/ccbench/cc/cicada/include/transaction.hh:173-195`
**成果物への影響:** 同じ inline slot が再利用され、登録時と commit 時の wts が同じなら `READ_WTS_MISMATCH=0` のまま見逃す。`REUSE_VERSION=0` では保護が破れた場合、比較そのものが解放済み heap 版を読む。非ゼロを stock の診断不合格にするのは妥当だが、原因を再利用と断定すると一次資料が言い過ぎる。
**推奨対処:** plan の診断扱いを維持し、ゼロを安全性の証拠に使わない。非ゼロや異常終了は raw と条件を残し、機序は別途調査する。

### A4 正例の帰属規則が弱く、inline 固有の盲点も試していない

**重大度:** must-fix
**根拠:** `plan.md:61-67`、`launch_cicada_run.base-md17.py:590-648`、`patches/broken-cicada-skip-read-recheck.patch:600-612`
**成果物への影響:** 雛形の帰属は事象の txn 時刻・key・読んだ版に合う **いずれか一つ**の rw 辺を数え、再検査が見た版 `b_wts` との一致を要求しない。高競合 cell では偶然の一致を「期待した経路で検出」としうる。成功しても示せるのは read recheck を壊した巡回の検出で、inline slot の ABA や誤記録の検出力ではない。
**推奨対処:** `b_wts` と辺の次版、raw の R・相手の W を照合して帰属させる。正例の結論をその壊し方に限定し、inline 専用の検出力は未検査と記す。

### A5 build と実行条件の束縛に五軸以外の穴がある

**重大度:** should
**根拠:** `plan.md:25-35,109-123`、`launch_cicada_run.base-md17.py:32-36,237-255,845-856`、`tools/vhash_cicada_tuning/driver.py:59-105`、`external/ccbench/cc/cicada/transaction.cc:85-87`
**成果物への影響:** plan の compile command 期待値は五軸・TRACE・ADD_ANALYSIS が中心で、`SINGLE_EXEC=0` の照合と、実行時に受理された YCSB flags の照合を明示していない。`SINGLE_EXEC` が変わると読みの経路自体が変わり、表の BEST/CTRL というラベルが実体を束縛しなくなる。
**推奨対処:** cache と三 TU の `-D` に `SINGLE_EXEC=0` を含める。md_11 の `check_flags()` と同様に、stdout の有効 flags を argv と照合し、結果 JSON に保存する。BACK_OFF の重複指定を除去する plan の修正は採用してよい。

### A6 小走行の陰性を主比較全体の採用判定に広げている

**重大度:** must-fix
**根拠:** `s1-brief.md:3,6-7,19`、`plan.md:41-55,77-79,130-134`、`vhash-cicada-baseline-tuning/README.md:114-140`、`ruling-D2279.md` 決定 4
**成果物への影響:** 200 tuple・1 秒の陰性や、容量を理由に省いた 1M cell から、md_11 の 1M・t48 の主比較条件まで「正しさ確認済み」と読む余地がある。判定器自体の上限も indeterminate である。
**推奨対処:** 結論を実走した genome・workload・tuple・thread・GC・時間ごとに書く。省略した尺度は未検査とし、主比較への採用判断と小走行の結果を分ける。

## 総括

現状の plan は、そのままでは採用しにくい。最大の問題は、inline 件数と正例の成功から trace の忠実性全体を主張できる形になっていることだ。件数診断は到達確認に限り、版の選択時刻と body の観測限界を一次資料に残す必要がある。正例は帰属条件を強めた上で、read recheck 経路の検出力だけを示すものとする。build では `SINGLE_EXEC` と実行時 flags も束縛する。これらを直し、陰性を実走条件だけの indeterminate として報告するなら採用可能である。より強い inline 忠実性を完了条件にする場合は、既存 instr patch の bytes 不変と検査範囲の衝突を裁定に回すべきである。