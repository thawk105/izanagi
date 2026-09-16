## 所見

必読5件を読了した。以下、`D`＝`tools/pegasus/dispatch_compute.py`、`F`＝`docs/failures.md`、`P`＝指定された `s2-plan.md`。実走・変更はしていない。

1. **A/B/C は条件付きで有効だが、実際の子孫寿命を固定できる設計とはまだ言えない。**
   - **主張:** 75秒は子の終了予定であり、scheduler が保証する生存時間ではない。job 本体終了時に session・process group・cgroup 単位で終了処理があれば、全条件が同じ早期終了になる。
   - **根拠:** D:1112、D:1131 は user/mount namespace を作るが、PID namespace や新 session を作らない。scheduler 側の残存 process 処理はこのコードにはない。M12。
   - **実験設計への影響:** 早期消滅は H1/H2 の反証でなく打切り観測。PID/starttime に加え SID・PGID・cgroup 所属を記録し、実際の生存を条件ごとに確認する必要がある。「記録が途絶えた」だけで scheduler の kill と断定することもできない。
   - **正しさ境界か実効性か:** 因果判定の正しさ境界。
   - **scope 内か外か:** 内。

2. **「全条件75秒で END」は、存在だけによる待機の証明ではない。**
   - **主張:** fd 保持と所属 process 待機が両方の必要条件なら、後者が75秒まで残るため fd 解放の効果は見えない。全条件で保持する観測ファイルなど、第三の参照も残る。
   - **根拠:** P:55、P:102、P:119。全条件で子孫の存在・所属・観測ファイル保持を固定している。
   - **実験設計への影響:** この結果は「この条件では fd 解放だけでは早期 END にならない」まで。H2 全般の refuted や「存在だけが原因」への格上げは不可。逆に A≈J、B≈R、C≈X かつ B の END 後生存が確認できれば、fd 解放の因果効果を強く支持する。
   - **正しさ境界か実効性か:** 正しさ境界。
   - **scope 内か外か:** 内。

3. **親 brief の P1-a/P1-c には、plan が十分展開していない process 構造の差がある。**
   - **主張:** F853 の残存 process は直接の親を timeout で殺された FIFO 待ちの孫である。今回の probe は親が正常終了し、子は sleep する。fd 以外に終了経路、待機状態、pytest の capture、所属が異なり得る。
   - **根拠:** F:23215、F:23218、P:55。M12 の「全子孫が同じ SID/PGID・出力を共有」は、dispatcher の起動指定だけでは全 descendant に一般化できない。途中の wrapper は所属や標準出力を変更できる。
   - **実験設計への影響:** 今回の陰性を F853 の反証にしない。陽性も「この単純構造で成立した機序」として記録する。本番の受入全走への外挿には実際の descendant の capture・所属との対応が必要。
   - **正しさ境界か実効性か:** 正しさ境界。
   - **scope 内か外か:** 比較と結論限定は内。過去条件を再現する hang 変異の投入は不可。

## 実験設計の交絡と対処

4. **fd 1/2 の差替えと、元の出力先への全参照消滅は別である。**
   - **主張:** 子自身の fd 一覧は必要だが、他 process の複製や参照まで否定しない。`readlink` の文字列一致も open file description の同一性の証明ではない。
   - **根拠:** D:1140 は status/exec pipe を渡す。ただし D:229 で両方を非継承に戻し、D:305 の exec に成功すれば probe には残らない。したがって正常な generic probe がこれらを保持するという疑いは、静的には否定できる。
   - **実験設計への影響:** exec 後の初期 fd と差替え後を比較し、fd 番号だけでなく種類・device/inode・参照先を記録する。複製を作る観測コードを避け、差替え用に開いた fd 自身も残さない。祖先の元出力先が読めなければ、NQSV 出力先との同一性は未確認とする。job 全体の参照消滅には dispatcher/supervisor の終了確認も要る。
   - **正しさ境界か実効性か:** 正しさ境界。
   - **scope 内か外か:** 内。

5. **namespace は出力 fd を置き換えないが、外部 process の観測能力を変え得る。**
   - **主張:** このコードは `/proc` を新しい PID namespace 用に mount し直していない。継承 fd の参照先は維持される一方、入れ子 user namespace によって他 process の `/proc/<pid>/fd` 等を読めない可能性は残る。
   - **根拠:** D:271 の mount 操作、D:293 の追加 user namespace、D:1112 の unshare argv。
   - **実験設計への影響:** self の fd と外部 process の存否を別々に記録する。読取り拒否を消滅に数えない。さらに `/proc` に PID があるだけでは実行中とは言えず、starttime と state を確認する。`Z` の dispatcher を「まだ終了処理中」と数えると H3 を誤判定する。
   - **正しさ境界か実効性か:** 正しさ境界。
   - **scope 内か外か:** 内。既存の残存数判定は変更しない。

