単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/paper-story-2026-09-21b

必読事項の射影: 下記の絶対パスを読む。**読めなければ即停止し、読めなかった path を報告せよ。**
この停止規則は下記に列挙した射影 file にだけ掛かる。お前が自分で探した path が不在でも、
それを理由に検査全体を打ち切ってはならない (その path は「不在」と記録して先へ進め)。

- /work/1/SFC/tanab/izanagi/.claude/worktrees/paper-story-2026-09-21b/docs/paper-story/2026-09-21b.md (**レビュー対象の新版**、778,391 bytes / 5,493 行 — **全文 `cat` しないこと**。`grep -n "^## \|^### \|^#### "` で節の位置を出し、`sed -n` で 80 行以内ずつ読め)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/paper-story-2026-09-21b/docs/paper-story/claim-evidence/2026-09-21.md (**レビュー対象の新稿**、251,391 bytes / 767 行。行が非常に長い表なので `grep -n "^| C21 \|^| L54 "` 等で行を特定し、`awk 'NR==<n>'` で 1 行ずつ読め)
- /home/SFC/tanab/.claude/jobs/0adb58a3/tmp/brief-s1.md (親の段 1 brief と provisional 裁定 (P1)〜(P5)。新版が従うべき scope と不変条件)
- /home/SFC/tanab/.claude/jobs/0adb58a3/tmp/codex/readme.diff (**この wave の README 更新の差分**。版の履歴表 1 行、「最新 =」、訂正一覧、stale 注記 2 件 → 0 件と移管先、claim-evidence 表 1 行)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/paper-story-2026-09-21b/docs/paper-story/2026-09-21.md (**前版**、736,407 bytes / 5,266 行、差分照合用。全文 cat 禁止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/paper-story-2026-09-21b/docs/paper-story/claim-evidence/2026-09-20.md (**前稿**、差分照合用。全文 cat 禁止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/paper-story-2026-09-21b/docs/paper-story/results/2026-09-20-a1-balanced5-sized-attempt2-descriptive.md (A-1 attempt-0002 の単独稿。**§2.7 が 2 attempt の並記の出所、§3 が限定 L-A1S2-1〜13 と L-A1S-4 の読み替え**)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/paper-story-2026-09-21b/docs/paper-story/results/2026-09-18-a1-balanced5-sized-attempt1-descriptive.md (attempt-0001 稿。**§3 の L-A1S-4 の原文**が新版の書き換えの対象)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/paper-story-2026-09-21b/output/insights/2026-09-20/t2797-b5-contrast/README.md (B-5 の残部品の実装と上限付き試走。§0・§6・§6.3・§8 が新版 §8 B-5 と claim-evidence C38 の出所)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/paper-story-2026-09-21b/output/insights/2026-09-20/t2810-g1-launch-validation/README.md (凍結 v2 g1 の launch validator の整合。§2・§5・§6 が新版 §8 A-4 (9) の出所)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/paper-story-2026-09-21b/output/insights/2026-09-20/t2792-a1-sized-attempt2/README.md (attempt-0002 の投入・時系列・受領証)

読んでよい (必要な節だけ) 資料: `output/insights/2026-09-20/t2807-b8-prerun/README.md` (B-8 の試走と発効束)、
`output/insights/2026-09-20/t2795-k2-pair-attempt/README.md` (K2 pair の不成立)、`output/insights/2026-09-20/k2-loop-originals-lost-downstream/README.md` (F1034 の下流影響)、
`output/insights/2026-09-21/branch-residue-cleanup/README.md` (F1036 と D2197)、`output/insights/2026-09-21/dev-wave-wall-decomp/README.md` (D2195)、
`output/insights/2026-09-21/paper-results-ja/README.md` と `output/insights/2026-09-21/paper-abstract-conclusion-ja/README.md` (日本語草稿の採用時点)、
`docs/paper-story/figures/README.md` (195 KB — fig13 / fig8b 節だけ)、公開 leaf `output/insights/2026-09-13/paper-story-a1-balanced5-sized{,-attempt-0002}/result.json` (`workloads[].statistics` だけ。`python3 -c` で key を取ってよい)。

**巨大 file の扱い (必ず守れ):** `docs/decisions.md` は約 5.9 MB / 70,000 行、`docs/failures.md` は約 2.8 MB。**全文 `cat` してはならない。**
`grep -n "^## D<番号>"` で位置を出し `sed -n` で 60 行以内ずつ読め。検算に要るのは **D2194 (第 27 回の全 14 項。`grep -n "^## D2194"`、項の見出しは `^### 項 `)**、
D2195 / D2196 / D2197 / D2198 / D2199、および新版が引く D2172 項 2・3・4、D2174 項 3、D2178、D2180、D2183、D2184、D2186 項 1・2・7、D2187、D2190、D2193。
F1034 / F1035 / F1036 は `grep -n "^### F103[456]" docs/failures.md`。worklog は `docs/worklog.md` (entry 1776〜1779) と archive
`docs/archive/worklog-phase3-0921-177[1-5].md` (entry 1771〜1775。本文は先頭 10〜60 行、残りは carry 行)。

この段では commit・push・file の書き込みを行わない。成果は最終メッセージの本文だけで返す
(read-only sandbox では `-o` の file を書けない。**出力は最終メッセージ本文に全文**)。
pytest・build・測定は走らせない (sandbox に書込可能 tmp が無い。静的検査でよい。テスト実測は親が行う)。
予算が尽きそうなら、途中までの結論を下記の出力形式どおりに書いて終われ。無出力が最悪である。

## 役割分担

親 (Claude) が新版と claim-evidence 新稿の本文を書いた。この wave は軽量版 (docs-only、実装面ゼロ) で、段 2 plan と段 3 敵対相談は省いた。
**お前は D2148 項 11 が定める「一次資料から事実を再抽出する docs-only wave の段 6 read-only 独立レビュー 1 本」であり、下の 2 レンズを 1 本で担う。**

親が実走した検査: `tools/check_docs.py` rc=0 (3 file とも)、job dir の numcheck (本文が引く repo 内 path の実在、引いた D 番号が
`docs/decisions.md` に実在すること、転記 literal 35 件が名指した一次資料に逐語で在ること、claim-evidence が pin した版の sha256 が現物と一致すること) が
すべて一致。A-1 の 6 cell の値は公開 leaf の `result.json` 2 本 (`372f199e…` / `b7e0518e…`) から直接読み出して表にした。fig8b の provenance
`429b4028…` は現物で再計算した。

**新版の作り方 (3 層のずれを疑え):** 前版 `2026-09-21.md` を複製し、**最初に機械置換 (「前版」→「2026-09-20b 版」266 件、「この版」→「前版」216 件、
「本版」→「この版」5 件、括弧付き版名 5 件、「・」直後に入った空白 9 件の除去) を当ててから**、冒頭・§0・§2 (g)・§10 を全面差替え、§7 の後半 9 項を前半へ移して
後半 7 項を新設し、他節は箇所ごとに exact 1 回一致の置換で再導出した (置換表 r2〜r33)。**したがって本文中の「2026-09-20b 版で X」「前版で X」は前版が
「前版で X」「この版で X」と書いていた事実で、「この版で X」は今回新しく書いた事実である。この 3 層がずれている箇所 (前版の出来事を「この版で」、
この版の出来事を「前版で」、2026-09-20b 版の出来事を「前版で」) があれば must-fix。** 機械置換で構造語・工程語 (節見出し、「この節は前版から引き写して
いない」、「§10 の契約」、「この版の要求事項」等) が誤変換された残りも探せ。**とくに「この版でも」「この版時点の事実」は機械置換から保護した語なので、
起点 `5efd69367` で偽になっていないかを 1 件ずつ確かめよ** (親は 3 件を見つけて直したと brief に書いている。他にも残っていないか)。

## レンズ

**レンズ A (一次資料との照合・母集合・射程・件数):**
1. **A-1 の 6 cell の表** (新版 §8 A-1 の表、claim-evidence C21)。値・h・B・sd/σ 比・分類・breach を公開 leaf の `result.json` 2 本と
   attempt-0002 稿 §2.7 で照合せよ。小数の丸め・桁区切り・符号を 1 つずつ見ろ。**B は attempt ごとに違う** (baseline 平均に依存)。
2. **B-5 の試走の数値** (新版 §0 の 3、§2 (c)、§6、§8 B-5、claim-evidence C38)。score 3 値・endpoint・CV・53 論理 session・318 verify 走・
   floor 3.0% の内側・最大差 1.06%・固有費 217〜509 s・lock 待ち 59%・job Elapse 61,261 s・親手番の待ち 7,360 s・rep 1 が最大の 36 session・
   本走の 1,773 論理 session × 510 s ≈ 251 時間を insight §6 / §6.3 / §8 と突き合わせよ。**単位 (論理 session / 物理 attempt / job) の取り違えを疑え。**
3. **g1 の validator** (新版 §2 (c) 床値、§8 A-4 (9)、claim-evidence C36 / L57)。段階番号 (段階 4 / 6 / 8)、cause 名 (`closure-hit-mismatch`、
   `manifest-invalid`、`generation-introduction`)、受理形 2 つ、変異 14/14、実 repo 実測の 2 回を insight と D2196 で照合せよ。
4. **D2194 の 14 項の要約** (新版 §0 の 1、§8 各項、claim-evidence C40)。**項番号と内容の対応**を D 本文で 1 件ずつ確かめよ (とくに項 2・3・4・5・8・9・10・11・12)。
5. **件数**: §7 の前半 109 + 後半 7 = 116 と `- [ ]` 行の実数、claim-evidence の C 行 (C1〜C43) と L (L01〜L64) の連番の穴・重複、
   運用素材「この版で加わった 5 つ」と実際の項目数、規律 7 の適用例「3 件」と実際の数、§0 の「6 点」と列挙数。
6. **path・D・T・F 番号**の実在 (親の numcheck は repo 内 path と D だけを見ている。T 番号と F 番号、insight の節番号 (§6.3 等) は未検査)。

**レンズ B (主張の強さ・分類の一貫性・二重計上・先取り):**
7. **L-A1S-4 の書き換えが「解除」に滑っていないか。** 新版 §8 A-1 の「L-A1S-4 の書き換え」小節、§2 (f)、§6、§7、§9、claim-evidence L54 / C21 を読み、
   **禁止の中身が保持されているか、根拠だけが替わっているか、「解除は裁定されていない」と書いてあるか**を確かめよ。attempt-0001 稿 §3 の L-A1S-4 の
   原文と読み比べて、引用・言い換えが原文の意味を変えていないか。**凍結稿を書き換えていないこと**も確かめよ (`git status` で稿が変更されていないこと)。
8. **並記が「再現」へ滑っていないか。** 6 cell の一致を「再現した」「安定している」「2 attempt で確かめた」と読ませる文、プールした推定量・差・比・
   区間の重なりの判定、図の作成の示唆が無いか。D2194 項 6 の「作らない」列挙と突き合わせよ。
9. **裁定と実施の区別** (D2194 の後段、B-8 の承認、K2 4 巡目、B-4 carrier、closure 次段、g1 候補文書の削除)。**「承認された」「裁定された」を
   「実施した」「取得した」と読ませる文**が無いか。逆に、実際に着地したもの ([T-2810]、B-5 試走、pin 前進) を「未着地」「未実施」と書いた箇所が無いか。
10. **分類の一貫性。** §9 の 7 種別への割り当て (B-5 の試走 score = 第 4 種、その verify = 第 5 種、裁定・工程 = 第 6 種) と、§0 の「増えたのは 4 種類」、
    claim-evidence の (c) 欄が矛盾していないか。**同じ観測を 2 つの種別へ置いていないか。**
11. **二重計上・取り込み漏れ。** README の stale 注記 2 件の移管先 (新版の節) が実在し、漏れなく取り込まれているか。README の版の履歴表の新しい行の
    headline が本文と食い違わないか。claim-evidence §7 の対応表が実際の行・限定の扱いと一致しているか。
12. **先取り・scope。** 稼働中で未着地の wave の内容を書いていないか (着地済み正典は local main `5efd69367`、entry 1779 まで)。新しい主張を足していないか。
    裁定を先取りしていないか (例: B-8 の校正・本走の結果、K2 の修復と 4 巡目、B-4 の carrier の実装、A-1 の 3 本目、L-A1S-4 の解除、B-5 の本走、
    g1 候補文書の削除、第 28 回 /rulings)。
13. **依頼 (2) を実施済みとした親の裁定 (P3) を攻撃せよ。** README の results 系列に fig13 の追補段落が実在するか、entry 1773 が [T-2816] の吸収を
    記録しているか、stale 注記に F1034 を積まない判断が README の規則 (「最新版の起点より後に着地したもの」) と整合するかを、現物で確かめよ。
14. **前版から消えた項目。** 前版 §5・§6・§7・§8 にあって新版に無い記述があれば列挙し、落としてよいか個別に判定せよ (§7 は 116 項で「落とした項目は
    無い」と書いてある)。claim-evidence でも前稿の行・限定が落ちていないか (前稿 C1〜C37 / L01〜L53 の継承)。

## 守らせる不変条件 (これを緩める所見は refuted として扱う)

- 凍結物 (旧版・前稿・results 稿・図・figures README) は 1 byte も変えない。旧 attempt の判定を取り消さない。protocol status は成否宣告ではない (D12)。規律 7。
- B-10 の言い方は事前登録 §4.5 の固定表現に限る。B-7 の充足は 4 語の限定付きでだけ書く。B-8 は取得と書かない。3 走行と A-1 の 2 attempt と B-7 fixed5 を
  pool しない (D1993 項 6)。2 attempt から何も計算しない。2 cohort を合成しない (D2157)。B-5 の試走は主標本外で優劣を言わない。
- 「A-1 の値がある」「再現した」「B-10 を閉じた」「mocc は第 2 成功例」「床値が発効したので oracle が走れる」「B-8 を取得した」とは書かない。
- 仮想リスク向けの gate・検査・台帳・一般化は scope 外。隣接 docs (results 稿・figures/) の訂正・図の作成・新しい主張の追加も scope 外。
  英語稿・2 本目論文の版は作らない。**L-A1S-4 の解除を提案する所見は refuted。**

## 出力形式 (この見出しをそのまま使う)

## 所見

番号付き。各所見に `real / refuted`、`must-fix / should-fix / nit`、該当 file と節 (§番号・行 ID)、一次資料の path または
D 番号、対案 (訂正後の文面) を書け。**所見ごとに、放置したときに論文の主張・分類・参照がどう変わるかを 1 行で書け**
(書けない所見は nit)。

## stale 注記 2 件の取り込み先

表 (README の項目 → 新版の節)。

## 照合して一致を確認した範囲

所見ではなく、消極的な証拠として記録する。数値群・参照群を列挙せよ。

## GO / NO-GO

新版と新稿をこのまま凍結してよいか。NO-GO なら must-fix の一覧。

## 総括

10 行以内。
