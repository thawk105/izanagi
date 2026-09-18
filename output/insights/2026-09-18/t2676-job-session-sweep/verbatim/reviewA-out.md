## 総括

- **real 3件 / refuted 4件 / nit 1件。must-fix あり、NO-GO。**
- 焦点走は **14 passed / 1 failed**。ログ上は login local 実行ではなく、計算ノード request `5015.nqsv` の結果です。
- TERM fixture の成立と、M2 の検出力の扱いを是正する必要があります。
- 所属不明の stat 読取り失敗が、job session の集計を汚す経路があります。
- SHA gate、child env 除去、pidfd、通常例外時の result 保持は、指定仕様に沿っています。
- 本レビューでは変更・追加実走を行っていません。

## 所見

**RA-1 — real / must-fix：TERM fixture が既定動作を確立しておらず、正常版も赤。**

位置：`orchestrator/tests/test_pegasus_dispatch_compute.py:7758–7765,7857`、`focus-new1.log`。

`ignore` と `late` は handler を設定しますが、`term` は設定しません。継承した SIGTERM の無視状態・block mask に依存するため、「SIGTERM 既定動作の C」という裁定 §1.8 の前提が成立していません。既存テストの同ファイル :4716–4717 は `SIG_DFL` と `SIG_UNBLOCK` を明示しています。

焦点走は実際に `after="term"` の不存在で失敗しています。ただし失敗時の `records` が出ていないため、継承状態が今回の直接原因だったとは断定できません。

**放置時の影響：** 焦点走・受入全走の緑を満たせず、正常版から赤い nodeid を M2/M7 の KILLED 証拠として誤帰属できます。
**是正案：** readiness 通知前に各 mode の handler と SIGTERM の unblock を確立し、失敗時に records を表示する。期待値を緩めず正常版を再確認する。

**RA-2 — real / 集計の仕様不適合：session 所属不明の process が `unreadable` を増やす。**

位置：`tools/pegasus/dispatch_compute.py:755–777,890–902`。

stat 読取り失敗では `session=None` の record が残り、最終集計は **attributed に限定せず**全 record の `readable=False` を数えます。数値 PID が見える一方で stat を拒否される環境では、別 session の process によっても `status="error"` になります。PID 自体が列挙されない場合はこの経路には入りません。

なお、`readable=False` は必ずしも `attributed=False` ではありません。その後の namespace readlink が成功して異なる値なら True です。いずれも :845 の readable gate によって signal はされません。

裁定 §1.5(7) の「最終列挙で残る attributed 候補の集計」とは異なります。一方、所属不明を黙って捨てて clean とするのも不適切です。焦点走の外側 dispatcher は実際に `unreadable=0, status=clean` なので、「計算ノードでは毎回 error」とまでは言えません。

**放置時の影響：** 別 session のアクセス制限だけで判定表 §3 の unreadable=0 を満たせなくなり、回収成功を期待外と報告する可能性があります。
**是正案：** session 所属未確定の走査エラーを、確認済み session の残存集計と区別する。所属未確定なら成功を断定しない方針を保持し、判定表との対応を明文化する。

**RA-3 — real / must-fix（台帳）：M2 は祖先保護の挙動を検出していない。**

位置：`orchestrator/tests/test_pegasus_dispatch_compute.py:7797–7802,7842–7844,7969`、`s5-author-out.md` の M2。

現 fixture の L と scanner は同じ user namespace です。祖先除外を削っても帰属述語が L を保護します。赤になるのは `fixture-exclusions` の集合 assert であり、「L が死ぬ」という事前登録の機序ではありません。author はこの差を正しく申告していますが、申告だけで挙動検出へ格上げはできません。

挙動で検出する別構成は可能です。例えば別 session 内で S だけ新しい user namespace に入り、L を外側に残す構成なら、L は namespace 述語上の候補になります。ただし通常 production の「dispatcher は init namespace」という条件から離れるため、独立した祖先 gate の試験として扱う必要があります。

**放置時の影響：** 変異台帳に「祖先の誤殺を検出した」と記録すると、実際以上の安全性を certified 選択・レポートへ持ち込みます。
**是正案：** 現 M2 は **冗長 gate の diagnostic sensitivity pin として別枠**にする。挙動検出を要求するなら別 fixture を登録する。変更前の裁定 §4 を満たしたとは扱わない。

**RA-4 — refuted：祖先鎖が session 外へ進むこと、ppid=0 により危険な走査になる。**

位置：`tools/pegasus/dispatch_compute.py:915–928`。

pid 1 は追加後に終了し、ppid=0 は次の while 条件で終了します。`/proc/0` は読みません。既訪問も終了条件です。session 外の祖先を除外集合へ含めても、候補を追加する効果はありません。祖先 stat の失敗は sweep 自体を中止します。

**影響判定：** 指摘された経路による誤殺は認められません。
**是正案：** 現行を維持。祖先の消滅・付け替わりを含む完全な同時 snapshot の保証とは区別する。

**RA-5 — refuted：通常の PID 再利用、fd 管理、poll が終了を捏造する。**

位置：`tools/pegasus/dispatch_compute.py:797–819,848–889`。

列挙後の pidfd 取得と starttime 再照合があり、不一致を zombie より先に判定します。不在・読取り不能も signal しません。skip 時は close 後に `opened` から除去し、正常経路で二重 close しません。poll 済み fd は pending から除いて unregister し、最後に close します。

空イベントでは期限まで再 poll します。POLLIN を伴わない HUP/NVAL は終了として数えません。ただし即時返却が続けば期限まで busy loop になり得ます。`after=term/kill` は観測段階であり、死亡原因の証明ではありません。

