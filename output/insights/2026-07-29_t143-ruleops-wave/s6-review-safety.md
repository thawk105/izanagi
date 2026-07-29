## 差分確認

静的判定は **NO-GO**。BLOCKER 1件、MUST 6件、SHOULD 2件、NIT 1件。

- 指定7ファイルはすべて絶対パスで全文確認した。
- staged diff はなし。tracked 7件、新規の `tools/ruleops.py`、対応test、RuleOps docs/ledgerを全行確認した。主要差分のハッシュは再確認時も不変だった。
- wave の構造化 artifact は確認した。巨大な `*.log` は `CLAUDE.md` の生ログ全文非読込規律に従い、内容を根拠にしていない。
- 編集、commit、RuleOps CLI、pytest、checkerは実行していない。段5の実走結果は自己申告データであり、緑として追認しない。

## findings

### RA-1 — BLOCKER: repository-local Git configから外部helperを起動でき、read-onlyではない

- 根拠: Git環境はglobal/system configを無効化するが、repository-local configは残る。[`tools/ruleops.py:253`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:253) Git起動時に上書きするのも `core.useReplaceRefs` だけである。[`tools/ruleops.py:278`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:278) その状態で複数の `git log` を実行する。[`tools/ruleops.py:446`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:446) [`tools/ruleops.py:689`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:689)
- `log.showSignature=true` と `gpg.program` の組合せは外部programを起動できる。`submodule.recurse` 等もlocal configから有効化できる。optional lockを止めてもこの実行面は閉じない。
- 放置時の成果物影響: configされたhelperがworktree、Git metadata、外部ファイルを書けるため、P1のread-only境界が成立しない。後でparse失敗してrc=2になっても書込みは取り消されない。
- 最小fix: `git log` に署名表示・external diff・textconvを明示的に無効化し、grepのsubmodule再帰も無効化する。local configに毒helperを設定したsynthetic repoで「helper未起動」を検査する。現在のtestはGIT環境変数だけを検査している。[`test_ruleops.py:651`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/orchestrator/tests/test_ruleops.py:651)

### RA-2 — MUST: 一つのsnapshot内で可変な`HEAD`を再参照し、epochが混ざる

- 根拠: `head`を一度取得する一方、treeは再び文字列`HEAD`から取得する。[`tools/ruleops.py:333`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:333) [`tools/ruleops.py:336`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:336) last-change、grep、pickaxeも各時点の`HEAD`を参照する。[`tools/ruleops.py:453`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:453) [`tools/ruleops.py:592`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:592) [`tools/ruleops.py:694`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:694)
- 放置時の成果物影響: 並行commit/checkoutにより、出力の`head=A`、tree/blob=B、grep/history=Cになり得る。grepが新blobでhitし、line抽出が旧blobを読む場合はhitを黙って落とし、誤った`structurally_valid=true`まで到達し得る。
- 最小fix: 全Git queryを最初に取得したOIDへ束縛し、成功直前にHEAD不変を再確認する。shallow/graft状態についても開始・終了の不変確認を置く。

### RA-3 — MUST: control除外が「exact artifact」ではなくpath全履歴・pathspec patternを免除する

- 根拠: control pathをそのまま `:(exclude)<path>` に連結する。[`tools/ruleops.py:687`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:687) `_repo_path`は正当なGit filenameである `*`、`?`、`[` を禁止しない。[`tools/ruleops.py:241`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:241) control側の履歴検索もliteral指定ではない。[`tools/ruleops.py:710`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:710)
- literalな`receipt*.json`というfilenameは他pathまで除外する。また現在receipt/ledgerであるpathの、control化以前の普通のconsumer履歴も全て未レビュー免除になる。
- 放置時の成果物影響: `pickaxe_events`から本物の過去consumerを落とし、exact control artifactだけ除外するという裁定と異なる候補packageを通す。
- 最小fix: pathspecを明示literal化し、除外を現在のpathだけでなくcontrol blob・導入epochへ束縛する。metachar filenameと「普通のconsumerを後からreceipt pathへ転用」の回帰testを追加する。

### RA-4 — MUST: worktree ledgerのpathをHEAD上のcandidate/consumerとaliasできる

- 根拠: `--ledger`はrepo内の任意のregular worktree fileを受理する。[`tools/ruleops.py:877`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:877) HEAD snapshot取得後に、そのworktree bytesを別epochから読む。[`tools/ruleops.py:1315`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:1315) [`tools/ruleops.py:1318`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:1318) ledger pathは無条件にcontrol集合へ入るが、candidate集合との交差を拒否しない。[`tools/ruleops.py:1156`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:1156) [`tools/ruleops.py:1360`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:1360)
- 例えばcandidate fileのworktree内容をledger JSONに置き換え、同pathを`--ledger`に指定すると、HEADではcandidate、worktreeではcontrol ledgerとして扱われる。candidate自身のhitまで除外できる。
- 放置時の成果物影響: exact control artifactでないHEAD blobをscan対象から外し、不完全なreview集合を構造validとして人間裁定へ送る。
- 最小fix: `ledger_rel in candidate_paths`を拒否する。HEADにledger pathが存在する場合は、そのHEAD blob自体がstrict RuleOps ledgerであることを確認してからcontrol扱いし、untracked ledgerは「HEAD上に除外物なし」と扱う。

