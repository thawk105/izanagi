"""Real compiler fixture support for condition-gated synthetic drivers."""
from __future__ import annotations

import shutil
from pathlib import Path

from orchestrator.campaign.condition_meaning_gate import DEFINE_SPECS, DefineSpec


_FIXTURE_ROOT = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "condition_meaning_gate"
    / "supplied"
)

_OPTIONS = """set(CCBENCH_BACK_OFF 1 CACHE STRING "backoff")
set(CCBENCH_NO_WAIT_LOCKING_IN_VALIDATION 1 CACHE STRING "no wait")
set(CCBENCH_NO_WAIT_OF_TICTOC 0 CACHE STRING "tictoc wait")
set(CCBENCH_TRACE 0 CACHE STRING "trace")
set(CCBENCH_WAL 0 CACHE STRING "wal")
set(CCBENCH_BACKOFF_FIXED -1 CACHE STRING "static backoff")
set(CCBENCH_BACKOFF_TRIGGER_GATING 0 CACHE STRING "trigger gate")
set(CCBENCH_SORT_VARIANT 0 CACHE STRING "sort variant")

function(ccbench_universal_definitions out_var)
  set(${out_var}
    BACK_OFF=${CCBENCH_BACK_OFF}
    NO_WAIT_LOCKING_IN_VALIDATION=${CCBENCH_NO_WAIT_LOCKING_IN_VALIDATION}
    NO_WAIT_OF_TICTOC=${CCBENCH_NO_WAIT_OF_TICTOC}
    TRACE=${CCBENCH_TRACE}
    WAL=${CCBENCH_WAL}
    BACKOFF_FIXED=${CCBENCH_BACKOFF_FIXED}
    BACKOFF_TRIGGER_GATING=${CCBENCH_BACKOFF_TRIGGER_GATING}
    SORT_VARIANT=${CCBENCH_SORT_VARIANT}
    PARENT_SCOPE)
endfunction()
"""

SORT_VARIANT_SOURCE = '''#include "storage.hh"
#ifndef SORT_VARIANT
#error "SORT_VARIANT must be defined"
#endif
static constexpr int condition_gate_sort_variant = SORT_VARIANT;
class TxExecutor {
 public:
  bool validationPhase() {
    // EVOLVE-BLOCK-BEGIN silo-writeset-sort
    // fixture
#if SORT_VARIANT
    sort(write_set_.begin(), write_set_.end());
#else
    sort(write_set_.begin(), write_set_.end());
#endif
    // EVOLVE-BLOCK-END silo-writeset-sort
    return condition_gate_sort_variant >= 0;
  }
};
'''

TRIGGER_GATING_SOURCE = '''#include "backoff.hh"
#ifndef BACKOFF_TRIGGER_GATING
#error "BACKOFF_TRIGGER_GATING must be defined"
#endif
#if BACKOFF_TRIGGER_GATING
static constexpr int condition_gate_trigger_variant = 1;
#else
static constexpr int condition_gate_trigger_variant = 0;
#endif
class TxExecutor {
 public:
  void abort() {
#if BACKOFF_TRIGGER_GATING
  bool izanagi_gate_pass = true;
#endif
  // EVOLVE-BLOCK-BEGIN silo-backoff-trigger-gating
  // fixture
#if BACKOFF_TRIGGER_GATING
  izanagi_gate_pass = true;
#else
  Backoff::backoff(FLAGS_clocks_per_us);
#endif
  // EVOLVE-BLOCK-END silo-backoff-trigger-gating
#if BACKOFF_TRIGGER_GATING
  if (izanagi_gate_pass) {
    Backoff::backoff(FLAGS_clocks_per_us);
  }
#endif
  }
};
'''


def backoff_fixed_source(value: int) -> str:
    """Return a materialized BACKOFF_FIXED decoder for one exact value."""
    if type(value) is not int or value < 0:
        raise ValueError("backoff fixture value must be a non-negative exact int")
    return f'''// EVOLVE-BLOCK-BEGIN silo-backoff-magnitude
#if BACKOFF_FIXED >= 0
    double now_backoff = {value}.0;
#else
    double now_backoff = Backoff_.load(std::memory_order_acquire);
#endif
// EVOLVE-BLOCK-END silo-backoff-magnitude
'''


