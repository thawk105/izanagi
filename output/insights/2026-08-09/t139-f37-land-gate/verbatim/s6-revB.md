静的レビューの結論は **NO-GO** です。pytest は実行しておらず、緑は主張しません。

## 1. lock-busy の即時契約を共有 stub が隠している

**深刻度: blocker**

**根拠:** `tools/dev_wave_land.py:1863-1869` では最大 3900 秒の監査が lock 試行より先です。一方、既存テストは `orchestrator/tests/test_dev_wave_land.py:1223-1239` で、lock 保持中は 2 秒未満で `lock-busy` を返す契約を固定しています。fixture の即時終了 stub (`:119-134`) により、このテストは実 checker の待ち時間を全く観測しません。D102 も common lock を shared mutable 検査より前に置く契約です (`docs/decisions.md:4521-4525`)。

既存 64 test の assert 自体には削除・変更はありませんが、この test の意味は変わっています。実環境では「nonblocking lock」が最大 65 分後に初めて試されます。

**成果物影響:** 競合 wave は即時 `lock-busy` にならず、受入 lease と land 終端を長時間保持したまま、レポート・canonical 3 台帳・fold receipt を main に反映できません。

**修正案:** 短い lock preflight を先に行い、busy なら checker を一度も起動せず即時返却すること。新規 admit が必要な場合だけ lock を解放して監査し、再取得後に現行検査をすべてやり直す二相構成にする。pre-held lock＋停止 checker で「marker 未生成、2 秒未満」を固定する既存 test 強化が必要です。

## 2. `already-landed` と active recovery は監査対象外になっていない

**深刻度: blocker**

**根拠:** 監査は無条件に `tools/dev_wave_land.py:1864` で走ります。receipt の検査を active plan だけ免除するのは `:1930-1935` ですが、その時点では監査の timeout、checker 欠落、起動失敗を既に通過済みです。通常の `already-landed` 判定はさらに後の `:2041-2066` です。

したがって:

- 同じ request の2回目も full audit を再実行する。
- 2回目の dispatch 障害・timeout・checker 欠落で、既存の `already-landed` が rc=29 `rejected` に変わる。
- active recovery は checker の非ゼロ rcだけは無視するが、欠落・symlink・timeout・例外では `:1882` の active plan 読み込みにすら到達しない。

これは adjudication の「recovery は関門対象外」「idempotency を保つ」という契約 (`s4-adjudication.md:80-94`) と不一致です。既存 idempotency test (`test_dev_wave_land.py:1784-1815`) は常時緑 stub のため失敗可能性と追加時間を隠しています。

**成果物影響:** active fold が途中状態のまま固着し、canonical worklog/decisions/failures と `FOLDED.md` が before/after 混在になります。また2回目の受理集合が `already-landed` から `rejected` へ縮みます。

**修正案:** 短い lock 内 preflight で `locked_main == tested_tip` を確定し、新規 commit を admit しない通常 `already-landed` と active recovery は監査を起動せず進めること。新規 admit だけを lock 外監査へ送る。次を追加テストにするべきです。

- 2回目だけ checker が失敗しても `already-landed`
- active recovery で checker 欠落・timeoutでも recovery 完了
- 新規 admit では同じ入力を rc=29 で拒否

## 3. 3900 秒 timeout は lease TTL と前景上限の双方を破る

**深刻度: blocker**

**根拠:** land の timeout は `tools/dev_wave_land.py:1270-1281` の 3900 秒です。dispatch 既定は queue 900秒、walltime 2400秒、grace 300秒、さらに accounting grace 60秒です (`tools/pegasus/dispatch_compute.py:28-31,1581-1633,1647-1684`)。

一方、受入 lease の policy TTL は 2400秒 (`tools/wave_land_window.py:27,144-151`)。claim は受入前で (`docs/pegasus-runbook.md:764-773`)、実測された受入だけで約1055秒を消費します (`:757-760`)。land 開始時点の残 TTL は既に約1345秒以下で、3900秒監査中に必ず失効し得ます。別 wave は stale lease を削除して再取得できます (`wave_land_window.py:320-329`)。fencing token はありません (`pegasus-runbook.md:786-788`)。

さらに runbook は helper を前景実行しています (`:779-782`)。親の前景 tool 経路には10分上限があり、上限超過で親ごと SIGKILL された実績があります (`docs/failures.md:670-677`)。3900秒 timeout は外側の600秒上限より後なので、timeout mapping と JSON 出力まで到達しません。

