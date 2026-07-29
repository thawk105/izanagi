## 差分確認

指定12ファイルはすべて絶対パスで全文確認した。

現在の未commit差分は tracked 11ファイル、追加3,807行・削除2行、staged差分なし。`tools/ruleops.py` 2,002行、`orchestrator/tests/test_ruleops.py` 1,478行を含め、実コード・テスト・docs の全差分を確認した。未追跡の wave artifact は一覧と指定された構造化文書を確認し、指示どおり巨大な `*.log` は読んでいない。現実装との確認に不要だったため `s6-pre-fix-integrated.patch` 本文も読んでいない。

編集、commit、RuleOps CLI、pytest、checker、外部通信は実行していない。親・fixer記録の実走結果は green の根拠にしていない。

## finding closure

| finding ID | 状態 | 根拠 path:line | root cause が閉じた、または残る理由 |
|---|---|---|---|
| RA-1 | closed | `tools/ruleops.py:304-362`; `orchestrator/tests/test_ruleops.py:1150-1198` | 全Git呼出しがclosed helperを通り、local configの署名・external diff・textconv・submodule再帰をcommand/config双方で無効化する。poison helper testも独立sentinelを持つ。 |
| RA-2 | partial | `tools/ruleops.py:383-397`; `tools/ruleops.py:420-426`; `orchestrator/tests/test_ruleops.py:1228-1245` | HEAD OID固定とemit前HEAD再確認は閉じたが、shallow/graftsは開始時しか検査せず、終了時はHEADだけを見る。**MUST**。放置時はHEAD不変のまま履歴境界が途中で変わり、hit/historyが欠落したpackageを出せる。最小fixはsnapshot終了検査へnon-shallow/grafts不在を追加し、その移動negative testを置くこと。 |
| RA-3 | closed | `tools/ruleops.py:837-910`; `orchestrator/tests/test_ruleops.py:1248-1280` | control pathspecは`:(top,literal)`。除外は現在blobの最終導入eventだけで、同pathの旧non-control履歴とglob隣接pathを残す。 |
| RA-4 | closed | `tools/ruleops.py:1152-1183`; `tools/ruleops.py:1900-1917`; `orchestrator/tests/test_ruleops.py:1283-1300` | ledger/candidate aliasを拒否し、ledgerはworktree bytesがHEAD strict blobと一致する場合だけcontrolになる。dirty ledgerは除外特権を得ない。別種のledger/evidence aliasはRR-2。 |
| RA-5 | closed | `tools/ruleops.py:583-611`; `orchestrator/tests/test_ruleops.py:950-1000` | markerはbyte 0のcanonical typed marker一個だけ。quote、fence、先頭ゴミ、duplicate/noncanonical JSONを拒否する。 |
| RA-6 | closed | `tools/ruleops.py:244-257`; `tools/ruleops.py:1385-1415`; `tools/ruleops.py:1542-1626` | rationale/queryはstrip後nonempty・control-free。AST symbol実在とreceiptのtarget/review/result/guard/node集合を照合する。receipt `head` 自体の未束縛はRR-1。 |
| RA-7 | closed | `tools/ruleops.py:1025-1040`; `tools/ruleops.py:1728-1746`; `orchestrator/tests/test_ruleops.py:436-472` | inspect/check双方がevidence 128件、candidate 8件、query 4件の上限を明示reasonで拒否する。 |
| RA-8 | partial | `tools/ruleops.py:943-960`; `tools/ruleops.py:1186-1222`; `tools/ruleops.py:1907-1917`; `orchestrator/tests/test_ruleops.py:403-433` | worktree ledgerとreceiptは事前size検査されたが、dirty/custom ledgerではHEAD側ledger blobをsize検査前に`_blob()`で全取得する。**MUST**。放置時は小さいworktree ledgerと巨大HEAD blobの組合せでrunnerをOOM/長時間停止させられる。最小fixは`ledger_entry.size <= MAX_LEDGER_BYTES`を`_blob()`前に強制し、dirty tracked/custom ledgerの独立negative testを追加すること。 |
| RA-9 | partial | `orchestrator/tests/test_ruleops.py:203-259`; `orchestrator/tests/test_ruleops.py:591-603`; `orchestrator/tests/test_ruleops.py:1413-1469` | synthetic fixtureはliteral oracleへ直ったが、real-checkout E2Eはproduction `inspect`のreceipt、observed hits、pickaxe eventsをそのままexpected ledgerへ戻している。**MUST**。放置時はinspect/check共通欠陥がE2Eを生存する。最小fixはtarget blob・hit・historyを独立Git/literal oracleで構築すること。 |
| RA-10 | closed | `tools/ruleops.py:1944-1998`; `orchestrator/tests/test_ruleops.py:1108-1136` | argparse errorを`cli-args`、rc=2、tracebackなしへ正規化し、closed command setをliteral pinする。 |
| RB-1 | closed | `tools/ruleops.py:1085-1120`; `orchestrator/tests/test_ruleops.py:576-662`; `docs/ruleops.md:135-149` | `inspect --draft`が完全なadvisory receipt skeletonを出し、receipt先行commitから非空candidate checkまでの人間経路が実装・文書化された。 |
| RB-2 | partial | `tools/ruleops.py:34-40`; `tools/ruleops.py:124-133`; `tools/ruleops.py:861-925`; `orchestrator/tests/test_ruleops.py:1339-1478`; `tools/run_tests.py:521-527` | memoizationと上限は入ったが、最大8候補×各最大6 tokenで最大48本の全履歴`git log -S`が直列になり得る。cache keyに候補別control集合を含むため、同じqueryもreceiptが違えば再走する。60秒testは1候補・1queryだけ。**MUST**。放置時はschema-validな複数候補ledgerがrc=15 timeoutになる。最小fixはraw pickaxeを`(snapshot, token)`で共有してcontrol filteringを後段化し、global token予算と最大許容ledgerの60秒境界testを置くこと。 |
| RB-3 | closed | `orchestrator/tests/test_ruleops.py:905-920`; `tools/ruleops.py:929-998` | duplicate basenameとliteral consumer/historyを置き、basenameが曖昧ならsignalへ加えないことをliteralに検査する。 |
| RB-4 | closed | `orchestrator/tests/test_ruleops.py:553-574`; `orchestrator/tests/test_ruleops.py:679-834`; `orchestrator/tests/test_ruleops.py:1248-1280` | M5はexact current controlと旧履歴、M6は個別validな二候補とcross-candidate参照を分離したfixtureになった。 |
| RB-5 | partial | `orchestrator/tests/test_ruleops.py:1339-1478` | inventory非空・既知hit・runner接続は強化されたが、非空candidateの全signal expectedはproduction `inspect`由来で独立oracleではない。**MUST**。放置時はreal-checkout testがproducer/validatorの自己整合しか証明しない。最小fixは既知path/blob/commit/hit集合を独立Git照会とliteral expectedで作ること。 |
| RB-6 | closed | `tools/ruleops.py:1385-1415`; `tools/ruleops.py:1542-1626`; `orchestrator/tests/test_ruleops.py:1028-1085` | accepted root causeであるAST node実在、candidate path/blob、review state、guard結果、failed-node/guard集合の相互照合は実装された。receipt headの意味的未束縛は新規RR-1。 |
| RB-7 | closed | `tools/ruleops.py:583-611`; `docs/ruleops.md:113-120`; `orchestrator/tests/test_ruleops.py:950-1000` | docsと実装がbyte-leading canonical marker grammarで一致する。 |
| RB-8 | closed | `tools/run_tests.py:508-520`; `orchestrator/tests/test_run_tests_preflight.py:302-326` | runner側のledger定数と`--ledger`指定を除去し、CLI defaultへ一本化した。 |
| RB-9 | closed | `tools/ruleops.py:244-257`; `orchestrator/tests/test_ruleops.py:1003-1025` | 空白・制御文字だけのcandidate/review rationaleとqueryを拒否する。 |
| RB-10 | closed | `tools/ruleops.py:1944-1998`; `docs/ruleops.md:126-130`; `orchestrator/tests/test_ruleops.py:1108-1136` | CLI argument failureのrc/reason/envelopeが実装・docs・literal testで一致する。 |

