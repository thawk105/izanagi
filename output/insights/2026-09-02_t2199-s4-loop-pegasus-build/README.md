# [T-2199] 段 4 loop を Pegasus で build へ到達させる道は、認可 gate で塞がっている (2026-09-02)

wave: `dev-wave-t2199-s4-loop-pegasus-build` / branch `worktree-dev-wave-t2199-s4-loop-pegasus-build`
実装面の差分: **ゼロ** (裁定 C2 により実装しない)。記録のみ。

## 一行で

**preprocess は環境側で解けるが、その先に編集面の外の壁がある。** 段 4 loop は
Pegasus 計算ノード上で、build より前の認可検査に拒否される。原因は環境ではなく
`p3_s4_loop.py` が環境タグを固定していることで、この file は稼働中の別 wave の所有である。
**実行場所は Pegasus のままとし、cygnus へは退避しない。**

## 何を決めたか

| # | 問い | 決定 | 根拠 |
|---|---|---|---|
| 1 | 移植するか、`linux-baremetal` を使うか | **Pegasus を継続** | 下記「実行場所の択一」 |
| 2 | 本 wave で実装するか | **実装しない** | 目的が許可された編集面で到達不能。安全な部分実装も無い |
| 3 | preprocess の原因 | **`config.h` 不在を強く支持** (確定ではない) | 前 wave の残存 artifact を実見 |

## 到達不能の証明 (親がコードを実見した)

1. `orchestrator/campaign/p3_s4_loop.py:111` — `ENV_TAG = "linux-baremetal"` が固定。
2. 同 `1428-1433` — `authorization_contract=env_contract.authorize(ENV_TAG)` を `run_campaign` へ渡す。
3. `orchestrator/campaign/loop.py` の `_authorize_measurement` が
   `execution_guard.require_certified_writer_authorization()` を **build より前**に呼ぶ。
4. `orchestrator/campaign/execution_guard.py:136-159` — site が Pegasus compute のとき、
   activation state 内で `attestation_mode == "required"` の契約がちょうど 1 つで、
   提示された契約がそれと同一であることを要求する。
5. `orchestrator/campaign/env_contract.py:292-311` — `linux-baremetal` の `attestation_mode` は
   `"none"`、`pegasus` は `"required"`。よって Pegasus 計算ノード上で `linux-baremetal` 契約を
   提示すると 4 の条件で拒否される。**build へ到達しない。**

**この拒否は正しい。** 目的は、Pegasus で得た値が `linux-baremetal` の系列へ混入するのを防ぐこと
である。迂回しない。

## 編集面の内側に残った案を採らなかった理由

唯一の前進策は、job-private な CMake wrapper を PATH 先頭に置き、pin 済み
`FETCHCONTENT_SOURCE_DIR_*` を configure 時だけ注入することだった。**採らない。**

condition gate は wrapper を CMake の実体として実行する。ところが gate の green record は
**CMake の path も wrapper の hash も実効 configure argv も保存しない**
(`condition_meaning_gate.py:1402-1415, 1479-1490, 2064-2085`)。
`condition_meaning_gate.py` を 1 byte も変えなくても、これは実質的な受理集合の変更である。
束縛を足すには gate 側を変える必要があり、それも編集面の外である。

**教訓として一般化できる形:** 「code file を変えない」ことは「受理集合を変えない」ことと同じではない。
判定器が環境から実体を解決する設計では、PATH・環境変数・生成された入力が受理集合の一部である。

## preprocess 失敗の診断

段 2 が静的連鎖から立てた仮説 (確信度 0.85) を、親が**前 wave の残存 artifact** で裏取りした。

- `external/ccbench/cmake/ThirdParty.cmake:57-78` — `config.h` と archive は
  `add_custom_target(masstree_build)` の**ビルド時**生成物。configure は source を置くだけ。
- `external/ccbench/include/masstree_wrapper.hh:20` — `#include <config.h>` を無条件で行い、
  owner TU `cc/silo/transaction.cc` は `cc/silo/include/common.hh:12` 経由でここへ到達する。
- **T-2182 の投入 6 が残した configure 木**
  (`/work/1/SFC/tanab/izanagi-exploration-t2182/configure-probe3`) の実見:
  `FETCHCONTENT_SOURCE_DIR_MASSTREE` は空、`FETCHCONTENT_FULLY_DISCONNECTED=OFF`、
  `_deps/masstree-src` は clean clone として populate 済み (`configure.ac`・`bootstrap.sh` あり)、
  **`config.h` はこの木のどこにも存在しない。**
- condition gate は configure 直後に owner TU を preprocess し、`masstree_build` を建てない。

**言える:** gate が preprocess する木には、owner TU の include 閉包が要求する `config.h` が実在しない。
**言わない:** これが観測された `preprocess-failed` の literal な原因であること。前 wave は stderr を
保存していない。同じ reason code へ落ちる条件は 7 つある
(`condition_meaning_gate.py:1370-1399, 1993-2012`)。**確度は上がったが確定ではない。**

## 実行場所の択一 — Pegasus を継続する

段 2 の起草子は cygnus を推奨した。**不採用**とした。

| 観点 | Pegasus | cygnus (`linux-baremetal`) |
|---|---|---|
| 実測された到達点 | 6 投入。configure rc=0 まで。build 未到達 | 段 4 loop の iteration 1-4 が certified まで到達 (過去) |
| 残る障害 | 認可 gate の配線 (`p3_s4_loop.py` 5 か所) | 現在の到達性が未測定 |
| この session からの接続 | 実行中 | `~/.ssh/config` に entry 無し |
| ユーザー方針 | 新規 evidence の既定先 | 「使えるが使わない」(2026-08-05 裁定) |

