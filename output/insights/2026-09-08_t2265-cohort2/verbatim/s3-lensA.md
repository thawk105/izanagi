## 所見 1: count-closed 化は欠測修正ではなく推定対象の変更である

- 所見: cohort 2 の `D[r]` は、固定時間窓の throughput 効果ではなく、約 10,000 commit への到達で終了する窓の rate 変化を、5 秒までに生じた更新機会について平均する局所 ITT になる。
- 根拠: 凍結済み v2 は `T = window_commits / window_us`、`Y = ln(T[i+1] / T[i])` とし、3 秒以内に後続 event を持つ更新だけを対象としている [事前登録:149-176](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2/docs/backoff-counterfactual-preregistration.md:149)。cohort 1 は count または 10,240 us cap で閉じる混合窓だった [事前登録:113-140](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2/docs/backoff-counterfactual-preregistration.md:113)。対して段 2 は cap を実質無効化し、5 秒後も次の count closure まで走らせ、従来落としていた最後の割当まで terminal を following として使う [s2-plan:5-12](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2/s2-plan.md:5)、[s2-plan:200-207](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2/s2-plan.md:200)。count-closed では `window_commits` がほぼ閾値で、`window_us` が処置の影響を受ける停止時間になるが、overshoot もあり、主層では最大 26,418 commit である [probe-window-structure:209-214](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2/probe-window-structure.txt:209)。これは無効な outcome ではないが、「count 閾値到達までの観測 rate」という別の outcome である。
- 実害: cohort 2 の `equivalent` や優越判定を、cohort 1 の hybrid-window、3 秒、最後の割当除外という主推定量の確定または再現として扱うと、別の受理集合と別の時間・状態分布に対する結論を同一視する。
- 提案: 新事前登録では推定対象を「初回更新を除き、nominal 5 秒より前に発生した割当について、次の count-threshold closure までの rate 変化を測り、最後の割当も count-closed terminal を following として含める ITT」と書き直すこと。cohort 1 の主仮説の厳密な確認とは呼ばず、「cohort 1 を pilot とした、関連する新しい count-closed estimand の前向き確認試験」と呼ぶこと。主層では `seq >= 1` の cap は 4 件だけだった [probe-cap-events:19-19](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2/probe-cap-events.txt:19) が、数値的に近いかは未計算であり、推定対象の同一性は件数の少なさからは出ない。

## 所見 2: cap 撤去は cohort 2 内の outcome 除外ではないが、cohort 1 の outcome に基づく設計変更であり、非閉鎖を選択に使えば処置後選択になる

- 所見: 全固定 seed を新規に走らせ、完了可否を含めて結果どおり扱う限り cap 撤去は cohort 2 内の complete-case 選択ではないが、既知の outcome で測定機序を変更した outcome-informed redesign であり、さらに count 閾値へ到達しない run を落とせば処置後選択になる。
- 根拠: 「0 commit は cap 窓だけ」は、約 155,000 event を開いた後の観察で、`seq >= 1` の 0 は同じ seed の 2 件、どちらも cap だった [brief:74-95](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2/brief.md:74)、[probe-cap-events:223-231](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2/probe-cap-events.txt:223)。`window_commits` は `T` の分子、`window_us` は分母であり、trigger と固定時間内 event 数も速度の proxy なので、「構造量だけで outcome は見ていない」は誤りである。段 2 自身も、commit が永久停止すれば terminal event を作らず timeout にするとしている [s2-plan:5-14](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2/s2-plan.md:5)。従って「0 が構成上ない」は「次の 10,000 commit に到達して受理された窓では」という条件付き保証にすぎず、cap による 0 を outcome-dependent noncompletion に移す可能性がある。
- 実害: timeout や terminal 非生成の seed を再投入、置換、除外して 12 完走 run だけを集めると、処置後の commit 継続性で受理集合を選び、停止した軌跡を推定量から消す。
- 提案: 固定 seed の terminal 非閉鎖は outcome-blind な設備故障と区別し、commit 停止が否定できない場合はその seedを差し替えず主判定全体を `inconclusive` とすること。新事前登録の開示節には、少なくとも次を逐語で置くこと。

