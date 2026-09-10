対象は `s5-author.md` が報告した「3 file・78 行追加」の段5 snapshot。調査中に別 fix を含む `296486c7` が worktree に反映されたため、BLOCKER 1 は修正前 snapshot `64808422` との差分に対する所見である。

### BLOCKER 1 — 独立 inventory mirror が更新されていない

- 主張: 3 pin・同一ファイル内 collateral mirror・filename tuple だけでは閉じていない。段5差分は独立期待集合 `EXPECTED_TEST_HOLD_GROUPS` と `EXPECTED_TEST_COLLATERAL_NOTES` を更新していない。
- 根拠 file:line: `s5-author.md:5-7,14` は変更を3ファイルだけと報告する。一方、修正前 `orchestrator/tests/test_hold_inventory.py:304-311` は独立集合を構築し、`set(details) == set(GROWTH_TEST_HOLDS)` を要求する。consumer は同 `:476-479,599-652`。段3も `s3-lensB.md:125` でこの mirror を明示していた。
- これが真なら何が壊れるか: 新 registry は59件、独立集合は56件のままなので、少なくとも `test_inventory_projects_exact_registered_source_sets` と `test_main_dispatches_human_and_json` が AssertionError になる。段5 snapshot は受入不能である。
- 提案: 3 node の `docs_bytes` group と3 collateral noteを `test_hold_inventory.py` に同一 patch で追加する。現在見えている `296486c7` はこの形の修正を含むが、pytest未実走なので修正済み判定は親の再検証へ残す。

### must-fix 1 — 30日判定は自分の表に反証されている

- 主張: A06/A09/A10を「30日間不変の固定用途集合」とした裁定は誤り。特に `tools/task_runs` は実際に0→7 fileへ増えている。
- 根拠 file:line: `adjudication.md:30-38` の表は `tools/task_runs` を0→7と記録しながら、直後にcopytree対象4部分木は「1 fileも増えていない」と結論する。同 `:98-102` はA06/A09/A10を不変として非比例へ分類する。実consumerは `test_codex_agents.py:37-46`、`test_dev_waves_checker.py:60-71`、`test_dev_waves_integration.py:160-165`。独立再計数でも4部分木合計は34 file / 486,395 bytesから41 file / 629,077 bytesへ増えた。
- これが真なら何が壊れるか: 段7の棚卸しが成長比例nodeを非比例と誤記し、同型の将来追加をD335から外す。`.claude/agents` も新軸で追加される設計である (`docs/axis-onboarding.md:198-201`)。
- 提案: A06/A09/A10を `growth-real / D451-not-held` へ再分類する。保留追加はしない。A10はさらにguard binding blockedを併記する。

### must-fix 2 — 機械可読 inventory が封鎖済み経路を「bypass」と報告する

- 主張: `tools/hold_inventory.py` の bypass台帳は実装と逆である。
- 根拠 file:line: `tools/hold_inventory.py:107-141` はplain runner、`--noconftest`、`--confcutdir`、direct callを `known-unresolved-bypass` とする。しかし import時は `growth_test_holds.py:640-649`、call時は同 `:593-600` がexact tokenなしを拒否する。回帰契約も `test_growth_test_holds_contract.py:788-877` で拒否を期待するのに、`test_hold_inventory.py:569-610` は古いbypass表現を固定している。
- これが真なら何が壊れるか: ユーザー向けhold inventoryが実効受理集合を偽って報告し、テストもその誤報を正解として通す。
- 提案: 4経路を `refused-without-exact-token` 等へ更新するか、bypass surfaceからclosed surfaceへ分離し、inventory goldenも同時更新する。

### nit 1 — `full documentation corpus` は過大表現

- 主張: 追加rowのreasonは `check_docs.py` が全文書corpusを読むと断定するが、実装は明示 `LIVING_DOCS` と選択的globである。
- 根拠 file:line: `growth_test_holds.py:84-87` 対 `tools/check_docs.py:47-87,1999,5258-5267,5405`。
- これが真なら何が壊れるか: 比例判定自体はarchive等で成立するが、machine-readable reasonが実際の入力閉包より広い。
- 提案: 「growing living-doc/archive/handoff sets」のように実際の成長集合を名指しする。

### REFUTED — guard binding の実在consumer BLOCKER

- 主張: live repoのimport/runpy/spec/subprocess/hook/tool/CI/docs閉包に、pytest外で `test_check_docs.py` を読み込む正規consumerは確認できなかった。
- 根拠 file:line: 唯一の動的全hold importは、既にpytest session内の `test_growth_test_holds_contract.py:672-680`。`tools/codex_reasoning_ab.py:85-102,143-156` の参照は歴史snapshot用データでありmodule実行ではない。
- これが真なら何が壊れるか: 現時点では裁定 `adjudication.md:85-94` のguard可判定は維持される。
- 提案: 追加変更不要。ただし新しいplain consumerを作る変更では同じ閉包探索を再実施する。

### REFUTED — 通常collection・xdistで全fileがerrorになる

- 主張: 通常pytestとxdist workerでは、test module import前にenforcement IDが立つ。
- 根拠 file:line: `conftest.py:616-620` がconfigure時にmarkし、pytest 9.1.1の `_pytest/main.py:326-330,380-394` はconfigure後にcollectionする。xdist 3.8.0も `xdist/remote.py:420-427` から同じcmdline lifecycleへ入る。skipは `conftest.py:404-414` の一致nodeだけに付く。
- これが真なら何が壊れるか: 既定走行では3 held nodeだけがskip候補となり、他302 functionはguardでwrapもskipもされない。
- 提案: 変更不要。`--noconftest` 等は意図したfail-closed errorであり、通常collection回帰とは分けて記録する。

## 総括

- BLOCKER: 段5の3-file snapshotは `test_hold_inventory.py` の独立mirror漏れで受入不能。
- BLOCKER修正らしき変更は現在の `296486c7` に見えるが、未実走なのでclosedとはしない。
- must-fix: A06/A09/A10の30日不変判定は、裁定自身の0→7 fileという実測に反する。
- must-fix: hold inventoryの4 bypass記述は二層guardの実効挙動と逆である。
- nit: `full documentation corpus` は実際の選択的入力閉包へ狭めるべき。
- guardの正規plain consumerは見つからず、この焦点の追加BLOCKERはなし。
- 通常pytest・xdistのconfigure→collection順は静的に成立している。
- pytestは一切実行しておらず、緑は主張しない。