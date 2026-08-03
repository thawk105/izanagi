結論から言うと、P1 の「累積差分への置換」は不採用です。`landed_main_sha` は post-fold HEAD なので範囲端が誤っているうえ、正しい `base_main_sha..wave_tip` に直しても、fold 後に tree を戻す履歴や merge 親間で状態を往復させる履歴を見逃します。

安全な修正は、commit ごとの検査を残し、merge に限って「その署名が trusted main の親から未変更で取り込まれた」と三つの tree で証明できた場合だけ免除する方式です。以下は実装を伴わない静的プランです。テストは実走しておらず、緑は主張しません。

## 1. 現行経路の棚卸し

### 入力と呼び出し元

`verify_declared_fold_commit` は [git_state.py:699](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:699) にあり、3 module・4 static call site から呼ばれます。

| 呼び出し元 | 引数の由来 |
|---|---|
| [dev_wave_land.py:1513](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_wave_land.py:1513) | fold commit は [1478–1487](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_wave_land.py:1478) で main に作った commit。`landed_main_sha` はその commit、`wave_tip` は request の `tested_wave_tip_sha`、`landed_commits` は後述の `audited`。 |
| [dev_wave_land.py:1820](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_wave_land.py:1820) | no-fold 経路。`landed_main_sha=wave_tip=tested_tip`、`landed_commits=audited`。HEAD が tip に見える main または wave worktree を選ぶ。 |
| [checker.py:543](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/checker.py:543) | receipt の `fold_commit_sha` / `landed_main_sha` / `landed_commits` と、実 branch の `wave_tip_before`。`base_main_sha` は `VerificationInput.before_main_sha` に binding 済み。 |
| [daemon.py:1526](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/daemon.py:1526) | recovery receipt の同三 field と、context の wave branch から再観測した tip。receipt の `base_main_sha` は wave manifest に binding 済み。 |

land 側の順序契約は明確です。

- CLI は `--audited-commit` を「`git rev-list --reverse A..T` と同順」と定義します。[dev_wave_land.py:1963](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_wave_land.py:1963)
- request の `tested_main` / `tested_tip` は [1661–1666](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_wave_land.py:1661) で確定します。
- `_verify_audit` は実際に `git rev-list --reverse <tested_main>..<tested_tip>` を実行し、申告 tuple と完全一致しなければ拒否します。[dev_wave_land.py:932](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_wave_land.py:932)
- その戻り値が `audited` となり、各 fold 経路へそのまま渡されます。[dev_wave_land.py:1707](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_wave_land.py:1707)、[1781](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_wave_land.py:1781)、[1875](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_wave_land.py:1875)、[1934](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_wave_land.py:1934)
- checker も `verify_ff_chain(before_main, wave_tip, receipt.landed_commits)` で同じ `--reverse` 順を照合します。[git_state.py:517](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:517)、[checker.py:489](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/checker.py:489)
- daemon recovery は再度 `rev-list` せず、すでに `WAVE_ACCEPTED` になった receipt と `last commit == tip` に依存します。[daemon.py:1474](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/daemon.py:1474)、[1513](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/daemon.py:1513)

### `verify_declared_fold_commit` の検査順

`_fold_fail` は常に `reason=COMMIT_MISMATCH` を返し、表の文字列を `detail` にします。[git_state.py:553](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:553)

