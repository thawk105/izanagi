判定は **NO-GO**。must-fix は **9件**です。現状のまま10 runを実走してはいけません。指定資料はすべて読了しました。pytest・runner・mutationは実行しておらず、author報告の緑を本レビューでは追認しません。

## Must-fix 所見

### MF-1 — arm間の treatment 同一性が自己申告でしかない

- severity: **CRITICAL**
- real/refuted: **real**
- 根拠: `collect-run` は `argv_sha256` と `snapshot_manifest_sha256` を引数から受け取ってそのまま receipt に写すだけです。[codex_reasoning_ab.py:915](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:915) aggregate 側では prompt/snapshot SHA が manifest から欠落しても受理します。[codex_reasoning_ab.py:1497](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:1497) CLI version は非空しか検査せず、model も caller が期待値を変更できます。CODEX_HOME、`config.toml`、auth/config closure、bwrap argv、binary SHA、sandbox/world-state、環境変数には receipt がありません。
- arm漏洩経路: `render-prompt --new-root` が絶対pathをpromptへ埋めるため、root名に `max/high` やrun IDが入れば直接漏れます。[codex_reasoning_ab.py:730](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:730) CODEX_HOME名、PWD、環境変数、`/proc/*/cmdline`、実行中rolloutの `turn_context.effort` からも復元可能です。
- **成果物影響:** prompt・snapshot・CLI・config・sandbox差をreasoning差として誤帰属し、T-184のroutingを反転させられます。
- 最小fix: caseごとに単一のcanonical prompt SHA/content-manifest SHAを必須化し、同caseの全armで集合濃度1をassertする。launch receiptには正規化した実argv、bwrap/version、CLI binary/version、config SHA、環境allowlist、sandbox/world-stateを保存し、許容差をeffort一箇所だけに固定する。pathはarm-neutralにする。

### MF-2 — snapshot内のGit履歴から正解逐語へ到達できる

- severity: **CRITICAL**
- real/refuted: **real**。E5の「正確な旧focus pathが見えない」はrealですが、「歴史回答・他run出力が不可視」への一般化はrefutedです。
- 根拠: snapshotは現在repoを通常の `git clone --no-hardlinks` で丸ごとcloneし、古いHEADをcheckoutするだけです。[codex_reasoning_ab.py:542](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:542) `.git`検査はルートがdirectoryかを見るだけで、refs、reflog、objects、alternates、replace、remote refsを閉じません。[codex_reasoning_ab.py:619](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:619)
- read-only Git検査では、`ARTIFACT_COMMIT=08a7e5f2` は統合commitの子孫で現行refsから到達可能であり、そこから `focus1.md` / `focus2.md` を `git show` できます。working tree上の禁止file assertは無意味化されています。
- probeの射程:

  - probe 1のmain repo `ls`成功・出力空はtmpfs mountpointとして正常であり、漏洩証拠ではありません。
  - `.codex/sessions/2026` の存在はfresh run自身のsessionと歴史sessionを区別していません。
  - exact `focus1.md` のENOENTはその1 pathだけを証明します。
  - probe 2はsnapshot markerの可視性しか証明しません。
  - relative `..`、glob/find、別clone、symlink/hardlink、Git objects/common-dir、`/proc/*/{environ,cmdline,fd}`、CODEX_HOMEの兄弟runは未検査です。

- transcript外部参照auditは `/home/...` の明示文字列だけを探し、hitしてもrunを無効化しません。[codex_reasoning_ab.py:888](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:888)
- **成果物影響:** POSは既知正解、NEGは歴史GO回答を読めるため、R-1件数、新規finding、偽陽性、arm差がすべて汚染されます。
- 最小fix: snapshot作成後に期待branch以外の全ref/remote/reflog/replace/alternatesを除去し、unreachable objectをpruneする。`git cat-file -e 08a7e5f2` と禁止成果物の全ref検索が失敗することをoracle化する。bwrapはsnapshotを`--ro-bind`し、home/tmpを全面maskして必要pathだけbind、envをallowlist化し、PID/procも分離する。上記残経路を負probeとして実走前に殺す。

### MF-3 — NEG snapshotが訂正版仕様に追随していない

