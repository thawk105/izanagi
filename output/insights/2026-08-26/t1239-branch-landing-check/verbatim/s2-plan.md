# 実装プラン

## 判定モデル

3 値は維持する。

| verdict | 意味 | `decision.landed` | exit code |
|---|---|---:|---:|
| `landed` | branch の全変更について着地の十分な証拠がある | `true` | 0 |
| `not-landed` | 少なくとも 1 file に未着地の確定証拠がある | `false` | 1 |
| `indeterminate` | 未着地の確定証拠はないが、全 file の着地も証明できない | `null` | 2 |

CLI 構文不正は exit 64、`--help` は 0 とする。構文解析後の実行結果は、失敗を含め stdout に JSON 1 行だけを出す。

file verdict の合成は次の順序にする。

1. 1 file でも `not-landed` なら branch は `not-landed`。
2. `not-landed` がなく、1 file でも `indeterminate` なら branch は `indeterminate`。
3. 全 file が `landed`、または net tree diff が空なら `landed`。

ただし P2 の「全層を無条件に選言」は採用しない。spool fragment は receipt 専用、非 fragment は change type ごとの証明に分ける。

| change | `landed` の十分条件 | match 不在時 |
|---|---|---|
| spool fragment の追加・変更 | branch tip blob の SHA-256 が main tip の有効な `FOLDED.md` receipt にある | receipt を全件正常に読めたなら `not-landed` |
| spool fragment の削除 | この tool では fold identity を復元できない | `indeterminate` |
| regular text の追加・変更 | exact blob が main tipまたは merge-base 後の main 履歴にある、または後述の安全な逐語照合が成立 | closed-world の負証拠がある場合だけ `not-landed`、それ以外は `indeterminate` |
| regular binary | exact blob 証拠のみ | `indeterminate` |
| 削除 | main tip で不在、または merge-base 後に当該 path の削除が履歴にある | 履歴を打ち切らず全確認できた場合だけ `not-landed` |
| mode 変更 | branch が要求する mode が main tipまたは merge-base 後の path 履歴に現れる | 全確認できれば `not-landed` |
| gitlink・symlink・type 変更 | `(mode, object ID)` の完全一致が main tipまたは履歴にある | 全確認できれば `not-landed` |
| rename | `--no-renames` により削除と追加へ正規化し、両方を個別判定 | 片側だけの一致では `landed` にしない |

逐語層は、Git の numstat が「削除 0、追加 1 以上」と示す regular text に限定する。branch tip の全行列が main tip の同 path の行列に順序と重複数を保った subsequence として存在するときだけ `landed` 証拠にする。単なる `grep -qxF` は、既存の同一行や重複数不足で偽陽性になるので使わない。

`not-landed` にできる代表例は次のとおり。

- spool receipt が確実に存在しない。
- branch が追加した新規 text path が main の対象期間に一度も現れず、main tip にもない。
- main tip の当該 file が merge-base と byte・mode とも同じで、branch の純追加だけがなく、履歴探索も打ち切られていない。
- 削除、mode、gitlink の要求状態が完全な履歴探索に一度も現れない。

置換、生成物、削除を伴う text diff、巨大 file は、exact blob がなければ原則 `indeterminate` とする。これが originless baseline 型を誤って `not-landed` にしない境界になる。

## CLI 署名

`tools/check_branch_landed.py:540-630` に次を実装する。

```text
python3 tools/check_branch_landed.py BRANCH
    [--repo PATH]
    [--main MAIN]
    [--timeout-seconds FLOAT]
    [--max-files INT]
    [--history-candidates INT]
```

引数と既定値:

- `BRANCH`: 必須。`refs/heads/` 配下の local branch 名。
- `--repo PATH`: 既定は script の親の親、つまり repo root。
- `--main MAIN`: 既定 `main`。これも local branch 名だけを受ける。
- `--timeout-seconds FLOAT`: 全判定の monotonic deadline。既定 60 秒、許容 0 より大きく 300 以下。
- `--max-files INT`: net diff の最大 file 数。既定 256、許容 1〜4096。
- `--history-candidates INT`: 1 path の履歴候補上限。既定 64、許容 1〜1024。内部では `N+1` 件要求して打ち切りを検出する。

