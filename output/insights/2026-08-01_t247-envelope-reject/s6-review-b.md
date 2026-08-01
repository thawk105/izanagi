NO-GO。登録済み変異は静的にはすべて KILL 可能ですが、受理集合の穴と共有 fixture の忠実度低下が各 1 件あります。pytest は実行していません。

## 所見

1 / **must-fix** / [t126_qualification.sh:456](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/tools/pegasus/t126_qualification.sh:456)、[submit_t126_qualification.sh:216](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/tools/pegasus/submit_t126_qualification.sh:216)、[test_t126_pegasus_tools.py:1237](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/orchestrator/tests/test_t126_pegasus_tools.py:1237)

予約 policy の整数型が凍結されていません。Python では `900.0 == 900` なので、job/submit の `!=` 比較と静的 assert は、`member_cap_s=900.0`、`round_gap_s=1800.0`、`attestation_cap_s=600.0`、`finalize_reserve_s=600.0` をすべて受理します。これらは Bash mapping assert の出力対象でもありません。新設負例も整数 drift しか試していません。

- 実証: ローカル Python で全比較と合計が `True` になることを確認。production subprocess は未実証。
- 成果物影響: 承認外の float 型 policy により `reservation_policy_sha256`・source-tree・series identity の参照が変わっても、submit/job の受理集合には残ります。
- scope: **内**。8 key の個別凍結そのものです。
- 必要修正: 両 embedded Python で `type(value) is int` を要求し、float 単独負例を production subprocess テストへ追加する必要があります。

2 / **must-fix** / [test_t126_pegasus_tools.py:826](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/orchestrator/tests/test_t126_pegasus_tools.py:826)

`_attempt` が `shutil.copy2` を無条件に `read_text` → `write_text` へ変えたため、scratch 置換を使わない既存 caller も含め、job script の executable bit を失います。新規 path と現在の umask `0022` では `0644` になり、production の tracked mode `100755` と不一致です。行 831 の「置換数 1」assert は本文だけを数え、mode drift を検出しません。

- 実証: source/index mode `100755` と umask `0022` は確認済み。fixture commit の実生成は未実証。
- 成果物影響: 62 個の既存 `_attempt` caller が production と異なる source-tree mode/series identity を検証し、mode 依存の job 起動失敗を偽緑にできます。
- scope: **内**。新設 job subprocess fixture の変更です。
- 必要修正: override なしでは従来どおり `copy2`、override ありでも source mode を保存し、fixture の mode assert を置く必要があります。

3 / **nit** / [t126_qualification.sh:475](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/tools/pegasus/t126_qualification.sh:475)、[submit_t126_qualification.sh:232](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/tools/pegasus/submit_t126_qualification.sh:232)

command substitution は末尾 newline をすべて除去するため、producer が `3 値 + 空行` を返しても here-string 復元後は配列長 3 となり、長さ guard を通ります。ログインノード Bash 5.1 の microprobe で `rows=3` を実証しました。

- 成果物影響: 現 producer の値は変わらず、中間出力 shape の受理だけが広がるため nit です。
- scope: **内**。
- 計算ノード上の Bash 挙動は未実証です。

## Bash・実行経路の確認

- `if ! OUT=$(python ...); then exit 2; fi` は producer の非 0 を捕捉します。`!` 文脈では ERR trap は発火しませんが、job の `driver_rc` はこの位置では既定値 2 で、明示的な `exit 2` が EXIT trap に渡ります。
- command substitution の出力は親 shell の変数へ入り、here-string の `readarray` も親 shell で実行されます。subshell scope の取り違えはありません。
- producer が完全な 3 行を出して rc=73 を返す microprobeでは、3 行を捕捉したまま失敗 branch に入りました。
- heredoc の閉じ方と quoting は、両 script 個別の `bash -n` で rc=0。これは意味論の緑を意味しません。
- 新しい明示 temp file はありません。現ログインノードでは `noclobber` 有効・不正な `TMPDIR` でも小さい here-string は成功しましたが、計算ノードでは未実証です。
- submit の通常 exit は既存 EXIT trap が submission stage を削除します。SIGKILL 残骸と job の `$SCR_ROOT` 非 cleanup は既存挙動で、この差分による新規 blocker とは判定しません。

