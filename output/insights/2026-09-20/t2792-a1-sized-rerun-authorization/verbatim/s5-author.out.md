## 実装内容

**実装済み・未実走です。** 指定の 3 ファイルだけに差分を残しました。commit は作成していません。

変更前は、同 study の先行 bench 到達を拒否し、公開先は従来の exact leaf に限定していました。変更後は、一致 record と定数の組合せに限り、attempt-0002 に対する attempt-0001 の反復禁止を解除し、兄弟公開先を受理します。

reader・digest helper・create-only producer・CLI を追加し、submit と v3 materialize に source SHA を配線しました。先行証拠の完全性検査、study 不一致拒否、namespace 再使用拒否、公開先 create-only は維持しています。

## 総括

| 変更ファイル | 追加／削除行 |
|---|---:|
| [driver](orchestrator/campaign/paper_story_a1_paired.py) | +147 / −3 |
| [paired test](orchestrator/tests/test_paper_story_a1_paired.py) | +392 / −3 |
| [job_contract test](orchestrator/tests/test_paper_story_a1_job_contract.py) | +73 / −0 |
| 合計 | +612 / −6 |

新規テストは **22 関数・静的集計 52 ケース**です。新規全関数の「受理／拒否」2 文 docstring、3 ファイルの AST parse、`git diff --check` を確認しました。

**実走結果**

- 指定 2 ファイルの全走を試行しましたが、runner が qstat preflight 失敗で終了しました（rc=16、`child_started=false`）。
- 実走 nodeid 範囲：なし。passed / failed / skipped：集計なし（pytest 未起動）。
- spawn-site、campaign AST pin、plain-runner、P3 namespace/build-authority、official-perf-closure、固定範囲 non-touch の関連テストも runner 経由で試行し、同じ理由で未起動です。
- runner が生成した今回の一時 dispatch 成果物は除去しました。

**M1〜M14 の 1 理由性**

以下は静的判定であり、変異の KILLED 実績ではありません。

| 変異 | 狙うケース | 判定・重複拒否の確認 |
|---|---|---|
| M1 | `rejects_absent_record` | 成立。正常な先行証拠以外に拒否理由なし |
| M2 | `rejects_other_attempt[attempt-0003]` | 成立。filename・current・record は一致 |
| M3 | `rejects_other_attempt[attempt-0002]` | 成立。定数側 attempt は一致 |
| M4 | `rejects_other_study[pilot]` | 成立。caller・record・先行証拠は pilot |
| M5 | `rejects_other_study[sized]` | 成立。定数側 study は一致、先行証拠は caller と一致 |
| M6 | `rejects_other_source` | 成立。有効な別 SHA、digest 再計算済み |
| M7 | `rejects_other_decision[id]` | 成立。他の裁定 field は一致 |
| M8 | `rejects_bad_digest` | 成立。digest の形式・identity は正常 |
| M9 | `preserves_prior_integrity` | 成立。ready の epoch だけ不正 |
| M10 | `rejects_other_prior_reached_bench` | 成立。両先行証拠は正常、追加候補の禁止だけが残る |
| M11 | `rejects_existing_sibling` | 成立。exact 比較・親 dir 検査は通る |
| M12 | `rejects_sibling_without_record` | 成立。兄弟指定の拒否を先に検証 |
| M13 | `authorize_rerun_is_create_only` | 成立。ただし事前検査除去＋上書き化の **2 hunk 必須** |
| M14 | 配線負例 `[source]` | **固定値の具体化が必要**。`"b" * 40` なら成立。head と同じ `"a" * 40` 固定は検出不能 |

**波及の静的確認**

- rear gate の production caller は `_run_submit_v3` 1 箇所。必須 `source_commit` を追加し、既存 test の 3 呼出しも更新しました。
- 公開先 helper の production caller は v3 materialize と非 v3 materialize。v3 のみ context を追加し、非 v3 は従来呼出しを維持しました。
- job_contract は既存 `_v3_submit_cli_fixture` を再利用し、paired test の独立 JSON／証拠 builder を共有しています。
- 配線テストは policy-ready・CCBench・git・durable base・hostname の既存 stub と、qsub 捕捉・既存 qstat visibility fixture を使用します。証明対象は **scheduler 境界までの配線**であり、今回は未実走です。
- job shell 内に `materialize`／`--destination` argv は見つかりませんでした。shell は変更していません。
- anomaly の既存 collector／sidecar consumer test と、destination 判定前の observation 検査は変更していません。

未実施：pytest 全走、関連 meta-test の実走、変異本走、実 durable base 複製での検証。全層の実行成立は未確認です。

直接の指定 pytest コマンドも、PreToolUse の `guard_bash` が「Pegasus ログインノードでの pytest 実行禁止」を理由に拒否しました。拒否を迂回していません。