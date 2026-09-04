# [T-2253] 変異台帳

対象 commit: 590f2425f983d8753db54b735dd5295a7a921ff8 (段 6 fix 後の最終実装 commit)。
runner: `python3 tools/run_tests.py --force-dispatch test_p3_s4_loop_sort.py test_p3_s4_loop.py test_buildcache_v2.py test_build_site_gate.py -q -rf` (dispatch、計算ノード)。
baseline: 666 passed (PASSED)。

## 走行

| 走 | spec | sha256 | 結果 |
|---|---|---|---|
| probe | `mutation-probe-spec.json` (18 件、全件 SURVIVED 期待で観測 node を集める) | 2c1ccb4f8812feb477c6204915b9f32c328e914ed19954ef4493601910789d3a | 17 件 MISMATCH (赤 = 期待どおり)、M14 SURVIVED。`mutation-probe-out.json` |
| 本走 | `mutation-final-spec.json` (観測 node の完全集合を KILLED 期待、M14 SURVIVED) | 52c2d64a9ab01ed60a975e566c03dd1a0c65ce44577997d73d8c45862c852f73 | **17/17 KILLED (node 完全一致)、1 SURVIVED (M14)、harness rc=0** |

## 事前登録との差 (erratum)

- 段 4 (C3) は M1〜M14 を登録した。段 6 レビュー B が M8 / M11 の過剰決定を予測したため、実装後に単一理由の再照準
  M16 (NUL 拒否の除去 → T10)、M17 (v2 fresh 出口 → T8[v2-fresh])、M18 (legacy hit 出口 → T8[legacy-hit]) と、
  再照合の resolver 転送 M15 (→ T9) を足した。事前登録の 14 件はすべてそのまま走らせた。
- M14 の等価変異は `or not sort_oracle_contract_id` → `or sort_oracle_contract_id == ""` (直前の `type is not str` 検査で
  str 以外は到達しないので同値)。

## 帰属の分類 (DW-M03)

| 区分 | 変異 | 赤 node | 判定 |
|---|---|---|---|
| 単一理由 (単独変異の証拠) | M1 | T1 `test_require_sort_oracle_contract_accepts_only_running_contract` | producer の一致検査 |
| 〃 | M2 | T2 `test_sort_driver_forwards_producer_contract_to_run_campaign` | driver → run_campaign の転送 |
| 〃 | M9 | T10 `test_sort_binder_exact_preimage_and_rejections` | preimage の domain 文字列 |
| 〃 | M10 | T4 `test_resolved_src_token_rejects_both_bindings` | 相互排他 |
| 〃 | M12 | T8[v2-hit] | v2 hit 出口の再照合転送 |
| 〃 | M13 | T8[legacy-fresh] | legacy fresh 出口 |
| 〃 | M15 | T9 `test_recheck_source_evidence_forwards_sort_contract_to_resolver` | 再照合 → resolver |
| 〃 | M16 | T10 | NUL 拒否 |
| 〃 | M17 | T8[v2-fresh] | v2 fresh 出口 |
| 〃 | M18 | T8[legacy-hit] | legacy hit 出口 |
| 過剰決定 (冗長 gate、単独証拠から外す) | M8 | T10, T12, T13 (3 node) | binder が raw を返す → T12 / T13 も raw alias を検査するため同時に赤 |
| 〃 | M11 | T7, T8[v2-fresh], T8[v2-hit] (3 node) | build_v2 wrapper の欠落は v2 両出口も同時に壊す |
| drift mask (冗長 gate に吸収) | M3, M4 | 58 node (`mutation-drift-mask.json`) | `loop.py` は contract-loader の HEAD blob 束縛 file。任意の 1 行変更が `run_campaign` 内の drift 検査で先に止まり、owner のはずの T5 も mask 内。**T5 の単独帰属は変異では示せない** (静的論証: lens B 予測表) |
| drift mask + 固有 owner | M5 | 58 + T6[legacy], T6[v2] | pipeline pre-build resolver の欠落 |
| 〃 | M6 | 58 + T6[legacy] | legacy build_options |
| 〃 | M7 | 58 + T6[v2] | v2 common |
| 等価 (harness の正例) | M14 | なし (SURVIVED) | 生成 bytes 不変 |

単一理由と確認できたのは 10 件。M3 / M4 は DW-M03 に従い単独変異の証拠から外す (drift mask は変異の意味を見ていない)。

## 注入実在

全 18 件の `old` は対象 file にちょうど 1 箇所 (親が spec 生成時と本走直前の HEAD で機械確認)。
M14 の SURVIVED は mutated 内容の diff で注入実在を確認済み (harness の `anchor_counts` = 1)。
