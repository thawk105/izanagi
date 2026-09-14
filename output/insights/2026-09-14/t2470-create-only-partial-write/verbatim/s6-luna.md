## Q-1 — M1〜M9 の生存経路は静的追跡では見つからなかった

**自己判定: refuted／scope 内。** 以下は実走結果ではなく、変異によって赤になる箇所の静的予測。

表中の nodeid はすべて `orchestrator/tests/test_trial_registry.py::` を接頭辞とする。`retry` は `test_attempt_create_only_failure_removes_residue_and_allows_retry` の略。

| 変異 | 赤になる nodeid | 現物の検出箇所と失敗理由 |
|---|---|---|
| M1 撤去削除 | `retry[genesis-write]` | `test_trial_registry.py:8477`。1 byte の残骸が残り、不在 assert が失敗 |
| M2 既存名も撤去 | `test_attempt_registry_genesis_is_closed_before_first_performance_observation` | `test_trial_registry.py:6764`。拒否後の `read_bytes()` が失敗 |
| M2 同上 | `test_attempt_registry_classification_rejection_preserves_receipt_bytes` | `test_trial_registry.py:8653`。既存受領証の消失を検出 |
| M2 同上 | `test_genesis_cli_rejects_second_creation_without_changing_bytes` | `test_trial_registry.py:6851`。既存台帳の消失を検出 |
| M3 親 fsync を撤去対象外へ移動 | `retry[genesis-directory_fsync]`、`retry[classification-directory_fsync]` | `test_trial_registry.py:8477`。親 fsync の例外は伝わっても対象が残る |
| M4 size 条件削除 | `test_attempt_create_only_keeps_file_extended_by_another_writer` | `test_trial_registry.py:8532`。追記済み台帳を消すため bytes 読取りが失敗 |
| M5 inode 条件削除 | `test_attempt_create_only_keeps_replaced_inode_at_same_name` | `test_trial_registry.py:8550` で同じ size を確保し、`:8560` で別 inode の消失を検出 |
| M6 `written > 0` に限定 | `retry[genesis-write_no_progress]`、`retry[classification-write_no_progress]` | `test_trial_registry.py:8454` で 0 を返し、`:8477` で空ファイル残留を検出 |
| M7 `Exception` に限定 | `test_create_only_interrupt_removes_residue_and_allows_retry` | `test_trial_registry.py:8611`。KeyboardInterrupt 自体の捕捉後、残骸の不在確認が失敗 |
| M8 cleanup 例外を再送出 | `test_create_only_unlink_failure_preserves_original_error` | `test_trial_registry.py:8586`。`__cause__` が cleanup の OSError に置き換わる |
| M9 裸の raise 削除 | `retry[genesis-write]` | `test_trial_registry.py:8469`。writer が正常 return し、`pytest.raises` が失敗 |

M4 は別 fd の追記を実際に write/fsync する構造であり、期待 bytes の生成だけで済ませていない（`test_trial_registry.py:8512`、`:8517`、`:8520`）。M5 は元 fd を保持したまま同名ファイルを再作成し、inode 不一致と size 一致を両方確認する（`:8547`〜`:8550`）。

成果物への影響: これらの変異を見逃すと、試行台帳・分類受領証の消失、再試行の拒否、失敗の成功扱いを許すが、上記の観測点がそれぞれ阻止する。

受理の含意: 残骸を撤去した後、同一入力による作成成功を許す。
拒否の含意: 既存完成物の消失や書込み失敗の握り潰しはテストが拒否する。
通る正例: `retry[classification-write]` は注入解除後、受領証の digest と台帳の classification 行まで確認する（`:8478`〜`:8488`）。

## Q-2 — 注入の取り違え・恒真 assert による偽緑は成立しなかった

**自己判定: refuted／scope 内。**

追加 assert を役割ごとに追った結果は次のとおり。

