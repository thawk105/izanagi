## 総括

専用 helper 化の方向は妥当ですが、現 plan はそのままでは正しさ境界を満たしません。  
特に child の依存閉包、親へ移す fixture の 108-byte 条件、`pytest.skip` の protocol、mutation anchor が未確定です。  
D452 の (a)(c) は裏付け可能ですが、(b) は mutation の一意性確認後でなければ主張できません。  
item4 の測定経路は実 pytest と一致しますが、将来の commit range への一般化は成立しません。

## 正しさ境界の所見

- **blocker** — [handoff.md:26](</work/1/SFC/tanab/dev-wave-jobs/t1222-population-closure/handoff.md:26>)、[handoff.md:88](</work/1/SFC/tanab/dev-wave-jobs/t1222-population-closure/handoff.md:88>)：D499 の item2 は「ユーザー明示命令まで保留」なのに、consult 依頼を解除命令と解釈している。放置すると、裁定なしに保留解除・実装へ進む。

- **major** — [stage2-plan.md:19](</work/1/SFC/tanab/dev-wave-jobs/T-1222-population-closure/stage2-plan.md:19>)、[test_dev_waves_integration.py:1687](</work/1/SFC/tanab/izanagi/.claude/worktrees/T-1222-population-closure/orchestrator/tests/test_dev_waves_integration.py:1687>)、[test_dev_waves_integration.py:259](</work/1/SFC/tanab/izanagi/.claude/worktrees/T-1222-population-closure/orchestrator/tests/test_dev_waves_integration.py:259>)：移設リストだけでは `_supervisor`、`_profile`、`_request`、`_wait_terminal`、`_best_effort_wait_cleanup` の依存閉包が閉じない。実装時に integration を再 import するか `NameError` になり、PASS/FAIL envelope が壊れる。

- **major** — [stage2-plan.md:19](</work/1/SFC/tanab/dev-wave-jobs/T-1222-population-closure/stage2-plan.md:19>)、[test_dev_waves_integration.py:1696](</work/1/SFC/tanab/izanagi/.claude/worktrees/T-1222-population-closure/orchestrator/tests/test_dev_waves_integration.py:1696>)、[test_dev_waves_integration.py:2024](</work/1/SFC/tanab/izanagi/.claude/worktrees/T-1222-population-closure/orchestrator/tests/test_dev_waves_integration.py:2024>)：helper は標準ライブラリと `tools.dev_waves.*` だけ、という条件では `pytest.skip.Exception` を扱えない。alias bind 不許可時に SKIP が FAIL または unstructured error へ変わる。

- **major** — [stage2-plan.md:21](</work/1/SFC/tanab/dev-waves-jobs/T-1222-population-closure/stage2-plan.md:21>)、[test_dev_waves_integration.py:1688](</work/1/SFC/tanab/izanagi/.claude/worktrees/T-1222-population-closure/orchestrator/tests/test_dev_waves_integration.py:1688>)、[test_dev_waves_integration.py:1693](</work/1/SFC/tanab/izanagi/.claude/worktrees/T-1222-population-closure/orchestrator/tests/test_dev_waves_integration.py:1693>)：`TemporaryDirectory()` の process-local な tempdir 状態、親の environment、cleanup 境界が変わるため、108-byte 判定と異常時の受理集合が同一とは証明できない。特に Supervisor 作成前に probe すると、現行の runtime 作成順序（1694-1696）が崩れる。

- **major** — [stage2-plan.md:31](</work/1/SFC/tanab/dev-wave-jobs/T-1222-population-closure/stage2-plan.md:31>)、[test_dev_waves_integration.py:2054](</work/1/SFC/tanab/izanagi/.claude/worktrees/T-1222-population-closure/orchestrator/tests/test_dev_waves_integration.py:2054>)、[test_growth_test_holds_contract.py:1493](</work/1/SFC/tanab/izanagi/.claude/worktrees/T-1222-population-closure/orchestrator/tests/test_growth_test_holds_contract.py:1493>)：live target の旧 launcher 文言は現状 integration 側では1箇所だが、plan は「module 名置換」としか定義していない。static assertion や fixture に同じ token が増えるため、DW-M04 の一意性は未確認であり、repository-wide replacement なら複数箇所になる。

