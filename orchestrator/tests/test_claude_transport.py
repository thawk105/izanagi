# -*- coding: utf-8 -*-
"""T-276 transport admission boundary and non-tautological oracle tests."""
from __future__ import annotations

import ast
import hashlib
import inspect
import json
import os
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from orchestrator.campaign import claude_transport as T  # noqa: E402
from orchestrator.campaign import claude_projected_provider as CP  # noqa: E402
from orchestrator.campaign import p3_autonomous_workload_trial as A  # noqa: E402
from campaign.build_admission import (  # noqa: E402
    GeneratorId,
    build_run_context,
)
from orchestrator.campaign.claude_projected_provider import (  # noqa: E402
    ClaudeProjectedRoleProvider,
)
from orchestrator.campaign.s8b_prediction_runner import (  # noqa: E402
    PredictionRunnerError,
    ProviderResponse,
)
from orchestrator.qualification import collector as COLLECTOR  # noqa: E402
from orchestrator.qualification import qsub_binding as QSUB  # noqa: E402


_COMMITTED_POLICY_BYTES = b'''{
  "schema_version": "pegasus-claude-transport-policy/v1",
  "site": "PEGASUS_COMPUTE",
  "mode": "explicit-http-proxy-env",
  "endpoint_values": {
    "http_proxy": "http://10.120.96.1:8080",
    "https_proxy": "http://10.120.96.1:8080"
  }
}
'''
_COMMITTED_POLICY_SHA256 = (
    "67297d505bf01df80c6b77dbe21d837a19091018c41e8e2106ce432b5cbd33f2"
)
_COMMITTED_ENDPOINT_SHA256 = (
    "f08f46ffdec97849236010f3dcc8d6a313e43bd5c7c689c44d6b05ca7d65c962"
)
_DISTINCT_POLICY_BYTES = b'''{
  "schema_version": "pegasus-claude-transport-policy/v1",
  "site": "PEGASUS_COMPUTE",
  "mode": "explicit-http-proxy-env",
  "endpoint_values": {
    "http_proxy": "http://proxy-a.example:18080",
    "https_proxy": "http://proxy-b.example:18443"
  }
}
'''
_DISTINCT_ENDPOINT_SHA256 = (
    "8600267e0e37ea741979c88de241b910804defdb9ea147f4d0f5200a4ece3cfb"
)
_DISTINCT_POLICY_SHA256 = (
    "279fcecffc6e0c636171799fa7744f58495730698d3c75f9fb18534e1430797c"
)
_REVERSE_POLICY_BYTES = b'''{
  "schema_version": "pegasus-claude-transport-policy/v1",
  "site": "PEGASUS_COMPUTE",
  "mode": "explicit-http-proxy-env",
  "endpoint_values": {
    "https_proxy": "http://reverse-https.example:28443",
    "http_proxy": "http://reverse-http.example:28080"
  }
}
'''
_REVERSE_ENDPOINT_SHA256 = (
    "fa07a5da8b1a8b2dd415e313ddd050a819ac5defae92916c2fb80812df6d9368"
)
_VALID_RECEIPT = {
    "schema_version": "claude-transport-receipt/v1",
    "mode": "explicit-http-proxy-env",
    "site": "PEGASUS_COMPUTE",
    "admitted_env_keys": ["http_proxy", "https_proxy"],
    "endpoint_values": {
        "http_proxy": "http://proxy-a.example:18080",
        "https_proxy": "http://proxy-b.example:18443",
    },
    "endpoint_values_sha256": _DISTINCT_ENDPOINT_SHA256,
    "policy_path": "tools/pegasus/policies/transport_v1.json",
    "policy_sha256": _DISTINCT_POLICY_SHA256,
    "source_tls_trust_override_keys": [],
    "forwarded_tls_trust_override_keys": [],
    "pbs_jobid": "987654.pegasus",
}
_METERED_TRANSPORT_KEYS = (
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_AUTH_TOKEN",
    "ANTHROPIC_BASE_URL",
    "CLAUDE_CODE_USE_BEDROCK",
    "CLAUDE_CODE_USE_VERTEX",
)


def _copy_receipt() -> dict:
    return json.loads(json.dumps(_VALID_RECEIPT))


def _no_build_context():
    return build_run_context(generator_id=GeneratorId.S8A_TRIGGER_SWEEP)


def _source(
    http: str = "http://proxy-a.example:18080",
    https: str = "http://proxy-b.example:18443",
) -> dict[str, str]:
    return {
        "HOME": "/fixture/home",
        "PBS_JOBID": "987654.pegasus",
        "http_proxy": http,
        "https_proxy": https,
    }


def _expect_transport_error(code: str, thunk, *forbidden: str) -> str:
    try:
        thunk()
    except T.ClaudeTransportError as exc:
        assert exc.code == code, (exc.code, code)
        message = str(exc)
        prefix = f"{code}: "
        assert message.startswith(prefix)
        body = message[len(prefix):]
        for sentinel in forbidden:
            assert sentinel not in body
        return message
    raise AssertionError(f"ClaudeTransportError({code}) が必要")


def _policy_with(endpoint_values: str, *, top_extra: str = "") -> bytes:
    return (
        "{"
        '"schema_version":"pegasus-claude-transport-policy/v1",'
        '"site":"PEGASUS_COMPUTE",'
        '"mode":"explicit-http-proxy-env",'
        f'"endpoint_values":{endpoint_values}{top_extra}'
        "}"
    ).encode("utf-8")


def _evaluate(
    *, source_env=None, policy_bytes: bytes = _DISTINCT_POLICY_BYTES,
    site: str = "PEGASUS_COMPUTE",
):
    return T.evaluate_transport_admission(
        source_env=_source() if source_env is None else source_env,
        policy_bytes=policy_bytes,
        site=site,
    )


def test_committed_policy_matches_independent_literal_hash_and_registry() -> None:
    policy_path = _ROOT / "tools/pegasus/policies/transport_v1.json"
    actual = policy_path.read_bytes()
    assert actual == _COMMITTED_POLICY_BYTES
    assert hashlib.sha256(actual).hexdigest() == _COMMITTED_POLICY_SHA256
    registry = json.loads(
        (_ROOT / "tools/pegasus/policies/registry_v1.json").read_text(encoding="utf-8")
    )
    assert registry == {
        "schema_version": "pegasus-policy-registry/v1",
        "policy_paths": [
            "orchestrator/qualification/t126_reservation_policy_v1.json",
            "tools/pegasus/policies/calibration_v1.json",
            "tools/pegasus/policies/floor_v1.json",
            "tools/pegasus/policies/transport_v1.json",
            "tools/pegasus/policy.json",
        ],
    }


def test_accepts_committed_literal_with_exact_receipt() -> None:
    source = _source(
        "http://10.120.96.1:8080", "http://10.120.96.1:8080"
    )
    admission = _evaluate(source_env=source, policy_bytes=_COMMITTED_POLICY_BYTES)
    assert admission.env_dict() == {
        "http_proxy": "http://10.120.96.1:8080",
        "https_proxy": "http://10.120.96.1:8080",
    }
    assert admission.receipt.as_dict() == {
        "schema_version": "claude-transport-receipt/v1",
        "mode": "explicit-http-proxy-env",
        "site": "PEGASUS_COMPUTE",
        "admitted_env_keys": ["http_proxy", "https_proxy"],
        "endpoint_values": {
            "http_proxy": "http://10.120.96.1:8080",
            "https_proxy": "http://10.120.96.1:8080",
        },
        "endpoint_values_sha256": _COMMITTED_ENDPOINT_SHA256,
        "policy_path": "tools/pegasus/policies/transport_v1.json",
        "policy_sha256": _COMMITTED_POLICY_SHA256,
        "source_tls_trust_override_keys": [],
        "forwarded_tls_trust_override_keys": [],
        "pbs_jobid": "987654.pegasus",
    }


def test_accepts_distinct_http_https_synthetic_vector() -> None:
    admission = _evaluate()
    assert admission.env_dict() == {
        "http_proxy": "http://proxy-a.example:18080",
        "https_proxy": "http://proxy-b.example:18443",
    }
    receipt = admission.receipt.as_dict()
    assert receipt["endpoint_values"] == {
        "http_proxy": "http://proxy-a.example:18080",
        "https_proxy": "http://proxy-b.example:18443",
    }
    assert receipt["endpoint_values_sha256"] == _DISTINCT_ENDPOINT_SHA256


def test_m5_leaf_preserves_distinct_http_and_https_values() -> None:
    admission = _evaluate()
    assert admission.transport_env == (
        ("http_proxy", "http://proxy-a.example:18080"),
        ("https_proxy", "http://proxy-b.example:18443"),
    )


def test_p3_accepts_when_metered_transport_keys_are_absent() -> None:
    source = _source()
    assert all(key not in source for key in _METERED_TRANSPORT_KEYS)
    assert _evaluate(source_env=source).receipt.as_dict() == _VALID_RECEIPT


