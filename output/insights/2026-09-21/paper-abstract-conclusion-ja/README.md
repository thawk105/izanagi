# 本体論文 (日本語) の要旨・結論の新規起草 — wave の記録

authority: none / default_effect: no-state-change (可変状態の正本は worklog 末尾と現行 phase doc)

- 依頼: ユーザー (2026-09-21、dev-wave 引数、台帳 ID 未起票)。逐語は job dir `HANDOFF.md` の冒頭。
- wave: `worktree-dev-wave-paper-abstract-conclusion-ja` (背景 job c9f564c0、job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-abstract-conclusion-ja/`)。
  着手直前の local main `285477c00` から fresh worktree (startup gate rc=0)。同じ wave で結果・考察稿の 2026-09-21 版
  (`output/insights/2026-09-21/paper-results-ja/`) も作った (A-1 attempt-0002 の反映)。
- 構成: docs-only 軽量版 (`DW-C00`)。段 2・3 省略、書き手は親、段 6 に read-only codex レビュー 2 本 (A: 結果稿の次版 / B: 要旨・結論) + 焦点再レビュー
  (一次資料から事実を再抽出する docs-only wave の規則)。実装差分ゼロなので変異 matrix は免除、受入全走は land 前に実施。

## 1. 成果物

| file | 内容 | 大きさ |
|---|---|---|
| `abstract.md` | 要旨草稿 — 短縮版 (約 550 字)、標準版 (約 1,500 字)、構造化版 (背景 / 目的 / 方法 / 結果 / 結論)、要旨に書かないこと | 約 14 KB |
| `conclusion.md` | 結論草稿 — 問いに対する答え、否定的結果が決めた価値の所在、正しさの側と測定契約の側の到達点、未実証のまま残る主張、方法論としての含意、次に必要な証拠 | 約 18 KB |

2 稿は平易な日本語の論文本文で、末尾に「出所 (執筆者向け)」を持つ (先例 = 序論・貢献・限界稿と同じ書式)。本文には T 番号を書かず、D 番号と
一次資料は出所へ寄せた。版 (`docs/paper-story/`)・claim-evidence 稿・results 稿・図・README・既存の 4 稿は 1 byte も変えていない。

## 2. 入力と正本の選び方

- 依頼は「story 最新版 §6 と 4 稿 (いずれも 2026-09-20 版) から起草。story の 2026-09-21 版が main に在ればそれを、無ければ 20b + README stale 注記を正本にする」。
  着手時の local main `285477c00` に 2026-09-21 版は無く (並走 wave [7e7657] が同時刻に起草中。その成果は数えない)、**正本 = `docs/paper-story/2026-09-20b.md` §6 +
  `docs/paper-story/README.md` の stale 注記 5 件** (pin 前進、[T-1871] 追補 1、B-8 試走認可、K2 pair 初投入、A-1 attempt-0002 完走)。
- 4 稿 = 序論・貢献・限界 (`output/insights/2026-09-20/paper-intro-ja/`)、方法 (`output/insights/2026-09-20/paper-methods-ja/`)、関連研究
  (`output/insights/2026-09-20/paper-related-work-ja/`) の 2026-09-20 版と、結果・考察の **2026-09-21 版** (同 wave で attempt-0002 を反映した次版。依頼の
  「2026-09-20 版」は起草時点の最新版を指すと読み、次版がある以上それを使う。attempt-0002 以外の数値・主張は 2026-09-20 版と同じ)。
- 状態語は、認可・禁止・手番を D 本文で、完走・発効・未達・件数を採用時点の実施記録 (worklog entry と記録 insight) で確かめた: A-1 attempt-0002 の
  認可は D2172 項 2、gate は D2178 (投入は同決定に含まれない)、完走は entry 1755 と `output/insights/2026-09-20/t2792-a1-sized-attempt2/README.md`、
  充足・formal 化はユーザー手番 (D2044 項 8)。B-7 の限定付き充足は D2174 項 3。g1 の承認方式は D2180、発効と起動検査未達は entry 1742 と
  `output/insights/2026-09-20/t2724-ax-delegated/README.md`。B-5 は D2158 / D2172 項 4 (本走未認可)。B-8 は D2175 / D2186 (試走認可) と D2190・entry 1766
  (発効前試走、未発効)。K2 pair の不成立は D2187 と entry 1754。B-4 の実施不可の規則は D1986 項 4、赤 precursor 0 件は story 2026-09-20b 版 §6 と結果・考察稿 §8.2
  (worklog entry 1748〜1770 の見出しに更新なし)。Silo 固定の解除は D2114、pin 前進の実施は README stale 注記 1 件目 (entry 1747)。LLM の必要性 (D1067)、非列挙の壁 (D1409)、
  権限の不在 (D1829)。
- 正典の文をそのまま運ばず、序数・不在の含意を立てない: 位置づけは関連研究稿 §2.1 の 1 文の逐語引用だけ (構造化版の目的、結論 §5)、「先行なし / 世界初 /
  唯一 / 最も近い / N 本目」は使わない。合成軸の勝ち負けは対象 (書込ロック順の並べ替え / コンパイル時フラグ最適化 / 静的 backoff 最良値) を名指しで書く。

## 3. 親の機械照合 (job dir `artifacts/numcheck.py`)

- 2 稿の数値 token 57 件 (要旨 25・結論 32、2 桁以下の整数・年を除く) を、一次資料の本文 (results 稿 20 本・story 2026-09-20b 版・paper-story README・
  figures README・claim-evidence 2026-09-20 稿・4 稿・decisions) に対して桁区切りの有無を両方で逐語存在検査し、**未検出 0**。
- 数値は結果・考察稿の表の逐語 (P2-5 表 1、P2-4 §2、A-2 / A-6 / T-1998 §3、B-7 §4、A-1 表 7・7b、S-1a 表 9・10) と序論・限界稿 (判定器の検出力 1,310 / 3,576、
  検証相 30 verify) から取り、要旨・結論のために新しく計算した値は無い。
- 禁止句の grep (世界初 / 先行なし / 唯一 / 最も近い / 本目 / 新しい CC ができた / LLM でなければ / 無人で / 保証した / 第 2 の成功例) の hit は、
  「書かない」節の列挙と否定文 (結論 §1 の「『LLM でなければ…』という因果的必要性は実証していない」) だけで、肯定的な使用は無い (肯定・否定の別は
  grep でなく手読みで確かめた)。

## 4. 段 6 — 独立 read-only レビューと焦点再レビュー

(段 6 の実施後に記す。実施前の欄は作らない)

## 5. 限界と言わないこと

- 本稿は執筆者向けの草稿であり、投稿本文ではない。英語化は scope 外。字数は投稿先の制限に合わせて執筆者が選ぶ。
- 要旨・結論の主張の強さは story 2026-09-20b 版 §6 と 4 稿を超えない。採用時点より後に着地した事実 (attempt-0002 の記述図、story 2026-09-21 版など) は
  反映していない。次に正典が動いたら、本稿を書き換えず新しい日付の稿で再導出する。
- 文書成果の完了であり、未取得の測定 (A-1 充足・A-5・B-1・B-2・B-4・B-5・B-8 など) や Phase 3 全体の完了を意味しない。
