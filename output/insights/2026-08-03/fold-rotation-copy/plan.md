brief と対象コードは読了した。以下は実装を伴わない段 2 プランである。

## 現行と変更後の受理・拒否挙動

`verify_declared_fold_commit` は、landed 区間と申告された fold commit を別々に検査する。

現行の landed 区間では次を `landed-fold-owned-path` で拒否する。

- `M docs/spool/FOLDED.md`
- `D <fragment path>`
- `Rnnn <fragment path> <移動先>`。先頭の移動元だけを見る。
- それ以外の status/path は、この署名分類だけでは拒否しない。したがって fragment の `M`/`A`/`C`、fragment 以外を移動元にする `R` は許容される。

申告 fold commit の現行受理集合は次のとおり。

- `M`: `docs/worklog.md`、`docs/decisions.md`、`docs/failures.md`、`docs/phase3.md`、`docs/spool/FOLDED.md`。加えて `docs/archive/README.md` は rotation の `A` がちょうど 1 件ある場合だけ許容。
- `D`: `_FRAGMENT_PATH_RE` に一致する fragment path のみ。1 件以上必須。
- `A`: `_ROTATION_PATH_RE` に一致する rotation path のみ。最大 1 件。archive README の変更は必須ではない。
- `docs/spool/FOLDED.md` の `M` が必須。
- `Rnnn`、`Cnnn`、および M/D/A 以外は `path-status` で拒否。
- 現行の `status.startswith(("R", "C"))` は、直後の `status not in {"M", "D", "A"}` と論理的に重複している。

したがって現行では、同じ rotation commit でも Git が archive を `A` と報告すれば受理され、類似度により `Cnnn` と報告すれば拒否される。

変更後は移動検出を無効化し、移動・コピー候補を `M`/`D`/`A` として検査する。

- 高類似度の worklog→archive も `M docs/worklog.md` と `A <rotation path>` になり、既存条件を満たせば受理される。
- landed 区間での fragment rename は `D <fragment>` + `A <移動先>` となり、`D` によって引き続き拒否される。
- copy は元を削除しないため `A` になり、現行の `C` と同じく fold 削除署名とは扱わない。
- M/D/A の path allowlist、archive 最大 1 件、README 結合条件、minimum shape は変わらない。

## 変更点

| 箇所 | 変更前 | 変更後 | 理由 |
|---|---|---|---|
| [tools/dev_waves/git_state.py:90-93](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/dev_waves/git_state.py:90) | `commit-diff` の末尾が `-M`, `-C` | 両方を削除し、`--no-renames` を置く | ユーザー裁定を argv 上で明示し、類似度によらず D/A/M の閉じた形検査へ入力する。P1 の config 対策としては不要だが、コマンド契約として有効。 |
| [tools/dev_waves/git_state.py:557-562](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/dev_waves/git_state.py:557) | fragment 削除元を `D` または `R*` から取得 | `D` の fragment だけを判定 | `--no-renames` 下では rename が D+A になる。到達不能な R 特例を primary guarantee にしない。 |
| [tools/dev_waves/git_state.py:760-764](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/dev_waves/git_state.py:760) | `R/C` 特判または M/D/A 外を拒否 | `status not in {"M", "D", "A"}` だけで拒否 | R/C はこの閉集合判定だけで拒否でき、受理集合は変わらない。 |
| [orchestrator/tests/test_dev_waves_git_state.py:66-71](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_dev_waves_git_state.py:66) | 移動検出 argv の固定なし | `commit-diff` の期待 tuple を固定する新規テスト | `-M`、`-C`、長形式の再導入や `--no-renames` 脱落を機械検出する。 |
| [orchestrator/tests/test_dev_waves_git_state.py:206-230](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_dev_waves_git_state.py:206) | `_fold_commit` は rotation を準備しない | 既存 helper の期待・既定動作を変えず、事前 stage した rotation を fold commit に含める新規 test helper を後置 | 現実に近い高類似度 fixture と境界負例を重複なく作る。 |
| [orchestrator/tests/test_dev_waves_git_state.py:233-428](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_dev_waves_git_state.py:233) | rotation の正例・隣接境界なし | 後述のテスト 4 本を追加 | 受理修正と既存 allowlist 不変条件を同時に固定する。 |

