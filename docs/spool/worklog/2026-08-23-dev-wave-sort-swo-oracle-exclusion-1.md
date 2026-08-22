---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-23
wave: dev-wave-sort-swo-oracle-exclusion
seq: 1
title: test_sort_swo_oracle.py を受入全走から恒久除外する機構を新設し、除外が別の防壁を壊す経路 3 本を塞いだ (branch worktree-dev-wave-sort-swo-oracle-exclusion)
---

## 本文

- ユーザー裁定 {{D:sort-swo-oracle-removal}} の実装 wave。可否は裁定済みで、本 wave は実装だけを行った。
  裁定内容と D532 との supersede 関係は同 D、実装機構の裁定は
  {{D:sort-swo-oracle-exclusion-mechanism}} を正本とする。
- **除外そのものより「除外が別の防壁を壊さないようにする」ことが作業の本体だった。**
  素朴に `--ignore` を注入する実装は、次の 3 経路で正しさ防壁を緩めていた。3 本とも
  実測または敵対レビューでしか見つからなかった。
  1. `orchestrator/tests/conftest.py` の growth hold 完全収集判定は、起動引数に `--ignore` が
     1 つでもあると偽を返し、registry の hold が収集から欠落しても `UsageError` を出さない。
     注入がそのままこの防壁を無効化していた (段 3 レンズ B が発見、親がコードで裏取り)。
  2. 契約 literal を runner と conftest に二重定義すると、片方だけ書き換えたとき payload 不一致で
     同じ防壁が**黙って**外れる (fail-open)。親と段 6 レビュー 2 本が独立に指摘。
     `os.path.abspath` と `Path.resolve` の正規化差でも同じ破れ方をする。
  3. runner 側で除外内容を stderr へ出す案は、**repo の絶対 path を stderr へ漏らさない既存ガード**
     (`test_bootstrap_failure_emits_diagnostic_and_preserves_rc_output`) と、受入走の stderr が
     完全に空であることを固定する述語を破った。親が焦点走で実測し、撤回を裁定した。
     非沈黙の要件は除外が実際に効く層 (pytest 側) で満たされている。
- 注入条件は `_is_acceptance_run(args)` に一本化した。9 パターンを実行検証し、
  引数なし・`-q`・`--rootdir .`・既定 target の明示 (絶対/相対とも) では注入され、
  `-k` だけ・`--collect-only`・ユーザー `--deselect`・対象 file の明示指定では注入されないことを確認した。
  `_is_full_suite` では既定 target の明示走行が False になり迂回を塞げないため、この述語は使えない。
- **前提の訂正 2 件。** (a) 除外対象 file の実行時間は些少である
  (clean worktree で `26 failed, 36 passed in 2.81s`)。41 分の実体は非帰属判定であり、
  除外の効果は受入 wall の短縮ではなく判定器の入力を空にすることである。
  (b) production の sort SWO oracle について、`critic/digest` は直接 caller ではなく下流 consumer で、
  実際の caller は `s1_direct_comparison` / `p3_s4_loop_sort` / `s8b_*` である。
  段 1 brief の記述を本 entry で訂正する。
- **変異検査は probe までで打ち切った。** 事前登録した 6 変異は probe 走で**全件が実際に殺され**、
  落ちる node の完全集合も観測できた (M1=9 / M2=8 / M3=5 / M4=1 / M5=1 / M6=3、baseline は赤ゼロ)。
  とくに M1 (受入形以外へも注入する = 過剰除外) は `test_growth_test_holds_contract.py` 側の
  2 件まで落とし、M4 (conftest が裁定済み除外を認識しない = 防壁が黙って外れる) は防壁維持テストを
  ちょうど 1 件落とす。単一理由性と過剰除外の検出力はここで示せている。
  KILLED 期待での正式再走はユーザー指示により中止した (下記)。
