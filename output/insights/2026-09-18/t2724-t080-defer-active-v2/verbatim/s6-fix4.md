## 所見ごとの対応表 (closed / partial / regressed、所見 ID → 変更箇所)

| 所見 | 状態 | 対応 |
|---|---|---|
| I1 / RR-1 | closed（実装・静的確認） | receipt 接続分岐の親 calibration 読取りと selector 材料補完を除去。role file は shared base 構築時に取得 |
| I1：残存 caller | closed（静的確認） | 非層2負例の output snapshot が親 Git ignore 情報を読む経路も、copy 自身へ変更 |
| I2 | closed | production、S、登録簿、走査除外、hold、allowlist、既存 landed test の期待値、sink pin は不変 |
| 接続正例・反実仮想の実証 | partial | 直接呼出しを試行したが、下記の実行制約で未達 |
| I3 / RR-4 | 親担当 | 編集していない |

## 実装した変更 (file ごと)

変更は2ファイル、29行追加・7行削除です。

- [test_s8b_ratified_freeze.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2724-t080-fix4/orchestrator/tests/test_s8b_ratified_freeze.py:1030)
  - receipt 接続時に calibration・selector source・parser の計7入力を copy 内で必須化。不足時は path を示す assert。
  - calibration bytes は `root / calibration_path` から取得。
  - selector 材料の親 root fallback を削除。
  - 不足入力7ケースの負例を既存 module に追加。

- [test_s8b_oracle_driver.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2724-t080-fix4/orchestrator/tests/test_s8b_oracle_driver.py:1439)
  - `.claude/agents/selector-8b.md` は既存 base の複製対象外だったため、active-v2 base の basis commit 前に複製。
  - `test_t080_active_v2_preserves_nonlayer2_receipt_refusal` の snapshot を copy 自身の Git 情報に束縛。拒否集合と副作用不変の assertion は維持。

## 接続正例 fixture の結果

**本巡での接続正例の成立は未確認です。**

`test_t080_active_v2_delegation_accepts_full_receipt` の直接呼出しを試みましたが、module import が `GrowthTestHoldBypassRefused` で拒否されました。guard は解除していません。

各段の静的検算結果は次のとおりです。

| 段 | 確認内容 |
|---|---|
| basis | orchestrator・tracked output・source closure・ccbench に加え、role を初期材料として複製。既存 freeze namespace の除去は basis 前 |
| R | 既存の実 draft→validate→finalize→receipt commit 経路を維持。追加 role の実 conjunction hit はゼロ |
| selector seed / protocol | copy 内7入力を確認後、fixture protocol と seed を生成。selector helper の fallback は存在確認により到達しない |
| C | copy の `repo_root` と ccbench を campaign に渡し、certificate callback で commit |
| G | 通常接続経路は `frozen_at_head=C`、その後 G を commit。順序変更なし |
| A / X | fixture 内の approval・pointer を各 commit。変更なし |
| load / launch / receipt | copy の root を明示して実機構へ接続。変更なし |

指定ログの2672 passed／1097 passed は **fix-3 の結果**であり、本変更後の成功証拠には数えていません。

## 自己検証の結果

| 検証 | 結果 |
|---|---|
| 新規不足入力 test の直接呼出し | **7/7成功**。`tmp_path` は `tempfile.mkdtemp()` |
| selector helper の直接検算 | **成功**。材料を複製後、fixture の親取得先を利用不能にして実 helper を実行 |
| 追加 role の実 conjunction 検査 | rr80／rr20 とも hit ゼロ |
| calibration の供給元 | tracked output に存在することを確認 |
| 通常 emitter の immutable token test | 呼出し不能：`FloorCampaignError: machine-pin: 未対応 site 'PEGASUS_LOGIN'` |
| m6 反実仮想 | process 内で predicate 属性を差し替えて試行。同じ site 拒否で token 生成前に停止。**kill 証拠には数えない**。属性復元済み |
| 全変更ファイルの AST parse | 成功 |
| `git diff --check` | 成功 |
| landed test の保護 | 基点に存在する driver 129関数・ratified 61関数について、本巡による test 本体変更なし |
| production 3ファイル | HEAD と bytes 一致 |
| driver sink pin | 最終行番号 **1781：`pipeline.evaluate`、1794：`evaluate_fn`**。両 pin と一致 |

