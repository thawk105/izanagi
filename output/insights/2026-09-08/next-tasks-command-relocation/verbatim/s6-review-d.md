[must-fix] commit A は通常の `dev_wave_land` 経路では着地できない  
根拠: `_CONTROL_CONTAINERS` は `.codex/worktrees` を保護対象に固定し（[tools/dev_wave_land.py:146](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-next-tasks-command-20260908/tools/dev_wave_land.py:146)）、target がその配下なら main 更新前に無条件拒否する（[tools/dev_wave_land.py:1953](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-next-tasks-command-20260908/tools/dev_wave_land.py:1953)、呼出しは同ファイル:5493）。さらに回避しても、削除 gitlink の実パスまたは `.git/modules` が残れば D16 同期を拒否する（同ファイル:2463）。main の `.codex/worktrees` には現在115ディレクトリあり、c12e25078 の110名は全件残存している。  
成果物影響: 通常 land は control-plane collision で main 更新前に停止し、強行後も実体を残す限り postcondition が緑にならない。  
推奨: 明示的なユーザー裁定後、main checkout 上で `git rm --cached -r .codex/worktrees` を直接行う forward commitを作る。JSONと後述のtest修正も同時に入れ、実体を削除しない。その main をwaveへ取り込み、新mainをtested baseとして受入を取り直して残りを通常landする。

[must-fix] known-violation のユーザー裁定が射影内では未成立  
根拠: `KnownViolationSpec` は「ユーザー裁定済み」の違反を表す（[tools/check_ai_provenance.py:182](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-next-tasks-command-20260908/tools/check_ai_provenance.py:182)）一方、新JSONの `ruling` は「ユーザー承認は事後報告」と明記している（[登録JSON:5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-next-tasks-command-20260908/tools/known_violations/c12e25078ad155486c19eae633fde14e59753272--missing-codex-author--e71feba76c46009a79736502615fb83ee633e1f59fe27b71f07421f28289904b.json:5)）。原因sessionの了承はユーザー裁定の代替とは確認できない。  
成果物影響: 現状で全史監査を緑扱いすると、未批准の例外で c12e25078 の違反を相殺した成果物になる。  
推奨: land前にユーザーからこの1 findingの登録を明示批准してもらい、その記録を正本へ残す。射影外に既存批准があるなら、その具体的な記録を提示すれば本所見は解消する。

[must-fix] 既知違反の件数pinが4 nodeで古い  
根拠: HEADにはknown-violation JSONが56件あり、baseline 53件に対してpost-baselineは3件になったが、以下はなお `_known_violation_group_stdout(53, 2)` を期待している（[test file:3455](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-next-tasks-command-20260908/orchestrator/tests/test_check_ai_provenance.py:3455)、同:3949、4905、7082）。

- `orchestrator/tests/test_check_ai_provenance.py::test_unregistered_malformed_finding_remains_rc1_with_production_registry`
- `orchestrator/tests/test_check_ai_provenance.py::test_ledgered_3f2c43d7580b_is_known_and_rc0`
- `orchestrator/tests/test_check_ai_provenance.py::test_forward_correction_unrelated_history_remains_native_valid`
- `orchestrator/tests/test_check_ai_provenance.py::test_audit_history_empty_range_returns_zero_findings`

成果物影響: 正規pytestではこの4 nodeが赤になり、受入が成立しない。  
推奨: production registryを使う4期待値だけ `53, 3` へ更新する。合成registryの `0, 1` は変更しない。

[should] c12e25078 を含む既存4 worktreeはmain修正だけでは回復しない  
根拠: `git for-each-ref --contains=c12e25078` と各HEADの `git ls-tree` では、現wave以外の次の4 treeに110 gitlinkが残る。

- `dev-wave-research-gate` (`7c0440ff…`)
- `dev-wave-t2423-floor-protocol-identity` (`c12e2507…`)
- `dev-wave-t2430-a6-readheavy-mechanism` (`25b9c7e0…`)
- `rulings-full15-verdicts` (`541a0bb5…`)

現在のmainでは `git submodule status --recursive` が rc=128、修正済み現waveではrc=0だった。  
成果物影響: 4 treeは受入preflight不能のままで、古いtipを扱えばgitlink再導入またはland拒否になる。  
推奨: main修正後に各treeへ修正commitを取り込み、修正済みmainをbaseとして受入を再取得する。

[nit] gitlink除去集合と登録JSONの機械的形状は正しい  
根拠: c12e25078の追加110件と48837186cの削除110件を比較した `comm -3` は空。`git ls-tree -r HEAD | grep 160000` は `external/ccbench` だけで、[.gitmodules:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-next-tasks-command-20260908/.gitmodules:1) と一致する。JSONは `sha, kind, value, ruling, note` 順でcanonical形式（[checker:196](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-next-tasks-command-20260908/tools/check_ai_provenance.py:196)、同:690）、内容SHA-256とfilename digestはいずれも `e71feba7…904b`。  
成果物影響: tree修正後のsubmodule列挙は正規submoduleだけとなり、JSON形式破損によるrc=2は生じない。  
推奨: 除去集合、kind、digest、本文は維持する。

[nit] 登録は c12e25078 の1 findingだけを相殺する  
根拠: c12e25078は`.codex/`配下110 pathだけを変更し、messageには有効なClaude manager trailerがあるがCodex authorがない。checkerの実装面判定（[checker:1536](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-next-tasks-command-20260908/tools/check_ai_provenance.py:1536)）から finding は `missing-codex-author`。相殺はfull SHAとkind一致で1 entryを一度だけ消費し、それ以外はfindingsへ残す（同:2005）。  
成果物影響: c12e25078の別findingや他commitのfindingが隠れる受理集合拡大はない。  
推奨: exact SHA/kind方式を維持する。

[nit] 48837186c のprovenance trailerに追加scopeは不要  
根拠: CodexはJSONを実質著作しており、`tools/`の非Markdownは実装面なのでCodex authorが必要（[docs/ai-provenance.md:44](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-next-tasks-command-20260908/docs/ai-provenance.md:44)）。親のcached除去実行自体は「Git操作の機械的代行は記録しない」に該当する（同:71）。同一roleの重複行がないためscopeも任意（同:28）。  
成果物影響: trailer追加・role変更をしなくても48837186c自身のprovenance検査結果は変わらない。  
推奨: Claude manager＋Codex authorの現trailerを維持する。

[nit] `.gitignore` を変更しなかった判断はF599どおり  
根拠: 48837186cの`.gitignore`差分は空で、現在も`.codex/worktrees`はignoreされていない。F599は `?? .codex/worktrees/` を共有木観測に残すことを恒久対応としている（[docs/failures.md:17217](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-next-tasks-command-20260908/docs/failures.md:17217)、同:17229）。`.git/modules/.codex/worktrees` の残骸は現在0件。  
成果物影響: ignoreを足すとmutationの共有snapshot観測面が変わり、走行中runは `shared_snapshot_matches=false` / `MUT_RC=125` になり得る。  
推奨: `.gitignore`・`.git/info/exclude`とも変更しない。

## 総括

must-fix 3件、should 1件。最大のblockerは、修正内容は正しい一方で、その修正自体を通常landできないbootstrap問題。確信のない点は、射影外に既存の明示的ユーザー批准があるかどうかと、「一度も実体へ触れていない」という過去操作そのもの（現時点では110名すべて残存を確認）。pytestは要求どおり実行していないが、4件の期待値不一致は静的に確定できる。