| 箇所（`test_trial_registry.py`） | 攻撃結果 |
|---|---|
| `:8451`、`:8463` | fd と対象 inode を照合。別 I/O を捕まえると AssertionError になり、期待する TrialRegistryError では通らない |
| `:8471` | write は 2 回、進捗なし・file fsync は 1 回、directory fsync は 2 回を要求。注入未到達を通さない |
| `:8473`、`:8474`、`:8476` | 0 返却では writer が作る OSError の型・本文、それ以外では注入例外そのものを要求 |
| `:8477`〜`:8488` | 不在だけでなく、再試行後の改行・parse・digest・分類行まで観測 |
| `:8501`、`:8514`、`:8518` | 注入先・別 fd・追記進捗の前提確認。これら単独は cleanup 変異を殺さないが、最終検証は `:8532`、`:8533` に別途ある |
| `:8530`、`:8531` | 元例外の同一性と注入 1 回を要求 |
| `:8549`、`:8550` | 別 inode／同じ size という M5 の成立条件を確認 |
| `:8558`〜`:8560` | 元例外・注入回数・差し替え先 bytes を検証 |
| `:8571`、`:8575`、`:8576` | write と unlink の対象を確認 |
| `:8585`〜`:8587` | cleanup 到達・元例外保存・空ファイル残留を検証 |
| `:8599`、`:8609`〜`:8613` | 注入対象・中断例外の同一性・2 回の write・撤去・再試行成功を検証 |
| `:8629`、`:8640`〜`:8642` | fsync 対象、返却 path、完全 bytes、順序を検証 |
| `:8653`、`:6764` | 拒否後の既存 bytes を検証 |

`R.os` は共有 module なので patch は局所的な module 隔離ではない。ただし fixture 作成と reservation は patch 開始前に終わる（`:8444`、`:8448`、`:8421`、`:8422`）。genesis の前処理と親ディレクトリ作成には `os.write/fsync` がなく、classification の台帳追記は create-only writer より後にある（`trial_registry.py:1108`、`:2545`、`:3303`、`:3337`）。

追記注入内の fsync は保存した本物を呼ぶため再帰しない（`test_trial_registry.py:8520`）。assert 失敗を成功へ変える捕捉もない。pytest の通常の結果報告・fixture teardown より前に `monkeypatch.context()` が終了する。外部 plugin の任意の並行 I/O までは静的に保証しない。

成果物への影響: 狙っていない I/O の失敗を cleanup の成功証拠にする経路は確認できなかった。

受理の含意: 対象 writer に注入が到達し、期待した後状態を満たすケースを通す。
拒否の含意: 注入未到達、別 fd、例外原因の置換は通さない。
通る正例: `retry[genesis-directory_fsync]` は file fsync を実行してから親 fsync を失敗させる（`:8460`〜`:8471`）。

## Q-3 — 撤去後の再試行欠落・揮発期待値は見つからなかった

**自己判定: refuted／scope 内。**

8 個の `retry` nodeid は全件、patch 解除後に同じ closure の `invoke()` を再実行する（`test_trial_registry.py:8417`、`:8433`、`:8478`）。中断テストも同様（`:8612`）。**撤去成功を扱う正例で、再試行成功まで到達しない nodeid はない。**

追記済み・別 inode・unlink 失敗のテストは、意図的にファイルを残す別条件の検査であり、「撤去後の再試行成功」の代用には数えられない。

固定時刻、`pid=101`、`"a" * 40` 等は合成入力であり、現在時刻・実 pid・現在の HEAD の期待値ではない（`:8427`、`:8507`〜`:8509`）。path と受領証 digest は fixture から導出する（`:8429`〜`:8431`）。環境依存値の焼き込みによる赤は予言できなかった。

成果物への影響: 同一受領証 path が失敗後も塞がる回帰は、再試行の実呼出しで検出される。

受理の含意: 同一 capability・同一 kwargs による分類の再試行成功を許す。
拒否の含意: ファイルだけ消して、その後の分類処理を壊す実装も拒否する。
通る正例: `retry[classification-file_fsync]` は再試行後の台帳イベント列まで確認する（`:8487`）。

## Q-4 — 既存テスト弱化とメタテスト破壊は確認できなかった

**自己判定: refuted／scope 内。**

指定 baseline と AST の名前集合を照合した結果、**既存 202 名の消失 0、改名 0、新規 7 関数**だった。parametrize 展開では新規 14 nodeid になる。

差分から変更前の本文をメモリ上で復元して AST 比較したところ、既存テストの変更は `test_attempt_registry_genesis_is_closed_before_first_performance_observation` だけ。変更内容は snapshot 取得と拒否後の一致 assert の追加である（`test_trial_registry.py:6754`、`:6764`）。反転・緩和・skip・削除はなかった。CLI 負例も保持されている（`:6835`）。

