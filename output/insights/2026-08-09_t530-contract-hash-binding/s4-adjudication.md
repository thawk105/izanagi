# [T-530] 段 4 裁定 — real/refuted、採否、scope、plan v2、変異事前登録

## 親が独立に実測して確定した事実 (段 3 の争点を解く)

1. **D125 決定 (2)「OTHER の campaign_id は 1 bit も変えない」は、T-343 が既に破って land 済み。**
   `orchestrator/tests/test_p3_s4_loop_trigger_gating.py:107-116` が
   `_PRE_T343_OTHER_CAMPAIGN_ID = ...-3f72ecd5` と `_T343_OTHER_CAMPAIGN_ID = ...-ccba936e` を
   並べて pin しており、D125 が根拠に挙げた「既存の最終成果物」の id は現行コードでは再現しない。
2. **既存 30 campaign の `campaign.lock` は 30/30 が `build_admission` を持たない (pre-T343)。**
   したがって `ident.campaign_id(config_for(...))` による再計算は**現時点で既に**既存 dir を
   1 本も指していない。これは本 wave が開ける穴ではなく status quo である。
3. **`replay.discover_campaign_dir` は元々 id 再計算を避け、dir 名 prefix で discover する**
   (`replay.py:89-107`、C1 回避として明記)。歴史 campaign の読み出し経路は id 非依存である。
4. **母数訂正**: official campaign dir は **30**、うち WAL 3086 record は全て
   `env_tag=linux-baremetal`。repo 全体の `campaign.lock` 32 のうち 2 本は
   `output/insights/2026-08-04_wave-a-campaign-transport-smoke/` 配下の smoke evidence である。
   親 brief の「32」は母集団混在の誤りで、レンズ B P-01 が real。

## 所見の裁定

### real・採用 (本 wave で実装する)

| 所見 | 裁定 | 反映 |
|---|---|---|
| F-02 | real | 照合は恒真でない。設計を維持する |
| F-03 / B-04 | **real・must-fix** | tail repair と recovery の**追記より前**、同じ fd lock 内で parse 可能 prefix の照合を完了する |
| B-03 | **real・must-fix** | 必須性を record の field 有無から推論しない。**lock が H を束縛しているときだけ必須**とする |
| B-07 | **real・must-fix** | equality だけでなく `resolve_by_contract_sha256` で ever-active 解決し、COMMIT の `env_tag` と解決契約の `env_tag` を照合する |
| B-09e / M4 / T06 / T15 | **real・scope 縮小** | qualification event sink 2 口は WAL でなく T126 event ledger。**本 wave から外す**。COMMIT 束縛は `wal.log` の 2 口のみ。AST gate は `len == 2` を維持 |
| T12 | real | matching resume の正例は「evaluate/build が呼ばれないこと」を spy する |
| 揮発 golden (B 節末) | **real・must-fix** | `_T530_*` golden を ambient active head から導出しない。明示構成した contract から導く |
| M2/M6/M7/M8 | real | 帰属不成立。単独 validator の対向 2 例へ差し替える (下の事前登録) |
| B-11 | real・不採用 | 分割案は妥当だが、S8b と qualification を外した後の残りは所有が割れず中間赤を生む。**単一 Codex 単位のままとする** (理由 = ident/wal/loop が同一不変条件を分担) |

### real・scope 外 → 裁定パッケージへ返す

| 所見 | 返す理由 |
|---|---|
| F-04 / B-06 | historical 21 本の `historical-not-reclassified` を certified 入力から外すかは、`docs/phase3.md:409` が「最終成果物」と呼ぶ既存 campaign の受理集合を変える。**承認外の受理縮小**になるため親は決めない |
| F-06 / B-05 | raw reader (`screening_driver`, `s1_report`, `s1_known_axes_freeze`, `s8b_oracle_report`) への照合配線。既存成果物を遡って拒否しうるので同上 |
| B-08 / B-09a | S8b private lock の exact-4 化と offline report 側の照合。標準 identity lock ではない別機構で、consumer 側の独立 wave |
| P-06 | `attestation_mode="none"` の receipt 発行。起票文は言及するが T-530 裁定文は「identity と WAL COMMIT」しか言わない。[T-658] の「全書込み口配線」とは別問題として返す |
| F-09 / P-05 の残り | D125 決定 (2) を decisions 上どう supersede 表記するか (T-343 が既に破っている事実を含む) |
| F-12 | contract を更新すると campaign id が分裂する結合。[T-657] の pegasus 第 2 世代活性化と直結するので裁定へ上げる |

### refuted

