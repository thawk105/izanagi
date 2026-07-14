#!/usr/bin/env python3
"""Codex agent profile の同期と安全な有効化集合を検査する。

`.claude/agents/*.md` の role 本文を意味契約の正本とし、Codex で権限境界を
近似できる role だけを `.codex/agents/*.toml` に生成する。通常実行は検査のみ、
`--write` は対応 profile を決定的に再生成する。
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

try:  # Python 3.11+
    import tomllib  # type: ignore[import-not-found]
except ModuleNotFoundError:  # Python 3.10 (Izanagi の現行環境)
    try:
        import tomli as tomllib  # type: ignore[import-not-found,no-redef]
    except ModuleNotFoundError:
        tomllib = None  # type: ignore[assignment]

REPO = Path(__file__).resolve().parent.parent

_FRONTMATTER_KEYS = {"name", "description", "tools", "model", "effort"}

# Codex custom agent の sandbox で Claude の権限境界を安全側に近似できる初期集合。
# model を全 role で固定し、モデル差と製品 adapter 差を同時に持ち込まない。
SUPPORTED = {
    "auditor": {
        "model": "gpt-5.6-sol",
        "reasoning": "high",
        "sandbox": "read-only",
    },
    "critic": {
        "model": "gpt-5.6-sol",
        "reasoning": "high",
        "sandbox": "read-only",
    },
    "verifier": {
        "model": "gpt-5.6-sol",
        "reasoning": "high",
        "sandbox": "read-only",
    },
}

# 発見可能な `.codex/agents/` に実体化してはいけない role。理由は人間向け README と
# D54 に詳述する。ここでは全 inventory を fail-closed に分類すること自体が目的。
BLOCKED = {
    "axis-proposer": "tools:[] による file-read 経路不存在を再現できない",
    "calibrator": "書込先を calibration 成果物だけに限定できない",
    "coder": "EVOLVE-BLOCK 単位の編集面を profile だけでは限定できない",
    "coder-v4-autonomous": "tools:[] による Model Y のリーク遮断を再現できない",
    "coder-v4-autonomous-sort": "tools:[] による Model Y のリーク遮断を再現できない",
    "coder-v4-autonomous-trigger-gating": "tools:[] による Model Y のリーク遮断を再現できない",
    "critic-experiment": "guided.py だけを許す Bash-only 境界を再現できない",
    "planner-v4": "tools:[] による file-read 経路不存在を再現できない",
    "profiler": "perf 出力先だけに書込みを限定できない",
}

# 分類理由が前提にする Claude 側の権限/model 契約。ここが変わったとき、同じ supported/blocked
# 判定を黙って使い続けない。順序も source の意図的な tool surface 表記として固定する。
SOURCE_CONTRACT = {
    "auditor": (("Read", "Grep", "Glob"), "opus", "high"),
    "axis-proposer": ((), "opus", "high"),
    "calibrator": (("Read", "Write", "Bash"), "sonnet", "medium"),
    "coder": (("Read", "Grep", "Glob", "Edit"), "sonnet", "medium"),
    "coder-v4-autonomous": ((), "opus", "high"),
    "coder-v4-autonomous-sort": ((), "opus", "high"),
    "coder-v4-autonomous-trigger-gating": ((), "opus", "high"),
    "critic": (("Read", "Grep", "Glob", "Bash"), "opus", "high"),
    "critic-experiment": (("Bash",), "opus", None),
    "planner-v4": ((), "opus", "high"),
    "profiler": (("Read", "Grep", "Glob", "Bash"), "opus", "high"),
    "verifier": (("Read", "Grep", "Glob", "Bash"), "sonnet", "high"),
}

_ADAPTER_PREAMBLE = """# Izanagi Codex runtime adapter

この profile は `.claude/agents/{role}.md` の意味的な役割を Codex に移すための条件付き
adapter であり、Claude Code の tools allowlist と同等の隔離を主張しない。