固定上限:

- 逐語照合用 blob: 1 blob 8 MiB。
- ledger hit 出力: 100 件。
- 1 回の履歴 Git command: 5 秒または全体残時間の短い方。

打ち切り、timeout、上限超過、parse 不能、shallow repository、replace ref、ref 移動はすべて `indeterminate` と exit 2 にする。`not-landed` へは倒さない。

## JSON schema

`tools/check_branch_landed.py:85-145,585-615` で dataclass から正準 JSON を生成する。`ensure_ascii=False`、`sort_keys=True`、compact separator、末尾 LF とする。

```json
{
  "schema": "izanagi-branch-landed-v1",
  "decision": {
    "verdict": "landed | not-landed | indeterminate",
    "landed": true,
    "conclusive": true
  },
  "repository": {
    "root": "/absolute/path"
  },
  "branch": {
    "name": "worktree-dev-wave-t1239-example",
    "tip": "40-hex-sha-or-null"
  },
  "main": {
    "name": "main",
    "tip": "40-hex-sha-or-null"
  },
  "merge_base": "40-hex-sha-or-null",
  "summary": {
    "changed_files": 1,
    "landed": 0,
    "not_landed": 0,
    "indeterminate": 1
  },
  "files": [
    {
      "path": "path/in/repo",
      "change": "A | M | D | T",
      "old_mode": "100644",
      "new_mode": "100644",
      "old_oid": "40-hex-or-all-zero",
      "new_oid": "40-hex-or-all-zero",
      "decision": {
        "verdict": "indeterminate",
        "landed": null,
        "conclusive": false
      },
      "evidence": [
        {
          "layer": "blob-history",
          "outcome": "matched | not-matched | not-applicable | indeterminate",
          "reason": "stable reason code",
          "commit": null,
          "content_sha256": null
        }
      ]
    }
  ],
  "auxiliary_evidence": {
    "patch_id": {
      "decisive": false,
      "status": "complete | indeterminate",
      "commits": [
        {
          "sha": "40-hex",
          "relation": "equivalent | unmatched",
          "subject": "commit subject"
        }
      ]
    },
    "task_index": {
      "decisive": false,
      "status": "complete | indeterminate",
      "task_ids": ["T-1239"],
      "hits": [
        {
          "task_id": "T-1239",
          "path": "docs/worklog.md",
          "line": 123
        }
      ],
      "truncated": false
    }
  },
  "limits": {
    "timeout_seconds": 60.0,
    "max_files": 256,
    "history_candidates": 64,
    "max_text_bytes": 8388608
  },
  "issues": [
    {
      "code": "history-timeout",
      "scope": "file",
      "path": "path/in/repo",
      "affects_verdict": true,
      "message": "short diagnostic"
    }
  ]
}
```

`decision.landed` を `true`、`false`、`null` に固定対応させることで、`not-landed` と `indeterminate` の取り違えを防ぐ。schema test ではこの対応を全 verdict について検査する。

## `tools/check_branch_landed.py` の file:line 計画

- `1-35`: shebang、D720 条件 1 だけを扱う docstring、imports、schema 名、exit code、全上限定数、spool path・task ID regex。
- `36-84`: `Decision`、`Issue`、`TreeEntry`、`ChangedPath`、`LayerEvidence`、`FileReport`、`BranchReport` dataclass。`Decision` constructor で verdict と `landed/conclusive` の不整合を禁止する。
- `85-145`: JSON 変換。optional 値も field 自体は省略せず、型を安定させる。
- `146-215`: monotonic deadline と読み取り専用 Git runner。`shell=False`、stdin `/dev/null`、raw bytes、許可 return code の明示、timeout の reason code 化。
- `216-260`: repo、main、branch の固定 SHA 解決、shallow・replace ref 拒否、単一 merge-base の取得。
- `261-325`: `diff-tree --raw -z` parser。mode、OID、status、UTF-8 path を厳密検証し、rename を D+A として受ける。
- `326-375`: FOLDED receipt の main-tip 読み取り、JSON bullet の厳密 parse、SHA-256 集合生成、spool file 判定。
- `376-455`: main tip tree entry、blob 履歴、mode・削除・gitlink 履歴の探索。候補上限と timeout を outcome に保存する。
- `456-515`: regular text の純追加判定、blob size・NUL 検査、行列 subsequence、closed-world の負判定。
- `516-539`: file verdict の branch への合成、ref 再取得による移動検出。
- `540-584`: `git cherry` と task ID 台帳検索。両者を `decisive:false` の補助証拠へ隔離する。
- `585-630`: parser、exit code mapping、JSON 1 行出力、既知例外の `indeterminate` 化、`main()`。
- `631-634`: `if __name__ == "__main__": raise SystemExit(main())`。

