判定は **NO-GO** です。親実測の targeted **173 passed / rc=0** と snapshot 実測は前提に採用しました。fix5 報告の自己申告は証拠に使っていません。

## 旧17件の対応表

| 所見 | 判定 | fix5後の静的根拠 |
|---|---|---|
| Review A MF-1 — NEG allowlist | `closed` | 訂正版6件を literal 化し、prompt参照集合とも照合する。[impl:111](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:111) [impl:1463](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:1463) |
| Review A MF-2 — replay verifier | `closed` | raw artifactを必須読込し、snapshot、`collect_run()`、`score_run()`を再実行して保存JSONとcanonical byte比較する。[impl:3937](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:3937) [impl:4101](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:4101) [impl:4107](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:4107) |
| Review A MF-3 — stale/extra session | `closed` | session時刻をlaunch envelopeへ拘束し、ID三者一致と`(path,inode,id,session_id,timestamp)`集合一致を要求する。[impl:2626](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:2626) [impl:3257](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:3257) [impl:4202](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:4202) |
| Review A MF-4 — retry上限 | `closed` | supervisorが1〜3を強制し、pair同世代、親run、ledger/manifest集合を照合する。[impl:2065](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:2065) [impl:2145](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:2145) [impl:3795](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:3795) |
| Review A MF-5 — primary verdict join | `partial` | packet→run→slot、二読者、judgmentのjoin自体はあるが、裁定時に読まれたpacket bytesをverdictへ束縛していない。[impl:3361](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:3361) [impl:4388](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:4388) |
| Review A MF-6 — scorer | `partial` | 強調除去と既知の曖昧表現は改善したが、後述N-5の句読点越し否定を受理する。[impl:3041](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:3041) [impl:3062](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:3062) |
| Review A MF-7 — golden独立性 | `closed` | route Bは独立parser/byte decoderを使い、production entrypointが両routeを比較しsource rollout SHAも検査する。[impl:425](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:425) [impl:536](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:536) [impl:559](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:559) |
| Review A MF-8 — turn graph/classification | `closed` | 非空turn ID、context/start/terminal join、イベント順・timestamp envelope、正token、構造的treatment開始を検査する。[impl:2653](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:2653) [impl:2725](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:2725) [impl:2894](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:2894) |
| Review B MF-1 — arm treatment同一性 | `closed` | supervisorがcanonical argv/bwrap/envを構築し、agent-visible pathをopaque化、case内identity濃度1を要求する。[impl:1702](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:1702) [impl:1814](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:1814) [impl:4216](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:4216) |
| Review B MF-2 — Git object閉包 | `closed` | rootと初期化済みsubmoduleを再帰検査し、ref、remote、reflog、replace、grafts、alternates、pseudo-ref、unreachable objectを拒否する。[impl:667](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:667) [impl:855](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:855) [impl:1053](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:1053) |
| Review B MF-3 — NEG snapshot | `closed` | Review A MF-1と同じ訂正版6件に一致する。[impl:111](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:111) |
| Review B MF-4 — raw replay/freeze | `closed` | `sessions-root`必須でraw receipt/scoreを再生成し、自己申告された集計値を採用しない。[impl:4119](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:4119) [impl:4234](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:4234) |
| Review B MF-5 — label-masked adjudication | `partial` | 二読者とfreeze→reveal APIはあるが、same-owner custodianとpacket bytesの時間的非束縛が残る。[impl:4265](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:4265) [impl:4339](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:4339) |
| Review B MF-6 — slot/attempt/失敗分類 | `regressed` | pair-invalidated自体は追加されたが、mateのpost-treatmentを上書きし、reliabilityはfinal attemptだけを見るため発生済みarm failureを消す。[impl:3555](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:3555) [impl:3718](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:3718) |
| Review B MF-7 — 同時実行干渉 | `closed` | pairはfor-loopで逐次起動され、monotonic時刻でoverlap・逆順・過大gapを拒否する。[impl:2168](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:2168) [impl:3890](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:3890) |
| Review B MF-8 — 全域decision function | `closed` | completeness、POS四分岐、NEG除外を順に処理し、最終eligibilityは論理ANDで導出する。[impl:3683](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:3683) [impl:3713](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:3713) |
| Review B MF-9 — T-181指標 | `partial` | primary、finding、resource、decisionはaggregate由来だが、logical turnは非計測、新規findingはexact-string intersection、N-3でreliabilityが欠落し得る。[impl:3641](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:3641) [impl:3655](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:3655) [impl:3783](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:3783) |

全17件は **closed 12 / partial 4 / regressed 1** です。fix4時点でclosedだった10件（A-1〜A-4、A-7、A-8、B MF-2〜MF-4、B MF-7）にはfix5回帰を認めません。

## N-1〜N-6

