"""F10 live-root transport; synthetic compiler output, real metadata validation."""
from pathlib import Path
import json
import sys

import pytest

from orchestrator.campaign import buildcache
from orchestrator.campaign.model import Genome
from orchestrator.tests import test_buildcache_v2 as fixtures


@pytest.mark.parametrize("external", [False, True])
def test_f10_build_result_carries_observed_masstree_root(tmp_path, monkeypatch, external):
    fixtures._install_toolchain(tmp_path, monkeypatch)
    source = tmp_path / "ccbench"
    source.mkdir()
    header = source / "compiler-input.hh"
    header.write_bytes(b"snapshot header\n")
    dependency = tmp_path / "supplied" / "masstree-src"
    dependency.mkdir(parents=True)
    external_header = dependency / "fixture.hh"
    external_header.write_bytes(b"actual masstree header\n")
    events = fixtures._install_real_compiler_input_build_without_masstree_resolution(
        monkeypatch, tmp_path, input_path=external_header if external else header,
    )
    run_compiler = buildcache._run

    def run(cmd, what, **kwargs):
        run_compiler(cmd, what, **kwargs)
        if what == "configure" and external:
            staging = Path(cmd[cmd.index("-B") + 1])
            with (staging / "CMakeCache.txt").open("a") as cache:
                cache.write(f"FETCHCONTENT_SOURCE_DIR_MASSTREE:PATH={dependency}\n")
            fixtures._write_masstree_depend_info(staging, ((
                dependency / "config.h", dependency / "libkohler_masstree_json.a",
            ),))

    monkeypatch.setattr(buildcache, "_run", run)
    genome = Genome("silo", {"BACK_OFF": 1})
    context, evidence, admission = fixtures._admission_bundle(genome, "a" * 40, str(source))
    result = buildcache._build_v2_impl(
        genome, admission=admission, build_context=context, source_evidence=evidence,
        source_snapshot_sha256=buildcache.s8b_expected_materialization.snapshot_tree_digest(source),
        allow_external_compiler_inputs=external, expected_evolve_block_sources=None,
        contract=fixtures._contract(1), ccbench_commit="a" * 40, trace=False,
        src_token="stock", cc="test-cc", cxx="test-cxx",
        cache_root=str(tmp_path / "cache"), ccbench_dir=str(source),
    )
    assert events == ["configure", "build"]
    assert isinstance(result, buildcache.BuildResult)
    assert result.compiler_input_masstree_root == (str(dependency) if external else "")
    assert result.compiler_input_manifest["inputs"][0].get("root", "snapshot") == (
        "fetchcontent-masstree" if external else "snapshot"
    )
    completion = (Path(result.build_dir) / buildcache._V2_COMPLETION_MANIFEST).read_text()
    assert "compiler_input_masstree_root" not in json.loads(completion)
    assert str(dependency) not in completion


def test_f10_legacy_build_result_defaults_to_empty_root():
    result = buildcache.BuildResult(Genome("silo", {}), False, "/binary", "a" * 64, "/build", False)
    assert result.compiler_input_masstree_root == ""


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
