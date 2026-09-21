# 本体論文 (日本語) の結果・考察草稿 2026-09-21b 版 (同日第 2 版) — B-8 の 3 値判定 `pass` を反映し、同じ wave で要旨・結論と限界節も改めた (docs のみ、台帳 ID 未起票の執筆依頼)

authority: none / default_effect: no-state-change (可変状態の正本は worklog 末尾と現行 phase doc)

- 成果物: `results-discussion.md` (本 dir)。**同日の前稿 `output/insights/2026-09-21/paper-results-ja/results-discussion.md` (2026-09-21 版、worklog entry 1772) を
  supersede する。** 前稿の bytes は変えない (wave 開始時の sha256 `b593e70a…` を記録 commit 時にも照合する)。前稿 dir の `README.md` の冒頭に前方 pointer の節を足す
  (09-20 → 09-21 の先例と同じ)。
- 同じ wave の成果物: 要旨・結論の同日第 2 版 `output/insights/2026-09-21/paper-abstract-conclusion-ja-b/{abstract,conclusion,README}.md` (前稿 = 同 `paper-abstract-conclusion-ja/`)、
  限界節の 2026-09-21 版 `output/insights/2026-09-21/paper-intro-ja/{limitations,README}.md` (前稿 = `output/insights/2026-09-20/paper-intro-ja/limitations.md`、
  別表は同 README §2)。**wave の記録 (段 1 の実測・段 6 のレビューと裁定・検査) は本 README に集約する。**
