# 段 2 プラン — [T-1825] / [T-1826]

## 1. 新規 tool の CLI 契約

新規 file は `tools/check_branch_rescue.py`、stdout schema は `izanagi-branch-rescue-v1` とする。`tools/check_branch_landed.py` の `izanagi-branch-landed-v1` とは名前・意味を分離する。

### CLI

```text
python3 tools/check_branch_rescue.py [OPTIONS] BRANCH [BRANCH ...]
python3 tools/check_branch_rescue.py [OPTIONS] --ledger-only
```

引数:

- `BRANCH [BRANCH ...]`: 削除候補の local branch 名。1 回の呼び出しで全候補を必須入力する。
- `--repo PATH`: 対象 repository。既定は repo root。
- `--ledger PATH`: 期限台帳。既定は `docs/unreachable-object-ledger.md`。repo 外は拒否する。
- `--ledger-only`: branch を評価せず、台帳通知だけを返す。BRANCH との併用は usage error。
- `--timeout-seconds FLOAT`: tool 全体の上限。既定 300 秒、範囲 1〜900。
- `--assessment-timeout-seconds FLOAT`: `check_branch_landed.py` 1 回の上限。既定 8 秒、範囲 1〜60。
- `--max-deletion-loss-commits INT`: 閉包列挙上限。既定 4096、範囲 1〜100000。
- `--max-assessments INT`: landed 判定を実施する commit 数。既定 64、範囲 1〜4096。
- `--now RFC3339`: test 専用の時刻固定。通常 CLI では非表示の開発用引数とし、UTC 以外や不正値は拒否する。

通常終了では stdout に JSON 1 行だけを出す。全 object は固定 field とし、該当しない値は field を省略せず `null` にする。

### `izanagi-branch-rescue-v1` の全 field

- `schema: string`
- `mode: "preview" | "ledger-only"`
- `generated_at: string`
- `repository`
  - `root: string`
  - `common_dir: string`
  - `objects_dir: string`
  - `object_format: "sha1" | "sha256"`
  - `git_version: string`
- `candidates: array`
  - `input: string`
  - `refname: string`
  - `start_tip: string`
  - `end_tip: string | null`
  - `checked_out_worktrees: string[]`
- `root_snapshot`
  - `complete: boolean`
  - `stable: boolean`
  - `started_at: string`
  - `completed_at: string`
  - `start_digest: string`
  - `end_digest: string`
  - `roots: array`
    - `kind: "ref" | "worktree-head" | "index-commit" | "reflog-old" | "reflog-new"`
    - `name: string`
    - `oid: string`
    - `worktree: string | null`
    - `reflog_timestamp: string | null`
  - `excluded: array`
    - `kind: "candidate-ref" | "candidate-reflog" | "alternate-ref" | "non-root-pseudoref"`
    - `name: string`
    - `oid: string | null`
    - `reason: string`
    - `wrong_inclusion_bias: "under-report"`
  - `worktrees: array`
    - `path: string`
    - `head: string`
    - `branch: string | null`
    - `detached: boolean`
    - `index_object_count: integer`
    - `index_commit_root_count: integer`
    - `inspection_complete: boolean`
  - `reflogs`
    - `included_file_count: integer`
    - `excluded_candidate_file_count: integer`
    - `root_oid_count: integer`
    - `inspection_complete: boolean`
  - `indexes`
    - `object_count: integer`
    - `commit_root_count: integer`
    - `inspection_complete: boolean`
  - `alternates`
    - `present: boolean`
    - `object_directories: string[]`
    - `alternate_refs_used_as_roots: false`
    - `inspection_complete: boolean`