def test_reverse_endpoint_key_order_uses_literal_canonical_digest() -> None:
    source = _source(
        "http://reverse-http.example:28080",
        "http://reverse-https.example:28443",
    )
    receipt = _evaluate(
        source_env=source, policy_bytes=_REVERSE_POLICY_BYTES
    ).receipt.as_dict()
    assert list(receipt["endpoint_values"]) == ["https_proxy", "http_proxy"]
    assert receipt["endpoint_values_sha256"] == _REVERSE_ENDPOINT_SHA256


def test_rejects_non_compute_sites_and_wrapper_orders_io(tmp_path: Path) -> None:
    for site in ("PEGASUS_LOGIN", "PEGASUS_SUSPECT", "OTHER", ""):
        _expect_transport_error(
            "site-not-compute", lambda site=site: _evaluate(site=site)
        )

    original = T.site_policy.current_site
    calls = []
    try:
        T.site_policy.current_site = lambda: calls.append("site") or "PEGASUS_LOGIN"
        missing_root = tmp_path / "missing-policy-root"
        missing_root.mkdir()
        _expect_transport_error(
            "site-not-compute",
            lambda: T.admit_claude_transport(
                source_env=_source(), repository_root=missing_root
            ),
        )
        assert calls == ["site"]
    finally:
        T.site_policy.current_site = original

    tree = ast.parse(Path(T.__file__).read_text(encoding="utf-8"))
    wrapper = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "admit_claude_transport"
    )
    current_calls = [
        node for node in ast.walk(wrapper)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "current_site"
    ]
    policy_reads = [
        node for node in ast.walk(wrapper)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_read_policy_bytes"
    ]
    assert len(current_calls) == 1
    assert len(policy_reads) == 1
    assert current_calls[0].lineno < policy_reads[0].lineno


def test_transport_import_surface_has_no_site_or_policy_io() -> None:
    tree = ast.parse(Path(T.__file__).read_text(encoding="utf-8"))
    executable_top_level = [
        node for node in tree.body
        if not isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Import, ast.ImportFrom))
    ]
    forbidden = []
    for statement in executable_top_level:
        for node in ast.walk(statement):
            if not isinstance(node, ast.Call):
                continue
            if isinstance(node.func, ast.Attribute) and node.func.attr in {
                "current_site", "read_bytes", "open", "lstat",
            }:
                forbidden.append(node.func.attr)
            if isinstance(node.func, ast.Name) and node.func.id in {
                "open", "_read_policy_bytes", "admit_claude_transport",
            }:
                forbidden.append(node.func.id)
    assert forbidden == []


def test_rejects_pbs_job_witness_failures_without_disclosure() -> None:
    for bad in (None, "", 1, True):
        source = _source()
        if bad is None:
            del source["PBS_JOBID"]
        else:
            source["PBS_JOBID"] = bad  # type: ignore[assignment]
        _expect_transport_error(
            "pbs-jobid-missing", lambda source=source: _evaluate(source_env=source)
        )


def test_pbs_jobid_grammar_matches_qualification_authority_exactly() -> None:
    assert T.PBS_JOBID_PATTERN == QSUB._JOB_ID_TEXT
    assert T._PBS_JOBID_RE.pattern == QSUB._JOB_ID.pattern
    assert COLLECTOR._JOB_ID.pattern == rf"(?:0:)?{T.PBS_JOBID_PATTERN}"
    for value in ("a", "987654.pegasus", "job_name-1", "x" * 256):
        assert T.is_valid_pbs_jobid(value)
        assert QSUB._JOB_ID.fullmatch(value) is not None
    for value in ("", ".job", "-job", "_job", "job:id", "job/id", 1, None):
        assert not T.is_valid_pbs_jobid(value)


def test_rejects_pbs_jobid_outside_strict_syntax_without_disclosure() -> None:
    for bad in (
        "job id",
        "job/123",
        "job:123",
        ".",
        ":",
        "credential-sentinel@host",
        "\n",
    ):
        source = _source()
        source["PBS_JOBID"] = bad
        _expect_transport_error(
            "pbs-jobid-invalid",
            lambda source=source: _evaluate(source_env=source),
            bad,
            "credential-sentinel",
        )


def test_rejects_each_tls_override_without_secret_disclosure() -> None:
    keys = (
        "SSL_CERT_FILE",
        "SSL_CERT_DIR",
        "REQUESTS_CA_BUNDLE",
        "CURL_CA_BUNDLE",
        "NODE_EXTRA_CA_CERTS",
        "NODE_TLS_REJECT_UNAUTHORIZED",
        "SSLKEYLOGFILE",
    )
    for key in keys:
        for value in ("", "credential-sentinel"):
            source = _source()
            source[key] = value
            _expect_transport_error(
                "tls-override-present",
                lambda source=source: _evaluate(source_env=source),
                "credential-sentinel",
            )


def test_rejects_each_unadmitted_proxy_name_without_disclosure() -> None:
    keys = (
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "NO_PROXY",
        "ALL_PROXY",
        "FTP_PROXY",
        "no_proxy",
        "all_proxy",
        "ftp_proxy",
    )
    for key in keys:
        source = _source()
        source[key] = "http://proxy-secret-sentinel.invalid:9999"
        _expect_transport_error(
            "proxy-key-unadmitted",
            lambda source=source: _evaluate(source_env=source),
            "proxy-secret-sentinel",
        )


def test_m16_rejects_each_metered_transport_key_by_presence() -> None:
    for key in _METERED_TRANSPORT_KEYS:
        for value in ("", "credential-sentinel"):
            source = _source()
            source[key] = value
            _expect_transport_error(
                "metered-transport-env-present",
                lambda source=source: _evaluate(source_env=source),
                "credential-sentinel",
            )


def test_env_preflight_wins_over_broken_policy_without_reader_call(
    tmp_path: Path,
) -> None:
    missing_root = tmp_path / "missing-policy-root"
    missing_root.mkdir()
    calls: list[Path] = []
    original_site = T.site_policy.current_site
    original_reader = T._read_policy_bytes
    try:
        T.site_policy.current_site = lambda: "PEGASUS_COMPUTE"

        def forbidden_reader(repository_root):
            calls.append(repository_root)
            raise AssertionError("policy reader must not be called")

        T._read_policy_bytes = forbidden_reader
        no_pbs = _source()
        del no_pbs["PBS_JOBID"]
        tls = _source()
        tls["SSL_CERT_FILE"] = "credential-sentinel"
        proxy = _source()
        proxy["HTTP_PROXY"] = "http://credential-sentinel.invalid:1"
        metered = _source()
        metered["ANTHROPIC_API_KEY"] = "credential-sentinel"
        cases = [
            ("source-env-type", None),
            ("pbs-jobid-missing", no_pbs),
            ("tls-override-present", tls),
            ("proxy-key-unadmitted", proxy),
            ("metered-transport-env-present", metered),
        ]
        for key in ("http_proxy", "https_proxy"):
            missing_pair = _source()
            del missing_pair[key]
            cases.append(("proxy-pair-missing", missing_pair))
            non_string_pair = _source()
            non_string_pair[key] = None  # type: ignore[assignment]
            cases.append(("proxy-pair-missing", non_string_pair))
        for code, source in cases:
            _expect_transport_error(
                code,
                lambda source=source: T.admit_claude_transport(
                    source_env=source,  # type: ignore[arg-type]
                    repository_root=missing_root,
                ),
                "credential-sentinel",
            )
        assert calls == []
    finally:
        T._read_policy_bytes = original_reader
        T.site_policy.current_site = original_site


def test_rejects_missing_non_string_and_drifted_required_pair() -> None:
    for key in ("http_proxy", "https_proxy"):
        source = _source()
        del source[key]
        _expect_transport_error(
            "proxy-pair-missing", lambda source=source: _evaluate(source_env=source)
        )
        for bad in (None, b"bytes", True, 1):
            source = _source()
            source[key] = bad  # type: ignore[assignment]
            _expect_transport_error(
                "proxy-pair-missing", lambda source=source: _evaluate(source_env=source)
            )

    for drift in (
        "http://proxy-a.example:18080/",
        " http://proxy-a.example:18080",
        "HTTP://proxy-a.example:18080",
        "http://proxy-a.example:18081",
        "http://credential-sentinel@proxy-a.example:18080",
    ):
        source = _source(http=drift)
        _expect_transport_error(
            "proxy-value-mismatch",
            lambda source=source: _evaluate(source_env=source),
            drift,
            "credential-sentinel",
        )


def test_rejects_source_and_policy_input_types() -> None:
    for bad in (None, [], "mapping", 1):
        _expect_transport_error(
            "source-env-type",
            lambda bad=bad: T.evaluate_transport_admission(
                source_env=bad,  # type: ignore[arg-type]
                policy_bytes=_DISTINCT_POLICY_BYTES,
                site="PEGASUS_COMPUTE",
            ),
        )
    for bad in (None, bytearray(_DISTINCT_POLICY_BYTES), "bytes"):
        _expect_transport_error(
            "policy-bytes-type",
            lambda bad=bad: T.evaluate_transport_admission(
                source_env=_source(),
                policy_bytes=bad,  # type: ignore[arg-type]
                site="PEGASUS_COMPUTE",
            ),
        )
    for bad in (None, 1, "tools/pegasus/policies/other.json"):
        _expect_transport_error(
            "policy-path",
            lambda bad=bad: T.evaluate_transport_admission(
                source_env=_source(),
                policy_bytes=_DISTINCT_POLICY_BYTES,
                site="PEGASUS_COMPUTE",
                policy_path=bad,  # type: ignore[arg-type]
            ),
        )


