指定先が workspace の書込許可範囲外だったため、書込みは拒否されました。`mutation-spec.json` は存在せず、repo 内ファイル、job dir、git、pytest には一切変更・操作していません。

## 登録予定として確定した変異

| id | 位置 | 変異内容 | 期待 node 数 |
|---|---|---|---:|
| `swo.identity-external-binding-drop` | `s8b_sort_swo_receipt.py:231` | `cell_id`、`entry_sha256`、`binary_sha256` の外部期待値束縛を自己申告へ戻す | 5 |
| `binary.sort-receipt-optional` | `s8b_binary_admission.py:264,348` | exact-key gate と参照を同時に緩め、sort receipt 欠落を optional 化 | 1 |
| `stats.empty-binaries-fallback` | `s8b_floor_stats.py:976,988` | 空 binaries の直接拒否と完全一致検査を同時に迂回 | 1 |
| `admission.campaign-filter-drop` | `s8b_holdout_admission.py:1709,1938` | main/attempt ledger の `campaign_run_id` filter を除去 | 2 |
| `admission.claim-content-skip` | `s8b_holdout_admission.py:1796` | claim の exact key・内容照合を省略 | 5 |
| `admission.completed-only-fallback` | `s8b_holdout_admission.py:1841,1909` | start 不在時の coverage と marker authorization を迂回 | 1 |
| `contract.canonical-attempt-id-drop` | `s8b_floor_contract.py:167,178` | planned/retry attempt ID の正準再導出照合を除去 | 4 |
| `holdout.binary-external-binding-drop` | `s8b_holdout_freeze.py:1437,1490` | result/manifest equality と journal-derived `expected_binaries` を同時に除去 | 1 |
| `ratified.inspector-unavailable-skip` | `s8b_ratified_freeze.py:3099` | inspector の mismatch/unavailable を空問題として skip | 3 |

全件 `expected_status: KILLED`、`hang_risk: false`、時間設定は 120/600/900 秒として構成済みです。

## 単一理由性の確認結果

- identity 束縛は形状検査を残し、外部値との対応だけを落とす設計です。対象3 fieldを同じ入力で拒否する前段はありません。
- sort receipt は `.get()` 化だけでは exact-key gate に遮られるため、両方を一変異へまとめました。
- 空 binaries は直接拒否後にも集合完全一致があるため、両 gate を同時変異しました。
- campaign filter より前には対象 campaign を選別する層がなく、他 campaign 行の共存を守る正例が実効検出点です。
- claim 改竄は ledger 再構築を通過した後、claim 内容比較だけが実効 gate です。
- completed-only は marker 側にも start coverage があるため、2箇所を同時変異しました。
- canonical attempt ID は inspector 前段の frozen attempt 集合だけでは同一 cell 内 transplant を拒否できず、共通 validator が実効 gate です。
- binary 外部束縛は result/manifest gate が先行するため、`expected_binaries` 不渡しと一体化しました。
- ratified inspector 以後には live filesystem を再検査する層がなく、skip 後は artifact 内部整合だけが残ります。

## 除外した候補

- built record の SWO key 脱落: 正常 campaign の広範な node が影響し、完全集合を静的に確定できませんでした。
- raw compiler/path の portable 混入: exact-key と SHA 形状検査に遮られ、producer/validator の多重変異が必要です。
- central key 集合の common 固定化: 全 sort consumer を過剰拒否し、期待 node 完全集合を確定できませんでした。
- pair set 比較への後退: canonical cell identity と central external tuple が同じ入力を後段で拒否します。
- missing/zero-byte main ledger の空列受理: nonempty campaign gate と cell coverage gateがさらに拒否します。
- caller supplied expected の復活: signature だけの変更は診断感度に留まり、実効自己投入まで変えると影響集合が確定できません。
- journal/result session の片方向化: throughput 改竄は後段の統計再計算でも拒否され、単独では診断文字列だけが変わります。

## 再照準

`.get()` optional、空 binaries、completed-only、`expected_binaries` 不渡しの4件は、単独候補が別 gate に mask されるため実効 gate と組み合わせた `both-layers` へ再照準しました。

## anchor の一意化

`if configuration_id == "sort_best":` は同一ファイル内に2箇所あるため、`try` と validator 呼出しまで広げました。campaign の2つの filter は代入を含む comprehension 全体、ratified の例外処理は `except` 本体全体へ広げています。

## positive 変異の設計

`admission.campaign-filter-drop` を positive としました。正直な対象 campaign 証拠が揃った共有台帳へ、別 campaign の正当な行が追記されても対象 receipt と受理結果が変わらないことを守ります。

## 総括

登録件数: **0件**。書込権限拒否によりファイルは未作成です。書込可能なら上記9件を登録できます。

除外件数と理由: **7件**。主因は別層による mask、または期待 node 完全集合を静的に確定できないことです。

最も自信のない変異: `admission.claim-content-skip`。対象5 nodeは特定済みですが、複数の高位 consumer が同じ inspector を共有するため、完全集合の静的判断では最も波及範囲が広いものです。