| 順 | 現行検査・発火入力 | 結果 / pin |
|---:|---|---|
| 1 | `landed_main_sha`、`wave_tip`、全 `landed_commits`、任意の `fold_commit_sha` が full lowercase SHA でない。[713–721](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:713) | `detail` ではなく `ValueError`。helper 直接の負例 pin なし。 |
| 2 | `landed_commits` が空。[716–717](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:716) | `landed-commits-empty`。直接 pin なし。completed receipt は別層で空を拒否。[receipt.py:183](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/receipt.py:183) |
| 3 | timeout を作り、対象 checkout の HEAD を読む。[722–726](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:722) | timeout/Git/encoding 異常は `DevWavesError`。直接 pin なし。 |
| 4 | `landed_commits[-1] != wave_tip`。[727–728](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:727) | `wave-tip`。直接 pin なし。 |
| 5 | landed commit のどれかに `M docs/spool/FOLDED.md`、または fragment の `D` / source-side `R*` がある。[730–735](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:730)、分類は [557–562](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:557) | `landed-fold-owned-path`。`test_n31` [374](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_git_state.py:374)、fragment delete [503](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_git_state.py:503)、rename D+A [517](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_git_state.py:517)、R record 単体 [533](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_git_state.py:533)、FOLDED M [570](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_git_state.py:570)。 |
| 6a | null fold なのに `HEAD != landed_main` または `landed_main != tip`。[737–739](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:737) | `null-head`。直接 pin なし。 |
| 6b | null fold の HEAD tree に、三つの spool ledger directory 配下の README 以外が残る。[669–696](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:669)、[740–743](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:740) | `null-pending-fragment`。N32 [388](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_git_state.py:388)。ゼロ件正例 P07 [400](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_git_state.py:400)。 |
| 7 | declared fold なのに `HEAD != landed_main` または `landed_main != fold_sha`。[746–747](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:746) | `declared-head`。直接 pin なし。 |
| 8a | commit message が exact `FOLD_COMMIT_MESSAGE` でない。[626–635](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:626) | `message`。正しい形は exact-shape 正例 [255](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_git_state.py:255) が間接 pin。負例なし。 |
| 8b | header key、必須 header 数、parent 数、encoding bytes が不正。[636–655](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:636) | `header`。merge fold N33 [411](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_git_state.py:411)、encoding 正例 [441](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_git_state.py:441)。 |
| 8c | parent が ASCII full SHA でない。[657–661](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:657) | `parent`。直接 pin なし。 |
| 8d | author が固定 identity または timezone 契約に合わない。[662–663](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:662) | `author`。正例による間接 pin のみ。 |
| 8e | committer identity/timezone が不正。[664–665](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:664) | `committer`。正例による間接 pin のみ。 |
| 9 | fold parent が `landed_commits[-1]` と `wave_tip` の双方に一致しない。[753–754](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:753) | `parent`。直接 pin なし。 |
| 10a | fold commit の status が M/D/A 以外。[760–764](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:760) | `path-status`。typechange N [348](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_git_state.py:348)。 |
| 10b | M path が canonical allowlist、FOLDED、archive README のいずれでもない。[766–772](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:766) | `modified-path`。直接負例なし。許可側は non-signature paths [457](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_git_state.py:457)。 |
| 10c | D path が fragment regex 外。[773–776](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:773) | `deleted-path`。直接 pin なし。 |
| 10d | A path が rotation regex 外、または rotation が2件以上。[777–782](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:777) | `added-path` は N34 [585](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_git_state.py:585)、`archive-count` は [307](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_git_state.py:307)。rotation 正例 [267](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_git_state.py:267)。 |
| 11 | archive README を M したのに rotation A がちょうど1件でない。[783–784](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:783) | `archive-readme`。[329](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_git_state.py:329)。 |
| 12 | fragment D が0件、または FOLDED M がない。[785–786](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:785) | `minimum-shape`。直接負例なし。exact fold 正例が間接 pin。 |
| 13 | 全条件成立。 | `no-fold` [744](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:744) または `fold-shape` [787](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:787)。 |

補助契約も残します。

- `commit-diff` は現在 `diff-tree --root -r -m ... --no-renames` です。[git_state.py:90](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:90)
- `_diff_entries` は R/C の二 path NUL record を読みます。[git_state.py:565](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:565)、parser test [tests:541](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_git_state.py:541)
- `--no-renames` 契約は [tests:75](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_git_state.py:75) が pin しています。
- FOLDED の A は署名でなく許可されます。[tests:484](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_git_state.py:484)
- fragment M も許可されます。[tests:555](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_git_state.py:555)

## 2. 脅威モデル

この gate が防ぐのは、wave が lock 外で spool fold を行い、次のいずれかを landed history に紛れ込ませることです。

- fragment を消して canonical へ反映されない作業を失わせる。
- `FOLDED.md` を書き換え、fold receipt、content hash、採番・順序の由来を偽装する。
- 最後に正しい形の fold commit を1本付け、その直前にあった不正 fold を隠す。
- merge 親の差として上記操作を見えにくくする。

実装上は二条件の論理積ではなく、`M FOLDED` と `D/R fragment` のどちらか一方だけで拒否します。この意味は変えません。

`test_n31_landed_interval_cannot_hide_an_earlier_fold` が守る攻撃を逐語化すると、次の通りです。