**cygnus 推奨を採らない理由:** 比較の cygnus 側が**過去の成功**で、Pegasus 側が**目的の異なる 6 投入**
である。沈んだ費用を将来費用として読んでいる。段 2 自身も現在の cygnus 到達性を未確認と書いた。
段 3 の両レンズが独立に Pegasus 継続を支持した。

**「cygnus では不可能」とは言わない。** 費用の項が欠けていると言う。

## 引き継ぎ — 配線の先例が repo 内にある

`orchestrator/campaign/p3_s4_loop_trigger_gating.py` は**既に site-aware である**。

- `_site_admits_measurement()` / `_admit_env_contract()` (442-455 行) が site を契約へ写像し、
  未知 site を fail-closed で拒否する。
- `_campaign_cfg_for_site()` が解決済み契約を identity へ束縛し、Pegasus marker を分離する。
- 815 行が `authorization_contract=env_contract.authorize(contract.env_tag)` を渡す。

**p3 を所有する wave は、この兄弟 file の形を `p3_s4_loop.py` の 111-113 / 1019-1021 /
1347-1349 / 1428-1433 / 1965-1968 へ写せばよい。新設ではなく移植である。**

配線が着地した後に job script を作る wave が満たすべき既存義務 (段 3 が実測で挙げた):

- 計算ノードで `python3` を 3.10 へ向ける PATH shim (手順書 124-149 行。無しで 19 件失敗した実測)。
- raw qsub の `-o` / `-e` を repo 外へ転送する (作業ツリーを汚すと次回起動が止まる)。
- `tools/pegasus/admission_registry.json` + `orchestrator/tests/test_hooks.py` の literal golden +
  手順書の投影表 + `tools/pegasus/README.md` の tagged qsub command を同時に同期する。

## 主張の境界

- **言える:** 段 4 loop は現行 HEAD では Pegasus 計算ノードで build へ到達できない。
  停止点は認可 gate であり、環境の未整備ではない。これは親がコードを実見して確定した。
- **言える:** 実行場所の択一は Pegasus で決着した。根拠は上表。
- **言わない:** preprocess の literal な原因を確定したこと。
- **言わない:** 配線を足せば build が通ること。次に出る障害 (attestation の exact 照合、
  reservation と claim root の束縛) は段 3 が予測しただけで未実測である。
- **言わない:** cygnus が到達不能であること。測っていない。

## 段 3 が返した scope 外の real 所見 (裁定パッケージ)

1. PATH wrapper に trace 有効化と strip を同時注入されると、`izanagi_trace` symbol 検査
   (`buildcache.py:3445` が strip 済み binary は素通りと明記) を抜ける経路がある。
   **本 wave は wrapper を採らないので発火しないが、将来 PATH wrapper を導入する設計は
   絶対規律 1 の穴を開けうる。**
2. `p3_s4_loop` の CLI は build 後に `outcome=aborted` でも一般検査が通れば rc=0 を返し、
   condition gate の canonical record を保存しない。terminal verdict の証拠が成果物に残らない。
3. p3 経路の単独性確認は canary 付き probe ではなく plain `pgrep` である。D59 条件 3 の
   充足度に関わる。

いずれも編集面の外 (p3 所有) であり、本 wave では実装しない。

## 一次資料

- 段 1 brief: `s1-brief.md`
- 段 4 裁定: `s4-adjudication.md`
- 段 2 プラン (逐語): `verbatim/s2-plan.md`
- 段 3 レンズ A (逐語): `verbatim/s3-lensA.md`
- 段 3 レンズ B (逐語): `verbatim/s3-lensB.md`

## 逐語の正規化 (erratum)

`verbatim/` の 3 file は、`git diff --check` の末尾空白検出に抵触したため、
**行末の空白だけを除去する可逆最小正規化**を行った (`DW-S07`)。可視文字は 1 文字も変えていない。
除去したのは markdown の hard line break として置かれた行末の半角空白であり、
除去 bytes は s2-plan が 10、s3-lensA が 8、s3-lensB が 18 である。

| file | 正規化前 sha256 | 正規化前 bytes | 正規化後 bytes |
|---|---|---|---|
| `verbatim/s2-plan.md` | `0c2b9d2683de39f8199a50c2e8842b80bfae0e646e590fde64d42412c1a041dc` | 38868 | 38858 |
| `verbatim/s3-lensA.md` | `f3a532e479806d03d8d84b6fe344ca4e62da4d46e35204bddfcbeb9b460eaa56` | 10023 | 10015 |
| `verbatim/s3-lensB.md` | `6366ab614a7f035b2af4aeb21778a78f38ecd1f2634c53bab5972837d1a02d52` | 13029 | 13011 |

`verbatim/s2-plan.md` の正規化前 sha256 は、段 2 子の受領証 `attempts[0].output_sha256` と
byte 一致する。**復元法:** 各 file の元 bytes は job 側 artifact
(`<artifact-root>/dev-wave-t2199-s4-loop-pegasus-build/{s2-plan,s3-lensA,s3-lensB}.md`) に残る。
repo 側だけから戻すなら、上表の行末へ半角空白 2 個を戻せば元 hash に一致する。
