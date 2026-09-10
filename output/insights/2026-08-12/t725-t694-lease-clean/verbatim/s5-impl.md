実装済み・未実走です。指定された 2 ファイルだけを編集し、docs・cleanup・commit には触れていません。

## 変更前の挙動

- `_identity_preflight` は `git status --porcelain --untracked-files=no` の stdout が空なら受理していました。tracked/index の変更や表示対象の submodule dirt は拒否しますが、untracked-only の木は受理し、claim へ進んでいました。
- merge message は、message file の存在・読取、非空、行頭 `AI-Agent:` の存在、`git commit --dry-run -F`、commit 後 message に同じ行が残ることを検査していました。`AI-Agent:` の product/model/reasoning/role 形式は検査していませんでした。
- claim 成功後から受入 command 投入直前までに、木の dirty 状態を再検査する段はありませんでした。

## 実装内容

- plan v2-1: [tools/dev_wave_wait.py:553](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/tools/dev_wave_wait.py:553)
  - `preflight-clean` を `git status --porcelain --ignore-submodules=none` に変更。
  - untracked-only も claim 前に rc=2 で拒否します。

- plan v2-2: [tools/dev_wave_wait.py:879](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/tools/dev_wave_wait.py:879)
  - merge 成功後、commit dry-run 前に `check_ai_provenance.py --message-file` を追加。
  - stage は `merge-message-provenance`。失敗時は既存の merge abort + release 経路です。

- plan v2-3: [tools/dev_wave_wait.py:919](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/tools/dev_wave_wait.py:919)
  - `commit-head-postcheck` 後に無条件の `prerun-clean` を追加。
  - stdout 非空を rc=70 とし、検出した status path を stderr へ出します。
  - ACQUIRED/HELD_SELF の帰結は既存 cleanup に委譲しています。

テスト側では [test_dev_wave_wait.py:37](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/orchestrator/tests/test_dev_wave_wait.py:37) の共通 argv、[test_dev_wave_wait.py:196](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/orchestrator/tests/test_dev_wave_wait.py:196) の queue helper、[test_dev_wave_wait.py:1313](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/orchestrator/tests/test_dev_wave_wait.py:1313) の `_STAGES` を更新しました。指定された既存 7 定義・8 case にも新段を正しい順序で追加しています。

## 新設テストと変異

1. `test_prerun_clean_allows_acceptance_submission_without_release`
   - M6: clean 木まで常時拒否する過剰拒否を殺す。

2. `test_prerun_tracked_dirty_blocks_submission_and_releases`
   - M1: gate 削除を殺す。
   - M2: stdout 判定の恒真化を殺す。

3. `test_prerun_untracked_dirty_blocks_submission_and_releases`
   - M1/M2を untracked-only 入力でも殺し、新述語を固定する。

4. `test_postmerge_tracked_dirty_blocks_submission_and_releases`
   - M1: prerun gate 削除を殺す。
   - M5: `behind == 0` 限定への退行を殺す。

5. `test_held_self_prerun_dirty_blocks_without_releasing_lease`
   - M1を殺し、HELD_SELF の release 権限を誤って広げる変更も検出する。

6. `test_malformed_ai_agent_message_fails_provenance_before_commit`
   - M4: provenance checker 呼出し削除を殺す。
   - 非空で `_message_has_ai_agent` を通る通常の Git messageを使い、checker の非0だけを失敗理由にしています。必須順序上、checker 失敗後の dry-run は投入されません。

7. `test_preflight_untracked_dirty_rejects_before_claim`
   - M3: `--untracked-files=no` への巻き戻しを、rc=2・stage・claim 不投入まで exact に検出する。

8. `test_real_git_dirty_after_claim_blocks_acceptance_command`
   - M1/M2を実 subprocess・実 Git 配線で殺し、command sentinel 不出力と lease release を確認する設計です。

各 fake 負例は rc、stage、exact event 列、command/release/abort、`assert_drained()`を併せて検査しています。

## 所有外への波及可能性

`rg` で確認した範囲では、所有外に Python import/runtime launcher はありません。運用上の起動元・consumer は次です。

- [.claude/commands/dev-wave.md:52](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/.claude/commands/dev-wave.md:52): acceptance/release の標準手順。
- [docs/dev-wave/operations.md:11](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/docs/dev-wave/operations.md:11)、[docs/dev-wave/core.md:17](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/docs/dev-wave/core.md:17): producer/waiter consumer。
- [docs/pegasus-runbook.md:777](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/docs/pegasus-runbook.md:777): 実運用 acceptance 起動例。
- [tools/check_docs.py:3918](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/tools/check_docs.py:3918) と [test_check_docs.py:5897](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/orchestrator/tests/test_check_docs.py:5897): canonical waiter consumer pin。
- [test_mutation_fanout.py:877](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/orchestrator/tests/test_mutation_fanout.py:877): mutation fanout command に waiter を混入させない制約。
- 共有 fixture は所有ファイル内の `_FakeEffects`、`_RoutingAcceptanceEffects`、`_PREFLIGHT_EVENTS`、実 Git temporary-repo helper です。全 status 応答と既存 real-Git fixtureを新述語へ更新しました。

## 期待赤と静的 finding

テストは実走していません。runbook §7.3やF191 erratumの未 landだけを理由に赤になるテストは、静的検索上ありません。`test_dev_wave_waiter_consumer_pins_accept_current_docs_contract` はrunbook/F191本文を検査しないため、これを含め赤が出れば回帰として扱うべきです。

親が並行編集した [docs/pegasus-runbook.md:830](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/docs/pegasus-runbook.md:830) には、現時点で「provenance checker → merge」の順序が書かれています。実装・裁定は「merge → provenance checker → dry-run」であり、checker 非0時に `merge --abort` へ載せる契約なので、docs 側で順序訂正が必要です。この docs 差分は私の編集ではありません。

静的確認として、対象 2 ファイルの `git diff --check` は問題ありませんでした。

## 総括

- 編集ファイル:
  - `tools/dev_wave_wait.py`: 1,134行、差分 +25/-1
  - `orchestrator/tests/test_dev_wave_wait.py`: 3,108行、差分 +662/-28
- 新設テスト: 8本
- 状態: **実装済み・未実走**
- 未解決・要判断:
  - 親によるテスト実走・mutation/acceptance確認が必要。
  - runbookのprovenance/merge順序を実装契約へ合わせる必要あり。
  - F191 erratumは親のdocs作業として未 land。