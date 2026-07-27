#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""[T-140] trace_*.log から commit 時 set-size 分布を集計する。

raw trace は AI の context に読ませず (D31)、この digest JSON だけを持ち帰る。
入力 = IZANAGI_TRACE_DIR (trace_<thid>.log 群、書式は include/trace.hh:
  C txid thid epoch tid / R txid key e t / W txid key op e t / X txid key reason)。
1 committed trx = 1 つの C 行に R*/W* が連続で続く (per-thread file、単一書き手)。

exit code: 0=OK / 2=usage / 3=構造エラー (txid 不一致・C 前の R/W・未知タグ) /
4=X 行検出 (lock violation — 壊れた run の分布を結果にしない) /
5=--expect-commits 不一致 (trace C 行数 != stdout commit_counts_)。

bnode の python3 は 3.9 (runbook §7) — 3.6+ 互換で書く (match 文等は使わない)。
"""
import glob
import json
import os
import sys


def percentile_from_hist(hist, total, q):
    """hist: {size(int): count} から q 分位点 (最近傍上側) を返す。"""
    if total == 0:
        return None
    need = q * total
    acc = 0
    for size in sorted(hist):
        acc += hist[size]
        if acc >= need:
            return size
    return max(hist)


def add(hist, size):
    hist[size] = hist.get(size, 0) + 1


def main(argv):
    if len(argv) < 3:
        sys.stderr.write(
            "usage: parse_trace.py TRACE_DIR OUT_JSON [--expect-commits N]\n")
        return 2
    trace_dir, out_json = argv[1], argv[2]
    expect_commits = None
    if len(argv) >= 5 and argv[3] == "--expect-commits":
        expect_commits = int(argv[4])

    files = sorted(glob.glob(os.path.join(trace_dir, "trace_*.log")))
    if not files:
        sys.stderr.write("no trace_*.log under %s\n" % trace_dir)
        return 3

    hist_r = {}
    hist_w = {}
    hist_t = {}
    n_commit = 0
    n_r_rows = 0
    n_w_rows = 0
    n_x_rows = 0
    structural_errors = []
    per_file_commits = {}
    sum_r = 0
    sum_w = 0

    for path in files:
        cur_txid = None
        cr = 0
        cw = 0
        fname = os.path.basename(path)
        commits_this_file = 0
        with open(path, "r") as f:
            for lineno, line in enumerate(f, 1):
                parts = line.split()
                if not parts:
                    continue
                tag = parts[0]
                if tag == "C":
                    if cur_txid is not None:
                        add(hist_r, cr)
                        add(hist_w, cw)
                        add(hist_t, cr + cw)
                        sum_r += cr
                        sum_w += cw
                    cur_txid = parts[1]
                    cr = 0
                    cw = 0
                    n_commit += 1
                    commits_this_file += 1
                elif tag == "R" or tag == "W":
                    if cur_txid is None or parts[1] != cur_txid:
                        if len(structural_errors) < 20:
                            structural_errors.append(
                                "%s:%d: %s row txid=%s outside block txid=%s"
                                % (fname, lineno, tag, parts[1], cur_txid))
                        else:
                            structural_errors.append("...")
                            break
                    elif tag == "R":
                        cr += 1
                        n_r_rows += 1
                    else:
                        cw += 1
                        n_w_rows += 1
                elif tag == "X":
                    n_x_rows += 1
                else:
                    if len(structural_errors) < 20:
                        structural_errors.append(
                            "%s:%d: unknown tag %r" % (fname, lineno, tag))
        if cur_txid is not None:
            add(hist_r, cr)
            add(hist_w, cw)
            add(hist_t, cr + cw)
            sum_r += cr
            sum_w += cw
        per_file_commits[fname] = commits_this_file

    def stats(hist, row_sum):
        return {
            "hist": {str(k): hist[k] for k in sorted(hist)},
            "mean": (float(row_sum) / n_commit) if n_commit else None,
            "p50": percentile_from_hist(hist, n_commit, 0.50),
            "p90": percentile_from_hist(hist, n_commit, 0.90),
            "p99": percentile_from_hist(hist, n_commit, 0.99),
            "p999": percentile_from_hist(hist, n_commit, 0.999),
            "max": max(hist) if hist else None,
            "min": min(hist) if hist else None,
        }

    result = {
        "schema_version": "t140-setsize-distribution/v1",
        "trace_dir": os.path.abspath(trace_dir),
        "n_trace_files": len(files),
        "n_commit_trace": n_commit,
        "expect_commits_stdout": expect_commits,
        "n_read_rows": n_r_rows,
        "n_write_rows": n_w_rows,
        "n_x_rows": n_x_rows,
        "n_structural_errors": len(structural_errors),
        "structural_errors_sample": structural_errors[:20],
        "per_file_commits": per_file_commits,
        "read_set": stats(hist_r, sum_r),
        "write_set": stats(hist_w, sum_w),
        "total_set": stats(hist_t, sum_r + sum_w),
    }
    with open(out_json, "w") as f:
        json.dump(result, f, ensure_ascii=False, sort_keys=True, indent=2)
        f.write("\n")

    if structural_errors:
        sys.stderr.write("structural errors: %d\n" % len(structural_errors))
        return 3
    if n_x_rows:
        sys.stderr.write("X (lock violation) rows: %d\n" % n_x_rows)
        return 4
    if expect_commits is not None and expect_commits != n_commit:
        sys.stderr.write("commit mismatch: trace=%d stdout=%d\n"
                         % (n_commit, expect_commits))
        return 5
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
