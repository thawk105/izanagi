## テストの実効性

**所見 1:** 6 key、seed 1 / 777 の設計は、現在の未修正実装を確実に赤にする。

**判定:** refuted

**根拠の file:line:** プランは6 keyと2 seedを使い、bytes一致と各 report 内のWW key昇順を検査する（[s2-plan.md:32](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2436-ww-reason-order/s2-plan.md:32)、[s2-plan.md:35](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2436-ww-reason-order/s2-plan.md:35)、[s2-plan.md:79](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2436-ww-reason-order/s2-plan.md:79)、[s2-plan.md:93](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2436-ww-reason-order/s2-plan.md:93)）。親実測では未修正時の順序が seed 1 で `524136`、seed 777 で `213456` であり、互いに異なり、どちらも昇順ではない（[s1-probe.md:23](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/output/insights/2026-09-08_t2436-ww-reason-order/verbatim/s1-probe.md:23)、[s1-probe.md:27](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/output/insights/2026-09-08_t2436-ww-reason-order/verbatim/s1-probe.md:27)）。

6 keyの列挙順を独立一様な順列と近似すると、bytes比較だけが偶然通る確率は `1/6! = 1/720`、約0.139%。さらに両 report が昇順である必要があるため、テスト全体の偶然緑は `1/(6!)² = 1/518400`、約0.000193%。ただしset順序は独立一様乱数ではないため、これは危険度の目安であって形式的確率ではない。固定seedの現行環境については実測により偶然緑経路は否定されている。

**成果物への影響:** 現行CPython 3.10.12では、元の集合走査へ戻すと最初のbytes assertで確実に失敗する。SHA-256比較はbytes一致から数学的に従うため検出力としては冗長だが、欠陥を隠さない。

**直し方:** テスト設計の修正は不要。ただし「全Python実装で必ず」ではなく「実測したCPython 3.10.12と固定入力・固定seedで確実」と記す。将来のPython変更に対する限界はプラン自身も明記している（[s2-plan.md:198](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2436-ww-reason-order/s2-plan.md:198)）。

**所見 2:** subprocessのhash seed設定とrepo import経路は整合している。

**判定:** refuted

**根拠の file:line:** `PYTHONHASHSEED`は各`sys.executable -c`起動前に子のenvへ設定され（[s2-plan.md:65](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2436-ww-reason-order/s2-plan.md:65)）、`cwd=_REPO`が指定される（[s2-plan.md:70](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2436-ww-reason-order/s2-plan.md:70)）。`_REPO`はこのworktreeのrepo rootとして算出されている（[test_verifier.py:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/orchestrator/tests/test_verifier.py:38)）。親probeも同じ公開経路を通している（[s1-probe.md:16](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/output/insights/2026-09-08_t2436-ww-reason-order/verbatim/s1-probe.md:16)）。

**成果物への影響:** 親processのhash secret継承や別checkoutの誤importによる偽検査は見当たらない。

**直し方:** 変更不要。`cwd`、`env`、`sys.executable`を骨格どおり維持する。

## 所要時間と受入への影響

**所見 1:** 通常所要時間とプロセス数の見積りは妥当である。

**判定:** refuted

**根拠の file:line:** 起動する子processはseed 1と777の2本で、ループ内で直列に起動する（[s2-plan.md:64](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2436-ww-reason-order/s2-plan.md:64)）。類似する2-seed nodeの台帳値は0.33秒（[acceptance_duration_ledger.json:16317](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/orchestrator/tests/acceptance_duration_ledger.json:16317)）。プランの合計0.2から0.5秒、1本あたり概算0.1から0.25秒は整合する（[s2-plan.md:119](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2436-ww-reason-order/s2-plan.md:119)）。異常時は各30秒で、第一子が30秒近くで完了して第二子がtimeoutする場合の最大は約60秒。

**成果物への影響:** 通常経路では5分上限への影響は小さく、serial markerや長時間jobも増えない。静的見積りであり、実測値ではない。

**直し方:** 実装後に当該node単独の時間を測り、0.2から0.5秒という仮定を確認する。

**所見 2:** 新nodeを台帳へ登録しないという結論は、プラン内の根拠だけでは不十分である。

**判定:** real

**根拠の file:line:** 台帳はnodeidごとの秒数を保持し、現在の辞書件数と`nodeid_count`がともに20,042で一致する（[acceptance_duration_ledger.json:2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/orchestrator/tests/acceptance_duration_ledger.json:2)、[acceptance_duration_ledger.json:20046](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/orchestrator/tests/acceptance_duration_ledger.json:20046)）。既存`test_verifier.py` node群も個別登録されている（[acceptance_duration_ledger.json:19831](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/orchestrator/tests/acceptance_duration_ledger.json:19831)）。新nodeは未登録である。プランは90%以上のcoverage検査を通ることだけを根拠に更新不要としている（[s2-plan.md:193](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2436-ww-reason-order/s2-plan.md:193)）が、許容閾値を通ることと、既知の新nodeを台帳から意図的に除外してよいことは同義ではない。誰がいつ実測・登録するかも書かれていない。

