## 変更 file 一覧

**段5は一部未完です。** 新規5 file、既存11 fileを変更しました。

新規：

- `patches/mocc-temperature-predicate-variant.patch`
- `patches/instr-mocc-lock-coverage-temperature.patch`
- `orchestrator/campaign/axis_mocc_temperature.py`
- `orchestrator/campaign/s3_mocc_template_proof.py`
- `orchestrator/tests/test_mocc_template_proof.py`

既存：auditor.md、review_ledger、originless baseline、condition gate 本体・fixture・test、materializer 登録、screening defaults、build authority test、spawn site test、campaign の期待表。

adapter と `liveness-run.sh` は配置未完です。

## template と計装 template 版の検査結果

| 検査 | 結果 |
|---|---|
| template → e9e477ca | rc=0 |
| template → 511c9538 | rc=1、transaction.cc の context 不一致 |
| 新計装 → template 適用後 | rc=0 |
| 旧計装 → template 適用後 | rc=1 |
| 新計装 → template なし | rc=1 |
| syntax、TRACE×predicate の4組 | 全 rc=0 |
| 計装あり syntax の4組 | 全 rc=0 |

- `#line` 実測：`36 / 1025 / 1026 / 1193 / 1204 / 1222 / 1230`
- offset：`19 / 35 / 35 / 35 / 35 / 35 / 35`
- 旧新計装の追加本文・操作前後 context・復元番号：一致。
- OFF の実 `g++ -E -P`：helper 消失を確認。
- 論理行列：OFF 543行、ON-B 548行。それぞれ計装なし／ありで一致。

## 軸 module・driver の設計と CHECK_KEYS / MATRIX

`CHECK_KEYS` は順序固定30項目、`MATRIX` は W/U × hot/cold/default × t1/t4 の12走です。

束縛、auditor 射影、計装保存、DQ 13＋deny-only 4対照、旧証拠参照、5 build・逐次保存処理を実装しました。空入力では全 check が false になります。

実 resolver の OFF=stock／ON-B≠stock は検査済み。**driver の5 build・12走・完成JSON生成は実装済み・未実走**です。

## auditor.md の追記と pin 3 箇所の実測 sha

本文 SHA-256：

`dc63a3118393503f7eed4952478f0aa34690b344ee1ca98915e455e210165f34`

- ledger：更新済み。
- originless baseline：更新済み。6件置換の assert を import 時に確認。
- adapter：renderer の生成は成功しましたが、書込みは **read-only filesystem、Errno 30** で失敗しました。

`check_codex_agents.py` は adapter parity drift により rc=1 です。

## 登録簿の変更と件数 pin の実測値

| 項目 | 実測値 |
|---|---:|
| define supply | 40 |
| compile-time witness | 16 |
| cache route | 23 |
| Counter pin | 36 / 40 / 26 / 26 |

NON_ADMISSIBLE 登録、defaults、軸期待表も追加済み。新しい直接 subprocess site はありません。

## 実走した検査

| 範囲 | 結果 |
|---|---|
| 新 `test_mocc_template_proof.py` 全13 node | 11緑、指定2 node赤 |
| 旧 `test_mocc_mutation_proof.py` 全11 node | 全緑 |
| 旧 `test_mocc_proof_surface.py` 全18 node | 全緑 |
| `test_condition_meaning_gate.py` 全126 node | 全緑 |
| `test_ccbench_spawn_sites.py` | 初回69緑・2赤・既存2 skip。件数修正後、赤2 node再走で緑 |
| `test_p3_build_authority_cli.py` 自走19 node | 全緑 |
| `test_codex_agents.py` 自走 | 38緑・7赤 |

新テストの赤はJSON不在による次の2件だけです。

- `test_mocc_mutation_surface_requires_auditor_live`
- `test_mocc_template_proof_json_is_complete_and_bound`

指定の以下3 nodeも緑です。

- `test_materializer_registry_covers_all_python_build_launches`
- `test_all_naked_izanagi_macro_patches_are_registered_or_allowlisted`
- `test_axis_driver_source_rel_within_edit_surface`

Codex test の赤は adapter 未更新関連6件と、自走 harness の引数不足1件です。originless file は自走入口がなく、指定コマンドでは import のみ。2 test関数は未実走です。

## 波及の静的列挙

- plain-runner 閉包：新fileに `_run()` を実装。
- duration ledger：新nodeは未計測。変更していません。
- `_DEFERRED_GATE_MEMBERS`：集合・行番号とも変更なし。
- B-4 の47 module pin：変更なし。`p3_s4_loop` への新importなし。
- role adapter を消費する checker・test：更新待ちで赤。

旧32／14 check、旧5 patchとwitness、旧JSON、Silo gate、auditor型番号1〜21 schemaは変更していません。

## 総括

**R11の生死確認scriptと、R20のadapter pin更新が未完です。** job dir は書込み許可範囲外、`.codex` は read-only でした。R21のcompute・n=1は親側の未実施事項です。

`.scratch-t2773/` は削除済み。最終 `git status --short` は所有範囲の **11 modified＋新規5 fileのみ**で、scratch残骸・submodule変更はありません。仮JSONは置いていません。