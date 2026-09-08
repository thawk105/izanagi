## 所見 1: `common/runner.hh` 追加は現行 source evidence の allowlist で必ず停止する

- 所見: 段 2 の 3-path patch C は、driver が build 前に `common/runner.hh` を allowlist 外変更として拒否するため、そのままでは計測経路が存在しない。
- 根拠: `s2-plan.md:120-128` は C の変更先に `common/runner.hh` を追加する一方、`orchestrator/campaign/source_digest.py:97-100` の `ALLOWLIST` は `"cmake/Options.cmake", "include/backoff.hh", "cc/silo/transaction.cc", "cc/mocc/transaction.cc"` だけである。driver は patch 適用後に certification では `t2187_adaptive_const_probe.py:2979-2982`、performance/diagnostic では `:3357-3368` から `resolve_evidence` を呼び、同関数は `source_digest.py:2400-2402` で変更 path を検査する。さらに `test_campaign.py:11325-11333` が `EVOLVE_BLOCK_SOURCES` と `ALLOWLIST` の exact 関係を literal pin している。
- 実害: cohort 1、cohort 2、certification のいずれも CMake configure より前に `ALLOWLIST 外の tracked 改変` で停止し、成果物は一件も生成されない。
- 提案: 段 4 で「`common/runner.hh` だけを patch 適用用の明示許可 path として追加し、coder 編集面には開かない」scope 拡張を裁定するか、runner を触らない終了方式へ戻すこと。`EVOLVE_BLOCK_SOURCES` への単純追加は hook、digest preimage、複数 consumer を広げるため親 scope 外。

## 所見 2: terminal event は複数回記録され得る

- 所見: 提案された handshake は request を保持したまま `recorded` を分岐条件に使わないため、main thread が再 scheduling される前に terminal event が二件以上記録され得る。
- 根拠: `s2-plan.md:57-66` の骨格は `if (izanagi_backoff_trace_terminal_requested())` のたびに `record_terminal` と `mark_terminal_recorded` を実行し、`izanagi_backoff_trace_terminal_recorded()` を確認しない。leader は `cicada-adaptive-dynamic.patch:452-462` の経路を繰り返し通る。対して plan 自身は `s2-plan.md:107-110` で terminal は末尾一件、`flushes=1` を要求している。
- 実害: main の停止が一回の count scan 間隔より遅れると `flushes>1` または terminal が複数になり、正しい run が parser で不適格になる。
- 提案: request 後は、未記録なら一度だけ記録して `recorded=true`、記録済みなら通常更新も追加 flush もせず return する三状態相当の処理にする。request を解除すると terminal 後に通常 event が出るため解除してはならない。

## 所見 3: 観測者効果の compile-time 分離は成立するが、巨大 cap は計装ではない

- 所見: terminal handshake を提示どおり実装すれば trace 計装は性能 build から除去できる一方、巨大 cap と除算比較は trace 無効 buildにも残る CC 機構変更である。
- 根拠: 現行 C の trace state と出力は `cicada-adaptive-counterfactual.patch:283-373`、event 材料は `:435-448,516-538,575-624`、ring writer は `:627-678`、static state は `:697-700` と、いずれも `#if BACKOFF_TRACE` 内である。新 runner hook も `s2-plan.md:73-84` の `#if BACKOFF_TRACE && BACKOFF_COUNT_WINDOW > 0` 内である。`s2-plan.md:58-65` の runtime `if (izanagi_backoff_trace_terminal_requested())` は存在するが compile-time guard の内側であり、trace 有効性を判定する `if (tracing)` ではない。一方、cap 判定は現行 patch `:385-395`、policy による挙動変更は `:478-586` と guard の外側にある。
- 実害: cap 変更まで「計装」と扱うと、trace-disabled performance buildの機構条件が別物になり、trace runとの帰属が崩れる。
- 提案: cap値、overflow-safe 比較、count closure は「CC 本来の機構」と明記し、trace on/off で同一値を使う。trace0 前処理検査は `include/backoff.hh` だけでなく実際の `common/runner.hh` も入力にする。

## 所見 4: certification の exact cell 追加自体は緩みではないが、全 consumer の cell別化が必須である

