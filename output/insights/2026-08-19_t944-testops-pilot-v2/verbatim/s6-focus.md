```text
統合後焦点再レビュー。必読7文書と `git diff main`、未追跡の中心実装・テストを静的確認した。親提供の403 passed×2は補助証拠として扱い、緑だけではclosedにしていない。

判定の意味: closed=裁定・実装・検査範囲が一致、partial=一部修正だが契約または経路が未閉鎖、not-attempted=必要な実証・記録なし、regressed=修正前より悪化。

【Review-A blocker】
| ID | 判定 | 対応 |
|---|---|---|
| A-BLK1 | closed | `RootReport.published_run_count` は published+incomplete+damaged。ledger/generationの開始拒否も10件到達を確認する。aggregate表示の欠陥はB-BLK2で残る。 |
| A-BLK2 | closed | repo/base/generationのFD identityをgit確認前後で検証する実装になった。 |
| A-BLK3 | partial | orphan lease回収・remove identityは改善したが、run_testsのsignal、Popen/subprocess例外時にfinish/cleanupがfinallyで保証されない。 |
| A-BLK4 | partial | selfcheckを含むmanaged guardとrepo rename対策は入ったが、guard判定後のpath差替えをfdで保持・再検証していない。 |

【Review-B blocker】
| ID | 判定 | 対応 |
|---|---|---|
| B-BLK1 | partial | cap分母は直ったが、damaged/unknownをautomaticが無診断で継続し、R-CLOSEORDERの固定series-invalid優先順位を満たさない。 |
| B-BLK2 | partial | automatic/CLIの`validate_series`結線とempty=`None`は入ったが、`aggregate.py`は個別rootだけを読む。report headerもseries healthを主張範囲に明記せず、incompleteをcap表示に数えない。 |
| B-BLK3 | partial | qsub前失敗の「診断のみ」は直ったが、qsub後に実child markerが無いinfra経路を`child_started=True`扱いし得る。親はそのreceiptを厳密に検証せずtask/eventを作る。 |
| B-BLK4 | closed | CLI guardにselfcheckが追加され、managed generationへのwrite経路を拒否する。残るraceはA-BLK4。 |
| B-BLK5 | closed | automatic開始前にgeneration selfcheckを一度実行し、status markerと固定diagnosticを使う。 |

【Review-A must-fix】
| ID | 判定 | 対応 |
|---|---|---|
| A-M1 | partial | damaged/unknownを許可する`_root_diagnostics_are_nonblocking`が残り、固定`recording-unavailable:series-invalid`を返さない。 |
| A-M2 | closed | final marker、report実体、SHA-256をroot lock/FD経由で検証する。 |
| A-M3 | partial | signalは伝播するが、direct/dispatchのsession.finishとsidecar cleanupをsignal・child例外時にも保証しない。 |
| A-M4 | partial | bounded scopeのPopen前startは改善したが、directはsubprocess.call前、dispatchは実child確認前にensure_startedする。 |
| A-M5 | partial |通常のdiagnosticは固定化されたが、admission/queue/Popen/wait例外で`type(exc)`や本文をstderrへ出す経路が残る。 |
| A-M6 | partial | generation側removeはidentity検証済みだが、`pytest_stats.read_sidecar`はlstat後にpath再解決して読む。 |
| A-M7 | closed | CLIの`max_task_runs`等を固定hyphen形式へ射影する。 |
| A-M8 | not-attempted | real dispatchは環境変数未設定でskip可能で、Unit Aの実generation lifecycleもmockされている。 |

【Review-B must-fix】
| ID | 判定 | 対応 |
|---|---|---|
| B-M1 | partial | truth tableは実装自己比較からliteral期待値へ改善したが、direct/dispatch/scopeの実経路を十分に通らない。 |
| B-M2 | partial | 手作業stagingのrecovery検査はあるが、mkdir/init/fsync/rename各境界のkill・fault injectionがない。 |
| B-M3 | not-attempted | real dispatchのskip可能性とUnit A lifecycle mockが残る。A-M8と重複するが両所見とも未閉鎖。 |
| B-M4 | closed | provenanceのallowlistを空にし、job script/childでsidecar・auto markerを除去する。 |
| B-M5 | closed | direct/dispatch/boundedの生成bytesをsentinel横断検査するテストが追加された。raw exception経路はA-M5として別に残る。 |
| B-M6 | partial | READMEのmanual check wrapper区別は修正済みだが、testは文言中心で、実child限定eventの実装欠陥も残る。 |
| B-M7 | not-attempted | production差分の再見積り、要求別行数、未追跡new fileを含むstage6記録がない。 |

【nit】
| ID | 判定 | 対応 |
|---|---|---|
| A-N1 | partial | 親提供の同一5ファイル403 passed×2は確認できるが、flock待ち時間・負荷下再現率の証拠はない。 |
| A-N2 | not-attempted | 不正tupleを`(True,None)`へfail-openする処理が残る。 |
| B-N1 | partial | automatic triggerはunspecified固定だが、unset/invalid/finalのparametrizeが不足。 |
| B-N2 | not-attempted | 外部固定nodeid selectorの確認・記録がない。 |
| B-N3 | not-attempted | generation.py等の中心ファイルがgit statusでuntrackedのまま。 |

集計: blockerはclosed 4 / partial 5 / regressed 0。must-fixはclosed 4 / partial 8 / not-attempted 3 / regressed 0。nitはpartial 2 / not-attempted 3。

重点確認:
1. cap計算そのものは published+incomplete+damaged に直り、11件目拒否の方向は正しい。ただしR-CLOSEORDERのdiagnostic優先順位とaggregateのcap表示が未接続である。
2. series readerはautomatic/CLI入口まで改善したが、s4-ruling R-SERIESREADERが要求する既存aggregate/report consumerへの結線がない。空seriesを個別reportが健全と見せ得る。
3. selfcheckはautomatic開始前に接続され、ここはclosed。ただしmanaged guardのcheck/use raceは別問題として残る。
4. dispatchは「qsub前にchild無し」は扱えるが、qsub後にpytest childを実際に起動した証拠がないinfra returnを成功扱いし得る。R-B4SCOPEとR-COVERAGEに反する。

Unit Aが編集権限外と報告した`aggregate.py`および`pytest_stats.py`のpartialは許容しない。s4-rulingの受入契約がUnit境界より上位であり、追加fixの担当再割当または明示的な再裁定が必要である。したがって残るblockerはA-BLK3/A-BLK4/B-BLK1/B-BLK2/B-BLK3、残るmust-fixはA-M1/A-M3/A-M4/A-M5/A-M6/A-M8/B-M1/B-M2/B-M3/B-M6/B-M7である。別個のregressedは0だが、未閉鎖の統合欠陥は存在する。本レビューではpytestを実行していない。
```

## 総括
NO-GO。残る blocker 5件、must-fix 11件（重複込み）、regressed 0。pytestは本レビュー未実施（親提供の2回は403 passed, 1 skipped）。