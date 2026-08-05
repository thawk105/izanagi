# 段 4 裁定 — [T-337] 正例 artifact の適格性権威

親が段 2 プランと段 3 敵対 2 レンズの所見を real/refuted・採否・scope 内外で裁定した結果。

## 総合判定

**DW-G04 = 不成立。本 wave は docs-only とし、段 5・6 を飛ばして `4→7→8→9` とする。**

4 系統が独立に同じ結論へ至った。(i) 親の段 1 実測 6 (正例 artifact 未存在)、(ii) 段 2 プラン §3、
(iii) レンズ A 総括、(iv) レンズ B 総括 (「唯一の 3-arm path `877859` は不成立かつ J=1、T-126 は
二者・no-promotion、現行層 3 は qualification lineage を拒否、RF consumer/caller は 0 件」)。
親も独立に確認した — `output/env/pegasus/qualification/` は**存在しない** (実 receipt 0 件)。

実装差分がゼロのため、**変異 matrix と受入全走は射程外**である (`DW-S04`)。

## 所見の裁定

### 採用 (real) — 新 D 条文へ反映する

| # | 所見 | 出所 | 裁定 |
|---|---|---|---|
| R1 | validator の source hash は「その validator が実行された」証拠にならない。detached decision を信用してはならない | A5 | **採用**。条文へ「consumer は decision を入力として受け取らず、trusted validator を同一呼出し内で raw path から再実行する」を明記する。既存先例 `artifact_admission.require_admitted_campaign()` と同型 |
| R2 | 前後 hash 比較は ABA と検証後差替えを防がない | A6 | **採用**。条文へ「単一 fd / snapshot で読み、hash と parse は同一 byte buffer に対して行う。symlink を拒否する」を明記する |
| R3 | 状態閉表が Q9 裁定の `weak_denominator_not_certifiable` を欠く。「少なくとも〜」は閉表を将来拡張可能にする表現 | B4 | **採用**。状態名は裁定済みのものを含む固定閉表とし、「少なくとも」という書き方をやめる |
| R4 | RF の `trial_id` は既存 8c `trial_id` (H1/H2 × on/off/swapped の 6 cell、arm/holdout/campaign_id 束縛) と別実体 | B5 | **採用**。親が独自に導入する識別子であり裁定対象外のため、設計メモでは `rf_trial_id` と綴り、既存 `trial_id` との foreign-key を持たない旨を明記する |
| R5 | arm/source/binary を事前登録 identity へ再束縛するための入力 field が存在しない | A2 | **採用**。設計メモは「再束縛する」と書かず、「再束縛に必要な field が現在は不在であり、producer 設計と同時に決める必要がある」と書く |
| R6 | 提案された双射・family binding は自己根付きであり、成功した試行だけを含む prereg を後から作れる | A3 | **採用**。設計メモは file-drawer を塞いだと書かない。prereg manifest の path/hash・期待集合・alpha 台帳が別途要ることを未解決として明記する |
| R7 | `cluster_id` の自己申告だけでは真の J=1 を J=11 にできる | A4 | **採用**。cluster を node / 時間窓から独立に導出する規則が未設計であることを明記する (Q4 は allocation ID すら独立性の必要十分条件でないと裁定済み) |
| R8 | docs-only なのに未実装層を現在形の保証として数えている | A9 | **採用**。設計メモは全層被覆を「本 wave 0/9」と数え、将来形で書く |

### 採用 (real) — 親 brief の誤りとして訂正する

