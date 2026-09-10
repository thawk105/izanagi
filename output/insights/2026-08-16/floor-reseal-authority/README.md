# 床値 protocol の再封印を AI へ開放する — 材料 (2026-08-16)

wave = `floor-reseal-authority` / branch `worktree-dev-wave-floor-reseal-authority`

2026-08-16 のユーザー裁定 (案 1 + 案 3) を実装した wave の一次資料。
逐語控えの正本は `/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-16-floor-reseal-ai-authority.md`。

## 何を land したか

**AI が発行できる床値 protocol の issuer と、(環境契約 hash, ccbench pin) の組 index。**
実 repo へ protocol artifact は 1 件も追加していない。consumer 6 件の resolution 切替も行っていない。
したがって本 wave の成果は **dormant な issuer と index** であり、
「案 1 + 案 3 実装完了」「正しさ防壁が閉じた」とは記録しない。

## 段 1 の実測 (すべて read-only、実装差分ゼロ)

| # | 実測 | 値 |
|---|---|---|
| M-1 | 封印済み protocol の `ccbench_pin` | `d706650cdb31e442bef45b9b4216951d4fb40969` |
| M-2 | HEAD の `external/ccbench` gitlink | `511c9538e4e8efa54b45cda62e72389ed3b706ec` |
| M-3 | `s8b_approved.CCBENCH_FULL_SHA` | `511c9538e4e8efa54b45cda62e72389ed3b706ec` |
| M-4 | 封印済み protocol の `contract_sha256` | `e576e9cd…e242c01` (pegasus g1) |
| M-5 | active 環境契約 (activation serial 1) | pegasus g1。g2 は登録済み・非活性 |
| M-6 | 封印 path | `output/s8b-freeze/floor_protocol.json` 固定・create-only |
| M-7 | 凍結チェーン検証 | `freeze_verification_hold.HELD = True` (解除はユーザー明示命令のみ) |
| M-8 | 保留中の該当 check | `s8b-floor.protocol-bytes-expected-pin` / `s8b-floor.sealed-protocol-ccbench-pin-current-head` |
| M-9 | 床値 campaign の protocol | 固定 1 本 (`tools/pegasus/floor_campaign.sh:947`) |
| M-10 | 封印済み protocol の live admission | **今日も PASS**。`validate_protocol` は `ccbench_pin` を HEAD と cross-check しない |
| M-11 | 承認定数から今日組み立て直した protocol と封印済みの差 | **`ccbench_pin` の 1 field だけ**。他 17 key は完全一致 |
| M-12 | 組み立て直した canonical sha256 | `2c8cf9be929d83653814ecf5f2d5ed134a2af89686d796b8144da2fd45dfa58a` |
| M-13 | 固定 path を参照する production consumer | Python 5 件 + shell 1 件 = 6 件 |

**M-10 は親 brief の初稿を訂正した実測である。** 「再封印しないと今日何も走らない」は成り立たない。
止まっているのは凍結チェーン側の 2 検査で、それは 2026-08-12 の裁定で保留中である。
正しい記述は「記録された測定条件が実体と食い違ったままで、新しい組で真正な物差しを封印できない」。

**M-11 は裁定の実データ裏づけである。** 「2 field だけ動かす」は、今日の実 repo では
literally 1 field の差にしかならない。

## 段 4 裁定の要点

`verbatim/s4-adjudication.md` が正本。設計の確定形は次のとおり。

- **D1** path = `output/s8b-freeze/floor-protocols/<contract_sha256>--<ccbench_pin>.json`。組から一意導出。
- **D2** `_CHAIN_RECORD_PATTERNS` へ exact pattern を登録する。**これが無いと versioned protocol を
  1 件置いた瞬間に launch certificate の未知 file 拒否が発火し、既存 campaign が止まる**
  (親が `_assert_freeze_allowlist` の `rglob` を読んで実測確認)。
- **D3** 既裁定 Q3 (両成分がともに交代) の機械化として、target contract が index に既出なら拒否する。
- **D4** lineage anchor は working tree でなく固定 HEAD commit の 100644 blob から読む。
- **D5** 恒真ゲートを積まない。publish 直前の env contract 再照合は削除した
  (authority snapshot は PID ごとに cache されるため必ず一致する)。
