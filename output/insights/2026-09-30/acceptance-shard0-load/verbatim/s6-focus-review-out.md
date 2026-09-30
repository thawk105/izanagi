## 所見ごとの対応表

判定対象は `6ec6c1f28`。行番号は指定された wave の木、または job dir 内の資料を指す。

| 所見 | 判定 | 根拠 file:line | 残る問題 |
|---|---|---|---|
| A1 / B1 | closed | `orchestrator/tests/conftest.py:2603-2605,2627-2637` | 生存 builder は daemon のまま終了し、木が `/tmp` に残りうる。これは段 6 裁定の受理範囲。 |
| A2 | closed | `orchestrator/tests/conftest.py:2606-2615,2627-2631`; `orchestrator/tests/test_s8b_oracle_driver.py:1417-1466` | 後始末の例外処理には下記の新規所見 1 がある。 |
| A3 | closed | `orchestrator/tests/test_s8b_oracle_driver.py:1400-1414` | T6 は timeout 時の木・lock 保持と、解放後の撤去を検査する。 |
| A4 | closed | `orchestrator/tests/test_s8b_oracle_driver.py:1293-1308` | 別参加者 object から両 key の hit を検査する。同一 process 内の模擬参加であり、段 6 裁定の指定どおり。 |
| A5 | partial | `s6-ruling.md:27`; `codex/fix1-u1-out.md:14` | M3/M5/M6 の登録は具体化されたが、期待赤 node の完全集合と単一理由性は probe 未確認。 |
| A6 | closed（refuted 維持） | `orchestrator/tests/conftest.py:3108-3122,3541-3543` | 反論なし。prewarm の finish は可視 output の finish より先。 |
| B2 | closed | `meas/aggregate-ab.py:242-250,282-293` | L4 は対 1 の `W0(B)−W0(A)≤0` と等価。 |
| B3 | closed | `meas/run-arm.sh:45-61`; `meas/aggregate-ab.py:102-160,172-210` | 正式受入の実物を使う対 2 は未実走。起動時刻の証拠は別ファイルに依存する。 |
| B4 | closed | `meas/aggregate-ab.py:227-238` | 共通 nodeid の shard 0 所属差を無効化する。実対での発火は未確認。 |
| B5 | closed | `meas/run-pair-ab.sh:25-35`; `meas/aggregate-ab.py:223-226` | 対 1 の両腕を起動前 pyc 0 で検査する。 |

対照の量は、`meas/aggregate-ab.py:25-74` が W、pre、T、span、占有、群 A/B、T-080 別時間を算出し、`:282-293` が L1〜L4 を計算する。対 2 では正式受入の receipt と child log の SHA、shard request の commit を照合する（`:102-159,201-210`）。`SELFCHECK.md:7-15,30-34` の過去 3 走の派生値と「すべて一致」という主張は、元の baseline 成果物が今回の射影に含まれず、独立には照合できない。

焦点走 2 の `focus2/junit.xml:1` に、T1〜T7 の各 nodeidと起動失敗 test の `[False]`・`[True]` があり、いずれにも failure/error 要素がない。焦点走 1 の赤 4 node は `focus1/run.log:38-132,166-170`、差し替え先 module の追加は `orchestrator/tests/test_s8b_oracle_driver.py:1244-1250`。4 node が焦点走 2 で緑になったため、その原因は閉じた。一方、焦点走 2 全体は `focus2/run.log:119-121` のとおり **418 passed / 1 failed / 9 skipped**。赤は別 node の `test_real_repo_writer_drains_overlapping_reader_stream[legacy]` であり、親の単独再走結果はこの資料にない。

## 新規所見

1. **should — 起動失敗時の cleanup 例外が失われる。** `orchestrator/tests/conftest.py:2606-2615` は `_finish_t080_shared_base_prewarm()` の例外を無条件に捨て、`bases.lifetime.closed` が真なら job 属性も消す。`_T080SharedBases.close()` は木の撤去が失敗しても fd を閉じる（`orchestrator/tests/test_s8b_oracle_driver.py:931-944`）ため、この場合は撤去失敗を報告・再試行する手掛かりが消える。受理するなら、元の start 例外を主例外に保ちつつ cleanup 例外を連結して記録する。拒否すると、起動例外だけが見えて残存木の原因を失う。通る正例は、2 本目の start と木の撤去がともに失敗したとき、両例外が確認できること。

2. **nit — 起動失敗 test の `Thread.start` 差し替え範囲が広い。** `orchestrator/tests/test_s8b_oracle_driver.py:1433-1464` は process 全体の `threading.Thread.start` を test 終了まで差し替える。monkeypatch は pytest の teardown で復元されるため、他 test への恒久的な漏れは確認されないが、差し替え中に別の background thread が起動すると誤って失敗する。受理するなら、差し替えを `_start_t080_shared_base_prewarm(node)` 呼出しの `monkeypatch.context()` 内に限る。拒否すると、並行起動に対する偶発的な赤を残す。通る正例は、start 失敗を注入した直後に元の `Thread.start` が復元されること。

## 総括

**NO-GO（現時点の land 判定）。** A1〜A4・B1〜B5 の修正経路は閉じたが、A5 の変異 probe、実対の対照、焦点走 2 の残る赤の帰属確認が未完了。焦点走 2 を全緑、または赤を独立に非帰属と確認した結果として扱うことは、現資料からはできない。