> pending fragment が2件ある状態で、wave が landed interval 内の `first_fold` で1件を削除し `FOLDED.md` を変更する。その後、申告された正規 fold slot に見せかけた `second_fold` で残り1件を削除する。`second_fold` 単体の graph・message・author・path shape は正しいため、landed interval を走査しなければ、先行する lock 外 fold を隠せる。

### 累積差分に対する (a)〜(e)

`B` を trusted main の tree、`T` を wave tip とします。

| 攻撃 | `git diff --no-renames B T` | 結論 |
|---|---|---|
| (a) wave が fragment を A し、自分で D + FOLDED M | FOLDED が B に存在し最終 receipt が残れば M で捕まる。fragment は A→D で消える。 | P2 はこの限定条件だけ正しい。FOLDED が B にない初回導入では最終 status が A、または receipt を B へ戻せば見逃す。 |
| (b) B にある fragment を削除/rename | 最終的に消えていれば D。`--no-renames` なら rename も D+A。 | 捕まる。ただし後で元へ戻せば累積差分から消える。 |
| (c) FOLDED を書き換える | 最終 bytes が違えば M。 | 捕まる。ただし restore、または B で未作成なら捕捉不能。 |
| (d) fold commit を含め、tip tree を B へ戻す | protected path の差分は空。 | **捕まらない。P1 を棄却する決定的反例。** |
| (e) merge commit に隠す | 最終 tree が違えば累積で捕まるが、親から状態を交互に継承して最終 tree を戻せば空。 | 累積単独でも `--cc` 併用でも回避可能。 |

(a)〜(d) の基本操作列は次です。

```bash
# B には FOLDED.md と fragment f がある
git switch -c wave B

# (a)
printf 'new fragment\n' > "$g"
git add "$g"
git commit -m 'add fragment'
git rm "$g"
printf 'fold\n' >> docs/spool/FOLDED.md
git add docs/spool/FOLDED.md
git commit -m 'hidden fold'

# (b)
git rm "$f"
git commit -m 'delete existing fragment'

# (c)
printf 'forged\n' >> docs/spool/FOLDED.md
git commit -am 'rewrite folded receipt'

# (d): hidden fold の後、protected tree を B へ戻す
git restore --source=B -- docs/spool/FOLDED.md "$f" "$g"
git add -A
git commit -m 'restore protected tree'
git diff --name-status --no-renames B HEAD
# protected path は出ない
```

`--cc` も単独では不十分です。次の標準的な branch/merge 操作で、各 merge result を片方の親と同一にできます。

```bash
# O は FOLDED/f 導入前、B は導入後
git switch -c folded-state O
# FOLDED を A として作るが f は作らない
printf '# folded\nhidden\n' > docs/spool/FOLDED.md
git add docs/spool/FOLDED.md
git commit -m 'side folded state'

git switch -c wave B
git merge --no-commit folded-state
git rm "$f"
git checkout folded-state -- docs/spool/FOLDED.md
git add -A
git commit -m 'inherit folded state from side parent'   # M1

git switch -c restore B
printf 'restore parent\n' > restore.txt
git add restore.txt
git commit -m 'make restore parent non-ancestor'

git switch wave
git merge --no-commit restore
git checkout restore -- docs/spool/FOLDED.md "$f"
git add -A
git commit -m 'restore from other parent'               # M2

git diff --name-status --no-renames B M2
git diff-tree --cc -r --name-status --no-renames M1
git diff-tree --cc -r --name-status --no-renames M2
# protected path はいずれにも出ない:
# endpoint は B、各 merge result は片方の親と一致するため。
```

したがって、最重要所見は「累積差分は history 内の fold 署名を保存しない」です。`test_n31` の一般化された攻撃は P1 では守れません。

なお read-only の実 repo 観測でも、merge `ee28642` は現在の `-m` で `M docs/spool/FOLDED.md` を出し、main 側親との二点 diff と `--cc` では同 path が出ませんでした。テスト実走ではなく Git object の静的観測です。

## 3. 判定領域の設計

### 候補比較

