## 総括

現行 job body は D1700 に従い、共有 gitdir の prune を撤去し、自 path の remove 2 本を維持しています。  
関数抽出は現在の bytes では全文を取得し、prune 復活時には兄弟保存 test が実際に赤になります。  
real 所見は 2 件です。台帳更新の未実施と、関数外へ置いた難読化 prune を検出できない穴があります。  
本レビューではテストを実走しておらず、親提示の緑を前提とした静的検査です。

## real 所見

1. acceptance duration ledger の必須更新が欠落しています。

   段4裁定は、新規 node により被覆率が 90% を割るため、実装対象を job body・契約テスト・台帳の3ファイルと明記しています（[s4-adjudication.md:15](/home/SFC/tanab/.claude/jobs/1314c3cf/tmp/wave-t2354/s4-adjudication.md:15)、[s4-adjudication.md:87](/home/SFC/tanab/.claude/jobs/1314c3cf/tmp/wave-t2354/s4-adjudication.md:87)）。一方、実装報告は変更が2ファイルだけで台帳を未変更と明記しています（[s5-author2.md:24](/home/SFC/tanab/.claude/jobs/1314c3cf/tmp/wave-t2354/s5-author2.md:24)、[s5-author2.md:64](/home/SFC/tanab/.claude/jobs/1314c3cf/tmp/wave-t2354/s5-author2.md:64)、[s5-author2.md:80](/home/SFC/tanab/.claude/jobs/1314c3cf/tmp/wave-t2354/s5-author2.md:80)）。

   成果物影響: このままでは acceptance-duration 被覆 gate が 90% 未満となり、変更を完了扱いにできません。

   修正案: 実走 JUnit を得た後、裁定どおり `tools/update_acceptance_duration_ledger.py --add-only <JUnit>` で2 nodeを登録し、`test_acceptance_schedule_order.py` の被覆 gate を確認してください。

2. 関数外へ置いた難読化 prune は、静的・runtime の両 gate を通過します。

   静的検査は literal な `worktree prune` だけを拒否します（[test_a5_second_boot_job_contract.py:363](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/orchestrator/tests/test_a5_second_boot_job_contract.py:363)、[test_a5_second_boot_job_contract.py:387](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/orchestrator/tests/test_a5_second_boot_job_contract.py:387)）。runtime snippet に入る job bytes は `remove_worktrees` と `cleanup_worktrees` の2関数だけです（[test_a5_second_boot_job_contract.py:88](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/orchestrator/tests/test_a5_second_boot_job_contract.py:88)）。

   したがって、たとえば job 本文末尾の [a5_second_boot_backoff_sweep.sh:810](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/tools/pegasus/a5_second_boot_backoff_sweep.sh:810) の後へ次を1回挿入すると、regex は通過し、2本のruntime testでも実行されません。

   ```bash
   timeout "$remaining" git -C "$CCBENCH_BASE" worktree "pr""une" --expire now || true
   ```

   成果物影響: D1700違反の job body が契約テストを通過し、別ノードで生存中の兄弟登録を削除できます。

   修正案: literal の個数 pin ではなく、job 全体の Bash tokenを解析し、すべての実行可能な `git worktree` 呼出しについて subcommand が許可された `add` / `remove` であることを検査してください。少なくとも隣接 quote を連結した後にも prune 不在を検査する必要があります。

### 所見なしだった攻撃点

関数抽出は現行 bytes では正しいです。[`_shell_function`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/orchestrator/tests/test_a5_second_boot_job_contract.py:59) が探す最初の `\n}` は、`remove_worktrees` では [job body:161](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/tools/pegasus/a5_second_boot_backoff_sweep.sh:161)、`cleanup_worktrees` では [job body:176](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/tools/pegasus/a5_second_boot_backoff_sweep.sh:176) です。receipt の内側の閉じ brace は bytes が `0a 20 20 7d`、関数終端は `0a 7d` なので、[job body:159](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/tools/pegasus/a5_second_boot_backoff_sweep.sh:159) では切れません。両関数の全文を取得し、job 本文側の trap は除外したうえで同じ trapを [test:90](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/orchestrator/tests/test_a5_second_boot_job_contract.py:90) に張り直しています。

兄弟 fixture は lock されていません。兄弟を登録後に directoryだけを削除し（[test:486](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/orchestrator/tests/test_a5_second_boot_job_contract.py:486)、[test:490](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/orchestrator/tests/test_a5_second_boot_job_contract.py:490)）、lock 操作は別の失敗 test の自 path だけです（[test:549](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/orchestrator/tests/test_a5_second_boot_job_contract.py:549)）。gitdir metadata は作成直後の mtime ですが、親の実測前提どおり `--expire now` の対象です。literal prune を戻すと静的 assert と [兄弟登録 assert:521](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/orchestrator/tests/test_a5_second_boot_job_contract.py:521) が赤になり、`"pr""une"` なら後者だけが赤になります。

