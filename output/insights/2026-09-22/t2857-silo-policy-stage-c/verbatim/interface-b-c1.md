# 単位 B と C1 の接続 interface (親が固定、2026-09-22 段 5)

単位 B が実装し、単位 C1 の smoke 入口が import して使う。B と C1 は並列に書くので、この形から外れない。

```python
# orchestrator/campaign/silo_policy_grammar.py  (単位 B)
@dataclasses.dataclass(frozen=True)
class PolicyDecision:
    accepted: bool
    stage: str                 # 常に "grammar"
    rule_id: str | None        # 受理なら None。拒否なら固定の規則 ID (例 "lex.alternative-token")
    offset: int | None         # 拒否位置の元文字列 offset (0 起点)
    line: int | None           # 1 起点
    column: int | None         # 1 起点
    reason: str | None         # 人が読む短い理由 (上限つき)

def validate_policy(source: str) -> PolicyDecision: ...
# 候補の拒否は値で返す。検査器自身の内部障害 (想定外の例外) は例外のまま上げ、拒否に変換しない。

# orchestrator/campaign/silo_policy_compile.py  (単位 B)
@dataclasses.dataclass(frozen=True)
class CompileDecision:
    accepted: bool             # returncode == 0 かつ timed_out でも unavailable でもない
    returncode: int | None
    timed_out: bool
    unavailable: bool          # compiler が無い・起動できない
    diagnostic: str            # 上限つき
    diagnostic_truncated: bool
    command: tuple[str, ...]   # 実際の argv
    compiler_version: str | None

def compile_policy(source: str, *, compiler: str, scratch_dir: str) -> CompileDecision: ...
# 単独 TU = "#include <cstdint>\n#include <algorithm>\n#include \"<api header の絶対 path>\"\n"
#           + "namespace izanagi_silo_policy {\n" + source + "\n}\n"
# argv = [compiler, "-std=c++17", "-Wall", "-Wextra", "-Werror", "-fsyntax-only", <TU>]。-D・-I を与えない。
# 環境変数 CPATH / CPLUS_INCLUDE_PATH / C_INCLUDE_PATH / GCC_EXEC_PREFIX / COMPILER_PATH を子の環境から外す。

def check_policy_body(source: str, *, compiler: str, scratch_dir: str
                      ) -> tuple[PolicyDecision, CompileDecision | None]: ...
# 構文検査 → 受理のときだけ単独 TU compile。構文検査で拒否なら 2 つ目は None。

def run_ubsan_harness(policy_dir: str, *, compiler: str, scratch_dir: str) -> dict: ...
def main(argv: list[str] | None = None) -> int: ...
# CLI: `python3 -m orchestrator.campaign.silo_policy_compile check <file> [--compiler C]`
#      `python3 -m orchestrator.campaign.silo_policy_compile ubsan --policy-dir <dir> --out <json> [--compiler C]`
```

C1 の smoke 入口は、4 段 (既存 DiffQuarantine → 既存 effect gate → `check_policy_body` の構文検査 → 単独 TU compile) の全部が受理した本文だけを build へ進める。どの段の拒否・例外・`timed_out`・`unavailable` でも build へ進まない。検査した本文と materialize した本文の sha256 が一致することを結果に記録する。
