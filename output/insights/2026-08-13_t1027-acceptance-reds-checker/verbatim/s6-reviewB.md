## 裁定 R1〜R9 との照合

| 裁定 | 評価 | 根拠と成果物影響 |
|---|---|---|
| R1 | [M] literal 4200 と適用範囲は実装済みだが、dispatch を最終 deadline の権威にできていない。`tools/check_acceptance_reds.py:621-650,899-968`、`tools/pegasus/dispatch_compute.py:29-31,1587-1651`。queue 最大 900 秒の後に deadline が `RUN 観測 + 3600 + 300` へ再設定され、さらに accounting 60 秒があるため、最悪約 4860 秒を外側 4200 秒が先に kill する。影響: 長い queue と長い子では checker receipt が作られず rc=2 となり、certified 受理集合が不必要に空になる。 |
| R2 | [N] 実装は裁定どおり。`tools/check_acceptance_reds.py:177-407`。非 relay の一意な保存行、location、v2 schema、request args、child outcome、accounting、stdout 完全性を検査している。影響: この層を外すと部分 collection から `non-attributable-only` が生成され、受理集合が広がる。 |
| R3 | [N] 実装済み。`tools/check_acceptance_reds.py:830-872`。singular、plural、deselected 算術、0 件、重複、件数一致を検査する。影響: 件数 gate を外すと欠落 nodeid を含む collection が rc=0 へ進める。 |
| R4 | [B] author 報告と実装が食い違う。`tools/check_acceptance_reds.py:359-407,1199-1225` は検証済み nonce と fallback receipt しか消さず、`__pycache__` と空の `output/pegasus-dispatch/` を残す。`tools/check_acceptance_reds.py:742-769` の絶対指紋 gate が実測どおり発火する。影響: 赤がある実 log は常に rc=2、checker receipt、report、台帳反映がゼロになる。 |
| R5 | [N] production runner では実装済み。`tools/check_acceptance_reds.py:875-938`。rc=1 に加え、同 selector の FAILED/ERROR と完全 terminal summary を要求する。影響: この照合を外すと session-level rc=1 を非帰属と誤認し、rc=0 の受理集合が広がる。 |
| R6 | [B] 部分実装に留まる。`tools/check_acceptance_reds.py:653-660` は三つの `PYTEST_*` だけを正規化するが、producer は `IZANAGI_RUN_GROWTH_HELD_TESTS` と `IZANAGI_T080_E2E` も伝播する。前者は実際に skip/実行を変える。`tools/pegasus/dispatch_compute.py:56-68`、`orchestrator/tests/conftest.py:387-410`。影響: acceptance と checker の環境差で rerun rc が変わり、`nodes[].classification`、status、rc=0 の受理集合が変わる。 |
| R7 | [N] 実装済み。`orchestrator/tests/test_check_acceptance_reds.py:1332-1354` は private helper 直呼びでなく、default collection runner から production parser を発火させる。影響: footer gate を除去すると同 node は rc=2 から rc=0 へ反転する。 |
| R8 | [N] 実装済み。`tools/check_acceptance_reds.py:343-348,386-397`。receipt tail と local stdout の U+FFFD を拒否する。影響: 除去すると壊れた nodeid bytes から status と nodes が確定しうる。 |
| R9 | [N] 指定 field は記録済み。`tools/check_acceptance_reds.py:1432-1455`。ただし `receipt_path` は R4 cleanup 後には存在しないため、実質的な監査鍵は nonce、request ID、stdout hash である。影響: status は変わらないが、元 receipt を path から再読する監査はできない。 |

したがって、author.md の「R1〜R9 をすべて実装」「判定不能経路は閉じた」という総括は、R4 と R6について成立しない。R1の「git 等は120秒」は正しく、4200秒が一律適用された事実はない。4200秒の対象も collection と rerun の二経路へ入っており、短い git command は120秒のままである。

## 残 blocker への評価

[B] 親案を「既知の path を再帰的に消す」と実装するのは、正しさ防壁を弱める。`orchestrator/tests/test_check_acceptance_reds.py:748-767` は、rerun node が作った ignored `__pycache__/marker.pyc` も必ず拒否する既存契約である。checker の子が作ったという事実だけでは、Python runtime の残骸とテスト自身の副作用を区別できない。影響: テストが ignored path に副作用を残しても fingerprint が空になり、従来 rc=2 だった走行が rc=0または1へ入り、受理集合が広がる。

安全な直し方は次である。

- Python cacheは「後から消す」のではなく、compute childへ `PYTHONDONTWRITEBYTECODE=1` を伝播し、receiptにも環境を束縛する。現在は checker側で設定しても producer allowlistに無いためPBS childへ届かない。`tools/check_acceptance_reds.py:653-660`、`tools/pegasus/dispatch_compute.py:56-68,1339-1384`。
- dispatch成果物は、既に検証した nonceとfallbackを消した後、exact `output/pegasus-dispatch` に対して `rmdir` のみ行う。空でなければ削除せずrc=2にする。再帰削除、glob、root内の任意ファイル削除はしない。
- cleanup後も現在の絶対 fingerprintをそのまま使う。`git status` から `!!` 行を除外する方式でも tracked改変自体は残せるが、ignored副作用を見逃して既存契約を弱める。pathspecでdirectory全体を除外すればtracked改変まで見逃しうる。

この修正には裁定 §4 の producer scopeを開き直す必要がある。新しい実測により、producer変更なしでは「指紋を維持した安全な修正」が成立しないためである。

## 次に止まる場所

