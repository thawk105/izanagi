| 所見 | 判定 | 根拠（file:line） |
|---|---|---|
| A1 復号による log bytes・rc の差 | closed | `tools/run_tests.py:1487–1490` は locale で厳密復号し改行を正規化する。復号失敗時は `1496–1498` で従来収集へ進む。ただし再収集そのものの同値性には下記の反例がある。 |
| A2 再インデントの規模 | not-applicable | 段6裁定で不採用。`tools/run_tests.py:2700–2826` の所有スコープは残るが、採否条件ではない。 |
| A3 成功後の子孫停止 | not-applicable | 段6裁定で従来経路と同じ範囲と判断。`tools/run_tests.py:1503–1514` は collection 子自身を扱う。 |
| A4 採算・集合不変の実測 | partial | `orchestrator/tests/test_run_tests_shards.py:929–957` に実 fork テストは加わった。指定された同時刻対照・受入全走は未実施。 |
| B1 起動直後の signal 窓 | partial | 独自 handler と新 session は除去されたが、`tools/run_tests.py:2699–2700` では起動が `try` より前にある。親だけへの SIGINT で後始末に入れない窓が残る。 |
| B2 後始末中の signal | partial | 独自 handler は除去された。一方 `tools/run_tests.py:1505–1514,2824–2826` の cleanup 中に KeyboardInterrupt が入れば、その `finally` は子の reap まで保証しない。 |
| B3 一時出力失敗の新しい rc | partial | 既定の tempfile と再収集は `tools/run_tests.py:1522–1526,1496–1498` に実装された。失敗時に deadline が残る保証はなく、log 公開後の失敗には create-only 衝突がある。 |
| B4 reap 済み PID への killpg | closed | `tools/run_tests.py:1503–1511` は `poll()` で未回収の `Popen` のみ terminate/kill/wait する。 |
| B5 SIGTERM の終了形式 | closed | 独自 handler はなく、`tools/run_tests.py:1524–1527` も新 session を作らない。launcher の子 rc 正規化は `tools/acceptance_launcher.py:130–133,274`。 |
| B6 実 worker 寿命を通すテスト | partial | `orchestrator/tests/test_run_tests_shards.py:929–957` は実 fork と worker PID の終了を通す。ただし report 読取と merge は `933–941` で代役に置換している。 |

## 新規所見

1. **must — 再収集は「従来経路と同じ結果」を保証しない。** `tools/run_tests.py:1482–1484,1496–1498` は前倒しの非ゼロ rc を捨てて二度目を実行する。既存の `fail_first` fixture (`orchestrator/tests/test_run_tests_shards.py:733–734,896–905`) 自体が反例で、同じ木でも従来の一度目は rc 16 と失敗 log、修正後は二度目が成功して rc 0 と成功 log になる。前倒し成功・従来の実行時点では失敗する場合は逆も起こる。**放置時:** 受理集合、rc、log が実行回数に依存する。**推奨修正:** 同値性を要求するなら失敗の再実行を結果として採用しない。再試行を仕様とするなら不変条件と対照実験を改訂し、「初回失敗・次回成功」の正例で期待 rc と log を明記する。

2. **must — log 公開後の例外で create-only が再収集を妨げる。** 前倒し側は `tools/run_tests.py:1490–1498` で log 書込みまで `OSError` の再収集対象にする。`tools/acceptance_shards.py:250–255` では宛先への hard-link 後にも directory の open/fsync があり、ここで失敗すると log は存在する。再収集が `tools/run_tests.py:1554–1556` から同名 log を create-only で書き、衝突して rc 16 になる。通常の成功後も `tools/run_tests.py:1499–1514` の file close 例外が結果を覆いうる。通常時の二度の `close()` (`1500–1501,2824–2826`) 自体はほぼ冪等だが、失敗時の回復契約はない。**放置時:** 成功内容の log が残ったまま rc 16 となり、再収集結果は成果物にならない。**推奨修正:** log 公開前に前倒し結果を確定し、公開後の失敗を再収集へ流さない所有・コミット境界を設ける。link 後の fsync 失敗と close 失敗を注入し、rc と log の組合せを検査する。

3. **should — 割込み時の後始末に窓が残る。** 起動は `tools/run_tests.py:2699`、所有する `try` は `2700` から始まる。また `collect()` の `finally` は `collected` が真の場合だけ close し (`1499–1501`)、KeyboardInterrupt は `run_parallel` の `BaseException` 捕捉 (`tools/acceptance_shards.py:1499–1508`) 後、main の `finally` に依存する。そこでの `terminate`・`wait` 中 (`tools/run_tests.py:1505–1511`) に再度割込みが入ると reap を完遂できない。**放置時:** 親だけを対象にした割込みで collection 子が残り、予定した rc が覆われうる。**推奨修正:** 起動直後から所有スコープに入れ、割込み中も reap と file close を完遂できる cleanup にする。Popen 直後と cleanup 待機中への SIGINT を正例として確認する。

4. **should — timeout 後の「従来収集へ戻る」は実質的に実行できない。** `tools/run_tests.py:1479–1482` は残り deadline 全部を前倒し子の `wait` に渡す。timeout 後に `1497` の停止処理が最大 0.2 秒以上使い、`1498` の従来経路は `1546–1548` で残り時間なしとして rc 16 を返す。**放置時:** tempfile 障害や遅い前倒し子を再収集で救済するという受理範囲は timeout 境界では成立しない。**推奨修正:** 再収集用の時間を予約するか、timeout は救済不能と仕様化する。境界時刻の正例で再収集の起動有無と rc を固定する。

5. **should — 追加テストには偽緑・偽赤の余地がある。** 復号比較の CRLF ケース (`orchestrator/tests/test_run_tests_shards.py:909–926`) は二回起動を期待するため、前倒しを迂回して従来経路を二回通しても同じ rc・log なら通る。universe の一致も比較しない。不正 byte の期待 rc 16 は locale に依存し、`\xff` を復号できる locale では偽赤になる (`739–741,909`)。実 fork テストは report gate を代役にし (`933–941`)、PID 判定は `/proc` が無い環境なら即座に成功する (`835–842`)。**放置時:** 前倒し不実行や report gate の回帰を見逃し、環境差で焦点テストが赤になる。**推奨修正:** 前倒し経路の使用と両 universe を明示的に記録・比較し、不正 byte テストの locale を固定する。fork テストは worker の `exitcode` も確認し、report gate の検査範囲を別途明記する。

## 総括

**NO-GO。** `fail_first` が「同じ木なら従来と同じ rc・universe・log」という主張への具体的反例になっている。log 公開後の再収集衝突と割込み時の所有窓も残る。焦点走の 747 passed / 1 skipped は確認済みだが、変異・受入全走・同時刻対照は未実施。