- severity: **CRITICAL**
- real/refuted: **real**
- 根拠: 正本の訂正版はNEGを `brief.md / adjudication-plan-v2.md / review-a / review-b / focus1 / fix2` の6件とし、`fix1.md`を禁止しています。[adjudication-plan-v2.md:76](/home/SFC/tanab/.claude/jobs/c94644e8/tmp/t181-wave/adjudication-plan-v2.md:76) 実装は旧5件 `review-a / review-b / fix1 / fix2 / focus1` のままです。[codex_reasoning_ab.py:116](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:116)
- **成果物影響:** NEG promptは必須2資料を読めず即停止するか、要求されていないfix1を見た別treatmentになります。負対照の偽陽性occurrenceは解釈不能です。
- 最小fix: allowlist/hashを訂正版6件へ変更し、prompt内絶対path集合とsnapshot untracked集合の完全一致テストを追加する。実NEG buildを静的fixtureではなく正本blobで再検証する。

### MF-4 — `verify` は凍結artifactのreplayではなく、可変な自己申告JSONのjoin

- severity: **CRITICAL**
- real/refuted: **real**
- 根拠: freeze保証は `frozen: true` というbooleanだけです。[codex_reasoning_ab.py:1598](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:1598) `verify` はraw events/rollout/done/snapshotからreceiptを再生成せず、既製receipt/scoreを信用します。scoreはoutput SHAだけ合わせれば `r1_candidate` やdecisionを任意に書けます。[codex_reasoning_ab.py:1461](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:1461) sessions-rootも任意なのでsession集合検査を省略できます。
- `test_verify_replays...` は合成receipt/scoreを直接作って通すテストで、replayを試していません。[test_codex_reasoning_ab.py:602](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:602) 「real slice」も実rollout bytesではなく、転記した定数からJSONLを再生成する自己追認fixtureです。[test_codex_reasoning_ab.py:34](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/orchestrator/tests/test_codex_reasoning_ab.py:34)
- freshnessのinode、初期size、launch envelopeもpost-hocにcallerが渡せ、prelaunch取得を証明しません。
- **成果物影響:** run後のschedule、arm、score、token、attemptを変更しても「frozen replay valid」と表示でき、trial ledgerの監査性が成立しません。
- 最小fix: prelaunch schedule hashを外部artifactへ先に凍結し、各run receiptへ束縛する。manifestでraw rollout/events/done/output/prompt/snapshot oracle/config/argvのSHAとroot内pathをpinし、`verify`自身が`collect-run`と`score-run`を再実行する。sessions-rootはrunごとの必須mappingにする。trackedな実rollout sliceをgoldenにする。

### MF-5 — `blind_id` とprimary adjudication経路が存在しない

- severity: **CRITICAL**
- real/refuted: **real**
- 根拠: コード・テストに`blind_id`、blind packet、judgment取込、unblind操作がありません。scoreとaggregateはいずれも `primary_endpoint: not_scored` です。[codex_reasoning_ab.py:1326](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:1326)
- manifest、receipt、aggregateはarm、run ID、session ID、token、wall-clock、並び順を公開します。launcherでもある親はscheduleを既知なので、後から名前だけ乱数化しても盲検にはなりません。armを含むpathやcurrent rolloutから出力本文自身へeffortが漏れる経路もあります。
- historical controlテストが検証するのは機械candidateであり、primary人手裁定者がcodebook controlを先に通った証拠ではありません。
- **成果物影響:** primaryの`r1_detected`が得られず、期待armや長文化傾向を知った親の判断を「盲検primary」と誤記できます。
- 最小fix: launcherとは別の評価者へ、暗号学的乱数ID・ランダム順・均一filenameの本文だけを渡す。receipt/score/timestamp/token/mapは渡さず、全blind IDの3命題判定を凍結してからmappingを公開する。独立評価者を確保できなければ「label-masked探索評価」と明記し、盲検primaryを名乗らない。

### MF-6 — retry・部分出力・abortの分類と全attempt計上が成立しない

- severity: **CRITICAL**
- real/refuted: **real**
- 根拠:

  - manifestは常に10行を要求する一方、attemptを1〜3で許します。[codex_reasoning_ab.py:1432](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:1432) 元attemptと最大2 retryを全保存すれば10行を超えるため、仕様2.7とschemaが両立しません。
  - unresolved technical-invalidがあってもaggregate全体は`valid=true`になり得ます。
  - post-treatment理由とtechnical理由が併存すると、technical扱いでpair全体を分母から外せます。
  - ledgerの`fragment` outcome自体はfailureへ伝播せず、既存validator rejectを見落とせます。
  - summary冒頭のdecisionしか見ないため、後段の相反GO/NO-GOを曖昧として拒否しません。[codex_reasoning_ab.py:1276](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:1276)
  - abort/incompleteではwall-clockが`None`となり、全attempt計上に反します。

