# 段 1 brief — dev-wave [T-434] [T-1709] [T-1338]

基準 main `f5423e2fff3adb164731963ca33e82ed08d08c4d`。worktree
`/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-t1709-t1338`。

## 研究前進

8b oracle の受入経路には、D496 決定 1 が禁じた「過去の床値 campaign 由来の値・bytes を今回の
受理条件にする」束縛が 3 本残っている。事前登録は 2026-08-18 に対測定 (§10) へ移って発効済みなので、
宣言と実装が食い違ったまま official 系列が動く。本 wave はその 3 本を外し、8c 条件 2 については
「非干渉性は未解決」と本文へ明記して過大な主張を消す。完了判定 = 3 本の述語が消え、各々を
supersede する既存述語が正例で発火し、8c 本文に未解決の明記が入ること。

## scope (3 件)

- **[T-434]**: 実装しない。裁定は D1433 / D1434 として 2026-09-02 に着地済みと実測した (下記 P1)。
  本 wave は記録の照合だけを行い、二段束縛の部品は land しない (D1421)。
- **[T-1709]**: docs のみ。8c 条件 2 の証拠契約は据え置き、**条件 2 (非干渉性) が未解決である
  ことを明記**する。`DECIDER_VERSION` の bump も次世代 record の発行も行わない (D911)。
- **[T-1338]**: 実装。受入関門 3 述語を撤去する。他の 3 項 (driver の floor/budget null refusal、
  budget の凍結数値 loader、report の解決経路) は依頼が名指ししていないので scope 外。

## 確定済みユーザー裁定

- 本 wave の起動時裁定: 「撤去を scope に入れる」(2026-09-14、親が実測を添えて照会し回答を得た)。
- D1433: D1407 の内容 commit は単一の導入 commit。共有 git 信頼境界の統一は起票しない。
- D1434: P6 の所有は既存記録どおりとして停止項を閉じる。
- D911: 8c 条件 2 の証拠契約は据え置き、周辺の確定後に一度だけ改訂する。
- D501 決定 8: 撤去対象 3 述語とその冗長性の根拠。「いずれの撤去も受理集合を広げる」。
- D496 決定 1: 凍結した過去値を比較の基礎にしない。

## 不変条件

1. **絶対規律 2 を緩めない。** 撤去してよいのは D501 決定 8 が名指した 3 述語だけ。variant の
   correctness gate・anomaly 検出・serializability 判定には一切触れない。
2. **8b が凍結する事項を変えない。** `s8b_verdict` の条件 3 と scale gate は 2026-07-16 の
   ユーザー裁定が逐語凍結した truth table の一部であり、本 wave は触らない (D501 決定 7)。
3. **8c の条件契約 (§6 前提条件・§5 欄名・規範本文・発効ポリシー) の bytes を変えない。**
   変えると hash 世代台帳の bump が要り、D911 の「据え置き」に反する。
4. `_GENERATOR_SOURCES` の 5 file は本 wave の編集面に**入らない** (実測: manifest module も
   driver module も同集合に無い)。generator identity は動かない。
5. 撤去する各述語について、**supersede する既存述語が実在して発火することを正例で示す**。
   示せない述語は撤去しない。

## 成果物の形

- 実装差分: `s8b_oracle_manifest.py` / `floor_pair_driver.py` と、その所有テスト。
- docs: `docs/phase3-8c-preregistration.md` への未解決の明記、decisions 1 本 (撤去の採用理由)。
- insight: `output/insights/2026-09-14/t1338-floor-gate-removal/`。

## 実アンカー表 (親が現物で実測)

| # | 対象 | file:line | supersede する既存述語 |
|---|---|---|---|
| A | per-pair 床値対表 exact 検査 `_validate_holdout_floor` | `orchestrator/campaign/s8b_oracle_manifest.py:609` | freeze 全 byte hash 照合 `:1053` と、schedule holdout / cell 集合の独立検査 (D501 決定 4) |
| B | `floor_budget_snapshot_sha256` の生成 | 同 `:807` | 同 `:1053` |
| B' | 同 の照合 | 同 `:1093` | 同 `:1053` |
| B'' | 同 が属する文書 key 集合 | 同 `:58` | — (受理形が変わる。P2 参照) |
| C | driver の測定 binary bytes 束縛 `_validate_build_receipt` | `orchestrator/campaign/floor_pair_driver.py:1091` | 無し (D496 決定 1 により束縛自体が不要) |
| D | `s8b_verdict` の同等 strict 検査 (二重定義回避) | `orchestrator/campaign/s8b_verdict.py:846` | A/B を消すと連動する。所有に含める |
| E | 8c 条件 2 の非干渉性 | `docs/phase3-8c-preregistration.md:96`, `:214`, `:443`-`:449` | — (docs) |

## 割れうる前提 (親の provisional 裁定・攻撃対象)

- **(P1)** [T-434] は本 wave で実装できない。D1407 §1・§3 が内容 commit `G` に「実装一式
  (P6 本体・calibration・admission 結線・受領証機構・新 manifest・全 consumer 結線)」を要求し、
  D1421 が部品の先行 land を禁じる。P6 は実測で未実装
  (`reflux_formal_consumer.py:1480` が `P6Unavailable` を返す経路が生きている)。所有は [T-941]。
  → 親裁定 = 記録の照合のみ。覆す材料があれば段 3 で出す。
- **(P2)** `floor_budget_snapshot_sha256` を文書 key 集合から外すと **manifest の受理形が変わる**。
  既存の凍結 manifest bytes との互換をどう扱うかは未決。親の provisional = 「述語 (照合) と生成を
  外し、key は残して値を検査しない」形は**採らない** — 恒真な field が残るため。段 2 は両案の
  file:line と、既存 artifact への影響を出すこと。
- **(P3)** 述語 A の supersede 主張。D501 決定 8 は「構成集合の凍結は決定 4 の別述語が担う」と書くが、
  A は `pairs` の key 集合が「構成集合 − stock」と一致することも見ている。この分だけが
  純減にならないか、段 2 が実コードで確かめる。
- **(P4)** 述語 C の撤去で `s8b_binary_admission` の receipt 消費者がゼロにならないか。
  ゼロなら「呼び手の無い機構」を残すことになるので、段 2 が他の consumer を列挙する。

## 並列分割方針

- 段 2 = plan 1 本 (read-only)。段 3 = 敵対 2 レンズ並列 (正しさ境界と既裁定整合 / 実効性と正例負例)。
- 段 5 = 所有素集合で 2 単位を想定。単位 1 = `s8b_oracle_manifest.py` + `s8b_verdict.py` と所有テスト。
  単位 2 = `floor_pair_driver.py` と所有テスト。docs は親が書く。
