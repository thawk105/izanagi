## 総括

- 判定は **blocker、現プランのまま実装へ進めてはならない**。
- 通常の `LandResult` / `_Reject` 経路では判定前 release は起きないが、予期しない例外や中断を `main()` で terminal 化する案は、merge・fold・rollback の途中状態でも lease を解放する。
- `terminal = rc not in {11, 21}` は成立しない。特に rc=26/27/30 は同一 request の recovery で直りうる。rc=28 は逆に release-safe ではない。
- TTL 後に異なる slug が取得した lease は holder guard が守る。一方、同一 slug の別 invocation は新しい lease でも旧 lander が削除できる ABA が成立した。
- release を JSON 出力より前に置くと、main と台帳を更新し lease も消したのに `land-result.json` が空、という回復不能な観測欠落が増える。
- provenance が receipt 完全検証より前なのは実コードどおり。二重 parse は同じ parser を使っても、二回の読取間の差し替えを拘束できない。
- F3 の中央値・最大値は lease 保持時間を証明しない。基準 commit までを再集計しても、記載された 26 対・中央値 308 秒を再現できなかった。
- land の受理条件、全史 provenance、ff-only を弱める直接のリワードハックは見つからなかった。問題は受理集合ではなく、排他と回復可能性、結果参照の完全性である。

## Blocker 1 — 中断された mutation を terminal 化して解放する

根拠は `codex/plan.md:43-70`、`tools/dev_wave_land.py:3020-3024,3052-3065`、`tools/dev_wave_land.py:2142-2208` である。

成立順序:

1. `land()` が lock 内で `git merge --ff-only` を開始する。
2. Git が ref を更新した直後、または親が完了を観測する前に `KeyboardInterrupt` が入る。
3. `_git()` は `OSError` しか捕捉しないため中断が `land()` から脱出する。
4. `land()` の `finally` は land lock と repository を閉じる。
5. プランどおり `main()` が中断を rc=130 の terminal `LandResult` へ作り替える。
6. release が走り、別 wave が main の中間状態を基準に受入を開始できる。

fold 中はさらに悪い。`apply_fold()` は transaction state を先に保存してから canonical path を書く (`tools/spool_fold.py:3053-3069`)。最初の中断は `_fold_main_locked()` が rollback へ送るが、rollback 自身は `KeyboardInterrupt` を捕捉しない (`tools/dev_wave_land.py:2412-2445,2142-2208`)。rollback 中の二度目の中断は不完全状態のまま `main()` へ抜け、同じ terminal-release を通る。これは、二度目の signal では lease を残す既存契約とも逆である (`docs/pegasus-runbook.md:891-894`)。

修正条件は、予期しない例外と中断を一律 terminal にしないこと。各 return site が「main と fold transaction が quiescent で release-safe」と明示できた場合だけ解放すべきである。

**成果物影響:** certified の受理条件自体は後段 gate が守るが、main が進んだまま fold 台帳が before/after 混在し、`land-result` と fold commit の参照が欠落した状態で別 wave の受入集合が作られる。

## Blocker 2 — rc と release-safe を同じ `terminal` bit に畳めない

`codex/plan.md:20-39` の分類は、現行 recovery 制御流と矛盾する。

| rc | 実際の状態 | 同一 request の挙動 |
|---:|---|---|
| 26 | rollback 完了後の fold 失敗を含む | main が動かなければ再実行で成功しうる |
| 27 | active transaction の検査・recovery 失敗 | 一時的な I/O や検査例外なら再実行で直りうる |
| 28 | rollback 不完了、journal または中間状態あり | terminal かもしれないが release-safe ではない |
| 30 | fold commit 検証後、journal の finalize 失敗 | 同一 request の recovery が明示的に実装されている |

rc=30 の具体的順序は、fold commit 作成、`mark_fold_committed()`、postcondition 成功、`finalize_fold()` 失敗、rc=30 返却である (`tools/dev_wave_land.py:2379-2463`)。次の同一 request は active plan を検出して `_finalize_recovered_fold_commit()` を通り、再 commit せず finalize する (`tools/dev_wave_land.py:2467-2534,2778-2882`)。したがって「同じ tip を叩き直して直るか」という brief の定義でも rc=30 は retryable である。

成功した active recovery と `already-landed` no-op は、receipt 検証と finalize が完了してから返るので release-safe である。失敗した recovery まで同じ扱いにはできない。

**成果物影響:** rc=30 を `terminal=true` とすると、main 上の fold commit と残存 journal の対応参照が未完のまま完了報告され、別 wave は origin 不一致の rc=27 に落ち、台帳更新が停止する。

