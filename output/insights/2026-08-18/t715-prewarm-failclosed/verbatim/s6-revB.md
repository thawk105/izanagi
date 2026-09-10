## 所見

1. [Critical] memo singleton が pytest session 境界を越え、nested / 反復 `pytest.main()` を壊す

`_RECEIPT_MEMO` は module global (`real_repo_receipt_memo.py:397`) だが、`pytest_configure` (`conftest.py:727-732`) と `pytest_sessionfinish` のどちらでも初期化されない。さらに `prewarm()` は run ID の確認より先に `process_prewarmed` なら即 return する (`real_repo_receipt_memo.py:277-280`)。

- 2 回目の serial `pytest.main()` は新 snapshot を作らず、前 session の `R(X)` を再利用する。
- 2 回目の xdist `pytest.main()` は新 UID を設定しても controller が旧 process value を返し、新 UID の pickle を作らない。その後 worker は `cache-missing` (`real_repo_receipt_memo.py:371-385`) で赤になる。
- `conftest.py:388-390` は prewarm 成功として新 config に印を付けるため、この欠落を検出しない。

成果物影響: 同一 process の再入時に certified 判定が前 session の working-tree snapshot を参照するか、consumer 全体が偽赤になり、選択結果と証跡が session に閉じない。

2. [Major] `/tmp`、flock、同一 UID が通常走行を簡単に偽赤へ倒す

xdist cache key は `tempfile.gettempdir()`、UID hash、HEAD だけである (`real_repo_receipt_memo.py:101-108`)。

- controller と worker の `/tmp` が異なると、controller の prewarm は成功するが worker は別 path を読み、次の message で test node が赤になる。

  `IZANAGI_RECEIPT_MEMO_FAIL_CLOSED_V1 {"cache_path":"<worker tmp>/izanagi-t057-receipt-<hash>-<head>.pickle","head":"<head>","prewarm":false,"process_prewarmed":false,"reason":"cache-missing","run_id":"<uid>"}`

- flock 非対応時は `lock-open-failed` または `lock-acquire-failed` (`real_repo_receipt_memo.py:227-244`)。controller なら collection internal error、worker なら consumer node の test error になる。
- 同じ明示 UIDと同じ HEADの並行 session は同じ keyになる。一方が保存すると他方は lock 待ち後に `cache-preexists-before-prewarm` (`real_repo_receipt_memo.py:314-318`) で必ず赤になる。別 worktreeや別 cloneも root pathを keyに含まない。
- 任意文字列 UID 自体は SHA-256 化され (`real_repo_receipt_memo.py:101-108`)、`ci-job-42`、空文字、空白、slash は拒否されない。この must-fix は成立している。
- stale prune は `*.pickle` のみを対象にし current path を除外する (`real_repo_receipt_memo.py:171-187`)。lock unlink 問題は閉じている。

現行 Pegasus dispatch は controller と worker が同一計算ノードにいるため `/tmp` 分離を通常は踏まないが、コード上の事前条件として検査されていない。

成果物影響: 正しい test inputでも環境構成や session UID の再利用だけで全 consumer が赤になり、certified 成果物を生成できない。

3. [Major] `tools/run_tests.py -p no:xdist` は prewarm に到達しない

素の `pytest -p no:xdist` は `getoption(..., None)` の guard (`conftest.py:719-724`) により serial prewarmへ入れる。

一方 `tools/run_tests.py -p no:xdist` は、xdist が利用可能なら先に `-n N --dist loadgroup` を追加し (`tools/run_tests.py:380-399`)、後段の `-p no:xdist` で plugin を無効化する。そのため `-n` / `--dist` が未定義となり pytest usage error で停止する。`-p` は acceptance shapeからも除外される (`tools/run_tests.py:519-535`)。

成果物影響: runner経由の非xdist経路は testを1本も実行せず、serial fail-closed契約の受入証跡を作れない。

