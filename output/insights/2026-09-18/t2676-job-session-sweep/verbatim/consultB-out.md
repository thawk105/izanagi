## 総括

- **real 5件／refuted 4件／nit 2件。must-fix あり**（B-1〜B-4）。
- 親 brief への異議は **4件**。方針の全面撤回は不要だが、観測からの断定と完了条件を修正する。
- `keep`／`no-child` の2走は、限定した generic 単一子条件の検証には足りる。実 workload 全般や計算ノードの SIGKILL 経路の実証にはならない。
- `E−J` と消滅確認の分離、`child-exit` 不在の事前許容、`_job_run` 経由のテストは plan に既にある。
- 問題は heartbeat の時刻境界、M6 の検出保証、総遅延の合否条件、実 process テストの時間予算である。
- 指定資料による静的レビュー。書込み・テスト・計算ノード投入は実施していない。

## 所見

以下、`plan-out.md`・`facts.md`・`s1-brief.md` は指定された T-2676 job dir 内、`probe` は指定された T-2675 の Python ファイルを指す。

**B-1 — real／must-fix：heartbeat の判定境界が signal より前にある。**
位置：`plan-out.md:242`、`probe:122`、`probe:249`。

`session-signal-attempt` の記録から実際の `os.kill` までに子が heartbeat を記録できる。したがって「最終 heartbeat ≤ attempt 時刻」は、TERM で正常に終了した走でも偽になり得る。signal の送信成功も、その瞬間の死亡を意味しない。

**放置時の影響：** 回収・会計終了とも成功した走を失敗と分類し、レポートの結論や追加実測の所要を変える。

是正案：attempt、送信結果、独立した消滅確認の時刻を別々に残す。heartbeat は「最終記録 ≤ 消滅確認時刻」を整合性条件とし、attempt との前後関係は記述統計にする。厳密な「TERM 時刻以前に最後の heartbeat」を必須にするなら、現器具では保証できないことを事前登録する。

---

**B-2 — real／must-fix：M6 は再列挙の欠落を確実に検出する変異になっていない。**
位置：`plan-out.md:77`、`:80`、`:198`。

TERM 後の再列挙だけを初回 snapshot に置き換えても、KILL 後の再列挙で新しい子を発見し、2巡目で TERM・消滅確認できる。現行の「新しい process が処置された」という assert は、この変異でも緑になり得る。

**放置時の影響：** 事前登録した M6 が SURVIVED になるか、変異後に test を合わせることになり、変異台帳の帰属が崩れる。

是正案：

- M6 が問う契約を「特定時点の再列挙」か「後発 process を回収すること」かに固定する。
- 後者なら、後発 process の処置を一行で無効化する実装箇所を author 後に選び直す。正当な冗長経路を残した一行削除に KILLED を要求しない。
- 全変異を、対象 file・関数・確定行番号・変更前後の一行・対象 nodeid で、実行前に固定する。M5 の「最終確認用 stat 読取り」も実装形状との照合が必要。

---

**B-3 — real／must-fix：総終了遅延は記録されるが、成功判定の閾値になっていない。**
位置：`s1-brief.md:6`、`plan-out.md:149`、`:234`、`:251`。

plan は `E−J` だけでは sweep 内への遅延移動を見逃すと認識している。しかし判定表は sweep が13秒以内なら通り、`supervisor-wait-complete` から E までの時間は併記に留まる。TERM 既定動作の keep が約13秒かかった場合も「終了遅延が消えた」とまとめられる。

**放置時の影響：** 遅延の一部を前段へ移した結果を解消と報告し、受入 shard ごとの追加所要を過小評価する。

是正案：下記判定表のように `W→J` と `W→E` の数値条件を加える。通常 TERM 終了と、5秒猶予を使う SIGKILL 経路を別の期待値にする。残存0では待機しないことも必須にする。

予算の概算は、同時に送信して待つ実装なら process 本数ではなく巡数に依存する。

| 経路 | job 1本への追加所要の設計値 |
|---|---:|
| 残存0 | 列挙・trace のみ |
| TERM で即時消滅 | 列挙・poll・確認の所要 |
| TERM 無視、1巡 | 約5秒＋KILL確認最大1秒＋走査 |
| 2巡を使用 | 協調的予算13秒まで |

