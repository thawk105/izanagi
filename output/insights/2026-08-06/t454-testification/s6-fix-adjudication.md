# 段 6 fix 裁定 — 段 4 裁定の訂正と must-fix の処理

段 6 のレンズ C / D は**いずれも NO-GO**。所見 C-01〜C-06、D-01〜D-09 の 15 件を
すべて real と裁定した (refuted 0)。うち must-fix は C-02 / C-03 / C-04 / D-01 / D-02 /
D-03 / D-04 / D-06 / D-08 / D-09 の 10 件。

## 1. 段 4 裁定の訂正 (erratum)

段 4 裁定は次の 3 点が誤っていた。**本節が優先し、段 4 裁定の当該記述は破棄する。**

### E-1 (D-06) — P1 / N1 の命題が二軸を潰していた

段 4 は P1 を「refuted (ただし採用)」、N1 を「real (一般化は refuted)」と書いた。
これは**別命題を 1 セルへ潰した表記の誤り**である。分解して確定する。

| 命題 | 判定 |
|---|---|
| P1a: ユーザー発話が「全 Markdown 凍結」を含意する | **refuted** |
| P1b: 本 wave は `docs/dev-wave/**` を変更しない | **adopted** (親の wave-local 選択。ユーザー命令ではない) |
| N1a: 変更のない同一 L2 外延を全件再棚卸しする | **redundant** (3 度目は不要) |
| N1b: 前回 anchor 以後の delta 監査も不要 | **refuted** (O10 は前回監査後に実発火した) |
| R7 (delta 監査への手順変更) | **未発効・ユーザー裁定待ち** |

worklog では「docs 凍結はユーザー命令」と書いてはならない (P1a が refuted のため)。

### E-2 (D-04) — R6 の scope 復旧が不完全で、142 bytes の符号も誤っていた

- 142 bytes は**削減候補ではなく `DW-S01` / `DW-S02` への +142 bytes の追記**である
  (`output/insights/2026-08-05_t244-p2-noninterference/s4-adjudication.md` 段 8 節)。
  段 4 は「撤回 142 bytes」と書いており符号が逆だった。
- `DW-G05` への **+274 bytes の追記** ([T-287] §5 で文面確定済み) が R6 から脱落していた。
  archive (244) が持ち越した「必要枠 270 bytes」は「追記 274 − 当時の残り 4」である。
  原文 274 / 歴史不足 270 / 現行需要 274 を混同しない。

### E-3 (D-03) — 「20 件すべて real」は `DW-S04` の三軸要求を満たしていない

`DW-S04` は real/refuted に加え**採否と scope 内/外**を要求する。段 4 は real 判定だけで
採否・scope を書いていなかった。§3 で全所見を三軸へ確定する。

## 2. must-fix の処理

| 所見 | 処理 |
|---|---|
| C-03 (`failed ⊂ expected` 未固定) | **段 6 fix で実装**。`failed_keys <= expected_keys` 変異を殺す node を追加 |
| C-04 (`_match_key` の path 成分落とし) | **段 6 fix で実装**。異なる path・同 test part の node を追加 |
| C-02 (MU-3 の期待 node が未確定) | **変異事前登録を訂正**。§4 参照 |
| D-01 (wave 全体が過小実行) | **採用**。T-454 は完了扱いにせず active のまま残す。既割当の起草物を裁定パッケージで実体化する |
| D-02 (exact set の片側だけ) | C-03 と同一。fix で閉じる |
| D-03 / D-04 / D-06 | §1 の E-1〜E-3 と §3 で訂正 |
| D-08 (worklog 必須文言) | **採用**。段 7 で逐語を入れる |
| D-09 (見送り一覧) | **採用**。段 7 で 12 項を明示 |

C-01 / C-05 / C-06 / D-05 / D-07 は nit (攻撃不成立・親方針は正しい) として記録のみ。

## 3. 段 3 全所見の三軸裁定 (`DW-S04`)