静的集計では、現行`test_verifier.py`の82 node合計は約0.398秒であり、新テストの0.2から0.5秒は同fileの既知所要を約50%から125%増やす。全体比は小さくても、file単位の見積りには無視しにくい。

**成果物への影響:** 受入shardが未登録nodeへ使うfallback次第で所要見積りが過小になる。少なくとも、台帳を更新しない判断の監査可能性が不足する。

**直し方:** 実装後、受入を担当する親が当該nodeを実測して台帳へ登録する時点をプランに追加する。もし正式契約が「coverage閾値内なら次回一括再計測まで未登録可」なら、使用するfallback規則、根拠となる検査、次回更新の担当と時点を明記する。推定値0.33秒を実測せず直接登録してはならない。

**所見 3:** 新規test fileや追加harnessは発生しない。

**判定:** refuted

**根拠の file:line:** 追加先は既存`test_verifier.py`と指定されている（[s2-plan.md:24](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2436-ww-reason-order/s2-plan.md:24)）。同fileの素のrunnerは引数なしの全`test_`関数を自動収集する（[test_verifier.py:2794](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/orchestrator/tests/test_verifier.py:2794)）。

**成果物への影響:** 新規file固有の自走harness費用はない。

**直し方:** 計画どおり既存fileへ追加する。

## fixture の副作用

**所見:** fixture新設によるREADME・inventory副作用は回避され、temporary traceの後始末も設計済みである。

**判定:** refuted

**根拠の file:line:** fixture READMEは各directoryを1 runとして一覧管理している（[fixtures/README.md:3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/orchestrator/tests/fixtures/README.md:3)、[fixtures/README.md:14](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/orchestrator/tests/fixtures/README.md:14)）。実際の列挙・計数検査は`test_all_v2_fixture_files_have_clean_framing`で、`_V2_FIXTURE_FILES`とのexact一致を要求する（[test_verifier.py:406](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/orchestrator/tests/test_verifier.py:406)、[test_verifier.py:445](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/orchestrator/tests/test_verifier.py:445)）。プランはfixtureを作らず、既存`_tmp_trace`を使う（[s2-plan.md:121](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2436-ww-reason-order/s2-plan.md:121)）。helperは一時directoryと`trace_0.log`を生成し（[test_verifier.py:386](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/orchestrator/tests/test_verifier.py:386)）、プラン骨格は`finally`で`shutil.rmtree(..., ignore_errors=True)`を実行する（[s2-plan.md:97](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2436-ww-reason-order/s2-plan.md:97)）。

**成果物への影響:** README更新、fixture bytes pin、exact inventory更新はいずれも不要。subprocess失敗やtimeoutでも`finally`へ入り、通常の一時directory漏れはない。

**直し方:** 計画どおりtemporary traceを使う。fixtureへ変更する場合だけ、READMEと`_V2_FIXTURE_FILES`を同時更新する。

## 変異帰属の成立

**所見 1:** M1はテストnodeを赤にするが、契約上「KILLED」とは数えられない。

**判定:** real

**根拠の file:line:** M1の失敗nodeは完全なnodeidで名指しされている（[s2-plan.md:139](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2436-ww-reason-order/s2-plan.md:139)）。しかしプラン自身が、変更は理由の集合、cycle、受理集合を変えないとしている（[s2-plan.md:18](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2436-ww-reason-order/s2-plan.md:18)）。変異契約は、受理集合またはfail-closed挙動が変わった場合だけkillと数え、診断文字列だけの赤を除外する（[mutation.md:18](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/docs/dev-wave/mutation.md:18)）。さらに、受理集合を変えず構造化シグナルだけをpinする変異は`diagnostic sensitivity pin`へ別枠記録する、と明記されている（[mutation.md:62](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/docs/dev-wave/mutation.md:62)）。テストの`total_cycles == 1`とanomaly 1件は変異後も通り、赤になるのはbytesまたは理由順だけである（[s2-plan.md:85](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2436-ww-reason-order/s2-plan.md:85)）。

**成果物への影響:** M1からM4を`KILLED`として変異台帳へ記録すると、DW-M03／DW-M08違反になる。テストの検出力自体は有効だが、帰属ラベルが不正確である。

**直し方:** M1からM4はすべて`diagnostic sensitivity pin`として事前登録し、赤nodeを記録する。「pytest nodeが失敗した」と「契約上KILLED」を分ける。受理判定を変える変異を無理に追加する必要はない。

**所見 2:** M4の検出保証には実測またはprobe指定が不足している。

**判定:** real

