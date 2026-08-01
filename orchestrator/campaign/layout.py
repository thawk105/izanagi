# -*- coding: utf-8 -*-
"""出力レイアウト — campaign 軸 + env 軸の二分 (D13 / orchestrator-design.md)。

```
output/
  env/<env-tag>/{calibration,noise-floor}   ← 環境スコープ (campaign 横断・入力非依存)
  campaigns/<campaign-id>/
    campaign.lock    同一性の正準 pre-image (改竄不能な identity 源)
    spec/            凍結した入力 spec (レポート自己完結)
    runs/            この campaign の WAL (env-tag 必須)
    variants/        variant ソース/patch + ビルドキャッシュキー
    reports/         D12 材料レポートの射影先
    insights/        campaign 固有 insight / whiteboard
  insights/          グローバル知見 (CCBench 還元等, D6)
  whiteboard/        campaign 横断の教訓 (任意)
```

paths を一箇所に集約し、WAL/ビルドキャッシュ/lock がここだけを参照する。
**WAL を開く前に campaign-id が確定している前提** (orchestrator-design.md Phase1 反映 1)。
"""
from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Optional

from .durable_root import (
    DurableRootError,
    DurableRootPolicy,
    WriteCapability,
    resolve_policy_root,
)


def repo_output_root() -> str:
    """リポジトリ直下の output/ (orchestrator/campaign/layout.py からの相対)。

    layout.py = <repo>/orchestrator/campaign/layout.py → repo は dirname×2。"""
    here = os.path.dirname(os.path.abspath(__file__))     # <repo>/orchestrator/campaign
    repo = os.path.dirname(os.path.dirname(here))         # <repo>
    return os.path.join(repo, "output")


def default_durable_root_policy() -> DurableRootPolicy:
    """shared code の既定 durable allowlist。機械固有 path は注入側だけが持つ。"""
    root = Path(repo_output_root()).resolve(strict=True)
    return DurableRootPolicy(approved_roots=(root,), forbidden_roots=())


def authorize_output_root(
    output_root: str = "", *, policy: Optional[DurableRootPolicy] = None,
) -> WriteCapability:
    """未作成の output root を包含する approved root の capability を返す。

    directory 作成前の admission に使う。実際の file open 前には、作成済みの
    run/store directory を :func:`write_capability_for_directory` で再解決し、mount ID
    もその leaf まで再検査する。
    """
    policy = policy or default_durable_root_policy()
    if not isinstance(policy, DurableRootPolicy):
        raise DurableRootError("policy は DurableRootPolicy でなければならない")
    candidate = Path(output_root or repo_output_root())
    if not candidate.is_absolute():
        candidate = candidate.absolute()
    try:
        desired = candidate.resolve(strict=False)
        approved = tuple(root.resolve(strict=True) for root in policy.approved_roots)
    except OSError as exc:
        raise DurableRootError("output/approved root を解決できない") from exc
    matching = [root for root in approved if desired == root or desired.is_relative_to(root)]
    if not matching:
        raise DurableRootError("output_root が approved root 配下でない")
    root = max(matching, key=lambda item: len(item.parts))
    return resolve_policy_root(policy, str(root)).acquire_write_capability()


def ensure_directory_with_capability(
    capability: WriteCapability, directory: Path,
) -> Path:
    """capability root 配下だけに directory component を作る。symlink は辿らない。"""
    if not isinstance(capability, WriteCapability):
        raise DurableRootError("write capability が必要")
    target = Path(directory)
    if not target.is_absolute():
        target = target.absolute()
    try:
        relative = target.relative_to(capability.root)
    except ValueError as exc:
        raise DurableRootError("作成先 directory が capability root 外") from exc
    current = capability.root
    for part in relative.parts:
        current = current / part
        capability._verify_identity()
        try:
            os.mkdir(current, 0o700)
        except FileExistsError:
            if current.is_symlink() or not current.is_dir():
                raise DurableRootError(
                    f"directory component が通常 directory でない: {current}"
                )
        except OSError as exc:
            raise DurableRootError(f"directory を作成できない: {current}") from exc
    return target


