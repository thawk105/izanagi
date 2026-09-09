## 総括

A-5 の終了処理から共有 CCBench gitdir への prune と全付随処理を撤去し、自身の CCBench／superproject worktree の `remove --force` だけを残す。  
receipt は先頭の cleanup rc を B-10 と揃えつつ、失敗して残った path を型別の機械可読行で追記する。  
契約テストでは prune の字句的不在と自 path remove を固定し、実 git fixture では見えない兄弟登録が normal／abnormal exit の双方を跨いで残ることを検証する。  
`WORKTREE_CLEANUP_CAP_S`、B-10、投入器、登録簿は変更しない。実装・テスト実走は行っていない。

## 変更設計

### `tools/pegasus/a5_second_boot_backoff_sweep.sh`

現行 `remove_worktrees()` の変数宣言 2 行を削除する。

| 現行位置 | 現行逐語 | 置換後 |
|---|---|---|
| `rekt:126` | `local remove_rc=0` | 削除 |
| `:127` | `local prune_rc=0` | 削除 |

現行 `:130-154` の二つの自 path remove は残す。行削除後は `:128-152` になる。

```bash
if [[ -n "$CCBENCH_BASE" && -n "$JOB_CCBENCH" ]]; then
  remaining=$((deadline - SECONDS))
  if [[ "$remaining" -le 0 ]]; then
    cleanup_rc=124
  else
    timeout "$remaining" git -C "$CCBENCH_BASE" worktree remove --force \
      "$JOB_CCBENCH" >>"$OUTPUT_ROOT/env/ccbench-worktree-remove.stdout" \
      2>>"$OUTPUT_ROOT/env/ccbench-worktree-remove.stderr" || command_rc=$?
    [[ "$command_rc" -eq 0 ]] || cleanup_rc=$command_rc
    [[ "$command_rc" -eq 0 ]] && JOB_CCBENCH=""
  fi
fi
command_rc=0
if [[ -n "$REPO_BASE" && -n "$JOB_REPO" ]]; then
  remaining=$((deadline - SECONDS))
  if [[ "$remaining" -le 0 ]]; then
    [[ "$cleanup_rc" -ne 0 ]] || cleanup_rc=124
  else
    timeout "$remaining" git -C "$REPO_BASE" worktree remove --force \
      "$JOB_REPO" >>"$OUTPUT_ROOT/env/repo-worktree-remove.stdout" \
      2>>"$OUTPUT_ROOT/env/repo-worktree-remove.stderr" || command_rc=$?
    [[ "$cleanup_rc" -ne 0 || "$command_rc" -eq 0 ]] || cleanup_rc=$command_rc
    [[ "$command_rc" -eq 0 ]] && JOB_REPO=""
  fi
fi
```

`$JOB_CCBENCH` と `$JOB_REPO` はいずれも当該 job が作った自 path である。superproject 側 remove まで外すと自分の `$JOB_REPO` を漏らすため、D1700 の趣旨に反する。危険なのは共有 CCBench gitdir全体を走査する prune であり、現行 `:148-152` の repo remove ではない。

現行 `:155-169` は次の全体を撤去する。

```bash
remove_rc=$cleanup_rc
if [[ -n "$CCBENCH_BASE" ]]; then
  remaining=$((deadline - SECONDS))
  if [[ "$remaining" -le 0 ]]; then
    prune_rc=124
  else
    timeout "$remaining" git -C "$CCBENCH_BASE" worktree prune --expire now \
      >>"$OUTPUT_ROOT/env/ccbench-worktree-prune.stdout" \
      2>>"$OUTPUT_ROOT/env/ccbench-worktree-prune.stderr" || prune_rc=$?
  fi
  [[ "$cleanup_rc" -ne 0 || "$prune_rc" -eq 0 ]] || cleanup_rc=$prune_rc
fi
printf '%s\nprune_rc=%s\n' "$remove_rc" "$prune_rc" \
  >"$OUTPUT_ROOT/env/worktree-remove.rc" || true
return "$cleanup_rc"
```

置換後 `:153-160` は次の逐語とする。

