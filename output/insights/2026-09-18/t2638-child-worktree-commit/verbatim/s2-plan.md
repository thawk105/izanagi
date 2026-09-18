## 変更面 (file:line 表)

行番号は現状のもの。追加関数・テストは挿入先の既存行を示す。指定された射影のみを読み、書き込み・実装・pytest 実行は行っていない。

| scope | 変更箇所 | 現状 → 変更後 |
|---|---|---|
| 1 起動器 | `tools/dev_wave_codex.py:226` `_launcher_argv`、`:248` | 生成した job-id・artifact_dir は argv 内だけで利用 → 終端処理にも渡せるよう、解決済み値を args に保持。argv の既存内容は維持 |
| 1 起動器 | `tools/dev_wave_codex.py:339` `main`、特に `:347` | launcher rc を即 return → rc を保存し、workspace-write の author/fix だけ共有 helper を呼び、結果と rc を合成 |
| 2 待ち手 | `tools/dev_wave_wait.py:1591` `_ProducerArgumentParser.parse_args`、`:1630` `_producer_parser` | commit opt-in なし → `--commit-worktree` を `Path`、既定 `None` で追加し、指定時だけ絶対パス検査 |
| 2 待ち手 | `tools/dev_wave_wait.py:1961` `wait_for_producer` | 死亡待ち・ファイル待ちのみ → opt-in 時だけ終端 commit を実施。既存のファイル待ちと失敗を維持 |
| 2 待ち手 | `tools/dev_wave_wait.py:1827`、`:1927` の間に `_commit_producer_worktree` を追加 | 共通の終端処理なし → 通常待機と check-only から呼ぶ小さな adapter。producer receipt の payload は変更しない |
| 3 helper | `tools/dev_waves/git_state.py:68` `GIT_COMMANDS`、`:214` 後に `commit_worker_worktree` を追加 | 観測・worktree 作成中心 → 終端残差の commit を行う共有関数を1つ追加 |
| 4 message | 同 helper 内。入力根拠は `tools/codex_worker_launch.py:2638`、`:2642`、`:2645` | 終端 commit message なし → receipt を参照し、指定本文と単一 `AI-Agent` trailer を生成 |
| 5 docs・親担当 | `docs/dev-wave/workers.md:20`〜`:24` | HEAD 基準の staged patch → `<base>` 基準。終端 commit 文を追加し、同節で bytes 相殺 |
| 6 テスト | `orchestrator/tests/test_dev_wave_codex.py:381`、`:432`、`:638` 前 | 実 Git＋fake launcher を拡張し、終端 commit と rc 契約を検証 |
| 6 テスト | `orchestrator/tests/test_dev_wave_wait.py:5090`、`:5155`、`:5273`、`:5303`、`:5455` 後 | CLI option 集合の更新、opt-in 終端処理、非 opt-in の bytes 回帰を追加 |
| 6 テスト | `orchestrator/tests/test_dev_waves_git_state.py` | helper の実 Git テストを追加。既存本文は射影外のため挿入行は未確認 |

**配線上の未確認箇所:** waiter の `main` は指定範囲外である。`_parse_cli(:1695)` が返す args を、通常待機・check-only の両経路へ渡す変更も必要。実装段ではその呼出し部分だけを追加確認し、正確な変更行を確定する。`:1961` の変更だけで CLI 配線が完了するとは扱わない。

## helper 設計

**既存 `tools/dev_waves/git_state.py` に追加する。** `_git_env(:164)`、`_run(:178)`、`_text(:208)` と Git hardening を再利用でき、新 module から private 関数を輸入する構造や Git 実行の重複を避けられる。

共有関数は例えば以下とする。永続 schema・台帳・結果 class は作らない。

```python
commit_worker_worktree(
    repo_root, *, artifact_dir, wave, job_id, stage, launcher_rc
) -> tuple[str, str | None]
```

返値は `(committed, sha)`、`(clean, None)`、`(skipped, reason)`、`(failed, reason)`。helper が固定書式を1回出力し、呼出し元は返値で rc を決める。

`GIT_COMMANDS(:68)` は以下の変更に限定する。

