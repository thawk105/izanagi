"""Fixed source amendments for the registered A1 pilot and sized studies."""
from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path

from . import buildcache, patchharness, s8b_expected_materialization, s8b_floor_campaign

PILOT_STUDY_ID = "paper-story-a1-20260901-balanced5-pilot-v1"
SIZED_STUDY_ID = "paper-story-a1-20260901-balanced5-sized-v1"

CONTRACT_PATH = "orchestrator/campaign/paper_story_a1_source.v1.json"
CONTRACT_SHA256 = "21477b74ad440f9eed8c27f78417f0469d757cb2bea2f579b2b212632b69f4b7"
SOURCE_PATHS = (
    CONTRACT_PATH,
    "orchestrator/campaign/paper_story_a1_source.py",
    "patches/silo-backoff-fixed.patch",
    "output/insights/2026-09-11/t2397-a1-source-amendment/README.md",
)


SIZED_CONTRACT_PATH = "orchestrator/campaign/paper_story_a1_source.v2.json"
SIZED_CONTRACT_SHA256 = "b50a4edf86250033aa0e2b18efa2d7842d7c90025fdb901011fdad7adf052fe1"
SIZED_SOURCE_PATHS = (
    SIZED_CONTRACT_PATH,
    "orchestrator/campaign/paper_story_a1_source.py",
    "patches/silo-backoff-fixed.patch",
    "output/insights/2026-09-17/t2590-a1-sized-source-amendment/README.md",
)
CONTRACTS = {
    PILOT_STUDY_ID: (CONTRACT_PATH, CONTRACT_SHA256, SOURCE_PATHS),
    SIZED_STUDY_ID: (SIZED_CONTRACT_PATH, SIZED_CONTRACT_SHA256, SIZED_SOURCE_PATHS),
}


def load_contract(repo_root: Path, study_id=PILOT_STUDY_ID) -> dict:
    contract_path, contract_sha256, _ = CONTRACTS[study_id]
    raw = (repo_root / contract_path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != contract_sha256:
        raise RuntimeError("A1 source amendment bytes differ")
    contract = json.loads(raw)
    for key in ("patch", "policy", "preregistration", "amendment"):
        if hashlib.sha256((repo_root / contract[key]).read_bytes()).hexdigest() != contract[key + "_sha256"]:
            raise RuntimeError(f"A1 source {key} bytes differ")
    return contract


def binding_matches(files: dict, *, study_id=PILOT_STUDY_ID) -> bool:
    contract = load_contract(Path(__file__).resolve().parents[2], study_id)
    contract_path, contract_sha256, _ = CONTRACTS[study_id]
    expected = {contract_path: contract_sha256,
                contract["patch"]: contract["patch_sha256"],
                contract["amendment"]: contract["amendment_sha256"]}
    return all(files.get(path, {}).get("working_sha256") == digest
               for path, digest in expected.items())


@dataclass(frozen=True, init=False)
class SourceContext:
    """Issued by materialized(); callers cannot supply an expected digest."""

    def __init__(self, repo_root: Path, base: Path, root: Path, *, study_id=PILOT_STUDY_ID):
        contract = load_contract(repo_root, study_id)
        patch = repo_root / contract["patch"]
        pin = contract["canonical_head"]
        patchharness.assert_pinned_clean(os.fspath(base), pin)
        expected = s8b_expected_materialization.produce_expected_materialization_sha256(
            ccbench_commit=pin, configuration=(
                "a1-attempt-0004" if study_id == PILOT_STUDY_ID else "a1-balanced5-sized-v1"
            ),
            base_dir=base, template_patch=patch,
        )
        object.__setattr__(self, "pin", pin)
        object.__setattr__(self, "expected", expected)
        object.__setattr__(self, "root", root.resolve(strict=True))

    def validate(self, root: str, pin: str) -> None:
        if self.root is None or Path(root).resolve(strict=True) != self.root or pin != self.pin:
            raise RuntimeError("A1 build source root or canonical pin differs")
        head = patchharness._git(root, "rev-parse", "--verify", "HEAD^{commit}")
        if head.returncode != 0:
            raise RuntimeError("A1 build source HEAD query failed")
        if head.stdout.strip() != self.pin:
            raise RuntimeError("A1 build source HEAD differs")
        s8b_expected_materialization.assert_expected_materialization(self.root, self.expected)


@contextmanager
def materialized(repo_root: Path, *, base: Path | None = None, study_id=PILOT_STUDY_ID):
    base = base or repo_root / "external/ccbench"
    contract = load_contract(repo_root, study_id)
    pin = contract["canonical_head"]
    patchharness.assert_pinned_clean(os.fspath(base), pin)
    with patchharness.checkout(pin, base_dir=os.fspath(base)) as stock:
        with patchharness.checkout(pin, base_dir=os.fspath(base)) as root:
            with patchharness.applied(os.fspath(repo_root / contract["patch"]), pin, ccbench_dir=root):
                context = SourceContext(repo_root, base, Path(root), study_id=study_id)
                context.validate(root, pin)
                yield context, Path(stock)


def prepare_dependencies(*, root: Path, source: Path, repo_root: Path,
                         dependency_prefix: str, toolchain: dict) -> dict:
    staged = s8b_floor_campaign._verify_pristine_floor_dependency_sources(root, repo_root=repo_root)
    options = dict(fetchcontent_base_dir=os.fspath(root), **{
        f"{name}_source_dir": os.fspath(staged[name])
        for name in ("masstree", "mimalloc", "googletest")
    })
    buildcache.prepare_masstree_fetchcontent(
        ccbench_dir=os.fspath(source), dependency_prefix=dependency_prefix,
        expected_toolchain_manifest=toolchain, configure_timeout_s=900,
        target_timeout_s=900, **options,
    )
    receipt = buildcache._observe_fetchcontent_dependency_receipt(options["masstree_source_dir"])
    return dict(options, fetchcontent_dependency_receipt=receipt)


def configure_dependencies(options: dict) -> tuple[str, ...]:
    return tuple(f"-D{define}={options[key]}" for key, define in (
        ("fetchcontent_base_dir", "FETCHCONTENT_BASE_DIR"),
        ("masstree_source_dir", "FETCHCONTENT_SOURCE_DIR_MASSTREE"),
        ("mimalloc_source_dir", "FETCHCONTENT_SOURCE_DIR_MIMALLOC"),
        ("googletest_source_dir", "FETCHCONTENT_SOURCE_DIR_GOOGLETEST"),
    ))