- **成果物影響:** arm依存のtruncation、rate limit、post-inference abortをtechnical-invalidとして選択的に捨て、残存runだけで品質不変を作れます。retry分のtoken/wallも消えます。
- 最小fix: 10個のassigned slotと、各slot配下の1〜3 attemptsを別tableにする。全attemptを保存・資源集計し、最後までtechnical-invalidなら`experiment_complete=false`として品質裁定を禁止する。treatment開始後のpartial/abort/validator rejectは優先的にarm failureとし、rate-limit・retry・compactionを明示field化する。

### MF-7 — pair同時実行がprimary品質へ干渉する

- severity: **HIGH**
- real/refuted: **real**
- 根拠: 実装が保証するのは任意幅のlaunch envelopeが一部重なることだけです。[codex_reasoning_ab.py:1450](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/tools/codex_reasoning_ab.py:1450) start差上限、pair間逐次性、overlap時間は検査しません。テスト自身も2時間の共通envelopeを使っています。
- 交絡経路:

  - 同じAPI key/accountのTPM、同時request、retry quotaを両armで奪い合う。
  - maxの長い推論がhighの429・queue・retryを誘発する、または逆方向に遅延させる。
  - backend batching、cache、serving queue、共有windowが相関を作る。
  - CPU、memory、network、disk、page cache、共有snapshotのtool callが競合する。
  - 短いarmは全時間競合し、長いarmは末尾を単独実行するためwall-clock exposureが非対称。
  - 失敗pairだけ後のwindowでretryされ、時刻に対する適応的選択になる。

- **成果物影響:** rate-limitやpartial outputというprimary結果自体が相手armにより変わるため、「wall-clockは二次指標」と注記するだけでは足りません。
- 最小fix: primaryはarm順を事前乱数化した隣接逐次crossover blockにする。時刻傾向はblockと順序で記録する。同時実行を維持するならquota・host資源を分離し、start lag、overlap、pair makespan、429/retryを測る必要があります。

### MF-8 — 事前登録表が全観測に対する一意な決定関数ではない

- severity: **HIGH**
- real/refuted: **real**
- 表にない、または複数行が同時適用される観測:

  - retry上限後もtechnical-invalid pairが残る。
  - POS 3/3対3/3と同時に、NEGで片armの偽must-fixが出る。
  - NEGで「偽」ではなく独立裁定でrealな新規findingが出る。
  - 同じ2/3でも、silent missと可観測partial outputが混在する。
  - human primaryと`r1_candidate`が不一致になる。
  - max基準missとhigh偽陽性が同時発生する。
  - qualityは同じだがtoken/turn/wallが採用想定と逆転する。

- `technical-invalid発生`行は再実行手順だけで、retry枯渇後の裁定を定義していません。負例行もoccurrenceを記録するだけで、POS rowに対する優先順位やhigh採否を決めません。
- **成果物影響:** 観測後に「どの失敗を採用阻止に使うか」を選べ、同一データからT-184の異なるpolicyを正当化できます。
- 最小fix: `experiment completeness → POS primary → NEG adjudicated false finding → post-treatment reliability → resource report` の優先順位を持つ全域decision tableをrun前に凍結する。silent missはoffline不採用条件、partial outputはonline max escalation候補として別出力にする。aggregateが適用rowと理由を機械出力できるschemaを追加する。

### MF-9 — T-181の必須指標を成果物として出せない

- severity: **CRITICAL**
- real/refuted: **real**
- [T-181]要求は [phase3.md:537](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/docs/phase3.md:537) に対し、現状は次のとおりです。

