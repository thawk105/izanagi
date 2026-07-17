#!/usr/bin/env bash
# strip_claude_session_trailers.sh — 全履歴の commit message から `Claude-Session:` trailer を除去する
#
# 何をするか:
#   0. preflight: このスクリプトが属する checkout に「リモート未反映で Claude-Session を含む
#      commit」が残っていないか検査する (残っていれば中止 — 書き換え後に push すると復活するため)
#   1. リポジトリを新規 clone する (filter-repo は使い込んだ clone での実行を拒否するため)
#   2. git filter-repo の message-callback で、全 commit message から
#      `Claude-Session:` で始まる行だけを削除する。tree / 差分 / 作者情報には一切触れない
#   3. 「残存 0 件」「commit 総数 不変」を検証して停止する — push はしない
#
# push (リモート履歴の実際の上書き。不可逆) はこのスクリプトの外で、検証結果を目視
# 確認したうえで手動で行う。成功時に末尾へ表示されるコマンドを使う。
#
# 前提:
#   - git-filter-repo (`pip install --user git-filter-repo` または `pipx install git-filter-repo`)
#   - 全ローカル作業 (全マシン・全 worktree) が push / merge 済みであること。preflight は
#     このマシンのこの checkout しか見ない — 他マシン (Pegasus 等) は手で確認する
#   - GitHub 側で main が protected (force-push 禁止) なら一時的に解除しておく。保護されたまま
#     push すると main だけ拒否され、他ブランチだけ書き換わる中途半端な状態になる
#
# 使い方:
#   bash tools/strip_claude_session_trailers.sh /path/to/workdir
#
# push 後の後始末:
#   - このマシンの checkout / 各 worktree: git fetch origin && git reset --hard origin/<branch>
#     (完全に消したい場合は clone し直すか、reflog expire + gc。reset だけでは旧 commit が
#      reflog 経由で ~90 日残る)
#   - 他マシンの clone (Pegasus 等の計測環境) も同様に fetch + reset、または clone し直し
#   - 万一 未 push の trailer 付き commit を持つブランチが後から見つかった場合、
#     rebase --onto では message が複製され trailer が復活する。そのブランチも filter-repo に
#     かけるか、cherry-pick 後に message を手で直すこと
#   - この書き換えで消えないもの (別途対応):
#       * GitHub の PR / issue 本文・コメント内のセッション URL (`gh pr list` で確認し
#         `gh pr edit` で編集する。PR 本文にはセッション URL が自動付与されていた可能性がある)
#       * GitHub が refs/pull/* 経由で保持する旧 commit (force-push でも残り、SHA 直打ちで
#         到達できる。private repo なので閲覧者は限定的。完全消去は GitHub Support に依頼)
#   - submodule (external/ccbench) は別リポジトリで今回の対象外 (gitlink は書き換えで不変)
set -euo pipefail

REPO_URL="${IZANAGI_REPO_URL:-git@github.com:thawk105/izanagi.git}"
CLONE_DIR_NAME="izanagi-rewrite"

if [ $# -ne 1 ]; then
    echo "usage: $0 <workdir>" >&2
    exit 2
fi
WORKDIR=$1

if ! command -v git-filter-repo >/dev/null 2>&1; then
    echo "error: git-filter-repo が見つからない (pip install --user git-filter-repo)" >&2
    exit 1
fi

# preflight: この checkout のローカルブランチに、リモート未反映かつ trailer 付きの commit が
# あれば中止する。書き換え後にそれを push / merge すると trailer がリモートへ復活する
SCRIPT_REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
if git -C "$SCRIPT_REPO" rev-parse --git-dir >/dev/null 2>&1; then
    unpushed=$(git -C "$SCRIPT_REPO" log --branches --not --remotes --format=%h \
        --grep='Claude-Session:' | wc -l)
    if [ "$unpushed" -ne 0 ]; then
        echo "error: リモート未反映で Claude-Session を含む commit が ${unpushed} 件ある:" >&2
        git -C "$SCRIPT_REPO" log --branches --not --remotes --oneline \
            --grep='Claude-Session:' >&2
        echo "先に push / merge してから再実行する (rebase では trailer は消えない)" >&2
        exit 1
    fi
fi

mkdir -p "$WORKDIR"
CLONE_DIR="$WORKDIR/$CLONE_DIR_NAME"
if [ -e "$CLONE_DIR" ]; then
    echo "error: $CLONE_DIR が既に存在する。前回の残骸なら削除してから再実行する" >&2
    exit 1
fi

# --no-local: ローカルパスからの clone でもネットワーク clone と同じ経路にし、
# filter-repo の fresh-clone 判定を安定させる (SSH URL では無視される)
git clone --no-local "$REPO_URL" "$CLONE_DIR"
cd "$CLONE_DIR"

before_hits=$(git log --all --oneline --grep='Claude-Session:' | wc -l)
before_commits=$(git rev-list --all --count)
echo "== before: Claude-Session を含む commit ${before_hits} 件 / 総 commit ${before_commits} 件 =="

# message のみ書き換える。fresh clone では filter-repo が refs/remotes/origin/* を
# refs/heads/* に付け替えて全ブランチを書き換え対象にし、origin remote を取り外す。
git filter-repo --message-callback '
import re
return re.sub(rb"(?m)^Claude-Session:[^\n]*\n?", b"", message)
'

# after 側は実害基準で数える: セッション URL (claude.ai/code) または行頭の trailer 形式が
# 1 件でも残れば fail-closed で止める。件名・本文でこの対応自体に言及するプロース
# (例: 「Claude-Session trailer を停止」という commit 件名) は無害なので許す
after_hits=$(git log --all --oneline -E --grep='claude\.ai/code|^Claude-Session:' | wc -l)
after_commits=$(git rev-list --all --count)
echo "== after: Claude-Session を含む commit ${after_hits} 件 / 総 commit ${after_commits} 件 =="

if [ "$after_hits" -ne 0 ]; then
    echo "error: 除去しきれていない (${after_hits} 件残存)。push しないこと" >&2
    exit 1
fi
if [ "$after_commits" -ne "$before_commits" ]; then
    echo "error: commit 総数が変わった (${before_commits} -> ${after_commits})。push しないこと" >&2
    exit 1
fi

echo
echo "検証 OK。message の目視確認: cd $CLONE_DIR && git log --format='%h %s%n%b' | less"
echo "旧→新 SHA 対応表: $CLONE_DIR/.git/filter-repo/commit-map"
echo
echo "リモート履歴を上書きするには (不可逆・要最終確認。main の branch protection は事前に解除):"
echo "  cd $CLONE_DIR"
echo "  git remote add origin $REPO_URL"
echo "  git push --force --all origin"
echo "  git push --force --tags origin"
echo "  git ls-remote origin   # 全ブランチが新 SHA になったことを確認する"