| ID | 判定 | severity / real-refuted / 根拠 |
|---|---|---|
| N-1 | `partial` | **CRITICAL / real**。public stateからmapとSHAは除かれたが、caller自身が指定するsame-ownerの0700 custodian内に平文mapが存在する。またverdict rowは裁定時のpacket bytesを記録しない。[impl:4315](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:4315) [impl:4339](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:4339) [impl:4388](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:4388) |
| N-2 | `closed` | **HIGH / real→closed**。attempt receiptはagent workspace外、書込bindはCODEX_HOME/output/stdout/stderrだけ、agent pathは乱数名でslot/block/attempt語を拒否する。[impl:1814](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:1814) [impl:1835](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:1835) [impl:2334](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:2334) |
| N-3 | `regressed` | **HIGH / real**。非対称technical retryは通るようになったが、mateの既存post-treatmentを`pair-invalidated`へ上書きし、final-only reliability集計から消す新回帰がある。[impl:3578](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:3578) [impl:3718](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:3718) |
| N-4 | `closed` | **CRITICAL / real→closed**。POS四分岐を先に固定し、NEG除外をANDする。16通りの直積fixtureもある。[impl:3683](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:3683) [test:1596](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:1596) |
| N-5 | `partial` | **HIGH / real**。提示された強調付き4例は拒否するが、正規化後も限定的disclaimer regexである。`GO。これは最終判断ではない。`はdecision=`GO`、disclaimer=falseとなる。[impl:3062](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:3062) [impl:3070](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:3070) |
| N-6 | `closed` | **MEDIUM / real→closed**。恒真な`logical_turns=1`を資源値から除き、single-turn protocolと`model_calls`比較へ明示的に降格した。[impl:2956](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:2956) [impl:3783](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:3783) |

N-1〜N-6は **closed 3 / partial 2 / regressed 1** です。

## 回帰・M1〜M12・自己追認

歴史controlは維持されています。実ファイルSHAを独立literalへ照合したうえで、`focus1 → NO-GO / true`、`focus2 → GO / false`を直接assertします。[test:1649](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:1649)

M1〜M12の名目nodeは全件実在します。

| 変異 | 期待node |
|---|---|
| M1 | [test:734](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:734) |
| M2 | [test:743](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:743) |
| M3 | mode/HEAD/extra/focus各node。[test:762](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:762) [test:774](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:774) |
| M4 | [test:1381](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:1381) |
| M5 | 実extra session負例。[test:1196](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:1196) |
| M6 | 名目nodeはあるが実効対応なし。[test:1898](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:1898) |
| M7 | [test:1389](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:1389) |
| M8 | [test:1406](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:1406) |
| M9 | [test:1472](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:1472) |
| M10 | [test:1649](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:1649) |
| M11 | [test:1724](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:1724) |
| M12 | [test:1734](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:1734) |

M6のnodeは実際のrow/body swapではありません。2 packetへ同一本文を置き、二読者の不一致と誤ったjudgmentを検出しているだけです。[test:1907](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:1907) [test:1929](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:1929) packet A/B本文を交換して裁定させ、freeze後に戻す変異には対応しません。したがって実効検出力は「12/12」ではなく、**M6の1件が未対応**です。

実rollout goldenのsource pinは実効です。full rollout SHA、literal token行SHA、実ファイルの該当行を三者照合しています。[test:1128](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:1128) 一方、fake E2Eは同じproduction `collect_run` / `score_run`から期待JSONを生成するため、単独では独立oracleではありません。[test:556](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:556)

## Git object閉包

| 経路 | 結論 |
|---|---|
| packed-refs / reflog / loose replace / grafts | 削除と非空拒否の双方がありclosed。[impl:682](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:682) [impl:1070](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:1070) |
| alternates / http-alternates / `.git/objects/info` | 外部object経路は閉じ、`fsck --unreachable`も行う。commit-graph等は回答blobの外部到達経路ではない。[impl:702](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:702) [impl:1095](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:1095) |
| 初期化済みsubmodule | object storeを再帰検査する。[impl:855](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:855) |
| 未初期化submodule | gitlink SHAだけでなく、空worktree、`.git` markerなし、admin storeなしを要求する。[impl:812](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:812) |
| `--reference` / extra bind | bwrap argvをcanonical再構成し、snapshot以外のhost object storeをmountしない。[impl:1702](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:1702) [impl:2409](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:2409) |
| snapshot外 `GIT_*` | allowlist生成時とbwrap `--clearenv`で除去する。[impl:1506](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:1506) [impl:1858](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:1858) |
| `/proc` | fresh PID namespaceなのでhost/兄弟process経路は閉じる。自分自身のeffort argvは意図したtreatment情報。[impl:1713](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:1713) |

残るのはobject閉包ではなく、root `.git`内の任意メタデータを外部goldenへ固定しないN-7と、未初期化submodule URLへnetwork egressできるN-8です。親実測のPOS/NEG成果物へ回答到達する経路は立証されていないため、いずれも **LOW / realだが現成果物影響なし / backlog・limitationとして記録可** です。

## 実走を止めるべき所見

