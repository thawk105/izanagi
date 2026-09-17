## 所見ごとの判定表

以下、C＝`orchestrator/tests/conftest.py`、T＝`orchestrator/tests/test_real_repo_serialization.py`、R＝`orchestrator/tests/README.md`。

| 所見 | 判定 | 根拠 file:line |
|---|---|---|
| A-1 | closed | C:1364 で gate open、C:1368 で SH 解放、C:1369 で gate EX、C:1374 で main EX。C:1382 の finally が timeout・KeyboardInterrupt 時も gate UN＋close を実行する。 |
| B-1 | closed | T:4452 は watchdog 30.0。P2 の `started`・実時間 assert は削除済み。T:4441 の入れ子 reader、T:4487 の再競合拒否、T:4491 の別 fd EX probe、T:4507 の `blocked == [True]`、T:4508 以降の mode・fd・参照数 2→1、T:4522 の空 state は維持。 |
| B-2 | closed | T:2225〜2236 は state 同一性・mode・fd・holders・参照数・gate_fd と kernel SH 保持を独立に検査。旧順序なら解放された key の EX probe が成功し、T:2233 の `pytest.raises(BlockingIOError)` が赤になる。common 拒否前の legacy 昇格を T:2209 で確認し、C:1452 の context 巻戻しから C:1408、C:1421、C:1429 を通って read に戻る。 |
| nit：actor cleanup／docstring | closed | T:2058 の finally に pipe close があり、wait 例外でも到達する。T:1981 は normal response readiness の watchdog に説明を限定。 |
| nit：deadline test 整形 | closed | T:2247 の `with` は括弧付き複数行に整形済み。 |
| nit：README | partial | R:258 の飢餓「抑制」、R:262 の common-dir 事前解決、R:266 の厳密優先の否定は反映済み。ただし R:265 の保証に過大表現が残る。下記参照。 |

## regression

所見：README の「writer が gate を保持する間、fresh reader を入れない」は、事前検査済み reader まで含む保証になっている。
分類：real
根拠：`orchestrator/tests/README.md:265`。`orchestrator/tests/conftest.py:1509` で reader は gate を解放し、`:1515` で後から main を取得する。reader が全 gate 検査を通過 → writer が gate EX を取得して既存 SH の解放待ち → 当該 reader が main SH を取得、という順序が可能。
影響：nit。fix の文言は gate 保持中の main 入場禁止を保証するように読めるが、実装が止めるのは当該 gate の事前検査。
推奨：「writer が gate を保持する間、その gate の事前検査を行う fresh reader を待たせる。検査済み reader の main 取得は妨げない」と限定する。

snapshot→final の差分では、指定された順序修正・負例追加・P2 修正・actor cleanup・整形・README 以外の内容変更は見当たらない。指定外の期待値変更、新しい依存、production deadline／retry の変更、および新しい実装上の欠陥は確認できなかった。

## 変異 anchor の照合

| 変異 | 現物の逐語 anchor | 照合 |
|---|---|---|
| M0 | C:1360 `# Writers hold the gate only while acquiring main; fresh readers` | 一致 |
| M1 | C:1491 `if not _REAL_REPO_PROCESS_LOCKS:` | 一致 |
| M2 | C:1362 `if target_mode == "write":` | 一致 |
| M3 | C:1362 `if target_mode == "write":` | 一致 |
| M4 | C:1378 `state.fd,` → C:1379 `deadline=deadline,` | 一致 |
| M5 | C:1387 `os.close(state.gate_fd)` | 一致 |
| M6 | C:1491 `if not _REAL_REPO_PROCESS_LOCKS:` | 一致 |

M2／M3 で gate open を省くと、C:1366 配下の明示 UN も省かれる点は fix 報告と一致する。これは anchor と制御構造の静的照合であり、変異の再実走判定ではない。

## 裁定パッケージ候補

追加候補なし。一般的な昇格 timeout 後の state 回復、gate 取得前の公平性は、既存の段 4 裁定の対象外事項として維持する。

## 総括

**GO（must-fix 0 件、README の nit 1 件残存）。**

A-1／B-2 と B-1 は closed。ファイル変更・git 状態変更・pytest・変異実行は行っていない。fix 子の「33 件通過」は本レビュー自身の実走結果として扱っていない。