| 操作 | 対応 |
|---|---|
| `symbolic-ref --quiet --short HEAD` | 既存 `branch(:72)` を使用 |
| `rev-parse --show-toplevel` | 既存 `toplevel(:70)` を使用 |
| `rev-parse --path-format=absolute --git-path <name>` | `git-path` を追加。linked worktree の管理ファイルを正しく解決 |
| `git add -A` | `add-all` を追加 |
| `git diff --cached --quiet` | `staged-quiet` を追加。戻り値 0 と 1 を明示的に許可 |
| `git -c commit.gpgSign=false commit -F <file>` | `commit-file` を追加 |
| commit 後の SHA | 既存 `head(:71)` を使用 |

`_run` の allowlist 判定・例外処理そのものは広げない。既存 `GIT_HARDENING_CONFIG(:37)` により hooks は無効化されたままとする。

identity は `_git_env(:168)` が global/system config と環境注入を排除するため、brief 指定の repo-local `user.name/user.email` を使う。helper が `thawk105` を設定したり、架空の identity を補ったりしない。identity 不備による commit エラーは `failed reason=commit`。stage 済み内容を戻さない。

## 発火判定と rc

起動器は `main(:347)` の launcher 復帰後に判定する。dry-run は既存 `:344` の return で終わり、helper を呼ばない。read-only も helper を呼ばない。

stage は author/fix を対象とし、それ以外の workspace-write 指定は `skipped reason=stage`。理由は後述の P2。`AUTHORITY_BOUND_STAGES` は review/focus も含むため、発火集合として流用しない。

helper は **`add -A` より前**に次を順番に検査する。

| 条件 | 結果 |
|---|---|
| `toplevel.resolve()` と `repo_root.resolve()` が不一致 | `skipped reason=root-mismatch` |
| `branch` の rc=1 | `skipped reason=detached-head` |
| branch が厳密に `main` または `master` | `skipped reason=protected-branch` |
| `MERGE_HEAD` が存在 | `skipped reason=merge-in-progress` |
| `rebase-merge` または `rebase-apply` が存在 | `skipped reason=rebase-in-progress` |
| `CHERRY_PICK_HEAD` または sequencer が存在 | `skipped reason=sequencer-in-progress` |
| Git が解決した `index.lock` が存在 | `skipped reason=index-lock` |
| Git 起動・観測・管理パス確認でその他のエラー | `failed reason=<固定識別子>` |

`.git` をディレクトリと仮定せず、各管理パスを `git-path` で得る。lock は削除しない。事前検査後に lock が出現して add/commit が失敗した場合も、lock の存在を確認できれば skip、それ以外は failed とする。

安全条件を満たした後は `add-all` → `staged-quiet` → 必要なら `commit-file` → `head`。diff の rc=0 は clean、1 は変更あり、それ以外は failed。失敗時に reset・checkout・clean・再試行はしない。

stdout は helper 呼出し1回につき以下のどれか1行。Git 自身の stdout は捕捉する。

```text
worktree-commit: committed <sha>
worktree-commit: clean
worktree-commit: skipped reason=<reason>
worktree-commit: failed reason=<reason>
```

skip の NOTE、failure の `NG:` は stderr に出す。

起動器の rc は P1 を採用する。

| launcher rc | helper 結果 | 最終 rc |
|---|---|---|
| 非0 | すべて | 元の rc |
| 0 | committed / clean / skipped | 0 |
| 0 | failed | 2、stderr に `NG:` |

signal による負の `subprocess` returncode も、今回だけ別の値へ変換しない。launcher 起動自体の `OSError(:349)` は従来のエラー経路を維持する。

## commit message

件名を固定し、本文値は単一行に escape する。receipt 内の改行から追加 trailer を混入させない。

```text
[T-2638] 起動器/待ち手の終端契約 (D2044 項 16)

wave: <wave>
job-id: <job-id>
stage: <stage>
launcher rc: <rc-or-unknown>
receipt outcome: <outcome-or-unknown>

AI-Agent: product=codex; model=<model>; reasoning=<effort>; role=author
```

model と effort は**別々に**、空でない文字列の `recorded_*` → `requested_*` → `unknown` を採る。根拠は launcher receipt の `:2642`〜`:2646`。欠落・破損 receipt は残差 commit を妨げず、取得不能な値を unknown にする。

正規化は `docs/ai-provenance.md:31` に合わせる。

