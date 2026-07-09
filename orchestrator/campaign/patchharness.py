# -*- coding: utf-8 -*-
"""apply/revert ハーネス — patch を 1 variant 評価の間だけ working-tree に適用する駆動部。

phase3.md 機構節「適用の隔離」の実装: patch は submodule working-tree への out-of-band
適用 (HEAD は pin 不動 → campaign-id 不変) で、**1 variant 評価ごとに
clean→apply→build→revert** する。歴代の patch 適用は手動だった (= 記述のみで駆動部が
無い) のを、fails-closed の assert 込みで機械化する (phase3.md blocking タスク)。

順序の固定 (タスク定義): **apply → resolve(src_token) → build → revert**。
resolve より後に tree を動かさない = revert は必ず build (+ buildcache の TOCTOU 再照合)
の後。この順序は `applied()` context manager の形状で担保する — apply は enter、revert は
exit で、resolve/build/verify/bench は body の中で行う。

fails-closed (規律2/6):
- apply 前: working-tree が **pinned-clean** (HEAD == pin かつ tracked 改変ゼロ) で
  あることを assert。汚れた tree への適用は「どの variant を評価しているか」の identity を
  壊す (別セッションの残骸・前 variant の revert 漏れとの合成 patch になる)。
- revert 後: tracked 改変ゼロ + patch が作った新規ファイルの残骸ゼロを assert。
  revert 漏れは**次の** variant の評価を汚染する (偽 cache hit の温床) ため、検出したら
  自動修復を試みず停止して人間に出す (規律6: 素性の知れない状態を沈黙して進めない)。
- untracked (`??`) のうち patch 由来でないもの (build-variants 等のビルド生成物) は無視
  する — source_digest.assert_worktree_within_allowlist と同じ規則。

`checkout()` (段5 git worktree 隔離): `applied()` は共有 tree 1本 + flock 直列化だが、
`checkout()` は 1 variant 専用の使い捨て git worktree を作る。呼び出しごとに一意パスなので
他の並行評価と競合しない。`with checkout(pin) as sub: with applied(patch, pin, sub): ...`
と組み合わせて使う (責務は分離: worktree の生成/破棄と patch の apply/revert は別関数)。
"""
from __future__ import annotations

import contextlib
import fcntl
import hashlib
import os
import shutil
import subprocess
import tempfile
from typing import List


def _git(sub: str, *args: str) -> subprocess.CompletedProcess:
    """submodule で git を回す。起動不能は RuntimeError (identity 核なので fails-closed)。

    `-c core.quotepath=false` を常に渡し、非 ASCII パスの C-style quote (`"include/\\346..."`)
    を抑止する — patch_files/_tracked_changes が出力パスを生で FS 操作に使うため、quote された
    文字列だと残骸削除と leftovers 検査が両方素通りする (2026-07-03 敵対検証 low)。制御文字は
    quotepath=false でも quote されうるが、coder の非 ASCII/制御文字ファイル名追加は #include
    死角 assert (include 行 HEAD 固定) と EVOLVE-BLOCK 制約で手前で止まる。"""
    try:
        return subprocess.run(["git", "-C", sub, "-c", "core.quotepath=false", *args],
                              capture_output=True, text=True)
    except (OSError, subprocess.SubprocessError) as e:
        raise RuntimeError(
            f"patchharness: git 起動失敗 ({e}) — working-tree の状態を確定できず "
            "fails-closed で停止") from e


def _lock_path(sub: str) -> str:
    """submodule working-tree の apply 排他 lock ファイルパス (tree を汚さぬよう TMPDIR に)。"""
    h = hashlib.sha256(os.path.realpath(sub).encode("utf-8")).hexdigest()[:16]
    d = os.environ.get("TMPDIR", "/tmp")
    return os.path.join(d, f"izanagi_apply_{h}.lock")


