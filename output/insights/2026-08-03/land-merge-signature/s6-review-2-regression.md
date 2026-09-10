判定は **NO-GO** です。実装自体の主経路は裁定どおりですが、land の2つの consumer 配線を捕捉するテストがなく、checker/daemon の実行時挙動も完全同一ではありません。また、事前登録変異8件のうち2件は現実の置換として成立しません。

以下は静的レビューです。テストは実行しておらず、緑は主張しません。

## 1. 既存テストの誠実性

この観点での疑義は **refuted** です。

`8440786` が変更したテストは [test_dev_waves_git_state.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_git_state.py:1) の `+224/-0` のみです。

- 既存期待値の反転・緩和: なし
- skip / xfail の追加: なし
- 既存テストの削除: なし
- 既存 fixture の置換: なし
- 新しい `_main_fold_merge` は追加であり、既存 fixture の差し替えではない

指定された N31 テストは親 commit と `8440786` の両方で抽出部分の SHA-256 が同一でした。

`3b75ae89d4419d372cfbbf025ba61e011b7e0e422d49f70363ecf18a803dbfc5`

現在の逐語は [test_dev_waves_git_state.py:408](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_git_state.py:408) です。

```python
def test_n31_landed_interval_cannot_hide_an_earlier_fold():
    with _fresh() as tmp:
        repo = _repo(Path(tmp))
        pending = _seed_pending(repo, 2)
        tip = _code_commit(repo)
        first_fold = _fold_commit(repo, pending[:1])
        second_fold = _fold_commit(repo, pending[1:])
        result = verify_declared_fold_commit(
            repo, fold_commit_sha=second_fold, landed_main_sha=second_fold,
            landed_commits=(tip, first_fold), wave_tip=first_fold,
        )
        assert (not result.ok) and result.detail == "landed-fold-owned-path"
```

成果物影響: 既存の N31 拒否集合はテスト編集によって変更されていません。

## 2. consumer 閉包

`verify_declared_fold_commit` の production 呼び出しは4箇所です。

| consumer | 引数の変化 | 受理挙動の変化 | 制約するテスト |
|---|---|---|---|
| [dev_wave_land.py:1514](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_wave_land.py:1514) fold 経路 | `trusted_main_cutoff_sha=trusted_main_cutoff_sha` を追加 | trusted parent が一意なら、その parent→commit だけを検査して正当な main-fold merge を受理可能 | helper の直接テストのみ。land consumer E2E なし |
| [dev_wave_land.py:1823](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_wave_land.py:1823) no-fold 経路 | `trusted_main_cutoff_sha=tested_main` を追加 | 同上 | land consumer E2E なし |
| [checker.py:543](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/checker.py:543) | 無変更、cutoff 省略 | 正常な Git 応答では従来どおり全 parent 検査。ただし subprocess・失敗経路が増加 | no-cutoff helper テストはあるが、deadline/consumer テストなし |
| [daemon.py:1526](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/daemon.py:1526) | 無変更、cutoff 省略 | 正常な Git 応答では従来どおり全 parent 検査。ただし5秒 deadline 内のコマンド数が増加 | schema-v2 recovery の非 merge テストのみ。deadline/merge テストなし |

### F1 — real / must-fix: land の cutoff 配線をテストが捕捉していない

実装の重要な2行は次です。

```python
trusted_main_cutoff_sha=trusted_main_cutoff_sha,
```

— [dev_wave_land.py:1517](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_wave_land.py:1517)

```python
trusted_main_cutoff_sha=tested_main,
```

— [dev_wave_land.py:1826](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_wave_land.py:1826)

ところが、新しい正例は helper を直接呼んでいます。

```python
result = verify_declared_fold_commit(
    repo,
    fold_commit_sha=fold,
    landed_main_sha=fold,
    landed_commits=(tip,),
    wave_tip=tip,
    trusted_main_cutoff_sha=trusted_main,
)
```

— [test_dev_waves_git_state.py:426](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_git_state.py:426)

`test_dev_wave_land.py` には `trusted_main_cutoff_sha` を観測するテストがありません。既存の stale-resync E2E は merge を作りますが、main 側に fold signature を含めません。

```python
first = _land(repo.request(winner, tip=winner_tip))
...
_git(loser, "merge", "--no-edit", "main")
```

— [test_dev_wave_land.py:2482](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_wave_land.py:2482)

したがって、1517行または1826行の keyword を削除しても、新しい helper 正例は影響を受けず、既存 land テストも静的にはその欠落を捕捉しません。

