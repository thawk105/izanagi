## 総括

静的レビュー結果は **must-fix なし、承認相当**です。pytest は実走しておらず、緑とは判定しません。

同じ repository 状態で競合が増えない前提なら、F851 の `/scr/.../job-repo` 2 登録はいずれも `FileNotFoundError` を経て絶対 path のまま保持され、`/tmp/izanagi-fold-gate-*` と重ならないため、旧 `rc=31 / fold-gate-failed` は発生しません。以降にも `/scr` 登録を理由に赤になる箇所は見つかりませんでした。

T9 は `(RC_OK, "landed")`、T10 は現行どおり `(RC_DIRT, "rejected")` を厳密に固定しています。追加テストが共有 repo `/work/1/SFC/tanab/izanagi/.git` へ worktree を登録する経路もありません。

## must-fix 所見

なし。

## nit / backlog

1. T4 の名前・説明は、証明している範囲より少し強いです。実際の assert は改行を含む `linked` 自体ではなく、porcelain の最初の改行までの `raw_prefix` が返ることを確認しています。[test_dev_wave_land.py:9134](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2347-scr-worktree-land/orchestrator/tests/test_dev_wave_land.py:9134)

   根拠 / land 値: **real** — 現行の行走査契約および marker 除外変異の kill には十分だが、lossless な改行 path 復元の証拠ではない。放置しても F851 の rc/status は変わらない。

2. T9 は不在登録を 1 本だけ作り、F851 逐語の「同時に 2 本」は再現していません。[test_dev_wave_land.py:9288](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2347-scr-worktree-land/orchestrator/tests/test_dev_wave_land.py:9288)

   根拠 / land 値: **real だが裁定違反ではない** — 裁定の T9 は単数の不在登録を要求し、実装は全行を同じループで処理するため現在の 2 本も通る。放置時の現実装は `landed` のままだが、将来「最初の不在登録だけ受理」という回帰は T9 をすり抜けうる。

3. テストコストは軽微とは言いにくい規模です。T1〜T10 は parametrization を展開すると 12 case、12 個の standalone repo、12 個の通常 wave と 8 個の detached worktree、すなわち `git worktree add` 20 回です。primary worktree も含めると延べ 32 worktree directory を作ります。`land()` は 2 回、`_execute_fold_gate()` は 3 回です。T10 は dirt preflight で止まるため fold gate を走らせません。

   根拠 / land 値: **real** — 静的下限でも約 200 回の Git subprocess に加えて 2 回の land があり、serial では数秒、遅い共有 filesystem では十数秒程度の上積みが見込まれる。放置しても land の rc/status は変わらず、suite 時間だけが増える。

## 反証した懸念

4. **F851 が二本目の `/scr` 登録や downstream revalidation で再び赤になる懸念は refuted。**

   実行順は `_locked_preflight` → fold planning → `_run_fold_gate` → `_execute_fold_gate` → `_registered_worktree_paths` です。[dev_wave_land.py:3449](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2347-scr-worktree-land/tools/dev_wave_land.py:3449) では各 `/scr/...` を独立に処理し、`resolve(strict=True)` の ENOENT を `absolute()` に落とします。その後の overlap は `/tmp/...` 対 `/scr/...` なので偽です。[dev_wave_land.py:3805](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2347-scr-worktree-land/tools/dev_wave_land.py:3805) 再取得後の `_control_snapshot` は `.claude/worktrees` と `.codex/worktrees` の filesystem child を見るだけで、外部 `/scr` 登録を再解決しません。

   根拠 / land 値: **refuted** — 同じ状態なら旧 `(31, "fold-gate-failed")` は除去され、他の通常 gate が通れば `(0, "landed")` まで進む。`/scr` 登録そのものを理由にした別の赤はない。

5. **T9 が「例外が出なかった」だけの弱いテストという懸念は refuted。**

   T9 は実 `land()` を通し、結果を `(LAND.RC_OK, "landed")` と完全一致で確認します。[test_dev_wave_land.py:9341](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2347-scr-worktree-land/orchestrator/tests/test_dev_wave_land.py:9341) さらに不在登録と admin directory が land 後にも残ることを確認しています。

   根拠 / land 値: **refuted** — 旧 `(31, "fold-gate-failed")` は必ず assert failure となり、別の非例外 status も成功扱いされない。

6. **T10 が期待値を新実装へ合わせて変更した懸念は refuted。**

   dirt は `_Repo.add_wave()` が作った実在 linked landing-wave worktree に追加されます。`_locked_preflight` の `_verify_wave_clean` が現行 `RC_DIRT=20` を返し、`land()` の外側が現行 status `"rejected"` に畳みます。T10 はその完全な pair を要求し、main HEAD と dirt bytes の不変も確認します。[test_dev_wave_land.py:9357](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2347-scr-worktree-land/orchestrator/tests/test_dev_wave_land.py:9357) 既存の直接契約テストも同じ plain untracked dirt と `RC_DIRT`、理由文字列を固定済みです。[test_dev_wave_land.py:8220](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2347-scr-worktree-land/orchestrator/tests/test_dev_wave_land.py:8220)

   根拠 / land 値: **refuted** — 放置時も dirt ありは `(20, "rejected")`、dirt を誤受理する変更では T10 が赤になる。

