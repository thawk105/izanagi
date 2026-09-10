# [T-1431] 床値 (floor value) pilot 再投入 — 試行記録と確定した 2 blocker

## 要約

D581 に従い床値 pilot を再投入した (request `940170.nqsv`)。**前回 (2026-08-20、request
`926261.nqsv`) を止めていた 2 本の閂は実際に外れており、12 セル中 3 セルのビルドが完了した。
しかし 4 セル目 `sort_best` のビルドが失敗し、床値の実測値は再び得られなかった (計測到達セルは
0)。** admission チケットの消費は今回も 0 枚で、`retry_slots_per_cell=2` は全 12 セル満枠のまま
である。

停止点は 2 つあり、片方は今回顕在化した一次要因、もう片方は**仮に一次要因を直しても直後に必ず
止まる潜在要因**である。後者は最小 probe で構造的に再現不能であることを実証した。どちらも
正しさゲートを緩める方向の回避はしていない。

## 環境・実行パラメータ (D581 が求める記録)

- **実行環境**: Pegasus, queue=gen_S, nodes=1, elapstim_req_s=36000 (10h 割当)、実行ノード
  `bnode001`。PBS 指示子は `tools/pegasus/floor_campaign.sh` の
  `-A SFC` / `-q gen_S` / `-l elapstim_req=10:00:00` / `-b 1`
- **投入元 commit**: `c301c4fdb0bc7997d729fe0de80f8b99356a6012` (main HEAD、worktree
  `dev-wave-t1431-floor-pilot-rerun` 経由)
- **submission nonce**: `841537990c502065fb92c79655f47fe7`、request ID = `940170.nqsv`
- **投入コマンド**: `tools/pegasus/submit_floor.sh --confirm-irreversible-pilot-holdout`
  (標準投入経路。先に `--dry-run` で qsub argv を確認した)
- **ccbench pin**: `511c9538e4e8efa54b45cda62e72389ed3b706ec` (pinned submodule gitlink)
- **floor protocol**: `output/s8b-freeze/floor-protocols/e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01--511c9538e4e8efa54b45cda62e72389ed3b706ec.json`
  (`resolve-current-protocol` の live 解決結果、rc=0。前回試行と同一ファイル)
  - `contract_sha256=e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01`
  - `stock_configuration=stock_common`、`n_sessions=8`、`reps=5`、`retry_slots_per_cell=2`、
    `extime_s=5`、`env_tag=pegasus`、`schedule_algorithm=round-permutation/v2`
  - freeze: `output/s8b-freeze/holdout_freeze.json`
    (`sha256=315b1eb83d6fbdc525448c3c96c66ab6013df72487f35d8fa519c27ba34bc688`、
    protocol の記録値と一致)
- **toolchain**: 計算ノード実測で `gcc (Ubuntu 11.4.0-1ubuntu1~22.04.3) 11.4.0` /
  `g++` 同版。ログインノードも同一版である。実体は job-staging の
  `compiler.path` / `compiler.version` / `cxx.*` / `cmake.*` に記録済み
- **最適化 / build**: `buildcache.build_v2` 経由、trace-disabled (規律1)
- **perf**: `available:false` (probe rc=2)。本機で perf を要求しない既定方針どおり blocker と
  しない
- **ワークロード**: 未到達 (12 セル中 0 セルが計測開始に到達)
- **所要**: 19:04:17 投入 → 19:11 実行開始 (`bnode001`) → 19:13 終了。scheduler の
  `Remaining Elapse: 35879S` が示すとおり、割当 36000 秒のうち実消費は約 121 秒である

## 投入前に外した、パラメータ表に無い閂

`tools/pegasus/submit_floor.sh` の `stage_floor_third_party_payload` は、
`FLOOR_THIRD_PARTY_PERSISTENT_ROOT`
(`output/env/pegasus/silo_ladder_rung1/job-staging/thirdparty-src`) が実在することを要求し、
不在なら `floor third-party source root is missing or unsafe` で fail-closed して
**qsub 自体を実行しない**。この path は `.gitignore` 対象の機体ローカル cache であり、
**本 wave の worktree・main checkout・[T-1461] 自身の worktree のいずれにも実在しなかった。**