| 案 | 正規 main merge | (d)/(e) | 判断 |
|---|---|---|---|
| P1 の literal `<landed_main_sha>..<wave_tip>` | fold ありでは `landed_main_sha` が post-fold commit なので逆向き。FOLDED M を再び見る。no-fold では同一 endpoint。 | 不適切 | 棄却。実入力の意味を取り違えている。 |
| 正しい `base_main_sha..wave_tip` の endpoint 累積差分 | 通る。 | tree restore で見逃す。 | 単独採用不可。 |
| merge parents の merge-base から merge result | stale wave と main の共通祖先以降にある正規 main fold まで再検出する。 | 一部捕捉 | false positive が残る。 |
| merge を除外し、非 merge だけ per-commit | 通る。 | merge resolution 自体の fold を見逃す。 | 棄却。 |
| 非 merge per-commit + merge だけ `--cc` | 通る。merge result が全親と違う場合は捕捉可能。 | 親の一方と同じ状態を交互に選ぶ上記 M1/M2 で回避可能。 | 棄却。 |
| **全 parent diff + trusted-main 三 tree 証明** | trusted main 由来だけを免除。 | hidden commit、merge resolution、parent laundering を捕捉。 | **採用推奨。** |

### 採用案

`Receipt` にはすでに `base_main_sha` があります。[schema.py:298](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/schema.py:298)、binding は [receipt.py:167](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/receipt.py:167) です。これを `verify_declared_fold_commit` の必須 keyword `base_main_sha` として明示的に渡します。schema 変更は不要です。

判定は次の形にします。

```text
for C in landed_commits:
    parents = parents(C)

    if parent 数 < 2:
        現行どおり root/single-parent diff の各署名を拒否
        continue

    parent ごとに diff(parent, C) を取り、
    現れた署名 key = (folded-modified | fragment-deleted, path) を集める

    各 key について、次をすべて満たす direct parent P があれば
    「trusted main からの取り込み」と証明して免除する:
      1. P は base_main_sha の ancestor（P == base_main_sha を含む）
      2. merge result C の対象 path は P から不変
      3. key を出した各別 parent Q について merge-base(Q, P) は一意
      4. merge-base(Q, P) から Q まで対象 path は不変

    証明できない key が1件でもあれば landed-fold-owned-path
```

この三 tree 条件は次を意味します。

```text
merge-base(Q,P) の path == Q の path
P の path               == merge result C の path
```

したがって `Q → C` に見える D/M は、wave が作った変更ではなく trusted main の `merge-base → P` の状態遷移そのものです。wave が fragment を追加・変更した場合は第一等式が壊れ、merge resolution が main と違う場合は第二等式が壊れます。

### `git diff` か `git diff-tree` か

`git diff A..T` の二点表記も endpoint tree 比較ですが、「commit range の走査」に見えやすく、現行 allowlist/parser と表現がずれます。`git diff-tree` を使います。

[git_state.py:68–96](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:68) の argv 表を次のように分割します。

```python
"commit-diff": (
    "diff-tree", "--root", "-r", "--no-commit-id",
    "--name-status", "-z", "--no-renames",
),
"tree-diff": (
    "diff-tree", "-r", "--no-commit-id",
    "--name-status", "-z", "--no-renames",
),
"commit-parents": ("rev-list", "--parents", "--max-count=1"),
"merge-bases": ("merge-base", "--all"),
```

- `commit-diff` から欠陥の原因である `-m` を外す。
- `tree-diff` は検証済みの二つの SHA を別 argv として渡す。
- `merge-bases` は `--all` を使い、複数なら免除を与えず fail-closed にする。
- 両 diff に `--no-renames` を置き、rename は D+A とする。
- `_landed_fold_output_path("R100", ...)` の予備防壁と `_diff_entries` の二 path parse は残す。

これにより既存 rename 2 本は両方生き残ります。

- 実 Git 経路の D+A 拒否: [tests:517](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_git_state.py:517)
- R record の予備分類: [tests:533](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_git_state.py:533)

## 4. file:line 粒度の変更プラン

### `tools/dev_waves/git_state.py`

1. [68–96](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:68)

   - 上記 `commit-diff` 修正と `tree-diff` / `commit-parents` / `merge-bases` 追加。
   - mutating verb は増やさない。

