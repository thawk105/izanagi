# [T-2213] A+B+C patch stack の inert 要求は、既存機構では stock 同等の緑に到達しない — 計算ノードで実測

- wave: `dev-wave-t2213-inert-abc-measure` / branch `worktree-dev-wave-t2213-inert-abc-measure`
- 起点 main: `8f17db598` (実測時の worktree HEAD)。記録時に local main `15b22ac78` へ ff。
  この間に `orchestrator/campaign/condition_meaning_gate.py`・`tools/pegasus/dispatch_compute.py`・
  `patches/` の変更は無い (`git diff --stat` 空)
- 日付: 2026-09-16
- 結論: **不到達。** adaptive const probe が使う A+B+C patch stack (13 macro) を当てた木に対する
  inert 要求は、計算ノード (bnode006、request `1832.nqsv`) で supply 腕が
  **赤 `compile-command-drift`** になり、bytes 比較の手前で止まる。原因は環境ではなく構造で、
  下記の 2 点が独立に緑を塞ぐ。どちらも既存機構の改修か patch の作り直しを要し、本 wave は実装しない
- 実装面の差分: 0 件。gate・PBS・probe・patch・dispatch は無変更。glue script も repo に作っていない
- 一次資料: D1856、D1936 項 17、D1986 項 8、worklog 1425 (T-2213)・1455 (T-2518)・1486 / 1517 (T-2519)

## 1. 依頼と、守った裁定

依頼は「既存機構で inert 要求が stock 同等の緑へ到達するかを計算ノードで実測する。編集不要の実測に
限定し、改修が要ると分かったらその事実を構造化して返して実装しない」。守った裁定は次の 3 つ。

| 裁定 | 内容 | 本 wave での扱い |
|---|---|---|
| D1936 項 17 | 13 macro の witness 新設も supply 先行配線もしない。まず既存機構で計算ノード実測 | 実測のみ。witness・配線に触れていない |
| D1986 項 8 (T-2518) | 依存供給と CLI 入力をつなぐ最小の入り口を新設しない | 新しい入り口を作らず、既存 CLI + 既存 generic dispatch + `git clone` / `git apply` + 既存の依存 install prefix の**組み合わせ (使い方)** だけで走らせた |
| command 引数 | 稼働中の `dev-wave-t548-versioned-dep-procurement` が編集中の PBS に触らない | PBS は使っていない。同 wave の mutation harness 稼働を `ps` で実測し、ファイルを読んだだけ |

## 2. 何をどう測ったか

すべて既存の部品で、新しい機構は無い。

| 部品 | 現物 |
|---|---|
| 判定器 | `python3 -m orchestrator.campaign.condition_meaning_gate` (CLI、main `8f17db598` の blob `82a2779f0`) |
| 計算ノード投入 | `tools/pegasus/dispatch_compute.py --task generic -- <argv>` (clean env、cwd = 投入元 worktree、submission dir だけ read-only) |
| 木 (A+B+C) | `/work/1/SFC/tanab/dev-wave-scratch/t2213-inert-abc-20260916/ccbench-abc` — `external/ccbench` の shared clone を pin `511c9538e4e8efa54b45cda62e72389ed3b706ec` で detach し、`patches/cicada-adaptive-params.patch` (sha256 先頭 `9b2153e0547e1678`) → `cicada-adaptive-dynamic.patch` (`f3fe6b7e67931775`) → `cicada-adaptive-counterfactual.patch` (`4c04caa89244d74a`) を順に `git apply`。結果 `cmake/Options.cmake` +29、`include/backoff.hh` +603/−6。probe の `_applied_patch_stack` と同じ順序・同じ操作 (`patchharness.apply_patch` = `git apply`) |
| 木 (stock) | 同 `…/ccbench-stock` — 同じ pin の clean な detach checkout (`status --porcelain` 空) |
| 依存 (gflags / glog) | 既存の install prefix `/work/SFC/tanab/ss2pl-study-deps/{gflags,glog}-install` (gflags 2.2.2 / glog 0.5.0 = pin と同じ版、2026-08-25 作成)。login node で pinned source から build しようとしたが `cmake --build` を guard が拒否したため、再 build はしていない。**両腕が同じ prefix を使うので前処理 bytes の比較結果には影響しない** (stock 比較では `dependency-closure-drift` の検査も行わない) |
| FetchContent | `-DFETCHCONTENT_SOURCE_DIR_{MASSTREE,MIMALLOC,GOOGLETEST}=/work/1/SFC/tanab/izanagi-thirdparty-cache/<name>` — t316 が 2026-09-15 に緑到達した受領証 (`0:999027.nqsv`) と同じ形 |
| compiler / cmake | `/usr/bin/x86_64-linux-gnu-g++-11` (11.4.0) / `/usr/bin/cmake` (3.22.1)。login と bnode006 で同一 |
| cell | probe の代表 cell `stock:1:100:1000:10` (`verbatim/login/cell-defines.txt`)。`genome.cmake_defines()` から `DEFINE_SPECS` の macro を除いた base 引数 = `-DCCBENCH_BACK_OFF=1 -DCCBENCH_NO_WAIT_LOCKING_IN_VALIDATION=1 -DCCBENCH_NO_WAIT_OF_TICTOC=0 -DCCBENCH_WAL=0` (+ `-DCCBENCH_TRACE=0`、build type、compiler)。これは `screening_driver._condition_gate_base_configure_args()` と同じ規則。domain 3 macro (`BACKOFF_INCR_MILLI=100000` / `BACKOFF_MAX_US=1000` / `BACKOFF_UPDATE_US=10`) はすべて `inert_values` に載る |