呼出側の必須契約:
- 起動直前に親 turn の実効 sandbox を read-only にする。親の live permission override は profile の
  `sandbox_mode` より優先されるため、workspace-write / danger-full-access の親から起動しない。
- 毎回 `fork_turns=\"none\"` の fresh subagent として起動する。
- 対象 role が許された入力だけを明示的に射影して渡す。作業ツリーを探索して入力を補わない。

開始時に自分の実効 sandbox が read-only であることを確認する。確認できない、または read-only
でない場合は `ADAPTER-REFUSED: effective sandbox is not read-only` とだけ返し、tool を使わず停止する。
read-only は書込み防止だけで読取面・Bash 面を制限しきらない。研究上の証拠に使う前に元の
verifier / auditor / 人間 gate を通す。
"""

_ROLE_OVERRIDES = {
    "auditor": """この起動で明示的に渡された監査射影と、その中で列挙された path だけを扱う。
WAL、fitness、throughput、worklog、phase、handoff、output 配下を探索・読取してはならない。""",
    "critic": """入力は呼出側が inline で渡した digest だけに限定する。共有本文にある
`orchestrator/critic/digest.py` の自走許可はこの Codex adapter では無効。campaign directory、WAL、
worklog、phase、handoff を探索・読取して digest を補ってはならない。""",
    "verifier": """入力は呼出側が inline で渡した trace、または明示した trace path と検査コードだけに
限定する。性能値、期待 verdict、worklog、phase、handoff、output の別成果物を探索・読取してはならない。""",
}

_ADAPTER_EPILOGUE = """# Codex runtime override (tool 境界)

