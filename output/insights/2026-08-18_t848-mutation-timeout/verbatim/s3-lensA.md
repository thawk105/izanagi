結論は、段 2 プランをそのまま段 5 へ送らず、段 4 で scope を組み直すべきです。

## 所見 0 — 宣言上の dispatch timeout 閉鎖は確認できる

主張: 追補の実測 1 は正しいです。`runner_mode="dispatch"` で `_run_tests` が `timed_out=True` を返した場合、通常台帳の `TIMEOUT` へ到達する反例は見つかりませんでした。

根拠となる file:line:

- `tools/mutation_harness.py:274-304` は dispatch timeout なら必ず `OrphanHoldStop` を返す。既存 hold でも `:305-313` で停止し、`None` は「非 dispatch」または「timeout、receipt 異常、既存 hold の全てが無い」場合だけ。
- 変異では `tools/mutation_harness.py:1822-1832` が stop を投げ、status 算出は `:1841-1843` と後段。
- `:1872-1877` は例外を再送出する。`finally` の `:1897-1918` も、元の stop が伝播中なら握り潰さない。
- baseline と collection もそれぞれ `:1698-1708`、`:1314-1324` で status 作成前に止まる。
- `:2803-2812` が sidecar を書いて rc=2。挙動テストも `orchestrator/tests/test_mutation_harness.py:900-970` に存在する。
- SignalAbort は hold があれば `:1911-1912` で stop を付帯し、`:2813-2823` で sidecar を書いた後に signal 終了する。hold が無くても `:2831-2844` の signal rc となり、通常 TIMEOUT record は作らない。

深刻度: nit（確認事項）

成果物への影響: 宣言上 dispatch の harness timeout は通常台帳の `completed` を増やさず、orphan-stop と rc=2、または signal rc になる。

## 所見 1 — 段 2 プランは追補後の生存欠陥を直さない

主張: 生きている欠陥は追補どおり「local 申告の `tools/run_tests.py` が実際には dispatch する」経路です。しかし段 2 プランは local timeout を無条件 `TIMEOUT` のまま残し、分類器を宣言上 dispatch にしか置きません。実装しても T-848 の検出力は増えません。

根拠となる file:line:

- 段 2 プラン `s2-plan.md:17-27,46-57,224-226` は inventory と receipt 分類を dispatch に限定し、local timeout を terminal `TIMEOUT` とする。
- `_runner_identity` は local でも `tools/run_tests.py` を許可する。`tools/mutation_harness.py:703-724`。
- `run_tests.py` は admission 不明または不足を dispatch へ倒す。`tools/run_tests.py:1028-1040,1064-1075,1760-1795,1856-1862`。
- local 申告なら orphan 防壁は即 `None`。`tools/mutation_harness.py:274-275`。
- local timeout は `:1649-1650` で terminal `TIMEOUT` となり、`finally` も hold を無視して source を復元する。`:1879-1883,1920-1921`。
- 追補自身もこの不整合を `brief-addendum.md:32-47,60-68` で scope の中心としている。

深刻度: blocker

成果物への影響: queue で一度も走らなかった変異が引き続き `TIMEOUT` として `completed` を増やし、さらに残存 job がある状態で source 復元や次変異へ進み得るため、変異 ID と実行 bytes の対応まで壊れる。

## 所見 2 — receipt の永続化時刻では RUN と QUE を安全に分類できない

主張: timeout 時の receipt は保証されません。さらに保存できた場合も、最後の通常履歴が QUE で cleanup 時の fresh qstat が RUN を観測する経路を段 2 分類器が落とします。これは DW-M06 の hang 証拠を失わせます。

根拠となる file:line:

- `state_history` と `queue_wait_observed=True` はまずメモリ上で更新されるだけ。`tools/pegasus/dispatch_compute.py:1805-1813,1825-1837`。
- 正常時の永続化は結果収集後の `:1951-1975`。signal・例外時も cleanup を実行した後の `:2002-2056` まで保存されない。
- signal handler は `:1601-1615`、cleanup は `:1617-1652`。既定 budget は 90 秒 `:55`、個々の scheduler command も最大30秒 `:422-437`。
- 一方 harness は SIGTERM 後5秒で SIGKILLする。`tools/mutation_harness.py:1540-1554`。
- cleanup の fresh qstat が RUN を観測すると `qdel.gate.scheduler_state="RUN"` を残して取消拒否する。`tools/pegasus/dispatch_compute.py:1365-1373`。この時点で通常の `state_history` は直前の QUE のままでもよい。
- 段 2 プラン `s2-plan.md:49-56` は `queue_wait_observed` と通常 history しか terminal 判定に使わず、この qdel 側の肯定的 RUN 証拠を使わない。
- hang timeout は dispatch 起動時から数える。`tools/mutation_harness.py:1618-1623,1810-1817`。dispatch 自身の queue 上限は900秒 `tools/pegasus/dispatch_compute.py:47`。
- 具体例では `output/insights/2026-08-09_t553-git-budget-mutation-spec.json:4-5,53-68` の hang 変異が60秒であり、RUN 前の QUE だけで timeout できる。静的集計では hang 20件中16件が900秒未満だった。
- DW-M06 は hang timeout を kill 証拠として残し harness を落とさない契約。`docs/dev-wave/mutation.md:37-40`。現行 D454 は dispatch timeout を全て orphan stop にする。`docs/decisions.md:18997-19003`。

深刻度: blocker

成果物への影響: 実際には RUN 後に hang した変異も `QUEUE_TIMEOUT` または orphan-stop へ落ち、terminal な hang kill が1件減り、検出力の分子と `completed` が不足する。

## 所見 3 — fail-closed が逆向きの分岐は2つある

主張: 証拠不足または矛盾から terminal 側へ倒れる分岐が残っています。

根拠となる file:line:

1. local 自己申告だけで terminal `TIMEOUT` とする分岐。`s2-plan.md:48,226`。実体が dispatch し得る根拠は `tools/run_tests.py:1760-1795,1856-1862`。
2. `queue_wait_observed=True` なら、history に RUN が無くても terminal とする分岐。`s2-plan.md:49`。producer は RUN entry を先に append してから true を設定するため、true なのに RUN history が無い receipt は矛盾している。`tools/pegasus/dispatch_compute.py:1805-1813,1834-1837`。プランは逆向きの「false + RUN」だけを conflict 扱いする。`s2-plan.md:56`。

深刻度: must-fix

成果物への影響: local 申告または壊れた receipt だけで terminal `TIMEOUT` が作られ、台帳の `completed` が実行証拠なしに1増える。

## 所見 4 — 新 status 自体から新しい偽の緑は開かない

主張: 段 2 プランどおり `QUEUE_TIMEOUT` を非 terminal、期待 status 外に保てば、単走、wrapper、fan-out の全てで赤になります。

根拠となる file:line:

- spec の期待 status は閉集合で検証される。`tools/mutation_harness.py:41,505-512`。
- status と期待が違えば `matches_expectation=False`。`:1849-1852`。続行しても最終 rc は1。`:2800-2802`。即停止なら `:2793-2797` 相当から rc=2。
- summary の `completed` は terminal 集合だけを数える。`:1924-1944`。
- wrapper は record status が terminal 集合外なら拒否し、`registered/recorded/completed` の全一致も要求する。`tools/mutation_worktree.py:865-889`。
- child rc 0/1 なのに非 terminal なら wrapper rc=125。`:1163-1172,960-967`。child rc=2 ならそのまま赤。
- fan-out は `registered == recorded` と全 record/completed 数を要求し、未知 status も拒否する。`tools/mutation_fanout_contract.py:942-968`。例外時 rc=2 は `:1552-1557`。

深刻度: nit（確認事項）