## new findings

### RR-1 — MUST: receiptの`head`がOID形式しか検査されない

- 根拠: `tools/ruleops.py:1556-1561`。`head`は`_validate_oid()`だけで、commit実在、candidate path/blob、現在snapshotとの関係を一切照合しない。対応negative testも`orchestrator/tests/test_ruleops.py:1040-1085`にない。
- 成果物影響: 存在しないOIDや無関係なcommitを「実験head」とするreceiptでも`structurally_valid=true`になり、人間裁定packageへ偽の実験epochを運ぶ。
- 最小fix: receipt headが実在commitで、そのtreeの`candidate_path`が`candidate_blob`を指すことをliteral `ls-tree`で検査する。後続receipt/ledger commitとの差分許容境界も明文化・検査するか、保証できないなら`head` fieldを削除する。

### RR-2 — MUST: custom ledgerを同一pathのHEAD receipt/evidenceとaliasできる

- 根拠: `tools/ruleops.py:1152-1183`は任意repo内regular fileをledgerにできる一方、`tools/ruleops.py:1648-1670`はreceipt pathと`ledger_path`の一致を拒否しない。渡された`ledger_path`は`tools/ruleops.py:1634`、`tools/ruleops.py:1782`で未使用。
- 成果物影響: HEADではstrict receipt、worktreeではcustom ledgerという同一pathを作ると、そのpathをledger入力兼receipt controlとして扱える。commitすればreceiptを上書きして壊れる非永続・循環packageでも、dirty worktree上では構造validになり得る。
- 最小fix: ledger pathをreceipt、guard、node module、sourceの全evidence pathから無条件に排除する。tracked-dirty custom ledger/receipt aliasのnegative testと、別path custom ledgerのpositive controlを追加する。