- **major** — [test_growth_test_holds_contract.py:1488](</work/1/SFC/tanab/izanagi/.claude/worktrees/T-1222-population-closure/orchestrator/tests/test_growth_test_holds_contract.py:1488>)、[test_growth_test_holds_contract.py:1499](</work/1/SFC/tanab/izanagi/.claude/worktrees/T-1222-population-closure/orchestrator/tests/test_growth_test_holds_contract.py:1499>)：現 test は両 consumer を `(True, ())` で検証している。integration fixture を helper import・`False` に変える際、`test_s8b_floor_campaign.py` の `True` を個別に残さなければ、self-load detector の positive control が死ぬ。

- **minor** — [docs/decisions.md:19305](</work/1/SFC/tanab/izanagi/.claude/worktrees/T-1222-population-closure/docs/decisions.md:19305>)、[handoff.md:103](</work/1/SFC/tanab/dev-wave-jobs/t1222-population-closure/handoff.md:103>)：D463 の第3区分判定に、HEAD の file 数とサイズだけでは不十分。内容複雑度、bytes 増加、複数 commit tip での入力集合成長、実走査コストを排除できない。

## 親実測の検証結果

- **item4:** 測定経路は一致。`test_ledgered_3f2c43d7580b_is_known_and_rc0` が `site=site_policy.OTHER` を明示しており、[test_check_ai_provenance.py:3122](</work/1/SFC/tanab/izanagi/.claude/worktrees/T-1222-population-closure/orchestrator/tests/test_check_ai_provenance.py:3122>)、`main()` は OTHER を受理し、Pegasus login dispatch 分岐を通らない（[check_ai_provenance.py:2666](</work/1/SFC/tanab/izanagi/.claude/worktrees/T-1222-population-closure/tools/check_ai_provenance.py:2666>)、[check_ai_provenance.py:2700](</work/1/SFC/tanab/izanagi/.claude/worktrees/T-1222-population-closure/tools/check_ai_provenance.py:2700>)）。監査本体は `_audit_history()` に到達する（[check_ai_provenance.py:2805](</work/1/SFC/tanab/izanagi/.claude/worktrees/T-1222-population-closure/tools/check_ai_provenance.py:2805>)）。数値自体は再測定していないが、0.173秒/0.137秒という handoff 記録とは経路上整合する。なお、1 commit の `^!` と将来の任意 range・commit 増加への一般化は不可。D463 が要求する複数時点・呼出し閉包の証拠が不足している。

- **item1:** 現在の file 数・bytes 結果は handoff の記録（[handoff.md:103](</work/1/SFC/tanab/dev-wave-jobs/t1222-population-closure/handoff.md:103>)）と一致するが、`git ls-tree -r -l HEAD -- <path>` だけでは D463(b) と第3区分を判定するには不十分。少なくとも複数 tip で count と byte sum を比較する必要がある。再現用の最小コマンドは `for c in HEAD <older-tip>; do git ls-tree -r -l "$c" -- .claude/agents .codex/role-adapters orchestrator/codex_roles; done`。

## 裁定パッケージ候補

- consult 依頼を D499 の「明示的な item2 解除」とみなすか。
- fixture を親生成に移す場合の tempdir 固定、Supervisor 作成順、timeout 後の descendant cleanup 契約。
- helper で `pytest` を許すか、独自 SKIP sentinel と argv schema を設けるか。
- mutation を AST/完全 anchor で一箇所に固定し、DW-M04 を満たす方法。
- growth contract の期待値を `s8b=True / dev-waves=False` の個別 map にすること。