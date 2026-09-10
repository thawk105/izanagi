<!-- parent-owned dev-wave artifact; 2026-07-30 JST -->

# T-126 FR3 closure — focused review 1 裁定

reviewはexit 0 / validator green / NO-GO。計算ノード受入はjob `874318.nqsv`で
`346 passed, 9 skipped`、static全green、source-before-after一致だったが、
静的root causeを閉じない5件を検出した。5件とも成果物影響がありreal / scope内と裁定する。

| ID | 裁定 | fix 2の最小条件 | 放置時の成果物影響 |
|---|---|---|---|
| FR1-1 / S6-C3 | real / BLOCKER | shared `create_bytes()`を全entry preflight→一括applyへ統一し、multiple/suffix/uid/mode/nlink/symlink/nonregular/external hardlinkでは一件もunlinkしない。`create_or_verify_bytes()`はnamespace safety errorを同一target bytesで吸収しない | receipt、attempt ledger、snapshot、rejected-evidenceのattack/crash stagingを消したclean closureを作れる |
| FR1-2 / S6-C5 | real / HIGH | early resultのstructuralだけでなくWmax/timing/script identity等semantic分類をadoption mutation前に行い、semantic-invalid bytesをcanonical名へ移さずrejected-evidenceへ元path/lstat/hash付きで保存する | semantic-invalid bytesがcanonical名になり、元early path/dev/ino/nlink provenanceが消える |
| FR1-3 / S6-A5 | real / HIGH | invocationとattempt-ledgerの全consumerで`type(retry_index) is int and retry_index in (0,1)`を共通validatorとして必須化する。intent/submitted/outcome payloadとshell consumerも同義にする | JSON false/trueが0/1としてinvocation snapshot・submitted/outcome ledger・public receipt検証を通る |
| FR1-4 / S6-A6-C6b | real / HIGH | M8dを実job prologueと全consumerへ通す。M11bはpersistent import mutantだけがsentinelへ到達する実fixtureにする。registryはsource path、exact anchor bytes、replacement、exact nodeを固定し、mutation harnessが同じtransformを使える形にする | M1〜M11 mutation ledgerがFR3 consumer同義性とpublisher isolationを検出した証拠にならない |
| FR1-5 / correction-3 | real / HIGH | pytest parentは変えず、outer childでTERM/HUPを明示`SIG_IGN`、inner reset launcherでinitial IGN→final DFLを記録してexact Bashへexecする。reset削除mutantが同じ5 nodeで赤になる | signal-chain acceptanceが環境依存でreset未実行を見逃す |

修正は`artifacts.py`、`collector.py`、invocation/ledger consumers、production shell、
T-126 tests/registryを横断するため、相互依存する単一Codex実装単位へ寄せる。親は実装を編集しない。
同一UID全成果物再作成、power-loss、system interpreter/LD_PRELOAD、同一UID path raceは
既裁定どおりscope外のままとする。