上の共有 role 本文にある「特定 tool だけを持つ」「Bash/Edit/Write が構造的に不可能」という記述は
Claude Code 側の契約であり、この Codex session の実際の tool surface を表さない。Codex では本
adapter 冒頭の制約を優先し、見えている追加 tool を入力面の拡張や書込みに使わない。
"""


class ProfileError(ValueError):
    """agent 定義が限定 schema に違反した。"""


@dataclass(frozen=True)
class ClaudeAgent:
    path: Path
    name: str
    description: str
    tools: tuple[str, ...]
    model: str
    effort: str | None
    body: str


def _decode_scalar(raw: str, path: Path, key: str) -> str:
    if raw.startswith('"'):
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ProfileError(f"{path}: {key} の quoted value が不正: {exc}") from exc
        if not isinstance(value, str):
            raise ProfileError(f"{path}: {key} は文字列でなければならない")
        return value
    if key == "description" and " #" in raw:
        raise ProfileError(
            f"{path}: description 内の # は JSON quote が必要 (YAML comment 切断を防ぐ)"
        )
    if not raw:
        raise ProfileError(f"{path}: {key} が空")
    return raw


def parse_claude_agent(path: Path) -> ClaudeAgent:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].rstrip("\r\n") != "---":
        raise ProfileError(f"{path}: frontmatter 開始 `---` がない")
    try:
        end = next(i for i, line in enumerate(lines[1:], 1) if line.rstrip("\r\n") == "---")
    except StopIteration as exc:
        raise ProfileError(f"{path}: frontmatter 終端 `---` がない") from exc

    values: dict[str, object] = {}
    for lineno, line in enumerate(lines[1:end], 2):
        raw_line = line.rstrip("\r\n")
        if not raw_line:
            continue
        key, sep, raw = raw_line.partition(":")
        if not sep or key not in _FRONTMATTER_KEYS:
            raise ProfileError(f"{path}:{lineno}: 未対応 frontmatter 行: {raw_line!r}")
        if key in values:
            raise ProfileError(f"{path}:{lineno}: {key} が重複")
        raw = raw.strip()
        if key == "tools":
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ProfileError(f"{path}:{lineno}: tools は JSON 配列で書く: {exc}") from exc
            if not isinstance(parsed, list) or not all(isinstance(v, str) for v in parsed):
                raise ProfileError(f"{path}:{lineno}: tools は文字列の JSON 配列でなければならない")
            values[key] = tuple(parsed)
        else:
            values[key] = _decode_scalar(raw, path, key)

    required = {"name", "description", "tools", "model"}
    missing = required - values.keys()
    if missing:
        raise ProfileError(f"{path}: frontmatter 必須キー欠落: {sorted(missing)}")
    if values["name"] != path.stem:
        raise ProfileError(f"{path}: filename と name が不一致 ({values['name']!r})")

    body = "".join(lines[end + 1 :])
    if body.startswith("\n"):
        body = body[1:]
    if not body or not body.endswith("\n"):
        raise ProfileError(f"{path}: prompt 本文は非空かつ LF 終端でなければならない")

    return ClaudeAgent(
        path=path,
        name=str(values["name"]),
        description=str(values["description"]),
        tools=tuple(values["tools"]),
        model=str(values["model"]),
        effort=str(values["effort"]) if "effort" in values else None,
        body=body,
    )


def load_inventory(root: Path) -> dict[str, ClaudeAgent]:
    source_dir = root / ".claude" / "agents"
    paths = sorted(source_dir.glob("*.md"))
    if not paths:
        raise ProfileError(f"{source_dir}: Claude agent 定義がない")
    inventory: dict[str, ClaudeAgent] = {}
    for path in paths:
        agent = parse_claude_agent(path)
        if agent.name in inventory:
            raise ProfileError(f"{path}: role name {agent.name!r} が重複")
        inventory[agent.name] = agent
    return inventory


def render_profile(agent: ClaudeAgent) -> str:
    policy = SUPPORTED[agent.name]
    expected_effort = policy["reasoning"]
    if agent.effort != expected_effort:
        raise ProfileError(
            f"{agent.path}: Claude effort={agent.effort!r} と Codex reasoning={expected_effort!r} "
            "が一致しない。意図的な写像変更なら policy と D54 を同時改訂する"
        )
    instructions = (
        _ADAPTER_PREAMBLE.format(role=agent.name)
        + "\n"
        + agent.body
        + "\n"
        + "# Codex role-specific input override\n\n"
        + _ROLE_OVERRIDES[agent.name]
        + "\n\n"
        + _ADAPTER_EPILOGUE
    )
    if "'''" in instructions:
        raise ProfileError(f"{agent.path}: TOML multiline literal の終端 `'''` を本文に含む")
    q = lambda value: json.dumps(value, ensure_ascii=False)
    rendered = (
        f"name = {q(agent.name)}\n"
        f"description = {q(agent.description)}\n"
        f"model = {q(policy['model'])}\n"
        f"model_reasoning_effort = {q(policy['reasoning'])}\n"
        f"sandbox_mode = {q(policy['sandbox'])}\n"
        "developer_instructions = '''\n"
        f"{instructions}"
        "'''\n"
    )
    _validate_rendered_profile(rendered, agent, policy, instructions)
    return rendered


def _parse_toml(text: str, label: object) -> dict[str, object]:
    if tomllib is None:
        raise ProfileError(
            f"{label}: TOML parser がない。Python 3.11+ を使うか Python 3.10 に tomli を導入する"
        )
    try:
        parsed = tomllib.loads(text)
    except Exception as exc:  # tomllib/tomli で例外 class が異なる
        raise ProfileError(f"{label}: TOML parse 失敗: {exc}") from exc
    if not isinstance(parsed, dict):
        raise ProfileError(f"{label}: TOML root は table でなければならない")
    return parsed


def _validate_rendered_profile(
    rendered: str,
    agent: ClaudeAgent,
    policy: dict[str, str],
    instructions: str,
) -> None:
    parsed = _parse_toml(rendered, agent.path)
    expected = {
        "name": agent.name,
        "description": agent.description,
        "model": policy["model"],
        "model_reasoning_effort": policy["reasoning"],
        "sandbox_mode": policy["sandbox"],
        "developer_instructions": instructions,
    }
    if parsed != expected:
        raise ProfileError(f"{agent.path}: renderer の TOML round-trip が不一致")


def expected_profiles(root: Path) -> dict[str, str]:
    inventory = load_inventory(root)
    actual_roles = set(inventory)
    classified = set(SUPPORTED) | set(BLOCKED)
    overlap = set(SUPPORTED) & set(BLOCKED)
    if overlap:
        raise ProfileError(f"policy: supported/blocked が重複: {sorted(overlap)}")
    if actual_roles != classified:
        unknown = actual_roles - classified
        stale = classified - actual_roles
        details = []
        if unknown:
            details.append(f"未分類 role={sorted(unknown)}")
        if stale:
            details.append(f"実体のない policy role={sorted(stale)}")
        raise ProfileError("policy inventory 不一致: " + "; ".join(details))
    if set(SOURCE_CONTRACT) != actual_roles:
        raise ProfileError("SOURCE_CONTRACT inventory が role policy と不一致")
    for name, agent in inventory.items():
        observed = (agent.tools, agent.model, agent.effort)
        if observed != SOURCE_CONTRACT[name]:
            raise ProfileError(
                f"{agent.path}: Claude source contract drift: observed={observed!r}, "
                f"expected={SOURCE_CONTRACT[name]!r}。supported/blocked 判定を再レビューする"
            )
    return {f"{name}.toml": render_profile(inventory[name]) for name in sorted(SUPPORTED)}


def check(root: Path = REPO) -> list[str]:
    try:
        expected = expected_profiles(root)
    except (OSError, ProfileError) as exc:
        return [str(exc)]

    profile_dir = root / ".codex" / "agents"
    actual = {path.name: path for path in profile_dir.glob("*.toml")}
    findings: list[str] = []
    for name in sorted(set(actual) - set(expected)):
        role = Path(name).stem
        reason = BLOCKED.get(role, "policy にない余分な profile")
        findings.append(f"{actual[name]}: 有効化禁止/余分な profile ({reason})")
    for name in sorted(set(expected) - set(actual)):
        findings.append(f"{profile_dir / name}: 対応 profile が欠落 (`--write` で再生成)")
    for name in sorted(set(expected) & set(actual)):
        try:
            current = actual[name].read_text(encoding="utf-8")
        except OSError as exc:
            findings.append(f"{actual[name]}: 読み取り失敗: {exc}")
            continue
        try:
            _parse_toml(current, actual[name])
        except ProfileError as exc:
            findings.append(str(exc))
            continue
        if current != expected[name]:
            findings.append(
                f"{actual[name]}: source/policy から drift (`python3 tools/check_codex_agents.py --write`)"
            )
    return findings


def write_profiles(root: Path = REPO) -> None:
    expected = expected_profiles(root)
    profile_dir = root / ".codex" / "agents"
    profile_dir.mkdir(parents=True, exist_ok=True)
    unexpected = sorted(path for path in profile_dir.glob("*.toml") if path.name not in expected)
    if unexpected:
        names = ", ".join(str(path) for path in unexpected)
        raise ProfileError(f"余分/blocked profile は自動削除しない: {names}")
    for name, content in expected.items():
        (profile_dir / name).write_text(content, encoding="utf-8", newline="\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="対応 profile を決定的に再生成する")
    parser.add_argument("--root", type=Path, default=REPO, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    try:
        if args.write:
            write_profiles(args.root)
        findings = check(args.root)
    except (OSError, ProfileError) as exc:
        findings = [str(exc)]
    if findings:
        for finding in findings:
            print(f"ERROR: {finding}", file=sys.stderr)
        return 1
    print(f"OK: Codex agent profiles ({len(SUPPORTED)} active / {len(BLOCKED)} blocked)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