## テスト到達性・回帰

新設テストは production script/function を実行しています。文字列 assert やテスト側再実装だけで KILL を主張してはいません。

- Submit 負例は production submitter を通り、診断に加えて scheduler call file が存在しないことを確認します。
- Job 正例は mapping assert より後の `git ... rev-parse HEAD` を wrapper で停止させ、marker と固有診断の両方を要求します。前段 guard での rc=2 を正例扱いしていません。
- Late-failure は reservation 呼出し 1 回・注入 1 回を assert し、その後の手動 2 回目では実 Python への再委譲を確認します。
- scratch 文字列の置換数 1 assert は存在します。ただし所見 2 の mode drift は対象外です。
- protocol 負例は production `validate_protocol` を直接呼び、旧 positivity・合計・Wmax 条件を保つ vector です。

既存 caller の静的走査結果は `_attempt` 62、`_submit_fixture` 21、`_run_submit` 30、`_run_bound_job_terminal` 7。optional 引数による呼出し互換性の破壊はありません。直接赤くなる既存テストは静的には 0 件と予告しますが、`_attempt` の全 caller は所見 2 の偽緑側へ変わります。script hash は動的計算で、既存文字列 anchor と FR3 meta-test の対象名集合にも直接衝突しません。

## C 節変異の静的追跡

以下はすべて**未実走の KILL 見込み**です。

| 変異 | 赤になる production test / assert |
|---|---|
| M-S1 | `1500/0/600` が scheduler まで進み、`test_t126_pegasus_tools.py:3052` の rc と `:3055` の call 不在が赤 |
| M-S2 | `1500/600/0`、同じ assert |
| M-S3 | `900/1200/0`、同じ assert |
| M-S4 | 上記いずれか、同じ assert |
| M-S5 | process substitution 復帰で scheduler へ進み、`:3069` の rc と `:3077` が赤 |
| M-J1 | walltime drift が dependency marker へ達し、`:3923` の診断と `:3924` が赤 |
| M-J2 | member-cap drift、同上 |
| M-J3 | round-gap drift、同上 |
| M-J4 | attestation drift、同上 |
| M-J5 | finalize drift、同上 |
| M-J6 | walltime-s の Python比較＋mapping assert 削除で marker 到達、同上 |
| M-J7 | wmax の両層削除、同上 |
| M-J8 | prologue の両層削除、同上 |
| M-J9 | index 交換で mapping assert が canonical を早期拒否し、`:3918` の marker 正例が赤 |
| M-J10 | process substitution 復帰で dependency 診断・marker が出て、`:3935` と `:3937` が赤 |
| M-C1 | `900/1199/1` が受理され、`test_t126_qualification_contract.py:77` の `pytest.raises` が赤 |
| M-C2 | `1499/1/600`、同上 |
| M-C3 | `1499/600/1`、同上 |
| M-C4 | 上記いずれか、同上 |

M-S/M-C の各 vector は、登録どおり二比較同時削除に対する証拠です。単独削除の証拠には数えていません。M-J6〜J8 も登録どおり両層変異です。

正例 P-J は dependency marker、P-S は既存 qsub/receipt 正例、P-C は canonical `load_protocol`/`validate_protocol` で過剰拒否を検出します。ただしすべて pytest 未実走です。

## 総括

- (a) blocker 一覧: **なし**。must-fix は所見 1、2。
- (b) C 節の殺せない変異: **静的追跡上はなし**。ただし未登録の `U-B1: member/gap/attestation/finalize を同値 float へ変更` は全新設 guard/test を生存します。
- (c) 判定: **NO-GO**。整数型の受理穴と `_attempt` の mode drift を修正し、焦点 pytest・変異 matrix・P-S/P-J/P-C・全走を親環境で実測するまで段 7 へ進めません。