@contextlib.contextmanager
def _tree_lock(sub: str):
    """submodule working-tree の apply→build→revert 区間を直列化する flock。

    working-tree は全セッション共有の単一資源。apply→(他セッションの build がこの汚染 tree を
    読む)→revert の ABA は TOCTOU 再照合 (両端一致) では原理的に見えない (2026-07-03 敵対検証
    high)。区間全体を排他して single tree の並走 apply/build を防ぐ = 段 5 の git worktree 隔離
    (並列化) までの最小防壁 (phase3.md)。規律4 の計測直列とも整合する。"""
    fd = os.open(_lock_path(sub), os.O_CREAT | os.O_RDWR, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def _tracked_changes(sub: str) -> List[str]:
    """tracked な改変 (porcelain の非 ?? 行) のパス一覧。untracked は無視。"""
    r = _git(sub, "status", "--porcelain")
    if r.returncode != 0:
        raise RuntimeError(
            f"patchharness: git status 失敗 (rc={r.returncode}) → fails-closed。\n"
            f"  {r.stderr.strip()[-300:]}")
    out = []
    for line in r.stdout.splitlines():
        if not line.strip() or line[:2] == "??":
            continue
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ")[-1]
        out.append(path.strip())
    return out


def patch_files(patch_path: str, sub: str) -> List[str]:
    """patch が touch するファイル一覧 (`git apply --numstat` — 適用はしない)。"""
    r = _git(sub, "apply", "--numstat", patch_path)
    if r.returncode != 0:
        raise RuntimeError(
            f"patchharness: patch を読めない ({patch_path}, rc={r.returncode}) → "
            f"fails-closed。\n  {r.stderr.strip()[-300:]}")
    files = []
    for line in r.stdout.splitlines():
        cols = line.split("\t")
        if len(cols) == 3 and cols[2]:
            files.append(cols[2])
    if not files:
        raise RuntimeError(
            f"patchharness: patch が 1 ファイルも touch しない ({patch_path}) — "
            "空 patch の評価は identity を汚すだけなので停止")
    return files


def assert_pinned_clean(sub: str, pin_commit: str) -> None:
    """working-tree が pinned-clean (HEAD==pin かつ tracked 改変ゼロ) を assert (fails-closed)。"""
    if not pin_commit:
        raise RuntimeError("patchharness: pin_commit が空 — pin 照合なしで patch を"
                           "当てない (campaign-id 不変の前提が崩れる)")
    if len(pin_commit) < 7:
        # startswith 照合は短い pin ほど衝突確率が上がる (1 文字なら 1/16)。git の短縮 SHA
        # 慣行 (7 桁) 未満は弱照合として拒否 — 呼び手の切り詰めミスで関所を形骸化させない
        # (2026-07-03 敵対検証 low)。
        raise RuntimeError(
            f"patchharness: pin_commit が短すぎる ({pin_commit!r}, 7 桁未満) — startswith "
            "照合が形骸化するため拒否 (別版の tree に誤って patch を当てないための下限)")
    r = _git(sub, "rev-parse", "HEAD")
    head = r.stdout.strip()
    if r.returncode != 0 or not head:
        raise RuntimeError(
            f"patchharness: HEAD を確定できない (rc={r.returncode}) → fails-closed。\n"
            f"  {r.stderr.strip()[-300:]}")
    if not head.startswith(pin_commit):
        raise RuntimeError(
            f"patchharness: HEAD ({head[:12]}) が pin ({pin_commit}) と不一致 — "
            "別版の tree に patch を当てない (fails-closed)")
    dirty = _tracked_changes(sub)
    if dirty:
        raise RuntimeError(
            "patchharness: working-tree が clean でない (tracked 改変あり) — 前 variant の "
            f"revert 漏れ / 別セッションの残骸を疑え。汚れた tree に patch を重ねない "
            f"(fails-closed): {sorted(dirty)}")


def apply_patch(patch_path: str, sub: str) -> None:
    """patch を working-tree に適用する (index は触らない = HEAD/pin 不動)。"""
    r = _git(sub, "apply", patch_path)
    if r.returncode != 0:
        raise RuntimeError(
            f"patchharness: git apply 失敗 ({patch_path}, rc={r.returncode})。\n"
            f"  {r.stderr.strip()[-500:]}")


def revert_worktree(sub: str, files: List[str]) -> None:
    """patch 適用を巻き戻し、戻り切ったことを assert する (fails-closed)。

    tracked 改変は `git checkout -- .` で HEAD へ戻す。patch が**新規作成**したファイルは
    checkout では消えない (untracked に残る = 次 variant の評価を汚染) ので、patch の
    touch 集合のうち HEAD に無いものを明示削除する。最後に tracked-clean + 残骸ゼロを
    assert し、破れていたら停止 (自動修復で上書きしない、規律6)。"""
    r = _git(sub, "checkout", "--", ".")
    if r.returncode != 0:
        raise RuntimeError(
            f"patchharness: revert (git checkout -- .) 失敗 (rc={r.returncode}) — "
            f"working-tree が汚染されたまま。人間が復旧すること。\n"
            f"  {r.stderr.strip()[-300:]}")
    for rel in files:
        exists_in_head = _git(sub, "cat-file", "-e", f"HEAD:{rel}").returncode == 0
        p = os.path.join(sub, rel)
        if not exists_in_head and os.path.lexists(p):
            os.unlink(p)                         # patch が新規作成 → untracked 残骸を除去
    dirty = _tracked_changes(sub)
    if dirty:
        raise RuntimeError(
            "patchharness: revert 後も tracked 改変が残る — 次 variant の評価を汚染する"
            f"ため停止 (人間が復旧すること): {sorted(dirty)}")
    leftovers = [rel for rel in files if os.path.lexists(os.path.join(sub, rel))
                 and _git(sub, "cat-file", "-e", f"HEAD:{rel}").returncode != 0]
    if leftovers:
        raise RuntimeError(
            f"patchharness: revert 後も patch 由来の新規ファイルが残る: {leftovers} — "
            "停止 (人間が復旧すること)")


@contextlib.contextmanager
def applied(patch_path: str, pin_commit: str, ccbench_dir: str = ""):
    """`with applied(patch, pin): resolve→build→verify→bench` の駆動部。

    enter = pinned-clean assert + apply、exit = revert + clean assert。body 内で
    source_digest.resolve → buildcache.build を行うこと (順序固定: resolve より後に
    tree を動かさない = revert は必ず build + TOCTOU 再照合の後)。body の例外時も
    revert は走る (finally) — revert 自体の失敗は body の例外を握り潰さず両方表に出す。
    """
    sub = ccbench_dir or _default_ccbench_dir()
    with _tree_lock(sub):                     # apply→build→revert 全区間を直列化 (ABA 防止)
        assert_pinned_clean(sub, pin_commit)  # check-then-act を排他内に (lock 取得後に照合)
        files = patch_files(patch_path, sub)
        apply_patch(patch_path, sub)
        try:
            yield files
        finally:
            revert_worktree(sub, files)


def _default_ccbench_dir() -> str:
    here = os.path.dirname(os.path.abspath(__file__))     # <repo>/orchestrator/campaign
    repo = os.path.dirname(os.path.dirname(here))         # <repo>
    return os.path.join(repo, "external", "ccbench")


def _worktree_paths(base: str) -> List[str]:
    """base repo に登録済みの worktree 絶対パス一覧 (`git worktree list --porcelain`)。

    leak 検出 (checkout() の破棄後に base の worktree 一覧へ残っていないか) にのみ使う。"""
    r = _git(base, "worktree", "list", "--porcelain")
    if r.returncode != 0:
        raise RuntimeError(
            f"patchharness: git worktree list 失敗 (rc={r.returncode}) → fails-closed。\n"
            f"  {r.stderr.strip()[-300:]}")
    prefix = "worktree "
    return [ln[len(prefix):].strip() for ln in r.stdout.splitlines() if ln.startswith(prefix)]


@contextlib.contextmanager
def checkout(pin_commit: str, base_dir: str = ""):
    """1 variant 評価専用の使い捨て git worktree を pin_commit で作り、exit で破棄する
    (段5 git worktree 隔離、phase3.md 後続段5)。patch は当てない (骨格/hole 適用は
    呼び手が返り値の path を `applied()` に渡して組み合わせる — 責務の分離)。

    `applied()` (共有 tree + flock 直列化) と違い、worktree は呼び出しごとに一意パスなので
    他の並行評価と原理的に競合しない — 共有 tree の HEAD を誰かが動かす、という C1 残課題の
    前提そのものが起きなくなる (並行合成時の id 安定化)。`git worktree add <path> <pin>` は
    base repo の checkout 状態に依存せず任意の既存 commit を独立 checkout できるため、
    base 側の pinned-clean を要求しない。

    exit で worktree ごと使い捨てるため、内側で `applied()` を使っても `revert_worktree` の
    untracked 残骸検査 (「porcelain 空」より弱い既知の限界、残存リスク節) の限界はこの経路
    では実害が無い — tree ごと消えるので残骸が次 variant に持ち越されることがない。"""
    base = base_dir or _default_ccbench_dir()
    parent = tempfile.mkdtemp(prefix="izanagi_wt_", dir=os.environ.get("TMPDIR", "/tmp"))
    path = os.path.join(parent, "wt")     # git worktree add は対象パス非存在を要求 → 親だけ予約
    r = _git(base, "worktree", "add", "--detach", path, pin_commit)
    if r.returncode != 0:
        shutil.rmtree(parent, ignore_errors=True)
        raise RuntimeError(
            f"patchharness: git worktree add 失敗 (pin={pin_commit}, rc={r.returncode}) → "
            f"fails-closed。\n  {r.stderr.strip()[-500:]}")
    try:
        assert_pinned_clean(path, pin_commit)   # 防御的 (worktree は必ず真だが既存契約と揃える)
        yield path
    finally:
        r2 = _git(base, "worktree", "remove", "--force", path)
        if r2.returncode != 0:
            _git(base, "worktree", "prune")
            shutil.rmtree(path, ignore_errors=True)
        shutil.rmtree(parent, ignore_errors=True)
        remaining = {os.path.realpath(p) for p in _worktree_paths(base)}
        if os.path.realpath(path) in remaining:
            raise RuntimeError(
                f"patchharness: worktree 破棄後も base repo の一覧に残る ({path}) — leak を "
                "疑え。手動で `git worktree remove --force` して復旧すること (fails-closed、規律6)")
