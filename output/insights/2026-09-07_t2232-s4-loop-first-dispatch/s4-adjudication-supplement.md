# 段 4 裁定追補 — 初回投入の実測後

C3 が留保した「実測で欠陥が出た場合の修正の要否」を、job `981655.nqsv` の結果を見て裁定する。

## 実測結果 (job 981655.nqsv、bnode116、Elapse 9S、driver_rc=1)

通った層 (初回投入で実機確認できたもの):

| 層 | 結果 | 根拠 |
|---|---|---|
| host gate (`bnode[0-9]+`) | 通過 | `IZANAGI_RESERVATION_HOST=bnode116` |
| 環境 sanitize と PATH 固定 | 通過 | 後段まで到達 |
| (P3) `python3.10` 解決と shim | 通過 | `python_realpath=/usr/bin/python3.10`、sha256 記録 |
| expected HEAD / superproject clean | 通過 | 後段まで到達 |
| CCBench pin exact 照合 | 通過 | submodule を PIN へ checkout 済み (所見 1) |
| (P2) `/scr/$USER` の scratch | 通過 | shim dir 作成が成功 |
| (P4) `qstat -f` の reservation 束縛 | **通過** | `reservation.json` に 8 変数すべて。`REQUESTED_S=10800`、`SCHEDULER_STARTED_EPOCH=1788787806`、`DEADLINE_EPOCH=1788798606` |
| (P7) claim root の provisioning | **通過** | `submit-tree/output/env/pegasus/claims` が 0700 で存在 |
| third-party 3 本の scratch 複製 | 通過 | prebuild へ到達 |

止まった層:

- **(P5) masstree の FetchContent 事前構築が configure で失敗した。**
  `MasstreeFetchContentError: configure failed (rc=1): Could NOT find gflags
  (missing: gflags_LIBRARY_FILE gflags_INCLUDE_DIR)`、
  発生箇所は CCBench の `cmake/Findgflags.cmake:9` ← `CMakeLists.txt:33`。
- (P6) attestation の exact 照合には**到達していない**。driver は起動していない。

## D1 — gflags/glog が計算ノードに無いのは job body の欠落 (real)

原因は環境の偶発ではなく、job body に**依存の供給経路が無い**ことである。

- 兄弟 job body は自前で建てている。`tools/pegasus/floor_scoping.sh:218-290` が policy の pin から
  gflags と glog を `$TMPDIR` へ configure / build / install し、
  `export CMAKE_PREFIX_PATH="$GFLAGS_INSTALL_DIR:$GLOG_INSTALL_DIR"` してから CCBench を configure する
  (同 script の出典表記は `floor_campaign.sh:703-878`)。
- `p3_s4_loop_pegasus.sh` は逆に `unset CMAKE_PREFIX_PATH` するだけで、gflags/glog を建てない。
- 供給元は実在する。`tools/pegasus/policy.json` の
  `gflags_source_path=/work/SFC/tanab/github/gflags` (pin `e171aa2d15ed9eb17054558e0b3a6a413bb01067`)、
  `glog_source_path=/work/SFC/tanab/github/glog` (pin `8f9ccfe770add9e4c64e9b25c102658e3c763b73`)。
  **両方とも実在し、HEAD が pin と exact 一致し、clean である**ことを本 wave で実測した。
- `fetch_third_party.py` の cache root に gflags/glog は無い (masstree / mimalloc / googletest の 3 本のみ)。
  したがって hydrate 経路の拡張ではなく、floor 系と同じ policy 経由の prologue が対応する形である。

## D2 — 本 wave では実装しない (scope 外、裁定パッケージへ送る)

段 1 brief の scope は「scope 外: 予測された障害の先回り修正、attestation 照合の緩和、
**job body の機能追加**、一般化」と凍結してある。gflags/glog prologue の追加は job body の機能追加に
当たる。`DW-O12` により凍結は自分が直前に書いたものでも拘束するため、本 wave では実装しない。

純粋な移植ではなく設計択一が残ることも、送る理由である。

- prologue が policy.json を読むなら、この job body に policy 依存が新設される (現在は非依存)
- floor 系は provenance file 群 (`gflags-configure.stdout` 等) を記録する。s4 でも記録するか
- 契約テスト `test_p3_s4_loop_job_contract.py` (44 node) と admission registry の同時更新が要る
- `-j` と timeout の値、`CMAKE_PREFIX_PATH` を driver 本走まで持たせるかの束縛

## D3 — 所見 1 (README §7 の手順欠落) も裁定パッケージへ送る

`tools/pegasus/README.md` §7 の手順どおりに投入すると必ず rc=2 になる。
docs 修正は 1 行で済むが、これも「本題の実装だけ」の外なので、推奨案として返す。

## 結論

実装面の差分ゼロを維持する。変異 matrix は `DW-S04` により免除。受入全走は実施する。