- `deletion_loss_closure`
  - `definition: "reachable-from-all-candidate-tips-minus-post-delete-gc-commit-roots"`
  - `complete: boolean`
  - `limit: integer`
  - `observed_commit_count: integer`
  - `commit_count: integer | null`
  - `commits: array`
    - `oid: string`
    - `parents: string[]`
    - `source_candidate_refs: string[]`
    - `landed_assessment`
      - `schema: "izanagi-branch-landed-v1"`
      - `verdict: "landed" | "not-landed" | "indeterminate"`
      - `reason: string`
      - `conclusive: boolean`
      - `checker_rc: integer | null`
      - `elapsed_seconds: number`
      - `corpus_bytes_read: integer | null`
      - `report_sha256: string | null`
      - `branch_delete_authorized: false`
      - `manual_review_required: boolean`
      - `complete: boolean`
    - `retention`
      - `storage_kind: "loose" | "packed" | "loose-and-packed" | "alternate" | "missing" | "indeterminate"`
      - `cat_file_type: "commit" | null`
      - `loose_path: string | null`
      - `loose_mtime: string | null`
      - `pack_path: string | null`
      - `pack_mtime_observed: string | null`
      - `loss_possible_not_before: string`
      - `lower_bound_basis: "loose-object-mtime-plus-prune-expire" | "assessment-time-conservative-floor"`
      - `deadline_status: "determinate" | "indeterminate"`
      - `reason: string`
- `gc`
  - `config`
    - `gc_auto`, `gc_prune_expire`, `gc_reflog_expire`,
      `gc_reflog_expire_unreachable`: 各々
      `{raw: string | null, effective: string, source: string, default_used: boolean, parsed: boolean}`
  - `count_objects`
    - `count: integer`
    - `size_kib: integer`
    - `in_pack: integer`
    - `packs: integer`
    - `size_pack_kib: integer`
    - `prune_packable: integer`
    - `garbage: integer`
    - `size_garbage_kib: integer`
    - `parsed_complete: boolean`
  - `auto_trigger`
    - `enabled: boolean | null`
    - `threshold: integer | null`
    - `loose_count: integer | null`
    - `headroom: integer | null`
    - `utilization: number | null`
    - `proximity: "disabled" | "below-90-percent" | "within-10-percent" | "at-or-above" | "indeterminate"`
    - `next_eligible_git_command_may_trigger: boolean | null`
    - `caveat: string`
- `ledger`
  - `path: string`
  - `schema: "izanagi-unreachable-object-ledger-v1"`
  - `parse_complete: boolean`
  - `entry_count: integer`
  - `pending_count: integer`
  - `notifications: array`
    - `entry_id: string`
    - `object_oid: string`
    - `source_refs: string[]`
    - `status: string`
    - `urgency: "pending" | "urgent" | "deadline-passed" | "object-missing" | "stale-resolution"`
    - `loss_possible_not_before: string`
    - `message: string`
- `candidate_status`
  - `value: "clear" | "rescue-required" | "indeterminate"`
  - `reason_codes: string[]`
- `notification_status`
  - `value: "none" | "due" | "indeterminate"`
  - `reason_codes: string[]`
- `deletion_authorized: false`
- `manual_review_required: boolean`
- `limits`
  - `timeout_seconds: number`
  - `assessment_timeout_seconds: number`
  - `max_deletion_loss_commits: integer`
  - `max_assessments: integer`
- `timing`
  - `total_elapsed_seconds: number`
  - `landed_assessment_seconds: number`
  - `git_child_processes: integer`
- `issues: array`
  - `code: string`
  - `phase: string`
  - `scope: "repository" | "branch" | "commit" | "ledger"`
  - `subject: string | null`
  - `message: string`
  - `affects_candidate_status: boolean`

### rc

- `0`: root snapshot、閉包、期限、台帳の読取りが完全で、全 commit が `landed`、通知なし。削除許可ではない。
- `1`: `not-landed` が 1 件以上あり、救出またはユーザー裁定が必要。
- `2`: `indeterminate`、timeout、上限超過、parse 不能、ref/index/reflog の移動、期限不明、台帳不正のいずれか。最優先 rc。
- `3`: candidate は `clear` または `--ledger-only` だが、未裁定台帳 entry の通知あり。
- `64`: CLI usage error。stdout は空、stderr に usage。
- signal 終了や上記以外の rc は契約外であり、呼び手は rc2 相当として削除停止する。

