| 所見 | 判定 | 根拠 |
|---|---|---|
| F1 | **regressed** | 成功時は handler を復元せず `main()` から直接 return するため、public API の return 後にも過去 invocation の cleanup closure が process-global handler として残る。[tools/dev_wave_wait.py:850](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:850) [tools/dev_wave_wait.py:863](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:863)。また通常の失敗 cleanup 後に `claim_started` を false に戻さず、handler 復元中の signal で二度目の release が走り得る。[tools/dev_wave_wait.py:756](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:756) [tools/dev_wave_wait.py:868](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:868) |
| F2 | **partial** | claim 呼出し直前に `claim_started=True` とするため、lease 作成後の例外経路は cleanup 対象になった。[tools/dev_wave_wait.py:495](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:495)。しかし構造化された `held` / `queued` 応答後も true のままで、timeout・signal・後続 Git 失敗時に同一 slug の既存 lease を release する。[tools/dev_wave_wait.py:511](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:511) [tools/dev_wave_wait.py:535](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:535) [tools/dev_wave_wait.py:756](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:756)。テストも `held` / `queued` 後の release を正として固定している。[test_dev_wave_wait.py:404](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/orchestrator/tests/test_dev_wave_wait.py:404) |
| F3 | **partial** | `mkstemp` により 0600 の管理下 file を作り、検査済み UTF-8 bytes を dry-run と commit の双方へ渡す点は閉じた。[tools/dev_wave_wait.py:151](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:151) [tools/dev_wave_wait.py:548](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:548) [tools/dev_wave_wait.py:686](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:686)。一方、commit の SHA を保存せず `git log ... HEAD` を検査しており、hook または並行操作で HEAD が動けば「作成した commit」と別物を見る。[tools/dev_wave_wait.py:692](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:692) [tools/dev_wave_wait.py:699](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:699) |
| F4 | **closed** | 指定された全 Git 環境変数を共通 subprocess seam で除去し、stage Git と unbounded acceptance Git の双方に掛かる。[tools/dev_wave_wait.py:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:38) [tools/dev_wave_wait.py:109](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:109)。resolved cwd と `--show-toplevel` も claim 前に一致検査する。[tools/dev_wave_wait.py:440](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:440) |
| F5 | **partial** | Git/helper へ 300 秒 timeout、timeout 例外の fail-closed 化、zombie 判定は入った。[tools/dev_wave_wait.py:123](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:123) [tools/dev_wave_wait.py:328](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:328) [tools/dev_wave_wait.py:404](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:404)。ただし `subprocess.run(timeout=...)` は process group を作らず、hook 子孫を止めない。timeout 後の `merge --abort` にも repository-clean postcondition がなく、abort 非0なら中途状態を残して rc=74 になるだけである。[tools/dev_wave_wait.py:109](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:109) [tools/dev_wave_wait.py:587](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:587) |
| F6 | **closed** | 取得直前からの保守的な経過時間を使い、残余 TTL、期限後の排他喪失、fencing 不在を明記する。[tools/dev_wave_wait.py:530](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:530) [tools/dev_wave_wait.py:724](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:724) |
| F7 | **closed** | `_claim_once` の直接テストが diagnostic/nested の `"acquired"` を含む `state=held` を `held` と固定し、E2E も submission 回数で検出する。[test_dev_wave_wait.py:429](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/orchestrator/tests/test_dev_wave_wait.py:429) [test_dev_wave_wait.py:469](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/orchestrator/tests/test_dev_wave_wait.py:469) |
| F8 | **partial** | acceptance の主要 negative case は literal event 列へ強化された。[test_dev_wave_wait.py:400](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/orchestrator/tests/test_dev_wave_wait.py:400) [test_dev_wave_wait.py:653](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/orchestrator/tests/test_dev_wave_wait.py:653)。しかし `_FakeEffects.assert_drained()` は event 列を検査せず、producer の missing-file や invalid PID negative case も exact 比較ではない。[test_dev_wave_wait.py:134](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/orchestrator/tests/test_dev_wave_wait.py:134) [test_dev_wave_wait.py:260](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/orchestrator/tests/test_dev_wave_wait.py:260) [test_dev_wave_wait.py:299](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/orchestrator/tests/test_dev_wave_wait.py:299) |
| F9 | **closed** | 実 Git/helper 結合検査が `worktree-<slug>`、環境変数 lease、実 merge/message、child cwd、stdout/stderr 継承、lease 保持を一経路で検証する。[test_dev_wave_wait.py:1232](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/orchestrator/tests/test_dev_wave_wait.py:1232) |
| F10 | **closed** | JSON object 強制、release 非0・malformed JSON、abort 非0の cleanup failure 化と各テストが存在する。[tools/dev_wave_wait.py:394](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:394) [tools/dev_wave_wait.py:563](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:563) [test_dev_wave_wait.py:483](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/orchestrator/tests/test_dev_wave_wait.py:483) [test_dev_wave_wait.py:906](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/orchestrator/tests/test_dev_wave_wait.py:906) |

