## 総括

**blocker 1 件、nit 2 件。現状の統合は不受理です。**  
静的検査のみで、pytest は実走しておらず緑とは判定していません。

| ID | 種別 (blocker / must-fix / nit) | 所見 | file:line | 事故で成立するか | 成果物影響 (1 行) |
|---|---|---|---|---|---|
| A-01 | blocker | 非帰属赤の存在だけで、元 child の非 0 終了原因まで非帰属とみなしている。checker は `child_rc` を受け取らず log の赤 nodeid だけを判定するため、pytest の完全な summary 出力後に `run_tests.py` が signal・内部異常で終了しても、main 側で同じ nodeid が赤なら receipt が発行される。裁定自身が全 `child_rc != 0` を許しており、land テストは `child_rc=23` の成功を明示的に固定している。 | `s4-adjudication-delta.md:42`, `tools/dev_wave_wait.py:1622`, `tools/dev_wave_wait.py:1651`, `tools/check_acceptance_reds.py:900`, `tools/check_acceptance_reds.py:918`, `tools/dev_wave_land.py:577`, `orchestrator/tests/test_dev_wave_land.py:769` | **はい**。summary 出力後、wrapper 終了前の signal などで成立する。 | テスト以外の理由で落ちた受入に `non-attributable-only` receipt が発行され、その tip が land されうる。 |
| A-02 | nit | 新規外部 file の共通 preflight は `Path.exists()` 相当しか見ず、dangling symlink を拒否しない。log は後段の `open("xb")` で失敗するため誤受理にはならないが、claim 前拒否という裁定を満たさない。receipt path では最終 `rename` が dangling symlink entry を置換できる。 | `tools/dev_wave_wait.py:700`, `tools/dev_wave_wait.py:717`, `tools/dev_wave_wait.py:780`, `tools/dev_wave_wait.py:1451`, `orchestrator/tests/test_dev_wave_wait.py:1760` | **はい**。古い dangling symlink の残存で成立する。 | 誤った外部 path を claim 後まで持ち込み、receipt symlink entry を上書きしうるが、不正な走行の受理には直結しない。 |
| A-03 | nit | checker 起動に実 timeout がない。`effects.run` は checker を bounded stage に分類せず通常の `subprocess.run` を使い、checker 内の単一 node 再走も `timeout=None`。timeout 時に受理へ倒れはしないが、そもそも timeout 終端へ到達しない。 | `tools/dev_wave_wait.py:207`, `tools/dev_wave_wait.py:227`, `tools/dev_wave_wait.py:1352`, `tools/check_acceptance_reds.py:466` | **はい**。再走の hang で成立する。 | receipt が永久に発行されず、wave の land が停止する。 |

A-01 を塞ぐ最小の変更:

- 裁定を「元 child の raw return code が pytest の通常失敗を表す exact `1`、かつ checker が `non-attributable-only`」へ縮小する。
- waiter と land の双方で `child_rc == 1` を要求する。
- 有効な非帰属 log と `child_rc=23`／signal return code の組を拒否するテストへ変更する。現在の `child_rc=23` 成功 fixture は反転する。

A-02 を塞ぐ最小の変更:

- `_external_new_file_preflight` で `path.is_symlink()` 相当も検査し、dangling symlink を claim 前に拒否する。
- log・receipt・checker receipt の各 dangling symlink 回帰テストを追加する。

A-03 を塞ぐ最小の変更:

- checker 専用 timeout を裁定し、process group ごと停止する bounded 起動へする。
- timeout／signal／OSError で receipt が発行されない回帰テストを追加する。

確認できた閉鎖経路は、`status=="green"`、checker rc 1/2、checker receipt の欠損・壊れ・field 不一致、log hash 不一致、3 種の postrun 検査失敗、`tested_main`・`waiter_blob_sha`・`checker_blob_sha` 不一致です。checker は postrun 検査後にだけ起動され、land の `already-landed` 成功経路も receipt 検証後にあります。新しい bypass flag・環境変数・警告化も見当たりません。

同一 Unix user が receipt や log を意図的に書き換える経路は、指定どおり **refuted（脅威モデル外）** とし、real 所見には数えていません。