`tools/check_branch_rescue.py:1-96` にこの契約と定数、`:97-220` に固定 payload builder と CLI error、`:870-980` に集約・rc、`:981-1040` に parser/main を置く。

## 2. root 集合の決定規則

`tools/check_branch_rescue.py:221-420` で root snapshot を作る。開始時と終了時に同じ棚卸しを行い、canonical JSON の SHA-256 が一致しなければ `indeterminate` とする。

Git 2.34.1 で使用するコマンドと形式:

```text
git rev-parse --show-toplevel
# 1 行の worktree root

git rev-parse --git-common-dir
git rev-parse --git-path objects
# 各々 path 1 行

git for-each-ref \
  --format='%(refname)%00%(objectname)%00%(objecttype)%00%(symref)%00'
# ref ごとに NUL 4 field

git worktree list --porcelain
# worktree <absolute-path>
# HEAD <full-oid>
# branch refs/heads/<name> または detached
# entry 間は空行

git -C <worktree> ls-files --stage -z
# "<mode> <oid> <stage>\t<path>\0"

git rev-parse --git-path logs/refs
git -C <worktree> rev-parse --git-path logs/HEAD
# reflog file または directory の path 1 行
```

reflog は各 record の `<old-oid> <new-oid> ... <timestamp> ...\tmessage` を raw bytes で厳密に解析し、old/new の両方を root 候補にする。候補 branch 自身の `logs/refs/heads/<branch>` は、現行 `git branch -d` が ref と reflog を除くため負側へ入れない。別 ref や各 worktree の HEAD reflog に同じ oid があれば、それは残る root として入れる。

集合差は branch ごとに分けず、stdin 1 回で計算する。

```text
git rev-list --topo-order --reverse --parents \
  --max-count=<limit+1> --stdin
```

stdin:

```text
<candidate-tip-1>
<candidate-tip-2>
...
--not
<surviving-ref-root>
<worktree-head-root>
<surviving-reflog-old-or-new-root>
<index-commit-root>
...
```

stdout は `commit_oid [parent_oid ...]` の LF 区切り。`limit+1` 件目、未知の oid 長、非 ASCII、不正 parent、途中切れは閉包不完全として `indeterminate` にする。

root ごとの規則:

| 種類 | 扱い | 誤った扱いの向き |
|---|---|---|
| 削除候補以外の全 `refs/*` | 入れる。`heads`、`tags`、`remotes`、`stash`、notes 等を namespace で狭めない | 落とすと root inventory は過小、喪失閉包は過大 |
| 削除候補の `refs/heads/*` | 入れない | 入れると失われる commit を過小報告 |
| 他 worktree の HEAD | detached/symbolic とも入れる。候補 branch が checkout 中なら削除モデル不成立として `indeterminate` | 落とすと root inventory は過小、喪失閉包は過大 |
| 全 worktree の index | 全 oid を object root として記録。`git cat-file` で commit と判定できた oid だけ commit の負 root に入れる。blob/tree は commit を保持しない | 省略は index が保持する object の喪失を過大報告。解析不能を無視するのは禁止 |
| `refs/stash` | ref と残存 reflog を入れる | 落とすと喪失閉包を過大報告 |
| `refs/remotes/*` | 入れる | 落とすと喪失閉包を過大報告 |
| 残存 reflog | old/new oid を入れる。期限設定と entry timestamp も記録 | 落とすと現時点の喪失閉包を過大報告 |
| 削除候補 branch 自身の reflog | 現行 `branch -d` モデルでは入れない | 入れると喪失閉包を過小報告 |
| alternates の refs | 入れない。local gc の root ではない | 入れると喪失閉包を過小報告 |
| alternate にだけある object | root ではない。local gc は削除しないが外部 ODB の保持期限を証明できないため期限は `indeterminate` | local repo の設定を期限へ流用すると偽の猶予を報告 |
| `ORIG_HEAD` 等の非 ref pseudoref | Git の gc root と確認できないものは入れない | 入れると喪失閉包を過小報告 |
| `refs/replace/*`、grafts、shallow | 意味を補正せず preflight で `indeterminate` | 通常 DAG として続行すると集合自体が不定 |

