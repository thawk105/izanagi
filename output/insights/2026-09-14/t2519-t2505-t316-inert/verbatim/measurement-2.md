# 実測 2 — 拒否理由の直接証拠を計算ノードで取得した (2026-09-14)

## 投入

段 6 まで閉じた実装 commit `fecb4f709e40cf0119940d760aa80b38b1ceafae` を束縛して投入した。

```
qsub -N izdw-t316b -v IZANAGI_PEGASUS_THIRDPARTY_CACHE=/work/1/SFC/tanab/izanagi-thirdparty-cache,IZANAGI_T139_DEPENDENCY_SOURCE_ROOT=/work/1/SFC/tanab/izanagi-thirdparty-deps,IZANAGI_T316_EXPECTED_COMMIT=fecb4f709e40cf0119940d760aa80b38b1ceafae,IZANAGI_T316_EXPECTED_WORKTREE_ROOT=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2519-t2505-t316-inert tools/pegasus/probes/t316_sandbox_backend_probe.pbs
```

応答: `Request 996829.nqsv submitted to queue: gen_S.` (rc=0)

## 実行束縛

| field | 値 |
|---|---|
| `PBS_JOBID` | `0:996829.nqsv` |
| `hostname` | `bnode016` (実測 1 の `bnode040` とは別ノード) |
| `observed_commit` | `fecb4f709e40cf0119940d760aa80b38b1ceafae` |
| `bound_paths_clean` | `True` |
| probe 内 `elapsed_ns` | 25680195221 (25.7 秒) |

PBS: Created 11:42:33 / Started 11:42:41 / Ended 11:43:07 JST、Elapse 31S。
受領証 = `output/env/pegasus/t316-sandbox-backend/0:996829.nqsv/receipt.json` (147290 bytes) + `COMPLETED`。

## 受領証の S6 (実測 1 と同一)

```json
{"attempted": false,
 "error": {"message": "condition gate rejected t316 CCBench build: supply=red/configure-failed, meaning=unestablished/meaning-witness-undeclared",
           "type": "RuntimeError"},
 "reason": "S6 raised"}
```

stage verdict も同じく `S6_BUILD_NOT_ATTEMPTED` / `blocked`。
**receipt の schema・field・文面は 1 文字も変わっていない** (D1849 を守った設計どおり)。

## 新たに得られた直接証拠 (job stderr の逐語)

```
condition gate rejected t316 CCBench build: supply detail=successful process wrote stderr=b'CMake Warning:\n  Manually-specified variables were not used by the project:\n\n    CCBENCH_BACKOFF_FIXED\n    IZANAGI_GFLAGS_SRC_HEAD\n    IZANAGI_GLOG_SRC_HEAD\n    RULE_LAUNCH_COMPILE\n\n\n'; argv=/usr/bin/cmake -S /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2519-t2505-t316-inert/external/ccbench -B /tmp/izanagi_condition_supply_gh4nt2dh/requested -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DCMAKE_CXX_COMPILER=/usr/bin/x86_64-linux-gnu-g++-11 -DCMAKE_BUILD_TYPE=Release -DENABLE_SANITIZER=OFF -DCCBENCH_TRACE=0 -DCCBENCH_BACK_OFF=0 -DCCBENCH_NO_WAIT_LOCKING_IN_...<argv truncated; limit=500 bytes; original=1202 bytes; sha256=acb67b71c0ee05ae535d04f057aed96b5340bb10d891c1719e739baa7e6364de>
condition gate rejected t316 CCBench build: meaning detail=<no detail>
```

## この証拠が確定させたこと

1. **CMake configure は成功している。** detail の先頭は
   `successful process wrote stderr=` である。つまり `condition_meaning_gate._run_process` の
   rc≠0 分岐 (1610-1616) ではなく、**rc=0 かつ stderr 非空の分岐 (1617-1622)** で赤になった。
   起動失敗でも timeout でも identity drift でもない。
2. **stderr の中身は CMake の未使用変数警告であり、載っている変数は 4 件である。**
   `CCBENCH_BACKOFF_FIXED` / `IZANAGI_GFLAGS_SRC_HEAD` / `IZANAGI_GLOG_SRC_HEAD` /
   **`RULE_LAUNCH_COMPILE`**。
3. **落ちたのは requested 側である。** argv の `-B` は
   `/tmp/izanagi_condition_supply_gh4nt2dh/requested` を指す。stock 側の configure は実行されていない
   (requested が例外を投げた時点で停止するため)。段 3 レンズ sol が「どちらで落ちたか未確定」と
   指摘した点が、これで確定した。
4. **`-S` は素の CCBench 木である。** patch を当てた木ではない。
5. **meaning arm は detail を持たない。** `<no detail>` と出た。`unestablished` record に `detail` が
   無いことは D1849 が述べていたとおりで、`.get` を使う設計が実機で正しかったことも実証された。

## 段 4 裁定で「仮説」に格下げした 2 点の決着

- **(A) 素の木に `CCBENCH_BACKOFF_FIXED` が無いため、gate が requested 側で必ず足すこの変数が
  未使用警告に載る** — **実測で裏づけられた。** 警告の第 1 行が `CCBENCH_BACKOFF_FIXED` である。
- **(B) t316 が CCBench の使わない変数を渡している** — **実測で裏づけられた。**
  さらに、段 3 レンズ sol が「`RULE_LAUNCH_COMPILE` の警告発生は裏づけられていない」と指摘した点も、
  実測の警告本文に `RULE_LAUNCH_COMPILE` が現れたことで**裏づけられた**。
  未使用変数は親が静的に挙げた 3 件 (`IZANAGI_GFLAGS_SRC_HEAD` / `IZANAGI_GLOG_SRC_HEAD` /
  `RULE_LAUNCH_COMPILE`) に `CCBENCH_BACKOFF_FIXED` を加えた 4 件だった。

## この実測がなお確定させていないこと

- **stock 側が単独で緑になるか**は未測定である。requested が先に落ちるため到達していない。
  stock 側は `-DCCBENCH_BACKOFF_FIXED` を渡されないので警告は 3 件になるが、
  **3 件でも stderr は非空であり、同じ分岐で赤になると読める。** ただしこれは推論であって実測ではない。
- 失われた job `0:996644.nqsv` (実測 1) の stderr 逐語そのものは復元できない。実測 2 は
  **別 commit・別ノードでの再現走**であり、実測 1 と同じ reason code・同じ stage verdict を示した。
- 1 allocation・`bnode016`・束縛 commit `fecb4f709` での観測であり、全ノード・将来の main へは
  一般化しない。