**根拠の file:line:** 親probeが測ったのは元のset走査順だけであり（[s1-probe.md:41](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/output/insights/2026-09-08_t2436-ww-reason-order/verbatim/s1-probe.md:41)）、`key=hash`でsortした順序は測っていない。プランは「hashがseed依存だから同じnodeがKILLED」としている（[s2-plan.md:160](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2436-ww-reason-order/s2-plan.md:160)）が、hash値が変わることだけでは6 keyの相対順がseed間で必ず変わるとは証明できない。昇順assertにより失敗する可能性は高いが、保証ではない。契約は未確定時の初回をprobeとして扱う経路を定めている（[mutation.md:51](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/docs/dev-wave/mutation.md:51)）。

**成果物への影響:** M4だけは現状の資料から失敗nodeの完全一致を事前確定できない。

**直し方:** M4を初回probeとして登録し、変異後の両seed順序と実際の失敗nodeを採取してから再登録するか、事前登録候補から外す。いずれの場合も結果区分は`diagnostic sensitivity pin`とする。

**所見 3:** 等価変異の区別とnodeidの指示は概ね成立している。

**判定:** refuted

**根拠の file:line:** key自身を先頭にしたsort key、交差演算子の左右交換、同値なintersection表記は等価変異として明確に分離されている（[s2-plan.md:171](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2436-ww-reason-order/s2-plan.md:171)）。M1は完全nodeid、M2からM4は「同じnodeid」と参照しており、プラン上の対象は一意である。

**成果物への影響:** 等価変異を誤ってSURVIVED扱いする設計にはなっていない。

**直し方:** 段6の実際の変異specでは「同じnodeid」という省略を使わず、各候補に完全nodeidを反復記載する。

## scope と残る限界

**所見 1:** WWだけを変更し、wr／rwとconsumer正規化をscope外にする判断は本題に対して妥当である。

**判定:** refuted

**根拠の file:line:** 非決定な走査はWW枝のset intersectionにある（[dsg.py:524](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/orchestrator/verifier/dsg.py:524)）。wrとrwは`Txn.reads`を順に走査する（[dsg.py:533](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/orchestrator/verifier/dsg.py:533)、[dsg.py:538](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/orchestrator/verifier/dsg.py:538)）。親probeでもrwは全6 seedで`123456`、wrは同じread list走査としている（[s1-probe.md:37](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/output/insights/2026-09-08_t2436-ww-reason-order/verbatim/s1-probe.md:37)、[s1-probe.md:49](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/output/insights/2026-09-08_t2436-ww-reason-order/verbatim/s1-probe.md:49)）。D1817も局所修正を確定している（[D1817.txt:3](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2436-ww-reason-order/verbatim/D1817.txt:3)）。

**成果物への影響:** wr／rwやconsumerへ変更を広げなくても、観測済みのhash-seed非決定性はproducer側で閉じる。

**直し方:** scope拡大は不要。

**所見 2:** 残る限界は二つあり、最終成果物にも明示すべきである。

**判定:** real

**根拠の file:line:** テストは`workers=1`だけを通す（[s2-plan.md:34](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2436-ww-reason-order/s2-plan.md:34)）。また固定したseed 1 / 777の保証が現行CPython環境に限られることは、プランも認めている（[s2-plan.md:197](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2436-ww-reason-order/s2-plan.md:197)）。`_reasons()`はworker数にかかわらずcycle選択後に呼ばれるため局所修正自体には問題ないが（[dsg.py:569](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/orchestrator/verifier/dsg.py:569)、[dsg.py:585](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/orchestrator/verifier/dsg.py:585)）、このテスト単独では「worker数を変えてもreport全体が同じ」ことまでは証明しない。

**成果物への影響:** 本題は閉じるが、保証範囲を「現行CPython、固定seed、workers=1で観測したWW理由順」に限定して読まなければ、report全体の普遍的canonicalityを過大主張する。

**直し方:** scopeは広げず、最終spool fragmentへ次を残す。固定seedテストは将来Python実装に対する形式証明ではないこと、worker数間のreport同一性は今回の検査対象ではないこと。加えて、既存台帳の更新／延期判断は機能scope外ではなく受入成果物の処理として明記する。

## 総括

テスト本体は現行環境の未修正実装を確実に赤にする。seed 1と777は親実測と一致し、6 key・bytes一致・昇順assertの組合せに実効性がある。subprocess import、temporary trace、cleanup、新規test file回避も整合している。

real所見は二点である。

第一に、新nodeを受入所要時間台帳へ登録しない判断は、90% coverageを通るという説明だけでは不十分で、実測・登録または正式な延期条件の担当と時点が必要である。

第二に、M1からM4はテストnodeを赤にしても受理集合やfail-closed判定を変えないため、契約上`KILLED`ではなく`diagnostic sensitivity pin`である。特にM4は`key=hash`変異そのものの順序実測がなく、初回probeまたは候補除外が必要である。

pytest、subprocess probe、受入は実走していない。以上は指定資料だけによる静的点検であり、緑とは報告しない。