[N] 上記の安全な残骸対策まで入れば、`acceptance3.log` の一件について、checker内に次の決定的な停止点は静的には見つからない。collectionは既に selector 解決後の `tools/check_acceptance_reds.py:1224-1225` まで到達している。次の rerunがpassなら attributable、同じFAILEDを再現すればR5を通ってnon-attributableとなり、どちらも `tools/check_acceptance_reds.py:1414-1456` のreceipt生成まで進める。

[M] ただし条件付きの次候補は外側4200秒とqueueの一発失敗である。`tools/run_tests.py:1825-1831` は `--force-dispatch` を一度呼ぶだけでretryせず、checkerはcollection rc非0またはrerun rcが0/1以外なら `tools/check_acceptance_reds.py:974-977,1231-1235` でrc=2となる。影響: schedulerの一過性失敗や4200秒超過で、receiptと台帳候補が作られない。

[B] 実運用全体で数える「6つ目」は production consumer不在である。standalone checkerが完走しても、`tools/dev_wave_wait.py:943-973` は渡されたacceptance commandのrcしか扱わず、`tools/dev_wave_land.py:1535-1577` はprovenance receiptを検証するだけでchecker receiptを消費しない。影響: certified選択、受入report、台帳の受理集合は一切変化せず、実運用到達とは呼べない。

## scope 外3件の評価

- [B] consumer不在は別waveへ分けること自体は可能だが、「実運用到達」の完了条件から外してはならない。`tools/dev_wave_wait.py:943-973; tools/dev_wave_land.py:1535-1577`。影響: standalone receiptが生成されてもcertified選択、report、台帳へ反映されない。
- [M] 2n dispatchは一件の実データ通過には必須修正でないが、一般運用前には解消が必要。`tools/check_acceptance_reds.py:1174-1230`。影響:赤n件のreportと台帳確定が約2n dispatch分遅れ、queue timeoutの機会も2n倍になる。
- [B] producer容量と環境束縛は、今回の安全な残骸修正に直接必要となったため、もはや完全なscope外には置けない。`tools/pegasus/dispatch_compute.py:33-35,56-68,1339-1384`。影響:容量超過はrc=2で成果物を失い、環境未束縛はnodes分類とrc=0受理集合を変えうる。

## 変異 M0〜M8

| 変異 | 静的評価 | 期待 node と成果物影響 |
|---|---|---|
| M0 | [N] 実行可能。前段maskなし。 | `test_truncated_relay_uses_complete_dispatch_receipt` がfooter count mismatchで赤になる。影響:完全receiptで通るべき入力がrc=2へ縮む。 |
| M1 | [N] 実行可能。目的selectorはfixture内にあるため後段へ進む。 | `test_collection_footer_count_mismatch_fails_closed_before_rerun` がrc=2期待からrc=0へ反転して赤。影響:部分collectionが受理集合へ入る。 |
| M2a | [N] 実行可能。sizeは正しく、omittedだけが不正。 | `test_dispatch_receipt_with_omitted_scheduler_stdout_fails_closed` が赤。影響:打ち切られたtailからnodesとstatusが作られる。 |
| M2b | [N] 実行可能。omitted=0なのでM2aに先取りされない。 | `test_dispatch_receipt_size_mismatch_fails_closed` が赤。影響:byte不一致tailが権威化される。 |
| M3 | [N] 実行可能。locationと残りschemaは有効。 | `test_dispatch_collection_receipt_requires_bound_request_args` がrc=2からrc=0へ進んで赤。影響:別走行のcollectionで受理集合が決まる。 |
| M4 | [M] 登録どおりの単一変異では実行不能。`tools/check_acceptance_reds.py:204-249` にroot一致、`relative_to`、canonical path、shapeの複数gateがあり、一条件を恒偽化しても他層が先取りする。 | `test_dispatch_receipt_outside_probe_root_fails_closed_before_rerun` は変異後もrc=2のままで生存する。影響:location gateの検出力を証明できず、外部receipt受理集合への防壁が未検証となる。 |
| M5 | [N] 実行可能なpositive control。 | `test_single_test_collection_footer_is_accepted` がrc=0からrc=2となり赤。影響:正当な一件collectionの受理集合縮小を検出する。 |
| M6 | [N] 実行可能。fixtureはrc=1を維持し、出力nodeidだけを違わせる。 | `test_rerun_rc_one_without_matching_outcome_fails_closed` がrc=2からrc=0へ進み赤。影響:session errorを非帰属として受理する。 |
| M7 | [N] literal pinとして実行可能。git timeoutは別値のまま。 | `test_dispatch_commands_use_dispatch_aware_timeout` が `[120,120]` を観測して赤。影響:実環境では長いdispatchがreceipt前にrc=2となる。 |
| M8 | [N] 登録されたPYTEST_ADDOPTS変異は実行可能。 | `test_collection_environment_neutralizes_pytest_addopts` が継承値を観測して赤。影響:deselectされたcollectionからstatusとnodesが変わる。ただしR6全体の環境面は網羅しない。 |

## 総括

R4は実装報告に反して実データで発火せず、R6も選択環境を閉じ切っていない。  
親の再帰cleanup案は既存のignored副作用検出を弱めるため、producer側で残骸を生成させない修正が必要である。  
安全な修正後、対象logに対するchecker内部の決定的な第6 blockerは静的には見つからない。  
実運用上の第6 blockerはconsumer不在であり、producer修正とともにscope再裁定が必要である。  
M0〜M8ではM4だけが多重location gateにmaskされ、登録どおりの単一変異になっていない。