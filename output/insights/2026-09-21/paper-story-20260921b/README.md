# 論文ストーリー 2026-09-21b 版と claim-evidence 2026-09-21 稿の再導出 (D2194 項 6・7)

**wave:** `worktree-paper-story-2026-09-21b` (背景 job 0adb58a3)。起点 local main `5efd69367b641b9bfbd6fb426478f66ae5762783`
(2026-09-21 05:25 JST、worklog entry 1779 までの fold)。開始 gate rc=0 (08:23 JST、`startup-gate.log`)。

## 0. この wave が主張すること・しないこと

**主張する。**

1. **第 27 回 /rulings D2194 項 6 を実施した** — A-1 balanced5 sized 本走の 2 attempt を「同一配置の反復で分類と符号が一致した観察」として
   新版 §8 A-1 に表で並記し、claim-evidence の C21 / L54 に同じ書き方を置き、attempt-0001 稿の限定 L-A1S-4 を「2 attempt の観察に基づく
   限定」として読む形へ改めた。**凍結稿 (attempt-0001 稿・attempt-0002 稿) の bytes は変えていない。解除ではない。**
2. **依頼 (2) (D2194 項 7 の fig13 行の追補と [T-2816] の stale 注記) は、着手時の段 1 で「前版の wave が吸収済み」と判定し、二重に
   実施しなかった。** 判定の根拠は README の results 系列に実在する追補段落、前版本文の F1034 の取り込み、entry 1773 の記録、
   [T-2816] が次の一手から消えていること。
3. **版と claim-evidence を起点の正典全体から再導出した** — 版は前版 `2026-09-21.md` (entry 1770 起点) から entry 1771〜1779 と
   D2194〜D2199 と F1036 を反映し、claim-evidence は前稿 (2026-09-19 版起点) から 2 世代分の着地を反映した。
4. **機械置換で保護した現在形の語が起点で偽になる箇所を 3 件見つけて直した** (§2 (b) と §8 B-5 の「B-5 は基準 HEAD では動いていない」、
   §8 A-4 の「[T-2810] は基準 HEAD では未着地である」)。いずれも前版の執筆時点では真で、後続の着地が古くした型である。

**主張しない。**

- 新規計測・新しい主張は無い。A-1 の充足・formal 化・非認証 lane・L-A1S-4 の解除には触れていない。
- 2 attempt から何も計算していない (プールした推定量・差・比・合成区間・区間の重なりの判定・再現判定・図を作らない)。
- B-5 の試走は主標本外 (n = 1 系列 / arm) で優劣を言わない。B-8 は承認であって取得ではない。g1 の validator の整合は P3 の受理ではない。
- gate・検査・台帳の追加、図の作成、英語稿、2 本目論文の版は行っていない。

## 1. 置いたもの

| path | 内容 |
|---|---|
| `docs/paper-story/2026-09-21b.md` | 版 (同日第 2 版、5,493 行)。§0〜§10 を起点の正典から再導出 |
| `docs/paper-story/claim-evidence/2026-09-21.md` | claim-evidence 新稿 (767 行)。行 C1〜C43、限定 L01〜L64 |
| `docs/paper-story/README.md` | 版の履歴 1 行、「最新 =」、訂正一覧、stale 注記 2 件の移管と 0 件化、claim-evidence 表 1 行 |
| `docs/spool/worklog/2026-09-21-paper-story-2026-09-21b-1.md` | worklog fragment (decisions / failures fragment は無し) |

## 2. 段 1 brief と親の provisional 裁定

brief の全文は `verbatim/brief-s1.md`。provisional 裁定は (P1) 版名と機械置換、(P2) 前版の執筆時点の誤りは 0 件、(P3) 依頼 (2) は
実施済み、(P4) L-A1S-4 の「書き換え」は凍結稿を編集しない、(P5) 裁定と実施を分ける、の 5 つ。

## 3. 作り方 (3 層のずれを避ける手順)

1. 前版を複製し、時点語を 1 版ずらす機械置換を当てた (`artifacts/r1_timewords.py`) — 「前版」→「2026-09-20b 版」266 件、
   「この版」→「前版」216 件、「本版」→「この版」5 件、括弧付き版名 5 件。**「この版でも」「この版時点」「この版の基準」「この版が採る」は
   保護語として置換せず、後で 1 件ずつ起点での真偽を確かめた。**