4. [Critical] infrastructure 赤と test 赤の区別は message 内にしかなく、結果型では閉じていない

cache/lock由来の例外には prefix と JSON がある (`real_repo_receipt_memo.py:51-82`)。しかし結果レベルでは次のように分裂する。

- controller prewarm例外は collection hookから伝播し、pytest internal error rc 3になる。
- workerの `cache-missing` は通常の failed test node、rc 1になる。
- mutation harnessは rc 0/1以外を `PARSE_ERROR` とし (`tools/mutation_harness.py:1904-1920`)、rc 1と失敗nodeがあれば通常の mutation kill候補として扱う。
- 未初期化 submoduleはさらに悪い。production resolverが全例外を `ReceiptResolution(state="invalid")` に変換する (`s8b_oracle_driver.py:116-133`) ため、raw pytestやtargeted runnerでは memo prefixが出ない。期待された product refusalとして通るnodeと、通常 assertionで赤になるnodeに分かれる。
- full acceptanceだけは runner preflightが rc 14と「submodule marker ...」を返す (`tools/run_tests.py:699-725`)。

従って「prefixを目視すればcache infraと分かる」は成立するが、runner、JUnit、mutation ledgerで構造的に分類できるとは言えない。

成果物影響: `/tmp` 障害を変異killやtest回帰と誤認し、逆に未初期化submoduleを正当なproduct refusalとして偽緑にできる。

5. [Major] 「consumerを含まない焦点走では memo moduleをimportしない」は広い意味では偽

conftest側のimportは遅延化されている (`conftest.py:361-365`)。別test fileだけの焦点走なら memo importもprewarmもない。

しかし2 consumer fileはmodule scopeでcanonical memoをimportする。

- `test_s8b_oracle_driver.py:34`
- `test_s8b_binding_driftguards.py:44`

したがって、例えば `test_s8b_oracle_driver.py` 内のmemo非consumer nodeを1本だけ選んでも、collectionでmemo、driver、migrationをimportする。`--collect-only`も同じである。新設検査はresolver回数0だけを確認し (`test_real_repo_serialization.py:1829-1861`)、module import 0は確認していない。

prewarm自体の実解決回数は次のとおり。

- 通常consumer nodeの焦点走: 1回、約19.70秒。
- `test_s8b_binding_driftguards.py` 全体: 1回。
- `test_s8b_oracle_driver.py` 全体: prewarm 1回に加え、scope外CLI child (`test_s8b_oracle_driver.py:3729-3755`) がproduction resolverを1回呼ぶため計2回、約39.40秒相当。
- 全走: 同じく実repo解決は計2回。prewarm 1回とCLI child 1回。
- 別のconsumer非含有file: 0回かつmemo importなし。
- 同じconsumer file内の非consumer nodeだけ: 0回だがmemo importあり。
- `--collect-only`: 0回だが、consumer fileをcollectすればmemo importあり。

prewarm 19.70秒は collection barrier (`conftest.py:577-588`) でtest scheduling前へ直列に乗る。静的上界は既裁定どおり192.80秒、1.114倍であり、合格はpaired実測でしか示せない。

成果物影響: 「consumerなし焦点走」の定義をfile単位とnode単位で取り違えると、1.1倍判定のimport overheadを過少申告する。

6. [Critical] M9は事前登録どおりの単独変異では落ちない

worker除外は二重に実装されている。

- `pytest_collection_finish` の外側 guard: `conftest.py:559-565`
- `_prewarm_receipt_memo` 内側 guard: `conftest.py:372-375`

片方だけを除去しても他方がworker prewarmを止めるため、fake wiring検査も実xdist順序検査も緑のままである。両方同時に外す変異として再登録しない限りM9は生存する。

両方を外してconsumerを含む実xdist走を行うと、controller 1回に加えて各workerが `run_id=None` で実解決するため、worker数に近いqが再発する。期待nodeを1本だけに限定するなら、実consumerをrunner範囲へ混ぜてはならない。