def write_capability_for_directory(
    directory: Path, *, policy: Optional[DurableRootPolicy] = None,
) -> WriteCapability:
    """作成済み mutating entry root を policy/mount 検査して capability 化する。"""
    policy = policy or default_durable_root_policy()
    return resolve_policy_root(
        policy, str(Path(directory)),
    ).acquire_write_capability()


def open_with_write_capability(
    capability: WriteCapability, path: Path, mode: str,
) -> BinaryIO:
    """WriteCapability を必須化した binary open (append/create/truncate)。

    leaf capability の ``open_for_write`` は truncate 専用なので、append-only journal と
    create-only artifact が同じ admission/identity/O_NOFOLLOW 防壁を使えるよう mode を
    閉じた集合で補う。read-only entry はこの API を通さない。
    """
    if not isinstance(capability, WriteCapability):
        raise DurableRootError("write capability が必要")
    if mode not in {"ab", "xb", "wb"}:
        raise DurableRootError(f"未対応 write mode: {mode!r}")
    target = Path(path)
    if not target.is_absolute():
        target = target.absolute()
    try:
        relative = target.relative_to(capability.root)
        parent = (capability.root / relative.parent).resolve(strict=True)
    except (OSError, ValueError) as exc:
        raise DurableRootError("write target の親が capability root 外/未作成") from exc
    if not parent.is_relative_to(capability.root) or not parent.is_dir():
        raise DurableRootError("write target の親が capability root 外または directory でない")
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None:
        raise DurableRootError("O_NOFOLLOW が利用できない")
    flags = os.O_WRONLY | os.O_CREAT | nofollow
    if mode == "ab":
        flags |= os.O_APPEND
    elif mode == "xb":
        flags |= os.O_EXCL
    else:
        flags |= os.O_TRUNC
    capability._verify_identity()
    try:
        fd = os.open(parent / relative.name, flags, 0o600)
    except FileExistsError:
        raise
    except OSError as exc:
        raise DurableRootError(f"write target を安全に open できない: {target}") from exc
    try:
        return os.fdopen(fd, "wb" if mode == "xb" else mode)
    except Exception:
        os.close(fd)
        raise


@dataclass(frozen=True)
class CampaignLayout:
    """1 campaign のディレクトリ群。`ensure()` で作る。"""
    root: str                   # output/campaigns/<id>/

    @property
    def lock_file(self) -> str:
        return os.path.join(self.root, "campaign.lock")

    @property
    def spec_dir(self) -> str:
        return os.path.join(self.root, "spec")

    @property
    def runs_dir(self) -> str:
        return os.path.join(self.root, "runs")

    @property
    def wal_file(self) -> str:
        return os.path.join(self.runs_dir, "wal.jsonl")

    @property
    def variants_dir(self) -> str:
        return os.path.join(self.root, "variants")

    @property
    def reports_dir(self) -> str:
        return os.path.join(self.root, "reports")

    @property
    def insights_dir(self) -> str:
        return os.path.join(self.root, "insights")

    def ensure(self) -> "CampaignLayout":
        for d in (self.root, self.spec_dir, self.runs_dir, self.variants_dir,
                  self.reports_dir, self.insights_dir):
            os.makedirs(d, exist_ok=True)
        return self


def _campaign_slug(campaign_id: str) -> str:
    cid = str(campaign_id)
    # campaign-id は slug (人間入力由来) を含む。パス区切り/相対参照が混じると
    # namespace の外へ書き出しうる → 関所で弾く (path traversal 防御)。
    if (not cid or cid in (".", "..") or cid.startswith(".")
            or os.sep in cid or (os.altsep and os.altsep in cid)):
        raise ValueError(f"不正な campaign_id (パス区切り/相対参照を含む): {cid!r}")
    return cid


