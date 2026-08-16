# [T-1184] 8c 事前登録 証拠契約の第 3 世代改訂 — dev-wave insights

2026-08-16 / branch `worktree-dev-wave-t1184-prereg-contract-revision` / 実装 commit `00e1ebdf`

前 wave (worklog 580) が D438 として実装形を land し、D439 が分割規律を定めた改訂の実施 wave。
D439 形 1 (裁定を記録した決定が既に main に着地) に該当するため、第 3 世代の凍結記録は
`ruling_reference = D438` を引けた。

## ファイル

| path | 内容 |
|---|---|
| `brief.md` | 段 1 brief + 段 4 裁定 (scope・不変条件 I1〜I8・変異事前登録・親の実測 M1〜M8) |
| `s6-adjudication.md` | 段 6 レビュー裁定 (採用 5 件 / scope 外 4 件、real/refuted の根拠) |
| `verbatim/s5-author.md` | 段 5 実装子の逐語報告 |
| `verbatim/s6-lensA.md` | 段 6 敵対レビュー レンズ A (規律 2/3) の逐語報告 |
| `verbatim/s6-lensB.md` | 段 6 敵対レビュー レンズ B (凍結手続・consumer) の逐語報告 |
| `verbatim/s6-fix.md` | 段 6 fix 子の逐語報告 (契約全条件の識別子実在走査を含む) |
| `mutation-spec.json` | 変異事前登録 (6 件、runner 範囲と対の期待 node) |
| `mutation-ledger.json` | 変異 matrix の結果台帳 (6/6 一致) |

## 変異 matrix

`repo_head = 00e1ebdff16ba11aeaf511465ceaf06842bb84d2`、runner は計算ノード dispatch。

| id | 期待 | 結果 | 固有の検出力 (冗長ゲートを除く) |
|---|---|---|---|
| m1 C01 を wave 前の `machine_checkable: false` へ戻す | KILLED 8 node | KILLED 一致 | 負の対照 `[nc_c01…-C01]` / 双方向整合 / gap snapshot / 充足可能集合 の 4 件 |
| m2 評価器を持たない C02 を `true` にする | KILLED 7 node | KILLED 一致 | 双方向整合 / gap snapshot / 充足可能集合 の 3 件 |
| m3 `SATISFIABLE_CONDITION_IDS` を `{"C11"}` へ拡大 | KILLED 1 node | KILLED 一致 | 単一理由 |
| m4 C11 の射影識別子要求から 1 件削除 | KILLED 1 node | KILLED 一致 | 単一理由 |
| m5 条件 8 の親集合完全一致を祖先関係へ弱める | KILLED 5 node | KILLED 一致 | 二段束縛 assert の 1 件 |
| m6 **正例** 機械検査可能集合の等価 refactor | SURVIVED | SURVIVED 一致 | 過剰拒否なし |

### 冗長ゲートの明記 (DW-M03)

契約 JSON を触る変異 (m1・m2・m5) はいずれも、生きた契約 hash の pin 4 件を同時に落とす。
これは「凍結成果物の意味を変えたら世代を上げよ」という正しい冗長ゲートであり、
各変異固有の検出力は上表の右列で数える。

### 凍結チェーンのゲートは変異では測っていない

`test_candidate_freeze_matches_contract_and_generation_chain` は
`pytest.mark.xdist_group` を持ち、loadgroup 実行では FAILED 行の node ID に `@<group>` が付く一方、
`--collect-only` の node ID には付かない。変異 harness の `_normalize_node` は `@<group>` を
落とさないため、期待 node をどちらの空間で書いても片側で必ず外れる。
したがって runner 範囲から当該ファイルを外し、期待 node を範囲と対にした。

**代わりに直接の前後証拠を使う** — 第 3 世代の凍結記録を作る前の走行 (14:13) では当該テストが赤、
作った後の走行 (14:44) では緑だった。改訂と世代記録を別 commit に分けられないことは、
この 2 点で実証されている。

## 実走

| 走行 | 範囲 | 結果 |
|---|---|---|
| 焦点走 1 (14:06) | 3 ファイル、bounded local | `rc=16` — cgroup を attest できず基盤失敗 (F155 の既知事象) |
| 焦点走 2 (14:13) | 3 ファイル、計算ノード | 4 件赤 — 契約 hash pin 3 件 + 凍結チェーン 1 件 (世代記録 未生成) |
| 焦点走 3 (14:44) | 3 ファイル、計算ノード、g3 込み | **386 passed / rc=0** |
| 変異 probe (14:47) | 6 変異 | 期待 node の完全集合を実測で確定 |
| 変異本走 (14:57) | 6 変異 | **6/6 一致 (5 KILLED + 正例 1 SURVIVED)** |

段 5 実装子と段 6 fix 子はいずれも bounded local が `rc=16` になり pytest を 1 件も実走できていない。
テスト実走はすべて親が `--force-dispatch` で計算ノードへ回した。

## 工数

Codex 子 4 本、いずれも `gpt-5.6-sol` reasoning=high、受理検査 rc=0。

| 段 | wall | model call | output token |
|---|---|---|---|
| 段 5 実装 | 467 秒 | 36 | 20,009 |
| 段 6 レビュー レンズ A | 452 秒 | 28 | 19,420 |
| 段 6 レビュー レンズ B | 399 秒 | 36 | 16,943 |
| 段 6 fix | 445 秒 | 32 | 19,622 |