成果物への影響: `recorded` は増えても `completed` は増えず、wrapper receipt の `terminal_ledger` と fan-out index は緑にならない。

## 所見 5 — 「全史 TIMEOUT 0件」は probe の測定範囲を超えている

主張: probe の再実行結果は `scanned_ledger_like=762, broken=0, timeout_hits=0` でしたが、これは repo 全史の不在を証明しません。実際に timeout を記録した list-root JSON を構造上除外しています。

根拠となる file:line:

- probe は `*.json` のみ。`scan_timeout.py:10`。
- JSON root が object でないものを除外する。`:16-17`。
- `summary` または `mutations` が無い形式も除外し、`status=="TIMEOUT"` だけを見る。`:18-35`。
- `output/insights/2026-07-27_t119-t105-stopcont-and-vanished-artifact-mutation-ledger.json:1` は list-root。
- 同台帳 `:31-44` は `verdict="KILLED-BY-HANG"`、`timed_out=true`、120.1秒を記録しているが probe は走査件数にすら含めない。
- `output/insights/2026-08-01_t247-envelope-reject/evidence/mutation-ledger.jsonl:1` のような JSONL 台帳も拡張子段階で対象外。

深刻度: must-fix

成果物への影響: 記録文言は「全史 TIMEOUT 0件」から「probe が受理した object-root JSON には exact `status=TIMEOUT` が0件」へ狭める必要があり、過去 timeout 実績の主張値は0ではなく少なくとも1件存在する。

## 所見 6 — resume 成功後も fan-out が永久拒否する設計になっている

主張: プランは `QUEUE_TIMEOUT` を history へ移して再実行すると約束する一方、再実行成功後も history に1件あれば fan-out が拒否する設計です。wrapper と fan-out の完了意味論が一致しません。

根拠となる file:line:

- プランは nonterminal を history へ移し、current record から外す。`s2-plan.md:127-139,185-187`。
- 同じプランが fan-out では history の `QUEUE_TIMEOUT` を拒否する。`:155-161,207-209`。
- 現行 fan-out は history の `PARSE_ERROR` を検証後に許しており、他 status だけを拒否する。`tools/mutation_fanout_contract.py:1011-1036`。
- wrapper の terminal 判定は current `mutations` の全件性を検査するが history は拒否条件にしていない。`tools/mutation_worktree.py:836-889`。

深刻度: must-fix

成果物への影響: 再走で全変異が terminal になっても shard は併合不能のままとなり、fan-out の検出力集計値そのものが作れない。

## 所見 7 — 新 status では即停止を選ぶべき

主張: 択一は (a) 記録直後に即停止が正しいです。系統的な queue 混雑中に残り変異を走らせても独立した検出力は増えません。

根拠となる file:line:

- `output/insights/2026-08-10_t139-producer-slice-mutation-spec.json:4-6` は timeout 600秒。同 spec は最初の ID が `:8`、最後が `:302` で計19件。
- 最初から混雑した場合、続行は最大 `19 × 600 = 11,400秒`、即停止は600秒。差は10,800秒、3時間。
- 900秒未満の実効 timeout 176件を静的集計すると、全件続行の deadline 合計は96,600秒、26時間50分。
- resume loader が非 terminal を current から除けば、`tools/mutation_harness.py:2662-2665` はその ID を pending に戻す。現行の同型処理は `PARSE_ERROR` を history へ送る `:2333-2351` と、kept を再設定する `:2370-2375`。

深刻度: nit（段 2 の即停止方針を維持）

成果物への影響: 即停止と続行で有効な検出力は変わらず、続行だけが最大で残り変異件数分の timeout を追加消費する。

## 総括

blocker は2件です。  
最優先は、段 2 プランが追補後の local申告と実dispatchの乖離を一切直さないことです。  
段 4では現プランを停止し、まず runner-modeとargvの整合強制を主案として再計画すべきです。  
pytestは指示どおり未実走で、所見は静的検査とread-only集計に基づきます。