```bash
{
  printf '%s\n' "$cleanup_rc"
  [[ -z "$JOB_CCBENCH" ]] || \
    printf 'remaining_ccbench_path=%s\n' "$JOB_CCBENCH"
  [[ -z "$JOB_REPO" ]] || \
    printf 'remaining_repo_path=%s\n' "$JOB_REPO"
} >"$OUTPUT_ROOT/env/worktree-remove.rc" || true
return "$cleanup_rc"
```

これにより次も消える。

- `env/ccbench-worktree-prune.stdout` への追記
- `env/ccbench-worktree-prune.stderr` への追記
- prune timeout の `124`
- `prune_rc` と `cleanup_rc` の合成
- remove 結果を退避するだけだった `remove_rc`

remove 失敗の伝播経路は次のまま保たれる。

- CCBench remove 失敗: 現行 `:137-139`、置換後 `:135-137` で `cleanup_rc=$command_rc`、path はクリアされない。
- repo remove 失敗: 現行 `:150-152`、置換後 `:148-150` で、先行失敗が無ければ `cleanup_rc=$command_rc`、path はクリアされない。
- `remove_worktrees` は置換後 `:160` でその `cleanup_rc` を返す。
- `cleanup_worktrees` は現行 `:178`、置換後 `:169` で `remove_worktrees || cleanup_rc=$?` として受け取る。
- 元の job rc が 0 の場合だけ、現行 `:180-183`、置換後 `:171-174` が `write_failure_receipt` を呼び、job rc を cleanup rc にする。
- 元の job rc が非 0 なら、現行 `:180` の条件は成立せず、現行 `:184`、置換後 `:175` から元の rc で終了する。

`WORKTREE_CLEANUP_CAP_S=120` は変更しない。したがって `:16-27` の計算は引き続き `6150 + 1049 = 7199 < 7200` であり、契約テスト `test_a5 rospector:249-270` と矛盾しない。

## receipt 書式の裁定

案 (b) を採る。正常時は B-10 と同じく一行だけである。

```text
0
```

失敗時は次の形になる。二方とも残れば両行を書き、一方だけなら対応行だけを書く。

```text
<cleanup_rc>
remaining_ccbench_path=<JOB_CCBENCH の絶対 path>
remaining_repo_path=<JOB_REPO の絶対 path>
```

先頭を裸の `<cleanup_rc>` に保つため、B-10 の一行形式との共通部分も失わない。成功した remove は現行どおり変数を空にするので、残置行は「remove が成功しなかった path」にだけ現れる。

案 (a) の一行 rc と stderr だけでは D1700 の「残置を明示」を満たさない。特に現行 `:132-134` と `:145-147` の cleanup deadline 枯渇では git 自体を起動しないため、stderr に path が出ない。git を起動した場合も stderr は非構造テキストであり、path の出力をこの job body は保証していない。一方、案 (b) は成功時にだけ空へ更新される `JOB_CCBENCH`／`JOB_REPO` をそのまま記録するため、後続の安全な掃除が調査すべき path を確定できる。

`rg -n --hidden --fixed-strings 'worktree-remove.rc' . --glob '!.git/**'` の全ヒットは次の4件だった。

- `tools/pegasus/a5_second_boot_backoff_sweep.sh:168` — A-5 producer。今回変更対象。
- `tools/pegasus/b10_backoff_grid.sh:169` — B-10 producer。変更しない。
- `orchestrator/tests/test_backoff_extended_sweep.py:1785` — B-10 receipt を `"0\n"` と読む consumer。A-5 の出力ではなく、変更不要。
- `output/insights/2026-09-07_t2320-backoff-sweep-gate-layer2/README.md:195` — 過去実測の歴史記録。consumer ではなく変更しない。

これに加えて `orchestrator/tests/test_a5_second_boot_job_contract.py:298` がファイル名を介さず、producer の `printf` 逐語を静的に固定している。現時点で A-5 receipt を実行時に読む repo 内 script は無い。今回追加する実 git fixture が最初の A-5 runtime consumer になる。

## テスト設計

### 静的契約の改訂

`orchestrator/tests/test_a5_second_boot_job_contract.py:297-298` の現行逐語:

```python
assert 'git -C "$CCBENCH_BASE" worktree prune --expire now' in normalized_job
assert "printf '%s\\nprune_rc=%s\\n'" in job
```

これを次へ置換する。