`refs/heads` と `refs/tags` だけに限定しないことを、`tools/check_branch_rescue.py:270-360` の source-kind table 一か所で定義する。閉包計算側はその table が返した `commit_roots` だけを消費し、別の root 規則を持たない。

## 3. gc 期限の算出規則

`tools/check_branch_rescue.py:421-610` に object storage と期限計算を置く。

設定は effective value を次で読む。未設定時は M1 の Git 2.34.1 既定値を明示的に採用する。

```text
git config --show-origin --get-all gc.auto
git config --show-origin --get-all gc.pruneExpire
git config --show-origin --get-all gc.reflogExpire
git config --show-origin --get-all gc.reflogExpireUnreachable
git count-objects -v
```

M1 の現在値:

- `gc.auto=6700`
- `gc.pruneExpire=2.weeks.ago`
- `gc.reflogExpire=90 days`
- `gc.reflogExpireUnreachable=30 days`
- loose count 6268、headroom 432、利用率約 0.9355
- pack 6、in-pack 64396

object ごとの確認:

```text
git cat-file --batch-check='%(objectname) %(objecttype) %(objectsize) %(objectsize:disk)'
```

1 oid 1 行を stdin に渡し、commit の存在と型を確認する。loose path は `<objects_dir>/<oid[:2]>/<oid[2:]>` を `lstat` し、regular file、dev、inode、size、mtime_ns を前後 2 回照合する。

local pack の所在確認は、`objects/pack/*.idx` ごとに次を一度だけ実行する。

```text
git verify-pack -v <pack.idx>
```

- loose のみにある object:
  `loss_possible_not_before = max(assessment_time, loose_mtime + pruneExpire期間)`。
- loose mtime が既に 14 日窓より古い object:
  下界は assessment time。次の auto gc で失われうる。
- packed または loose-and-packed:
  pack file の mtime は object 個別の到達不能時刻ではない。観測値としてだけ出し、下界は assessment time、`deadline_status=indeterminate`。
- alternate にだけ存在:
  下界は assessment time、`deadline_status=indeterminate`。
- object 不在、pack index の検査失敗、custom expiry の安全な解釈不能、stat の途中変化:
  下界を `null` にせず assessment time を保守的下界として残し、必ず `indeterminate`。

`gc.auto` は時間の保証ではないため、期限とは別に以下を出す。

```text
headroom = max(gc.auto - count, 0)
utilization = count / gc.auto
```

6268/6700 は `within-10-percent`、headroom 432 とする。閾値到達は gc 実行の保証ではなく、「閾値到達後の auto-maintenance 対象 git command で窓が閉じうる」という risk 表現に限定する。

tool が起動する Git command には可能な範囲で `-c gc.auto=0 -c maintenance.auto=false` を与え、自身の観測が auto gc を誘発しないようにする。ただし実効設定を読む `git config` の値にはこの override を混ぜない。

allowlist に `rev-parse`、`for-each-ref`、`worktree list`、`ls-files`、`rev-list`、`cat-file`、`verify-pack`、`count-objects`、`config` だけを置く。`gc`、`prune`、`reflog expire` は実装にも subprocess 引数にも存在させない。

## 4. check_branch_landed.py との関係

`tools/check_branch_landed.py` は変更しない。

新 tool の用語は `deletion_loss_closure`、既存 schema 内の用語は D922 の `closure` のままとする。

- `deletion_loss_closure`: 複数 branch 削除後の gc root 集合との差。
- `izanagi-branch-landed-v1.closure`: 1 入力について `main` との差から introduced state を判定する既存概念。

