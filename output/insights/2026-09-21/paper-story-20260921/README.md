# 論文ストーリー 2026-09-21 版 (`2026-09-21.md`) の全項目再導出 — wave 記録

`docs/paper-story/2026-09-21.md` を、2026-09-21 00:21 JST 時点の正典全体から全項目再導出して追加した wave の
記録である。**新規計測はしていない。** 既存の版 11 本・`results/` 20 稿・`figures/`・`claim-evidence/`・
`docs/paper-story-backoff/` は 1 byte も変えていない。

- wave: `dev-wave-paper-story-20260921`、branch `worktree-dev-wave-paper-story-20260921`、背景 job 50774bad
- 起点: local main `285477c0052819e272e390d798f6442658075866` (2026-09-21 00:21 JST、worklog entry 1770 までの fold を含む)。
  **導出の起点は `285477c00`。** 段 7 で local main `b880449bb` (entry 1772 まで) を ff-only で取り込んでから README を更新した。
- 成果物: `docs/paper-story/2026-09-21.md` (新規、5,266 行、約 736 KB) と `docs/paper-story/README.md` の更新
  (版の履歴表へ 1 行、「最新 = `2026-09-21.md`」、訂正一覧を「0 件」へ、stale 注記 5 件を本文へ移管し、起点より後に着地した 2 件
  (第 27 回 /rulings D2194 = entry 1771、日本語結果・考察稿 2026-09-21 版 + 要旨・結論草稿 = entry 1772) を積み、results 系列に
  B-10 待ち方 grid 稿の「図は無い」への fig13 追補段落を足した (D2194 項 7、[T-2816] の後半))。実装面ゼロ。
- 依頼: 逐語は `verbatim/brief-s1.md` 冒頭。要旨 — 「前版 2026-09-20b と README の stale 注記 5 件 (pin 前進 `e9e477ca` [T-2304]、
  [T-1871] 追補 1、第 26 回 D2186 の B-8 試走認可、[T-2795] K2 pair 不成立、[T-2792] A-1 attempt-0002 完走) に加え、版以後の着地
  ([T-2807] B-8 試走完了と発効束、[T-2153] witness 23、[T-2766] pairing 既定 on、[T-2803] / [T-2804]、[T-2344] 63 → 85、F1034 の K2 原本消失)
  を本文へ取り込み、§8 A 群 (A-1 但し書き 1) の現在地を更新する。数値は各 results 稿の表の逐語を numcheck で照合し、状態語は D 台帳で
  現在地へ揃える。稼働中 [T-2797] の未着地結果は取り込まない。前版・稿・図・凍結物は不変、新規測定なし、A-1 の充足・formal 化・再現は
  判定しない (D1993 項 6、D2172 項 2)。稿の再導出だけ。gate・検査・台帳・一般化の追加は scope 外」。

## 1. 段 1 — brief と provisional 裁定

`verbatim/brief-s1.md`。反映集合を A (README stale 5 件)、B (版以後の着地で状態語を動かすもの)、C (運用素材と訂正だけのもの) に分け、
P1〜P7 を provisional 裁定として置いた。要点:

- **P1 (資料の締切):** 起点 `285477c00` に固定。稼働中の wave (B-5 β 試走 [T-2797]、fig9b、日本語結果稿の attempt-0002 反映、[T-2810]、
  第 27 回 /rulings) の完了を待たず、着地後の項目は README の stale 注記が持つ。
- **P2 (前版の執筆時点の誤り):** brief 前の照合で 0 件。stale 5 件はいずれも前版起点 `fec4a8187` (2026-09-20 18:01 JST) より後の着地
  (entry 1747 / 1751 / 1752 / 1754 / 1755) で「当時は真で後続が古くした」型。
