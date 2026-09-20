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
  変えていない。repo 内の差分は本 dir の 2 file + `verbatim/` + `docs/phase3.md` の [x] 1 項 + worklog fragment だけ。

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
  出現を言い換えた (Polyjuice・FunSearch の「系譜の起点」→「本研究が参照する系譜は … に始まる」、ShinkaEvolve の「最も直接的な比較対象」→「公開実装として
  本研究が比較対象に置くもの」、LaMDAgent の「最も近い参照実装」→「同じ形をとる参照実装」、knob 系譜の「最古参」→「早くから目指してきた」、Kraska の「元祖」→
  「提案」、OpenEvolve の「査読論文は存在しない」→ 確認の方法と日付を併記した内部の不在)。
- **内部の不在の書き方:** 2.3 (SysInsight 1 論文内、母集合 87,303 文字 + 走査語 6 語) と 2.7 (索引 26 エントリ内、走査語 2 組) は母集合と走査語を同じ段落に置き、
  「世界の不在ではない」を併記した。
- **位置づけの 1 文:** story §3 項目 1 の逐語 (太字 3 条件 + 括弧書き) をそのまま引用し、出典節・掃引日 2026-07-10・監査前を同じ段落に置いた (7.7.3 の `RW1`)。

## 4. 段 6 — 独立 read-only レビュー (親が記録前に追記する)

(段 6 実施後に追記)

## 5. 限界と言わないこと

- 本稿は執筆者向けの統制稿であり、投稿本文ではない。英語化は scope 外。
- 文献の判定・限定・成熟度・件数の権威は正典と claim-survey の凍結物にあり、本稿は転記の検算 (逐語存在) までを行った。一次資料 (論文本文) の再読は行っていない。
- 稿が引く arXiv ID の実在確認は正典の各エントリの `id検証:` 欄の日付のものであり、本稿は再確認していない。
- 採用時点より後に着地する事実 (story 2026-09-20b 版、序論稿の land) は反映していない。次に正典 (関連研究 README / claim-survey / 版) が動いたら、
  本稿を書き換えず新しい日付の稿で再導出する (結果稿・方法稿と同じ扱い)。