これにより同名識別子を別定義で置かない。

`tools/check_branch_rescue.py:611-740` から、閉包の各 distinct commit に対し公開 CLI を subprocess として呼ぶ。

```text
python3 tools/check_branch_landed.py \
  --repo <repo> \
  --timeout-seconds <assessment-timeout> \
  <commit-oid>
```

import はしない。理由は、既存の公開境界が CLI schema と rc であり、`_enumerate_closure` など private 関数を共有すると P2 に反して二つの closure を密結合させるためである。

検査事項:

- stdout が JSON 1 object、schema が `izanagi-branch-landed-v1`。
- rc 0/1/2 と `decision.verdict` が既存の対応表に一致する。
- `branch_delete_authorized` は常に false。
- malformed JSON、timeout、signal、未知 rc、schema mismatch は当該 commit を `indeterminate`。
- checker の start/end ref snapshot 不一致もそのまま `indeterminate`。

M2 の実測から、N commit の名目所要は約 `3N` 秒、ledger corpus 読込は約 `21,275,222N` bytes。既定 `N<=64` なので名目約 192 秒、累積読込約 1.36 GB。実際の上限は per-child 8 秒、全体 300 秒の小さい方とする。64 件を超えた commit は実行せず `assessment-limit-exceeded` の `indeterminate` にする。打切り分を黙って落とさない。

既存 `audit_dangling_commits.py` は削除後の別検査なので import・subprocess とも行わない。`cleanup-branches` では従来どおり独立して実行する。

## 5. [T-1826] の台帳と通知

台帳は tracked file `docs/unreachable-object-ledger.md` とする。

`docs/unreachable-object-ledger.md:1-34` に schema、運用、次の警告を置き、`:35-` に 1 object 1 JSON bullet を置く。

> この台帳は SHA の所在を記録するだけで、Git object を延命しない。救出は branch/tag 等の Git ref を作成し、その ref から object が到達可能であることを再検査して初めて成立する。

台帳 schema 名は `izanagi-unreachable-object-ledger-v1`。各 bullet は全 field 固定:

- `schema: string`
- `entry_id: string`
- `recorded_at: string`
- `source_refs: string[]`
- `source_tips: object`。key は full refname、value は full oid
- `assessment_report_sha256: string`
- `object_oid: string`
- `object_type: "commit"`
- `assessment_schema: "izanagi-branch-landed-v1"`
- `assessment_verdict: "landed" | "not-landed" | "indeterminate"`
- `assessment_reason: string`
- `storage_kind: string`
- `object_mtime: string | null`
- `loss_possible_not_before: string`
- `lower_bound_basis: string`
- `gc_auto_threshold: integer | null`
- `loose_count_at_loss: integer | null`
- `gc_headroom_at_loss: integer | null`
- `status: "pending" | "rescued" | "accepted-loss" | "reachable-again" | "object-missing"`
- `resolved_at: string | null`
- `rescue_ref: string | null`
- `resolution_note: string | null`

`entry_id` は candidate ref/tip 集合、object oid、実際の ref loss 時刻の canonical JSON SHA-256 とし、重複追記を拒否する。

追記契機は preview 時ではなく、ユーザー指示による branch 削除が成功し、削除直前 report の candidate tip と実際に消えた expected tip が一致した直後。複数 branch を同時評価した report から、閉包全 commit を追記する。

通知は `/cleanup-branches` §1 で毎回 `--ledger-only` を実行し、全 `pending` entry を通知する。

- `loss_possible_not_before <= now`: `deadline-passed`
- 7 日以内: `urgent`
- それ以外: `pending`
- `git cat-file -e <oid>^{object}` が失敗: `object-missing`
- `status=rescued` なのに `rescue_ref` が消失または oid を保持しない: `stale-resolution`

陳腐化 entry は削除しない。再到達可能なら `reachable-again`、明示的な救出 ref ができたら `rescued`、ユーザーが喪失を受容した場合だけ `accepted-loss` に更新する。tool は候補の status 更新案を JSON へ出すだけで、台帳を自動編集しない。

