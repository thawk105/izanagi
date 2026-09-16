# [T-2636] B-4 床値の候補・参照バイナリと portable binary record — 実 build から 1 件調達した

`authority: none`
`default_effect: no-state-change`

2026-09-16。wave `dev-wave-t2636-b4-binary-record`、branch `worktree-dev-wave-t2636-b4-binary-record`。
起点 local main `262c2993eae89f452dcea35fc61f97e41a689e8e`。
可変状態の正本は worklog 末尾と現行 phase doc であり、本書ではない。

## 依頼と答え

依頼は「B-4 床値測定用の候補・参照バイナリを build し、`s8b-binary-admission/v3` を内包する
portable binary record を repo へ入れる。較正の取得とは別件。本題の build と record 投入だけ」。

**答え: 調達した。** tracked な portable binary record が repo に 1 件ある。

```
output/insights/2026-09-16/t2636-b4-binary-record/records/rr20--stock_common.json
```

対応する実バイナリは 701,760 bytes、実行権限あり、実 bytes の sha256 が record と一致する。
保管先は repo 外の
`/work/1/SFC/tanab/izanagi-b4-floor-binaries/binaries/7cdf0dc345f7eccdb50604e77521ce625c1792cc0eb8966b544f65a15ef274a4`。

## 何を調達したか (現物の値)

| field | 値 |
|---|---|
| key 数 | 12 (exact。`sort_best` でないので `sort_swo_oracle` は無い) |
| `cell_id` | `rr20::stock_common` |
| `holdout_id` / `configuration_id` | `rr20` / `stock_common` |
| `binding.genome_canonical` | `silo\|BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0` |
| `binary_sha256` | `7cdf0dc345f7eccdb50604e77521ce625c1792cc0eb8966b544f65a15ef274a4` |
| `admission_receipt.schema` | `s8b-binary-admission/v3` |
| `admission.class` / `review_id` | `human-reviewed` / `s8b-floor` |
| `subject.trace` | `false` |
| `cached` | `false` (実 build。cache hit ではない) |
| record blob sha256 | `760287f629ee96c5c0e31c43be7b6dc30bfbf48dd5ebbe4c0da8b5b0b3e389b0` |

親が消費側の検査器を直接通した。`s8b_binary_admission.validate_portable_binary_record(record,
expected_policy=None)` が通り、receipt の `subject.binary_sha256` と record の `binary_sha256` が
一致し、実バイナリの bytes sha256 も一致する。

## 主張しないこと

- **`rr20` は s8b holdout の識別子であって B-4 の workload ではない。** record の identity は
  producer のものである。**この record を別 protocol の床値として説明してはならない。**
- **binary は workload 非依存なので 1 件で 3 spec を覆える。** `Genome` は `(protocol, flags)` だけ、
  `ScalePoint` は `(records, threads)` だけで、workload (rratio) は runner の実行時引数である。
  これは「1 件で足りる」の根拠であって、「rr20 で測った」という主張ではない。
- **spec は作っていない。** 凍結 spec の `artifacts[]` をどう書くか、candidate と reference に
  どの artifact ID を割り当てるかは本 wave の scope 外である。
- **binary を消費 checkout から解決する配置は未定である。** 消費側 `floor_pair_driver` は
  `--repo-root` からの相対 path で regular file を要求する。現在の保管先は repo 外なので、
  凍結 spec を書く wave が配置規則を決める必要がある。

## 採用対象をどう確定したか (段 4 の核心)

段 1 の親 brief も段 2 plan も段 3 の 2 レンズも、そろって「対象 driver と軸が未確定」と扱った。
**誤りである。** `docs/phase3-b4-reflux-ablation-preregistration.md` の §5 表 1 行目は既に

```
base (silo-backoff-magnitude); evidence_set=t2341-eligibility; ... 記入者 = レビュー者 = thawk105 (D1266、D1638)
```

で埋まっている。親が段 4 で現物から拾って閉じた。**凍結文書の記入済み欄を読む**という段 1 の手順が
無いことが、4 者そろって同じ誤認をした理由である。

対照対は D1641 決定 3 と事前登録 §11.2 の逐語どおり **byte 単位で同一の候補**であり、
candidate と reference は同じ binary bytes でよい。spec 上の artifact ID は
`floor_pair_driver.py:851`・`:856` が別々を要求するが、同じ binary path/sha と同じ receipt を
共有することは `:1143` が許す。

## 段 3 レンズ A の「stock 衝突で解けない」を親が反証した

レンズ A は「current clean stock は `build_admission.py:634` で `STOCK_BASELINE` に分類され、
review receipt を渡しても覆らないので `s8b_binary_admission.py:219` の `HUMAN_REVIEWED` 要求と
衝突し、現 scope では解けない」と返した。**refuted。**

