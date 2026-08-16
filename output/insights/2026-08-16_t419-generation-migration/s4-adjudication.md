# 段 4 親裁定 — [T-419] U-2 世代移行

base main `b7142712`、branch `worktree-dev-wave-t419-generation-migration`。
段 2 プラン (`s2-plan.md`)、段 3 敵対 2 レンズ (`s3-lensA.md` / `s3-lensB.md`)、
親の独立実測 (`parent-measurements.md`) を突き合わせた裁定。

**両レンズとも NO-GO。親も NO-GO を採る。ただし理由はレンズが挙げたものと同じではない。**

---

## 1. 裁定の結論

**本 wave は g2 の活性化を実施しない。実装差分ゼロとし、裁定パッケージをユーザーへ返す
(`DW-S04`)。段 5・6 を飛ばし `4 → 7 → 8 → 9` とする。**

停止根拠は `DW-STOP` の「承認済み裁定の前提を覆す未見の新事実がある、
またはユーザー裁定待ちなら該当段へ進まず停止する」である。

### 1.1 停止させた事実 (親が一次資料で確認)

**[D272] (2026-08-10、`docs/decisions.md:12507-12530`)**

> 環境契約の活性化 (較正) と ratified freeze の世代を、**上位層の権限束**として 1 つの
> identity のもとで解決する。正本は `docs/calibration-freeze-authority-bundle-design.md`
> (第 1 設計段、**裁定待ち**)。
> 理由: 較正の世代交代は凍結の世代交代なしに完了しない。
> **環境だけ進めると live admission の契約 hash が食い違い**、
> 固定 path の凍結成果物を上書きすると履歴不変条件と盲検封印の紐付けが同時に壊れる。

**[T-657] 設計正本 (`docs/calibration-freeze-authority-bundle-design.md:1-40`)**

- **状態: 段 0 実施中 (`incomplete`)**
- ユーザー裁定 2026-08-10 / 2026-08-11:
  - **Q2 = 上位束の承認 A・発効 X とも人間**、A は digest + 添付レポートの確認
  - **Q3 = lockstep (片側交代を拒否し、承認条件へ「両成分がともに交代」を加える)**
- **ユーザー裁定待ちが 1 件** (§12.3 R4 = 上位 cancellation record の扱い)

本 wave が計画していたのは、まさに **環境側だけの片側交代**を、**AI (Codex author) が発効する**
ことである。これは上記 2 件の既裁定に正面から反する。

### 1.2 8/16 の裁定はこれを破棄していない

- 裁定控え `2026-08-16-rulings-full-43rulings.md` に **`T-657` は 1 度も出現しない** (grep rc=1)。
- 控え §3.1 が名指しするのは [T-419] U-2 / [T-475] / [T-478] だけで、上位権限束には触れていない。
- [T-657] の worklog 最新エントリ (2026-08-12、archive `worklog-phase3-0812-484.md:409`) は
  docs 予算の残余についてであり、lockstep・人間手番を破棄していない。

**したがって「AI が単独で環境世代を発効してよい」は 8/16 裁定時の未見事実である。**
`DW-S04` の「承認済み裁定は裁定時の未見事実でだけ止め、親は不採用にせず、
新事実を添えてユーザー再裁定待ちへ戻す」に従う。

### 1.3 親自身の対案 (X) も取り下げる

親は段 3 へ対案 (X)「活性化を先に。移行前の方が悪い」を渡したが、
**親自身の実測 (M-3) とレンズ A の A-05 が独立に反証した。** 取り下げる。

---

## 2. 所見の real / refuted 裁定

### レンズ A

| id | 判定 | 裁定 |
|---|---|---|
| A-01 g1 の自己不整合が historical 経路で検証済み扱い | **real** | 親が独立確認 (`calibration_verify.py:112-142` は clock self-pass を再計算しない、`env_contract.py:601-612` は `quality.status` のみ)。**本 wave では実装しない** — 是正は受理集合を縮小し、g1 期成果物の歴史検証を落とすため、上位束の設計と対で決める。裁定パッケージへ |
| A-02 g1 origin と g2 campaign の混在 | **real だが未発火** | 現在 active な世代は 1 つだけで、混在の発火条件を満たす artifact path が存在しない。`DW-G04` により設計メモに留める。活性化 wave の必須 scope として引き継ぐ |
| A-03 上位 authority-bundle との衝突 | **real・停止根拠** | 上記 1.1。本裁定の中核 |
| A-04 g2 の取得 provenance は成果物だけでは立証できない | **real** | D143 (b) の clock 条件は支持されるが、`accepted` 文字列を活性化根拠にしない点は正しい。上位束の Q/A が束縛するか、人間が残余を明示受容するかを裁定パッケージへ |
| A-05 (X) の「移行前は何も走らない」は偽 | **real** | 親の M-3 と独立に一致。(X) を取り下げる |
| A-06 新規に閉じる経路と既に閉じている経路の混同 | **real** | 新規拒否 = floor static admission / ratified live launch / holdout producer の 3 経路。既存拒否 = silo current binding / prediction seal / live resume。親の M-5 と一致 |
| A-07 receipt に path を選ばせると受理集合が広がる | **real** | seam の設計制約として裁定パッケージへ。path/hash は人間承認済み束の generation record から resolver が決める |
| A-08 既知例外の空化は検査対象の縮小である | **real** | 現行テストは `ec.REGISTRY` = active view だけを走査するため、活性化で g1 が loop から消える。空化は「直った」ではなく「見なくなった」になる。**本 wave の最重要の防止事項**として活性化 wave へ引き継ぐ |