## Git command と既存関数の再利用

全自前 command には [git_state.py:37](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1239-branch-landing-check/tools/dev_waves/git_state.py:37) の `GIT_HARDENING_CONFIG` を再利用する。環境も同 file の `_git_env()` [git_state.py:164](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1239-branch-landing-check/tools/dev_waves/git_state.py:164) と同等にし、さらに `GIT_OPTIONAL_LOCKS=0` と `GIT_LITERAL_PATHSPECS=1` を加える。

branch SHA は公開関数 `branch_tip()` [git_state.py:1040](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1239-branch-landing-check/tools/dev_waves/git_state.py:1040) を、全体 deadline の残時間を渡して再利用する。

実行 command:

```text
git rev-parse --is-shallow-repository
git for-each-ref --format=%(refname) refs/replace
git merge-base --all <main_sha> <branch_sha>
git cherry -v <main_sha> <branch_sha>
git diff-tree -r --no-commit-id --raw -z --no-abbrev --no-renames \
    <merge_base> <branch_sha>
git ls-tree -z --full-tree <main_sha> -- <path>
git cat-file -s <blob_oid>
git cat-file blob <blob_oid>
git show <main_sha>:docs/spool/FOLDED.md
git log --full-history --format=%H --find-object=<new_oid> \
    --max-count=<N+1> <merge_base>..<main_sha> -- <path>
git log --full-history -m --format=%x1e%H --raw -z --no-abbrev \
    --no-renames --max-count=<N+1> <merge_base>..<main_sha> -- <path>
git diff --no-ext-diff --no-textconv --no-renames --numstat -z \
    <merge_base> <branch_sha> -- <path>
git grep -n -I -F -e T-<id> <main_sha> -- \
    docs/worklog.md docs/decisions.md docs/archive
```

履歴範囲を `merge_base..main_sha` に限定する。merge-base より前に同じ blob があっただけの revert branch を、着地済みと誤認しないためである。

再利用しないもの:

- `_run()` [git_state.py:178](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1239-branch-landing-check/tools/dev_waves/git_state.py:178) は private で、今回必要な `cherry`、`log --find-object`、raw diff、`grep` が allowlist にない。共有 allowlist を広げるより、新 tool 内を読み取り専用 command に限定する。
- `_is_ancestor()` と `_rev_list()` [git_state.py:603](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1239-branch-landing-check/tools/dev_waves/git_state.py:603) は private で、複数 merge-base や net tree diff を扱わない。
- `_tree_diff()` [git_state.py:714](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1239-branch-landing-check/tools/dev_waves/git_state.py:714) は name-status だけで mode・OID・gitlink を失うため不適切。
- `_pending_fragment_paths()` [git_state.py:907](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1239-branch-landing-check/tools/dev_waves/git_state.py:907) は 1 tree 全体の pending fragment 列挙であり、branch の変更 file と receipt hash の照合には使えない。
- `verify_declared_fold_commit()` [git_state.py:937](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1239-branch-landing-check/tools/dev_waves/git_state.py:937) は land 時の fold commit identity verifier であり、取り残し branch の content 判定とは責務が異なる。
- `spool_fold._receipt_records()` [spool_fold.py:1692](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1239-branch-landing-check/tools/spool_fold.py:1692) は private で、working tree の完全 schema 検査に結合している。新 tool は固定 main SHA の `FOLDED.md` から JSON bullet と `content_sha256` だけを厳密抽出する小さい parser を持つ。

## patch-id と補助台帳の扱い

`git cherry -v` の結果は全件 JSON に残すが verdict を動かさない。親実測の Git 2.34.1 には `git patch-id --verbatim` がなく、空白差を無視するためである。新 tool は存在しない `--verbatim` を呼ばず、`git cherry` の `-` を landed の十分条件にも、`+` を not-landed の十分条件にもしない。

