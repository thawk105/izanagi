## 総括

[receipt_reuse_replay.py:115](/work/1/SFC/tanab/izanagi/.codex/worktrees/pcd-unit-probe/build/probe/receipt_reuse_replay.py:115) の許可集合に `ls-files` / `ls-tree` を追加しました。変更前との bytes 比較で、**この1行以外の変更なし**を確認しました。直接呼出し経路の追加・bug fix はありません。直前の旧コメントも変更していません。

指定コマンドは **rc=0** で完了しました。[結果 JSONL](/work/1/SFC/tanab/izanagi/.codex/worktrees/pcd-unit-probe/build/probe/out/reuse-replay-self-2.jsonl) と [stdout 全文](/work/1/SFC/tanab/izanagi/.codex/worktrees/pcd-unit-probe/build/probe/out/reuse-replay-self-2.stdout.txt) を保存済みです。

| replay | M | R |
|---|---:|---:|
| `success` | 47 | 4 |
| `未判定: bindings 不一致` | 1 | 25 |
| `未判定: 候補なし` | 0 | 8 |
| 合計 | 48 | 37 |

`fail:` は0件。候補単位の prefix 失敗も0件。registry 世代差による未判定は **M=0 / R=0件**で、現行 manifest digest は `6ad7b460d863`。不一致受領証側の digest は該当なしです。

所有外への波及なし。作業前後の tracked status は空で、**tracked file 変更0**。共有 store・親 job directory への書込み、commit、既存テスト実行はありません。依頼作業の未完了はありません。結果は再利用可能性の事後推定であり、実際の再利用実績ではありません。並走・prune・上書き・当時の実行時失敗については前巡の制限が残ります。

P-2 集計 stdout 全文：