pytest／`tools/run_tests.py` は実行していません。

## 所有外への波及

`grep -rn` と caller の現物で確認しました。

| 経路・箇所 | 親 root／共有 ccbench の読取り |
|---|---|
| shared base builder：driver 1434、1438、1442、1463、1486、1522行付近 | source・output・role・履歴・ccbench を取得。**key ごとの base 構築時のみ** |
| `_t080_stub_free_e2e_repo` | base の copy と document の deepcopy。親材料の再取得なし |
| receipt emitter：ratified 1030行付近 | copy の calibration・selector 材料・ccbench のみ |
| `_install_emitter_selector_prediction:728` | 通常 fixture 用の親 fallback は残るが、接続経路では全入力確認後なので到達しない。直接検算でも確認 |
| 非層2負例の snapshot：driver 1790行付近 | copy 自身の Git 情報へ変更 |
| 接続8 node の実検査・draft1 node | fixture root を渡す。draft は emitter を経由しない |
| root 境界・cache identity | 親 path の比較／識別に使用。受入材料の bytes 取得とは別 |

通常の `_prepare_emitter_base` と g2 emitter の親材料取得は維持しました。`load_emitter_g1` の署名は不変です。

所有外 consumer は migration、oracle report、verdict、ratified verify、oracle manifest。通常 fixture 経路は変更していません。selector helper を差し替える既存 ratified-verify test の署名契約も不変です。

登録簿・golden・shared-base consumer の14関数／20 node pin は変更していません。

## 変異事前登録への対応 (m0〜m11 の anchor 更新、位置の一意性)

production は不変です。各 anchor が対象関数内で一意であることを検査しました。以下は `orchestrator/campaign/` 配下です。

| ID | 最終 anchor |
|---|---|
| m0 | `t080_freeze_migration.py:2231` predicate の comment |
| m1 | `s8b_ratified_freeze.py:3550` `current != expected` |
| m2a | `s8b_oracle_driver.py:200` `allowed=not merged` |
| m2b | 同219行の raise／220行の invalid 拒否文言 |
| m3 | `t080_freeze_migration.py:2274` 後段の `if not delegated`＋search assertion |
| m4a | 同2215行、expressions 比較 |
| m4b | 同2202行、match convention 比較 |
| m5 | `s8b_oracle_driver.py:1531` campaign-start 再解決＋epoch 比較 |
| m6 | `t080_freeze_migration.py:2236` outer HEAD 比較 |
| m7 | 同2247行、列挙 digest 比較 |
| m8a | `s8b_floor_campaign.py:5534` search assertion |
| m8b | `t080_freeze_migration.py:1728`。F4裁定どおり単独証拠から除外 |
| m9 | 同2234行、root 比較 |
| m10 | 同2241行、世代再解決と比較 |
| m11 | F1裁定どおり除外。`fresh_validated` 不在を確認 |

正式な変異 matrix は未実走です。

## 未完・未実走・懸念

- 修正後の接続正例、両木焦点走、通常受入は未実走です。
- predicate 反実仮想は fixture 構築で停止し、検出力を実証できていません。
- shared base 構築時の親読取りは残ります。key lock が real-repo writer を排除するとの主張はしていません。
- RR-2 の時間評価、RR-3 の正式変異実測、RR-4 の親報告修正は未対応です。
- docs・tracked output・登録簿は未変更。commit と報告ファイルは作成していません。

## 総括

**RR-1 の修正を2つの test file に実装しました。** 不足入力7ケースと selector の copy 内完結は直接確認済みです。接続全体と変異の実証は実行制約で未達のため、修正後の受入完了とは判断していません。