### レンズ B

| id | 判定 | 裁定 |
|---|---|---|
| B-01 g2 protocol 発行が循環で詰まる | **real** | 親も builder / writer / admission / wrapper を確認。seam なしでは floor v2 に到達できない |
| B-02 silo 完全検証が current binding で壊れる | **partially refuted** | 機構の指摘 (`silo_ladder_rung1.py:3564-3572` が current contract と照合) は real。しかし **severity は誤り** — 当該入口は今日すでに赤である (M-5 の実走)。「今動く能力が壊れる」ではなく「同じ入口に 2 つ目の不一致が加わる」が正しい |
| B-03 campaign identity の世代束縛が不完全 | **real・未発火** | A-02 と同型。活性化 wave へ引き継ぐ |
| B-04 activation record は正規経路で巻き戻せない | **real** | forward-only。誤発行の復旧手順が無いことは、人間発効 (Q2) を要求する既裁定の妥当性を補強する |
| B-05 移行テストの一部が production 自己参照 | **real** | 活性化 wave の変異事前登録で等価変異として弾く必要がある |
| B-06 親の焦点走は静的に再現不能 | **real** | そのとおり。赤 9 件は親の一時変異実測であり、レンズは独立確認していない。記録でそう書く |
| B-07 [T-478] (a)〜(e) の現況 | **real** | (d) 未実装が floor v2 を直接阻む。(a)(b)(e) 部分実装、(c) 未実装 |
| B-08 順序は seam 先 | **real だが本 wave では moot** | 活性化自体を行わないため順序問題は活性化 wave へ移る |

### 段 2 プラン

| 項目 | 判定 |
|---|---|
| pin 閉包の分類表 (§1) | **採用**。活性化 wave の一次資料として保存する |
| `env_contract.py` の編集は head 定数 2 件だけ (§2) | **下位 authority に限れば real**。ただし sanctioned transition 全体としては偽 (A の指摘どおり) |
| 既知例外の空化 (§3) | **不採用**。A-08 のとおり検査対象の縮小になる |
| source identity pin (§4) | **採用**。`env_contract.py` の bytes 変更は T126 series identity を再発行させる |
| current 束縛経路の一覧 (§5) | **採用。ただし A-06 の分類 (新規拒否 / 既存拒否 / 歴史生存) を重ねる** |
| P2 成立 (§6) | **不成立**。g1 は active view から消えるだけで ever-active resolver の受理対象からは消えない |
| P4 成立 (§6) | **成立**。D143 (b) の取得時受入検査は再実装不要 |
| P5 成立 (§6) | **成立**。`s8b_approved.CCBENCH_FULL_SHA` は既に `511c9538` |
| commit 順序 (§7) | **活性化 wave へ持ち越し**。ただし actor は人間である |

---

## 3. 親 brief の誤り (自認・レンズ確認分を統合)

1. **(13)(15) 「移行しなければ Pegasus 実行が落ち続ける」は誤り** — 親が M-1 / M-3 で自己反証。
   受理帯は g1/g2 で同一、壁 1 は方式 α 結線で構造上開いている。レンズ A-05 が独立に一致。
2. **「世代機構は実装済み、未実施は活性化だけ」は過度な一般化** — 上位 authority-bundle
   ([T-657]) と protocol generation authority が未完成である。レンズ A の指摘が正しい。
3. **(P2) 「既知例外の対象が消える」は誤り** — historical resolver が g1 を受理し続ける。
4. **(P3) 「歴史検証は全部生存」は過大** — silo の完全検証入口は current binding を含む。
   ただし B-02 の severity は親が M-5 で反証した。
5. **(8) の赤 9 件は親の一時変異実測にのみ依存する** — blast radius 全体の証明ではない。
6. **(11) 「(P1) の循環は存在しない」は builder レベルに限れば正しいが、運用経路では誤り** —
   writer が create-only で旧固定 path へ書き、実凍結領域への任意 path 書込みは拒否される。

---

