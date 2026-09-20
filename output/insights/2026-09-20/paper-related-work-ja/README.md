# 本体論文 (日本語) の関連研究節の新規起草 — 正典 `docs/related-work/` と `claim-survey/` の範囲だけで書き、軸 1 = `RW1`・軸 3 = `RW0` の成熟度を本文の限定にした (docs のみ、台帳 ID 未起票の新規執筆依頼)

authority: none / default_effect: no-state-change (可変状態の正本は worklog 末尾と現行 phase doc)

- 成果物: `related-work.md` (本 dir、8 小節 + 出所 22 件)。序論稿 (別 wave `dev-wave-paper-intro-ja`、稿の構成節が「第 2 節で関連研究」と書く) の後ろに置く第 2 節の統制稿。
- 依頼: ユーザー (2026-09-20、dev-wave 引数、台帳 ID 未起票)。逐語は `verbatim/s1-brief.md` の冒頭。
- wave: `dev-wave-paper-related-work-ja` (branch `worktree-dev-wave-paper-related-work-ja`)。着手直前の local main `7baf3f375` (= origin/main) から fresh worktree、
  開始 gate `check_wave_startup.py --mode fresh --external-handoff` rc=0 (20:53 JST)。job dir = `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-related-work-ja/`、
  専用 handoff は背景 job の tmp (`/home/SFC/tanab/.claude/jobs/bf514bea/tmp/handoff-paper-related-work-ja.md`)。
- 構成: docs-only 軽量版 (`DW-C00`)。段 2・3 省略、書き手は親、段 6 に read-only codex レビュー 1 本 + 焦点再レビュー (一次資料から事実を再抽出する
  docs-only wave の規則、D2148 項 11)。実装差分ゼロなので変異 matrix は免除 (`DW-S04`)、受入全走は免除しない。
- **新規の文献取得は 0 件、Web は使っていない。** 正典 (`docs/related-work/README.md`、`claim-survey/` の凍結物)、版 (`docs/paper-story/`)、decisions の bytes は 1 byte も
  変えていない。初稿 commit (`19dda064f`) 時点の repo 内の差分は本 dir の 3 file (稿・README・`verbatim/s1-brief.md`) だけで、段 7 で `docs/phase3.md` の [x] 1 項と
  worklog fragment を足す。

---

## 0. この wave が主張すること・しないこと

- **主張する:** 関連研究節の統制稿が 1 本あり、その本文の判定 (強さ・極性)・限定・成熟度・件数は正典の凍結物からの転記で、新しい判定を 1 つも下していない。
- **主張しない:** 先行研究の不在 (世界の不在)、優先権、系譜の序数。調査の完了。稿が投稿本文であること (執筆者向けの統制稿である)。
  依頼文の「差別化の核 (説明可能性、軸 3)」は D1598 の 3 点 (対象がトランザクション CC・action vocabulary の拡張・正しさゲートを毎反復) で書き、
  「説明可能性が核」という短縮形は稿に置いていない (story 2026-09-20 版 §1 の規定)。

## 1. 段 1 brief (親、20:57 JST。逐語は `verbatim/s1-brief.md` = handoff の段 1 節)

- 研究前進 = 論文本文の第 2 節の統制稿。完了判定 = 正典の限定・成熟度を 1 つも落とさない散文が独立 read-only レビューで must-fix 0 になること。
- scope = 本 dir の 2 file、`docs/phase3.md` の [x] 1 項、worklog fragment。正典は不変。英訳・要旨・結論・新規実験・新規文献取得は scope 外。
- 確定裁定 = D1598 / D1760 / D1931 / DCDS 裁定の限定 3 つ / CIR+CVN の限定 / SysInsight 裁定 §2.7 の 3 限定と核にできない 3 語 / 7.7.2〜7.7.3 の表現規律 / D2148 項 11。
- (P1) `docs/paper-story/README.md` の「表 1 行」: 同 README の表は版の履歴・claim-evidence 系列・results 系列の 3 つで、いずれも凍結物系列の一覧。草稿を載せる表は無く、
  先例 3 wave (results-ja 09-10 / 09-20、methods-ja 09-20、intro-ja) も README に行を足していない。→ README 行は足さず `docs/phase3.md` の [x] 1 項だけで登録する。
  新しい表の新設は hot file への構造変更で、稼働中の story 2026-09-20b wave の README 編集と衝突するうえ「表 1 行」の意味を超える。段 6 の攻撃対象。
