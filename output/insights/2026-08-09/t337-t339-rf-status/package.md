# [T-337][T-338][T-339] 束ね裁定依頼 — 現況照合パッケージ (2026-08-09)

```text
authority: none
default_effect: no-state-change
```

本書は依頼「[T-337][T-338][T-339] を束ねた裁定パッケージ (RF 規範の統計設計 5 点、正例 artifact
適格性の権威境界 択 a/b/c、RF producer/consumer 設計 択 a/b、実測と推奨付き)」への回答である。
**新しく裁定を求める問いは 0 件である** — 依頼された 3 件はすべて裁定済みで、台帳に記録済みである。
本書は裁定文書ではなく、その照合結果 (どこで・どう裁定されたか) と、この線で現在も生きている
ユーザー手番の所在を返す。

---

## 0. 結論 (先に読むこと)

1. **依頼の 3 裁定はすべて裁定済み。** [T-338] は 2026-08-03 に 11 問へ組み替えのうえ **11/11 裁定完了**、
   [T-337] は択 (a) 採用 → **D162 (2026-08-05) で条文化済み**、[T-339] は択 (b) 採用 →
   Q11 で scope 具体化済み。依頼文の 5 点/択 a/b/c/択 a/b という切り方は 2026-08-02〜03 の
   起票時点の文面であり、現在の台帳状態より古い。
2. **[T-144] の裁定側 blocker は 2026-08-03 に解消済み**
   (`docs/archive/worklog-phase3-0803-142-143.md:22-24` に明記)。残る従属は裁定ではなく
   [T-139] の実装・計測連鎖 (追補 A → producer 実装 → pilot → validator/consumer → 本走) である。
3. この線で今生きているユーザー手番は 2 件だけ:
   **(i)** [T-139] R4 環境 probe (稼働中 wave) 完了後の**凍結承認パッケージの一括承認** (将来発生)、
   **(ii)** roadmap §3.6(3'') の**最厳格解釈の差の追認** (2026-08-07 に返却済み・未裁定)。

---

## 1. 依頼項目 1 — RF 規範の統計設計 5 点 → [T-338] (11/11 裁定完了)

**照合結果:** 5 点のままでは裁定できないことが D134 (2026-08-03、`docs/decisions.md`) で確定し、
11 問 (Q1〜Q11) へ組み替えて返され、**全問裁定済み**。正本は worklog (139)/(140)/(142)
(`docs/archive/worklog-phase3-0803-138-139.md:41-44, 411-415`、同 `0803-142-143.md:34-40`)、
パッケージ本体は `output/insights/2026-08-03_t338-rf-statistical-design/package.md`。

依頼文の 2 論点はこう決着している:

- **推定量 E[N]/E[D] か E[N/D] か** → **Q1 = (a) 総回復率 `RF = E[N]/E[D]`** (劣化幅で加重)。
  `E[N/D]` (session 等重みの典型回復率) は不採用。両者は劣化幅と比が相関すると一致しない別母数
  (D134 決定 (1))。
- **paired session 差の floor 定義** → floor 単独の量としては**消滅**した。判定は floor 値との比較でなく
  **Q3 = 同時信頼領域** (workload ごとに `N > 0 ∧ D > δ_D ∧ G > 0` の連言、D229 決定 (2) で
  3 条件と確定) で行う。paired 設計自体は roadmap §3.6(3'') の限定例外 (協議改訂 2026-08-07、
  [T-139] の RF 3-arm paired cluster study だけ) として採用済み。自動 unpaired fallback は
  D134 決定 (4) で禁止 (pairing 不成立 ⇒ 判定不能の fail-closed)。

残り: Q2 = `δ_D` を stock 比相対量で workload 別事前登録・primary endpoint は trace-disabled
`throughput_tps` 1 本。Q4 = 1 allocation = 1 subcampaign + trial 層 cluster 標本化。
Q5 = pilot 先行二段階・目標効果量 d≈1.0・**結果を見て J を足すことは禁止**。Q6 帰無分布 /
Q7 多重比較 family / Q8 選択的欠測 / Q9 区間と境界の帰属 / Q10 事前登録方式 / Q11 = 独立 validator が
raw receipt から再計算する gate 実体化 (これが [T-339] の中身になった)。