## positive controls

- productionコードにGit以外の外部実行面やfile write APIはなく、全Git呼出しは`_git_read()`へ集約されている。
- `ls-tree`、`log`、`grep`、pickaxeは捕捉OIDを使用し、後続epoch queryで文字列`HEAD`を使っていない。`HEAD`再参照は開始捕捉とemit前確認に限られる。
- control pathspecはliteralで、current exact blob/eventだけを除外する。旧同一path履歴とglob隣接pathのpositive controlがある。
- duplicate/unknown key、非UTF-8、BOM/CR/NUL、noncanonical marker、candidate cycle、blob drift、AST node不存在はfail closed。
- 成功出力は3 fieldだけで`human_approved:false`固定。docsもmutation receiptを自己申告のadvisory evidenceと明記し、削除安全・実験証明・受理集合同値を主張していない。
- testは非実走であり、greenやmutation killを確認したとは記録しない。

## scope 外の確認

- index/staged-tree bindingは追加されていない。`docs/ruleops.md:148-160`もHEAD snapshot機構として明示している。
- D97 `PYTEST_ADDOPTS` classifierは`tools/run_tests.py:367-373`の既存挙動のままで、RuleOps差分は変更していない。
- preflight refusalは引き続きtask-run取得・記録より前にreturnする。`tools/run_tests.py:784-794`対`tools/run_tests.py:827-830`。暗黙のtask-run記録追加はない。
- mutation producer、実削除、既存insight一括移行、node単位retirementも追加されていない。
- defer境界自体は保持されており、今回のNO-GO理由には使用していない。

## 総括

判定は **NO-GO**。

accepted findingに `partial` がRA-2、RA-8、RA-9、RB-2、RB-5の5件残る。加えて新規MUSTのRR-1、RR-2がある。特に、最大許容ledgerの60秒境界、real-checkout oracleの自己参照、receipt head/custom-ledger aliasが未閉鎖である。

test・checkerは一切実走しておらず、緑とは記録しない。