# [T-1835][T-1718] 事前ビルド道具の身元を生成物への独立期待権威で照合する

wave branch: `worktree-dev-wave-t1835-t1718-tool-identity`
実装 commit: `0e8272d3a268ba6bad185607e9a12d542017130d`

## この wave が越えた壁

archive に独立した期待権威を置く試みは、本 wave が初めてではない。

- 2026-08-23、`tools/pegasus/policies/floor_masstree_payload_v1.json` は
  `archive_sha256` = `9c1034fac8f6ac5b96d6521de9c2b42513560b41e6ec7c22d9150e33e45c30ea` を持ち、
  postflight に `floor-dependency-postflight-archive-expected-mismatch` があった。
  計算ノードの実 run は `0a6514a05a143edd081657df678b93ab99aa2b6c29c460b419c6c542f2042bfd` を観測し、
  **初回使用で不一致**になった。pin と `config.h` は一致し、食い違ったのはビルド成果物だけだった
  (`output/insights/2026-08-23_t1431-floor-pilot-rerun/README.md`)。
- 2026-08-24、commit `b913bb6e5` が
  "replace the non-reproducible masstree archive byte pin with source, config, policy, and
  toolchain-manifest bindings" として撤去した。
- 撤去後に残った `expected_toolchain_manifest_sha256` は realpath + version の束縛であり、
  **D1076 が明示的に却下した「検証済み絶対 path への束縛」**に該当する。
  D1076 (2026-08-27) は撤去より後のユーザー裁定である。

本 wave の新規性は、その壁を越える手段を実測で示した点にある。

## 実測 1 — raw bytes は path 依存で再現しない

同じ pin (`b3c5d054b66b08374d7a6ff5a0faeaf28b041a38`) を 2 つの異なる path で
`external/ccbench/cmake/ThirdParty.cmake` の recipe どおり build した。

| 対象 | archive raw sha256 |
|---|---|
| build A | `7550d87d690852179b9acd30b6615bf343cc3c58743760ca2deab4e3f671532a` |
| build B (別 path) | `7c251d066da70cbc6d5d6ed89fe3a0d1f775a39465aba7e8eb7258014242af50` |

11 object すべてが相違した。`config.h` は両方 `e9a4ecd3df…` で、
committed policy の `config_sha256` と完全一致した (probe が実 recipe を再現している証拠)。

## 実測 2 — 相違の原因は build dir path だけで、build 自体は決定的

- 同一 path で 2 回独立に build → archive 完全一致 (`b83840491d…`)。
- `-ffile-prefix-map` で build dir を正規化すると、異なる 2 path でも一致 (`68572e60e4…`)。
- `ar cr` は deterministic mode で動作しており timestamp / uid は漏れていない
  (`ar: 'u' modifier ignored since 'D' is the default`)。
- 道具: GNU ar 2.38、gcc 11.4.0。

## 実測 3 — 非 debug 射影は 6 本の独立 build で 1 値に収束する

production 実装 (`orchestrator/campaign/masstree_archive_projection.py`、
射影 ID `gnu-ar-elf-nondebug/v1`) で測った値。

| 対象 | 非 debug 射影 |
|---|---|
| 生成器の二重 build (build-a / build-b) | `844334920db6592852abaa36b2320929bbaf16a7323a7b011ec821dfed7bd514` |
| 共有 third-party cache の archive (2026-08-24 生成、別 process・別 path) | 同左 |
| login build A | 同左 |
| login build B (別 path) | 同左 |

**distinct 値は 1。raw sha256 は全経路で相異なる。**
親の使い捨て probe で section 単位に突き合わせた結果、
非 debug section は 1 つも相違しなかった (`.symtab` / `.strtab` / `.comment` を含めて byte 一致)。
したがって除外集合は `.debug*` 族だけで足り、`objcopy` / `strip` / `readelf` は不要である。

## 実測 4 — compiler の期待値は既存 receipt から到達可能

- Mocc pilot receipt 37 件の `environment.compiler.version` は全文 1 種。
- 計算ノード calibration receipt
  (`output/env/pegasus/calibration/job-staging/0:892707.nqsv/acquisition-receipt.json`) の
  `toolchain.compiler_version` は `gcc (Ubuntu 11.4.0-1ubuntu1~22.04.3) 11.4.0`。