- **P3 (pin 前進の書き方):** 「pin は前進した (基準 HEAD の gitlink は `e9e477ca`)」と書き、「mocc の certified 系列が開いた」「探索が
  解禁された」「旧系列を新 main から再開できる」とは書かない。D2083 項 5 の「hook」= R/W trace hook (pin に入った) と [T-2294] の X/P
  計装 (patch `instr-mocc-lock-coverage.patch` のまま) を分ける — pin の `transaction.cc` に R/W hook はあり `emit_lock_violation` は patch
  側にだけある (親の grep)。
- **P4 (A-1 attempt-0002):** 「完走し 3 workload とも `resolved-above-floor`、符号は 2 attempt とも + / + / −、`variance_plan_breach` は
  write-heavy / read-heavy で true」と書き、「A-1 の値がある」「再現した」「安定した」「3 本目を投入できる」とは書かない。2 attempt から
  何も計算しない。
- **P5 (K2 pair):** 「pair は投入されたが不成立」「候補 10 の再評価 (certified、811,956 tps) は昇格させない」「修復方向は別 wave、再投入と
  4 巡目は D2172 項 3 の予算の再提示」。同日の原本消失 (F1034、[T-2815]) は provenance の事実として同じ節へ。
- **P6 (B-8):** D2186 項 1 の段階認可 → [T-2807] の試走 6 本完走と発効束 (案 A identity `b0f95b21…` / `a0219ce0…`、runner v5 `4ff6652a…`)
  → 発効 commit + 本走認可の 1 行再提示 (D2190) までを書き、「B-8 を取得した」「発効した」とは書かない。
- **P7 (段構成):** 軽量版 (段 2・3 省略、実装面ゼロ)。段 6 は D2148 項 11 の read-only レビュー 1 本 + 焦点再レビュー。変異 matrix は
  `DW-S04` により免除、受入は免除しない。

## 2. 依頼が挙げた事実と状態語を動かす裁定の一次資料と実測値

| 事実 | 一次資料 | 版で確かめたこと |
|---|---|---|
| ccbench pin 前進 `e9e477ca` ([T-2304]、D2184、entry 1747) | `output/insights/2026-09-20/t2304-pin-advance/README.md`、`external/ccbench` gitlink | 起点 HEAD の gitlink `e9e477ca1b55348ab4530de0b1cf663ce4555290`、`pin.CURRENT_PIN="e9e477c"`、admission policy epoch `949ddcc2…` → `db6bc9ea…`、旧系列は固定 checkout ([T-2812]) |
| [T-1871] 追補 1 (entry 1752) | `output/insights/2026-09-20/t1871-nonenum-addendum/README.md` §0 | 5 本 (s1 2 + s8b 3) に source hash が記録されている確認と、直接 verifier `s1_known_axes_freeze.verify()` 1 経路の変異実測 (全 8b 経路ではない) |
| 第 26 回 D2186 (entry 1751) | `docs/decisions.md` D2186 項 1・2・7 | B-8 の対象 = 案 A・定義・試走の段階認可、verifier 改修の帰結 3 点は据え置き、上流報告は人間手番 |
| K2 pair 不成立 ([T-2795]、D2187、entry 1754) | `output/insights/2026-09-20/t2795-k2-pair-attempt/README.md` §0〜§1 | job・campaign・候補 10 の 811,956 (反復 817,565 / 806,347)、stock の one-shot claim 停止、修復方向 |
| A-1 attempt-0002 ([T-2792]、entry 1755) | `output/insights/2026-09-20/t2792-a1-sized-attempt2/README.md` §3、`results/2026-09-20-a1-balanced5-sized-attempt2-descriptive.md` §2.1 / §2.7 | 18 数値・3 分類・breach・比・限定 13 件・3 命題を `numcheck.py` で逐語照合。job と終端時刻の対応 = balanced `13221` 18:22:12 → read-heavy `13222` 18:25:34 → write-heavy `13220` 18:28:57 |
| B-8 試走完了と発効束 ([T-2807]、D2190、entry 1766) | `output/insights/2026-09-20/t2807-b8-prerun/README.md` §5 / §7 | runner v5 sha、identity 全桁、6 試走、timeout の出所 (校正 3600 = §11 / 本走 1800 = §12・D2186 項 1 (5) / 再検証 3600 = D2160 継承) |
| witness 23 ([T-2153]) / pairing 既定 on ([T-2766]、D2188) / [T-2803] / [T-2804] / [T-2344] 63 → 85 (D2193) | 各 insight と D2188 / D2189 / D2191 / D2193 | pairing の A/B = 採用前 / 採用後で全対の main が動いた (同一 SHA は prewarm の E/L 7 対)、対差 145.8 / 86.3 / 57.3 秒、対率 29.1 / 19.6 / 12.6 % |
| K2 原本消失 (F1034、[T-2815]、entry 1759) | `output/insights/2026-09-20/k2-loop-originals-lost-downstream/README.md`、`docs/failures.md` F1034 | 消失した原本と派生物から byte 一致で再構成できるものの対応表、[T-2815] との区別 |

