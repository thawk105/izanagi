## 直した内容

- must-fix 1: [_git_changed_paths](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2412-frozen-spec-fixpoint/orchestrator/campaign/floor_pair_driver.py:627) に `--ignore-submodules=none` を追加。
- must-fix 1: [模擬 Git の argv 期待](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2412-frozen-spec-fixpoint/orchestrator/tests/test_floor_pair_driver.py:353)を同じ形へ更新。
- must-fix 1: [実 Git 負例](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2412-frozen-spec-fixpoint/orchestrator/tests/test_floor_pair_driver.py:532)を追加。親 commit に `ignore = all` の `.gitmodules` と gitlink を置き、freeze commit で spec 追加と gitlink 差し替えを行う。
- must-fix 2: [blob query test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2412-frozen-spec-fixpoint/orchestrator/tests/test_floor_pair_driver.py:883)を、spec・calibration・一意な build receipt 2 件の exact multiset 比較へ強化。
- must-fix 3: [synthetic summary](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2412-frozen-spec-fixpoint/orchestrator/tests/test_p3_b4_floor_artifact_issuer.py:109)を `driver_tests.HEAD` に修正し、[既存 consumer test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2412-frozen-spec-fixpoint/orchestrator/tests/test_p3_b4_floor_artifact_issuer.py:504)で実際に load した spec との一致を検査。

## 変更後の挙動

通常の spec-only freeze commit は引き続き受理対象です。

`.gitmodules` の `ignore=all` により隠される submodule pointer 更新も差分へ強制的に現れるため、spec と gitlink を同時変更した freeze commit は拒否されます。

test fixture の summary は、親 `source_commit` ではなく実際の `loaded_head` を記録します。issuer production 側への新しい比較 gate は追加していません。

## 新設 test の帰属

- gitlink 負例は M08 専用です。親関係、spec blob、calibration、receipt は正当で、拒否点は changed-path exact 判定だけです。オプションを除去すると gitlink が `ignore=all` に吸われ、`pytest.raises(..., match="changed paths")` が成立しません。
- 強化した blob test は現在の fixtureで exact 4 queryを要求します。spec、calibration、candidate receipt、reference receipt のいずれかを削除、または symbolic `HEAD:` に戻すと `Counter` 比較だけが失敗します。calibration verifier は模擬済みで、他層には吸われません。
- consumer assertion は summary を旧親 `C` に戻す変異を直接検出します。production issuer はこの不一致を拒否しないため、別 gate に吸われません。

## 実走した検査

実装済み・未実走です。

- `test_real_git_spec_and_ignored_gitlink_in_freeze_commit_are_rejected`
  - 通常 dispatch: harness rc=16、子未開始。
- 上記と `test_blob_queries_use_the_once_resolved_loaded_head`、`test_authority_issue_is_create_only_exact_and_loadable`
  - `--force-dispatch`: harness rc=16、子未開始。
- 原因はいずれも `qstat -Q preflight rc=1`。各 nodeid の pytest rc は取得できていません。
- 指定3ファイルの `ast.parse`: rc=0。
- 指定3ファイルの `git diff --check`: rc=0。
- 対象ファイル全体および full suite は未実走です。

失敗 dispatch が生成した固有 receipt ディレクトリ2件は除去し、指定外の生成物を残していません。

## 波及可能性

共有 `_install_git` の呼び手は静的に全列挙済みです。

- `test_floor_pair_driver.py`: 451, 484, 669, 765, 791, 812, 824, 850, 863, 872, 887, 934, 1024, 1052, 1069, 1105, 1139, 1157, 1176, 1233, 1250, 1265, 1285, 1297, 1316, 1343, 1656, 2195, 2378
- `test_p3_b4_floor_artifact_issuer.py`: 66

共有 `_synthetic_source` の15呼び手は同ファイルの 257, 282, 301, 315, 334, 375, 395, 423, 436, 485, 504, 562, 583, 628, 657 です。

新しい subprocess site は追加していません。指定外の production issuer、schema、exact key 集合、既存の `acceptance_duration_ledger.json` と `test_ccbench_spawn_sites.py` には触れていません。

## 未了・判断を仰ぐ点

pytest 子が開始されなかったため、clone なしの gitlink 構築を含む実 Git 負例は live 未確認です。queue infrastructure 復旧後に上記3 nodeidの再実走が必要です。

裁定外の issuer production gate は意図どおり未実装で、追加判断事項はありません。

## 総括

fix2 must-fix 1〜3を指定3ファイルへ反映しました。  
submodule ignore の穴、blob比較削除変異、旧 loaded-head fixture をそれぞれ直接固定しています。  
静的検査は rc=0ですが、pytest は dispatch infrastructure failure のため未実走です。  
commit、指定外編集、scope外 hardening は行っていません。