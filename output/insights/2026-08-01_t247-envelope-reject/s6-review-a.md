NO-GO です。既存拒否を弱める blocker が 1 件、受理集合の未裁定ずれと未検出変異が各 1 件あります。pytest は実行していません。

## 所見

1. blocker — command substitution 化により既存の walltime 拒否が迂回できる

   - 根拠: [submit_t126_qualification.sh:189](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/tools/pegasus/submit_t126_qualification.sh:189)、同 225–239。Python は walltime 自体を比較せず出力し、command substitution 後の Bash 文字列だけで判定している。
   - 実証: 有効な JSON 文字列 `10:00:\u000000` は Python 上で `10:00:` + NUL + `00` になる。現ホストで同じ出力経路を probe すると、HEAD の process substitution は先頭要素を `10:00:` と読み拒否した一方、新しい command substitution は NUL を除去して `10:00:00` にし、3 行 guard と最終比較を通した。command substitution の warning は rc を非 0 にしない。
   - 未実証: submit script 全体の pytest/subprocess 実走。
   - 成果物影響: HEAD が qsub 前に拒否した予約 policy を新実装は受理して scheduler を呼べるため、submit 受理集合が拡大し job 受理集合と分離する。
   - scope: 内。A4 の status 修正に伴う副作用であり、規律 2 と「既存条件を外さない」に反する。

2. must-fix — mapping assert が未裁定の型縮小を作り、submit/job/protocol がずれる

   - 根拠: [t126_qualification.sh:456](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/tools/pegasus/t126_qualification.sh:456)、同 468–482、[submit_t126_qualification.sh:218](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/tools/pegasus/submit_t126_qualification.sh:218)、[contract.py:230](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/orchestrator/qualification/contract.py:230)。
   - 実証: `prologue_cap_s: 900.0` は Python の `900.0 == 900` により submit と job の Python 比較を通る。submit は prologue を出力しないので qsub へ進むが、job は `"900.0" == "900"` の mapping assert で拒否する。対応する control protocol 値は `type(value) is not int` で拒否される。
   - 未実証: 3 層の end-to-end 実走。
   - 成果物影響: 同じ意味値の policy を submit が投入後、job が予約検査で rc=2 にするため、scheduler 呼出しと job 成果物の受理集合が食い違う。
   - scope: 内。ただし literal な mapping assert は s4 指示どおりであり、これは裁定が見落とした副作用として再裁定が必要。

3. must-fix — submit の「単独削除は等価変異」という解析が偽

   - 根拠: [submit_t126_qualification.sh:218](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/tools/pegasus/submit_t126_qualification.sh:218)、[test_t126_pegasus_tools.py:3034](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/orchestrator/tests/test_t126_pegasus_tools.py:3034)。
   - 実証: 現行の演算順で以下はいずれも対象値が canonical と不等なのに、浮動小数点丸め後の `calculated` は `29100.0 == 29100` になる。

     - prologue: `900.0000000000001`
     - attestation: `600.0000000000001`
     - finalize: `600.0000000000001`

     対象比較を単独削除すれば、他の比較・和・Wmax・walltime guard をすべて通る。一方、新テストの3ベクトルは常に2 capを同時に変えるため、単独削除時は残ったもう一方の比較で拒否され、テストは緑のままになる。repo 全体検索でもこれらを単独理由で検査する負例はなかった。
   - 未実証: 実 mutant を適用した pytest。
   - 成果物影響: cap 比較を1つ落とす回帰がテストを通過したまま submit 受理集合を拡大し、near-float policy を scheduler へ送れる。
   - scope: 内。DW-M01/C 節の変異登録と検出力の欠落。

