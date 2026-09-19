## 所見ごとの対応表 (closed / partial / regressed、所見 ID → 変更箇所)

8 ファイルを修正しました。接続正例と受入は未達です。以下、`C/` は `orchestrator/campaign/`、`T/` は `orchestrator/tests/`。

| 所見 ID | 状態 | 対応箇所・結果 |
|---|---|---|
| F1・RA-1・RB-2 | partial | `C/s8b_oracle_driver.py:run_block`：再 launch を削除し gate 時 token で再解決。実装済み・回帰未実走 |
| F2・RA-2・RB-1 | partial | `T/test_s8b_ratified_freeze.py:_make_emitter_build`、driver 接続 fixture：実 pin の compiler input を指定。接続未実走 |
| F3・RA-3 | partial | F1 の変更で再解決と epoch 比較を維持。`[missing]` の動的確認は未達 |
| F4・RA-4 | partial | `T/test_s8b_oracle_driver.py:test_run_block_refuses_invalid_receipt_after_gate_seam` を追加。kill 未実証 |
| F5・RA-5・RB-3 | partial | floor E2E の期待 digest に残存 chain record を独立列挙して追加。E2E は toolchain 不在で停止 |
| F6・RA-6・RB-4 | closed | driver sink の最終行番号へ追随。両テストの直接呼出し成功 |
| F7・RB-5 | partial | trailer 不正を公開 gate とも同じ単一の完全拒否集合に固定。failed-launch は拒否数も固定。v1 の完全拒否集合化は未実施 |
| F8・RB-6 | partial | conftest と独立 golden に接続系・draft・新 seam test を登録。静的一致確認済み、collection 未実走 |
| F9・RB-7 | partial | 合成負例の件数を修正。元 consumer 単独選択の lazy 対照を追加。直接実行は import guard で停止 |
| F10 | closed（静的） | caller を再列挙。keyword 省略経路と既存 double の利用経路を確認 |

新たな退行は確認していませんが、未実走部分の無退行は保証できません。

## 実装した変更 (file ごと)

| file | 変更 |
|---|---|
| `C/s8b_oracle_driver.py` | campaign-start 前の再 launch・新 token 比較を削除。既存 token による再解決と4要素 epoch 比較を保持 |
| `C/t080_freeze_migration.py` | predicate の説明を親の鮮度裁定に追随 |
| `T/test_s8b_ratified_freeze.py` | compiler input を引数化。既定は `fixture.txt`。接続側は実 pin の tracked regular file を検査し、渡された source root の bytes を hash 化 |
| `T/test_s8b_oracle_driver.py` | `CMakeLists.txt` の配線、新規 late-hit file、trailer の完全拒否集合、invalid epoch seam 負例を追加 |
| `T/test_s8b_floor_campaign.py` | digest 用期待集合へ、独立した正規表現と tracked path 列挙で chain record を追加。preflight allowlist は維持 |
| `T/test_ccbench_spawn_sites.py` | `pipeline.evaluate` を1781行、`evaluate_fn` を1794行に追随 |
| `T/conftest.py` | 実 root reader の登録を追加 |
| `T/test_real_repo_serialization.py` | 独立 golden、合成負例の件数、元 consumer の lazy 対照を更新 |

docs・tracked output は未編集、commit は作成していません。

## 接続正例 fixture の結果

**active-valid 到達は未確認です。**

接続8 node は driver module の import が `GrowthTestHoldBypassRefused` で拒否されるため、直接呼出し不能でした。guard は解除していません。

構築段階を静的検算しました。

| 段階 | 確認内容 |
|---|---|
| basis | 初期 commit 前に接続用の G・budget input・selector 材料を除去。既知の ccbench pin を checkout |
| R | 実 draft／finalize／receipt 検証を利用 |
| selector seed・protocol | fixture 自身の seed commit と既存 ccbench pin に束縛 |
| C | certificate callback による commit |
| G | 通常経路の `frozen_at_head` は C。G の直前 commit も C |
| A | generation SHA に束縛した approval |
| X | approval SHA に束縛した active pointer |