成果物影響: must-fix 1を片側だけ失う実装退行をmutation matrixが検出できず、worker数分のresolver再発を見逃す。

7. [Major] M7、M8、M11はrunner modeを分離しないと期待node完全一致にならない

mutation harnessは1 specにつき全mutation共通のtest commandを使う (`tools/mutation_harness.py:1923-1955`, `:2071-2100`)。

- M7はxdistで走らせなければならない。serialではxdist wiring meta-testだけが赤で、代表consumerはserial hookにより通る。
- M8は`-n 0`で走らせなければならない。xdistではserial wiring meta-testだけが赤で、代表consumerはxdist hookにより通る。
- M11の期待赤はidentity meta-testだけである。serialではcanonical consumer singletonがprewarmされず、代表consumerも追加で赤になる。xdistなら非修飾controller moduleが作ったpickleをcanonical worker moduleが読めるため、代表consumerは通りidentityだけが赤になる。
- 従ってM7とM8を同一spec、同一commandで期待完全一致にすることはできない。少なくともxdist specとserial specへの分割が必要である。
- 裁定表の「wiring meta-test」「代表consumer 2 node」はcanonical nodeidを名指ししていない。現時点では実行可能なexpected node完全集合ではない。

成果物影響: 現状のまま一括本走するとKILLEDではなくMISMATCHになり、must-fixの検出力を証明できない。

8. [Minor] 変更後consumerのcollection中に実repoを書く直接経路は見つからないが、回帰検査はresolverだけを見ている

変更2 consumer fileにはmodule-scope fixtureがなく、autouse fixture本体はtest setupまで実行されない。module-scopeの実行はpath設定、marker生成、`enforce_held_functions`によるnamespace wrapper設定であり、変更されたmemo moduleのmodule初期化もsingleton生成だけ (`real_repo_receipt_memo.py:390-397`) である。変更5file内ではcollection時の実repo writerは見つからない。

ただし `test_receipt_memo_consumers_do_not_resolve_during_collection` はresolver呼出し0しか固定せず、実repo snapshot前後差やwrite syscallを検査しない。将来import時writerが追加されてもこのtestは通る。

成果物影響: 現差分ではsnapshot前の実repo変更はないが、collection副作用の将来退行を既存meta-testだけでは検出できない。

## 経路表 (実装後)

| 経路 | prewarm / 実解決 | 障害時の赤 |
|---|---|---|
| `tools/run_tests.py` + xdist controller | 最初にconsumerを報告したworkerのcallbackで1回 (`conftest.py:577-588`) | prewarm失敗はcollection internal error、rc 3 |
| xdist worker | prewarmなし。test bodyの最初のconsumerがpickleを読む (`real_repo_receipt_memo.py:347-387`) | `/tmp`差、cache欠落、flock不能はconsumer nodeの赤 |
| 素の `pytest -n N` | controllerで1回。runner preflightなし | submodule不全はinvalid resolutionとして混入しうる |
| 非xdist / `-n 0` | serial `pytest_collection_finish`で1回、`run_id=None`。pickle/flock不使用 | resolver例外だけが`resolver-failed`。通常production例外はinvalid resolutionへ翻訳される |
| 素の `pytest` | 上と同じ | pytest test赤またはcollection internal error |
| 素の `pytest -p no:xdist` | absent option guardが効きserial prewarm | prewarm失敗時はrc 3 |
| `tools/run_tests.py -p no:xdist` | 到達しない | 注入済み`-n/--dist`のusage error |
| bounded local成功 | cgroup内childが通常のxdist/serial経路を実行 | childの赤を返す |
| bounded local attestation失敗 | 0回 | pytest未実行、rc 16 (`tools/run_tests.py:1417-1430`) |
| dispatch成功 | login側0回、compute child側で通常1回 | 公式経路は同一node `/tmp`。compute側障害はjob結果へ出る |
| dispatch失敗 | 0回 | rc 16、test赤ではない |
| worker crash再起動 | controllerの追加prewarmなし。replacement workerもprewarmせず既存pickleを読む | 同一`/tmp`なら成立。cache不可視ならreplacementのconsumerが`cache-missing` |
| serialの2回目 `pytest.main()` | 0回。旧process snapshotを再利用 | 赤にならずstale snapshot |
| xdistの2回目 `pytest.main()` | 0回。新UIDのpickleを作らない | replacement全workerが`cache-missing` |
| production CLI child | pytest memo対象外 | `test_cli_subprocess_returns_rc_2_on_gate_refused`では実repo resolver 1回 |
| mutation collection | `-n 0 --collect-only`なので0回 (`mutation_harness.py:1287-1318`) | collection失敗はharness error |
| mutation baseline / mutant | runner範囲に代表consumerがあれば各process原則1回 | M7/M8 mutantはprewarm削除により0回でconsumer赤。M9両guard除去はworkerごとに再解決 |
| `--collect-only` | 0回。cache書込みなし | consumer fileのmemo import自体は起きる |
| consumer 35 node + opt-out 3 node正例 | prewarm 1回。opt-outはstubしたresolverを各node内で検査 | prewarm infra失敗なら正例全体が成立しない |