計算ノードへ渡した argv の逐語は `verbatim/dispatch-1832/request.json` の `args`。要点だけ書くと

```
python3 -m orchestrator.campaign.condition_meaning_gate
  --source-root <…>/ccbench-abc --stock-root <…>/ccbench-stock
  --driver-id t2213-inert-abc-compute
  --macro BACKOFF_MAX_US --requested-value 1000 --stock-comparison
  --cxx /usr/bin/x86_64-linux-gnu-g++-11 --cmake /usr/bin/cmake
  --configure-arg=-DCMAKE_BUILD_TYPE=Release --configure-arg=-DENABLE_SANITIZER=OFF
  --configure-arg=-DCMAKE_C_COMPILER=/usr/bin/x86_64-linux-gnu-gcc-11
  --configure-arg=-DCMAKE_PREFIX_PATH=<gflags-install>;<glog-install>
  --configure-arg=-DFETCHCONTENT_SOURCE_DIR_MASSTREE=<cache>/masstree   (MIMALLOC / GOOGLETEST も同様)
  --configure-arg=-DCCBENCH_BACK_OFF=1 --configure-arg=-DCCBENCH_NO_WAIT_LOCKING_IN_VALIDATION=1
  --configure-arg=-DCCBENCH_NO_WAIT_OF_TICTOC=0 --configure-arg=-DCCBENCH_WAL=0 --configure-arg=-DCCBENCH_TRACE=0
```

`--configure-arg -D…` (空白区切り) は argparse が「expected one argument」で拒むので、等号形が要る。

## 3. 結果

| 走行 | 場所 | macro (inert 値) | supply 腕 | runtime-meaning 腕 | admitted | 逐語 |
|---|---|---|---|---|---|---|
| 計算ノード (本命) | bnode006、`1832.nqsv`、20:16:43–46 JST、queue 待ち 5.2 s、accounting_verified | `BACKOFF_MAX_US=1000` | **red / `compile-command-drift`** (comparison `stock-inert-identity`) | unestablished / `meaning-witness-undeclared` | false (child rc=2) | `verbatim/dispatch-1832/izdw-8a40522fbc.o1832` (3 行 JSON)、`receipt.json`、`result.json` |
| login 生死確認 | pegasus login | `BACKOFF_MAX_US=1000` | red / `compile-command-drift` | unestablished | false | `verbatim/login/login-liveness-BACKOFF_MAX_US.stdout` |
| login 補助 (B family) | pegasus login | `BACKOFF_COUNT_WINDOW=0` | red / `compile-command-drift` | unestablished | false | `verbatim/login/login-family-b-BACKOFF_COUNT_WINDOW.stdout` |
| login 補助 (C family) | pegasus login | `BACKOFF_STEP_POLICY=0` | red / `compile-command-drift` | unestablished | false | `verbatim/login/login-family-c-BACKOFF_STEP_POLICY.stdout` |

4 走とも、判定器が保存した前処理 bytes は同じ値である — requested (A+B+C 木) 4,952,686 bytes /
sha256 先頭 `95967b12f97eff83`、control (stock 木) 4,949,514 bytes / `b092ee3f0f9f3985`。
計算ノードと login node で bytes が一致するので、**判定は環境に依らない**。owner TU
(`cc/silo/transaction.cc`) の sha256 も両腕で同一 (`17554ea72d98076a…`)。

## 4. なぜ到達しないか — 独立した 2 つの構造的原因

### 原因 1 (実測): 判定器は「要求 macro と同じ patch の family」しか compile command から除外しない

`condition_meaning_gate.py` 2252–2258 行。stock 比較のとき `allowed_names` は
「要求 macro + companion + **同じ `patch_rel` を持つ `DEFINE_SPECS` の macro**」で、
`_preprocess_argv` はこの集合に入る `-D` だけを comparable argv から外す。

A+B+C を同時に当てた木の compile command は、3 つの patch が `ccbench_universal_definitions`
へ足した 13 個の `-DBACKOFF_*` をすべて持つ (evidence の `requested_replay_argv` にだけ在る
`-D` が 13 件、`control_replay_argv` には 0 件)。要求が `BACKOFF_MAX_US` なら
params family の 3 個だけが許容され、dynamic family 7 個と counterfactual family 3 個が残る。
どの family の macro を要求しても他 2 family が残るので、**3 family とも同じ理由で
`compile-command-drift`** になる (上表の B / C 補助実測)。判定器はこの時点で bytes 比較へ進まない。