## Blocker 3 — P1 は安全側ではなく可用性側であり、rc=29 も単一意味ではない

`_audit_provenance_history()` は checker の決定的な非0だけでなく、480秒 timeout、`KeyboardInterrupt`、binding 読取失敗などの全 `BaseException` を rc=29へ畳む (`tools/dev_wave_land.py:1867-1908`)。receipt 再照合中の例外も同じ rc=29である (`tools/dev_wave_land.py:1938-1954`)。D254 自身も timeout は再試行へ回すとしている (`docs/decisions.md:11718-11719`)。

具体例は、計算ノード dispatch の一時 timeout、rc=29、`terminal=true`、release、同じ tip の再試行機会喪失である。F2 が証明するのは「checker が明示的に rc=1 を返した一件が決定的だった」ことだけで、rc=29 全体の終端性ではない。

逆方向にも穴がある。rc=21 は一時的な snapshot churn に加え、wave tip が foreign control-plane path と衝突する決定的拒否も含む (`tools/dev_wave_land.py:1293-1309`)。したがって rc=21 全体を retryable として保持すると、F2 と同型の占有を再現できる。

比較すると、

- terminal を retryable と誤る最悪値は、TTL または誤った loop が続く間の停止である。
- retryable・未知・中断状態を terminal と誤る最悪値は、元 lander が再開可能な間に排他を解き、別 wave の受入を重ねることである。

よって P1 は正しさ上の安全側ではない。理由と mutation phase から `retryable_same_request` と `release_safe` を別々に出す必要がある。

**成果物影響:** JSON の `terminal` 値が実状態と食い違い、呼び手が再受入不要の tip を破棄したり、逆に決定的 rc=21 を再試行し続けたりして、受入レポートの試行集合と lease 状態が変わる。

## Blocker 4 — holder digest だけでは TTL 後の同一 slug ABA を防げない

lease payload は `{holder, main_sha, ttl}` だけで generation を持たない (`tools/wave_land_window.py:167-183`)。`release()` は current lease の holder と `sha256(wave)[:12]` だけを比較し、mtime、`main_sha`、旧 inode、receipt generation は照合しない (`tools/wave_land_window.py:784-821`)。

成立順序:

1. invocation A が slug `S` の lease を取得する。
2. A の land 中に TTL 2400秒を超える。
3. invocation B が同じ slug `S` で claim し、stale inode を unlink して新 lease を作る (`tools/wave_land_window.py:763-772`)。
4. A が terminal になり `release(dir, S)` を呼ぶ。
5. B の新 lease も同じ digest なので、A がそれを unlink する。

read-only 制約下で I/O seam だけを差し替えて実 `release()` を実行した結果は次のとおりだった。

- 異なる slug の stale lease: `not-owner`、unlink 0回
- 同一 slug の新 generation: `released`、unlink 1回

これは runbook が既に認める「slug は invocation を識別しない」という限界そのものである (`docs/pegasus-runbook.md:982-985,1003-1006`)。また、lease directory は land request や receipt に束縛されず、terminal 後に環境変数から読む案なので (`codex/plan.md:94-111`)、誤った directory に同じ slug の lease があればそれも削除する。

P4 の「generation/fencing に触らない」と I2 の絶対保証は両立しない。少なくとも directory identity と claim generation を束縛した compare-and-delete が必要である。

**成果物影響:** B の正当な受入中に A が lease を消し、C も受入を開始できる。land gate は不正 commit の certified 採用を防ぐが、B/C の receipt は stale になり、レポート上の受入集合と `lease_release` の所有者帰属が誤る。

## Blocker 5 — receipt 二重 parse は同じ parser でも TOCTOU を残す

順序はプラン記載どおりである。通常 ff land では provenance が `tools/dev_wave_land.py:2701-2759`、receipt 完全検証が `:2761-2767` である。

プランの事前 snapshot が `_read_acceptance_receipt()` と `_receipt_object()` をそのまま再利用するなら、duplicate key や exact-field 規則の差は生じない。この攻撃は成立しなかった。しかし、各読取内の inode 同一性しか検査しない (`tools/dev_wave_land.py:490-520`) ため、二回の読取間の atomic replacement は拘束されない。

成立する二経路は以下である。

1. R1 の wave/holder だけが一致する。
2. provenance が rc=29 になり、完全検証へ到達しない。
3. R1 の他 field が不正でも、事前 snapshot を権限として release する。

