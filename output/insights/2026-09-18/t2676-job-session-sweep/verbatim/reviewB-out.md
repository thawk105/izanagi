## 総括

- **real 2件／refuted 4件／nit 1件。must-fix あり。現状は NO-GO。**
- 焦点走は既に **1 failed, 14 passed in 5.59s**。通常 TERM 終了の検査が赤であり、受入全走へ進める基線が成立していない。
- 提示ログは login-local 実行ではなく、計算ノードへ dispatch した request **5015.nqsv** の結果。
- 必要な production trace、固定定数の配線、M1〜M7 の置換箇所の一意性は確認できた。
- 書込み・テスト・変異実走は実施していない。5分予算内の受入全走、指定 probe 2走の合格は未確認。

## 所見

以下、`DC` は `tools/pegasus/dispatch_compute.py`、`TEST` は `orchestrator/tests/test_pegasus_dispatch_compute.py`。

**RB-1 — real／must-fix：通常 TERM 終了が既に赤。短い猶予と期限を正当化する計測も不足。**
位置：`TEST:7801`、`:7835`、`:7839`、`:7857`。証拠：[focus-new1.log:74](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2676-job-session-sweep/focus-new1.log:74)。

失敗は `orphan` に対応する `after="term"` の終了事象がないこと。fixture 内の `records` が失敗ログへ出ないため、**KILL への移行、signal エラー、再照合時の消失などの区別はできない**。0.5秒の猶予不足が原因と断定してはいけない。

ただし、通常 C の終了観測、late C の handler 実行→fork→G の ready→C 終了を一律0.5秒に収める根拠はない。遅延すると KILL 経路へ進み、`:7857` または `orphan_signals == ["TERM"]` が赤になる。準備3秒は test module 全体の読込み・コンパイル・import も含む。今回その期限を通ったことは、指定の全走負荷での余裕を証明しない。

**放置時の影響：** 現在の赤が受入を阻害し、負荷依存の赤を変異の KILLED と誤帰属する可能性が残る。

是正案：

- 失敗時に `records` 全体、mode、準備・sweep・回収の実所要を残し、今回の赤の原因を確定する。
- 暫定設計値として **準備15秒／sweep20秒／回収10秒**、実 process の **TERM猶予5秒／KILL猶予1秒**を提案する。sweep20秒は2巡の待機最大12秒に走査・同期の余裕を加えた値。負荷下で検証する必要がある。
- 外側と leader 内側の期限をともに変更する。期限延長は固定待機を増やさないが、ignore ケースの TERM 待ちは0.5秒から5秒へ増える。
- 起動を軽くするなら最小 fixture module へ分離する。同じ巨大 module を単に `-m` に変えるだけでは import 負荷は解消しない。
- TERM の期待値は維持し、KILL も許す変更で赤を隠さない。

**RB-2 — real／must-fix：finally は group 全員の終了を確認していない。**
位置：`TEST:7875`〜`:7890`。

`killpg` は L の group 全体へ送るが、`wait()` するのは直接の子 L と D だけ。N/C/G の終了確認はない。L が先に終了すれば、残る process に SIGKILL が pending の段階でも fixture が戻れる。また L の `wait()` が timeout すると、後続の wait・stream close・pidfd close が実行されない。

`unshare --user` はこのコードでは session／process group を変更しないため、C/G が送信対象から外れる問題ではない。**送信と全員の終了確認の違い**である。

**放置時の影響：** 失敗・変異時の子孫が次の検査や job 終端まで残り、受入所要や残存計数に影響し得る。

是正案：N/C/G を含む fixture 所属 process の pidfd を確保・追跡し、KILL 後は共通の回収期限まで終了を確認する。各 wait が失敗しても残りの後始末と fd close を継続する構造にする。非子の reap は init に任せ、subreaper は追加しない。

**RB-3 — refuted：準備同期が欠け、未準備の C/G を走査する。**
位置：`TEST:7746`、`:7758`、`:7784`〜`:7792`。

ignore の `SIG_IGN` 設定、late の handler 設定は PID 通知より前。leader は PID 通知を受け、短命親 P の `wait()` を完了してから ready を返す。pytest が C の pidfd を開いて「s」を送り、その後 scanner が起動する。

late の G は `SIG_DFL` 設定後に ready を書き、C はそれを読んでから終了する。C/G の標準入出力は DEVNULL で、leader の標準入出力 pipe を保持しない。

影響：準備順序の欠落による赤という疑義は棄却できる。
是正案：この同期を維持する。F973 の原因だった production の reparenting 変更も今回の差分にはない。ただし RB-1・RB-2 は別途対応が必要。

**RB-4 — refuted：裁定§3に必要な trace が欠ける／`time_ns` が二重指定で壊れる。**
位置：`DC:715`、`:791`、`:815`、`:834`、`:895`、`:929`、`:1371`、`:1905`、`:4713`。

正常経路には必要な事象・項目が揃う。

| 指標 | 出力 |
|---|---|
| W | `supervisor-wait-complete` |
| S | `session-sweep-start`、sid・own_user_ns・ancestors |
| residual | `round`、`process` 内の pid・ppid・comm・state・uid・starttime・user_ns・attributed 等 |
| T | `session-signal`、TERM・result・明示 time_ns |
| G | `session-process-exited`、after・明示 time_ns |
| C | `session-sweep-complete`、elapsed_ms・status・各 count |
| J | `job-run-returned` |

`_job_trace` の辞書は既定値の後に `**fields` を展開するため、明示 `time_ns` が優先される。関数引数の重複エラーではない。対象 PID は `process.pid`、最上位 `pid` は発行者。