**成果物影響:** lease 失効後に別 wave の受入が並走し、片方の受入結果が stale になります。前景 kill では `land-result.json`、release、fold commit、canonical 台帳参照が欠落します。

**修正案:** 現在の2ファイル scopeでは閉じません。少なくとも以下を同時に設計し直す必要があります。

- ownerだけが更新できる lease renew/heartbeat と fencing
- land 最大時間より長い有効期間、または残 TTL に収まる明示的 deadline
- runbook の detached 実行、`.done` と独立 rc file、完了後の JSON/rc照合
- timeout/killを含む全終端での release

単に TTL を延長するだけでは、死んだ holder の停止時間を同じだけ延ばすため不十分です。

## 4. FD を束縛したが、その FD の bytes を実行していない

**深刻度: blocker**

**根拠:** checker は FD で開いています (`tools/dev_wave_land.py:1223-1252`) が、実際の subprocess は pathname `str(checker.path)` を再度開きます (`:1270-1279`)。`close_fds=True` なので束縛した `checker_fd` は子へ渡りません。pathname の再照合は子終了後です (`:1282`)。

したがって、bind 後に pathname を差し替え、別 bytesを実行し、終了前に元 inodeへ戻す raceでは検出できません。receipt の `checker_blob_sha` も Git tree の blobであり、実行された pathname bytes の hashではありません。実装子の「FDで監査中まで束縛」という申告 (`s5-impl.md:8-10`) は成立していません。

**成果物影響:** receipt が示す blobとは異なる checkerが rc=0 を返し、provenance違反 commitが land 受理集合へ入り、台帳の commit参照が未監査履歴を指します。

**修正案:** 開いた FD の内容と committed blobを照合し、その同じ FDを子へ `pass_fds` して実行すること。checker の repo root 解決を壊さない専用 launcherが必要です。bind→pathname swap→実行→restore の race testも追加してください。

## 5. 未検証状態で checker を実行し、後段検査では過去の副作用を復元できない

**深刻度: must-fix**

**根拠:** audit (`tools/dev_wave_land.py:1864`) は history/config/main clean/wave clean のすべてより前です。

後段で捕捉できる範囲は次のとおりです。

| 状態変化 | 後段で捕捉 |
|---|---|
| shallow/graft/replace/config が残る | `:1878-1879` |
| main tracked/index/submodule dirt が残る | `:1898-1902` |
| wave dirt が残る | `:1903` |
| wave HEAD/ref が動く | `:1917`, `:1930-1931` |
| main が監査閉包外へ動く | `:1919-1929` |
| persistent な untracked/ignored collision | `:1898-1902`, `:2094-2099` |
| 並行 land | lock `:1868-1877` と head再照合 `:1917-1929` |
| checker が dirt/collisionを削除後に自身を cleanへ戻す | **捕捉不能** |
| pathnameやmainを一時変更して復元する | **捕捉不能** |

特に dirty wave の working-tree checkerを実行する一方、receipt は committed blobを記録します。後で dirtが残れば拒否されますが、「何を実行したか」は復元できません。

**成果物影響:** checkerが ignored collisionを消すと、同じ main 状態なら拒否される incoming pathが受理され、レポートやcanonical台帳の既存 artifactが上書き対象になります。

**修正案:** 二相化し、最初の短い lock 内で history/config/main/wave cleanlinessと no-admit判定を行うこと。新規 admitだけ lockを解放して監査し、再取得後に全検査を繰り返す。dirty wave・dirty main・lock-busy時に checkerが未起動であることもテストで固定してください。

## 6. rc=29 自体に閉集合 consumer 回帰はないが、運用 docs は不十分

**深刻度: must-fix**

**根拠:** rc=29 は CLI process rcにだけ現れ、JSON schemaは変わっていません。`LandResult.as_json()` の fieldは従来どおりです (`tools/dev_wave_land.py:97-105,2187-2197`)。

consumer の静的追跡結果:

- `wave_land_window.message` は rcを読まず、`landed` / `already-landed` の statusだけを許可する (`tools/wave_land_window.py:35,428-437`)。rc=29 の JSON status=`rejected` は既存どおり通知拒否。
- real supervisor は land APIを持たない (`tools/dev_waves/daemon.py:1-6`)。その不在は `test_dev_waves_integration.py:2622-2628` でも固定。
- `orchestrator/tests/test_dev_waves_*.py` に helper rcの閉集合 consumerはない。
- `test_wave_land_window.py:583-623` は generic `rejected` を既に失敗扱いする。

したがって「未知 rc=29 のため land 後に既存 consumer testが赤になる」経路は見つかりません。