branch 名から `t1239` 型を境界付きで抽出し、`T-1239` を worklog、decisions、archive から検索する。複数 ID はすべて検索する。hit、検索失敗、truncation は `auxiliary_evidence.task_index` にだけ入り、file・branch verdict には触れない。

## 計算量と打ち切り

changed file 数を `F`、各 path の対象期間の候補 commit 数を `H_i` とすると、通常は次になる。

- net diff、merge-base、`git cherry`: Git graph に対する各 1 回。
- main tip tree 照合: `O(F)` command。
- exact blob が main tip にない file だけ `--find-object`: 最大 `F` 回。
- mode、削除、gitlink の履歴照合: 該当 file だけ最大 1 回。
- text bytes 比較: 合計読み取り byte 数に線形。ただし各 blob 8 MiB で打ち切る。

親実測の `--find-object` は 1 file 1 秒未満だが、既定 60 秒の全体 deadline、1 command 5 秒、256 file、64 candidate を上限とする。残り時間がなくなった file は `history-budget-exhausted`、未処理 file は `global-timeout` として `indeterminate` にする。

`N+1` candidate が返った場合、最初の `N` 内に正の一致があれば採用できる。一致がなく `N+1` 件目があれば探索不足なので `indeterminate` とし、`not-landed` にはしない。

## テストの file:line 計画

新設 `orchestrator/tests/test_check_branch_landed.py` は全ケースで `tmp_path` 内に合成 Git repo を作る。

- `1-35`: imports、tool の importlib load、定数。
- `36-115`: `_git()`、`_init_repo()`、branch 作成、text/binary 書込み、commit、chmod、gitlink、FOLDED receipt 作成 helper。
- `116-165`: tool 呼出し、stdout JSON parse、schema と exit code の共通 assertion。
- `166-235`: patch `-` だが未 fold fragment を含むケース。
- `236-280`: patch `+` だが receipt fold 済みのケース。
- `281-330`: patch `+` だが main tip exact blob のケース。
- `331-375`: originless baseline 型の `indeterminate`。
- `376-405`: 真に未着地の純追加 file。
- `406-475`: landed へ倒れすぎない負の対照。
- `476-555`: 削除、rename、mode、gitlink、binary。
- `556-625`: timeout、候補上限、malformed FOLDED、shallow、replace ref、複数・不在 merge-base、ref 移動。
- `626-670`: task ID evidence が verdict を動かさないこと、JSON schema、全 exit code。
- `671-676`: `_run()` が `pytest.main(["-q", __file__])` を呼ぶ self-run harness。

必須の 5 合成ケース:

1. rulings-20260818-floor-measurement 型
   branch の 1 commit で spool fragment を 2 本追加する。main に同一 patch commit を作って `git cherry` を `-` にした後、両 fragment を削除し、片方だけ FOLDED receipt に記録する。1 file が `landed`、もう 1 file が `not-landed`、branch は `not-landed`。

2. t1458-side-ccbench-provenance-fix 型
   branch は fragment を追加するが、main は fragment commit を持たず receipt だけを持つ。`git cherry` は `+`、file と branch は `landed`。

3. workload-policy-hint 型
   branch は 1 commit で 2 行追加する。main は 2 commit に分けて同じ最終 blob を作り、branch commit と同じ patch-id を持たせない。`git cherry` は `+`、main tip blob で `landed`。

4. originless baseline 型
   base の巨大 1 行を branch と main が別々の巨大 1 行へ置換する。blob 不一致、branch の追加行も main tip にないが削除を伴うため逐語層は非適用。`indeterminate` と `landed:null` を要求する。

5. 真に未着地
   branch が新規 text file を追加し、main は merge-base のままにする。全履歴探索が完了し path も blob もないので `not-landed`。

負の対照は最低でも次を入れる。

