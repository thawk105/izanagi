# -*- coding: utf-8 -*-
"""8b oracle の issuer (driver) と verifier (report) が同一 leaf を参照する契約。

parser 分裂を構造的に排除するため、この module は stdlib 以外や他の campaign
module を import しない。

identity-error は現行 oracle driver 経路では発行されず、pipeline の
src_token=None 経路のみが発行するが、分類器契約として保持する。
"""

TIMEOUT_ABORT_REASONS: frozenset[str] = frozenset({"trace-timeout"})

BUILD_FAILED_ABORT_REASONS: frozenset[str] = frozenset({
    "build-error",
    "identity-error",
})

VERIFY_INCONCLUSIVE_ABORT_REASONS: frozenset[str] = frozenset({
    "trace-run-nonzero-exit",
    "trace-empty",
    "trace-no-abort-counts",
    "trace-no-commit-witness",
    "trace-batch-commits-unattributed",
    "trace-witness-unsupported-workload",
    "trace-parse-error",
    "verify-competing-tenant",
})

BENCH_FAILED_ABORT_REASONS: frozenset[str] = frozenset({
    "bench-competing-tenant",
    "bench-no-throughput",
    "bench-cv-undefined",
})
