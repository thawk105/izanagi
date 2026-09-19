# author-u1.patch (逐語)

Codex author (gpt-6-astra, medium) の実装差分 = commit 4208bf332 (base 8fd1eecf9)。所有 path 限定。

```diff
diff --git a/orchestrator/tests/t1259_scan_bound.py b/orchestrator/tests/t1259_scan_bound.py
new file mode 100644
index 000000000..3a119bbec
--- /dev/null
+++ b/orchestrator/tests/t1259_scan_bound.py
@@ -0,0 +1,13 @@
+"""D2148 項 12 / F945: production の 30.0 は不変、この候補値は受入 fixture の module snapshot 1 回分にだけ効く。"""
+from pathlib import Path
+from typing import Any
+
+from tools.pegasus.probes import t1259_qsub_env_delivery_probe as probe
+
+FIXTURE_GIT_TIMEOUT_SECONDS: float = 120.0
+
+
+def fixture_repo_snapshot(repo_root: Path) -> dict[str, Any]:
+    return probe._repo_snapshot(
+        repo_root, git_timeout_seconds=FIXTURE_GIT_TIMEOUT_SECONDS
+    )
diff --git a/orchestrator/tests/test_t1259_qsub_env_delivery_probe.py b/orchestrator/tests/test_t1259_qsub_env_delivery_probe.py
index bdd36f58e..3410307b3 100644
--- a/orchestrator/tests/test_t1259_qsub_env_delivery_probe.py
+++ b/orchestrator/tests/test_t1259_qsub_env_delivery_probe.py
@@ -11,6 +11,7 @@ from pathlib import Path

 import pytest

+from orchestrator.tests import t1259_scan_bound
 from tools.pegasus.probes import t1259_qsub_env_delivery_probe as probe


@@ -73,7 +74,7 @@ EXECUTING_PBS_SHA256 = _sha256(REPO_ROOT / PBS_PATH)
 @pytest.fixture(scope="module")
 def _clean_detached_source_snapshot_template() -> dict[str, object]:
     """Capture the real submit-tree identity once, before modelling cleanliness."""
-    snapshot = probe._repo_snapshot(REPO_ROOT)
+    snapshot = t1259_scan_bound.fixture_repo_snapshot(REPO_ROOT)
     snapshot["detached"] = True
     snapshot["tracked_status"] = ""
     snapshot["untracked_paths"] = []
diff --git a/orchestrator/tests/test_t1259_scan_bound.py b/orchestrator/tests/test_t1259_scan_bound.py
new file mode 100644
index 000000000..1ae31d1c8
--- /dev/null
+++ b/orchestrator/tests/test_t1259_scan_bound.py
@@ -0,0 +1,100 @@
+"""Exercise fixture scan bounds using real Git operations in temporary repositories."""
+from __future__ import annotations
+
+import subprocess
+import sys
+from pathlib import Path
+
+import pytest
+
+if __package__ in (None, ""):
+    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
+
+from orchestrator.tests import t1259_scan_bound
+from tools.pegasus.probes import t1259_qsub_env_delivery_probe as probe
+
+
+def _temporary_repo(tmp_path: Path) -> tuple[Path, str]:
+    root = tmp_path / "repo"
+    root.mkdir()
+    subprocess.run(["git", "init", str(root)], check=True, capture_output=True)
+    for relative in (
+        probe.PROBE_RELATIVE_PATH, probe.PBS_RELATIVE_PATH, probe.CAMPAIGN_RELATIVE_PATH
+    ):
+        source = root / relative
+        source.parent.mkdir(parents=True, exist_ok=True)
+        source.write_text(f"temporary source: {relative}\n", encoding="utf-8")
+    subprocess.run(["git", "-C", str(root), "add", "."], check=True, capture_output=True)
+    subprocess.run(
+        ["git", "-C", str(root), "-c", "user.name=Scan Test",
+         "-c", "user.email=scan@example.invalid", "commit", "-m", "initial"],
+        check=True, capture_output=True,
+    )
+    head = subprocess.run(
+        ["git", "-C", str(root), "rev-parse", "HEAD"],
+        check=True, capture_output=True, text=True,
+    ).stdout.strip()
+    (root / "untracked.txt").write_text("untracked\n", encoding="utf-8")
+    return root, head
+
+
+def _spy(monkeypatch: pytest.MonkeyPatch) -> list[dict]:
+    calls: list[dict] = []
+    real_run = subprocess.run
+
+    def run(*args, **kwargs):
+        calls.append(dict(kwargs))
+        return real_run(*args, **kwargs)
+
+    monkeypatch.setattr(probe.subprocess, "run", run)
+    return calls
+
+
+def test_production_snapshot_keeps_thirty_second_bound(tmp_path, monkeypatch):
+    root, head = _temporary_repo(tmp_path)
+    calls = _spy(monkeypatch)
+    snapshot = probe._repo_snapshot(root)
+    assert len(calls) == 4
+    assert all(call["timeout"] == 30.0 for call in calls)
+    assert snapshot["head"] == head
+    assert "untracked.txt" in snapshot["untracked_paths"]
+
+
+def test_fixture_snapshot_uses_local_candidate_bound(tmp_path, monkeypatch):
+    assert t1259_scan_bound.FIXTURE_GIT_TIMEOUT_SECONDS == 120.0
+    root, head = _temporary_repo(tmp_path)
+    production = probe._repo_snapshot(root)
+    calls = _spy(monkeypatch)
+    snapshot = t1259_scan_bound.fixture_repo_snapshot(root)
+    assert len(calls) == 4
+    assert all(
+        call["timeout"] == t1259_scan_bound.FIXTURE_GIT_TIMEOUT_SECONDS
+        and call["timeout"] != 30.0 for call in calls
+    )
+    assert snapshot.keys() == production.keys()
+    assert snapshot["head"] == production["head"] == head
+    assert snapshot == production
+
+
+def test_fixture_snapshot_propagates_timeout(tmp_path, monkeypatch):
+    root, _ = _temporary_repo(tmp_path)
+    failure = subprocess.TimeoutExpired(
+        cmd=["git", "-C", str(root), "rev-parse", "--verify", "HEAD"],
+        timeout=t1259_scan_bound.FIXTURE_GIT_TIMEOUT_SECONDS,
+    )
+
+    def timeout(*args, **kwargs):
+        raise failure
+
+    monkeypatch.setattr(probe.subprocess, "run", timeout)
+    with pytest.raises(subprocess.TimeoutExpired) as caught:
+        t1259_scan_bound.fixture_repo_snapshot(root)
+    assert caught.value is failure
+
+
+def _run():
+    return pytest.main([__file__])
+
+
+if __name__ == "__main__":
+    raise SystemExit(_run())
diff --git a/tools/pegasus/probes/t1259_qsub_env_delivery_probe.py b/tools/pegasus/probes/t1259_qsub_env_delivery_probe.py
index b2d9861ce..356c4de83 100755
--- a/tools/pegasus/probes/t1259_qsub_env_delivery_probe.py
+++ b/tools/pegasus/probes/t1259_qsub_env_delivery_probe.py
@@ -130,7 +130,9 @@ def _strict_object(raw: bytes, *, source: Path) -> dict[str, Any]:
     return document


-def _run_git(repo_root: Path, *args: str) -> str:
+def _run_git(
+    repo_root: Path, *args: str, git_timeout_seconds: float = 30.0
+) -> str:
     environment = dict(os.environ)
     environment["GIT_OPTIONAL_LOCKS"] = "0"
     completed = subprocess.run(
@@ -139,12 +141,14 @@ def _run_git(repo_root: Path, *args: str) -> str:
         capture_output=True,
         text=True,
         env=environment,
-        timeout=30.0,
+        timeout=git_timeout_seconds,
     )
     return completed.stdout


-def _repo_is_detached(repo_root: Path) -> bool:
+def _repo_is_detached(
+    repo_root: Path, *, git_timeout_seconds: float = 30.0
+) -> bool:
     environment = dict(os.environ)
     environment["GIT_OPTIONAL_LOCKS"] = "0"
     completed = subprocess.run(
@@ -153,15 +157,20 @@ def _repo_is_detached(repo_root: Path) -> bool:
         capture_output=True,
         text=True,
         env=environment,
-        timeout=30.0,
+        timeout=git_timeout_seconds,
     )
     if completed.returncode not in (0, 1):
         raise ProbeError("cannot determine whether repository HEAD is detached")
     return completed.returncode == 1


-def _repo_snapshot(repo_root: Path) -> dict[str, Any]:
-    head = _run_git(repo_root, "rev-parse", "--verify", "HEAD").strip()
+def _repo_snapshot(
+    repo_root: Path, *, git_timeout_seconds: float = 30.0
+) -> dict[str, Any]:
+    head = _run_git(
+        repo_root, "rev-parse", "--verify", "HEAD",
+        git_timeout_seconds=git_timeout_seconds,
+    ).strip()
     if HEX40_RE.fullmatch(head) is None:
         raise ProbeError("repository HEAD is not an exact lowercase 40-hex commit")
     tracked = _run_git(
@@ -170,6 +179,7 @@ def _repo_snapshot(repo_root: Path) -> dict[str, Any]:
         "--porcelain=v1",
         "--untracked-files=no",
         "--ignore-submodules=none",
+        git_timeout_seconds=git_timeout_seconds,
     )
     untracked_raw = _run_git(
         repo_root,
@@ -177,10 +187,13 @@ def _repo_snapshot(repo_root: Path) -> dict[str, Any]:
         "--others",
         "--exclude-standard",
         "-z",
+        git_timeout_seconds=git_timeout_seconds,
     )
     return {
         "head": head,
-        "detached": _repo_is_detached(repo_root),
+        "detached": _repo_is_detached(
+            repo_root, git_timeout_seconds=git_timeout_seconds
+        ),
         "tracked_status": tracked,
         "untracked_paths": sorted(path for path in untracked_raw.split("\0") if path),
         "source_sha256": {

```
