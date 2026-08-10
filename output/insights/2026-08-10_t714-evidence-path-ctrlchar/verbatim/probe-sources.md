# 実測 probe の逐語 (段 1 v1 / 段 4 v2)

実行可能資材として repo へ置かないため、逐語を markdown で凍結する。実行時の cwd は wave worktree、v1 は blob の長さだけを比べており (F29 再発の証跡)、v2 は blob OID / sha256 で同一性を測る。

## v1 — 段 1 (長さ比較。誤った測定対象)

```python
"""[T-714] 段 1: 裁定前提の実測 (read-only、production 無改変)。

1. read_blob_at が末尾 CR 付き path を CR 無し path へ alias するか
2. _safe_path が CR / LF を受理するか
3. LF を含む path が read_blob_at で何を返すか
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve()
REPO = Path("/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t714-evidence-path-ctrlchar")
sys.path.insert(0, str(REPO / "orchestrator"))

from campaign import s8c_preregistration as core  # noqa: E402
from campaign import s8c_preregistration_evidence as ev  # noqa: E402

head = core.resolve_commit(REPO, "HEAD")
print("commit:", head)

for label, path in (
    ("plain", "CLAUDE.md"),
    ("trailing-CR", "CLAUDE.md\r"),
    ("trailing-LF", "CLAUDE.md\n"),
    ("embedded-LF", "CLAUDE.md\nREADME.md"),
    ("leading-CR", "\rCLAUDE.md"),
):
    try:
        raw = core.read_blob_at(REPO, head, path, required=False)
        got = f"bytes={len(raw)}" if raw is not None else "None(missing)"
    except Exception as exc:  # noqa: BLE001
        got = f"{type(exc).__name__}: {getattr(exc, 'reason', exc)}"
    print(f"read_blob_at[{label}] {path!r} -> {got}")

for label, path in (
    ("plain", "CLAUDE.md"),
    ("trailing-CR", "CLAUDE.md\r"),
    ("trailing-LF", "CLAUDE.md\n"),
    ("embedded-LF", "a\nb.md"),
    ("tab", "a\tb.md"),
    ("NUL", "a\x00b.md"),
):
    try:
        out = ev._safe_path(path, where="probe")
        got = f"accepted {out!r}"
    except Exception as exc:  # noqa: BLE001
        got = f"{type(exc).__name__}: {getattr(exc, 'reason', exc)}"
    print(f"_safe_path[{label}] {path!r} -> {got}")
```

## v2 — 段 4 (blob OID / sha256 比較)

```python
"""[T-714] 段 4: 裏取り probe v2 (read-only、production 無改変)。

段 3 レンズ A の 2 所見を親が独立に裏取りする。
- #4: 「同一 blob」を長さではなく blob OID / sha256 で測る。
- #1: NUL 付き path が prefix の blob へ alias するか。
"""
import hashlib
import subprocess
import sys
from pathlib import Path

REPO = Path("/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t714-evidence-path-ctrlchar")
sys.path.insert(0, str(REPO / "orchestrator"))

from campaign import s8c_preregistration as core  # noqa: E402
from campaign import s8c_preregistration_evidence as ev  # noqa: E402

head = core.resolve_commit(REPO, "HEAD")
print("commit:", head)


def batch_check(path: str) -> str:
    out = subprocess.run(
        ["git", "cat-file", "--batch-check"],
        cwd=REPO,
        input=f"{head}:{path}\n".encode(),
        capture_output=True,
    )
    return out.stdout.decode("utf-8", "replace").strip().replace("\n", " | ")


for label, path in (
    ("plain", "CLAUDE.md"),
    ("trailing-CR", "CLAUDE.md\r"),
    ("NUL-suffix", "CLAUDE.md\x00not-the-contract-path"),
    ("NUL-only-tail", "CLAUDE.md\x00"),
    ("tab-suffix", "CLAUDE.md\t"),
):
    raw = core.read_blob_at(REPO, head, path, required=False)
    digest = hashlib.sha256(raw).hexdigest() if raw is not None else None
    print(f"read_blob_at[{label}] {path!r} -> sha256={digest}")
    print(f"  batch-check -> {batch_check(path)}")

for label, path in (
    ("NUL-suffix", "CLAUDE.md\x00not-the-contract-path"),
    ("dot-slash", "./CLAUDE.md"),
):
    try:
        out = ev._safe_path(path, where="probe")
        got = f"accepted {out!r}"
    except Exception as exc:  # noqa: BLE001
        got = f"{type(exc).__name__}: {getattr(exc, 'reason_code', exc)}"
    print(f"_safe_path[{label}] {path!r} -> {got}")

# 非文字列 bypass (レンズ A #3)
try:
    raw = core.read_blob_at(REPO, head, Path("CLAUDE.md"), required=False)  # type: ignore[arg-type]
    print("read_blob_at[Path-obj] ->", hashlib.sha256(raw).hexdigest() if raw else None)
except Exception as exc:  # noqa: BLE001
    print("read_blob_at[Path-obj] ->", type(exc).__name__, exc)
```