### RA-5 — MUST: markerと`derived-report`分類が引用・code fenceで偽装できる

- 根拠: marker parserは先頭64行のどこにあっても、行文字列が一致すればmarkerとする。[`tools/ruleops.py:500`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:500) JSON側もduplicate-keyを拒否しない通常の`json.loads`である。[`tools/ruleops.py:512`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:512) `artifact_class`はledger値だけ、source引用は単なるsubstringで成立する。[`tools/ruleops.py:1259`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:1259) [`tools/ruleops.py:1288`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:1288)
- docsは「冒頭の正準marker」を要求しており、実装と一致しない。[`docs/ruleops.md:85`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/docs/ruleops.md:85)
- 放置時の成果物影響: 凍結証拠がcode fence内でmarker例を引用し、本文でsource pathを否定的に言及するだけでもderived-report候補として通る。自動削除はされないが、人間裁定packageの分類が偽になる。
- 最小fix: byte先頭の一意なfrontmatterだけをstrict parserで認識し、fence・引用・duplicate keyを拒否する。retention classはtarget本文の自己申告ではなく、blob-pinnedな人間分類として分離する。

### RA-6 — MUST: replacement evidenceと「人間review」が構造的に空でも通る

- 根拠: `replacement_guards`は任意のtracked regular blobでよく、guard/checkerであることを確認しない。[`tools/ruleops.py:1163`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:1163) `replacement_nodes`は`file::symbol`形とfile blobだけを検査し、symbolの実在を確認しない。[`tools/ruleops.py:1177`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:1177) [`tools/ruleops.py:1184`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:1184)
- `_string`は空白だけを非空として受理するため、candidate/review rationaleやsemantic queryを空白で満たせる。[`tools/ruleops.py:203`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:203) [`tools/ruleops.py:964`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:964)
- 放置時の成果物影響: 存在しないpytest node、無関係なREADME、空白rationaleだけで代替・人間review欄を埋め、`structurally_valid=true`を得られる。
- 最小fix: symbol実在を観測signalとして静的確認する。ただし同値性・安全証明とは呼ばない。guard種別を構造化するか、少なくとも個別review/rationaleを必須にする。人間記入欄とqueryはstrip後の非空・control文字なしを要求する。

### RA-7 — SHOULD: 128件を超えるsignalはdraft可能だが永久にcheck不能

- 根拠: evidence array上限は128件。[`tools/ruleops.py:38`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:38) `inspect --draft`は計算した全hit/eventを上限確認なしで出す。[`tools/ruleops.py:837`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:837) 一方、checkはreviewed arrayを128件で拒否する。[`tools/ruleops.py:945`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:945) [`tools/ruleops.py:990`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:990)
- 放置時の成果物影響: common queryや高頻度pathが128件を超えると、全件reviewしてもpackageは永久赤になる。RuleOpsが候補を人間へ運べない。
- 最小fix: inspect時点で明示的な`signal-overflow`にするか、review集合を別のblob-pinned artifactへ分離する。上限内外のuser journeyをtestする。

### RA-8 — SHOULD: JSON size limitを全bytes読んだ後にしか検査しない

- 根拠: ledgerは`read_bytes()`後に1 MiB制限を適用する。[`tools/ruleops.py:1318`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:1318) [`tools/ruleops.py:1322`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:1322) receiptもblob全体を`cat-file`で取得してから256 KiB制限を確認する。[`tools/ruleops.py:1070`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:1070)
- 放置時の成果物影響: 巨大ledger/receiptでOOMまたは長時間停止し、安定reason codeによるfail-closedではなく受入環境自体を落とし得る。
- 最小fix: ledgerはopen後の`fstat`とbounded read、receiptは既知の`TreeEntry.size`をblob読取前に検査する。symlink交換を避けるため同じfile descriptorで検査・読取する。

### RA-9 — MUST: hit/history testの期待値がproduction計算への自己参照

- 根拠: valid ledger fixtureはproductionの`inspect_target`で期待hit/eventを生成し、そのままvalidatorへ戻す。[`test_ruleops.py:213`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/orchestrator/tests/test_ruleops.py:213) [`test_ruleops.py:219`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/orchestrator/tests/test_ruleops.py:219) M7相当は、その自己生成集合から1件popするだけである。[`test_ruleops.py:497`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/orchestrator/tests/test_ruleops.py:497) pickaxeも同型である。[`test_ruleops.py:509`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/orchestrator/tests/test_ruleops.py:509)
- 例えば `_pickaxe` が各tokenへ任意の1 commitを返す実装へ壊れても、inspectとcheckが同じ集合を使うため主要testは通る。
- read-only testもGit porcelainの前後一致だけで、ignored file、`.git/config`、外部helperの書込みを観測しない。[`test_ruleops.py:698`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/orchestrator/tests/test_ruleops.py:698)
- 放置時の成果物影響: consumer/historyの過少・過大計算やread-only退行がtest緑のままlandし、候補packageの検出力が黙って蒸発する。
- 最小fix: synthetic historyで作成時に得たcommit OID、literal path、lineを独立期待値としてexact集合比較する。local-config helper、control path reuse、metachar path、marker fenceを独立negative controlにする。