- 所見: raw literal二本を正確に追加する限り受理集合の制御された拡張だが、global `CERT_EXTIME` を一括変更したり `CERT_CELLS` だけを増やす実装は旧 cellを壊す。
- 根拠: 現行 `_certification_contract` は raw allowlist `t2187_adaptive_const_probe.py:1187-1191`、parsed exact membership `:1192-1199`、workload/thread/extime/slot `:1200-1219`、24 pathと外部束縛 `:1220-1268`、予算 `:1269-1282` の連言である。下流も row の cell/claim `:1985-2011`、default genomeとpatch identity `:2028-2077`、group内 genome/cell一意性 `:2268-2300,2345-2350`、published receipt `:2457-2469,2502-2524` を再検査する。plan の `CERT_EXTIME_BY_CELL` はこの構造を保てる。
- 実害: 一箇所でも global extime 3 のままなら新 cellを全拒否し、逆に全体を5へ変えると旧 tuned/cw-as-dyn certificationを全拒否する。
- 提案: `CERT_CELLS`、raw allowlist、claim、namespace、row、group、payload、PBS の全箇所で exact cellから extimeとclaimを引く閉じた表にする。prefix、任意 positive extime、parsed値だけの受理は導入しない。

## 所見 5: policy 2 certification と seed 排他は default seed限定なら両立するが、実測12 binaryの認証とは両立しない

- 所見: explicit seed禁止を保った certification は default compile seedの一 binaryだけを認証でき、cohort 2 の12 seed別 policy 2 binaryを認証するという意味では設計択一が未裁定である。
- 根拠: 現行は mode 判定前の `t2187_adaptive_const_probe.py:3250-3251` で policy 2 に seedを要求し、certify branch `:3252-3257` では同seedを禁止するため、今の順序では policy 2 certificationは到達不能である。plan は要求検査をperformance側へ移す。移動後は `genome_for` が seed未指定時に `STOCK_STEP_POLICY_SEED` を入れる `:601-608` ため、default seed buildなら成立する。group validatorも `genome_for(cell)` を exact期待値にする `:2032-2048`。一方、実測 policy 2 row は明示seedを genomeへ入れる `:3361-3366`。
- 実害: default seed receiptを12 seed成果物全体の正しさ認証として扱うと、認証された binary SHAと解析対象 binary SHAが一致しない。
- 提案: 段 4 で「default seed一 binaryだけを認証し、12 seedには外挿しない」か「certifyでexact preregistered seedを許し、seed別identityを認証する」かを名指しで選ぶこと。

## 所見 6: 新 certification の preregistration と performance extime の束縛がplanから漏れている

- 所見: policy≠0 cellを追加しても、現案のままでは旧 dynamic preregistration SHAを記録し、extimeの異なるperformance artifactもcertificationへ結合できる。
- 根拠: 旧 preregistrationは `dynamic-backoff-preregistration.md:161-165` で `cw-as-dyn` 一腕、cap 10240、extime 3だけを認証対象にしている。driver は certificationで無条件に旧SHAを読む `t2187_adaptive_const_probe.py:2843-2846`、payloadへ入れる `:2895-2907`、row/receiptでも同じ旧SHAを要求する `:2051,2385,2463`。また `_performance_artifact_identity` のfull binding `:1800-1818` は repo head、prereg SHA、stack SHA、cellを検査するが `extime_s` を検査しない。
- 実害: cohort 2 certification receiptが対象外の旧事前登録を指し、extime 3 performance artifactとextime 5 certificationを誤って同一条件として束縛できる。
- 提案: 旧二cellは旧SHA/extime 3、新二cellは新cohort 2 SHA/extime 5とするexact cell別表を certification payload、row、group、performance artifact validatorへ通す。

## 所見 7: 「patch C の literal pinは無い」は反証され、旧pinは更新せず歴史的束縛として残す必要がある

