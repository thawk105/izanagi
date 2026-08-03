実装完了しました。

変更ファイル:

- [compare_verdicts.py](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/g01/compare_verdicts.py) — 723 行
- [run_leg1_dispatch.sh](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/g01/run_leg1_dispatch.sh) — 60 行

追加した合否条件:

- ledger/spec の schema、完全な field 集合、型を検証。
- spec 非空、ID 重複なし、spec ID 列と両 ledger ID 列の順序付き一致。
- `repo_head` の固定 anchor 一致と、実 spec bytes の SHA-256 一致。
- runner/tool/registration/artifact/evidence の記録済み hash を実データから再計算。
- `test_command`、timeout、registration、tool identity、経路非依存 runner identity を比較。
- baseline の `PASSED`、rc=0、failed_nodes=[]、非 timeout、artifact_error=null。
- 全 mutation の spec 射影、期待 field、evidence field、`matches_expectation is true`。
- collection の PASSED/rc=0、正規化 node 列の件数・内容・重複度・順序。
- collection stdout の生 nodeid 列も、件数・内容・重複度・順序で比較。
- 除外 policy 以外の全 ledger field を再帰的に比較。
- 判定条件と除外 field は実際の gate/policy オブジェクトから出力。
- 除外 field を含む全実データ差分を「経路差／非等価性」付きで出力。
- `G01_WORKTREE` override を削除し、worktree を `$ROOT/worktree` に固定。他の検査は維持。

実データでは raw nodeid 列は両 leg とも 5282 件で順序まで一致し、正規化・重複除去後は 5281 件でした。衝突は次の2 nodeidです。

- `...test_closure_path_raw_posix_grammar_rejected_unit[output//x]`
- `...test_closure_path_raw_posix_grammar_rejected_unit[output\\x]`

実データの不一致は全54 leaf fieldです。黙って除外したものはありません。

| field（完全一覧。`i=0,1,2`） | 件数 | 判断・根拠 |
|---|---:|---|
| `procedure.test_command[0]` | 1 | 非等価性。明示的な semantic command が `/usr/bin/python3.10` と `/bin/python3.10` で異なる |
| `runner_identity.command[0]` | 1 | 非等価性。同上。同一 executable bytes の証拠がなく、記録 SHA も異なる |
| `date`, `updated_at` | 2 | 経路差。別 run の時刻 |
| `runner_sha256` | 1 | 経路差。mode 固有 identity を含む派生 hash |
| `runner_identity.{runner_mode,dispatch_entrypoint_path,dispatch_entrypoint_sha256,dispatch_head_blob_sha256,executable_sha256}` | 5 | 経路差。transport/host 固有 identity |
| `procedure.runner_mode` | 1 | 経路差。比較対象 transport 自体 |
| `procedure.collection.{duration_s,runner_sha256}`、同 `artifact.{runner_mode,receipt_path,job_stdout_path,stdout,stdout_sha256}` | 7 | 経路差。collection の transport、所要、時刻入り stdout |
| `baseline.{duration_s,runner_sha256,collection_sha256,test_output_sha256}`、同 `artifact.{runner_mode,receipt_path,job_stdout_path,stdout,stdout_sha256}` | 9 | 経路差。run transport、所要、stdout と派生 hash |
| 各 `mutations[i].{duration_s,runner_sha256,collection_sha256,test_output_sha256}`、同 `artifact.{runner_mode,receipt_path,job_stdout_path,stdout,stdout_sha256}` | 27 | 経路差。各3 mutationの transport、所要、stdout と派生 hash |

したがって、静的照合上は非等価差分2件により NO-GO になる設計です。`executable_sha256` 自体は host 固有の outer Python identity として経路差扱いですが、その除外では semantic な `test_command/command` 差を消しません。

確認結果:

- `compare_verdicts.py`: AST 構文解析成功。ただし比較器自体は未実行。
- `run_leg1_dispatch.sh`: `bash -n` 成功。
- テスト: 未実行・未確認。実走と rc は親の担当。
- repo tracked diff: なし。repo file は一切編集せず、commit もしていません。
- `git status` には untracked の `output/insights/2026-08-03_t357-mutation-transport-smoke/` が現存しますが、今回未編集です。
- 外部 caller は `g01/README.md`。共有入力は read-only の spec/ledger。consumer test と共有 fixture の変更はありません。

## 総括

- spec順、完全schema/type/hash、baseline、mutation evidence、collection順序を fail-closed 化した。
- 除外 policy を比較実装そのものへ接続し、全条件・全除外・全差分を自動列挙する。
- 実データの非等価差は `procedure.test_command[0]` と `runner_identity.command[0]`。
- 残る52差分はすべて経路差として明示し、黙って除外していない。
- この比較器でも実効 inner Python の byte identity は証明できない。
- この3変異を超える一般同値性や cross-node lock・kill/resume の運用安全性は証明できない。