`tools/pegasus/README.md` §6 が定める標準供給経路で hydrate した。

```
python3 tools/pegasus/fetch_third_party.py verify  --repo-root <WORKTREE> --cache-root <CACHE>
python3 tools/pegasus/fetch_third_party.py hydrate --repo-root <WORKTREE> --cache-root <CACHE>
```

- `verify` rc=0。masstree / mimalloc / googletest の 3 本とも `policy.json` の pin と exact 一致
- `hydrate` rc=0。offline であり、`.gitignore` 対象 path にしか書かず、tracked file へ触れない。
  submit 側の pin/clean 検査はそのまま走る
- 永続 cache には gitignore 対象の in-tree autotools 生成物が 39 件あった (`config.h`, `*.o`,
  `libjson.a`, `GNUmakefile`, `configure`, `autom4te.cache/`, `.deps/` 等)。
  `hydrate` はこれらを**供給先へ持ち込まない**ことを実測で確認した (staging 側に `config.h`・
  `*.o`・`GNUmakefile`・`libjson.a` はいずれも不在)。cache を consumer へ直接渡してはならない
  という同 README の注意はここで効いている

## 前回の閂 2 本は実際に外れた (実測)

1. **[T-1437] / D615 (mocc protocol の macro 供給表分離)** — 前回 0 セルで止まった
   `source_digest.resolve` を突破した。checkpoint は `protocol-resolution` を通過し、
   `floor-driver` が run_dir を発行して cell build まで進んだ。
2. **[T-1461] (masstree staging 配線の実効化)** — checkpoint に**前回存在しなかった
   `fetchcontent-staging` 段が現れ、entered した**。計算ノード側の受領記録
   (`sort-swo-oracle-dependency.json`) は
   `dependency_head = dependency_expected_head = b3c5d054b66b08374d7a6ff5a0faeaf28b041a38`、
   `dependency_transport_mode = "source-dir"`、
   `dependency_root` は計算ノード scratch 配下の `masstree-src` を示す。
   **masstree は期待どおりの版で計算ノードへ届いている。**
3. **実ビルドが動いた証拠** — build cache
   (`output/s8b-build-cache/contracts/e576e9cd…/`) に `completion.json` と
   実行ファイルを持つ cell が 3 本でき、binary sha256 は 3 本とも異なる
   (`2f5e8938…` / `f76093fc…` / `ec5c5bcc…`)。4 本目は `2437fc79….building` に
   `owner.json` だけを残して失敗した。

## blocker A (一次要因): `sort_best` セル build の失敗理由が永続化されない

### 事象

driver は rc=1 で終了し、stdout に次の構造化 error だけを出した。

- `error: SortSwoOracleUnavailable: sort-swo-oracle-infrastructure-unavailable`
- `phase: floor-dependency-postflight`
- `detail_code: floor-dependency-postflight-build-failed`
- `origin: floor-dependency-postflight:masstree`
- `outcome: execution-failed`

### 根本原因が特定できない理由 (file:line 裏取り済み)

`orchestrator/campaign/s8b_floor_campaign.py:3616` の `build_fn(...)` が送出した例外を、
`:3628` の `except Exception as exc:` が捕捉し、`:3634` の `_floor_postflight_error(...)` が
作る構造化 error へ `raise ... from exc` で**差し替える**。この経路で
**元例外の本文はどこにも書き出されない**。実測でも次のとおりである。

- `floor-driver.stderr` = 0 byte
- `sort-swo-oracle-postflight-failure.json` に例外 message / traceback の field なし
- build は計算ノードローカルの scratch (`/scr` 配下、PBS job id 付き) で行われ、ジョブ終了と
  ともに消える。ログインノードから当該 path は存在しない

### 分かっていること

`.building/owner.json` の `starttime` (epoch 1787479990) と `failure.json` の
`recorded_epoch` (1787479997) の差は **7 秒**である。cell build の制限は
`build_cap_per_cell_s=900` なので timeout ではない。7 秒という短さは、CCBench 本体の
コンパイルではなく **configure 段の即時エラー**を示唆するが、**本試行の記録からは確定できない。**

### 影響範囲