これは T-2519 で緑に到達した 2 経路 (backoff_sweep / t316) との差でもある。どちらも
`silo-backoff-fixed.patch` の **1 patch・1 family** を当てた木を比べており、13 macro を一度に
materialize する木を判定器に渡した driver は本 wave が最初である。

### 原因 2 (再生で実測): 原因 1 が無くても、patch A/B/C は inert 値で stock と同じ文面にならない

D1856 が「緑になるかどうかが配線の成否を決める」と書いていた bytes 比較そのものを、
判定器の関数 (`_select_owner_entry` / `_preprocess_argv` / `_classify_stock_inert_root_location_difference`)
をそのまま呼んで login node で再生した (`verbatim/replay/summary.json`)。
13 macro をすべて許容した仮定では comparable argv は一致する (原因 1 は消える) が、
前処理 bytes は一致しない —

- 差分 8 hunk のうち 6 hunk は `__FILE__` の path (`ccbench-abc` / `ccbench-stock`) だけの差 = 分類器が
  許す位置差。
- source root を正規化して残るのは **2 hunk、+72 / −5 行、すべて `include/backoff.hh` 由来の
  `Backoff` class** (`verbatim/replay/control-rootnormalized-vs-requested.diff.txt`)。
  patch A は `kMaxBackoff = 1000;` を `static_cast<double>(1000);` に、`kIncrBackoff = 100;` を
  `static_cast<double>(100000) / 1000.0;` に書き換え、`kUpdateBackoffUs` と static_assert 群を足し、
  `check_update_backoff` を `check_update_backoff_at` へ分割する。B / C も同じ class へ定数と
  static_assert を無条件に足す。`silo-backoff-fixed.patch` のように `#if … #else <stock 原文> #endif`
  で stock 側の文面を保つ構造ではない。
- 分類器の判定は `location_only=false, has_residual=true` → 原因 1 を解いても
  **`stock-inert-mismatch` の赤**になる。

意味的には stock と等価 (定数値は同じ) だが、判定器が見るのは前処理後の bytes であり、
`inert_values` の宣言は「bytes が一致する」ことまで保証していない。

## 5. 改修が要るとしたら何か (構造化して返す。実装しない)

到達させるには次のどちらか、または両方が要る。どれも本 wave の scope 外で、ユーザー裁定の対象。

1. **判定器側**: multi-patch stack を 1 つの family として宣言し、`allowed_names` がその stack の
   全 macro を除外できるようにする (`DefineSpec.patch_rel` が 1 patch しか表せない現状の拡張)。
   共有の正しさ防壁の改造であり、負例 (別 family の define を黙って許す方向) の変異が要る。
2. **patch 側**: A/B/C の `include/backoff.hh` 変更を、inert 値のとき stock 原文が前処理に残る
   `#if` 構造へ作り直す。B10 系列の測定は patch の bytes (`patch_stack_sha256`) に束縛されているため、
   作り直した patch は別 stack として扱う必要がある。
3. 上記を行わない場合、この driver の inert 要求は supply 腕の機械証拠を持てない。
   D1856 の繰延べ (probe の build sink 2 件) は維持のままになる。

原因 1 だけを直しても原因 2 で赤になるので、1 だけの改修は緑に到達しない。

## 6. この insight が保証しないこと

- 依存 prefix は本 wave が pinned source から build したものではない (既存 artifact)。判定に影響しない
  理由は §2 に書いた。certified 経路で再現するなら PBS prologue と同じ /scr build を使う。
- runtime-meaning 腕は 13 macro とも `unestablished` (D1856 条件 1、本 wave の対象外)。
- 性能値・certified 成果物・凍結成果物は一切作っていない。
- B / C family の 2 走は login node の補助実測で、計算ノードでは走らせていない。判定は決定的な argv 比較で
  環境に依らないことを bytes の一致 (§3) で示した。

## 7. 親が踏んだこと

- `cmake --build` を login node で実行しようとして guard に拒否された (迂回せず既存 prefix へ切替)。
- `--configure-arg -D…` を空白区切りで渡して argparse に拒否された (等号形へ)。
- helper script (launcher / detach / replay / cell-defines) を一度 insight の verbatim へ複写したが、
  「probe を repo へ入れない」規律に照らして除去し、`/work/1/SFC/tanab/dev-wave-scratch/t2213-inert-abc-20260916/helpers/`
  へ保全した。argv は `request.json` に逐語で残る。
- 前処理出力の比較 (`verbatim/replay/*.diff.txt`) は `.diff` のままだと provenance checker が拡張子で
  実装面 (適用可能な patch) と分類し Codex author を要求する。適用対象の無い証拠テキストなので
  `.diff.txt` に改名した (内容は不変)。

## 8. 環境の後始末

- scratch `/work/1/SFC/tanab/dev-wave-scratch/t2213-inert-abc-20260916/` (木 2 本、replay の .ii 各 5 MB、
  log、helpers) は残してある。再現に使わなくなったら削除してよい。
- dispatch の受領証原本は worktree の `output/pegasus-dispatch/8a40522fbc66c3d5e11e4a3ef4eab1f5/`
  (gitignore)。verbatim へ複写済み。
