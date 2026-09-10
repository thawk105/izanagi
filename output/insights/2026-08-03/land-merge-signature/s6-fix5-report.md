実装を完了しました。指定された 2 ファイルのみ変更し、docs 編集・commit はしていません。

変更箇所:

- [_landed_commit_diff](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/tools/dev_waves/git_state.py:695)
- [追加テスト群](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-merge-signature/orchestrator/tests/test_dev_waves_git_state.py:429)

### 変更後の分岐

```text
if parent 数 < 2:
    commit 全体との差分
else if cutoff is None:
    全 parent との差分
else:
    T = cutoff の祖先である parent

    if |T| == parent 数:
        線形走査で極大候補を選ぶ
        全 parent が候補の祖先なら:
            候補との差分だけ
        else:
            全 parent との差分
    else if |T| == 1:
        その trusted parent との差分だけ
    else:
        全 parent との差分
```

untrusted parent が含まれる場合は、従来どおり trusted が 1 個のときだけ単一 parent を選び、それ以外は全 parent 走査です。

### 新設テスト nodeid

- `orchestrator/tests/test_dev_waves_git_state.py::test_all_trusted_chain_accepts_main_fold_merge_without_wave_commit`
- `orchestrator/tests/test_dev_waves_git_state.py::test_all_trusted_chain_rejects_fragment_deleted_by_merge_resolution`
- `orchestrator/tests/test_dev_waves_git_state.py::test_all_trusted_incomparable_maxima_keep_all_parent_scan`

既存テストの本文・期待値は変更していません。

### `_is_ancestor` 呼び出し数

parent 数を `p` とすると:

- `p < 2` または cutoff 未指定: `0`
- cutoff 指定、全 trusted でない場合: `p`
- 全 parent trusted: trusted 判定 `p` + 候補走査最大 `p-1` + 検証最大 `p-1`
- 合計上限: `3p - 2`

結果は `(before, after)` 単位でキャッシュするため、重複比較は再実行しません。計算量は `O(p)` です。

### 実測例が受理される根拠

`4c176743...` では:

1. `ea6ca43...` と `e805d69...` はともに cutoff `1a3604b...` の祖先なので全 parent trusted。
2. `_is_ancestor(ea6ca43..., e805d69...)` が真なので候補は `e805d69...` になる。
3. 全 parent が候補の祖先であるため、一意な極大元として確定する。
4. 走査対象は `diff-tree e805d69... 4c176743...` のみ。
5. この差分は静的実測で空でした。fragment ディレクトリにも README 以外は存在しません。

したがって main 由来の fold 署名を古い parent との差分から拾わず、merge 解決自体に署名がなければ受理されます。

### 検査状況

- `python3 -m py_compile ...`: 成功
- `git diff --check`: 成功
- pytest: **未実走**
- 試行コマンド: `python3 tools/run_tests.py orchestrator/tests/test_dev_waves_git_state.py -q`
- 理由: Pegasus dispatch が `qstat -Q preflight rc=1`、直接確認でも socket 作成不能。`rc=16` でテスト開始前に停止しました。

影響する所有外 caller は land CLI の cutoff 指定経路です。checker/daemon は cutoff を渡さないため、受理集合は従来どおりです。共有 fixture は `_repo`、`_seed_pending`、`_fold_commit` を再利用しています。

## 総括

全 parent trusted の場合だけ一意な極大 parent を選ぶ規則を実装した。  
untrusted 混在、cutoff 未指定、単一 parent の挙動は維持した。  
極大判定は `O(p)`、呼び出し上限は `3p-2`。  
指定された正例 1 本・負例 2 本を追加した。  
既存テストの期待値、docs、scope 外 consumer は変更していない。  
静的検査は成功、pytest は dispatch 障害により未実走。