def cxx_flag_owner_source(macro: str) -> str:
    """Return an owner TU whose bytes expose one CMAKE_CXX_FLAGS request."""
    if not macro or not macro.replace("_", "").isalnum():
        raise ValueError("fixture macro must be a non-empty identifier")
    return f'''#ifndef {macro}
#error "{macro} must be defined"
#endif
#if {macro}
static constexpr int condition_gate_cxx_flag = 1;
#else
static constexpr int condition_gate_cxx_flag = 0;
#endif
int main() {{ return condition_gate_cxx_flag; }}
'''


def condition_gate_compilers() -> tuple[str, str] | None:
    """Return installed C and C++ compilers suitable for live gate evidence."""
    cc = next(
        (path for name in ("gcc-13", "gcc-12", "gcc", "cc")
         if (path := shutil.which(name)) is not None),
        None,
    )
    cxx = next(
        (path for name in ("g++-13", "g++-12", "g++", "c++")
         if (path := shutil.which(name)) is not None),
        None,
    )
    if cc is None or cxx is None or shutil.which("cmake") is None:
        return None
    return cc, cxx


def install_condition_gate_build_fixture(
    source_root: str | Path,
    *,
    define_spec: DefineSpec | None = None,
) -> Path:
    """Install a real target and cache-to-owner-TU define graph.

    A caller may create the selected ``DefineSpec.owner_tus[0]`` or
    ``include/backoff.hh`` first. Those materialized driver sources are
    preserved. Missing Silo fixture files retain the existing default path.
    """
    root = Path(source_root)
    spec = DEFINE_SPECS["BACKOFF_FIXED"] if define_spec is None else define_spec
    if type(spec) is not DefineSpec or len(spec.owner_tus) != 1:
        raise ValueError("condition gate fixture requires one exact owner TU")
    owner_rel = spec.owner_tus[0]
    (root / "cmake").mkdir(parents=True, exist_ok=True)
    (root / "cc" / "silo").mkdir(parents=True, exist_ok=True)
    (root / owner_rel).parent.mkdir(parents=True, exist_ok=True)
    (root / "include").mkdir(parents=True, exist_ok=True)

    shutil.copy2(_FIXTURE_ROOT / "CMakeLists.txt", root / "CMakeLists.txt")
    if spec.target != "ycsb_silo.exe":
        with (root / "CMakeLists.txt").open("a", encoding="utf-8") as stream:
            stream.write(
                f"add_executable({spec.target} {owner_rel})\n"
                f"target_compile_definitions({spec.target} PRIVATE "
                "${condition_gate_defines})\n"
            )
    shutil.copy2(
        _FIXTURE_ROOT / "cc" / "silo" / "CMakeLists.txt",
        root / "cc" / "silo" / "CMakeLists.txt",
    )
    (root / "cmake" / "Options.cmake").write_text(
        _OPTIONS, encoding="utf-8",
    )

    silo_owner = root / "cc" / "silo" / "transaction.cc"
    if not silo_owner.exists():
        shutil.copy2(
            _FIXTURE_ROOT / "cc" / "silo" / "transaction.cc", silo_owner,
        )
    backoff = root / "include" / "backoff.hh"
    if not backoff.exists():
        shutil.copy2(_FIXTURE_ROOT / "include" / "backoff.hh", backoff)

    for header in (
        root / "include" / "atomic_tool.hh",
        root / "cc" / "silo" / "storage.hh",
        root / "cc" / "silo" / "backoff.hh",
    ):
        if not header.exists():
            header.write_text(
                "// condition gate preprocessing fixture\n", encoding="utf-8",
            )
    return root


def install_backoff_condition_gate_roots(
        base: str | Path) -> tuple[Path, Path]:
    """Install distinct patched and stock roots for inert backoff requests."""
    parent = Path(base)
    patched = install_condition_gate_build_fixture(parent / "patched")
    stock = install_condition_gate_build_fixture(parent / "stock")
    return patched, stock