## 3. 版の作り方

前版 `2026-09-20b.md` を複製し、**最初に時点語の機械置換** (`前版` → `2026-09-20 版`、`この版` → `前版` 等、job dir の `r0_epoch.py` /
`r1_space.py`) を当ててから、冒頭・§0・§2 (g)・§10 を全面差替え (`splice.py`)、他節は exact 1 回一致・all-or-nothing の置換 script
(`r2_sec7.py`〜`r8_sec9b.py`) で再導出した。§7 は前版の後半 13 項を前半末尾へ移し (100 項) この版で 9 項を足した (計 109 項)。§0 は 13 点、
§2 (g) は 14 点、§2 (d) は 6 例、§2 (e) の運用素材は 8 つ。数値は `numcheck.py` (hash prefix 71 件を figures / results / leaf / policy の
sha256 と git rev-list の集合と照合、D 247 / T 95 / F 22 の見出し実在、path 218 件の実在) で照合した。集合に無い hash prefix 3 件
(`41f52341` / `c37fda1f` / `f6dca3b9`) は `s3_mocc_template_proof.json` と K2 round 2 / 3 の `layer3_report.json` の sha256 として個別に
現物照合した。不在 path 7 件は placeholder 表記 (`<env_tag>` 等)・前版から継承する旧 insight の相対断片・本 wave 自身の insight dir。

## 4. 段 6 — read-only レビュー 1 本と焦点再レビュー 1 本

- **レビュー 1 (Codex `gpt-6-astra` / medium、read-only、01:54〜02:01 JST、24 model call、wall 417 秒): NO-GO、所見 7 件 (must-fix 6・
  should-fix 1)。親が一次資料で検算して real 7 / refuted 0。** 逐語は `verbatim/prompt-review.md` と `verbatim/review-out.md`。
  1. 「新しい測定は A-1 の 1 件だけ」が §9 の分類 (候補 10 の再評価 = 第 4・5 種) と矛盾 → 「測定記録は 2 件、新しい単独 results 稿は 1 本」へ
     8 か所。
  2. pairing を「同一 SHA の隣接対」と書いた → 採用前 / 採用後の隣接 3 対で全対の main が動いた、同一 SHA は prewarm の E/L 7 対、へ 3 か所。
  3. job と終端時刻の対応が入れ替わっていた (entry 1755 の略記を写した転記誤り) → 一次資料 §3 の順へ。
  4. 序論稿の未反映を着地順で説明していた (序論は entry 1757 > 1755) → 採用時点 `482f19b88` の締切による、へ。
  5. timeout 3 値を「事前登録自身の数」と一括した → 校正 3600 = §11 / 本走 1800 = §12・D2186 項 1 (5) / 再検証 3600 = D2160 継承、へ 3 か所。
  6. 版名の無い「冒頭の訂正 1」と §6 導入の機械置換の残り → 非列挙は前版 (2026-09-20b 版)、仮説層は 2026-09-20 版、§6 は「前版
     (2026-09-20b 版) から引き写していない」へ。
  7. [T-1871] の実測範囲を凍結成果物 5 本へ広げて読める → 5 本への記録確認と直接 verifier 1 経路の変異実測を分けて書く。

  fix は job dir の `r9_fix1.py` (置換 20 件 + README 1 件、exact 1 回一致・all-or-nothing) と `verbatim/fix-extra.md` の 3 件。