def campaign_layout(campaign_id: str, output_root: str = "") -> CampaignLayout:
    cid = _campaign_slug(campaign_id)
    root = output_root or repo_output_root()
    return CampaignLayout(root=os.path.join(root, "campaigns", cid))


_EXPLORATION_NAMESPACE_BYTES = b'{"namespace":"exploration"}\n'


def ensure_exploration_namespace(output_root: str = "") -> str:
    """``output_root`` 直下の exploration namespace marker を保証する。

    ``output_root`` 省略時は campaign 用の ``output/exploration`` を使う。
    8c journal のような別 root も同じ exact-bytes / symlink 拒否契約を共有する。
    返り値は marker の絶対 path。
    """
    root = Path(output_root or os.path.join(repo_output_root(), "exploration"))
    if not root.is_absolute():
        root = root.absolute()
    os.makedirs(root, exist_ok=True)
    marker = root / "namespace.json"
    if marker.is_symlink():
        raise ValueError("exploration namespace marker が symlink")
    temporary: Optional[Path] = None
    try:
        fd, temporary_name = tempfile.mkstemp(
            prefix=".namespace.", suffix=".tmp", dir=root,
        )
        temporary = Path(temporary_name)
        with os.fdopen(fd, "wb") as stream:
            stream.write(_EXPLORATION_NAMESPACE_BYTES)
            stream.flush()
            os.fsync(stream.fileno())
        # link(2) は既存の marker を上書きしない。temp の exact bytes を
        # atomic に公開し、親 directory の dirent を campaign tree より先に
        # durable 化する。
        os.link(temporary, marker)
        temporary.unlink()
        temporary = None
        dir_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        dir_fd = os.open(root, dir_flags)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    except FileExistsError:
        if marker.is_symlink():
            raise ValueError("exploration namespace marker が symlink")
        try:
            existing = marker.read_bytes()
        except OSError as exc:
            raise ValueError("exploration namespace marker を読めない") from exc
        if existing != _EXPLORATION_NAMESPACE_BYTES:
            raise ValueError("exploration namespace marker が exact contract と不一致")
    finally:
        if temporary is not None:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass
    return str(marker)


@dataclass(frozen=True)
class ExplorationCampaignLayout:
    """official CampaignLayout と継承関係を持たない探索専用 layout。"""
    root: str                   # output/exploration/campaigns/<id>/

    @property
    def lock_file(self) -> str:
        return os.path.join(self.root, "campaign.lock")

    @property
    def spec_dir(self) -> str:
        return os.path.join(self.root, "spec")

    @property
    def runs_dir(self) -> str:
        return os.path.join(self.root, "runs")

    @property
    def wal_file(self) -> str:
        return os.path.join(self.runs_dir, "wal.jsonl")

    @property
    def variants_dir(self) -> str:
        return os.path.join(self.root, "variants")

    @property
    def reports_dir(self) -> str:
        return os.path.join(self.root, "reports")

    @property
    def insights_dir(self) -> str:
        return os.path.join(self.root, "insights")

    @property
    def namespace_file(self) -> str:
        return os.path.join(os.path.dirname(os.path.dirname(self.root)), "namespace.json")

    def ensure(self) -> "ExplorationCampaignLayout":
        ensure_exploration_namespace(os.path.dirname(self.namespace_file))
        for d in (self.root, self.spec_dir, self.runs_dir, self.variants_dir,
                  self.reports_dir, self.insights_dir):
            os.makedirs(d, exist_ok=True)
        return self


def exploration_campaign_layout(
    campaign_id: str, output_root: str = "",
) -> ExplorationCampaignLayout:
    cid = _campaign_slug(campaign_id)
    root = output_root or repo_output_root()
    return ExplorationCampaignLayout(
        root=os.path.join(root, "exploration", "campaigns", cid),
    )


def env_scope_dir(env_tag: str, output_root: str = "") -> str:
    """環境スコープ (calibration/noise-floor の置き場、campaign 非依存)。"""
    root = output_root or repo_output_root()
    return os.path.join(root, "env", env_tag)