`_diff_entries` の R/C 二経路 parser は scope 外なので変更しない。

## (P1) repo-local Git config の検証

P1 の前提は反証される。

Git の公式 `git-config` 文書は `diff.renames` が `git diff`/`git log` のような Porcelain にだけ作用し、lower-level command には作用しないと明記している。また copy 検出は `diff.renames=copies` で指定し、独立した公式設定 `diff.copies` は存在しない。[git-config の `diff.renames`](https://git-scm.com/docs/git-config#Documentation/git-config.txt-diffrenames)

ソースでも `git diff-tree` は `git_diff_basic_config` を読み、「diff UI options は読まない」としている。[Git `builtin/diff-tree.c`](https://github.com/git/git/blob/master/builtin/diff-tree.c#L115-L118) `diff.renames` を処理するのは `git_diff_ui_config` 側であり、basic config 側ではない。[Git `diff.c`](https://github.com/git/git/blob/master/diff.c#L2714-L2732)

したがって、現行 Git 契約では `-M -C` を消すだけで十分である。ただし私は read-only sandbox 上で controlled repo を作れず、config 別の実測はしていない。親が実測する最小例は次のとおり。

```bash
probe_dir=$(mktemp -d)
git -C "$probe_dir" init -q
git -C "$probe_dir" config user.name Test
git -C "$probe_dir" config user.email test@example.invalid
mkdir -p "$probe_dir/docs/archive"
seq 1 100 > "$probe_dir/docs/worklog.md"
git -C "$probe_dir" add . && git -C "$probe_dir" commit -qm base

sed -n '1,85p' "$probe_dir/docs/worklog.md" \
  > "$probe_dir/docs/archive/worklog-phase3-0101-1.md"
sed -n '86,100p' "$probe_dir/docs/worklog.md" > "$probe_dir/worklog.next"
mv "$probe_dir/worklog.next" "$probe_dir/docs/worklog.md"
git -C "$probe_dir" add -A && git -C "$probe_dir" commit -qm fold

git -C "$probe_dir" config diff.renames copies
git -C "$probe_dir" config diff.copies true
git -C "$probe_dir" diff-tree --root -r --no-commit-id --name-status HEAD
git -C "$probe_dir" diff-tree --root -r --no-commit-id --name-status -M -C HEAD
git -C "$probe_dir" diff-tree --root -r --no-commit-id --name-status --no-renames HEAD
```

期待は、1 本目と 3 本目が `M`+`A`、2 本目だけが `M`+`Cnnn` になること。

実装としては、それでも `--no-renames` を推奨する。現在の config 脅威への対策ではなく、ユーザー裁定を明示する fail-closed なコマンド契約であり、Git 自身もこのオプションを「設定による既定値があっても rename detection を切るもの」と定義しているためである。[git-diff-tree の `--no-renames`](https://git-scm.com/docs/git-diff-tree#Documentation/git-diff-tree.txt---no-renames)

## (P2) R/C 分岐の判断

残す案の利点は、将来 `-M`/`-C` が誤って戻り、argv 固定テストまで同時に弱められた場合にも landed fragment rename を拒否できること。欠点は、正常系では到達不能で、主要防壁であるかのような誤解を招くこと。`path-status` の明示 R/C 判定は閉集合判定との完全な重複でもある。

消す案の利点は、入力契約を「Git が D/A/M に正規化する」に一本化し、保証の実体を `--no-renames` とそのテストへ集約できること。欠点は、移動検出フラグと固定テストが同時に壊れた場合、landed 区間の R fragment を拾う予備防壁がなくなること。

推奨は「特殊分岐を消す」。

- `_landed_fold_output_path` は M FOLDED と D fragment だけにする。
- fold slot の明示 R/C 条件は消すが、閉集合判定が引き続き R/C を拒否する。
- fragment rename が D+A として拒否される統合テストを追加し、I2 が弱まらないことを実経路で固定する。

## (P3) テスト計画

静的に確認した fold 系 12 本は以下を覆う。

- 通常 fold 正例、null-fold の正負、隠れた先行 fold、merge parent、encoding header。
- landed 区間の通常文書、FOLDED 作成、fragment 削除・変更、FOLDED 変更。
- fold commit への allowlist 外 `A` の拒否。

一方、landed 区間で archive path を許すテストは fold slot の rotation 被覆ではない。valid rotation `A`、archive 2 件、archive README 単独変更、no-renames 下の fragment rename は未被覆だった。

純増するテストは次の 5 本を推奨する。

1. `test_commit_diff_explicitly_disables_rename_and_copy_detection`

   これがないと、rotation fixture の類似度次第で `-M` または `-C` の再導入を見逃す。

2. `test_declared_fold_accepts_high_similarity_rotation_with_repo_local_diff_config`

   85〜95% 相当を archive へ移し、対照の明示 `-M -C` が実際に `Cnnn` を返すことを確認したうえで、repo-local `diff.renames=copies` / `diff.copies=true` があっても verifier が受理することを検査する。これがないと今回の実障害そのものを見逃す。

3. `test_declared_fold_rejects_multiple_rotation_archives`

   valid rotation path を 2 件追加して `archive-count` を期待する。これがないと archive 最大 1 件の縮退を見逃す。

4. `test_declared_fold_rejects_archive_readme_without_rotation`

   README の M と archive A=0 で `archive-readme` を期待する。これがないと README と rotation の結合条件消失を見逃す。

5. `test_landed_interval_rejects_fragment_rename_after_move_detection_is_disabled`

   landed commit で fragment を rename し、D+A 化後も `landed-fold-owned-path` を期待する。これがないと R 特例削除による I2 の実経路退行を見逃す。

既存テストの期待値・名前は変更しない。

## 変異候補

- `--no-renames` を `-M -C` に戻す → 新規 command 契約テストと高類似度 rotation 正例が赤になるべき。
- `--no-renames` に加えて `-M` だけを再導入する → command 契約テストが赤になるべき。copy fixture だけでは `-M` 単独を捕捉できない。
- valid `A` を常に `added-path` にする → rotation 正例が赤になるべき。
- `archive_adds > 1` を `archive_adds > 2` にする → multiple archives 負例が赤になるべき。
- `archive_readme_modified and archive_adds != 1` を削除する → README 単独変更負例が赤になるべき。
- `_landed_fold_output_path` から D fragment 判定を削除する → 既存 fragment deletion と新規 fragment rename の両方が赤になるべき。

過剰検出確認の「通る正例」は、最初の `-M -C` 復元変異を入れても `test_declared_fold_accepts_exact_direct_child_shape_without_plan_comparison` が緑のままであること。rotation/copy のない通常 fold まで一律拒否する変異になっていないことを確認する。

## 呼び出し側への静的波及

- [tools/dev_wave_land.py:1513](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/dev_wave_land.py:1513): rotation fold が `path-status` で落ちず、成功結果へ進む。従来の rollback、エラー detail、API は変更しない。
- [tools/dev_wave_land.py:1820](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/dev_wave_land.py:1820): noop 検証の結果は変わらない。landed rename は D+A として引き続き検出する。
- [tools/dev_waves/checker.py:543](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/dev_waves/checker.py:543): schema v2 の valid rotation receipt が `fold-commit` pass になる。slot 名、reason/detail 変換、例外処理は不変。
- [tools/dev_waves/daemon.py:1526](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/dev_waves/daemon.py:1526): valid rotation を含む完了 receipt の recovery が受理され、誤った `AMBIGUOUS_RECOVERY` 停止を避ける。timeout、schema v1 分岐、identity 条件は不変。
- `commit-diff` の参照は `_commit_diff` に閉じているため、3 caller の引数、戻り値、公開 interface に編集は不要。

テストは実行していない。環境は `pegasus02` ログインノードであり、read-only 制約とリポジトリ規律により pytest は実行不可。緑の nodeid は主張しない。

## 総括

- 実装の核は `commit-diff` の `-M -C` を `--no-renames` へ置換し、R/C 特例を整理すること。
- path allowlist と最低形、archive 最大数、landed fold 署名は変えない。
- P1 裁定: config 脅威の前提は反証。択一は「単に削除」対「明示 `--no-renames`」で、後者を推奨。
- P2 裁定: 到達不能な特殊分岐を残す対消すで、消す案を推奨。fold slot の R/C 拒否自体は閉集合判定に残る。
- P3 裁定: 親案の 2 本だけにする対、隣接境界を含む 5 本にするで、5 本を推奨。