**状態: 裁定完了 → 実装待ち** (最新実体 = `docs/archive/worklog-phase3-0803-142-143.md:34-40`、
以後エントリ 319 までポインタ連鎖のみで更新なし)。

## 2. 依頼項目 2 — 正例 artifact 適格性の権威境界 (択 a/b/c) → [T-337] (択 a 裁定済み・条文化済み)

**照合結果:** 起票 (択 a = 新 D で権威境界 / b = ledger exact-one contract 改訂 / c = artifact 発行せず
計測記録に留める、`docs/archive/worklog-phase3-0802-117-121.md:360-364`) に対し
**択 (a) 採用済み** (同 `:1407-1409`)。その条文が **D162 (2026-08-05)**
(`docs/decisions.md`、一次資料 `output/insights/2026-08-05_t337-qualification-authority/`):

- 適格性は producer が宣言せず、**独立 validator の raw receipt からの再計算だけを権威**とする。
- consumer は decision を入力に取らず、trusted validator を同一呼出し内で再実行する。
- 状態は固定閉表 (`weak_denominator_not_certifiable` 等)。`RF > 1` は「stock 超過」とだけ述べる。
- 凍結 patch ledger の exact-one contract は不変。3 field は負制約であり昇格権威ではない。
- **機械化は DW-G04 発火条件 3 点が揃うまで見送り** (D162 決定 (10))。D229 決定 (6) により
  pilot 自身を発火条件 (i)(ii) の充足計測にする形で、D162 を書き換えずに進む。

残っていた種別 field 名も **[T-479] 択 (b) で裁定済み** (第一候補 `declared_use_class`、実装 wave の
新 D で確定。`rulings-inbox/2026-08-04-rulings-session-5rulings.md` §13)。

**状態: 実装可** (最新実体 = `docs/archive/worklog-phase3-0805-199.md:18-21`、以後更新なし)。

## 3. 依頼項目 3 — RF の producer/consumer 設計 (択 a/b) → [T-339] (択 b 裁定済み・scope 具体化済み)

**照合結果:** 起票 (択 a = consumer とセットで設計 / b = 正例 artifact 先行・consumer 後続、
`docs/archive/worklog-phase3-0802-117-121.md:370-372`) に対し **択 (b) 採用済み** (同 `:1413-1414`)。
[T-338] Q11 が中身を確定した (`docs/archive/worklog-phase3-0803-134.md:81-87`): 計測 producer /
attempt registry / schedule validator / RF calculator / [T-337] の適格性権威 / 層 3 の次版 /
selector・材料レポートの consumer / 双射・変異検査。状態 field の producer 自己申告は禁止
(D127 の恒真 gate の型)、層 3 calibration floor 閉表への混載も禁止。

**状態: P2・裁定済み** (最新実体 = 上記 0803-134、以後更新なし)。着手順序は D229 決定 (6) が
「producer → pilot → validator/consumer → 本走」と固定済みで、consumer 実装は pilot の後。

## 4. 依頼後の進展 (この線の現在地、2026-08-09 実測)

裁定は依頼文の想定よりはるかに先へ進んでいる:

- 代替 X の生死確認が両 workload で成立 (D187、request `892042`)。
- **D229 (2026-08-07):** 本走の実験計画を起草し 11 件の裁定へ分解 → 裁定済み →
  **事前登録 core を凍結** (digest `ac939af4…`、`output/insights/2026-08-07_t139-prereg-freeze/`)。
- **producer 実装 wave (2026-08-08):** NO-GO で実装せず。凍結 core の内部矛盾
  (`a01..a12` vs `a01..a13` が exact-key で互いに素) を発見し 4 問へ返却
  (`output/insights/2026-08-08_t139-producer-adjudication/package.md`) → 同日裁定
  (a13 採用・erratum で supersede)。
