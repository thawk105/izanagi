## 1 — must-fix : E2E は現行 xdist 実走で既に赤く、受入 gate として閉じていない

(i) `t1.log` では 1 failed / 20 passed。実際の `longreprtext` に `[gw4] linux -- Python ...` が付加され、`source_bytes` が期待値より 936 bytes 多い。

(ii) 一次資料: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t677-relay-reach/t1.log:77-84`、`orchestrator/tests/test_pytest_failure_digest.py:480-511`、`orchestrator/tests/test_pytest_failure_digest.py:484-486`

(iii) 成果物影響: 実運用に近い nested xdist 経路を通す E2E が緑にならず、digest 到達 gate を記録できない。

(iv) 対処案: xdist が実際に付加する worker prefix を独立 oracle に含める。worker id・Python 表記を固定できないなら、prefix の形式を検証したうえで実際の prefix bytes を会計へ反映する。

## 2 — must-fix : failure 件数が多いと digest 選択が二次計算量になる

(i) `_build_failure_digest` は `selected_count=1..N` ごとに `_render_failure_digest` を再実行し、選択済み全 block を再描画する。110 件で各診断が 1 KiB 程度なら `110×111/2=6,105` block 描画、最大約 6.1M 文字の escape。1,000 件なら 500,500 block、約 500M 文字になる。4 KiB tail なら約 2.0B 文字。秒数は未実測だが、110 件でも秒級、数千件では分級になり得る。

(ii) 一次資料: `orchestrator/tests/conftest.py:350-376`、`orchestrator/tests/conftest.py:490-546`

(iii) 成果物影響: 失敗全走の終了処理に診断生成時間が追加され、walltime・relay 到達前 timeout のリスクが増える。

(iv) 対処案: block を一度だけ incremental に描画し、累積 bytes が予算を超えた時点で停止する。`rendered_blocks`、`retained_bytes`、rank を保持し、候補ごとに全 block を再描画しない。

## 3 — must-fix : pytest.main() の再入で外側 session の failure stash が消える

(i) `_FAILURE_REPORTS` は module global で、`pytest_configure` が毎回 clear する。外側 session の途中で `pytest.main()` を呼ぶと、内側 session が外側の report を消し、外側 `pytest_unconfigure` は digest を出せない。

(ii) 一次資料: `orchestrator/tests/conftest.py:320-326`、`orchestrator/tests/conftest.py:600-605`、`/home/SFC/tanab/.local/lib/python3.10/site-packages/_pytest/config/__init__.py:1207-1219`

(iii) 成果物影響: 同一 process 内の再入経路で「失敗したのに digest なし」が発生する。現行 self-run harness は `pytest.main()` を process 終端で呼ぶだけで、この再入を検査していない。

(iv) 対処案: `config` または session object に stash を束縛し、global list を廃止する。少なくとも nested session の回帰テストを追加する。

## 4 — must-fix : lazy ImportError が relay 実装破損を無言の診断消失に変える

(i) `from tools.pegasus.dispatch_compute import ...` の全 ImportError を `return` で握っている。トップレベル `tools` 不在と、dispatch_compute 内部の依存欠落・壊れた import を区別していない。

(ii) 一次資料: `orchestrator/tests/conftest.py:550-560`

(iii) 成果物影響: 実運用で relay module が壊れても exit code は維持され、digest も error marker も出ず、診断到達 gate が偽陽性になる。

(iv) 対処案: `ModuleNotFoundError` の `exc.name` が対象トップレベル module の場合だけ fail-open とし、内部依存の ImportError は error digest または再送出にする。

## 5 — must-fix : relay 結合テストは実 relay を通るが、境界条件を検査していない

(i) (h) は実際に `_relay_scheduler_logs` を呼んでいるため「通したふり」ではない。しかし、64 KiB ちょうど、digest が 64 KiB 境界をまたぐ、digest 後に child 出力がある、の 3 ケースはない。現在は digest が child stdout の末尾にあり、最終 64 KiB に丸ごと入るケースだけである。

(ii) 一次資料: `orchestrator/tests/test_pytest_failure_digest.py:602-644`、`tools/pegasus/dispatch_compute.py:687-704`、`tools/pegasus/dispatch_compute.py:741-804`

(iii) 成果物影響: `_utf8_tail` の境界誤り、digest の先頭欠落、後続出力による digest 非末尾化を見逃す。

(iv) 対処案: relay fixture を 3 つに分け、`size == 65536`、digest 開始位置が tail 境界の前後、digest 後に sentinel を置くケースを追加する。

## 6 — must-fix : excerpt の一行化は人間向け診断の可読性を大きく損なう

(i) 改行を `\x0a` に変換するため、最大 4 KiB の診断が一行になる。端末折返し、pager 検索、docs 転記、差分比較が困難になる。`_utf8_tail` の文字境界処理自体は ASCII escape 後なので壊れにくい。

(ii) 一次資料: `orchestrator/tests/conftest.py:350-376`、`orchestrator/tests/conftest.py:389-405`、`tools/pegasus/dispatch_compute.py:701-704`

(iii) 成果物影響: digest は届いても、人間が原因を読めず、耐久ログやレポートへの転記品質が落ちる。

(iv) 対処案: 改行を保持し、各物理行に `> ` を付ける。`_failed_nodes` は `|` だけを除去するため、`> ` prefix なら偽 `FAILED` node を防げる。行単位で byte 会計する。

## 7 — must-fix : 9 テストには単独で生存する具体的な欠陥が残る

(i) 以下は各テスト単独で緑のままになる具体例である。

- T1 `test_failure_digest_contains_nodeid_and_diagnostic_tail`: `sha256={item.sha256}` を固定値にしても hash を検査しないため緑。
- T2 `test_failure_digest_is_silent...`: `sys.stdout.write` を `sys.stderr.write` に変えても `.out` だけを検査するため緑。
- T3 `test_failed_and_collect_reports...`: block の hash や excerpt 内容を壊しても nodeid と件数だけなので緑。
- T4 `test_failure_digest_budget...`: tail slice を head slice に変えても source byte 数と予算は同じで、末尾 sentinel を検査しないため緑。
- T5 E2E: selected nodeid と account を正しく出しつつ、excerpt 本文を別内容に置換しても、sentinel が digest 内のどこかにあれば緑。selected=0、実 nodeid 不在、sentinel が digest 外だけ、単純な stats 件数だけの実装は現行 assertions が検出する。
- T6 `test_failure_digest_budget_is_bound...`: `_load_failure_digest_budget` を `49152` の固定値にしても、現在の relay limit が 64 KiB の間は緑。
- T7 `test_failure_digest_exception_boundaries...`: `pytest_unconfigure` から `_emit_failure_digest` 呼び出しを削除しても、stash を clear してから wrapper を検査しているため緑。
- T8 consumer test: newline・C0・非 ASCII の escape を壊しても、fixture が単一 ASCII 行なので緑。
- T9 relay test: relay limit を `65535` にしても、末尾に丸ごと存在する digest は残るため緑。

(ii) 一次資料: `orchestrator/tests/test_pytest_failure_digest.py:210-227`、`:237-293`、`:296-315`、`:318-342`、`:491-511`、`:514-519`、`:522-579`、`:586-599`、`:602-644`

(iii) 成果物影響: 他テストが偶然補うだけで、個別 gate の診断保証・relay保証・wrapper結線保証が独立していない。

(iv) 対処案: T5 は各 entry と excerpt tail の対応を hash または独立計算で検証する。T7 は通常経路で wrapper が実際に writer を呼ぶ test を追加する。T9 は境界 fixture を追加する。

## 8 — nit : M1〜M6 は静的には帰属可能だが、M7 は実在する一行変異として未束縛

(i) 静的な期待結果は次のとおり。

- M1: T4/T6 が予算差を検出。変更前 HEAD には digest code がなく、既存 relay literal test は緑の見込み。
- M2: T1 の head sentinel assertion、T5 の末尾 sentinel assertion が検出。
- M3: T8 の `> ! FAILED` と raw/1段/2段 relay assertion が検出。
- M4: T4/T5 の `omitted_bytes` oracle が検出。
- M5: T2 の worker 無出力、T5 の `selected > 0` が検出。
- M6: T7 の RuntimeError fail-open assertion が検出。
- M7: 現行実装には `terminalreporter.stats` を参照する一行が存在せず、「stash を stats["failed"] へ置換」は実際の一行変異として注入位置が定まらない。したがって帰属は未確認。

(ii) 一次資料: `s4-adjudication.md:117-131`、`orchestrator/tests/conftest.py:330-344`、`orchestrator/tests/test_pytest_failure_digest.py:237-342`、`:491-579`

(iii) 成果物影響: M7 を KILLED と記録すると、実在しない変異を検出したという誤った検出力証拠になる。なお、M1〜M7 の実変異走行および変更前 HEAD の別走行は今回実施していないため、実測結果ではない。

(iv) 対処案: M7 を撤回し、実在する `if report.failed:` を `if False:` または常に空 stash となる一行へ置換する変異に再登録する。新テスト集合と HEAD 集合の双方を実走して初めて帰属を確定する。

## 9 — nit : 予算算術は安全側だが、2 bytes の余裕を常時捨てている

(i) `65536 × 3 // 4 = 49152` は正しい。excerpt は `4096 - len("> ! \n") = 4091` で、通常 frame の overhead は `"> "` + `"\n"` の 3 bytes、`FAILED ` 無害化時は追加 2 bytes なので最大 5 bytes予約は整合する。ただし通常 excerpt は 2 bytes短くなる。block 5120 と frame/account 1024 は上限チェックで守られている。

(ii) 一次資料: `orchestrator/tests/conftest.py:292-299`、`:389-405`、`:470-486`、`orchestrator/tests/test_pytest_failure_digest.py:28-30`、`tools/pegasus/dispatch_compute.py:34-35`

(iii) 成果物影響: correctness 上の off-by-N はないが、利用可能な excerpt payload を最大 4093 bytesまで使えるケースで 4091 bytesに制限している。

(iv) 対処案: `payload_budget = 4093` とし、`FAILED ` 無害化後だけ追加 2 bytesを予約する。ただし条件分岐を誤ると上限超過するため、現状の安全側設定を維持する判断も可能。

## 総括

- E2E は xdist prefix 会計差で現に赤く、まず修正が必要。
- digest 選択ループは failure 数に対して二次計算量で、110〜数千件では実運用コストが危険。
- `pytest.main()` 再入と広すぎる ImportError fail-open は診断消失経路。
- relay 結合テストは境界条件を欠く。
- 一行 excerpt は可読性を損なうため、行保持 + `> ` prefix を検討すべき。
- M7 は実在する一行変異として未登録であり、検出力証拠に使ってはならない。