`sort_best` は 12 セルのうち SWO oracle を要求する構成であり、これが通らない限り
床値 campaign は完走しない。前段の 3 セルはビルドできているため、影響は
`sort_best` 系の構成に限局する。

## blocker B (潜在要因・確定): 固定した `archive_sha256` は構造的に再現不能

**blocker A を直しても、その直後の postflight で必ず止まる。** これは今回の実測値と
最小 probe で確定した。

### 機構

`orchestrator/campaign/s8b_floor_campaign.py:3209` の
`_verify_floor_oracle_dependency_postflight` は、build 後に

- `after.config_sha256 != expected_config_sha256` →
  `floor-dependency-postflight-config-expected-mismatch`
- `after.archive_sha256 != expected_archive_sha256` →
  `floor-dependency-postflight-archive-expected-mismatch`

で拒否する。expected 値の正本は
`tools/pegasus/policies/floor_masstree_payload_v1.json` である。

この `archive_sha256` は**ソースの tar ではなく、ビルド成果物である静的ライブラリ
`libkohler_masstree_json.a` の sha256** である
(`tools/pegasus/generate_floor_masstree_payload_policy.py` の `_build_and_hash`)。

### 実測値の不一致

今回の計算ノード側受領記録は次を残した。

| 項目 | 実測 | policy の期待 | 判定 |
|---|---|---|---|
| `dependency_head` | `b3c5d054b66b08374d7a6ff5a0faeaf28b041a38` | 同左 | 一致 |
| `dependency_config_sha256` | `e9a4ecd3dfb9aef9c159e99cb2b7000651a2036ec909095f750b2c891404694a` | 同左 | 一致 |
| `dependency_archive_sha256` | `0a6514a05a143edd081657df678b93ab99aa2b6c29c460b419c6c542f2042bfd` | `9c1034fac8f6ac5b96d6521de9c2b42513560b41e6ec7c22d9150e33e45c30ea` | **不一致** |

pin と `config.h` は一致し、**食い違うのはビルド成果物だけ**である。
なお preflight (`:2856` 以降) は expected 値を binding へ記録するだけで比較しない。比較は
build 後の postflight だけなので、今回は blocker A に先に当たり、この不一致は発火前だった。

### 再現不能である理由

- 生成器は
  `tempfile.TemporaryDirectory(prefix="izanagi-floor-masstree-policy-")` の中で
  bootstrap → configure → make → `ar` を実行する
  (`generate_floor_masstree_payload_policy.py` の `main`)。**呼ぶたびに path が変わる。**
- 計算ノードは PBS job id を含む scratch directory でビルドする。
- ビルド flag は `CXXFLAGS=-g -W -Wall -O3 -fPIC` であり、`-g` があるため object の DWARF に
  `DW_AT_comp_dir` (ビルド directory の絶対 path) が入る。

最小 probe (同一 source・同一 `g++ 11.4.0`・同一 flag、directory だけを変えた 2 本) で実証した。

| ビルド dir | object sha256 | archive sha256 |
|---|---|---|
| probe の `dirA` | `2e14f5f63936a11f8d5df55b6c3ed94e269c301e46a447a563b0e74680d9786e` | `2622c2292be777f0cb3084cc59a00e412a1cddfc88946e432713e5daa889f07c` |
| probe の `dirB` | `6df2b6acad45ac55952667d4d311c82ba8b7b156a7bec634b6dd2e9efa6946e7` | `83358a6e7c70969775e12bbd886eea937f5aff0a7a8f29a3bcdb7726d856e1d9` |

`readelf --debug-dump=info` は各 object の `DW_AT_comp_dir` にそれぞれの絶対 path を記録して
いた。**したがってこの期待値は計算ノードの run と一致しえず、生成器を 2 回走らせても
互いに一致しない。**

### 補強事実

- 当該 policy file は [T-1461] の commit `1488fe68` で新設されたのが唯一の履歴であり、
  **実機 run で一度も一致を確認されていない**。今回が初の実行使用で、初回から不一致だった。
- compiler は計算ノード・ログインノードとも `gcc 11.4.0` で同一であり、**環境差では説明できない**。
  食い違いの出所は期待値の作り方そのものである。
