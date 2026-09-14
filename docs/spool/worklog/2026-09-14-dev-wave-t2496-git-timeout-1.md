---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-14
wave: dev-wave-t2496-git-timeout
seq: 1
title: [T-2496] run_trial 経路の git 呼び出しへ hard timeout を入れた (コード + テスト、branch worktree-dev-wave-t2496-git-timeout、変異 matrix = baseline PASSED・6/6 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- **ユーザー直接依頼の wave。** scope は「timeout を渡す局所修正まで。監視 framework や汎用
  watchdog は作らない。仮想リスク向けの gate・検査・台帳・一般化は scope 外」。この裁定に
  従い、他 module の git helper・`executor`・`max_wall_s` の意味変更はいずれも実装していない。
- 設計判断は {{D:trial-registry-git-hard-timeout}}。実測・変異・保証の限界は
  `output/insights/2026-09-14_t2496-git-timeout/README.md`、子の逐語は同 `verbatim/`。
- **段 3 の 2 レンズが独立に同じ穴を指摘し、親が採用した。** 段 2 plan の追加テストは 3 件とも
  予算を明示引数で渡す形だったため、**本番既定値だけを無効化する誤実装が素通りする**。本番 16
  呼び出しは引数を渡さないので、それでは timeout が効かない。既定値の束縛と、その値が
  `subprocess.run` へ実際に届くことを検査する node を足した。
- 段 3 luna の是正も 3 件採用した。(a) 実 repo を使う負例に `timeout_s=1.0` を課すのは根拠が無く、
  短い予算が間欠赤を生む (本 wave の問題設定と逆行する) ため、正常完了側の負例は production
  既定値で走らせる。(b) **D265 は固定 300 秒を裏付ける裁定ではない** — ruleops について
  「BASE 20 秒 + 作業量比例、CAP 300.0」を決めたものなので、300.0 は「実測で安全を証明した値」
  ではなく暫定運用値と記述する。(c) 集約の限界を具体例まで書く。
- 段 3 sol の負例強化も採用した (非 0 rc の負例を 1 本追加)。ただし提案された rc=0/1/128 の
  3 本は受入枠を無駄に使うので 1 本に絞った。
- **段 6 レンズ A が親の変異設計の欠陥を本走前に指摘した。** 当初登録した M4「予算定数を
  0.001 秒にする」の期待赤 3 件は、**shim が 1 ms 以内に終われば負例が緑のままになりうる
  タイミング依存の期待**で、`DW-M08` の完全集合要件を満たさなかった。決定的な 2 変異
  (`check=False` → `check=True`、`stdout=PIPE` → `None`) へ差し替え、M5 も `timeout=0.25` では
  負荷依存だったので `timeout=30.0` に変えて期待赤を確定した。型は F28 と同じで再発として記録した。
- **段 6 の 2 レンズはいずれも実装の欠陥を出していない。** spawn-site 登録簿の件数 1 は走査規則上
  不変、既存の `_git` monkeypatch 2 箇所は二引数のままで無傷、scope 逸脱なし。
- **不採用にした段 6 所見 2 件。** (a) 例外処理中の attempt 終端記録が失敗すると後続の lifecycle
  後始末へ届かない経路は、**非 0 rc でも同じ既存性質**で、この差分が作ったものではない。
  timeout は新しい発火条件を足すだけである。(b) timeout の診断文が 16 箇所すべてで同一になる件は
  改善余地だが、放置時に成果物の値・受理集合・参照がどう変わるかを書けないので `DW-G05` により
  must-fix にせず新規項目へ送った。
- **段 3 sol が挙げた「partial report の payload に status complete が残りうる」は refute せず
  scope 外とした** — [T-2497] として既に起票済みの項目である。
- 親が実測した git 呼び出しの所要 (login node、load 57〜81、10,369 commit / 24,757 tracked file) を
  予算の根拠にした。単一呼び出しの最大は `rev-list --all --topo-order --reverse` の 6.954 秒
  (4 回で 5.031 / 5.868 / 6.954 / 4.015)。CPU 時間はいずれも 0.2 秒未満で I/O 待ちが支配する。
  標本は 4 点であり、尾部確率の根拠にはならないと段 3 luna が指摘したとおり記述を弱めた。
- 実走: 変更した test file の単独走 rc=0 / 252 passed / 16.42 秒。consumer 焦点走 20 file
  (producer・spawn-site 登録簿・attempt registry・reflux・s8c 事前登録・layer3 ほか)
  rc=0 / 2328 passed / 5 skipped / 115.49 秒。`check_ai_provenance.py` rc=0 (9831 件、新規違反なし)。
- **セッション異常 2 件。** (1) wave slug に `git` を含めたため、worktree 絶対 path を含む複合 shell
  を guard が「git を名指しする検証不能な形」として拒否した。単純形へ分解して回避した。
  (2) 親が検査を 2 度パイプへ通し、集計行と rc を落として走らせ直した。1 度目は受入でなく焦点走
  だったので実害は queue 待ちの再消費だけである。
- 子は段 2 plan 1 本、段 3 consult 2 本、段 5 author 1 本、段 6 review 2 本の計 6 本。
  実装子は自走 harness が file 全体 715 秒で予算外と判断し、正直に「実装済み・未実走」と報告した。
- **段 8 の自己改善候補 1 件は収容できず「実施しない」で閉じた。** 候補は上記のセッション異常 (1) を
  「wave slug に `git` を含めない」として手順へ入れること。同形の command で path に `git` を含む
  ときだけ拒否される A/B を実測して裏取りした。収容を 2 か所で試したが、`DW-C01` は
  `check_docs.py` の exact 契約で節全体が pin されており、かつ追記で 1137 bytes > 単節予算 1000 bytes。
  `DW-O20` も 1109 bytes > 1000 で入らなかった。独立 3 例に満たないので D730 の例外収容は取れず、
  D782 に従い上限を引き上げずに閉じた。安全義務の削減による捻出は行っていない。

## 次の一手差分

### 完了

- [T-2496] `trial_registry._git` へ 300.0 秒の hard timeout を入れ、timeout を fail-closed の
  拒否へ写した。正例・負例・機構の 4 node を同じ commit に足し、変異 6/6 KILLED で検出力を示した。
  remaining: none
  base: f7376dc82e8c3725c121ad1e7e58ef46d978336448dc1b80a6b482ff001e2b27

### 新規

- {{T:attempt-registry-history-walk-cost}} **P2・新規**: attempt registry の append-only gate
  (`_assert_attempt_registry_history_append_only`) は `rev-list --all` の全 commit を回し、各 commit で
  全 tree の `ls-tree -r` と blob ごとの `cat-file` を行う。現在は genesis
  (`output/s8c-preregistration/attempt-registry.jsonl`) が不在なので未発火だが、
  **genesis が作られた時点から production 経路 (`load_attempt_registry` と locked updater) で発火する。**
  単一呼び出しの実測 (`ls-tree -r -z --full-tree` = 1.653 秒) と現在の 10,369 commit から導くと、
  blob ごとの `cat-file` を除いても 4.7 時間を下回らない。**1 呼び出しごとの timeout ではこの loop を
  縛れない。** 発火条件と現実的な所要を実測し、走査の絞り込みか呼び出し条件の見直しを決める。
- {{T:git-operational-timeout-diagnostic}} **P3・新規**: `trial_registry._git` の timeout 診断文が
  16 呼び出しすべてで同一で、subcommand・repository・commit が分からない。`from exc` で
  `TimeoutExpired.cmd` は保持されるが、origin 境界は例外の型名と message だけを取り出すため
  報告では argv が落ちる。診断に何を載せるかを決めて足す。
