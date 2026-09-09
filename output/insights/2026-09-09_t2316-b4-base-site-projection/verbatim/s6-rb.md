## 受理集合の変化 (表)

前提は、site 以外の入力と各 revision に対応する admission record が妥当で、launch 系は実物の `DRIVER_REGISTRY` を使う場合です。`A` は return まで受理、`R` は例外による拒否です。on/off 両 arm で同じです。

| 関数 | driver | OTHER | PEGASUS_COMPUTE | PEGASUS_LOGIN | PEGASUS_SUSPECT |
|---|---|---|---|---|---|
| `_driver_configs` | base | A→A、ID 不変、contract 付与 | A→A、ID は未射影→射影済み | A→R、早期拒否 | A→R、早期拒否 |
| `prepare_launch` | base | A→A | A→A、context の ID が射影済みに変化 | A→R、早期拒否 | A→R、早期拒否 |
| `launch_bootstrap` | base | A→A | R→A、driver 境界の ID が一致 | R→R、拒否点を driver から prepare へ前倒し | R→R、同左 |
| `launch_continuation` | base | A→A | R→A、driver 境界の ID が一致 | R→R、critic 起動前へ拒否を前倒し | R→R、同左 |
| `_driver_configs` | sort | A→A | A→A | A→A | A→A |
| `prepare_launch` | sort | A→A | A→A | A→A | A→A |
| `launch_bootstrap` | sort | A→A | A→A | A→A | A→A |
| `launch_continuation` | sort | A→A | A→A | A→A | A→A |
| `_driver_configs` | trigger | A→A | A→A | R→R | R→R |
| `prepare_launch` | trigger | A→A | A→A | R→R | R→R |
| `launch_bootstrap` | trigger | A→A | A→A | R→R | R→R |
| `launch_continuation` | trigger | A→A | A→A | R→R | R→R |

根拠は、base にだけ追加された site 解決と射影 [p3_b4_launcher.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/campaign/p3_b4_launcher.py:147)、許可集合と射影内容 [p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/campaign/p3_s4_loop.py:133)、prepare から両 launch への共有経路 [p3_b4_launcher.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/campaign/p3_b4_launcher.py:545)、base driver 側の同じ射影と厳密照合 [p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/campaign/p3_s4_loop.py:2589) です。

なお、同一 byte の admission record を固定して比較すると別の変化があります。launcher は全 driver の projection closure に含まれるため [p3_b4_closed_critic.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/campaign/p3_b4_closed_critic.py:623)、旧 hash を pin した record は全 driver・全 site の prepare/launch で A→R になります。ただしこれは段4で明示的に裁定済みで、更新対象となる実 record は存在しないと確認されています [s4-adjudication.md](/home/SFC/tanab/.claude/jobs/f8a552e6/tmp/t2316/s4-adjudication.md:40)。

## 所見 (real)

RB1 — 高: LOGIN / SUSPECT の新しい fail-close を追加 5 node のどれも固定していません。

N1、N3 は COMPUTE、N4 は OTHER、N2 は COMPUTE と OTHER、N5 は sort の COMPUTE だけです [test_p3_b4_launcher.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/tests/test_p3_b4_launcher.py:332)。通常の既存 test は autouse fixture により OTHER になります [conftest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/tests/conftest.py:239)。

したがって、base 分岐が LOGIN / SUSPECT で未射影 `configs` を返すよう変異しても、N1からN5はすべて緑になり得ます。これは裁定が認めた新しい拒否集合そのものを未検査にしているため real です。

RB2 — 低: N2 の contract assertion が失敗しても、どちらの site か直接特定できません。

ループの site 一致 assertion は比較値から判別できますが、contract の検査はラベルなしの `assert all(...)` だけです [test_p3_b4_launcher.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/tests/test_p3_b4_launcher.py:369)。ここだけ失敗すると、通常の assertion 表示は `assert False` と generator 情報に留まり、hostname / expected_site が示されません。coverage の抜けではありませんが、要求された失敗箇所の識別性は満たしていません。

## 所見 (refuted)

RB3 — refuted: 裁定外の site 受理変更は、production launch の実効集合にはありません。base の COMPUTE は意図どおり R→A、LOGIN / SUSPECT は拒否位置が前倒しされるだけです。OTHER、sort、trigger の受理集合は不変です。

RB4 — refuted: 既存 test の期待値は変更されていません。test file の差分は 177 行追加、削除 0 行で、既存の固定 ID 期待値も残っています [test_p3_b4_closed_critic.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/tests/test_p3_b4_closed_critic.py:3081)。skip、期待値緩和、既存 node の置換もありません。

RB5 — refuted: `site_policy.socket` は test 間や xdist worker 内へ漏れません。autouse と test 本体は同じ function-scope `monkeypatch` fixture を共有します。undo は逆順なので、N2 の2周目→1周目→autouse 値→元 module の順で復元されます。途中 assertion が失敗しても teardown は実行されます [conftest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/tests/conftest.py:239)。

RB6 — refuted: N2 が片方だけを検査して緑になる経路はありません。2要素 tuple を直接ループし、lambda の default 引数で各 hostname も正しく固定しています [test_p3_b4_launcher.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/tests/test_p3_b4_launcher.py:365)。1周目で止まる場合は test 自体が赤になります。

RB7 — refuted: `mock.Mock(gethostname=...)` による module 代替は、この経路では壊れません。`site_policy` が `socket` から参照する属性は `gethostname` だけで、例外型や `gaierror` は参照していません [site_policy.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/campaign/site_policy.py:66)。

RB8 — refuted: N3 の live hash fixture はテストを甘くしていません。helper が現行 closure hash を record に入れるため [test_p3_b4_closed_critic.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/tests/test_p3_b4_closed_critic.py:692)、admission mismatch ではなく対象の site 射影まで到達できます。base 分岐を削除すれば、N3 の実物 `require_b4_production_context` は依然 ID 不一致で拒否します [test_p3_b4_launcher.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/tests/test_p3_b4_launcher.py:409)。

RB9 — refuted: scope 逸脱と自己申告の実体不一致はありません。commit が変更したのは launcher とその test の2 fileだけです。launcher は指定された base 分岐だけ [p3_b4_launcher.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/campaign/p3_b4_launcher.py:165)、test は import と N1からN5だけです [test_p3_b4_launcher.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/tests/test_p3_b4_launcher.py:24)。docs、台帳、禁止対象 file は未変更です。子が add、stash、branch 操作をしなかったこと自体は commit object から証明できませんが、親が commit を作ったという前提との矛盾もありません。

## scope 外だが real (裁定へ返す候補)

新規候補はありません。段4の B11 は既に裁定へ返されており、この commit は該当する `p3_s4_loop.py` や授権境界を変更していません [s4-adjudication.md](/home/SFC/tanab/.claude/jobs/f8a552e6/tmp/t2316/s4-adjudication.md:51)。

## 総括

実装本体の受理集合と2 file の scope は裁定どおりです。一方、追加 test は新たに拒否すべき LOGIN / SUSPECT を固定しておらず、その fail-close を失う変異を見逃します。N2 には失敗 site を表示できない診断上の欠陥もあります。

pytest は実走していません。結論は指定資料、対象 commit、静的な呼び出し経路の読解だけに基づきます。