2. [557–610](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:557)

   - 二条件を一意に扱う内部 helper `_landed_fold_signature(status, paths) -> tuple[kind, path] | None` を追加。
   - 公開済み単体テスト用 `_landed_fold_output_path` は `return _landed_fold_signature(...) is not None` とし、M/D/R の意味を変えない。
   - `_diff_entries` は変更しない。
   - `_tree_diff(before, after)`、`_commit_parents(commit)`、`_merge_bases(left, right)` を追加。
   - tree diff 内で path が一度でも現れたかを見る `_tree_path_changed` を追加。mode/type/blob のどれが変わっても「変更」とする。

3. [699–735](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:699)

   - 必須 keyword `base_main_sha` を `landed_main_sha` の前へ追加し `_validate_base` する。
   - `landed_commits[-1] == tip` までの detail 順序は維持。
   - 現行二重 loop を `_landed_commit_has_untrusted_fold_signature(...)` 呼び出しへ置換。
   - non-merge は従来と同じ commit diff。
   - merge は上記三 tree 証明を行い、証明不能時だけ従来と同じ `landed-fold-owned-path`。
   - [737–787](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:737) の null-head 以降には手を入れない。

4. `landed_commits` は削除しない。

   - scan 対象と順序は引き続き `git rev-list --reverse base..tip` の exact closure。
   - land/checker が持つ既存 exact-closure gate を前提とする。
   - daemon recovery は過去の `WAVE_ACCEPTED` 検証結果を引き続き使う。

### production caller

1. [dev_wave_land.py:1407](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_wave_land.py:1407)

   - `_fold_main_locked` に `base_main_sha: str` を追加。
   - [1781](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_wave_land.py:1781)、[1875](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_wave_land.py:1875)、[1934](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_wave_land.py:1934) から `tested_main` を渡す。
   - fold call [1513](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_wave_land.py:1513) に `base_main_sha=base_main_sha`。
   - no-fold call [1820](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_wave_land.py:1820) に `base_main_sha=tested_main`。

2. [checker.py:543](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/checker.py:543)

   - `base_main_sha=receipt.base_main_sha` を追加。
   - これは [408–413](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/checker.py:408) で `spec.before_main_sha` に binding 済み。

3. [daemon.py:1526](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/daemon.py:1526)

   - `base_main_sha=receipt.base_main_sha` を追加。
   - receipt は [1500–1504](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/daemon.py:1500) で `wave_manifest.base_main_sha` に binding 済み。

このため、親 brief の「原則2ファイル」という編集面は安全に実装するには狭すぎます。段4では上記 caller 3 module の一行伝播と `_fold_main_locked` の引数伝播を scope に追加すべきです。schema/receipt format は変えません。

## 5. `test_n31` の意図保存な書き直し

現行 [tests:374](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_git_state.py:374) を、累積差分だけでは本当に捕まらない強い形へします。

```python
def test_n31_landed_interval_cannot_hide_an_earlier_fold():
    with _fresh() as tmp:
        repo = _repo(Path(tmp))
        pending = _seed_pending(repo, 2)
        base_main = _git(repo, "rev-parse", "HEAD")

        code_tip = _code_commit(repo)
        first_fold = _fold_commit(repo, pending[:1])

        # hidden fold の protected tree を landed tip 前に元へ戻す。
        _git(
            repo, "restore", "--source", code_tip, "--",
            "docs/spool/FOLDED.md", pending[0],
        )
        restored_tip = _commit(
            repo, "restore hidden fold",
            "docs/spool/FOLDED.md", pending[0],
        )

        # land が申告する fold は restored_tip の direct child で、単体 shape は正しい。
        declared_fold = _fold_commit(repo, pending)
        landed = tuple(
            _git(
                repo, "rev-list", "--reverse",
                f"{base_main}..{restored_tip}",
            ).splitlines()
        )
        assert landed == (code_tip, first_fold, restored_tip)

        result = verify_declared_fold_commit(
            repo,
            fold_commit_sha=declared_fold,
            base_main_sha=base_main,
            landed_main_sha=declared_fold,
            landed_commits=landed,
            wave_tip=restored_tip,
        )
        assert (not result.ok) and result.detail == "landed-fold-owned-path"
```

この形なら、

- `base_main..restored_tip` の protected endpoint 差分は空。
- landed closure は実際の `rev-list --reverse` と一致。
- declared fold は `wave_tip` の direct child。
- hidden `first_fold` の per-commit 検出を消した場合だけ受理される。

したがって期待値反転や skip ではなく、N31 の意図を強化します。

## 6. 新設する正例