13秒は300秒の **4.3%**。元の job が287秒近辺なら、sweep だけで5分枠を超え得る。新規テスト所要は別途加算される。

---

**B-4 — real／must-fix：実 process テストの「各2秒」は、起動・回収を含めた負荷耐性の根拠がない。**
位置：`plan-out.md:172`、`:174`、`:179`、`:181`。

TERM 猶予0.1秒、KILL確認0.3秒、全体2秒は、process が runnable になる遅延や init による zombie 回収待ちに左右される。pipe 同期は準備不足を防ぐが、その同期自体の timeout は別問題である。また、短命親 P は leader L の子なので、P の終了通知だけでなく **L による P の wait 完了**を同期しないと fixture 自身の zombie が混ざる。

**放置時の影響：** 焦点走では緑でも負荷下の受入全走で timeout／残存判定が赤になり、F973 と同じ検証上の失敗を繰り返す。

是正案：

- 起動・準備、sweep、finally の回収に別の期限を設け、2秒を正常所要の目標と絶対打切り期限で兼用しない。
- TERM 無視 handler の設定完了と、P の wait 完了を同期する。
- 短い猶予の注入は私有 helper の引数に限る。production wrapper は固定の5秒を渡し、CLI・request・env から変更できる経路を作らない。
- production の5秒・2巡・13秒の配線を fake clock／mock で検査する。実 process テストだけを短縮しても production 定数の検証にはならない。
- 正常時の追加所要は数秒を見込めるが、受入全走が300秒以内になることは資料だけでは確定できない。全走の実 wall と新規 nodeid の所要を測る。

---

**B-5 — real：F-1 の祖先断定は提示された trace からは導けない。**
位置：`facts.md:8`、`s1-brief.md:33`、`plan-out.md:276`。

trace は dispatcher PID、probe の SID・PPID、supervisor PID を示すが、dispatcher から session leader までの祖先鎖は示していない。PID と SID が異なることだけでは、session leader が現存する祖先であることや、NQSV process の役割までは証明できない。

**放置時の影響：** レポート・decisions に未観測の祖先関係を実測事実として残し、「非祖先は回収対象でよい」という設計判断の証拠を過大にする。

是正案：F-1 を「dispatcher は session leader ではない。祖先関係は未採取」と訂正する。祖先除外方針は維持してよい。今回構築する祖先鎖を trace に残せば、追加走なしで確認できる。no-child の未知の非祖先残存は成功から除外せず、期待外として扱う。

---

**B-6 — refuted：5秒猶予があるため `E−J ∈ [−1,5]` に入れない。**
位置：`plan-out.md:76`、`:146`、`tools/pegasus/dispatch_compute.py:4499`。

J は sweep 後であり、TERM 成功時は5秒を待ち切らない。SIGKILL に進んでも猶予は J より前なので、`E−J` の窓は同じでよい。

影響：この疑義を理由に会計窓を広げる必要はない。
是正案：増えるのは `W→J`／`W→E` であると表に明記する。

---

**B-7 — refuted：`child-exit` 不在の keep は事前契約上すべて不適格になる。**
位置：`plan-out.md:245`、`:247`、`probe:254`。

plan は TERM 終了時に `child-exit` を要求しないと明記し、heartbeat 0件も事前に許容している。自然終了専用の記録を要求しない判断は妥当である。

影響：旧 wave と同じ適格性の事後変更は、この点では生じない。
是正案：この規則を投入前の insight にそのまま固定する。記録途絶だけで成功とせず、同一個体の消滅確認を必須にする。

---

**B-8 — refuted：sweep 呼出しを入れ忘れても、計画されたテストはすべて緑になる。**
位置：`plan-out.md:166`、`:183`、`:193`、`orchestrator/tests/test_pegasus_dispatch_compute.py:4156`。

helper は実際に `_job_run` を呼ぶ。M1 をその呼出し行に当て、sweep 呼出しと result 公開の順序を assert すれば欠落を検出できる。

影響：追加の実 process 統合テストを必須にする理由にはならない。
是正案：wrapper 自体を mock すると opt-in 判定を迂回するため、env 有無を検査するケースでは wrapper を実行し、内側の sweep を mock する。result・guard の実体も照合する。