```text
REUSE SUMMARY rows=85 excluded_ledger_errors=0
再利用可能性の事後推定であり実績ではない。mtime順・残存集合・現行checker条件に限定。
population	verdict	cause	n
M	候補あり (bindings 不一致)	参考区分: 旧形 attributes fingerprint の候補集合変化	1
M	候補あり (replay 成功)		47
R	候補あり (bindings 不一致)	attributes 差 (新形、原因未特定)	3
R	候補あり (bindings 不一致)	参考区分: 旧形 attributes fingerprint の候補集合変化	22
R	候補あり (replay 成功)		4
R	候補なし	checker sha 変更	6
R	候補なし	partition 跨ぎ	2
PARTITION SUMMARY: population	partition	verdict	cause	n
M	4608b761416c	候補あり (replay 成功)		10
M	53e9a718e601	候補あり (bindings 不一致)	参考区分: 旧形 attributes fingerprint の候補集合変化	1
M	c508d1de93e1	候補あり (replay 成功)		37
R	18d19753b740	候補なし	checker sha 変更	1
R	2a6c7dae048c	候補あり (bindings 不一致)	attributes 差 (新形、原因未特定)	3
R	2a6c7dae048c	候補あり (replay 成功)		2
R	2a6c7dae048c	候補なし	checker sha 変更	1
R	4608b761416c	候補なし	partition 跨ぎ	1
R	53e9a718e601	候補あり (bindings 不一致)	参考区分: 旧形 attributes fingerprint の候補集合変化	8
R	53e9a718e601	候補あり (replay 成功)		1
R	5f183033771c	候補あり (bindings 不一致)	参考区分: 旧形 attributes fingerprint の候補集合変化	13
R	7669d7b2ef9a	候補なし	partition 跨ぎ	1
R	8c683754078a	候補あり (bindings 不一致)	参考区分: 旧形 attributes fingerprint の候補集合変化	1
R	ae7ec43852ce	候補なし	checker sha 変更	1
R	c508d1de93e1	候補なし	checker sha 変更	1
R	cceb9da4d834	候補なし	checker sha 変更	1
R	cfdf571bda61	候補あり (replay 成功)		1
R	cfdf571bda61	候補なし	checker sha 変更	1
COLD/UNDETERMINED ROWS: mtime partition tip checker population verdict cause comparison diff_fields compound
2026-09-20T21:05:52.000000000+09:00 5f183033771c da0e7127cdb1 7c02fb2d5fec R 候補あり (bindings 不一致) | 参考区分: 旧形 attributes fingerprint の候補集合変化 | 5f183033771c/a79e72553ec6 | attributes | compound=False
2026-09-20T21:14:47.000000000+09:00 5f183033771c ddd3fb344537 7c02fb2d5fec R 候補あり (bindings 不一致) | 参考区分: 旧形 attributes fingerprint の候補集合変化 | 5f183033771c/da0e7127cdb1 | attributes | compound=False
2026-09-20T21:31:54.000000000+09:00 8c683754078a 8b58dce4a070 7c02fb2d5fec R 候補あり (bindings 不一致) | 参考区分: 旧形 attributes fingerprint の候補集合変化 | 8c683754078a/716004faa224 | attributes | compound=False
2026-09-20T21:32:02.000000000+09:00 5f183033771c 25334c9b7bf5 7c02fb2d5fec R 候補あり (bindings 不一致) | 参考区分: 旧形 attributes fingerprint の候補集合変化 | 5f183033771c/ddd3fb344537 | attributes | compound=False
2026-09-20T21:44:12.000000000+09:00 5f183033771c 26b7a35e46ce 7c02fb2d5fec R 候補あり (bindings 不一致) | 参考区分: 旧形 attributes fingerprint の候補集合変化 | 5f183033771c/25334c9b7bf5 | attributes | compound=False
2026-09-20T21:46:19.000000000+09:00 cceb9da4d834 4c532aa0b400 1acbb4961ca6 R 候補なし | checker sha 変更 | 5f183033771c/a79e72553ec6 | attributes,environment.checker,environment.config,environment.inherited.GIT_ATTR_NOSYSTEM,environment.inherited.GIT_CONFIG_GLOBAL,environment.inherited.GIT_CONFIG_SYSTEM,environment.inherited.GIT_EDITOR,environment.inherited.GIT_NO_LAZY_FETCH,environment.inherited.GIT_NO_REPLACE_OBJECTS,environment.inherited.GIT_OPTIONAL_LOCKS,environment.inherited.GIT_TERMINAL_PROMPT,environment.inherited.LC_ALL,environment.schema | compound=True
2026-09-20T21:51:57.000000000+09:00 5f183033771c b3082348cc7c 7c02fb2d5fec R 候補あり (bindings 不一致) | 参考区分: 旧形 attributes fingerprint の候補集合変化 | 5f183033771c/26b7a35e46ce | attributes | compound=False
2026-09-20T21:52:06.000000000+09:00 ae7ec43852ce aa81e3c64445 89a60a884088 R 候補なし | checker sha 変更 | 5f183033771c/a79e72553ec6 | environment.checker,environment.config,environment.inherited.GIT_ATTR_NOSYSTEM,environment.inherited.GIT_CONFIG_GLOBAL,environment.inherited.GIT_CONFIG_SYSTEM,environment.inherited.GIT_EDITOR,environment.inherited.GIT_NO_LAZY_FETCH,environment.inherited.GIT_NO_REPLACE_OBJECTS,environment.inherited.GIT_OPTIONAL_LOCKS,environment.inherited.GIT_TERMINAL_PROMPT,environment.inherited.LC_ALL | compound=True
2026-09-20T21:53:50.000000000+09:00 53e9a718e601 47719ab411fa 7c02fb2d5fec R 候補あり (bindings 不一致) | 参考区分: 旧形 attributes fingerprint の候補集合変化 | 53e9a718e601/482f19b88dbb | attributes | compound=False
2026-09-20T21:59:35.000000000+09:00 5f183033771c a49941b437e7 7c02fb2d5fec R 候補あり (bindings 不一致) | 参考区分: 旧形 attributes fingerprint の候補集合変化 | 5f183033771c/b3082348cc7c | attributes | compound=False
2026-09-20T22:06:39.000000000+09:00 53e9a718e601 0ee3e5075ea6 7c02fb2d5fec R 候補あり (bindings 不一致) | 参考区分: 旧形 attributes fingerprint の候補集合変化 | 53e9a718e601/482f19b88dbb | attributes | compound=False
2026-09-20T22:07:27.000000000+09:00 2a6c7dae048c 62ed683aba12 65476dafe9c0 R 候補なし | checker sha 変更 | ae7ec43852ce/aa81e3c64445 | environment.checker | compound=False
2026-09-20T22:07:55.000000000+09:00 53e9a718e601 f82b1e30f4e5 7c02fb2d5fec R 候補あり (bindings 不一致) | 参考区分: 旧形 attributes fingerprint の候補集合変化 | 53e9a718e601/0ee3e5075ea6 | attributes | compound=False
2026-09-20T22:09:45.000000000+09:00 5f183033771c e2d6b88005b0 7c02fb2d5fec R 候補あり (bindings 不一致) | 参考区分: 旧形 attributes fingerprint の候補集合変化 | 5f183033771c/a49941b437e7 | attributes | compound=False
2026-09-20T22:12:25.000000000+09:00 18d19753b740 4c9c8d480e9f 65476dafe9c0 R 候補なし | checker sha 変更 | 5f183033771c/a79e72553ec6 | environment.checker,environment.inherited.GIT_ATTR_NOSYSTEM,environment.inherited.GIT_CONFIG_GLOBAL,environment.inherited.GIT_CONFIG_SYSTEM,environment.inherited.GIT_NO_LAZY_FETCH,environment.inherited.GIT_NO_REPLACE_OBJECTS,environment.inherited.GIT_OPTIONAL_LOCKS,environment.inherited.GIT_TERMINAL_PROMPT,environment.inherited.LANG,environment.inherited.LC_ALL,environment.inherited.LC_CTYPE | compound=True
2026-09-20T22:14:35.000000000+09:00 53e9a718e601 b7dc82bbff75 7c02fb2d5fec R 候補あり (bindings 不一致) | 参考区分: 旧形 attributes fingerprint の候補集合変化 | 53e9a718e601/482f19b88dbb | attributes | compound=False
2026-09-20T22:14:47.000000000+09:00 5f183033771c 82705b75480a 7c02fb2d5fec R 候補あり (bindings 不一致) | 参考区分: 旧形 attributes fingerprint の候補集合変化 | 5f183033771c/e2d6b88005b0 | attributes | compound=False
2026-09-20T22:15:47.000000000+09:00 53e9a718e601 4242a6ebaa00 7c02fb2d5fec R 候補あり (bindings 不一致) | 参考区分: 旧形 attributes fingerprint の候補集合変化 | 53e9a718e601/47719ab411fa | attributes | compound=False
2026-09-20T22:32:57.000000000+09:00 53e9a718e601 74163cf5952f 7c02fb2d5fec R 候補あり (bindings 不一致) | 参考区分: 旧形 attributes fingerprint の候補集合変化 | 53e9a718e601/47719ab411fa | attributes | compound=False
2026-09-20T22:38:37.000000000+09:00 5f183033771c e4dca4255d2f 7c02fb2d5fec R 候補あり (bindings 不一致) | 参考区分: 旧形 attributes fingerprint の候補集合変化 | 5f183033771c/82705b75480a | attributes | compound=False
2026-09-20T22:39:54.000000000+09:00 5f183033771c bc66f8b4c6e1 7c02fb2d5fec R 候補あり (bindings 不一致) | 参考区分: 旧形 attributes fingerprint の候補集合変化 | 5f183033771c/82705b75480a | attributes | compound=False
2026-09-20T22:45:21.000000000+09:00 5f183033771c 56e00b2f379c 7c02fb2d5fec R 候補あり (bindings 不一致) | 参考区分: 旧形 attributes fingerprint の候補集合変化 | 5f183033771c/bc66f8b4c6e1 | attributes | compound=False
2026-09-20T22:51:30.000000000+09:00 5f183033771c e55255ac90de 7c02fb2d5fec R 候補あり (bindings 不一致) | 参考区分: 旧形 attributes fingerprint の候補集合変化 | 5f183033771c/56e00b2f379c | attributes | compound=False
2026-09-20T22:54:10.000000000+09:00 53e9a718e601 cf1f1370ad2d 7c02fb2d5fec R 候補あり (bindings 不一致) | 参考区分: 旧形 attributes fingerprint の候補集合変化 | 53e9a718e601/482f19b88dbb | attributes | compound=False
2026-09-20T22:58:04.000000000+09:00 53e9a718e601 a5fc308b9dde 7c02fb2d5fec R 候補あり (bindings 不一致) | 参考区分: 旧形 attributes fingerprint の候補集合変化 | 53e9a718e601/74163cf5952f | attributes | compound=False
2026-09-20T23:03:17.000000000+09:00 cfdf571bda61 47fbfd58cf6a 2b72e1d543cd R 候補なし | checker sha 変更 | 5f183033771c/e55255ac90de | attributes,environment.checker,environment.config,environment.inherited.GIT_ATTR_NOSYSTEM,environment.inherited.GIT_CONFIG_GLOBAL,environment.inherited.GIT_CONFIG_SYSTEM,environment.inherited.GIT_EDITOR,environment.inherited.GIT_NO_LAZY_FETCH,environment.inherited.GIT_NO_REPLACE_OBJECTS,environment.inherited.GIT_OPTIONAL_LOCKS,environment.inherited.GIT_TERMINAL_PROMPT,environment.inherited.LC_ALL | compound=True
2026-09-20T23:09:33.000000000+09:00 5f183033771c 0fef5ed1f2be 7c02fb2d5fec R 候補あり (bindings 不一致) | 参考区分: 旧形 attributes fingerprint の候補集合変化 | 5f183033771c/e55255ac90de | attributes | compound=False
2026-09-20T23:12:12.000000000+09:00 2a6c7dae048c 7cac2d8c7d07 65476dafe9c0 R 候補あり (bindings 不一致) | attributes 差 (新形、原因未特定) | 2a6c7dae048c/62ed683aba12 | attributes | compound=False
2026-09-20T23:17:15.000000000+09:00 2a6c7dae048c b8fa2c57629e 65476dafe9c0 R 候補あり (bindings 不一致) | attributes 差 (新形、原因未特定) | 2a6c7dae048c/7cac2d8c7d07 | attributes | compound=False
2026-09-20T23:27:48.000000000+09:00 7669d7b2ef9a 1e5fb5705d18 65476dafe9c0 R 候補なし | partition 跨ぎ | 2a6c7dae048c/1e5fb5705d18 | environment.config,environment.inherited.GIT_ATTR_NOSYSTEM,environment.inherited.GIT_CONFIG_GLOBAL,environment.inherited.GIT_CONFIG_SYSTEM,environment.inherited.GIT_EDITOR,environment.inherited.GIT_NO_LAZY_FETCH,environment.inherited.GIT_NO_REPLACE_OBJECTS,environment.inherited.GIT_OPTIONAL_LOCKS,environment.inherited.GIT_TERMINAL_PROMPT,environment.inherited.LC_ALL | compound=True
2026-09-20T23:36:39.000000000+09:00 2a6c7dae048c 43c32588b3e6 65476dafe9c0 R 候補あり (bindings 不一致) | attributes 差 (新形、原因未特定) | 2a6c7dae048c/1e5fb5705d18 | attributes | compound=False
2026-09-20T23:45:43.000000000+09:00 c508d1de93e1 65966f4d8a92 e69764c1d885 R 候補なし | checker sha 変更 | cfdf571bda61/ddae70ed1296 | environment.checker | compound=False
2026-09-21T00:08:30.000000000+09:00 4608b761416c 65966f4d8a92 e69764c1d885 R 候補なし | partition 跨ぎ | c508d1de93e1/65966f4d8a92 | environment.config,environment.inherited.GIT_ATTR_NOSYSTEM,environment.inherited.GIT_CONFIG_GLOBAL,environment.inherited.GIT_CONFIG_SYSTEM,environment.inherited.GIT_EDITOR,environment.inherited.GIT_NO_LAZY_FETCH,environment.inherited.GIT_NO_REPLACE_OBJECTS,environment.inherited.GIT_OPTIONAL_LOCKS,environment.inherited.GIT_TERMINAL_PROMPT,environment.inherited.LC_ALL | compound=True
2026-09-21T04:11:50.000000000+09:00 53e9a718e601 a6ac2c54c2c2 7c02fb2d5fec M 候補あり (bindings 不一致) | 参考区分: 旧形 attributes fingerprint の候補集合変化 | 53e9a718e601/482f19b88dbb | attributes | compound=False
```