fixture が指定する pin `d706650c…` に `CMakeLists.txt` が mode `100644` の blob として存在することは、`git ls-tree` で確認しました。

## 自己検証の結果

**成功**

- 両 sink pin テストの直接呼出し。
- 最終変更8ファイルの AST parse。
- `git diff --check`。
- refusal return は15箇所。
- 登録簿と独立 golden の静的一致。
- memo consumer は8関数、opt-out は従来の2関数。

**呼出し不能・停止**

- driver／serialization：既存 growth-hold guard による import 拒否。
- emitter の token test：`machine-pin: 未対応 site 'PEGASUS_LOGIN'`。
- floor E2E：`floor toolchain cc が PATH に存在しない: 'gcc-13'`。
- predicate 負例：同じ site 拒否で token 構築前に停止。

m6 はプロセス内で predicate の outer activation HEAD 比較だけを除去して呼出しましたが、baseline と同じ構築障害で停止しました。**kill 証拠には数えません。**

pytest／`tools/run_tests.py` は実行していません。

## 所有外への波及

`grep -rn` で指定 caller を再列挙しました。

- `s8b_holdout_freeze.py` の receipt／adapter 呼出し、migration CLI は token 省略の従来経路。
- driver の token なし経路と adapter 転送は維持。
- memo、driftguards、serialization の生成 script は root-only 呼出しを確認。
- `_make_emitter_build` の既定値と g2 emitter の呼出しを維持。
- 新 seam test は既存 helper を利用し、memo opt-out 集合を増やしていません。

`[missing]` は、tracked path 列挙が worktree の存在確認を使わないため digest が維持される構造を確認しました。ただし、接続 fixture 上で predicate が report を返す動的確認は未達です。

## 変異事前登録への対応 (m0〜m11 の anchor 更新、位置の一意性)

| ID | 最終 anchor |
|---|---|
| m0 | `C/t080_freeze_migration.py:2231`：helper comment |
| m1 | `C/s8b_ratified_freeze.py:3550`：`if current != expected:` |
| m2a | `C/s8b_oracle_driver.py:200`：`allowed=not merged` |
| m2b | 同`:219–220`：invalid epoch の raise。新 seam test を追加 |
| m3 | `C/t080_freeze_migration.py:2274–2275`：`_verify_holdout_live_scan` の後段 `if not delegated`／assert |
| m4a | 同`:2215`：expressions 比較 |
| m4b | 同`:2202`：match convention 比較 |
| m5 | `C/s8b_oracle_driver.py:1531`：campaign-start 再解決と epoch 比較 |
| m6 | `C/t080_freeze_migration.py:2236`：outer activation HEAD 比較 |
| m7 | 同`:2247`：列挙 digest 比較 |
| m8a | `C/s8b_floor_campaign.py:5534`：search assert |
| m8b | 単独変異の証拠から除外。draft 負例は維持 |
| m9 | `C/t080_freeze_migration.py:2234`：root 比較 |
| m10 | 同`:2241`：active generation 再解決と続く比較 |
| m11 | 親裁定により登録から除外 |

m3 の assert 文は file 内に複数存在するため、**関数名と後段分岐を含めて照準**してください。他の現役 anchor は検索結果上1箇所です。m5 の単独証拠候補は `[changed]` と既存 g4、`[missing]` は除外します。

## 未完・未実走・懸念

- 接続8 node、`[missing]`、disk-swap 回帰、新 invalid epoch 負例は未実走。
- floor の chain 有り／無し digest 一致、serialization の動的検証は未達。
- 正式な変異 matrix、両木焦点走、通常受入、RB-8 の時間評価は未実施。
- 同名 file の内容交換は親裁定どおり predicate の検出対象外。残余の docs 記録は親担当です。

## 総括

**修正は未 commit で残しています。sink の2件は直接確認できましたが、主要な接続検証が未達のため、着地可能とは判断しません。**