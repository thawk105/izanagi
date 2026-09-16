## 実施した変更

新規作成は `patches/silo-backoff-fixed-v1.patch` の 1 ファイルのみ。

作成前に blob 型・対象未存在・symlink でないことを確認（rc=0）。指定の `noclobber` コマンドで書き出しました（rc=0）。既存ファイルの編集、ステージング、commit はしていません。

## 検証コマンドと出力

1. `sha256sum patches/silo-backoff-fixed-v1.patch` — rc=0

```text
35237d314df708c6a6cb6fece0a8a59cd199bb57337013f95f6ed50ea2a2f911  patches/silo-backoff-fixed-v1.patch
```

2. `git hash-object patches/silo-backoff-fixed-v1.patch` — rc=0

```text
f7a54445764025112317151106712bb9d97678ab
```

3. `git show f7a54445764025112317151106712bb9d97678ab | cmp - patches/silo-backoff-fixed-v1.patch` — rc=0、出力なし。

4. `sha256sum patches/silo-backoff-fixed.patch` — rc=0

```text
a5e0710c3f76744755b58ec66024c277daba00e49ce3cbf3d6d263cd7228580a  patches/silo-backoff-fixed.patch
```

5. `git status --porcelain --untracked-files=all` — rc=0

```text
?? patches/silo-backoff-fixed-v1.patch
```

## テスト

以下を直接実行しました（rc=0）。

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B -c 'import sys; sys.path.insert(0, "orchestrator/tests"); import test_p3_s4_loop as t; t.test_all_naked_izanagi_macro_patches_are_registered_or_allowlisted(); print("test_all_naked_izanagi_macro_patches_are_registered_or_allowlisted: PASS")'
```

出力：

```text
test_all_naked_izanagi_macro_patches_are_registered_or_allowlisted: PASS
```

pytest・焦点走・全体受入・変異検査は未実走です。指定された sandbox の dispatch 制約に従い、試行していません。

`test_source_and_test_are_the_only_non_output_worktree_changes` は未 commit の新ファイルにより赤となる予測です。実測ではありません。

## 波及の静的列挙

- `orchestrator/tests/test_ccbench_spawn_sites.py:632`：共有走査 helper が新 patch を読み、define 在庫・cross-product 検査へ波及します。新しい macro key は増えず、判定は変わらない予測です。
- `orchestrator/tests/test_p3_s4_loop.py:7842`：token 在庫検査の対象になります。該当関数の直接呼出しは PASS。
- `orchestrator/tests/test_p3_b4_wiring_probe.py:1521`：作業ツリー変更検査が新ファイルを検出し、未 commit 状態では赤となる予測です。
- `orchestrator/campaign/p3_s4_loop.py:128`：現行 patch の固定パスを参照するため、使用する patch は変わりません。
- `orchestrator/campaign/backoff_requested_us.py:1062`：上記固定パスから現行 patch を読むため、新ファイルへ切り替わりません。

## 総括

U1 の実装完了。指定の 5 検証はすべて期待どおりです。変更は新 patch 1 本のみ。直接呼出しの検査は PASS、pytest による受入は「実装済み・未実走」です。