---

**B-9 — refuted：計算ノードで SIGTERM 無視の追加1走が必須である。**
位置：`plan-out.md:160`、`:251`、`D2124.md` の確定範囲。

今回の結論を「generic 単一子・TERM 終了」に限定するなら、追加走は必須ではない。実 process テストは通常終了と SIGKILL の機能を検証できる。ただし計算ノードでの SIGKILL 成功を実証したとは書けない。

影響：限定した完了条件なら2走の予算を維持できる。
是正案：計算ノードの SIGKILL 経路まで完了条件に含める場合だけ、Codex author に TERM 無視条件と準備完了記録を追加させ、別 hash・別 evidence・別判定表で追加1走を事前登録する。既存 probe の同一性を主張したまま改変しない。

---

**B-10 — nit：行番号と再列挙理由に誤記がある。**
位置：`facts.md:17`、`:18`、`:23`、`s1-brief.md:40`。

isolation 失敗 return は `dispatch_compute.py:1685–1687`、child 分岐は1647以降、env pop は1625以降である。plan は主要な配置誤りを既に補正している。reparenting で SID は変わらず、再列挙の主要目的は新規 fork の捕捉である。

影響：現在の plan に従えば成果物・受入への具体的差はない。
是正案：親資料を現行アンカーと plan の説明へ合わせる。F-2 の「session 走査が唯一の経路」も「今回採る経路」に弱める。

---

**B-11 — nit：実測後の後始末と orphan hold 確認が手順として不足する。**
位置：`plan-out.md:208`、`:232`、`:257`。

probe 非 commit 方針はあるが、保全・削除・status 確認の順序と、receipt に加えて orphan hold を確認する手順が明文化されていない。

影響：方針違反や hold 発生の証拠は現時点でなく、具体的な結果差は未確認。
是正案：probe を job dir に保全・照合して worktree から除き、成果物を意図的に stage した後、`git status --short --untracked-files=all` で `??` が0件であることを確認する。無関係な untracked は削除しない。orphan hold は対象 request の終端時状態として記録し、「一度も発生しなかった」と拡大しない。

## 判定表の提案

以下を**投入前に採択・固定**する。追加する時間閾値は実測由来ではなく、今回の受入仕様として提案する値である。

- `W`：dispatcher の `supervisor-wait-complete`
- `S`／`C`：sweep 開始／終了
- `T`：対象への TERM attempt。送信結果時刻も別に記録
- `G`：同一 `(pid,starttime)` の独立した消滅確認
- `J`：`job-run-returned`
- `E`：対応する `.e` の `Ended Request Time`。JST・秒精度を明記
- `H`：最後に保存された子 heartbeat の記録時刻

| 指標 | no-child | keep：TERM 終了 | SIGKILL 経路の期待・扱い |
|---|---|---|---|
| 初回残存 | 0 | 1、probe 子と同一 | 既定2走で現れれば期待外 |
| signal | なし | TERM 成功、KILL なし | TERM→猶予→KILL 成功 |
| 終了確認 | 対象なし、読取り不明なし | `G≤C≤J`、寿命75秒より前 | KILL 後に同じ確認が必要 |
| 最終状態 | 生存・Z・不明・離脱0 | 同左 | 残存・不明・離脱は成功にしない |
| `E−J` | [−1,5]秒 | [−1,5]秒 | 回収済みなら同じ窓 |
| `J−W` | 5秒以内 | 5秒以内 | 別登録走なら18秒以内を提案 |
| `E−W` | [−1,10]秒 | [−1,10]秒 | 別登録走なら[−1,23]秒を提案 |
| sweep 所要 | 待機なし、全体予算内 | 早期終了、全体予算内 | 1巡で約5秒＋確認、2巡でも協調的予算13秒 |
| heartbeat | 子記録なし | 0件を許容。存在すれば `H≤G` | TERM 後の heartbeat は許容、`H≤G` |
| `child-exit` | 該当なし | 不要 | 不要 |

13秒は kernel 内の停止や同期 trace 書込みまで保証する絶対上限ではない。18秒はその13秒に result 公開等の許容5秒を加えた**合否上限**であり、実行保証ではない。