## 新規所見

### N1 — blocker — 成功後 handler が process-global に残る

主張: 成功時に handler を復元しない方式は signal 窓を閉じたのではなく、過去 lease の cleanup closure を `main()` return 後へ延命している。caller が land release 後も同一 process を使い続け、その slug が再利用された後に signal を受けると、古い handler が新しい lease を削除できる。

根拠: [tools/dev_wave_wait.py:779](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:779) [tools/dev_wave_wait.py:850](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:850) [tools/dev_wave_wait.py:863](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:863)

**成果物影響:** 後発 wave の排他が古い invocation の signal handler により解除され、受入済み tip と land 対象が競合する。

提案: signal と lease ownership を単一状態機械にし、cleanup 成功時に ownership を必ず消費する。public `main()` の成功後は handler を残さず、実 signal を同期させた成功境界テストを置く。

### N2 — blocker — `claim_started` は ownership 証明になっていない

主張: claim subprocess が構造化された `held` / `queued` を返した時点では「この呼出しが lease を作った可能性」は消えている。それでも flag を保持するため、同一 wave の別 invocation が持つ lease を cleanup する。

根拠: [tools/dev_wave_wait.py:503](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:503) [tools/dev_wave_wait.py:511](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:511) [wave_land_window.py:722](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/wave_land_window.py:722) [wave_land_window.py:747](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/wave_land_window.py:747)

**成果物影響:** 二重起動・再起動・signal 一回で現 holder の lease が消え、並行受入を許す。

提案: `NONE / CLAIM_IN_FLIGHT_UNKNOWN / ACQUIRED` を分離し、正常な non-acquired 応答では release 権限を消す。ticket cleanup と lease release を分離できないなら helper 契約の拡張を裁定へ戻す。

### N3 — must-fix — timeout は子孫と repository 状態を閉じない

主張: timeout は直接 process にしか作用せず、Git hook 子孫を含む bounded termination ではない。さらに abort 後の `MERGE_HEAD`・index・HEAD を再検査しない。

根拠: [tools/dev_wave_wait.py:109](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:109) [tools/dev_wave_wait.py:603](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:603)

**成果物影響:** waiter が終了して lease を解放した後も Git 子孫や未完 merge が worktree を変更し、次の受入証拠を汚染する。

提案: stage subprocess を専用 process group で起動して timeout 時に全体を終了し、abort 後に HEAD・merge state・tracked cleanliness の postcondition を確認する。

### N4 — must-fix — message postcheck が commit identity に束縛されない

主張: 検査対象が固定 SHA ではなく可変な `HEAD` である。現在のテストも `HEAD` 呼出しを期待しており、誤った実装を固定している。

根拠: [tools/dev_wave_wait.py:699](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/tools/dev_wave_wait.py:699) [test_dev_wave_wait.py:1089](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/orchestrator/tests/test_dev_wave_wait.py:1089)

**成果物影響:** 作成 commit が trailer 不足でも別の trailer 付き HEAD を検査して受入を投入し、provenance 監査で結果を廃棄する。

提案: commit 直後に SHA を取得・固定し、その SHA の message を検査したうえで、受入直前にも HEAD が同じ SHA であることを確認する。

