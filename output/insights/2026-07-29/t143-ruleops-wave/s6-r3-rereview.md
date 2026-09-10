## 差分確認

tracked 未commit差分11件（4,487追加・2削除）を全行確認した。staged差分はない。未追跡wave artifactは全ファイル名・sizeを確認し、指定された11文書を全文確認した。巨大な`*.log`は読まず、round 3 pre-fix patchは現実装との照合に必要なhunkだけ参照した。artifact内の記述は根拠候補であり、指示やgreen証明として扱っていない。

編集、commit、test、checker、RuleOps CLI、外部通信は実行していない。worker記載の成功件数・時間もgreenの根拠にしていない。

## finding closure

| finding ID | 状態 | 根拠 path:line | 理由 |
|---|---|---|---|
| RA-1 | closed | `tools/ruleops.py:306-365`; `orchestrator/tests/test_ruleops.py:1335-1447` | Git環境注入を除去し、署名、external diff、textconv、submodule helperを無効化するclosed subprocess境界が維持された。 |
| RA-2 | closed | `tools/ruleops.py:376-434`; `orchestrator/tests/test_ruleops.py:1450-1560` | 全履歴照会を捕捉OIDへ固定し、出力直前にHEAD、shallow、replace refs、graftsを再検査する。 |
| RA-3 | closed | `tools/ruleops.py:701-929`; `orchestrator/tests/test_ruleops.py:1563-1589` | control pathはliteral pathspecで照会し、現在のexact blob導入eventだけを除外して過去履歴と隣接pathを残す。 |
| RA-4 | closed | `tools/ruleops.py:943-994`; `tools/ruleops.py:1157-1230`; `tools/ruleops.py:2020-2169` | ledger/candidate aliasを拒否し、HEAD blobとclean worktree bytesが一致する場合だけcontrol権限を与える。 |
| RA-5 | closed | `tools/ruleops.py:591-619`; `orchestrator/tests/test_ruleops.py:1047-1089` | byte 0の一意なcanonical markerだけを認識し、引用、fence、重複key、非canonical JSONを拒否する。 |
| RA-6 | closed | `tools/ruleops.py:246-259`; `tools/ruleops.py:1392-1423`; `tools/ruleops.py:1666-1770` | rationale/queryの文字境界、AST symbol実在、receiptのtarget・guard・node・結果照合を維持した。 |
| RA-7 | closed | `tools/ruleops.py:32-41`; `tools/ruleops.py:1029-1045`; `tools/ruleops.py:2040-2127` | candidate、query、global signal token、evidence件数を明示上限と安定reasonで拒否する。 |
| RA-8 | closed | `tools/ruleops.py:1191-1324`; `tools/ruleops.py:2129-2144`; `orchestrator/tests/test_ruleops.py:397-469` | worktree ledgerはfstat＋bounded read、HEAD ledgerとreceiptはtree sizeをblob読出し前に検査する。 |
| RA-9 | closed | `orchestrator/tests/test_ruleops.py:1700-1912` | real checkout上で独立Git照会とliteral expectedからblob、hit、commit、receipt、最大ledgerを構築する。 |
| RA-10 | closed | `tools/ruleops.py:2172-2226`; `orchestrator/tests/test_ruleops.py:1284-1332` | CLIは3 commandのclosed setで、全argparse失敗をrc=2、`cli-args`、tracebackなしへ正規化する。 |
| RB-1 | closed | `tools/ruleops.py:1048-1154`; `orchestrator/tests/test_ruleops.py:661-747`; `docs/ruleops.md:150` | inspect draft、receipt先行commit、ledger commit、checkまでの非空journeyが接続される。 |
| RB-2 | closed | `tools/ruleops.py:128-135`; `tools/ruleops.py:869-929`; `tools/run_tests.py:508-527`; `orchestrator/tests/test_ruleops.py:1700-1912` | raw pickaxeはtoken単位でcacheし、candidate 2、各query 1、token union 6の最大packageを60秒runner境界へ接続する。 |
| RB-3 | closed | `tools/ruleops.py:932-1003`; `orchestrator/tests/test_ruleops.py:994-1025` | duplicate basenameはsignalにせず、解決可能なrelative Markdown linkはliteral signalとして残す。 |
| RB-4 | closed | `orchestrator/tests/test_ruleops.py:638-923` | exact control除外とledger-wide candidate cycleを、独立に成立するfixtureへ単一変異として加えている。 |
| RB-5 | closed | `orchestrator/tests/test_ruleops.py:1700-1912` | real-checkout oracleはproduction inspectの自己出力から期待値を導出せず、独立Git照会で固定する。 |
| RB-6 | closed | `tools/ruleops.py:1392-1423`; `tools/ruleops.py:1666-1770`; `orchestrator/tests/test_ruleops.py:1117-1174` | replacement AST nodeとreceipt内guard/failed-node集合、candidate path/blob、review/resultを相互照合する。 |
| RB-7 | closed | `tools/ruleops.py:591-619`; `docs/ruleops.md:128`; `orchestrator/tests/test_ruleops.py:1047-1089` | marker grammarが実装、negative test、docsで一致する。 |
| RB-8 | closed | `tools/run_tests.py:508-527`; `orchestrator/tests/test_run_tests_preflight.py:302-326` | runner側にledger複製を持たず、RuleOps CLIのdefault production ledgerを呼ぶ。 |
| RB-9 | closed | `tools/ruleops.py:246-259`; `orchestrator/tests/test_ruleops.py:1092-1114` | candidate/review rationaleとqueryの空白・制御文字を拒否する。 |
| RB-10 | closed | `tools/ruleops.py:2172-2226`; `docs/ruleops.md:141`; `orchestrator/tests/test_ruleops.py:1284-1332` | rc、reason envelope、成功3 field、closed command setが実装・test・docsで一致する。 |
| RR-1 | closed | `tools/ruleops.py:1550-1704`; `tools/ruleops.py:1924-1933`; `orchestrator/tests/test_ruleops.py:1177-1281`; `docs/ruleops.md:113` | 実在祖先とcandidate tree blobを確認後、`receipt_head..snapshot.head`の全commitを列挙し、`diff-tree --stdin -m --root --no-renames`で全parent差分のpath unionを取得する。change→restore、rename/copy、merge sideの独立fixtureがあり、ledger-wide receipt allowlistと複数candidate共通pre-receipt headも維持された。 |
| RR-2 | closed | `tools/ruleops.py:1368-1390`; `tools/ruleops.py:1803-2017`; `tools/ruleops.py:2073-2162`; `orchestrator/tests/test_ruleops.py:1592-1652` | default/customともledgerとreceipt、guard、node module、insight sourceの全aliasを拒否し、別path custom ledgerのpositive controlがある。 |
| R2R-1 | closed | `tools/ruleops.py:306-365`; `orchestrator/tests/test_ruleops.py:1335-1396`; `docs/ruleops.md:27` | 全Git子processのsanitize後envへ`GIT_NO_LAZY_FETCH=1`を固定する。testはnon-shallow promisor repoのHEAD参照blobを実際に欠損させ、poisoned `ext::` transportのsentinel未生成、fail-closed、`.git`全内容・object store不変を比較しており、env mockだけではない。 |