> 本 cohort 2 は outcome-naive な追試ではない。設計凍結前に、cohort 1 の全 12 成果物と v1/v2 の結果を閲覧した。v2 の主判定が `window_commits_zero` により `inconclusive` であること、`seq >= 1` の 0 commit が policy 2 / write-heavy / 48 threads の同一 seed に 2 件あり、いずれも time-cap closure だったこと、全 18 cell では `seq >= 1` の cap closure が 206 件だったこと、主層の event 数が run あたり 555 から 671 件だったこと、最後の記録済み窓が 2,560 から 10,846 us だったことを見た。`window_commits` と `window_us` は指定 outcome `T` の構成要素であり、trigger と event 数も速度に依存する量である。これらの観察を受けて、time cap の実質無効化、count-closed terminal、nominal extime 5 秒を選んだ。cohort 1 で既に開示された 5 副次層の正の推定値も閲覧済みである。従って本設計は cohort 1 の outcome に informed された新規 cohort の前向き protocol であって、盲検の holdout または cohort 1 と同一推定対象の反復ではない。
>
> confirmatory set に含める固定 R run の outcome は、本書の凍結前に一つも閲覧していない。凍結前に実施した liveness job `<job id>` は pilot として confirmatory set から永久に除外し、閲覧した field と集約値をここへ全て列挙する。count-closed terminal は、次の count 閾値へ到達した受理窓についてのみ `window_commits > 0` を保証する。固定 seed が terminal closure に到達しない場合、その seed を outcome に基づいて置換または除外せず、主判定を `inconclusive` とする。

## 所見 3: 部分 terminal 窓を推定量へ混ぜると最後の 1 outcome だけ別の観測時間と閉鎖規則を持つ

- 所見: 即時の部分 flush を入れる案は等質な「1 count-closed window 先」の target を壊すが、段 2 の count-closed terminal なら後続窓の完備と窓の等質性は両立できる。
- 根拠: 親 P3 は「extime 後の最初の窓閉鎖まで」と「短い部分窓を作らない」としている [brief:35-40](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2/brief.md:35) 一方、同じ brief の後段は terminal flush が count で閉じず 0 になりうるとしており、内部で矛盾する [brief:91-96](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2/brief.md:91)。段 2 は部分 flush の `window_commits=0` と高分散を認識し、count closure 待ちへ変更している [s2-plan:88-101](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2/s2-plan.md:88)。
- 実害: 部分窓を含めると最後の割当だけ残余時間で測る高分散 outcome となり、0 なら全判定を止め、非 0 でも割当側の平均へ不均等な leverage を与える。
- 提案: 選択肢ごとの target を事前登録で明記すること。(a) 部分窓を入れるなら「count-closed outcome と administratively truncated terminal outcome の混合」であり同質性を主張しない、(b) 部分窓を落とすなら「後続 event を持つ更新」に戻り最後の割当を失う、(c) 推奨する count-closed terminal なら terminal は following 専用、割当なし、通常窓と同じ count 条件とし、nominal 5 秒前に発生した最後の割当まで含める。両立するのは (c) だが、terminal 非閉鎖時の全体 `inconclusive` 規則が必要である。

## 所見 4: 5 秒化による event 増加だけから R = 12 の検出力は保証できない

- 所見: R = 12 が十分と言えるのは新しい `D[r]` の真の cluster SD と真の効果位置に条件を置いた場合だけで、現時点では十分とは言えない。
- 根拠: cohort 1 主層は 3 秒で 555 から 671 event、中央値 617 だった [probe-window-structure:209-214](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2/probe-window-structure.txt:209)。単純な時間比例という推測では 5 秒で約 925 から 1,118 event、中央値約 1,028 になるが、隣接 `Y` は同じ窓を共有し、持ち越しもある [事前登録:169-176](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2/docs/backoff-counterfactual-preregistration.md:169)。従って event 数は有効独立数ではない。凍結済み表も、R = 12 の等価判定力 0.823 は「真値 0、正規な run 差、cluster SD = 0.032」という計画仮定だけに基づき、run 内 SE から cluster SD は推定できないと明記する [事前登録:221-245](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2/docs/backoff-counterfactual-preregistration.md:221)。5 秒化は run 内誤差を減らしうる一方、後半の状態を追加して `D[r]` 自体と run 間異質性を変えうる。
- 実害: 「event が約 5/3 倍なので powered」と書くと、未知の cluster 間 SD、系列依存、時間非定常性を無視し、`inconclusive` を予防できるという根拠のない期待を成果物へ入れる。
- 提案: 新事前登録には「R = 12 の十分性は主張しない。真の `theta=0`、独立かつ概ね正規な run 差、cluster SD `<=0.032`、12 run 完備という条件下に限り、旧計画モデルでは等価判定力約 0.823 である。新 target に対する SD は未検証であり、実測 `s_D`、CI 半幅、decision を報告する。実用優越については効果量仮定を置いておらず、検出力を主張しない」と書くこと。R を増やすなら、cohort 2 outcome を一つも見る前に R を 18 または 27 などへ固定し、ASCII `izanagi-t2265-cohort2-policy2-seed-NN` の SHA-256 先頭 8 byteを big-endian uint64 とする規則、全 seed 値、非 0・一意性を凍結すること。停止規則は「exact R slot、途中解析なし、同一 seed の再試行は outcome-blind な設備・queue・build 不成立だけ最大 2 回、最初の完走物を採用、terminal 非閉鎖や速度を理由に追加・置換しない、R が揃わなければ確認的判定なし」とする。