def test_rejects_malformed_duplicate_nonfinite_and_schema_policy() -> None:
    cases = [
        ("policy-utf8", b"\xff"),
        ("policy-json", b"{"),
        (
            "policy-duplicate-key",
            b'{"schema_version":"x","schema_version":"y"}',
        ),
        (
            "policy-json",
            _policy_with(
                '{"http_proxy":"http://proxy-a.example:18080",'
                '"https_proxy":"http://proxy-b.example:18443",'
                '"weight":NaN}'
            ),
        ),
        (
            "policy-json",
            _policy_with(
                '{"http_proxy":"http://proxy-a.example:18080",'
                '"https_proxy":"http://proxy-b.example:18443",'
                '"weight":Infinity}'
            ),
        ),
        ("policy-schema", b"[]"),
        (
            "policy-schema",
            _policy_with(
                '{"http_proxy":"http://proxy-a.example:18080",'
                '"https_proxy":"http://proxy-b.example:18443"}',
                top_extra=',"extra":true',
            ),
        ),
        (
            "policy-contract",
            _DISTINCT_POLICY_BYTES.replace(
                b"pegasus-claude-transport-policy/v1", b"wrong/v1"
            ),
        ),
        (
            "policy-contract",
            _DISTINCT_POLICY_BYTES.replace(b"PEGASUS_COMPUTE", b"OTHER"),
        ),
        (
            "policy-contract",
            _DISTINCT_POLICY_BYTES.replace(
                b"explicit-http-proxy-env", b"other-mode"
            ),
        ),
        ("policy-endpoint-shape", _policy_with("{}")),
        (
            "policy-endpoint-shape",
            _policy_with('{"http_proxy":"http://proxy-a.example:18080"}'),
        ),
        (
            "policy-endpoint-shape",
            _policy_with(
                '{"http_proxy":"http://proxy-a.example:18080",'
                '"https_proxy":"http://proxy-b.example:18443",'
                '"extra_proxy":"http://extra.example:1"}'
            ),
        ),
        (
            "policy-endpoint",
            _policy_with(
                '{"http_proxy":1,'
                '"https_proxy":"http://proxy-b.example:18443"}'
            ),
        ),
    ]
    for code, policy_bytes in cases:
        _expect_transport_error(
            code,
            lambda policy_bytes=policy_bytes: _evaluate(policy_bytes=policy_bytes),
        )


def test_rejects_every_policy_uri_forbidden_form_and_redacts_credentials() -> None:
    bad_values = (
        "https://proxy-a.example:18080",
        "http://proxy-a.example",
        "http://user:credential-sentinel@proxy-a.example:18080",
        "http://proxy-a.example:18080?q=credential-sentinel",
        "http://proxy-a.example:18080#credential-sentinel",
        "http://proxy-a.example:18080/forbidden-path",
        "http://proxy-a.example:18080/\ncredential-sentinel",
    )
    for bad in bad_values:
        policy = _policy_with(
            json.dumps(
                {
                    "http_proxy": bad,
                    "https_proxy": "http://proxy-b.example:18443",
                },
                separators=(",", ":"),
            )
        )
        source = _source(http=bad)
        _expect_transport_error(
            "policy-endpoint",
            lambda policy=policy, source=source: _evaluate(
                source_env=source, policy_bytes=policy
            ),
            bad,
            "credential-sentinel",
        )


def test_policy_surface_rejects_missing_symlink_nonregular_and_oversize(
    tmp_path: Path,
) -> None:
    _expect_transport_error(
        "repository-root-type",
        lambda: T._read_policy_bytes(str(tmp_path)),  # type: ignore[arg-type]
    )
    _expect_transport_error(
        "repository-root",
        lambda: T._read_policy_bytes(tmp_path / "missing"),
    )
    root_file = tmp_path / "root-file"
    root_file.write_bytes(b"x")
    _expect_transport_error("repository-root", lambda: T._read_policy_bytes(root_file))

    def target(root: Path) -> Path:
        path = root / "tools/pegasus/policies/transport_v1.json"
        path.parent.mkdir(parents=True)
        return path

    missing_root = tmp_path / "missing-policy"
    (missing_root / "tools/pegasus/policies").mkdir(parents=True)
    _expect_transport_error(
        "policy-surface", lambda: T._read_policy_bytes(missing_root)
    )

    final_link_root = tmp_path / "final-link"
    final_link = target(final_link_root)
    outside = tmp_path / "outside-policy.json"
    outside.write_bytes(_DISTINCT_POLICY_BYTES)
    final_link.symlink_to(outside)
    _expect_transport_error(
        "policy-surface", lambda: T._read_policy_bytes(final_link_root)
    )

    ancestor_root = tmp_path / "ancestor-link"
    ancestor_root.mkdir()
    outside_tools = tmp_path / "outside-tools"
    outside_policy = outside_tools / "pegasus/policies/transport_v1.json"
    outside_policy.parent.mkdir(parents=True)
    outside_policy.write_bytes(_DISTINCT_POLICY_BYTES)
    (ancestor_root / "tools").symlink_to(outside_tools, target_is_directory=True)
    _expect_transport_error(
        "policy-surface", lambda: T._read_policy_bytes(ancestor_root)
    )

    directory_root = tmp_path / "directory-final"
    target(directory_root).mkdir()
    _expect_transport_error(
        "policy-surface", lambda: T._read_policy_bytes(directory_root)
    )

    fifo_root = tmp_path / "fifo-final"
    fifo = target(fifo_root)
    os.mkfifo(fifo)
    _expect_transport_error("policy-surface", lambda: T._read_policy_bytes(fifo_root))

    exact_root = tmp_path / "exact-size"
    target(exact_root).write_bytes(b" " * 16_384)
    exact = T._read_policy_bytes(exact_root)
    assert len(exact) == 16_384
    oversize_root = tmp_path / "oversize"
    target(oversize_root).write_bytes(b"x" * 16_385)
    _expect_transport_error(
        "policy-too-large", lambda: T._read_policy_bytes(oversize_root)
    )

    read_once_root = tmp_path / "read-once"
    target(read_once_root).write_bytes(_DISTINCT_POLICY_BYTES)
    read_calls = []

    def recording_read(fd, size):
        read_calls.append((fd, size))
        return os.read(fd, size)

    assert T._read_policy_bytes(
        read_once_root, read_fd=recording_read
    ) == _DISTINCT_POLICY_BYTES
    assert len(read_calls) == 1
    assert read_calls[0][1] == 16_385

    def failing_open(path, flags):
        del path, flags
        raise PermissionError("credential-sentinel")

    _expect_transport_error(
        "policy-read",
        lambda: T._read_policy_bytes(read_once_root, open_fd=failing_open),
        "credential-sentinel",
    )


def test_m12_pre_open_rejects_policy_symlink_before_open(tmp_path: Path) -> None:
    root = tmp_path / "pre-open"
    policy = root / "tools/pegasus/policies/transport_v1.json"
    policy.parent.mkdir(parents=True)
    outside = tmp_path / "credential-sentinel-outside.json"
    outside.write_bytes(_DISTINCT_POLICY_BYTES)
    policy.symlink_to(outside)
    open_calls = []

    def forbidden_open(path, flags):
        open_calls.append((path, flags))
        raise AssertionError("pre-open gate must reject before open")

    _expect_transport_error(
        "policy-surface",
        lambda: T._read_policy_bytes(root, open_fd=forbidden_open),
        "credential-sentinel",
    )
    assert open_calls == []


def test_m12_post_open_rejects_controlled_regular_file_swap(
    tmp_path: Path,
) -> None:
    root = tmp_path / "post-open"
    policy = root / "tools/pegasus/policies/transport_v1.json"
    policy.parent.mkdir(parents=True)
    policy.write_bytes(_DISTINCT_POLICY_BYTES)
    replacement = tmp_path / "credential-sentinel-replacement.json"
    replacement.write_bytes(_COMMITTED_POLICY_BYTES)
    read_calls = []

    def swapped_open(path, flags):
        assert path == policy
        return os.open(replacement, flags)

    def forbidden_read(fd, size):
        read_calls.append((fd, size))
        raise AssertionError("post-open identity gate must reject before read")

    _expect_transport_error(
        "policy-surface",
        lambda: T._read_policy_bytes(
            root, open_fd=swapped_open, read_fd=forbidden_read
        ),
        "credential-sentinel",
    )
    assert read_calls == []