stub は `write_failure_receipt` の内部だけを置換しています（[test:85](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/orchestrator/tests/test_a5_second_boot_job_contract.py:85)）。発火条件は抽出した実体の [cleanup_worktrees:171](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/tools/pegasus/a5_second_boot_backoff_sweep.sh:171) が担っています。`CURRENT_STAGE` は remove 呼出し前の [job body:168](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/tools/pegasus/a5_second_boot_backoff_sweep.sh:168) で設定されるため、stub の [test:86](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/orchestrator/tests/test_a5_second_boot_job_contract.py:86) は正しい stage を観測します。

rc 周辺の変更前逐語は次です。

```bash
  remove_rc=$cleanup_rc
  if [[ -n "$CCBENCH_BASE" ]]; then
    remaining=$((deadline - SECONDS))
    if [[ "$remaining" -le 0 ]]; then
      prune_rc=124
    else
      timeout "$remaining" git -C "$CCBENCH_BASE" worktree prune --expire now \
        >>"$OUTPUT_ROOT/env/ccbench-worktree-prune.stdout" \
        2>>"$OUTPUT_ROOT/env/ccbench-worktree-prune.stderr" || prune_rc=$?
    fi
    [[ "$cleanup_rc" -ne 0 || "$prune_rc" -eq 0 ]] || cleanup_rc=$prune_rc
  fi
  printf '%s\nprune_rc=%s\n' "$remove_rc" "$prune_rc" \
    >"$OUTPUT_ROOT/env/worktree-remove.rc" || true
  return "$cleanup_rc"
```

変更後逐語は次です（[job body:153](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/tools/pegasus/a5_second_boot_backoff_sweep.sh:153)）。

```bash
  {
    printf '%s\n' "$cleanup_rc"
    [[ -z "$JOB_CCBENCH" ]] || \
      printf 'remaining_ccbench_path=%s\n' "$JOB_CCBENCH"
    [[ -z "$JOB_REPO" ]] || \
      printf 'remaining_repo_path=%s\n' "$JOB_REPO"
  } >"$OUTPUT_ROOT/env/worktree-remove.rc" || true
  return "$cleanup_rc"
```

self-remove の失敗は引き続き `|| command_rc=$?` で捕捉され（[job body:133](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/tools/pegasus/a5_second_boot_backoff_sweep.sh:133)、[job body:146](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/tools/pegasus/a5_second_boot_backoff_sweep.sh:146)）、最後に明示 return されます。さらに cleanup は先に `EXIT ERR` trap を解除し、`remove_worktrees || cleanup_rc=$?` として呼ぶため（[job body:166](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/tools/pegasus/a5_second_boot_backoff_sweep.sh:166)、[job body:169](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/tools/pegasus/a5_second_boot_backoff_sweep.sh:169)）、brace 化による `set -e`／ERR trap／job rc の退行はありません。変わったのは prune が cleanup rc に寄与しなくなった点だけで、これは意図どおりです。

`JOB_CCBENCH` と `JOB_REPO` が両方空の receipt `"0\n"` も掃除用途には曖昧ではありません。両変数は空で初期化され（[job body:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/tools/pegasus/a5_second_boot_backoff_sweep.sh:38)）、各 path は対応する `worktree add` より先に代入されます（[job body:451](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/tools/pegasus/a5_second_boot_backoff_sweep.sh:451)、[job body:458](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/tools/pegasus/a5_second_boot_backoff_sweep.sh:458)、[job body:468](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/tools/pegasus/a5_second_boot_backoff_sweep.sh:468)、[job body:469](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/tools/pegasus/a5_second_boot_backoff_sweep.sh:469)）。両方空なら後続掃除へ渡す既知 path がありません。元 job の失敗 rc・stage は別の failure receipt が担います（[job body:104](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/tools/pegasus/a5_second_boot_backoff_sweep.sh:104)、[job body:114](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/tools/pegasus/a5_second_boot_backoff_sweep.sh:114)）。

既存期待値の移動も裁定どおりです。旧 prune 正例と旧 receipt pinを削り、prune 不在を追加し、receipt 書式と self-remove はruntime側で固定しています。禁止された remove count、`prune_rc` 不在、旧 filename 不在、printf逐語の静的 pinは追加されていません（[test:363](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/orchestrator/tests/test_a5_second_boot_job_contract.py:363)）。checkout 分割もなく、D1700が残せとした自 path remove は維持されています。

## 各 assert の落とし方