- (P2) phase3 [x] の位置 = 現行チェックポイントの先頭 (results-ja 09-20 の先例)。intro wave は [T-2340] 項直後 → anchor が違う。衝突したら両行保持で解く。

## 2. 稿の作り方

| 項目 | 実測 | 稿での扱い |
|---|---|---|
| 正典 README | 全文 790 行 (7.0 索引 28 エントリ、7.1〜7.5 の全エントリ、7.6、7.7.1〜7.7.8) を読了 | 各エントリの一言・採る / 採らない・系譜上の位置を、判定タグと接地の限定を保って散文化 |
| claim-survey | README の一覧 (33 file の 1 行要約)、inventory (08-26) §0〜§2・§4〜§7、CIR+CVN 裁定 §0〜§1、軸 1 裁定 3 (08-27) §0・§1・§6、軸 1 実行記録 (08-27) §0〜§2・§8・§9、(08-30) §0・§3・§4、(09-19) 全文、SysInsight 裁定 (09-03) 全文 | 2.1 / 2.3 / 2.6 / 2.7 / 2.8 の判定・限定・件数の出所 |
| story 2026-09-20 版 | §1 (核 3 点、3 限定、SysInsight、調査の状態)、§3 (軸 1〜5 の実証状態)、§8 C-4 | 2.1 の 1 文 (逐語) と禁止形、2.8 の状態語 |
| decisions | D1598 / D1760 / D1931 の本文 | 核の書き方、停止の理由と「取り消さないもの」 |
| 稼働中 wave の版 `2026-09-20b.md` (未 land) | §1 は 2026-09-20 版 §1 と版名の時点語だけが違う (job dir `s1-20.txt` / `s1-20b.txt` の diff で実測) | 依頼どおり 2026-09-20 版 §1 に揃えた。20b の着地は稿の内容を変えない |
| 隣接 wave | intro 稿 (未 land) は「個々の先行との比較は関連研究の節に委ねる」「第 2 節で関連研究」と書く | 本稿はその第 2 節。intro 稿は出所にしない (未 land) |

本文の書き方: 平易な日本語の論文本文 (投稿本文の文体)、本文に T 番号を書かず、D 番号と一次資料 path は末尾「出所 (執筆者向け)」へ寄せる
(先例 = `output/insights/2026-09-20/paper-intro-ja` / `paper-methods-ja` / `paper-results-ja` の稿)。

## 3. 親の自己点検 (段 5)

- **arXiv ID の集合比較:** 稿の `NNNN.NNNNN` 形 32 件はすべて正典 README に存在 (job dir `numcheck.py`)。
- **数値 token の逐語存在:** 3 桁以上の整数・小数・比・区間 36 件 (年月日・2 桁以下・D / T 番号を除く) を正典 README・claim-survey 全 file・story 2026-09-20 版・
  decisions の本文に対して桁区切りの有無を両方で検査し、未検出 0。初稿の未検出 2 件 (`1358–1371` の en dash、`171/173` の合成表記) は一次資料の表記へ直した。
- **禁止句・序数表現の走査:** 「世界初 / 先行なし / 唯一 / 最も近い / 何本目 / 最古参 / 元祖 / 起点 / 存在しない / 前版 / この版」を grep し、禁止の言明と出所以外の
  出現を言い換えた (初稿の段階では Polyjuice・FunSearch の「系譜の起点」→「… に始まる」、ShinkaEvolve の「最も直接的な比較対象」→「公開実装として本研究が
  比較対象に置くもの」、LaMDAgent の「最も近い参照実装」→「同じ形をとる参照実装」、knob 系譜の「最古参」→「早くから目指してきた」、Kraska の「元祖」→「提案」、
  OpenEvolve の「査読論文は存在しない」→ 確認の方法と日付を併記)。**このうち「… に始まる」と OpenEvolve の言い換えは、段 6 レビューが「歴史上の始点の主張が残る」
  「走査語と列挙可能な母集合を持たない不在」として must-fix にし、fix で「本節では … を方法論的な参照点として取り上げる」「独立した査読論文の有無は本節では
  判定しない」へ直した (§4)。** grep だけでは序数・不在の含意を消せない。