- 所見: 親brief `:31-33` の「literal pinはpatch Aのみ」は事実と異なり、patch Cの完全hashとstack hashは複数箶所に固定されている。
- 根拠: 現CのSHAは `794b7b48...a396`。完全literalは `docs/backoff-counterfactual-preregistration.md:140`、`orchestrator/campaign/backoff_counterfactual_analysis.py:33-40`、`orchestrator/tests/test_backoff_counterfactual_analysis.py:34-49`、`output/insights/2026-09-07_t2265-backoff-itt/verbatim/stage1-liveness.md:34`、同 `prereg-draft.md:74`、`s6-review-lensB.md:10`、`s5-author.md:8` にある。旧stack SHA `192be42d...7433c` も `stage1-liveness.md:35` と `prereg-draft.md:74` にある。driver側は current bytesを動的算出する `t2187_adaptive_const_probe.py:691-719`。
- 実害: 旧literalを新C SHAへ置換するとcohort 1の凍結契約と12成果物の受理集合が変わり、置換しないことを「pin無し」と誤解すると新cohortのidentity更新漏れが起きる。
- 提案: 旧docs、旧解析器、旧解析test、既存outputのliteralは変更しない。新SHAは新事前登録、新driver成果物、新解析器だけへ固定する。

## 所見 8: v2事前登録のbytesとcohort 1解析器には現時点で変更経路がないが、plot拡張が唯一の共有consumerリスクである

- 所見: planの所有集合どおりなら旧事前登録と旧解析器は保持できるが、共有plotでschema選択を緩めると既存成果物の受理が変わる。
- 根拠: `docs/backoff-counterfactual-preregistration.md` の実SHAは `526d9384...495a` でtracked diffなし。このSHAは旧解析器 `backoff_counterfactual_analysis.py:23-25` と旧test `test_backoff_counterfactual_analysis.py:24-25` にpinされる。旧解析器は artifact中の旧patch SHAを検査する `backoff_counterfactual_analysis.py:121-133` がcurrent patch file自体は読まない。plotもcurrent Cを読まず、artifactのordered stackを検査する `plot_dynamic_backoff.py:219-299`。
- 実害: 旧三ファイルを触らない限り12成果物は保持されるが、plotで「A+B+Cなら任意cell/extime」とするとcohort 1と2が混線する。
- 提案: 旧SHA、旧schema、旧cell set、extime 3の分岐を逐語保持し、新cohortは別schema、別cell set、extime 5の独立分岐にする。実12 JSON自体は指定資料に無いため再parse確認は親担当。

## 所見 9: producerの二cohort受理は実装可能だが、plotのextime受渡し案は現行parse順と合わない

- 所見: driver/PBSはliteralから期待extimeを引く閉じた表で両cohortを受理できるが、plotはperformanceを先にparseするため「diagnostic contractからexpected extimeを渡す」だけでは実装できない。
- 根拠: driverの現行trace gateは二literalを同じextime 3へ固定する `t2187_adaptive_const_probe.py:2738-2758`、PBSも二literalだけを受理する `t2187_adaptive_const_probe.pbs:149-156`。performance branchには `--extime` が無い `:389-401`、`:415` はcertification専用でありplanの訂正は正しい。一方plotは `load_inputs` でperformanceを `plot_dynamic_backoff.py:1026`、diagnosticを`:1040` の順にparseし、各parse中の `_common_identity:219-257` が直ちにextime 3を要求する。
- 実害: planの記述だけで実装するとcohort 2 performanceがextime 5で拒否されるか、旧schemaが任意extimeを受ける緩みになる。
- 提案: diagnostic contractを先に選んで、そのexact expected extimeをperformance parserへ渡すようparse順を変えるか、cohort 2専用performance schemaを設ける。任意positive受理は不可。

## 所見 10: tracked-cleanかつcanonicalな投入手順がplanに無い

- 所見: planには12 jobの所要記述しかなく、PBSが要求するcanonical rootとtracked-clean commitからqsubする具体的手順が欠けている。
- 根拠: `s2-plan.md:173,274` は同時投入と必要performance artifactに触れるだけで、S7のqsub手順が無い。PBSは `t2187_adaptive_const_probe.pbs:40-43` で `PBS_O_WORKDIR` と`realpath`の逐語一致、`:45-53` でexact HEADとtracked-cleanを要求し、driverも `t2187_adaptive_const_probe.py:762-798` で再検査する。現worktreeは `cc9bba523ac7804aadb7891d686bf4c925789a3f` かつ現在はcleanだが、実装後はcommit前のtreeから投入できない。
- 実害: script pathだけを指定して別cwdからqsubするか未commit差分を残すと、全jobが測定前にexit 2となる。
- 提案: 親が新事前登録と実装をcommitした後、各submit-treeを同一commitへdetached、submodule pinned-cleanにし、`cd -P`した各canonical rootからqsubする手順、seed、output path、job ID記録をS7へ明記する。

