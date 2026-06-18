# -*- coding: utf-8 -*-
"""TSC 周波数 (clocks_per_us, MHz) を実測する。

CCBench の `clocks_per_us` は runtime gflag で自動校正が無い (default 2100、
anatomy §6)。throughput[tps] は非依存だが backoff/epoch の実挙動は依存するので、
**毎 run 正しい値を渡す**のが calibrator の責務 (anatomy §6 残課題 3)。

authoritative な測り方 = rdtscp を CLOCK_MONOTONIC 区間で挟む (anatomy §6)。
Python から TSC は直接読めないので最小の C ヘルパを TMPDIR にビルドして実行する。
本ホストは constant_tsc + nonstop_tsc (invariant TSC) を確認済みなので、TSC は
コア周波数の上下と無関係に一定レートで進む = 1 回測れば足りる (複数回測って中央値)。
"""
from __future__ import annotations

import os
import shutil
import statistics
import subprocess
import tempfile
from typing import Optional

_C_SRC = r"""
#include <stdio.h>
#include <stdint.h>
#include <time.h>
#include <x86intrin.h>

static double now_s(void) {
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return (double)t.tv_sec + (double)t.tv_nsec / 1e9;
}

int main(int argc, char **argv) {
    double interval = (argc > 1) ? atof(argv[1]) : 0.3;
    unsigned aux;
    double a = now_s();
    uint64_t t0 = __rdtscp(&aux);
    while (now_s() - a < interval) { /* busy wait */ }
    uint64_t t1 = __rdtscp(&aux);
    double b = now_s();
    double secs = b - a;
    if (secs <= 0) return 1;
    printf("%.6f\n", (double)(t1 - t0) / (secs * 1e6));  /* MHz */
    return 0;
}
"""


def _build_helper(workdir: str) -> Optional[str]:
    cc = shutil.which("cc") or shutil.which("gcc")
    if cc is None:
        return None
    src = os.path.join(workdir, "tsc_probe.c")
    out = os.path.join(workdir, "tsc_probe")
    with open(src, "w") as f:
        f.write("#include <stdlib.h>\n" + _C_SRC)
    r = subprocess.run([cc, "-O2", "-o", out, src],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return None
    return out


def measure_clocks_per_us(rounds: int = 5, interval: float = 0.3) -> Optional[int]:
    """TSC 周波数を MHz 整数で返す。計測不能なら None。

    `rounds` 回測って中央値 → 整数 MHz に丸める (CCBench の gflag は整数)。
    """
    tmp = tempfile.mkdtemp(prefix="izanagi_tsc_")
    try:
        helper = _build_helper(tmp)
        if helper is None:
            return None
        vals = []
        for _ in range(rounds):
            r = subprocess.run([helper, str(interval)],
                               capture_output=True, text=True)
            if r.returncode == 0:
                try:
                    vals.append(float(r.stdout.strip()))
                except ValueError:
                    pass
        if not vals:
            return None
        return int(round(statistics.median(vals)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