7. **追加 fixture が共有 repo の `.git` を汚染する懸念は refuted。**

   `_Repo` は `tempfile.TemporaryDirectory` 内で新規 `git init` し、全 helper は `repo.main` に対して `worktree add` します。[test_dev_wave_land.py:148](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2347-scr-worktree-land/orchestrator/tests/test_dev_wave_land.py:148) detached、不在、改行 path はすべて `repo.root` 配下です。`ROOT` は production module の import にしか使われません。

   根拠 / land 値: **refuted** — 共有 registry には登録されず、将来の共有 land を rc=31 にする残骸は作らない。

8. **fixture cleanup 漏れの懸念は refuted。**

   `_repo` の `finally` が synthetic repo・その `.git/worktrees`・全外部風 path を同じ temporary root ごと削除します。不在 path の admin directoryもその root 内です。T1 の残る isolation directoryも root cleanup 対象、T8 は context `finally` で明示削除、T9 の実 fold isolation `/tmp/izanagi-fold-gate-*` は production の `TemporaryDirectory` context が削除します。

   根拠 / land 値: **refuted** — 放置後に登録や改行 path は残らず、後続 land の rc/status に影響しない。

## 波及の列挙 (参照関係で引いた結果)

9. production の参照鎖は一本です。

   `_registered_worktree_paths`
   → `_execute_fold_gate`
   → `_run_fold_gate`
   → `land`
   → CLI `main`

   根拠 / land 値: **real** — production の直接 caller は `_execute_fold_gate` だけで、変更は非-noop fold gate にのみ波及する。正常に解決できる既存登録の値は従来と同一なので、通常 land の rc/status は変わらない。

許可された consumer test 内の参照結果は次のとおりです。

- 実 `_registered_worktree_paths` を通る既存 consumer:
  - `test_fold_gate_exports_full_tree_applies_raw_bytes_and_runs_one_pytest`
  - `test_fold_gate_tmp_isolation_preserves_main_and_wave_status_bytes` の 2 case

- `_registered_worktree_paths` を monkeypatch して変更を迂回する既存 consumer:
  - `test_fold_gate_missing_junit_reports_bounded_escaped_child_output`
  - `test_fold_gate_real_argv_environment_create_junit_in_gitless_tree`

- 新規直接 consumer:
  - T1・T8: `_execute_fold_gate`
  - T2〜T7: `_registered_worktree_paths`
  - T9: `land()` から間接到達
  - T10: dirt preflight で停止し、fold gate には到達しない

- 共有 fixture `_Repo` / `_repo` は変更されていません。追加された `_add_detached_worktree`、`_worktree_porcelain`、`_verified_repository` は新規 T1〜T10 からしか参照されません。

なお「`orchestrator/tests/` 全体を module 名で検索」は、指定された絶対 path 以外を読まないという射影制約に抵触するため実行していません。許可された `test_dev_wave_land.py` 内では、module は [test_dev_wave_land.py:32](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2347-scr-worktree-land/orchestrator/tests/test_dev_wave_land.py:32) で path 経由ロードされ、上記以外の `_registered_worktree_paths` 参照はありません。したがって他 test file に consumer がないとは主張しません。

## 変異帰属の検査

10. M1〜M8 を先に kill する既存テストは、許可された consumer test 内にはありません。

   根拠 / land 値: **refuted** — 新規ブロック以前のテストには `_registered_worktree_paths`、`prunable`、空一覧、Permission/Unicode resolve、registered overlap の assert がなく、既存 `_execute_fold_gate` consumer は正常な実在登録か monkeypatch 済みである。既存テストだけなら各変異は land 判定の誤りを見逃すため、本 wave のテスト効果の帰属は成立する。

| 変異 | 既存テストによる先行 kill | 新規テスト内の kill |
|---|---|---|
| M1: `FileNotFoundError` → `OSError` | なし | T5 permission |
| M2: 不在 path を捨てる | なし | T2、T7、T8 |
| M3: `strict=False` | なし | T5 permission |
| M4: `UnicodeError` を fail-closed から外す | なし | T5 unicode |
| M5: `prunable` marker で除外 | なし | T2、T3、T4、T7 |
| M6: 空判定を削除 | なし | T6 |
| M7: overlap 拒否を無効化 | なし | T1、T8 |
| M8: `worktree prune --expire now` を追加 | なし | T2、T3、T7、T8 |

複数の新規テストが同じ変異を cross-kill しますが、いずれも本 wave 内です。したがって「既存テストが先に赤を出し、新規テストの効果を示さない」変異はありません。