逆に、事前読取 R1 が失敗した後で valid な R2へ差し替わると、land は R2で成功するが、epilogue は holder-unverified として lease を残す。これは F1 の再発である。

release 権限と land が検証する receipt は、同じ immutable bytesまたは同じ digestへ束縛しなければならない。

**成果物影響:** `acceptance_receipt_sha256` が示す receipt と release 判断に使った receipt が別物になり、レポートから「どの受入証跡がどの lease 解放を認可したか」を復元できなくなる。

## Blocker 6 — release 後 print は I3 と `land-result.json` を同時には保証できない

プランの順序は `land()`、release、`print()` である (`codex/plan.md:43-51`)。runbook は shell redirection で出力先を起動時に truncate する (`docs/pegasus-runbook.md:1050-1055`)。

成立順序:

1. land と fold が成功し、main と canonical 台帳が進む。
2. `release()` が `acceptance.lease` を unlink する (`tools/wave_land_window.py:806-814`)。
3. `print()` の前に SIGKILL、二度目の SIGINT、`BrokenPipeError` が発生する。
4. `land-result.json` は空のままになり、`_load_land_result()` が拒否する (`tools/wave_land_window.py:856-869`)。

通常の `Exception` を捕捉して元 rc を維持する実装は可能だが、`release()` は unlink 後の `finally` 内 `os.close()` からも例外を出しうる (`tools/wave_land_window.py:818-821`)。`KeyboardInterrupt` は `Exception` 捕捉では足りず、SIGKILL はどの catch でも閉じない。

同じ JSON に実 release 結果も含めるなら、単純な stdout だけでは原子的に保証できない。最低でも core land result を atomic な `--result-file` へ先に確定し、その後の release telemetry を sidecar または atomic update にする必要がある。

**成果物影響:** main と fold 台帳の値は更新済みなのに `main_after`、`fold_commit_sha`、receipt SHA を参照する結果 JSONと landed 通知が存在しない、という不一致が残る。

## Blocker 7 — 外部 consumer の監査は JSON schema だけで、release の副作用を見ていない

プランは5本の外部 script が未知 JSON field を無視すると確認している (`codex/plan.md:133-141`)。しかし terminal 後に lease が消えるという制御流変更には対応していない。

実例の t1142 loop は、rc=21/29なら5秒後に同じ land を再実行し、lease の再 claim をしない (`wave-t1142-oracle-n-pilot/land2-loop.sh:9-31`)。実際の land command は同じ receipt と slug を使う (`run-land2.sh:7-17`)。

新挙動では最初の rc=29 が lease を解放し、二回目以降は別 wave が lease を保持していても land を走らせる。`dev-wave-t721-source-closure/finish2.sh:66-82` や `dev-wave-s1-design-choice/land-retry.sh:22-32` にも、成功するまで land を繰り返す同型がある。

未知 field の互換性は成立するが、呼出し protocol の互換性は成立しない。terminal 結果を受けた caller は停止するか、新規 claim・受入・receipt 発行からやり直す契約が必要である。

**成果物影響:** 旧 loop が lease 外で land を再試行し、並行 wave の受入 receipt を stale にするため、受入レポートの試行回数と有効 receipt 集合が変わる。

## 重要所見 8 — F3 の 308秒・4827秒は lease 生存時間を証明しない

主張は `handoff.md:58-67` にある。基準 commit `0c689a96...` までを再集計すると、

- subject を時系列に「受入 lease 内 merge → 次の Fold」で結ぶ: 30対、中央値397.5秒、最大4827秒
- Fold commit の第一 parent が当該 merge である厳密対: 20対、中央値276.5秒、最大2037秒

となり、記載された26対・中央値308秒を再現できなかった。

最大4827秒は merge `5bf49c55...` と、親子関係のない後続 Fold `fe8a3555...` の時刻差である。同じ wave はその後もう一度 merge している。fold のない land、merge のない land、失敗後の再 merge、他 wave の Fold が混ざるため、commit 時刻差から一つの lease inode が連続して生存したとは言えない。

TTL超過 race 自体は D239 とコードから存在するが、F3 の max はその実在証明ではない。

**成果物影響:** certified 値は変わらないが、brief / handoff の p50・max と「TTL超過 holder が実在」というレポート上の結論は、測定方法と参照 commit を付けて訂正する必要がある。

## 重要所見 9 — F2/H の正確な回数と所要幅は保存 artifact と一致しない

`handoff.md:124-140` は31回+11回=42回としている。しかし保存済みログは、

- `land-loop.log:1-31`: 31回
- `land2-loop.log:1-12`: 12回