- base/main に同じ行が 1 個あり、branch が同じ行をもう 1 個追加する。単純な `grep -qxF` なら誤って landed になるが、重複数不足により `not-landed`。
- branch は旧行を削除して新行へ置換し、main は旧行を残したまま同じ新行を別位置へ追加する。追加行の存在だけでは landed にせず `indeterminate`。
- main 履歴に spool fragment blob が一度存在しても receipt がないケース。blob 層が spool receipt 不在を上書きしない。
- 空白だけ異なる main/branch patch が `git cherry -` になっても、exact blob 不一致なら `landed` にしない。
- 同じ path・同じ行数だが内容が異なる file を `landed` にしない。

構造別 test:

- 削除が main 履歴にもある正例と、main に残る負例。
- rename を D+A として両側一致させる正例、追加側だけ一致する負例。
- 同一 blob でも 100644 と 100755 を区別する mode test。
- `git update-index --cacheinfo 160000,...` で作る gitlink の exact OID 正例と異なる OID 負例。
- NUL を含む binary は exact blob なら landed、別 blobなら indeterminate。
- 65 件以上の候補を小さい test 上限で再現し、打ち切りが `not-landed` にならないこと。
- malformed receipt、Git timeout、branch/main ref の再取得不一致が必ず exit 2 になること。

## 既存テストへの波及

新しい `test_check_branch_landed.py` は [test_plain_runner_coverage.py:44](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1239-branch-landing-check/orchestrator/tests/test_plain_runner_coverage.py:44) が列挙する `test_*.py` 集合に入る。同メタテストは [test_plain_runner_coverage.py:60](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1239-branch-landing-check/orchestrator/tests/test_plain_runner_coverage.py:60) で self-run harness または allowlist 登録を要求する。

計画では末尾に `pytest.main` を使う self-run harness を置くため、`_HARNESS_SIGNALS` [test_plain_runner_coverage.py:25](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1239-branch-landing-check/orchestrator/tests/test_plain_runner_coverage.py:25) を満たす。したがって `orchestrator/tests/README.md:129-184` の allowlist 追記は不要であり、追記すると逆に stale/self-runnable test により失敗する。

[test_pytest_collection_config.py:423](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1239-branch-landing-check/orchestrator/tests/test_pytest_collection_config.py:423) にも `test_*.py` の glob があるが、これは `verifier` / `oracle` 名の恒久除外だけを検査しており、新しい file 数の固定値は持たない。追随変更は不要。その他に `orchestrator/tests/` 直下の file 数を固定するメタテストは静的検索では見つからなかった。

## repo 規律との整合

- shallow repository、replace ref、複数 merge-base、非 UTF-8 path、Git output parse 不能、timeout、履歴打ち切りはすべて `indeterminate`。
- `git patch-id --verbatim` は呼ばない。Git 2.34.1 の `git cherry` は補助証拠に限定する。
- path 一致、行数一致、追加行が 1 回見つかったことだけでは landed にしない。
- branch、worktree、index、refs は一切変更しない。固定 SHA の object database だけを読む。
- 判定開始時と終了時に main/branch tip を再取得し、移動していれば固定 SHA で結果を得ていても `indeterminate` にする。
- D720 条件 2 の妥当性監査は JSON schema にも verdict logic にも入れない。

## 総括

プランの核は、3 値判定、file 単位判定、branch 単位連言を維持しつつ、spool・regular text・binary・削除・mode・gitlink を同じ選言へ押し込まないことである。`not-landed` は receipt 不在や完全な履歴探索などの closed-world 証拠がある場合だけ返し、証明力の足りない置換・生成物は `indeterminate` に残す。

親の P1 には同意する。originless baseline 型を `not-landed` から隔離するため 3 値が必要である。P2 は branch 単位連言には同意するが、file 単位の無条件選言には反対する。特に spool は receipt が正本であり、blob 履歴で代用できない。また追加行の単純な存在確認は、削除未反映や重複数不足を見落とす。P3 には同意する。task ID hit はその task の記録であって、この branch の bytes の着地証明ではない。

規模は `tools/check_branch_landed.py` が約 600 行、合成 repo test が約 650 行で、純増はおおむね `10^3` 行の桁を見込む。既存 production file の変更は不要である。

残る不確実性は、D720 の「main 履歴」を全史ではなく `merge_base..main` と解釈する点、生成物や意味保存変換を byte 比較では判定できない点、巨大 text・binary の非一致を安全に未着地へ倒せない点である。これらは偽陽性を避けるため `indeterminate` として明示的に残す。