## 所見 11: buildcache claimは現行t2187経路では使われず、detached treeによる衝突回避という親説明は誤りである

- 所見: 12 job同時投入時、現行driverはv2 claimを共有せずjobごとのscratchで独立buildするため、親のclaim衝突回避策は実経路と一致しない。
- 根拠: v2 claimは `buildcache.py:2195-2204` で既存claimを即拒否し、完成entryよりclaimを先に見る `:2552-2565` が、t2187はv2 APIでなくlegacy `buildcache.build` を certification `t2187_adaptive_const_probe.py:3019-3030` とperformance `:3387-3398` から呼ぶ。cache rootはjob別の `$TMPDIR/build-variants` `:2972,3301`、PBSのTMPDIRはPBS_JOBID由来 `t2187_adaptive_const_probe.pbs:225-230` である。cache keyはgenome、trace、source token、toolchain、admission receiptから決まる `buildcache.py:624-642`。SourceEvidence receiptには絶対`source_root`も入る `source_digest.py:249-260`。
- 実害: 同時投入してもclaim衝突は起きない代わりに、共通なpolicy 0/1 binaryも12 jobで重複buildされ、1+11投入やdetached treeではcache reuseも生じない。
- 提案: 現行のjob別scratchを前提に12本を同時投入するのが最小手順。共有v2 cacheへ変えるならscope外のdriver変更であり、同一cache rootと同一source/admission identityを使う一jobのpublish完了とclaim消滅を確認してから残りを出す必要がある。

## 所見 12: stale claimの回収は自動化されておらず、exact claimだけを手動回収する必要がある

- 所見: v2経路を将来使う場合、stale claimが一個でも残れば完成binaryがあっても永久に拒否される。
- 根拠: `buildcache.py:2202-2204` は「待機・自動 retry・stale 自動削除は行わない; 手動回収が必要」、`:2560-2564` は「完成 entry より claim を先に見る」と明記する。owner receiptは`:2207-2215` の `pid`, `host`, `starttime`, `nonce` である。正常publish後だけ`:2225-2239` がclaimを除去する。
- 実害: killやpublish後crashで`${digest}.building`が残ると、同一identityの全再試行が失敗する。
- 提案: 全候補job停止を確認し、exact `${digest}.building/owner.json` のhost/PID/jobが生存していないことと完成entryの有無を確認してから、そのclaimの`owner.json`と空claim directoryだけを手動除去し再投入する。親directoryやglobを削除してはならない。

## 所見 13: 変異候補には冗長な組と、帰属を証明しない検査案が残る

- 所見: planのnode集合比較だけではgate帰属は決まらず、複数の変異が同じterminal/schema検査へ落ちる。
- 根拠: plan自身が `s2-plan.md:446` で「runner hook削除」と「requestを立てない」を同じterminal未生成集合、`:448` で「flushes削除」と「retained=updates」を同じsummary集合と認める。さらに`:434` の部分窓変異は二つのtestを同時に赤くするため、その二nodeは当該変異に対して冗長である。`:435` のterminal updateと`:438` のterminal `assigned_invert=0`も、実装次第で同じterminal sentinel/LCG nodeへ落ちる。正しい帰属の決め手はnode集合ではなく、変異差分が一つの意味条件だけを変え、期待したfailure reasonで落ちることである。
- 実害: 同じ赤node数を独立な防壁と数えると、実際には一つのparser条件しか行使していないのに複数gateを検証済みと誤記録する。
- 提案: runner未生成組とsummary組は各一変異だけを本登録し、部分窓の二testも主となる一nodeを帰属先にする。これは既存候補の整理であり、新しい台帳や一般gateは不要。

## 所見 14: trace0、count closure、LCG負例はfixtureの作り方次第で恒真または別gate先着になる