T は送信処理後の記録時刻、G は pidfd の終了観測時刻。他の既定 `time_ns` は事象発行時刻であり、厳密な死亡時刻ではない。

影響：この疑義による trace 追加は不要。
是正案：判定側は `process` の入れ子と時刻の意味に合わせる。同一 PID が複数巡に出るため、residual の行数をそのまま個体数にしない。

**RB-5 — refuted：短縮猶予が production に流入し、既存テストの契約も壊す。**
位置：`DC:171`、`:931`、`:1129`、`:1847`、`TEST:2312`、`:4086`、`:4571`、`:7968`。

production wrapper は定数5.0／1.0／2を渡し、その値をテストが assert している。env／request／CLI から猶予や巡数を変更する配線はない。fixture の短縮は scanner 子内の private helper 呼出しに限定される。

追加引数は keyword-only、既定値は `None`。既存 caller の呼出し形は維持される。連続 export の assert は生成順と一致する。厳密な fsync 事象列を検査する2件は `_write_result_replace` を直接呼ぶため、sweep の追加対象外。wrapper 自体も SHA 不一致なら trace を出さず戻る。

影響：静的には、この変更を理由とする既存期待値の修正は不要。
是正案：既存 consumer の実走結果を別途確認する。

**RB-6 — refuted：keep の帰属判定は成立せず、計算ノードでは常に unreadable で失敗する。**
位置：`DC:743`、`:775`、`:800`、`:890`、probe `:276`。証拠：`focus-new1.log:143`〜`:153`。

keep は bootstrap 内で fork し、子は親の user namespace を継承する。dispatcher の init namespace と異なるため、外側から namespace を読めれば帰属述語に一致する。陽性対照 trace も probe の入れ子 namespace を示す。

別 session の process は、stat が読めれば namespace 読取り前に除外される。他ユーザーの namespace が読めないだけで全走が error になる構造ではない。一方、**stat 自体が読めない process は所属不明として記録され、最終列挙に残れば error**となる。

提示焦点走では production が実際に `found_total=0`、`unreadable=0`、`status=clean`、`elapsed_ms≈33.76`を出した。W→J は約0.141秒。候補0では poll も sleep も行わない。

影響：計算ノードでの成立不能という疑義は棄却できる。
是正案：指定の no-child／keep 2走では判定表をそのまま適用する。この焦点走を probe no-child の代用にはしない。

**RB-7 — nit：時間短縮のため実 process 3本を1本へ統合する案。**
位置：`TEST:7893`〜`:7902`、`focus-new1.log:74`。

ログの5.59秒は **15件全体**の pytest 所要であり、新規14件だけの合計や各 process テストの時間ではない。受入全走の追加 wall timeへ直接換算できない。

mode をループするだけでは起動回数は減らず、同一 session で同時処理すると ignore の待機が他ケースの観測順序も変える。単一 nodeid 化は事前登録した M2/M4/M6/M7 の帰属も変更する。

放置時の影響：3本のままであることによる具体的な予算超過は未確認。
是正案：3 nodeid を維持し、最小 fixture module の共有を優先する。各段所要と受入全走 wall time を測り、300秒以内か判定する。

## 変異の一意性

`s5-author-out.md` の変更前文字列を production 全体で固定文字列検索した結果、**M1〜M7 はすべて1箇所**。

| 変異 | DC行 | 変更前 → 変更後 | 構文の目視判定 |
|---|---:|---|---|
| M1 | 1906 | `_maybe_sweep_job_session(request_sha256)` → `pass` | if 本体が残り成立 |
| M2 | 928 | `excluded = {ancestor["pid"] for ancestor in ancestors}` → `excluded = {os.getpid()}` | 成立 |
| M3 | 908 | SHA／env 判定行 → `if False:` | 成立 |
| M4 | 877 | `_signal_session_process(fd, record, signal.SIGKILL)` → `pass` | for 本体が残り成立 |
| M5 | 809 | `events = poller.poll(math.ceil(remaining * 1000))` → `events = [(fd, select.POLLIN) for fd in pending]` | 成立 |
| M6 | 829 | `for round_index in range(rounds):` → `for round_index in range(1):` | 成立 |
| M7 | 775 | `attributed = user_ns is not None and user_ns != own_user_ns` → `attributed = True` | 成立 |

M2 は L の死亡ではなく、`:7843` の除外集合 assert で検出する実装。`:7969` も赤になり得るため、期待 nodeid 完全一致には事前登録どおり較正・drift mask が必要。M6 は1巡にすると G の回収がなくなり、remaining／2巡目の assert で検出する構造である。

**基線が赤の通常 TERM テストを、現状のまま M2/M7 の KILLED 証拠にはできない。**

## 言えないこと

- 今回の TERM 検査の赤が0.5秒の猶予不足によるものか。fixture 内 trace が必要。
- 3秒の準備期限が指定の全走負荷で必ず不足すること、また提案した期限なら必ず足りること。
- 受入全走の緑・300秒以内、指定 probe 2走の両軸合格、M0〜M7 の実測結果。
- finally の残存が今回の実走で発生したこと。確認できたのは終了確認の欠落。
- 他ノード・他時点でも `unreadable=0` になること、generic 単一子の結果が実 workload 全般を代表すること。

自動実行審査 `guard_bash` は、文字列置換後の AST を検査する読取り専用 Python コマンドを「Pegasus ログインノード上の未登録実行体」として拒否した。変異後 AST の機械検査は未実施であり、一意性は `rg`、構文は目視で確認した。