で、合計43回である。後半ログの開始時刻差は43〜66秒で、loop 自身に5秒 sleep があるため、land 一回は概ね38〜61秒である。自己申告の25〜45秒幅は独立に支持されない。

一方、保存された reason が `provenance full-history audit rejected the wave (rc=1)` であり、同一 tip の決定的再試行だったという中心結論は支持される。設計根拠に必要なのは42という正確な値ではなく、少なくとも一件の決定的 rc=29 が繰り返された事実である。

**成果物影響:** certified 選択は変わらないが、F2/H を引用するレポートの試行数と所要統計が変わり、42回・25〜45秒を根拠にした比較は再計算が必要になる。

## 不変条件に不足しているもの

I1〜I5だけでは不十分である。少なくとも次が必要になる。

- I6: `terminal` と `release_safe` を分離し、active fold state、rollback 不完了、mutation outcome 不明では release しない。
- I7: release capability を lease directory identity、holder、claim generationへ束縛し、同じ generationだけを compare-and-delete する。
- I8: release 判断と完全検証は同一 receipt bytesを使う。
- I9: mainを進めた結果 JSON は release より先に durable にし、SIGKILL時の残余を明文化する。
- I10: auto-release 後の同一 receipt による再 land を禁止し、再試行には新 claim が必要とする。

`already-landed` no-op と成功した active recovery は I6 を満たす。rc=27/28/30 で失敗した recovery は満たさない。

**成果物影響:** これらがないと、terminal JSON、lease ownership、fold journal、結果ファイルの4者を同じ land invocationへ一意に結び直せず、台帳とレポートの参照完全性を保証できない。

## 攻撃したが成立しなかった面

- 通常の return / `_Reject` では、land lock と repository が閉じた後にだけ `main()` へ戻る (`tools/dev_wave_land.py:3052-3065`)。例外を synthetic terminal にする案を除けば、判定前 release はない。
- TTL後に異なる slug が lease を取り直した race は holder guardで閉じる。実 `release()` 分岐の実行でも `not-owner` かつ unlink 0回だった (`tools/wave_land_window.py:801-814`)。
- P2 の stale-main terminal 分類は正しい。rc=10 は active plan がなく、current main が `tested_main..tested_tip` の監査済み閉包外にある場合だけ返る (`tools/dev_wave_land.py:1559-1572,1716-1726`)。同一 request の再実行では直らない。
- `already-landed` no-op は full receipt 検証後に返り、active recovery 成功は journal finalize 後に返るため、安全に解放できる (`tools/dev_wave_land.py:2761-2767,2939-2964,2514-2534`)。
- 計算 property の `terminal` は dataclass field ではないので、frozen dataclass equality と既存 `LandResult(...)` 構築を変えない (`tools/dev_wave_land.py:139-167`)。JSONの未知 fieldも `message()` は無視する (`tools/wave_land_window.py:875-884`)。
- rc=1/130 は現行 land rc 0,10,11,20〜30とは衝突しない (`tools/dev_wave_land.py:42-55`)。rc=130 は既存 wait 側でも中断を意味する。数値衝突は見つからず、問題は外部 loop の副作用である。
- lease directory 不在・open失敗時に別 directoryへ fallbackする経路はない。`unavailable` になるだけである。
- provenance、receipt、ff-only、fold の受理条件を弱める案はプランにない。D254 の no-op/recovery provenance 除外も、新 commit を admit しない既存裁定どおりであり、リワードハックは成立しなかった (`docs/decisions.md:11672-11724`)。

## provisional 裁定への判定

- P1: **却下**。rc allowlistでは retryability と release safetyを表現できず、未知を terminal にするのは安全側ではない。
- P2: **支持**。stale-main は同一 request では回復不能。
- P3: **条件付き支持**。新 field の追加は互換だが、計算 property を rcだけから求めてはならない。
- P4: **I2を絶対条件とする限り却下**。少なくとも release 用 generation CAS が必要。扱わないなら、I2を「異なる holder digestだけ」に弱め、同一 slug invocation の残余を明記する必要がある。

F1、F4、F5の中心結論は支持される。`perf-optional` の script は land rc=0 でそのまま exitし、release を呼ばない (`2026-08-16_perf-optional/unattended_land.sh:69-86`)。現行 `main()` にも release はなく (`tools/dev_wave_land.py:3087-3099`)、D253 は release 忘れのTTL比例停止を明記している (`docs/decisions.md:11664-11670`)。

pytest は制約どおり実行していない。実 `release()` の分岐確認以外は静的検査で、作業 tree は変更なし・clean である。