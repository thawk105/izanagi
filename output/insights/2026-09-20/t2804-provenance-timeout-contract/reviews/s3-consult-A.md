## 所見

以下、`plan` は [s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2804-provenance-timeout-contract/codex/s2-plan.md)、`brief` は [s1-brief.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2804-provenance-timeout-contract/s1-brief.md)、`dispatcher` は `tools/pegasus/dispatch_compute.py` を指す。

1. **real / must-fix — 全経路で「480秒より前に receipt 保存・return」は保証されない。** `plan:75,114`、`dispatcher:2303,3664,3876,3916`。**放置時：条件付きの運用予算を完了保証と扱い、SIGKILL・receipt欠落・hold残留が再発する。**

   `D=deadline_at=t0+448`、dispatch呼出し時刻を `t=t0+e` とすると、

   ```text
   Q = min(Q_existing, 178−e)       # M_pre=180
   Tq = t+p+Q+δ
   D−Tq ≥ 90+180−p−δ
   ```

   `p+δ≤180` なら、queue timeout検出時にcleanup用90秒を残す算術は正しい。ただし **予算が残ることと、cleanup・保存が完了することは別**。

   | 経路 | 実コードによる結果・残り物 |
   |---|---|
   | queue超過 | `4215`で検出しcleanupへ。fresh QUE/HLDで取消成功ならjob・holdを解消可能。RUNへの遷移、観測失敗、qdel失敗ならjob残留の可能性とholdが残る。 |
   | RUN超過 | `4207`の再基準後も `min(RUN初観測+W+G,D)`。D到達時はcleanup予算0、`3103`でqdelを拒否しholdへ。RUN jobは自然終了まで残り得る。 |
   | collection超過 | `4245`の `min(now+A,D)`。Dが先ならcleanup予算0となり、END観測済みでもfresh END確認へ進めずholdになり得る。marker欠落では `4303`のsubmission-disabledも残る。 |
   | qsub非ゼロ終了 | `4035`で結果不明を解除、activeにはならず、通常はreceipt保存後にpendingを解除してrc=16。保存失敗・停止ではpendingが残り得る。 |
   | qsub結果不明 | `4422`でjob残存可能としてholdへ昇格しdiscovery。jobの有無は不明、holdは残る。 |
   | checkerで投入前拒否 | dispatcher未呼出しなので新規job・hold・dispatcher receiptはない。receipt不在は設計どおり。 |
   | dispatcher前段で枯渇 | preflight以前ならjobなし。pending作成後、`4014`以降で期限切れになると、qsubを実際には起動できなくても結果不明経路に入りholdを残し得る。 |

   見落としてはいけない既存保護は `3664–3683`：schedulerコマンドは `timeout=min(requested,D−now)`、sleepもDで制限される。したがって「qstatが常にDを30秒超過する」という指摘は **refuted**。

   一方、`2303`のblocking `flock`、holdの書込み・fsync、`3540`のreceipt保存、collectionのファイル読取りはこの制限の外。保存が失敗すればreturnできてもreceiptは欠落する。`R_post=32`では全経路保証にならない。

2. **refuted / — 「許可された予算伝播だけではRUN holdを必ず防げない」は正しい。** `plan:94–102`、`dispatcher:3103,3179,3916`。**影響：この限定を維持すれば、queue改善をRUN残留の解消と誤認しない。**

   Dを前倒ししてもcleanup締切も同時に動く。W/G等でDより早く監視を打ち切ってcleanup時間を残しても、fresh RUNはqdel対象外。dispatcher不変で、投入した任意のRUN jobについてholdなしを保証する追加策は確認できない。

   **確率の数値化は判定不能。** `plan:100`は中央値30.7秒、新checkerの24〜42秒を上限保証とせず、ここは妥当。RUNでDに掛かる条件は概ね、

   ```text
   e+p+q+RUN所要 ≥ 448
   ```

   旧checkerの475.9秒は通常の前段・queueでも該当する。一方、新checkerの観測範囲は十分短いが、cap_oomで先に消費した時間や観測母集団の偏りを含めた発火確率は出せない。85件をそのまま新checker・landの確率母集団にはできない。

3. **real / must-fix — landとcheckerの時計の起点差が式にない。** `plan:17,42,56,118`、`tools/check_ai_provenance.py:3551,3588,3617,3648`、`tools/dev_wave_land.py:3561`。**放置時：起動遅延の分だけ実効余裕が減り、内側期限が外側kill期限より後ろになることもある。**

   landのtimeout計測起点を `L`、checkerのmain先頭を `t0=L+s` と置けば、

   ```text
   K = L+480
   D = t0+448 = K−32+s
   K−D = 32−s
   ```

   D後の処理時間を `h` とすると必要条件は **`s+h<32`**。planの `448+16<480` は `s` を落としている。

   site判定・headroom評価・queue観測・cap_oom前のlocal監査は、planどおりmain先頭から測れば `e` に含まれる。これらが丸ごと未控除という疑いは **refuted**。しかしmain到達前のinterpreter起動・import等には有限の上限をコードから導けず、spawn全体を単純に固定秒へ換算することもできない。

   また、admissionやlocal scopeの実行自体をこの予算が中断するわけではない。cap_oom後に到達できれば残余拒否できるが、その前にlandがkillする経路は残る。

