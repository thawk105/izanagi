# 実装プラン

親 brief の P1〜P4 はすべて、現行コードの制御フローと整合している。R1 は `run_acceptance` への 1 段追加と、その呼び出し順を厳密に扱うテスト更新だけで実現できる。

## 1. 挿入位置と評価順

[tools/dev_wave_wait.py:901](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/tools/dev_wave_wait.py:901) の `postcheck` と、[tools/dev_wave_wait.py:903](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/tools/dev_wave_wait.py:903)〜907 の `commit-head-postcheck` が完了した直後、現在の `acceptance-command argv=` 出力 [tools/dev_wave_wait.py:908](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/tools/dev_wave_wait.py:908) より前に次相当を挿入する。

```python
prerun_status = _run_capture(
    effects,
    ("git", "status", "--porcelain", "--untracked-files=no"),
    repo,
    "prerun-clean",
)
if prerun_status.stdout:
    raise _StageFailure("prerun-clean")
```

評価順は次のとおり。

- `behind > 0`:

  `postclaim-rev-parse` → `behind-count` → overlap 判定 → merge/commit → commit SHA・message 検査 → `postcheck` → `commit-head-postcheck` → `prerun-clean` → argv/timeout 出力 → acceptance command

- `behind == 0`:

  `postclaim-rev-parse` → `behind-count` → merge 節をスキップ → `postcheck` → `committed_sha is None` のため `commit-head-postcheck` をスキップ → `prerun-clean` → argv/timeout 出力 → acceptance command

したがって両経路とも投入直前に検査され、特に残差のある `behind == 0` 経路でも必ず通る。

## 2. 述語、argv、stage

既存の preflight は [tools/dev_wave_wait.py:552](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/tools/dev_wave_wait.py:552)〜557 で次を実行している。

```text
git status --porcelain --untracked-files=no
```

新段の argv は、要素・順序とも一字一句同じにする。stdout 判定も `if status.stdout:` とし、`.strip()` などを挟まず「生の stdout が厳密に空文字列」を成功条件にする。したがって述語は `preflight-clean` と同一である。

相違するのは失敗時の契約だけで、これは意図的である。

- git rc `0`、stdout `""`: 通過。
- git rc `0`、stdout 非空: `_StageFailure("prerun-clean")`、rc `70`。
- git rc 非 `0`: `_run_capture` [tools/dev_wave_wait.py:444](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/tools/dev_wave_wait.py:444)〜456 により、stage `prerun-clean`、rc `70`、`source_rc` に git rc を保存。
- subprocess/encoding 例外: stage `prerun-clean`、rc `70`。
- preflight 側だけは [tools/dev_wave_wait.py:526](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/tools/dev_wave_wait.py:526)〜531 が rc を `2` に写像する。新段ではその wrapper を使わない。

## 3. rc と lease の帰結

追加処理は既存 `_StageFailure` 経路へそのまま載せ、cleanup 実装は変更しない。

- `_StageFailure` は [tools/dev_wave_wait.py:940](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/tools/dev_wave_wait.py:940)〜941 で primary outcome になる。
- `finally` の [tools/dev_wave_wait.py:948](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/tools/dev_wave_wait.py:948)〜961 が必ず `_cleanup_lifecycle` を呼ぶ。
- `ACQUIRED` は [tools/dev_wave_wait.py:812](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/tools/dev_wave_wait.py:812)〜815 により release する。
- `HELD_SELF` は release せず保持し、[tools/dev_wave_wait.py:817](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/tools/dev_wave_wait.py:817)〜822 の既存警告を出す。
- release 成功なら `prerun-clean` の rc `70` を返す。cleanup が失敗した場合だけ、既存契約どおり rc `74` が primary を上書きする。

検査時点では merge commit 完了後に `merge_pending=False` となっているため、dirty 検出時は merge abort ではなく lease release のみになる。

## 4. 既存テストへの影響

### 共通 helper

[orchestrator/tests/test_dev_wave_wait.py:164](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/orchestrator/tests/test_dev_wave_wait.py:164)〜180 の `_preflight` 直後に、二回目の status 応答を明示登録する `_prerun_status` helper を追加する。