4. nit — 共有 fixture が全 caller で job script の executable bit を落とす

   - 根拠: [test_t126_pegasus_tools.py:826](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t247-envelope-reject/orchestrator/tests/test_t126_pegasus_tools.py:826)。`job_scratch_root is None` でも `shutil.copy2` ではなく新規 `Path.write_text` を使う。production blob は `100755` だが、新規書込みに execute bit は付かない。
   - 実証: ソース mode は `git ls-tree HEAD` で `100755`。新規 `write_text` の作成 mode に execute bit はない。
   - 未実証: 既存 `_attempt` caller の pytest と生成 fixture tree の実測。
   - 成果物影響: fixture の `superproject_tree` と派生 series ID が変わり、job script の executable-mode 回帰を既存統合テストが観測しなくなる。
   - scope: 外。scratch 差替えに付随した不要な共有 fixture metadata 変更。

## 受理集合監査

以下は他の入力を canonical に固定した場合の実装後集合です。

| 層 | 実装後の受理集合 |
|---|---|
| submit | 重複 key は拒否。8 key 必須。5 cap/member/gap は Python 数値等価、和 29100、Wmax closure、walltime_s を検査。出力後は3行と walltime/time_s/Wmax の文字列を検査。ただし command substitution の NUL 除去後に walltime が `10:00:00` なら通る。schema_version、term grace、追加 key は非拘束。 |
| job | 重複 key は last-wins。8 key を Python 数値等価で検査し、time_s/Wmax/prologue はさらに出力文字列を固定。追加 key、schema_version、term grace は非拘束。和の独立検査はない。 |
| `validate_protocol` | timing は正確な8 key集合で、全値が strict `int > 0`。member/gap/3 cap/Wmax/walltime は固定。`member_term_grace_s` は任意の正整数。予約 policy の walltime 文字列はこの入力には存在しない。 |

整数による compensated cap drift は3層とも拒否するため、s4 の主目的は実装されています。ただし blocker #1 と must-fix #2 の入力では層がずれます。重複 key 非対称は A5、term grace は A8、予約 policy consumer の意味論未検査は A2 残余として裁定済み scope 外です。

## 変異 kill 追跡

すべて静的追跡であり、実走 kill は未実証です。

| 変異 | 期待される最初の赤 assert |
|---|---|
| M-S1 | `(1500,0,600)`。`test_submit_rejects_compensating_cap_drift_before_scheduler_calls` の `completed.returncode == 2`、同ファイル:3052 |
| M-S2 | `(1500,600,0)`。同 :3052 |
| M-S3 | `(900,1200,0)`。同 :3052 |
| M-S4 | 上記いずれか。同 :3052 |
| M-S5 | `test_submit_reservation_reader_rejects_python_failure_after_complete_output` の `completed.returncode == 2`、同 :3069 |
| M-J1 / J2 / J3 / J4 / J5 | 各 drift が dependency marker まで進み、`completed.stderr == "qualification envelope mismatch\n"`、同 :3923 |
| M-J6 / J7 / J8 | Python 比較と対応 mapping assert の両方を消すと同 :3923 |
| M-J9 | canonical 行が mapping assert で停止し、`downstream_marker.is_file()`、同 :3918 |
| M-J10 | dependency failure まで進むため、`completed.stderr == ""`、同 :3935 |
| M-C1 | `(900,1199,1)` が no-raise となり `pytest.raises`、`test_t126_qualification_contract.py:77` |
| M-C2 | `(1499,1,600)`。同 :77 |
| M-C3 | `(1499,600,1)`。同 :77 |
| M-C4 | 上記いずれか。同 :77 |

過剰拒否側は P-J が `test_t126_pegasus_tools.py:3918`、P-S が同 :3135、P-C が `test_t126_qualification_contract.py:50` で静的には観測できます。

scope 外4件については、A2 残余・A5・B6の残り7 block・A8への production 変更は差分中にありません。

## 総括

(a) blocker 一覧

- #1: command substitution の NUL 除去による submit 既存拒否の消失。

(b) 殺せない変異の一覧

- 登録済み ID: 静的にはなし。ただし全て実走未実証。
- 未登録だが非等価で生存する変異:
  - submit prologue 比較の単独削除
  - submit attestation 比較の単独削除
  - submit finalize 比較の単独削除

(c) 判定

**NO-GO**。#1 の既存受理集合拡大を閉じ、#2 の型・表現集合を再裁定し、#3 の単独削除変異を登録・kill するまで段 7 へ進めません。