4. **refuted / — D612が却下した自動選択(2)とは別物。** `verbatim/D612.md:9,19`、`plan:125,135,138`。**影響：明示予算の上限制約という境界を維持すれば、D612の却下案を復活させない。**

   D612の却下案は、argvの形から所有・残余TTLを推測して既定値を選ぶものだった。今回は呼び手がこのinvocationの外側予算を明示し、未設定時の既定値を維持する契約である。

   ```text
   Q_effective = min(Q_explicit,Q_derived) ≤ Q_explicit
   ```

   よって明示上書きは緩まない。Gも値自体は維持し、Dとのminで実効期限だけ短縮する。ただしQ=0等を投入前拒否へ変えることは、緩和ではなく受理集合の縮小として記録が必要。

5. **real / must-fix — P1をD2148項8の実装と呼ぶのは不整合。** `brief:52–54`、`verbatim/D2148-item8.md:4`、`verbatim/T-2484-ruling-package.md:9`、`tools/mutation_harness.py:1446–1453`。**放置時：内側期限を維持する裁定を、内側期限を短縮する新方針に無断で読み替える。**

   項8は明示的に(a-1)+(a-3)を採り、

   ```text
   外側予算 ≥ P+Q+W+G+A+C
   ```

   とする。実装も `max(spec,区間和)`。一方、planはQと実効RUN・collection期限を短縮する。dispatcherの**ソースと既定定数が不変でも、この呼出しの期限は不変ではない**。

   T-2804起点が求めるのは「両立契約を決めること」であり、480秒固定を既に裁定したものではない。480秒固定の限定契約を採るなら、項8の単純実装ではなく、land固有の受理集合縮小・残留リスクを伴う選択として返す必要がある。

6. **real / should — kwargs恒等の計画はあるが、既存helper呼出し互換の明記が不足。** `plan:15,16,175,216`、`orchestrator/tests/test_t2337_dispatch_timeout_overrides.py:191,216,241`。**放置時：`started_at`を必須引数にすると既存suiteがTypeErrorで壊れる。**

   env未設定時に既存辞書だけを渡すならkwargs恒等は成立し、`plan:175`のexact比較で固定できる。引数辞書に「bytes同一」という性質はなく、ここではkey・値のexact一致を要求すべき。

   meta-testの実体は `:48–57`のparser結果比較であり、ソースbytes比較ではない。parser不変更ならこの部分は維持できるが、同ファイルは `_default_dispatch(argv)` と `_invoke_dispatch(None,argv)` も直接呼ぶ。新引数は省略可能にする等、互換契約が必要。新envを消すfixtureも明示する。

7. **判定不能 / — briefの閾値別件数は、指定probe出力だけでは完全検算できない。** `brief:21`、`probe/dispatch-stats-1.txt:6–8,52–67`。**影響：未検算の「0件／厳密に2件」が定数選択の根拠として残る。**

   probeには全85件の合計値も閾値別集計もない。確認できるのは少なくとも次の2件が480秒を超えること。

   ```text
   旧checker: queue 5.2 + RUN span 475.9 = 481.1秒以上
   本日例:    queue 716.4839 + span 40.9599 = 757.4438秒以上
   ```

   briefの482.3／758.6秒はこの下限と矛盾しないが、完全な合計値とは再照合できない。したがって「>480がちょうど2件」「375〜480が0件」は確定できない。

   **real / should — 母集団の限界がbriefに明記されていない。** `brief:13,21`。**放置時：残存する資料の85件を、撤去済みwaveやkill例を含む全履歴へ一般化する。**

   「残存main/worktreeの探索範囲」「撤去済みwaveを含まない」「旧新checker・range指定・rcが混在」を明記すべき。`no receipt:0`も探索範囲内だけの結果。

   **real / should — SIGKILLの説明は成立条件を補う必要がある。** `brief:26–27`、`dispatcher:2469,4002,3876,4525`。**放置時：qsub前やjob終端後のkillまで、必ずjobとpendingが残ると誤読する。**

   pendingはqsub直前にdurable化され、通常はreceipt保存後に解除される。したがって「投入済み・未終端、pending未解除でSIGKILL」ならbriefの説明は裏付けられる。SIGKILLは例外処理・`_return_infra`を走らせないが、全kill時点でjob残存を断定はできない。

