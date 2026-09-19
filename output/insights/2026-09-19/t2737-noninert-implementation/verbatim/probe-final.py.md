"""One-shot real build probe; invoke only via tools/run_tests.py --force-dispatch.

The same-stem JSON sidecar supplies STOCK, THIRDPARTY, GFLAGS, GLOG as existing
absolute directories and OUTPUT as an existing absolute parent; each run gets a unique child.
Full old/new TU diffs are evidence for independent instrument-preservation review,
not an assertion that every diff is harmless. No benchmark is executed.
"""
import difflib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile

import pytest


def test_t2737_pristine_phase1_and_rejected_stock_arm():
    root = Path.cwd()
    spec = importlib.util.spec_from_file_location(
        "t2737_live_driver", root / "tools/pegasus/run_ss2pl_lock_study.py")
    driver = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(driver)
    inputs = json.loads(Path(__file__).with_suffix(".json").read_text())
    paths = {key: Path(inputs[key]) for key in
             ("STOCK", "THIRDPARTY", "GFLAGS", "GLOG", "OUTPUT")}
    assert all(path.is_absolute() for path in paths.values())
    out = Path(tempfile.mkdtemp(prefix="t2737-", dir=paths["OUTPUT"]))
    print(f"T2737 attempt output: {out}", flush=True)
    assert not (paths["THIRDPARTY"] / "masstree/config.h").exists()
    staging = out / "thirdparty"
    shutil.copytree(paths["THIRDPARTY"], staging, symlinks=True)
    assert not (staging / "masstree").is_symlink()
    stock, new, old = (out / name for name in ("stock", "new", "old"))
    for source in (stock, new, old):
        driver.clone_network_free(paths["STOCK"], source)
    old_patch = out / "old.patch"
    old_patch.write_text(driver._run_checked([
        "git", "show", "7975385b55a2e3451f6c80d584a9312f44d5199d:"
        "patches/ss2pl-lock-protocol-study.patch"], cwd=root, timeout=30).stdout)
    driver._apply_patch(old, old_patch, reverse=False)
    driver._apply_patch(new, root / "patches/ss2pl-lock-protocol-study.patch", reverse=False)
    kwargs = dict(backoff=1, gflags_prefix=paths["GFLAGS"],
                  glog_prefix=paths["GLOG"], thirdparty_root=staging)
    document = {"stage_deadlines": {}}
    with driver._stage_deadline(document, "build", 1800):
        record = driver.build_target(new, stock, out, build_id="phase1",
                                     arm="phase1", jobs=4, **kwargs)
        assert (staging / "masstree/config.h").is_file()
        gates = record["condition_gates"]
        assert [row["reason_code"] for row in gates[:4]] == [
            "requested-default-preprocess-different"] * 4
        assert [row["reason_code"] for row in gates[4:8]] == [
            "meaning-witness-undeclared"] * 4
        assert gates[8]["admitted"] is True
        with pytest.raises(driver.ContractError, match="condition gate rejected") as rejected:
            driver.build_target(new, stock, out, build_id="rejected-S",
                                arm="S", jobs=4, **kwargs)
        assert str(rejected.value).count("owner-tu-unresolved") == 3
        assert str(rejected.value).count("configure-failed") == 1
        driver._configure(old, out / "old-phase1", arm="phase1", **kwargs)
        target = "ycsb_ss2pl.exe"
        texts = {}
        for label, build in (("old", "old-phase1"), ("new", "phase1")):
            entries = driver._target_compile_entries(out / build, target)
            texts[label] = {}
            for entry in entries:
                name = Path(driver._entry_source(entry)).name
                text = driver._preprocess(entry).decode()
                texts[label][name] = text
                (out / f"{label}-{name}.ii").write_text(text)
        assert texts["old"].keys() == texts["new"].keys()
        assert set(texts["new"]) == {"transaction.cc", "util.cc", "wfg.cc", "ycsb_ss2pl.cc"}
        for name in texts["new"]:
            (out / f"{name}.diff").write_text("".join(difflib.unified_diff(
                texts["old"][name].splitlines(True), texts["new"][name].splitlines(True),
                fromfile=f"old-{name}", tofile=f"new-{name}")))
        plain = out / "plain-S"
        driver._configure(new, plain, arm="S", **kwargs)
        driver._run_checked(["cmake", "--build", str(plain), "--target", target,
                             "--parallel", "4"], timeout=600)
        record["plain_S_wfg_absence"] = driver._wfg_absence_evidence(
            driver._find_binary(plain, target), driver._target_compile_entries(plain, target))
        record["abort_ownership"] = driver.validate_abort_counter_ownership(new)
        record["study_declarations"] = driver._study_lock_header_declarations(new)
        for impl in (0, 1):
            driver._run_checked(["cmake", "-S", str(new), "-B", str(plain),
                                 "-DCCBENCH_BUILD_SS2PL_TESTS=ON",
                                 f"-DCCBENCH_SS2PL_LOCK_IMPL={impl}"], timeout=120)
            driver._run_checked(["cmake", "--build", str(plain), "--target",
                                 "sbomb_d2pl.exe", "bomb_ss2pl.exe", "tpcc_ss2pl.exe",
                                 "study_lock_test", "make_db_test", "--parallel", "4"], timeout=600)
            for target in ("study_lock_test", "make_db_test"):
                result = driver._run_checked([str(driver._find_binary(plain, target))], timeout=120)
                (out / f"{target}-impl{impl}.log").write_text(result.stdout + result.stderr)
    assert not (paths["THIRDPARTY"] / "masstree/config.h").exists()
    record.update(document)
    (out / "result.json").write_text(json.dumps(record, indent=2))