6. **5秒／15秒の閾値は、時計と観測対象を分ければ使える。現状の根拠は不足している。**
   - **主張:** 会計の `Ended Request Time` と、親が qstat で END を見た時刻は別物。会計との比較に polling 2秒を単純加算する説明は不正確であり、qstat の観測間隔も最大2秒ではない。
   - **根拠:** M2 は正常標本で約−1～0秒。D:600 の scheduler command timeout は30秒、D:4009 は sleep の後に qstat を実行する。D:714 の J は stderr 書込み前に生成される時刻で、process 終了時刻ではない。
   - **実験設計への影響:** 会計時刻の生成元、timezone、compute と会計側の時計差・時刻補正を誤差源に含める。R は差替え完了後、X は終了直前であって終了そのものではないと明記する。各観測に realtime/monotonic の対応を持たせる。誤差が5秒未満と確認できれば閾値は実用的だが、5～15秒は判別保留とする。
   - **正しさ境界か実効性か:** 正しさ境界。
   - **scope 内か外か:** 内。

7. **条件間の観測動作自体を揃える必要がある。**
   - **主張:** 「保持中だけ stderr に解放直前行を書く」と、A/B/C で出力時刻・出力先の負荷が違う。逆順再実施で同じ evidence path を使えば、上書きや過去行混入も起こり得る。
   - **根拠:** P:100、P:102、P:123、P:96。
   - **実験設計への影響:** 子の測定記録は全条件で同じ通常ファイル経路・同じ観測予定に揃え、job stderr への条件依存の追加書込みを減らす。request・条件・反復を識別できる一意の evidence path を使う。hostname と実際の寿命・J の遅延を照合してから反復間を比較する。
   - **正しさ境界か実効性か:** 正しさ境界と観測の実効性。
   - **scope 内か外か:** 内。

## 実現可能性と安全の実測すべき点

8. **probe の配置と提示 argv は、確認した admission／argv 契約に適合する。**
   - **主張:** `tools/probe_t2622_job_exit.py` は F660 の未登録 Pegasus 実行体に当たらない。generic は新規 probe の登録や hash を argv 受理条件にしていない。
   - **根拠:** F:19273 の supersede、`hooks/guard_bash.py:614`、同:1205。main 現物 `/work/1/SFC/tanab/izanagi/tools/pegasus/admission_registry.json:52` も dispatcher を `local-ok` としている。D:1350 は string list、D:1354 は非空の先頭引数だけを要求する。
   - **実験設計への影響:** 提示 argv は静的には通る。compute hostname、request hash/envelope、submission isolation、既存 hold は別の実行条件として残る。generic の `python3` は PATH 解決なので実際の interpreter も記録する。hook の実発火や投入成功まで検証したとは言わない。
   - **正しさ境界か実効性か:** 実行経路の実効性。
   - **scope 内か外か:** 内。

9. **evidence の場所は成立するが、「output 配下なら投入後は何でも書ける」という規則ではない。**
   - **主張:** isolation が read-only にするのは submission directory。兄弟側の `output/insights/...` は、その指定だけでは read-only にならない。
   - **根拠:** D:278、D:281、D:1671。`hooks/guard_write.py:310`、同:319 の保護対象は提示された insights path と異なる。一方、受入待機中の親による同一 worktree への書込みは禁止されている（`docs/pegasus-runbook.md:1117`）。
   - **実験設計への影響:** generic probe 自身の evidence 出力は静的に成立する。親ディレクトリ・権限・symlink 解決先を投入前に確認し、submission directory や保護対象へ解決されないことを確認する。受入全走と並行せず、probe の全書込み終了後に受入へ進む。コード上の一般的な「output 以外を全部禁止する」防壁は確認できなかった。
   - **正しさ境界か実効性か:** 運用境界と実効性。
   - **scope 内か外か:** 内。

10. **120秒 walltime の十分性は静的には証明できない。暫定値は180秒を勧める。**
   - **主張:** 75秒の前に起動 overhead、後に job 終端処理がある。45秒の余白を実測なしに十分とはできない。
   - **根拠:** D:882 の hostname・marker、D:893 の最大3候補の interpreter 起動、D:1556 の guard 作成と fsync、D:271 の mount 群が probe より先に走る。mount は祖先数を n とすると n+3 回で、この深さでは十数回。これらには一律の時間上限がない。
   - **実験設計への影響:** **180秒＝起動予算60秒＋子寿命75秒＋終端余白45秒**を暫定設計値にする。ただし60秒は実測値でなく予算。既存の比較可能な generic job と今回の `t0−Started`、`Ended−X` で点検する。想定超過時は次条件を投入せず再評価し、walltime kill を成功扱いしない。
   - **正しさ境界か実効性か:** 安全な実行の実効性。
   - **scope 内か外か:** 内。