2. 「・」の直後に入った空白 9 件を除去した (置換規則が「・」をカタカナ範囲と見なすため)。
3. 冒頭・§0・§2 (g)・§10 を全面差替え (`artifacts/splice.py` + 差替え本文)、§7 の後半 9 項を前半末尾へ移して後半 7 項を新設、
   他節は exact 1 回一致の置換表 (`artifacts/r2_*.json`〜`r33_*.json`、`apply.py`) で更新した。
4. claim-evidence は前稿を写し、冒頭・§1・§2 の該当行・§3 の限定・§4・§5・§6・§7 を同じ applier で更新し、新しい行 C38〜C43 と
   限定 L54〜L64 を足した (`artifacts/ce_*.json` / `ce_r2.py` / `ce_r5.py` / `ce_r6.py`)。
5. A-1 の 6 cell の値は公開 leaf の `result.json` 2 本から直接読み出した (`artifacts/a1_facts.py` / `a1_facts.out`)。稿 §2.7 と一致。

## 4. 検査

- `python3 tools/check_docs.py` 違反なし (版・claim-evidence・README・fragment の各段階で 5 回)。
- job dir の `artifacts/numcheck.py` — 本文が引く repo 内 path の実在、引いた D 番号が `docs/decisions.md` に実在すること、
  転記 literal 35 件 (A-1 の 6 値、B-5 の score と所要、B-8 の identity と runner、g1 の cause 名、K2 の値、F1036 の件数ほか) が
  名指した一次資料に逐語で在ること、claim-evidence が pin した版の sha256 と現物の一致 — **すべて一致**。
- `python3 tools/spool_fold.py --dry-run` rc=0 (status `planned`)。
- fig8b の provenance `429b4028…` を現物で再計算して版の記述と一致を確認した。
## 5. 段 6 — 敵対レビュー 1 本と焦点再レビュー 2 本 (`DW-O16` の上限 3 巡)

| 巡 | 子 | 所要 | 結果 |
|---|---|---|---|
| 1 | `review-1` (read-only、`gpt-6-astra` / medium) | 09:20〜09:28 JST、25 model call、wall 474 s | **NO-GO**。所見 12 件 = real 10 (must-fix 7 / should-fix 3) + refuted 2 |
| 2 | `focus-1` | 09:33〜09:38 JST、11 model call、wall 231 s | **NO-GO**。closed 6 / partial 4 / regressed 0 + 新規 3 件 |
| 3 | `focus-2` | 09:41〜09:44 JST | **NO-GO**。closed 5 / partial 2 / regressed 0 + 新規 1 件 |

逐語は `verbatim/` (prompt と出力を巡ごとに保存)。

**所見の型は 1 つに集約できる — claim-evidence の新稿が、前稿 (2026-09-19 版から作られた) の旧い限定をそのまま継承したうえに更新文を
足したため、同じ事実について古い現在形と新しい現在形が併存していた。** 1 巡目の 10 件は (1) g1 の「未発効・chain は main に無い・
A / X は人間手番」、(2) pin 前進前の「基準 HEAD の pin は `511c9538`」、(3) B-5 の「生成器の実装は認可されていない」、(4) B-7 の
「要件充足へは昇格させない」(D2044 項 3 は D2174 項 3 が supersede 済み)、(5) **「非列挙」の定義を「未裁定」と書いた前稿の誤り**
(D1441 は 2026-09-02 に裁定済みで、前稿の執筆時点で既に偽)、(6) 検証相の記録義務と B-8 の仕分けの旧手番、(7) **版**の
「LLM arm の親手番 1,080 巡」、(8) L51 の時点の欠落、(9) C35 の出所欄が消失した原本を無注記で案内、(10) §7 の継承表の 6 行の欠落。
**refuted 2 件は、依頼 (2) を実施済みとした親の (P3) と、L-A1S-4 の書き換えが解除へ滑っていないことの追認である。**

