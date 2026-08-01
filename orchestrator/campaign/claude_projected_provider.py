# -*- coding: utf-8 -*-
"""Projection-only Claude role provider for bounded unattended campaigns.

The provider deliberately lowers every source role to ``tools=[]`` at runtime.
The caller must project every byte the role may inspect into the JSON payload.
This is the same fresh-context/headless isolation used by the ratified 8b
selector runner, generalized for planner/coder/auditor/critic roles.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from .s8b_prediction_runner import (
    CLAUDE_ENV_ALLOWLIST,
    CLAUDE_TIMEOUT_S,
    PredictionRunnerError,
    ProviderResponse,
    _canonical_json_bytes,
    _create_neutral_root,
    _now_iso,
    _parse_json_object,
    _remove_neutral_root,
    _sha256,
    _write_bytes_bound,
)


_INVOCATION_ID_RE = re.compile(r"[a-z0-9][a-z0-9._-]{0,127}")


def _parse_frontmatter(role_bytes: bytes, *, expected_name: str) -> tuple[dict[str, Any], str]:
    try:
        text = role_bytes.decode("utf-8")
    except UnicodeError as exc:
        raise PredictionRunnerError("projected role が UTF-8 でない") from exc
    if not text.startswith("---\n") or "\n---\n" not in text[4:]:
        raise PredictionRunnerError("projected role frontmatter がない")
    frontmatter_text, body = text[4:].split("\n---\n", 1)
    values: dict[str, Any] = {}
    for line in frontmatter_text.splitlines():
        if ":" not in line:
            raise PredictionRunnerError("projected role frontmatter 行が不正")
        key, raw_value = line.split(":", 1)
        key = key.strip()
        raw_value = raw_value.strip()
        if key in values:
            raise PredictionRunnerError(f"projected role frontmatter duplicate: {key}")
        if key == "tools":
            try:
                values[key] = json.loads(raw_value)
            except json.JSONDecodeError as exc:
                raise PredictionRunnerError("projected role tools が JSON 配列でない") from exc
        elif raw_value.startswith('"'):
            try:
                values[key] = json.loads(raw_value)
            except json.JSONDecodeError as exc:
                raise PredictionRunnerError("projected role frontmatter string 不正") from exc
        else:
            values[key] = raw_value
    required = {"name", "description", "tools", "model", "effort"}
    if not required <= set(values):
        raise PredictionRunnerError(
            f"projected role frontmatter 必須 field 欠落: {sorted(required - set(values))}"
        )
    if values["name"] != expected_name:
        raise PredictionRunnerError(
            f"projected role name が期待値でない: {values['name']!r} != {expected_name!r}"
        )
    if values["model"] != "opus" or values["effort"] != "high":
        raise PredictionRunnerError("projected role model/effort は opus/high 必須")
    tools = values["tools"]
    if not isinstance(tools, list) or any(not isinstance(item, str) for item in tools):
        raise PredictionRunnerError("projected role tools は string 配列必須")
    if not isinstance(values["description"], str) or not values["description"]:
        raise PredictionRunnerError("projected role description が不正")
    if not body.strip():
        raise PredictionRunnerError("projected role 本文が空")
    return values, body


class ClaudeProjectedRoleProvider:
    """Invoke one named role per fresh, tool-less Claude CLI context."""

    provider_kind = "claude-headless-projected"

    def __init__(
        self,
        *,
        artifact_root: Path,
        role_file: Path,
        role_name: str,
        mediated_contract: str,
        repository_root: Path,
        executable: str | os.PathLike[str] = "claude",
        runner: Callable[..., Any] = subprocess.run,
        environ: Mapping[str, str] | None = None,
    ) -> None:
        if not isinstance(mediated_contract, str) or not mediated_contract.strip():
            raise PredictionRunnerError("mediated contract は空でない文字列必須")
        self.artifact_root = Path(artifact_root)
        self.artifact_root.mkdir(parents=True, exist_ok=True)
        self.artifact_root = self.artifact_root.resolve(strict=True)
        resolved = shutil.which(os.fspath(executable))
        if resolved is None:
            raise PredictionRunnerError(f"claude executable を解決できない: {executable}")
        self.executable = str(Path(resolved).resolve(strict=True))
        try:
            executable_bytes = Path(self.executable).read_bytes()
            role_bytes = Path(role_file).read_bytes()
        except OSError as exc:
            raise PredictionRunnerError(f"projected provider source を read-once できない: {exc}") from exc
        self.executable_sha256 = _sha256(executable_bytes)
        frontmatter, body = _parse_frontmatter(role_bytes, expected_name=role_name)
        self.role_name = role_name
        self.role_file = str(Path(role_file))
        self.role_file_sha256 = _sha256(role_bytes)
        self.source_declared_tools = list(frontmatter["tools"])
        self.runtime_declared_tools: list[str] = []
        self.effective_prompt = (
            body.rstrip()
            + "\n\n---\n\n"
            + "# T-178 mediated projection contract (this section takes precedence)\n\n"
            + mediated_contract.strip()
            + "\n"
        )
        self.effective_prompt_sha256 = _sha256(self.effective_prompt.encode("utf-8"))
        self.inline_agent_name = "izanagi-projected-inline"
        self.inline_agents_json = _canonical_json_bytes({
            self.inline_agent_name: {
                "description": frontmatter["description"],
                "prompt": self.effective_prompt,
                "tools": [],
                "model": frontmatter["model"],
            }
        }).decode("utf-8")

        self.cleanup_error: BaseException | None = None
        (
            self.neutral_root,
            self._neutral_root_identity,
            self._neutral_root_finalizer,
        ) = _create_neutral_root(
            self,
            prefix="izanagi-projected-",
            repository_root=repository_root,
            artifact_root=self.artifact_root,
        )
        try:
            self.mcp_config_path = self.neutral_root / "empty-mcp-config.json"
            _write_bytes_bound(self.mcp_config_path, b'{"mcpServers":{}}')
            self.neutral_cwd: Path | None = None
            self._observed_session_ids: set[str] = set()
            source_env = os.environ if environ is None else environ
            self.env = {
                key: source_env[key]
                for key in CLAUDE_ENV_ALLOWLIST
                if key in source_env
            }
            if "HOME" not in self.env:
                raise PredictionRunnerError("claude 認証に必要な HOME が allowlist env にない")
            self._runner = runner
            self.argv = [
                self.executable,
                "-p",
                "--agent",
                self.inline_agent_name,
                "--agents",
                self.inline_agents_json,
                "--output-format",
                "json",
                "--input-format",
                "text",
                "--effort",
                "high",
                "--setting-sources",
                "",
                "--disable-slash-commands",
                "--strict-mcp-config",
                "--mcp-config",
                str(self.mcp_config_path),
                "--no-session-persistence",
            ]
        except BaseException:
            self.close()
            raise

    def close(self) -> None:
        """Best-effort, idempotent cleanup; cleanup failures never escape."""
        finalizer = self._neutral_root_finalizer
        if not finalizer.alive:
            return
        try:
            _remove_neutral_root(self._neutral_root_identity, self.artifact_root)
        except BaseException as exc:
            self.cleanup_error = exc
            return
        self.cleanup_error = None
        finalizer.detach()

    def invoke(self, *, invocation_id: str, payload: Mapping[str, Any]) -> ProviderResponse:
        if not isinstance(invocation_id, str) or _INVOCATION_ID_RE.fullmatch(invocation_id) is None:
            raise PredictionRunnerError(f"invocation_id が安全な形式でない: {invocation_id!r}")
        if not isinstance(payload, Mapping):
            raise PredictionRunnerError("projected role payload は object 必須")
        payload_bytes = _canonical_json_bytes(payload)
        payload_path = self.artifact_root / f"payload_{invocation_id}.json"
        _write_bytes_bound(payload_path, payload_bytes)

        neutral_cwd = Path(tempfile.mkdtemp(prefix="cwd-", dir=self.neutral_root))
        if neutral_cwd.is_symlink() or not neutral_cwd.is_dir() or any(neutral_cwd.iterdir()):
            raise PredictionRunnerError("neutral cwd は invocation ごとの空 directory 必須")
        self.neutral_cwd = neutral_cwd
        started_at = _now_iso()
        try:
            completed = self._runner(
                list(self.argv),
                input=payload_bytes,
                cwd=str(neutral_cwd),
                env=dict(self.env),
                timeout=CLAUDE_TIMEOUT_S,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except subprocess.TimeoutExpired as exc:
            raise PredictionRunnerError("claude projected invocation timeout") from exc
        except OSError as exc:
            raise PredictionRunnerError(f"claude projected invocation 起動失敗: {exc}") from exc
        finished_at = _now_iso()
        stdout = getattr(completed, "stdout", None)
        if not isinstance(stdout, bytes):
            raise PredictionRunnerError("claude envelope stdout は bytes 必須")
        envelope_path = self.artifact_root / f"envelope_{invocation_id}.json"
        envelope_sha256 = _write_bytes_bound(envelope_path, stdout)
        if getattr(completed, "returncode", None) != 0:
            raise PredictionRunnerError(
                f"claude projected invocation nonzero rc: "
                f"{getattr(completed, 'returncode', None)!r}"
            )
        envelope = _parse_json_object(stdout, source=envelope_path)
        if envelope.get("type") != "result" or envelope.get("subtype") != "success":
            raise PredictionRunnerError("claude envelope type/subtype が result/success でない")
        if envelope.get("is_error") is not False:
            raise PredictionRunnerError("claude envelope is_error は false 固定")
        if type(envelope.get("num_turns")) is not int or envelope["num_turns"] != 1:
            raise PredictionRunnerError("claude envelope num_turns は 1 固定")
        if envelope.get("permission_denials") != []:
            raise PredictionRunnerError("claude envelope permission_denials は [] 固定")
        result = envelope.get("result")
        session_id = envelope.get("session_id")
        if not isinstance(result, str):
            raise PredictionRunnerError("claude envelope result は str 必須")
        if not isinstance(session_id, str) or not session_id:
            raise PredictionRunnerError("claude envelope session_id は空でない str 必須")
        if session_id in self._observed_session_ids:
            raise PredictionRunnerError("fresh context に反する session_id 重複を観測")

        model_usage = envelope.get("modelUsage")
        if not isinstance(model_usage, Mapping) or any(
            not isinstance(record, Mapping) for record in model_usage.values()
        ):
            raise PredictionRunnerError("claude envelope modelUsage schema が不正")
        opus_slugs = [
            key
            for key in model_usage
            if isinstance(key, str) and key.startswith("claude-opus-")
        ]
        if len(opus_slugs) != 1:
            raise PredictionRunnerError("modelUsage の主 claude-opus- slug が一意でない")
        opus_usage = model_usage[opus_slugs[0]]
        for token_key in ("inputTokens", "outputTokens"):
            token_count = opus_usage.get(token_key)
            if type(token_count) is not int or token_count <= 0:
                raise PredictionRunnerError(
                    f"modelUsage の主 claude-opus- record は正の {token_key} 必須"
                )
        usage = envelope.get("usage")
        server_tool_use = usage.get("server_tool_use") if isinstance(usage, Mapping) else None
        if not isinstance(server_tool_use, Mapping):
            raise PredictionRunnerError("usage.server_tool_use は object 必須")
        for key, count in server_tool_use.items():
            if not isinstance(key, str) or isinstance(count, bool) or not isinstance(count, int):
                raise PredictionRunnerError("usage.server_tool_use count schema が不正")
            if count != 0:
                raise PredictionRunnerError("server tool use を観測したため拒否")

        self._observed_session_ids.add(session_id)
        return ProviderResponse(
            raw_response=result,
            provenance={
                "child_id": session_id,
                "role_name": self.role_name,
                "role_file": self.role_file,
                "role_file_sha256": self.role_file_sha256,
                "effective_prompt_sha256": self.effective_prompt_sha256,
                "model": opus_slugs[0],
                "started_at": started_at,
                "finished_at": finished_at,
                "fresh_context": True,
                "source_declared_tools": list(self.source_declared_tools),
                "declared_tools": [],
                "capability_lowering": "projection-only-tools-empty",
                "observed_tool_events": [],
                "payload_sha256": hashlib.sha256(payload_bytes).hexdigest(),
                "envelope_sha256": envelope_sha256,
                "claude_executable_path": self.executable,
                "claude_executable_sha256": self.executable_sha256,
            },
        )