def test_trial_receipt_gate_rejects_missing_extra_type_and_hash_mismatch() -> None:
    assert A._validate_transport_receipt(_copy_receipt()) == _VALID_RECEIPT
    mutants = []
    missing = _copy_receipt()
    del missing["site"]
    mutants.append(missing)
    extra = _copy_receipt()
    extra["extra"] = True
    mutants.append(extra)
    wrong_type = _copy_receipt()
    wrong_type["admitted_env_keys"] = ("http_proxy", "https_proxy")
    mutants.append(wrong_type)
    wrong_scalar_type = _copy_receipt()
    wrong_scalar_type["site"] = 1
    mutants.append(wrong_scalar_type)
    nested_extra = _copy_receipt()
    nested_extra["endpoint_values"]["extra"] = "http://extra.example:1"
    mutants.append(nested_extra)
    bad_endpoint_hash = _copy_receipt()
    bad_endpoint_hash["endpoint_values_sha256"] = "0" * 64
    mutants.append(bad_endpoint_hash)
    bad_policy_hash = _copy_receipt()
    bad_policy_hash["policy_sha256"] = "g" * 64
    mutants.append(bad_policy_hash)
    empty_job = _copy_receipt()
    empty_job["pbs_jobid"] = ""
    mutants.append(empty_job)
    malformed_job = _copy_receipt()
    malformed_job["pbs_jobid"] = "credential-sentinel/job"
    mutants.append(malformed_job)
    for mutant in mutants:
        try:
            A._validate_transport_receipt(mutant)
        except A.AutonomousTrialError as exc:
            assert "proxy-a.example" not in str(exc)
            assert "987654.pegasus" not in str(exc)
        else:
            raise AssertionError(f"receipt mutant を拒否しなかった: {mutant}")

    valid_but_different = _copy_receipt()
    valid_but_different["policy_sha256"] = "2" * 64
    try:
        A._validate_transport_receipt(
            valid_but_different, expected=_VALID_RECEIPT
        )
    except A.AutonomousTrialError:
        pass
    else:
        raise AssertionError("run-level policy hash mismatch を拒否しなかった")


def test_cli_flag_default_and_all_four_wiring_links_are_explicit() -> None:
    assert inspect.signature(A.run_trial).parameters[
        "allow_pegasus_compute_transport"
    ].default is False
    assert inspect.signature(ClaudeProjectedRoleProvider).parameters[
        "allow_pegasus_compute_transport"
    ].default is False
    tree = ast.parse(Path(A.__file__).read_text(encoding="utf-8"))

    flag_calls = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "add_argument"
        and any(
            isinstance(argument, ast.Constant)
            and argument.value == "--allow-pegasus-compute-transport"
            for argument in node.args
        )
    ]
    assert len(flag_calls) == 1
    keywords = {keyword.arg: keyword.value for keyword in flag_calls[0].keywords}
    assert isinstance(keywords["action"], ast.Constant)
    assert keywords["action"].value == "store_true"
    assert isinstance(keywords["default"], ast.Constant)
    assert keywords["default"].value is False

    def function(name: str) -> ast.FunctionDef:
        return next(
            node for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == name
        )

    main_calls = [
        node for node in ast.walk(function("main"))
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name) and node.func.id == "run_trial"
    ]
    assert len(main_calls) == 1
    main_kw = {keyword.arg: keyword.value for keyword in main_calls[0].keywords}
    assert isinstance(main_kw["allow_pegasus_compute_transport"], ast.Attribute)
    assert main_kw["allow_pegasus_compute_transport"].attr == (
        "allow_pegasus_compute_transport"
    )

    provider_set_calls = [
        node for node in ast.walk(function("run_trial"))
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name) and node.func.id == "_provider_set"
    ]
    assert len(provider_set_calls) == 1
    provider_set_kw = {
        keyword.arg: keyword.value for keyword in provider_set_calls[0].keywords
    }
    assert isinstance(
        provider_set_kw["allow_pegasus_compute_transport"], ast.Name
    )
    assert provider_set_kw["allow_pegasus_compute_transport"].id == (
        "allow_pegasus_compute_transport"
    )

    factory_calls = [
        node for node in ast.walk(function("_provider_set"))
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "provider_factory"
    ]
    assert len(factory_calls) == 1
    factory_kw = {keyword.arg: keyword.value for keyword in factory_calls[0].keywords}
    assert isinstance(factory_kw["allow_pegasus_compute_transport"], ast.Name)
    assert factory_kw["allow_pegasus_compute_transport"].id == (
        "allow_pegasus_compute_transport"
    )


def test_provider_set_passes_one_immutable_receipt_object_to_four_roles(
    tmp_path: Path,
) -> None:
    admission = _evaluate()
    calls = []

    class FakeProvider:
        def __init__(self, **kwargs):
            calls.append(kwargs)

        def close(self):
            return None

    providers = A._provider_set(
        kind="claude-headless",
        run_root=tmp_path / "run",
        executable="claude",
        allow_pegasus_compute_transport=True,
        transport_admission=admission,
        source_env=_source(),
        projected_provider_factory=FakeProvider,
    )
    assert list(providers) == ["planner", "coder", "auditor", "critic"]
    assert len(calls) == 4
    assert all(call["allow_pegasus_compute_transport"] is True for call in calls)
    assert all(call["transport_admission"] is admission for call in calls)
    assert all(call["transport_admission"].receipt is admission.receipt for call in calls)


def test_m10_real_providers_share_run_admission_without_resolving_per_role(
    tmp_path: Path,
) -> None:
    """M10': production providers must not re-enter the resolver per role."""
    admission = _evaluate()
    resolver_calls = []
    original_resolver = A.admit_claude_transport
    original_which = CP.shutil.which
    providers = {}

    def per_role_resolver(*, source_env, repository_root):
        resolver_calls.append((source_env, repository_root))
        return _evaluate()

    try:
        A.admit_claude_transport = per_role_resolver
        CP.shutil.which = lambda executable: sys.executable
        providers = A._provider_set(
            kind="claude-headless",
            run_root=tmp_path / "run",
            executable="claude",
            allow_pegasus_compute_transport=True,
            transport_admission=admission,
            source_env=_source(),
        )
        assert list(providers) == ["planner", "coder", "auditor", "critic"]
        assert all(
            isinstance(provider, ClaudeProjectedRoleProvider)
            for provider in providers.values()
        )
        assert all(
            provider.transport_receipt is admission.receipt
            for provider in providers.values()
        )
        assert resolver_calls == []
    finally:
        A._close_owned_providers(providers)
        CP.shutil.which = original_which
        A.admit_claude_transport = original_resolver


def _role_file(path: Path) -> Path:
    path.write_text(
        "---\n"
        "name: fixture-auditor\n"
        "description: fixture\n"
        'tools: ["Read"]\n'
        "model: opus\n"
        "effort: high\n"
        "---\n"
        "Return JSON only.\n",
        encoding="utf-8",
    )
    return path


def _executable(path: Path) -> Path:
    path.write_bytes(b"#!/bin/sh\nexit 0\n")
    path.chmod(0o700)
    return path


def _subprocess_shim(path: Path) -> Path:
    path.write_text(
        f"#!{sys.executable}\n"
        "import json, os\n"
        "keys = ['http_proxy', 'https_proxy', 'HTTP_PROXY', "
        "'SSL_CERT_FILE', 'SECRET']\n"
        "observed = {key: os.environ.get(key) for key in keys}\n"
        "envelope = {\n"
        "  'type': 'result', 'subtype': 'success', 'is_error': False,\n"
        "  'num_turns': 1, 'permission_denials': [],\n"
        "  'result': json.dumps(observed, sort_keys=True),\n"
        "  'session_id': 'real-subprocess-session',\n"
        "  'modelUsage': {\n"
        "    'claude-opus-4-6': {'inputTokens': 3, 'outputTokens': 2}\n"
        "  },\n"
        "  'usage': {'server_tool_use': {'web_search_requests': 0}},\n"
        "}\n"
        "print(json.dumps(envelope, separators=(',', ':')))\n",
        encoding="utf-8",
    )
    path.chmod(0o700)
    return path


def _role_subprocess_shim(path: Path) -> Path:
    path.write_text(
        f"#!{sys.executable}\n"
        "import json, sys\n"
        "payload = json.loads(sys.stdin.buffer.read())\n"
        "if 'current_perf' in payload:\n"
        "  role = 'planner'\n"
        "  result = {'proposal': {'axis': 'silo-backoff-trigger-gating', "
        "'direction': 'increase', 'magnitude': 'small', "
        "'justification': 'wrapper fixture', 'uncertainty': 'fixture'}}\n"
        "elif 'gating_spec' in payload:\n"
        "  role = 'coder'\n"
        "  result = {'proposal': {'axis': 'silo-backoff-trigger-gating', "
        "'wire': '11111', "
        "'justification': 'wrapper fixture', 'confidence': 'low'}}\n"
        "elif 'working_diff' in payload:\n"
        "  role = 'auditor'\n"
        "  result = {'verdict': 'pass', 'diff_digest': payload['diff_digest'], "
        "'violations': [], 'nits': [], 'proposed_tests': [], "
        "'uncertainty': 'fixture'}\n"
        "else:\n"
        "  role = 'critic'\n"
        "  result = {'attribution': 'fixture', 'recommend': 'stop', "
        "'avoid': 'overclaim', 'uncertainty': 'fixture', "
        "'reverse_recommended': False}\n"
        "envelope = {\n"
        "  'type': 'result', 'subtype': 'success', 'is_error': False,\n"
        "  'num_turns': 1, 'permission_denials': [],\n"
        "  'result': json.dumps(result, separators=(',', ':')),\n"
        "  'session_id': 'wrapper-' + role,\n"
        "  'modelUsage': {\n"
        "    'claude-opus-4-6': {'inputTokens': 3, 'outputTokens': 2}\n"
        "  },\n"
        "  'usage': {'server_tool_use': {'web_search_requests': 0}},\n"
        "}\n"
        "print(json.dumps(envelope, separators=(',', ':')))\n",
        encoding="utf-8",
    )
    path.chmod(0o700)
    return path