```python
def _prerun_status(
    fake: _FakeEffects,
    *,
    stdout: str = "",
    returncode: int = 0,
) -> None:
    fake.expect_run(
        ("git", "status", "--porcelain", "--untracked-files=no"),
        DW._CommandResult(returncode, stdout),
    )
```

`_PREFLIGHT_EVENTS` には追加しない。preflight status と prerun status は別イベントだからである。

### 機械的に壊れる既存テスト

`_FakeEffects.run` は未登録呼び出しを許容しない [orchestrator/tests/test_dev_wave_wait.py:81](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/orchestrator/tests/test_dev_wave_wait.py:81)〜90。以下の7テスト定義、8 collected cases が新しい status 呼び出しで壊れる。

| 既存テスト | 更新 |
|---|---|
| [test_held_and_queued_refresh_main_before_every_claim:936](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/orchestrator/tests/test_dev_wave_wait.py:936) | postcheck 応答の行945後、command 登録の行946前に `_prerun_status(fake)`。 |
| [test_acquired_reloads_main_before_behind_check:960](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/orchestrator/tests/test_dev_wave_wait.py:960) | 行966と967の間に `_prerun_status(fake)`。 |
| [test_merge_sequence_and_postcheck_are_exact:1208](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/orchestrator/tests/test_dev_wave_wait.py:1208) | commit-head 応答の行1227後、command の行1228前に `_prerun_status(fake)`。`git_mutations` の期待値は status が mutation ではないため変更せず、Fake の exact argv queue に新 argv を正しい位置で追加する。 |
| [test_acceptance_command_red_is_propagated_after_release:1545](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/orchestrator/tests/test_dev_wave_wait.py:1545) | 行1551と1552の間に helper。期待 events の行1564と1565の間にも capture=`True` の status event を追加。 |
| [test_release_failure_overrides_primary_result:1621](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/orchestrator/tests/test_dev_wave_wait.py:1621) | 行1627と1628の間に helper。期待 events の行1640と1641の間にも status event。 |
| [test_release_subprocess_failures_are_cleanup_failures:1652](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/orchestrator/tests/test_dev_wave_wait.py:1652) | 2 parameter cases とも対象。行1658と1659の間に helper、期待 events の行1673と1674の間に status event。 |
| [test_signal_after_core_success_uses_restored_real_handler:2039](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/orchestrator/tests/test_dev_wave_wait.py:2039) | 行2047と2048の間に helper。期待 events の行2090と2091の間にも status event。 |

期待 event はすべて次をそのまま追加し、部分一致への緩和はしない。

```python
(
    "run",
    ("git", "status", "--porcelain", "--untracked-files=no"),
    _REPO,
    True,
)
```

### 既存 stage harness の拡張

[test_nonzero_stage_blocks_submission_and_releases:1272](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/orchestrator/tests/test_dev_wave_wait.py:1272) は既存 case 自体は機械的には壊れないが、新 stage の非0 rc 契約を保つため必ず拡張する。

- `_STAGES` [同ファイル:1256](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/orchestrator/tests/test_dev_wave_wait.py:1256) に `prerun-clean` を `commit-head-postcheck` の後へ追加。
- 行1295〜1344と1384〜1412の到達段集合へ `prerun-clean` を追加し、それ以前の merge、commit、message、postcheck、commit-head は成功応答にする。
- `prerun-clean` case だけ status に `DW._CommandResult(9)` を登録する。
- exact event 列では commit-head event の後、unlink/release の前に status eventを追加する。
- `merge_pending` は既に false なので `_ABORT_CLEAN_EVENTS` は追加せず、release のみを期待する。

## 5. 追加テスト

[orchestrator/tests/test_dev_wave_wait.py:1913](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/orchestrator/tests/test_dev_wave_wait.py:1913) の既存 postcheck テスト直後へ、次の2本を追加する。

### 正例: clean なら command を投入

`test_prerun_clean_allows_acceptance_submission`:

1. `_preflight(fake)` で claim 前 status=`""`。
2. `_acquired(fake)`。
3. postclaim `rev-parse main` を成功。
4. `behind-count` と `postcheck` を双方 `"0\n"`。
5. `_prerun_status(fake)` で二回目の status=`""`。
6. `_COMMAND` を capture=`False`、rc `0` で登録。
7. outcome rc `0`、command event が存在し、その直前が二回目の status event、release がないことを exact に検査。
8. `fake.assert_drained()`。