stock 分岐の条件は `source.ccbench_commit == CURRENT_PIN` であり、**`CURRENT_PIN` は 7 文字の
短縮形** `"511c953"` (`pin.py:28`) である。floor 経路が `source_digest.resolve_evidence` へ渡すのは
40 桁の gitlink (`511c9538e4e8efa54b45cda62e72389ed3b706ec`) なので、この分岐は発火しない。
実 record の `admission.class` が `human-reviewed` であることが実測の裏取りである。

短縮形と完全形の表現不整合は `pin.py:39-41` が自ら既知の潜在課題として記している。
**real だが本 wave の scope 外。触っていない。**

## 計算ノードでの実走 3 回 — 2 つの停止原因を実測で閉じた

| # | request | elapse | 結果 |
|---|---|---|---|
| 1 | `605.nqsv` | 25 秒 | gflags/glog 導入は成功。toolchain preflight で停止 |
| 2 | `696.nqsv` | 52 秒 | toolchain gate と CCBench build を通過。receipt 発行直前で停止 |
| 3 | (3 回目) | 51 秒 | **成功。record を生成** |

いずれも既登録の `tools/pegasus/dispatch_compute.py --task generic` (main 側
`admission_registry.json` で `class=local-ok`、D895) から起動した。**新規 `tools/pegasus/` 実行体を
作っていないので F660 には当たらない。** 絶対 path による迂回もしていない。

### 停止原因 1 — 較正が束縛する cmake が clean 環境から消える

1 回目が表に出したのは `sort-swo-oracle-infrastructure-unavailable` の 1 行だけで、
実体は job 外に永続化された private JSON の `floor-toolchain-receipt-mismatch` だった。

親が probe を投げて計算ノードの clean 環境を実測し、登録済み較正
`calibration-753f535a8d024727.json` と突き合わせた。

| leg | 較正の束縛 | 計算ノード実測 | |
|---|---|---|---|
| C compiler realpath | `/usr/bin/x86_64-linux-gnu-gcc-11` | 同じ | 一致 |
| C++ compiler realpath | `/usr/bin/x86_64-linux-gnu-g++-11` | 同じ | 一致 |
| compiler version | gcc 11.4.0 | gcc / g++ 11.4.0 | 一致 |
| **cmake version** | **3.25.0** | **3.22.1** (`/usr/bin/cmake`) | **不一致** |

原因は `--task generic` の `env_mode=clean` が `MODULEPATH` ごと環境を落とすことである。
較正取得 job は既定 module 環境 (`module_list=["intelpython/2022.3.1"]`) を持ち、そこに
cmake 3.25.0 が入る。実体は
`/system/apps/ubuntu/20.04-202210/oneapi/2022.3.1/intelpython/latest/bin/cmake` に実在し、
**同 dir に gcc / g++ は無い** (親が現物で確認したので、PATH へ足しても compiler の leg は動かない)。

対処は `--path-prepend` で実在する道具の directory を PATH 先頭へ置くことである。
**一致要求は緩めていない。** `floor_toolchain_matches` も `_bind_current_toolchain` も編集していない。
やったのは「登録済み較正が指す実物の道具を実際に PATH 上へ置く」ことだけである。

### 停止原因 2 — build が使った masstree root を receipt 発行へ渡す経路が非 sort に無い

2 回目は `current FetchContent masstree root is required` で止まった。因果は次のとおり。

1. `buildcache.py:2912` が build 成功時に実 CMake cache から masstree の実効 root を読む。
2. その結果 `s8b_compiler_input.py:1313` が compiler input を `fetchcontent-masstree` に分類する。
3. `s8b_floor_campaign.py:4587` の `issue_binary_admission_receipt` は
   `current_compiler_input_masstree_root` を **sort_best 専用の `dependency_binding` からしか取らない。**
4. よって非 sort では None が渡り、`s8b_compiler_input.py:1113` が拒否する。

**検査が過剰なのではなく、渡す経路が無い。** 同種の情報である `compiler_input_dependency_prefix_roots`
は既に `BuildResult` 経由で `s8b_floor_campaign.py:4541` が受けており、masstree root だけが
その経路を欠いていた。同型の additive な field を 1 本足し、build 成功時に既に読んでいる実効 root を
そのまま載せ、floor 側は `dependency_binding` が無いときだけそれを使う。

**受理側の変化は意図したものである** — 正しい masstree 入力を使った非 sort build が、root の
伝達漏れだけで拒否されなくなる。**拒否側は不変で**、root 不在・root の重なり・per-entry の
実 bytes hash 不一致はいずれも従来どおり拒否される。`s8b_compiler_input`・`s8b_binary_admission`・
`build_admission` は編集していない。sort_best 経路の値と分岐は 1 bit も変えていない。

この変更は段 4 裁定の「既存 producer を編集しない」を覆す。**実測が制約を覆したので親が明示的に
再裁定した** (`DW-O12`)。

## 段 6 の敵対レビュー 2 本が実走前に見つけた欠陥