def _envelope() -> bytes:
    return json.dumps({
        "type": "result",
        "subtype": "success",
        "is_error": False,
        "num_turns": 1,
        "permission_denials": [],
        "result": '{"ok":true}',
        "session_id": "fresh-session-transport",
        "modelUsage": {
            "claude-opus-4-6": {"inputTokens": 3, "outputTokens": 2},
        },
        "usage": {"server_tool_use": {"web_search_requests": 0}},
    }, separators=(",", ":")).encode()


class _Runner:
    def __init__(self):
        self.calls = []

    def __call__(self, argv, **kwargs):
        self.calls.append((argv, kwargs))
        return SimpleNamespace(returncode=0, stdout=_envelope(), stderr=b"")


def test_projected_provider_default_and_opt_in_env_provenance_boundaries(
    tmp_path: Path,
) -> None:
    default_runner = _Runner()
    default = ClaudeProjectedRoleProvider(
        artifact_root=tmp_path / "default-artifacts",
        role_file=_role_file(tmp_path / "default-role.md"),
        role_name="fixture-auditor",
        mediated_contract="Return JSON only.",
        repository_root=_ROOT,
        executable=_executable(tmp_path / "default-claude"),
        runner=default_runner,
        environ={"HOME": "/fixture/home", "SECRET": "not-forwarded"},
    )
    try:
        response = default.invoke(invocation_id="default.auditor", payload={"x": 1})
        assert default_runner.calls[0][1]["env"] == {"HOME": "/fixture/home"}
        assert "transport_receipt" not in response.provenance
    finally:
        default.close()

    admission = _evaluate()
    opt_runner = _Runner()
    source = _source()
    source["SECRET"] = "not-forwarded"
    opted = ClaudeProjectedRoleProvider(
        artifact_root=tmp_path / "opt-artifacts",
        role_file=_role_file(tmp_path / "opt-role.md"),
        role_name="fixture-auditor",
        mediated_contract="Return JSON only.",
        repository_root=_ROOT,
        executable=_executable(tmp_path / "opt-claude"),
        runner=opt_runner,
        environ=source,
        allow_pegasus_compute_transport=True,
        transport_admission=admission,
    )
    try:
        response = opted.invoke(invocation_id="opt.auditor", payload={"x": 1})
        assert opt_runner.calls[0][1]["env"] == {
            "HOME": "/fixture/home",
            "http_proxy": "http://proxy-a.example:18080",
            "https_proxy": "http://proxy-b.example:18443",
        }
        assert response.provenance["transport_receipt"] == _VALID_RECEIPT
    finally:
        opted.close()


def test_projected_provider_rejects_flag_types_and_snapshot_drift(
    tmp_path: Path,
) -> None:
    base = {
        "artifact_root": tmp_path / "artifacts",
        "role_file": _role_file(tmp_path / "role.md"),
        "role_name": "fixture-auditor",
        "mediated_contract": "Return JSON only.",
        "repository_root": _ROOT,
        "executable": _executable(tmp_path / "claude"),
        "environ": _source(),
    }
    for bad in (1, "true", None):
        try:
            ClaudeProjectedRoleProvider(
                **base, allow_pegasus_compute_transport=bad  # type: ignore[arg-type]
            )
        except PredictionRunnerError:
            pass
        else:
            raise AssertionError(f"bool でない opt-in を受理した: {bad!r}")
    admission = _evaluate()
    drifted = _source(http="http://credential-sentinel.invalid:18080")
    try:
        ClaudeProjectedRoleProvider(
            **{**base, "artifact_root": tmp_path / "drift-artifacts", "environ": drifted},
            allow_pegasus_compute_transport=True,
            transport_admission=admission,
        )
    except PredictionRunnerError as exc:
        assert "credential-sentinel" not in str(exc)
        assert drifted["http_proxy"] not in str(exc)
    else:
        raise AssertionError("admission/source env drift を受理した")


def test_m5_provider_real_subprocess_preserves_distinct_admitted_pair(
    tmp_path: Path,
) -> None:
    admission = _evaluate()
    source = _source()
    source["SECRET"] = "not-forwarded"
    provider = ClaudeProjectedRoleProvider(
        artifact_root=tmp_path / "artifacts",
        role_file=_role_file(tmp_path / "role.md"),
        role_name="fixture-auditor",
        mediated_contract="Return JSON only.",
        repository_root=_ROOT,
        executable=_subprocess_shim(tmp_path / "claude-shim"),
        environ=source,
        allow_pegasus_compute_transport=True,
        transport_admission=admission,
    )
    try:
        response = provider.invoke(invocation_id="real.opted", payload={"x": 1})
        assert json.loads(response.raw_response) == {
            "HTTP_PROXY": None,
            "SECRET": None,
            "SSL_CERT_FILE": None,
            "http_proxy": "http://proxy-a.example:18080",
            "https_proxy": "http://proxy-b.example:18443",
        }
        assert response.provenance["transport_receipt"] == _VALID_RECEIPT
    finally:
        provider.close()


def test_default_provider_real_subprocess_has_no_transport_fields(
    tmp_path: Path,
) -> None:
    provider = ClaudeProjectedRoleProvider(
        artifact_root=tmp_path / "default-artifacts",
        role_file=_role_file(tmp_path / "default-role.md"),
        role_name="fixture-auditor",
        mediated_contract="Return JSON only.",
        repository_root=_ROOT,
        executable=_subprocess_shim(tmp_path / "default-claude-shim"),
        environ={
            "HOME": "/fixture/home",
            "http_proxy": "http://ambient.invalid:1",
            "https_proxy": "http://ambient.invalid:2",
            "HTTP_PROXY": "http://ambient.invalid:3",
            "SSL_CERT_FILE": "/ambient/ca",
            "SECRET": "not-forwarded",
        },
    )
    try:
        response = provider.invoke(invocation_id="real.default", payload={"x": 1})
        assert json.loads(response.raw_response) == {
            "HTTP_PROXY": None,
            "SECRET": None,
            "SSL_CERT_FILE": None,
            "http_proxy": None,
            "https_proxy": None,
        }
        assert "transport_receipt" not in response.provenance
    finally:
        provider.close()


def _assert_no_transport_fields(value) -> None:
    if isinstance(value, dict):
        assert all(not str(key).startswith("transport") for key in value)
        for nested in value.values():
            _assert_no_transport_fields(nested)
    elif isinstance(value, list):
        for nested in value:
            _assert_no_transport_fields(nested)


def _append_run_start(
    journal: A.AttemptJournal,
    *,
    trial_id: str,
    provider: str,
    workloads: list[str],
    generations: int,
    max_wall_s: int,
    do_build: bool = False,
) -> None:
    journal.append({
        "event": "run-start",
        "schema_version": A.SCHEMA_VERSION,
        "trial_id": trial_id,
        "provider": provider,
        "workloads": workloads,
        "generation_budget_per_workload": generations,
        "max_wall_s": max_wall_s,
        "do_build": do_build,
        "performance_early_stop": False,
        "scientific_claim": False,
    })


def _append_transport_preamble(
    journal: A.AttemptJournal,
    *,
    receipt: dict,
    trial_id: str,
    workloads: list[str],
    generations: int,
    max_wall_s: int,
) -> None:
    journal.append({
        "event": "transport-admission",
        "transport_receipt": receipt,
    })
    _append_run_start(
        journal,
        trial_id=trial_id,
        provider="claude-headless",
        workloads=workloads,
        generations=generations,
        max_wall_s=max_wall_s,
    )