1. 小文字化する。
2. `[a-z0-9._-]` 外の文字を `-` に置換し、連続する `-` を畳む。
3. 先頭が英数字になるまで先頭の記号を除き、末尾の置換区切りを除く。
4. 空または fullmatch 不成立なら `unknown`。

最終段落には `AI-Agent` をちょうど1行置く。`AI-Agent: none` は使わない。

message は `artifact_dir/tmp/` の一意な一時ファイルへ UTF-8 で書き、close 後に `commit -F` へ渡す。**一時ファイルの生成は `add -A` と staged 判定の後**に行い、artifact_dir が repo 内にある場合も message 自体を新たに stage しない。処理後に削除するのはこの一時ファイルだけとする。

## 待ち手

`_producer_parser(:1630)` に `--commit-worktree <abs>` を追加し、既定値は `None`。既存 `--receipt-file` は producer の証明書出力であり、launcher receipt と混同しない。

opt-in 呼出しでは、既存 `--artifact-file` に対象 job の `<artifact_dir>/receipt.json` を渡す契約とする。そこから artifact_dir、親ディレクトリから wave、ディレクトリ名から job-id を得る。receipt があれば stage・sandbox・provenance を参照し、`sandbox=read-only` または非実装 stage なら共有 commit helper を呼ばない。

receipt 未生成時にも救済するため、**`--commit-worktree` 自体を workspace-write 実装子に対する呼出し元の明示指定**として扱う。receipt 欠落時の stage 等は unknown。この flag を read-only 子へ渡さないことは呼出し側契約であり、存在しない receipt から sandbox を推測したとは報告しない。

通常待機では `wait_for_producer(:1961)` に任意引数を追加する。

- flag 無しでは、done 内容の追加 read、receipt の追加 read、Git 操作を一切行わない。
- opt-in では「done file 非空」または `_PidState.DEAD` の観測後だけ helper を1回呼ぶ。
- 空の done file と生存 PID、または死亡の根拠がない UNKNOWN では呼ばない。
- rc≠0 の done 内容でも commit は行う。
- receipt/output が未生成でも、PID 死亡確定後の残差 commit は行う。既存のファイル欠落失敗は成功に変えない。

check-only でも `_derive_producer_state(:1827)` の観測後に同じ adapter を呼ぶ。done 非空による commit 許可と、既存 producer receipt の公開条件は分ける。`_producer_state_outcome(:1846)` と `_producer_receipt_payload(:1909)` の成功条件・field・serializer は変更しない。

waiter の既存失敗 rc は維持する。opt-in で既存 outcome が成功の場合、done の非0 rc が得られればそれを返し、そうでなければ helper failed を rc=2 にする。成功 receipt の公開より前にこの合成を行う。

flag 無しの保証は JSON の同値比較では足りない。既存成功・失敗ケースで stdout、stderr、rc、receipt **raw bytes**、書込み有無と mtime を固定する。CLI help に新 option が増える差だけは意図した変更として扱う。

## テスト計画

新規テストは実 Git repo と実ファイルを主とする。helper・死亡判定を monkeypatch しない。必要な失敗注入だけ既存 `subprocess.run` seam を利用し、それ以外の Git 呼出しは実行する。

`test_dev_wave_codex.py:638` の plain runner は引数なしで test を呼ぶため、このファイルの追加テストも既存同様 `TemporaryDirectory` を使う。helper・waiter の pytest テストは `tmp_path` を使う。

