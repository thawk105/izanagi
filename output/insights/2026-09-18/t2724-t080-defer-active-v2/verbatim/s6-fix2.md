## 所見ごとの対応表 (closed / partial / regressed、所見 ID → 変更箇所)

| 所見 | 状態 | 対応 |
|---|---|---|
| G1 | closed | 旧 `floor-protocols` と合成 legacy anchor の継承比較が拒否原因になることを現物で確認 |
| G2 | closed（実装） | 接続 fixture の basis commit 前除外を、freeze namespace の v1 holdout 以外全部＋budget-inputs 全体へ変更 |
| G3 | partial | 各構築段と後段検査を静的確認。接続正例の直接呼出しは import guard により未到達 |
| G4 | closed | production、S、既存期待値、sink pin は変更なし |
| F2／RA-2／RB-1 | partial | build seam 修正を維持し、次の protocol 残存障害を修正。接続8 node の成功は未確認 |

F1・F3〜F9 は本巡で変更・再判定していません。新たな退行を示す実測はありませんが、回帰緑も主張しません。

## 実装した変更 (file ごと)

変更は [test_s8b_oracle_driver.py:1392](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2724-t080-fix2/orchestrator/tests/test_s8b_oracle_driver.py:1392) の1箇所、17行追加・9行削除です。

`active_v2_base=True` の場合だけ、次の宣言集合を basis commit 前に除去します。

- `output/s8b-freeze/`：`holdout_freeze.json` 以外の全 file／directory。
- `output/s8b-freeze-budget-inputs/`：全内容。

除外理由をコメントに記載しました。known-axes、v1 holdout、positive control、`orchestrator/` は保持します。共有の削除集合 S は変更していません。

## 接続正例 fixture の結果

**`active-valid` 到達は未確認です。**

`test_t080_active_v2_delegation_accepts_full_receipt` の直接呼出しを準備しましたが、module import 時に次で停止しました。

```text
GrowthTestHoldBypassRefused:
IZANAGI_GROWTH_HOLD_BYPASS_REFUSED_V1
```

代わりに構築段を静的検算しました。

| 段 | 確認内容 |
|---|---|
| basis | 除外は最初の commit より前。後続の known-axes source 復元に、除去した freeze protocol を戻す参照は見つからない |
| R | 既存の実 draft→validate→finalize→R commit 経路を維持 |
| protocol／selector seed | 合成 protocol を seed commit に収録し、その commit を selector の `pre_oracle_head` に使用 |
| certificate／C | 実 preflight・certificate 発行後、callback が certificate を単独 commit |
| G | `frozen_at_head=C`。通常分岐では途中の追加 commit がなく、`G^=C` |
| A／X | fixture が生成した G hash・approval hash から構築し、それぞれ commit |
| load／launch | namespace clean、C の厳密祖先性、G 導入集合、selector 祖先・bytes 束縛、closure 完全一致の検査を維持 |

`resolve_current_floor_protocol` は「初回封印」専用分岐ではなく、legacy anchor と namespace の索引を作ります。今回の変更後は、emitter が作成・commit した anchor だけが入り、旧 record に対する `validate_ai_reseal_inheritance` を実行する対象がなくなります。

## 自己検証の結果

- `git diff --check`：成功。
- 本巡変更1 file、および基点からの wave 全13 Python file：AST parse 成功。
- 変更 module の import／接続 test 直接呼出し：上記 growth-hold guard により不能。
- m6 相当の predicate 属性差替え：process 内で実施し、終了後に復元。
- m6 の基準・変異とも、実 token 構築中に以下で停止。**kill／SURVIVED の証拠には数えていません。**

```text
FloorCampaignError: machine-pin: 未対応 site 'PEGASUS_LOGIN'
```

driver sink の最終行番号は、production 呼出しと test pin が一致しています。

| sink | production 行 | test pin |
|---|---:|---:|
| `pipeline.evaluate` | 1781 | 1781 |
| `evaluate_fn` | 1794 | 1794 |

