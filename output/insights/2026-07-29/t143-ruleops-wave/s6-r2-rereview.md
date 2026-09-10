## 差分確認

tracked 未commit差分11件（4,357追加・2削除）を全行確認した。staged差分はない。未追跡wave artifactは全ファイル名・sizeを確認し、指定された構造化文書を全文確認した。巨大な`*.log`と、現実装との照合に不要なpre-fix patch本文は読んでいない。

実装2,206行、RuleOps test 1,810行、runner・docs・checker差分を静的確認した。編集、commit、CLI、pytest、checker、外部通信は実行していない。worker記載の成功件数・時間はgreenの根拠にしていない。

## finding closure

| finding ID | 状態 | 根拠 path:line | root cause が閉じた、または残る理由 |
|---|---|---|---|
| RA-1 | closed | `tools/ruleops.py:306-364`; `orchestrator/tests/test_ruleops.py:1286-1345` | accepted対象だった署名、external diff、textconv、submodule再帰、Git環境注入は無効化され、poison helper testもある。promisor lazy-fetchという別のread-only bypassはR2R-1。 |
| RA-2 | closed | `tools/ruleops.py:375-433`; `orchestrator/tests/test_ruleops.py:1375-1458`; `docs/ruleops.md:27-32` | 全epoch照会は捕捉OIDへ固定され、emit直前にHEAD、non-shallow、replace refs、graftsを再検査する。HEAD不変の3境界negativeも揃う。 |
| RA-3 | closed | `tools/ruleops.py:834-929`; `orchestrator/tests/test_ruleops.py:1461-1487` | control照会はliteral pathspecで、現在のexact blob導入eventだけを除外し、glob隣接pathと旧non-control履歴を残す。 |
| RA-4 | closed | `tools/ruleops.py:1156-1187`; `tools/ruleops.py:2049-2120`; `orchestrator/tests/test_ruleops.py:1490-1497` | ledger/candidate aliasを無条件拒否し、HEAD strict blobとworktree bytesが一致する場合だけcontrol権限を与える。 |
| RA-5 | closed | `tools/ruleops.py:590-618`; `orchestrator/tests/test_ruleops.py:1047-1089` | byte 0のcanonical typed markerだけを認識し、引用、fence、先頭ゴミ、重複key、非canonical JSONを拒否する。 |
| RA-6 | closed | `tools/ruleops.py:246-259`; `tools/ruleops.py:1392-1423`; `tools/ruleops.py:1642-1746` | rationale/queryはstrip後nonempty・control-free。AST symbol実在とreceiptのtarget、guard、node、結果を相互照合する。 |
| RA-7 | closed | `tools/ruleops.py:1029-1044`; `tools/ruleops.py:1241-1295`; `orchestrator/tests/test_ruleops.py:472-508` | candidate、query、signal件数に明示上限と安定reasonがあり、inspect/check双方でoverflowを拒否する。 |
| RA-8 | closed | `tools/ruleops.py:942-965`; `tools/ruleops.py:1190-1222`; `tools/ruleops.py:1306-1323`; `tools/ruleops.py:2105-2119`; `orchestrator/tests/test_ruleops.py:412-469` | default/custom ledgerともworktreeはfstat＋bounded read、捕捉HEAD ledgerはentry sizeをblob取得前に検査する。receiptもtree sizeを先に検査する。 |
| RA-9 | closed | `orchestrator/tests/test_ruleops.py:1599-1805` | real-checkoutはcontrolled commitと独立Git/literal値からblob、hit、pickaxe commit、receipt、ledgerを構築する。production `inspect`は独立oracleとの比較だけに使う。 |
| RA-10 | closed | `tools/ruleops.py:2148-2202`; `orchestrator/tests/test_ruleops.py:1255-1283` | CLIは3 commandのclosed setで、全argparse失敗をrc=2、`cli-args`、tracebackなしへ正規化する。 |
| RB-1 | closed | `tools/ruleops.py:1047-1138`; `orchestrator/tests/test_ruleops.py:661-747`; `docs/ruleops.md:146-160` | inspect draft、receipt先行commit、ledger commit、checkまでの非空journeyが実装・独立test・docsで接続される。 |
| RB-2 | closed | `tools/ruleops.py:128-135`; `tools/ruleops.py:868-929`; `tools/ruleops.py:1996-2103`; `orchestrator/tests/test_ruleops.py:511-557`; `orchestrator/tests/test_ruleops.py:1599-1810`; `tools/run_tests.py:508-527` | raw pickaxeはsnapshot/token単位で一度だけ取得し、candidate別control filteringは後段。candidate 2、各query 1、token union 6を履歴前に制限し、最大packageを60秒timeout付きrunner childへ通すtestである。非実走なので時間は追認しない。 |
| RB-3 | closed | `tools/ruleops.py:932-1002`; `orchestrator/tests/test_ruleops.py:994-1009` | duplicate basenameとliteral consumerを実構築し、曖昧basenameをsignal化しない外延を固定する。 |
| RB-4 | closed | `orchestrator/tests/test_ruleops.py:638-659`; `orchestrator/tests/test_ruleops.py:764-923` | M5はexact current controlと旧履歴を分離し、M6は独立validな二候補へcross-candidate参照だけを加えるfixtureになっている。 |
| RB-5 | closed | `orchestrator/tests/test_ruleops.py:1599-1805` | inventory非空、controlled blob/hit/history、receipt、最大非空ledger、runner接続を独立oracleから構築し、inspect/checkの自己参照を排除した。 |
| RB-6 | closed | `tools/ruleops.py:1392-1423`; `tools/ruleops.py:1642-1746`; `orchestrator/tests/test_ruleops.py:1117-1174` | replacement AST nodeの実在とreceipt内guard/failed-node集合、candidate path/blob、review/resultを相互照合する。 |
| RB-7 | closed | `tools/ruleops.py:590-618`; `docs/ruleops.md:124-131`; `orchestrator/tests/test_ruleops.py:1047-1089` | marker grammarが実装、negative test、docsで一致する。 |
| RB-8 | closed | `tools/run_tests.py:508-520`; `orchestrator/tests/test_run_tests_preflight.py:302-326` | runner側のledger literalを除去し、RuleOps CLIのdefault ledgerを単一正本として呼ぶ。 |
| RB-9 | closed | `tools/ruleops.py:246-259`; `orchestrator/tests/test_ruleops.py:1101-1114` | candidate/review rationaleとqueryの空白・制御文字を拒否する。 |
| RB-10 | closed | `tools/ruleops.py:2148-2202`; `docs/ruleops.md:137-141`; `orchestrator/tests/test_ruleops.py:1255-1283` | 引数失敗のrc、reason envelope、closed command setが実装・test・docsで一致する。 |
| RR-1 | partial | `tools/ruleops.py:1614-1639`; `orchestrator/tests/test_ruleops.py:1177-1232`; `docs/ruleops.md:111-113`; `docs/ruleops.md:148-155` | **MUST**。実在祖先commitとcandidate blobは検査するが、変更pathは`diff-tree receipt_head snapshot.head`による両端treeの差分だけである。途中で無関係pathを変更して元へ戻すと検出されない。放置時はdocsが禁止するreceipt後の無関係変更を含むpackageが`structurally_valid`になり、実験epochを偽装できる。最小fixはcommit range内の各commitが触れたpathのunionを検査し、「無関係path変更→revert」の独立negativeを追加すること。 |
| RR-2 | closed | `tools/ruleops.py:1368-1389`; `tools/ruleops.py:1801-1880`; `tools/ruleops.py:1958-1967`; `orchestrator/tests/test_ruleops.py:1500-1550`; `docs/ruleops.md:88-90` | default/customともledgerとreceipt、guard、node module、insight sourceのaliasを無条件拒否し、別path custom ledgerのpositive controlがある。 |