| 追加先・名前 | 正例／負例と実体 |
|---|---|
| `test_dev_waves_git_state.py` `test_commit_worker_worktree_records_residue_once` | topic branch に tracked 編集・削除・untracked を作る。commit が1つ増え、tree に全残差、trailer が1行、index が clean |
| 同 `test_commit_worker_worktree_clean_is_noop` | clean repo と2回目呼出しで `clean`、HEAD 不変 |
| 同 `test_commit_worker_worktree_skips_detached` | 実 `checkout --detach`。HEAD・index・作業ファイル不変 |
| 同 `test_commit_worker_worktree_skips_protected_branch` | 実 `main` / `master`。双方で skip |
| 同 `test_commit_worker_worktree_skips_merge_in_progress` | 実 merge conflict を作り、`MERGE_HEAD` と unmerged index を保持したまま skip |
| 同 `test_commit_worker_worktree_skips_rebase_and_cherry_pick` | 実 rebase/cherry-pick conflict を作り skip。sequencer の未完了状態も対象 |
| 同 `test_commit_worker_worktree_skips_nested_root_and_index_lock` | repo サブディレクトリ指定、linked worktree の実 index.lock を別ケースで確認 |
| 同 `test_commit_worker_worktree_uses_local_identity` | repo-local identity を commit author/committer で確認 |
| 同 `test_commit_worker_worktree_identity_failure_keeps_residue` | identity を確定できない構成で failed。HEAD 不変、残差・stage 済み内容は保持 |
| 同 `test_commit_worker_worktree_provenance_fallback_and_normalization` | recorded 優先、片方欠落、requested fallback、receipt 欠落・破損、改行・`;`・先頭記号を実 commit message で確認 |
| 同 `test_commit_worker_worktree_base_patch_survives_commit` | add 後と helper commit 後の `git diff --cached <base> -- <所有パス>` bytes が一致 |
| `test_dev_wave_codex.py:638` 前 `test_workspace_write_commits_after_launcher_failure` | fake launcher が編集後 rc=7。commit は1つ増え、dispatcher rc=7 |
| 同 `test_commit_failure_preserves_launcher_rc` | launcher rc=0/7 × commit 失敗で最終 rc=2/7、`NG:` を確認 |
| 同 `test_read_only_never_invokes_worktree_commit` | dirty な安全な topic branch、read-only、launcher rc=0/7。commit 行なし、HEAD/index 不変。run seam で helper 用 Git 呼出しゼロも確認 |
| 同 `test_non_author_stage_workspace_write_skips_commit` | review/plan＋workspace-write の実呼出しで stage skip |
| 同 `test_dry_run_never_commits_worktree` | workspace-write dry-run でも HEAD/index 不変 |
| `test_dev_wave_wait.py:5455` 後 `test_producer_commits_after_death_without_receipt` | 実 producer を終了・回収し、receipt 未生成でも残差を commit。既存 files 失敗は維持 |
| 同 `test_producer_nonempty_done_allows_terminal_commit` | producer の終了通知後、PID がまだ残る条件で1回だけ commit |
| 同 `test_producer_alive_with_empty_done_does_not_commit` | 実生存 PID＋空 done＋短い timeout。HEAD/index 不変 |
| 同 `test_producer_read_only_receipt_never_commits` | opt-in でも receipt sandbox=read-only なら helper 不発火 |
| 同 `test_producer_commit_is_idempotent_after_dispatcher` | dispatcher commit 後は clean、追加 commit なし |
| 同 `test_producer_commit_check_only_and_failure_rc` | check-only でも死亡後のみ発火し、helper failure・done 非0を成功にしない |
| 同 `test_producer_without_commit_flag_preserves_bytes` | flag 無しで stdout/stderr/rc/receipt bytes を既存契約と比較。repo に残差があっても不変 |
| 同 `test_producer_commit_worktree_requires_absolute_path` | 相対パスは rc=2、Git 操作なし |

既存 `:5090` の option 集合には新 flag だけを追加する。`:5028` の exact event sequence、`:5155` の single-pass、`:5204`・`:5273` の不完全状態拒否、`:5303` の killed waiter 再確認契約は維持する。

実装後の検証は親が `tools/run_tests.py` 経由で対象テストを実行する。本段の静的確認をテスト成功とは扱わない。

## DW-S05-A 改訂案と予算相殺

親が `docs/dev-wave/workers.md:20`〜`:24` を次へ置換する。`:25` の pin 行はそのまま残す。

```text
所有 path が素な単位を別 worktree へ。依存完了後、所有 path 限定 patch
（`git add -A`→`git diff --cached <base> --output=<f> -- <所有パス>`→`git apply`。隔離 session の `git -C` 禁止）のみ展開・並列投入。
worktree は`-b`必須(detachedは midflight rc=1)。
投入先へ cd せず直前に `tools/check_wave_startup.py --repo <abs> --mode midflight`。rc≠0 で停止。
乖離量は非関門。gate 実測 NOTE≠0 なら anchor 再読（fail-open INFO を除く）。
workspace-write 残差は起動器/待ち手が終端 commit。
```