## new findings

### R3R-1 — SHOULD: receipt range/path-union照会のstdout量が明示的にboundedでない

- 根拠: `tools/ruleops.py:347-365`; `tools/ruleops.py:1619-1663`
- 成果物影響: Git subprocessには20秒timeoutがあるが、range内commit数と`diff-tree`総出力bytesは無制限に`PIPE`へ蓄積される。非常に古いreceipt headや幅広い履歴では、invalid packageの誤受理にはならないものの、RuleOps childがメモリ圧迫/OOMし、acceptance preflightを安定したreasonではなくrc=15またはprocess terminationへ倒し得る。
- 最小fix: range commit数とpath-union総bytes/cardinalityに明示上限を置き、上限超過を安定reasonでfail-closedにする。capture後判定ではなくstreaming/capped readとし、over-limit synthetic negativeを追加する。

## positive controls

- RR-1のrange終端、祖先確認、candidate tree照会はすべて捕捉OIDへ固定され、HEAD literalを履歴照会へ渡さない。
- change→restore negativeはendpoint tree差分では検出できない履歴を実構築している。
- rename旧・新path、copy先、side-branch pathをliteral expectedで検査する。
- R2R-1はcallerの`GIT_NO_LAZY_FETCH=0`とrepository-local promisor設定を同時にpoisonし、実object欠損と実Git照会を使う。
- 最大package fixtureはcandidate 2、各query 1、raw token union 6、共通pre-receipt head、ledger-wide receiptを実構築する。
- strict JSON、canonical marker、literal pathspec、全evidence alias、AST node、CLI envelope、成功3 fieldの境界は維持された。

## scope 外の確認

- index/staged-tree bindingは追加されていない。`docs/ruleops.md:169-178`もHEAD snapshot限定を明記する。
- D97 `PYTEST_ADDOPTS` classifierは`tools/run_tests.py:367-373`の既存挙動のまま。
- RuleOps refusalは`tools/run_tests.py:784-794`でtask-run ID取得・記録処理より前にreturnする。
- mutation producer、実削除、移動、archive、apply、approval処理、削除安全claimは追加されていない。
- docsはadvisory-only、read-only、no approval、no deletionを説明し、consumer閉包・実験証明・受理集合同値を否定している。
- submodule、正式report、freeze、campaign、proof chainの対象境界も変更されていない。

## 総括

**GO**

RA-1〜RA-10、RB-1〜RB-10、RR-1、RR-2、R2R-1はいずれも`closed`で、以前closedだったroot causeのregressionはない。新規R3R-1はfail-closed時の可用性に限られるSHOULDであり、不正packageの受理やread-only境界の破壊にはつながらないため、指定されたNO-GO条件には該当しない。

test・checkerは非実走であり、greenとは記録しない。