```python
assert re.search(r"\bworktree\s+prune\b", normalized_job) is None
assert "ccbench-worktree-prune." not in job
assert "prune_rc" not in job
assert normalized_job.count(
    'timeout "$remaining" git -C "$CCBENCH_BASE" '
    'worktree remove --force "$JOB_CCBENCH"'
) == 1
assert normalized_job.count(
    'timeout "$remaining" git -C "$REPO_BASE" '
    'worktree remove --force "$JOB_REPO"'
) == 1
assert "printf '%s\\n' \"$cleanup_rc\"" in job
assert "printf 'remaining_ccbench_path=%s\\n' \"$JOB_CCBENCH\"" in job
assert "printf 'remaining_repo_path=%s\\n' \"$JOB_REPO\"" in job
```

単一の旧コマンド文字列だけを `not in` に反転するより強い形である。

- 正規化後の全 job body から literal な `worktree prune` 呼出しを禁止する。
- 旧 prune artifact 名と `prune_rc` の残骸も禁止する。
- 許可する二つの自 path remove を各1回に固定する。
- 構文の書き換えで静的検査をすり抜けても、後述の実 git fixture が兄弟登録の消失を検出する。

`_assert_execution_shape` の他の契約とは矛盾しない。現行 `:291-292` は `$JOB_REPO` と `$JOB_CCBENCH` が当該 job 固有 path であることを既に固定し、`:293-296` は出力／finalizer、`:299-303` は投入器を検査しているだけである。walltime は別 helper の `:249-270` が固定しており、cleanup cap は変えない。

### 実 git fixture

新規 test file は作らず、`orchestrator/tests/test_a5_second_boot_job_contract.py` に追加する。理由は、job body の静的受理形と挙動を同じ `_assert_current_pair_contract` 系列に置け、変更ファイルを job body と契約テストの2件に限定できるためである。

現行 `:1-6` の import へ `shutil`、`subprocess`、`tempfile` を追加する。現行 `:13` の定数群直後には、B-10 の先例 `test_backoff_extended_sweep.py:46-88` と同型のローカル helper を置く。

- `_git(cwd, *args, input_text=None)`
- `_fixture_git_repository(root)`
- `_add_detached_worktree(repository, path, commit)`
- `_shell_function(script, name)`
- A-5 固有の `_run_a5_cleanup_snippet(...)`

B-10 test moduleから private helper を import すると、その巨大な pytest module と campaign import 群まで読み込むため採らない。共通 helper file への一般化も本 wave の scope 外である。

現行 `:374` の `_run()` より前に、引数なしの次の2 test を追加する。既存 self-run harness `:374-393` は `test_` 関数を引数なしで直接呼ぶため、pytest の `tmp_path` fixtureは使わず `tempfile.TemporaryDirectory()` を使う。

#### `test_a5_job_exit_cleanup_preserves_missing_sibling_worktree_registration`

fixture と assert は次の構成にする。

1. superproject 用と CCBench 用の二つの bare git repository を作る。
2. superproject repository から `$JOB_REPO` を detached worktree として作る。
3. CCBench repository から `$JOB_CCBENCH=$JOB_REPO/external/ccbench` を detached worktree として作る。
4. 同じ CCBench repository から別 path に兄弟 job の detached worktree を作り、そのディレクトリだけを `shutil.rmtree` で消す。gitdir 側の登録は残し、事前に `git worktree list --porcelain` に兄弟 path が現れることを assert する。
5. job body から `_shell_function` で `remove_worktrees` と `cleanup_worktrees` を抽出する。
6. `WORKTREE_CLEANUP_CAP_S=30`、各 base/path、`OUTPUT_ROOT_READY=1` を束縛した bash snippet に `trap cleanup_worktrees EXIT` を設定する。
7. `job_rc` を `0` と `23` の二通りで、それぞれ独立 fixture 上で実行する。

各ケースで以下を assert する。

- subprocess returncode は入力した `job_rc` と等しい。
- `$JOB_CCBENCH` と `$JOB_REPO` のディレクトリが消える。
- 両自 path がそれぞれの `git worktree list --porcelain` から消える。
- ローカルには存在しない兄弟 path は CCBench repository の worktree 登録に残る。
- `env/worktree-remove.rc` は正確に `"0\n"`。
- cleanup 成功なので、stub の `write_failure_receipt` は呼ばれない。