共通の適格性・手順：

1. 同一 worktree・同一コードで **no-child→keep を直列実行**し、前走の receipt・会計・evidence 確認を完了してから次を投入する。
2. probe の SHA-256 と30,373 bytes は現物と一致した。各走の evidence は新規の worktree 相対パスとする。probe は `O_APPEND` なので、既存ファイルへの追記で別走を混ぜない。
3. request ID、submission dir、host、probe 条件、J、E を対応付ける。`terminal_reason=scheduler-end-state`、`accounting_verified=true`、`qdel.attempted=false`、正常 rc、対象 orphan hold なしを確認する。
4. child-start と residual の同一性、完全な記録、記録異常なしを確認する。TERM 中断による記録欠損も事後に許容せず「判定不能」にする。
5. 会計窓外、残存、期限到達、EPERM は**観測された不成功／期待外**として残す。単なる「不適格」として成功集計から消さない。
6. `00:03:00` は正常時約5秒、無効時の自然寿命75秒、既存 alarm の余裕を含む器具として妥当。ただし割込み不能状態への保証ではなく、queue 待ち・会計待ちを含む壁時計の3分保証でもない。

結論は二軸で記録する。

| 会計・総遅延 | 独立した消滅確認 | 結論 |
|---|---|---|
| 合格 | 合格 | 当該条件で終了遅延短縮と残存消滅を確認 |
| 合格 | 不合格／不明 | 回収成功とは言わない |
| 不合格 | 合格 | 回収成立、終了遅延の目的未達 |
| 不合格 | 不合格／不明 | 対策成立を示せない |

## 親 brief への異議

1. **P1 の根拠の強さ**：祖先除外には賛成だが、「session leader が NQSV 側の現存祖先」は未観測。B-5 の訂正が必要。
2. **P4 の値の扱い**：5秒・2巡は暫定値として採れるが、必要十分性や最適性は未実測。plan が加えた KILL確認1秒、全体13秒、poll 50ms も設計値である。テストの0.1秒・0.3秒・2秒も未実測。
3. **P5／完了判定**：`E−J` だけで終了遅延解消としない。総遅延条件と B-1 の heartbeat 修正が必要。[−1,5]秒は過去の分類窓であり、変更後の保証値ではない。各条件1走・反復なしも予算上の判断である。
4. **P6 の確定時点**：author 前に意味と期待を登録し、author 後・変異実行前に実行可能な一行 patch と nodeid を固定する二段階が必要。M6 は現在の形では確定できない。

P2 の env pop、P3 の result 前配置は妥当。P7 の uid フィルタ省略について、本レンズでは反対する実測根拠はない。ただし EPERM を捕捉することは回収成功の証拠にはならない。

F-5 の164 worktree・競合なし・pin なしは、今回指定された資料だけでは再確認していない。F-6 の probe hash・bytes・heartbeat・TERM handler 不在は確認できた。

## 言えないこと

- 単一 Python 子の keep は、FIFO で block した孫、多数の孫、xdist worker、TERM handler 付き process、割込み不能 I/O を代表しない。受入全走が緑でも、それらの残存条件を実際に通った証明にはならない。
- dispatcher 側では、runner の終了待ち→supervisor 終了待ち→sweep の順序を確認できる。通常終了済み pytest の assertion を後から sweep が赤にする経路はない。一方、**xdist の異常終了時も全 worker の teardown が完了していることまでは、指定資料から確認できない**。取り残された worker は回収対象になり得る。
- 今回は reparenting を変えないため、F973 の subreaper による zombie 滞留と同じ変更ではない。ただし短い timeout・`/proc` の消滅待ちによる負荷依存の赤は残る。
- `/proc` 不在・identity 変更は追跡個体の消滅を示すが、TERM が唯一の死因だったことや厳密な死亡時刻までは示さない。heartbeat 途絶だけでは死亡を示さない。
- 別 session に移った process、sweep 到達前に runner が戻らない経路、全ノード・全負荷での時間上限は対象外。
- sweep 失敗時も child rc／result を保持する設計なので、**受入全走の緑だけで回収成功を判定してはいけない**。job 終端・会計・sweep trace を併せて報告する。