- **ユーザー指示で計算ノード job を停止した。** 変異の正式走で投入した `938251.nqsv` が
  経過 3401 秒・累積 CPU 80432 秒に達し、ユーザーから「テストは最悪 5 分まで」との指摘を受けて
  `qdel` した。原因は親の対象選定ミスで、**変異対象の焦点走に
  `test_growth_test_holds_contract.py` を選んだこと**である。この file は入れ子でスイート全体を
  subprocess 実行するメタテストを含むため、「2 file の焦点走」に見えて実際には変異ごとに
  全スイートが回っていた。証拠として worktree 直下に、指定していないテスト群
  (`izanagi_camp_*` / `izanagi_critic_*` / `izanagi_pipe_*` 等) の残骸が 699 件生成されていた。
  同じ 2 file を通常の焦点走で回すと 26.7 秒で終わる。**テストが重いのではなく対象選定が誤り**である。
  停止後に変異を復元し、残骸 699 件を除去して tree を clean へ戻した。
- 並行 5 セッションから、この 26 件が受入判定器の 41 分の直接原因であり、本 wave の着地が
  複数 wave の land を解く経路だという実測が届いた。優先順位を land へ切り替えた。
- 段 6 で親が実測した赤のうち 2 件は本変更に起因しなかった。いずれも既知失敗の再発として記録した
  (F373 の色環境、F457 の `/tmp/.git`)。段 6 の fix 子が親の未追跡 fragment を削除した件も
  F106 の再発として記録した。

## 次の一手差分

### 新規

- {{T:selection-exclusion-receipt-evidence}} **P2・新規**: 恒久除外集合を task-run receipt /
  aggregate / acceptance launcher receipt へ証跡化し、「full を名乗るのに全走でない」状態を
  受入結果の同一性から検出できるようにする。本 wave は編集面が 5 file 以上増える schema 移行を
  段階導入 (規律 5) の観点で scope 外とし、実行時 fail-closed で最小構成に閉じた。
  正本 = {{D:sort-swo-oracle-exclusion-mechanism}}。
- {{T:mutation-target-must-not-be-suite-spawning-metatest}} **P2・新規**: 変異 harness の
  焦点走対象に、入れ子でスイート全体を subprocess 実行するメタテスト file
  (`test_growth_test_holds_contract.py` 等) を選ばせない仕組みを入れる。
  本 wave では親がこれを選び、2 file の焦点走のつもりで累積 CPU 80432 秒を消費した。
  対象 file 集合の事前検査 (nested full-suite spawn の静的検出) か、
  harness 側の所要見積りに実測を反映する形を検討する。
- {{T:sort-swo-oracle-restore-after-masstree}} **P3・新規**: masstree の `config.h` 欠落が
  解消したら、`tools/run_tests.py` の恒久除外表から該当 entry を 1 件削って
  `orchestrator/tests/test_sort_swo_oracle.py` を受入全走へ復帰させる。
  復活は表の 1 entry 削除だけで完了し、そのとき既定 command が変更前の形へ戻ることは
  テストで固定済み。正本 = {{D:sort-swo-oracle-removal}}。
- {{T:selection-contract-module-naming}} **P3・新規**: 共有契約 module
  `orchestrator/test_selection_contract.py` は production module でありながら pytest の
  収集パターン `test_*.py` に一致する。現状は `testpaths` が `orchestrator/tests` に
  限定されているため誤収集されず、自走 harness メタテストの走査対象
  (`os.listdir(orchestrator/tests)`) にも入らないが、収集範囲が広がると潜在的な偽緑面になる。
  改名は成果物影響を 1 行で書けないため本 wave では nit として見送った。
- {{T:dw-o18-color-env-rule-needs-budget}} **P2・ユーザー裁定待ち**: F373 (親セッションの色強制が
  pytest の要約行を汚し無関係な node を落とす) の恒久対応「`FORCE_COLOR`/`COLORTERM` を外して
  起動する」を `DW-O18` へ入れようとしたが、**節の byte 予算に収まらない**。
  最小形 (`起動は \`FORCE_COLOR\`/\`COLORTERM\` を外す (F373)。`) でも 1055 bytes > 1000 bytes。
  DW-O18 の既存本文を圧縮すると安全義務か exact pin を壊す危険があり、予算値を上げる変更は
  自己改善契約で独立審査対象と定められている。本 wave では入口を編集せず裁定へ返す。
  F373 は本 wave で 3 度目の再発であり、機械強制も入口記載も無いまま各 wave が同じ偽赤を踏み続ける。