成果物影響: 配線が退行すると、正当な main-fold merge を land CLI が `landed-fold-owned-path` と判定し、land 成果物を生成せず rollback します。

### F2 — real / must-fix: checker.py / daemon.py は「完全に同じ挙動」ではない

意味上の受理集合は、Git コマンドが正常終了する限り同じです。しかし実行時挙動は変わっています。

```python
parents = _commit_parents(
    repo_root,
    commit_sha,
    deadline=deadline,
    timeout_seconds=timeout_seconds,
)
if len(parents) < 2:
    return _commit_diff(...)
```

— [git_state.py:677](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:677)

従来は landed commit ごとに `_commit_diff` だけでした。現在は、

- 非 merge: `rev-list --parents` + `diff-tree` の2 subprocess
- merge: `rev-list --parents` + parent 数ぶんの `diff-tree`

になります。

checker では追加コマンドの失敗が次へ写像されます。

```python
except (DevWavesError, subprocess.TimeoutExpired):
    return _fold_commit_reason(receipt, check_id, "git-error")
```

— [checker.py:558](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/checker.py:558)

daemon は5秒 timeout を共有し、失敗すると recovery を ambiguous にします。

```python
timeout_seconds=5,
...
accepted_matches = False
```

— [daemon.py:1533](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/daemon.py:1533)

`test_landed_interval_without_cutoff_keeps_all_parent_scan` は全-parentという意味論だけを制約します。追加 subprocess、共有 deadline、consumer 側のエラー写像は制約しません。

成果物影響: 従来 deadline 内で受理できた長い landed interval が、checker では `fold-commit/git-error`、daemon では ambiguous recovery へ変わる可能性があります。

## 3. 新設テストの実効性

旧実装へ新テストファイルをそのまま載せると、新しい private symbol の import 自体で collection が失敗します。その機械的な赤を除き、「旧アルゴリズムを互換 API で呼べた場合」に欠陥を捕まえるかを判定しました。

| 新設テスト | 修正前での意味上の結果 | 判定 |
|---|---|---|
| `test_landed_diff_commands_pin_merge_and_root_contract` [97](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_git_state.py:97) | 旧 `commit-diff` は `-m` を含み、`tree-diff` がないため赤 | 構造変更を捕捉。元欠陥の受理挙動テストではない |
| `test_landed_interval_allows_main_fold_merge_from_trusted_cutoff` [422](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_git_state.py:422) | 旧全-parent検査は wave parent 側の FOLDED 変更を見て `landed-fold-owned-path`。`assert result.ok` が赤 | **元欠陥を実際に捕捉する唯一の正例** |
| `test_landed_interval_without_cutoff_keeps_all_parent_scan` [437](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_git_state.py:437) | 旧実装も全-parent検査して同じ detail で拒否。緑 | 旧欠陥を捕捉しない。scope外 consumer の回帰 pin |
| `...rejects_deleting_fragment_present_on_trusted_main` [451](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_git_state.py:451) | 旧全-parent検査も fragment D を拒否。緑 | 新しい exemption の安全性テストであり、旧欠陥 detector ではない |
| `...rejects_folded_resolution_on_trusted_main` [479](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_git_state.py:479) | 旧実装も FOLDED M を拒否。緑 | 同上 |
| `...without_trusted_parent...` [511](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_git_state.py:511) | 旧全-parent検査も拒否。緑 | 同上 |
| `test_octopus...` [539](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_git_state.py:539) | 旧全-parent検査も拒否。緑 | 同上 |
| `test_new_git_output_parsers...` [748](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_git_state.py:748) | 旧版には symbol がなく import/collection 赤 | 新機構の fail-closed pin。旧受理欠陥の detector ではない |

5本の「修正前でも緑」のテストは無価値ではありませんが、旧欠陥を赤にする根拠としては使えません。

成果物影響: これら5本を旧欠陥の検出証拠として扱うと mutation/acceptance 記録の意味が誤ります。製品の受理集合を直接変えないため、単独なら backlog です。

## 4. 波及と argv pin

実装報告の consumer 列挙には漏れがあります。

- checker 経由の schema-v2 fold consumer: [test_dev_waves_integration.py:492](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_integration.py:492)
- daemon recovery consumer: [test_dev_waves_integration.py:986](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_integration.py:986)
- fold-success を作る共有 fake fixture: [test_dev_waves_fake.py:237](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_fake.py:237)

いずれも非 merge/direct-child の成功経路であり、今回の merge exemption は制約しません。報告漏れ自体は consumer-closure 証拠を不完全にしますが、直ちに受理集合を変えないため backlog です。