| assert | 実装を壊す具体例 | 恒真性 |
|---|---|---|
| [test:494](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/orchestrator/tests/test_a5_second_boot_job_contract.py:494) 兄弟の事前登録 | fixture の兄弟 `worktree add` を削除する、または別 repository に登録する。 | 実装非依存のfixture gate。恒真ではない。 |
| [test:510](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/orchestrator/tests/test_a5_second_boot_job_contract.py:510) 元job rc | cleanup 成功時にも常に `exit 0`、または常に cleanup rc で上書きする。 | job rc 0/23の双方で有効。 |
| [test:511](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/orchestrator/tests/test_a5_second_boot_job_contract.py:511) ccbench directory削除 | ccbench側の self-remove を削除する、または誤ったpathへ向ける。 | 恒真ではない。 |
| [test:512](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/orchestrator/tests/test_a5_second_boot_job_contract.py:512) repo directory削除 | repo側の self-remove を削除する、または誤ったpathへ向ける。 | 恒真ではない。 |
| [test:519](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/orchestrator/tests/test_a5_second_boot_job_contract.py:519) repo登録削除 | `git worktree remove` を単なる directory削除へ置換し、管理登録を残す。 | directory assertとは別に登録を検査する。 |
| [test:520](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/orchestrator/tests/test_a5_second_boot_job_contract.py:520) ccbench登録削除 | ccbench self-remove を単なる directory削除へ置換する。 | 恒真ではない。 |
| [test:521](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/orchestrator/tests/test_a5_second_boot_job_contract.py:521) 兄弟登録保存 | literal pruneを戻す、または関数内へ `worktree "pr""une" --expire now` を戻す。 | runtime gateの中心で、実際に赤になる。 |
| [test:522](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/orchestrator/tests/test_a5_second_boot_job_contract.py:522) 正常receipt | 旧 `prune_rc=0` 行を戻す、成功後もJOB変数をclearしない、または異なるrcを書く。 | 恒真ではない。 |
| [test:523](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/orchestrator/tests/test_a5_second_boot_job_contract.py:523) 正常時stub未発火 | cleanup rc 0でも `write_failure_receipt` を呼ぶ。 | 恒真ではない。 |
| [test:570](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/orchestrator/tests/test_a5_second_boot_job_contract.py:570) cleanup rc非0 | remove失敗後に `cleanup_rc=0` とする、または `return 0` にする。 | 恒真ではない。 |
| [test:571](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/orchestrator/tests/test_a5_second_boot_job_contract.py:571) 残置path書式 | remove失敗時にもJOB変数をclearする、path順を逆転する、旧receiptへ戻す。 | 入力反射は可能だが、書式・clear条件は検出する。 |
| [test:575](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/orchestrator/tests/test_a5_second_boot_job_contract.py:575) locked ccbench directory残存 | lockを無視して `rm -rf "$JOB_CCBENCH"` する。 | 恒真ではない。 |
| [test:576](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/orchestrator/tests/test_a5_second_boot_job_contract.py:576) locked repo directory残存 | lockを無視して `rm -rf "$JOB_REPO"` する。 | 恒真ではない。 |
| [test:577](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/orchestrator/tests/test_a5_second_boot_job_contract.py:577) ccbench登録残存 | cleanup内でunlock後にremoveする、または管理登録を削除する。 | 実際の登録を検査している。 |
| [test:580](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/orchestrator/tests/test_a5_second_boot_job_contract.py:580) repo登録残存 | repo worktreeをunlockして削除する、または管理登録を消す。 | 実際の登録を検査している。 |
| [test:584](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/orchestrator/tests/test_a5_second_boot_job_contract.py:584) 正常jobへのcleanup rc昇格 | `remove_worktrees` を `return 0` にする、またはcleanup失敗を終了rcへ反映しない。 | M2を殺す。 |
| [test:585](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/orchestrator/tests/test_a5_second_boot_job_contract.py:585) failure receipt 1回・stage | 呼出しを削除、重複、誤rc、または `CURRENT_STAGE` 設定を削除する。 | 発火条件とstageを検出する。 |
| [test:589](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/orchestrator/tests/test_a5_second_boot_job_contract.py:589) 元rc 23優先 | 条件から `original_rc == 0` を外し、cleanup rcで常に上書きする。 | M4を殺す。 |
| [test:590](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/orchestrator/tests/test_a5_second_boot_job_contract.py:590) 元job失敗時stub未発火 | 元rc 23でもcleanup failure receiptを追加発火する。 | 恒真ではない。 |

なお、[test:566](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/orchestrator/tests/test_a5_second_boot_job_contract.py:566) から [test:569](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/orchestrator/tests/test_a5_second_boot_job_contract.py:569) は明示的な `assert` ではありませんが、receipt欠落・空・非数値を例外として赤にします。

## 推測

今回、real と分離して残す未検証推測はありません。上記2件は、裁定・実装報告・現在のsource bytesから静的に確定できます。

## nit

1. 失敗 test 単独では、「locked状態を認識したらremoveを実行せず、非0 rcと受領pathをそのまま書く」実装でも通ります。ただし test 全体では、正常系が自 path のdirectoryと登録の削除を要求し、失敗系も登録実体を [test:577](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/orchestrator/tests/test_a5_second_boot_job_contract.py:577) と [test:580](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2354-a5-prune-removal/orchestrator/tests/test_a5_second_boot_job_contract.py:580) で確認しています。要求成果物の差を示せないため nit です。

2. 兄弟事前条件の assert は登録だけを見ており、`not sibling_ccbench.exists()` とlock不在を明示assertしていません。ただし現行fixtureは直前に `shutil.rmtree` し、兄弟へlockを一度も設定していないため、現在の prune 検出力には影響しません。

3. `_shell_function` の開始探索は行頭anchorを持たないため、将来、定義より前のcommentや文字列へ `remove_worktrees() {` が入ると誤抽出します。現行bytesでは最初の一致が実定義なので、現在の結果には影響しません。