ただし runbook の `python3 ... > land-result.json` は JSONしか保存せず、コメントの「rc と JSON を保存する」を満たしません (`docs/pegasus-runbook.md:779-782`)。直後の `message` が `$?` を3へ上書きするため、元の29を失います。

**成果物影響:** rc=29が land失敗ではなく通知失敗 rc=3として記録され、worklog/レポートの停止理由と再開判断が誤ります。

**修正案:** JSON・rc・完了 markerを別 artifactへ保存し、`rc==0`かつ status成功、`main_after`照合後だけ messageを生成する手順へ置換してください。

## 7. fixture の SHA/path/cwd/別 process 波及は、上記以外は反証できる

**深刻度: nit**

**根拠:**

- `git diff --unified=0` 上、既存 assertの削除・変更はありません。変更は fixture の `git add` 展開と、新規8 testです。
- base/tree/commit SHAはすべて実 repoから動的取得 (`test_dev_wave_land.py:134-176`)。固定 SHA assertはない。
- stubは base commitに入り、linked waveも同じ baseから作る (`:122-149`)。通常の `_target_paths` では main/wave双方に同一 pathがあるため差分集合へ入りません。
- CLI E2Eは synthetic waveを cwdにして実 helperを起動する (`:2938-2966`) ため stubが届きます。
- helper別 process経路も `cwd=wave` (`:2744-2785`) で同じ stubを使います。
- `_verify_repository` の cwd要求 (`tools/dev_wave_land.py:443-445`) と audit の `cwd=repository.wave` (`:1270-1273`) は競合しません。childのcwd指定は親processのcwdを変更しません。

**成果物影響:** tree SHA・path集合・collision判定・CLI schema・cwd束縛については、静的には受理集合や台帳参照の追加変化はありません。

**修正案:** この部分の実装変更は不要です。ただし実走結果ではなく静的結論に限ります。

## 実装子の (c) 自己申告の裏取り

- `s5-impl.md:38`: 親での全走が残る、は正しい。今回も未実走です。
- `:39`: latencyとrc consumerへの波及申告は方向として正しいが、supervisorは実 consumerではありません。一方、lease TTL・前景600秒・lock-busy即時契約を漏らしています。
- `:40`: fixture波及先の列挙は概ね正しいが、既存 lock-busy testが実 checker時間を見なくなった意味変更と、`already-landed`が毎回監査する点を漏らしています。
- `:41`: cooperative trust rootの残余申告は正しいものの、「FDで監査中まで束縛」という実装内容自体が誤りです。

## docs 修正箇所

親が直すべき箇所は次です。ただしコード blockerを先に閉じ、最終挙動へ合わせてください。

- `docs/dev-wave/operations.md` `DW-O17`: commit後 full auditは引き続き必須で、land gateの再監査が代替しないこと。
- 同 `DW-O23`: 新規 admitだけの lock外 audit、lock内 receipt再照合、rc=29、no-admit/recovery、background rc保存を明記。
- `docs/dev-wave/core.md` `DW-S09`: lease→受入→監査→land→全終端releaseの順序と、rc=29停止を明記。
- `docs/pegasus-runbook.md` §7.3: detached land、`.done`/rc/JSON照合、lease renew/fencing、timeoutとの時間収支。
- `docs/decisions.md` D102/D239: D239は「landの監査は不変」と書いており (`:11179-11182`)、今回の変更と矛盾します。既存決定を改竄せず、superseding decision fragmentが必要です。

`docs/dev-wave/**` は現在 25,199 / 25,200 bytesで余白1 byte、`operations.md` も 8,329 / 8,400 bytesです。追記は禁止に近い状態です。`DW-O17`・`DW-O23`・`DW-S09` の既存文を置換・縮約し、合計 bytesを増やさないでください。`tools/check_docs.py:430-435` が固定する S09 の2 literalは逐語保存が必要です。

## 総括

- **(a) blocker: あり。** lock-busy回帰、no-admit idempotency破壊、lease/前景timeout不整合、FD実行体未束縛の4件です。
- **(b) 最も危険な回帰:** active fold recoveryが監査の欠落・timeout・infra赤で開始不能になり、canonical 3台帳とfold receiptを部分状態に固着させることです。
- **(c) 親が docs で直す箇所:** `DW-O17`、`DW-O23`、`DW-S09`、Pegasus runbook §7.3、D102/D239を supersedeする decision fragment。docs/dev-waveは追記せず、既存節の縮約置換で総 bytes不増にしてください。