### RA-10 — NIT: 引数errorの「安定reason code」契約が実装されていない

- 根拠: docsは引数errorにも安定reason codeを要求する。[`docs/ruleops.md:93`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/docs/ruleops.md:93) しかし`parse_args`は例外処理の外にあり、argparse標準文言で終了する。[`tools/ruleops.py:1407`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:1407) testも`invalid choice`だけを期待している。[`test_ruleops.py:639`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/orchestrator/tests/test_ruleops.py:639)
- 放置時の成果物影響: CLI wrapperがargument failureをstable codeで分類できない。候補内容の安全性には直接影響しない。
- 最小fix: parserの`error()`をoverrideしてRuleOps reason codeへ正規化するか、docsを「validation failureのみ」に狭める。

## positive controls

- CLI source自身にはrepo fileのwrite APIがなく、stdout書込み以外はclosed Git helperへ集約されている。[`tools/ruleops.py:267`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:267) [`tools/ruleops.py:1422`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:1422)
- `GIT_OPTIONAL_LOCKS=0`と`--no-optional-locks`は二重に指定されている。[`tools/ruleops.py:259`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:259) [`tools/ruleops.py:279`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:279)
- inventory対象はHEAD regular blobに限定され、symlink/gitlinkはcandidateでも拒否される。[`tools/ruleops.py:373`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:373)
- ledger全候補集合を先に作り、guard、node、receipt、sourceからcandidate pathを排除する実装は正しい。[`tools/ruleops.py:928`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:928) [`tools/ruleops.py:1143`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:1143) [`tools/ruleops.py:1188`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:1188)
- ledger/receiptのduplicate key、unknown key、raw非UTF-8、NFC、path traversal、OID形式、object formatはfail-closedである。[`tools/ruleops.py:163`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:163) [`tools/ruleops.py:192`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:192) [`tools/ruleops.py:232`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:232)
- 成功出力は3 fieldに限定され、`human_approved`は常にfalse。docsも削除安全・受理集合同値・完全なconsumer閉包を明確に否定する。[`tools/ruleops.py:1376`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:1376) [`docs/ruleops.md:10`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/docs/ruleops.md:10)
- runnerは既存の未stage削除gateを先頭に維持し、RuleOps失敗後はsubmodule/pytestへ進まない。targeted非発火も既存分類と同じである。[`tools/run_tests.py:787`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/run_tests.py:787)
- inventory scopeとcheck出力keyにはtest側のliteral pinがあり、現HEAD hashの焼込みはない。[`test_ruleops.py:240`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/orchestrator/tests/test_ruleops.py:240) [`test_ruleops.py:619`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/orchestrator/tests/test_ruleops.py:619)

## scope 外の裁定候補

### RA-11 — MUST（scope外、C-1）: staged/index treeと受入結果の機械束縛

- 根拠: 既存削除gateはworktree上の未stage削除だけを`git ls-files --deleted`で見る。[`tools/run_tests.py:455`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/run_tests.py:455) RuleOpsはHEAD inventoryとworktree ledgerを検査し、index treeは読まない。[`tools/ruleops.py:1315`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/tools/ruleops.py:1315)
- staged deletion、またはindexにstagedしたledger Aとworktree ledger Bの差がある状態では、受入はcommit予定treeと異なる内容を検査できる。
- 放置時の成果物影響: precommitの緑を、実際には検査していないindex treeへ帰属させられる。commit後に再走すれば検出できるが、precommit結果との機械束縛はない。
- 最小裁定案: 現waveへ混ぜず、C-1としてapproval receipt、index tree OID、削除対象、fresh packageを束縛するcommit gateを別設計する。docsもこれを明示的に別裁定としている。[`docs/ruleops.md:108`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t143-ruleops/docs/ruleops.md:108)

nested test外延、mutation producer、実削除自動化も既裁定どおりscope外。現在HEADにnested testがないため、新たなin-scope findingには昇格しない。

## 総括

現状はread-onlyという最上位境界がRA-1で破れ、RA-2〜RA-6により非空candidateの「構造valid」も信頼できない。特にGit config helper、混合HEAD epoch、pathspec単位のcontrol免除、ledger/candidate alias、marker引用誤認はland前修正が必要である。

pytest・checkerは未実走であり、静的レビューとしての結論は **NO-GO**。