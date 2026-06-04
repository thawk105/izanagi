#!/usr/bin/env bash
# devcontainer 作成後に実行されるセットアップ。
set -eu

# CCBench submodule が既に追加されていれば、正確な依存リストを読んで追加インストール
DEPS_FILE="external/ccbench/build_tools/ubuntu.deps"
if [ -f "$DEPS_FILE" ]; then
  echo "[post-create] installing CCBench deps from $DEPS_FILE"
  sudo apt-get update -y
  # shellcheck disable=SC2046
  sudo apt-get install -y $(cat "$DEPS_FILE")
else
  echo "[post-create] $DEPS_FILE not found (submodule 未追加)。Phase 1 タスク0 で追加後、コンテナをリビルドするか本スクリプトを再実行すること。"
fi

# orchestrator 用 Python 環境 (依存が増えたら requirements.txt に固める)
python3 -m venv .venv 2>/dev/null || true
echo "[post-create] done"
