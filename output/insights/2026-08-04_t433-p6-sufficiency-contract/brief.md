# [T-433] 段 1 brief — P6 意味的充足契約の起草 (2026-08-04)

## scope

D150 決定 (6)(a) が「本 D では定義しない」と明示した空白 — **「実装のふりをした非適用」の判定基準** —
を埋める意味的充足契約 (P6 を「実装済み」と認定する基準) の**案**を起草し、裁定パッケージで
ユーザーへ返す。V1 (`NOT_CLAIMED` の射程 = global 免責か per-run gate か) の裁定案も同時に返す。
**実装しない** (ユーザー裁定の文言どおり「設計と裁定パッケージまで」)。

## 確定済みユーザー裁定 (2026-08-04 /rulings、worklog (175))

- [T-433] (V2): P6 設計 wave が意味的充足契約の案を起草して裁定パッケージで返す。
- 契約案は次の 3 要素を**必ず**含む (裁定の指定):
  1. **正負 calibration の具体反例** — 本物の実装が通り、偽物 (空 handler・恒真 assert 等) が
     落ちる具体ケース。
  2. **非空の限界効果を示す変異** — 実装が実際に発火し判定を変えることを示す変異。
  3. **独立検査者の要求** — 実装者と独立のコンテキストによる認定。
- 目的 = 空 handler と恒真 assert が D138 の列挙 (handler・全 witness-kind adapter・
  正負 calibration・未知 kind の fail-closed) を形式的に満たす穴を塞ぐ。
- V1: u2-na-bifurcation s4 の択 (a) `NOT_CLAIMED` を global 免責でなく per-run gate にする /
  (b) `NOT_CLAIMED` 構成では cap を開けないと明示 / (c) U2 のまま global 免責を許す。
  「P6 実装の裁定と同時に決める」既定方針は追認済みで、本 wave が裁定案を出す。

## 前提実測 (2026-08-04、親)

- P6 実装要素 (`derive_p6_cut` / `PrecommittedHypothesis` / `P6Derived` / `witness_class`) は
  `orchestrator/` `tools/` の *.py に **0 件** — D150「現時点の P6 は `NOT_IMPLEMENTED`」は現在も事実。
- `docs/phase3.md` は L478 に散文ポインタ「P6 の意味的充足と receipt … 未確定または未実装」のみ。
- main = 864613d (clean)。spool は空。

## 不変条件

- `MAX_APPROVED_GENERATIONS = 1` (D114) を変えない。cap-lift を機械 gate へ結線しない。
  機械検査・status field を新設しない (`DW-G04`: 発火条件を満たす既存 artifact path・計測 ID は 0 件)。
- 凍結 bytes 不変 — 成果物は新規 insight dir + spool fragment のみで既存ファイルを編集しない。
  事前登録文書 `docs/phase3-main-experiment.md` に触れない (S-1 freeze、D150 決定 (7) と同じ)。
- D150・D138 を supersede しない。契約案は D150 (6)(a) の空白を埋める**追補の案**として書く。
- 規律 2 の固定条項 (P6 は verifier の代替にならない・verifier を省略/短縮/緩和しない) は弱化不能。
- ユーザー裁定 (U2: `NOT_CLAIMED` だけを免責) を覆す案を親が採用しない — V1 の 3 択は
  いずれも U2 の「失敗に数えない」を保存する読みで比較する。

## 成果物の形

`output/insights/2026-08-04_t433-p6-sufficiency-contract/` に brief / s2-plan / s3-lensA / s3-lensB /
s4-adjudication / README (= 契約案本文 + 裁定パッケージ)。worklog fragment と decisions fragment
(D138 先例の「設計 wave の D」形式 — 契約案の形は D として記録し、採否と V1 はユーザー裁定へ)。

## DW-G05 (成果物影響)

実装差分ゼロのため certified 選択・材料レポート・試行台帳の値・受理集合・参照は**不変**。
起草しない場合 = 承認者が認定基準を持たず D150 (4-b) の fail-closed で cap-lift 承認が永久保留
(安全側だが、ユーザーが残した `NOT_CLAIMED` 免責経路が事実上死んだままになる)。

## 並列分割

段 2 = read-only codex 1 本 (契約案の起草)。段 3 = read-only codex 敵対 2 本
(レンズ A = 恒真化・ゲーム化・正しさ境界 / レンズ B = 実効性・consumer 結線・運用可能性)。
段 4 で「実装しない」を裁定し 4→7→8→9 (段 5・6 なし、変異事前登録・変異 matrix・受入全走は対象外)。
受入 = `tools/check_docs.py` + docs 影響テスト (login node)。

## 親の provisional 裁定 (攻撃対象)

- **(P1)** 契約は「人間 gate の判定規則 + 機械検査可能条項の列挙」として書き、実装 wave が来るまで
  機械 gate を作らない。各条項に §3.12 (2026-08-03 P6 設計 README) と同形式の検査可能度分類を付ける。
- **(P2)** V1 の推奨 = **択 (a)** — `NOT_CLAIMED` を global standing 免責にせず per-run
  (運転構成・revision・origin 単位) の gate にする。免責は保存する (D121 の cap 人質化懸念を回避)
  が、構成が変われば再判定。cap-lift receipt (T-434/V3) への束縛は T-434 の設計事項として境界を書く。
- **(P3)** 「非空の限界効果を示す変異」は変異テスト形式で条項化する — 契約の各必須条項に、それを
  破ると calibration 判定が反転する変異を最低 1 つ対応付け、反転しない条項は恒真として契約から落とす。

## 一次資料 (絶対パス)

- /work/1/SFC/tanab/izanagi/docs/decisions.md — D138 (L6718〜6803)、D150 (L7348〜7484)
- /work/1/SFC/tanab/izanagi/output/insights/2026-08-03_t244-p6-contract/README.md — P6 契約設計の正本
  (§3.11.2 が NOT_IMPLEMENTED の列挙、§3.12 が検査可能度表)
- /work/1/SFC/tanab/izanagi/output/insights/2026-08-03_t244-p6-contract/s4-adjudication.md — U1〜U5
- /work/1/SFC/tanab/izanagi/output/insights/2026-08-04_t244-u2-na-bifurcation/s4-adjudication.md — V1 の 3 択 (L103)
- /work/1/SFC/tanab/izanagi/docs/worklog.md — (175) の [T-433]/[T-244] 項
