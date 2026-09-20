#!/usr/bin/env python3
"""T-2304 disposable shape probe: <repo_root> <build_dir> <out_json>."""
import hashlib
import json
from pathlib import Path
import re
import sys


repo_root, build_dir, out_json = sys.argv[1:]
sys.path.insert(0, repo_root)
result = {
    "schema": "t2304-shape-probe/v1",
    "build_dir": build_dir,
    "checks": {},
    "cmake_cache_lines": [],
    "depend_info_pairs_block": [],
    "sha256": {},
}


def failure(exc):
    causes = []
    cause = exc.__cause__
    while cause is not None:
        causes.append({"type": type(cause).__name__, "message": str(cause)})
        cause = cause.__cause__
    return {"ok": False, "type": type(exc).__name__,
            "message": str(exc), "causes": causes}


try:
    from orchestrator.campaign import buildcache
except Exception as exc:
    for key, marker in (("disconnected", "DISCONNECTED"),
                        ("masstree_root", "MASSTREE_ROOT")):
        result["checks"][key] = failure(exc)
        print(marker + "_FAILED")
else:
    for key, marker, check in (
        ("disconnected", "DISCONNECTED",
         buildcache._assert_fetchcontent_fully_disconnected_effective),
        ("masstree_root", "MASSTREE_ROOT",
         buildcache._masstree_source_root_from_cmake_cache),
    ):
        try:
            value = check(build_dir)
        except Exception as exc:
            result["checks"][key] = failure(exc)
            print(marker + "_FAILED")
        else:
            result["checks"][key] = {"ok": True, "value": value}
            print(marker + "_OK" + (" " + str(value) if value is not None else ""))

for relative in ("CMakeCache.txt", "CMakeFiles/masstree_build.dir/DependInfo.cmake"):
    try:
        raw = (Path(build_dir) / relative).read_bytes()
        result["sha256"][relative] = hashlib.sha256(raw).hexdigest()
        text = raw.decode("utf-8")
        if relative == "CMakeCache.txt":
            result["cmake_cache_lines"] = [
                line for line in text.splitlines(keepends=True)
                if re.match(r"^(CMAKE_GENERATOR|FETCHCONTENT_SOURCE_DIR_MASSTREE|"
                            r"FETCHCONTENT_BASE_DIR)(?::[^=\r\n]*)?=", line)
            ]
        else:
            result["depend_info_pairs_block"] = re.findall(
                r"(?m)^[ \t]*set\([ \t]*CMAKE_MULTIPLE_OUTPUT_PAIRS[ \t]*\r?\n"
                r"[\s\S]*?^[ \t]*\)[ \t]*(?:#[^\r\n]*)?(?:\r?\n|$)", text,
            )
    except (OSError, UnicodeError) as exc:
        result["sha256"].setdefault(relative, None)
        result.setdefault("read_errors", {})[relative] = failure(exc)

Path(out_json).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8")
sys.exit(0 if all(check["ok"] for check in result["checks"].values()) else 3)