- **焦点再レビュー (同 model、02:06〜02:10 JST、17 model call、wall 261 秒): GO、closed 6 / partial 1 / regressed 0、新規所見なし。**
  逐語は `verbatim/prompt-focus.md` と `verbatim/focus-out.md`。派生値 (fix 24 対の新文 1 回・旧文 0 回、§0 の 13 項・§2 (g) の 14 項、
  pairing の対差と対率、候補 10 の median、[T-1871] の 5 本 = s1 2 + s8b 3) を原データから独立に数え直して一致。partial 1 = 所見 7 の
  残り 1 か所 (§5 の [T-1871] 素材)。親が対案どおり直し、同型の文が §2 (e) 6 と §3 項目 5 にも残っていたので同時に直した (3 か所、
  grep で同型 0 件)。**3 巡目は起動していない** (DW-O16 の上限内)。
- レビュー出力 2 file は行末空白だけの可逆正規化 (`verbatim/verbatim-normalization.json`。原文 sha256 は job dir の receipt と一致)。

## 5. 検査

- `python3 tools/check_docs.py` 違反なし (段 5 後・fix 後・§10 完了形後・README 更新後・main 取り込み後)。`git diff --check` 0。
- `numcheck.py`: hash prefix 71 (集合一致 68 + 個別現物照合 3)、D 247 / T 95 / F 22 実在、attempt-0002 統計 6 key × 3 workload の逐語一致
  (`mean_signed_positional_difference_tps` / `descriptive_half_width_tps` / `floor_boundary_tps` / `baseline_mean_tps` /
  `sample_sd_positional_difference_tps` / `planned_sigma_tps`、小数 2 桁)。
- 開始 gate `check_wave_startup.py --mode fresh` rc=0 (`verbatim/startup-gate.log`)。編集面重複検査: 起点で hit 0、受入前 (main `b880449bb`
  取り込み後、32 worktree、unreadable 0) で README を触る他 wave 0、`docs/phase3.md` は [T-2810] wave の tip だけ (本 wave は phase3.md を
  触らない)。
- 起点より後に着地した第 27 回 /rulings (D2194、entry 1771) は本文の起点を動かさず README の stale 注記に積んだ。その項 6 (次の story 版で
  L-A1S-4 を「2 attempt の観察に基づく限定」へ書き換える) は本版が起点で見ていないので**本版では実施していない** — 次版の依頼文が運ぶ。項 7
  (fig13 行の追補) は本 wave が README で実施した。
- 受入全走 (記録 commit の tip、`dev_wave_wait.py acceptance`) と land の結果は本 README に書かず、受領証 (job dir) と land の記録が持つ。
  child-green でなければ land しない。

## 6. 工数

codex 子 2 本 (review 1、focus 1、いずれも gpt-6-astra / medium、read-only)。author / fix 子は 0 (実装面ゼロ)。親: 前版全 10 節 (4,578 行)、
worklog entry 1747〜1770 の見出しと 14 件の本文、D2184〜D2193、insight 13 本、稿 1 本の表、figures README の fig13 節、path 218 件、
hash 71 件。

## 7. 言わないこと

- 本 wave は版と README を書いただけである。測定・判定・裁定・gate・台帳の追加は行っていない。
- 段 6 の 2 レビューが「一致を確認した」と列挙した範囲は消極的な証拠であり、前版全体の「誤り 0 件」の証明ではない。レビューが未完と
  自ら書いた範囲 (全行の完全照合、§5〜§8 の意味単位の脱落、全 hash の現物再計算、全禁止表現の文脈判定) は検証済みとは扱わない。
- README の stale 注記に積んだ 2 件は「着地した」事実だけで、B-8 の発効 commit・校正・本走・判定が完了したことも、日本語草稿が投稿本文で
  あることも意味しない。