レンズ A (正しさ・恒真化・record の意味) とレンズ B (API 整合・実行時の現実性) を並列で回した。
**実走で顕在化する前に 7 件を閉じた。** 特に効いた 2 件は次である。

- **durable な複製に実行権限が無い。** `store_binaries` は `open(tmp, "xb")` で作って hard link
  するだけなので実行ビットが付かない。sha 一致は実行可能性を保証しない。消費側は実際に exec する。
  これは record が受理されても**測定できない**状態を作る。
- **非 sort に offline 依存が届かない。** `external/ccbench/CMakeLists.txt:43` の
  `include(ThirdParty)` は無条件で FetchContent を走らせるのに、floor producer は sort_best にしか
  依存引数を渡さない。計算ノードは外部ネットワーク不在なので configure で落ちる。

レビューが反証した所見も記す。`binary` を store 複製へ書き換えても bytes 同一性検査は恒真にならない
(書換えは store 完了後で、store 自身が元 bytes の sha を照合している)。`build_fn` seam は
production 分岐・admission・descriptor を落とさない (`prepare_fn is prepare_cell` が成立する)。

## 変異 matrix

`repo_head = e7dffed7adb583de00cc683c08bb03d8d2a34e15`。runner は
`python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_b4_binary_record.py -rf`、
`--runner-mode dispatch`。

**baseline = PASSED、7/7 KILLED、SURVIVED 0、MISMATCH 0、期待 node 完全一致。**

| id | 変異 | 殺した node |
|---|---|---|
| M1 | cell 選択から stock 絞り込みを外す | `test_stock_selection_and_explicit_holdout` |
| M2 | `store_binaries` を飛ばす | 4 件 |
| M3 | portable record validator を外す | `test_real_store_projection_validation_and_single_json` |
| M4 | `prepare_fn` を production でないものにする | `test_production_wiring_and_environment_restore` 3 param |
| M5 | 出力を create-only から上書きへ | `test_create_only_preserves_existing_output` |
| M6 | durable binary の実行権限付与を外す | `test_real_store_projection_validation_and_single_json` |
| M7 | PATH を復元しない | `test_cli_path_prepend_and_restore` 6 param |

**M3 と M6 は同じ node を殺すが、赤の assertion は別である** (`DW-M03` の単一理由性)。
親が probe 走の job stdout で確認した — M3 は validator 呼出しの assert (`test_b4_binary_record.py:59`)、
M6 は `assert os.access(..., os.X_OK)` で落ちる。

probe 走 (全件 SURVIVED 登録で観測 node を集める `DW-M08` の手順) の結果は
`mutation-probe-result.json`、本走は `mutation-final-result.json` に置く。

## 実装子が上限で打ち切られた 1 件

producer 側の経路追加 (F10) を担当した Codex 子は壁時計上限 3600 秒で打ち切られ、
**完了報告を 1 byte も出していない** (`limit_trigger=wall_clock_admission_bound_s`、134 model call)。
原因は login node で `test_s8b_floor_campaign.py` (545 件) を走らせたことだと推定する。
同じ集合は計算ノードへ dispatch すると 60 秒で終わる。

編集だけが作業ツリーに残ったので、**親が差分を逐行監査し、独立の read-only 子に再監査させた**。
再監査は must-fix ゼロで、攻め筋 5 本 (受理集合の拡大・sort 経路の上書き・positional 構築の破壊・
恒真な新規テスト・台帳 pin の緩和) をすべて反証した。

## 実走の記録

- 焦点走 (計算ノード): `test_s8b_floor_campaign.py` + `test_buildcache.py` + `test_b4_binary_record.py`
  = **545 passed / 3 skipped / rc=0** (60.8 秒)。
- login: `test_ccbench_spawn_sites.py` 47 件、`test_acceptance_schedule_order.py` 79 件、
  `test_p3_build_authority_cli.py` 19 件、`test_plain_runner_coverage.py` 3 件、
  `test_b4_binary_record.py` 23 件がいずれも rc=0。
- 受入全走の結果は worklog へ書く。

## real だが scope 外 (裁定パッケージ候補)

1. 消費側は B-4 採用の意味的一致も人間の review 行為も機械認証しない (段 3 レンズ A)。
2. login node での build 一般は不可能ではない。`t152_write_intent_coverage` と
   `silo_ladder_rung1` の直接 CMake 経路には site gate が無い (段 3 レンズ B)。
3. `pin.py` の短縮形 / 完全形の表現不整合。
4. `buildcache._run` は非ゼロ終了時に stderr 末尾 800 文字しか例外へ載せない (段 6 レンズ B)。
5. cache hit 経路では新 field が空のままである。正式 S8b 経路で hit が起きない理由は
   `buildcache.py:2456` にあるが、root 伝達が cache hit まで実装されたとは言えない (段 6 監査子)。