`<base>` は子へ渡した base commit を使う。子の現在 HEAD に置き換えない。

UTF-8・末尾 LF 込みの bytes は以下。

| 箇所 | 現状 | 改訂 | 差 |
|---|---:|---:|---:|
| 20行目 | 137 | 92 | −45 |
| 21行目、`<base>` 追加込み | 153 | 160 | ＋7 |
| 22行目 | 54 | 54 | 0 |
| 23行目 | 122 | 114 | −8 |
| 24行目 | 118 | 99 | −19 |
| 終端 commit 文 | 0 | 64 | ＋64 |
| **計** | **584** | **583** | **−1** |

L1.5 は brief の値を基準に **9,695 / 9,696 bytes**。同節だけで相殺できる。全層の実計数と pin 検査は親の編集後に `check_docs.py` で確定する。

## 変異候補

親が段4で、実装後の対象行とともに事前登録する。

| 反転・破壊する述語 | 殺すテスト |
|---|---|
| `sandbox == workspace-write` を反転／削除 | `test_read_only_never_invokes_worktree_commit` |
| author/fix stage 判定を削除 | `test_non_author_stage_workspace_write_skips_commit` |
| detached の rc=1 を許可 | `test_commit_worker_worktree_skips_detached` |
| protected branch 集合判定を反転 | `test_commit_worker_worktree_skips_protected_branch` |
| `MERGE_HEAD` の存在判定を反転 | `test_commit_worker_worktree_skips_merge_in_progress` |
| root 一致判定を削除 | `test_commit_worker_worktree_skips_nested_root_and_index_lock` |
| index.lock の存在判定を無視 | 同テスト |
| staged diff の rc=0/1 分岐を反転 | `test_commit_worker_worktree_clean_is_noop` と `...records_residue_once` |
| launcher rc=0 の場合だけ helper を呼ぶ | `test_workspace_write_commits_after_launcher_failure` |
| helper 結果で元の非0 rc を0にする | `test_commit_failure_preserves_launcher_rc` |
| failed＋元 rc=0 を成功にする | 同テスト |
| trailer を削除／requested を recorded より優先 | `test_commit_worker_worktree_provenance_fallback_and_normalization` |
| waiter opt-in 判定を削除 | `test_producer_without_commit_flag_preserves_bytes` |
| done の非空判定を existence 判定へ変更 | `test_producer_alive_with_empty_done_does_not_commit` |
| 死亡条件を外して commit | 同テスト |
| PID 死亡後も receipt 必須にする | `test_producer_commits_after_death_without_receipt` |

## brief への異論

**P2 の「sandbox だけで足りる」という根拠には異論。**

`tools/dev_wave_codex.py:65` と `:73` は stage/sandbox を独立に受理し、`_validate_combinations(:190)` は対応関係を検査しない。さらに `orchestrator/tests/test_dev_wave_codex.py:184` は plan＋workspace-write を正例としている。`AUTHORITY_BOUND_STAGES(:27)` も sandbox の制約ではない。

したがって「全 read-only 段は必ず read-only」という性質は現コードから保証できない。既存 CLI 受理集合を変えず、**終端だけ author/fix に限定する stage 判定**を追加する案とする。

**P3 は opt-in の意味を明文化する必要がある。** 現行 producer parser `tools/dev_wave_wait.py:1630` には sandbox・stage・launcher artifact_dir がない。`--commit-worktree` を workspace-write 実装子の明示指定とし、opt-in 時の `--artifact-file` を launcher receipt に結び付ける契約が必要。receipt が消失している read-only 子への誤指定まで、flag 単独で機械的に排除できるとは主張できない。

P1・P4・P5・P6：同意。P6 の稼働 branch 状態は本段では再走査していない。

## 総括

既存 `git_state.py` の共有 helper に、残差 commit・skip・provenance を集約する。起動器と opt-in 待ち手から終端時だけ呼び、元の失敗 rc と残差を保持する。文書案は同節内で1 byte削減できる。

実装段で追加確認が必要なのは waiter `main` の通常待機／check-only 配線と、helper テストファイルの挿入位置。P2 の stage 前提と P3 の opt-in 入力契約は上記の補足を採用する。