## 所見 5: cohort 2 は前向き事前登録を名乗れるが、outcome-naive または cohort 1 と同一の確認試験は名乗れない

- 所見: confirmatory cohort の全 outcome より前に exact protocol を凍結すれば前向きだが、凍結前 pilot を confirmatory set へ戻すか、固定 run を見て設計を変えれば前向き性を失う。
- 根拠: brief は新 cohort outcome 前の commit 凍結を要求する一方、凍結前に liveness 1 job を走らせる予定である [brief:22-30](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2/brief.md:22)、[brief:69-72](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2/brief.md:69)。既存 v2 は outcome の一部を見た後なので「事前指定の再解析計画」までしか名乗れないと自己限定している [事前登録:27-48](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2/docs/backoff-counterfactual-preregistration.md:27)。今回の probe は cohort 1 の既開示データなので cohort 2 confirmatory units に対する前向き性自体は壊さないが、設計を outcome-informed にする。
- 実害: pilot と本走の境界または凍結時点が曖昧だと、都合のよい terminal、extime、R、seed、除外規則を見た後に選んだ疑いを排除できず、確認的というラベルが過大になる。
- 提案: 名乗る条件は、(1) prefreeze liveness は別 job、別 artifact namespace として永久除外、(2) 閲覧した field と値を全開示、(3) 推定対象、窓閉鎖、terminal、除外、timeout、R、seed、再試行、等価域、判定順を凍結、(4) その後に fixed R を開始、(5) outcome 後の改訂を別 protocol にすること。前向き性を壊す行為は、fixed R の `window_commits`、`window_us`、event 数、trigger、T、Y、D、`s_D`、CI、decision のいずれかを凍結前に見ること、pilot を R に算入すること、結果に応じて extime・R・seed・terminal inclusion・除外・margin を変えること、速度や terminal 非閉鎖で再測定または差替えすることである。commit 順序は文書の祖先関係しか証明せず、未閲覧の証明ではないことも継承する。

## 所見 6: LCG 一致検査は割当実装を証明するだけで因果的な無作為化を証明しない

- 所見: seed から `assigned_invert` が正しく再現できても、決定的 LCG と outcome-dependent な更新時刻が物理過程から独立という仮定は未検証のままである。
- 根拠: 凍結済み事前登録は、LCG が形式的に独立な stream ではなく、「物理過程と同期していない」という as-if 無作為化仮定の下の ITT だと明記する [事前登録:119-129](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2/docs/backoff-counterfactual-preregistration.md:119)。段 2 の新検査は LCG state と event field の exact 一致だけを検査する [s2-plan:209-232](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2/s2-plan.md:209)。count closure では throughput が次の event の時刻を決め、先行割当が後続の event index と物理時刻の対応を変える。
- 実害: LCG 検査合格を「無作為割当を検証した」「交絡のない因果効果」と表現すると、同期、持ち越し、処置履歴依存の visit process という未検証仮定を隠す。
- 提案: LCG 検査は `assignment-integrity check` とだけ呼び、v2 の as-if 無作為化限定を逐語継承すること。「causal ITT」と書く場合は必ず「事前固定 LCG が物理過程と同期しないという未検証仮定の下で」を付ける。

## 所見 7: P1 から P6 のうち因果推論上覆すべき中心は P2 の同一性主張と P3 の曖昧さである

- 所見: P1 と P6 は保持可能だが、P2 は条件付き保証と別 estimand に直し、P3 は count-closed と partial の矛盾を解消し、P4 と P5 は inferential validity を支える主張として使わない必要がある。
- 根拠:
  - P1: 新規文書にする判断は、既存 v2 と新しい測定条件を混同しないため正しい [brief:35-36](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2/brief.md:35)。
  - P2: 「全 event で 0 が構成上不可能」は、count closure に到達した event にだけ真であり、timeout という欠測を残す。また cohort 1 と同じ推定対象ではない [brief:37-38](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2/brief.md:37)。
  - P3: brief 本文の「最初の窓閉鎖まで」は count-closed だが、後段は部分 flush として扱う。段 2 も P3 を「部分窓」と攻撃しており、brief の最初の文面に対しては straw man になっている [s2-plan:450-454](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2/s2-plan.md:450)。
  - P4: patch C の in-place 改訂は実装選択であり、推定対象の連続性を保証しない。最終 bytes の identity を新 protocol に束縛しなければ、前向きな測定契約も曖昧になる。
  - P5: certification は因果推論の根拠ではないうえ、「実際に使う policy!=0 cell」を全て認証するという親文面は広すぎる。段 2 自身が最小 49 job では policy 2 の default seed と 48 threadしか覆わず、12 seed binary と 24 threadを覆わないと認める [s2-plan:339-349](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2/s2-plan.md:339)。
  - P6: cohort 専用 module は受理集合の分離として正しい [brief:46-46](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2/brief.md:46) が、v2 の margin、R、判定定数をコピーしても、新 `D[r]` の power や同一 estimand は継承されない [s2-plan:175-187](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2/s2-plan.md:175)。
