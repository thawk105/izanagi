# 本体論文 (日本語) の結果・考察草稿 (2026-09-21 版) — 09-20 の前稿を supersede し、A-1 sized attempt-0002 (認可済み独立再現) の完走と登録済み解析の出力を attempt-0001 と並記した (docs のみ、台帳 ID 未起票の執筆依頼)

authority: none / default_effect: no-state-change (可変状態の正本は worklog 末尾と現行 phase doc)

- 成果物: `results-discussion.md` (本 dir)。**前稿 `output/insights/2026-09-20/paper-results-ja/results-discussion.md` (worklog entry 1750) を
  supersede する。前稿の bytes は変えず (sha256 `a2068a93…` を wave 開始時と記録 commit 時に照合)、前稿 dir の `README.md` の冒頭に前方 pointer の節を足した
  (09-10 → 09-20 の先例は前稿 dir に README が無かったので新規作成、今回は既存 README への追記)。**
- wave: `worktree-dev-wave-paper-abstract-conclusion-ja` (背景 job c9f564c0、job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-abstract-conclusion-ja/`)。
  同じ wave で要旨・結論の草稿 (`output/insights/2026-09-21/paper-abstract-conclusion-ja/`) も起草した。
- 起点 local main: `285477c00` (着手直前の local main、fresh worktree、startup gate rc=0、worklog entry 1770 までの fold を含む)。**採用時点も `285477c00`**。
  実装面 (repo 内) の差分 0 (本 dir の 2 file・前稿 dir の README 1 file・要旨結論 dir の 3 file・`docs/phase3.md` のチェック 1 項・worklog fragment のみ)。
  変異 matrix は `DW-S04` により免除、受入全走は免除しない
- **新規の測定は 0 件。** 凍結物 (results 稿 20 本・版・claim-evidence・figures・前稿本文) の bytes は 1 byte も変えていない
- ユーザー依頼の確定事項 (dev-wave 引数の逐語は job dir の HANDOFF.md): (1) 前稿 §12 と出所節が attempt-0002 を「gate 拒否・測定値なし」と書く箇所を、
  凍結稿 `results/2026-09-20-a1-balanced5-sized-attempt2-descriptive.md` の表の逐語で次版に更新する。09-10 → 09-20 の先例どおり前稿本文は不変で新 dir に置き、
  前稿 dir に前方 pointer を残す。2 attempt はプールせず並記 (D1993 項 6)、充足・formal 化・再現は判定しない。scope 外 = 英訳・新規測定・版・凍結物の変更・
  gate・検査・台帳の追加

---

## 1. 一行で

前稿 (2026-09-20 版、12 節・表 15) の骨格と本文を継承し、前稿の採用時点 (`482f19b88`) より後に main へ着地した事実のうち本稿の記述に触るもの 5 件を
現在地へ揃えた。主対象は A-1 sized attempt-0002 の完走 (entry 1755) で、§5 に attempt-0002 稿 §2.7 の並記表を **表 7b** として逐語で置き、§11 / §12 /
出所 9・26 の「gate 拒否・測定値なし」を「完走・descriptive 出力・充足は未判定」に置き換えた。残り 4 件 (K2 同 job pair の初投入と不成立、fig13、B-8 の
試走認可と発効前試走、K2 原本消失の provenance 注記) は §8.1 / §9.1 / §12 / 出所 15〜18・27 の該当箇所だけを最小限に直した。本文の全面再導出はしていない。

## 2. 段 1 の実測 (親、2026-09-21 00:4x〜01:0x JST、login node、読み取りだけ)

| 項目 | 実測 | 稿での扱い |
|---|---|---|
| attempt-0002 稿 | `results/2026-09-20-a1-balanced5-sized-attempt2-descriptive.md` (527 行)。§0.4 主判定文、§2.1 (statistics 全桁)、§2.3 (arm ごとの記述)、§2.4 (verify_done 6 record)、§2.7 (2 attempt × 3 workload の並記表)、§3 限定 L-A1S2-1〜13 を読了 | §5 本文と表 7b (§2.7 の逐語)、§11、§12、出所 26 |
| 前稿の attempt-0002 言及 | §5 の 1 段落 (gate 拒否・測定値なし)、§11 (read-heavy の列挙)、§12 A-1 項、出所 9 | すべて現在地へ |
| story | 2026-09-21 版は main に無い (並走 wave [7e7657] が起草中、数えない)。最新は `2026-09-20b.md`。§6 の A-1 に関する「投入未・測定値なし」「A-1 の 2 本目が走ったとは書かない」は README stale 注記 5 件目 (attempt-0002 完走) が supersede | 冒頭で 20b + stale 注記 5 件を正本と明記 |
| 採用時点以後に動いた状態語 | (i) attempt-0002 完走 (entry 1755)、(ii) K2 pair 初投入・不成立 (D2187、entry 1754)、(iii) fig13 (entry 1763)、(iv) B-8 試走認可 (D2186) + 発効前試走 (T-2807、entry 1766、D2190)、(v) K2 loop 原本消失 (F1034、T-2815、entry 1764)。[T-1871] 追補 1 (entry 1752) は稿に該当語なし | (i)〜(v) を最小限で反映、(vi) は不変 |
| 並走 wave | ListAgents 9 本。fig9b (attempt-0002 の記述図) [1d8d9b] と story 2026-09-21 版 [7e7657] が同時刻に開始。どちらの成果も数えない (§5「attempt-0002 の図は本稿の採用時点で無い」) | 採用時点 = `285477c00` |

## 3. 親の機械照合 (job dir `artifacts/numcheck.py`)

- 本稿の数値 token 399 件 (2 桁以下の整数・年を除く) を、一次資料の本文 (results 稿 20 本・story 2026-09-20b 版・paper-story README・figures README・
  decisions・worklog と当日 archive entry・関連 insight・凍結 JSON 2 本・S' 最終報告) に対して桁区切りの有無を両方で逐語存在検査した。
  **未検出 6 件は前稿 (334 token) と同じ 6 件で、すべて稿側の表記の違い** (P2-5 表 1 の `3.750` = 集計の `3.75`、S-1a 稿の表は `−37.4` / `−44.6` /
  `+83.5` を `%` 無しの列で持つ、`0.1154` は tally の `0.11538…` の丸め、K2 稿は `+18.7 %` と空白入り)。本版で足した 65 token は全件一致。
- 前稿本文の sha256 `a2068a93eaf29819bf8680c544795862ed8a5f6a8e21f50ae32b6a8715f37851` は wave 開始時に記録し、記録 commit 前に再照合した。
- 差替えは job dir `artifacts/apply_v21.py` (exact 1 回一致、all-or-nothing、15 箇所) で当て、母集合の文 1 箇所 (出所が引く結果稿 17 → 18 本) を追加で直した。

## 4. 前稿との対応

| 前稿の箇所 | 本稿での扱い |
|---|---|
| 冒頭 (版名・supersede・採用時点・正本) | 2026-09-21 版、前稿 (entry 1750) を supersede、採用時点 `285477c00`、story 20b + stale 注記 5 件 |
| §5 見出し・attempt-0002 の段落・言えること | 見出しに attempt-0002 を追加、段落を完走・登録済み解析の出力・`variance_plan_breach` の記録値へ、表 7b (稿 §2.7 の逐語) を新設、並記から書ける事実命題 (a)〜(c)、言えないことに「再現した」「安定している」「L-A1S-4 の解除」「3 本目の認可」を追加 |
| §8.1 「pair の投入は 1 job も行われていない」 | 初投入 `13339.nqsv` と不成立 (候補 10 certified 811,956 tps / stock は claim leaf 拒否)、対照未達は不変 |
| §9.1 「図は無い」 | fig13 (結果図、判定は provenance から、等価性検定ではない) |
| §11 read-heavy の列挙 | attempt-0002 (−560,565.60 tps) を追加 |
| §12 冒頭・A-1・B-8 | 採用時点、A-1 (2 attempt とも descriptive、充足・formal 化・L-A1S-4・3 本目は未判定)、B-8 (試走認可・発効前試走・発効 commit と本走認可は再提示待ち) |
| 出所 8 / 9 / 12 / 15 / 16 / 18 | story 20b、attempt-0002 の完走は出所 26 へ、D 番号 5 件追加、K2 原本消失の provenance 注記、pair 初投入、fig13 |
| 出所 (末尾) | 26 (attempt-0002 稿・公開 leaf・記録・裁定)、27 (B-8 の試走認可と発効前試走) を追加 |
| それ以外の本文・表 1〜15 | 不変 |

## 5. 段 6 — 独立 read-only レビュー (A) と焦点再レビュー (3 巡、DW-O16 の上限)

### 5.1 review-A (read-only、gpt-6-astra / medium、24 call、381 秒、01:10〜01:16 JST、rc=0、`outcome: accepted`)

prompt = job dir `prompt-review-a.md` (2 レンズ = A: 一次資料との照合・帰属・母集合 / B: 主張の強さ・状態語・禁止句・story §6 と stale 注記の整合)。
対象は本版と README 2 本 (要旨・結論は別のレビュー B)。**NO-GO、所見 5 = must-fix 1 / should-fix 1 / nit 1 / refuted 2。表 7b は 78 セル全一致
(両公開 leaf の `result.json` でも statistics を照合)、§5 の値・条件・限定は attempt-0002 稿と一致。** 親の裁定: real 3・採用、refuted 2 は親の
provisional 裁定 (P1)(P2) の維持。

| # | 種別 | 所見 (要旨) | 一次資料 | 親の fix |
|---|---|---|---|---|
| 1 | must-fix | 出所 15 の provenance 注記が再構成対象を取り違え (byte 一致で再構成できるのは round 3 `loop_state.json` と round 2 / 3 `agent_outputs.jsonl`。材料レポートは入力側で残存)、「WAL は内容同一まで」が round 1 にも読める (round 2 = byte 一致の写し、round 3 = 内容同一、round 1 = 値のみ) | `output/insights/2026-09-20/k2-loop-originals-lost-downstream/README.md` §0〜§1、entry 1764 | 巡ごとに範囲を書き分け、材料レポートを対象から外す |
| 2 | should-fix | §8.1 の pair 段落が正しさ (serializable / certified) と性能 (811,956 tps) を 1 文に畳む | `output/insights/2026-09-20/t2795-k2-pair-attempt/README.md` §1 | trace 無効 build の性能と trace 有効 build の検査を別文に |
| 3 | nit | §11 に足した attempt-0002 の値 (−560,565.60 tps) の段落末に出所 26 が無い | — | `[…, 26]` を追加 |
| 4 | refuted | (P1) attempt-0002 以外の状態語 4 件の更新は scope 逸脱か | D2186 / D2187 / D2190、entry 1748〜1770 の見出し | 採用時点 `285477c00` の版として妥当。直し漏れなし (維持) |
| 5 | refuted | (P2) 前稿 README への pointer 追加は前稿不変違反か | `git diff 285477c00 HEAD -- <前稿本文>` = 空、sha256 一致 | 維持 |

fix commit `4034e945c` (`artifacts/fix1.py`、レビュー B の所見と合わせて 4 file +61/−40)。

### 5.2 focus-1 (read-only、12 call、235 秒、01:23〜01:27 JST) と focus-2 (3 call、60 秒、01:30〜01:31 JST)

focus-1 は A / B の所見 14 件を 1 本で判定: **closed 8 / partial 3 (いずれもレビュー B 側) / refuted 妥当 3 / regressed 0**。本版に関わる A-1〜A-3 は closed、A-4 / A-5 は refuted 妥当。
focus-2 は残 3 件 (要旨・結論側) を closed にして **GO**。本版側の 3 巡目の対象は無い。

### 5.3 費用と気づき

- codex 4 本 (review-A 24 call / review-B 19 call / focus-1 12 call / focus-2 3 call、いずれも gpt-6-astra / medium)。
- 数表の転記 (表 7b 78 セル) は機械照合で守れたが、**親が要約した provenance の注記 (再構成できる file の種類と巡の範囲) は要約で範囲が広がった**。
  再構成・残存・欠落の型を持つ注記は、一次資料の表を file × 巡で写してから縮める。

## 6. 限界と言わないこと

- 本稿は執筆者向けの統制稿であり、投稿本文ではない。英語化は scope 外。
- 数値の権威は各 results 稿とその権威 bytes にあり、本稿は転記の検算 (逐語存在) までを行った。権威 bytes からの独立再計算は行っていない。
- attempt-0002 の反映は「並記」であり、2 attempt の差・比・区間の重なり・再現判定・A-1 の充足・formal 化・3 本目の認可のいずれも判定しない。
- 採用時点より後に着地した事実 (story 2026-09-21 版など) は反映していない。次に正典が動いたら、本稿を書き換えず新しい日付の稿で再導出する
  (前稿と同じ扱い)。
- **採用時点より後、本 wave の記録 commit の直後 (01:36 JST) に main `2afb39768` へ着地した第 27 回 /rulings (D2194、2026-09-21) のうち本稿の記述に触るもの
  (本稿は書き換えない。執筆時点では真で、後続で古くなった型):** 項 1 = B-8 事前登録 v1 を案 A の発効束で発効し、校正と本走の投入を認可 (本稿 §12 の B-8 項
  「発効 commit と本走の認可はユーザーへの再提示待ち」は採用時点の記述。発効 commit・校正・本走の実施は承認後の AI 手番で、着地時点では未実施)。
  項 6 = 次の論文ストーリー版と claim-evidence で 2 attempt の並記を「同一配置の反復で分類と符号が一致した観察」として書き、L-A1S-4 を 2 attempt の観察に基づく限定へ
  書き換え、attempt-0002 の図は作らない (本稿 §5 の (a)〜(c) と「L-A1S-4 の解除可否は判定しない」はこの裁定と整合し、「図は本稿の採用時点で無い」は据え置き)。
  項 2 = K2 4 巡目の入力元は round 3 の派生物から組む (投入は pair 修復後の再提示、本稿 §8.1 の記述は不変)。項 7 = paper-story README の results 表の
  fig13 行を追補 (本稿 §9.1 は既に fig13 を引く)。
