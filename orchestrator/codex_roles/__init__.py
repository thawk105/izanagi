"""Codex role adapter の共有 source contract。"""

from .spec import (RoleSpec, RoleSpecError, adapter_digest, adapter_path,
                   expected_adapters, get_role_spec, load_role_specs,
                   render_adapter)
from .policy import (RolePolicyError, find_forbidden_keys,
                     validate_input_semantics, validate_output_semantics)

__all__ = [
    "RoleSpec",
    "RoleSpecError",
    "RolePolicyError",
    "adapter_digest",
    "adapter_path",
    "expected_adapters",
    "get_role_spec",
    "load_role_specs",
    "render_adapter",
    "find_forbidden_keys",
    "validate_input_semantics",
    "validate_output_semantics",
]
