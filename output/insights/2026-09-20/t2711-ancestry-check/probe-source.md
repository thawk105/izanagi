# 前提 probe の source (repo 外 `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2711-ancestry-check/probe/premise_classify_ancestry.py`、親が login で 1 回実走)

実走結果 (2026-09-20 07:1x JST):

```
known_axes AncestryResult(status='missing-commit', recorded='2066ce6b47c6a5d43ca2c8ab3cc7728d32336be1', observed=None, refusal_reason=None)
holdout AncestryResult(status='missing-commit', recorded='2e20d441aaf7ae267e941ecda09e4b53050943cf', observed=None, refusal_reason=None)
```

```python
"""段 1 前提の実測 (repo 外 probe、親が走らせる)。

hermetic な空 repo (init 直後 + 1 commit) に対し、M の _classify_ancestry が
記録 commit (実 repo の SHA) を「object 不在」として missing-commit / observed=None で
返すことを、production 関数そのものを呼んで確かめる。fixture 全体は作らない。
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

WORKTREE = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(WORKTREE))

from orchestrator.campaign import t080_freeze_migration as migration  # noqa: E402


def _env():
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update({
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_OPTIONAL_LOCKS": "0",
    })
    return env


def _vcs(root, *args):
    return subprocess.run(
        ["git", *args], cwd=root, check=True, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=_env(),
    ).stdout.strip()


with tempfile.TemporaryDirectory(prefix="t2711-premise-") as tmp:
    root = Path(tmp) / "repo"
    root.mkdir()
    _vcs(root, "init", "-q")
    _vcs(root, "config", "user.email", "probe@example.invalid")
    _vcs(root, "config", "user.name", "probe")
    (root / "a.txt").write_text("a\n")
    _vcs(root, "add", "a.txt")
    _vcs(root, "commit", "-q", "-m", "seed")
    head = _vcs(root, "rev-parse", "HEAD")
    for artifact, recorded in (
        ("known_axes", "2066ce6b47c6a5d43ca2c8ab3cc7728d32336be1"),
        ("holdout", "2e20d441aaf7ae267e941ecda09e4b53050943cf"),
    ):
        result = migration._classify_ancestry(recorded, head, root, artifact=artifact)
        print(artifact, result)
    print("constants", migration.KNOWN_AXES_RECORDED_HEAD, migration.HOLDOUT_RECORDED_HEAD)
    print("head", head)
```