## 4. 本 wave が実装しない理由 (安全な部分実装も採らない)

「活性化はできないが、周辺の hardening だけ入れる」案を検討し、**いずれも不採用とした。**

- **A-08 対策 (走査領域を `ever_active` へ広げる)**: 現時点で
  `ever_active == active == {linux-baremetal g1, pegasus g1}` であり、
  **走査領域を広げても検査内容が 1 bit も変わらない。**
  したがって「`ever_active` を `REGISTRY` に戻す」変異は**必ず生存する等価変異**であり、
  `DW-M01` の単一理由性を満たせない。活性化と同一 wave で入れる。
- **A-02 / B-03 対策 (世代混在の束縛)**: active な世代が 1 つしかないため発火条件を満たす
  artifact path を brief に書けない。`DW-G04` により設計メモに留める。
- **M-2 対策 (`effective_clock.method` の恒真ゲート是正)**: 是正すると期待側 (素朴法) と
  観測側 (方式 α) が不一致になり、**Pegasus の全 attestation が即座に落ちる。**
  活性化と対でしか入れられない。裁定パッケージへ。
- **seam (versioned protocol path)**: A-07 のとおり path authority は人間承認済み束の
  generation record から解決すべきで、その束が `incomplete` である。今作ると作り直しになる。

**結論: 実装差分ゼロ。変異 matrix は `DW-S04` により免除。受入全走は免除しない。**

---

## 5. 本 wave が実施すること (docs のみ)

1. **`docs/decisions.md:17896` の stale な記述の是正** — 「unmet — D143 のユーザー裁定待ち」は
   2026-08-16 の裁定で陳腐化した。正しい状態は
   「D143 は択 (b) で裁定済み。実施は [T-657] 上位権限束の lockstep 待ち」。
2. **新しい決定記録 (D96 手続)** — D143 (b) の裁定内容、実施が [T-657] に従属すること、
   および M-1 / M-2 / M-3 / M-5 / M-6 の実測を設計判断として残す。
3. **failures 台帳** — M-2 の恒真ゲートと、M-5 / M-6 の「pin 前進が凍結証拠の完全検証を赤にする」
   型 (DW-G03 の独立 2 例成立) を登録する。
4. **worklog fragment** — [T-419] / [T-420] / [T-475] / [T-478] / [T-987] の状態更新と、
   [T-987] (b) の `ccbench_pin` が既に承認定数側に入っている事実。
5. **裁定パッケージ** — 下記 6。

---

## 6. ユーザーへ返す裁定パッケージ (択一)

**問: 環境契約 g2 の活性化を、[T-657] 上位権限束の完成を待たずに実施するか。**

- **(a) 待つ (親の推奨)。** [T-657] 段 0 を完成させ、Q2 (人間 A / 人間 X) と
  Q3 (lockstep = 環境と凍結の同時交代) のとおり発効する。
  - 有利: 既裁定を破らない。凍結側と環境側の直積が人間承認を経る。
    B-04 の巻き戻し不能性に対して人間手番が保険になる。
  - 不利: [T-657] は §12.3 R4 がユーザー裁定待ちで、完成時期が読めない。
    その間 D143 (b) は「裁定済み・未実施」のまま残る。
- **(b) 環境側だけ先に発効する (D272 の片側交代拒否を、本件に限り解除する)。**
  - 有利: D143 (b) と [T-987] (b) の chain が今すぐ動く。
  - 不利: **D272 が名指しで却下した経路**である。live admission の契約 hash が食い違い、
    floor / ratified launch / holdout の 3 経路が新規に閉じる (A-06)。
    seam を同時に作らないと床値 v2 に到達できない (B-01)。
    発効は forward-only で巻き戻せない (B-04)。
- **(c) 上位束の完成を待たず、seam と test-net の hardening だけ先に land する。**
  - 有利: 活性化の準備が進む。
  - 不利: A-07 のとおり seam の path authority は上位束の generation record から解決すべきで、
    束が未確定のまま作ると作り直しになる。A-08 対策は等価変異になり検証できない (§4)。

**あわせて裁定を要する従属項目**

- **(i) M-2 の恒真ゲート**: `effective_clock.method` の比較を「両方が非空 str」から
  実体一致へ変えるか。変えると g1 active のままでは Pegasus の全 attestation が落ちる。
  活性化と対で入れるのが自然だが、**受理集合を縮小する変更なので単独裁定を要する。**
- **(ii) A-01 の historical grandfather**: 自己不整合な g1 較正を historical resolver が
  「検証済み」として受理し続けてよいか。是正すると g1 期成果物の歴史検証が落ちる。
- **(iii) A-04 の source acquisition proof**: g2 を active にする根拠を
  `quality.status=accepted` だけに置いてよいか、人間が残余リスクを明示受容するか。