| 要求 | 現実装 | 判定 |
|---|---|---|
| must-fix再現率 | heading依存の`r1_candidate_n`のみ。primary `r1_detected`なし | **出せない** |
| 新規finding | 各scoreに候補heading/hashはあるがaggregateで破棄。novelty、real/refuted、意味dedupの定義なし | **出せない** |
| token | receiptにinput/cached/output/reasoning/CLI reportedはあるがaggregateはCLI合計のみ。retry/invalid全attemptを欠落可能 | **部分的** |
| turn | `turn_id`はあるがturn数なし。`model_calls`は非null token-count event件数でturnではない | **出せない** |
| wall-clock | 正常taskのevent差のみ。launch→exit、abort、retry、pair makespanなし | **部分的** |
| max escalation裁定 | arm failure数は出るがprimary miss、偽finding、判定表row、escalation outcomeなし | **出せない** |

- 「新規finding」の実装上の定義は存在しません。最小定義は「事前凍結した既知finding集合と意味同値でなく、対象snapshotに対して盲検裁定でrealと認定され、root cause単位でdedupされたfinding」です。単なるR番号やheading件数にしてはいけません。
- **成果物影響:** insightがT-181の要求を満たさず、T-184は未計測値を「finding coverage」「turn削減」「品質劣化gate」と誤引用できます。
- 最小fix: primary judgment ledger、新規finding adjudication/dedup ledger、全attempt resource ledger、logical turnとmodel-callの別field、process monotonic wall、最終decision rowをtracked artifact schemaへ追加する。

## 現実装から許される最強の主張

現状の実装だけから書ける上限は次です。

> manifestに記載された10行と、そこから参照された可変receipt・score・outputの一部fieldについて相互整合を検査し、自己申告されたcase/arm別に機械候補件数、CLI reported token、token-count event件数、正常taskのtimestamp差を再集計した。

これはlive runの真正性、arm同一性、隔離、盲検primary、must-fix再現率、新規finding、reasoningの因果効果を支えません。

T-184で禁止すべき表現は以下です。

- 「両armはbyte-identicalなprompt/snapshot/configを見た」
- 「歴史回答と先行run出力は到達不能だった」
- 「primaryは盲検だった」
- 「high/maxのmust-fix再現率はX%」
- 「新規finding coverageは同等だった」
- 「偽陽性率は0だった」
- 「highはmaxと同等・非劣性・安全だった」
- 「reasoningだけが観測差の原因である」
- 「backendが実際にmax/high相当の計算を行った」
- 「pair同時実行でserving window交絡を除去した」
- 「wall-clock短縮はeffort変更の効果である」
- 「partial outputを含めても品質不変だった」
- 「全attemptのtoken/turn/wall-clockを計上した」
- 「凍結artifactをraw rolloutからreplay検証した」
- 「T-181がsilent品質劣化を検出してmaxへescalateできるようにした」
- 「この結果だけでfocused reviewをhighへ変更できる」

## 裁定パッケージ候補

以下はscope外のままで、実装済みと扱ってはいけません。

- **裁定パッケージ候補:** 非名指しheld-out正例によるblind discovery評価。
- **裁定パッケージ候補:** margin/powerを定めた非劣性実験。
- **裁定パッケージ候補:** backend build/compute identity attestation。
- **裁定パッケージ候補:** productionでのsilent miss検出。oracleなしではruntime escalation不能であり、max shadow・周期監査・人手oracleの択一が必要です。

## 総括

NO-GO。must-fixは9件です。要旨は、第一に通常cloneされたsnapshotのGit refs/objectsから後発のfocus1/focus2逐語へ到達でき、親probeが確認したexact pathのENOENTでは隔離閉包を証明できないこと、第二にprompt・snapshot・argv・CODEX_HOME・config・CLI/bwrap環境のarm同一性が自己申告であり、effortやarm名がpath・環境・`/proc`・current rolloutへ漏れ得ること、第三に`verify`がraw artifactを再生せず可変receipt/scoreを信用し、run前freezeも証明しないこと、第四にblind_idとprimary adjudication、全attempt retry台帳、新規finding定義、logical turn、失敗時wall-clockが存在しないことです。さらにNEG snapshotは訂正版allowlistへ追随しておらず、負対照自体が別treatmentです。pair同時実行は共有quota・rate limit・serving queue・host資源を介してprimary品質へ干渉し、wall-clockを二次指標と呼ぶだけでは交絡を除去できません。したがって本A/Bの実走は許可できません。少なくともGit object閉包、arm同一性receipt、NEG修正、raw replay freeze、独立盲検、slot/attempt分離、非干渉schedule、全域判定表、T-181指標schemaを閉じた後に段6再レビューへ戻す必要があります。