- `config_sha256` が一致することは、configure の出力が再現することを示す。再現しないのは
  **コンパイル成果物だけ**である。

### 影響範囲

`sort_best` セルを持つ全ての floor run (pilot / official を問わない) が、build 成功後の
postflight で `floor-dependency-postflight-archive-expected-mismatch` により
`attempt-infra` 扱いで停止する。**床値が確定しない限り
`s8b_oracle_driver.py gate-check` の `floor-null` refusal は解けず、8b oracle block を
起動できない。**

## この場で修正しなかった理由

- 本 wave の scope は再投入と実測であり、fail-closed の回避や正しさゲートの緩和を含まない。
- blocker B の是正は「ビルド成果物の同一性をどう固定するか」という設計択一を含む。
  再現可能にする方向 (`-ffile-prefix-map` 等でビルド path を正規化する、`ar` を決定的 mode で
  使う、期待値を計算ノード上で生成する) と、述語自体を変える方向 (成果物 bytes ではなく
  ソース同一性 + toolchain manifest で束縛する) は**受理集合が変わる**ため、親の一存で
  決めない。裁定へ返す。
- blocker A は根本原因が未特定であり、診断が残らないこと自体を先に直さなければ、
  再投入しても同じ情報しか得られない。

## 推奨する次の一手

1. **build 失敗の診断を計算ノード外へ残す。** `s8b_floor_campaign.py:3628` の
   `except Exception as exc:` が握り潰している元例外の本文 (と、可能なら configure/build の
   stderr 末尾) を、`marker_root` 配下の失敗 record へ構造化して載せる。これが無い限り
   blocker A の再投入は情報を増やさない。
2. **blocker B の裁定を仰ぐ。** 上記 3 案の受理集合への影響を並べて裁定パッケージにする。
   `config_sha256` は再現するので、束縛を弱めずに再現可能へ寄せる余地がある。
3. **`sort_best` セルの build を floor driver の外で単独再現する。** `--fetchcontent-base-dir`
   は pilot 専用の seam として既に存在するので、hydrate 済み payload を与えて cell build だけを
   計算ノードで走らせれば、blocker A の原因は driver を再投入せずに取れる。
4. 再発防止として、`floor_masstree_payload_v1.json` のような**ビルド成果物 hash の pin は、
   生成器と consumer が同じ環境・同じ path で走ることを検査するテスト**を伴わせる
   ([テスト代表性] gap — 今回の policy は生成されただけで、consumer 経路で一度も検証されて
   いなかった)。

## 一回性 key の消費について

**確認済み: 本試行もチケットを 1 枚も消費していない。** admission root
(`s8b_holdout_admission.shared_admission_root`、全 worktree 共有) 配下に
2026-08-23 00:00 以降に作成・更新された file は 0 件だった
(`attempt-ledger.jsonl` / `ledger.jsonl` / `claims/` / `consumed/` はいずれも 2026-08-16 のまま)。
cell 単位の attempt ticket を消費する段より前で停止したためであり、設計上の予想と一致する。
次回の再投入も `retry_slots_per_cell=2` を全 12 セルぶん保持した状態から開始できる。

## 証拠の所在

- 計算ノード側 checkpoint (15 record): job evidence root の
  `pegasus/940170.nqsv/841537990c502065fb92c79655f47fe7/checkpoint.jsonl`
- job staging (toolchain 実測値・失敗 record・scheduler 出力):
  `output/env/pegasus/floor/job-staging/` の当該 PBS job id 配下
- 投入 receipt: `output/env/pegasus/floor/attempts/submissions/841537990c502065fb92c79655f47fe7/`
- run_dir (journal 2 event): `output/env/pegasus/calibration/s8b-floor-pilot/20260823T101139Z-2c8cf9be/`
- build cache (3 完了 + 1 失敗): `output/s8b-build-cache/contracts/e576e9cd…/`
- wave の作業記録・probe: dev-wave-jobs の
  `dev-wave-t1431-floor-pilot-rerun/`

repo 内の上記 output path は、将来の official 床値 job の起動証明を止める holdout clean-scan
汚染を避けるため、本 wave の記録が済んだ時点で repo 外へ退避する。