| 所見 | real/refuted | 採否 | scope |
|---|---|---|---|
| A-01 / B-02 / B-04 (二経路併存・二重投資) | real | 不採用 (実装しない) | scope 外 → R1 |
| A-02 (startup 前死亡が終端化できない) | real | 不採用 | scope 外 → **R8** |
| A-03 (flock の権威性・job-dir 所有条件) | real | 不採用 | scope 外 → **R8** |
| A-04 / B-09 (checker 採用の E2E 未結線) | real | 不採用 | scope 外 → **R8** |
| A-05 / A-06 (probe の ABA・starvation) | real | 不採用 | scope 外 → R3 |
| A-07 / B-06 (condition identity と schema 衝突) | real | 不採用 | scope 外 → **R8** |
| A-08a (集合関係の象限 — 等 / 互いに素 / 真上位 / 真部分) | real | **採用** | **scope 内 (段 6 fix 1・2 巡で実装)** |
| A-08b (正規化衝突 vector — basename / 末尾 2 component / case / class namespace) | real | **採用** | **scope 内 (段 6 fix 2 巡目で実装)** |
| A-08c (A-08 が一般化した「既存実装+テスト = 純増ゼロ」の禁止則) | real | 採用 (原則) | scope 外 → **R9** |
| A-09 (delta 監査へ) | real | 不採用 | scope 外 → R7 |
| B-01 (回収 0 bytes / 見込み −207) | real | 採用 (記録) | scope 内 → 段 7 |
| B-03 (先行機械化は対象節 +70 bytes) | real | 採用 (原則) | scope 外 → **R9** |
| B-05 (既割当 scope の脱落) | real | 採用 | scope 内 → R6 + 段 7 |
| B-07 (事実記録と D 発効の境界) | real | 採用 | scope 内 → 段 7 |
| B-08 (dogfood と `DW-G01`) | real | 不採用 | scope 外 → **R9** |
| A-10 / B-10 (前提の総括) | real | 採用 | §1 E-1 |

## 4. 変異事前登録の訂正 (`DW-M01` / `DW-M08`)

段 4 の MU-1〜MU-3 を破棄し、次で確定する。**期待 node は段 6 fix 完了後の実 nodeid で
最終確定し、実測が期待の上位集合になったら `DW-M02` / `DW-M08` に従い初回台帳を
erratum として残して取り直す。**

- **走行対象を `orchestrator/tests/test_mutation_harness.py` に限定する。**
  C-02 の実測により、全ファイル走行だと MU-3 で既存 14 node が赤くなり、
  うち 13 本は冗長 gate になる。対象限定で MU-1 / MU-3 とも単一理由になる。

| ID | 位置 | old → new | 期待 status | 期待 node |
|---|---|---|---|---|
| MU-1 | `tools/mutation_harness.py:1193` | `failed_keys == expected_keys` → `expected_keys <= failed_keys` | KILLED | strict-superset node のみ |
| MU-2 | 同上 (**変更前 HEAD `616ef5db` のテスト版で再走**) | 同上 | SURVIVED | (空) |
| MU-3 | `tools/mutation_harness.py:1193` | `failed_keys == expected_keys` → `failed_keys <= expected_keys` | KILLED | C-03 で追加した node のみ |
| MU-4 | `tools/mutation_harness.py:812-813` | `_match_key` が path 成分を捨てる形へ差し替え | KILLED | C-04 で追加した node のみ |
| MU-5 | `tools/mutation_harness.py:1193` | `return "KILLED" if ...` → 常に `"MISMATCH"` | KILLED | 等集合の正例 node (`test_normal_run_uses_cumulative_replacements_and_full_failed_line`)。**過剰拒否を検出する正例** (`DW-M01`) |
| MU-6 | 同上 (**変更前 HEAD のテスト版で再走**) | MU-3 と同じ | SURVIVED | (空) |
| MU-7 | 同上 (**変更前 HEAD のテスト版で再走**) | MU-4 と同じ | SURVIVED | (空) |

MU-2 / MU-6 / MU-7 が `DW-M08` の「テスト強化だけの wave は新旧両走を登録する」要求を満たす。

## 5. 裁定パッケージの追加項目

段 4 の R1〜R7 に次を足す。

| # | 項目 | 種別 |
|---|---|---|
| R8 | S1 を将来実装する場合の必須安全条件 — startup 前死亡の終端化 (A-02)、job-dir の所有・mode・shared FS 権威性 (A-03)、論理 condition key と generation nonce の分離 (A-07/B-06)、`launch.json` / `.done` の namespace 衝突回避 (A-07)、checker 採用までの E2E 結線 (A-04/B-09) | 設計前提 |
| R9 | 削減の計上条件と `DW-G01`。機械化した時点では bytes を計上せず、pointer 適用 + caller 強制の commit 後だけ計上する (B-03)。S1 を復活させるなら本実装前に薄い adapter で正常 / stale `.done` / 二重 waiter / producer kill の 4 実験を行う (B-08) | 手順 |

R6 は E-2 に従い次へ差し替える。

- `DW-G05` +274 bytes ([T-287] §5 確定文面)
- `DW-S01` / `DW-S02` +142 bytes (2026-08-05 に予算超過で撤回した 2 候補)
- F112 / F124 の `DW-S06-B` 追記 ([T-521] が T-454 pass へ委任)
- [T-505] の削除リスト + 恒久 3 機構の規範文 + 新 D draft (**起草のみ。発効は裁定へ**)
