## 変更 file と要点

所有 path に IR parser、方策専用 driver、固定 coder spec、対応 test を追加しました。auditor の違反型上限は呼出し側の keyword 引数とし、既定値 21 を維持しました。新 driver だけが 26 を指定します。proposal 契約 `policy-cpp` / `policy-ir`、reject subtype `policy-grammar` / `policy-compile`、coder build entrypoint も追加しました。commit と docs 編集は行っていません。

## interface の実装

IR は全 object に `kind` を持つ閉じた JSON 形です。例は `{"kind":"Const","type":"u32","value":0}`。`parse_policy_ir` は key・型・値域を検査してから `validate_ir` を呼びます。

driver は両形を本文へ変換した後、共有 `quarantine(write=False)`、構文検査、単独 TU、auditor digest と deny-only veto の順に通します。書込み後の diff digest も再照合します。coder 入力は固定 projection path と当該 layout の履歴から作り、justification を射影しません。固定 `policy_spec` は [silo_function_policy_coder_spec.md](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865-unit-core/orchestrator/campaign/silo_function_policy_coder_spec.md) です。

## test の実走

`python3 tools/run_tests.py -q -p no:cacheprovider <所有 test・制約 meta-test>` は qstat preflight 失敗（rc=16）で子テストが起動しませんでした。直接 pytest も PreToolUse hook に拒否されました。**pytest は 0 件実走で、passed / failed 件数は報告できません。**

`py_compile`、`git diff --check`、`tools/check_codex_agents.py`、`tools/check_docs.py` は通りました。軽量実行では最小 IR の parse、coder 入力の key 集合、auditor の 21/26 境界、差分 fixture の共有 quarantine 通過を確認しました。

## 変異の事前登録

M-E1〜M-E11 と P-E1 に対応する fixture を test に置きました。構文だけの拒否には `++`、単独 TU だけの拒否には未使用局所変数を候補とし、前者の grammar 拒否と後者の grammar 受理は確認済みです。**実 compiler による両 fixture の確認と、各変異が単一理由で期待 node を落とす確認は未実走**です。P-E1 は裁定どおり diagnostic pin として扱います。

## 所有外への波及と、変えなかった既存の受理・拒否挙動

所有外の主な consumer は sort・trigger・backoff driver、`p3_autonomous_workload_trial.py`、critic の汎用 diff rejection 経路、build authority と探索 namespace の制約 test です。`AuditorVerdict` の新引数は `InitVar` とし、既存の `vars` / `asdict` 出力形に field を増やしていません。

共有 `p3_s4_loop.quarantine()`、既存 3 契約、既存 subtype、auditor の既定上限 21 は変更していません。したがって既存 3 軸と段階 C/D の受理・拒否経路を変えない実装ですが、その回帰 test は未実走です。

## 総括

実装と静的確認は完了しました。pytest と実 compiler を含む受入確認は、Pegasus dispatch 障害と直接実行 hook の拒否により残っています。