- **内部の不在の書き方:** 2.3 (SysInsight 1 論文内、母集合 87,303 文字 + 走査語 6 語) と 2.7 (索引 26 エントリ内、走査語 2 組) は母集合と走査語を同じ段落に置き、
  「世界の不在ではない」を併記した。
- **位置づけの 1 文:** story §3 項目 1 の 1 文を、語句・太字・括弧書きを保って引用した (改行位置のみ調整。可視文字は一致するが改行・空白配置は原文と異なる)。
  出典節・掃引日 2026-07-10・監査前を同じ段落に置いた (7.7.3 の `RW1`)。

## 4. 段 6 — 独立 read-only レビュー 1 本と焦点再レビュー

### 4.1 review-1 (read-only、gpt-6-astra / medium、20 call、446 秒、21:14〜21:21 JST、rc=0、`outcome: accepted`、対象 = 初稿 commit `19dda064f`)

prompt = job dir `prompt-review.md` (2 レンズ = A: 一次資料との照合 — 判定・限定・成熟度・母集合・件数 / B: 論文散文としての主張の強さ・禁止句・story §1 整合・scope)。
**NO-GO、所見 12 = must-fix 5 / should-fix 4 / nit 2 / refuted 1。書誌・数値・SysInsight の 3 限定の転記は一致で、所見は「圧縮時の条件脱落と総括文の過大化」に集中。**
親の裁定: 所見 1〜11 は real・採用 (nit 2 件は部分採用)、所見 12 は (P1)(P2) への攻撃がレビュー自身により退けられたもので、親の裁定を維持。