- 所見: 提案されたtest名だけでは歯を証明できず、少なくとも三箇所で「謳うだけのassert」になり得る。
- 根拠: 現行 `test_trace_preprocesses_out_of_trace_zero_builds` は `test_dynamic_backoff_transitions.py:1492-1514` で`backoff.hh`だけをincludeしており、runner漏出は観測しない。terminal-last artifactだけでsentinelを確認しても、terminal後のLCG stateが観測されないため「LCGを進めない」の証明にならない。`window_commits=10000`をtest fixture自身が設定してparserへ渡すだけなら、C++がcount境界を待つことを行使しない。LCG負例については `s2-plan.md:245` が二番目のbitを1から0へ変えるが、そのeventの`inversion_realized=1`を残すとproducer parserの `t2187_adaptive_const_probe.py:1069-1078` がLCGより先に拒否する。
- 実害: 変異が対象実装を殺さずfixtureまたは別schema検査だけを殺し、LCG、runner guard、count closureへの帰属が成立しない。
- 提案: runner自身をtrace0/1でpreprocessする。terminal処理前後のpolicy stateをC++ seamで比較する。count closureはC++のleader seamでK-1/Kを行使する。LCG負例は`inversion_realized=0`のeventを反転するか `_validate_assignment_lcg` を直接呼ぶ。

## 所見 15: 親briefのline anchorは一箇所以外一致し、段2による`:1202`批判は成立しない

- 所見: 現HEADでの数値的食い違いはplotの`parity_branch`検査位置だけで、他の列挙anchorは一致する。
- 根拠: `brief.md:52` のpatch 707行、window 439付近、`:53` のdriver 272/1185/242/2732/2761、`:54` のPBS 21/151/415/5、`:57` のdynamic test 731/740/750/1146/1174/1185/1202/1348、`:58` のspawn 923/936/2688/2693/2702はいずれも現物に対応する。`brief.md:56` のplot `parity_branch 検査 (474)` は`:474`が文字列取得で、許可集合の実検査は `plot_dynamic_backoff.py:477-478`。一方 `s2-plan.md:404` はbriefの`:1202`を「test開始位置ではない」と攻撃するが、briefは開始位置でなく構造検査のanchorとして挙げており、実際`:1202`はpatch C読込み行なので不一致ではない。
- 実害: 誤ったline批判を残すと、本当に漏れているsource_digest pathとplot検査位置が埋もれる。
- 提案: briefのplot anchorを`:477-478`へ直し、`:1202`批判は撤回する。driver編集後はspawn sinkの実AST行を再導出する。

## 所見 16: 段5の三単位は現状file-wiseには素集合だが、実装可能にする追加fileのownerが無い

- 所見: Unit A/B/Cの記載pathに重複は無いが、所見1を直すために必要なsource evidence側fileがどのunitにも割り当てられていない。
- 根拠: `s2-plan.md:410-425` のUnit A、B、Cは同じfileを一つも共有しない。patch C SHAはA完成後にB/Cへ渡す依存であり、同一file所有ではない。ただし `source_digest.py:97-100` とliteral関係を固定する `test_campaign.py:11317-11333` はどのunitにも無い。
- 実害: 三unitが記載どおり完了してもdriverはallowlist拒否で動かず、後から別unitが同じ設計面を追加修正することになる。
- 提案: stage 4でscope拡張を採る場合だけ、exact `common/runner.hh` 許可に必要なfileをUnit Aへ追加する。三unit間の既存file所有はそのまま素集合を保てる。

## 総括

- 実装前に必ず直すべき所見 (優先順): source_digest allowlistによる実行不能、terminal多重記録、policy 2 seedの設計択一、新cellのpreregistration/performance extime束縛、canonical clean投入手順、plotのextime parse順。
- 親briefのprovisional裁定のうち覆すべきもの: P4の「C改訂はliteral pinを壊さず局所的」、P5を実測12 seed binaryの認証と読める表現、detached submit-treeでbuildcache claim衝突を避けるという投入理由。
- 判定不能・情報不足で結論できなかった点: 未実装testの実pytest node集合、terminal handshakeのlive scheduling、実在するcohort 1の12 JSONの再parse結果は静的資料だけでは確定できない。pytestは実走せず、緑も要求していない。