## 6. cleanup-branches への配線

現在の `.claude/commands/cleanup-branches.md` は 3999 bytes、64 行、実測した最長行は 87 文字。

変更位置:

- 現在の line 16 後、§1 に `--ledger-only` の rc0/2/3 配線を 2 行追加。
- 現在の line 20 後、§1 に「全削除候補を 1 回の preview へ渡す」「分割禁止」「rc0 以外は停止」を 4 行追加。
- 現在の line 25 後、§2 に「rc0 は削除許可ではなく、ユーザー指示と既存条件も必要」を 1 行追加。
- 現在の line 37 後、§3 に削除成功後の ref-loss entry 追記を 2 行追加。
- §5 に rc1/2/3 の reason と未裁定 entry を報告対象へ含める短い追記を 1 行追加。

追加は約 820 bytes、追記後は約 4819 bytes、最長行は現在値以下になるよう折り返す。詳細な root/期限/schema 表を command file へ複製しない。

`python3 tools/check_docs.py` が byte または最長行予算を拒否した場合、予算値は変更せず、§1/§2 には実行コマンドと rc routing だけを残す。詳細は `docs/unreachable-object-ledger.md` の「Rescue gate contract」節と tool の `--help` へ移す。

## 7. テスト設計 (変異とその負例)

新規 test は既存期待値を変更せず、次の 2 file に分ける。

### `orchestrator/tests/test_check_branch_rescue.py`

- `:1-90`: temp repository、複数 worktree、ref、reflog、loose mtime、fake landed checker の helper。
- `:91-160`: CLI、固定 schema、正常 rc、usage rc64。
- `:161-350`: root 集合と同時 closure。
- `:351-470`: gc 期限。
- `:471-610`: landed subprocess、timeout、上限、rc。
- `:611-690`: read-only 性と start/end snapshot。

主要な負例:

1. `test_all_candidates_are_subtracted_together`
   - 同じ未 main commit を指す branch A/B を作る。
   - A 単独では B が隠し、B 単独では A が隠すが、A/B 同時削除では 1 commit が失われる。
   - branch ごとの結果の和を取る変異を殺す。

2. `test_other_worktree_detached_head_is_a_root`
   - candidate tip と同じ commit を別 worktree の detached HEAD に置く。
   - HEAD を落とす変異は root inventory を過小報告し、喪失閉包を過大報告するため、期待する空 closure と root source の双方で殺す。
   - 「失われる commit 自体の過小報告」を起こす変異は、逆向きの `test_candidate_reflog_is_not_a_post_delete_root` で殺す。

3. `test_candidate_reflog_is_not_a_post_delete_root`
   - candidate commit が自身の branch reflog だけに現れる fixture。
   - candidate reflog を負 root に誤って入れ、失われる commit を隠す変異を殺す。

4. `test_remote_stash_and_surviving_reflog_roots`
   - `refs/remotes/*`、`refs/stash`、別 HEAD reflog がそれぞれ commit を保持する fixture。
   - `heads+tags` だけに縮退する変異を殺す。

5. `test_index_commit_root_and_noncommit_index_object`
   - index の commit 型 root と blob 型 object を分ける。
   - index を無視する変異と、blob を commit root と誤解する変異を殺す。

6. `test_alternate_refs_are_not_local_gc_roots`
   - alternate ref を負 root に入れて closure を空にする変異を殺す。
   - alternate-only object の期限を local `gc.pruneExpire` で確定する変異も殺す。

7. `test_indeterminate_never_returns_zero`
   - fake checker が valid schema、`verdict=indeterminate`、rc2 を返す。
   - top-level rc0 へ倒す変異を殺す。

8. `test_assessment_limit_marks_every_unrun_commit`
   - 上限超過 commit が消えず、各々 `indeterminate` になることを確認。