- login node の gcc / g++ を実 `tool_version_body()` で正規化した digest も同じ
  `b713e6ab62b67126b772f6b0a8d9751070f0d0315c7017291cb5dde67747b9c0`。

`tool_version_body()` は起動名の第 1 token を落とすため、gcc と g++ の body は同一になる。
これは role 混成を検出できないという限界を意味する。

## 期待値の発行

裁定した発行経路 (`tools/pegasus/generate_floor_masstree_payload_policy.py` の二重 build) を
pinned-clean な masstree checkout に対して実行し、rc=0 で次を得た。

```
build-b clone_root=/tmp/izanagi-floor-masstree-policy-q7v5j080/build-b/masstree-src
  config_sha256=e9a4ecd3dfb9aef9c159e99cb2b7000651a2036ec909095f750b2c891404694a
  archive_nondebug_sha256=844334920db6592852abaa36b2320929bbaf16a7323a7b011ec821dfed7bd514
  archive_sha256=5af77fd98d5ee7249e24f401ba093c3be202d31e537536212510153361346b85
```

発行元は login node である。計算ノードで実際に build した archive の射影は測っていない。
食い違えば gate は fail-closed で発火し、期待値を再発行すれば回復する。黙って通ることはない。

## 変異 matrix

probe → 再照準 → 本走の 3 段で回した。台帳の逐語は
`mutation-spec-final.json` / `mutation-ledger-final.json` / `mutation-ledger-probe.json`。

**本走: baseline PASSED、10/10 KILLED、SURVIVED 0、MISMATCH 0、matching 10。**

probe を回した価値があった。初回登録の `MUT-T1835-MU2-RELOC-TARGET-RETAINED` は
`relocation_target is not None` を `is None` へ倒す形で、非 relocation section に対して
`AttributeError` を起こし **parser 全体を壊して 20 node を落としていた**。
これでは赤理由が 1 つに絞れない。rejection の `raise` だけを `pass` へ倒す外科的な形へ再照準し、
本走では狙った負例 1 件だけが赤になることを確認した。
probe なしで本走していれば、効いていない機構を効いていると誤認していた。

`MUT-T1718-MU8` と `MUT-T1718-MU10` は同じ node
(`test_mocc_trace_policy_parser_emits_17_values_and_rejects_duplicates`) を落とす。
別々の原因が 1 つの test に載っている形であり、各変異は単独で自分の理由により赤にする。

## 段 6 敵対レビューが見つけた構造的な穴

レンズ A が見つけた最も重い所見は、射影の除外条件の穴である。
`.debug` で始まる名前を持つ relocation section (`SHT_REL` / `SHT_RELA`) は、
その `sh_info` が **live (非除外) section** を指していても hash から落ちていた。
つまり細工した archive が、射影値を変えずに実コードの再配置を書き換えられた。
非 ALLOC・非実行・許可 type の条件だけでは塞げない経路である。
fix で、除外対象が relocation のときは `sh_info` の指す先も除外対象であることを要求する
fail-closed 条件を足した (`MUT-T1835-MU2` がこの gate を守る)。

## 覆した前提

- 親 brief の「`config.h` 一致が実 recipe 再現の証拠」は強すぎる。
  configure 段の再現しか示さず、make / ar / ranlib は argv の同一性でしか裏取りしていない。
- 段 2 プランの「T-1718 は gcc の計算ノード初回 probe が land 前に必須」は誤り。
  計算ノード receipt に gcc の全文があり、body digest は g++ と同一である。
- 親 brief の「道具が変わったことを検出する」は強すぎる。
  直接検出するのは archive 射影または version body の差である。

## ユーザー裁定へ返す 3 件

1. mocc の期待値が submit authority に束縛されていない。policy を一時変更して読ませ、
   pre-judgment capture 前に戻せば通る。`submit_mocc_trace.sh` へ policy raw SHA と
   compiler mapping を捕捉し、job 側 raw bytes・shell 変数・最終 receipt の三者照合が要る。
2. non-sort floor build / mocc の CCBench build / 通常 buildcache consumer へ同じ期待権威を
   広げるか。`buildcache.py` 所有 wave の終了待ちが要る。
3. T-1718 の保証水準を「version drift 検出」に留めるか、role 混成と launcher まで含む
   compiler identity を要求するか。後者なら固定 C / C++ challenge の出力照合が要る。
