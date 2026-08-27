### 所見 1: `rev-list --stdin` は stdin 中の `--not` を受理せず、中心コマンドが失敗する
- 重大度: blocker
- 向き: 正しさ以外
- 根拠: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1825-rescue-gate/s2-plan.md:227-246`。Git 2.34.1 で提示形式を read-only 実行すると `fatal: options not supported in --stdin mode` となった。stdin の `<positive-oid>` と `^<negative-oid>` は受理された。
- 成果物影響: 全 preview が閉包を算出できず rc2 になる。parse 失敗を空集合扱いすれば、さらに過小報告になる。
- 提案: stdin は候補 tip を `<oid>`、負 root を `^<oid>` とする。数万 root でも argv 制限を受けない。別案は候補 tip を argv、`--not --stdin` の後へ root OID を渡す形だが、候補数にも上限を設ける。

### 所見 2: root 棚卸しは worktree-private ref と壊れた administrative entry を尽くしていない
- 重大度: must-fix
- 向き: 正しさ以外
- 根拠: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1825-rescue-gate/s2-plan.md:207-225,250-267` は `for-each-ref` を一度だけ実行し、worktree は porcelain に現れた HEAD、index、reflog だけを読む。`refs/worktree/*`、`refs/bisect/*`、`refs/rewritten/*` は worktree-private であり、単一 worktree の ref view だけでは全 administrative ref store の棚卸しにならない。Git 2.34.1 では linked worktree の HEAD は別途 GC 保護される一方、private namespace を GC root として扱える範囲は invocation worktree の ref store と同一視できないため、未検証の private ref を負 root に入れてはならない。prunable と locked の正常な登録は porcelain に現れる。今回の read-only 観測でも 53 record、locked 38、prunable 0 だった。しかし壊れた administrative entry は省略または command failure になり得るため、`$common/worktrees/*` との照合が必要である。`MERGE_HEAD`、`CHERRY_PICK_HEAD`、`REVERT_HEAD`、`BISECT_HEAD` などの `BISECT_*`、`ORIG_HEAD`、`FETCH_HEAD` は存在するだけでは通常 ref root にならない。対して `refs/bisect/*` は ref である。Git の reachability 処理が明示的に読む rebase state も表にない。main worktree の `logs/HEAD` は lines 220-225 により、main record を必ず処理すれば含まれる。Git 2.34.1 の `git branch -d` は ref と `logs/refs/heads/<branch>` を削除するため、candidate reflog を除外する判断自体は正しい。
- 成果物影響: `root_snapshot.complete=true` が偽になり、正当な root の欠落なら喪失閉包を過大報告する。逆に GC が honor しない private ref を追加すると過小報告へ反転する。
- 提案: common worktree registry と porcelain を相互照合し、全 entry の HEAD、logs、index、private refs を検査する。壊れた entry、未証明の private ref、未知 state は rc2 とする。root 表を Git 2.34.1 の reachability source 単位で固定する。

### 所見 3: reflog と prunable worktree を恒久的な負 root にすると、期限ではなく閉包そのものを過小報告する
- 重大度: blocker
- 向き: 過小報告 (失われるものを見落とす)
- 根拠: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1825-rescue-gate/s2-plan.md:256-261,306-315`。Git GC は reflog を期限設定に従って expire し、残った root を用いて prune する。別 ref の移動で候補 commit がその reflog にだけ残った場合、plan は commit を負 root へ入れて閉包から完全に落とす。その entry は通常 `gc.reflogExpireUnreachable` の対象で、期限後は GC root でなくなる。`gc.<pattern>.reflogExpireUnreachable` の ref pattern 別設定も plan の読取り対象外である。prunable worktree の HEAD、reflog、index も `gc.worktreePruneExpire` により administrative entry ごと消え得る。なお Git 2.34.1 の repack が unreachable packed object を loose 化する場合、loose mtime は現在時刻ではなく元 pack の mtime を引き継ぐ。`git gc --auto` が prune を行う場合は effective `gc.pruneExpire` を使い、未設定時だけ既定 2 週間となる。packed object を assessment time の不確定 floor とする点は安全側である。assessment time が実際の ref loss や GC より早いことも下界としては安全側である。
- 成果物影響: 本来 1 commit を期限付きで報告すべき例が `commit_count=0` となり、retention row と台帳 entry が一切作られない。
- 提案: reflog、prunable worktree、その他期限付き root は恒久的な負 root にしない。commit は閉包へ残し、追加保持源とその失効下界を retention に記録する。少なくとも解析不能時は assessment time、rc2 とする。

### 所見 4: root snapshot と削除が結合されず、M7 の「expected-tip CAS」も実在しない
- 重大度: blocker
- 向き: 過小報告 (失われるものを見落とす)
- 根拠: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1825-rescue-gate/s2-plan.md:195,399,535` は tool 内の start/end snapshot と candidate tip 一致しか要求しない。tool 終了後、削除前に surviving ref、HEAD、index、reflog が消えても検出しない。さらに `tools/dev_wave_cleanup.py:990-998` は tip の事前比較後に `git branch -d` を呼ぶだけである。`tools/dev_wave_cleanup.py:919-931` の SHA 照合は削除成功後の診断検査であり CAS ではない。branch が line 991 後に動けば、別 tip が削除された後で partial を検出し得る。main の non fast-forward に加え、この branch-ref TOCTOU がある。また同 tool は `tools/dev_wave_cleanup.py:979-988` で worktree administrative root を prune してから branch を削除するため、preview 時の worktree root が削除時まで残る保証もない。
- 成果物影響: preview では surviving root に隠れて `commit_count=0` だった commit が、root と candidate branch の連続削除で無参照になり得る。
- 提案: P1 を撤回し、`dev_wave_cleanup.py` を編集面へ戻す。worktree prune 後、branch 削除直前に rescue snapshot を再取得し、candidate ref は expected old OID 付き CAS で削除する。main OID と root digest の変化も削除停止へ結び付ける。