8. **real / should — M_pre=180の移植は、受理集合への費用を評価していない。** `plan:44,75–84`、`tools/mutation_harness.py:1446`、`probe/dispatch-stats-1.txt:59`。**放置時：従来480秒以内に成功したqueue待ち278.7秒の例を、新たに失敗へ変える。**

   harnessの180秒は外側を延ばす余裕で、今回は固定480秒からqueue予算を削る余裕。効果が逆であり、そのままの移植根拠にはならない。

   | 条件：B=480、e=10 | M=180 | M=60 |
   |---|---:|---:|
   | 導出Q | 168秒 | 288秒 |
   | `15.9+5=20.9`秒に対する倍率 | 8.61倍 | 2.87倍 |
   | queue検出時のDまでの残余※ | 249.1秒 | 129.1秒 |
   | C=90を除く追加余裕※ | 159.1秒 | 39.1秒 |
   | queue 278.7秒の既知成功例 | queue timeoutへ変わる | queue条件を通過可能 |

   ※`p+δ=20.9`を仮定。qstat所要等の上限証明ではない。

   60秒でもこの仮定下ではcleanup90秒を残す。ただしQが278.7秒以上になる条件は `e≤19.3`。eが大きければ60秒案でも落ちる。

   85件全体の**厳密な成功→失敗件数は判定不能**。表示された例では180秒案にqueue由来の追加失敗が少なくとも1件あり、60秒案ではその1件を回避できる。旧checkerの475.9秒RUN例は双方でDに掛かるが、元からlandの480秒にも収まらない。これを新規退行と混ぜて数えてはいけない。

   また、`Q_min=16.6`はqueue所要ではなくqsub後合計の観測最小値（`plan:46,151`）。「これ未満では実行不能」ではなく、経験的な投入拒否方針として別途根拠を示す必要がある。

9. **real / should — 注入seam変更は不要で、提示された代案が既存pinをよりよく保つ。** `plan:24–33,190`、`tools/check_ai_provenance.py:2895`、`orchestrator/tests/test_check_ai_provenance.py:5541,5660,6777`。**放置時：既存fakeの契約を変更し、予算導出に無関係なテストまで修正する。**

   推奨接続は次。

   ```text
   dispatch_fnあり → 現行どおり dispatch_fn(argv)
   dispatch_fnなし → _default_dispatch(argv, started_at=共通起点)
                   → dispatch_compute.dispatch(argv, **kwargs)
   ```

   新規テストは末端の `dispatch_compute.dispatch` をmonkeypatchし、`main`へdispatch_fnを渡さずforce／headroom_short／cap_oomを通す。これで既存argv-only pinを保存しつつ、本番の導出経路を3本とも検査できる。cap_oomではfake clockをscope中に進め、起点が再設定されないことも固定する。

## 親 brief への指摘

- P1の「内側の全締切を外側以下にすれば項8を保つ」は撤回が必要。cleanupと監視が同じDに切られるため、全区間を確保する契約にもなっていない。
- §(a)の閾値集計は再計算可能な全件表または集計出力を添える。それまでは未検算とし、母集団の欠落・混在を明記する。
- §(b)の残留説明を「投入後・解除前のkillでは残り得る」へ限定する。
- §(c)のmeta-testはbytes比較ではなく結果比較。
- P4について、planがqueue/RUNをcheckerの診断から外した理由は妥当。dispatcherの戻り値だけでは区間値を取得できないため、brief側もreceiptを権威とする記述へ合わせる。

## plan v2 に入れるべき変更

1. **保証を分ける。** queue取消に余裕を残す条件付き契約、RUN／collectionのhold残留、receipt永続化の非保証を別々に記す。
2. **時計を呼び手へ結び付ける。** 同一ホストのland側で取得したmonotonic期限を伝播する案を優先する。秒数480だけを渡す案を続けるなら、`s+h<R_post`を明記し、保証とは呼ばない。
3. **D2148との関係を裁定事項に戻す。** 定数不変更と実効期限不変更を区別する。
4. **M_preの比較表を追加する。** 180／60秒について、e・前段・観測遅延を含む受理集合とcleanup余裕を示す。R_postは後段自体の観測で評価する。
5. **既存注入seamを保存する。** helperの旧呼出し互換も残し、新規3経路テストは末端monkeypatchで実施する。
6. **境界テストを補う。** 起動遅延、cap_oom消費、qsub結果不明、DでのRUN／collection終了を検査し、kwargs算術テストをreceipt保存保証の証拠にしない。

## 裁定パッケージへ返すべき択一

| 選択 | 契約と帰結 |
|---|---|
| **A：D2148項8に沿って外側を全区間へ追随させる** | 内側期限を維持する。480秒とland全体のwatchdog算術を変更する裁定が必要。 |
| **B：480秒固定で内側を短縮する** | land固有の限定契約として採用する。従来成功例の拒否、RUN／collection hold、永続化の非保証を明示して受け入れる。 |

Bを選ぶ場合は、M_pre=180と60等の選択も、実測倍率だけでなく「どの成功例を落とすか」を添えて決めるべき。

## 総括

**現planはqueue待ちによる親の先行打切りを減らす案として成立するが、全経路の480秒以内完了保証にも、D2148項8のそのままの実装にもならない。** 必須修正は、時計の起点差、保証範囲、既裁定との関係の3点。180秒の予約と注入seam変更は再設計を推奨する。

指定資料の静的検査のみ実施。書込み・pytest・実走は行っていない。