`_commit_diff` の argv を pin するテストは、関連範囲では [test_dev_waves_git_state.py:78](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_git_state.py:78) と新設の97行だけです。既存テストは `{"-r", "-m", "-z"}` を許容集合としているだけで、`-m` の存在を必須化していません。

322行・396行の `diff-tree -m` は Git の対照出力を構築する直接呼び出しで、production argv pin ではありません。他の argv 固定テストへの波及は認めませんでした。

成果物影響: `_commit_diff` の `-m` 削除によって既存 argv-pin test の参照値が反転・緩和されることはありません。

## 5. 裁定との差

scope 逸脱の疑義は **refuted** です。

- 変更ファイルは `git_state.py`、`dev_wave_land.py`、専用テストの3本
- 署名2条件は変更されていません

```python
if status == "M" and paths[0] == "docs/spool/FOLDED.md":
    return True
deleted_path = paths[0] if status == "D" or status.startswith("R") else None
```

— [git_state.py:561](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:561)

- checker/daemon は cutoff を渡していません
- `receipt.py` と `schema.py` は無変更
- cutoff の receipt/schema 永続化もありません

したがって、裁定がユーザー判断へ戻した「署名2条件の不完全性」「checker/daemon の cutoff/schema」には手を出していません。ただし前述のとおり、共有 helper の subprocess 構成変更は cutoff を渡さない consumer にも運用上波及しています。

成果物影響: 裁定外の新しい署名受理や receipt field は導入されていません。

## 6. 事前登録変異8件

| # | old 逐語候補 | 一意性 / 先行拒否 / 赤理由 | 判定 |
|---|---|---|---|
| 1 | [git_state.py:689](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:689) `if _is_ancestor(...):` | 一意。先行拒否なし。ただし常時 True にすると2 parent とも trusted になり、`len(trusted) == 1` を満たさず全-parent fail-closed へ戻る | **不成立**。登録された「任意 parent を trusted にして削除負例が緑」は起きない |
| 2 | [git_state.py:696](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:696) `if len(trusted) == 1:` | 一意。`<= 1` 等で0件を通すと空 diff となり、no-trusted 負例だけが受理へ反転 | 成立 |
| 3 | [git_state.py:697](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:697) `diff_parents = trusted` | 一意。`trusted[:1]` で octopus の複数 trusted を単一化可能。先行拒否なし | 成立 |
| 4 | [git_state.py:685](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:685) `diff_parents = parents` | 一意。cutoffなしで空/単一 parent にすれば no-cutoff test が受理へ反転 | 成立 |
| 5 | [git_state.py:680](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:680) `if len(parents) < 2:` ～ `return _commit_diff(...)` | 一意。先行拒否なし。空 diff 化なら原因は非 merge scan の欠落に一本化 | 成立。ただし赤 node は N31、fragment D、rename、FOLDED M の4本を登録すべき |
| 6 | [git_state.py:701](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:701) `_tree_diff(repo_root, parent, commit_sha, ...)` | 一意。P/C 交換で fragment D が A となり、削除負例が受理へ反転。先行拒否なし | 成立 |
| 7 | 候補なし。現実の実装は [git_state.py:86](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:86) `("merge-base", "--is-ancestor")` | boolean 0/1 の ancestry 検査であり、複数 merge-base の出力や分岐が存在しない | **不成立**。置換対象がない |
| 8 | [git_state.py:696](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:696) `if len(trusted) == 1:` / 697 `diff_parents = trusted` | ブロックは一意。分岐を無効化すれば正例だけが従来の全-parent拒否へ戻る | 成立 |

### F3 — real / must-fix: 変異 #1 と #7 は現況に適合しない

#1 は注入自体はできますが、事前登録された反転理由が誤っています。#7 は対象コードが存在しません。このままでは8件を有効な mutation matrix として消化できません。

成果物影響: 修正しない場合、mutation 記録の kill 数・赤理由・対象参照が実装と一致せず、段6/7の検査証跡が偽になります。

## 総括

**NO-GO** — 静的レビューのみ。テスト実行・緑の主張はしていない。  
- 最重: land の2つの cutoff keyword を直接制約する consumer E2E がなく、配線退行が捕捉されない。  
- 次点: checker/daemon は意味上全-parentを維持するが、追加 subprocess と共有 deadline により完全同一挙動ではない。  
- 次点: 事前登録変異 #1 は想定反転が誤り、#7 は置換対象そのものが存在しない。  
既存テスト弱体化、N31 改変、署名条件・checker/daemon cutoff/schema への scope 逸脱は refuted。