### 所見 5: `6268/6700` と headroom 432 は Git 2.34.1 の auto GC 発火余裕を表さない
- 重大度: must-fix
- 向き: 過小報告 (失われるものを見落とす)
- 根拠: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1825-rescue-gate/measurements.md:18-27` と `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1825-rescue-gate/s2-plan.md:317-324`。Git 2.34.1 の loose-object auto GC 判定は `count-objects` の総数を `gc.auto` と直接比較せず、fanout directory の標本数から近似する。したがって総数との差 432 は発火までに作成可能な object 数ではない。pack 数による `gc.autoPackLimit` の別発火条件も schema にない。
- 成果物影響: `headroom=432` と `next_eligible_git_command_may_trigger=false` 相当の表示が、実際には現在発火可能な状態を安全と見せ得る。
- 提案: Git 2.34.1 の標本 heuristic と `gc.autoPackLimit` を正確に再現するか、headroom を `null`、proximity を `indeterminate` とする。6268 は観測総数としてのみ表示する。

### 所見 6: M6 は集合差の実行可能性だけを示し、正しい閉包を事前算出できることまでは実証していない
- 重大度: should-fix
- 向き: 正しさ以外
- 根拠: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1825-rescue-gate/measurements.md:88-100` は heads と tags だけを負 root に使い、detached HEAD の欠落を明記している。さらに所見 1 のとおり、plan の実際の stdin command は動かない。有限の安定 snapshot が得られれば集合差を事前算出できるという数学的主張は妥当だが、M6 は complete root inventory の実証ではない。
- 成果物影響: M6 を受入根拠にすると、不完全な root fixture でも `complete=true` を許すテスト設計になる。
- 提案: 結論を「完全かつ安定した root snapshot を取得できる場合に限り算出可能」と限定し、M6 は rev-list 方式と所要時間だけの根拠に降格する。

### 所見 7: M9 の一回走査と後追い再検査から「重複ゼロ」とは言えない
- 重大度: must-fix
- 向き: 正しさ以外
- 根拠: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1825-rescue-gate/measurements.md:129-141`。53 worktree の status は非原子的な逐次 snapshot であり、走査中または終了直後に追加された worktree を含まない。後から 3 件を拾うことは race の存在を示すだけで、最後の再検査後に追加がないことを証明しない。今回の独立 read-only 観測も 53 worktree だったが、これも別の一時点にすぎない。
- 成果物影響: 段 5 開始時に同じ file を編集中の新 worktree を見落とし、所有面が素集合という前提が崩れる。
- 提案: 段 5 の直前に branch と worktree registry の start/end digest 付きで再検査し、途中増減または対象 path の差分があれば開始しない。dispatcher 側で新規 worktree 作成との直列化も行う。

### 所見 8: `verify-pack` は read-only だが、auto 抑止と allowlist は landed checker の孫 Git process を覆わない
- 重大度: should-fix
- 向き: 正しさ以外
- 根拠: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1825-rescue-gate/s2-plan.md:300-304,326-328,341-350`。現 repo の 6 idx を Git 2.34.1 の `verify-pack -v` へまとめて渡した read-only 実測は elapsed 7.28 秒、最大 RSS 747712 KiB だった。`verify-pack` は pack と idx を読み、stdout を生成するだけで repository を変更せず、auto GC も起動しない。一方 `tools/check_branch_landed.py:63-69,216-230` の Git argv には `gc.auto=0` と `maintenance.auto=false` がなく、環境も作り直すため親からの通常の環境注入は伝わらない。同 checker は `diff-tree`、`log`、`ls-tree` など plan の allowlist 外の Git command も実行する。
- 成果物影響: 自身の直接 Git process は安全でも、「tool が呼ぶ全 Git command に override」という read-only 証明と禁止 command test が grandchild を覆わない。
- 提案: checker 側の共通 Git safety config に 2 override を追加するか、grandchild は auto-maintenance 非対象の read-only command のみという別契約を明文化して argv を監査する。`git config` 読取りだけ override を外す分離は runner の mode を分ければ実装可能である。

## 総括

- blocker の数: 3
- must-fix の数: 3
- プランを実装してよいか: NO-GO
- 最も見落としやすい 1 点: surviving reflog を負 root にすると、保持期限を少し長く見積もるのではなく、対象 commit が閉包と台帳から完全に消えること。