#!/usr/bin/env bash
# Codex は PreToolUse command の rc=2 だけを拒否として扱う。guard 本体の
# 欠落・起動失敗・例外を rc=1/127 のまま返すと fail-open になるため、0/2 以外は
# すべて拒否へ正規化する。

kind=${1-}
case "$kind" in
  write)
    guard="${BASH_SOURCE[0]%/*}/guard_write.py"
    ;;
  bash)
    guard="${BASH_SOURCE[0]%/*}/guard_bash.py"
    ;;
  *)
    exit 2
    ;;
esac

if [[ ! -f "$guard" ]] || ! command -v python3 >/dev/null 2>&1; then
  exit 2
fi

python3 "$guard"
rc=$?
case "$rc" in
  0|2)
    exit "$rc"
    ;;
  *)
    exit 2
    ;;
esac