pytest／`tools/run_tests.py` は実行していません。

## 所有外への波及

`grep -rn` で builder、共有 fixture、receipt caller を列挙しました。

- `active_v2_base=True` を渡すのは `_build_t080_active_v2_repo` の1箇所。影響は接続7関数／8 node。
- 共有 T-080 fixture と draft 負例は既定の `False` を使い、本巡の除外変更を通りません。
- emitter の固定 fixture 分岐、signature、resource 登録簿、memo consumer は変更なし。
- `verify_receipt` 等の caller は driver、holdout verifier、migration CLI、driftguards、serialization 生成 script に残り、本巡の signature 差分はありません。

残存 output の authority 経路は次のように確認しました。

| 材料 | 読取り・干渉の確認 |
|---|---|
| Linux calibration ref | emitter が契約指定 path に同じ実 bytes を配置。campaign loader は既存の合成 verified-calibration seam |
| Pegasus registered calibration | 複製は残るが、合成 protocol は `linux-baremetal`。旧 floor protocol authority として選択する経路は見つからない |
| env contract | module 側の登録 catalog／activation authority を使用。複製した任意 output から protocol を探索しない |
| campaign claims | `single_process` 条件付き。Linux fixture は当該条件が false |
| holdout admission claims | 新規 fixture repo の Git common directory 配下。実 root の `.git` は複製しない |
| active-chain／selector 証拠 | 今回空にする namespace に fixture 自身が再生成。旧証拠の祖先・hash を引き継がない |

追加の除外が必要な残存 authority 経路は見つかりませんでした。ただし、残存 output を含む最終 full scan の成功は未実証です。

## 変異事前登録への対応 (m0〜m11 の anchor 更新、位置の一意性)

production は本巡で変更していないため、anchor の移動はありません。以下で `C/` は `orchestrator/campaign/` です。

| ID | 最終 anchor |
|---|---|
| m0 | `C/t080_freeze_migration.py:2231`、`Historical verification…` comment |
| m1 | `C/s8b_ratified_freeze.py:3550`、`if current != expected:` |
| m2a | `C/s8b_oracle_driver.py:200`、`allowed=not merged,` |
| m2b | 同 `_campaign_t080_value:219–220` の invalid 拒否 |
| m3 | `C/t080_freeze_migration.py:2274–2275`、後ろ側の `if not delegated:`＋`_assert_search_pass` |
| m4a | 同`:2215`、expressions 比較 |
| m4b | 同`:2202`、match convention 比較 |
| m5 | `C/s8b_oracle_driver.py:1531` から campaign-start 再解決・epoch 比較 |
| m6 | `C/t080_freeze_migration.py:2236`、outer activation HEAD 比較 |
| m7 | 同`:2247`、enumeration digest 比較 |
| m8a | `C/s8b_floor_campaign.py:5534`、`_holdout_freeze._assert_search_pass(report)` |
| m8b | 同 migration`:1728`。fix-1 裁定に従い単独変異証拠から除外 |
| m9 | 同 migration`:2234`、root 比較 |
| m10 | 同 migration`:2241` から active generation 再照合 |
| m11 | fix-1 裁定に従い登録対象外 |

m3 の `if not delegated:` は2箇所あるため、**後続の `_assert_search_pass(report)` と組にして特定**する必要があります。他は指定関数・上記逐語 anchor で位置を特定できます。正式な変異 matrix は未実走です。

## 未完・未実走・懸念

- 接続8 node、修正後の両木焦点走、通常受入は未実走。
- protocol 残存原因への修正は完了しましたが、その先の別拒否がないとは保証できません。
- predicate 反実仮想は環境拒否より先へ進まず、検出力は未確認。
- docs・tracked output・production の変更、作業 worktree の commit はありません。

## 総括

**fix-2 の test 側修正を1 file に実装し、差分・構文・後段構造を確認しました。接続正例は環境制約で未達のため、着地可能とは判定しません。**