### 負例: claim 後に dirty なら投入せず release

`test_prerun_dirty_blocks_submission_and_releases_acquired_lease`:

1. `_preflight(fake)` は clean。
2. `_acquired(fake)` で claim 成功。
3. postclaim main、`behind-count=0`、`postcheck=0`。
4. `_prerun_status(fake, stdout=" M tracked.txt\n")` とし、claim 後の二回目だけ dirty を返す。
5. `_release(fake)` を登録。
6. outcome の `rc == 70`、`stage == "prerun-clean"`、`source_rc is None`。
7. `_COMMAND` event が存在しないこと、status の直後に release が一度だけ行われることを検査。
8. `fake.assert_drained()`。

実 git の新規テストは追加しない。[test_default_wiring_with_real_git_and_lease_helper:2180](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/orchestrator/tests/test_dev_wave_wait.py:2180)〜2254 が、実 merge 後の clean 木で child sentinel が実行される既存 end-to-end 正例として新 gate も通過する。claim 後だけ dirty にする時点制御は `_FakeEffects` の二段 status 応答の方が決定的である。

## 6. 恒真化の risk

主な risk と防止策は次のとおり。

- rc だけ確認すると、clean/dirty とも通常は git rc `0` なので dirty 検査が恒真になる。必ず stdout 非空を失敗にする。
- claim 前の `preflight-clean` 結果を保存・再利用すると、待機中の変更を見ない恒真 gate になる。投入直前に新しい subprocess を必ず起動する。
- `_RoutingAcceptanceEffects` は [同ファイル:354](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/orchestrator/tests/test_dev_wave_wait.py:354)〜355 で全 status 呼び出しへ常に `""` を返すため、これだけでは負例にならない。追加2本は `_FakeEffects` で二回の応答を別々に登録する。
- `_FakeEffects` で prerun status を登録し忘れると AssertionError が `run_acceptance` の fail-closed 捕捉に吸収され、rcだけを見る負例が誤って通る可能性がある。`stage == "prerun-clean"`、exact events、`assert_drained()` を同時に検査する。

## 7. 副作用と cleanup との非干渉

- 新しい git 呼び出しは通常 stage 内で実行し、`_cleanup_after_claim` の signal mask 区間 [tools/dev_wave_wait.py:749](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/tools/dev_wave_wait.py:749)〜785 の内側へ移動しない。signal が発生すれば既存の signal outcome と `finally` cleanup に載る。
- `_abort_pending_merge` の status [tools/dev_wave_wait.py:704](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/tools/dev_wave_wait.py:704)〜740 と argv は同じだが、実行条件は排他的である。merge/commit 途中の失敗は新 gate へ到達せず abort status、prerun gate 到達時は `merge_pending=False` なので abort status は走らない。
- したがって `_abort_clean` helper や既存 merge-failure テストには新しい prerun 応答を追加しない。位置順で二つの status を混同しないことが重要である。

runbook との対応は、親 brief が指定する `docs/pegasus-runbook.md` §7.3 の F191 点3b「受入 command 投入直前の tracked clean 検査」であり、R2 の編集自体は本プランに含めない。

## 総括

- 挿入位置: [tools/dev_wave_wait.py:907](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/tools/dev_wave_wait.py:907) の直後、現在の argv 出力行908の直前。
- 壊れる既存テスト: 7定義・8 collected cases — [936](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/orchestrator/tests/test_dev_wave_wait.py:936)、[960](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/orchestrator/tests/test_dev_wave_wait.py:960)、[1208](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/orchestrator/tests/test_dev_wave_wait.py:1208)、[1545](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/orchestrator/tests/test_dev_wave_wait.py:1545)、[1621](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/orchestrator/tests/test_dev_wave_wait.py:1621)、[1652](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/orchestrator/tests/test_dev_wave_wait.py:1652)、[2039](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/orchestrator/tests/test_dev_wave_wait.py:2039)。加えて stage harness [1272](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/orchestrator/tests/test_dev_wave_wait.py:1272) を1 case拡張。
- 追加テスト: 新規2本、加えて既存 parameterized test に `prerun-clean` 1 case。
- provisional P1〜P4: 不同意なし。