[tests helper:48–61](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_git_state.py:48)、[194–211](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_git_state.py:194)、[228–252](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_git_state.py:228) を使い、production に近い「main fold + wave 自身の fragment + post-land declared fold」にします。

```python
def test_landed_interval_allows_main_fold_merge_before_declared_fold():
    with _fresh() as tmp:
        repo = _repo(Path(tmp))
        main_pending = _seed_pending(repo)
        divergence = _git(repo, "rev-parse", "HEAD")

        _git(repo, "switch", "-c", "wave")
        wave_code = _code_commit(repo)

        wave_fragment = (
            f"docs/spool/worklog/2000-01-01-dev-wave-dw-"
            f"{'a' * 32}-w001-2.md"
        )
        path = repo / wave_fragment
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("wave-owned fragment\n", encoding="utf-8")
        wave_fragment_commit = _commit(
            repo, "wave adds its pending fragment", wave_fragment,
        )

        _git(repo, "switch", "main")
        assert _git(repo, "rev-parse", "HEAD") == divergence
        main_fold = _fold_commit(repo, main_pending)

        _git(repo, "switch", "wave")
        _git(repo, "merge", "--no-ff", "--no-edit", main_fold)
        merge_tip = _git(repo, "rev-parse", "HEAD")

        # land lock 内で作る fold slot を模した direct child。
        declared_fold = _fold_commit(repo, (wave_fragment,))
        landed = tuple(
            _git(
                repo, "rev-list", "--reverse",
                f"{main_fold}..{merge_tip}",
            ).splitlines()
        )
        assert landed[-1] == merge_tip
        assert wave_code in landed
        assert wave_fragment_commit in landed

        result = verify_declared_fold_commit(
            repo,
            fold_commit_sha=declared_fold,
            base_main_sha=main_fold,
            landed_main_sha=declared_fold,
            landed_commits=landed,
            wave_tip=merge_tip,
        )
        assert result.ok, result
```

現行実装で赤になることは静的に確定できます。

1. `merge_tip` は `landed` に含まれる。
2. 現行 `commit-diff` は `-m`。
3. wave 親から merge result への差分は、少なくとも `M docs/spool/FOLDED.md` と `D <main_pending>`。
4. [git_state.py:734–735](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:734) が declared fold 検査より先に拒否する。

修正後の想定では、trusted parent `P=main_fold`、`merge-base=divergence` について、

- divergence→wave parent は FOLDED/main fragment が不変。
- main_fold→merge_tip も同 path が不変。

なので main 由来と証明され、wave 自身の fragment A と declared fold は従来条件で受理されます。

追加で、三 tree 証明を固定する負例を2本置きます。

- `test_main_fold_merge_rejects_deleting_a_wave_modified_fragment`: wave が merge-base 上の fragment を M した後、main fold の deletion を選ぶ。merge-base→wave parent が変わるため拒否。
- `test_main_fold_merge_rejects_folded_resolution_not_equal_to_main`: merge commit が FOLDED を main parent と異なる第三の bytes に解決する。main parent→merge result が変わるため拒否。

[dev_wave_land test:1748](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_wave_land.py:1748) の直接 helper 呼び出しにも `base_main_sha=request.tested_main_sha` を追加します。

## 7. 受理集合の変更

| 入力 | 修正前 | 修正後 |
|---|---|---|
| tested main が fold 済みで、wave がその main commit を親として未変更取り込みする | `landed-fold-owned-path` | 受理 |
| current tested main より前の main ancestor を一度取り込み、その後さらに新しい main を取り込んだ landed closure | 以前の merge で拒否 | 各 trusted main ancestor 由来を証明して受理 |
| main fold merge 後、wave 自身の fragment を declared fold が処理する | merge の時点で拒否 | declared fold の既存 shape 条件で受理 |
| 非 merge の fragment D/R、FOLDED M | 拒否 | 拒否 |
| hidden fold 後に tree restore | 拒否 | 拒否 |
| merge resolution 自身が D/M を作る | 拒否 | 拒否 |
| wave が追加・変更した fragment を main merge 解決で捨てる | 拒否 | 拒否 |
| FOLDED A、fragment A/M、通常文書変更 | 受理 | 受理 |
| declared fold の message/header/parent/path/minimum 異常 | 各既存 detail で拒否 | 同じ detail で拒否 |