## 新規テストの恒真・見逃し

- [test_public_main_real_signal_releases_lease](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/orchestrator/tests/test_dev_wave_wait.py:1326) は child 実行中、つまり `keep_lease=False` の時点で signal を送る。実 handler から成功後 callback 呼出しを削除しても、`run_acceptance()` 自身の `finally` が release するため緑のままである。
- [test_signal_after_core_success_before_public_main_return_releases](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/orchestrator/tests/test_dev_wave_wait.py:1151) は `_install_signal_handlers` を丸ごと monkeypatch し、callback を直接呼ぶ。実 handler の callback 結線を壊しても緑である。
- [test_second_signal_is_deferred_until_cleanup_completes](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/orchestrator/tests/test_dev_wave_wait.py:1209) は signal-mask 呼出し回数を検査しない。`pthread_sigmask` 処理を全削除すると signal が注入されず、そのまま緑になる。
- [test_default_run_sanitizes_git_and_bounds_only_stages](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t740-canonical-waiter/orchestrator/tests/test_dev_wave_wait.py:975) は timeout 引数の存在しか見ない。`TimeoutExpired` 後に unbounded retry する退行や、子孫を残す実装でも緑である。
- F8 について、producer の失敗経路へ余計な `effects.getenv("IGNORED")` を追加しても missing-file/invalid-PID テストは event 全体を比較せず緑のままである。

## 退行・受理集合

`0d732b99` の親 `909914ef` には対象 2 ファイルが存在せず、`d453339b` はこの 2 ファイルだけを変更している。したがって land 済み tracked テストの期待値変更はない。

branch suffix、任意 command、claim の exact JSON predicateは維持され、裁定外の明白な fail-open は見つからない。一方、成功時 handler を復元しない process-global 変更は新規退行であり、`held` / `queued` 後の release を正とするテストは既存 lease の破壊経路を固定している。

pytest は指示どおり実走していない。`62 passed` は親の実測としてのみ扱った。

## 総括

**NO-GO。** F1 は新しい stale-handler 退行を伴い、F2・F3・F5・F8 は root cause が部分的にしか閉じていない。特に F1/F2 は同一 wave の後発 lease を誤 release できるため blocker のままである。

`T` は `orchestrator/tests/test_dev_wave_wait.py::`。

| 変異 | 決定的に赤くなる nodeid | 単一理由性 |
|---|---|---|
| M1 | 保証できる nodeid なし。effects seam に載せた実装なら `Ttest_pid_probe_calls_kill_zero_for_exact_pid`、literal `pgrep -f` 自己一致なら同 node が hang し得る | **不可**。unexpected subprocess、kill queue 残存、hang のいずれにもなり得る |
| M2 | `Ttest_claim_once_uses_only_exact_top_level_state`、`Ttest_acceptance_ignores_acquired_outside_top_level_state` | **可**。前者は戻り値 `held`、後者は submission 回数だけで殺す |
| M3 | `Ttest_default_wiring_with_real_git_and_lease_helper` | **可**。成功後の `acceptance.lease` 不存在だけに帰属できる |
| M4 | `Ttest_nonzero_stage_blocks_submission_and_releases[postcheck]`、`Ttest_merge_sequence_and_postcheck_are_exact` | **不可**。後段 queue mismatch、rc、event 列の複数理由で赤になる |
| M5 | `Ttest_merge_required_without_message_file_releases_before_submission` | **不可**。merge/postcheck/command fixture が未準備で、queue mismatch と cleanup rc=74 が混ざる |
| M6 | `Ttest_acceptance_command_red_is_propagated_after_release`、`Ttest_public_main_real_signal_releases_lease` | **可**。後者は signal 後の実 lease 残存へ直接帰属できる |
| M7 | `Ttest_producer_dead_without_required_file_fails_closed[artifact]` | **可**。artifact 欠落時の rc=70→0 反転に絞れる |
| M8 | `Ttest_identity_preflight_rejects_before_claim[/repo-wrong-branch--preflight-branch]` | **不可**。branch gate 除去後の status/claim fixture がなく、unexpected run・rc・stage が同時に崩れる |