| # | 所見 | 出所 | 裁定 |
|---|---|---|---|
| R9 | 「適格性 field を読む consumer は 0 件」は誤り。ledger contract 2 call site と evidence validator 2 call site が実際に読み、不一致なら計測を止める | A7 / B2 (独立に一致) | **採用・親の誤り**。正しくは「**昇格 (promotion) 権威として読む consumer が 0 件**」であり、既存 rung に対する authoritative な**負制約**としては現に機能している。brief の実測 3 と provisional 裁定 (P2) の後半を訂正する |
| R10 | (P4) が D126 決定 (4) を過度に一般化し、裁定済みの代替 X 再走まで禁止している | A8 / B3 (独立に一致) | **採用・親の誤り**。D126 決定 (4) が禁じたのは「結果を見てから同じ probe の候補・workload を差し替える」ことだけである。事前登録を新たに commit した新 study は裁定済みで許されている。本 wave が正例を作らない理由は **scope と実経路不在**であり、D126 決定 (4) ではない |
| R11 | T-126 receipt は repo 外ではなく `$REPO_ROOT/output/env/pegasus/qualification/t126` に書かれる | B6 | **採用・親の誤り**。brief の「repo 外の persistent root」は誤り。親が独立に確認し、当該 directory は**存在しない** (実 receipt 0 件) ため DW-G04 の結論は不変 |

### scope 外 — 裁定パッケージでユーザーへ返す

| # | 所見 | 出所 | 裁定 |
|---|---|---|---|
| U1 | 種別軸の field 名を `artifact_role` のままにするか改名するか | A1 / B1 (両レンズが blocker) | **本 wave では決めない。** [T-318] と [T-337] のユーザー裁定は literal に `artifact_role` と書いており、親が独断で `declared_use_class` へ読み替えるのは `DW-S04` の「実装方向まで裁定済みの項目を非同値な択一へ戻さない」に反する。段 2 の改名案は**不採用**とし、新 D は field 名を確定させず、衝突の事実と両案をユーザー再裁定へ返す |

**U1 に添える新事実 (親が実測):** 既存 `artifact_role` は `orchestrator/campaign/s8b_oracle_artifacts.py:26`
で `{manifest, observations, verdict}` (exploration oracle の**文書種別**) を意味し、commit `4857534`
(**2026-07-20**) で land している。[T-318] の裁定 (worklog (116)、2026-08-02) と [T-337] の裁定
((121)、同日) は**いずれもこの衝突に触れていない**。したがって「裁定時点で未見だった事実」ではなく
「裁定記録が扱っていない事実」である。加えて `artifact_class` も `docs/ruleops.md:126` で
`derived-report` の別用途に既出であり、素直な代替名も 1 つ埋まっている。

**択一:** (a) literal `artifact_role` を種別軸として維持し、exploration oracle 側の文書種別 field を
改名する (production 8 hit・CLI producer 1 経路が影響)。(b) 種別軸を別名にし、[T-318]/[T-337] の
裁定文を明示 supersede する。(c) 同名のまま schema 文脈で二義を許す (D75 に抵触するため親は非推奨)。
**両レンズの推奨は (b)、ただし両者とも「親が独断で確定せずユーザーへ返す」ことを求めている。**

## 却下 (refuted)

なし。段 3 の全所見を real と裁定した。

## プラン v2 (本 wave で作るもの)

1. `docs/spool/decisions/` へ新 D の fragment — 権威境界の条文。**field 名は確定させない。**
   R1〜R8 を条文へ反映し、R9〜R11 の訂正を含める。
2. `output/insights/2026-08-05_t337-qualification-authority/mechanization-design.md` — 未実装の
   機械化設計メモ。将来形で書き、未解決点 (R5〜R7) と層被覆 0/9 を明記する。
3. `docs/spool/worklog/` へ worklog fragment — 実装差分ゼロのため変異 matrix・受入全走が射程外である
   ことを明記し、U1 をユーザー裁定待ちとして起票する。
4. 段 2 プランと段 3 両レンズの逐語を insights へ凍結する。

**production code・schema・test・凍結 artifact は 1 byte も変更しない。**

## 変異事前登録 (`DW-M01`)

**対象外。** 本 wave は gate を新設せず受理集合を変えない。無効化できる gate も、赤になる test node も
存在しない。後続実装時に、live positive artifact と実 consumer が揃った段階で改めて事前登録する。
