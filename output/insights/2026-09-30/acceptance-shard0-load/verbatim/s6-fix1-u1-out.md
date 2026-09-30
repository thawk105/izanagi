[conftest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/as0-u1/orchestrator/tests/conftest.py:2562) と [test_s8b_oracle_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/as0-u1/orchestrator/tests/test_s8b_oracle_driver.py:1244) だけを修正しました。commit はしていません。

構築 thread を daemon にし、finish と起動失敗時の join に共通の合計上限を適用しました。生存 thread があれば controller の lifetime lock と session 木を保持して例外を返します。T1 には別参加者からの 2 key の hit、T6 には timeout 前後の木と lock の検査を追加しました。prewarm 系 test は conftest が import する module の builder も差し替えます。起動失敗の完了済み・生存中の両例も test に追加しました。

| 場面 | 変更前 | 変更後 |
|---|---|---|
| 通常終了 | join 後に close、木を撤去 | 同じ |
| builder 例外 | 回収後に close | 同じ |
| join 超過 | close で構築中の木を撤去しうる | close せず lock と木を保持して例外 |
| 2 本目の起動失敗 | 先行 thread を無期限 join | 上限付き join。生存中は保持、完了済みなら close し、元の起動例外を返す |

**検査は実装済み・未実走です。** `tools/run_tests.py` で T1〜T7 の各 nodeid を指定した走行と、`test_s8b_oracle_driver.py -k "t080_shared_base or t080_visible_output"` を試みました。いずれも `qstat -Q preflight rc=1`、`rc=16` で子プロセスが起動せず、実走できた nodeid はありません。新設した起動失敗 test も後者の選択対象ですが未実走です。依頼された `importlib.import_module(...) is sys.modules[__name__]` の**実走での真偽も未確認**です。静的検査では AST parse と `git diff --check` が通りました。

E4 の変異は静的には、M1→T1、M2→T2、M3→T3、M4→T4、M6→T7 と既存の複製独立性 test が赤になる見込みです。M2 は conftest 側 builder の呼出しを数えるようになりました。M5 は T5 などが赤になる見込みですが、非選択時には可視 job 不在の例外もあり、単一理由性と正確な赤 node 集合は probe なしには確定できません。M3・M6 の集合も実走確認が必要です。

## 総括

裁定 A1・B1・A2・A3・A4 と、焦点走で示された builder 差し替え先の問題に対応しました。
テスト runner の dispatch 障害により、修正後の合否と module identity は未確認です。