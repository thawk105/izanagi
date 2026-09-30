## 変更内容

R 配下の次の 6 file を作成・変更しました。commit はしていません。

| file | 内容 | SHA-256 |
|---|---|---|
| [transaction.cc](/work/1/SFC/tanab/izanagi/.codex/worktrees/silo-line-a/output/runs/silo-line/ccbench/cc/silo/transaction.cc) | 指定された後段の `#line` 4 本だけを +3 | `80d76560f9086c6439ce60c774125cf3ffe5373cbae48af0b1687c858900740e` |
| [commit-msg.txt](/work/1/SFC/tanab/izanagi/.codex/worktrees/silo-line-a/output/runs/silo-line/commit-msg.txt) | 英語の commit message。subject は 60 字、trailer なし | `0022f341269e35f580f598bb50d08dbca8ae3b4f2de849422d2499dc4597d89e` |
| [instr-silo-gate-witness-L.patch](/work/1/SFC/tanab/izanagi/.codex/worktrees/silo-line-a/output/runs/silo-line/patches/instr-silo-gate-witness-L.patch) | 新 tip 用の計装 patch | `edaad46302a09d6311004c7c695a009a2ed36828a572afd85620a5386cfb1297` |
| [run_judge_v3.sh](/work/1/SFC/tanab/izanagi/.codex/worktrees/silo-line-a/output/runs/silo-line/scripts/run_judge_v3.sh) | GCC 11 または 12 で D297 (b) だけを実行 | `ad212521be24843d2a5016474703041c84d63df9cb669620f741acadcd6068b6` |
| [run_ci_then_judge_v3.sh](/work/1/SFC/tanab/izanagi/.codex/worktrees/silo-line-a/output/runs/silo-line/scripts/run_ci_then_judge_v3.sh) | CI build と GCC 11 の (b) を順に実行し、各 rc を記録 | `b3d0ff73c3b0e944c88542552c1bfdb9fcb931acce1d14dc3f816faf43ddd9d0` |
| [launch_gate_liveness_v3.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/silo-line-a/output/runs/silo-line/scripts/launch_gate_liveness_v3.py) | 新しい親子照合、build 別 patch、両 patch の SHA-256 記録 | `11d2610ef4874e0173e1ce549041a49cf7ef3a52b146a984d8bf4c72ef97cebf` |

`#line 365` と `#line 381` は据え置きました。clone は HEAD `7e5fa528037805dfc0459c742e4a21d6114c9799` の detached 状態で、作業ツリーの変更は `transaction.cc` だけです。repo の tracked file と既存 script の写しに変更はありません。一時 worktree と一時ファイルは撤去しました。

## 予測の自己確認

pin の `transaction.cc` に F→7e5fa528 の修正を `git apply` し、変更後 file と比較しました。両方とも include 行を空行にし、`ERR` を `IZ_ERR_AT(__LINE__)` に置き換えて `g++ -E -P -nostdinc -x c++ -DTRACE=0` で処理した結果、出力は **11,698 bytes で byte 一致**しました。`ERR` の値も両方 `106`・`693` です。この確認は Silo の当該 file の予測 probe の範囲です。

## 計装 patch の差

F 用と L 用の `diff -u` は **文脈の `#line 658` → `#line 661` の 1 行だけ**でした。hunk の行番号を含め、他の差はありません。F の clean 木と L の変更後の木で、それぞれ素の `git apply --check` が rc=0。適用後の `include/trace.hh`、`include/ycsb.hh`、`cc/silo/transaction.cc` は、`check_instr_v2.py` の `strip_trace` 方法で `#if TRACE` 枝を除くと、各適用前と byte 一致しました。

## 実走した command と rc

| command・範囲 | rc・結果 |
|---|---|
| clone の `git diff --stat` | 0。1 file、4 insertions・4 deletions |
| `/usr/bin/clang-format --dry-run --Werror`、変更 file | 0。clang-format 14.0.0 |
| `check_format_ci.sh`、CI と同じ 213 file | 0 |
| 上記 TRACE=0 予測 probe の `git show`、`git diff`、`git apply`、両 `g++` | すべて 0。出力一致 |
| F/L の一時 worktree で各 `git apply --check`・`git apply`・非 TRACE bytes 比較 | すべて 0・一致 |
| 2 本の shell script の `bash -n`、Python の `py_compile` と AST parse | すべて 0 |
| v3 script の usage、OID 形式拒否 | shell 2 本・Python とも想定どおり rc=2。Python `--help` は rc=0 |
| F/L patch の `diff -u`、v2/v3 script 3 組の `diff -u` | 差があるため各 rc=1。差分を確認済み |

v2→v3 の差分は、judge が (a) と二つの GCC を回す形から **指定された一つの GCC の (b) のみ**へ変わり、二つの bundle head・親子・tree を照合して 4 path の `--expect-paths` を渡すものです。束ね script は CI に固定の親 OID を渡し、GCC 11 の v3 judge を呼びます。trace 起動器は `--fix-parent-oid` と build 別 patch を受け、F→親→fix を照合し、両 patch の SHA-256 を JSON に残します。

## 未実走・残る懸念

計算ノードでの **CI build、D297 (b) の GCC 11・12、trace 本走は未実走**です。したがって、それらの合否はまだ主張しません。今回の TRACE=0 一致は指定された単一 file の probe であり、D297 の全 entry・header 展開の合格は本走待ちです。

## 総括

段 4 裁定の実装面を R 配下に用意し、指定された編集・format・予測 probe・計装 patch の検査は通りました。親が新 tip を commit した後に、計算ノードでの本走が必要です。