- **追補 A wave (worklog エントリ 316、2026-08-08):** `a01`〜`a13` を全部埋めて R1〜R7 + 凍結可否を
  返却 (`output/insights/2026-08-08_t139-addendum-a/package.md`) →
  **R1〜R7 全問推奨どおり裁定済み** (`rulings-inbox/2026-08-04-rulings-session-5rulings.md` §47:
  R1 (a) approval manifest + exact set / R2 (a) 第 2 erratum で stress check 化 /
  R3 (a) a13 移管 + 原子予約台帳 / R4 (a) gen_S 環境 probe 先行・導出写像を先に凍結 /
  R5 (a)+(d) 公表側 guard / R6 (a) schema は producer wave が発行し digest 固定 / R7 (a) 予備置換なし)。
- **現在稼働中:** R4 (a) を執行する環境 probe wave `dev-wave-t139-r4-probe`
  (handoff = `/work/1/SFC/tanab/dev-wave-jobs/handoff/dev-wave-t139-r4-probe.md`、段 0 起動中を確認)。
  probe 完了後に追補 A を再発行し、凍結承認パッケージを段階 1 一括で再提出する。

## 5. [T-144] への影響 (依頼が名指しした従属)

- [T-144] (スペクトル補間 = Shirakami-LTX との中間) の従属は **[T-139] + [T-338] Q1**
  (`docs/archive/worklog-phase3-0803-134.md:174-176` — 「E[N]/E[D] と E[N/D] では
  『既知解までの距離』の定義自体が変わる」)。
- Q1 = (a) `E[N]/E[D]` の裁定により、**[T-144] の裁定側 blocker は 2026-08-03 に解消済み**
  (`0803-142-143.md:22-24`)。物差しは確定している。
- 残る従属は実装・計測連鎖である: [T-139] の pilot が RF 計測経路 (producer → validator) を
  実証するまで、[T-144] は RF を反復測定に使えない。なお [T-338] の段 4 note
  (`dev-wave-jobs/t338-rf-statdesign/s4-notes.md`) が指摘したとおり、[T-144] は RF を探索ループ中で
  **反復使用**するため、一度きりの qualification とは多重比較 family が別物になる —
  [T-144] 着手時に Q7 の family を [T-144] 用に事前登録し直す必要がある (新裁定ではなく
  Q10 の事前登録手続きの適用)。

## 6. 推奨

1. **本依頼に対する新規裁定は不要。** 3 件とも裁定済みであり、再裁定は DW-S04
   (未見の新事実なしに承認済み裁定へ触れない) に反する。本 wave は照合のみで終端する。
2. **ユーザー手番は 2 件を待てばよい:** (i) `dev-wave-t139-r4-probe` 完了後の凍結承認パッケージ
   (段階 1 一括再提出) の承認、(ii) roadmap §3.6(3'') 最厳格解釈の差の追認
   (2026-08-07 の prereg-freeze wave が返却、`output/insights/2026-08-07_t139-prereg-freeze/README.md`。
   rulings-inbox に裁定記録なしを 2026-08-09 に実測)。
3. **[T-144] は着手可能性の判断を「裁定待ち」から「[T-139] pilot 待ち」へ読み替える。**
   着手時の追加作業は Q7 family の [T-144] 用事前登録のみ。

## 7. 実測の要約 (本照合が拠った一次確認)

- ポインタ連鎖: [T-337]/[T-338]/[T-339] の worklog 連鎖をエントリ 319 (2026-08-09) から実体記述まで
  一段も欠落なく遡及 (それぞれ 0805-199 / 0803-142-143 / 0803-134 が最新実体)。
- 台帳: D126 決定 (3)、D134、D162、D229 を本文で直接確認。
- repo 外: rulings-inbox 全 12 file を走査 — [T-337][T-338][T-339][T-144]/RF の未記録裁定・見送り裁定は
  §13 (T-479) と §47 (T-139 R1〜R7) 以外に**存在しない**。§47 と 0805-199 の逐語は親が直接再確認した。
- 稼働 handoff 7 件を走査 — 本 wave と scope が重複する wave は無し。`dev-wave-t139-r4-probe` は
  本照合の対象裁定の**執行側** (競合ではない)。
