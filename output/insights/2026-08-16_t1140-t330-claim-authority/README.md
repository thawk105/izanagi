# [T-1140](a) / [T-330](a) — 変異台帳と逐語

2026-08-16 / wave `dev-wave-t1140-t330-claim-authority`

## 収録物

| ファイル | 内容 |
|---|---|
| `spec-round2.json` | 変異 spec (11 変異、期待 node は probe 走から再導出した完全集合) |
| `result-round2.json` | 本走の結果 (HEAD `6eb77ef9`) |
| `spec-round3-m10.json` | M10 のみの再走 spec (フレーク由来の node を期待から除いた形) |
| `result-round4-m10.json` | POS-8 訂正後の M10 確認走 (HEAD `30def5d5`) |

`spec-round1-probe.json` / `result-round1-probe.json` は probe 走であり、期待 node の
完全集合を導出するためだけに使った。結論には使わないため収録しない
(job dir `/work/1/SFC/tanab/dev-wave-jobs/2026-08-16-t1140-t330-claim-authority/mutation/` に残す)。

## 結論

**11 変異すべて KILLED。SURVIVED 0 / TIMEOUT 0 / PARSE_ERROR 0。** baseline は
`395 passed, 2 skipped` (rc=0、失敗 node なし)。

| ID | 変異位置 | 壊した逐語 | 赤くなった node 数 |
|---|---|---|---|
| M01 | `campaign_claim._scan_protocol_conflicts` | protocol digest 比較の反転 | 8 |
| M02 | 同 `_owner_state` | zombie (`state == "Z"`) 判定の削除 | 1 |
| M03 | 同 `_owner_state` | starttime 一致検査の恒真化 | 1 |
| M04 | 同 `_owner_state` | boot_id 不一致を LIVE 扱い | 1 |
| M05 | `campaign_claim.acquire_claim` | post-scan の削除 | 3 |
| M06 | `campaign_claim._claim_entries` | `os.scandir` を `Path.glob` へ戻す | 2 |
| M07 | `campaign_claim.acquire_claim` | record と self 実測値の照合削除 | 3 |
| M08 | `floor_submit_receipt._require_job_binding` | nonce 比較の恒偽化 | 2 |
| M09 | `floor_submit_receipt._require_script_binding` | script SHA 比較の恒偽化 | 2 |
| M10 | `s8b_floor_campaign` | receipt gate 配線の削除 | 2 |
| M11 | `s8b_floor_campaign` | protocol digest を run 依存値へ置換 | 3 |

## 3 層の分割 (裁定材料の設計制約 1)

- **leaf 単体**: M01〜M09。`acquire_claim` / receipt leaf を直接呼ぶため、wrapper も
  reservation 検査も前段に無い。
- **wrapper を通らない呼び手**: M10 / M11。shell wrapper (`tools/pegasus/floor_campaign.sh`) を
  起動せず、Python の production entry から入る。M10 が赤くする 2 node は
  `pin/env/hash の検査より前で measure_fn が呼ばれてはいけない` で落ちており、
  **新 gate が副作用の前に止めていること**が実測できている。
- **実運用 end-to-end**: M01 / M05 / M11 が赤くする
  `test_two_floor_subprocesses_same_protocol_different_runs_never_both_succeed` が、
  異なる run identity・同一 protocol digest の 2 実 subprocess を同一ノード・共有 claim root で
  同時起動する。

wrapper が先に落とす入力は Python 側 gate の kill に数えていない。

## 数えなかったもの

- **schema 検査順序の変異**: 旧 schema の receipt は exact key set 検査でも落ちるため、
  順序を壊しても拒否理由が変わるだけで受理集合は動かない。
  `test_schema_is_checked_before_nonce_field` は診断契約の pin として残し、kill には数えない。
- **oracle 経路**: `campaign_id` が manifest 従属であるため claim identity と protocol digest が
  1 対 1 であり、新 gate は追加拒否を 1 件も生まない。schema 追随のみで、検出力に計上しない。

## 過剰拒否 (承認外の拒否) を検出する正例

受理集合を縮小する wave のため、次を事前登録して固定した。いずれも本走で緑である。

| ID | 正例 | 守るもの |
|---|---|---|
| POS-1 | 同一 protocol・owner が消滅 → 取得成功 | 床値の繰り返し pilot 投入 |
| POS-2 | 同一 protocol・pid 再利用 → 取得成功 | crash 後の再投入 |
| POS-3 | 同一 protocol・owner が zombie → 取得成功 | reaping されない crash からの復帰 |
| POS-4 | 別 boot_id の同一 protocol → 取得成功 | 裁定どおりの明示的 fail-open |
| POS-5 | 異なる protocol の live owner → 取得成功 | 無関係 campaign の巻き添え防止 |
| POS-6 | 有効 receipt + hostname 不一致 → 通過 | hostname を authority にする変異を殺す |
| POS-7 | `single_process=False` の契約で receipt 不要 | exploratory / test の巻き添え防止 |
| POS-8 | 全 owner 死亡後に次の投入が成功 | 永久停止しないこと |

POS-8 は当初 `[False, False]` (双方が必ず拒否) を要求していたが、これは production が
保証しない性質だった。判定を「成功数は高々 1」+「全 owner 死亡後に次が通る」へ訂正している。