新規 test file は差分にない。既存 harness はファイル全体を `pytest.main` に渡すため、新規関数も対象になる（`:8656`〜`:8660`）。メタテストの判定はファイル単位であり、関数名の固定列挙ではない（`test_plain_runner_coverage.py:35`、`:60`）。

新規 14 nodeid の所要台帳登録は **0 件**。ただし未登録は scheduler で unknown cost として扱われ、拒否にはならない（`conftest.py:1661`、`:1742`）。台帳メタテストも未登録を含む coverage で exit 0 を期待する（`test_update_acceptance_duration_ledger.py:441`〜`:454`）。全 collection との完全一致を要求する変更ではない。

成果物への影響: 既存拒否条件の弱化は見つからず、未登録所要が直接変えるのは実行順の見積りである。

受理の含意: 所要未計測の新規 nodeid も実行対象に残る。
拒否の含意: 未計測を理由に新規テストが自動除外される構造ではない。
通る正例: 新規 `retry[genesis-write_no_progress]` も既存ファイルの harness から収集される。

## Q-5 — 14 file は変更ファイルの全参照元を網羅していない

**自己判定: real、ただし nit／scope 内。must-fix にはしない。**

焦点走外に次の参照元がある。

| ファイル | 現物の参照 |
|---|---|
| `test_reflux_formal_consumer.py` | `:2301`、`:2305` で `trial_registry.py` を読み、`:2312` から AST を走査 |
| `test_ccbench_spawn_sites.py` | `:284` に `trial_registry._git` の spawn inventory |
| `test_claude_transport.py` | `:1367` で `A.trial_registry.launch_admission_record` を呼ぶ |

ただし、変更 symbol `_write_create_only` の直接 caller は `trial_registry.py:2545` と `:3303` の 2 箇所。外側の入口は同ファイルの CLI（`:6574`）、分類の別名（`:3351`）、`p3_autonomous_workload_trial.py:4876` へ追える。対応する writer・CLI・runner のテストは焦点集合に含まれる。

外れた参照元について、今回の差分で成果物の値・受理集合・参照が変わる経路は立証できない。特に formal consumer の AST 検査は `aborted=False`／`OriginSealed` を検査しており、追加 cleanup 呼出しは該当しない（`test_reflux_formal_consumer.py:2318`、`:2334`）。

成果物への影響: 未立証。したがって「変更ファイルの全 consumer を網羅」という主張の訂正事項に留める。

受理の含意: 14 file を変更 symbol の焦点検証として扱うことは、この参照漏れだけでは否定されない。
拒否の含意: 14 file で変更ファイルの全参照元を検査したという主張は成立しない。
通る正例: 正常な genesis 作成は `test_attempt_registry_core_equivalence.py:392` から変更 writer に到達する。

## Q-6 — P1／P2 は赤になっても構造 pin のまま扱う必要がある

**自己判定: 混入の疑いは refuted／scope 内。集計実施の確認は未了。**

P1 は `test_create_only_success_preserves_bytes_and_fsync_order` の順序 assert で赤になる（`test_trial_registry.py:8642`）。directory-fsync 注入側の回数 assert（`:8471`）も赤になり得る。

P2 は `fail_unlink(name, *, dir_fd)` の必須引数契約により、絶対 path だけの呼出しでは TypeError になり得る（`:8574`）。これは同名ファイル消失を観測した検出ではなく、呼出し形を固定する検出である。

成果物への影響: この赤を M1〜M9 と同じ受理集合変化の証拠に数えると、変異検出実績を過大に報告する。

受理の含意: bytes と fsync 順序を保つ成功経路を構造検査が通す。
拒否の含意: 順序・unlink 呼出し形の変更による赤だけでは、成果物の誤受理防止を証明しない。
通る正例: 1 byte ずつ書いても完全な payload と `[file, directory]` が残るケース（`:8624`〜`:8642`）。

## 総括

**must-fix は 0 件。M1〜M9 の SURVIVED は予言できなかった。** 各変異の検出先は現物から特定したが、KILLED を実測したとは報告しない。

残る指摘は、14 file を「変更ファイルの全 consumer」と呼べない点の nit。新規 14 nodeid は所要未登録だが、それによる検査失敗・実行除外は確認できなかった。

静的検査のみ実施。pytest・変異走・編集・commit は行っていない。