9. `test_loose_deadline_uses_object_mtime`
   - clock を T、mtime を T-1日、pruneExpire を14日とし、下界を T+13日と期待。
   - `now+14日` という上界を出す変異を殺す。

10. `test_old_loose_object_can_be_lost_now`
    - mtime が T-20日の object の下界を T と期待。
    - 常に追加 14 日を与える変異を殺す。

11. `test_packed_mtime_is_not_object_mtime`
    - pack mtime を object deadline に流用する変異を殺し、assessment time＋`indeterminate` を要求。

12. `test_root_or_ref_move_is_indeterminate`
    - 開始後に ref、worktree HEAD、index、reflog の各 snapshot を変える parameterized test。

13. `test_forbidden_git_commands_are_absent`
    - subprocess argv を記録し、`gc`、`prune`、`reflog expire` が一度も現れないことを確認。
    - refs、index、object path の before/after digest も一致させる。

### `orchestrator/tests/test_branch_rescue_ledger.py`

- `:1-80`: canonical ledger fixture。
- `:81-190`: schema、重複、malformed entry、tracked path 制約。
- `:191-310`: pending/urgent/deadline-passed/object-missing。
- `:311-390`: rescued/reachable-again/accepted-loss と stale rescue ref。
- `:391-440`: `--ledger-only` rc0/2/3。

実装時の予定実行:

```text
python3 tools/run_tests.py \
  orchestrator/tests/test_check_branch_rescue.py \
  orchestrator/tests/test_branch_rescue_ledger.py
python3 tools/check_codex_agents.py
python3 tools/check_docs.py
```

この段では sandbox が read-only のため、pytest を含めテストは実走していない。

## 8. 編集面の所有分割

段 5 は file 所有が素集合になる 2 単位に分ける。

### 単位 A: 閉包・期限・既存判定器連携

- `tools/check_branch_rescue.py`
- `orchestrator/tests/test_check_branch_rescue.py`
- `output/insights/2026-08-26_t1825-rescue-gate/README.md`

### 単位 B: 台帳・通知・command 配線

- `docs/unreachable-object-ledger.md`
- `orchestrator/tests/test_branch_rescue_ledger.py`
- `.claude/commands/cleanup-branches.md`
- `docs/spool/worklog/2026-08-26-dev-wave-t1825-rescue-gate-1.md`
- `docs/spool/decisions/2026-08-26-dev-wave-t1825-rescue-gate-1.md`

単位 B の test は単位 A の確定済み CLI 契約だけを利用し、`tools/check_branch_rescue.py` を編集しない。

`tools/check_branch_landed.py`、`tools/audit_dangling_commits.py`、既存 test は変更しない。

`tools/dev_wave_cleanup.py` も変更しない。M7 の通常経路は candidate tip の再確認、main ancestry、expected-tip 付き削除を持ち、main が通常の fast-forward で進む限り closure は空のままである。所見として、ancestry 検査と削除の間に local main が非 fast-forward で巻き戻されると、candidate tip の CAS だけでは main snapshot を拘束しない TOCTOU が残る。これは本 wave では実装せず insight に記録する。submodule gitlink は superproject commit 自体の ancestry を崩さず、reflog は追加の一時保持 root なので、この所見を拡大しない。

## 9. 親 brief への異議 (無ければ「なし」)

なし。

P1 の対象外経路には上記の非 fast-forward main TOCTOU 所見があるが、M7/M9 と本 wave の編集面分離を覆す実測ではないため、`tools/dev_wave_cleanup.py` を追加編集する異議とはしない。

## 総括

- 実装単位の数: 2
- 新規 file の数: 7
- 変更する既存 file: `.claude/commands/cleanup-branches.md`
- 最大の未解決点: 通知発火点が `/cleanup-branches` §1 だけなので、cleanup 自体が実行されない期間について wall-clock 上の事前通知を保証できないこと。台帳は全 pending entry を毎回即時通知するが、scheduler は P3 の scope 外である。