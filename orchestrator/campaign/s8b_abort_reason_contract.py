# -*- coding: utf-8 -*-
"""8b oracle の issuer (driver) と verifier (report) が同一 leaf を参照する契約。

parser 分裂を構造的に排除するため、この module は stdlib 以外や他の campaign
module を import しない。
"""

BENCH_FAILED_ABORT_REASONS: frozenset[str] = frozenset({
    "bench-competing-tenant",
    "bench-no-throughput",
    "bench-cv-undefined",
})
