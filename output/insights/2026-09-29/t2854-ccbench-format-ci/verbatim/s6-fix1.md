## 変更内容

[run_ci_build.sh](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2854-fmt-a/output/runs/t2854-fmt-ci/scripts/run_ci_build.sh) だけを変更しました。3 依存を cache から `git clone --no-local` で scratch に取り出し、pin OID を detached checkout します。HEAD の一致、detached 状態、`git status --porcelain --ignored` が空であることを確認し、失敗時は build 前に rc=2 で停止します。report の HEAD・tree 記録を残し、取り出し方法を追加しました。cache は変更していません。

## 実走した command と rc

- `bash -n run_ci_build.sh`: rc=0
- Pegasus ログインノードでの入口実行: rc=2（bnode 必須）
- masstree cache から `/tmp` への `git clone -q --no-local` と pin の detached checkout: 各 rc=0
- clone の HEAD は pin と一致。`git status --porcelain --ignored` は rc=0・出力なし。`config.h` と `libkohler_masstree_json.a` の不在確認は各 rc=0。一時 clone は削除済みです。

## 未実走・残る懸念

計算ノードでの CI image build は**実装済み・未実走**です。

## 総括

S6-1 の clean な依存供給と build 前の照合を実装しました。ログインノードで許された範囲の確認は通過しています。