- wave: `worktree-dev-wave-paper-b8-pass-ja` (背景 job、job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-b8-pass-ja/`、依頼の逐語は同 dir の
  `request-verbatim.md`、段 1 brief は `s1-brief.md`)。
- 起点 local main = **採用時点 `d99c556df`** (2026-09-21 13:35 JST、worklog entry 1795 までの fold を含む。着手直前の local main から fresh worktree、
  開始 gate rc=0 = job dir `startup-gate.log`)。段 4 直前に main を再走査し前進 0。
- **新規の測定は 0 件。** 凍結物 (results 稿・版・claim-evidence・figures) と前稿本文の bytes は 1 byte も変えていない。実装面の差分 0 で変異 matrix は `DW-S04` により免除、
  受入全走は免除しない。
- 依頼の確定事項: 対象 3 組 (結果・考察 / 要旨・結論 / 限界節)、出所は B-8 の結果稿 `docs/paper-story/results/2026-09-21-b8-final-candidate-longrun-verify.md` と
  insight `output/insights/2026-09-21/t2807-b8-effective/README.md`、旧稿の bytes は不変で同日版の命名規則に従う新版、条件語 (30 枠、extime 10 s、8 反復 × 3 workload、
  対象が案 A) を要約で落とさない、英語稿なし、並走の論文ストーリー 21c 版 wave と同じ結果稿に書き方を揃える、本題の執筆だけ (gate・検査・台帳・一般化の追加は scope 外)。

---

## 1. 一行で

3 稿の前稿の骨格と本文を継承し、B-8 (最終候補の種を変えた長時間検証) を「未発効・未取得」から「発効した事前登録 v1 の下で、案 A に対する
独立 8 反復 × 3 workload・extime 10 s の検証で判定集合 30 枠すべて anomaly 0、3 値判定 `pass`」へ移した。結果・考察稿は §6 を 6.1 (採用候補 2 genome の
検証相、案 B) と 6.2 (B-8、表 8b) に分けた。あわせて、新しい採用時点で前稿の記述を偽にしていた状態語だけを最小限に直した (§3)。

## 2. 段 1 の実測 (親、2026-09-21 14:0x〜14:3x JST、login node、読み取りだけ)

| 項目 | 実測 | 稿での扱い |
|---|---|---|
| B-8 の main への着地 | 発効 commit `624c84986` (08:42 JST)、land 着地 tip `7bde4b60e` (10:58 JST)、fold `acd7cdb30` (11:03 JST、D2202 / entry 1791 を採番) | 3 稿の前稿の採用時点 (`285477c00` = 09-21 00:21 JST / `482f19b88` = 09-20 17:56 JST、commit 時刻) はいずれもこれより前 |
| B-8 の数値と限定 | 結果稿 §3.1〜§3.4 と §4 の限定 11 件、insight §5 / §6 | 表 8b と「言えること / 言えないこと」は結果稿 §3.3 / §4 の逐語・言い換えに限る |
| 論文ストーリー入口 | `docs/paper-story/README.md` の stale 注記 3 (B-8 の発効と判定、仕分け (2) は発効をもって「独立 process の自己シード」へ改まる、検証相は B-8 に数えない) | B-8 の語彙の照合先 (21c 版 wave も同じ出所) |
| 前稿の採用時点以後の着地の走査 | worklog entry 1771〜1795 (結果・考察 / 要旨・結論) と 1748〜1795 (限界節) の見出し、D2186 / D2194 / D2200 の項見出し | 前稿の記述を偽にするものだけを直す (下の表)。B-5 の試走完走 (entry 1779) と段階認可 (D2200 項 1) は「本走は未認可」を偽にしない |
| 旧稿の path を読む機械 file | `*.py` / `*.json` / `*.sh` / `*.toml` / `*.yaml` の走査で診断 JSON 1 件 (`output/insights/2026-09-21/land-roundtrip-diagnosis/waves.json`、データとしての言及) だけ。sha pin 0 件 | 旧 path はそのまま残す |
| 同日版の命名 | 同日第 2 版の先例は insight dir `paper-story-20260921b` だけ (`output/README.md` は子名に日付を重ねない) | 同日第 2 版は `-b` 接尾 (`paper-results-ja-b/`、`paper-abstract-conclusion-ja-b/`)。限界節は日付が変わるので `2026-09-21/paper-intro-ja/` |

## 3. 前稿の記述を偽にしていた状態語 (B-8 以外、最小限に直したもの)

| # | 稿・箇所 | 前稿の記述 | 本稿 | 根拠 (実施記録) |
|---|---|---|---|---|
| 1 | 結果 §12・結論 §7・限界 §5 | g1 の起動検査は既存の不整合 2 件で拒否 | 2 件は整合済み、live は ccbench pin 前進後の段階 4 (binary admission policy 不一致) で拒否 | D2196 / entry 1776、entry 1787 / 1790、D2201 |
| 2 | 結論 §7 (結果 §8.1 は 1 文追加) | 同 job stock 対照は driver の修復と再投入の認可を待つ | driver は修復済み (緑は結合検査まで)、実機の再投入は予算の再提示待ち | D2205 / entry 1795、`t2795-pair-repair` §0 |
| 3 | 限界 §1 | A-1 の独立再現 2 本目は未投入で測定値は無い | 2 本とも完走、同一配置の反復で分類と符号が一致した観察 | entry 1755、D2194 項 6 |
| 4 | 限界 §3 | 「非列挙」の定義の置き直しは未裁定 | 2026-09-02 に裁定済み、壁と休眠は不変 (**前稿の執筆時点で既に偽**) | D1441、21b 版 §2 第 3 幕 (b)、20b 版の訂正 1 |
| 5 | 結果 §6.1 | 検証相は B-8 の 3 要素 (対象・種・長さ) のいずれも要件と違う | 対象と長さが違う (種の仕分けは B-8 の発効で独立 process の自己シードへ改まった) | insight §2、stale 注記 3 |
| 6 | 結果 §12 (pin) | §3〜§6 はいずれも pin `511c9538` の下 | §6.2 の B-8 だけが前進後の pin `e9e477ca` の下 | B-8 の結果稿 §1.2 |

## 4. 段 6 read-only レビューと裁定

(段 6 の実施後に書く。)

## 5. 検査と受入

(段 7 の実測後に書く。)

## 6. 限界・言わないこと

- 3 稿は執筆者向けの日本語草稿であり投稿本文ではない。英語稿は作っていない。新規の測定・図・gate・検査・台帳は足していない。
- 前稿の本文は継承しており、§3 の表と B-8 の箇所以外を採用時点 `d99c556df` の正典と逐文で照合し直してはいない。論文ストーリー 2026-09-21 版・21b 版
  (entry 1773 / 1793) の本文との逐文照合もしていない (走査は worklog entry の見出しと D の項見出しによる)。
- 稼働中・未着地の wave (論文ストーリー 2026-09-21c 版、B-4 の対応証拠、mocc の X/P 計装、B-5 の Tier0 など) の内容は数えない。
- B-8 の `pass` は規則の機械適用の出力であって研究の成功宣告ではない (D12)。本 wave はそれを論文草稿へ運んだだけで、判定・測定を足していない。
- 文書成果の完了であり、未取得の測定 (A-1 充足・A-5・B-1・B-2・B-4・B-5 など) や Phase 3 全体の完了を意味しない。