これは B-10 の `test_backoff_extended_sweep.py:1752-1785` と同じ実関数抽出・実 git 実走だが、A-5 固有の二重 worktree と「欠落していて prune 可能な兄弟登録」を負例として追加する。

#### `test_a5_cleanup_failure_records_remaining_paths_and_preserves_exit_precedence`

二つの bare repository に対し、`JOB_CCBENCH` と `JOB_REPO` には登録されていない path を渡して、両 `worktree remove --force` を実 git エラーにする。同じ snippet を元 job rc `0` と `23` で走らせる。

各ケースで以下を assert する。

- receipt の第1行は非0整数。
- 続く行は順に
  `remaining_ccbench_path=<指定 path>`、
  `remaining_repo_path=<指定 path>`。
- 元 job rc `0` の場合、subprocess returncode は receipt 第1行と一致し、stub の `write_failure_receipt` は同じ rc と `worktree_cleanup` stage を1回記録する。
- 元 job rc `23` の場合、subprocess returncode は `23` のままで、stub の `write_failure_receipt` は呼ばれない。

これで `remove_worktrees → cleanup_worktrees → job rc` の fail-closed 伝播と、現行 `:180` の failure receipt 発火条件を挙動として固定する。

新規 test file ではないため、pytest-only allowlist や新しい self-run harness は不要である。既存 `:374-393` が二つの新規 no-argument test も自動収集する。

## 変異事前登録候補

行番号は上記 job body 置換後の予定行。実装後、DW-M07 に従い exact line と old 逐語の一意性を再確認する。

| ID | 位置・old 逐語 | 変異 | 期待 KILL node | 単一理由性 |
|---|---|---|---|---|
| M1 | `a5_second_boot_backoff_sweep.sh:160`、`return "$cleanup_rc"` | 直前へ `git -C "$CCBENCH_BASE" worktree prune --expire now` を注入 | `test_current_scripts_are_a_positive_example_of_the_complete_contract`、`test_a5_job_exit_cleanup_preserves_missing_sibling_worktree_registration` | 追加される状態変化は共有 gitdir の prune だけ。静的 node は禁止呼出し、実 git node は同じ呼出しによる兄弟登録消失を検出する。意味上の赤理由は一つ。 |
| M2 | `a5_second_boot_backoff_sweep.sh:160`、`return "$cleanup_rc"` | `return 0` | `test_a5_cleanup_failure_records_remaining_paths_and_preserves_exit_precedence` | remove 失敗を成功へ変える唯一の変化。静的 execution-shape node はこの return 逐語を固定しないため mask／重複 kill がない。 |
| M3 | `a5_second_boot_backoff_sweep.sh:137`、`[[ "$command_rc" -eq 0 ]] && JOB_CCBENCH=""` | `JOB_CCBENCH=""` | `test_a5_cleanup_failure_records_remaining_paths_and_preserves_exit_precedence` | 失敗した CCBench path を成功扱いで忘れ、receipt の `remaining_ccbench_path` だけを欠落させる。rc 伝播自体は残るため赤理由を残置明示の欠落に限定できる。 |
| M4 | `a5_second_boot_backoff_sweep.sh:171`、`if [[ "$original_rc" -eq 0 && "$cleanup_rc" -ne 0 ]]; then` | `if [[ "$cleanup_rc" -ne 0 ]]; then` | `test_a5_cleanup_failure_records_remaining_paths_and_preserves_exit_precedence` | cleanup 前から非0だった job rc を cleanup rc で上書きし、failure receipt を余分に発火させる一変更。兄弟保存・静的 prune 検査には影響しない。 |

M1 の期待 node は完全集合として2件を登録する。二つの test failure は同じ共有 prune の再導入を異なる観測面で示すもので、別々の受理集合変更ではない。

## 未解決・親への差し戻し

設計上の未解決事項はない。(P1) は、receipt 専用 field を採用、repo 側の自 path remove を維持、実 git fixture を既存 A-5 契約テストへ追加、で決着できる。  
書込み不能かつ段2プランのみの依頼なので、pytest、bash snippet、mutation harness は実走しておらず、緑とは報告しない。