## 変異検出力の判定

| 変異 | 判定 | 実際に落ちるnode / 過剰決定 |
|---|---|---|
| M1 | 検出可能 | `test_receipt_memo_l1_to_l5_are_fail_closed_and_uid_is_hashed`。L1は独立nodeではなく同test内のassertion |
| M2 | 検出可能 | 同node。lock fallbackで期待例外がなくなる |
| M3 | 検出可能 | 同node。cache missからresolve/storeすると期待例外がなくなる |
| M4 | 検出可能、冗長 | 上記nodeと`test_receipt_memo_session_cache_round_trip_preserves_the_resolution`の2node。裁定どおり過剰決定 |
| M5 | 検出可能 | L1〜L5統合node。store例外握り潰しで期待例外がなくなる |
| M6 | 検出可能 | `test_receipt_memo_public_endpoint_is_fail_closed_before_prewarm`。direct/private層は先にfallbackしないため公開端理由に絞れる |
| M7 | 条件付き | xdist限定ならwiring meta-testと代表consumer 2node。serialでは代表consumerが通りMISMATCH |
| M8 | 条件付き | `-n 0`限定ならwiring meta-testと代表consumer 2node。xdistでは代表consumerが通りMISMATCH |
| M9 | 検出不能 as registered | guardが2箇所あり、片側除去は生存。両層同時変異への再登録が必要 |
| M10 | 検出可能 | `test_receipt_memo_consumer_inventory_and_optouts_are_complete`。golden、source AST、configured setの三者比較で落ちる |
| M11 | 条件付き | xdistなら`test_receipt_memo_module_identity_and_resolver_caller_are_fixed`だけが赤。serialでは代表consumerも赤となり期待集合超過 |

mutationの時間はrunner command未登録のため一意には確定できない。最小分割ならM1〜M6、M9、M10は実repo解決0回、M7/M8/M11のbaselineは各1回、M7/M8 mutantは0回、M11 xdist mutantは1回である。1 specの共通runnerへ代表consumerを入れるなら、baselineとprewarmを壊さない各mutantがそれぞれ約19.70秒を払う。

## 総括

判定は差し戻し。

実装は通常の単一pytest sessionではcontroller-only prewarmとfail-closedを成立させるが、session境界、同一UID、分離`/tmp`、runner経由の`-p no:xdist`で偽赤またはstale snapshotを作る。変異面ではM9が明確に生存し、M7/M8/M11はrunner mode分割とcanonical expected nodeの確定なしには完全一致判定できない。

pytestは実行していない。変更5fileとrunner、mutation harnessを静的に監査した。