1. **F3-1 — packet内容とverdictの時間的束縛欠落**

   - severity: **CRITICAL**
   - real/refuted: **real**
   - 成果物影響: packet A/Bの本文を裁定前に交換し、freeze後に戻すと、最終packet SHA・output SHA・freeze SHAはすべて通る一方、verdictは逆runへ帰属します。arm別`k/3`、NEG finding、新規finding、T-184 eligibilityを反転できます。
   - 根拠: verdict append時はpacketファイルを読まず、最終verify時に「現在の」本文だけを検査します。[impl:4388](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:4388) [impl:3543](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:3543)
   - 最小fix: 各readerのverdict rowへ、読取時packet digestまたはcustodian keyed commitmentを機械付与し、freezeとrevealでoutput SHAへ結ぶ。strong maskingを主張するならcustodianを別OS権限/processへ移す。

2. **F3-2 — N-3 fixがpost-treatment occurrenceを消す**

   - severity: **HIGH**
   - real/refuted: **real / fix5 regression**
   - 成果物影響: `max=technical-invalid、high=partial-output`のgenerationをretryして成功すると、highの既発生failureが`post_treatment_reliability=0`、`online_max_escalation_candidate=false`になります。
   - 根拠: `individual_failure_class`へ退避後に`pair-invalidated`へ上書きし、reliabilityはfinal attemptだけを数えます。[impl:3581](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:3581) [impl:3718](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:3718)
   - 最小fix: primary分母ではpair-invalidatedを除外しつつ、reliabilityは全attemptの`failure_class`または`individual_failure_class == post-treatment`を数える。その組合せの負例を追加する。

3. **F3-3 — 曖昧decisionの残存fail-open**

   - severity: **HIGH**
   - real/refuted: **real**
   - 成果物影響: 本来arm failureである未確定出力がvalidとなり、primary分母とreliability、escalationを楽観化します。
   - 反例: 500 bytes以上の総括を`GO。これは最終判断ではない。`で開始する。
   - 最小fix: 正規化後の第一decision文を有限grammarで完全一致させるか、二読者verdictへ`decision_unambiguous`を追加して機械regexをprimary validityに使わない。反例を独立nodeにする。

4. **F3-4 — prelaunch failureがattempt ledgerを中途状態にする**

   - severity: **HIGH**
   - real/refuted: **real**
   - 成果物影響: `_supervise_one()`がconfig copy、version probe、`Popen`等で例外になると`reserved`だけが残り、resource計上もpair retryもできず、実験全体が再利用不能になります。
   - 根拠: reservation後の`_supervise_one()`に例外捕捉がなく、completed行は正常return後だけ追記されます。[impl:2155](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:2155) [impl:2168](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:2168)
   - 最小fix: supervisor例外も構造化technical-invalid completionとして必ずledgerへ残し、未起動mateを明示したうえで次pair generationを許す。

## limitationとして記録可能な残差

- **MEDIUM / real:** `turn_accounting`は恒真値を除いた点で正しい一方、T-181はlogical turn差を測定できません。T-184で「turn削減」を根拠にしなければ limitationとして記録可。
- **MEDIUM / real:** novel findingは両読者の`root_cause`等のexact tuple一致だけを採用します。[impl:3477](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:3477) 同義別表現を落とし得るため、finding coverageは下限・advisoryと明記するなら limitationとして記録可。
- **MEDIUM / real:** packetは均一乱数名、ランダム順、固定mtimeですが本文bytesと長さはそのままです。[impl:4301](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:4301) [impl:4312](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:4312) 出力文体・長さによるeffort推測はplan A4どおり制御不能であり、blindではなくsame-owner advisory maskingと記録する必要があります。
- **LOW / backlog:** N-7のroot `.git`任意メタデータとN-8のnetwork egressは、親実測snapshotへの回答到達・成果物影響が未立証です。limitationとして記録可。

## 総括

**NO-GOです。全17件はclosed 12 / partial 4 / regressed 1、N-1〜N-6はclosed 3 / partial 2 / regressed 1です。fix4時点でclosedだった10件にはfix5による回帰を認めません。歴史focus1→NO-GO/R-1候補true、focus2→GO/falseのcontrol、Git object閉包、raw collect/score replay、逐次crossover、NEG訂正版、golden source SHA pinも維持されています。親実測173 passedを前提にしても、テスト数不足を理由に止めているのではありません。止める理由は、裁定時に読まれたpacket本文がverdictへ束縛されずswap→restoreでarm帰属を反転できること、fix5のpair-invalidated処理がmate側の実在post-treatment failureをreliabilityとescalationから消す新回帰、句読点越しの曖昧decisionをvalidにする残存受理経路、prelaunch technical failureをretry可能なattemptとして記録できないことです。特に前二者はT-184の品質・採用rowを直接変えるため、単なるinsight上の注意書きには落とせません。したがってこの実装のまま10 runの実走へ進むべきではありません。logical turn非計測、exact-string finding dedup、same-owner masking、N-7/N-8は主張を限定すればlimitationとして記録可能ですが、上記4件を親がreal/refuted裁定し、少なくともpacket/verdict束縛とN-3集計回帰を閉じるまでは実走開始を承認できません。**