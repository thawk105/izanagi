# 成果物

[patches/instr-mocc-lock-coverage-pin-candidate.patch](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2844-author-a/patches/instr-mocc-lock-coverage-pin-candidate.patch) を作成しました。

- サイズ: **4,041 bytes**
- SHA-256: `9b06feed940d4d45318bfc7d2147a19e291abf7363285c3825b34c00c8907e94`
- 適用後 source は、旧 patch 適用結果から指定の 3 箇所だけを変更した bytes と完全一致。
- BASE への再適用結果の blob・SHA-256 は目標値に一致。

# 検査の argv と出力

すべて cwd は `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2844-author-a`。`rc=` は実行ラッパーが記録した終了コードです。以下は最終成果物での実測です。

```text
$ git apply --check --directory=tools/t2844_scratch/verify patches/instr-mocc-lock-coverage-pin-candidate.patch
rc=0
$ git apply --directory=tools/t2844_scratch/verify patches/instr-mocc-lock-coverage-pin-candidate.patch
rc=0
source contract: exact three replacements; reapplied bytes identical
$ git hash-object tools/t2844_scratch/verify/cc/mocc/transaction.cc
e393efbfd5fad7bbe05117b43669ccc0f44abb6a
rc=0
$ sha256sum tools/t2844_scratch/verify/cc/mocc/transaction.cc
712e31b5cbf2a3a63df442d50203c5c0787c98c83672d49a20210719bf32ebe4  tools/t2844_scratch/verify/cc/mocc/transaction.cc
rc=0
$ git apply --numstat patches/instr-mocc-lock-coverage-pin-candidate.patch
64	0	cc/mocc/transaction.cc
rc=0
$ grep -n '^#include' /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2844-mocc-xp-hook-branch/verbatim/mocc-transaction-e9e477ca.cc
1:#include <stdio.h>
2:#include <algorithm>
3:#include <cmath>
4:#include <thread>
6:#include "../../include/atomic_wrapper.hh"
7:#include "../../include/backoff.hh"
8:#include "include/atomic_tool.hh"
9:#include "include/scan_callback.hh"
10:#include "include/transaction.hh"
11:#include "include/tuple.hh"
15:#include "../../include/trace.hh"
rc=0
$ grep -n '^#include' tools/t2844_scratch/verify/cc/mocc/transaction.cc
1:#include <stdio.h>
2:#include <algorithm>
3:#include <cmath>
4:#include <thread>
6:#include "../../include/atomic_wrapper.hh"
7:#include "../../include/backoff.hh"
8:#include "include/atomic_tool.hh"
9:#include "include/scan_callback.hh"
10:#include "include/transaction.hh"
11:#include "include/tuple.hh"
15:#include "../../include/trace.hh"
rc=0
$ grep -n '^#line' tools/t2844_scratch/verify/cc/mocc/transaction.cc
17:#line 17
996:#line 990
1015:#line 991
1201:#line 1158
1217:#line 1169
1242:#line 1187
1258:#line 1195
rc=0
$ git apply --check --directory=tools/t2844_scratch/verify patches/broken-mocc-lockskip-validation.patch
rc=0
$ git apply --check --directory=tools/t2844_scratch/verify patches/broken-mocc-permutation-erase.patch
rc=0
$ git apply --check --directory=tools/t2844_scratch/verify patches/broken-mocc-early-unlock.patch
rc=0
$ git apply --check --directory=tools/t2844_scratch/verify patches/broken-mocc-hot-update-unlock.patch
rc=0
$ sha256sum patches/instr-mocc-lock-coverage.patch
e9e65b7876050865ee1cbc4d3a05516b09a8fe0b18149e0c063632162fd7bb48  patches/instr-mocc-lock-coverage.patch
rc=0
$ wc -c patches/instr-mocc-lock-coverage-pin-candidate.patch
4041 patches/instr-mocc-lock-coverage-pin-candidate.patch
rc=0
$ sha256sum patches/instr-mocc-lock-coverage-pin-candidate.patch
9b06feed940d4d45318bfc7d2147a19e291abf7363285c3825b34c00c8907e94  patches/instr-mocc-lock-coverage-pin-candidate.patch
rc=0
```

include 列の完全一致・11 行、および `#line` の指定値・7 行を assert でも確認しました。負例 4 本は同じ候補 source にそれぞれ単独で `--check` し、適用による累積変更は行っていません。

途中の初版では Python の diff 生成による行の対応付けが受入条件と合わず、次の出力でした。

```text
$ git apply --numstat patches/instr-mocc-lock-coverage-pin-candidate.patch
66	2	cc/mocc/transaction.cc
rc=0
```

source bytes を変えず Git で diff を再生成し、最終版では上記の `64	0` に解消しています。最終検査に赤はありません。

# 所有範囲と未実走

scratch は全削除済み。開始時の `git status --porcelain` は出力なし、終了時は以下のとおりで、所有外 file の変更は 0 です。submodule 作業木は編集していません。

```text
$ test '!' -e tools/t2844_scratch
rc=0
$ git status --porcelain
?? patches/instr-mocc-lock-coverage-pin-candidate.patch
rc=0
```

build、runtime、D297 前処理検査、pytest、全体の docs・agents 検査、provenance 監査は**未実走**です。commit は作成していません。本段の検査は親の検査を代替しません。

## 総括

指定の patch 1 file のみを作成しました。目標 source ハッシュ、`+64/-0`、include 11 行、`#line` 7 行、負例 4 本の厳密適用、旧 patch 不変をすべて確認済みです。