**(7) は版の訂正。** insight §8.1 の「本走 108 系列 = 3 workload × 3 arm × 12」から LLM arm は 36 系列と読み直し、36 × 10 巡 = 360 巡
(直列なら ≈ 60〜78 時間) へ改め、insight §8.2 が 108 系列すべてに 10 巡を掛けていることを版に明記した (**凍結 insight は変更しない**)。
2 巡目のレビューがこの再計算を独立に検算して一致を確認した (108 / 36 / 360 / 60〜78 時間、251.175 時間、53 session と 318 verify、
official floor の 35,817.945 / 46,065.78)。なお第 28 回 /rulings (D2200 項 1、本 wave の起点より後に着地) の理由欄も同じ 3 倍過大を
指摘しており、独立に同じ結論へ達している。

**3 巡とも NO-GO だったので、`DW-O16` の上限に従い、残る所見は親が一次資料で裏取りして閉じた。** 2・3 巡目の partial と新規所見に対する
親の処置は 15 箇所 — C13 (e) / L15 の「採用は裁定されたが未発効」、§4.2 A-4 の「発効していない」、C24 (b) の「候補文書は main に無い」
(現物と `git log -- output/s8b-freeze-candidates/holdout_freeze.v2.g1.json` で main 着地を確認)、§2.4 の禁止句「pin を前進させた」、
C34 の「4 commit 先」の基準、C1 (e) の「attempt-0002 は gate で拒否され測定値が無い」、§4.2 A-1 の差分欄「1 attempt の完走」、
C28 の「pin 前進は承認のみ」、§4.3 B-8 の「次版で仕分ける」、C23b / L38 / §5.6 の「cohort 2 は図を持たない」(fig8b は着地済み)、
§1.2 の「上の 8 条」(§1.1 は 9 条)、§4.3 B-2 の「chain は main に無い」など。**親は指定 6 語 (未発効・人間手番・未着地・承認のみ・
裁定待ち・次版で仕分ける) を自分で grep して残存を洗い、残した「人間手番」3 件 (GitHub 公開、上流還元の判断) と「未発効」の残存
(B-5 事前登録 v1、8c 正式系列、g1 の未発効候補文書) は対象を限定した正しい用法と判定した。**

**3 巡を通じて、版の本文に対する must-fix は (7) の 1 件だけで、他はすべて claim-evidence 側である。** 版は前版 (1 世代前) から
作ったのに対し、claim-evidence は 2 世代前の版から作られた前稿を継承したことが、この非対称の原因である。

## 6. 受入全走・検査

- `python3 tools/check_docs.py` 違反なし (版・claim-evidence・README・fragment の各段階)。
- job dir の `artifacts/numcheck.py` すべて一致 (fix のたびに再走。版の sha256 を claim-evidence の pin と突き合わせる検査を含む)。
- `python3 tools/spool_fold.py --dry-run` rc=0。
- 受入全走は記録 commit を含む最終 tip に land 前に 1 回投入し、受領証は job dir と land の記録が持つ。child-green でなければ land しない。

## 7. 一次資料

- 版: `docs/paper-story/2026-09-21b.md`、claim-evidence: `docs/paper-story/claim-evidence/2026-09-21.md`、入口: `docs/paper-story/README.md`。
- A-1 の値: 公開 leaf `output/insights/2026-09-13/paper-story-a1-balanced5-sized{,-attempt-0002}/result.json` (sha256 `372f199e…` / `b7e0518e…`)。
- B-5 の試走: `output/insights/2026-09-20/t2797-b5-contrast/README.md` §6 / §6.3 / §8、D2198 / D2199。
- g1 の validator: `output/insights/2026-09-20/t2810-g1-launch-validation/README.md`、D2196。
- 裁定: D2194 (第 27 回、全 14 項)、D2172 項 2・項 4、D2174 項 3、D2178、D2180、D2183、D2184、D2186 項 1、D2187、D2190、D2193、D1441、D1993 項 6。
- 逐語: `verbatim/` (段 1 brief、レビュー 3 巡の prompt と出力)。

## 8. 言わないこと

- 新規計測・新しい主張は無い。A-1 の充足・formal 化・非認証 lane・L-A1S-4 の解除には触れていない。
- 2 attempt から何も計算していない (プール・差・比・合成区間・区間の重なりの判定・再現判定・図を作らない)。
- B-5 の試走は主標本外 (n = 1 系列 / arm) で優劣を言わない。B-8 は承認であって取得ではない。g1 の validator の整合は P3 の受理ではない。
- gate・検査・台帳の追加、図の作成、英語稿、2 本目論文の版は行っていない。**レビュー 3 巡の「未確認」範囲は検証済みとして扱わない。**