有効な repository 入力で「修正前は緑、修正後は赤」になる集合はありません。API 呼び出しに新しい必須 keyword が増えるため、更新漏れだけは Python の `TypeError` になりますが、全 static call site を同一変更で更新します。

## 8. 他 caller への波及

- `dev_wave_land.py`: false positive が消え、DW-O23 の正規 merge 後に no-fold / declared-fold の双方へ進める。それ以外の fold、rollback、postcondition は不変。
- `checker.py`: receipt の既存 `base_main_sha` を追加で使うだけ。valid receipt の受理変更は同じ正規 merge の赤→緑のみ。
- `daemon.py`: accepted-wave recovery が同じ正規 merge receipt を再受理できるようになる。`common_matches` や v1 handling は不変。
- `landed_commits`:廃止しない。hidden non-merge、untrusted merge parent、tip 順序を検査する主入力のまま。
- schema、receipt wire format、fold commit shape、pending path の範囲は変更しない。

## 9. 段4で事前登録する変異候補

以下の `old` は修正後コードへ置くべき逐語です。行番号は現行 insertion anchor です。

| # | 箇所 / old → mutation | 赤になる単一 test・理由 | 手前の拒否がない根拠 |
|---:|---|---|---|
| M1 | [git_state.py:90](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:90) `"--name-status", "-z", "--no-renames",` → `"--name-status", "-z", "--find-renames",` | 更新する `test_commit_and_tree_diff_disable_move_detection_by_contract`。argv 契約違反。 | command tuple 自体を直接読む test であり repository gate は先行しない。 |
| M2 | [git_state.py:557](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:557) `if status == "M" and paths[0] == "docs/spool/FOLDED.md":` → `status == "A"` | `test_landed_interval_rejects_folded_receipt_signature`。M receipt が受理される。 | tip commit に fragment D/R はなく、後続 declared fold は valid。 |
| M3 | [git_state.py:561](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:561) `status == "D" or status.startswith("R")` → `status == "A" or ...` | `test_landed_interval_rejects_fragment_deletion_signature`。D fragment が漏れる。 | landed tip は FOLDED を触らず、残り fragment の declared fold は valid。 |
| M4 | [git_state.py:602](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:602) non-merge branch の old `return any(_landed_fold_output_path(...))` → `return False` | 書き直した `test_n31...`。hidden fold + restore が受理される。 | endpoint protected diff は空で、declared fold の head/parent/shape は全て正しい。 |
| M5 | 同 helper の trusted-parent 選択 old `if not _is_ancestor(repo_root, trusted_parent, base_main, ...)` → `if True:` | 新正例 `test_landed_interval_allows_main_fold_merge_before_declared_fold`。main 親を候補にできず現行署名で拒否。 | SHA、closure、tip、declared fold はすべて valid。merge 署名だけが対象。 |
| M6 | current [git_state.py:610](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:610) 後へ入れる old `if _tree_path_changed(base_to_source, signature_path):` → `if False:` | `test_main_fold_merge_rejects_deleting_a_wave_modified_fragment`。wave の M fragment を merge D で捨てられる。 | fragment M は既存正例どおり許可され、FOLDED/main 取り込みは正当。source-tree 条件だけが拒否理由。 |
| M7 | 同箇所の old `if _tree_path_changed(trusted_to_merge, signature_path):` → `if False:` | `test_main_fold_merge_rejects_folded_resolution_not_equal_to_main`。第三の FOLDED bytes を main 由来と誤認。 | source parent は merge-base から protected path 不変で、fragment D は正当な main fold 由来。result-tree 条件だけが拒否理由。 |

## 総括

- P1 は `landed_main_sha` の意味を誤認しており、正しい base に直しても hidden fold + restore を見逃す。
- `--cc` も、merge result を片方の親と一致させる parent laundering で回避できる。
- commit ごとの検査は残し、trusted main 由来を三 tree の同一性で証明した merge 署名だけ免除する。
- `base_main_sha` は既存 receipt/manifest field を使い、schema は変えない。
- `--no-renames`、D+A rename test、R record 予備防壁をすべて維持する。
- `test_n31` は net-zero restore を含む強い負例へ書き換え、main fold merge の正例を純増する。
- 安全な実装には `git_state.py` 以外の3 caller と direct-call test への引数伝播を scope 追加する必要がある。