| 所見 | 反証 |
|---|---|
| F-01 | COMMIT 行だけの複写は `wal.py:995-1001` の attempt topology が先に拒否する。発火例から外す |
| F-05, F-10, B-01, B-10, P-02, P-07 | レンズ自身が反証済み。親も再確認した |
| F-07 (2) / F-08 / P-03 の「再計算で到達不能になる」 | **既に status quo** (上の実測 2・3)。本 wave が開ける穴ではない。ただし worklog にはこの事実を明記する |
| P-01 の件数 | real。母数を 30 official + 2 smoke evidence へ訂正した |

## plan v2 (実装する形)

1. `model.py` に共有 wire key を置く (`wal → ident` の循環回避)。
2. `ident.bind_environment_contract(cfg, contract)` を追加し、`search_config` へ
   `environment_contract_sha256` (64 lowercase hex scalar) を束縛する。env_tag・generation・
   receipt 属性・日時は入れない。既存の異なる値は上書きせず拒否する。
3. `canonical_preimage` は certified config でこの key を必須にする。lock の top-level は
   exact 5 key のまま変えない。
4. `loop.run_campaign` は admission bind → authorization → environment bind → campaign_id の順に
   固定する。認可前に id / layout を作らない。
5. `pipeline.evaluate` は guard の戻り値を保持し、**`wal.log` 経由の COMMIT 2 口**に
   `contract_sha256` を入れる。他 stage には入れない。
6. WAL 側に共有 validator を置き、
   - 期待値は campaign.lock の `search_config.environment_contract_sha256` から読む。
   - lock が H を束縛していない campaign では要求しない (legacy / guided lane)。
   - lock が H を束縛していれば、全 COMMIT に exact H を要求する。欠落・型不正・大文字・
     非 64hex・不一致を拒否する。
   - H は `env_contract.resolve_by_contract_sha256` で ever-active 解決し、解決契約の `env_tag` と
     COMMIT record の `env_tag` を照合する。
   - **この検証は tail repair の receipt 書込み・truncate と recovery の追記より前**に、
     同じ排他区間で行う。
7. `_validate_attempt_topology` に `campaign_lock` を渡す (4 呼出し元すべてで成立済み)。

## 変異事前登録 (DW-M01。anchor は統合 commit 後に `DW-M07` で再検証)

| # | 位置 | old → new | 期待赤 | 単一理由性の根拠 |
|---|---|---|---|---|
| 1 | `ident.bind_environment_contract` の衝突検査 | 条件 → 恒偽 | 束縛衝突 helper test | helper 直呼びで後段 gate に覆われない |
| 2 | `pipeline` no-bench COMMIT payload | H → `"0"*64` | no-bench WAL 束縛 test | raw record を直接 exact 比較する test |
| 3 | `pipeline` bench COMMIT payload | H → `"0"*64` | bench WAL 束縛 test | 同上 |
| 4 | validator の実値取得 | `.get(KEY)` → `.get(KEY, expected)` | 欠落拒否 test | 欠落だけを通す。topology は正当 |
| 5 | validator の必須性判定 | lock 由来 → record の field 有無由来 | 恒真化検出 test | 旧 writer COMMIT が自動 exempt になる |
| 6 | validator の呼出し位置 | repair より前 → repair より後 | 順序 test (repair receipt 不発生を assert) | 拒否時に WAL bytes が変わるか否かの 1 点 |
| 7 | validator の H 解決 | `resolve_by_contract_sha256` 呼出し削除 | 未知 H 拒否 test | self-consistent な偽 H を受理する |
| 8 | validator の env 交差検査 | 削除 | env_tag 不一致拒否 test | H と record env の食い違いだけが理由 |

正例 (承認外の受理縮小を検出する) を 2 件必ず登録する。

- lock=H_A・全 COMMIT=H_A の campaign は resume で terminal skip され、evaluate/build が呼ばれない。
- lock が H を束縛しない legacy / guided campaign は従来どおり読める。

## 成果物影響 (DW-G05)

- 実装する: 今後の campaign-id が変わり、WAL COMMIT に 1 field 増える。認可の事実が
  成果物 bytes に残り、改竄・移植・旧版 writer の COMMIT が resume の terminal 集合へ
  入らなくなる。既存 30 dir の bytes と凍結 23 件は不変。
- 実装しない残件 (裁定へ返した 6 件): historical 21 本と raw reader 経由では、無束縛 COMMIT が
  依然 certified 入力に残る。**したがって本 wave は「proof chain が全経路で完結した」とは
  名乗らない。**