11. **提示された timeout の組合せには、queue 待ち900秒より先に失敗する具体的経路がある。**
   - **主張:** RUN を観測する前も `walltime + overall_grace` の期限が動く。現設定では queue 待ち約420秒で `overall-timeout` になり得る。
   - **根拠:** D:3933 は `submitted_at + walltime_s + overall_grace_s`。D:3977 で RUN 初観測時だけ再設定し、D:4007 の期限検査は queue 中も通る。
   - **実験設計への影響:** これは一般的な scheduler 障害とは別の、計画で減らせる危険。queue 900秒を意図するなら、例えば walltime180秒・overall-grace900秒として期限の先後を整合させる。それでも queue timeout 自体は取消経路に入るため、投入直前の queue 状態確認は必要。dispatcher の実装修正は今回行わない。
   - **正しさ境界か実効性か:** 実効性。
   - **scope 内か外か:** 引数調整は内。

12. **「有限回の観測だから75秒以内に自然終了」は成立しないが、全障害の絶対保証を要求するのも過剰である。**
   - **主張:** 通常ファイルの write、stderr flush、metadata 操作も停止し得る。例外を捕まえても、返らない syscall には効かない。一方、この残余リスクは通常 dispatch にも存在する。
   - **根拠:** P:56、D:691、D:714。異常時 cleanup は D:4283、qsub 結果不明時 hold は D:4208。D:2956 は QUE/HLD 以外の取消を拒否するが、許可 snapshot 後の qdel は D:2990 にある。
   - **実験設計への影響:** 親が満たす水準は以下で十分であり、「絶対に hold がない証明」ではない。
     - 無期限 FIFO・pipe 待ち、hang 変異、walltime kill に依存する終了を含めない。
     - 観測を少量に限定し、fork 前準備後の子の待機は monotonic deadline に揃える。75秒は通常動作時の予定寿命と表現する。
     - detached・直列投入と期限整合を守り、異常時は追加投入を止める。
     - 通常終了・会計・receipt・hold 状態を確認してから次へ進む。

     違反し得る経路は、観測 I/O 停止、起動遅延による walltime 到達、queue/overall timeout、qsub 応答喪失、qstat 障害、親への signal、receipt/hold 永続化失敗。QUE/HLD の snapshot 後に RUN へ遷移する競合もコードだけでは消えない。これらを隠さず、実験が追加する危険と既存の残余リスクを区別する。絶対保証を理由に一律に未承認とする plan の結論は強すぎる。
   - **正しさ境界か実効性か:** 安全性の実効性と説明の正しさ。
   - **scope 内か外か:** 設計・記録は内。回収機構追加は外。

## scope 外の real 所見 (裁定パッケージ候補)

13. **既存 dispatcher の期限・取消契約には、今回と独立して説明すべき点がある。**
   - **主張:** RUN 前の overall deadline と queue timeout は独立で、短い walltime を指定すると queue timeout が先に働くとは限らない。また fresh snapshot は qdel 実行時の state を原子的に固定しない。
   - **根拠:** D:3933、D:3992、D:4007、D:2945、D:2990。
   - **実験設計への影響:** 今回は引数整合と既存運用で扱う。裁定候補は「RUN 前も overall deadline を適用する契約の意味」と「snapshot 後の遷移を含む取消の保証範囲」。事故が今回起きたとは主張しない。
   - **正しさ境界か実効性か:** 期限契約・取消保証の境界。
   - **scope 内か外か:** 契約や実装の変更は外。防壁・回収処理の実装案にはしない。

## 総括

**A/B/C は採用可能な骨格だが、全75秒という結果の解釈、実際の生存確認、時刻誤差、安全性の表現、timeout の組合せを修正してから実装へ渡すべきである。**

P1-b は D:693 の公開後にも directory fsync があるため refuted を維持できない。P1-d の J は process 終了証明ではない。P1-e は保存済み・終了済み標本に限定され、M5 が明示する受入全走級の欠落を越えて一般化できない。加えて、P1-a/P1-c の「全 descendant が同じ出力と所属を保持」という前提は実際の process ごとに確かめる必要がある。

追加探索で `docs/dev-wave/measurement.md` と `docs/dev-wave/author.md` は存在せず読めなかった。必読資料はすべて読めた。pytest・ジョブ投入・ファイル変更は行っていない。