## new findings

### R2R-1 — BLOCKER: promisor remoteのlazy fetchがread-only境界を迂回する

- 根拠: `tools/ruleops.py:306-317`は全`GIT_*`環境を除去する一方、lazy fetchを止める`GIT_NO_LAZY_FETCH`を設定しない。`tools/ruleops.py:320-364`、`tools/ruleops.py:459-489`はblob/object照会を実行する。既存negativeは`orchestrator/tests/test_ruleops.py:1286-1345`の署名・diff・textconv・submodule helperだけで、promisor remoteを覆わない。
- 成果物影響: non-shallowなpartial cloneは現在の境界を通る。promised objectが欠けている場合、`cat-file`、`grep`等がrepository-local promisor remoteへlazy fetchし、外部通信と`.git/objects`への書込みを起こし得る。P1のread-only preflightが成立しない。
- 最小fix: Git子環境へ`GIT_NO_LAZY_FETCH=1`を固定し、missing promised blobとpoisoned local promisor helperを持つsynthetic repoで、helper未起動・Git metadata不変・fail-closedを検査する。

## positive controls

- HEAD OID固定とemit直前のHEAD／履歴境界再検査は全3入口で共通化されている。
- raw pickaxe cacheはtokenだけをkeyにし、control集合をcache keyへ含めない。
- 最大package testはcandidate 2件、各query 1件、literal token union 6件を実構築し、runnerの`timeout=60`境界を通す。
- receiptのnonexistent、non-ancestor、candidate blob mismatch、unrelated path negativeがある。複数candidateが同じpre-receipt headを共有するpositiveもreal-checkout testにある。
- strict JSON、canonical marker、literal pathspec、exact control event、AST node、ledger-wide candidate cycle、全queryの捕捉OID固定は維持されている。
- 成功出力は3 fieldのみで`human_approved:false`固定。docsもadvisory-only、削除安全・承認・完全consumer閉包を否定している。

## scope 外の確認

- index/staged-tree bindingは追加されていない。`docs/ruleops.md:162-174`もHEAD snapshot限定を維持する。
- D97 `PYTEST_ADDOPTS` classifierは`tools/run_tests.py:367-373`の既存挙動のまま。
- preflight refusalは`tools/run_tests.py:784-794`でtask-run取得前にreturnし、記録追加はない。
- mutation producer、実削除、archive、apply、approval、safety claimは追加されていない。
- submodule、正式report、freeze、campaign、proof chainの対象境界も変更していない。

## 総括

判定は **NO-GO**。

第2裁定accepted findingのRR-1が`partial`であり、さらに新規BLOCKERのR2R-1がある。RR-1は途中変更後のrevertでepoch path制約を迂回でき、R2R-1はpartial cloneで外部通信・Git metadata書込みを起こし得る。

test・checkerは非実走であり、greenとは記録しない。