- 実害: P2/P3 を現状のまま凍結すると、実装が count-closed でも文書から partial inclusion と timeout の扱いが一意に決まらず、同じ artifact に異なる正当な解析が生じる。
- 提案: P1 と P6 は維持する。P2 は「受理され完了した窓について非 0」と「新 count-closed target」を明記して改訂する。P3 は段 2 の count-closed terminal に一本化する。P4 は単なる実装裁定として final SHA と protocol の束縛を要求する。P5 は「認証した exact binary、seed、thread 条件」だけを書く。段 2 の最終結論 [s2-plan:467-471](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2/s2-plan.md:467) は、count-closed terminal の採用自体は保持できるが、「cohort 1 の主判定を確定する」という帰結は撤回する。

## 所見 8: `equivalent` も `inconclusive` も cohort 1 や副次層を使って強い結論へ読み替えてはならない

- 所見: cohort 2 の decision は新しい主層 estimand にだけ適用し、cohort 1 の正の副次 5 層は開示済み pilot 情報としてしか使えない。
- 根拠: `equivalent` は 90% CI が ±`ln(1.03)` の内側に入ること、優越は 95% CI が実用境界を越えること、それ以外が `inconclusive` である [事前登録:198-219](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2/docs/backoff-counterfactual-preregistration.md:198)。cohort 1 の副次 5 層は全て正で 95% CI も正だった [cohort 1 v2 README:95-106](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2/output/insights/2026-09-08_t2265-itt-seq0/README.md:95) が、文書自身が主判定の代用、効果の証明、6 regime への一般化を禁じている [同:112-128](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2/output/insights/2026-09-08_t2265-itt-seq0/README.md:112)。
- 実害: prior secondary の符号を cohort 2 decision に足すと、多重性未調整の探索結果と変更後 estimand を事後的に合成し、主判定の受理集合を拡大する。
- 提案: `equivalent` の場合、次を書いてはいけない。
  - 「推奨方向と反転方向に効果はない」
  - 「controller の向きは commit 速度を変えない」
  - 「cohort 1 の主仮説または主判定を確認した」
  - 「policy 0 と policy 1 は等価である」
  - 「trace 無効 performance でも等価である」
  - 「全 workload、thread、個々の窓で差は 3% 未満である」
  - 「LCG により無交絡の因果効果が証明された」

  `inconclusive` の場合、次を書いてはいけない。
  - 「効果なし」「等価」「主仮説は棄却された」
  - 「R = 12 の検出力不足が原因である」と、実際の reason と CI を確認せず断定する
  - 「cap 撤去は失敗した」
  - 「cohort 1 の正の副次 5 層が主判定を救済する」
  - 「5 層が再び正なら推奨方向の実用優越である」
  - 「cohort 1 と合わせれば確認的証拠になる」

  cohort 1 の 5 層は「既に閲覧した探索的な prior context」として開示し、cohort 2 の endpoint、R、停止、decision を変えるためには使わない。事前指定した場合でも符号の並列記述までで、主判定の確認、救済、一般化には使わない。

## 総括

- 実装前に必ず直すべき所見 (優先順): 1. cohort 2 の新 estimand と cohort 1 との差、2. terminal 非閉鎖を含む timeout・置換規則、3. outcome-informed disclosure と pilot の永久除外、4. count-closed terminal の一意な定義、5. R = 12 の条件付き power 表現、6. LCG の as-if 限定。
- 親 brief の provisional 裁定のうち覆すべきもの: P2 の無条件な「0 commit は構成上不可能」と同一主判定扱い、P3 の count-closed と部分 flush の矛盾、P5 の「cohort 2 が実際に使う binary を認証した」という広い表現を覆す。P1 と P6 は維持、P4 は因果的根拠から外す。
- 判定不能・情報不足で結論できなかった点: 新 target の cluster SD、有効 event 数、R = 12 の実検出力、count-only 化による数値差、terminal 非閉鎖の確率、凍結前 liveness で実際に閲覧する field とその job が固定 R から確実に除外されるか。