| # | 種別 | 所見 (要旨) | 一次資料 | 親の fix |
|---|---|---|---|---|
| 1 | must-fix | 2.5「この系譜には起点から存在しない」は系譜全体への無限定の不在、2.2 / 2.5 の「… に始まる」は歴史上の始点の主張 | README 7.2、7.7.2〜7.7.3 | 4 研究の evaluator / validate の特徴づけと本研究の設計の対比へ書き換え、系譜の導入を「本節では … を方法論的な参照点として取り上げる」へ |
| 2 | must-fix | OpenEvolve の「査読論文は … 見つかっておらず」は走査語・列挙可能な母集合を持たない不在。2.3「先行に評価されていない」は SysInsight 1 論文から先行一般への拡張 | README 7.2、SysInsight 裁定 §4.1〜§4.2、D1598 | OpenEvolve は「正典が一次資料として挙げるリポジトリと作者のブログを参照する (査読論文の有無は判定しない)」へ。2.3 は「SysInsight が評価していない」に限定し、軸 3 `RW0` で先行一般は語れないと併記 |
| 3 | must-fix | Self-Harness の採用条件から「かつ少なくとも一方で改善」が落ちた | README 7.4 | 復元 |
| 4 | must-fix | ARA の採用済み / 将来雛形 / 反面教師の区別が揃わず、2.7 冒頭「機構は後続段に予約する」が採用済みの入力側隔離と衝突 | README 7.4 | 2.7 冒頭を「思想・外部補強 / 採用済み (ARA の入力側隔離 1 件) / 将来の予約」の区別へ、ARA 段落を 3 区分で書き直し (データ構造の対応は証拠鎖の実証を意味しない、Compiler / Live Research Manager は採らない) |
| 5 | must-fix | 軸 1 の件数は正しいが、同じ場所に置くべき限定 (53 leaf は 1 走の返却集合で完全とみなせない、2025・2026 年分 4 leaf は材料に無い、catalog 2026-09-02 の 6 枝、数えない 16 の内訳、未実装は検査器の 5 層) が落ちた | 2026-09-19 記録 §2〜§5、2026-09-18 記録 §3・§4 | 2.8 の同段落へ全部追加、出所 21 に内訳と出典を追記 |
| 6 | should-fix | 2.5 で EVOLVE-BLOCK の採用と「機構は非採用」が同じ稿で矛盾 | README 7.2 | 「採用するもの / 思想として参照するもの / 採らないもの」に分けて書き直し |
| 7 | should-fix | 圧縮で落ちた接地の極性・不採用条件 7 件 (DCDS の DSL 経路、軸 3 の基本極性「方法論的祖先」、SysInsight の履歴データから target workload を除外、Best-of-∞ は S-1 に適用しない・throughput へ直用しない、Vesper の worktree は物理干渉を防がない、Self-Developing は違反を選好対に入れない、LaMDAgent の 100 iteration 改善が leading indicators 前提と緊張) | README 各エントリ、SysInsight 裁定 §3.4・§4.1 | 7 件とも該当段落へ追記 |
| 8 | should-fix | DCDS の違い 3 つを 2.1 の 3 条件と一対一対応させた (トランザクション CC は共通点であり相違ではない) | 軸 1 裁定 3 §6.1〜§6.2、story §1 | 「対象を共有し、相違は合成主体・空間拡張・反復ごとの正しさ検査」へ書き直し、一対一ではないと明記 |
| 9 | should-fix | 2.8 の成熟度の一般説明が `RW2` の許容表現 (索引名・検索式 ID・cutoff 付きの限定付き未検出) を落とし、実際より厳しい規則にした | README 7.7.3 | 段階ごとの許容表現を正典どおりに書き直し |
| 10 | nit | 投稿用散文に運用語 (digest 射影、tier、層 2、leaf、epoch、pass 1、seal) が混在、2.8 は実行記録に近い、核と未実証の限定の反復 | brief の成果物の形 | 部分採用: digest 射影 / tier / 層 2 / hooks / Tier0 / seal・catalog を言い換え、leaf と pass 1 は 2.8 冒頭で定義して残す (所見 5 の限定は件数と同じ場所に要る)。反復は残した (各節が単独で読まれても限定が落ちないため) |
| 11 | nit | README の差分範囲 (初稿時点は 3 file だけ) と「逐語」の記録 (改行位置が原文と異なる) を正確に | Git 実測、story §3 項目 1 | README 冒頭と §3 を訂正 |
| 12 | refuted | (P1)(P2) を理由に正典へ導線を足すべきという疑義 — README の 3 表に草稿の行種別は無く、results / methods の先例も README を変えていない、phase3 先頭に results-ja の項が実在 | paper-story README、先例 README 2 本、phase3 | (P1)(P2) を維持。intro の先例はレビュー時点で未確認 (稼働中木) だったが、その後 main `799d38b97` に着地した同稿の README も paper-story README を変えていない (§4.3 で親が確認) |

review-1 が一致を確認した範囲 (消極的証拠): 索引 28 エントリの独立計数、2.1〜2.8 の書誌・判定・限定・件数 (詳細は job dir `review-out.md`「照合して一致を確認した範囲」)。
fix commit は §4.2 の焦点再レビューの前に作る。加えて親が自己点検で 1 箇所直した — 2.2「CCBench の中心主張が本研究の対照の取り方を決めている」は正典より強い
因果の言い方だったので「本研究が事前登録した対照も CCBench 内の LLM を使わない対照で閉じている」へ。

### 4.2 focus-1 (焦点再レビュー)

(実施後に追記)

### 4.3 main の前進の取り込み

(実施後に追記)

## 5. 限界と言わないこと

- 本稿は執筆者向けの統制稿であり、投稿本文ではない。英語化は scope 外。
- 文献の判定・限定・成熟度・件数の権威は正典と claim-survey の凍結物にあり、本稿は転記の検算 (逐語存在) までを行った。一次資料 (論文本文) の再読は行っていない。
- 稿が引く arXiv ID の実在確認は正典の各エントリの `id検証:` 欄の日付のものであり、本稿は再確認していない。
- 採用時点より後に着地する事実 (story 2026-09-20b 版、序論稿の land) は反映していない。次に正典 (関連研究 README / claim-survey / 版) が動いたら、
  本稿を書き換えず新しい日付の稿で再導出する (結果稿・方法稿と同じ扱い)。