def _p1_normalized_artifact_bytes(
    *, run_root: Path, report: dict, journal_events: list[dict]
) -> tuple[bytes, bytes]:
    """P1 の 2 run で次の明示的な揮発 field だけを正規化する。

    - ``attempts[].raw_response_path``: role 出力先なので run_root が異なる。
    - ``attempts[run-finish].report``: report 出力先なので run_root が異なる。
    - ``report.attempt_journal``: journal 出力先なので run_root が異なる。
    - ``report.cells[].campaign_id``: run_root 由来の config hash 接尾辞が異なる。
    - ``report.cells[].campaign_root``: run_root と上記 campaign_id の両方を含む。
    - ``report.cells[].generations[].roles.*.raw_response_path``: journal の run 固有 path を複製する。
    - ``report.attempt_journal_sha256``: run 固有 path を含む journal bytes の digest である。
    """
    root_text = str(run_root)

    def normalize_run_path(value: object) -> str:
        assert isinstance(value, str)
        assert value.startswith(root_text + os.sep)
        return "<RUN_ROOT>" + value[len(root_text):]

    normalized_events = json.loads(json.dumps(journal_events))
    for event in normalized_events:
        if "raw_response_path" in event:
            event["raw_response_path"] = normalize_run_path(
                event["raw_response_path"]
            )
        if event.get("event") == "run-finish":
            event["report"] = normalize_run_path(event["report"])
    journal_bytes = b"".join(
        json.dumps(
            event,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8") + b"\n"
        for event in normalized_events
    )

    normalized_report = json.loads(json.dumps(report))
    normalized_report["attempt_journal"] = normalize_run_path(
        normalized_report["attempt_journal"]
    )
    for cell in normalized_report["cells"]:
        campaign_id = cell["campaign_id"]
        assert isinstance(campaign_id, str)
        campaign_prefix, separator, hash_suffix = campaign_id.rpartition("-")
        assert separator == "-"
        assert len(hash_suffix) == 8
        assert all(character in "0123456789abcdef" for character in hash_suffix)
        normalized_campaign_id = campaign_prefix + "-<RUN_ROOT_HASH>"
        assert cell["campaign_root"] == str(
            run_root / "campaigns" / campaign_id
        )
        cell["campaign_id"] = normalized_campaign_id
        cell["campaign_root"] = (
            "<RUN_ROOT>/campaigns/" + normalized_campaign_id
        )
        for generation in cell["generations"]:
            for role_event in generation["roles"].values():
                if "raw_response_path" in role_event:
                    role_event["raw_response_path"] = normalize_run_path(
                        role_event["raw_response_path"]
                    )
    original_journal_sha256 = normalized_report["attempt_journal_sha256"]
    assert isinstance(original_journal_sha256, str)
    assert len(original_journal_sha256) == 64
    assert all(
        character in "0123456789abcdef"
        for character in original_journal_sha256
    )
    normalized_report["attempt_journal_sha256"] = hashlib.sha256(
        journal_bytes
    ).hexdigest()
    report_bytes = (
        json.dumps(
            normalized_report,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
    return journal_bytes, report_bytes


def test_p1_flag_omitted_run_trial_has_no_transport_io_or_fields(
    tmp_path: Path,
) -> None:
    calls = []
    original_admit = A.admit_claude_transport
    original_site = T.site_policy.current_site
    original_reader = T._read_policy_bytes
    original_now = A._now_iso
    original_provider_now = CP._now_iso
    original_monotonic = A.time.monotonic
    original_drive = A.trigger.drive_iteration
    original_preview = A._preview

    def forbidden(name):
        def call(*args, **kwargs):
            calls.append((name, args, kwargs))
            raise AssertionError(f"flag-off transport I/O: {name}")

        return call

    artifacts = []
    try:
        A.admit_claude_transport = forbidden("admit")
        T.site_policy.current_site = forbidden("site")
        T._read_policy_bytes = forbidden("policy")
        A._now_iso = lambda: "2026-08-01T00:00:00+09:00"
        CP._now_iso = lambda: "2026-08-01T00:00:00+09:00"
        A.time.monotonic = lambda: 0.0
        A.trigger.drive_iteration = _dry_drive
        A._preview = _dry_preview
        executable = str(_role_subprocess_shim(tmp_path / "p1-claude"))
        for index in range(2):
            run_root = tmp_path / f"p1-run-{index}"
            report = A.run_trial(
                trial_id="p1-flag-omitted",
                workloads=["ycsb-a"],
                generations=1,
                provider_kind="claude-headless",
                run_root=run_root,
                sub="/unused",
                do_build=False,
                max_wall_s=60,
                claude_executable=executable,
            )
            disk_report = json.loads((run_root / "report.json").read_bytes())
            journal_events = [
                json.loads(line)
                for line in (run_root / "attempts.jsonl").read_bytes().splitlines()
            ]
            assert report["status"] == "complete"
            _assert_no_transport_fields(disk_report)
            _assert_no_transport_fields(journal_events)
            artifacts.append(_p1_normalized_artifact_bytes(
                run_root=run_root,
                report=disk_report,
                journal_events=journal_events,
            ))
        assert calls == []
        assert artifacts[0] == artifacts[1]
    finally:
        A._preview = original_preview
        A.trigger.drive_iteration = original_drive
        A.time.monotonic = original_monotonic
        CP._now_iso = original_provider_now
        A._now_iso = original_now
        T._read_policy_bytes = original_reader
        T.site_policy.current_site = original_site
        A.admit_claude_transport = original_admit
    assert A.trigger.drive_iteration is original_drive
    assert A._preview is original_preview


def test_p2_flag_on_run_trial_admits_compute_wrapper_with_real_providers(
    tmp_path: Path,
) -> None:
    source = _source(
        "http://10.120.96.1:8080", "http://10.120.96.1:8080"
    )
    calls = {"site": 0, "policy": 0}
    original_environ = A.os.environ
    original_site = T.site_policy.current_site
    original_reader = T._read_policy_bytes
    original_now = A._now_iso
    original_monotonic = A.time.monotonic
    original_drive = A.trigger.drive_iteration
    original_preview = A._preview

    def counted_site():
        calls["site"] += 1
        return "PEGASUS_COMPUTE"

    def counted_reader(repository_root):
        calls["policy"] += 1
        return original_reader(repository_root)

    run_root = tmp_path / "p2-run"
    try:
        A.os.environ = source
        T.site_policy.current_site = counted_site
        T._read_policy_bytes = counted_reader
        A._now_iso = lambda: "2026-08-01T00:00:00+09:00"
        A.time.monotonic = lambda: 0.0
        A.trigger.drive_iteration = _dry_drive
        A._preview = _dry_preview
        report = A.run_trial(
            trial_id="p2-flag-on",
            workloads=["ycsb-a"],
            generations=1,
            provider_kind="claude-headless",
            run_root=run_root,
            sub="/unused",
            do_build=False,
            max_wall_s=60,
            claude_executable=str(_role_subprocess_shim(tmp_path / "p2-claude")),
            allow_pegasus_compute_transport=True,
        )
    finally:
        A._preview = original_preview
        A.trigger.drive_iteration = original_drive
        A.time.monotonic = original_monotonic
        A._now_iso = original_now
        T._read_policy_bytes = original_reader
        T.site_policy.current_site = original_site
        A.os.environ = original_environ
    assert A.trigger.drive_iteration is original_drive
    assert A._preview is original_preview
    assert calls == {"site": 1, "policy": 1}
    assert report["status"] == "complete"
    assert report["transport_receipt"]["pbs_jobid"] == "987654.pegasus"
    events = [
        json.loads(line)
        for line in (run_root / "attempts.jsonl").read_bytes().splitlines()
    ]
    assert events[0]["event"] == "transport-admission"
    assert events[0]["transport_receipt"] == report["transport_receipt"]
    role_events = [event for event in events if event.get("event") == "role-attempt"]
    assert [event["role"] for event in role_events] == [
        "planner", "coder", "auditor", "critic",
    ]
    auditor_event = role_events[2]
    assert auditor_event["event"] == "role-attempt"
    assert auditor_event["role"] == "auditor"
    assert auditor_event["status"] == "skipped"
    assert auditor_event["skip_reason"] == "machine-pre-audit-rejection"
    provider_role_events = [
        event for event in role_events if event["role"] != "auditor"
    ]
    assert [event["role"] for event in provider_role_events] == [
        "planner", "coder", "critic",
    ]
    assert all(
        event["provenance"]["transport_receipt"] == report["transport_receipt"]
        for event in provider_role_events
    )


class _RaisingProvider:
    artifact_root = None

    def __init__(self):
        self.calls = 0

    def invoke(self, *, invocation_id, payload):
        del invocation_id, payload
        self.calls += 1
        raise RuntimeError(
            "failed via http://proxy-a.example:18080 in job 987654.pegasus"
        )


class _ReceiptProvider:
    artifact_root = None

    def __init__(self, receipt):
        self.receipt = receipt
        self.calls = 0

    def invoke(self, *, invocation_id, payload):
        del invocation_id, payload
        self.calls += 1
        return ProviderResponse(
            raw_response=json.dumps({
                "proposal": {
                    "axis": "silo-backoff-trigger-gating",
                    "direction": "increase",
                    "magnitude": "small",
                    "justification": "fixture",
                    "uncertainty": "fixture",
                }
            }),
            provenance={"transport_receipt": self.receipt},
        )


class _DeepCopyReceiptFixtureProvider:
    artifact_root = None

    def __init__(self, role: str, receipt: dict) -> None:
        self.delegate = A.FixtureRoleProvider(role)
        self.receipt = json.loads(json.dumps(receipt))
        self.returned_receipts = []

    def invoke(self, *, invocation_id, payload):
        response = self.delegate.invoke(invocation_id=invocation_id, payload=payload)
        returned_receipt = json.loads(json.dumps(self.receipt))
        self.returned_receipts.append(returned_receipt)
        return ProviderResponse(
            raw_response=response.raw_response,
            provenance={
                **dict(response.provenance),
                "transport_receipt": returned_receipt,
            },
        )


def _dry_preview(*args, **kwargs):
    del args, kwargs
    return {
        "passed": False,
        "working_diff": "",
        "diff_digest": "0" * 64,
        "subtype": "fixture",
        "reason": "deterministic pre-audit stop",
        "forbidden_identifiers": [],
    }


def _dry_drive(*args, **kwargs):
    del args, kwargs
    return {
        "outcome": "rejected",
        "variant": "fixture-variant",
        "verdict": "fixture-verdict",
        "stop_reason": "continue",
        "iteration": 1,
        "ran": True,
        "records": {},
        "trigger_gate_binding_commitment": "b" * 64,
    }


def test_success_consumer_keeps_valid_receipt_in_journal_and_report(
    tmp_path: Path,
) -> None:
    run_receipt = _copy_receipt()
    providers = {
        role: _DeepCopyReceiptFixtureProvider(role, _copy_receipt())
        for role in ("planner", "coder", "auditor", "critic")
    }
    root = tmp_path / "success"
    root.mkdir()
    (root / "raw").mkdir()
    (root / "proposals").mkdir()
    journal = A.AttemptJournal(root / "attempts.jsonl")
    _append_transport_preamble(
        journal,
        receipt=run_receipt,
        trial_id="success-consumer",
        workloads=["ycsb-a"],
        generations=1,
        max_wall_s=60,
    )
    report = A._finish_trial(
        trial_id="success-consumer",
        selected=["ycsb-a"],
        generations=1,
        provider_kind="claude-headless",
        run_root=root,
        sub="/unused",
        do_build=False,
        cache_root="",
        max_wall_s=60,
        drive=_dry_drive,
        preview=_dry_preview,
        journal=journal,
        started="2026-08-01T00:00:00+09:00",
        started_monotonic=A.time.monotonic(),
        active_providers=providers,
        fatal_error=None,
        transport_receipt=run_receipt,
        build_context=_no_build_context(),
    )
    assert report["status"] == "complete"
    assert report["transport_receipt"] == _copy_receipt()
    assert providers["planner"].receipt is not run_receipt
    assert providers["planner"].receipt["endpoint_values"] is not run_receipt[
        "endpoint_values"
    ]
    assert providers["planner"].returned_receipts[0] is not run_receipt

    journal_events = [
        json.loads(line)
        for line in (root / "attempts.jsonl").read_bytes().decode("utf-8").splitlines()
    ]
    planner_journal = next(
        event for event in journal_events
        if event.get("event") == "role-attempt" and event.get("role") == "planner"
    )
    disk_report = json.loads((root / "report.json").read_bytes())
    planner_report = disk_report["cells"][0]["generations"][0]["roles"]["planner"]
    assert planner_journal["provenance"]["transport_receipt"] == _copy_receipt()
    assert planner_report["provenance"]["transport_receipt"] == _copy_receipt()
    assert planner_journal["provenance"]["transport_receipt"] is not (
        planner_report["provenance"]["transport_receipt"]
    )


def test_invoke_consumer_rejects_missing_extra_and_hash_receipts(
    tmp_path: Path,
) -> None:
    mutants = []
    missing = _copy_receipt()
    del missing["policy_sha256"]
    mutants.append(missing)
    extra = _copy_receipt()
    extra["extra"] = "forbidden"
    mutants.append(extra)
    bad_hash = _copy_receipt()
    bad_hash["endpoint_values_sha256"] = "0" * 64
    mutants.append(bad_hash)
    drifted_policy = _copy_receipt()
    drifted_policy["policy_sha256"] = "2" * 64
    mutants.append(drifted_policy)
    for index, mutant in enumerate(mutants):
        journal = A.AttemptJournal(tmp_path / f"attempts-{index}.jsonl")
        parsed, event = A._invoke(
            role="planner",
            provider=_ReceiptProvider(mutant),
            invocation_id=f"ycsb-a.g1.planner-{index}",
            payload={"descriptor_binding": {"output_sha256": "a" * 64}},
            raw_root=tmp_path,
            journal=journal,
            workload="ycsb-a",
            generation=1,
            transport_receipt=_copy_receipt(),
        )
        assert parsed is None
        assert event["status"] == "invalid"
        assert event["error_type"] == "AutonomousTrialError"
        assert event["transport_receipt"] == _VALID_RECEIPT
        assert "proxy-a.example" not in event["error"]


def test_opt_out_rejects_forged_provider_transport_receipt(tmp_path: Path) -> None:
    forged = _copy_receipt()
    forged["policy_sha256"] = "f" * 64
    provider = _ReceiptProvider(forged)
    journal = A.AttemptJournal(tmp_path / "opt-out-forged.jsonl")
    parsed, event = A._invoke(
        role="planner",
        provider=provider,
        invocation_id="ycsb-a.g1.planner-forged",
        payload={"descriptor_binding": {"output_sha256": "a" * 64}},
        raw_root=tmp_path,
        journal=journal,
        workload="ycsb-a",
        generation=1,
        transport_receipt=None,
    )
    assert provider.calls == 1
    assert parsed is None
    assert event["status"] == "invalid"
    assert event["error_type"] == "AutonomousTrialError"
    assert "transport opt-out provenance" in event["error"]
    assert "transport_receipt" not in event
    assert "provenance" not in event


def test_m11_invalid_attempt_keeps_same_receipt(
    tmp_path: Path,
) -> None:
    journal = A.AttemptJournal(tmp_path / "invalid-attempts.jsonl")
    receipt = _copy_receipt()
    provider = _RaisingProvider()
    parsed, invalid = A._invoke(
        role="planner",
        provider=provider,
        invocation_id="ycsb-a.g1.planner",
        payload={"descriptor_binding": {"output_sha256": "a" * 64}},
        raw_root=tmp_path,
        journal=journal,
        workload="ycsb-a",
        generation=1,
        transport_receipt=receipt,
    )
    assert provider.calls == 1
    assert parsed is None
    assert invalid["status"] == "invalid"
    assert invalid["error_type"] == "RuntimeError"
    assert invalid["transport_receipt"] == receipt
    assert "proxy-a.example" not in invalid["error"]
    assert "987654.pegasus" not in invalid["error"]


def test_m11_provider_init_error_keeps_same_receipt(tmp_path: Path) -> None:
    journal = A.AttemptJournal(tmp_path / "init-attempts.jsonl")
    receipt = _copy_receipt()
    init = A._append_provider_init_error(
        journal=journal,
        fatal_error={
            "type": "PredictionRunnerError",
            "message": (
                "init failed at http://proxy-a.example:18080 "
                "in job 987654.pegasus"
            ),
        },
        transport_receipt=receipt,
    )
    assert init["event"] == "provider-init-error"
    assert init["type"] == "PredictionRunnerError"
    assert init["transport_receipt"] == receipt
    assert "proxy-a.example" not in init["message"]
    assert "987654.pegasus" not in init["message"]

    tree = ast.parse(Path(A.__file__).read_text(encoding="utf-8"))
    run_trial = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "run_trial"
    )
    init_calls = [
        node for node in ast.walk(run_trial)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_append_provider_init_error"
    ]
    assert len(init_calls) == 1
    keywords = {keyword.arg: keyword.value for keyword in init_calls[0].keywords}
    assert isinstance(keywords["transport_receipt"], ast.Name)
    assert keywords["transport_receipt"].id == "transport_receipt"


def test_m13_trial_error_redacts_endpoint_and_jobid(tmp_path: Path) -> None:
    receipt = _copy_receipt()
    journal = A.AttemptJournal(tmp_path / "redacted-attempts.jsonl")
    provider = _RaisingProvider()
    parsed, invalid = A._invoke(
        role="planner",
        provider=provider,
        invocation_id="ycsb-a.g1.planner-redaction",
        payload={"descriptor_binding": {"output_sha256": "a" * 64}},
        raw_root=tmp_path,
        journal=journal,
        workload="ycsb-a",
        generation=1,
        transport_receipt=receipt,
    )
    assert provider.calls == 1
    assert parsed is None
    assert invalid["error_type"] == "RuntimeError"
    assert "http://proxy-a.example:18080" not in invalid["error"]
    assert "987654.pegasus" not in invalid["error"]


def test_m13_leaf_error_never_discloses_proxy_value() -> None:
    sentinel = "http://credential-sentinel@proxy-a.example:18080"
    source = _source(http=sentinel)
    calls = []

    def evaluate_once():
        calls.append(1)
        return _evaluate(source_env=source)

    message = _expect_transport_error(
        "proxy-value-mismatch",
        evaluate_once,
        sentinel,
        "credential-sentinel",
    )
    assert calls == [1]
    assert "proxy endpoint が policy と一致しない" in message


def test_artifact_diagnostic_oserror_preserves_original_invalid_attempt(
    tmp_path: Path,
) -> None:
    artifact_root = tmp_path / "provider-artifacts"
    artifact_root.mkdir()
    (artifact_root / "payload_ycsb-a.g1.planner.json").write_bytes(b"payload")
    (artifact_root / "envelope_ycsb-a.g1.planner.json").write_bytes(b"envelope")

    class Provider:
        def __init__(self):
            self.artifact_root = artifact_root

        def invoke(self, *, invocation_id, payload):
            del invocation_id, payload
            raise RuntimeError("original-role-failure")

    original_read_bytes = Path.read_bytes
    original_is_file = Path.is_file

    def failing_diagnostic_is_file(path):
        if path.parent == artifact_root and path.name.startswith("payload_"):
            raise OSError("diagnostic-stat-failure")
        return original_is_file(path)

    def failing_diagnostic_read(path):
        if path.parent == artifact_root:
            raise OSError("diagnostic-io-failure")
        return original_read_bytes(path)

    journal = A.AttemptJournal(tmp_path / "diagnostic-attempts.jsonl")
    try:
        Path.is_file = failing_diagnostic_is_file
        Path.read_bytes = failing_diagnostic_read
        parsed, invalid = A._invoke(
            role="planner",
            provider=Provider(),
            invocation_id="ycsb-a.g1.planner",
            payload={"descriptor_binding": {"output_sha256": "a" * 64}},
            raw_root=tmp_path,
            journal=journal,
            workload="ycsb-a",
            generation=1,
            transport_receipt=_copy_receipt(),
        )
    finally:
        Path.read_bytes = original_read_bytes
        Path.is_file = original_is_file
    assert parsed is None
    assert invalid["status"] == "invalid"
    assert invalid["error_type"] == "RuntimeError"
    assert invalid["error"] == "original-role-failure"
    assert invalid["error_artifacts"] == {}
    assert invalid["transport_receipt"] == _VALID_RECEIPT


def test_terminal_events_keep_transport_receipt(tmp_path: Path) -> None:
    receipt = _copy_receipt()
    original_run_workload = A._run_workload
    original_monotonic = A.time.monotonic

    error_root = tmp_path / "supervisor-error"
    error_root.mkdir()
    error_journal = A.AttemptJournal(error_root / "attempts.jsonl")
    _append_transport_preamble(
        error_journal,
        receipt=receipt,
        trial_id="terminal-error",
        workloads=["ycsb-a"],
        generations=1,
        max_wall_s=60,
    )
    try:
        A._run_workload = lambda **kwargs: (_ for _ in ()).throw(
            RuntimeError("supervisor failure")
        )
        A._finish_trial(
            trial_id="terminal-error",
            selected=["ycsb-a"],
            generations=1,
            provider_kind="claude-headless",
            run_root=error_root,
            sub="/unused",
            do_build=False,
            cache_root="",
            max_wall_s=60,
            drive=lambda *args, **kwargs: {},
            preview=lambda *args, **kwargs: {},
            journal=error_journal,
            started="2026-08-01T00:00:00+09:00",
            started_monotonic=A.time.monotonic(),
            active_providers={},
            fatal_error=None,
            transport_receipt=receipt,
            build_context=_no_build_context(),
        )
    finally:
        A._run_workload = original_run_workload
    error_events = [
        json.loads(line)
        for line in (error_root / "attempts.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert [event["event"] for event in error_events] == [
        "transport-admission", "run-start", "supervisor-error", "run-finish"
    ]
    assert "transport_receipt" not in error_events[1]
    assert all(
        event["transport_receipt"] == receipt
        for event in (error_events[0], *error_events[2:])
    )

    outer_root = tmp_path / "outer-wall"
    outer_root.mkdir()
    outer_journal = A.AttemptJournal(outer_root / "attempts.jsonl")
    _append_transport_preamble(
        outer_journal,
        receipt=receipt,
        trial_id="terminal-outer-wall",
        workloads=["ycsb-a"],
        generations=1,
        max_wall_s=1,
    )
    try:
        A.time.monotonic = lambda: 2.0
        A._finish_trial(
            trial_id="terminal-outer-wall",
            selected=["ycsb-a"],
            generations=1,
            provider_kind="claude-headless",
            run_root=outer_root,
            sub="/unused",
            do_build=False,
            cache_root="",
            max_wall_s=1,
            drive=lambda *args, **kwargs: {},
            preview=lambda *args, **kwargs: {},
            journal=outer_journal,
            started="2026-08-01T00:00:00+09:00",
            started_monotonic=0.0,
            active_providers={},
            fatal_error=None,
            transport_receipt=receipt,
            build_context=_no_build_context(),
        )
    finally:
        A.time.monotonic = original_monotonic
    outer_events = [
        json.loads(line)
        for line in (outer_root / "attempts.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert [event["event"] for event in outer_events] == [
        "transport-admission", "run-start", "supervisor-wall-budget", "run-finish"
    ]
    assert "transport_receipt" not in outer_events[1]
    assert all(
        event["transport_receipt"] == receipt
        for event in (outer_events[0], *outer_events[2:])
    )

    inner_root = tmp_path / "inner-wall"
    inner_root.mkdir()
    inner_journal = A.AttemptJournal(inner_root / "attempts.jsonl")
    try:
        A.time.monotonic = lambda: 2.0
        cell = A._run_workload(
            workload="ycsb-a",
            generations=1,
            providers={},
            journal=inner_journal,
            run_root=inner_root,
            sub="/unused",
            do_build=False,
            cache_root="",
            trial_id="terminal-inner-wall",
            started_monotonic=0.0,
            max_wall_s=1,
            transport_receipt=receipt,
            build_context=_no_build_context(),
        )
    finally:
        A.time.monotonic = original_monotonic
    assert cell["stop_reason"] == "supervisor-wall-budget"
    inner_events = [
        json.loads(line)
        for line in (inner_root / "attempts.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert len(inner_events) == 1
    assert inner_events[0]["event"] == "supervisor-wall-budget"
    assert inner_events[0]["generation"] == 1
    assert inner_events[0]["transport_receipt"] == receipt


def test_opt_in_report_and_opt_out_report_field_boundaries(tmp_path: Path) -> None:
    receipt = _copy_receipt()
    opt_root = tmp_path / "opt"
    opt_root.mkdir()
    opt_journal = A.AttemptJournal(opt_root / "attempts.jsonl")
    _append_transport_preamble(
        opt_journal,
        receipt=receipt,
        trial_id="opt",
        workloads=["ycsb-a"],
        generations=1,
        max_wall_s=1,
    )
    opt_fatal_error = {"type": "FixtureError", "message": "stopped"}
    A._append_provider_init_error(
        journal=opt_journal,
        fatal_error=opt_fatal_error,
        transport_receipt=receipt,
    )
    opt_report = A._finish_trial(
        trial_id="opt",
        selected=["ycsb-a"],
        generations=1,
        provider_kind="claude-headless",
        run_root=opt_root,
        sub="/unused",
        do_build=False,
        cache_root="",
        max_wall_s=1,
        drive=lambda *args, **kwargs: {},
        preview=lambda *args, **kwargs: {},
        journal=opt_journal,
        started="2026-08-01T00:00:00+09:00",
        started_monotonic=0.0,
        active_providers={},
        fatal_error=opt_fatal_error,
        transport_receipt=receipt,
    )
    assert opt_report["transport_receipt"] == receipt

    default_root = tmp_path / "default"
    default_root.mkdir()
    default_journal = A.AttemptJournal(default_root / "attempts.jsonl")
    _append_run_start(
        default_journal,
        trial_id="default",
        provider="fixture",
        workloads=["ycsb-a"],
        generations=1,
        max_wall_s=1,
    )
    default_fatal_error = {"type": "FixtureError", "message": "stopped"}
    A._append_provider_init_error(
        journal=default_journal,
        fatal_error=default_fatal_error,
        transport_receipt=None,
    )
    default_report = A._finish_trial(
        trial_id="default",
        selected=["ycsb-a"],
        generations=1,
        provider_kind="fixture",
        run_root=default_root,
        sub="/unused",
        do_build=False,
        cache_root="",
        max_wall_s=1,
        drive=lambda *args, **kwargs: {},
        preview=lambda *args, **kwargs: {},
        journal=default_journal,
        started="2026-08-01T00:00:00+09:00",
        started_monotonic=0.0,
        active_providers={},
        fatal_error=default_fatal_error,
        transport_receipt=None,
    )
    assert "transport_receipt" not in default_report
    default_events = [
        json.loads(line)
        for line in (default_root / "attempts.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert all("transport_receipt" not in event for event in default_events)


def test_opt_out_source_contains_no_transport_io_calls() -> None:
    tree = ast.parse(Path(A.__file__).read_text(encoding="utf-8"))
    run_trial = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "run_trial"
    )
    admit_calls = [
        node for node in ast.walk(run_trial)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "admit_claude_transport"
    ]
    assert len(admit_calls) == 1
    enclosing_if = [
        node for node in ast.walk(run_trial)
        if isinstance(node, ast.If)
        and isinstance(node.test, ast.Name)
        and node.test.id == "allow_pegasus_compute_transport"
        and any(admit_calls[0] is child for child in ast.walk(node))
    ]
    assert len(enclosing_if) == 1


def _run() -> int:
    functions = [
        value for name, value in sorted(globals().items())
        if name.startswith("test_") and callable(value)
    ]
    passed = failed = 0
    for function in functions:
        temporary = None
        try:
            parameters = inspect.signature(function).parameters
            args = []
            if parameters:
                assert list(parameters) == ["tmp_path"]
                temporary = tempfile.TemporaryDirectory(prefix="test-claude-transport-")
                args = [Path(temporary.name)]
            function(*args)
            print(f"PASS {function.__name__}")
            passed += 1
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL {function.__name__}: {type(exc).__name__}: {exc}")
            failed += 1
        finally:
            if temporary is not None:
                temporary.cleanup()
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_run())