**影響判定：** 指定された通常経路での対象取り違え・偽の終了加算は認められません。
**是正案：** 現行の同一性確認を維持。starttime の粒度や session 変更まで含む絶対的な原子性保証は主張しない。

**RA-6 — refuted：env 継承や配置によって login pytest を走査し、通常例外で result を変更する。**

位置：`tools/pegasus/dispatch_compute.py:908–937,1129–1130,1742–1745,1842–1847,1905–1933,4708–4723`。

SHA 不一致・None は getsid より前に return します。ambient `1` では既存 in-process caller も発火しません。export は既存 envelope substring を保持し、pop は overlay 後です。inherit の tests task でもこの値は子へ渡りません。

呼出しは指定どおり except 連鎖後、isolation failure return 前です。通常の sweep 例外は wrapper が記録し、payload や child_rc を変更しません。`main` と result schema は差分上不変です。

`KeyboardInterrupt` / `SystemExit` は捕捉しません。`_SignalAbort` は Exception 系なので捕捉対象ですが、通常の `--job-run` 経路は `dispatch()` の SIGTERM handler 登録を通りません。「job 内 SIGTERM は必ず `_SignalAbort`」とは言えません。

**影響判定：** 指定された env 継承と通常例外による受入破壊は認められません。
**是正案：** 現行を維持。同期 stderr の閉塞や外部 signal まで rc 不変と一般化しない。

**RA-7 — refuted：新規テストが両層 stub による恒真 gate になっている。**

位置：`orchestrator/tests/test_pegasus_dispatch_compute.py:7776–7807,7911–7928,7948–7970,7983–8090`。

実 process 3本は実 unshare・実 wrapper・実 sweep・実 pidfd を通ります。置換した sweep は猶予を短縮して実体へ委譲します。L と D は pytest とは別 session です。

`_fake_session` は列挙・stat・kernel 操作を置換しますが、sweep の分岐、送信順、poll、集計、close は実体です。帰属述語そのものの検査には使えませんが、別の列挙テストと実 process テストがあります。

opt-in 負例では触れた操作が AssertionError を投げ、wrapper がそれを捕捉しても trace が呼ばれるため、`trace.assert_not_called()` が検出します。単なる「例外が外へ出なかった」検査ではありません。

**影響判定：** 全体が stub 成功だけで緑になる構造ではありません。ただし RA-1 の実測赤は残ります。
**是正案：** 各 mock テストが保証する層を限定して報告する。

**RA-8 — nit：trace field 配置に仕様表記との差がある。**

位置：`tools/pegasus/dispatch_compute.py:791–793,815–816,834,886`。

裁定 §1.5 の対象 pid・starttime 等は、実装では `process` 内に格納されています。最上位 pid は発行者のままで、これは §1.7 と整合します。`round`、`after`、signal、時刻、事象名は保持されています。定数・配置・順序にも実質的な相違はありません。

新規 production に subreaper、PID namespace、setsid、非子 waitpid、数値 PID への os.kill は追加されていません。F973 の reparenting 変更や既存 consumer の受理集合変更もありません。

**放置時の影響：** 指定資料では既存 consumer への直接影響はありませんが、今後の probe 集計で対象 pid の参照位置を誤る余地があります。
**是正案：** trace 仕様を `process.pid` 等の実際の配置へ合わせる。RA-2 の集計差とは区別する。

## 変異対応表の検算

以下は静的判断です。正常版の赤を解消するまで、実 process nodeid の変異赤を KILLED と認定できません。

| 変異 | 判定 | 理由 |
|---|---|---|
| M1 | 赤になる | 呼出し削除で `test_job_run_sweeps_before_result_and_strips_opt_in` の順序が `["result"]` になり不一致。 |
| M2 | **別枠** | 集合 assert は赤になるが、L は namespace gate に守られる。祖先誤殺の挙動検出ではない。 |
| M3 | 赤になる | getsid stub の AssertionError が error trace になり、`trace.assert_not_called()` が失敗する。 |
| M4 | 赤になる | SIGTERM 無視の C に KILL が届かず、`after=kill`・独立 pidfd 終了確認等が成立しない。 |
| M5 | 赤になる | production の poll 呼出し自体を置換するため `events=False` stub は通らない。偽 POLLIN で exited が増え、ゼロ件 assert が失敗する。 |
| M6 | 赤になる | G は C の TERM handler 内で生まれ、1巡目 snapshot には存在しない。1巡固定では G の回収・2巡目記録が欠ける。 |
| M7 | 赤になる | readable な非祖先 N が pidfd→TERM、必要なら KILL の対象になり、生存 assert または signal 対象除外 assert が失敗する。 |

指定以外の nodeid も赤になり得ます。例えば M2 は共有 fixture を使う3本と opt-in 正例、M6 は round-limit テスト、M7 は namespace 列挙テストにも影響します。「期待 node 完全一致」は較正なしには申告できません。

## 言えないこと

- 焦点走の TERM 失敗の直接原因。handler、mask、全 records の証拠が不足しています。
- 計算ノード全体での hidepid・namespace readlink 可読性。提示ログは当該走の unreadable=0 を示すだけです。
- PID 再利用を starttime の有限粒度まで含めて完全排除したこと、列挙後の session 変更を原子的に防いだこと。
- namespace 不明・同 namespace の残存、2巡後の fork、session 離脱、子待機が戻らない経路の回収保証。
- zombies は最終列挙で attributed と判定できたものの計数です。namespace 読取り不能の Z まで網羅する保証はありません。
- 同期 trace 出力を含む厳密な時間上限。poll の猶予は協調的上限です。
- M0〜M7 の実測結果、計算ノード事前登録2走の合格、受入全走の緑。今回の焦点走はそれらを代替しません。