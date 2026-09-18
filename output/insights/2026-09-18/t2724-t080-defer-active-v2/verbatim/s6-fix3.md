## 所見ごとの対応表 (closed / partial / regressed、所見 ID → 変更箇所)

**テスト3ファイルを修正しました。接続系の再走は環境制約で未確認です。commit は作成していません。**

| 所見 ID | 状態 | 対応 |
|---|---|---|
| H1 | partial | delegated campaign-start 3 node の WAL 検査を当該 campaign layout に限定。marker／budget 不作成検査も追加。実走未確認 |
| H2 | partial | shared-base 経路、5要素 key、reader 登録解除、consumer pin を修正。lock deadline 解消は未実測 |
| H3 | closed | production・S・走査除外・hold・allowlist は変更なし |
| F1／F3 | partial | epoch refusal・evaluate 不到達の期待を維持し、残っていた副作用検査の射程を修正 |
| F8／RB-6 | partial | 親の改訂指示に従って登録を戻した。invalid-receipt seam の登録は保持 |
| F2／G2 | partial | 親の fix-2 ログでは接続正例を含む6 node が成功。本巡の共有化後は未実走 |
| F6／RA-6／RB-4 | closed | 最終 sink 座標と2本の直接呼出し成功を確認 |

その他の前巡項目は本巡で変更していません。退行の有無は受入再走が必要です。

## 実装した変更 (file ごと)

`orchestrator/tests/test_s8b_oracle_driver.py`

- `_T080SharedBases.get` を5要素 key に対応。従来の4要素 key と末尾 `False` の key は同じ digest を使用。
- `_t080_stub_free_e2e_repo` に `active_v2_base` を転送し、接続 fixture と draft 負例を共有 base の独立 copy に変更。
- 通常／active-v2／不正 trailer の分離、旧 digest 保持、copy 独立性を検査する test を追加。
- consumer pin を **14関数／20 node** に拡張。既存の11 node は保持。
- 接続経路にも実 output 配下の temp-root 拒否検査を追加。
- WAL 検査を `campaign_layout(_campaign_id(manifest_path), output_root=...)` 配下に限定。実行前検証に必要な複製 binary store は保持。
- 小型 builder double の入力を追随。既存4要素 test の期待値は不変。

`orchestrator/tests/conftest.py`

- 接続・draft の **8関数／9 node** を inventory／both-reader 登録から除去。
- `root=ROOT` を渡す `test_run_block_refuses_invalid_receipt_after_gate_seam` は登録を保持。

`orchestrator/tests/test_real_repo_serialization.py`

- 独立 golden を同じ登録変更へ追随。
- default selection／setup 検査の対象を11→20 nodeへ純増。

## 接続正例 fixture の結果

**本巡の直接呼出しは不能です。** driver module の import が `GrowthTestHoldBypassRefused` で停止しました。hold は解除していません。

静的検算結果：

| 段階 | 確認内容 |
|---|---|
| basis | active-v2 専用除外を初期 commit 前に適用。v1 holdout を保持 |
| R | 実 draft→validate→finalize→R 発行を維持。trailer は cache key に含む |
| selector seed | 独立 copy 内で seed commit を作り、その HEAD に証拠を束縛 |
| protocol | 複製済みの旧 protocol namespace は除去済み。実 ccbench pin を継承 |
| C | certificate 発行 callback が C を作る構造を維持 |
| G | 通常経路の `frozen_at_head=C`、G の直前親が C |
| A／X | generation SHA に対する承認と active pointer を個別 commit |
| load／launch | copy の root に対して実 loader／validator を実行。token は共有しない |

構築費用は、接続8 node の「通常 base 7回＋不正 trailer base 1回」から「各 base 1回＋8 copy」になります。draft は既存の通常 base を共有します。概算削減量は **通常 base 構築6回分−copy費用**。C→G→A→X と launch は各 node に残ります。秒数と5分達成は未測定です。

## 自己検証の結果

- **成功：** 最終差分の `git diff --check`、変更3ファイルの AST parse。
- **直接呼出し成功：** conftest の access-map 構築。独立 golden 148件との一致も確認。
- **静的検算成功：** consumer 14関数／20 node、serialization の exact node 集合、登録解除8関数／9 node、seam 登録保持。
- **直接呼出し成功：** driver sink の既存2 test。最終座標は `pipeline.evaluate:1781`／`evaluate_fn:1794`。
- **import 不能：** driver／serialization は growth-hold guard。
- **predicate 検証未成立：** wrong-activation-head 負例と、m6 をプロセス内属性差替えした反実仮想は、双方とも fixture の `machine-pin: 未対応 site 'PEGASUS_LOGIN'` で停止。kill には数えず、属性は復元済み。

pytest／`tools/run_tests.py` は実行していません。

## 所有外への波及

`grep -rn` で共有 fixture、production caller、memo、driftguards、serialization の生成 script を再列挙しました。

- shared-base の直接利用は driver test module 内に限定。
- `verify_receipt`／adapter／resolver の production signature は本巡で変更なし。
- memo endpoint、`test_s8b_binding_driftguards.py`、受入 tool の consumer は未変更。
- emitter の既存 `_real_bytes(calibration_path)` は各接続構築で実 root を読みます。したがって、**すべての実 root 読取りが base 構築1回だけになったとは言えません**。大きな複製・receipt 発行の共有化と、test 全体の read lock 除去を実装した状態です。

## 変異事前登録への対応 (m0〜m11 の anchor 更新、位置の一意性)

以下は `orchestrator/campaign/` 配下。各 anchor が対象関数内で一意であることを静的確認しました。

| ID | 最終 anchor |
|---|---|
| m0 | `t080_freeze_migration.py:2231` — Historical verification comment |
| m1 | `s8b_ratified_freeze.py:3550` — `if current != expected:` |
| m2a | `s8b_oracle_driver.py:200` — `allowed=not merged,` |
| m2b | 同`:220` — campaign epoch 拒否文言 |
| m3 | `t080_freeze_migration.py:2275` — 非委譲側 `_assert_search_pass(report)` |
| m4a | 同`:2215` — expressions 比較 |
| m4b | 同`:2202` — match_convention 比較 |
| m5 | `s8b_oracle_driver.py:1531` — campaign-start 再解決と後続 epoch 比較 |
| m6 | `t080_freeze_migration.py:2236` — outer activation HEAD 比較 |
| m7 | 同`:2247` — enumeration digest 比較 |
| m8a | `s8b_floor_campaign.py:5534` — clean-scan assertion |
| m8b | `t080_freeze_migration.py:1728` — 単独証拠から除外する前巡裁定を維持 |
| m9 | 同`:2234` — validation root 比較 |
| m10 | 同`:2241` — active-generation 再解決と4要素比較 |
| m11 | F1 裁定により登録除外を維持 |

m5 の `[changed]` anchor は `test_s8b_oracle_driver.py:1795`。late-hit-file は同`:1830`。正式な変異 matrix は未実走です。

## 未完・未実走・懸念

- H1 の3 node、共有 cache の新 test、default selection／setup の再走が必要。
- 両木焦点走、lock deadline 解消、通常受入、所要時間は未確認。
- predicate の反実仮想は fixture 前段で停止しており、有効な kill 証拠なし。
- docs・tracked output・production は変更なし。報告ファイル、commit は作成していません。

## 総括

**fix-3 の修正は実装済み、受入確認は未達です。** 差分はテスト3ファイルに限定し、静的整合と sink 2本の直接検証は通りました。親での両木焦点再走が必要です。