- **D6** 成果は dormant。consumer 結線と実発行は g2 活性化と同一 chain の後続 wave。

## 敵対検証の結果

| 段 | 子 | 判定 |
|---|---|---|
| 段 3 | レンズ A (正しさ防壁) | NO-GO (blocker 4) |
| 段 3 | レンズ B (整合・実効性) | NO-GO (blocker 2) |
| 段 6 | レンズ C (裁定との乖離・gate の歯) | NO-GO (blocker 1) |
| 段 6 | レンズ D (回帰・検出力) | NO-GO (blocker 1) |
| 段 6 | 焦点再レビュー 第 1 回 | NO-GO (blocker 1) |
| 段 6 | 焦点再レビュー 第 2 回 | **GO** |

親が実測で裏取りした重い所見:

- **launch certificate の未知 file 拒否** (`s8b_floor_campaign.py` の `_assert_freeze_allowlist`)。
- **`env_contract` の authority snapshot は PID ごとに cache される**ため、
  publish 直前の再照合は**恒真**になる (`env_contract.py:576-586`)。
- **`validate_protocol` は `master_seed` / `stock_configuration` を非空 str、
  `wired_min_rel_floor` を範囲でしか検査しない**ため、working tree の anchor を
  lineage authority にすると、validator を通る改変値が全 successor へ継承される。
- **ratified freeze の `floor_protocol` pointer は任意 canonical path を受理する**
  (`s8b_ratified_freeze.py` の `_closure_entries` / `_assert_canonical_relative_path`)。
  組の一意性は sanctioned namespace 内に限る。

## 変異 matrix

`mutation/` が正本。runner scope = `test_s8b_protocol_builder.py` + `test_s8b_floor_contract.py`
(`--force-dispatch`、`-rf`)。

- **probe 走 (spec-probe / result-probe)**: baseline PASSED、12 変異すべて赤、SURVIVED 0。
  7 件が期待 node と完全一致し、5 件は親の期待集合が不足していた。
  ここから失敗 node の完全集合を再導出した (DW-M08 の probe + 再登録)。
- **本走 (spec-round2 / result-round2)**: baseline PASSED、
  **KILLED 11 / MISMATCH 1 / SURVIVED 0 / TIMEOUT 0**。

唯一の MISMATCH (M01) は**実体ではなく node ID の表記差**である。
harness が報告する失敗 node のうち real-repo serial 2 件は xdist の実行グループ名
`@real-repo` を伴うが、harness の collection 実在検査は素の nodeid しか受理しない。
**どちらの形で登録しても一致しない** — 報告空間と collection 空間が harness 内部で不一致である。
失敗 node 数は期待どおり 19 件で、うち 17 件は完全一致した。変異は生存していない。

前回レビューが「手前の層に mask される」と指摘した M02 / M03 / M04 / M09 は
**2 層同時変異**へ組み替えて登録し、いずれも KILLED を得た。
とくに M03 (可変 field を 3 件化) は module 定数の件数 assert だけでなく、
公開 index を通る `test_public_index_rejects_validator_admitted_anchor_field_mutations` でも赤になる。
過剰拒否を検出する正例は M04p (contract 拒否を常時発火) と M07 (chain pattern 削除) の 2 本。

## 残る限界 (land しても閉じていないもの)

1. **pin を進めれば新しい組を作れる。** 案 3 が消したのは「同じ組で 2 本目」であって
   「pin を進めて新しい組で測り直す」ではない。閉じるには不採用の案 2 (事前登録) が要る。
2. **案 3 は protocol 単位であって run 単位ではない。** 同一 protocol の複数回実走は
   現在許されている ([T-1140] 問 1 が係属中)。
3. **削除すれば同じ組を再発行できる。** 履歴不変条件の検査は凍結チェーン保留 (M-7) の対象である。
4. **ratified pointer は sanctioned namespace 外を指せる。**
5. **共有 helper `source_digest._sanitized_git_env` には同型の注入面が残る。**
   独立 2 例が揃うまで族一般化しない (DW-G03) ため、本 wave では floor campaign 側の
   ローカル衛生化に留めた。
6. **失敗した発行は artifact を残す。** 自動削除しない方針は既存 `freeze_protocol` と同じで維持し、
   例外 message に exact path と「取り除くまで発行できない」旨を必ず載せる形にした。
